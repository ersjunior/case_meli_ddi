# Respostas ao desafio técnico — Analista de Dados (DDI)

Documento de apoio ao PDF de entrega: aqui estão as respostas **estruturadas** ao enunciado, com definições, SQL e ligação ao que foi implementado neste repositório (`transformation/dbt_projects`, `serving/streamlit`, `docker/`, `data/raw`).

---

## 1. Produto, métricas e governança

### 1.1.1 Quais decisões o dashboard atual não suporta bem / quais perguntas críticas ficam sem resposta?

Com base nos exemplos típicos de dashboard descritivos (cortes por site e por classificação) e na ausência de um **produto de dados** explícito, costuma faltar suporte a decisões como:

1. **Cobertura do indicador** — “Quantos colaboradores ativos **não** têm fotografia DDI no mês?” Sem `coverage_rate` por unidade de negócio, não dá para priorizar correção de integração vs. adoção real.
2. **Elegibilidade e exclusões auditáveis** — “Quantos Representantes de Shipping saíram do universo e em qual impacto no denominador?” Sem regra versionada e testes, a comparabilidade MoM quebra.
3. **Usuários potenciais (regra temporal)** — o enunciado exige **3 meses consecutivos** com `is_data_user = True`. Um painel que só mostra o flag no mês corrente **não** responde “quem entrou no funil de maturidade este mês?” nem “quem está a um mês de virar potencial?”.
4. **Migração entre classificações** — decisões de L&D / chapter de dados exigem **transition_rate** (fluxo Beginner → Intermediate, etc.), não só a fatia atual.
5. **Gap vs. referência** — sem **benchmark** (ex.: mediana por site/divisão), líderes não sabem se “80% data users” é bom ou ruim **para aquele contexto**.
6. **Drill hierárquico com mesma definição** — “Por que caiu em MLB?” exige decomposição **divisão → departamento → classificação** com a **mesma** definição de métrica em cada nível (hoje muitos relatórios misturam “headcount” com “DDI snapshot”).

**No repositório:** o Streamlit (`serving/streamlit/pages/`) cobre visão agregada, evolução e diagnóstico; a tabela `analytics.agg_ddi_month` materializa métricas alinhadas ao item 1.2.

---

### 1.2 Mini “metrics spec”

#### 1.2.1 Universo e elegibilidade

| Elemento | Definição adotada | Justificativa |
|----------|-------------------|---------------|
| **Universo base** | Colaboradores **ativos** no mês \(M\) | Alinhado ao PDF: “apenas colaboradores ativos”. |
| **Ativo no mês** | `start_date` ≤ último dia de \(M\) **e** (`end_date` IS NULL **ou** `end_date` ≥ primeiro dia de \(M\)) | `end_date` nulo = ainda na empresa; saída no meio do mês continua ativo no mês civil (ajustável para “ativo se >15 dias” se o RH assim definir). |
| **Exclusão** | `division = 'Shipping'` **e** `function = 'Representative'` | Texto literal do case. |
| **Org no mês** | Último registro de `tb_people_history` com `tim_day` ≤ último dia de \(M\) (por `username`) | Snapshot mensal simplificado (SCD tipo 2 “por mês”): congela site/divisão/departamento para o mês. |
| **Sem registro em `tb_ddi` no mês** | Colaborador ativo e elegível **sem** linha `username + date_month` em `tb_ddi` | Tratado como **“Sem registro DDI”** na silver (`fct_user_month`), **entra no denominador** de `coverage_rate` e nas contagens por classificação nesse bucket. |

Ambiguidades adicionais tratadas no repositório:

- **Duplicidade em `tb_ddi`** (mesmo `username` + `date_month`): deduplicação na `stg_ddi` com `DISTINCT ON` determinístico + testes (`dbt` + `tests/`).
- **Usuários só em DDI**: mantidos no DDI; o universo principal do mês vem de people → join à esquerda.

---

#### 1.2.2 Métricas (dicionário)

Todas calculadas no grão **Gold**: `date_month`, `site`, `division`, `department`, `user_classification` (modelo `agg_ddi_month`). Na **Silver** (`fct_user_month`): um registro por `username` + `date_month`.

| Métrica | Definição | Fórmula (conceitual) |
|---------|------------|----------------------|
| **active_collaborators** | Elegíveis ativos no recorte | `COUNT(DISTINCT username)` no grão após filtros. |
| **potential_users** | Usuários com **≥ 3 meses consecutivos** com `is_data_user = TRUE` no mês corrente (flag a partir do 3º mês da sequência) | `COUNT(DISTINCT CASE WHEN is_potential_user THEN username END)`. |
| **data_driven_users** | Uso declarado de dados no mês | `COUNT(DISTINCT CASE WHEN is_data_user THEN username END)` (complementar a classificações DDI no storytelling). |
| **share_per_ddi_classification** | Participação dos **potenciais** entre classificações DDI no mesmo mês/site/div/dept | `100 * potential_users / NULLIF(SUM(potential_users) OVER (PARTITION BY date_month, site, division, department), 0)`. |
| **coverage_rate** | Abrangência do DDI no universo (nível dept-mês) | `100 * (colaboradores com linha DDI no mês) / (ativos totais no dept-mês)` — implementado via CTE `dept_month` + join. |
| **transition_rate** | Dinâmica MoM da contagem de potenciais naquele grão | Variação percentual vs. mês anterior na mesma combinação `(site, division, department, user_classification)` (proxy para migração; fluxo matricial completo exigiria estado MoM por usuário). |
| **gap_to_target** | Sem meta oficial: **benchmark interno** | `potential_users - median_dept_potential` onde a mediana é das somas de potenciais por **department** dentro de `(date_month, site, division)`. |

---

#### 1.2.3 SQL — 3 meses consecutivos com `is_data_user = TRUE` (usuários potenciais)

Ideia: segmentar sequências de meses **consecutivos** em que `is_data_user` é verdadeiro usando duas `ROW_NUMBER()`; o tamanho da janela é o `COUNT(*) OVER (PARTITION BY username, grp)`.

```sql
-- Lógica equivalente à do modelo int_user_streak (após dedup em stg_ddi)
WITH base AS (
    SELECT
        username,
        date_month,
        is_data_user,
        ROW_NUMBER() OVER (PARTITION BY username ORDER BY date_month)
      - ROW_NUMBER() OVER (PARTITION BY username, is_data_user ORDER BY date_month) AS grp
    FROM stg_ddi
),
streaks AS (
    SELECT
        username,
        date_month,
        COUNT(*) OVER (PARTITION BY username, grp) AS streak
    FROM base
    WHERE is_data_user IS TRUE
)
SELECT
    username,
    date_month,
    CASE WHEN streak >= 3 THEN TRUE ELSE FALSE END AS is_potential_user
FROM streaks;
```

**Regra de negócio:** potencial a partir do **terceiro** mês consecutivo como `is_data_user = TRUE` (o próprio mês já conta se `streak >= 3`).

---

## 2. Modelagem

### 2.1 Design alvo para BI

**Camadas (Medallion simplificado)**

| Camada | Conteúdo | Materialização no repo |
|--------|-----------|-------------------------|
| **Raw** | `tb_people_history`, `tb_ddi` no Postgres `public` | Airflow DAG + `warehouse-init` |
| **Staging** | Tipagem, dedup DDI, limpeza | `stg_*` (views) |
| **Intermediate** | Elegibilidade mensal, streak, enriquecimento | `int_*` (views) |
| **Marts** | Consumo BI | `fct_user_month` (tabela), `agg_ddi_month` (tabela) |

#### 2.1.1 Granularidades

- **Silver — `fct_user_month`**: 1 linha por **`username` + `date_month`** com `site`, `division`, `department` congelados, `user_classification` (ou `Sem registro DDI`), flags `is_data_user`, `is_potential_user`, `has_ddi_row`.
- **Gold — `agg_ddi_month`**: agregado por **`date_month`, `site`, `division`, `department`, `user_classification`** com as métricas da tabela acima.

**Mudança de divisão/departamento:** para cada `(username, date_month)` do calendário DDI, escolhe-se a linha de `tb_people_history` com **`tim_day` máximo** entre as que satisfazem emprego no mês e a exclusão Shipping/Representative (`int_people_monthly`).

---

### 2.2 Qualidade e performance

#### 2.2.1 Validações mensais (duplicidade + classificação)

1. **Unicidade** `username + date_month` em `fct_user_month` e em `stg_ddi` pós-dedup (testes dbt + pytest no repo).
2. **`not_null`** em chaves e dimensões do mart.
3. **`accepted_values`** (recomendado evoluir no dbt) para `user_classification` ∈ {Basic, Beginner, …, `Sem registro DDI`}.
4. **Sanidade de cobertura**: `coverage_rate` entre 0 e 100 por dept-mês.
5. **Reconciliação**: soma de `active_collaborators` por classificação no dept = total de distintos no `fct` para o mesmo dept-mês (teste de consistência interna).

#### 2.2.2 Eficiência e custo

- **Particionamento** (futuro): `fct_user_month` / `agg_ddi_month` por `date_month` se volume explodir.
- **Índices** em `(date_month, site)` e `(username, date_month)` no Postgres para BI.
- **Apenas colunas usadas** no mart; evitar `SELECT *` em consumidores.
- **dbt incremental** (evolução) no gold se a tabela crescer muito.
- **Cache** curto no Streamlit (`run_query`).

---

## 3. SQL

### 3.1.1 Tabela mensal agregada (campos pedidos)

A materialização **`analytics.agg_ddi_month`** corresponde ao produto desta query lógica:

```sql
SELECT
    date_month,
    site,
    division,
    department,
    user_classification
    -- + métricas (item 3.1.2) na mesma tabela no projeto
FROM analytics.agg_ddi_month;
```

Definição completa (lógica dbt) está em `transformation/dbt_projects/models/marts/agg_ddi_month.sql`.

---

### 3.1.2 Métricas na agregação mensal

Na mesma relação `agg_ddi_month`:

```sql
SELECT
    date_month,
    site,
    division,
    department,
    user_classification,
    active_collaborators,
    potential_users,
    data_driven_users,
    share_per_ddi_classification,
    coverage_rate,
    transition_rate,
    gap_to_target
FROM analytics.agg_ddi_month;
```

---

### 3.2 Conceituais

#### 3.2.1 `COUNT(*)`, `COUNT(coluna)`, `COUNT(DISTINCT coluna)` com `tb_ddi`

- **`COUNT(*)`**: conta **linhas** da tabela após `FROM`/`WHERE`. Inclui duplicatas e linhas com qualquer coluna NULL.
- **`COUNT(coluna)`**: conta linhas em que **`coluna` IS NOT NULL**. Nulos são ignorados.
- **`COUNT(DISTINCT coluna)`**: conta **valores distintos não nulos** de `coluna`.

**Exemplo** (trecho hipotético com duplicidade no mesmo mês):

| username | date_month | user_classification | is_data_user |
|----------|------------|---------------------|--------------|
| u1 | 2025-03-01 | Beginner | TRUE |
| u1 | 2025-03-01 | No Use | FALSE |

- `COUNT(*) = 2`
- `COUNT(is_data_user) = 2` (boolean não nulo)
- `COUNT(DISTINCT username) = 1`
- Se `user_classification` tiver NULL em outra linha, `COUNT(user_classification)` ignora essa linha.

---

#### 3.2.2 Duplicidade `username + date_month`

**Efeitos**

- **`COUNT(*)`** infla o numerador/denominador se usado como “usuários”.
- **`COUNT(DISTINCT username)`** corrige contagens de **usuários**, mas **não** corrige **shares por classificação** se as duplicatas tiverem classificações diferentes (a linha “dupla” distorce a distribuição).

**Detecção**

```sql
SELECT username, date_month, COUNT(*) AS n
FROM tb_ddi
GROUP BY 1, 2
HAVING COUNT(*) > 1;
```

**Correção**

1. **Fonte** (preferencial): corrigir pipeline que grava `tb_ddi`.
2. **Curadoria**: regra determinística de prioridade (ex.: `ORDER BY is_data_user DESC, updated_at DESC`) com `DISTINCT ON` — como em `stg_ddi`.

---

#### 3.2.3 `WHERE` vs `ON` no `LEFT JOIN`

- **`WHERE` (lado direito nulo)**: transforma o `LEFT JOIN` em comportamento **tipo INNER** para linhas filtradas: linhas sem match **perdem-se** se a condição referir colunas da tabela direita e excluírem NULL.
- **`ON`**: preserva linhas da esquerda; condições de match ficam no **join**; filtros apenas na direita devem ir no `ON` ou usar `OR coluna_direita IS NULL` com cuidado.

**Exemplo**

```sql
-- Quer todos os users da people, mesmo sem DDI:
SELECT p.username, d.user_classification
FROM people p
LEFT JOIN tb_ddi d ON p.username = d.username AND d.date_month = DATE '2025-06-01'
WHERE d.user_classification = 'Beginner';  -- elimina quem não tem DDI (NULL)

-- Correto para filtrar classificação mantendo ausentes:
SELECT p.username, d.user_classification
FROM people p
LEFT JOIN tb_ddi d
  ON p.username = d.username
 AND d.date_month = DATE '2025-06-01'
 AND d.user_classification = 'Beginner';
```

---

#### 3.2.4 Registro mais recente “Beginner” por usuário

```sql
SELECT DISTINCT ON (username)
    username,
    date_month,
    user_classification,
    is_data_user
FROM tb_ddi
WHERE user_classification = 'Beginner'
ORDER BY username, date_month DESC;
```

(`DISTINCT ON` exige `ORDER BY` alinhado ao critério “mais recente”.)

---

## 4. Visualização e storytelling

### 4.1 Mockup / wireframe (como o repositório responde)

**Onde estamos?** — Página **Overview** (`1_Overview.py`): filtros site/divisão, KPIs de colaboradores ativos / data users / potenciais, barras por classificação e por site.

**O que mudou?** — Página **Evolution** (`2_Evolution.py`): série temporal, MoM e linha de tendência.

**Por que mudou?** — Página **Diagnosis** (`3_Diagnosis.py`): corte por divisão e departamento com `data_driven_users` por classificação.

**Power BI** — Página **Embedded** (`4_Embedded.py`): iframe com URL do `.env` para o relatório oficial / mock corporativo.

Para o **PDF de entrega**, recomenda-se anexar **prints** dessas páginas ou um wireframe estático (Figma) com a mesma hierarquia: **KPI → drill site → divisão → departamento → drivers**.

---

## Referência rápida — entregáveis do PDF

| Exigência do enunciado | Onde está no projeto |
|------------------------|----------------------|
| Métricas + modelagem | `transformation/dbt_projects/models/marts/agg_ddi_month.sql`, `fct_user_month.sql` |
| Regra 3 meses | `models/intermediate/int_user_streak.sql` |
| Universo ativo + sem DDI | `int_people_monthly.sql` + `fct_user_month.sql` |
| Exclusão Shipping Rep | `int_people_monthly.sql` |
| Qualidade (dbt) | `models/**/schema.yml`, `tests/assert_*.sql` |
| Orquestração | `orchestration/airflow/dags/ddi_pipeline.py`, `docker/scripts/bootstrap_warehouse.sh` |
| Dashboard | `serving/streamlit/pages/` |
| Dados sintéticos | `data/raw/*.csv` |

---

*Texto elaborado para apoio à montagem do PDF final; ajuste tom e marcações conforme o template corporativo do case.*
