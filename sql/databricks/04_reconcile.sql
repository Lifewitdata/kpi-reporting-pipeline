-- 04_reconcile.sql — run on Databricks AFTER 01-03.
-- Every row must read MATCH before the run is written up in
-- docs/databricks-run.md. Expected values come from the SQLite
-- pipeline on the same Kaggle extract (verified 2026-11-09).
--
-- avg_review_score is compared to 2 decimals on purpose: 31 orders
-- have tied latest reviews, so the 4th decimal is engine-dependent
-- (docs/escalation-log.md E4).

WITH actual AS (
    SELECT
        (SELECT COUNT(*) FROM clean_orders)              AS clean_rows,
        (SELECT COUNT(*) FROM master_orders)             AS master_rows,
        (SELECT COUNT(DISTINCT order_id) FROM master_orders) AS distinct_orders,
        (SELECT SUM(is_delivered) FROM master_orders)    AS delivered_orders,
        (SELECT ROUND(SUM(revenue_delivered), 2) FROM master_orders) AS revenue,
        (SELECT ROUND(SUM(item_price_total), 2) FROM master_orders
         WHERE is_delivered = 1)                         AS delivered_item_price,
        (SELECT COUNT(*) FROM kpi_monthly)               AS months,
        (SELECT ROUND(AVG(on_time_flag) * 100, 2) FROM master_orders
         WHERE is_delivered = 1)                         AS on_time_pct,
        (SELECT ROUND(AVG(delivery_days), 2) FROM master_orders
         WHERE is_delivered = 1)                         AS avg_delivery_days,
        (SELECT ROUND(AVG(review_score), 2) FROM master_orders
         WHERE is_delivered = 1)                         AS avg_review_score,
        (SELECT COUNT(*) FROM master_orders
         WHERE is_delivered = 1 AND order_delivered_customer_date IS NULL)
                                                         AS delivered_no_date
)
SELECT 'clean_orders rows'        AS metric, clean_rows      AS actual, 99441       AS expected, CASE WHEN clean_rows = 99441 THEN 'MATCH' ELSE 'DIFF' END AS result FROM actual
UNION ALL SELECT 'master_orders rows',   master_rows,      99441,       CASE WHEN master_rows = 99441 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'distinct order_id',    distinct_orders,  99441,       CASE WHEN distinct_orders = 99441 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'delivered orders',     delivered_orders, 96478,       CASE WHEN delivered_orders = 96478 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'revenue (R$)',         revenue,          15422461.77, CASE WHEN revenue = 15422461.77 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'delivered item price', delivered_item_price, 13221498.11, CASE WHEN delivered_item_price = 13221498.11 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'kpi_monthly months',   months,           25,          CASE WHEN months = 25 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'on-time rate (%)',     on_time_pct,      91.89,       CASE WHEN on_time_pct = 91.89 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'avg delivery days',    avg_delivery_days, 12.56,      CASE WHEN avg_delivery_days = 12.56 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'avg review score',     avg_review_score, 4.16,        CASE WHEN avg_review_score = 4.16 THEN 'MATCH' ELSE 'DIFF' END FROM actual
UNION ALL SELECT 'delivered w/o date',   delivered_no_date, 8,          CASE WHEN delivered_no_date = 8 THEN 'MATCH' ELSE 'DIFF' END FROM actual;
