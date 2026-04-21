"""
Validações contra o warehouse Postgres (mesmo alvo do Streamlit/dbt).

Exporte DATABASE_URL, ex.:
  set DATABASE_URL=postgresql+psycopg2://airflow:airflow@localhost:5433/airflow
"""
import os

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration

ALLOWED_CLASSIFICATIONS = {
    "Basic",
    "Beginner",
    "Intermediate",
    "No Use",
    "Sleeper",
    "Advanced",
    "Champion",
    "Sem registro DDI",
}


def _engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL não definido")
    return create_engine(url, pool_pre_ping=True)


@pytest.fixture(scope="module")
def engine():
    return _engine()


def test_agg_ddi_month_exists(engine):
    q = text(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'analytics' AND table_name = 'agg_ddi_month'"
    )
    with engine.connect() as conn:
        assert conn.execute(q).scalar() == 1


def test_fct_user_month_unique_grain(engine):
    q = text(
        """
        SELECT username, date_month, COUNT(*) AS c
        FROM analytics.fct_user_month
        GROUP BY 1, 2
        HAVING COUNT(*) > 1
        """
    )
    with engine.connect() as conn:
        bad = conn.execute(q).fetchall()
    assert not bad, f"Duplicidade user-month: {bad[:5]}"


def test_agg_coverage_rate_bounds(engine):
    q = text(
        """
        SELECT MIN(coverage_rate) AS lo, MAX(coverage_rate) AS hi
        FROM analytics.agg_ddi_month
        WHERE coverage_rate IS NOT NULL
        """
    )
    with engine.connect() as conn:
        lo, hi = conn.execute(q).one()
    assert lo is not None and hi is not None
    assert 0 <= float(lo) <= 100
    assert 0 <= float(hi) <= 100


def test_agg_classifications_allowed(engine):
    q = text(
        "SELECT DISTINCT user_classification FROM analytics.agg_ddi_month"
    )
    with engine.connect() as conn:
        rows = {r[0] for r in conn.execute(q)}
    unknown = rows - ALLOWED_CLASSIFICATIONS
    assert not unknown, unknown


def test_agg_non_negative_counts(engine):
    q = text(
        """
        SELECT COUNT(*) FROM analytics.agg_ddi_month
        WHERE active_collaborators < 0
           OR potential_users < 0
           OR data_driven_users < 0
        """
    )
    with engine.connect() as conn:
        n = conn.execute(q).scalar()
    assert n == 0


def test_fct_rowcount_matches_expectation_order_of_magnitude(engine):
    """Sanidade: fato user-month na ordem de milhares para a amostra 800 users x 12 meses."""
    q = text("SELECT COUNT(*) FROM analytics.fct_user_month")
    with engine.connect() as conn:
        n = conn.execute(q).scalar()
    assert 5000 < n < 20000
