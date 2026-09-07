# Book Radar v0.1

Book Radar is the small persistent memory for evidence-led publishing experiments. It records the path from discovery through actual D0/D7/D30/D60/D90 results without performing research, producing a book, publishing, or spending money automatically.

## Storage and invariants

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
