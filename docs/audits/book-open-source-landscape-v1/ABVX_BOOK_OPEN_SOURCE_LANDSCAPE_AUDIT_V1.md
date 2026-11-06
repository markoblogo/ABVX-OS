# ABVX Book Open-Source Landscape Audit V1

**Status:** completed desk audit; local pilots blocked by this host's missing Java runtime and unavailable network resolution. **Cost class:** EXPENSIVE (research phase authorized in the supplied audit brief); no purchases, credentials, external writes, production edits, or Ukrainian Modernism research performed.

## Executive result

ABVX already has a functioning book pipeline: source research/BookSpec, Pandoc-based EPUB and XeLaTeX print generation, structural and editorial gates, PDF utilities, and a manual KDP boundary. The material gaps are independent EPUB conformance/accessibility validation, repeatable market evidence capture, and clearer source provenance. The best next actions are small, reversible validators and a normalized evidence contract—not a second book factory or a scraping platform.

Recommended NOW: (1) make EPUBCheck a pinned, isolated validation tool when a Java runtime is available; (2) evaluate DAISY Ace as a separate accessibility gate; (3) formalize market-source snapshots and provenance in the existing Radar record before adding any collector. No package was installed or integrated in this audit. Existing proof EPUBs could not be validated because `java` cannot start on this host and GitHub DNS resolution failed. No test or integration success is claimed.

| Area | Current finding | Recommendation |
|---|---|---|
| Ebook build | Pandoc proof path exists; Kindle Previewer and EPUBCheck absent per factory capability map | Keep Pandoc; add EPUBCheck as independent validator, not converter |
| Accessibility | No independent EPUB accessibility gate recorded | Evaluate Ace; its automated report supplements, never replaces, human review |
| Print PDF | qpdf, Ghostscript, and Poppler tools are available; factory already has structural/visual gates | Reuse; improve documented preflight and visual checklist rather than add another PDF engine |
| Radar evidence | Existing Radar snapshots and KDP exports are manual; own sales reports are authoritative for own sales | Preserve dated source snapshots, URL/query/marketplace/context, observed fields, and confidence; do not infer sales from BSR |
| Rights/bibliography | No single authoritative source covers rights, editions, and translation existence | Use bibliographic catalogues to discover records, then verify rights with primary rights-holder/territorial evidence |
| KDP submission | KDP UI remains a human-controlled external gate | No automation of login, listing edits, uploads, or publication |

## Shortlist: top ten

1. **W3C EPUBCheck** — adopt as standalone conformance gate. Official W3C/DAISY project, BSD-3-Clause, active 5.4.0 release; EPUB 2/3 validation and functional/unit/integration tests. This validates standards conformance, not reader rendering or KDP acceptance. Sources: [repository](https://github.com/w3c/epubcheck), [releases](https://github.com/w3c/epubcheck/releases).
2. **DAISY Ace** — pilot accessibility reporting after EPUBCheck. MIT, maintained DAISY project with CLI/reports and automated tests. Automated checks cover only part of accessibility; retain human inspection. Source: [repository](https://github.com/daisy/ace).
3. **Keepa Python client** — defer to a separately approved, costed pilot. Apache-2.0 client and tests; data requires paid Keepa API access, monthly token plan, and credential handling. Official token rules show tokens expire after 60 minutes and subscriptions bill monthly; do not procure in this audit. Sources: [client](https://github.com/akaszynski/keepa), [official API plans](https://keepa.com/api-docs/plans-tokens.html).
4. **KDP Scout** — borrow its local snapshot/SQLite and explicit marketplace configuration patterns only. MIT/local Python CLI, tests present, but Amazon scraping/autocomplete and optional paid DataForSEO create fragility and policy risk; no automated collection recommendation. Source: [repository](https://github.com/rxpelle/kdp-scout).
5. **Google Books API** — candidate bibliographic discovery adapter, not rights evidence; quota/availability and field completeness must be tested against known records before adoption. [Official API](https://developers.google.com/books/docs/v1/using).
6. **Open Library APIs** — optional discovery/cross-reference source; community catalogue is incomplete and not authoritative for rights or translation existence. Respect its usage policy. [API](https://openlibrary.org/developers/api), [policy](https://openlibrary.org/developers/api#usage).
7. **BnF data.bnf.fr** — high-value French-language bibliographic discovery/reference source; assess stable identifiers and API/export behavior in a focused pilot. Not a substitute for rights-holder confirmation. [data.bnf.fr](https://data.bnf.fr/).
8. **Project Gutenberg Ebookmaker** — mature, tested, GPL-licensed format pipeline tuned to Gutenberg source conventions; do not adopt as a general ABVX converter. Useful only for metadata/normalization patterns. [repository](https://github.com/gutenbergtools/ebookmaker).
9. **Trendspyg** — optional exploratory Google Trends signal; actively developed with tests, but Google Trends access is unofficial/subject to change and is not Amazon demand or book sales. No decision weight until back-tested. [repository](https://github.com/flack0x/trendspyg).
10. **KDP Scraper** — reject as a foundation: low-maturity repository, paid scraping-provider dependency, no adequate test evidence located, marketplace coverage uncertain. No usage. [repository](https://github.com/Buoyairican/kdp-scraper).

## Data collection and decision rules

- Search/catalogue data suggests discoverability or edition existence; it does not establish public-domain status, territorial rights, or availability of a French translation.
- Amazon search/category/BSR/rating/review observations are point-in-time, personalized/marketplace-specific signals. Record exact date, locale, query, observed URL and fields. Do not convert BSR to sales as fact.
- KDP exports are the preferred evidence for ABVX-owned sales; keep the report period and export provenance. Public listing presence is verified separately from KDP Bookshelf/upload/preview/review states.
- Rights clearance needs a source document, territory, term, language/format, rights-holder identity, and human decision. Bibliographic APIs are discovery only.
- Store evidence append-only or versioned; retain raw source snapshots when permitted, normalized fields, source URI, retrieval timestamp, retrieval method, confidence, and reviewer. Never turn missing fields into negative claims.

## Pilot and safety outcome

No pilots could execute: `java -version` reports no usable Java runtime, despite a placeholder path; downloading the official release failed because the host could not resolve GitHub. Node is installed but Ace was not fetched or run. No existing manuscript, source, EPUB, or PDF was modified. Recommended next validation is a pinned EPUBCheck run on an existing design-proof EPUB, then Ace on the same artifact in isolated temporary storage; record tool version, exit code, raw report, and manual findings. These remain proposed, not completed.

### Sources / freshness

Upstream repositories and official documentation were checked during this audit on 2026-09-26. Repository activity, versions, quotas, APIs, and terms can change; refresh before adoption. Detailed candidate triage is in the adjacent JSON file. This audit deliberately does not research or update Ukrainian Modernism candidate evidence.
