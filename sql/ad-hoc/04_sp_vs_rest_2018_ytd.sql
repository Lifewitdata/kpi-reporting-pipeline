-- 04_sp_vs_rest_2018_ytd.sql
-- Request: "Is São Paulo carrying us this year?" (Head of sales)
-- Clarified: 2018 year to date = Jan-Aug 2018 (last full month).
-- Delivered revenue, delivered orders, AOV and share: SP vs all other states.

WITH ytd AS (
    SELECT
        CASE WHEN customer_state = 'SP' THEN 'SP' ELSE 'Rest of Brazil' END AS region,
        revenue_delivered,
        is_delivered
    FROM master_orders
    WHERE order_month BETWEEN '2018-01' AND '2018-08'
)
SELECT
    region,
    ROUND(SUM(revenue_delivered), 2) AS revenue,
    SUM(is_delivered) AS delivered_orders,
    ROUND(SUM(revenue_delivered) / SUM(is_delivered), 2) AS avg_order_value,
    ROUND(100.0 * SUM(revenue_delivered) / (SELECT SUM(revenue_delivered) FROM ytd), 1)
        AS revenue_share_pct
FROM ytd
GROUP BY region
ORDER BY revenue DESC;
