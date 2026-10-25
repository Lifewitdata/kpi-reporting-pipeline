-- 02_master_table.sql
-- Purpose: one master reporting table at ORDER grain.
-- Joins: clean_orders + customers + payments (aggregated first) +
-- order items (aggregated first) + latest review per order.
--
-- Why aggregate before joining: an order can have several payments
-- and several items. Joining the detail tables directly would fan out
-- the order grain and double-count payment_value if summed. Payments
-- and items are therefore summed per order_id in CTEs first.
--
-- Why the latest review only: 551 orders have more than one review
-- row. Keeping every review row would duplicate the order; the
-- latest review by review_creation_date is kept (see data quality log).
--
-- Product category is NOT in this table on purpose: category lives at
-- item grain, not order grain. Category revenue is aggregated
-- separately in the pipeline (category_monthly.csv) from order_items
-- joined to products, and is never summed from this order-grain table.
-- Geolocation is NOT joined either: it is keyed by zip-code prefix,
-- not by order, and would fan out the grain. State/city come from
-- customers, which is what the dashboard map uses.

DROP TABLE IF EXISTS master_orders;

CREATE TABLE master_orders AS
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
    -- Revenue counts only delivered orders. Payments on canceled and
    -- other non-delivered orders (R$ 586,410.35 in total) are kept in
    -- payment_value_total for reconciliation but excluded here.
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
