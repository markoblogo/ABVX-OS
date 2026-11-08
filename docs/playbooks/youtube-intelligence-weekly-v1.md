# YouTube Intelligence weekly and on-demand playbook v1

Cost class: NORMAL. Owner approved the bounded MVP on 2026-10-19. Read-only Google API acquisition, public research and private local records are authorized. No YouTube content/settings/monetization changes, publishing, purchases, paid infrastructure or Framewright development are authorized.

## Scope and reuse

Read current AGENTS.md. Use `bin/youtube-intelligence` (optional local Python environment) or the existing `abvx youtube` CLI route with an appropriately configured interpreter. The adapter reuses `process_learning.digest`, `_write_once`, the existing Draft 2020-12 validator, and `AnalyticsObservation` envelopes. MMR's commercial schemas, method winners and paid-demand labels stay separate. Framewright is optional production context, never a runtime dependency.

Runtime state lives in ignored `.tmp/youtube-intelligence/`. It is private local evidence, not public Git content. Its lifetime depends on the workstation; retain an owner-controlled backup when operating long-term. No Cortex transfer is enabled.

## Before every run

1. Run `./bin/youtube-intelligence context`. Read the baseline, up to three previous accepted reports/analyses, registered hypotheses and evaluation events. Original observations remain dated facts; previous proposals are not findings. Check the current PlayMCP/PocketputerDV backlog with the owner context, without automatically replacing or starting it.
2. Research current primary sources using existing search/browser tools. Record actual UTC start/end and spent research seconds, including failed searches. Budget: 45 minutes maximum; stop earlier when additional discovery is unlikely to improve the owner's decision. There is **no opportunity-count ceiling** and no minimum filler requirement.
3. Apply the approximate 40/40/20 guideline across proven themes, emerging opportunities and creative experiments. Report actual mix and explain material departures; never force ratios or publishing quotas. Proven means evidence from this channel, not generic industry popularity. New market signals are not proven channel demand. Use primary sources and record what each source actually establishes. Search-result popularity is not search-volume evidence.
4. Produce a `youtube-research/v1` packet conforming to `schemas/youtube_intelligence.schema.json`. Titles, hooks, visual and production concepts are English; rationale/report prose is Russian. Each card needs priority, sources with checked timestamps and claim support, lane, format, duration, complexity, hypothesis and primary metric. Use `recommended: false` for retained discoveries outside the concise priority menu; there is no hard count limit on either the discovery set or analyst-selected menu. Use `PARTIAL` when substantive research is missing; do not call an empty/incomplete scan complete merely to activate scheduling. Source checks must be within 72 hours and not in the future. `as_of` is the actual UTC acquisition date.

## Acquire and report

```
./bin/youtube-intelligence run --run-id <unique-safe-id> --research <private-research.json>
```

The command performs official API channel verification, complete uploads-playlist pagination, batched video metadata, 7/28-day channel and **all eligible public uploads** analysis, traffic/format reports and calendar-age windows for recent/tracked uploads. It includes unplanned/spontaneous content. Public, published, non-live content is eligible; inaccessible playlist items are retained as unavailable IDs. Scheduled, private/unlisted and currently live items are excluded. Archived livestreams remain distinct when Analytics identifies them. Budget exhaustion is a failure, never silent catalog truncation. Default budget: 250 calls / 600 acquisition seconds / 30-second request timeout / no automatic retries.

The default end date is UTC today minus three days to allow processing. Keep requested windows and returned day coverage distinct; revenue has its own query so it cannot shorten other reports. Calendar-age windows include the partial publication day in America/Los_Angeles. `age_2d` is **not exact first 48 hours**. Formats use Analytics `creatorContentType`; only confirmed SHORTS are Shorts. VOD is split descriptively below/above 180 seconds, not by an invented orientation measurement. No API classification means UNKNOWN_OR_MIXED. Publication briefs may specify horizontal intent, but Data API does not verify orientation.

Outputs: `started.json`, `acquisition.json`, `analytics-observations.json`, `research.json`, `analysis.json`, `execution.json`, `REPORT.md`. No source run is overwritten. All reports retain raw Analytics response tables and provenance. Empty/suppressed rows are NO_REPORTED_ROWS, never zero. Rendering shows a concise priority menu and refers to all uploads in analysis.json. The assistant must inspect source/window differences, identify comparable weak results, interpret previous hypotheses, and add a concise source-grounded commentary for the owner; deterministic rendering alone is not causal analysis or an autonomous research agent.

`COMPLETE` requires successful acquisition, channel data, and a research packet explicitly marked COMPLETE. `PARTIAL_DATA`/`PARTIAL_RESEARCH`/`BLOCKED` do not pass first-live schedule acceptance. Synthetic fixtures cannot count as live acceptance. Check actual source authenticity, report contents and timestamps, not just the terminal status string.

## Experiment learning

Use `register --file <experiment.json>` before publication. Explicit primary metric, minimum result, observation window and threshold basis are required. A threshold is an owner/analyst proposal, not an empirically established success rule. `event --file <event.json>` records APPROVED, PUBLISHED or CANCELLED. Approval and registration must precede the API-discovered publication timestamp. Bind a published video only with an explicit reviewed ID. Spontaneous uploads remain OBSERVATIONAL_ONLY; never invent prior hypotheses. One upload cannot count as independent successes for several experiments.

Mature registered 7/28-calendar-day windows are evaluated from actual daily API rows. Missing/suppressed/delayed days remain IMMATURE_OR_UNAVAILABLE. SUPPORTED / NOT_SUPPORTED adjudicates the registered numeric prediction, not causality or an entire strategy. Revisions are appended, original hypotheses remain frozen. On each following run read previous source reports and outcomes before recommending follow-ups; preserve failed assumptions. The system does not train model weights or adopt a new research method automatically.

## Studio supplements

For CTR, returning viewers, viewed/swiped away and Studio RPM use a minimized owner export/audit:

```
./bin/youtube-intelligence import-studio --file <typed-packet.json> --evidence <export.csv>
```

This saves hashed evidence as SUPPLEMENTARY_NOT_LIVE_API. Preserve metric definitions, units, exact periods and video scope. The API cannot fabricate these from other metrics. Historical owner-audit imports are not fresh API observations and never pass schedule acceptance. Do not retain tax, banking, browser profiles, credentials or unrelated account information in evidence.

## OAuth setup

Optional dependencies: create `.tmp/youtube-intelligence/runtime` with `python3 -m venv`, then install `requirements-youtube.txt` there through the official registry when network access is available. Core schema validation can use existing `.tmp/book-core-runtime`. Dependencies are not automatically installed by a scheduled run.

Use a separate Google Cloud project; enable YouTube Data API v3 and YouTube Analytics API. Create a Desktop OAuth client and configure consent for the owner. Keep `client.json` and `token.json` exclusively in `.tmp/youtube-intelligence/credentials/`, protected by owner-only permissions. Never paste their contents into chat, Git, reports or logs. Run `./bin/youtube-intelligence auth --monetary` to request the three read-only scopes. It writes a private authorization URL and waits up to five minutes for the loopback callback. The owner grants consent. Without monetary scope the rest can run; revenue is SCOPE_NOT_GRANTED. Verify channel ID during acquisition, not by Google account name. External testing apps may have short-lived refresh tokens; verify consent/publishing status before unattended use, without automatically expanding the app audience.

## Scheduling acceptance and duplicate prevention

Owner directive 2026-11-02 supersedes the older separate-schedule proposal. Use only the existing unified Nantes Radar, daily at 10:00 Europe/Paris, full menu Monday. Do not create a YouTube task or change any saved schedule. The research module does not install or own a scheduler. A healthy monitor is not proof of fresh research or delivery.

At the existing YouTube stage run `bin/youtube-intelligence radar-request`. Its bounded context and research instructions feed the current researcher, which must fetch fresh external evidence and write a `youtube-research/v1` packet. Then use the existing `run` command. Monday target is 10–20 diverse supported ideas, daily 0–3 changes; no filler. Today’s first menu may have up to 10. `radar-menu.json` retains selected supplied candidates and shortfall; this deterministic selector does not discover web trends itself. A missing fresh research provider must remain PARTIAL/BLOCKED, never reuse old ideas as fresh discovery.

Financial evidence: `financial-context.json` joins official video revenue with upload format. Revenue is queried in batches for all eligible uploads; age revenue includes all recent uploads and tracked experiments, plus the top five revenue videos. Geography and traffic sample tracked experiments plus the top five. This prevents financial review from selecting only winners. Missing/suppressed rows remain unknown; retained supplement failures disclose budget/access limits. Raw age revenue supports registered `estimatedRevenue` predictions at 7/28 days only with complete daily coverage. All other uploads remain observational. Do not retrospectively attach a hypothesis by title similarity.

For Studio CSV use `radar-csv --file <csv> --start YYYY-MM-DD --end YYYY-MM-DD`. Keep official exported RPM separate from calculated revenue per 1,000 views, retain source hash and declared period. Import the original proof and typed metric packet using existing `import-studio` for persistent supplements. The CSV adapter never assumes a YPP start or infers Shorts from duration. Compare post-YPP periods only after the effective YPP date is evidenced. Data lag is three days by default; last two days shown in Studio may still be processing.

The researcher must read prior hypotheses, failed predictions and financial evidence before choosing the next menu. Record observed facts, derived ratios, commercial hypotheses and unknowns separately; reject borrowed competitor RPM. Propose one evidence-bound method adjustment per week, retain counterevidence and avoid causal claims from one upload. Report revenue per actual owner production hour only when hours/costs are measured; otherwise UNKNOWN. Briefs include a dated publication window, original payoff, source claims, scene plan, Framewright assembly, effort estimate, rights risks, stop criteria and prospective 7/28-day evaluation proposal. These are production proposals, not publication authority.

## Retention

Own authorized historical Analytics statistics may be retained subject to active authorization and current YouTube policies. Check continuing authorization/deletion status at least every 30 days; delete data when authorization is revoked or the owner requests deletion. Metadata/public third-party API caches must be refreshed/deleted within applicable limits. MVP does not collect competitor API statistics. Operator retention review is manual in v1; do not claim automatic retention enforcement. See https://developers.google.com/youtube/terms/developer-policies .

## Initial verification state

21 isolated synthetic tests and 354 repository contract checks passed on 2026-10-19; see the latest local logs. This is software verification, not API integration proof. Google library installation was blocked by PyPI DNS resolution in the sandbox. The separate Cloud project `green-diagram-512119-e4` was created and visibly verified. After explicit owner approval, Google OAuth configuration and Desktop client ABVX OS YouTube Read Only were created; client.json was downloaded, checked for the correct project and stored under ignored credentials with mode 0600. YouTube Data API v3 and YouTube Analytics API were enabled and their Enabled states verified in the console. The owner account was added and verified as the sole listed test user. The owner subsequently completed terminal setup: Google libraries and token.json with all three requested read-only scopes and a refresh token are present; token mode 0600 was verified without exposing contents. No real API cycle or new weekly schedule has succeeded yet. Python DNS checks fail for pypi.org, oauth2.googleapis.com and youtubeanalytics.googleapis.com in the execution sandbox. The owner-run bin/youtube-intelligence-setup installs optional dependencies and opens the read-only OAuth flow in a terminal with normal network access. API acquisition also requires network access in the execution environment; installing dependencies alone does not solve that restriction. Inspect status before continuing; this paragraph is a dated implementation note, not a substitute for current evidence.

First-run handoff, 2026-10-19: a fresh bounded primary-source packet is retained at `.tmp/youtube-intelligence/research-20261019.json` (five initial proposals, 2 proven / 2 emerging / 1 creative, no production authority). `bin/youtube-intelligence-first-run` invokes the normal read-only runner from an owner terminal with a unique actual UTC run ID. This is an explicit owner-executed network operation, not a workaround executed by the agent. Research date/freshness checks still apply; refresh the packet if run on another UTC day. The next agent must inspect actual execution.json, responses, source periods and REPORT.md before claiming live success. Sandbox DNS remains blocked for Google even after libraries and credentials are installed; unattended weekly operation still needs an authorized network-capable execution environment.

First live acceptance: owner-terminal run `live-20261019T200214Z` completed on 2026-10-19, 20:02 UTC, with matching source/research hashes and full uploads pagination. Raw responses revealed lower/camel-case creatorContentType aliases; the adapter now normalizes them. Original analysis/report are preserved, corrected evidence is `analysis-v2.json` and `REPORT-v2.md`, and context prefers those revisions. Two Codex app heartbeat creation attempts failed; no matching saved automation exists. No weekly schedule is claimed active. Current Python sandbox Google DNS remains blocked, so unattended acquisition is not verified. Read the actual latest execution/status rather than earlier dated setup notes.

## Local host monitoring boundary

The owner-installed Mac monitor observes host readiness and saved schedules; it does not execute or replace this workflow. Preserve this playbook's acquisition, approval, report and learning requirements. See [the integration review](../maintenance/LOCAL_OPERATIONS_INTEGRATION_V1.md). A healthy host or ACTIVE saved schedule is not proof of a completed run.

## External discovery → channel filter → verified learning (owner clarification 2026-11-02)

The catalog defines the channel niche; internal analytics filters new opportunities discovered outside the channel. Do not reduce discovery to sequels of past winners or ignore channel evidence in favor of generic trends. Search distinct external lanes within the niche, then check the fresh complete catalog for repeated viewer questions. Record rejected candidates and missing evidence. A release is not measured momentum, developer stars are not YouTube demand, and competitor reach is not transferable RPM.

Radar cards (`method_version: youtube-radar/...`) require `selection`: external origin/signal, niche fit and reason, novelty key/status, catalog evidence, expected response and uncertainty. The menu rejects HOLD/REJECT, REPEAT/UNKNOWN and duplicate novelty keys. Semantic novelty is an evidence-bound researcher judgment; the selector does not infer it from titles. With an incomplete current catalog, disclose provisional novelty and obtain the missing catalog before production.

On a selected registered experiment, carry `selection` into the frozen registration. Optional `secondary_predictions` records additional reach/revenue thresholds and their bases, while primary metric stays fixed. These are prospective testable predictions, never backfilled after seeing results. `learning-review.json` keeps reach and monetization outcomes separate and proposes the next discriminating check. A supported threshold is not causal proof. Distinguish low exposure, packaging, retention, geography/traffic, inadequate monetization sample, costs and data-access failure. Strengthen a selection rule only after repeated independent evidence; retain false predictions and test proposed corrections on subsequent uploads.

## Nantes executable handoff (Pass 2)

For a manual Nantes review, optionally read the bounded [historical journal context](../OPPORTUNITIES.md#контекст-предыдущих-выпусков-только-чтение). Keep this workflow's own `context`, prospective hypotheses and source-age checks authoritative for their domains. Historical journal summaries are neither fresh acquisition nor owner decisions. No scheduled task is changed by this helper.

After `run`, call `bin/youtube-intelligence nantes-stage --run-dir <retained run directory> --mode weekly --token <existing journal stage token>`. Write the resulting JSON into the packet_file returned by the **existing** journal begin command and finish that same youtube stage. The adapter verifies acquisition/research hashes and capture age, carries partial status, and sends nothing. Use the same internal-disk journal ROOT already owned by the hosted Nantes task. Never create another scheduler or canonical learning store. The manual acceptance test uses an isolated journal root and never prepares/acknowledges a publication.

The weekly hosted stage must call radar-request, collect fresh external evidence, freeze the new shortlist before comparison, then run this collector and hand off its packet. Give this stage the bounded research budget (up to 45 minutes), superseding the legacy generic two-minute limit only for YouTube. On other days do no new discovery: check current own dashboards/metadata if available, otherwise label the retained evidence/date; do not pass an old weekly report off as fresh daily acquisition.

Acquisition now retains acquisition-progress.json after catalog discovery and each ten report responses (plus channel revenue). A budget/network failure leaves dated evidence for diagnosis; it does not become a successful complete run. The bound is 500 read-only calls / 600 seconds because 250 was exhausted in a real 2026-11-02 run after reauthorization. No API key, client or scope change is required.
