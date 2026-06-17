-- Largest absolute daily moves on the most recent trading day.
SELECT m.ticker, s.sector, m.trade_date,
       round(100 * m.daily_return, 2) AS pct_change,
       round(m.close, 2) AS close, round(m.rsi_14, 1) AS rsi_14
FROM marts.fct_daily_metrics m
JOIN marts.dim_security s USING (ticker)
WHERE m.trade_date = (SELECT max(trade_date) FROM marts.fct_daily_metrics)
ORDER BY abs(m.daily_return) DESC;
