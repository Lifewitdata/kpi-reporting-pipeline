# Ad-hoc request log — Sales-style requests on e-commerce data

**What this is.** Six one-off questions of the kind a Sales or commercial
team sends to an analyst, answered from the pipeline's reporting tables.
The data is the public Olist **e-commerce** dataset, not CRM data: there
are no leads, opportunities or sales reps. The requests are therefore
written as *Sales-style requests on e-commerce data*. The requesters are
example roles, not real people.

**How each request was handled:** vague question as asked → clarified
requirement (written down before writing any SQL) → reusable query in
`sql/ad-hoc/` → answer in plain language.

**Source tables:** every query reads the processed tables, never the raw
Kaggle CSVs. Requests 2–6 read `master_orders` (one row per order).
Request 1 reads `category_monthly`: product category exists per *item*,
not per order, so it is deliberately not a column in `master_orders`
(see `sql/02_master_table.sql`). Adding up order payments by category
would double-count orders that contain several categories.

**Reproduce every answer below:** `python src/run_adhoc.py` (or
`python src/run_adhoc.py 03` for one request). It loads
`data/processed/` into an in-memory database, so no raw download is
needed. Results below were copied from that run on 2026-11-09.

"Last full month" is **August 2018**: the extract ends on 17 Oct 2018
and September/October 2018 are incomplete (see `docs/kpi_definitions.md`).

---

## 1. Category performance last month

| | |
|---|---|
| **Requested by** | Sales lead, home & lifestyle categories |
| **Asked as** | "How did categories do last month?" |
| **Clarified as** | Top 10 categories by delivered item revenue (item price, excluding freight) in August 2018, with each one's share of that month's item revenue. |
| **Query** | `sql/ad-hoc/01_revenue_by_category_last_month.sql` |

| Category | Item revenue (R$) | Orders | Share |
|---|---:|---:|---:|
| health_beauty | 119,391.01 | 765 | 14.2% |
| watches_gifts | 69,767.06 | 387 | 8.3% |
| bed_bath_table | 60,891.09 | 555 | 7.3% |
| housewares | 58,763.36 | 549 | 7.0% |
| sports_leisure | 50,860.18 | 432 | 6.1% |

**Answer.** Health & beauty was clearly the biggest category in August
2018, bringing in about R$ 119k, roughly one in every seven reais of
product sales. Watches & gifts came second with about R$ 70k. No other
category reached 8% of the month's sales.

## 2. Late deliveries by state

| | |
|---|---|
| **Requested by** | Regional sales manager, North/Northeast |
| **Asked as** | "Where are we late?" |
| **Clarified as** | Share of delivered orders that arrived after the promised date, by customer state, for full months Jan 2017 – Aug 2018. Only states with at least 500 delivered orders, so small states don't top the list by chance. |
| **Query** | `sql/ad-hoc/02_late_deliveries_by_state.sql` |

| State | Delivered orders | Late | Late rate | Avg days |
|---|---:|---:|---:|---:|
| MA | 713 | 140 | 19.6% | 21.5 |
| CE | 1,273 | 196 | 15.4% | 21.2 |
| BA | 3,253 | 457 | 14.0% | 19.3 |
| RJ | 12,310 | 1,664 | 13.5% | 15.3 |
| PA | 942 | 117 | 12.4% | 23.8 |

**Answer.** Maranhão is the worst: about one order in five arrives
late, and the average wait is three weeks. Ceará and Bahia follow.
Rio de Janeiro has a lower late rate, but because it is so large it has
by far the most late orders in total (1,664), so that is where fixing
delivery would help the most customers.

## 3. Late delivery and ratings

| | |
|---|---|
| **Requested by** | Customer success lead (for the Sales QBR deck) |
| **Asked as** | "Do late orders hurt our ratings?" |
| **Clarified as** | For delivered orders with a delivery date and a review: average review score and share of 1-star reviews, on-time vs late. |
| **Query** | `sql/ad-hoc/03_review_late_vs_on_time.sql` |

| Delivery | Reviewed orders | Avg score | 1-star share |
|---|---:|---:|---:|
| On time | 88,163 | 4.29 | 6.6% |
| Late | 7,661 | 2.57 | 46.2% |

**Answer.** Yes, strongly. Orders that arrive on time average 4.3 stars;
late orders average 2.6. Almost half of late orders get a 1-star review,
compared with about 1 in 15 on-time orders. This shows the two go
together. It doesn't prove lateness is the only cause, because late
orders also tend to go to remote areas.

## 4. São Paulo vs the rest of Brazil, 2018 so far

| | |
|---|---|
| **Requested by** | Head of sales |
| **Asked as** | "Is São Paulo carrying us this year?" |
| **Clarified as** | "This year" = Jan – Aug 2018 (last full month). Delivered revenue, delivered orders, average order value and revenue share: SP vs all other states combined. |
| **Query** | `sql/ad-hoc/04_sp_vs_rest_2018_ytd.sql` |

| Region | Revenue (R$) | Delivered orders | Avg order (R$) | Share |
|---|---:|---:|---:|---:|
| Rest of Brazil | 5,124,685.02 | 29,448 | 174.02 | 60.6% |
| SP | 3,328,290.18 | 23,335 | 142.63 | 39.4% |

**Answer.** São Paulo matters a lot, but it is not carrying the business.
It brings in about 39% of 2018 revenue: SP orders are many but smaller.
Customers in the rest of Brazil spend about R$ 31 more per order (R$ 174
vs R$ 143), so the other states together bring in 61% of revenue.

## 5. Value lost to cancellations

| | |
|---|---|
| **Requested by** | Sales operations |
| **Asked as** | "How much are we losing to cancellations?" |
| **Clarified as** | Number of canceled orders, cancellation rate, and payments recorded on canceled orders, by year. These payments are already excluded from revenue, so this is sales that never happened, not refunds paid out. |
| **Query** | `sql/ad-hoc/05_canceled_order_value.sql` |

| Year | Canceled | Total orders | Rate | Payments on canceled (R$) |
|---|---:|---:|---:|---:|
| 2016 | 26 | 329 | 7.90% | 5,290.99 |
| 2017 | 265 | 45,101 | 0.59% | 62,832.96 |
| 2018 | 334 | 54,011 | 0.62% | 75,131.65 |

**Answer.** Very little. Since 2017, fewer than 1 order in 150 is
canceled, worth about R$ 63k in 2017 and R$ 75k in 2018, compared with
millions in revenue. The 7.9% in 2016 is from the platform's first few
months, when there were very few orders, and shouldn't be compared with
later years. The R$ 143,255.60 total matches `docs/kpi_definitions.md`.

## 6. Black Friday 2017

| | |
|---|---|
| **Requested by** | Marketing / Sales director |
| **Asked as** | "Was Black Friday worth it?" |
| **Clarified as** | Orders placed on 24 Nov 2017 vs the other 29 days of November 2017: orders and delivered revenue per day, plus the on-time rate and review score of those orders. |
| **Query** | `sql/ad-hoc/06_black_friday_2017.sql` |

| Day | Orders/day | Revenue/day (R$) | On time | Avg score |
|---|---:|---:|---:|---:|
| Black Friday | 1,176 | 175,250.94 | 80.0% | 3.78 |
| Other Nov 2017 days | 220 | 33,733.69 | 86.7% | 4.03 |

**Answer.** On sales, yes: Black Friday brought in about five times a
normal November day's orders and revenue (R$ 175k vs R$ 34k). But
delivery suffered. One in five Black Friday orders arrived late, and
those customers rated about a quarter-star lower. Next year, the extra
orders need extra delivery capacity planned in advance.
