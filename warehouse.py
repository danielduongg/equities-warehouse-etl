"""Tiny warehouse helper around DuckDB: connect, load raw, run SQL models."""
from __future__ import annotations
import pathlib
import os
import duckdb
import pandas as pd

DB_PATH = os.environ.get("EQUITIES_DB", "data/warehouse.duckdb")

def connect(db_path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(db_path)

def load_raw(con, df: pd.DataFrame) -> None:
    """Idempotent load of the raw landing table."""
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    con.register("incoming", df)
    con.execute("CREATE OR REPLACE TABLE raw.prices AS SELECT * FROM incoming;")
    con.unregister("incoming")

def run_sql_file(con, path: str) -> None:
    sql = pathlib.Path(path).read_text()
    con.execute(sql)

def run_models(con, model_paths: list[str]) -> None:
    for p in model_paths:
        run_sql_file(con, p)


def load_raw_incremental(con, df) -> None:
    """Append-only load: create raw.prices if needed, then insert only rows
    newer than what's already stored per ticker. Staging de-dupes by
    (ticker, date) keeping the latest ingest, so re-runs stay idempotent."""
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    exists = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema='raw' AND table_name='prices'").fetchone()[0]
    con.register("incoming", df)
    if not exists:
        con.execute("CREATE TABLE raw.prices AS SELECT * FROM incoming;")
    else:
        con.execute("""
            INSERT INTO raw.prices
            SELECT i.* FROM incoming i
            LEFT JOIN (SELECT ticker, max(date) md FROM raw.prices GROUP BY ticker) m
              ON i.ticker = m.ticker
            WHERE m.md IS NULL OR i.date > m.md;
        """)
    con.unregister("incoming")
