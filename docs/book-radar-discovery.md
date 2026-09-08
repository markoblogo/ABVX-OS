# Book Radar discovery

## Active policy: commercial potential first (v5)

Current strategy: `book-radar/strategies/candidate-generation-v5-commercial-first.json`.
Use `validate_commercial_candidate`, `commercial_discovery_decision`, then
`rank_commercial_candidates` in `src/abvx_harness/book_radar_discovery.py`
for new runs. Do not pass new fiction/business cards through the historical
problem/gap validators below. Existing v3/v4 run formats and scoring stay intact.

Search unit: `READERSHIP × READING MOTIVATION × BOOK MARKET × READER PROMISE × CHANNEL`.
Explore fiction, business, popular nonfiction, hobbies, children/education,
gift/visual books and practical references. Reading for pleasure, curiosity,
identity, atmosphere or a gift is valid. No compulsory deadline, practical
problem, dissatisfied review or unprecedented mechanism is needed.

Start by comparing existing markets and several relevant titles, including
plausible entry by less established authors. Category demand and the ability
of a new book to reach readers are separate. Do not use celebrity success as
proof of accessible entry. Small markets may qualify on viable economics.

Commercial evidence is primary. Document demand, reason to choose our book,
reachability and unit economics with sources and uncertainties. Require two
independent origins for comparable purchases/traction; reviews and ranks remain
proxies, not unit-sales claims. Emotional and entertainment value need evidence
of reader preferences, not proof of a missing utilitarian feature.

Rank eligible cards by STRONG then MODERATE commercial tier, and within each
by LOW/MEDIUM/HIGH production effort. These are reasoned research bands, not
predictions. Easy production never rescues weak demand. Include full editing,
quality review, illustration, verification, rights and owner attention in cost.
Genre satisfaction and narrative quality are real production requirements.

When a concept reaches packaging, run a current listing-pattern gate before a
manuscript decision. Sample at least eight ranked titles and two detail pages;
separate established franchises from recent or less-established entries. Record
title/subtitle structure, series signaling, cover hierarchy, price, format,
description opening, progression promise and review language. These patterns are
correlations on a volatile retail surface, not explanations of sales.

If a live reader panel is unavailable, do not invent or simulate one. Use the
listing-pattern gate for the pre-production decision, then learn from the real
listing after publication. KDP orders, KENP and rank are market outcomes but do
not reveal impressions. Title and subtitle must be settled before publication;
test later changes only on mutable surfaces such as description, keywords,
categories, price and cover. Amazon Ads impressions and clicks may support a
conversion experiment only after separate spend authorization.

`last30days-skill` is admitted as an optional pre-card discovery sensor at the
pinned revision recorded in `book-radar/audits/last30days-skill-assessment.json`.
Use it to nominate fast-moving topics, recurring requests and audience language.
Its opt-in Amazon lane may supply current prices, ratings and recent review
samples. Never convert social engagement, prediction activity, ratings, reviews
or a trend label directly into book demand, reachability or unit economics.
Every nominated topic must still clear the normal independent market evidence
gates. Record unavailable sources as coverage limits rather than negative demand.

RN10 applied these limits across all market families without finalist quotas:
at most 20 cards, 5 deep checks and 2 concepts. Future runs retain those bounds
unless separately changed. No discovery result authorizes production. Leave portfolio listings,
Monday audit and its schedule untouched. RN9's prototype instruction is deferred;
preserve its artifacts as history. Read this active policy before any old run's
next-step instruction.

## Historical v3/v4 policy (for interpreting old records only)


The generation unit is a buyer situation, not a topic or title:

`BUYER × PURCHASE TRIGGER × JOB TO BE DONE × CURRENT SPEND × UNMET NEED`

Record who pays, the triggering event, desired result and deadline, current
solution and spend, dissatisfaction, publishing-format fit, and discovery
channel before proposing a product.

Assess six dimensions independently: problem evidence, spending evidence,
book-format demand, competitive gap, reachability, and delivery fit. Each is
`SUPPORTED`, `NEGATIVE`, or `UNKNOWN`; every non-unknown result needs source
evidence. Finalists need corroboration from independent publishers.

Route candidates to `REJECTED_ON_EVIDENCE`, `INSUFFICIENT_EVIDENCE`,
`ATTRACTIVE_BUT_NOT_FOR_US`, or `READY_FOR_VALIDATION`. Missing evidence is
not a rejection. Paid services do not prove book demand. A strong competitor
or free alternative matters only after testing whether an accessible paid
advantage remains. `READY_FOR_VALIDATION` never authorizes production.

Current executable rules live in
`src/abvx_harness/book_radar_discovery.py`; the experimental strategy is
`book-radar/strategies/candidate-generation-v4-book-demand.json`.

## Book-demand-first extension

From RN8, candidates enter deep scan only after recording why a buyer chooses
a book, workbook, or reference; the dated evidence for purchases of a
comparable format; the discovery path; and the unmet use scenario. Topic
interest, service spending, listings, reviews, BSR, suggestions, and trends
remain separate signals and are never converted into unit-sales claims.

Temporary opportunities record a confirmed or bounded trigger, demand window,
and preparation time. Public-domain status is tracked separately for the source
text, translations, illustrations, and packaging. Existing assets are matched
only after external demand is established; fit may route to a packaging audit,
scenario adaptation, new content, or no fit.

Zero-sales diagnosis is layered: verify public availability first, then
visibility, conversion, product fit, and observation duration. Without
impressions or verified live dates, zero sales is an observation with an
unknown denominator, not evidence of zero demand.

Authenticated portfolio evidence may be collected under
`docs/kdp-portfolio-audit.md`. This channel is read-only and must not be used
to change listings without a separate explicit publishing instruction.

## Observation-first evidence card

From RN9, do not formulate a concept before recording three separate
foundations: comparable book-purchase evidence, a specific buyer scenario, and
an accessible unmet scenario. Each card records the dated observation,
interpretation, alternative explanation, and an independence key. Repeated
pages or links from one origin count once.

Before deep scan, reject or hold candidates with unknown book purchasing,
unsupported gaps, fewer than two independent origins, blocked rights,
unavailable expertise, or a demand window shorter than production. A direct
request for free advice is not book-purchase evidence. An event plus an old
official guide is only an analogy until a current buyer path is visible.

The machine-readable card schema is
`schemas/book_radar_evidence_cards.schema.json`; behavioral gates live in
`src/abvx_harness/book_radar_discovery.py`.
