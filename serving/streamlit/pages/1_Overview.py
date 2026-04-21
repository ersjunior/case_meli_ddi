import plotly.graph_objects as go
import streamlit as st

from utils.dates_filter import filter_df_by_month_range, month_range_filter_ui
from utils.db import mart_fqn, run_query
from utils.narrative import insight_block, page_header
from utils.theme import apply_meli_theme, chart_palette, meli_figure_layout, plotly_streamlit_config, render_kpi_metrics

apply_meli_theme()

page_header(
    "Overview",
    "Onde estamos na maturidade analítica — base (colaboradores), adoção data-driven (azul) e potencial de expansão.",
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

st.subheader("Filtros")
c_period, c_site, c_div = st.columns([0.85, 0.85, 0.85], gap="small")
d_start, d_end = month_range_filter_ui(
    df,
    date_col="date_month",
    key_prefix="ov",
    col_period=c_period,
    show_period_caption=False,
)
df = filter_df_by_month_range(df, d_start, d_end, date_col="date_month")

with c_site:
    site = st.selectbox("Site", ["Todos"] + sorted(df["site"].astype(str).unique()))
with c_div:
    division = st.selectbox("Division", ["Todos"] + sorted(df["division"].astype(str).unique()))

st.caption(
    f"Período **{d_start.strftime('%d/%m/%Y')}** → **{d_end.strftime('%d/%m/%Y')}** · "
    f"Site: **{site}** · Division: **{division}**"
)

if site != "Todos":
    df = df[df["site"] == site]
if division != "Todos":
    df = df[df["division"] == division]

kpi_df = (
    df.groupby("date_month", as_index=False)
    .agg(
        active_collaborators=("active_collaborators", "sum"),
        data_driven_users=("data_driven_users", "sum"),
        potential_users=("potential_users", "sum"),
    )
    .sort_values("date_month")
)

if kpi_df.empty:
    st.warning("Sem dados para os filtros selecionados.")
    st.stop()

current = kpi_df.iloc[-1]
previous = kpi_df.iloc[-2] if len(kpi_df) > 1 else current

d_act = int(current["active_collaborators"] - previous["active_collaborators"])
d_dd = int(current["data_driven_users"] - previous["data_driven_users"])
d_pot = int(current["potential_users"] - previous["potential_users"])

insight_block(
    eyebrow="Pergunta do case",
    pergunta="Onde estamos hoje em termos de maturidade analítica?",
    texto=(
        "Os cartões consolidam o **último mês do período filtrado** vs. o mês anterior nesse mesmo recorte: "
        "**base** (colaboradores ativos), **data-driven** e **potencial**. "
        "Deltas em verde/vermelho seguem o padrão do Streamlit (crescimento vs. retração)."
    ),
    section_id="overview_kpis",
    llm_context={
        "pagina": "overview",
        "periodo": {"de": str(d_start), "ate": str(d_end)},
        "filtros": {"site": site, "division": division},
        "kpi_ultimo_mes_do_recorte": {
            "active_collaborators": int(current["active_collaborators"]),
            "delta_active_vs_anterior": d_act,
            "data_driven_users": int(current["data_driven_users"]),
            "delta_data_driven_vs_anterior": d_dd,
            "potential_users": int(current["potential_users"]),
            "delta_potential_vs_anterior": d_pot,
        },
        "kpi_mes_anterior": {
            "active_collaborators": int(previous["active_collaborators"]),
            "data_driven_users": int(previous["data_driven_users"]),
            "potential_users": int(previous["potential_users"]),
        },
    },
)

render_kpi_metrics(
    [
        (
            "Base — colaboradores ativos",
            int(current["active_collaborators"]),
            d_act,
            "Universo operacional; referência estrutural (cinza nos gráficos de site).",
        ),
        (
            "Data-driven — adoção",
            int(current["data_driven_users"]),
            d_dd,
            "Usuários classificados como data-driven (azul nos gráficos).",
        ),
        (
            "Potencial — ainda não data-driven",
            int(current["potential_users"]),
            d_pot,
            "Oportunidade de expansão de maturidade.",
        ),
    ]
)

latest = df["date_month"].max()
snap = df[df["date_month"] == latest]

if snap.empty:
    st.warning("Sem snapshot para o último mês do período.")
    st.stop()

by_class = (
    snap.groupby("user_classification", as_index=False)["active_collaborators"]
    .sum()
    .sort_values("active_collaborators", ascending=True)
)

insight_block(
    eyebrow="Leitura do visual",
    pergunta="Como a base se distribui por classificação no fim do período?",
    texto=(
        "Barras em **azul** mostram colaboradores ativos por classificação no último mês do recorte. "
        "Passe o mouse sobre as barras para ver valores exatos."
    ),
    section_id="overview_classificacao",
    llm_context={
        "pagina": "overview",
        "grafico": "colaboradores_por_classificacao",
        "ultimo_mes_periodo": str(latest),
        "filtros": {"site": site, "division": division},
        "por_classificacao": by_class.to_dict(orient="records"),
    },
)

fig_class = go.Figure(
    go.Bar(
        x=by_class["active_collaborators"],
        y=by_class["user_classification"],
        orientation="h",
        marker=dict(color=pal["blue"], line=dict(color=pal["blue_dark"], width=1)),
        name="Ativos",
        hovertemplate="<b>%{y}</b><br>Colaboradores: %{x:,}<extra></extra>",
    )
)
meli_figure_layout(
    fig_class,
    title="Colaboradores ativos por classificação (último mês do período)",
    x_title="Colaboradores",
    palette=pal,
    hovermode="y unified",
)
st.plotly_chart(fig_class, use_container_width=True, config=plotly_streamlit_config())

by_site = (
    snap.groupby("site", as_index=False)["active_collaborators"]
    .sum()
    .sort_values("active_collaborators", ascending=True)
)

insight_block(
    eyebrow="Leitura do visual",
    pergunta="Quais sites concentram mais a base?",
    texto=(
        "Comparativo por **site** no último mês do período. Tom **cinza** para leitura estrutural; "
        "tooltip interativo ao passar o mouse."
    ),
    section_id="overview_site",
    llm_context={
        "pagina": "overview",
        "grafico": "colaboradores_por_site",
        "ultimo_mes_periodo": str(latest),
        "filtros": {"site": site, "division": division},
        "por_site": by_site.to_dict(orient="records"),
    },
)

fig_site = go.Figure(
    go.Bar(
        x=by_site["active_collaborators"],
        y=by_site["site"],
        orientation="h",
        marker=dict(color=pal["gray"], line=dict(color=pal["gray_dark"], width=1)),
        name="Ativos",
        hovertemplate="<b>%{y}</b><br>Colaboradores: %{x:,}<extra></extra>",
    )
)
meli_figure_layout(
    fig_site,
    title="Colaboradores ativos por site (último mês do período)",
    x_title="Colaboradores",
    palette=pal,
    hovermode="y unified",
)
st.plotly_chart(fig_site, use_container_width=True, config=plotly_streamlit_config())
