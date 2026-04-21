# Testes do case

## Sem banco (sempre rodam)

```bash
pytest tests/ -m "not integration" -q
```

ou simplesmente:

```bash
pytest tests/test_raw_csv.py -q
```

## Com Postgres (warehouse já carregado)

Defina `DATABASE_URL` apontando para o mesmo banco do dbt (ex.: porta **5433** no host com Docker):

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://airflow:airflow@localhost:5433/airflow"
pytest tests/ -m integration -q
```

Os testes de integração falham se `analytics.agg_ddi_month` ainda não existir — rode o `warehouse-init` ou o DAG `ddi_pipeline` antes.
