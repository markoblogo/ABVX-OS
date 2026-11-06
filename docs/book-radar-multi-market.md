# Multi-Market Product Opportunity Radar V1

Implemented 2026-10-08, after the [OSS/source-access audit](../book-radar/audits/multi-market-oss-reuse-v1/RESEARCH_REPORT.md). Cost class: NORMAL. This is an extension of the existing `./bin/abvx book-radar` interface. Amazon discovery, canonical records, scoring versions, outcome reports and production gates remain in place.

## Architecture and reuse

The existing Radar supplies JSON persistence, conflict-safe IDs, schema validation, catalog/performance links and CLI/report entrypoints. `book_radar_wide.py` supplies the retained-evidence/freshness/origin workflow; active discovery V5 supplies the evidence-band-before-effort decision principle. The new `book_radar_markets.py` adds three small manual providers and an Amazon bridge, one common opportunity contract, comparison, strategy and weekly proposals. No replacement database, app, scheduler, model call, scraping client or paid dependency was added.

Canonical `book-radar/state.json` is read only. Optional operational records for all four markets share `book-radar/multi-market/state.json`; its retained proof cache is `book-radar/multi-market/evidence/`. Both are ignored by Git. Intentional example bundles and reports are separate. A missing overlay is valid and existing Amazon reports work without it. Imports are bounded to 1,000 opportunities, 5,000 observations, 16 MiB JSON/proof files and 64 MiB retained proof per import.

## Working sources and manual limits

The working adapters validate and import supplied authorized records; they do **not** collect data from marketplace accounts. Source accessibility was researched in the preceding audit, but no live Etsy/Udemy/Kickstarter account data was obtained or remote provider authenticated for this implementation.

| Market | Permitted input path | Representable information | Current limitation |
|---|---|---|---|
| Amazon | Existing Radar/KDP observations, manual retailer evidence, authorized owner exports | Demand proxies, competition, paid orders/revenue, price/reviews, trends, delivery country | Existing workflows remain; competitor sales and unavailable keyword volume stay unknown. EN content requires Amazon.com + US delivery; FR requires Amazon.fr + FR delivery. |
| Etsy | Manual [Marketplace Insights](https://www.etsy.com/seller-handbook/article/1404564905677), authorized owner exports; licensed eRank/analytics exports when their license permits retention | Keyword searches/interest, listings, categories, price, format, seasonality/emerging terms, activity, paid owner outcomes | No verified public Insights API. Own orders are different from competitor estimates. [API terms](https://www.etsy.com/legal/api/) require express written analytics authorization; an app key is insufficient. |
| Udemy | Manual instructor [Marketplace Insights](https://teach.udemy.com/publishing/using-your-dashboard/) and authorized owner exports | Topic/language search demand, course supply, displayed revenue indicators, ratings, quality gaps, emerging subjects | No admitted Insights API. The previous [Affiliate API](https://www.udemy.com/developers/affiliate/) access ended 2025-01-01. Displayed revenue is labelled as reported/estimated according to its actual definition, never invented course sales. |
| Kickstarter | Authorized retained manual campaign observations and creator records | Category/format, backers, pledged, goal, status/timing, comparable supply, audience/fulfillment notes | No live collector or third-party scraped dataset admitted. Campaign funding is crowdfunding evidence, not retail sales or profit. Public visibility does not establish retention permission. |

`book-radar markets providers` lists each provider's precise metric names. A metric being supported by the contract does not mean the platform provides it. Missing, blocked or unavailable providers supply explicit availability and MISSING values; other providers still work. Numeric snapshots do not automatically establish trend dynamics: supply dated comparable windows and a labelled interpretation.

Official manual observations and owner exports retain their platform as upstream origin. Third-party records use `LICENSED_ANALYTICS` / `LICENSED_EXPORT`, record the actual upstream source and remain ESTIMATED or INFERRED. Retaining a record requires an operator-declared access/retention basis and `RETAINED_AUTHORIZED`; the declaration is not a legal clearance by Radar. Keep expired/withdrawn access out of the input and delete retained files when required by its terms; there is no automatic retention-expiry manager in V1. Automated Etsy access, if later authorized, must separately implement the documented rolling-24-hour quotas and applicable storage/display requirements.

## Evidence and explainable recommendations

An opportunity is a topic + buyer + buying job + language + country, with explicit keyword and format proposals. Related observations are deliberately attached to the same ID after semantic review. Exact normalized clusters deduplicate; different buyers/jobs remain separate. V1 does not infer topic equivalence or extract keywords from prose.

Every observation records source URL, upstream URL, query, capture date, data period, language/country/buyer/job/format, availability, limitations, metric units and status. Non-missing metrics require a retained local proof file and SHA256. Relative paths must remain inside the bundle/cache; hashes are checked at import and report load. Unknown is `MISSING` + null, never zero. VERIFIED means observed as defined by the source, not independent verification of a platform's estimator. Estimated platform/vendor revenue must stay ESTIMATED.

Demand, competition weakness and commercial validation are reasoned 1–5 assessments tied to allowed metric keys. These assessments remain INFERRED even when their inputs were observed. Format fit, reusability and risk are operator assessments; higher risk score means safer/lower risk. Positive commercial qualification requires an observed numeric paid indicator, fresh matching evidence and complete effort/cost estimates. Search interest, listings, ratings or estimated sales alone cannot pass it. Conflicting observations take the conservative minimum; observed zero cannot become positive demand.

The ranking policy is `multi-market-commercial-bands/v1`: STRONG, then MODERATE, then insufficient evidence; within an eligible band, lower estimated total effort and smaller first steps come first. STRONG/high confidence requires multiple upstream origins; Amazon requires two origins even for qualification. Licensed Amazon research can supplement a separately verified retailer/delivery context only with matching domain/country declarations; these declarations and all vendor metrics remain estimates. A vendor reproducing Amazon data has Amazon as upstream origin and does not provide a second origin. No bonus is added for platform count. Costs remain visible in their original currency; V1 does not convert currencies or pretend unknown margin is net commercial value. Existing Amazon scoring models are not modified.

Freshness defaults are 30 days for Amazon/Etsy/Udemy and 180 days for Kickstarter. They are local research thresholds, not assertions about platform retention rights. Both capture date and data-period end matter. An unknown period, old period or future capture cannot qualify. Evidence must match buyer/job/language/country and proposed format. Campaign commercial qualification additionally requires observed successful status and pledged >= positive goal in the same currency.

The comparison report shows all markets, raw observations, missing data, reasons, confidence, formats, effort/cost, catalog context and tracking. It selects an initial market/format from eligible proposals. Secondary formats require their own relevant paid evidence and independent upstream groups; otherwise SINGLE_MARKET or RESEARCH_ONLY. Any expansion still requires actual initial-product validation, format/rights review and unit economics. Kickstarter is always a feasibility proposal before a defined distinct project, funding, audience and fulfillment review.

## Catalog, policies and history

Use `--amazon-opportunity ID` for an existing opportunity or `--catalog-product ID` for a canonical product/portfolio product. Existing title metadata, raw historical actuals and their periods/status remain visible as context. Amazon performance does not become Etsy/Udemy demand. An existing book is not proposed again as a new Amazon book; another market requires an ADAPTED proposal with its own evidence. Unqualified adaptations can receive a bounded research task.

Rights and dated platform policy/AI reviews are separate gates. Non-Amazon reuse with unknown/enrolled KDP Select status is blocked pending review; V1 uses a conservative check instead of determining derivative-content legality. Udemy requires `STRUCTURED_DEMONSTRATIONS`, not narration alone. Kickstarter requires a new project, positive estimated funding and fulfillment budgets, shipping and audience plans. Policies must be reviewed against current controlling sources; a CLEAR input is an operator conclusion, not automatically inferred from a URL. References: [KDP Select](https://kdp.amazon.com/en_US/help/topic/GD9PMU58BV24QFZ7), [KDP content/AI rules](https://kdp.amazon.com/en_US/help/topic/G200672390), [Etsy creativity](https://www.etsy.com/legal/creativity/), [Udemy quality/AI](https://support.udemy.com/hc/en-us/articles/30999984483607-Course-Quality-Checklist-Use-of-AI), [Kickstarter rules](https://www.kickstarter.com/rules).

Tracking is chronological and append only: ACCEPTED, REJECTED, RESEARCHED, PLANNED, APPROVED, IN_DEVELOPMENT, PRODUCED, PUBLISHED, TESTED and REOPENED. Previously researched/rejected/planned/in-development/produced/published/tested work is suppressed in weekly proposals. Record a reasoned REOPENED to reconsider; even an ALL-market approval cannot bypass a terminal market decision. APPROVED is a recorded owner choice, not an automatic production instruction. Explicit metadata revisions retain their previous version and reason; historical reports use the version applicable on their date.

## Operator workflow

Start with a template, then fill the buyer/job/keywords, format, estimates and actual permitted observation:

```sh
./bin/abvx book-radar markets providers
./bin/abvx book-radar markets template etsy --as-of 2026-10-08 > /private/tmp/etsy-input.json
./bin/abvx book-radar markets template udemy --catalog-product portfolio-product:B0HFTTG5FH --as-of 2026-10-08 > /private/tmp/catalog-input.json
./bin/abvx book-radar markets check /private/tmp/etsy-input.json
./bin/abvx book-radar markets normalize /private/tmp/etsy-input.json
./bin/abvx book-radar markets import /private/tmp/etsy-input.json
./bin/abvx book-radar report markets --as-of 2026-10-08
./bin/abvx book-radar report markets --market etsy --opportunity YOUR_ID --json
./bin/abvx book-radar report weekly --amazon-committed 0 --hours 8 --as-of 2026-10-08
./bin/abvx book-radar markets export /private/tmp/portable-radar.json
```

`normalize` returns the validated normalized contract, not an arbitrary vendor CSV/prose parser. Templates contain unavailable placeholders, not newly researched evidence. Proof paths are relative to the input file; set the exact hash after retaining authorized evidence. Reimporting identical records is safe; changed records under the same ID fail before state writes. Add new dated observation IDs instead of rewriting old evidence. Optional exports include a sibling content-addressed proof folder; protect it as source material.

To track a decision, supply an import-version JSON bundle with empty opportunity/observation arrays and a decision containing `id`, `opportunity_id`, `marketplace` (or ALL), `status`, `date`, `reason`; use `book-radar markets track FILE`. To change a proposal, supply exactly one full existing opportunity and empty observations/decisions; use `book-radar markets revise FILE --reason "Changed scope after review" --as-of YYYY-MM-DD`. Revisions do not replace evidence or reopen decisions automatically.

## Weekly capacity

The report is generated on demand, with no installed weekly automation. It caps **new Amazon books at two per ISO week**, including declared and tracked commitments. `--amazon-committed` must include all already planned/produced books from existing workflows; unknown total means zero additional Amazon proposals. It uses the larger declared/tracked count. This is an owner planning ceiling, not a KDP provider rule.

Default preparation capacity is an explicit 8-hour assumption; override `--hours` to match reality. At most five bounded actions are proposed. Etsy/course milestones and Kickstarter feasibility are optional, at most one eligible action per additional market; no quotas. Unqualified ideas receive a 0.5-hour ESTIMATED research step or no action. Each task includes evidence references, format/language/buyer, estimated effort/cost, hypothesis, validation target and next action. All outputs retain `production_authorized: false`.

## OS ↔ Cortex phase capture

Follow [Book/business exchange rules V1](maintenance/BOOKS_BUSINESS_EXCHANGE_RULES_V1.md). Before a real reviewed market-evidence phase, record UTC start/end, actual elapsed time, active owner effort or UNKNOWN, corrections and separate quality/safety results locally. Earlier implementation work with unmeasured duration/owner effort remains UNKNOWN; do not reconstruct it from file timestamps or turn synthetic checks into a book outcome.

The first verified native-publication cycle is required before the one-phase book pilot and Cortex handoff. Use the existing `AbvxOsProcessOutcome` contract, one workflow/version, opaque stage/workload proof hashes and explicitly selected packets. Manuscripts, titles, private data, raw logs and paths remain local. A returned recommendation is independently checked and retained for review; it is never applied automatically. Missing acceptance proof leaves pilot/transfer pending without changing existing book approval gates.

## Examples, validation and optional work

See [example opportunity report](../book-radar/multi-market/examples/opportunity-report.md), [example weekly plan](../book-radar/multi-market/examples/weekly-plan.md) and [implementation/validation record](../book-radar/multi-market/IMPLEMENTATION_V1.md). Examples are explicitly unresearched, run in an isolated temporary state, and use the real catalog title only as an adaptation hypothesis. They contain no fabricated searches, sales or successful opportunities; no example is imported into operational state.

Optional next increments, each needing actual data/use-case evidence: vendor-specific permitted CSV mappings; catalog adaptation batches after bounded own-market research; lawful performance-event mappings for Etsy/Udemy; RapidFuzz duplicate suggestions after a collision benchmark; Etsy SDK only after written analytics authorization and access/retention/rate-limit qualification. Defer automatic acquisition, currency/margin models, trend calculations and forecasts until valid source data makes them useful. Existing performance remains descriptive; V1 does not automatically rescore or retrain from it.
