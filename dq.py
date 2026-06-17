"""Lightweight data-quality checks (a mini Great-Expectations) run as a
pipeline gate AND in CI. Each check returns (name, passed, detail)."""
from __future__ import annotations
import logging
import duckdb
log = logging.getLogger("equities.dq")

CHECKS = [
    ("no_null_close",
     "SELECT count(*) FROM marts.fct_daily_metrics WHERE close IS NULL"),
    ("positive_close",
     "SELECT count(*) FROM marts.fct_daily_metrics WHERE close <= 0"),
    ("no_duplicate_grain",
     """SELECT count(*) FROM (SELECT ticker, trade_date, count(*) c
        FROM marts.fct_daily_metrics GROUP BY 1,2 HAVING c > 1)"""),
    ("returns_in_sane_range",
     "SELECT count(*) FROM marts.fct_daily_metrics WHERE abs(daily_return) > 0.5"),
    ("every_security_has_rows",
     """SELECT count(*) FROM marts.dim_security d
        LEFT JOIN (SELECT DISTINCT ticker FROM marts.fct_daily_metrics) f USING(ticker)
        WHERE f.ticker IS NULL"""),
]

def run_checks(con: duckdb.DuckDBPyConnection) -> list[tuple[str, bool, int]]:
    results = []
    for name, sql in CHECKS:
        bad = con.execute(sql).fetchone()[0]
        passed = bad == 0
        results.append((name, passed, int(bad)))
        log.info("DQ %-26s %s (offending=%d)", name, "PASS" if passed else "FAIL", bad)
    return results

def assert_quality(con) -> None:
    failed = [r for r in run_checks(con) if not r[1]]
    if failed:
        raise AssertionError(f"Data-quality checks failed: {failed}")
