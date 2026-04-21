import streamlit as st

st.set_page_config(
    page_title="DDI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.narrative import page_header
from utils.theme import apply_meli_theme

apply_meli_theme()

page_header(
    "Data Driven Index",
    "Painéis com visual limpo: cinza para base, azul para data-driven, verde/vermelho nos deltas. "
    "Filtre o período (De / Até) nas páginas analíticas. Para o tema do app e dos gráficos Plotly, use o menu "
    "⋮ → **Configurações** → **Tema** (Claro ou Escuro).",
)

st.markdown(
    """
Use o menu lateral para navegar:

| Página | Pergunta de negócio |
|--------|---------------------|
| **Overview** | Onde estamos? Base, adoção data-driven e potencial. |
| **Evolution** | O que mudou? Tendência e MoM. |
| **Diagnosis** | Por que / onde aprofundar? Recorte por division e departamento. |
| **Embedded** | Power BI (URL configurável). |
| **Resoluções** | Respostas escritas ao desafio (`docs/Respostas.md`). |
    """
)

st.info(
    "Dica: cada gráfico nas páginas analíticas vem com um bloco de contexto "
    "(pergunta + interpretação) para alinhar leitura executiva ao case.",
    icon="ℹ️",
)
