-- Mesmo contrato do DAG ddi_pipeline (raw + schema dbt).
CREATE TABLE IF NOT EXISTS tb_people_history (
    tim_day DATE,
    username TEXT,
    start_date DATE,
    end_date DATE,
    country TEXT,
    site TEXT,
    department TEXT,
    division TEXT,
    function TEXT
);

CREATE TABLE IF NOT EXISTS tb_ddi (
    username TEXT,
    date_month TEXT,
    user_classification TEXT,
    is_data_user BOOLEAN
);

CREATE SCHEMA IF NOT EXISTS analytics;
