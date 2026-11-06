# ABVX Book Radar Data Source Map V1

| Signal / source | What it can support | What it cannot establish | Capture / control |
|---|---|---|---|
| Amazon search results/autocomplete | Query phrasing, observed competing listings, point-in-time discoverability | Total demand, stable rank, rights, sales, unbiased results | Date/time, marketplace, exact query, URL, session/personalization caveat, observed rows |
| Amazon category / BSR pages | Category placement and relative rank at observation time | Unit sales or durable demand; rank is volatile | Exact category path, marketplace, timestamp, ASIN, rank, capture evidence |
| Amazon price/reviews/rating | Current displayed offer and social-proof snapshot | Conversion, quality, author sales, historical trajectory | Record displayed values and source URL; do not infer causality |
| KDP reports for ABVX titles | Actual own-account sales/reads/royalties for report period | Competitor performance or future demand | Preserve original export, account/date period, normalized copy, access control |
| Google Trends / Trendspyg | Relative search interest over selected terms/geographies/time windows | Book purchases, absolute search volume, Amazon demand | Treat as exploratory; record term, geo, range, extraction version, caveat |
| Google Books / Open Library | Bibliographic discovery, edition metadata, identifiers, possible translation records | Completeness, rights status, proof that a translation is currently sold | Store provider record URL/ID and retrieval date; cross-check primary records |
| BnF / national library / authority records | French bibliographic records, author/title authorities, edition discovery | Territorial rights clearance or exhaustive translation inventory | Preserve authority identifiers, record URI and fields; review source jurisdiction |
| Publisher / author / estate / rights-holder documents | Rights chain and permission evidence when primary, current, and scoped | Unstated territories, formats, languages, terms | Human review, source document, parties, territory, term, format/language, decision |
| WorldCat / union catalogues | Library holdings and edition/translation discovery | Rights, current commercial availability, complete holdings | Use permitted access; record institution/source and retrieval date |
| Internet Archive / Gutenberg / Wikisource | Source text discovery and access to digitized witnesses | Copyright status in all target territories, reliable edition text by itself | Check item-level terms, source edition, scans, transcription provenance |
| Crossref / OpenAlex | Scholarly publication metadata and references | Commercial book market demand or rights | Use only where research literature is relevant; retain DOI/record URI |
| Manual editorial review | Fit, source quality, translation feasibility, audience judgment | Market facts not independently sourced | Reviewer, date, rationale, unresolved questions, confidence |

## Minimum normalized observation

`source_id`, `source_uri`, `retrieved_at`, `marketplace_or_jurisdiction`, `query_or_record_id`, `method`, `raw_snapshot_ref`, `observed_fields`, `confidence`, `limitations`, and `reviewer`. Keep source observations separate from derived scores and decisions. Missing data is `UNKNOWN`, not `false` or zero. Store a provenance trail for every derived assertion and refresh volatile evidence before decisions.

This map is a proposal, not a schema migration. Do not modify the existing Ukrainian Modernism package or infer/refresh its candidate evidence from this audit.
