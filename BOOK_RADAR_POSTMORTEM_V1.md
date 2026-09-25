# Book Radar Postmortem v1

**Scope.** Evidence-based analysis of the first Radar-native KDP cohort. This
audit changes no score, record, gate, schema, production workflow, or Amazon
listing.

**Evidence language.** **Observation** is a retained first-party or dated
research record. **Inference** is a bounded interpretation. **Hypothesis** is
testable but unproven. `UNKNOWN` means the repository does not establish it.

## Executive Summary

### What happened

**Observation.** The authenticated KDP Bookshelf check on 2026-09-21 showed
the sampled September products as Live. Orders for September 1-21 were 12
processed units: 8 eBooks and 4 print units; KENP was 106 pages and estimated
royalties were EUR51.85. The title-level distribution is in the
[KDP snapshot](book-radar/runs/kdp-weekly/2026-09-21/snapshot.json).

**Observation.** In completed first-14-day windows, PMP, Ham, French road
rules, and Solar had zero processed units. PMP had 10 KENP pages. The
non-Radar *Odyssey: Toki Pona Edition* had one print unit. These are outcomes,
not causes.

**Inference.** This is an early negative commercial signal for the first
Radar-native cohort, but does not prove selection failure. KDP records orders
and KENP, not impressions, search position, page visits, clicks, or checkout
conversion. Four zero-unit launch windows cannot tell whether the problem is
absent demand, poor Amazon intent, indexing, no exposure, weak result-tile
appeal, conversion, price, or normal variance.

**Observation.** The canonical Radar state has five product records but zero
`actuals` and zero `calibrations`; meanwhile first-party KDP observations are
stored in run artifacts. This makes a reproducible prediction-to-outcome
analysis impossible today. See [state](book-radar/state.json) and the
[weekly snapshots](book-radar/runs/kdp-weekly/).

**Most actionable finding.** The central weakness is the post-publication
discovery/measurement loop, not yet a demonstrated flaw in problem discovery.
The next information-gaining step is to measure discovery for already-live
books before producing another random niche.

## Current Radar Architecture

### What Radar actually does

**Observation.** Radar is local persistent memory for opportunities, evidence,
scores, decisions, products, portfolio products, similarity results, launches,
actuals and calibrations. It is designed to record, not autonomously research,
produce, publish, or spend. See [Book Radar](docs/book-radar.md) and
[implementation](src/abvx_harness/book_radar.py).

1. **Discovery/scoring.** `radar-native-v1` weights demand, momentum,
   competition weakness, newcomer viability, production feasibility, shelf
   life, economics, new-entrant evidence, and evidence quality. It penalizes
   paid-ad dependence and rights/compliance risk. It has no explicit metric for
   Amazon query intent, result-tile click appeal, conversion, or system/series
   potential. See [scoring model](book-radar/scoring-models/radar-native-v1.json).
2. **Evidence/gates.** Later discovery code distinguishes problem evidence,
   spending evidence, book-format demand, competitive gap, reachability and
   delivery fit. It explicitly says a listing is supply, and a topic trend or
   service spend is not book demand. See
   [discovery implementation](src/abvx_harness/book_radar_discovery.py) and
   [v4 strategy](book-radar/strategies/candidate-generation-v4-book-demand.json).
3. **Portfolio similarity.** Buyer, JTBD, trigger, promise, format,
   information architecture, search intent, audience and differentiation are
   compared; title similarity is intentionally excluded. This correctly
   diverted RN2-001 to an existing-product audit.
4. **Production quality.** Product-quality, human product, external KDP
   preview and commercial-package gates became stronger after real false
   positives. They validate manufacturability and reader quality, not demand.
5. **Feedback.** `actuals` and `calibrations` exist in the data model, but no
   canonical records exist. The reporting pathway is therefore present but not
   operationally closed.

### What works

- RN4 and RN6 both stopped at `NO PRODUCT`, rather than treating interesting
  problems as automatic book opportunities. See [RN4](book-radar/runs/rn4/radar-native-4-report.md)
  and [RN6](book-radar/runs/rn6/radar-native-6-report.md).
- Source, rights, currentness, production, and external-preview rigor improved
  from real feedback without inventing sales evidence.
- The active v5 strategy already addresses part of this audit: commercial
  evidence comes before production effort; it asks for comparable purchases and
  a reachable entrant path; it warns that no impressions means no conversion
  diagnosis. See [v5](book-radar/strategies/candidate-generation-v5-commercial-first.json).

### Observed architecture gaps

- **Canonical actuals gap.** KDP snapshots are not product-linked actuals, so
  `report experiments` cannot show D7/D14/D30 results or calibration error.
- **Marketplace-state drift.** Solar's internal package specifies $16.99 and
  a packaging state, while the authenticated Bookshelf observed a Live
  paperback at $15.99. This is a source-reconciliation problem, not a reason
  to alter its listing. See [Solar product state](book-radar/state.json) and
  [KDP snapshot](book-radar/runs/kdp-weekly/2026-09-21/snapshot.json).
- **No discovery snapshot.** There is no required list of actual buyer queries,
  result depth, indexing presence, sponsor density, competitor context, or
  recommendation-surface observation after launch.
- **No causal measurement contract.** No record binds a fixed listing state to
  impressions, clicks, spend, attributed orders, KENP, and an equal control
  window.

## RN1–RN6 Reconstruction

`D7` and `D14` are `UNKNOWN` unless a retained dated observation covers the
completed window. Submission is not itself a verified storefront-live date;
the September 21 Bookshelf observation is the availability evidence.

| RN | Product / thesis | Buyer / trigger | Expected Amazon query path | Evidence at decision | Decision / prediction | Published state | D7 / D14 / latest |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RN1 | *Project Management Certification in 2026*, a compact PMP orientation guide | Prospective PMP candidate needing orientation/eligibility clarity | PMP 2026; new PMP exam; PMP eligibility; PMP explained | Currentness/source rigor retained. Market demand, competition, WTP, numeric prediction and price-band evidence are **UNKNOWN** in its normalized import | Selected; prediction is `null` | Submitted 2026-09-04; Bookshelf later shows Kindle $4.99 and paperback $9.99, Live | D7 UNKNOWN; D14: 0 units, 10 KENP; latest same |
| RN2 | *Ham Radio Technician Visual Cram Map 2026-2030* | First-time Technician candidate during pool transition | ham radio technician 2026 2030 study guide | Query reportedly 521-526 results; a June 2026 entrant had 21 ratings and BSR 17,899; official pool reset. Estimated 20-50 90-day units / $76-260 gross royalty | Investment gate authorized; price $6.99 Kindle / $17.99 paperback | Submitted 2026-09-06; both formats later observed Live | D7 UNKNOWN; D14: 0 units, 0 KENP; latest same |
| RN3 | French road rules/signs FR-UA transition guide | Ukrainian novice or Ukrainian driver transferring knowledge to France | Ukrainian/French visual sign-atlas cluster on Amazon.fr | One recent Ukrainian comparable showed reviews/BSR; authoritative-source and paid-value gates passed; numeric forecast is **UNKNOWN** | Winner; print-first due Ukrainian Kindle constraint | Submitted 2026-09-07; paperback later observed Live at EUR16.70 | D7 UNKNOWN; D14: 0 units; latest same |
| RN4 | No product | Finalists included wedding speech, eulogy, home construction, VSME and watercolor jobs | Query-specific shelves | Real problems but weak paid-book/newcomer evidence, saturation, trust or production risk | `NO PRODUCT` after 200 screened / 18 deep-scanned | Not applicable | Not applicable |
| RN5 | *Solar Proposal Decoder*, quote-to-decision system | U.S. homeowner with 2+ solar/battery proposals before signing | Exact workbook query plus adjacent solar-buyer shelf | Strong external problem evidence; adjacent book traction. Exact book intent was explicitly the main risk. Estimated 30 90-day units / $195 / $16.99 | Conditional go; human product gates passed | Internal package says $16.99; Bookshelf shows Live paperback at **$15.99** | D7 UNKNOWN; D14: 0 units; latest same |
| RN6 | No product | 330 buyer-job markets; closest was First Swim Meet Parent Map | Query/channel checked | Real recurring problem, but free guides and no recent entrant / book-demand evidence | `NO PRODUCT` after 330 screened / 27 deep-scanned | Not applicable | Not applicable |

Evidence sources: [RN1 import](book-radar/imports/pmp-radar-native-1.json),
[RN2 opportunity](book-radar/imports/radar-native-2-opportunities.json),
[RN3 report](book-radar/runs/rn3/radar-native-3-report.md),
[RN5 report](book-radar/runs/rn5/radar-native-5-report.md), and the
[latest KDP snapshot](book-radar/runs/kdp-weekly/2026-09-21/snapshot.json).

## Toki Pona Positive Control

### Observation

September unit sales are spread across several Toki Pona products: Seneca (3),
*A Christmas Carol* (2), Epictetus (2), Meditations (1), Cicero (1), *The Tiny
Language Protocol* (1), and the new *Odyssey* (1 print). This is more than one
accidental bestseller. It remains too small to establish causal effects or a
stable revenue rate.

| Property | Toki Pona system / Odyssey | Radar-native standalone cohort |
| --- | --- | --- |
| Audience identity | Named language community with a shared cultural context | Broad professional/consumer problems; RN3 adds a narrow bilingual transition |
| Product legibility | Familiar source + Toki Pona transformation is visible in the title | Buyer payoff usually depends on a longer subtitle and use case |
| Amazon-native intent | Plausible direct audience/source/format queries | Query clusters named, but not verified as live discovery paths |
| Product system | Repeatable source transformation, collection behavior, potential cross-sell | Four unrelated one-off theses |
| Differentiation | Source familiarity plus language/sitelen transformation | Information architecture/workflow value, harder to infer from a tile |
| Economics | Reusable source and format pipeline | Research and QA cost resets for each product |

**Inference.** Toki Pona is a credible repeatable micro-market product system:
audience identity + known material + clear format + low direct substitutability
+ reusable pipeline. It is a positive control, not a Radar-native success and
not proof that any language community will behave the same way.

**UNKNOWN.** Repeat-buyer share, cross-sell attribution, query rank, category
placement, external community referrals, and why the Odyssey order occurred.

## Funnel / Failure-Chain Analysis

Legend: **SUPPORTED**, **WEAKLY SUPPORTED**, **UNKNOWN**, **CONTRADICTED**.
`CONTRADICTED` is not used for an early zero-unit result.

| Product | Real demand | Purchase intent | Book intent | Amazon intent | Discoverability | Click appeal | Conversion | Economics |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PMP | WEAKLY SUPPORTED | WEAKLY SUPPORTED | WEAKLY SUPPORTED | WEAKLY SUPPORTED | UNKNOWN | UNKNOWN | UNKNOWN | WEAKLY SUPPORTED |
| Ham | SUPPORTED | SUPPORTED | WEAKLY SUPPORTED | SUPPORTED | UNKNOWN | UNKNOWN | UNKNOWN | WEAKLY SUPPORTED |
| French road rules | WEAKLY SUPPORTED | WEAKLY SUPPORTED | WEAKLY SUPPORTED | WEAKLY SUPPORTED | UNKNOWN | UNKNOWN | UNKNOWN | WEAKLY SUPPORTED |
| Solar | SUPPORTED | SUPPORTED | WEAKLY SUPPORTED | WEAKLY SUPPORTED | UNKNOWN | UNKNOWN | UNKNOWN | WEAKLY SUPPORTED |

### Interpretation

**Observation.** The cohort had its strongest evidence at real problem,
authoritative content, production feasibility, and product quality. RN4/RN6
prove later gates can reject insufficient commercial evidence.

**Inference.** The thin links are usually “will this buyer purchase a book?”
and “will Amazon show this particular book for a usable query?” The system often
names the uncertainty, especially for Solar, but does not make it a measured
pre-publication condition.

**UNKNOWN.** Exact indexing, organic depth, recommendation exposure, thumbnail
comparative appeal, sessions, add-to-cart rate, and checkout conversion.

## What Radar Currently Knows vs Assumes

| Dimension | Current evidence capability | Cohort state |
| --- | --- | --- |
| Buyer problem | Strong: official sources, external research, community signals | Often supported |
| WTP | Mixed: price/ratings/BSR proxies | Proxy-heavy |
| Naturalness of book | Improved in v4/v5 | Solar explicitly uncertain; early cohort mixed |
| Amazon search intent | Query can be named | Not verified after launch |
| Reachable entrant | Newcomer listings/ratings/BSR proxies | Better than pain alone, still surrogate evidence |
| Click appeal | No fixed result-context review | UNKNOWN |
| Conversion | No traffic denominator | UNKNOWN |
| Repeatable-system potential | Portfolio similarity exists | No explicit v1 commercial dimension |
| Calibration | Schema exists | Canonical actuals/calibrations empty |

### Predictive-logic finding

**Inference.** The original v1 weights are relatively exposed to a false
positive from visible pain, narrowness, production ease, apparent competition
weakness, and newcomer evidence because they do not directly score book intent,
Amazon query intent, result-tile appeal, or series/system potential. This is
not proof that the weights alone caused the launches' early outcome.

**Counterevidence.** RN4-RN6 already corrected part of this by rejecting ideas
whose community/external problem evidence did not become paid-book evidence.
The earlier [effectiveness audit](book-radar/audits/discovery-effectiveness-rn4-rn6-audit.md)
reached the same limited conclusion: gates work, while early promotion/final
ranking need better commercial signals.

## Marketplace/Product-Fit Findings

1. A real, costly problem may naturally resolve through a service, software,
   installer, course, or free official material rather than a book.
2. An empty exact query can be a product gap or merely no book-buying query;
   Solar was explicitly exposed to this ambiguity.
3. A visual/workbook payoff can be real yet difficult to understand from title,
   cover thumbnail, and price alone.
4. Ukrainian Kindle ineligibility removes a format and KENP route from RN3.
5. Standalone products must win first discovery alone; Toki Pona may benefit
   from collection, audience, and recognizable-source signals.

## Toki Pona as a Repeatable Product System

The better question may be “what repeatable micro-market product systems can
we build?” rather than only “what unmet problems could become books?”

**Supported:** repeated titles produce orders; a new release did too; source
and format reuse reduce cost.

**Not supported:** that the system scales to EUR1,000/month; that its mechanism
is series behavior rather than individual titles; or that it transfers to other
niches.

**Minimal implication:** compare one system hypothesis with one standalone
hypothesis in the next learning cohort. Do not force all future products into
series or replace standalone discovery.

## Amazon Discovery Blind Spot

The owner hypothesis that Amazon may suppress organic reach while promoting ads
is **UNVERIFIED**. Repository evidence has no impressions, organic rank, or
controlled test capable of distinguishing platform conduct from ranking,
metadata/indexing, demand, seasonality, or conversion. It must not drive a
redesign.

### Amazon Discovery Audit v1 (proposal; do not implement yet)

For each live test title, capture `D14_DISCOVERY_SNAPSHOT` at D14 and D30:

```json
{
  "book_id": "product:example",
  "observed_at": "YYYY-MM-DD",
  "window": "D14",
  "marketplace": "Amazon.com",
  "listing_state": {"asin": "...", "format": "paperback", "price": 0, "live": true},
  "queries": [{
    "query": "real buyer wording",
    "origin": "buyer/competitor/autocomplete",
    "book_present": true,
    "organic_position_or_depth": "page 2 / position 14",
    "sponsored_density": 0,
    "top_competitors": [{"asin": "...", "price": 0, "format": "...", "review_count": 0}],
    "tile_assessment": {"title_legibility": "...", "cover_legibility": "...", "price_context": "..."}
  }],
  "categories_and_indexing": "observed/unknown",
  "recommendation_surfaces": "observed/unknown",
  "limitations": ["volatile personalized result pages"]
}
```

Use 5-10 realistic queries per title; retain screenshots/URLs; distinguish
sponsored from organic; record competitors in context; never infer impressions
from rank. This is a diagnosis record, not a new score until several snapshots
exist.

## Paid Discovery Experiment

### Purpose

Use paid discovery as a measurement instrument, not a revenue campaign. It can
separate low impressions from low CTR and clicks-without-attributed-orders. It
cannot establish long-run organic demand.

### Smallest useful design (proposal; not launched)

- **Budget:** EUR20-50 total after separate approval; a hard daily cap and no
  automatic renewal.
- **Products:** one Radar-native product with clear direct queries (Ham is the
  cleanest candidate) and one Toki Pona control. Do not spread the budget over
  all four Radar launches.
- **Window:** same 14 consecutive days, fixed marketplace, price, and listing
  state. No simultaneous cover/description/category changes.
- **Targeting:** 5-10 exact/phrase buyer queries per product; small competitor
  ASIN set only if relevant.
- **Record:** daily impressions, clicks, CTR, CPC, spend, attributed orders,
  attributed KENP, and organic orders/KENP for identical dates.
- **Stop:** fixed end date or hard budget cap; do not optimize bids mid-test.

Interpretation: no impressions suggests targeting/indexing/reachability; low
CTR versus control suggests query/tile appeal; clicks without orders leaves
proposition/page/price ambiguous; any orders/KENP are positive evidence, not a
scalability proof.

## Proposed Radar v2 Changes

These are proposals only. Active v4/v5 strategy already overlaps some items;
historical records should remain immutable and RN1-RN6 should not be rescored.

### A. Keep

- `NO PRODUCT` hard stops: RN4/RN6 show useful restraint.
- Portfolio Similarity Gate: it caught an existing-product collision.
- Human product / external KDP preview gates: they caught real quality defects.
- Source, rights and currentness QA proportional to product risk.

### B. Modify

- Treat an empty exact query as ambiguity, never automatic competition
  weakness. Motivation: Solar's explicit exact-book-intent risk.
- Make direct book buying and Amazon-query evidence visible before final
  selection. Risk: excessive incumbent bias; mitigation: one exploratory cell.
- Mark each opportunity `STANDALONE` or `SYSTEM` hypothesis. Motivation:
  Toki Pona differs structurally from the cohort; risk: overfitting to one
  small niche.
- Require a D0 observed marketplace-state reconciliation before a D14 outcome
  is interpreted. Motivation: Solar price/status drift.

### C. Add

- Append-only product-linked D0/D7/D14/D30 actuals.
- `D14_DISCOVERY_SNAPSHOT` and fixed query sets.
- A result-context rubric for title, cover and price legibility.
- A paid-discovery diagnostic contract with precommitted control, spend cap and
  stop rule.
- A system/series evidence card as an experimental dimension, not a permanent
  scoring weight.

### D. Remove or de-emphasize

- Generic community discussion, naked Amazon result counts, and an
  informational gap as strong positive signals without book-buying evidence.
- Production speed as compensation for weak commercial evidence.
- Any diagnosis of “no demand” or “bad conversion” from zero sales without
  visibility data.
- A complex recommendation engine before the missing measurement layer exists.

## Next Cohort Experimental Design

Do not start RN7 until discovery data exists for current releases. When it is
authorized, use a two-cell learning cohort rather than another broad random
scan:

1. **System cell:** a Toki Pona-adjacent public-domain/classic transformation
   selected against a clear audience/query/series baseline.
2. **Standalone search cell:** an established book category with direct buyer
   query language, recent reachable entrant evidence, a natural book job, and
   a precommitted D14 discovery plan.

Hold marketplace, format, observation windows, and packaging interventions as
stable as practical. Do not combine an unproven query, new language, novel
format, authority-heavy subject, and paid acquisition dependence in one test.

Before a production decision, require two independent observations of
comparable book buying or reachable newcomer traction; one documented
book-shaped query; a reason to choose a book over a free web/service solution;
D0 state plus D14 query plan; a declared standalone/system cell; and no open
rights, expertise, format, or product-quality gate.

## Open Questions

1. Are the four Radar-native products present for their intended queries?
2. Do those queries have meaningful Amazon shopper traffic?
3. Do title/cover/price communicate value at result-tile scale?
4. Is Solar's observed $15.99 intentional, and which future capture should be
   canonical?
5. What share of Toki Pona orders comes from series/repeat buyers versus source
   recognition or external community traffic?
6. Can EUR20-50 generate enough signal for a CTR/conversion diagnosis?

## Recommended Next Actions

1. Review this report; do not change Radar scoring yet.
2. Run a read-only D14 discovery snapshot for the four Radar-native titles and
   Odyssey using the fixed-query method above.
3. Reconcile observed Bookshelf state to Radar only after deciding the capture
   process; do not silently overwrite historical evidence.
4. If separately approved, run the one-treatment/one-control ad diagnostic.
5. Then decide whether RN7 is a standalone cell, a system cell, or `NO PRODUCT`.

## Decision

1. **Is there enough evidence that opportunity selection is failing?** **No.**
   The early outcome is weak, but no discovery or conversion denominator exists.
2. **Strongest weakness?** Marketplace-product-fit evidence and the
   post-launch measurement loop: book intent, query reachability, tile appeal,
   and canonical actuals/calibration.
3. **What cannot be diagnosed?** Organic exposure, indexing, rank, CTR,
   detail-page conversion, and alleged platform suppression.
4. **What should change before RN7?** Precommit a discovery observation plan,
   capture D0/D14/D30 actuals, and compare a system cell with a standalone cell.
5. **What should not change?** Do not rewrite weights, abandon `NO PRODUCT`,
   alter prices, or discard standalone opportunities from four weak windows.
6. **Highest-information experiment?** A fixed-query D14 discovery audit,
   followed only with separate approval by a EUR20-50 two-book Amazon Ads
   diagnostic: one direct-query Radar title versus one Toki Pona control.
