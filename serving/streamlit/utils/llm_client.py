"""Cliente chat compatível com OpenAI (nuvem ou local)."""

from __future__ import annotations

import json
from typing import Any

from utils.llm_config import get_llm_runtime, llm_provider


def complete_narrative(
    *,
    eyebrow: str,
    pergunta: str,
    texto_referencia: str,
    dados: dict[str, Any],
) -> str:
    """
    Gera markdown em português a partir de dados agregados (sem PII).
    Levanta ``RuntimeError`` se a configuração estiver incompleta.
    """
    rt = get_llm_runtime()
    if llm_provider() == "openai" and not rt.api_key:
        raise RuntimeError("OPENAI_API_KEY não definido no ambiente.")

    system = (
        "Você é analista de dados sênior em um dashboard de maturidade analítica (DDI). "
        "Escreva em português do Brasil, tom profissional e conciso. "
        "Use markdown leve (**negrito**, listas curtas). "
        "Baseie-se exclusivamente no JSON `dados` e na pergunta de negócio. "
        "Não invente métricas, percentuais ou categorias que não apareçam nos dados. "
        "Se os dados forem insuficientes, diga isso em uma frase."
    )

    user = json.dumps(
        {
            "secao": eyebrow,
            "pergunta_negocio": pergunta,
            "texto_referencia_fixo": texto_referencia,
            "dados": dados,
        },
        ensure_ascii=False,
        default=str,
    )

    user_msg = (
        "Redija a análise narrativa desta seção (2 a 5 parágrafos curtos ou equivalente em bullets). "
        "Responda à pergunta de negócio usando apenas os números e categorias em `dados`. "
        "O campo `texto_referencia_fixo` é o texto que o produto mostra quando a IA está desligada — "
        "você pode reescrevê-lo com mais riqueza, sem contradizer fatos.\n\n"
        f"{user}"
    )

    from openai import OpenAI

    client = OpenAI(
        api_key=rt.api_key,
        base_url=rt.base_url,
        timeout=rt.timeout_seconds,
        max_retries=1,
    )
    resp = client.chat.completions.create(
        model=rt.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.35,
        max_tokens=900,
    )
    choice = resp.choices[0].message
    content = (choice.content or "").strip()
    if not content:
        raise RuntimeError("Resposta vazia do modelo.")
    return content
