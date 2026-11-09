-- 01_clean_orders.sql — Databricks / Spark SQL port of sql/01_clean_orders.sql
-- Same logic, Spark functions:
--   strftime('%Y-%m', x)  -> date_format(x, 'yyyy-MM')
--   date(x)               -> to_date(x)
--   julianday(a)-julianday(b) -> (unix_timestamp(a)-unix_timestamp(b))/86400
-- on_time_flag compares the full timestamps, exactly as the SQLite
-- version compares the ISO strings: the estimated date is midnight, so
-- a delivery later on the promised day counts as late. Do not "fix"
-- this to to_date() on one side only, or the rate will not reconcile.
-- Run after 00_load_raw.py, in the schema it created.

CREATE OR REPLACE TABLE clean_orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END AS is_delivered,
    CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END AS is_canceled,
    order_purchase_timestamp,
    date_format(order_purchase_timestamp, 'yyyy-MM') AS order_month,
    to_date(order_purchase_timestamp) AS order_purchase_date,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    CASE
        WHEN order_status = 'delivered'
            AND order_delivered_customer_date IS NOT NULL
        THEN (unix_timestamp(order_delivered_customer_date)
              - unix_timestamp(order_purchase_timestamp)) / 86400.0
        ELSE NULL
    END AS delivery_days,
    CASE
        WHEN order_status = 'delivered'
            AND order_delivered_customer_date IS NOT NULL
            AND order_estimated_delivery_date IS NOT NULL
        THEN CASE
            WHEN order_delivered_customer_date <= order_estimated_delivery_date
            THEN 1 ELSE 0
        END
        ELSE NULL
    END AS on_time_flag
FROM orders
WHERE order_id IS NOT NULL;
