-- Staging model: clean & standardize the raw landing table.
CREATE SCHEMA IF NOT EXISTS staging;
CREATE OR REPLACE TABLE staging.stg_prices AS
SELECT
    upper(ticker)        AS ticker,
    CAST(date AS DATE)   AS trade_date,
    open, high, low, close,
    CAST(volume AS BIGINT) AS volume
FROM raw.prices
WHERE close IS NOT NULL AND close > 0
QUALIFY row_number() OVER (PARTITION BY ticker, CAST(date AS DATE)
                           ORDER BY ingested_at DESC) = 1;  -- de-dupe, keep latest
