# Portfolio Growth Dashboard Spec V1

Read-only view: `./bin/abvx book-radar report growth --as-of YYYY-MM-DD --json`. No additional UI, universal score, revenue forecast or scheduler.

Primary metrics: ROLLING_30D_ROYALTY (EUR), ROLLING_30D_PAID_UNITS, ACTIVE_COMMERCIAL_LINES, ROYALTY_BY_LINE, ROYALTY_PER_NEW_KDP_SLOT, MONTH_OVER_MONTH_ROYALTY_CHANGE. Owner target €1,000/month is displayed explicitly as a non-forecast. Output/candidate count is not the success KPI.

Rolling window is inclusive `[as_of−29 days, as_of]`; previous comparison is the adjacent non-overlapping 30 days. MoM is an absolute EUR delta between those windows, explicitly labelled rather than silently claiming calendar-month performance. It requires exact, complete window observations in both periods. Free downloads and KENP are excluded from paid units; canonical estimated royalties may include KENP royalties, retaining ESTIMATE/PROVISIONAL statuses.

An active commercial line has observed paid units >0 in the exact rolling window. Missing line coverage makes the total active count UNKNOWN; a known positive lower bound is shown separately. Structural planned lines are not active. The complete portfolio aggregate includes unassigned canonical titles, which are listed explicitly; line totals only include registered membership.

The slot denominator counts new first submissions per title-format in the same 30d window, across formats; creation is separately scarce and is not double-counted as another new release. It requires complete historical ledger coverage; missing coverage → UNKNOWN. Royalty-per-slot is descriptive portfolio efficiency, not attributed revenue caused by those submissions. Zero slots produce UNKNOWN rather than infinity. Creation and submission usage remain separate weekly quota views.

Lifetime totals are as observed, with all member windows required to agree; snapshot dates/statuses/evidence are retained. Latest snapshots do not imply current-day account evidence. A 90d or calendar-September observation cannot be rescaled into rolling 30d. No synthetic daily interpolation, missing-zero fill or currency conversion.

Current retained observations as of report 2026-10-07: rolling 30d and MoM UNKNOWN; slot history UNKNOWN. Stoic lifetime observed aggregate is 111 paid units / €505.09 through 2026-10-02 (estimated royalty), KENP 66 for 2026-09-01–2026-09-30. This is past evidence, not a monthly target run rate. Good Dogs has three live titles, but Authority outcome coverage is missing, so series totals and read-through remain UNKNOWN.

To unlock numeric KPIs, owner may provide evidence-backed exact rolling-window orders/royalties, prior-window comparison, applicable KENP and reconciled slot history through the existing outcome/evidence intake. This task did not access KDP or gather fresh account evidence.
