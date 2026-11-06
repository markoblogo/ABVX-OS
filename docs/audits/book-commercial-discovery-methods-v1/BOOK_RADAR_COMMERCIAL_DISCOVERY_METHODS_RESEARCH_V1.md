# Book Radar Commercial Discovery Methods Research V1

**Status:** PARTIAL — methods and source scan complete; evidence supports a bounded pilot, not a change to Radar or a book decision.
**Retrieved:** 2026-09-26.  **Cost class:** EXPENSIVE, explicitly approved.
**Boundary:** research only. No purchase/trial/account, scraping run, outreach, application, listing change, book selection/production, Radar V2, or D30 collection was performed. Existing historical validation remains **INSUFFICIENT_EVIDENCE**.

## Executive decision

| Question | Answer |
|---|---|
| What we know now | Current Radar cannot be judged predictive: no retained D30 series, no exposure denominator, and no defensible TP/FP labels. Treat this as unresolved, not as four failed or successful titles. |
| What Amazon hides | KDP reports own orders/reads/royalties, but public pages do not supply competitor units, query volume, organic impressions/clicks/conversion, or stable historical organic placement. Public rank is a relative, lagged, marketplace-specific sensor. |
| What other markets add | National POS panels can expose actual or estimated title sales to paying subscribers; public charts expose rank/units selectively. France additionally publishes a large sampled library acquisitions-and-loans barometer. These are independent channel evidence, not automatic Amazon.fr demand. |
| Institutional demand | Real, but channel-specific. Distribution/listing enables discovery and ordering; it does not guarantee stocking or sales. Tendering, selection schemes, and library purchasing have separate eligibility and quality gates. |
| Is Norway useful? | **Direct opportunity: PARTNER_REQUIRED / currently unclear.** Current schemes can buy copies after eligibility/selection, but no “libraries must buy any qualifying book” rule. A Norwegian organization number, Norwegian-language and scheme-specific rules, pre-publication timing and review matter. It is a strong intelligence case, not an accessible default ABVX route. |
| Most instructive method | Competitor-/buyer-job-first discovery, then confirm book intent and entry path with independent, dated evidence. KDP Scout contains useful separable collection ideas, but its composite score and estimated sales should not be copied. |
| Test first | Free/manual protocol against an owner-selected, already available hypothesis: fixed competing-title cohort, exact queries, repeated dated observations, and an independent market/library source. This research did not select the hypothesis or execute the pilot. |
| Spend to defer | Keepa, Publisher Rocket, KDSpy, Book Bolt, Helium 10, paid sales panels and any scraping proxy. First prove that persistence and independent signals alter a decision using free/manual evidence. |
| Before another Radar-native book | Retain D0/D7/D14/D30 own-title outcomes and exposure evidence where available; label channel/format; require observed buyer demand, book intent, supply gap, entry path, rights and accessible channel as separate claims. No universal score or automatic build threshold is justified yet. |

## 1. Existing ABVX evidence and constraint

The validation index, missing-data matrix, signal audit and open-source landscape audit were reviewed before external work. Their conclusions remain controlling: four Radar-native releases cannot yet be classified as true/false positives; D30 is absent; own KDP actuals are the strongest ground truth for ABVX titles; impressions/clicks/page views and comparable pre-launch histories are missing. No prior record was edited. The earlier open-source landscape audit is referenced, not replaced.

Radar currently describes a local, human-gated system with immutable scoring and a distinction between actuals and predictions. Commercial research should improve evidence and discovery methods without relaxing those boundaries.

## 2. What a small publisher can actually observe

Keep evidence types separate; do not store all of them as `demand`:

| Signal | Strength | What it establishes | What it does not establish |
|---|---|---|---|
| ABVX KDP orders/royalties/KENP | Direct for own title | Own account-reported transactions/reads and earnings, with report-specific delays | Organic exposure denominator or competitor sales |
| BookScan / NIQ / Circana POS | Direct or strong panel measure | Retailer-reported transactions within the panel and formats covered | Full market census, all self-published/e-book/library activity, or ABVX entry |
| Institutional acquisition record | Direct for that institution/sample | An institution selected/ordered/acquired a title | General retail demand or guaranteed future acceptance |
| Retailer bestseller/current rank | Strong proxy | Relative position at an observation time in one retailer/market/category | Units, causal trend, cross-retailer equivalence, historical demand unless captured over time |
| BSR estimate (tool) | Modelled proxy | A tool's conversion of rank/category/time into estimated sales | Actual competitor transactions; calibration validity unless independently proven |
| Query/autocomplete presence | Weak book-intent proxy | A phrase exists in a search suggestion/result system | Query volume, purchase intent, or sales |
| Reviews/ratings | Context/lagged proxy | Some readers encountered and chose to review/rate a book | Units or current demand; reviewer bias and platform policies affect the sample |
| Google Trends | Context | Relative sampled search interest by time/region/topic | Absolute volume or book purchase intent; zeros can mean low volume |
| Library holds/circulation | Direct library signal | Library users requested/borrowed within a system if exposed | Retail purchase intent or transferable Amazon demand |
| Bibliographic records/holdings | Supply/context | Editions, translations, subject metadata, institutional presence | Current sales or unmet demand |
| Community request/problem | Discovery/context | Repeated reader language or expressed need | Purchase, book intent, market size, or ability to enter |

**Amazon hypothesis:** supported with qualification. Amazon can answer “is the title purchasable here, what relative rank/price/reviews/formats and query neighborhood can I observe now, and what did my own account sell?” It is a major sales channel and a weak-to-moderate competitor-demand sensor. It cannot answer “how many competitors sold, how many searchers saw/clicked, is this niche profitable, or will another retailer/language transfer?” KDP says ranks are relative and lagged; rank alone is not a reliable activity ledger. Google Trends is explicitly normalized/sample-based, not absolute volume.

## 3. Tool and method reconstruction

The table distinguishes **documented** public behavior from **marketing** statements and **inference**. Prices are public list prices observed on the retrieval date when available; no paid access was obtained. “Unknown” means no public method/access evidence was established, not that none exists.

| Method/tool (type) | Data and method; signals/decision | History, cost/API, reproducibility and risk | ABVX disposition |
|---|---|---|---|
| Publisher Rocket (commercial) | Official tutorial/insights describe keyword/category research, estimated search/market measures, competitor and category analysis; tool markets estimated monthly searches/sales and competition. Exact estimation model and validation are proprietary/undocumented. | Current official page displayed $199 one-time. No public API verified. Terms restrict bot/script access, extraction, sharing and substitute services. Search/rank-derived sales remain estimates. | Import method: market-by-keyword/category decomposition and explicit comparable-title review. Ignore its proprietary scores as ground truth. No buy. |
| KDSpy (commercial browser tool) | Public pages describe keyword/category discovery, competitor pages, estimated sales/revenue from BSR and daily rank tracking across Amazon country stores. Details of estimator/calibration are opaque. | No verified current price/API in this scan. Browser/manual use; rank history is useful only if captured consistently. | Pilot-tool only if free access suffices; otherwise defer. Import dated cohort/rank concept; ignore unit claims. |
| KDP Spy by Book Bolt (commercial, distinct product) | Chrome listing advertises price, BSR, reviews and estimated sales; Book Bolt support describes estimates based on prior data, BSR and other factors. Low-/no-content focus. | Book Bolt displayed Pro $23.99/mo or $19.99/mo billed annually; Premium $35.99/mo or $29.99 annual; 3-day trial advertised (not started). Estimator is not independently reproduced. | Ignore for high-content opportunity gate; potential manual shelf observation only. |
| AuthorScout / commercial “KDP Scout” (commercial, distinct from OSS repo) | kdpscout.com advertises niche/title tracking, daily BSR snapshots, new indie title/review/price filtering and estimated sales; underlying inputs are Amazon pages/ranks and method is not transparent. | $9.99/mo Pro advertised and free tier; no public API verified. Marketing claims, not independent validation. Name collision with open-source `rxpelle/kdp-scout`. | Defer; no score adoption. |
| `rxpelle/kdp-scout` (open source) | Source inspection shows autocomplete seed expansion, product/BSR collection, local SQLite history, Amazon Ads CSV import and a composite keyword score. Weights include autocomplete, competition, BSR, own ads/orders/profitability, estimated volume, CPC, CTR, own rank and semantic relevance; semantic component is placeholder. | No paid API; Amazon scraping/TOS fragility. README reuses US BSR model for CA/AU, limiting transfer. Historical observations require running it over time. | **IMPORT_METHOD:** query neighborhoods, local dated snapshots, isolate own Ads evidence. **PILOT_TOOL:** only a constrained manual/local method, no production integration. **IGNORE:** composite score, modeled units and unattended scraping. |
| `Buoyairican/kdp-scraper` (open source) | Seed title→ASIN→category traversal, top-result scans, autocomplete seeds, rank/review thresholds for “winning” vs “authority” labels. README advertises paid scraping proxies and CAPTCHA handling. | Small project; weak test/maturity evidence, operational dependence on scraping services. | **IMPORT_METHOD:** competitor-first/category traversal as a discovery hypothesis. **IGNORE:** thresholds, paid proxy workflow and “winning niche” labels. Not a foundation. |
| KDP Niche Analyzer (Chrome product) | Current Chrome listing advertises Amazon.com/.ca/.fr/.co.uk/.de page analysis, limited free analyses, and page-signal display; method/score validation not public. Do not conflate with the previously audited similarly named tiny OSS project. | Free allowance/in-app purchase listed; no public API. Page reading/disclosures and extension permissions require separate review. | **PILOT_TOOL:** manual one-off comparison only if user elects; **IGNORE:** opaque score. Existing OSS project remains non-donor due license/method gaps. |
| Keepa + Python client (paid data + OSS wrapper) | Keepa API can return ASIN product data and historical rank/price/offer arrays; wrapper is Apache-2.0. Product Finder can aid ASIN discovery. Rank is not exact unit sales; review/rating historical availability depends on returned product fields/retention. | Paid token plan; cost varies with plan/token refill and query type. Official plan/token page lists current options. No purchase. API history is available only for tracked/retained product history; do not promise full arbitrary backfill. | **IMPORT_METHOD:** matched ASIN cohort, dated rank/price/availability persistence. **PILOT_TOOL:** future small calibration after separate cost decision. **IGNORE:** exact sales inference and broad ASIN mining before value is shown. |
| `trendspyg` (OSS Google Trends client) | Current repo supports regional/time interest, related/rising queries, Google properties/RSS; relative normalized interest only. Browser-backed Explore calls are slow/rate-limited; 429 risk. | No paid subscription/API key, but unofficial Google interface and breakage/rate limits. Historical series cannot be backfilled reliably; opt-in dated capture only. | **IMPORT_METHOD:** persistence/seasonality and related-query prompts. **PILOT_TOOL:** sparse cached manual sample. **IGNORE:** high-frequency trend scraping or book-sales inference. |
| MCP-KDP-Niche-Research / `nichedata.dev` (OSS project / hosted API) | Earlier repo now unavailable in the observed location; hosted service markets Amazon/Google/Books/open-library signals and score/estimated revenue; cross-signal aggregation does not prove independent validation or calibrated probability. | Hosted service advertises metered x402 price ($0.03 cached/$0.10 live) and crypto/network payment; no use. Repo/license/source continuity unresolved. | **IGNORE** as donor/foundation; reference only. MCP transport pattern alone adds no evidence quality. No calls/payment. |
| Helium 10 (commercial seller suite) | Seller-oriented keyword volumes, reverse-ASIN and product estimates; books may be included as Amazon products but book-specific calibration/publication-age handling not established. | Current plan page offers paid tiers (Platinum displayed $99/mo on annual billing); API/export depends on plan. Seller-facing estimated metrics, not book actuals. | Not a book-method donor. Defer unless a specific seller-side question remains. |
| Jungle Scout (commercial seller suite) | Not sufficiently verified in official public methodology for book-specific demand or calibration in this pass. Treat as adjacent Amazon seller research, not a demonstrated book sensor. | Current cost/API/history details not verified here. | **UNKNOWN / NOT NEEDED** pending a concrete question; no subscription. |
| Google Trends (public service) | Related/rising terms, geography, seasonality, relative search-interest series, normalized 0–100 from samples. | Free UI; unofficial collection APIs risk policy/rate changes. Relative not volume. | Context / idea generator. Never a build gate. |
| Reader-problem → selling-book workflow (manual) | Repeated reader problem across distinct communities → actual books recommended → independently verify title/market transactions → inspect specific, repeated product gap and accessible entry. | Free, human-led; community sample, survivorship and moderation biases. No broad social scraping. | Best hypothesis-generation method for useful non-fiction; preserve independent verification. |

### BSR-to-sales estimation conclusion

A rank-to-units estimator necessarily maps a **relative, time-varying ordinal** to units using a fitted or assumed relationship. Rank changes with marketplace, category, date, format and sales of other titles; category mix and rank volatility can make a snapshot translate to very different daily units. A model requires marketplace/category-specific calibration against transaction data and uncertainty intervals. Public tools generally do not disclose reproducible calibration sets or error bars. Treat every competitor-sales output as **ESTIMATED**, never as actual. The only direct comparator for ABVX-owned KDP books is ABVX account reporting; paid POS services can provide panel transaction ground truth for their covered market if access and coverage are verified.

## 4. Donor method decisions

| Donor concept | Decision | Reason / boundary |
|---|---|---|
| Buyer problem → books already recommended → transaction check → gap | IMPORT_METHOD | Starts from a buyer job and demands evidence before product design; complaints alone are not demand. |
| Competitor-first and category traversal | IMPORT_METHOD | A known selling title anchors buyer language, related books and adjacent shelves; category taxonomies differ by retailer. |
| Query/autocomplete neighborhood | IMPORT_METHOD | Useful vocabulary and route discovery; presence does not prove volume or sales. |
| Matched competitor cohort with timestamp, marketplace, format and age | IMPORT_METHOD | Makes rank persistence and entry trajectory auditable; observations are still proxy evidence. |
| Own KDP Ads CSV signals | IMPORT_METHOD | Preserve account-level impressions/clicks/orders separately from organic and market estimates. |
| Keepa historical ASIN data | PILOT_TOOL | Potentially resolves snapshot-noise question, but paid tokens and historical-coverage assumptions require later approval. |
| France public library acquisitions/loans | PILOT_TOOL | Free independent, local institutional evidence; sample/category limits mean it is not general retail validation. |
| NIQ/Circana/Edistat title-level panel access | PILOT_TOOL | Highest direct market evidence if a narrow decision can justify quotes; no purchase authorized. |
| Opaque universal niche scores; BSR as units | IGNORE | Mixed evidence types and hidden calibration obscure what is actually proven. |
| Broad scraping, proxy/CAPTCHA evasion, high-frequency polling | IGNORE | Fragile, high access/TOS risk, and weak incremental decision value. |
| Trend score as book demand; public-domain supply as demand | IGNORE | Interest/supply is not a transaction or book-intent signal. |
| MCP wrapper as validation | IGNORE | Transport/aggregation does not create independence, quality or calibration. |

## 5. Retailer and cross-market signal screen

Public retailer pages are **manual observation** unless an official, documented API/feed was verified. No bulk scraping or API probing was performed. Commonly observable fields include title, author, format, price, publication date, review/rating where present, category and related books; completeness varies. Public ranks are snapshots; rank depth/history and structured page data change. A bibliographic API is not a retail-sales API.

| Market/platform | Public signals and practical value | Units/history/API/access; transfer to Amazon |
|---|---|---|
| Apple Books (US, FR and other storefronts) | Paid/free and genre charts, title/price/format, editorial chart categories; useful independent ebook snapshot. | Charts publicly viewable; no public unit feed/history verified. Apple author/publisher reports are own-catalogue data. **Supporting**, format/market-specific. |
| Kobo / Kobo Plus (Canada, France, Europe) | Store search/catalogue, price, formats, ratings and selected lists; Kobo is relevant in Canada/parts of Europe. Subscription titles/reads are not unit sales. | No public title-unit API or stable historical chart established. Publisher-side data require distribution/account access. **Supporting**. |
| Google Play Books | Retail search, listing, prices, ratings and top-selling surfaces vary by region. | Google Books API is bibliographic, not Play Books sales. No public retail-unit API verified. **Supporting**. |
| Barnes & Noble (US) | Product metadata, reviews and categories; official rank is daily and weighted from prior six months of bn.com and store sales. | Public rank, not units or downloadable history. **Supporting**, US retailer-specific. |
| Waterstones / Blackwell’s (UK) | Search/catalogue, metadata, reviews and bestseller/current lists. | No public title-unit API or validated history found. UK POS panel/weekly chart is stronger. **Supporting/context**. |
| Fnac / Cultura / Decitre / Furet du Nord (France) | Local search, category, price, formats, reviews and featured/bestseller lists; discover French buyer language and availability. | No public unit data/API/history verified. Edistat/NIQ and ministry library data add stronger independent evidence. **Supporting**. |
| Thalia / Hugendubel (Germany) | Catalogue, category, price, formats, reviews and current charts. | Title units and open history not verified; Media Control has panel data. **Supporting**. |
| bol.com (NL/BE) | Catalogue/search, ranking/list surfaces and metadata; local language/availability context. | No public unit API/history verified; CPNB charts and NIQ add stronger evidence. **Supporting**. |
| Indigo (Canada) / Bookshop.org (US/UK) | Search, reviews, metadata, curated lists; Bookshop.org often reflects partner-store fulfillment and curation. | No public title sales history/API established. **Context / supporting**. |
| Audible / Apple audio / Storytel / Everand | Audiobook charts/catalogue/rating and subscription inclusion; reveals audio consumption and format signal. | Public starts/minutes/royalty units unavailable; own-publisher reporting only. Audio popularity transfers to print only as context. |
| Amazon KDP / Amazon retail | Search, autocomplete, category, current BSR, price, format, review count; own KDP account reports own sales/reads. | Public competitor units/query denominators/historical organic ranks absent; own reports and paid ad metrics are distinct. Strong channel, imperfect sensor. |

### Public and paid sales systems

| Country/system | Evidence/access | Coverage caveat and value |
|---|---|---|
| US — Circana BookScan / PubTrack Digital | Circana says BookScan tracks POS across ~85% of U.S. trade print via retailer feeds; title/category analytics are commercial. Public industry excerpts sometimes quote units. PubTrack Digital is a publisher participant panel. | Strong paid print sales benchmark, not full market or all self-published/e-books. Check exact coverage/ISBN and quote before any future pilot. |
| UK, France, Italy, Netherlands, Spain, Australia — NIQ BookData/BookScan | NIQ markets POS measurement and country products; public charts/media excerpts exist; title-level panel access is generally commercial. | Panel/format/territory coverage differs. “Sales” may be panel actuals/estimates, not a census. |
| France — Edistat | Public site advertises weekly ISBN-level sales estimates from a broad cash-register panel plus trend/chart services; public bestseller excerpts and paid detail. | Valuable local commercial signal; estimation, panel and licensing scope require quote/method review. |
| France — Ministry library barometer | 2024 barometer published 2025: 427 public libraries, reported 13.5m loans and 419k acquisitions, with ranked/category outputs. Public report/tables; sampled acquisitions and circulation. | Best free FR institutional sensor found; not the whole French market, not retail sales, and selected/top-title depth limits niche coverage. |
| Germany — Media Control | Company reports register/POS panel of 15,000 retailers and ~90% market coverage; charts visible through trade/media, deeper data commercial. | Strong German panel if subscription access justified. |
| Netherlands — CPNB / Bestseller 60 / Top 100 | Public weekly 60 and annual sales/lending lists; CPNB describes data drawn from hundreds of bookshops and broader outlets. | Rank/list visibility, selective categories/time; a useful local signal, not a general title-level feed. |
| Canada — BookNet SalesData | Weekly POS subscriber system with >2,000 outlets and stated ~85% English-language trade-print coverage; public bestseller ranks/excerpts. | Good English Canada panel; weaker coverage for French/self-published/e-book; access/data-sharing rules apply. |
| Norway — Bokhandlerforeningen | Weekly sales and distinct-title charts/exports from reporting members for defined book groups; historical views available. | Real sales signal but member/category coverage excludes important classes (including English books/textbooks/local books); panel composition changes and reuse permission matters. |
| Sweden/Nordic — Bokinfo / national trade charts | Publisher/member reporting and weekly/monthly lists; access/API is member-bound. | Market and format coverage vary; useful if local publisher access exists, not an open global feed. |
| Australia — NIQ / BookPeople | NIQ paid panel; BookPeople shares selected public lists. | Public chart is partial; separate print/ebook coverage. |
| Bibliographic agencies (BnF, Google Books, Open Library, WorldCat) | ISBN, edition, translation, publication and holdings/diffusion context. | Supply/map evidence, not transaction evidence. No sales transfer without independent validation. |

### France-specific finding

For France, prioritize three distinct layers: (1) **Edistat/NIQ** for panel sales estimates if the price and coverage can change a decision; (2) **Ministry library barometer** for free sampled library acquisition/loan evidence and real local institutional demand; (3) **Fnac/Cultura/Decitre** manual snapshots for discoverability, pricing, format and local supply. SNE and Culture Ministry sector statistics provide market context, not title-level demand. BnF deposit measures publication/supply, not reader demand. No single free public French source reproduces complete, current, title-level all-channel unit sales.

## 6. Discovery methods and combinations

| Method | Best use / demand and intent | Entry, cost and failure mode |
|---|---|---|
| AMAZON_QUERY_FIRST | Map exact purchase language, autosuggest families and comparable books. Good shelf vocabulary, weak volume proof. | Free/manual; autocomplete presence can be tiny or incidental. Pair with selling-book evidence and own ads/actuals if available. |
| COMPETITOR_FIRST | Start from an observed selling title; inspect adjacent titles, buyer job, complaints, formats, age, publisher and query overlap. | Better than brainstorm-only for grounding, but a top title may be famous/brand-led or unrepresentative. Verify transactions and low-review entrants. |
| CATEGORY / CHART_FIRST | Locate persistent small shelves and title patterns from public retailer/national charts. | Good discovery and market framing; chart popularity may imply strong incumbents, and categories vary across stores. |
| READER_PROBLEM / COMMUNITY_FIRST | Repeated specific requests, complaints, vocabulary and unmet tasks across independent communities. | Strong idea generator; not purchase proof. Workflow: problem → recommended books → transaction verification → repeated gap. Avoid social scraping and viral one-offs. |
| CROSS_RETAILER | Same or analogous titles over dated retailer charts/search in independent markets. | Triangulates channel demand; rank scales and chart methods differ, and coverage may share a data provider. Independence must be recorded. |
| CROSS_LANGUAGE / TRANSLATION_GAP | Demand in A, weak local supply in B, local query/library/retail evidence, rights availability and native-language quality. | Another language's bestseller is only a lead. Local book intent and rights are hard gates; translation does not create demand. |
| LIBRARY_DEMAND_FIRST | Acquisitions, holds/copies, circulation, library lists, OverDrive availability. | Direct institutional or library-user behavior. Distinct buyer, budgets/licensing and transfer to retail are unknown. Holds/copies is capacity-sensitive. |
| INSTITUTIONAL_PROCUREMENT_FIRST | Start from recurring buyer/procurement category, requirements, past award/notices, channel and eligibility. | Better than a book idea for structured demand. Procurement notices are not awards/purchases; tenders have qualification, competition and delivery burdens. |
| FORMAT / PRICE GAP | Compare actual demand by format, title price/length/age and complaints. | Requires evidence that format/value affects purchase; a low price or poorly reviewed incumbent is not itself a gap. |
| EXTERNAL TREND / Google Trends | Reject transience/decline, detect seasonality or compare relative language/region. | Context only. Short trend half-life may be faster than credible ABVX production; viral interest is particularly risky. |

**Best combination for retail:** competitor-first + dated cohort persistence + exact query neighborhood + one genuinely independent sales/library/chart source + supply/entry review.
**Best combination for cross-market:** source-market actual/persistent demand + local-language book intent + local supply/quality gap + rights/channel feasibility.
**Best institutional sequence:** buyer/programme → eligibility and product requirements → purchase/distribution mechanism → prior awarded/selected title evidence → realistic local channel and economics.
Do not count Amazon BSR and Amazon category rank as two independent confirmations; the roots are shared. Also audit whether two “independent” charts derive from the same BookScan panel.

## 7. Institutional demand: mechanisms, not a promise

### Norway seed case

Official Kulturdirektoratet scheme pages describe both automatic and selective acquisition routes. “Automatic” is a programme route with quality review, defined eligible categories, publication/application timing and a budgeted copy allocation—not a rule that every publisher/book is automatically bought. Current translated-literature criteria include works translated into Norwegian, specific eligible fiction/nonfiction/age groups, exclusions (e.g. textbooks, reference, self-help/professional material), application before publication, quality/selection constraints and normally direct translation from the original language (exceptions are narrow). The current page lists 502 copies for adult translated literature and 1,042 for translated children/YA from the stated round; verify the exact live round before modeling any economics. Books are delivered through the named distribution process. Applications require a Norwegian organization number according to official FAQ. Rejection/withdrawal creates real print/translation/royalty exposure under the scheme rules. Print-on-demand and KDP eligibility were **not established** by the rules reviewed; do not assume either qualifies. A French publisher cannot apply directly absent required Norwegian entity number; partner path is plausible but not confirmed by these rules. Public decision listings expose titles/publishers and decisions, useful for method research but not a submission denominator or clean acceptance rate without reconstructing eligibility and rejected population.

**Norway verdict:** direct ABVX path **PARTNER_REQUIRED / UNCLEAR**; as market-intelligence dataset **MEDIUM** (selection and listed titles, but selected sample and criteria bias); as a model to search elsewhere **HIGH** (a real public purchase/distribution mechanism whose gates can be verified). No profitability or acceptance probability is assumed. Illustrative economics must remain symbolic: eligible copies × net receipts/compensation − translation, print, delivery, application and rejection exposure; all unknown values require current confirmation.

### France and distribution

France's public library barometer is an observed sample of acquisitions and loans, not an automatic national procurement. CNL, regional and EU translation/cultural supports are primarily grants or cost relief unless a specific call explicitly purchases copies. EU TED and French procurement notices identify tenders, not completed awards or repeat demand without award/contract follow-through. OverDrive enables publishers to supply digital titles to library marketplaces; libraries select and license titles individually. Ingram's distribution/POD footprint makes a title orderable, not stocked or sold. The same distinction applies to library wholesalers/aggregators, including Gardners/Baker & Taylor: distributor access is **DISTRIBUTION_ONLY** unless a specific order is documented.

### Candidate mechanism screen (36 candidates; desk-screen only)

This is the requested 30–50-candidate first pass. It is a **mechanism inventory**, not 36 deeply verified actionable programs. A desk-screen label “theoretically interesting / unknown” means a local buyer/eligibility workflow must be established before any value claim. All current program specifics require live call/rules review before action.

| # | Country / mechanism | Economic type | First-pass fit for ABVX |
|---:|---|---|---|
| 1 | Norway Kulturdirektoratet automatic new Norwegian fiction acquisition | Automatic with quality review | Local entity/language gate; not direct |
| 2 | Norway acquisition of translated literature | Selective purchase | Norwegian-language/organization/prepublication gates; partner required |
| 3 | Norway nonfiction/educational acquisition schemes | Selective / category-limited | Specific call only; current eligibility not generalized |
| 4 | Norway Bokhandlerforeningen weekly panel / Boklista | Sales evidence, not purchase programme | Public, useful market sensor with scope caveats |
| 5 | France public library acquisitions/loans barometer | Recorded institutional purchases/loans | Direct free evidence sample; no guaranteed acquisition |
| 6 | France municipal library purchasing | Decentralized orders | Potential through distributors; no national guarantee |
| 7 | France CNL translation/publication support | Grant/cost relief | Secondary; not copies bought |
| 8 | France regional cultural book programs | Grant/curation/procurement varies | Unknown until specific call; not counted as sales |
| 9 | France school/education procurement | Tender/framework/listing | Unknown; curriculum/qualification burden |
| 10 | France university/library acquisitions | Decentralized purchase | Discoverable via catalogues/tenders; no guaranteed volume |
| 11 | EU TED book/library supply notices | Open tender | Public notice data; bid/eligibility burden; tender ≠ award |
| 12 | EU Creative Europe literary translation | Grant/circulation support | Grant, not purchase; rights/consortium conditions |
| 13 | France BOAMP/public procurement notices | Open tender/notices | Potential purchase intelligence; completion/award linkage needed |
| 14 | UK Public Lending Right | Loan-based remuneration | Rights-holder registration/eligibility; not a purchase guarantee |
| 15 | UK public library acquisitions via wholesalers | Decentralized ordering | Distribution route, library selection remains local |
| 16 | UK school reading/approved supplier channels | Framework/list-based | Specific supplier/quality barriers; unknown for ABVX |
| 17 | UK local authority book tenders | Open tender | Public notices; procurement qualification and competition |
| 18 | US public library collection procurement | Decentralized institutional orders | Wholesaler/distributor route; local selection |
| 19 | US OverDrive/Libby library marketplace | Library digital license | Publisher supply access; library selects, no guarantee |
| 20 | US Hoopla/library digital licensing | Library digital license | Contract/catalogue route; usage is not public sales |
| 21 | US Baker & Taylor library supply | Distribution/framework | Orderable ≠ ordered; terms/account access to verify |
| 22 | US Ingram library/retail distribution | Distribution/POD | Accessible supply infrastructure, not demand assurance |
| 23 | US school district/state instructional materials | Procurement/adoption | High requirements and brand/standards gate; not practical yet |
| 24 | US university course adoption | Instructor-led orders | Discoverable course lists, adoption not predictable |
| 25 | US professional association member books | Bulk/curated purchase | Specific relationship/product needed; unknown |
| 26 | Canada BookNet SalesData | Retail POS panel | Paid/subscriber sensor, English-print bias |
| 27 | Canada Book Fund publishing support | Grant | Local ownership/operation/content gates; not copy purchase |
| 28 | Canada public library acquisition | Decentralized purchase | Distributor/listing path, no guarantee |
| 29 | Canada provincial school-library supply | Procurement/framework | Province-specific; eligibility unknown |
| 30 | Canada Public Lending Right | Loan remuneration | Eligible rights/title registration; not acquisition guarantee |
| 31 | Germany Media Control book panel/charts | Retail sales measurement | Strong paid sensor; not an acquisition program |
| 32 | Netherlands CPNB Bestseller 60 / annual lists | Sales chart | Public rank/selected unit evidence; not guaranteed demand |
| 33 | Sweden Bokinfo / library-retail channels | Publisher reporting/distribution | Member/channel access; not direct guarantee |
| 34 | Denmark library book purchasing / public lending remuneration | Decentralized purchase / remuneration | Specific rules/ buyer route unverified here |
| 35 | Finland library procurement / public lending remuneration | Decentralized purchase / remuneration | Specific route and foreign eligibility unverified |
| 36 | Iceland library/cultural acquisition | Decentralized/possible cultural programs | Small market; exact current programme unverified |

**Classification:** Directly accessible now: public notices, public charts, public French barometer, public rule/decision data. Accessible with partner/distributor: digital/library supply, Norwegian scheme, local procurement. Accessible with local entity: Norway rules as reviewed. Theoretically interesting: tenders, school/university/professional purchasing, national cultural programs not deeply verified. Not practical as a generic KDP-volume strategy: applying speculatively to selective schemes. Unknown is not “none exists.” Grants, PLR and eligibility must not be reported as guaranteed copy purchases.

### Other institutional observations

- **Library demand is a separate path.** Acquisitions, circulation and holds/copies each measure different behavior. Holds/copies can suggest unmet demand only after accounting for copies, branch population, licensing, queue rules and availability. It does not transfer directly to Amazon.
- **Bulk sales can be repeatable only after a channel/job is concrete:** course adoption, association member benefit, procurement contract, distributor order or institutional license. Generic cold outreach is not a method and was not performed.
- **Public procurement:** TED supports documented search of notices; search terms include books, library supply, manuals, language-learning and educational materials. Notices are not awarded invoices. Link notice → award → repeat buyer and ISBN/requirements before treating as demand. No bid was placed.
- **OverDrive / Ingram:** publishers can make eligible content available to institutions/retailers, but this proves availability. Library acquisitions and fulfilled orders are separate evidence.
- **EU / Canada grants:** grants may reduce creation cost but are not book sales. Canada Book Fund eligibility includes Canadian ownership/operation conditions; not a current ABVX route.

## 8. Cross-market, format and entry implications

Cross-market transfer is a hypothesis, not an inference from a bestseller. Normalize buyer job and title/ISBN/edition, native language, local query phrase, format, price, age, rights, retailer coverage and channel. A UK rank can discover a French topic, but France needs local book-intent/supply confirmation. A library acquisition can discover public-sector fit, not retail demand. Audio charts are format-specific; subscription inclusion/reads differ from unit sales.

Useful evidence for an unknown entrant is not simply low incumbent reviews. Inspect age and publisher distribution in a stable observed cohort, repeated visibility of newer small-publisher titles, category/query overlap, price/format, and persistence. Low-review success is a possible entry signal only when sales/rank is independently credible. Literary/celebrity/fandom categories are often recommendation/brand-driven; utility/search-driven categories may be more discoverable by an unknown publisher, but still require authority and quality. No universal review cutoff or “low competition” threshold is supported.

Quality-gap types to preserve separately: content, format, freshness, language, price/value, packaging and trust. A low-rated non-selling title is not proof of a quality gap. A selling book plus repeated, specific complaints about a missing use case is a stronger hypothesis, still requiring transaction and feasibility checks.

Demand durability and production speed matter: prefer persistent buyer jobs, reference/practice, curated corpus, strong narrative or physical-use cases over short-lived social spikes unless ABVX can credibly deliver inside the trend window. AI commoditization is a qualitative product question, not a numeric score: “why buy a book instead of asking an assistant?” needs a concrete answer (authority, sequence, practice, curated data, visual reference, ownership, story or offline use). Strong sales can be brand-led; unknown-author entry evidence matters.

## 9. Recommended bounded pilots (design only)

No actual topic/title was selected. These pilots need later owner selection of an existing hypothesis and, where noted, separate cost/access authorization.

| Order | Pilot / question | Cost, time, dependencies | Changes decision; pass/fail condition |
|---|---|---|---|
| DO_FIRST | **Manual persistence + book-intent protocol:** does repeated rank/price/review/availability observation of a fixed competitor cohort change the interpretation versus one snapshot? | Free; 2–3 weeks of manual snapshots (estimate); requires owner-chosen hypothesis, query set, marketplace, matched titles and logging sheet. | Pass: materially separates persistent from transient positions and identifies age/format/entry context. Fail: observations are too unstable or fail to change any candidate decision. Does not prove units. |
| DO_LATER | **France independent-signal check:** do chart/retailer shelf observations and the public library barometer surface the same buyer job or distinct institutional needs? | Free; 1–2 days for bounded published tables/manual shelf audit (estimate); requires a hypothesis and access to barometer tables. | Pass: gives an independent, decision-relevant French signal or reveals transfer limits. Fail: sample/category resolution cannot observe the hypothesis. |
| DO_LATER | **Cross-retailer snapshot test:** compare a small matched title cohort on Apple Books/Kobo/Fnac or B&N/Apple and Amazon in one market. | Free; 1–2 days plus repeat capture; manual access, exact locale/category and date. | Pass: demonstrates a stable independent signal and exposes transfer errors. Fail: rankings too shallow/volatile or no extra decision information. |
| DO_LATER | **Public unit/rank chart extraction:** use one country chart with published units/ranks (e.g., Netherlands/Norway) to classify title age/category/publisher/format, then compare local Amazon shelf. | Free; 1–2 days; bounded published charts, no bulk crawl. | Pass: yields a plausible, auditable transfer lead plus local book intent. Fail: chart sample cannot resolve niche/entry. |
| DO_NOT_DO_YET | **Keepa historical BSR experiment** | Paid; tokens, plan, matched ASINs and calibration ground truth required; cost is plan/query-dependent and cannot be responsibly quoted as a fixed total without choosing sample/API calls. | Valuable only if free manual persistence is decision-relevant and there is an independent label to test. Later compare snapshot vs persistence for known positives and negative/weak controls. No subscription now. |

No 2–3-title Radar-native cohort is selected. Existing D30 observations remain a separate future validation stream. Pilot pass conditions are learning criteria, not universal build thresholds.

## 10. Future architecture options — decision gate only

Evidence supports **separate commercial paths**, not a single Amazon niche score:

1. **Retail/search:** observable transactions or persistent rank → book-intent/query family → supply/quality gap → new-entrant visibility → channel/format economics.
2. **Cross-market:** strong source-market evidence → local language demand and weak local supply → rights/localization feasibility → local entry/channel.
3. **Institutional:** identified buyer/programme → written eligibility and requirements → documented purchase/distribution mechanism → selection/tender evidence → local fulfillment/economics.
4. **Catalogue/series:** shared audience, read-through/repeat purchase and production reuse must be observed; Toki Pona can inform catalogue economics conceptually, but its cultural/editorial mission and sparse outcomes are not commercial proof.

Conceptual evidence record (not implemented): opportunity type; buyer and job; channel; claim; evidence item/source/URL/retrieval date/market/format; observed value and method; actual vs estimated vs rank vs interest; provenance/root source; freshness; source reliability; independence group; missingness/access-failure state; supply/entry/rights/feasibility; unresolved claim. Prefer claims (“people buy this kind of book,” “local purchase need exists,” “new entrant can be found,” “ABVX can access the channel”) over `NICHE_SCORE=78`.

Potential sensors: retail sales/rank, query/book intent, historical persistence, external trend, supply/gap, new entrant, institutional acquisition/procurement and rights/channel feasibility. LLMs can expand/normalize queries, classify comparable titles, summarize repeated review/community language, and synthesize gaps. They cannot invent demand, estimate units without calibrated evidence or authorize build. Human review remains necessary for relevance, native-language quality, rights, cultural fit, institutional eligibility and final BUILD.

### Current data collection worth preserving (passively)

For existing ABVX titles only: per-marketplace/format dated own KDP orders, royalties and reads at D0/D7/D14/D30 when available; report-generation/update time; Amazon ads impressions/clicks/orders clearly separated; manual exact-query shelf observations; matched competitor ASIN/ISBN, title age, rank/category, price, format, availability, reviews and observation date. Preserve `ACCESS_FAILED` distinctly from `NO_DATA`. Do not initiate new automation or D30 collection as part of this task.

## 11. Source register (primary sources unless marked)

All sources accessed 2026-09-26. Tool/vendor pages evidence public product claims, not independent efficacy. Country coverage and prices can change; recheck before purchasing or using rules.

### ABVX prior work

- `book-radar/validation/BOOK_RADAR_VALIDATION_INDEX_V1.md`
- `book-radar/validation/BOOK_RADAR_MISSING_DATA_V1.md`
- `book-radar/validation/BOOK_RADAR_SIGNAL_AUDIT_V1.md`
- `docs/audits/book-open-source-landscape-v1/ABVX_BOOK_OPEN_SOURCE_LANDSCAPE_AUDIT_V1.md`
- `docs/audits/book-open-source-landscape-v1/ABVX_BOOK_RADAR_DATA_SOURCE_MAP_V1.md`
- `registries/capabilities.json`; `registries/donor-capability-matrix.json`

### Amazon, search and tools

- [KDP sales ranking](https://kdp.amazon.com/en_US/help/topic/G201648140); [KDP reports](https://kdp.amazon.com/en_US/help/topic/GVTTXHKHVPAPBEDQ); [KDP Ads](https://kdp.amazon.com/en_US/help/topic/G201499010); [Amazon sales-rank description](https://sell.amazon.com/blog/amazon-best-sellers-rank).
- [Google Trends FAQ/method](https://support.google.com/trends/answer/4365533?hl=en).
- [Publisher Rocket tutorials](https://publisherrocket.com/tutorials/), [market insights](https://publisherrocket.com/insights/), [pricing](https://publisherrocket.com/), [terms](https://publisherrocket.com/terms-and-conditions/).
- [KDSpy](https://www.kdspy.com/), [book tracking](https://www.kdspy.com/help/book-tracking/).
- [Book Bolt](https://bookbolt.io/), [Book Cloud estimated-sales help](https://bookbolt.kb.help/book-cloud-how-to-see-the-best-selling-books-by-category/), [KDP Spy Chrome listing](https://chromewebstore.google.com/detail/kdp-spy-by-book-bolt/eimimdbkklcfefabegnlclkfakkfdcpc).
- [AuthorScout/KDP Scout](https://kdpscout.com/).
- [OSS KDP Scout README](https://github.com/rxpelle/kdp-scout), [keyword engine](https://github.com/rxpelle/kdp-scout/blob/main/kdp_scout/keyword_engine.py), [BSR model](https://github.com/rxpelle/kdp-scout/blob/main/kdp_scout/bsr_model.py), [autocomplete](https://github.com/rxpelle/kdp-scout/blob/main/kdp_scout/autocomplete.py).
- [kdp-scraper](https://github.com/Buoyairican/kdp-scraper); [KDP Niche Analyzer extension](https://chromewebstore.google.com/detail/kdp-niche-analyzer/eimhnefmhakppieblgfajmhhchocophk).
- [Keepa API token plans](https://keepa.com/api-docs/plans-tokens.html); [Keepa Python client](https://github.com/akaszynski/keepa).
- [trendspyg](https://github.com/flack0x/trendspyg); [nichedata.dev](https://nichedata.dev/) (hosted marketing page; underlying earlier repository continuity unresolved).
- [Helium 10 product research](https://www.helium10.com/tools/product-research/), [keyword research](https://www.helium10.com/tools/keyword-research/), [Magnet method help](https://kb.helium10.com/hc/en-us/articles/4765984652315-How-to-Analyze-Keywords-Using-Magnet).
- [Jungle Scout](https://www.junglescout.com/) (book-specific method not verified).

### Retail and national market data

- [Apple Books charts](https://books.apple.com/us/charts); [Google Books API](https://developers.google.com/books/docs/v1/using).
- [B&N sales-rank method](https://help.barnesandnoble.com/hc/en-us/articles/5356105661339-About-Sales-Rank).
- [Circana Books](https://www.circana.com/industries/books); [NIQ BookData global](https://nielseniq.com/global/en/landing-page/nielseniq-bookdata-measure/); [NIQ France](https://nielseniq.com/global/fr/landing-page/nielseniq-bookdata-france/) (country page availability may vary); [Edistat](https://www.edistat.com/).
- [French Ministry 2024 library barometer](https://www.culture.gouv.fr/thematiques/livre-et-lecture/actualites/barometre-des-prets-et-des-acquisitions-en-bibliotheque-2024); [method/report](https://www.culture.gouv.fr/Media/Thematiques/Livre-et-lecture/Files/Bibliotheques/barometre-des-prets-et-des-acquisitions-en-bibliotheque/barometre-des-prets-et-des-acquisitions-dans-les-bibliotheques-de-lecture-publique-2024); [SNE key figures](https://www.sne.fr/economie/chiffres-cles/); [BnF legal deposit observatory](https://www.bnf.fr/fr/lobservatoire-du-depot-legal-2024).
- [Norway Bokhandlerforeningen statistics](https://bokhandlerforeningen.no/salgsstatistikk/); [Kulturdirektoratet scheme overview](https://www.kulturdirektoratet.no/fag/litteratur/innkjopsordninger); [translated-literature rules](https://www.kulturdirektoratet.no/tilskuddsordninger/innkjoepsordning-omsett-litteratur); [official FAQ](https://www.kulturdirektoratet.no/hjelp-og-veiledning/spoersmaal-og-svar/innkjoepsordningane-for-litteratur); [decision search](https://www.kulturdirektoratet.no/vedtak).
- [CPNB Top 100](https://cpnb.nl/campagnes/cpnb-top-100/); [CPNB annual overview](https://jaaroverzicht.cpnb.nl/); [Media Control](https://www.media-control.de/buch1.html); [BookNet SalesData](https://www.booknetcanada.ca/salesdata); [BookNet sharing policy](https://booknetcanada.atlassian.net/wiki/spaces/UserDocs/pages/832503811/BNC+SalesData+LibraryData+Data+Sharing+Policy); [Bokinfo statistics](https://booksellers.se/om-branschen/statistik/).

### Libraries, distribution and procurement

- [OverDrive publisher access](https://company.overdrive.com/publishers/); [OverDrive library service](https://company.overdrive.com/public-libraries/); [Ingram wholesale distribution](https://lp.ingramcontent.com/publishers/wholesale-distribution-offer).
- [EU TED Search API](https://docs.ted.europa.eu/api/latest/search.html); [TED search help](https://ted.europa.eu/en/help/search-browse).
- [Canada Book Fund publishing support](https://www.canada.ca/en/canadian-heritage/services/funding/book-fund/publishing-support.html); [UK PLR](https://www.gov.uk/government/collections/public-lending-right-rate-per-loan-consultations).

## 12. Limitations and handoff

- The national-program scan meets the requested 36-candidate first screen, not exhaustive legal diligence. Only Norway, France, selected procurement/distribution routes and specific sales panels received deep treatment; “unknown” remains explicit.
- No retailer API was tested and no external account was created. Absence of a verified public API is not proof that a private partner API does not exist.
- No paid prices are asserted where current public pricing was not verified. Panel access should be quoted only against a specific decision question.
- No prospective 20–30 candidate search, topic selection, product brief or three-book cohort was performed.
- Recommendation: owner review, then authorize only the free/manual first pilot and choose its hypothesis. Radar V2 should remain gated jointly on pilot results and future D30 evidence.

**Final status: PARTIAL.** The research sufficiently answers the method and source-selection question to recommend what to test; it does not validate a future book opportunity or justify a production change.
