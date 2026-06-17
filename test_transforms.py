def test_fact_table_populated(warehouse):
    n = warehouse.execute("SELECT count(*) FROM marts.fct_daily_metrics").fetchone()[0]
    assert n > 0

def test_dimension_has_all_securities(warehouse):
    n = warehouse.execute("SELECT count(*) FROM marts.dim_security").fetchone()[0]
    assert n == 6

def test_no_null_or_negative_close(warehouse):
    bad = warehouse.execute(
        "SELECT count(*) FROM marts.fct_daily_metrics WHERE close IS NULL OR close <= 0"
    ).fetchone()[0]
    assert bad == 0

def test_grain_is_unique(warehouse):
    dupes = warehouse.execute("""SELECT count(*) FROM (
        SELECT ticker, trade_date, count(*) c FROM marts.fct_daily_metrics
        GROUP BY 1,2 HAVING c > 1)""").fetchone()[0]
    assert dupes == 0
