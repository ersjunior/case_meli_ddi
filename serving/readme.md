# Camada de consumo — Streamlit e artefatos de BI

| Pasta / arquivo | Descrição |
|-----------------|-----------|
| `streamlit/` | App principal (`app.py`) e páginas em `pages/`; utilitários em `utils/`. Lê o schema **`analytics`** (materializado pelo dbt). |
| `streamlit/.streamlit/config.toml` | Configuração do Streamlit na imagem/local. |
| `powerbi/` | Artefatos do case (`.pbix`, layouts exportados, documento de apoio). A página **Embedded** do Streamlit usa `POWERBI_EMBED_URL` no `.env` para iframe. |

Desenvolvimento e variáveis (`DATABASE_URL`, `PG_SEARCH_PATH`, Power BI): [README na raiz](../README.md).
