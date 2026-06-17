-- Dimension: one row per security (seed-style reference joined to live tickers).
CREATE SCHEMA IF NOT EXISTS marts;
CREATE OR REPLACE TABLE marts.dim_security AS
WITH seed(ticker, security_name, sector) AS (
    VALUES
      ('AAPL','Apple Inc.','Technology'),
      ('MSFT','Microsoft Corp.','Technology'),
      ('JPM','JPMorgan Chase','Financials'),
      ('XOM','Exxon Mobil','Energy'),
      ('JNJ','Johnson & Johnson','Healthcare'),
      ('TSLA','Tesla Inc.','Consumer Cyclical')
)
SELECT
    row_number() OVER (ORDER BY s.ticker) AS security_id,
    s.ticker,
    coalesce(seed.security_name, s.ticker) AS security_name,
    coalesce(seed.sector, 'Unknown')       AS sector
FROM (SELECT DISTINCT ticker FROM staging.stg_prices) s
LEFT JOIN seed USING (ticker);
