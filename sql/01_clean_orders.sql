-- 01_clean_orders.sql
-- Purpose: one clean row per order, standardised dates, delivery flags.
-- No rows are dropped except rows with a null order_id (there are none
-- in this extract, verified in the data quality log). Null delivery
-- dates are kept as NULL, not imputed, so delivery KPIs are computed
-- only over orders that actually have a delivery date.
-- Grain: one row per order_id.

DROP TABLE IF EXISTS clean_orders;

CREATE TABLE clean_orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END AS is_delivered,
    CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END AS is_canceled,
    order_purchase_timestamp,
    strftime('%Y-%m', order_purchase_timestamp) AS order_month,
    date(order_purchase_timestamp) AS order_purchase_date,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    -- Fractional days from purchase to delivery; NULL unless delivered
    -- with both dates present (8 delivered orders lack a delivery date).
    CASE
        WHEN order_status = 'delivered'
            AND order_delivered_customer_date IS NOT NULL
        THEN julianday(order_delivered_customer_date)
             - julianday(order_purchase_timestamp)
        ELSE NULL
    END AS delivery_days,
    -- 1 = delivered on or before the estimated date, 0 = late,
    -- NULL = not delivered or date missing (excluded from the rate).
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
