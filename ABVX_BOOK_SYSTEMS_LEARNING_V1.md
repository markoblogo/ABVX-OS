# ABVX Book Systems Learning V1

## Purpose

This is the control-plane entry point for learning from book experiments. It links retained run evidence to small, append-only learning records. It does not own manuscripts, translations, Pictiq vocabulary, Book Radar logic, publication, or sales claims.

The loop is: run → observation → inference → hypothesis → tested practice → promotion.

## Existing Learning Infrastructure

| Domain | Existing | Partial | Missing / stale |
| --- | --- | --- | --- |
| Book Radar | Book Radar runs, imports, state, audits, D0/D14/D30 design; platform lessons | Actuals/calibration structures exist but are not operationally complete for every launch | Paid-discovery diagnostic remains proposed, not a practice |
| Generative fiction | Bracken Ford audit, product spec, architecture, world/source records, bounded draft | Development results are project-local | No prior cross-book process record |
| Toki Pona | Book Radar imports, production contracts, QA/preflight artifacts, Jekyll pre-production artifacts | Catalogue-wide translation/name/sitelen learning is dispersed | One canonical factory delta record |
| Pictiq editorial | Protected Pictiq core, crosswalk/renderer/composer and visual-evaluation evidence live in the independent project | No book-insert evaluation exists | Narrative-comics benchmark and result record |

The existing platform lesson register remains canonical for platform-capability lessons. The book-systems record is the canonical book-learning register. It may point to platform lessons; it must not duplicate them.

## Canonical Locations

- learning/book-systems/records.jsonl — append-only book learning records.
- learning/book-systems/LEARNING_DELTA_TEMPLATE.md — small post-run capture form.
- learning/book-systems/PICTIQ_NARRATIVE_BENCHMARK_V1_PROPOSAL.md — unexecuted narrative-comics specification.
- Existing evidence remains at its original source paths.

## Learning Record Model

Every record contains: ID, date, domain, run/product, stage, observation, evidence, interpretation, lesson, confidence, scope, status, system-change candidate, validation required, and next test.

Statuses are OBSERVED, HYPOTHESIS, VALIDATED_ONCE, VALIDATED_REPEATEDLY, PROMOTED_TO_PRACTICE, REJECTED, and SUPERSEDED.

Observation is what happened. Inference is what it may mean. Hypothesis is a proposed test. Practice is a repeated, evidence-backed default. A status change appends a successor record; it never rewrites the original record.

## Promotion Rules

1. One observation: log it only.
2. Repeated observation or a successful bounded validation: nominate a practice.
3. Repeated success across relevant runs: promote to a skill, template, gate, QA check, automation, schema, or Radar strategy.
4. A promotion changes only its named destination after separate review; a record never mutates a system automatically.

## Post-Run Capture

At a meaningful book-stage completion, append only what is new: link evidence; separate observation from inference; add a successor only when status changes; name one next test or deferred change. This must take minutes, not produce a retrospective by default.

## Radar Learning

The register records the current evidence: problem evidence differs from book intent; book intent differs from Amazon-native query demand; and zero sales without visibility data does not diagnose demand or conversion. Toki Pona is a positive control for a repeatable micro-market, not proof of portfolio-scale economics. D0/D14/D30 discovery snapshots and a paid-discovery comparison are experiments, not promoted practice.

## Generative Fiction Learning

Bracken Ford's print and Kindle editions are author-reported as submitted; live listing links and identifiers remain unverified. Its reusable lesson is not its plot: cheap prototype → commercial audit → architecture gate → bounded prose gate can prevent a full draft from being justified by sunk cost alone. The completed run adds a canonical-source manifest, distinct structure/product completion states, reader-facing cleanliness before editorial acceptance, per-asset provenance, and format-specific print/Kindle gates. See `BRACKEN_FORD_FACTORY_POSTMORTEM_V1.md` and BSL-017. Human editorial attention remains a constrained downstream resource.

## Toki Pona Learning

Separate product-system, translation, sitelen pona, layout/KDP, and automation lessons. Existing production artifacts support gated source ingestion, format-specific QA, and explicit preflight. The Jekyll work is pre-production only. Catalogue sales support a small repeatable thesis, not the €1,000/month portfolio target.

## Pictiq Editorial Learning

Pictiq remains independently owned. No vocabulary, grammar, renderer, or icon changes are implied here. The proposed benchmark tests narrative comprehension, not visual appeal alone; any missing symbol/operator becomes a separate PICTIQ_CHANGE_CANDIDATE.

## Cross-System Learning

Generative fiction supplies narrative stress cases for Pictiq. Toki Pona supplies visual-language production and layout experience. Radar may later measure discovery/click effects of differentiated visual features. None of these relationships establishes a sales claim.

## Open Hypotheses

- A fixed D14 discovery snapshot improves diagnosis of zero-unit launches.
- A system/standalone comparison explains part of the Toki Pona/Radar difference.
- Bounded architecture gates reduce wasted human fiction-editing effort.
- Four-to-five-panel Pictiq inserts can convey narrative relations without uncontrolled vocabulary growth.

## Next Experiments

1. Capture the next D0/D14 Radar state using a fixed query set.
2. Return the active production slot to the Jekyll Toki Pona provider regression; keep Bracken Ford's launch observation plan dormant until live links exist.
3. Seek explicit approval before executing either Pictiq narrative-comics sample.
