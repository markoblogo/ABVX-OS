# Book Radar v0.1

## Active discovery policy

For new searches, read [Book Radar discovery](book-radar-discovery.md) first.
The active v5 strategy ranks evidence-backed commercial potential before
production effort across fiction, business and other book markets. Historical
run instructions and scoring models do not override this policy.

For new retail research, follow [market context policy V1](book-radar-market-context-v1.md):
English content uses Amazon.com with US delivery; French content uses Amazon.fr
with France delivery. Verify the visible country even in an unsigned browser.
Historical or mismatched contexts cannot substitute for the target market.

Book Radar is the small persistent memory for evidence-led publishing experiments. It records the path from discovery through actual D0/D7/D30/D60/D90 results without performing research, producing a book, publishing, or spending money automatically.

## Storage and invariants

### V2 observation and attribution (Phase 2)

The accepted Outcome Foundation is extended by a prospective production admission
gate: every new Radar product requires a frozen experiment contract or an explicit
OWNER waiver. Existing products and partial historical hypotheses are preserved;
unproduced historical candidates require a new contract when promoted to a product.
Generic imports and product recording enforce the same gate. No scoring or ranking
weights change.

See [the Phase 2 contract](../book-radar/audits/observation-attribution-v1/OBSERVATION_ATTRIBUTION_CONTRACT_V1.md),
[data observability](../book-radar/audits/observation-attribution-v1/DATA_OBSERVABILITY_V1.md)
and [search snapshot protocol](../book-radar/audits/observation-attribution-v1/SEARCH_OBSERVATION_PROTOCOL_V1.md).
`book-radar report cards`, `report funnel` and `report series` accept `--as-of YYYY-MM-DD`
and `--json`. New product plus contract is an atomic `book-radar import` bundle;
later evidence uses `book-radar attribution-import`. These commands do not collect
retailer data, create schedules or write externally. Unknown upstream stages block
failure attribution, and catalog sales do not establish matched-reader read-through.

- Canonical state: `book-radar/state.json`.
- Existing-book catalog imports: `book-radar/catalog-imports/` using `book-radar-catalog/v1`.
- Immutable scoring definitions: `book-radar/scoring-models/<id>.json`.
- Intentional source imports: `book-radar/imports/`.
- Stable IDs are unique within each record type. Re-importing identical records is safe; conflicting reuse of an ID fails closed.
- Predictions remain on opportunity evidence or product records; observed results are append-only `actuals` snapshots.
- A scoring-model ID cannot be overwritten. Changed definitions require a new ID/version.

Production status vocabulary is `DISCOVERED`, `SHORTLISTED`, `SELECTED`, `RESEARCHING`, `DRAFTING`, `EDITING`, `PACKAGING`, `KDP_SUBMITTED`, `LIVE`, `PAUSED`, and `ABANDONED`. Format-specific detail belongs in `status_note` and `transitions`.

## Commands

```text
./bin/abvx book-radar import book-radar/imports/radar-native-2-opportunities.json
./bin/abvx book-radar catalog-import book-radar/catalog-imports/human-backup-plan.json
./bin/abvx book-radar new-run --file /path/to/run.json
./bin/abvx book-radar shortlist --file /path/to/decision.json
./bin/abvx book-radar decide --file /path/to/decision.json
./bin/abvx book-radar product --file /path/to/product.json
./bin/abvx book-radar launch --file /path/to/launch.json
./bin/abvx book-radar actuals --file /path/to/D7.json
./bin/abvx book-radar calibrate --file /path/to/calibration.json
./bin/abvx book-radar report pipeline
./bin/abvx book-radar report experiments --json
./bin/abvx book-radar report backlog
./bin/abvx book-radar export /path/to/book-radar-export.json
```

Each `--file` command accepts one JSON record or an array. Record links are checked before state is atomically replaced. Import/export is structured JSON; no manual prose parsing is required for future runs.

## Portfolio Similarity Gate

`portfolio_products` stores normalized existing-book theses; `similarity_results` stores comparisons and dimension-level evidence. Similarity is assessed across buyer, JTBD, trigger, promise, format, information architecture, search intent, audience, and differentiation. Buyer job and promise receive the largest weights; titles are deliberately excluded from scoring.

Supported classifications are `NOVEL`, `EXISTING_PRODUCT_MATCH`, `ADJACENT`, `REPACKAGE_CANDIDATE`, and `CANNIBALIZATION_RISK`. A high-confidence `EXISTING_PRODUCT_MATCH` or `REPACKAGE_CANDIDATE` is not production-eligible and routes to `EXISTING_PRODUCT_AUDIT`. `ADJACENT` remains eligible with a warning. This gate records a bounded comparison; it is not a recommendation engine.

Future catalog records should be supplied as `book-radar-catalog/v1` JSON and imported with `catalog-import`. The boundary is ready for a structured KDP export, but this version does not scrape or manually reconstruct the rest of the catalog.

## Imported baseline

- PMP Radar-native #1: one selected product, KDP submitted, actuals unavailable.
- Asset Radar V1: minimum reliable decision set (winner, runner-up, non-KDP wildcard). The 36-row Markdown scan was not normalized because its composite cells do not cleanly preserve all core fields.
- Radar-native #2: all 120 native structured opportunities, evidence, reproducible scores, screening decisions, top three, and winner. Its winner remains unproduced and unauthorized.

Calibration records should compare predicted ranges with checkpoint actuals, identify systematic score error, and propose a new scoring-model version. They must never mutate the model used by an earlier run.

## Visual/reference Product Quality Gate

Factual QA, technical PDF/EPUB preflight and KDP package validity do not establish commercial product quality. Visual/reference books receive a separate advisory gate covering buyer fit, JTBD delivery, paid value, information density, perceived value, editorial enrichment, prior-knowledge leverage, format fit, template fatigue and page purpose. Ordinary pages with very low usable-area fill or an isolated, obviously groupable entry are flagged; title pages, section openers and deliberate teaching spreads may be explicitly excluded. A failed product-quality gate blocks a KDP-ready claim without changing Radar's global opportunity-scoring weights.

Production may return calibration signals without changing the scoring model: `PRODUCT_THESIS_STRENGTH`, `PRODUCT_QUALITY_REWORK`, `HUMAN_PRODUCT_GATE_REQUIRED`, `PRODUCTION_REWORK_MINUTES`, `TECHNICAL_FALSE_POSITIVE`, and `PRODUCT_FALSE_POSITIVE`. Radar retains these as evidence for later analysis; it does not turn them into automatic recommendations or retroactively rescore an opportunity.

## KDP report semantics and retained account evidence

Orders reports measure processed units/operations. Record **All, Paid and Free separately**, with the exact reporting period and eBook/print split. A free download is not a paid sale. A zero must come from an observed title row; an absent title or inaccessible report remains UNKNOWN.

Royalties Estimator measures estimated money, including separately reported KENP royalties. Preserve currency, period, estimate status and any reconciliation discrepancy. It is not a payment statement or net profit. KENP counts pages read, not purchases, unique readers or completed books. Do not infer a new paid sale from a change in the monetary estimate.

Use matching title identities, reporting windows and filters before comparing operations with money. Lifetime is the primary portfolio view; recent windows are overlays. Retain the displayed dates even if a generic UI limit label contradicts the selected window. Capture raw evidence separately from normalization and interpretation.

The authenticated Safari capture on 2026-10-02 retained all 34 current titles: [report definitions and limitations](../book-radar/runs/kdp-decision-audit/2026-10-02/README.md), [normalized observations and raw references](../book-radar/runs/kdp-decision-audit/2026-10-02/snapshot.json). The [decision-system audit](../book-radar/audits/decision-system-v1/BOOK_RADAR_DECISION_SYSTEM_AUDIT_V1.md) preserves historical-only titles separately. Owner-approved [Outcome Foundation Phase 1](../book-radar/audits/outcome-foundation-v1/BOOK_RADAR_V2_OUTCOME_FOUNDATION_IMPLEMENTATION_V1.md) now links these observations to canonical records; changes to scoring and candidate selection remain unauthorized.

Read-only reports: `book-radar report outcomes`, `cohorts`, `checkpoints`, and `calibration`, with optional `--as-of YYYY-MM-DD --json`. The [observation contract](../book-radar/audits/outcome-foundation-v1/BOOK_RADAR_V2_OBSERVATION_CONTRACT_V1.md) documents append-only `outcome-import`, explicit UNKNOWN/zero semantics, dates, evidence, applicability, and optional forward hypotheses. Reports calculate descriptive cohorts from canonical actuals; they do not grant publication or model-change authority.

## Manual evidence collection

Use `./bin/abvx radar observe --due`, then `./bin/abvx radar observe <experiment-id>`, manually collect and validate/record the packet, and run `--status`. For KDP submission events, the due report first asks `CONFIRM_LIVE_STATUS` for each format; commercial checkpoints start from the first confirmed LIVE date. The current book-level checkpoint engine uses the earliest supported format LIVE date while the launch record preserves each format's own date. [Canonical runbook](../book-radar/audits/evidence-collection-v1/BOOK_RADAR_EVIDENCE_COLLECTION_RUNBOOK_V1.md) and [operator CLI instructions](../book-radar/audits/evidence-collection-v1/BOOK_RADAR_EVIDENCE_COLLECTION_CLI_V1.md) preserve exact/late/approximate timing, missing evidence and the frozen controlled T7/T14 interpretation gate. No schedules or collectors are installed.

## Revenue operating model V2

[Multi-Market Radar V1](book-radar-multi-market.md) extends the same CLI with authorized manual Etsy/Udemy/Kickstarter inputs, market-specific comparison, catalog adaptation review and weekly proposals. Amazon discovery/outcomes remain intact; no production or publication is triggered.

[Operating model and boundary contracts](book-radar/revenue-v2/BOOK_RADAR_REVENUE_OPERATING_MODEL_V2.md) add external-only Lane E, a post-qualification commercial-line overlay, manual quota arbitration and derived revenue views. Use `./bin/abvx book-radar report growth --as-of YYYY-MM-DD --json`. The [current owner queue](book-radar/revenue-v2/CURRENT_RELEASE_QUEUE_V1.md) is C01 → Carmilla; Good Dogs is a complete live trilogy under observation, with extension HOLD. No production, submission or ads are authorized by these reports.
