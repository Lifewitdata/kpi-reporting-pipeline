-- 02_late_deliveries_by_state.sql
-- Request: "Where are we late?" (Regional sales manager)
-- Clarified: late = delivered after the promised date. Full months
-- Jan 2017 - Aug 2018, delivered orders with a delivery date, states
-- with at least 500 such orders, worst late rate first.

SELECT
    customer_state,
    COUNT(*) AS dated_delivered_orders,
    SUM(CASE WHEN on_time_flag = 0 THEN 1 ELSE 0 END) AS late_orders,
    ROUND(100.0 * SUM(CASE WHEN on_time_flag = 0 THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS late_rate_pct,
    ROUND(AVG(delivery_days), 1) AS avg_delivery_days
FROM master_orders
WHERE is_delivered = 1
  AND on_time_flag IS NOT NULL
  AND order_month BETWEEN '2017-01' AND '2018-08'
GROUP BY customer_state
HAVING COUNT(*) >= 500
ORDER BY late_rate_pct DESC
LIMIT 10;
