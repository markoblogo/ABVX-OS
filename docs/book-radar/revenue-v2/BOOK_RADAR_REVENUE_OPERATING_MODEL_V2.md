# Book Radar Revenue Operating Model V2

Status: APPROVED FOR OPERATING USE — owner decision 2026-10-07. Effective 2026-10-07. Cost class: NORMAL.
Owner objective: >€1,000/month royalties with sustained positive month-over-month growth. This is an operating objective, not a forecast or a promised date.

1. **External discovery:** zero portfolio. Existing A–D results remain frozen. New Lane E is PROVEN FORMAT × SPECIFIC ANGLE: repeated externally observed buying object + specific purchase proposition + plausible entry route. Competition scarcity is not an objective. No live discovery scan was executed.
2. **Qualification:** an external-only card is reviewed independently; `freeze_qualification` records QUALIFY/PARK/KILL/INSUFFICIENT_EVIDENCE with a content digest. Lane E requires at least two distinct external paid-activity objects. Evidence quality and entry remain human qualification decisions; repetition does not automatically QUALIFY. The strict card and observation allowlists reject portfolio/capability/outcome fields. Reviewer must also reject ABVX results embedded in free text. No ABVX state is accepted by the discovery API.
3. **Portfolio overlay:** only a frozen, unchanged QUALIFY can enter `post_qualification`. Exactly one launch class and commercial-line potential are recorded here. Qualification is never recomputed from fit, paid performance, production reuse or cost. Owner queue intent is stored separately from a verified independent qualification.
4. **Release review:** format-specific quota, readiness, qualification linkage and the paperback one-slot answer are required. Result is ELIGIBLE_FOR_OWNER_REVIEW or BLOCKED; it never authorizes submission. No weak-slot autofill, scheduler or production action.
5. **Outcome:** canonical title observations feed derived line views and exposure recommendations. Paid signal prompts line-exploit review before broad discovery; consider adjacency, second-title cost, same buyer, cross-sell, seasonality, series economics and cheaper updates. Meaningful paid signal can support a reader-kit → landing page → optional email → related-title recommendation. No infrastructure is built.

Operating principles, not scoring weights: known demand → differentiated object; one audience → related catalog; functional book as product; series/read-through economics; marketing after signal; owned audience after signal; production reuse; seasonal/language clusters; high output alone is not success. Anecdotal incomes are not prediction parameters.

Implementation: `src/abvx_harness/book_radar_revenue.py`; versioned configuration `book-radar/revenue-model-v2.json`; strict `schemas/book_radar_revenue_model.schema.json`. The overlay has its own state file to keep canonical `book-radar/state.json`, historical decisions, outcomes and scoring models byte-identical. Repository validation checks the new model. No new dependencies.

Read-only CLI: `./bin/abvx book-radar report growth --as-of 2026-10-07 --json`.
The six operating documents in this directory define the contracts; [verification evidence](VERIFICATION_V1.md) records test results and limitations. Existing discovery/qualification adapters and historical scores are retained for compatibility; they are not silently reclassified as this new zero-portfolio contract.

Owner correction supersedes the original future-LitRPG instruction: **Good Dogs of the Apocalypse is a complete LIVE three-book LitRPG series, EXISTING SERIES_BET — ALREADY LAUNCHED.** Source archive `/Volumes/Work/books archive/GD` was inspected only for file presence; owner reaffirmed Amazon LIVE. It belongs to outcome/portfolio intelligence, with further production/extension HOLD. There is no future Book 1/2/3 release queue item or duplicate LITRPG_SERIES line.

Owner model-review gate completed. The two legacy full-suite failures are KNOWN LEGACY FAILURES, NON-BLOCKING FOR REVENUE V2. Historical evidence, policy state and assertions remain unchanged.

Current priorities: owner manual C01 paperback submission after weekly reset; Carmilla EXPLOIT candidate next, with separate production authorization; Good Dogs outcome only / extension HOLD; exploit eligible existing original-IP catalog through D2D independently of scarce new KDP paperback slots. D2D eligibility and distribution execution remain separate checks; this acceptance records strategy and performs no external write.

Next commercial objective: observable paid outcomes and increasing rolling 30d royalties. No broad Market Discovery scan is triggered by model implementation or acceptance. The >€1,000/month target with sustained positive MoM growth has no forecast date.

Next operating gate: OWNER MANUAL C01 PAPERBACK SUBMISSION AFTER WEEKLY QUOTA RESET, with quota and title checks. Acceptance is not evidence of reconciled capacity or verified qualification; existing checks remain visible. Carmilla production needs separate authorization.
