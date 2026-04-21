"""Blocos de texto para storytelling (estático ou via LLM quando habilitado no .env)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import streamlit as st


def _resolve_llm_text(
    *,
    section_id: str,
    eyebrow: str,
    pergunta: str,
    texto: str,
    llm_context: dict[str, Any],
) -> str:
    from utils.llm_client import complete_narrative
    from utils.llm_config import get_llm_runtime, llm_narrative_enabled

    if not llm_narrative_enabled():
        return texto

    rt = get_llm_runtime()
    blob = json.dumps(
        {"section_id": section_id, "ctx": llm_context, "model": rt.model},
        sort_keys=True,
        default=str,
    )
    h = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:56]
    key = f"llm_narr_{section_id}_{h}"
    if key in st.session_state:
        return st.session_state[key]

    try:
        out = complete_narrative(
            eyebrow=eyebrow,
            pergunta=pergunta,
            texto_referencia=texto,
            dados=llm_context,
        )
        st.session_state[key] = out
        return out
    except Exception as exc:
        return texto + f"\n\n*(Não foi possível usar o modelo: {exc})*"


def insight_block(
    *,
    eyebrow: str,
    pergunta: str,
    texto: str,
    accent: str | None = None,
    llm_context: dict[str, Any] | None = None,
    section_id: str | None = None,
) -> None:
    """
    Bloco explicativo. Com ``LLM_NARRATIVE_ENABLED=true`` e ``llm_context`` + ``section_id`` definidos,
    o corpo do texto é gerado pelo modelo (OpenAI ou local); caso contrário, usa ``texto`` como hoje.
    """
    _ = accent
    corpo = texto
    if llm_context is not None and section_id:
        corpo = _resolve_llm_text(
            section_id=section_id,
            eyebrow=eyebrow,
            pergunta=pergunta,
            texto=texto,
            llm_context=llm_context,
        )

    with st.container(border=True):
        st.caption(eyebrow.upper())
        st.markdown(f"**{pergunta}**")
        st.markdown(corpo)
        if llm_context is not None and section_id:
            from utils.llm_config import llm_narrative_enabled

            if llm_narrative_enabled():
                st.caption(
                    "_Narrativa assistida por IA a partir de dados agregados; gráficos e tabelas prevalecem em caso de divergência._"
                )


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)
