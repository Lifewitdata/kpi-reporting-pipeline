# Databricks run — NOT RUN YET

**Status: the pipeline has never been executed on Databricks.** This
project runs on SQLite. Do not describe Databricks as a tool used on
this project, on a resume or in an interview, until the run below is
done and this page is filled in with real values and a screenshot.

What exists today is a **prepared, locally validated port** — not a
Databricks run.

## What is in the repo

| File | Purpose |
|---|---|
| `sql/databricks/00_load_raw.py` | Notebook cell: load the 9 CSVs from a Unity Catalog volume into tables, casting timestamps |
| `sql/databricks/01_clean_orders.sql` | Spark SQL port of `sql/01_clean_orders.sql` |
| `sql/databricks/02_master_table.sql` | Spark SQL port of `sql/02_master_table.sql` |
| `sql/databricks/03_kpi_monthly.sql` | Spark SQL port of `sql/03_kpi_monthly.sql` |
| `sql/databricks/04_reconcile.sql` | 11 metrics compared with the SQLite pipeline; every row must read MATCH |
| `src/check_databricks_port.py` | Local equivalence check (see below) |

Ported differences: `strftime` → `date_format`, `date()` → `to_date`,
`julianday` subtraction → `unix_timestamp` subtraction / 86400,
`CAST(… AS REAL)` → `CAST(… AS DOUBLE)`, `DROP` + `CREATE` →
`CREATE OR REPLACE TABLE`. The join and KPI logic is unchanged.

## What has been verified locally (2026-11-09)

`python src/check_databricks_port.py` transpiles the three Spark SQL
files to DuckDB with sqlglot, runs them on the raw CSVs, and executes
`04_reconcile.sql`. All 11 metrics matched the SQLite pipeline:

| Metric | Value |
|---|---|
| clean_orders / master_orders / distinct order_id | 99,441 |
| Delivered orders | 96,478 |
| Revenue | 15,422,461.77 |
| Delivered item price | 13,221,498.11 |
| kpi_monthly months | 25 |
| On-time rate | 91.89% |
| Average delivery days | 12.56 |
| Average review score | 4.16 |
| Delivered without delivery date | 8 |

**This proves the SQL logic is equivalent. It does not prove the files
execute on a Databricks SQL warehouse** — different engine, different
parser, different runtime. That is what the run below is for.

## How to do the run (Databricks Free Edition)

1. Sign in to Databricks Free Edition and open a **SQL warehouse**
   (Serverless starter warehouse is fine).
2. Upload the 9 Kaggle CSVs to a Unity Catalog volume, e.g.
   `/Volumes/main/kpi/raw/`. Create the schema and volume first if they
   do not exist.
3. Create a notebook, paste `sql/databricks/00_load_raw.py`, adjust
   `CATALOG` / `SCHEMA`, attach the warehouse and run it. Confirm the
   printed row counts match `docs/data_dictionary.md`.
4. Run `01_clean_orders.sql`, then `02_master_table.sql`, then
   `03_kpi_monthly.sql` in the SQL editor, in that order, in the same
   schema.
5. Run `04_reconcile.sql`. **Every row must say MATCH.** If one says
   DIFF, stop and investigate before writing anything up — the likely
   causes are timestamp inference in step 3 or the tie-break note below.
6. Screenshot the reconciliation result and the query history showing
   the three files, save them into `docs/`, and fill in the receipt.

### Two things that can legitimately differ

- **Review average, 4th decimal.** 31 delivered orders have two reviews
  with the same latest timestamp and different scores, so `ROW_NUMBER`
  breaks the tie arbitrarily (`docs/escalation-log.md`, E4). The
  reconciliation compares to 2 decimals (4.16) for that reason. Order
  counts and revenue must match exactly.
- **On-time comparison.** The estimate is midnight, so a delivery later
  on the promised day counts as late. The port compares full timestamps
  to preserve that. Changing one side to `to_date()` moves the rate.

## Run receipt — fill in only after a real run

| Field | Value |
|---|---|
| Date run | _not run_ |
| Databricks edition / workspace | _not run_ |
| SQL warehouse name and size | _not run_ |
| Catalog.schema | _not run_ |
| Files executed | `01_clean_orders.sql`, `02_master_table.sql`, `03_kpi_monthly.sql` |
| master_orders rows | _not run_ (expected 99,441) |
| Revenue | _not run_ (expected R$ 15,422,461.77) |
| Reconciliation | _not run_ (expected 11/11 MATCH) |
| Screenshot | _not saved_ — add `docs/databricks-reconciliation.png` |
| Run by | _not run_ |
