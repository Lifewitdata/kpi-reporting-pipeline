-- 01_revenue_by_category_last_month.sql
-- Request: "How did categories do last month?" (Sales lead)
-- Clarified: last FULL month in the extract = 2018-08; delivered item
-- revenue (item price, excl. freight) by category, top 10, with share.
-- Source: category_monthly, not master_orders, because category is
-- item grain; summing payments at item grain would double-count.

WITH last_month AS (
    SELECT category, item_revenue, orders
    FROM category_monthly
    WHERE order_month = '2018-08'
)
SELECT
    category,
    ROUND(item_revenue, 2) AS item_revenue,
    orders,
    ROUND(100.0 * item_revenue / (SELECT SUM(item_revenue) FROM last_month), 1)
        AS share_pct
FROM last_month
ORDER BY item_revenue DESC
LIMIT 10;
