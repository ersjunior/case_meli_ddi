#!/bin/bash
# Carga inicial: DDL + CSV + dbt (roda uma vez no compose antes do Streamlit).
# Sem "pipefail" para compatibilidade; arquivo deve estar em LF (ver .gitattributes).
set -eu

PGURL="${PIPELINE_POSTGRES_URL:-postgresql://airflow:airflow@postgres:5432/airflow}"

echo "[bootstrap] DDL + schema..."
psql "$PGURL" -v ON_ERROR_STOP=1 -f /bootstrap_ddl.sql

echo "[bootstrap] Truncate raw..."
psql "$PGURL" -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE tb_ddi, tb_people_history;"

echo "[bootstrap] COPY CSV..."
psql "$PGURL" -v ON_ERROR_STOP=1 <<'EOSQL'
\copy tb_people_history FROM '/data/tb_people_history.csv' WITH (FORMAT csv, HEADER true);
\copy tb_ddi FROM '/data/tb_ddi.csv' WITH (FORMAT csv, HEADER true);
EOSQL

echo "[bootstrap] dbt run + test..."
cd /dbt
dbt run --profiles-dir .
dbt test --profiles-dir .

echo "[bootstrap] OK."
