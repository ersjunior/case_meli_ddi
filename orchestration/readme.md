# Orquestração — Airflow

Pasta **`airflow/`**: DAGs, plugins e logs do Airflow usados pelo `docker-compose` em [`../docker/docker-compose.yml`](../docker/docker-compose.yml).

| Caminho | Uso |
|---------|-----|
| `airflow/dags/` | DAG `ddi_pipeline` — bootstrap Postgres (DDL + `\copy` dos CSVs) e execução **dbt** (`run` + `test`) |
| `airflow/dags/data/` | Volume montado a partir de [`../data/raw/`](../data/raw/); os CSVs **não** ficam duplicados dentro de `dags/` no Git — ver [`dags/data/README.md`](airflow/dags/data/README.md) |
| `airflow/plugins/` | Operadores/helpers compartilhados (ex.: `custom_operators.py`) |
| `airflow/logs/` | Logs de tarefas (diretório ignorado no Git, exceto `.gitkeep` se existir) |

Fluxo de alto nível: **Postgres (raw)** → tarefas Bash/Python no DAG → **dbt** materializa `analytics.*` para consumo no Streamlit.
