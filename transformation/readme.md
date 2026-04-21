# Transformação — dbt

Projeto **dbt** em [`dbt_projects/`](dbt_projects/): camadas **staging** → **intermediate** → **marts** no schema Postgres **`analytics`**.

- Configuração: `dbt_projects/dbt_project.yml`, `dbt_projects/profiles.yml` (variáveis de ambiente `DBT_POSTGRES_*`, alinhadas ao Docker e ao README raiz).
- Modelos principais: `stg_*`, `int_*`, `fct_user_month`, `agg_ddi_month` (consumo agregado no Streamlit).
- Testes: `schema.yml` + testes SQL em `dbt_projects/tests/`.

Execução local e no container: ver [README na raiz](../README.md) e [`docs/Respostas.md`](../docs/Respostas.md) (modelagem e métricas).
