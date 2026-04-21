# Dados no container

Não versionar CSV aqui: o `docker-compose` monta **`../../data/raw`** em `/opt/airflow/dags/data`.

O DAG e o `warehouse-init` leem `tb_*.csv` desse volume.
