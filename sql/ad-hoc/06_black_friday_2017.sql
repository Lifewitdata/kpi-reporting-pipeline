-- 06_black_friday_2017.sql
-- Request: "Was Black Friday worth it?" (Marketing / Sales director)
-- Clarified: Black Friday 2017 = purchases on 2017-11-24. Compare that
-- day with the other 29 days of Nov 2017: orders and delivered revenue
-- per day, plus on-time rate and review score across those orders.

WITH tagged AS (
    SELECT
        CASE WHEN date(order_purchase_timestamp) = '2017-11-24'
             THEN 'Black Friday' ELSE 'Other Nov 2017 days' END AS day_type,
        date(order_purchase_timestamp) AS purchase_date,
        is_delivered,
        revenue_delivered,
        on_time_flag,
        review_score
    FROM master_orders
    WHERE order_month = '2017-11'
)
SELECT
    day_type,
    COUNT(DISTINCT purchase_date) AS days,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT purchase_date), 0) AS orders_per_day,
    ROUND(SUM(revenue_delivered) / COUNT(DISTINCT purchase_date), 2) AS revenue_per_day,
    ROUND(100.0 * AVG(CASE WHEN is_delivered = 1 THEN on_time_flag END), 1) AS on_time_pct,
    ROUND(AVG(CASE WHEN is_delivered = 1 THEN review_score END), 2) AS avg_review_score
FROM tagged
GROUP BY day_type
ORDER BY day_type;
