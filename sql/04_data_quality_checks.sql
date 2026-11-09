-- 04_data_quality_checks.sql
-- Purpose: SELECT-only validation. Run after 01-03; it never changes data.
-- A WARNING here does not stop the pipeline (see src/quality_checks.py),
-- it is logged so a bad refresh is visible instead of silent.

SELECT 'clean_orders_row_count' AS check_name,
       (SELECT COUNT(*) FROM clean_orders) AS actual_value,
       CASE WHEN (SELECT COUNT(*) FROM clean_orders)
                 = (SELECT COUNT(*) FROM orders)
            THEN 'PASS' ELSE 'WARNING' END AS status
UNION ALL
SELECT 'master_orders_row_count',
       (SELECT COUNT(*) FROM master_orders),
       CASE WHEN (SELECT COUNT(*) FROM master_orders)
                 = (SELECT COUNT(*) FROM clean_orders)
            THEN 'PASS' ELSE 'WARNING' END
UNION ALL
SELECT 'master_null_order_id',
       (SELECT COUNT(*) FROM master_orders WHERE order_id IS NULL),
       CASE WHEN (SELECT COUNT(*) FROM master_orders
                  WHERE order_id IS NULL) = 0
            THEN 'PASS' ELSE 'WARNING' END
UNION ALL
SELECT 'master_duplicate_order_id',
       (SELECT COUNT(*) FROM master_orders)
         - (SELECT COUNT(DISTINCT order_id) FROM master_orders),
       CASE WHEN (SELECT COUNT(*) FROM master_orders)
                 - (SELECT COUNT(DISTINCT order_id) FROM master_orders) = 0
            THEN 'PASS' ELSE 'WARNING' END
UNION ALL
SELECT 'negative_revenue_delivered',
       (SELECT COUNT(*) FROM master_orders WHERE revenue_delivered < 0),
       CASE WHEN (SELECT COUNT(*) FROM master_orders
                  WHERE revenue_delivered < 0) = 0
            THEN 'PASS' ELSE 'WARNING' END
UNION ALL
SELECT 'negative_payment_value',
       (SELECT COUNT(*) FROM order_payments WHERE payment_value < 0),
       CASE WHEN (SELECT COUNT(*) FROM order_payments
                  WHERE payment_value < 0) = 0
            THEN 'PASS' ELSE 'WARNING' END
UNION ALL
SELECT 'delivered_missing_delivery_date',
       (SELECT COUNT(*) FROM master_orders
        WHERE is_delivered = 1
          AND order_delivered_customer_date IS NULL),
       -- Known value in this extract: 8. Flagged as INFO, not a failure:
       -- those 8 orders are excluded from delivery KPIs, not imputed.
       'INFO'
UNION ALL
SELECT 'kpi_monthly_months',
       (SELECT COUNT(*) FROM kpi_monthly),
       CASE WHEN (SELECT COUNT(*) FROM kpi_monthly) > 0
            THEN 'PASS' ELSE 'WARNING' END
UNION ALL
SELECT 'surplus_review_rows',
       (SELECT COUNT(*) FROM order_reviews WHERE review_score IS NOT NULL)
         - (SELECT COUNT(DISTINCT order_id) FROM order_reviews
            WHERE review_score IS NOT NULL),
       -- Known value in this extract: 551 surplus review rows across
       -- 547 orders. Handled by review_latest in 02_master_table.sql,
       -- which keeps one review per order. See escalation-log.md E1.
       'INFO'
UNION ALL
SELECT 'tied_latest_review_orders',
       (SELECT COUNT(*) FROM (
            SELECT order_id,
                   COUNT(*) AS top_rows,
                   COUNT(DISTINCT review_score) AS distinct_scores
            FROM (
                SELECT order_id, review_score, review_creation_date,
                       MAX(review_creation_date) OVER (
                           PARTITION BY order_id
                       ) AS latest_date
                FROM order_reviews
                WHERE review_score IS NOT NULL
            )
            WHERE review_creation_date = latest_date
            GROUP BY order_id
            HAVING top_rows > 1 AND distinct_scores > 1
        )),
       -- Orders whose latest review date is shared by reviews with
       -- different scores, so "keep the latest" is a coin flip for them
       -- and avg_review_score is not deterministic. Open, E4.
       'WARNING'
UNION ALL
SELECT 'delivered_without_payment',
       (SELECT COUNT(*) FROM master_orders AS m
        WHERE m.is_delivered = 1
          AND NOT EXISTS (SELECT 1 FROM order_payments AS p
                          WHERE p.order_id = m.order_id)),
       -- Known value in this extract: 1 (Sep 2016), counted as R$ 0
       -- revenue. Documented in escalation-log.md E3 so the R$ 0.00
       -- month is not read as a pipeline bug.
       'INFO';
