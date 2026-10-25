# Data quality log — issues found and how they were fixed

Source: `notebooks/01_eda.ipynb` (49 cells, executed, 0 errors).
All counts below were verified against the raw CSVs and again against
the pipeline outputs.

## Row counts (raw, verified with pandas — not `wc -l`)

| Table | Rows |
|---|---|
| orders | 99,441 |
| customers | 99,441 |
| order_items | 112,650 |
| order_payments | 103,886 |
| order_reviews | 99,224 |
| products | 32,951 |
| sellers | 3,095 |
| geolocation | 1,000,163 |
| category_translation | 71 |

Note: `wc -l` overcounts the reviews file (104,720 lines) because review
comments contain quoted newlines. Pandas, which respects CSV quoting,
gives the true 99,224 rows. That is why the pipeline's load check
compares pandas row counts, not line counts.

## Issues

1. **Duplicate reviews — 551 orders with more than one review row.**
   Fix: keep the latest review by `review_creation_date`
   (`ROW_NUMBER()` in `02_master_table.sql`). Result: 98,673 orders
   with a review, 95,832 of them delivered.
2. **Delivered orders with no delivery date — 8 orders.**
   Fix: none — excluded from delivery KPIs (on-time rate, delivery
   days), not imputed, not counted as late. Logged as INFO by check
   `delivered_missing_delivery_date` in `04_data_quality_checks.sql`.
3. **Missing dates elsewhere — expected, not errors.** `order_approved_at`
   missing for 160 orders, carrier date for 1,783, customer delivery
   date for 2,965 (mostly orders that were never delivered). Kept as
   NULL; no imputation.
4. **One delivered order with no payment row (Sep 2016).**
   Fix: `COALESCE(payment_value_total, 0)` gives it R$ 0 revenue.
   This is why `kpi_monthly` shows R$ 0.00 for 2016-09 (4 orders total).
   Immaterial (1 order), but documented so the R$ 0 is not mistaken
   for a pipeline bug.
5. **775 orders with no item row.** Mostly canceled / unavailable /
   invoiced orders that never reached an item. Kept in master_orders
   with `item_count = 0`; they contribute to total orders and
   cancellation rate, not to category revenue.
6. **610 products missing category, name length, description length
   and photo count (the same 610 rows).** Treated as incomplete
   catalogue rows. Their items fall into category `unknown` only if
   they have no category at all; the pipeline does not drop them.
7. **Two product categories with no English translation:**
   `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`.
   Fix: fall back to the Portuguese name in `category_monthly.csv`
   instead of dropping those sales.
8. **Geolocation: 261,831 full-duplicate rows; keyed by zip prefix,
   not by order.** Fix: loaded for completeness, never joined into
   the order-grain master table (joining it would fan out orders).
   State/city for the dashboard map come from `customers`.
9. **Partial months at both ends.** Sep 2016: 4 orders. No orders in
   Nov 2016. Sep 2018: 16 orders, Oct 2018: 4 orders, none delivered
   (extract ends 17 Oct 2018). Fix: `is_full_month` flag in
   `kpi_monthly`; dashboard trend filters to Jan 2017 – Aug 2018.
10. **Delivery-time long tail.** Mean 12.56 days, median 10.22 days,
    max 209.6 days, no negative values. The mean alone understates
    the tail; the dashboard therefore shows the delivery-delay buckets
    (0–3, 4–7, 8–14, 15–30, 30+ days) against review score.
11. **No negative values anywhere.** 0 negative `payment_value`,
    0 negative `revenue_delivered`, minimum item price R$ 0.85.
    Checks for these are in `04_data_quality_checks.sql` and pass.
12. **No duplicate keys in orders, customers, items, payments,
    products or sellers.** Verified; the master-table grain check
    (`master_duplicate_order_id = 0`) passes.

## Checks that run on every refresh

See `sql/04_data_quality_checks.sql` and `src/quality_checks.py`:
row-count match raw → clean → master, null keys = 0, duplicate
order_id = 0, negative revenue = 0, negative payments = 0, plus a
per-table load count. A WARNING is logged to `logs/pipeline_run.log`
and does not silently pass.
