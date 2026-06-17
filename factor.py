"""Single-factor (market) model: estimate each security's beta by regressing
its daily returns on the equal-weight market return. Writes a marts table and
a bar chart — the kind of analytical mart a quant data team would expose."""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from warehouse import DB_PATH

def compute_betas(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = con.execute("""
        SELECT ticker, trade_date, daily_return
        FROM marts.fct_daily_metrics WHERE daily_return IS NOT NULL
    """).df()
    wide = df.pivot(index="trade_date", columns="ticker", values="daily_return").dropna()
    market = wide.mean(axis=1)                     # equal-weight market factor
    var_m = market.var()
    rows = []
    for t in wide.columns:
        beta = wide[t].cov(market) / var_m
        alpha = wide[t].mean() - beta * market.mean()
        rows.append(dict(ticker=t, beta=round(float(beta), 3),
                         alpha_daily=round(float(alpha), 5),
                         ann_alpha=round(float(alpha) * 252, 4)))
    betas = pd.DataFrame(rows).sort_values("beta", ascending=False)
    con.execute("CREATE SCHEMA IF NOT EXISTS marts;")
    con.register("betas_df", betas)
    con.execute("CREATE OR REPLACE TABLE marts.fct_factor_exposure AS SELECT * FROM betas_df")
    con.unregister("betas_df")
    return betas

def plot(betas: pd.DataFrame, path="reports/betas.png"):
    os.makedirs("reports", exist_ok=True)
    plt.figure(figsize=(7, 4))
    plt.bar(betas.ticker, betas.beta, color="#2b6cb0")
    plt.axhline(1.0, color="k", ls="--", alpha=.5, label="market beta = 1")
    plt.ylabel("Market beta"); plt.title("Single-factor market beta by security")
    plt.legend(); plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()

if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    b = compute_betas(con); plot(b); print(b.to_string(index=False))
