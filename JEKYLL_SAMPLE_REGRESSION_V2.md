# Jekyll Sample Regression V2

This is a pipeline regression, not a complete translation. The exact representative source used by `JEKYLL_TOKI_PONA_PREPRODUCTION_V1.md` was segmented and rerun through the new local runner. The old sample and all V1 artifacts remain intact.

## Old Sample

The V1 sample was manually assembled and model-edited. It exposed fragile handling of conditional succession, evidence, character inference, proper names, and narrative identity.

## New Sample

V2 contains 40 stable source blocks, a persisted run manifest, translated block records, entity registry, phrase/constraint metadata, alignment/name/spoiler reports, sitelen input/output, and a 3-page 6×9 layout proof. The translation provider is explicitly marked `fixture-backed-local-regression`; it is not presented as a production literary provider.

## Old vs New

| Area | V1 status | V2 status |
|---|---|---|
| Stable block identity | absent | FIXED |
| Source/output alignment | manual | FIXED mechanically |
| Resume after block failure | absent | FIXED and tested |
| Proper-name allowlist | fragile | IMPROVED; ledger-backed |
| Knowledge metadata | implicit | IMPROVED; review flags |
| Spoiler checks | manual | IMPROVED; bounded checker |
| Literary quality | model/editorial | HUMAN_JUDGMENT_REQUIRED |
| Provider path | assumed/deployed URL | UNRESOLVED |

## Previously Known Failures

The same semantic targets remain review fixtures:

| Source function | Old problem | New status |
|---|---|---|
| unexplained three-month absence | conditional duration could be flattened | HUMAN_JUDGMENT_REQUIRED |
| succession condition | death/disappearance alternatives at risk | HUMAN_JUDGMENT_REQUIRED |
| Utterson judgement | inference could become fact | IMPROVED; flagged by knowledge metadata |
| Lanyon opinion | opinion could become diagnosis | IMPROVED; flagged for review |
| safe / escape | claim could become verified fact | HUMAN_JUDGMENT_REQUIRED |
| grounds for certainty | hidden knowledge boundary | IMPROVED; review constraint |
| trust / confidence | semantic distinction fragile | HUMAN_JUDGMENT_REQUIRED |
| lead / move | movement meaning requires editorial context | HUMAN_JUDGMENT_REQUIRED |
| laboratory / dissecting rooms / cabinet | locations could collapse | IMPROVED by entity/phrasebook data |
| proper names | inconsistent or semanticized | FIXED mechanically for approved forms |
| Poole fear / rhythm | emotion could become event fact | IMPROVED; review flag |
| identity / spoiler | premature relation disclosure risk | REVIEW; checker active |

No item is labelled FIXED merely because a string changed. Literary rows remain bounded human review.

## Alignment

Machine alignment is PASS: source and output counts match, order is preserved, and no missing/duplicate/unknown/empty block was emitted. The report is at `artifacts/jekyll-toki-pona-regression-v2/qa-results.json`.

## Names

The allowlist is derived from `JEKYLL_ENTITY_LEDGER_V1.json`. `jan Jekil` and `jan Hata` remain distinct; an unapproved `jan Xata` fails validation. Sitelen uses a deterministic styled-Latin cartouche fallback (`⟦jan …⟧`) for the sample.

## Knowledge Boundaries

Inference, document claims, and dialogue claims are stored as review metadata. The checker returns REVIEW rather than claiming that a model translation is semantically certified.

## Spoiler Preservation

Identity-sensitive blocks are flagged; no guide gloss is generated. The pipeline has a bounded early-disclosure detector, but literary spoiler review remains human.

## Sitelen

The same sample renders with the existing sitelen font and deterministic name fallback. The 3-page sample layout is technically readable and has no new overflow signal. Full-book density is not yet proven.

## Layout

6 × 9 black-ink sample: 3 pages, English → Latin Toki Pona → sitelen pona. It is at least as technically readable as V1. The layout is a copied V1 proof with V2 run metadata; a full book redesign is intentionally out of scope.

## Model Editorial Review

Model QA status: REVIEW. The new infrastructure makes fragile blocks visible and reviewable, but does not replace literary judgment. The existing V1 editorial review remains the baseline; a separate model pass is required after a real provider adapter is connected.

## Human Review Requirements

Review the will, letters, legal conditions, Lanyon opinion, Utterson inference, Poole fear, laboratory/cabinet distinctions, proper-name forms, and every spoiler flag. Confirm final Toki Pona voice and rhythm.

## Remaining Blockers

1. Resolve the current provider/deployment path; the previously tested public URL returned `NOT_FOUND`.
2. Connect an approved trusted translation adapter and record provider/model metadata.
3. Rerun the same sample with real output, then complete the human editorial gate.

## Regression Decision

**MODIFY_AND_RERUN.** The reusable pipeline foundations pass, but a production translation provider and the corresponding real-output editorial regression are still missing. Jekyll remains viable. No full translation, final paperback, cover, KDP metadata, or publication was started.
