-- 03_kpi_monthly.sql
-- Purpose: monthly KPI table, one row per purchase month.
-- Uses a CTE for the monthly aggregates and a window function (LAG)
-- for month-over-month revenue growth. Averages ignore NULLs in
-- SQLite, which is exactly the behaviour the KPI definitions want:
-- on-time rate and delivery days cover only delivered orders with the
-- relevant date present; review score covers only delivered orders
-- with a (deduplicated) review.
-- Grain: one row per order_month (YYYY-MM, by purchase date).

DROP TABLE IF EXISTS kpi_monthly;

CREATE TABLE kpi_monthly AS
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
    -- Full months in THIS extract only: the data starts 4 Sep 2016
    -- (4 orders that month, none in Nov 2016) and stops 17 Oct 2018
    -- (16 orders in Sep 2018, 4 in Oct 2018, none delivered). MoM
    -- growth and trend reads should be filtered to is_full_month = 1;
    -- the edge months are kept in the table for reconciliation, not
    -- dropped, so the monthly totals still sum to the overall totals.
    CASE
        WHEN order_month BETWEEN '2017-01' AND '2018-08' THEN 1
        ELSE 0
    END AS is_full_month,
    total_orders,
    delivered_orders,
    canceled_orders,
    CAST(canceled_orders AS REAL) / NULLIF(total_orders, 0)
        AS cancellation_rate,
    total_revenue,
    CASE
        WHEN delivered_orders > 0
        THEN total_revenue / CAST(delivered_orders AS REAL)
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
