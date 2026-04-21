import plotly.graph_objects as go
import streamlit as st

from utils.dates_filter import filter_df_by_month_range, month_range_filter_ui
from utils.db import mart_fqn, run_query
from utils.narrative import insight_block, page_header
from utils.theme import apply_meli_theme, chart_palette, meli_figure_layout, plotly_streamlit_config, render_kpi_metrics

apply_meli_theme()

page_header(
    "Evolution",
    "O que mudou no tempo — base (cinza tracejado) vs. data-driven (azul). Ajuste período e tema dos gráficos na barra lateral.",
)

try:
    agg_tbl = mart_fqn("agg_ddi_month")
except RuntimeError as exc:
    st.markdown(str(exc))
    st.stop()

query = f"""
SELECT date_month,
       SUM(active_collaborators) AS active,
       SUM(data_driven_users) AS data_users
FROM {agg_tbl}
GROUP BY date_month
ORDER BY date_month
"""

try:
    df = run_query(query)
except Exception as exc:
    st.error(f"Erro ao consultar `{agg_tbl}`: {exc}")
    st.stop()

pal = chart_palette()

st.subheader("Filtros")
d_start, d_end = month_range_filter_ui(
    df,
    date_col="date_month",
    key_prefix="evo",
    show_period_caption=False,
)
df = filter_df_by_month_range(df, d_start, d_end, date_col="date_month")

if df.empty:
    st.warning("Sem pontos na série para o período selecionado.")
    st.stop()

st.caption(
    f"Período **{d_start.strftime('%d/%m/%Y')}** → **{d_end.strftime('%d/%m/%Y')}** · série mensal no intervalo."
)

df = df.sort_values("date_month").reset_index(drop=True)
df["mom_pct"] = df["data_users"].pct_change()

current = df.iloc[-1]
previous = df.iloc[-2] if len(df) > 1 else current
mom_abs = int(current["data_users"] - previous["data_users"])
mom_pct = current["mom_pct"]
mom_pct_str = f"{mom_pct * 100:.2f}%" if mom_pct == mom_pct and mom_pct is not None else "—"

insight_block(
    eyebrow="Pergunta do case",
    pergunta="O que mudou mês a mês na adoção data-driven?",
    texto=(
        "Os cartões usam os **dois últimos meses do período filtrado**. O gráfico mostra toda a série no intervalo; "
        "passe o mouse para ver valores e compare as duas linhas."
    ),
    section_id="evolution_kpis",
    llm_context={
        "pagina": "evolution",
        "periodo": {"de": str(d_start), "ate": str(d_end)},
        "ultimo_mes": str(current["date_month"]),
        "mes_anterior": str(previous["date_month"]),
        "data_driven_ultimo": int(current["data_users"]),
        "data_driven_anterior": int(previous["data_users"]),
        "mom_abs": mom_abs,
        "mom_pct": mom_pct_str,
        "active_ultimo": int(current["active"]),
        "active_anterior": int(previous["active"]),
    },
)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.metric(
            label="Data-driven — último mês do período",
            value=int(current["data_users"]),
            delta=mom_abs,
            delta_color="normal",
        )
        st.caption("Variação absoluta vs. mês anterior no recorte.")
with c2:
    with st.container(border=True):
        st.metric(label="Variação % MoM (data-driven)", value=mom_pct_str)
        st.caption("Percentual mês a mês sobre usuários data-driven.")

insight_block(
    eyebrow="Leitura do visual",
    pergunta="A adoção acompanha a expansão da base?",
    texto=(
        "Se a linha azul sobe mais rápido que a cinza, há **ganho de maturidade relativa**. "
        "Tooltips unificados no eixo X facilitam comparar os dois indicadores no mesmo mês."
    ),
    section_id="evolution_serie",
    llm_context={
        "pagina": "evolution",
        "periodo": {"de": str(d_start), "ate": str(d_end)},
        "serie_mensal_ultimos_pontos": df[["date_month", "active", "data_users"]]
        .tail(12)
        .to_dict(orient="records"),
    },
)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df["date_month"],
        y=df["active"],
        name="Base — ativos",
        mode="lines",
        line=dict(color=pal["gray_dark"], width=2, dash="dash"),
        hovertemplate="<b>Base — ativos</b><br>%{x|%b %Y}<br>%{y:,}<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=df["date_month"],
        y=df["data_users"],
        name="Data-driven",
        mode="lines+markers",
        line=dict(color=pal["blue"], width=3),
        marker=dict(size=9, color=pal["blue"], line=dict(width=1, color=pal.get("yellow_accent", "#FFF159"))),
        hovertemplate="<b>Data-driven</b><br>%{x|%b %Y}<br>%{y:,}<extra></extra>",
    )
)
meli_figure_layout(
    fig,
    title="Evolução — base vs. usuários data-driven",
    y_title="Pessoas",
    x_title="Mês",
    palette=pal,
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True, config=plotly_streamlit_config())

with st.expander("Tabela de apoio (série mensal)"):
    st.dataframe(
        df.assign(mom_pct_fmt=df["mom_pct"].map(lambda x: f"{x * 100:.2f}%" if x == x else "")),
        use_container_width=True,
        hide_index=True,
    )
