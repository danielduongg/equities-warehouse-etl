import duckdb, pytest
from extract import extract
from warehouse import load_raw, run_models

MODELS = ["sql/stg_prices.sql", "sql/dim_security.sql", "sql/fct_daily_metrics.sql"]

@pytest.fixture
def warehouse(tmp_path):
    con = duckdb.connect(str(tmp_path / "wh.duckdb"))
    load_raw(con, extract(n_days=200, seed=1))
    run_models(con, MODELS)
    yield con
    con.close()
