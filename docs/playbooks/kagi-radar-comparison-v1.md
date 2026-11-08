# Kagi as an additional Radar source

Owner instruction: 2026-11-08. Scope: documentation and browser/manual research only. Cost class: CHEAP for this documentation change. Applies to Nantes, Multi-Market and YouTube Radar within their existing research windows and evidence contracts.

## Operating instruction

Use Kagi as an additional discovery source when an authorized browser session and a confirmed free search allowance are available. Keep the existing sources as the baseline. Open the normal Kagi search form or the already configured browser address-bar search in Chrome or Comet. A standard search URL is `https://kagi.com/search?q=<URL-encoded-public-query>`; it contains no authentication material. Check the complete query before submitting it.

Do not purchase, upgrade, top up, activate paid API/MCP access, create API keys, or use the API playground. Do not assume a browser subscription includes API usage. Do not extract cookies, passwords, session links or tokens, or use unofficial session-token clients. Do not change browser security settings or bypass protection. Send only public research terms, never private mail, account data or personal profiles.

If the session is unavailable, the free allowance is exhausted/unclear, or payment, CAPTCHA, additional permissions or a security warning intervenes, stop that Kagi attempt and record the concrete blocker. Continue with the existing authorized sources; no automatic login/retry loop. A failed Kagi attempt is not an empty market or zero demand. No scheduler, automation prompt, LaunchAgent, saved schedule or recurring task is changed by this procedure.

| Radar | Use Kagi to discover | Verify separately |
|---|---|---|
| Nantes | Local opportunities, employer pages, calls for projects | Original issuer, deadline, location, eligibility and actual terms; search hits are not confirmed leads |
| Multi-Market | Competitors, bibliography and buyer problems across the existing markets | Direct product/course/campaign evidence and paid-demand qualification; reviews, BSR, students, shop totals and search rank do not establish sales |
| YouTube | Original repositories, releases, documentation and relevant discussions | Current maintenance/access status and claim support; audience demand requires channel evidence, not search popularity |

Preserve the existing external-first ranking, market boundaries, production HOLD and publication/owner decision gates. Kagi does not replace authenticated analytics, KDP reports, direct marketplace acquisition or channel-specific evaluation.

## Controlled comparison: 5–8 queries

1. Before searching, freeze a manifest with a unique run ID, UTC start time, 5–8 exact public queries, their Radar/purpose, the named existing baseline search tool, free-allowance evidence and a total query budget. For a shared three-Radar test, cover each Radar with at least one query. Use one Kagi search and one baseline search per query; reserve no more than one corrective Kagi search, count it, and exclude it from paired scoring. Cap Kagi use at 9 searches and within the confirmed free remainder. If fewer than 5 pairs are affordable or fit the existing research budget, report PARTIAL and retain completed pairs without buying more or extending scheduled work.
2. Run identical strings in both tools in the same research session, alternating which tool runs first. Match country, language, date filters and lens where possible. Record actual settings, personalization UNKNOWN where unobserved, tool/route and UTC start/end per query. Do not change persistent account settings to force comparability. Mark unmatched settings and backend differences as limitations. The baseline is the named tool actually used, never an assumed Google backend.
3. Retain the first 10 organic result URLs/titles per query/provider, in observed order, or all if fewer. Mark sponsored results separately; exclude widgets and AI summaries from the organic set. Keep both original rank/URL and normalized destination; merge only verified redirects, locale aliases and identical content. Do not merge distinct product editions merely because titles match. Save minimized excerpts/captures in the run evidence directory, with UTC capture times and hashes; never capture authentication data. Preserve failures and missing results.
4. Judge relevance against the frozen query purpose. Separately open primary pages supporting any shortlisted finding and record what each actually proves, its date and access limits. A snippet remains a search proxy. Record unique relevant results, duplicates, verified primary-source results and incremental Kagi findings absent from that query's baseline set. Unsupported facts stay UNKNOWN. Include failed attempts in elapsed effort; engine-reported latency is separate from observed end-to-end time. Record active owner effort or UNKNOWN, corrections and allowance before/after.
5. Report each pair and the complete manifest, including failures: results retained, relevant unique URLs, duplicates, verified primary sources, incremental verified Kagi findings, elapsed effort and limitations. Novelty means new relative to this retained baseline set, not new to the web or the owner. Give an evidence-bound USE_AS_COMPLEMENT, INCONCLUSIVE or NO_OBSERVED_GAIN recommendation; a small sample does not establish general superiority. Preserve historical reports and learning records. Future API adoption or automation requires a separate owner decision and is outside this instruction.

### Retained record template

Keep private run material in `.tmp/radar-acquisition/<run-id>/kagi-comparison/` alongside the existing run context; do not create another canonical store or scheduled job. A Markdown/JSON/CSV record may use these columns (one row per result; separate paired summaries):

`query_id | radar | purpose | exact_query | provider/tool | route | settings | observed_at_utc | original_rank | original_url | normalized_url | duplicate_of | relevant/reason | primary_page_checked_at | supported_claim | evidence_path/hash | limitation`

Paired summaries add `retained_count`, `unique_relevant_count`, `duplicate_count`, `verified_primary_count`, `incremental_verified_kagi_count`, `elapsed_seconds`, `owner_effort_or_UNKNOWN`, `corrections`, `free_allowance_before/after`, `status` and `blocker`. Keep unavailable metrics null/UNKNOWN, not zero. A Kagi outage alone does not make a whole otherwise completed Radar run failed.

Where the existing Book Radar evidence contract applies, use `source_type=SEARCH_ENGINE`, `collection_method=BROWSER_OBSERVATION`, `evidence_class=SEARCH_PROXY` for SERP evidence and fill every required schema field before import. Retain independently checked primary-page evidence separately with its actual collection method. YouTube uses its own research packet, checked timestamps and source-age rules; this template is not an alternative import schema. Nantes uses its existing journal stages and source references. Do not auto-import comparison summaries as commercial observations or owner decisions.

## Initial evidence and limits

The 2026-11-08 exploratory check confirmed Kagi form search in Comet and address-bar search in Chrome, with the official extension visible in both. Chrome required normal Google sign-in; Comet had an existing session. The free counter reached 4/100 after three complete queries and one malformed query. These are dated observations, not a promise of current session availability. That exploratory check did not meet the 5–8-query protocol and did not demonstrate general superiority.

Official references: [browser search setup](https://help.kagi.com/kagi/getting-started/setting-default.html), [application integrations](https://help.kagi.com/kagi/getting-started/application-integrations.html), [Search API documentation](https://help.kagi.com/kagi/api/search.html), [official MCP](https://github.com/kagisearch/kagimcp). API/MCP are reference-only and are not enabled by this instruction.
