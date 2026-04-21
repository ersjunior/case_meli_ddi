"""
Power BI incorporado via iframe.
Configure POWERBI_EMBED_URL (e opcionalmente POWERBI_EMBED_HEIGHT, POWERBI_EMBED_WIDTH) no .env.
"""

import html
import os
import re

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Power BI", layout="wide", page_icon="📈")

from utils.narrative import insight_block, page_header
from utils.theme import apply_meli_theme

apply_meli_theme()

page_header(
    "Power BI (embedded)",
    "Relatório externo na mesma identidade visual do app; útil para comparar governança do case com um produto corporativo.",
)

insight_block(
    eyebrow="Quando usar",
    pergunta="Este iframe substitui os painéis nativos?",
    texto=(
        "Não — os gráficos Streamlit respondem ao pipeline do repositório (Postgres + dbt). "
        "Use o embed para **referência** ou demonstração do ambiente Power BI, mantendo as páginas "
        "*Overview / Evolution / Diagnosis* como fonte única para o case versionado em código."
    ),
)

st.caption(
    "Os filtros de período das outras páginas não se aplicam ao Power BI; use os filtros nativos do relatório embedado."
)


def _parse_embed_dimensions() -> tuple[str, int, int]:
    """
    Retorna (atributo HTML width do iframe, altura do iframe em px, largura do componente Streamlit em px).
    Largura do iframe: número inteiro → pixels; valor com % → CSS (ex.: 100%); default 100%.
    """
    height = int(os.getenv("POWERBI_EMBED_HEIGHT", "720"))
    raw = os.getenv("POWERBI_EMBED_WIDTH", "100%").strip() or "100%"

    if raw.endswith("%"):
        m = re.fullmatch(r"(\d{1,3})%", raw)
        if not m or not (1 <= int(m.group(1)) <= 100):
            raw = "100%"
        iframe_w = html.escape(raw, quote=True)
        # Área larga para o iframe em % ocupar a coluna do Streamlit sem ficar espremido.
        comp_w = 1920
        return iframe_w, height, comp_w

    try:
        px = int(raw)
    except ValueError:
        return "100%", height, 1400

    px = max(320, min(px, 3840))
    return str(px), height, px + 32


embed_url = os.getenv("POWERBI_EMBED_URL", "").strip()
iframe_width, height, component_width = _parse_embed_dimensions()

if not embed_url:
    st.info(
        "Nenhuma URL de incorporação configurada. Adicione ao `.env` na raiz do projeto:\n\n"
        "```\nPOWERBI_EMBED_URL=https://app.powerbi.com/reportEmbed?...\n```\n\n"
        "**Onde obter no Power BI Service:** abra o relatório → **Arquivo** → "
        "**Incorporar relatório** → **Site ou portal** (ou **Publicar na web**, se permitido pela governança) "
        "→ copie o link **seguro** de incorporação.\n\n"
        "Opcional: `POWERBI_EMBED_HEIGHT` (px), `POWERBI_EMBED_WIDTH` (px, ex.: `1180`, ou percentual ex.: `100%`).\n\n"
        "Para **Embed com token** (App owns data), a URL costuma vir da API de embed junto com o token no "
        "frontend; aqui usamos apenas o `src` do iframe — o fluxo completo de token fica fora deste app."
    )
    st.stop()

if not embed_url.lower().startswith("https://"):
    st.error("Por segurança, use apenas URLs **https://**.")
    st.stop()

safe_src = html.escape(embed_url, quote=True)

components.html(
    f"""
    <iframe
        title="Power BI"
        src="{safe_src}"
        width="{iframe_width}"
        height="{height}"
        frameborder="0"
        allowFullScreen="true"
        style="border:0; max-width:100%;"
        allow="fullscreen; autoplay; clipboard-write; encrypted-media; picture-in-picture"
    ></iframe>
    """,
    width=component_width,
    height=height + 24,
    scrolling=True,
)
