# KPI definitions — exact formulas

All KPIs are computed in `sql/03_kpi_monthly.sql` from `master_orders`.
Money is in Brazilian reais (R$). Month = purchase month (`order_month`,
YYYY-MM from `order_purchase_timestamp`).

| # | KPI | Formula | Overall value in this extract |
|---|-----|---------|-------------------------------|
| 1 | Total revenue | SUM(`revenue_delivered`) = payments on **delivered** orders only | **R$ 15,422,461.77** |
| 2 | Total orders | COUNT of orders | **99,441** (96,478 delivered) |
| 3 | Average order value (AOV) | Total revenue / delivered orders | **R$ 159.85** |
| 4 | Month-over-month growth % | (this month revenue − last month revenue) / last month revenue, via `LAG()` | Peak: **+53.6% in Nov 2017** (R$ 751,140.27 → R$ 1,153,528.05) |
| 5 | On-time delivery rate | Delivered on/before estimated date / delivered orders with a delivery date | **91.89%** |
| 6 | Average delivery days | AVG(purchase → customer delivery, in days) over delivered orders with a delivery date; median 10.22 days | **12.56 days** |
| 7 | Average review score | AVG(latest review per order) over delivered orders with a review | **4.16** (95,832 reviews) |
| 8 | Cancellation rate | Canceled orders / total orders | **0.63%** (625 / 99,441) |

## Decisions that change the numbers (read before reusing them)

- **Revenue counts delivered orders only.** All payments total R$ 16,008,872.12.
  The R$ 586,410.35 paid on non-delivered orders (including R$ 143,255.60 on
  canceled orders) is kept in `payment_value_total` for reconciliation but
  excluded from revenue. Counting it would present canceled sales as sales.
- **AOV denominator is delivered orders**, to match the revenue numerator.
  Revenue / all orders would be R$ 155.09 and would mix two populations.
- **On-time and delivery days exclude the 8 delivered orders with no
  delivery date.** They are not counted as late and their delivery time
  is not imputed. The denominator is therefore 96,470 dated delivered
  orders, not 96,478.
- **Review score uses the latest review per order.** 551 orders have more
  than one review row; averaging all rows would double-count those orders.
- **Category revenue is item price, not payment_value.** Category totals
  come from `category_monthly.csv` (order_items × products). Summing
  payment_value at item grain would double-count multi-item orders.
  Category item-price total for delivered orders is R$ 13,221,498.11
  (reconciles exactly to master_orders item_price_total for delivered
  orders). It is not expected to equal payment revenue
  (R$ 15,422,461.77), because payments also include freight and
  voucher / installment effects.
- **MoM growth is only meaningful for full months.** `kpi_monthly`
  carries `is_full_month` (1 for Jan 2017 – Aug 2018). Sep 2016 (4 orders),
  Nov 2016 (no orders), and Sep–Oct 2018 (dataset cut off 17 Oct 2018)
  are kept for reconciliation but must be filtered out of trend reads —
  otherwise Jan 2017 shows a meaningless +6,500% off a R$ 19.62 base.
