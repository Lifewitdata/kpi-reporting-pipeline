# Business insights — in plain language

All numbers below are from the executed pipeline outputs
(`data/processed/master_orders.csv`, `kpi_monthly.csv`,
`category_monthly.csv`, `delivery_by_state.csv`). Period: Sep 2016 –
Oct 2018; trend reads use full months Jan 2017 – Aug 2018 only
(see `kpi_definitions.md` for why the edge months are excluded).

## 1. Late delivery is the single biggest satisfaction lever

On-time orders average **4.29 stars**; late orders average **2.57 stars**
— **40.2% lower**. Only 8.1% of dated delivered orders are late, but
those 7,669 orders drag the overall average down disproportionately.
By delay bucket: 0–3 days 4.48, 4–7 days 4.40, 8–14 days 4.31,
15–30 days 3.97, **30+ days 2.25**. The damage is not gradual — it
cliffs after 30 days. Recommendation: flag any order approaching
30 days for proactive customer contact before it becomes a 1-star
review, rather than treating all late orders the same.

## 2. Revenue peaks in November 2017 — and the peak strains delivery

November 2017 is the highest-revenue full month at **R$ 1,153,528.05**,
up **+53.6%** on October 2017 (R$ 751,140.27) on 7,544 orders. That same
month has the weakest on-time rate among high-volume months (85.7%)
and average delivery jumps to 15.16 days, with average review falling
to 3.99 — the lowest full-month score in 2017. Recommendation: plan
peak capacity (carrier / seller SLAs) ahead of the November peak
instead of absorbing it, because the peak currently buys revenue at
the cost of satisfaction.

## 3. No single category carries the business

Top category by delivered item price is **health_beauty at
R$ 1,233,131.72 — only 9.3%** of delivered item revenue. The top 10
categories together are 62.4%. The next four: watches_gifts
R$ 1,166,176.98, bed_bath_table R$ 1,023,434.76, sports_leisure
R$ 954,852.55, computers_accessories R$ 888,724.61. Recommendation:
category strategy should be portfolio-wide (assortment, seller
performance) rather than a bet on one hero category; a problem in
any one category cannot explain a company-level revenue move.

## 4. Delivery is a geography problem, not a uniform one

São Paulo is 42.0% of delivered orders (40,501) with the fastest
average delivery among large states (8.76 days, 94.1% on time).
Contrast Bahia: 3,256 orders, 19.34 days, 85.96% on time, 3.93 stars;
Ceará: 21.27 days, 84.68% on time; Maranhão: 21.57 days, 80.33% on
time, 3.83 stars. Recommendation: set state-level delivery promises
and carrier targets instead of one national promise — the same
promise is easy in São Paulo and routinely missed in the North and
Northeast, and customers there rate accordingly.

## 5. Cancellation is not the problem; the average hides a split

Overall cancellation is only **0.63%**, and average review is 4.16 —
both look healthy. But 57.8% of reviews are 5 stars while 11.5% are
1 star, and the 30+ day delivery bucket scores 2.25. Recommendation:
report the 1-star share and the 30+ day share alongside the averages
in the weekly pack. Averages alone would tell leadership everything
is fine while a visible minority of customers has a bad experience.

## What this dashboard does not prove

- These are associations, not causal estimates: late orders may also
  be remote, heavy, or multi-seller orders. The next step before
  acting on Insight 1 would be a check by state and category.
- Revenue is delivered-order payments only (see KPI definitions);
  it is not gross merchandise value including canceled orders.
- The data ends in Oct 2018; nothing here describes current Olist
  performance.
