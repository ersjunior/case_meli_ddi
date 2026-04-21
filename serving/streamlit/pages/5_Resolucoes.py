"""
Consolida as respostas ao desafio (fonte: docs/Respostas.md no repositório ou /app/docs no Docker).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Resoluções", layout="wide", page_icon="✅")

from utils.narrative import insight_block, page_header
from utils.theme import apply_meli_theme

apply_meli_theme()


def _load_respostas_md() -> str:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "docs" / "Respostas.md",
        Path("/app/docs/Respostas.md"),
    ]
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return (
        "## Documento não encontrado\n\n"
        "Esperado `docs/Respostas.md` na raiz do repositório (desenvolvimento local) "
        "ou `/app/docs/Respostas.md` na imagem Docker. "
        "Inclua a cópia do arquivo no build ou monte o volume."
    )


page_header(
    "Resoluções do case",
    "Síntese em texto das perguntas do desafio — conteúdo espelhado de `docs/Respostas.md` (governança, modelagem, SQL e ligação ao que foi implementado).",
)

insight_block(
    eyebrow="Como usar esta página",
    pergunta="Qual a relação com os dashboards?",
    texto=(
        "As páginas **Overview**, **Evolution** e **Diagnosis** respondem visualmente a "
        "*onde estamos*, *o que mudou* e *por que / onde aprofundar*. Aqui fechamos o ciclo com as "
        "**respostas escritas** ao enunciado (métricas, decisões de modelagem, SQL de potencial, qualidade e próximos passos), "
        "para entrega e auditoria alinhadas ao PDF de negócio."
    ),
)

body = _load_respostas_md()
st.markdown(body)
