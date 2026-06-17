"""ELT orchestrator: extract -> load -> SQL models -> data-quality gate ->
factor model -> Parquet export. Supports incremental and full-refresh loads.

    python run_pipeline.py                 # incremental
    python run_pipeline.py --full-refresh  # rebuild raw from scratch
"""
from __future__ import annotations
import argparse, logging, os
from extract import extract, UNIVERSE
from warehouse import connect, load_raw, load_raw_incremental, run_models
import dq, factor

MODELS = ["sql/stg_prices.sql", "sql/dim_security.sql", "sql/fct_daily_metrics.sql"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="*", default=list(UNIVERSE))
    ap.add_argument("--days", type=int, default=600)
    ap.add_argument("--full-refresh", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("equities.pipeline")

    df = extract(tickers=args.tickers, n_days=args.days)
    con = connect()
    (load_raw if args.full_refresh else load_raw_incremental)(con, df)
    log.info("loaded raw.prices (%s)", "full" if args.full_refresh else "incremental")

    run_models(con, MODELS)
    dq.assert_quality(con)                      # gate: raises if quality fails
    betas = factor.compute_betas(con); factor.plot(betas)

    # Parquet export of marts (columnar, analytics-ready)
    os.makedirs("data/marts", exist_ok=True)
    for tbl in ("dim_security", "fct_daily_metrics", "fct_factor_exposure"):
        con.execute(f"COPY marts.{tbl} TO 'data/marts/{tbl}.parquet' (FORMAT PARQUET)")
    rows = con.execute("SELECT count(*) FROM marts.fct_daily_metrics").fetchone()[0]
    log.info("done: fct_daily_metrics=%d rows, betas for %d securities", rows, len(betas))
    con.close()

if __name__ == "__main__":
    main()
