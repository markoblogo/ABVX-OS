# Amazon Discovery Audit v1

Observed 21 September 2026. This is a read-only current snapshot, not a reconstruction of an exact day-14 Amazon page. Historical launch and sales windows remain in `book-radar/runs/kdp-weekly/2026-09-21/snapshot.json`; per-book structured observations are in `book-radar/runs/discovery-audit-v1/2026-09-21/`.

## Executive Summary

The four zero-unit Radar-native launches do not form one diagnosis. The limited observable evidence separates them: PMP and Ham entered real but saturated exam-prep shelves and were not found in the sampled major query's first result set; Solar's direct buyer phrase did not produce a meaningful homeowner-book shelf; French Road Rules was the sole organic result for the narrow bilingual query. Odyssey is a structural positive control: a source-plus-language query produces a tiny, legible, product-native set in which the book is the first non-sponsored result. One Odyssey print order is not evidence that discovery caused that sale.

## Method and limitations

- Direct listing pages and one high-intent search were observed for each product on 21 September 2026.
- `amazon.com` was an authenticated, personalized shopper session with international delivery settings. `amazon.fr` was signed out. Results, ads, availability and recommendations can vary by account, device, location and time.
- Exact rank is reported only where the rendered page exposed it. `NOT_FOUND` means absent from the observed result depth, never unindexed.
- Five realistic query paths per product are preserved in each snapshot. Only the highest-information one was sampled in this pass; remaining observations are deliberately `UNKNOWN`, not guessed.
- Amazon does not expose impressions, organic clicks, conversion, keyword indexing, or recommendation eligibility here. Sponsored tiles are labeled separately.

## Product reconstruction and observations

### PMP

**Listing.** *PMP 2026 in a Nutshell: A Plain-English Guide to the New PMP Exam, Project Management Fundamentals, and Whether PMP Is Right for You*; Amazon.com; Kindle ASIN `B0HHTMHW3Z` at $4.99 and paperback `B0HHTQMBVR` at $9.99; published 4 September. Original thesis: a compact orientation book for a person deciding whether to pursue PMP, rather than another question bank. The historical D14 window records zero units and 10 KENP pages.

`pmp 2026 guide` returned 362 results. The book was not among the first 16. The visible organic and sponsored products repeatedly promise 240–2,880 questions, mock exams, pass plans and full study systems; recognizable competitors include *PMP Exam Prep 2026* by Lauren Cartwright, Castmark's 2026–27 guide (18 ratings), and Mometrix study cards (109 ratings). This is **D — highly saturated established shelf**. The sampled result context makes the book's non-exam-prep differentiation hard to infer quickly, although its low price is legible.

**Classification: DISCOVERED_TOO_DEEP** for the sampled major query; more query sampling would be required to generalize.

### Ham

**Listing.** *Ham Radio Technician Visual Cram Map 2026–2030: A Diagram-First Guide to FCC Element 2 Concepts, Rules and Question-Pool Connections*; Amazon.com; Kindle `B0HDJFP6BY` $6.99 and paperback `B0HHZRDSG4` $17.99; published 6 September. Original thesis: diagram-first conceptual companion to the 2026–30 Technician pool, not a 409-question replacement. Historical D14 window: zero units.

`ham radio technician 2026 study guide` returned 146 results. The book was not in the first 16. First-screen books and ads promise complete pools, practice tests and licensing success: Ham Prep (26 ratings), SwiftStudy (11), Ria Jairam (217), Morse Code Publishing (332) and several newer all-question guides. This is **D — highly saturated established shelf**. The title/cover communicate a visual cram map, but that is a thinner promise next to full-pool/test-prep offers.

**Classification: DISCOVERED_TOO_DEEP** for the sampled major query.

### French Road Rules

**Listing.** *Французькі правила й дорожні знаки українською: Практичний довідник для першого знайомства і перенесення водійського досвіду до Франції*; Amazon.fr; paperback `B0HJ3WMYKD` €17.62, published 7 September. Original thesis: Ukrainian newcomer and experienced-driver transition reference, with France–Ukraine comparison. Historical D14 window: zero units.

`code de la route francais ukrainien` returned exactly one organic result: this book, at position 1. Below it, Amazon showed several French driving-test sponsored products (€9.97–€19.97). The bilingual result is immediately legible and competitively priced, but it represents a very narrow query. The direct product page's breadcrumb sat in linguistics, not driving, which is a possible indexing/category anomaly worth observing later, not a conclusion.

**Classification: VISIBLE_AND_COMPETITIVE** for the narrow bilingual query; overall demand and broader discoverability remain **INSUFFICIENT_EVIDENCE**.

### Solar Proposal Decoder

**Listing.** *Solar Proposal Decoder: A Homeowner's System for Comparing Quotes, Financing, Production Claims, Scope, and Warranties Before Signing*; Amazon.com paperback `B0HJ3VVDK8`, $15.99, published 7 September. Original thesis: a buyer-owned system for normalizing multiple proposals before a high-value purchase. Historical D14 window: zero units.

`solar proposal comparison workbook` returned one irrelevant PV-career workbook and an out-of-print institutional title; it did not return the book. The direct listing is clear and in stock, but visible category/related offerings skew toward off-grid installation and self-reliance, including high-review DIY books rather than homeowner quote comparison. The issue is not established as indexing failure: the stronger current hypothesis is **C — primarily non-book/problem search**. People with this job may begin with installers, calculators, consumer sites, spreadsheets, or web search rather than an Amazon book query.

**Classification: NO_MEANINGFUL_QUERY** for the sampled direct query; conversion cannot be diagnosed yet.

### Odyssey — positive control

**Listing.** *The Odyssey: Toki Pona Edition with Sitelen Pona (Stoic Wisdom in Toki Pona)*; Amazon.com Kindle `B0HHSK3Y45` $7.99 (fixed layout) and paperback `B0HHSMS6KQ` $29.99; published 4 September. It extends the existing Toki Pona catalogue and had one processed print order in its first 14-day window.

`the odyssey toki pona` returned three results: a sponsored general Odyssey graphic novel, then this book as the first non-sponsored result, then *Toki Pona: The Language of Good*. The tile exposes a named source, a named niche language and sitelen pona; the series is also visibly linked from the detail page. This is **A — small established book-buying niche**, not a broad high-volume market.

**Classification: VISIBLE_AND_COMPETITIVE** on its direct product-language query. It is a positive-control structural signal, not a sales explanation.

## Cross-product matrix

| Product | Book intent | Amazon intent | Query clarity | Organic presence | Organic depth | Competition | Sponsored density | Tile legibility | Price context | Recommendation evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| PMP | established | established | adequate | not in sample | beyond first 16 | saturated | high | weak | strong | none relevant |
| Ham | established | established | adequate | not in sample | beyond first 16 | saturated | high | adequate | adequate | none relevant |
| French | narrow | plausible | strong | observed | 1/1 narrow query | adjacent exam shelf | high below organic | strong | adequate | uncertain |
| Solar | uncertain | weak | weak | not observed | no peer shelf | mismatched DIY shelf | n/a | untested in peer tile | adequate | mismatched |
| Odyssey | small niche | strong | strong | observed | first non-sponsored | low direct-query competition | moderate | strong | adequate | series link; generic related uncertain |

## What the four zeroes mean now

1. **Poor discovery is a reasonable partial hypothesis for PMP and Ham** on the sampled high-intent queries: neither appeared in the first observed result set. It is not yet causal attribution.
2. **French Road Rules is discoverable enough on one highly specific query** that proposition/conversion and small total query demand are now more interesting than basic indexing. The sample does not prove it reaches broader buyers.
3. **Solar's intended query does not currently look like a meaningful Amazon book-buying market.** That is the clearest finding in this audit.
4. Without impression, click, search-volume and conversion data, we cannot know search demand, actual rank across queries, click-through, listing conversion, recommendation eligibility, or whether any buyer saw a result.
5. **French Road Rules** is the best later paid-diagnostic candidate: it has an observed organic entry point, a legible buyer/language proposition, and one coherent paperback format. This is a future diagnostic selection, not authorization to run ads.
6. **Odyssey changes the interpretation structurally, not causally.** It shows how source + niche-language + visible collection context can form an Amazon-native object query; its single order does not establish a performance benchmark.
