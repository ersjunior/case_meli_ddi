import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

default_args = {
    "owner": "analytics_engineer",
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
}

_pipeline_pg_url = os.environ.get(
    "PIPELINE_POSTGRES_URL",
    "postgresql://airflow:airflow@postgres:5432/airflow",
)

_bash_env = {
    "PIPELINE_POSTGRES_URL": _pipeline_pg_url,
}

with DAG(
    dag_id="ddi_pipeline",
    default_args=default_args,
    schedule_interval="@monthly",
    catchup=False,
    description="ELT DDI: raw → dbt (Mercado Livre case)",
    tags=["analytics", "dbt", "ddi"],
) as dag:

    create_tables = PostgresOperator(
        task_id="create_raw_tables",
        postgres_conn_id="postgres_default",
        sql="""
        CREATE TABLE IF NOT EXISTS tb_people_history (
            tim_day DATE,
            username TEXT,
            start_date DATE,
            end_date DATE,
            country TEXT,
            site TEXT,
            department TEXT,
            division TEXT,
            function TEXT
        );

        CREATE TABLE IF NOT EXISTS tb_ddi (
            username TEXT,
            date_month TEXT,
            user_classification TEXT,
            is_data_user BOOLEAN
        );

        CREATE SCHEMA IF NOT EXISTS analytics;
        """,
    )

    truncate_raw = PostgresOperator(
        task_id="truncate_raw_tables",
        postgres_conn_id="postgres_default",
        sql="TRUNCATE TABLE tb_ddi, tb_people_history;",
    )

    ingest_people = BashOperator(
        task_id="ingest_people_history",
        env=_bash_env,
        bash_command=r"""
set -euo pipefail
psql "${PIPELINE_POSTGRES_URL}" -v ON_ERROR_STOP=1 <<'EOSQL'
\copy tb_people_history FROM '/opt/airflow/dags/data/tb_people_history.csv' WITH (FORMAT csv, HEADER true);
EOSQL
""",
    )

    ingest_ddi = BashOperator(
        task_id="ingest_ddi",
        env=_bash_env,
        bash_command=r"""
set -euo pipefail
psql "${PIPELINE_POSTGRES_URL}" -v ON_ERROR_STOP=1 <<'EOSQL'
\copy tb_ddi FROM '/opt/airflow/dags/data/tb_ddi.csv' WITH (FORMAT csv, HEADER true);
EOSQL
""",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="""
set -euo pipefail
cd /opt/airflow/dbt
dbt run --profiles-dir .
""",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="""
set -euo pipefail
cd /opt/airflow/dbt
dbt test --profiles-dir .
""",
    )

    create_tables >> truncate_raw >> [ingest_people, ingest_ddi] >> dbt_run >> dbt_test
