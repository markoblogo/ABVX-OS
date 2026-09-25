# Bracken Ford Book Factory Postmortem V1

**Run:** *No Further Claims: A Bracken Ford Novel*  
**Capture date:** 2026-09-23  
**State:** Kindle submitted / publishing; paperback submitted / in review, as reported by the author. Live pages and identifiers are not independently verified.  
**Scope:** factory learning only. No listing, manuscript, interior, cover, Pictiq asset, or Radar configuration was changed.

## New learning

| Classification | Evidence and finding | Decision |
|---|---|---|
| OBSERVATION → PROMOTE_TO_PRACTICE | Review-era files remained discoverable after the locked novel and final candidates existed; the illustration manifest still names an obsolete review manuscript/placement. The production handoff is more current but prose-only. | Use a small machine-readable manifest with `CANONICAL_SOURCE`, `SUPERSEDED`, `PROTOTYPE`, and `TEXT_LOCK`; retain history. Implemented for this title. One run does not justify migrating every book. |
| OBSERVATION → PROMOTE_TO_PRACTICE | V1's 11,249 words had a compressed middle and duplicate hearing/ending test variants while clearing substantial development; V2's causal expansion and cleanliness review supported `HUMAN_EDIT_GO`. | Separate `STRUCTURE_COMPLETE` from `PRODUCT_COMPLETE`; require a reader-facing cleanliness scan before editorial acceptance. BSL-016 already captures duplicate cleanup; this adds the gate distinction and timing. |
| OBSERVATION → PROMOTE_TO_PRACTICE | Illustrations were created before final text and placement changed as chapter structure matured. | Permit early asset exploration; finalize placement only after structural/editorial lock. Preserve asset identity/hash through re-placement. |
| OBSERVATION → AUTOMATION_CANDIDATE | The Pictiq case record does not retain a complete linked source→composer input→composer output→final composite chain with version/hash metadata. | Require that capture for future cases. Do not change vocabulary or infer missing historical provenance. |
| OBSERVATION → PROMOTE_TO_PRACTICE | Amazon packaging found insufficient local origin evidence for the composite drawings/cover to support the AI-image disclosure decision. | Capture origin (`GENERATED`, `HUMAN`, `AI_ASSISTED`), tool/provider, date, source, hash, and modification history per asset before packaging. Bracken asset origins remain unresolved locally. |
| OBSERVATION → PROMOTE_TO_PRACTICE | The first final-interior candidate placed the Pictiq copyright block beyond the print safe-area boundary; its successor passed after correction. | Keep automated live-area/bottom-margin checking plus full-page visual review. Existing QA already checks objects outside calculated live area; add explicit footer/attribution coverage. |
| OBSERVATION → PROMOTE_TO_PRACTICE | A generated wrap showed a placeholder rectangle in the barcode zone even though KDP supplies the barcode. | Barcode zone is background-only unless a real publisher barcode is intentionally used. Generate wraps from the actual KDP template after trim, paper, ink, and final page count are fixed; check spine constraints. |
| OBSERVATION → PROMOTE_TO_PRACTICE | Art resolved to about 195 effective DPI and passed human visual proof. This is one accepted run, not general resolution evidence. | Below 300 DPI triggers explicit human print-risk review, not automatic rejection or upscaling. |
| OBSERVATION → PROMOTE_TO_PRACTICE | EPUB structure passed locally, but Kindle Previewer was unavailable before submission. | Keep `EPUB_VALID` distinct from `KINDLE_RENDER_VERIFIED`; KDP preview remains the environment-specific gate. |
| OBSERVATION → PROMOTE_TO_PRACTICE | The Text Lock hash stayed stable through interior attribution. | After `TEXT_LOCKED`, prose edits require `TYPO`, `DEMONSTRATED_FACTUAL_ERROR`, or `PRODUCTION_FORMATTING_DEFECT`, with a successor lock and affected QA rerun. |
| OBSERVATION → NOT_ENOUGH_EVIDENCE | Commercial audit, architecture, anchor, structural, human-edit, text-lock, and production-proof gates addressed different risks. The author reports submission, but local evidence lacks final URLs or KDP preview results. | No gate is shown redundant. Do not claim the external preview passed without its evidence. Package only after product/text lock; freeze launch metadata and observe D0/D7/D14/D30. |

## Factory changes

- Added the project-local `work/ostrich-black-comedy-book/BRACKEN_FORD_CANONICAL_MANIFEST_V1.json` with current pointers, status vocabulary, Text Lock hash, author-reported submission state, empty identifier/date fields, asset hashes, and unresolved origins. Historical files remain intact.
- Added a per-asset provenance JSON Schema and tightened the existing production skill and visual QA contract for provenance, barcode zone, template timing, sub-300-DPI review, footer/live-area checks, and Kindle rendering.
- BSL-016 already records duplicate development variants; it was left unchanged. BSL-017 captures only additional observations.
- Deferred retroactive origin attribution until reliable source evidence exists; automation for every PDF footer/barcode/spine geometry; migration of other book folders; and all Radar scoring changes.

## Readiness and next action

Factory readiness for the next book: **READY**, with the manifest and checklist requirements above. Bracken Ford remains **SUBMITTED / AWAITING FINAL LIVE LINKS**, not independently verified as published. Return the active production slot to the Jekyll Toki Pona provider regression.

## Append-only outcome note — publication closeout, 2026-09-23

The status above is the preserved pre-publication observation from this postmortem's capture. It is superseded by the dated closeout below; the historical statement is not retroactively rewritten.

- **OBSERVATION:** Authenticated KDP Bookshelf showed Kindle and paperback Live on 2026-09-23. Amazon.com retail detail pages resolved at Kindle ASIN B0HKTBFFJM and paperback ASIN B0HKTFR8ND; paperback ISBN 979-8176597592. Both retail pages displayed publication date 2026-09-23. Bookshelf showed $2.99 Kindle, $9.99 paperback, and eBook enrolled in KDP Select.
- **OBSERVATION:** With delivery set to Thouaré-sur-Loire, France, the Kindle detail page said the title was not currently available for purchase and the paperback page said it could not ship to the selected location. Each detail page exposed only its own format. Cross-format retail linkage and availability from a supported location remain pending.
- **OBSERVATION:** KDP Orders report filtered to this title, 2026-09-01 through 2026-09-23, showed 0 processed Kindle units and 0 print units. KDP notes processing may lag. Title-specific KENP, royalties, placed orders and review count were not verified; they remain unknown.
- **OBSERVATION:** Nine saved non-title Amazon.com Books queries were checked in a signed-in, personalized France-delivery session. Six wider-query searches had no organic result in the first two pages. Three narrow searches surfaced the book only in a “Previously viewed” module after organic results; that module is not counted as discovery. This is a single D0 shelf snapshot, not a stable indexing result.
- **INFERENCE:** The production case has reached verified KDP publication in both formats. Publication and a zero-processed-orders D0 report establish neither commercial success nor a product-fit conclusion.
- **HYPOTHESIS:** A repeat under comparable query conditions after indexing time may clarify whether the book is organically discoverable; France-location purchase restrictions may be territorial rather than a general listing defect. Both require later observation.
- **PRACTICE:** Store a dated publication/D0 snapshot, keep observed facts separate from the launch plan, exclude personalized recommendation modules from organic rank, and retain UNKNOWN rather than inferring sales/KENP/royalties. Keep D7/D14/D30 windows and metadata freeze; no ads or reactive changes absent a defect.

The successor manifest and machine-readable D0 evidence are in `book-radar/runs/bracken-ford-d0/2026-09-23/`. The canonical Text Lock and illustration hashes and unresolved asset provenance are preserved. This closeout does not change the Radar scoring model or the external novel project.

Return factory focus to the Jekyll Toki Pona provider regression.
