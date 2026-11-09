# Operations runbook — weekly KPI refresh

Owner: the analyst on reporting duty. Audience: whoever has to keep the
weekly pack running, including someone who did not build it.

**Scope.** One command rebuilds the reporting tables from the raw Olist
CSVs, runs the quality checks, and writes the four CSVs Tableau and the
spreadsheet read. Runtime measured on this machine: ~30 seconds for the
full run (2026-11-09), of which most is loading the 1M-row geolocation
file.

## Weekly refresh — steps

1. Confirm the raw inputs are present: the 9 CSVs listed in
   `docs/data_dictionary.md` in `data/raw/`. They are git-ignored, so a
   fresh clone has none — download from Kaggle first
   (https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
2. From the repository root:
   ```bash
   pip install -r requirements.txt   # first time only
   python src/pipeline.py
   ```
   This runs `sql/01_clean_orders.sql` → `02_master_table.sql` →
   `03_kpi_monthly.sql`, then `sql/04_data_quality_checks.sql`, then
   exports `data/processed/`. The checks are SELECT-only and cannot
   change data.
3. Read `logs/pipeline_run.log` from the bottom. A healthy run ends with
   `Exports: {'master_orders': 99441, 'kpi_monthly': 25,
   'category_monthly': 1273, 'delivery_by_state': 27}`.
4. Check the row counts against the table below and scan for `WARNING`.
5. Refresh the consumers: in Tableau, refresh the extract / data source
   for the workbook in `dashboard/`; rebuild the spreadsheet with
   `python src/build_spreadsheet.py` (see `spreadsheets/README.md`).
6. Only then publish the weekly pack. If a check warned, follow the
   table below **before** publishing.

## What each status means

- **PASS** — the check's condition holds. Nothing to do.
- **INFO** — a known, documented property of this extract. Not a
  failure; do not "fix" it. Details in `docs/escalation-log.md`.
- **WARNING** — a condition that should hold does not. The pipeline
  keeps going (a bad refresh must be visible, not silent), so a WARNING
  in the log is the signal, not an exception. **Do not publish** until
  it is explained.
- The run raises and stops only if `master_orders` comes back empty —
  then there is nothing to report and no export happens.

## Checks and the action for each

| Check | Expected here | If it warns, do this |
|---|---|---|
| `clean_orders_row_count` | PASS, 99,441 | Raw `orders` changed or a null `order_id` appeared. Compare the raw file row count (pandas, not `wc -l`) with the log; re-download if the extract is truncated. |
| `master_orders_row_count` | PASS, 99,441 | A join fanned out or dropped rows. Check `02_master_table.sql`: payments and items must be aggregated *before* joining, and only the latest review kept. |
| `master_null_order_id` | PASS, 0 | Upstream sent orders without a key. Quarantine those rows, ask the data owner, do not publish order counts. |
| `master_duplicate_order_id` | PASS, 0 | Grain broken — almost always a review or payment join. Find the offending order with a `GROUP BY order_id HAVING COUNT(*) > 1` on `master_orders`, fix the join, re-run. |
| `negative_revenue_delivered` | PASS, 0 | Refunds or credit notes entered the extract. Revenue is defined as delivered-order payments; decide with finance how to treat negatives before publishing. |
| `negative_payment_value` | PASS, 0 | Same as above, one step upstream. |
| `delivered_missing_delivery_date` | INFO, 8 | Known: excluded from delivery KPIs, not imputed (E2). If the number grows, raise it as an upstream capture gap. |
| `kpi_monthly_months` | PASS, 25 | Zero months means the master table is empty upstream; check the previous two checks. A *different* count means the extract's date range changed — re-check the `is_full_month` window in `03_kpi_monthly.sql` before reading trends. |
| `surplus_review_rows` | INFO, 551 | Known: 551 surplus rows across 547 orders, handled by `review_latest` (E1). Confirm `master_duplicate_order_id` is still 0. |
| `tied_latest_review_orders` | **WARNING, 31** | Open item E4. Expected to warn on this extract. Confirm the value is still 31 and that the review average still rounds to 4.16; if it changed materially, hold the review KPI and escalate per E4. |
| `delivered_without_payment` | INFO, 1 | Known: order `bfbd0f9b…`, Sep 2016, R$ 0 revenue (E3). If it grows, revenue is understated — raise with finance. |
| `load_<table>` (9 checks) | PASS | The CSV row count (read by pandas) differs from the loaded table. Usually a truncated or re-downloaded file, or a quoting problem. Re-download that file and re-run. |

## Common failures

- **`FileNotFoundError: Missing raw file`** — `data/raw/` is empty. It
  is git-ignored on purpose. Step 1 above.
- **`master_orders is empty; refusing to export`** — the SQL ran against
  an empty database. Re-run the whole pipeline, not just the SQL files.
- **A number changed but no check warned** — the checks cover grain,
  keys, signs and load counts, not business plausibility. Compare
  `kpi_monthly.csv` with the previous week (`git diff`) before
  publishing; revenue for this extract is R$ 15,422,461.77.
- **Review average moved slightly between runs** — see E4; tied latest
  reviews are picked arbitrarily. Below the second decimal it is noise.

## After a refresh

- Commit the regenerated `data/processed/*.csv` so the repo and the
  dashboard agree, and note the run date in the commit message.
- If a WARNING was explained rather than fixed, add it to
  `docs/escalation-log.md` with the evidence check name.
- Re-run ad-hoc answers if a stakeholder is waiting on them:
  `python src/run_adhoc.py`.
