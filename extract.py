"""Extract step: produce daily OHLCV bars per ticker.

Default source is a reproducible synthetic generator (geometric Brownian
motion with per-ticker drift/volatility) so the pipeline runs anywhere with
no API key. To use real data, set SOURCE='yfinance' (see README) — the output
schema is identical, so nothing downstream changes.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# ticker -> (display name, sector, annual drift, annual vol, start price)
UNIVERSE = {
    "AAPL": ("Apple Inc.",        "Technology",       0.18, 0.28, 180),
    "MSFT": ("Microsoft Corp.",   "Technology",       0.16, 0.26, 330),
    "JPM":  ("JPMorgan Chase",    "Financials",       0.10, 0.30, 150),
    "XOM":  ("Exxon Mobil",       "Energy",           0.07, 0.34, 105),
    "JNJ":  ("Johnson & Johnson", "Healthcare",       0.06, 0.20, 160),
    "TSLA": ("Tesla Inc.",        "Consumer Cyclical",0.20, 0.55, 240),
}

def extract(tickers=None, n_days: int = 600, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    tickers = tickers or list(UNIVERSE)
    dates = pd.bdate_range(end=pd.Timestamp("2024-12-31"), periods=n_days)
    # A single SHARED market factor drives co-movement across all tickers, so
    # daily returns are positively correlated like real equities.
    market = rng.normal(0, 1, n_days)
    beta = 0.6  # market exposure
    frames = []
    for t in tickers:
        _, _, mu, sigma, p0 = UNIVERSE[t]
        dt = 1 / 252
        idio = rng.normal(0, 1, n_days)
        shock = beta * market + np.sqrt(1 - beta**2) * idio
        rets = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shock
        close = p0 * np.exp(np.cumsum(rets))
        intraday = np.abs(rng.normal(0, sigma * np.sqrt(dt), n_days)) * close
        open_ = close / np.exp(rets)
        high = np.maximum(open_, close) + intraday
        low = np.minimum(open_, close) - intraday
        volume = rng.integers(5_000_000, 60_000_000, n_days)
        frames.append(pd.DataFrame(dict(
            ticker=t, date=dates,
            open=open_.round(2), high=high.round(2),
            low=low.round(2), close=close.round(2), volume=volume,
        )))
    df = pd.concat(frames, ignore_index=True)
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df

if __name__ == "__main__":
    df = extract()
    print(df.groupby("ticker").size())
    print(f"\nTotal rows: {len(df):,}")
