"""Configuração de narrativa por LLM (OpenAI ou servidor local compatível com a API OpenAI)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def llm_narrative_enabled() -> bool:
    """Se ``false``, o app mantém os textos estáticos atuais."""
    v = os.getenv("LLM_NARRATIVE_ENABLED", "false").strip().lower()
    return v in ("1", "true", "yes", "on")


def llm_provider() -> str:
    """
    ``openai`` — API OpenAI (ou compatível via ``OPENAI_BASE_URL``).
    ``local`` — SLM local (Ollama, LM Studio, vLLM, etc.) via ``LLM_LOCAL_BASE_URL``.
    """
    p = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    return p if p in ("openai", "local") else "openai"


@dataclass(frozen=True)
class LLMRuntime:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float


def get_llm_runtime() -> LLMRuntime:
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "90"))

    if llm_provider() == "local":
        base = os.getenv("LLM_LOCAL_BASE_URL", "http://127.0.0.1:11434/v1").strip().rstrip("/")
        key = os.getenv("LLM_LOCAL_API_KEY", "ollama").strip() or "ollama"
        model = os.getenv("LLM_LOCAL_MODEL", "llama3.2").strip() or "llama3.2"
        return LLMRuntime(base_url=base, api_key=key, model=model, timeout_seconds=timeout)

    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    return LLMRuntime(base_url=base, api_key=key, model=model, timeout_seconds=timeout)
