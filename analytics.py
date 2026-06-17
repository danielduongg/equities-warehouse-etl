"""Query the warehouse and render analytics artifacts (tables + charts)."""
from __future__ import annotations
import os, pathlib
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from warehouse import DB_PATH

def run():
    os.makedirs("reports", exist_ok=True)
    con = duckdb.connect(DB_PATH, read_only=True)
    top = con.execute(pathlib.Path("sql/top_movers.sql").read_text()).df()
    corr = con.execute(pathlib.Path("sql/return_correlation.sql").read_text()).df()

    px = con.execute("""SELECT trade_date, close, sma_20, sma_50
        FROM marts.fct_daily_metrics WHERE ticker='AAPL' ORDER BY trade_date""").df()
    plt.figure(figsize=(9, 4.5))
    for c, lbl in [("close", "Close"), ("sma_20", "SMA-20"), ("sma_50", "SMA-50")]:
        plt.plot(px.trade_date, px[c], lw=1, label=lbl)
    plt.title("AAPL close with moving averages"); plt.legend(); plt.tight_layout()
    plt.savefig("reports/aapl_price_sma.png", dpi=120); plt.close()

    print("=== Top movers ===\n", top.to_string(index=False))
    print("\n=== Most correlated pairs ===\n", corr.head(5).to_string(index=False))
    top.to_csv("reports/top_movers.csv", index=False)
    con.close()

if __name__ == "__main__":
    run()
