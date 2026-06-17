import dq

def test_all_checks_pass_on_clean_data(warehouse):
    results = dq.run_checks(warehouse)
    assert all(passed for _, passed, _ in results)

def test_null_close_is_detected(warehouse):
    warehouse.execute("INSERT INTO marts.fct_daily_metrics (ticker, trade_date, close) "
                      "VALUES ('ZZZ', DATE '2000-01-01', NULL)")
    results = dict((n, p) for n, p, _ in dq.run_checks(warehouse))
    assert results["no_null_close"] is False
