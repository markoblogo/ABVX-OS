# Book Radar discovery

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
