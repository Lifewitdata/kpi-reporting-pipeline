# Self-service guide — get the answer without asking an analyst

For sales, marketing and ops colleagues who do not write SQL. Three
routes, easiest first. All three read the same tables, so the numbers
agree.

## Route 1 — the Tableau dashboard (no files, no formulas)

Open the published workbook:
https://public.tableau.com/app/profile/isfaque.ansari5273/viz/Olist_KPI_Reporting_Advanced/ExecutiveSummary

**Monthly revenue, orders and on-time rate:**

1. On **Executive Summary**, use the **year** filter to pick the year
   (2017 or 2018 are complete enough to read).
2. The KPI cards at the top give revenue, orders, on-time %, average
   order value, delivery days, review score and cancellation rate for
   whatever is filtered.
3. For the month-by-month view, read the **Revenue MoM** and
   **Trend Revenue + On-time** charts — hover a month for its exact
   revenue and on-time rate.
4. To restrict to one state, use the **state** filter. Clear it again
   before comparing with the published totals.
5. For categories, go to **Deep Dive** and use the **Selected Category**
   and **Top N Categories** controls, plus **Map Metric** for the state
   map. Category filtering lives on page 2 on purpose: category is per
   item, so filtering the page-1 order cards by category would
   double-count payments.

Worksheets behind those views, if you open the workbook itself:
`KPI Revenue`, `KPI Orders`, `KPI On-time`, `Revenue MoM`,
`Trend Revenue + On-time`, `Top N Categories`, `State Ranking`,
`Review vs Delivery Delay`.

## Route 2 — the spreadsheet (Excel, filters and dropdowns)

Open `spreadsheets/Olist_KPI_Spreadsheet.xlsx` (guide:
`spreadsheets/README.md`).

- **Monthly KPIs** sheet: one row per month with revenue, orders and
  on-time rate. Filter `is_full_month` to 1 to exclude the partial
  months at each end.
- **Pivot by Month** / **Pivot by Category**: drag-free native
  PivotTables — use the month or category filter on the pivot.
- **Selector** sheet: pick a month and a category from the dropdowns and
  the answers recalculate.
- **Order Lookup** sheet: paste an `order_id` and get its category,
  delivery days and revenue.

## Route 3 — the CSV (Excel or Google Sheets, 30 seconds)

Open `data/processed/kpi_monthly.csv`. One row per purchase month:

| You want | Column |
|---|---|
| Revenue | `total_revenue` (R$, delivered orders only) |
| Orders | `total_orders` (all) or `delivered_orders` |
| On-time rate | `on_time_rate` — a fraction; format as % (0.9189 → 91.89%) |
| Average order value | `avg_order_value` |
| Growth vs last month | `mom_revenue_growth` — also a fraction |

**Filter `is_full_month = 1` first.** Sep–Dec 2016 and Sep–Oct 2018 are
partial months; including them makes growth figures meaningless (Jan
2017 shows +6,500% off a R$ 19.62 base).

Other files: `delivery_by_state.csv` for state performance,
`category_monthly.csv` for category revenue, `master_orders.csv` for
single-order detail. Columns explained in `docs/data_dictionary.md`.

## Route 4 — copy a reusable query

If you can run SQL, `sql/README.md` lists every query and the question it
answers. You do not need a database: `python src/run_adhoc.py 02` prints
the answer for request 2 straight from the CSVs. Copy the file, change
the month or state in the `WHERE` clause, run again.

## Three things that will otherwise trip you up

1. **Revenue is delivered orders only.** Payments on canceled orders
   exist in `payment_value_total` but are not revenue. Total revenue for
   this extract is R$ 15,422,461.77 on 99,441 orders.
2. **Rates are fractions in the CSVs, percentages in the dashboard.**
3. **Don't sum payments by category.** Use `category_monthly.csv`, which
   is item price; it will not equal R$ 15.4m and is not meant to
   (`docs/kpi_definitions.md`).

Still stuck? Log the request the way `docs/ad-hoc-requests.md` does:
what you asked, what you actually need, and the period. That is enough
for an analyst to answer it without a meeting.
