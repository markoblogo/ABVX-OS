# ABVX Book Factory — Cross-Pipeline Audit V1

Date: 2026-09-30. Mode: owner-approved EXPENSIVE audit/design only. Runtime, books, publication state, existing learning records and independent projects were not changed. Findings below are local evidence, not a new retailer observation. Existing dirty-worktree changes are not this audit's changes.

## Evidence and counting convention

Nine cases inspected: seven production/editorial cases, one additional reference-product case, and the unstarted GD3 foundation. Inspection depth is explicit; this does not mean nine complete or published pipelines. Six duplicated implementation families, nine recurring failure/process-gap classes, eight removable mechanical owner tasks, twelve proposed core capabilities, five book-type modules and four format modules are enumerated in this package. Sitelen is a render adapter, not a fifth format module. Counts are classifications, not measured savings.

| ID | Case and evidence inspected | Current evidence boundary |
|---|---|---|
| E1 | `books/rn10-003/GOOD_DOG_BOOK_ONE_PRODUCTION_POSTMORTEM_V1.md`; `production/v1/build_production.py` within that directory; canonical Manifest V6 / Publication Canon V4 and inherited V2 | Actual print was 413 pages, 5.5×8.5; EPUB/KPF failures are historical. Direct DOCX success is reported, exact uploaded binary not proven. Old Publishing observation is not current authority. |
| E2 | `books/rn10-003/GOOD_DOG_BOOK_TWO_PRODUCTION_POSTMORTEM_V1.md`, `GOOD_DOG_BOOK_ONE_TWO_REPEATED_FAILURES_V1.md`; `production/book-two/v1/build_book_two.py`, `v2/repair_print_margins.py`; Publication Canon V4 | Recorded Kindle/paperback/series LIVE; exact upload bytes, publication timestamp and commercial results UNKNOWN. Six-image margin escape documented on pages 4,91,97,160,213,251. |
| E3 | `books/rn10-003/BOOK_THREE_ORCHESTRATOR_FOUNDATION_IMPLEMENTATION_V1.md`; `src/abvx_harness/book_three.py`; state/event schemas and tests | Already implemented foundation, not merely proposed. State revision 1, Gate A pending, creative work NOT_STARTED. Helpers are not PDF/DOCX builders or complete preflight. |
| E4 | `NARRATIVE_TOKI_PONA_PIPELINE_V1.md`; `src/abvx_harness/narrative_pipeline.py`; `scripts/run_jekyll_full_translation_v1.py`; Jekyll cost audit, resume preflight, Text Lock report; V1.2 Contents/preflight reports | 351 valid checkpoints/111 remaining was a historical checkpoint, later 462-block lock. V1.2 reports 300 pages, 13 visible Contents entries and separate bookmarks. No fresh Kindle/KDP verification. |
| E5 | Odyssey independent folder listed below: original audit, editorial manifest, final layout preflight | ODT is authority for source structure; original audit HOLD progressed to local editorial/layout PASS. 629 PDF pages/630 effective print pages is a retained report, not new KDP processed-count evidence. Original translation run/cost chain unavailable. |
| E6 | Jeanne independent folder listed below: final QA, README, textual-issues ledger, source Bible and assembly-script inventory | 14 chapters/57,015 FR words; GO TO LAYOUT, not a publication lock or retailer PASS. Source lacunae retained; no end-to-end print/Kindle chain inspected. |
| E7 | `BRACKEN_FORD_FACTORY_POSTMORTEM_V1.md`, `ABVX_BOOK_SYSTEMS_LEARNING_V1.md`, `learning/book-systems/records.jsonl` | Append-only closeout supersedes historical submission paragraph. Assets' origins/Pictiq provenance remain limited. Publication observation is not general availability/commercial success. Independent novel is not migrated. |
| E8 | `RN2-037-production-contract.md`; `books/rn2-037/qa/rn2-037-post-production-learning.md`, preflight; factory quality lessons | Diagram-first reference production, 208-page print/EPUB route reported; initial contract NOT_STARTED is historical. Owner time not measured. Current storefront status not rechecked. |
| E9 | `books/rn3-091/v2/qa/release-preflight-v2.json`; `books/factory/lessons/publishing-quality-false-positives-v1.json`; publishing contracts/functions | Source-backed reference atlas, multiple product/commercial/eligibility/object-geometry regressions. Inspection is gate/QA evidence, not a new complete source or retailer audit. |

Book One naming trap: `books/rn10-003/GOOD_DOG_BAD_SYSTEM_TEXT_LOCK_V1.md` is the lock **report**, SHA `8d4054415e63bc6473fc2fa9bd1a62374cfeb71f37dca79a80e42e832586aea1`. Its actual manuscript pointer is `books/rn10-003/manuscript/GOOD_DOG_BAD_SYSTEM_TEXT_LOCK_V1.md`, independently hashed `7e7349fb5f07548d344b1a4a462137fcbe76bca1696ef1f1cc30211f2c061e81`. These are not conflicting manuscript copies. Identity must follow the recorded ref, not guess from basename.

Independent evidence roots (read only, never imported as a new canonical book):

- Odyssey: `/Users/antonbiletskiy-volokh/Documents/Codex/2026-09-03/referenced-chatgpt-conversation-this-is-an/outputs/`; selected `od-tp-editorial-qa/report.md`, `editorial-master-v1-manifest.json`, `editorial-master-v1-manual-decisions.md`, `kdp-layout-preflight.md`.
- Jeanne: `/Users/antonbiletskiy-volokh/Documents/Codex/2026-09-26/referenced-chatgpt-conversation-this-is-an/`; selected `outputs/JEANNE_FR_FINAL_QA.md`, `README_JEANNE_FR_FINAL.md`, `JEANNE_TEXTUAL_ISSUES_LEDGER.md`; source/script inventory under `work/`.

Registry review: `registries/capabilities.json` already declares book-production-quality-gates, content-ops-control-plane and Book Radar. Donor matrix keeps LoopX conditional mission state, workflow servers deferred, Dify a pattern source, Langfuse an optional trace pilot. No new external research or dependency is justified for this local foundation.

## Reconstructed pipelines

Legend: C COMMON; T BOOK-TYPE-SPECIFIC; F FORMAT-SPECIFIC; R RETAILER-SPECIFIC; H HISTORICAL_WORKAROUND. UNKNOWN is evidence absence, not an invented stage. Templates/layout implementations remain adapter-specific even when their contracts are common.

| Case | Input / development / editorial / locks / assets | Front matter / Contents / production / QA | Metadata / cover / retailer / publication / learning |
|---|---|---|---|
| GD1 | C source/canon identity → T novel editorial/36 chapters → C text lock → C approved art + F Lanczos print derivatives; T Pictiq | C title/copyright/preface; F visible print TOC + annotations; F ReportLab PDF / H EPUB→KC/KPF attempts→F DOCX; F font/structure/parity/render checks | C owner metadata/rights/disclosure; T Open Route cover; R KDP conversion/Previewer→dated observations; C closeout/postmortem. Exact upload chain limited. |
| GD2 | C recovered canon → T engines/architecture/4 sequences → T development/compression/Ch24 repair/line edit → C byte lock → T two silent/four Pictiq comics + accepted provenance limits | C front/back matter; F generated print labels and reflowable Contents; F PDF/DOCX → F local QA → H surgical six-page geometry repair; R preview independent | C dual author/series/default decisions; T cover → R submission → recorded LIVE per format; C Radar observation and learning. |
| GD3 | C pinned series inputs/state/events → T Gate A/B/C planned; C locks absent; T optional Composer Gate D | C/F future Contents policies; F future build evidence, not real builds | C future metadata/cover; R conditional Gate F per format; C prospective null metrics. Only foundation exists. |
| Jekyll | C normalized source blocks → T TP/name/knowledge policy → C resume checkpoints → T semantic/native continuous review + lexical owner decision → C translation/text lock → T Latin/sitelen render boundary | C translation note/anchors/names; F visible TOC parity and bookmarks separately → T render adapter + F TeX PDF → F glyph/continuation/font/bounds QA | C project metadata/illustration lock; R fixed-page Kindle/KDP planning outside local PDF proof; C cost/full-run learning. Current external status UNKNOWN. |
| Odyssey | C EN/TP/sitelen ODT → T layer/name/guide audit → T owner canonical decisions + bounded corrections → C editorial manifest (not a presumed byte-identical Markdown lock) | C guides/note; T synchronized layers; F ODT style variants → LibreOffice PDF; F final TOC/font/page/semantic parity | C metadata/cover/Kindle not begun in inspected preflight; R Previewer/physical proof outstanding; C canonical/fix ledgers. Original translation economics UNKNOWN. |
| Jeanne UA→FR | C prioritized UA witnesses/native-pass blocks/Bible v2 → T translation/native French assembly → T seam/voice/tense/name/source-issue QA; C formal source/translation/text locks not evidenced here | C process paratext removed; final manuscript GO TO LAYOUT; F Contents/build/QA not evidenced | C packaging/cover/R retailer/publication UNKNOWN in inspected package; C issues/changelog retain lacunae rather than fabricate reconstructions. |
| Bracken Ford | C product spec/source canon → T architecture/bounded draft→development/cleanliness/human edit→C lock→T Pictiq assets | C/F interior attribution/Contents; F print/EPUB gates; F footer-safe-area repair; origins unknown | C frozen packaging; R real-template/barcode constraints and observed Live closeout; C Radar D0/unknown metrics and BSL-017. |
| RN2-037 | C official pool/source registry → T original explanatory transformation/product contract → T factual/editorial/crosswalk QA; lock lifecycle not fully reconstructed | C/F front matter/TOC; F diagram/SVG/print/EPUB → local false negatives → bounds/collision/label/TOC correction | C commercial package; R submission observations only; C post-production learning. |
| RN3-091 | C licence/source inventory → T differentiated atlas/product prototype→T bilingual/editorial/product taste gates; exact lock lifecycle not inspected | F print/layout/object QA; local validity mistaken for product completion; T representative normal-page/productization repair | C metadata/pricing/content-version gate; R language×format eligibility and vector margin error; C eight retained quality cases. |

The common workflow is a dependency graph of evidence and accepted outputs, not one compulsory linear sequence. A source-backed edition can omit fiction drafting; prose-only books omit illustration lock; print-only books omit digital navigation by explicit target applicability. Visible Contents remains default required by current ABVX policy unless a title-specific owner waiver is recorded.

## Six duplicated implementation families

| ID | Actual overlapping implementations | Resolution, not authorized now |
|---|---|---|
| D1 | File/text SHA helpers in GD1 builder, GD2 builder/repair, GD3 and narrative runner | One core evidence/reference contract; adapters preserve bytes and normalization purpose. |
| D2 | Geometry in `book_preflight.audit_page_geometry`, `publishing_gates.audit_no_bleed_objects`, `book_three.image_safe_area`, repair script | Shared canonical geometry envelope; retailer policy and object extraction separate. Existing xyxy vs xywh conventions must be converted, not interchanged. |
| D3 | Resume/checkpoint logic in NarrativeRunner and Jekyll full runner | One versioned cache contract + adapter-specific provider/error handling. Both current skip predicates rely on source hash/success, not the complete desired policy key. |
| D4 | Result/gate vocabulary in publishing gates, preflight and GD3 | One evidence-bound five-state validator contract; no rename-only PASS promotion. |
| D5 | Chapter/section completeness and order in GD1/GD2/Jekyll source parsers and QA | Shared inventory validator over typed adapter inventories, not a universal Markdown parser. |
| D6 | Production manifests/hash/config/output recording in both GD builders, Jekyll builds and GD3 build helpers | One immutable build envelope, keep renderer-specific commands and evidence. |

Separate layout code is not automatically duplication: ReportLab, ODT and TeX serve different reader formats. Likewise TP semantics, French style and Pictiq semantics must not be consolidated into generic editorial rules.

## Top ten duplications / inefficiencies

1. D1 repeated evidence/hash scaffolding.
2. D2 multiple geometry envelopes and inconsistent coordinate conventions.
3. D3 source-only resume identity and separate provider-budget policies.
4. D4 local PASS/readiness wording with different release meaning.
5. D5 repeated structural inventories/count checks.
6. D6 build/config/provenance records rebuilt per title.
7. Manual current-file/status recovery from superseded prose records (GD/Bracken).
8. Repeated sequence/status handoff documents instead of one issues/events view (GD2).
9. Full entity ledger per small Jekyll block, zero observed cache reads in the audited run; optimization is unvalidated, not guaranteed savings.
10. Owner discovery of omitted Contents/unsafe objects and repeated metadata/default entry late in production (RN2/Jekyll/GD2/RN3).

## Nine recurring failure/process-gap classes

| ID | Evidence of recurrence | Introduced → detected; promotion target |
|---|---|---|
| R1 LOCAL_PASS_AS_EXTERNAL_SUCCESS | GD1/GD2/Bracken/RN2/RN3 | Gate aggregation → owner/retailer; separate per-format preview/upload/release proofs. |
| R2 PICTIQ_PROVENANCE_GAP | GD1/GD2/Bracken | Art capture → packaging/lock; exact source-speaker-Composer-approved-output chain. Historical exceptions remain historical. |
| R3 AUTHOR_SURFACE_CONFLATION | GD1→GD2 transfer record | Metadata → owner; book-facing/retailer-author assertions. |
| R4 SERIES_IDENTITY_DEFERRED | GD1→GD2 transfer record | Identity/package → owner series setup; ordered series config before packaging. |
| R5 SAFE_AREA_BLIND_SPOT | GD2/Bracken/RN2/RN3 vector case | Layout/extraction → KDP; complete text/image/vector/footer inventory + binding-side proof. |
| R6 STALE_AUTHORITY | Bracken obsolete illustration source; GD historical status/default conflicts; RN3 commercial version mismatch | Pointer/packaging → handoff/owner; immutable locks + dependency STALE gate. |
| R7 PROCESS_RESIDUE_OR_FORMAL_COMPLETENESS | Bracken duplicate variants; Jeanne production paratext; RN3 template leakage | Assembly/productization → editorial/human; cleanliness + continuous/representative review, not counts alone. |
| R8 CONTENTS_OMISSION_OR_STALENESS | RN2 print/Kindle omission; Jekyll V1.1 omission | Build → owner Kindle/retailer; visible page/parity/navigation independently. |
| R9 PRODUCT_OR_COMMERCIAL_FALSE_PASS | RN3 prototype/full/commercial/content-version cases | Product/gate → owner; product quality independent, commercial package finalized after content/layout freeze. |

These are process classes, not nine identical defects across every title. Single-case regressions are also warranted: GD1 unembedded fonts/print annotations/render performance; Jekyll persistent-error runaway/cost telemetry; Odyssey layer/name-guide drift; Jeanne corrupt witness/lacuna handling. Neither GD1's viewer hang root cause nor wrong Pictiq speaker attribution was proven; do not encode guessed causes as facts.

## Metrics and learning assessment

CURRENT METRICS COVERAGE: PARTIAL. Jekyll retains per-response usage, calls/retries and cost estimates; GD3 has prospective null fields. GD2 has measured words/revisions but no historical agent-run, billing, work-hour or owner-minute records. RN2 explicitly distinguishes zero subject-matter decisions from unmeasured owner time. File timestamps are not labour duration. Commercial outcomes are not production-quality metrics.

The existing append-only learning register remains canonical. The new learning JSON is a proposed promotion index, not a second historical ledger. Prior geometry advice did not prevent GD2's escape because that builder did not feed a complete margin inventory into a blocking release gate. Jekyll's Contents advice was not asserted by V1.1's builder. GD3 now has contracts/tests, but actual PDF extraction remains absent. Documentation alone is not enforcement.

## Preservation and evidence limitation

Protected focus set: 23 small source/lock/state/ledger/code/registry files hashed before and after architecture creation; includes actual GD1 manuscript and its distinct report, GD2 lock `3d29eb6e5e201b0b3805d92ca7b38d965d8bdfdad46a49ff8077ce425fb70a44`, Jekyll lock `a174999649808399aa49e5b8ff3319b89e30f39a78118be83d53bc93e37fd5ef`, GD3 state `31dbf80e755533241d754b43048796761df785cb2f3aa3c01bf31be16a877e55`. This is not a fresh hash/render certification of every historical PDF/image. No builder, model/provider, retailer or book-edit command was executed. Only the six named design artifacts may be added by this run. Final verification result is recorded in the implementation plan.
