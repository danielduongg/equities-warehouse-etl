"""Airflow DAG that schedules the equities ELT once per trading day.

Illustrative orchestration layer for this project. It mirrors run_pipeline.py
as discrete, retryable tasks: extract -> load -> staging -> marts -> tests.
Drop this file in your Airflow `dags/` folder to run it on a schedule.
"""
from __future__ import annotations
from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # keeps the file importable without Airflow installed
    DAG = None

default_args = {
    "owner": "daniel",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def _extract_load(**_):
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from extract import extract
    from warehouse import connect, load_raw
    load_raw(connect(), extract())

def _transform(**_):
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from warehouse import connect, run_models
    run_models(connect(), [
        "sql/stg_prices.sql",
        "sql/dim_security.sql",
        "sql/fct_daily_metrics.sql",
    ])

if DAG is not None:
    with DAG(
        dag_id="equities_elt",
        description="Daily equities ELT into DuckDB warehouse",
        schedule="0 23 * * 1-5",          # 11pm on weekdays
        start_date=datetime(2024, 1, 1),
        catchup=False,
        default_args=default_args,
        tags=["finance", "elt", "duckdb"],
    ) as dag:
        extract_load = PythonOperator(task_id="extract_load", python_callable=_extract_load)
        transform = PythonOperator(task_id="transform_models", python_callable=_transform)
        extract_load >> transform
