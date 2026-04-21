import os
import re

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, event, text


def _analytics_schema() -> str:
    raw = os.getenv(
        "DBT_POSTGRES_SCHEMA",
        os.getenv("PG_SCHEMA", "analytics"),
    ).strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", raw):
        return "analytics"
    return raw


def _redact_database_url(url: str) -> str:
    if not url or url == "(não definido — usando default do código)":
        return url
    return re.sub(r":([^:@/]+)@", r":***@", url, count=1)


def _missing_mart_message(table_name: str) -> str:
    publish = os.getenv("POSTGRES_PUBLISH_PORT", "5433")
    url = os.getenv("DATABASE_URL", "(não definido — usando default do código)")
    return (
        f"### Tabela `{table_name}` não encontrada neste Postgres\n\n"
        "**O que conferir:**\n\n"
        "1. **Airflow** — DAG `ddi_pipeline` ligado e executado (**Trigger**). Todas as tasks, "
        "principalmente **dbt_run**, devem ficar verdes.\n\n"
        "2. **Mesmo banco que o Docker** — Se o Streamlit roda **no seu Windows** (fora do container), "
        "`DATABASE_URL` tem que apontar para o Postgres **publicado pelo compose**. "
        f"Por padrão usamos a porta **{publish}** no host (evita conflito com Postgres local na 5432). "
        "Exemplo: `postgresql+psycopg2://airflow:airflow@localhost:"
        f"{publish}/airflow`\n\n"
        "3. **Streamlit dentro do Docker** — use `DATABASE_URL` com host `postgres` (já está no compose).\n\n"
        f"**URL em uso (senha oculta):** `{_redact_database_url(url)}`"
    )


@st.cache_resource
def get_connection():
    url = os.getenv(
        "DATABASE_URL",
        # Compose publica Postgres no host em 5433 por padrão (evita conflito com Postgres local).
        "postgresql+psycopg2://airflow:airflow@localhost:5433/airflow",
    )

    engine = create_engine(url, pool_pre_ping=True)

    @event.listens_for(engine, "connect")
    def _set_search_path(dbapi_connection, _connection_record) -> None:
        schema = _analytics_schema()
        cur = dbapi_connection.cursor()
        cur.execute("SET search_path TO %s, public", (schema,))
        cur.close()

    return engine


@st.cache_data(ttl=30)
def mart_fqn(table_name: str) -> str:
    """
    Descobre schema.tabela no banco atual (information_schema).
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
        raise ValueError("Nome de tabela inválido")

    engine = get_connection()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_schema
                FROM information_schema.tables
                WHERE table_name = :tname
                  AND table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY
                    CASE WHEN table_schema = 'analytics' THEN 0 ELSE 1 END,
                    table_schema
                """
            ),
            {"tname": table_name},
        ).fetchall()

    if not rows:
        raise RuntimeError(_missing_mart_message(table_name))

    schema = rows[0][0]
    return f"{schema}.{table_name}"


@st.cache_data(ttl=300)
def run_query(query: str) -> pd.DataFrame:
    engine = get_connection()
    return pd.read_sql(query, engine)
