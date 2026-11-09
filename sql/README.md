# SQL index — which query answers which question

Run order matters: `01` → `02` → `03`, then `04`. `python src/pipeline.py`
runs all four; you only need to run files by hand when debugging.
`sql/01`–`04` are SQLite dialect; Databricks versions of `01`–`03` are in
`sql/databricks/`.

## Pipeline queries

| File | Question it answers |
|---|---|
| `01_clean_orders.sql` | "Give me one trustworthy row per order, with delivery flags and delivery days." |
| `02_master_table.sql` | "Give me one row per order with its customer, revenue, items and latest review." |
| `03_kpi_monthly.sql` | "What are the 8 KPIs for each purchase month, and how did revenue move vs last month?" |
| `04_data_quality_checks.sql` | "Is this refresh safe to publish?" (SELECT-only; run by `src/quality_checks.py`) |

## Ad-hoc / reusable queries (`sql/ad-hoc/`)

All read the processed reporting tables, never the raw CSVs. Run any of
them without a database: `python src/run_adhoc.py 02` loads
`data/processed/` into memory and prints the answer. Change the month or
state in the `WHERE` clause to reuse it for a new request. Full request
context: `docs/ad-hoc-requests.md`.

| File | Question it answers |
|---|---|
| `ad-hoc/01_revenue_by_category_last_month.sql` | "Which categories sold best last month, and what share is each?" |
| `ad-hoc/02_late_deliveries_by_state.sql` | "Which states get the most late deliveries?" |
| `ad-hoc/03_review_late_vs_on_time.sql` | "Do late orders get worse reviews than on-time ones?" |
| `ad-hoc/04_sp_vs_rest_2018_ytd.sql` | "How much of this year's revenue is São Paulo vs everywhere else?" |
| `ad-hoc/05_canceled_order_value.sql` | "How many orders are canceled and how much money is tied up in them?" |
| `ad-hoc/06_black_friday_2017.sql` | "Did Black Friday beat a normal day, and did delivery cope?" |

## Copy-paste recipes for non-SQL users

See `docs/self-service-guide.md` for the dashboard and spreadsheet routes
first — they need no SQL at all. If you do need a query, the three most
reused are:

- **Monthly revenue, orders, on-time rate** — no query needed, read
  `data/processed/kpi_monthly.csv` (filter `is_full_month = 1`). To get
  it in SQL: `SELECT order_month, total_revenue, total_orders,
  on_time_rate FROM kpi_monthly WHERE is_full_month = 1;`
- **One order's detail** — `SELECT * FROM master_orders WHERE order_id =
  '…';` (or use the Order Lookup sheet in the spreadsheet).
- **Revenue by state** — copy `ad-hoc/04` and replace the
  `CASE WHEN customer_state = 'SP'` grouping with `customer_state`.

**Two rules when reusing these queries:** revenue means
`revenue_delivered` (delivered orders only), and category revenue comes
from `category_monthly`, never from summing payments at item grain.
Definitions: `docs/kpi_definitions.md`.
