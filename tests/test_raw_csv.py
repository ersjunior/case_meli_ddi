"""
Validações sobre os CSVs sintéticos do case (sem banco).
"""
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


@pytest.fixture(scope="module")
def ddi() -> pd.DataFrame:
    return pd.read_csv(RAW / "tb_ddi.csv")


@pytest.fixture(scope="module")
def people() -> pd.DataFrame:
    return pd.read_csv(RAW / "tb_people_history.csv")


def test_raw_files_exist():
    assert (RAW / "tb_ddi.csv").is_file()
    assert (RAW / "tb_people_history.csv").is_file()


def test_ddi_columns(ddi: pd.DataFrame):
    cols = {"username", "date_month", "user_classification", "is_data_user"}
    assert cols.issubset(set(ddi.columns))


def test_people_columns(people: pd.DataFrame):
    cols = {
        "tim_day",
        "username",
        "start_date",
        "end_date",
        "country",
        "site",
        "department",
        "division",
        "function",
    }
    assert cols.issubset(set(people.columns))


def test_ddi_date_month_format(ddi: pd.DataFrame):
    sample = ddi["date_month"].astype(str).head(20)
    assert all(s[:4].isdigit() and s[4:5] == "-" for s in sample), "Esperado YYYY-MM"


def test_dataset_has_duplicate_user_month_for_dqi_story(ddi: pd.DataFrame):
    """O case pede reflexão sobre duplicidade — a amostra contém mais de uma linha por par."""
    dup = ddi.groupby(["username", "date_month"]).size()
    assert (dup > 1).any()


def test_shipping_representative_rows_exist(people: pd.DataFrame):
    """Garante que a regra de exclusão tem linhas para testar."""
    mask = (people["division"].astype(str) == "Shipping") & (
        people["function"].astype(str) == "Representative"
    )
    assert mask.any()


def test_ddi_classifications_expected_set(ddi: pd.DataFrame):
    allowed = {
        "Basic",
        "Beginner",
        "Intermediate",
        "No Use",
        "Sleeper",
        "Advanced",
        "Champion",
    }
    found = set(ddi["user_classification"].dropna().astype(str).unique())
    unknown = found - allowed
    assert not unknown, f"Classificações fora do esperado: {unknown}"
