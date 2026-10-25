# Data dictionary

## Raw tables (data/raw/, from Kaggle Olist — not pushed to GitHub)

| File | Table | Rows | Key | Grain |
|---|---|---|---|---|
| olist_orders_dataset.csv | orders | 99,441 | order_id | one row per order |
| olist_customers_dataset.csv | customers | 99,441 | customer_id | one row per customer |
| olist_order_items_dataset.csv | order_items | 112,650 | order_id + order_item_id | one row per item in an order |
| olist_order_payments_dataset.csv | order_payments | 103,886 | order_id + payment_sequential | one row per payment |
| olist_order_reviews_dataset.csv | order_reviews | 99,224 | review_id (order_id repeats) | one row per review |
| olist_products_dataset.csv | products | 32,951 | product_id | one row per product |
| olist_sellers_dataset.csv | sellers | 3,095 | seller_id | one row per seller |
| olist_geolocation_dataset.csv | geolocation | 1,000,163 | zip-code prefix (repeats) | one row per zip prefix |
| product_category_name_translation.csv | category_translation | 71 | product_category_name | one row per category |

## master_orders.csv (data/processed/) — one row per order, 99,441 rows

| Column | Meaning |
|---|---|
| order_id, customer_id | Keys from orders / customers |
| customer_state, customer_city | Customer location (from customers) |
| order_status | delivered / shipped / canceled / unavailable / invoiced / processing / created / approved |
| is_delivered, is_canceled | 1/0 flags from order_status |
| order_purchase_timestamp, order_month | Purchase time; order_month is YYYY-MM |
| order_delivered_customer_date, order_estimated_delivery_date | Actual / promised delivery dates |
| delivery_days | Days from purchase to delivery (NULL if not delivered or date missing) |
| on_time_flag | 1 = delivered on/before estimate, 0 = late, NULL = not applicable |
| payment_value_total | Sum of all payments for the order (all statuses) |
| revenue_delivered | payment_value_total if delivered, else 0 — the revenue measure |
| item_count, item_price_total, freight_total | Item-grain aggregates for the order |
| review_score | Latest review score for the order (NULL if no review) |

## kpi_monthly.csv — one row per purchase month, 25 rows

order_month, is_full_month, total_orders, delivered_orders,
canceled_orders, cancellation_rate, total_revenue, avg_order_value,
on_time_rate, avg_delivery_days, avg_review_score, mom_revenue_growth.
Definitions: see `kpi_definitions.md`. Filter `is_full_month = 1` for trends.

## category_monthly.csv — one row per month × category, 1,273 rows

order_month, category (English, Portuguese fallback for 2 categories),
item_revenue (sum of item price, delivered orders only), orders
(distinct orders), items. **Do not sum payment_value from this file.**

## delivery_by_state.csv — one row per customer state, 27 rows

customer_state, delivered_orders, on_time_rate, avg_delivery_days,
avg_review_score. This is the dashboard map source.
