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
            THEN 'PASS' ELSE 'WARNING' END;
