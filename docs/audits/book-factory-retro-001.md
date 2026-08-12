# BOOK-FACTORY-RETRO-001 — First Acceptance Case Retrospective + Pipeline Compression

Status: STOP_FOR_HUMAN_DECISION
Cost class: NORMAL

## 1. What happened

### Acceptance-case timeline

| Mission | Purpose | Output | Human gate | Rework caused? | Reusable? | Avoidable next time? |
| --- | --- | --- | --- | --- | --- | --- |
| BOOK-FACTORY-003 | Intake, rights boundary, corpus extraction, donor audit | `BookProject`, `BookSourcePack`, repo matrix, rights verdict, donor notes | yes — source-use boundary | low | yes | no |
| BOOK-FACTORY-004 / 004A | Compact BookSpec, shortlist, sample entries | shortlist TSV, sample pages, compact scope | yes — shortlist and sample review | medium | yes | partly |
| BOOK-FACTORY-005 / 005A | Full manuscript + Voice Contract + human reading pack | `MASTER_MANUSCRIPT.md`, `VOICE_CONTRACT.md`, QA audit | yes — voice and editorial direction | medium | yes | partly |
| BOOK-FACTORY-006A | First renderer/proof selection | custom Python + XeLaTeX proof compiler, 4-page proof | yes — visual direction | high | partly | mostly |
| BOOK-FACTORY-006B | Full PDF build on first renderer | 28-page RC, text/link QA, publication packet prep | no new conceptual gate, but more correction slices followed | high | partly | mostly |
| BOOK-FACTORY-006C | Late publication-form correction | discovery-booklet structure, 23-page final PDF, canonical identity fixes | implicit through bounded correction | high | yes | mostly |
| BOOK-FACTORY-007 | ABVX Books publication and live verification | public book page, public PDF, homepage entry, live evidence | yes — external publication | low | yes | no |

### Missing canonical intermediate slices

The repo contains durable 006A / 006B / 006C / 007 evidence, but not distinct 006D / 006E records for the final LaTeX fact-block correction loop.

That is itself a process smell:

- expensive layout rework happened;
- the durable record kept the final artifact;
- the intermediate loop remained mostly prompt-level rather than contract-level.

## 2. What cost too much

### Cost / friction audit

| Category | Missions / touches | Rework | Human review value | Deterministic? | Codex reasoning needed? | Cost |
| --- | ---: | --- | --- | --- | --- | --- |
| SOURCE / RESEARCH | 003 | low | high | mostly | yes | MEDIUM |
| BOOK SPEC / EDITORIAL PLANNING | 004, 004A | medium | high | partly | yes | HIGH |
| WRITING | 005, 005A | medium | high | no | yes | HIGH |
| EDITORIAL QA | 005, 005A | medium | high | partly | yes | MEDIUM |
| DESIGN | 006A, 006B, 006C plus implicit 006D/006E loop | very high | medium | no | partly | VERY_HIGH |
| COMPILATION | 006A, 006B, 006C | medium | low | yes after renderer choice | low after setup | MEDIUM |
| TECHNICAL QA | 006B, 006C, 007 | medium | medium | mostly | low | MEDIUM |
| PUBLICATION | 007 | low | high | mostly | low | LOW |
| ARCHITECTURE / PLATFORM WORK | 001..002A plus ad hoc corrections | high | medium | partly | yes | HIGH |

### Highest-cost loops

1. Publication form changed too late: `PROSE_BOOK` behaved like the default mental model until 006C.
2. Renderer choice was under-specified: donor audit ended at `PATTERN_SOURCE`, then a local renderer grew anyway.
3. LaTeX layout debugging was pixel-level rather than token/profile-level.
4. Canonical link/identity corrections landed after PDF generation instead of before render freeze.
5. Human gates were split across too many small slices once the profile had already become obvious.

## 3. What worked

### Component decisions

| Component | Decision | Why |
| --- | --- | --- |
| BookProject | KEEP | Good high-level state, human gates, per-format states, readiness, next action |
| BookSourcePack | KEEP | Rights/provenance boundary worked and prevented unsafe reuse |
| BookSpec | KEEP | Useful planning object once scope became compact |
| source rights gate | KEEP | Caught a real issue early and correctly |
| donor/repository audit | SIMPLIFY | Useful once, too broad for every later slice |
| shortlist model | KEEP | Helped compress scope materially |
| Voice Contract | KEEP | Valuable human-review anchor for future prose generation |
| MASTER_MANUSCRIPT | KEEP | Good canonical prose spine |
| editorial QA | KEEP | Valuable, but should merge into one content mission |
| publication packet | KEEP | Helpful consumer handoff artifact |
| `abvx.publish-project` | MERGE/SIMPLIFY | Useful concept, but this case proved Books needs its own direct consumer path instead of pretending `/work` is the right seam |
| ABVX Books consumer path | KEEP | Real production path succeeded |
| public PDF validation | KEEP | Real value; catches the only success condition that matters |
| per-format state model | KEEP | Correctly separates format and publication state |

## 4. Root causes

### 4.1 Too many human gates

Gates that caught real problems:

- 003 rights/source-use gate
- 004 sample/voice/shortlist gate
- 007 external publication gate

Gates that mainly created more tiny missions:

- repeated layout/design acceptance after the profile was already clear
- late booklet-shape corrections that should have been profile defaults

### 4.2 Donor-first in name only

Actual donor reuse from `vpuna/markdown-to-book`:

- confirmation that `pandoc + XeLaTeX` was a viable seam
- print/KDP-oriented template patterns

What Codex rebuilt locally:

- renderer script
- LaTeX preamble
- page-layout logic
- fact-block layout behavior
- proof/final build flow

Verdict:

- donor value was `PATTERN_SOURCE`, not `COMPONENT` or `RUNTIME`
- local rebuild was justified for the first acceptance case
- but after that verdict, the process should have triggered an explicit `BUILD_VS_REUSE_CHECK`

### 4.3 LaTeX layout debug loop

Observed sequence:

`fact block -> screenshot -> prompt -> tabularx -> screenshot -> parbox -> screenshot -> remove table`

Why it happened:

- fact data existed only as prose/fact lines inside Markdown
- renderer had to parse and typeset them ad hoc
- no reusable design-token layer existed
- no renderer/profile routing was decided before layout work began
- review feedback targeted geometry, but the system had no single token to change

### 4.4 Publication form discovered too late

Evidence:

- `publication_form` stayed `PROSE_BOOK`
- the actual artifact only became a real `DISCOVERY_BOOKLET` in 006C
- title-page, chapter, intro, closing expectations were inherited from the wrong shape

Correction:

- editorial form must be selected before manuscript generation
- file format (`DIGITAL_PDF`) is not the publication profile

### 4.5 Content vs typesetting

Where Codex reasoning added value:

- rights boundary
- shortlist
- voice consistency
- verdict honesty
- structural compression
- final identity corrections

Where deterministic rendering should have taken over much earlier:

- fact layout
- spacing tweaks
- label treatment
- link treatment
- page geometry

### 4.6 Final identity/link QA

Canonical repo/link fixes in 006C show the identity contract arrived too late.

Canonical identity should become authoritative at:

research identity
→ structured content object
→ renderer input
→ displayed text
→ href

## 5. Old pipeline

`source intake -> donor audit -> broad BookSpec -> shortlist -> samples -> human review -> full manuscript -> human review -> renderer proof -> human review -> full render -> correction -> publication-form correction -> more correction -> public publication`

This worked, but it was too mission-heavy for a compact booklet.

## 6. Target compressed pipeline

### Proposed two-mission operating model

| Mission | Scope | Human gate |
| --- | --- | --- |
| MISSION 1 — CONTENT | SourcePack, rights/provenance, publication profile, shortlist, structure, manuscript, editorial QA, preview package | one approval: profile + voice + external-release intent |
| MISSION 2 — PRODUCTION | approved manuscript, deterministic renderer, final artifact, technical QA, publication packet, consumer publication, live verification | external publication approval only if not already bundled into the Mission 1 approval |

### Compression rule

For a known profile with a known renderer and known consumer:

- no separate design-iteration missions
- no separate compilation gate
- no separate tiny typography approval slices

## 7. Human gate policy

### Justified gates

- rights ambiguity
- publication-profile selection
- voice/editorial direction when novel
- visual direction when novel
- external publication

### Unjustified repeated gates

- small typography corrections
- routine QA PASS
- deterministic compilation
- known publication adapter usage
- known profile reuse

### Reusable rule

`KNOWN PROFILE + KNOWN RENDERER + KNOWN CONSUMER`

should run L2-style deterministic production without repeated design approval loops.

## 8. Publication profiles

### Minimal profile set

| Profile | Structural scaffolding | Default renderer | Human gates | QA emphasis |
| --- | --- | --- | --- | --- |
| CONVENTIONAL_BOOK | internal title page likely, headed intro, chapter scaffolding, longer close | `PANDOC_XELATEX` | scope, voice, external publication | text layer, chapter structure, print/export sanity |
| DISCOVERY_BOOKLET | no mandatory internal title page, short/no-heading intro, compact entries, short close, screen-first | `HTML_CSS_CHROMIUM` preferred | scope, visual direction, external publication | canonical links, overflow, clickable URLs, page-count sanity |
| HANDBOOK | procedural sections, reusable callouts, likely mixed long/short blocks | `PANDOC_XELATEX` default | scope, visual direction if new | structure completeness, internal navigation |
| REPORT | evidence-first sections, charts/tables, executive-summary pattern | `HTML_CSS_CHROMIUM` preferred | scope, external publication | source references, layout, links, export clarity |

### Implemented contract

Added:

- `publication_profile` to `BookProject`
- `publication_profile` to `BookSpec`

Current mappings:

- `your-saas-bill-is-ridiculous` → `DISCOVERY_BOOKLET`
- `unusual-indices-book` → `CONVENTIONAL_BOOK`
- `fragments-therapists-notebook` → `CONVENTIONAL_BOOK`

## 9. Renderer routing

### Decision

| Renderer family | Decision |
| --- | --- |
| `PANDOC_XELATEX` | KEEP for conventional prose books, print/KDP-oriented interiors, and long-form text-heavy work |
| `HTML_CSS_CHROMIUM` | PREFERRED NEXT PILOT for discovery booklets, reports, field guides, and card/fact/link-heavy digital PDFs |

### Why

The expensive failures were web-layout-class problems:

- alignment
- spacing
- fact blocks
- label treatment
- clickable links
- single-entry card/page layouts

Those are cheaper in HTML/CSS than in custom LaTeX table gymnastics.

### Implemented contract

Added:

- `preferred_renderer` to `BookProject`
- `preferred_renderer` to `BookSpec`

Current state:

- live booklet remains `PANDOC_XELATEX` because that is what shipped successfully
- `books/design/profiles/discovery-booklet.json` records `HTML_CSS_CHROMIUM` as the preferred default for the next comparable booklet

## 10. HTML/CSS micro-pilot

### Result

PILOTED

Artifacts:

- `tmp/book-factory-retro-001/agent-reach-html-pilot/agent-reach.html`
- `tmp/book-factory-retro-001/agent-reach-html-pilot/agent-reach.png`
- `tmp/book-factory-retro-001/agent-reach-html-pilot/agent-reach.pdf`

Observed:

- existing local browser path was available cheaply via Playwright CLI
- one entry rendered to PNG and PDF without adding a new repo dependency
- the fact block became a trivial vertical stack instead of a LaTeX table problem
- clickable URL behavior is straightforward

Verdict:

- yes, HTML/CSS would likely have made the repeated fact-block corrections materially cheaper
- not enough evidence yet to replace the current prose-book renderer generally

## 11. Canonical content-object decision

### Decision

Do not build a CMS.

But the next comparable booklet should stop relying on renderer-side parsing of fact lines from free-form Markdown.

### Recommended smallest object

`RepositoryEntry`

- `name`
- `category`
- `body`
- `replaces`
- `cost`
- `setup`
- `best_for`
- `verdict`
- `canonical_url`

### Current implementation status

NOT IMPLEMENTED in this mission.

Reason:

- high ROI conceptually
- but adding the object plus migrating the current manuscript would exceed the bounded retro scope

## 12. QA / preflight

### Compression decision

Do not build a large new CLI here.

Next useful seam should be one profile-aware preflight command conceptually covering:

- required sections
- canonical links
- duplicate/placeholder checks
- build success
- page-count sanity
- text layer
- clickable links
- artifact/packet existence

### Current implementation status

NOT IMPLEMENTED.

Reason:

- the contract is clear
- the command can be built cheaply later once the next profile/renderer is selected

## 13. Donor-policy correction

### New rule

Donor outcomes must distinguish:

- `REFERENCE`
- `PATTERN`
- `COMPONENT`
- `RUNTIME`

If the donor is not `COMPONENT` or `RUNTIME`, and the proposed custom work crosses a small complexity threshold, trigger:

`BUILD_VS_REUSE_CHECK`

### Lightweight threshold

Trigger the check when work implies any of:

- new renderer or layout engine
- new dependency
- 3+ new implementation files
- maintenance-bearing reusable adapter
- expected reuse beyond one acceptance case

Do not trigger it for tiny adapters or five-line patches.

### Current implementation status

Policy only in this retro. No donor-matrix vocabulary change implemented yet.

## 14. Success metrics

Next comparable digital publication should target:

| Metric | Target |
| --- | --- |
| production missions after intake | `<= 2` |
| human approval gates before publication | `<= 1` |
| layout-debug missions for known profile | `0` |
| manual page patches | `0` |
| canonical link errors in final RC | `0` |
| publication profile chosen before manuscript | `yes` |
| renderer chosen before design/build | `yes` |
| custom renderer code | `0 preferred`, otherwise one bounded reusable adapter |

## 15. Changes implemented

Implemented in this mission:

1. `publication_profile` contract added to `BookProject` and `BookSpec`
2. `preferred_renderer` contract added to `BookProject` and `BookSpec`
3. `books/design/profiles/discovery-booklet.json` added as a minimal reusable design-token/profile record
4. `book_design_profile.schema.json` added and wired into repository validation
5. `tmp/` added to `.gitignore`

Not implemented:

- canonical `RepositoryEntry` object
- consolidated preflight command
- donor-matrix status vocabulary expansion
- full HTML/CSS renderer

## 16. Readiness for next project

### unusual-indices-book

Status:

- NOT_READY

Exact remaining blocker:

- no approved `BookSpec` / publication-profile / renderer decision for that book yet

The Factory is more ready operationally, but `unusual-indices-book` is a different acceptance case and should not inherit `DISCOVERY_BOOKLET` by default.
