-- 02_master_table.sql — Databricks / Spark SQL port of sql/02_master_table.sql
-- Identical logic; only DROP + CREATE becomes CREATE OR REPLACE.
-- Payments and items are aggregated before joining so the order grain
-- does not fan out; only the latest review per order is kept.
--
-- Reconciliation note: 31 delivered orders have two reviews with the
-- same latest review_creation_date and different scores (see
-- docs/escalation-log.md E4). ROW_NUMBER breaks that tie arbitrarily,
-- so avg_review_score can differ in the 4th decimal between engines.
-- Order counts and revenue must match exactly; the review average is
-- expected to match to 2 decimals (4.16).

CREATE OR REPLACE TABLE master_orders AS
WITH payment_agg AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value_total,
        COUNT(*) AS payment_count
    FROM order_payments
    GROUP BY order_id
),
item_agg AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS item_price_total,
        SUM(freight_value) AS freight_total
    FROM order_items
    GROUP BY order_id
),
review_latest AS (
    SELECT order_id, review_score
    FROM (
        SELECT
            order_id,
            review_score,
            ROW_NUMBER() OVER (
                PARTITION BY order_id
                ORDER BY review_creation_date DESC
            ) AS rn
        FROM order_reviews
        WHERE review_score IS NOT NULL
    )
    WHERE rn = 1
)
SELECT
    c.order_id,
    c.customer_id,
    cu.customer_state,
    cu.customer_city,
    c.order_status,
    c.is_delivered,
    c.is_canceled,
    c.order_purchase_timestamp,
    c.order_month,
    c.order_delivered_customer_date,
    c.order_estimated_delivery_date,
    c.delivery_days,
    c.on_time_flag,
    COALESCE(p.payment_value_total, 0) AS payment_value_total,
    CASE
        WHEN c.is_delivered = 1 THEN COALESCE(p.payment_value_total, 0)
        ELSE 0
    END AS revenue_delivered,
    COALESCE(i.item_count, 0) AS item_count,
    COALESCE(i.item_price_total, 0) AS item_price_total,
    COALESCE(i.freight_total, 0) AS freight_total,
    r.review_score
FROM clean_orders AS c
LEFT JOIN customers AS cu
    ON c.customer_id = cu.customer_id
LEFT JOIN payment_agg AS p
    ON c.order_id = p.order_id
LEFT JOIN item_agg AS i
    ON c.order_id = i.order_id
LEFT JOIN review_latest AS r
    ON c.order_id = r.order_id;
