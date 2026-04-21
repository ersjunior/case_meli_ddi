# Docker — stack do case

Esta pasta concentra **orquestração em containers** do pipeline: Postgres, carga inicial do warehouse (`warehouse-init`), Airflow (scheduler + web) e Streamlit.

## O que há aqui

| Item | Função |
|------|--------|
| [`docker-compose.yml`](docker-compose.yml) | Serviços, portas, volumes e dependências entre containers |
| [`airflow/Dockerfile`](airflow/Dockerfile) | Imagem Airflow 2.8 + dependências Python/dbt usadas pelo scheduler e pelo job de bootstrap |
| [`airflow/requirements-airflow.txt`](airflow/requirements-airflow.txt) | Pins extras da imagem Airflow |
| [`streamlit/Dockerfile`](streamlit/Dockerfile) | Imagem do dashboard Streamlit |
| [`sql/bootstrap_ddl.sql`](sql/bootstrap_ddl.sql) | DDL inicial (schemas/tabelas raw) aplicado pelo bootstrap |
| [`scripts/bootstrap_warehouse.sh`](scripts/bootstrap_warehouse.sh) | `TRUNCATE`, `\copy` dos CSVs e `dbt run` / `dbt test` |

Volumes relevantes (definidos no compose): DAGs e plugins em `../orchestration/airflow/`, projeto dbt em `../transformation/dbt_projects`, CSVs somente leitura em `../data/raw`.

## Pré-requisitos

- Docker Engine e **Docker Compose v2**
- Arquivo **`.env`** na **raiz do repositório** (não nesta pasta), copiado de [`.env.example`](../.env.example)

## Subir a stack

Na raiz do repositório:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

- **Postgres** no host: porta **`5433`** por padrão (`POSTGRES_PUBLISH_PORT` no `.env`), mapeada para `5432` dentro da rede Docker.
- **Airflow UI**: `http://localhost:8080` (usuário/senha padrão conforme README raiz — altere em ambientes reais).
- **Streamlit**: `http://localhost:8501` (sobe após `warehouse-init` concluir com sucesso).

Para repetir só a carga do warehouse (DDL + CSV + dbt):

```bash
docker compose -f docker/docker-compose.yml run --rm warehouse-init
```

## Notas

- O `.gitattributes` força **EOL LF** nos scripts `.sh` bind-mounted, evitando falha no Linux do container quando o arquivo foi editado no Windows com CRLF.
- Conexões **de dentro** dos serviços usam host `postgres` e porta **5432**. Do **Windows/host** (DBeaver, Streamlit fora do Docker, pytest integração), use `localhost` e a porta publicada (ex.: **5433**).

Instruções completas de primeiro uso, DAG `ddi_pipeline` e desenvolvimento local: [README na raiz](../README.md).
