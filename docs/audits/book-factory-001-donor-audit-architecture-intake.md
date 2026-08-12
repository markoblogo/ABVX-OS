# BOOK-FACTORY-001 — Donor Audit + Architecture + First Book Intake

Status: READY_FOR_HUMAN_DECISION  
Cost class: NORMAL

## BOOK-FACTORY-001A extension

The foundation now explicitly supports:

- derived prose books
- translated editions
- comics / manga / webtoon publication forms
- translated comics where dialogue/text remains recoverable outside baked artwork

The architecture is still control-plane only. No production runtime was added.

## BOOK-FACTORY-001B extension

The foundation now explicitly models:

- canonical manuscript lineage
- format-specific derived artifacts
- format-specific QA
- per-format publication/submission state
- fail-closed blocked-edition behavior

## 1. Existing ABVX capability -> Book Factory use -> gap

| Existing capability | Book Factory use | Remaining gap |
| --- | --- | --- |
| `universal-artifact-intake` | preserve book ideas, source notes, external references, drafts | no book-specific intake/readiness contract yet |
| `read-only-cortex-context-retrieval` | gather bounded author/project/domain context for concept, outline and case-study prep | no book-project projection yet |
| `content-ops-control-plane` | model human-gated preparation, approval, packaging handoff patterns | not a manuscript or KDP package model |
| evidence + compact provenance patterns | preserve donor decisions, source-pack admission and disclosure boundaries | no book-specific provenance/disclosure contract |
| project events / playbooks | future routine packaging or asset steps | no book lifecycle state model |
| autonomy / donor-first policy | keeps KDP submission and manuscript generation fail-closed | no donor composition recorded for books |

Conclusion: ABVX already has the control-plane primitives. The missing layer is a narrow book-production contract set, not another runtime subsystem.

## 2. Primary donor findings

### `vpuna/markdown-to-book`

- Best current donor for deterministic compilation.
- Concrete seam:
  - `convert.js`
  - commands for paperback PDF, hardcover PDF, Kindle EPUB
  - trim size, TOC, metadata, front/back matter, EPUB cover support
- Why it matters:
  - ABVX does not need to build its own markdown -> KDP package compiler first.
- Decision:
  - `PILOT_NOW`

### `ekr0/auto-kdp`

- Relevant only at the submission boundary.
- Concrete seam:
  - `src/index.ts` action runner
  - `src/action/produce-manuscript.ts`
  - `src/action/update-content.ts`
  - `src/action/publish.ts`
- Why it matters:
  - proves a future supervised KDP adapter is plausible.
- Risk:
  - browser/KDP UI brittleness, retries, local browser-state coupling.
- Decision:
  - `PILOT_LATER`

### `wesleyscholl/book-generator`

- Strong shell workflow patterns, weak adoption safety.
- Concrete seam:
  - `scripts/generate_book.sh`
  - `scripts/optimized_chapter_handler.sh`
  - `scripts/compile_book.sh`
- Why it matters:
  - useful pattern source for step decomposition, extension/review loops, compile sequencing.
- Risk:
  - shell-heavy, provider-coupled, no clear license in repo root for code adoption.
- Decision:
  - `PATTERN_SOURCE`

### `alexeygrigorev/ai-book-generator`

- Strongest structured authoring/workspace donor, but not ready for direct adoption.
- Concrete seam:
  - `book_generator/models.py` book plan/workspace models
  - `book_generator/plan.py` structured plan generation
  - `book_generator/execute.py` chapter/section execution
  - `scripts/create_kdp_interior.py`
  - `scripts/create_kdp_cover.py`
- Why it matters:
  - good source for BookSpec / workspace / package boundary patterns.
- Risk:
  - heavy dependency stack, provider coupling, no clear license.
- Decision:
  - `PATTERN_SOURCE`

## 3. Secondary/reference donors

| Donor | Role | Decision |
| --- | --- | --- |
| `b7011343/kdp-gpt` | minimal prompt-to-pdf KDP generator | `REJECT` |
| `finxter/awesome-ai-book-writing` | donor discovery catalog | `REFERENCE_ONLY` |
| `gcui-art/awesome-ai-writing` | broad AI-writing catalog | `REFERENCE_ONLY` |
| GitHub `ai-writing` topic | future discovery surface | `REFERENCE_ONLY` |

## 4. File/function-level reuse matrix

| Repository | File / module | Function / command seam | Capability | Reuse method | Notes |
| --- | --- | --- | --- | --- | --- |
| `vpuna/markdown-to-book` | `convert.js` | `node convert.js ...` | deterministic markdown -> paperback/hardcover/epub | `THIN_ADAPTER` | best compile seam; local-first |
| `vpuna/markdown-to-book` | `templates/kdp-print.tex` | LaTeX template | trim-size-aware print layout | `ADOPT_PATTERN` | use only if compile pilot needs template customization |
| `ekr0/auto-kdp` | `src/index.ts` | action dispatcher | supervised KDP action execution | `ADOPT_PATTERN` | keep outside ABVX until submission pilot |
| `ekr0/auto-kdp` | `src/action/produce-manuscript.ts` | `produceManuscript` | local package existence gate before upload | `ADOPT_PATTERN` | useful pre-submit integrity check |
| `ekr0/auto-kdp` | `src/action/publish.ts` | `publish` | submit after status checks | `REFERENCE_ONLY` | brittle UI automation; future supervised use only |
| `wesleyscholl/book-generator` | `scripts/generate_book.sh` | `generate_book.sh --topic ...` | end-to-end generation pipeline | `ADOPT_PATTERN` | do not adopt shell runtime directly |
| `wesleyscholl/book-generator` | `scripts/optimized_chapter_handler.sh` | `process_chapter_by_length` / `extend_chapter_to_min_length` | chapter length/review loop | `ADOPT_PATTERN` | useful bounded QA pattern |
| `wesleyscholl/book-generator` | `scripts/compile_book.sh` | `compile_book.sh` | multi-format compile sequencing | `REFERENCE_ONLY` | donor already superseded by `markdown-to-book` for compile pilot |
| `alexeygrigorev/ai-book-generator` | `book_generator/models.py` | `BookPlan` family | structured BookSpec/workspace model | `ADOPT_PATTERN` | strongest contract inspiration |
| `alexeygrigorev/ai-book-generator` | `book_generator/plan.py` | structured planning flow | concept -> outline planning | `ADOPT_PATTERN` | candidate later if planning pilot justified |
| `alexeygrigorev/ai-book-generator` | `scripts/create_kdp_interior.py` | interior generation script | KDP interior package creation | `REFERENCE_ONLY` | future comparison against `markdown-to-book` |
| `alexeygrigorev/ai-book-generator` | `scripts/create_kdp_cover.py` | cover PDF generation | print-cover package step | `REFERENCE_ONLY` | useful only after explicit cover workflow exists |

## 5. Proposed donor composition

ABVX should own:

- intake
- BookProject / BookSourcePack contracts
- source admission
- provenance / disclosure policy
- lifecycle state
- human gates
- evidence
- packaging/submission boundaries

ABVX should not own first:

- autonomous manuscript generation runtime
- generic authoring IDE
- custom markdown-to-KDP compiler
- autonomous KDP submitter

Recommended composition:

1. ABVX control plane for intake, BookSpec state, evidence, gates.
2. `markdown-to-book` as the first deterministic packaging pilot.
3. owner-authored markdown as the first manuscript substrate.
4. `ai-book-generator` patterns only for future BookSpec/workspace refinement.
5. `auto-kdp` only as a future supervised submission adapter if the packaging path proves stable.

## 6. Production-mode model

Do not use one exploding `book_type` enum for every combination.

Use composition:

- `content_origin`
  - `ORIGINAL`
  - `DERIVED`
  - `TRANSLATION`
- `publication_form`
  - `PROSE_BOOK`
  - `ILLUSTRATED_BOOK`
  - `COMIC`
  - `MANGA`
  - `WEBTOON`

This cleanly covers:

- original prose book
- derived prose book
- translated prose book
- comic
- manga
- translated comic / translated manga

without inventing separate schemas for every combination.

## 7. Minimal Book Factory architecture

```
owner material / references
-> intake items
-> BookSourcePack
-> BookProject
-> human-approved BookSpec
-> manuscript workspace (future)
-> deterministic compile/package donor
-> human QA gate
-> supervised submission boundary
```

This keeps ABVX as orchestrator/control plane and leaves manuscript/compile/submission implementations replaceable.

## 8. Contracts added in this slice

### `BookProject`

Purpose:

- canonical machine-readable state for one book candidate
- ties together intake, context requests, source pack, donor profile, readiness and gates
- now also records `content_origin`, `publication_form`, and `cost_preference`
- now also records one canonical manuscript lineage, derived format artifacts, and per-format edition state

### `BookSourcePack`

Purpose:

- admitted source inventory for a book candidate
- explicit rights basis and reference-only exclusions
- disclosure obligations
- coverage/readiness signal before BookSpec
- now also records extraction status, allowed use, relevant sections and confidence notes per source

### `BookSpec`

Purpose:

- canonical edition definition once a concept is selected
- explicit title, audience, positioning, source/citation policy, outline, formats, trim size, KDP metadata and provenance classification
- operator-UI compatible state that does not require the UI to own book logic
- now also carries:
  - `content_origin`
  - `publication_form`
  - translation block
  - visual-narrative block
  - execution-cost preferences
  - format-specific QA boundaries

## 9. Translation contract

Translation is now first-class in `BookSpec.translation`.

It records:

- source and target language
- source edition
- translation method
- translation provider/model
- glossary
- proper-name policy
- terminology memory
- style / voice instructions
- segmented progress
- resume checkpoint state
- human-reviewed sections
- QA status
- rights status

Conceptual boundary:

`TranslationRequest -> TranslationProvider -> TranslationResult`

No provider was implemented in this slice.

## 10. Translation donor matrix

| Donor | What is real | Strengths | Weaknesses | Classification |
| --- | --- | --- | --- | --- |
| `hydropix/TranslateBooksWithLLMs` | real Python app + CLI + checkpoints | EPUB/DOCX/TXT, local/cloud providers, resume, glossary/state, formatting preservation, OpenAI-compatible + OpenRouter + Gemini + Ollama | heavier app stack, broader than a thin adapter | `PILOT_NOW` |
| `KazKozDev/book-translator` | real offline-first app | Ollama-first, terminology manager, cache, staged QA/review, TXT/EPUB/PDF/DOCX | heavier workflow, quality depends on multi-model local stack | `PATTERN_SOURCE` / strong free-local pilot reference |
| `DDChen666/translate-book` | real skill-style workflow | two-pass review, glossary/style guides, provider abstraction, QA reports | CC BY-NC-SA license blocks straightforward reuse for a general production foundation | `PATTERN_SOURCE` |
| `ViacheslavSysoev/perevodnik` | repo exists but weaker observable seams | low audit value versus stronger candidates | unclear strength compared with stronger candidates | `REJECT` |

Recommended first translation donor/pilot:

- `hydropix/TranslateBooksWithLLMs` for the first future translation pilot
- `KazKozDev/book-translator` as the strongest free/local comparison point

## 11. Comic / manga architecture

Do not model comics as prose books with many illustrations.

Minimum future contract set:

- `ComicSpec`
- `VisualBible`
- `CharacterSpec`
- `PageSpec`
- `PanelSpec`

Not all need first-class schemas yet, but the architecture must preserve these stages:

`SOURCE/STORY -> SCRIPT -> VISUAL BIBLE -> CHARACTER REFERENCES -> STORYBOARD -> PAGE/PANEL PLAN -> PANEL GENERATION -> CONSISTENCY QA -> LETTERING -> PAGE ASSEMBLY -> HUMAN REVIEW -> PRINT/DIGITAL PACKAGE`

Text must remain structured separately from artwork where possible so translation, typo fixes, re-lettering and localization stay feasible.

## 12. Comic donor matrix

| Donor | What is real | Strengths | Weaknesses | Classification |
| --- | --- | --- | --- | --- |
| `RemiPelloux/agent-mangaka-forge` | real Codex-ready repo + img-memory helper | strongest character consistency pattern, variants/evolutions, fail-closed reference discipline | not a full production pipeline | `PATTERN_SOURCE` |
| `lhfer/codex-novel-to-comic-studio` | real recoverable pipeline repo | strongest end-to-end adaptation architecture, page script, storyboard, lettering, QC, PDF/CBZ | skill/pipeline package, not a drop-in engine | `PATTERN_SOURCE` |
| `jbilcke-hf/ai-comic-factory` | real app/demo | panel/speech types, provider options, identity image concept | depends on external rendering infra, weak recoverable production boundary | `REFERENCE_ONLY` |
| `Yutarop/comic-generator` | real simple app | page chaining, optional character reference, quick manga demo | brittle, little resumability/editability, output text tends to bake into images | `REFERENCE_ONLY` |
| `LlamaGenAI/LlamaGenAI` | docs/API marketing repo | confirms a comic-panel API shape exists | not a meaningful OSS implementation donor | `REJECT` |

Strongest character-consistency donor/pattern:

- `RemiPelloux/agent-mangaka-forge`

Strongest full comic-architecture pattern:

- `lhfer/codex-novel-to-comic-studio`

## 13. Free / cost model

Book Factory now carries explicit cost preferences:

- runtime cost classes:
  - `FREE_LOCAL`
  - `FREE_TIER`
  - `LOW_COST_API`
  - `PAID_API`
  - `UNKNOWN`
- planning preference:
  - `FREE_FIRST`
  - `BALANCED`
  - `QUALITY_FIRST`

Default experimentation preference remains:

- `FREE_FIRST`

But quality gates remain mandatory.

## 14. Provenance / disclosure model

Rules:

1. every admitted source gets an explicit role and rights basis
2. external examples default to `PUBLIC_REFERENCE_ONLY`
3. AI assistance is disclosed as process metadata, not hidden inside owner-originated material
4. no source-pack item implies permission to copy third-party text or visuals
5. translation provenance remains explicit:
   - `HUMAN_TRANSLATED`
   - `AI_TRANSLATED`
   - `AI_ASSISTED_TRANSLATION`
   - `HUMAN_REVISED_AI_TRANSLATION`

## 15. State / human gates

Lifecycle:

`SOURCE -> CONCEPT -> BOOK_SPEC -> OUTLINE -> MANUSCRIPT -> EDITORIAL_QA -> ASSETS -> KDP_PACKAGE -> SUBMISSION -> POST_PUBLISH`

Strategic human gates that must remain:

- BookSpec approval
- editorial/package approval
- submission approval

For translation a conceptual sub-flow is now explicit:

`SOURCE -> SOURCE_NORMALIZATION -> TRANSLATION_SPEC -> GLOSSARY_AND_STYLE_MEMORY -> SEGMENTED_TRANSLATION -> CONSISTENCY_QA -> HUMAN_REVIEW -> MASTER_TRANSLATION -> NORMAL_BOOK_FACTORY_PATH`

Format-artifact boundary is now explicit:

`CANONICAL_MANUSCRIPT -> KINDLE_REFLOWABLE / PAPERBACK_INTERIOR / HARDCOVER_INTERIOR / EPUB / PRINT_COVER / EBOOK_COVER`

One manuscript must not be assumed suitable for all retail formats.

## 16. KDP boundary

What belongs inside Book Factory:

- metadata package preparation
- interior/cover package preparation
- disclosure record
- evidence of what would be submitted

What does not belong inside this slice:

- real browser automation
- real retailer submission
- autonomous publish

Submission remains per-format and supervised:

- submit one approved format artifact at a time
- do not treat "publish book" as one atomic action across Kindle, paperback and hardcover
- if one edition is `BLOCKED`, do not create duplicates as a workaround
- if one edition is `BLOCKED`, do not unpublish another live edition
- if one edition is `BLOCKED`, do not infer that the whole `BookProject` failed

## 17. Real production lesson: Fragments from a Therapist's Notebook

Recorded as:

- paperback = `LIVE`
- kindle = `BLOCKED`
- kindle external state = `CONTENT_REVIEW_ESCALATED`
- kindle waiting state = `WAITING_EXTERNAL`
- hardcover = `NOT_CREATED`

Interpretation:

- paperback success does not prove Kindle readiness
- Kindle requires its own format-specific artifact and QA
- blocked Kindle recovery is a supervised support/content-review path, not an automation path

## 18. Derived-book integration

The SourcePack is explicitly allowed to reference existing ABVX `ContentItem` artifacts without copying them into a second content store.

Examples supported by the architecture:

- ABVX writing notes -> cookbook
- #PopIndex / index material -> unusual-indices book
- essays/articles -> thematic collection

## 19. First real candidate comparison

### Candidate A — `unusual-indices-book`

Pros:

- already has context request
- already has context-pack evidence
- already has owner intent via POP intake
- already has at least one public proof/case-study seed

Cons:

- edition scope still broad
- visual policy unresolved

### Candidate B — cookbook material

Pros:

- clearly owner-originated
- voice seed is strong

Cons:

- only fragmentary source set exists in ABVX today
- no bounded concept or structure artifact yet

### Candidate C — MN7R Product Guide derivative/update

Pros:

- existing public book proof

Cons:

- less useful as a first *new* Book Factory intake because it is already a realized publication line

Selected first machine-readable intake:

- `unusual-indices-book`

Why:

- best ABVX evidence continuity
- best donor-first fit for a future controlled packaging pilot
- strongest immediate path to a bounded BookSpec without pretending manuscript readiness already exists

Correct classification after 001A:

- `content_origin = DERIVED`
- `publication_form = PROSE_BOOK`

## 20. First intake/readiness result

`books/projects/unusual-indices-book.json`

- status: `WAITING_FOR_HUMAN`
- stage: `CONCEPT`
- selected donor profile recorded
- source pack selected
- major gates explicit

`books/source-packs/unusual-indices-book-source-pack.json`

- status: `READY_FOR_BOOK_SPEC`
- admitted sources explicit
- rights marked `MIXED`
- KDP disclosure requirement marked `YES`

`books/specs/unusual-indices-book-spec.seed.json`

- seed BookSpec only
- enough structure to approve or reject Edition-1 scope
- explicitly not an approved outline/manuscript trigger yet

Additional real-case artifact:

`books/projects/fragments-therapists-notebook.json`

- demonstrates per-format publication state
- demonstrates blocked Kindle fail-closed handling
- demonstrates separation between canonical manuscript and format-specific derivatives

## 21. What ABVX still does not implement

- manuscript workspace/runtime
- chapter generation
- continuity engine
- editorial similarity/plagiarism subsystem
- cover generation pipeline
- KDP submission adapter
- post-publish automation
- translation runtime
- segmented translation executor
- visual bible runtime
- panel/page generator
- lettering pipeline

## 22. Revised BOOK-FACTORY-002

Smallest justified next slice:

`BOOK-FACTORY-002 — BookSpec + deterministic package pilot`

Scope:

1. create a `BookSpec` contract
2. narrow `unusual-indices-book` to Edition 1 and approve it as a `DERIVED` prose book
3. prepare one owner-controlled markdown manuscript workspace/stub
4. pilot `markdown-to-book` in report-only/local package mode
5. emit package evidence without any KDP submission

That is the first slice that can prove real packaging value without jumping into autonomous generation or retailer automation.

Translation and comic runtimes should not delay that first prose acceptance case.
