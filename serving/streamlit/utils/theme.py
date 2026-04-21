"""
Paleta Mercado Livre: cinza/azul/verde + amarelo (#FFF159) sutil.
Gráficos Plotly seguem o tema do app (menu ⋮ → Configurações → Tema: Claro / Escuro).
"""

from __future__ import annotations

from typing import Any, Literal

import plotly.graph_objects as go
import streamlit as st

# Amarelo marca (uso sutil — bordas, hover, modo escuro)
MELI_YELLOW = "#FFF159"
MELI_YELLOW_SOFT = "rgba(255, 241, 89, 0.35)"

LIGHT: dict[str, Any] = {
    "bg": "#FFFFFF",
    "surface": "#F5F5F5",
    "surface_card": "#FAFAFA",
    "text": "#333333",
    "text_muted": "#737373",
    "border": "#E6E6E6",
    "blue": "#3483FA",
    "blue_dark": "#2968C8",
    "gray": "#B8B8B8",
    "gray_dark": "#767676",
    "green": "#00A650",
    "red": "#F23D4F",
    "grid": "#EFEFEF",
    "legend_bg": "rgba(255,255,255,0.85)",
    "yellow_accent": MELI_YELLOW,
}

DARK: dict[str, Any] = {
    "bg": "#0E0E0E",
    "surface": "#1A1A1A",
    "surface_card": "#141414",
    "text": "#F0F0F0",
    "text_muted": "#A3A3A3",
    "border": "#333333",
    "blue": "#4DA3FF",
    "blue_dark": "#3483FA",
    "gray": "#6B6B6B",
    "gray_dark": "#9A9A9A",
    "green": "#3DDC84",
    "red": "#FF6B7A",
    "grid": "#2A2A2A",
    "legend_bg": "rgba(20,20,20,0.92)",
    "yellow_accent": MELI_YELLOW,
}

# Compatibilidade com imports antigos `MELI` (referência claro)
MELI = LIGHT


def _streamlit_app_theme_type() -> Literal["light", "dark"]:
    """
    Tema ativo conforme o menu do Streamlit (⋮ → Configurações → Tema).
    API oficial: ``st.context.theme.type`` em ``"light"`` | ``"dark"`` | ``None``.
    """
    try:
        th = st.context.theme
        t = getattr(th, "type", None) if th is not None else None
        if t in ("light", "dark"):
            return t  # type: ignore[return-value]
    except Exception:
        pass
    return "light"


def chart_palette() -> dict[str, Any]:
    """Paleta Plotly alinhada ao tema Claro/Escuro escolhido nas configurações do Streamlit."""
    return DARK if _streamlit_app_theme_type() == "dark" else LIGHT


def plotly_streamlit_config() -> dict[str, Any]:
    return {
        "responsive": True,
        "displayModeBar": True,
        "displaylogo": False,
        "scrollZoom": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "toImageButtonOptions": {"format": "png"},
    }


def apply_meli_theme() -> None:
    """CSS complementar (não força fundo do app — deixa o tema Claro/Escuro do Streamlit atuar)."""
    # Remover chave legada do rádio na sidebar (forçava paleta "light" na sessão).
    st.session_state.pop("chart_theme_mode", None)

    st.markdown(
        f"""
        <style>
          html[data-theme="dark"] [data-testid="stSidebar"] {{
            border-right: 3px solid {MELI_YELLOW_SOFT};
          }}
          html[data-theme="dark"] [data-testid="stHeader"] {{
            border-bottom: 1px solid {MELI_YELLOW_SOFT};
          }}
          html[data-theme="light"] [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{
            border-left: 3px solid {MELI_YELLOW};
            padding-left: 0.65rem;
          }}
          [data-testid="stMetricDelta"] {{
            font-weight: 600;
          }}
          div[data-testid="stExpander"] {{
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 8px;
          }}
          .js-plotly-plot .plotly {{
            width: 100% !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def meli_figure_layout(
    fig: go.Figure,
    *,
    title: str,
    y_title: str | None = None,
    x_title: str | None = None,
    palette: dict[str, Any] | None = None,
    hovermode: str = "closest",
) -> go.Figure:
    """
    ``hovermode``:
    - ``\"y unified\"`` — ideal para **barras horizontais**: tooltip ao mover na faixa da categoria (eixo Y / rótulo).
    - ``\"x unified\"`` — ideal para **linhas no tempo**: compara séries no mesmo mês.
    - ``\"closest\"`` — ponto mais próximo (padrão genérico).
    """
    c = palette or chart_palette()
    fig.update_layout(
        title=dict(text=title, font=dict(size=17, color=c["text"]), x=0, xanchor="left"),
        paper_bgcolor=c["bg"],
        plot_bgcolor=c["bg"],
        font=dict(color=c["text"], family="system-ui, Segoe UI, sans-serif", size=13),
        margin=dict(l=48, r=24, t=56, b=48),
        xaxis=dict(
            title=x_title,
            showgrid=True,
            gridcolor=c["grid"],
            linecolor=c["border"],
            zeroline=False,
        ),
        yaxis=dict(
            title=y_title,
            showgrid=True,
            gridcolor=c["grid"],
            linecolor=c["border"],
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor=c["legend_bg"],
        ),
        hovermode=hovermode,
        hoverdistance=-1,
        hoverlabel=dict(
            bgcolor=c["surface_card"],
            font_size=13,
            font_family="system-ui, Segoe UI, sans-serif",
            bordercolor=c.get("yellow_accent", MELI_YELLOW),
        ),
    )
    # Faixa horizontal por categoria (melhora hover nas barras horizontais e perto dos rótulos Y)
    if hovermode == "y unified":
        fig.update_yaxes(
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikecolor=c["border"],
            spikethickness=1,
        )
    if hovermode == "x unified":
        fig.update_xaxes(
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikecolor=c["border"],
            spikethickness=1,
        )
    return fig


def render_kpi_metrics(
    items: list[tuple[str, str | int | float, int | float | None, str]],
) -> None:
    """
    KPIs nativos Streamlit (sem HTML).
    items: (rótulo, valor, delta numérico vs. período anterior ou None, caption)
    """
    cols = st.columns(len(items))
    for col, (label, value, delta, hint) in zip(cols, items):
        with col:
            with st.container(border=True):
                if delta is not None:
                    st.metric(label=label, value=value, delta=delta, delta_color="normal")
                else:
                    st.metric(label=label, value=value)
                st.caption(hint)
