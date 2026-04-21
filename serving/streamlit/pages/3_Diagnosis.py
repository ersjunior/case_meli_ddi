import plotly.graph_objects as go
import streamlit as st

from utils.dates_filter import filter_df_by_month_range, month_range_filter_ui
from utils.db import mart_fqn, run_query
from utils.narrative import insight_block, page_header
from utils.theme import apply_meli_theme, chart_palette, meli_figure_layout, plotly_streamlit_config

apply_meli_theme()

page_header(
    "Diagnosis",
    "Decomposição por division e departamento; último mês **dentro do período** selecionado.",
)

try:
    agg_tbl = mart_fqn("agg_ddi_month")
except RuntimeError as exc:
    st.markdown(str(exc))
    st.stop()

query = f"""
SELECT *
FROM {agg_tbl}
"""

try:
    df = run_query(query)
except Exception as exc:
    st.error(f"Erro ao consultar `{agg_tbl}`: {exc}")
    st.stop()

pal = chart_palette()

insight_block(
    eyebrow="Pergunta do case",
    pergunta="Onde estão os desvios e concentrações que explicam o índice?",
    texto=(
        "Filtre o **período** e a **division**. O gráfico usa o último mês disponível nesse recorte; "
        "tooltips mostram valores ao passar o mouse."
    ),
    section_id="diagnosis_intro",
    llm_context={
        "pagina": "diagnosis",
        "periodo": {"de": str(df["date_month"].min()), "ate": str(df["date_month"].max())},
        "division": sorted(df["division"].astype(str).unique()),
    },
)

st.subheader("Filtros")
c_period, c_div = st.columns([0.85, 0.85], gap="small")
d_start, d_end = month_range_filter_ui(
    df,
    date_col="date_month",
    key_prefix="dx",
    col_period=c_period,
    show_period_caption=False,
)
df = filter_df_by_month_range(df, d_start, d_end, date_col="date_month")

if df.empty:
    st.warning("Sem dados no período selecionado.")
    st.stop()

with c_div:
    division = st.selectbox("Division", sorted(df["division"].astype(str).unique()))

st.caption(
    f"Período **{d_start.strftime('%d/%m/%Y')}** → **{d_end.strftime('%d/%m/%Y')}** · Division: **{division}**"
)

d_div = df[df["division"] == division]

latest = d_div["date_month"].max()
d_latest = d_div[d_div["date_month"] == latest]

if d_latest.empty:
    st.warning("Sem dados para esta division no último mês do período.")
    st.stop()

by_dept = (
    d_latest.groupby("department", as_index=False)["data_driven_users"]
    .sum()
    .sort_values("data_driven_users", ascending=True)
)

insight_block(
    eyebrow="Leitura do visual",
    pergunta="Quais departamentos puxam (ou seguram) a curva nesta division?",
    texto=(
        "Barras horizontais em **azul**; compare comprimentos e use o hover para leitura exata."
    ),
    section_id="diagnosis_departamentos",
    llm_context={
        "pagina": "diagnosis",
        "division": division,
        "ultimo_mes_periodo": str(latest),
        "por_departamento_data_driven": by_dept.to_dict(orient="records"),
    },
)

fig = go.Figure(
    go.Bar(
        x=by_dept["data_driven_users"],
        y=by_dept["department"],
        orientation="h",
        marker=dict(color=pal["blue"], line=dict(color=pal["blue_dark"], width=1)),
        name="Data-driven",
        hovertemplate="<b>%{y}</b><br>Data-driven: %{x:,}<extra></extra>",
    )
)
meli_figure_layout(
    fig,
    title=f"Usuários data-driven por departamento — {division} (último mês do período)",
    x_title="Usuários data-driven",
    palette=pal,
    hovermode="y unified",
)
st.plotly_chart(fig, use_container_width=True, config=plotly_streamlit_config())

with st.expander("Detalhe classificação × departamento (último mês do período)"):
    det = d_latest.sort_values(
        ["department", "user_classification"],
        ascending=[True, True],
    )[
        [
            "department",
            "user_classification",
            "active_collaborators",
            "data_driven_users",
            "potential_users",
        ]
    ]
    st.dataframe(det, use_container_width=True, hide_index=True)

insight_block(
    eyebrow="Próximo passo",
    pergunta="Como isso fecha com as respostas do case?",
    texto=(
        "Na página **Resoluções** estão consolidadas as respostas escritas ao desafio, alinhadas à modelagem e às métricas."
    ),
)
