# Dados

- **`raw/`** — CSV imutáveis do case (`tb_ddi.csv`, `tb_people_history.csv`). Fonte única para Docker (`warehouse-init`, volume do Airflow) e para testes em `tests/test_raw_csv.py`.

Staging e exports em arquivo não são usados neste repositório: a transformação vive no **Postgres** + **dbt** (`transformation/dbt_projects`).
