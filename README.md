# Case Mercado Livre — Data Driven Index (DDI)

Pipeline de referência: **Postgres** (raw) → **Airflow** (ingest) → **dbt** (staging / intermediate / marts) → **Streamlit** (consumo).

## Pré-requisitos

- Docker e Docker Compose v2
- Arquivo **`.env`** na raiz (use [`.env.example`](.env.example) como modelo)

## Subir tudo (Postgres + Airflow + Streamlit)

Na raiz do repositório:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

O Postgres do compose publica no host a porta **`5433`** por padrão (`POSTGRES_PUBLISH_PORT` no `.env`), para não conflitar com um Postgres local na **5432**. Airflow, dbt e Streamlit falam com o serviço `postgres` na **5432 interna** da rede Docker — nada a mudar aí. Para acessar do Windows (DBeaver, psql), use `localhost:5433`.

### Carga automática do warehouse (dbt)

O serviço **`warehouse-init`** roda **uma vez** após o Postgres ficar saudável: aplica o DDL, `TRUNCATE`, `\copy` dos CSVs em `data/raw/` e executa `dbt run` + `dbt test`. O **Streamlit só inicia depois** que isso termina com sucesso, então `agg_ddi_month` já existe ao abrir o app.

Novos DAGs no Airflow ficam **pausados por padrão** (`DAGS_ARE_PAUSED_AT_CREATION`). Para recarregar dados manualmente, despause e rode o DAG `ddi_pipeline`, ou execute só o bootstrap:

```bash
docker compose -f docker/docker-compose.yml run --rm warehouse-init
```

### Streamlit no Windows (fora do Docker)

O app usa por padrão `localhost:5433` no `DATABASE_URL` (mesmo Postgres do compose). Se ainda conectar a outro Postgres (ex.: porta 5432 local), a tabela `agg_ddi_month` não existirá. Defina no `.env`:

`DATABASE_URL=postgresql+psycopg2://airflow:airflow@localhost:5433/airflow`

- **Airflow UI**: [http://localhost:8080](http://localhost:8080) — usuário `admin` / senha `admin` (definidos no `docker-compose`, ajuste em produção).
- **Streamlit**: [http://localhost:8501](http://localhost:8501) — sobe automaticamente com o Compose; instala dependências a partir da raiz [`requirements.txt`](requirements.txt) na imagem do app.

> O Streamlit assume `search_path=analytics,public` e lê as tabelas materializadas pelo dbt no schema **`analytics`**. Até rodar o DAG, as consultas podem falhar ou retornar vazio.

### Power BI na página **Embedded**

No `.env`, defina `POWERBI_EMBED_URL` com a URL de incorporação do relatório (HTTPS). Opcional: `POWERBI_EMBED_HEIGHT` (px, default 720), `POWERBI_EMBED_WIDTH` (px, ex. `1180`, ou percentual ex. `100%`). O Streamlit já carrega o `.env` via Compose; reinicie o container após alterar.

## Primeira carga de dados

1. Acesse o Airflow e **ative o DAG** `ddi_pipeline` (toggle ON).
2. Dispare **Trigger DAG** (ou aguarde o agendamento mensal).
3. O fluxo: cria tabelas raw + schema `analytics` → `TRUNCATE` → `\copy` dos CSVs de [`data/raw/`](data/raw/) → `dbt run` → `dbt test`.

## Desenvolvimento local (sem Docker)

**Windows (PowerShell)** — com Postgres do Docker já rodando no host, use a porta publicada (padrão **5433**; veja `POSTGRES_PUBLISH_PORT` no `.env`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd serving/streamlit
$env:DATABASE_URL = "postgresql+psycopg2://airflow:airflow@localhost:5433/airflow"
$env:PG_SEARCH_PATH = "analytics,public"
streamlit run app.py
```

**Linux/macOS** (equivalente):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd serving/streamlit
export DATABASE_URL=postgresql+psycopg2://airflow:airflow@localhost:5433/airflow
export PG_SEARCH_PATH=analytics,public
streamlit run app.py
```

dbt, na pasta do projeto (contra o mesmo Postgres do compose no host):

```bash
cd transformation/dbt_projects
export DBT_POSTGRES_HOST=localhost
export DBT_POSTGRES_PORT=5433   # PowerShell: $env:DBT_POSTGRES_PORT = "5433"
dbt run --profiles-dir .
dbt test --profiles-dir .
```

## Documentação do case (respostas ao PDF)

O arquivo **[`docs/Respostas.md`](docs/Respostas.md)** consolida as respostas ao desafio (produto, métricas, modelagem, SQL conceitual, visualização) com referência ao código.

## Testes

```bash
pip install -r requirements.txt
pytest tests/test_raw_csv.py -q
```

Com Postgres já carregado (`warehouse-init` ou DAG) e `DATABASE_URL` definido:

```bash
pytest tests/ -m integration -q
```

Ver [`tests/README.md`](tests/README.md).

## Estrutura principal

| Pasta | Uso |
|--------|-----|
| `data/raw/` | CSV imutáveis (fonte do `\copy`) |
| `docker/` | `docker-compose.yml`, Dockerfiles, bootstrap SQL/shell — ver [`docker/readme.md`](docker/readme.md) |
| `orchestration/` | Airflow — ver [`orchestration/readme.md`](orchestration/readme.md) |
| `transformation/dbt_projects/` | Projeto dbt — índice em [`transformation/readme.md`](transformation/readme.md) |
| `serving/` | Streamlit + artefatos Power BI — ver [`serving/readme.md`](serving/readme.md) |
| `docs/` | `Respostas.md` + índices curtos |
| `tests/` | Pytest (CSV + integração warehouse) |

## Entrega do case (PDF)

O desafio pede documentação em PDF; 
Caminho do PDF: [`case/case_meli_ddi.pdf`](case_meli_ddi.pdf).
