# External sensors

ABVX-OS may observe external signals as bounded evidence. It must not become a custom analytics, SEO, research, media, presentation or personal-brain platform.

## Analytics observation boundary

`AnalyticsObservation` is the smallest current ABVX boundary for external analytics signals.

It records:

- source: `plausible`, `google_search_console`, or future source;
- project;
- period;
- metric and optional dimension;
- observation payload;
- provenance;
- confidence;
- capture timestamp.

This is intentionally not a dashboard, database, crawler, scheduler, Google client, attribution platform or SEO system. Observations are inputs to human/project review and later evidence-backed decisions.

Existing `project_event` was not reused because it is intentionally limited to routine project events such as content publication and media attachment. Existing `ContextRequest`/`ContextPack` was not reused because it carries retrieval context, not time-bounded analytics measurements.

## Google Search Console donor

`mcp-gsc` is the first donor candidate for Google Search Console observation. It should be piloted before any custom GSC client is built.

Narrow inspection result:

- locator: `AminForou/mcp-gsc`
- footprint: local Python MCP server, recommended `uvx mcp-search-console`; clone mode requires Python 3.11+
- authentication: OAuth desktop client or service-account JSON
- Codex compatibility: documented `~/.codex/config.toml` MCP server configuration
- read capabilities: properties, search analytics, performance overview, period comparison, page/query detail, advanced search analytics, URL inspection, batch indexing checks, sitemap reads
- write/destructive capabilities: property and sitemap mutations exist but are disabled by default and require `GSC_ALLOW_DESTRUCTIVE=true`
- ABVX stance: consume normalized MCP tool results into `AnalyticsObservation`; do not wrap the whole MCP or connect all properties

First pilot target should be AzurMenton because it already has guide/event freshness work, attribution evidence and a direct content/revenue loop, but Search Console baseline remains missing.

## Research provider boundary

The existing `ContextProvider` shape is sufficient for future research providers if the operation is treated as:

`ResearchRequest -> provider -> evidence-backed ResearchResult`

No new research framework is needed now. A future adapter can mirror the existing context provider expectations: `capabilities`, `health`, bounded execution, explicit provider status, sources, known gaps, confidence and evidence refs.

Future provider roles:

- HyperResearch: compare as open/pattern-source deep-research provider.
- Open Deep Research: compare as deep research provider when a real research mission starts.
- FutureSearch: forecasting and hypothesis support only, not general research.

## HyperResearch vs Open Deep Research bakeoff sketch

Trigger: a real opportunity, funding/program, market or company research mission with an owner decision at stake.

Fixture:

- same research question;
- same max elapsed time and source budget;
- same required citation/provenance format;
- no private data unless explicitly approved.

Metrics:

- source traceability;
- factual accuracy under spot check;
- useful decision structure;
- cost/time;
- uncertainty handling;
- repeatability;
- privacy and data-retention behavior.

Decision output:

- `PASS`, `CONDITIONAL_PASS`, `FAIL` or `INCONCLUSIVE`;
- recommendation;
- evidence refs;
- risks;
- unresolved questions;
- `STOP_FOR_HUMAN_DECISION`.

## Non-goals

Do not build custom first versions of:

- GSC client;
- analytics dashboard;
- SEO dashboard;
- crawler;
- deep-research agent;
- presentation factory;
- media/video pipeline;
- personal brain.
