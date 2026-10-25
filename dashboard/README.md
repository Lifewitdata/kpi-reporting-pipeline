# Dashboard

Workbook: `Olist_KPI_Reporting_Advanced.twbx` (in this folder),
published on Tableau Public at
https://public.tableau.com/app/profile/isfaque.ansari5273/viz/Olist_KPI_Reporting_Advanced/ExecutiveSummary

Screenshots: `screenshots/executive_summary.png` and
`screenshots/deep_dive.png`.

The workbook is built from the processed tables in
`../data/processed/` using the separate Tableau Build Pack guide
(local-only, not in this repo — see the delivery note). That guide
gives the exact sheets, calculated fields and dashboard layout for:

- Page 1 — Executive Summary (KPI cards, monthly revenue trend,
  filters: year, state; category filtering is on Page 2, where the
  data is item-grain — see the main README note on filters)
- Page 2 — Deep Dive (Top 10 categories, delivery map by state,
  review score vs delivery delay)
