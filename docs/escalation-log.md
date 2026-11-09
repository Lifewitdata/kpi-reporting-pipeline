# Escalation log — what I fixed, what I raised, and the evidence

Every entry below is a real issue in this dataset, found by the EDA
notebook and now checked on every refresh by
`sql/04_data_quality_checks.sql`. Values were re-verified on
2026-11-09 by running `python src/pipeline.py` end to end.

**How escalation works here.** This is a single-analyst project on a
public dataset, so there is no live incident channel. The owner roles
below are the roles a data issue of that type would go to, and
"escalated" means the decision was written down and left open for that
owner rather than silently resolved in code. Severity: **HIGH** = the
number on the dashboard would be wrong; **MEDIUM** = correct numbers,
ambiguous or incomplete input; **LOW** = cosmetic / immaterial.

---

## E1. Duplicate reviews — 551 surplus rows across 547 orders

- **Severity:** HIGH if unfixed (review score would be double-counted
  and the master table would fan out past one row per order).
- **Evidence:** `surplus_review_rows = 551` (INFO) and
  `master_duplicate_order_id = 0` (PASS) in
  `04_data_quality_checks.sql`. The 551 is the number of *surplus*
  review rows: 99,224 review rows, 98,673 distinct orders, 547 orders
  holding more than one row. Earlier docs said "551 orders"; corrected.
- **Fixed by me:** the `review_latest` CTE in
  `sql/02_master_table.sql` keeps one review per order using
  `ROW_NUMBER()` ordered by `review_creation_date DESC`. The master
  grain check passes, so the fix holds.
- **Escalated / excluded:** nothing excluded — all 547 orders keep a
  review. The tie case that this rule does *not* settle is raised
  separately as E4, not buried here.

## E2. Delivered orders with no delivery date — 8 orders

- **Severity:** MEDIUM (delivery KPIs would be wrong if these were
  imputed or counted as late).
- **Evidence:** `delivered_missing_delivery_date = 8` (INFO) in
  `04_data_quality_checks.sql`; `delivery_days` and `on_time_flag`
  stay NULL for them in `sql/01_clean_orders.sql`.
- **Fixed by me:** nothing imputed. `AVG()` ignores NULL, so these 8
  are outside the delivery KPIs. The on-time denominator is 96,470
  dated delivered orders, not 96,478 delivered orders.
- **Escalated / excluded:** excluded from on-time rate and average
  delivery days, kept in revenue and order counts. Raised to the
  operations owner as an upstream data-capture gap: status says
  delivered but the customer delivery timestamp never arrived. The
  decision to *not* impute is documented in `docs/kpi_definitions.md`
  so a future refresh does not quietly fill them with the estimate.

## E3. Delivered order with no payment row — 1 order, R$ 0 revenue

- **Severity:** LOW (1 order, immaterial to totals) but a real
  reconciliation trap.
- **Evidence:** `delivered_without_payment = 1` (INFO) in
  `04_data_quality_checks.sql`. Order
  `bfbd0f9bdef84302105ad712db648a6c`, Sep 2016, delivered, items worth
  R$ 134.97 + R$ 8.49 freight, no row in `order_payments`.
- **Fixed by me:** `COALESCE(p.payment_value_total, 0)` in
  `sql/02_master_table.sql` gives it R$ 0 revenue instead of dropping
  the order. That is why `kpi_monthly` shows R$ 0.00 for 2016-09.
- **Escalated / excluded:** not imputed from the item price — revenue
  is defined as payments, so inventing a payment would break the
  definition. Raised to the finance owner to confirm whether the
  payment record is genuinely missing upstream. Documented so the
  R$ 0.00 month is not reported as a pipeline bug. Note 3 other orders
  have payments that sum to R$ 0, so a `payment_value_total = 0`
  filter would find 4 orders, not this 1 — the check uses
  `NOT EXISTS` against the payment table deliberately.

## E4. Tied latest reviews — 31 delivered orders, OPEN

- **Severity:** MEDIUM (the published average review score is not
  fully deterministic).
- **Evidence:** `tied_latest_review_orders = 31` (**WARNING**) in
  `04_data_quality_checks.sql`. These orders have two or more reviews
  with the same latest `review_creation_date` but *different* scores,
  so `ROW_NUMBER()` picks one arbitrarily.
- **Fixed by me:** nothing yet — that is the point of leaving it open.
  The check now raises it on every refresh instead of letting it pass
  silently.
- **Impact measured:** across the 95,832 reviewed delivered orders,
  choosing the lowest or highest tied score moves the average from
  4.1556 to 4.1562 — the headline 4.16 is unaffected either way.
- **Escalated:** to the analytics owner with a proposed rule (keep the
  lowest score on a tie, or the review with a written comment) for a
  decision, since the right choice is a business rule, not a technical
  one. Until decided, the WARNING stays visible and the review KPI is
  reported to 2 decimals, where the ambiguity does not show.
