-- Fact: one row per security per day, with engineered trading metrics.
CREATE SCHEMA IF NOT EXISTS marts;
CREATE OR REPLACE TABLE marts.fct_daily_metrics AS
WITH base AS (
    SELECT ticker, trade_date, close, volume,
           LAG(close) OVER (PARTITION BY ticker ORDER BY trade_date) AS prev_close
    FROM staging.stg_prices
),
rets AS (
    SELECT *,
           close / NULLIF(prev_close, 0) - 1      AS daily_return,
           ln(close / NULLIF(prev_close, 0))      AS log_return
    FROM base
),
chg AS (
    SELECT *,
           greatest(daily_return, 0)  AS gain,
           greatest(-daily_return, 0) AS loss
    FROM rets
)
SELECT
    d.security_id,
    c.ticker,
    c.trade_date,
    c.close,
    c.volume,
    c.daily_return,
    c.log_return,
    avg(c.close)              OVER w20 AS sma_20,
    avg(c.close)              OVER w50 AS sma_50,
    stddev_samp(c.daily_return) OVER w20 * sqrt(252) AS ann_vol_20,
    -- RSI-14 (Cutler's simple-average variant; swap to Wilder's smoothing if preferred)
    100 - 100 / (1 + (avg(c.gain) OVER w14) / NULLIF(avg(c.loss) OVER w14, 0)) AS rsi_14
FROM chg c
LEFT JOIN marts.dim_security d USING (ticker)
WINDOW
    w20 AS (PARTITION BY c.ticker ORDER BY c.trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW),
    w50 AS (PARTITION BY c.ticker ORDER BY c.trade_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW),
    w14 AS (PARTITION BY c.ticker ORDER BY c.trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
ORDER BY c.ticker, c.trade_date;
