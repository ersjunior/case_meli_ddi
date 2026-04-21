# Arquitetura

Resumo end-to-end: **Postgres (raw)** → **dbt** (staging / intermediate / marts no schema `analytics`) → **Streamlit** + opcional **Power BI** (iframe).

Detalhes, camadas e decisões de implementação: **[Respostas.md](Respostas.md)** (seção 2).
