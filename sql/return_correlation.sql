-- Pairwise correlation of daily returns across the universe.
SELECT a.ticker AS ticker_a, b.ticker AS ticker_b,
       round(corr(a.daily_return, b.daily_return), 3) AS return_corr
FROM marts.fct_daily_metrics a
JOIN marts.fct_daily_metrics b USING (trade_date)
WHERE a.ticker < b.ticker
  AND a.daily_return IS NOT NULL AND b.daily_return IS NOT NULL
GROUP BY 1, 2
ORDER BY return_corr DESC;
