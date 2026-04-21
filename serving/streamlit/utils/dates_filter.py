"""Filtro de intervalo de datas para séries mensais (`date_month` = início do mês)."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st


def month_range_bounds(df: pd.DataFrame, *, date_col: str = "date_month") -> tuple[date, date] | None:
    """Retorna (d_min, d_max) ou None se não houver datas válidas."""
    if df.empty or date_col not in df.columns:
        return None
    s = pd.to_datetime(df[date_col], errors="coerce").dropna()
    if s.empty:
        return None
    d_min = s.min().normalize().date()
    d_max = s.max().normalize().date()
    return d_min, d_max


def _coerce_date_range(
    dr: Any,
    d_min: date,
    d_max: date,
) -> tuple[date, date]:
    """Normaliza o retorno do ``date_input`` em modo intervalo."""
    if isinstance(dr, (list, tuple)):
        if len(dr) >= 2:
            a, b = dr[0], dr[1]
            if isinstance(a, date) and isinstance(b, date):
                return (a, b) if a <= b else (b, a)
        if len(dr) == 1 and isinstance(dr[0], date):
            return dr[0], dr[0]
    if isinstance(dr, date):
        return dr, dr
    return d_min, d_max


def month_range_filter_ui(
    df: pd.DataFrame,
    *,
    date_col: str = "date_month",
    key_prefix: str = "range",
    col_period: Any | None = None,
    show_period_caption: bool = True,
) -> tuple[date, date]:
    """
    Um único controle **Período** (intervalo De → Até) via ``st.date_input`` com duas datas.

    ``col_period``: coluna Streamlit onde o widget deve aparecer (ex.: primeira coluna da linha de filtros).
    Se ``None``, ocupa a largura disponível do container atual.
    """
    bounds = month_range_bounds(df, date_col=date_col)
    if bounds is None:
        st.warning("Sem coluna de datas ou datas inválidas para filtrar.")
        today = date.today()
        return today, today

    d_min, d_max = bounds
    ctx = col_period if col_period is not None else nullcontext()

    with ctx:
        dr = st.date_input(
            "Período",
            value=(d_min, d_max),
            min_value=d_min,
            max_value=d_max,
            format="DD/MM/YYYY",
            key=f"{key_prefix}_period",
            help="Selecione a data inicial e a final do intervalo (um único controle).",
        )

    d_start, d_end = _coerce_date_range(dr, d_min, d_max)

    if d_start > d_end:
        st.error("A data inicial não pode ser posterior à data final.")
        st.stop()

    if show_period_caption:
        st.caption(
            f"Período: **{d_start.strftime('%d/%m/%Y')}** → **{d_end.strftime('%d/%m/%Y')}** · agregados mensais."
        )

    return d_start, d_end


def filter_df_by_month_range(
    df: pd.DataFrame,
    d_start: date,
    d_end: date,
    *,
    date_col: str = "date_month",
) -> pd.DataFrame:
    dm = pd.to_datetime(df[date_col], errors="coerce")
    p = dm.dt.to_period("M")
    p0 = pd.Timestamp(d_start).to_period("M")
    p1 = pd.Timestamp(d_end).to_period("M")
    return df[(p >= p0) & (p <= p1)].copy()
