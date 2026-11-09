-- 03_kpi_monthly.sql — Databricks / Spark SQL port of sql/03_kpi_monthly.sql
-- Identical logic. CAST(x AS REAL) becomes CAST(x AS DOUBLE); AVG
-- ignores NULLs in Spark as it does in SQLite, which is what the KPI
-- definitions require.

CREATE OR REPLACE TABLE kpi_monthly AS
WITH monthly AS (
    SELECT
        order_month,
        COUNT(*) AS total_orders,
        SUM(is_delivered) AS delivered_orders,
        SUM(is_canceled) AS canceled_orders,
        SUM(revenue_delivered) AS total_revenue,
        AVG(CASE WHEN is_delivered = 1 THEN review_score END)
            AS avg_review_score,
        AVG(CASE WHEN is_delivered = 1 THEN delivery_days END)
            AS avg_delivery_days,
        AVG(CASE WHEN is_delivered = 1 THEN on_time_flag END)
            AS on_time_rate
    FROM master_orders
    GROUP BY order_month
),
with_lag AS (
    SELECT
        *,
        LAG(total_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM monthly
)
SELECT
    order_month,
    CASE
        WHEN order_month BETWEEN '2017-01' AND '2018-08' THEN 1
        ELSE 0
    END AS is_full_month,
    total_orders,
    delivered_orders,
    canceled_orders,
    CAST(canceled_orders AS DOUBLE) / NULLIF(total_orders, 0)
        AS cancellation_rate,
    total_revenue,
    CASE
        WHEN delivered_orders > 0
        THEN total_revenue / CAST(delivered_orders AS DOUBLE)
    END AS avg_order_value,
    on_time_rate,
    avg_delivery_days,
    avg_review_score,
    CASE
        WHEN prev_month_revenue > 0
        THEN (total_revenue - prev_month_revenue) / prev_month_revenue
    END AS mom_revenue_growth
FROM with_lag
ORDER BY order_month;
