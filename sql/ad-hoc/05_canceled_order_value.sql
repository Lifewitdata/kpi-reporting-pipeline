-- 05_canceled_order_value.sql
-- Request: "How much are we losing to cancellations?" (Sales ops)
-- Clarified: canceled orders and the payments recorded on them, by year.
-- These payments are excluded from revenue (KPI definitions), so this
-- is the value that never became revenue, not a refund figure.

SELECT
    substr(order_month, 1, 4) AS year,
    SUM(is_canceled) AS canceled_orders,
    COUNT(*) AS total_orders,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 2) AS cancellation_rate_pct,
    ROUND(SUM(CASE WHEN is_canceled = 1 THEN payment_value_total ELSE 0 END), 2)
        AS canceled_payment_value
FROM master_orders
GROUP BY year
ORDER BY year;
