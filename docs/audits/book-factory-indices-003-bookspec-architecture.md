# BOOK-FACTORY-INDICES-003 — BookSpec Freeze + Narrative Architecture

Status: `READY_FOR_HUMAN_APPROVAL`

Cost class: `NORMAL`

This is the final pre-manuscript planning artifact for `unusual-indices-book`. It freezes a candidate BookSpec, narrative architecture, verification plan and manuscript handoff pack for human approval before `BOOK-FACTORY-INDICES-004 — Manuscript V1`.

## 002A closeout

`BOOK-FACTORY-INDICES-002A` was committed and pushed before this work.

- Commit: `c37ab25`
- Message: `chore: record unusual indices commercial package selection`
- Push: `origin/main`

## Frozen commercial package candidate

- Title: `Burgers, Lipstick & Underwear`
- Recommended subtitle: `What Strange Indicators Really Tell Us About the Economy`
- Primary objective: `COMMERCIAL_AMAZON_SUCCESS`
- Reader: curious general nonfiction reader interested in popular economics, strange comparisons and data storytelling.
- Cover territory: object-led popular nonfiction using burger, lipstick and underwear; no dashboards, owner-project branding or generic AI imagery.

Subtitle variants considered:

1. `What everyday objects reveal about the economy` — clear but too narrow and soft.
2. `The Strange Signals We Use to Understand the Economy` — good territory but less forceful.
3. `What Strange Indicators Really Tell Us About the Economy` — selected because it names indicators, economy and skepticism.
4. `How Burgers, Lipstick and Underwear Became Economic Signals` — memorable but repeats title objects and narrows the book.

## Thesis

Humans invent indices because reality is too large to hold in the head. A burger, an hour of work, a tube of lipstick or a ship full of grain can turn abstraction into something familiar enough to argue with. That translation is powerful: it can reveal purchasing power, confidence, risk, fragility and manipulation faster than official language can. But a vivid proxy is also dangerous. Some strange measures are grounded and useful; others survive because they are funny, flattering or convenient. This book is about learning to enjoy the strange measures without being fooled by them.

## Narrative architecture

Opening recommendation: `Big Mac Index`.

Reason: it is familiar, commercial, globally recognizable and naturally introduces usefulness and limitation without beginning with methodology, 1D3X or a definition of “index”.

Final chapter count: `8`.

1. `The Measure You Can Eat` — Big Mac, Starbucks Latte, IKEA Billy.
2. `Prices Become Human` — iPhone work-time, Working Hours, Date Night, affordability comparisons.
3. `The Folklore of Recession` — Lipstick, Men’s Underwear, Hemline, Skyscraper.
4. `The Economy Under the Economy` — Baltic Dry, Container Freight, electricity demand, restaurant reservations.
5. `Air You Can Count` — cigarette-equivalent air pollution and climate equivalence.
6. `When Measures Fight Back` — Goodhart risk, benchmark manipulation, LIBOR, Doing Business.
7. `Benchmarks for Machines` — AI Index, SWE-Bench, government AI readiness, Artificial Analysis.
8. `How to Read a Weird Index` — reader checklist, evidence taxonomy, source hierarchy.

The architecture avoids `one index = one chapter`. Chapters group related measures into a progression from familiar objects, to lived prices, folklore, physical systems, risk translation, manipulation, AI benchmarks and a final reader method.

## Content selection freeze

`CORE`:

- Big Mac Index
- iPhone / work-time
- Working Hours
- Cigarette Equivalent
- Lipstick Index
- Men’s Underwear Index
- Baltic Dry Index
- Container Freight
- manipulation/governance case
- AI benchmark case

`SUPPORT`:

- Starbucks Latte Index
- Skyscraper Index
- Date Night
- one affordability comparison
- CO2 Flight Equivalent
- Electricity Demand
- Restaurant Reservation

`SIDEBAR_OPTIONAL`:

- Hemline Index
- IKEA Billy Index
- Haircut Index
- Taxi Affordability
- Hotel Room Index
- Second-hand Index

`EXCLUDE`:

- owner-project promotional chapters
- raw corpus dumps
- AI governance disconnected from the index promise
- unverified internet folklore presented as fact

## Evidence policy

Internal evidence taxonomy:

- `ROBUST`
- `PLAUSIBLE`
- `CONTESTED`
- `FOLKLORE`
- `FAILED_DISCREDITED`
- `MANIPULATION_GOVERNANCE_CASE`

Source hierarchy:

1. original index publisher / methodology
2. academic paper / official institution
3. high-quality publisher or journalism
4. reputable secondary source
5. source-pack summary only as lead

The source pack is a lead, not final authority where an underlying source exists.

## Verification queue

Verification queue path: `books/research/unusual-indices/verification-queue.json`.

Counts:

- `P0`: 10
- `P1`: 8
- `P2`: 4

Highest-risk claims:

- lipstick evidence and recession-predictor status
- Men’s Underwear / Greenspan attribution and evidence
- skyscraper predictive performance
- cigarette-equivalent pollution methodology and health boundaries
- incompatible air-quality measures
- Goodhart / manipulation framing
- LIBOR manipulation as governance case
- AI benchmark framing

## Additional Intelligence task

One additional bounded task was admitted for this mission:

- Task: `research-relevance-ranking`
- Provider: `cheap.api`
- Model: `gpt-5.6-luna`
- Runtime artifact: `evidence/intelligence/book-factory-indices-003-research-relevance-ranking.runtime.json`
- Result: `SUCCEEDED`
- Estimated cost: `$0.0014978`
- Ranked items: `20`
- High-risk items: `6`

The task helped prioritize source/claim attention for the verification queue. It did not alter the architecture or create a new intelligence framework.

## ChapterContext contract

`ChapterContext` should contain:

- chapter id/title
- central question
- approved stories
- verified claims
- evidence status
- source references
- useful numbers/examples
- myth or uncertainty notes
- visual opportunities
- prohibited or unsupported claims

It should be generated from the chapter architecture, normalized corpus, source metadata and verification queue. It should not dump raw corpus paragraphs into prompts.

## RAG decision

`RAG = NOT_NEEDED_YET`.

Reason: chapter-specific ContextPacks can be produced deterministically from the structured corpus, chapter mapping, source metadata and verification queue. No concrete retrieval failure currently justifies vector infrastructure.

## Manuscript size and format plan

- Target word range: approximately `30,000-35,000` words.
- Expected print range: approximately `130-170` pages.
- Expected chapters: `8`.
- Primary formats: `KINDLE_REFLOWABLE` and `PAPERBACK_INTERIOR`.
- Hardcover: defer unless manuscript and demand justify it.
- Likely trim: `5x8`.
- Interior: black-and-white by default; color only if later visual QA proves value.

This avoids both a short booklet and padded 300-page nonfiction.

## Voice contract

Voice Contract path: `books/manuscripts/unusual-indices-book/VOICE_CONTRACT.md`.

Summary: smart popular nonfiction; dry, skeptical, fast, clear, occasionally provocative. Humor should come from observation, contrast, absurdity and precise phrasing, not constant punchlines or repeated AI-like transitions.

## Visual policy

Allowed:

- simple comparison charts
- small diagrams
- equivalence graphics
- historical examples
- myth-vs-measure graphics

Avoid:

- dashboard screenshots
- decorative AI imagery
- unnecessary illustrations
- excessive color dependency that harms paperback economics

Visuals should work in grayscale where practical.

## Amazon positioning

Provisional categories:

- Business & Money / Economics
- Science & Math / Mathematics / Statistics
- Computers & Technology / Data Science

Keyword territories:

- popular economics
- data storytelling
- economic indicators
- strange statistics
- Big Mac Index
- data literacy
- unusual comparisons
- Freakonomics

Provisional price ranges:

- Kindle: `$4.99-7.99`
- Paperback: `$12.99-16.99`

Metadata remains provisional until manuscript exists.

## Owner-project rule

`1D3X`, `POP` and `SPIKE` may appear only if author experience adds unique editorial value.

They must not define the book architecture, receive promotional chapters, appear in title/subtitle, appear on cover, receive automatic links/CTAs or receive ranking advantage.

Acceptable framing: `I encountered this problem while building an index.`

Unacceptable framing: `visit my platform.`

## 004 production model

`BOOK-FACTORY-INDICES-004 — Manuscript V1` should not generate the entire manuscript in one giant model call and should not create one Codex mission per chapter.

Preferred loop inside one production mission:

1. build `ChapterContext`
2. resolve P0 and chapter-relevant P1 evidence
3. draft chapter
4. factual QA
5. voice/repetition QA
6. append to `MASTER_MANUSCRIPT`

Human approval should be required only when a material factual, rights, scope or voice issue appears.

## Manuscript V1 acceptance

V1 means:

- complete beginning-to-end manuscript
- all planned chapters present
- P0 factual claims verified
- no known unsupported major claims
- voice reasonably consistent
- visuals marked/placeheld
- citations/source notes retained internally
- no layout/design/KDP work yet

V1 does not mean final copyedit, final cover or final KDP package.

## Context economy for 004

Read for 004:

- `books/specs/unusual-indices-book-spec.proposed.json`
- `books/research/unusual-indices/manuscript-mission-pack.json`
- `books/research/unusual-indices/chapter-architecture.json`
- `books/research/unusual-indices/verification-queue.json`
- `books/manuscripts/unusual-indices-book/VOICE_CONTRACT.md`
- `books/research/unusual-indices/normalized-corpus.json` only through targeted chapter lookup

Ignore by default:

- historical Book Factory audits before this mission
- all 3,786 original source paragraphs
- previous title brainstorms
- discarded TOCs
- owner-project promotional material unless directly relevant to a chapter claim

## State

- BookSpec: `BOOK_SPEC_READY_FOR_HUMAN_APPROVAL`
- Chapter architecture: `READY_FOR_HUMAN_APPROVAL`
- Verification queue: `READY_FOR_MANUSCRIPT_V1`
- Manuscript mission pack: `READY_FOR_HUMAN_APPROVAL`
- Project state: `WAITING_FOR_HUMAN`

Required human approvals before 004:

- subtitle
- chapter architecture
- content selection freeze
- verification queue priorities
- Voice Contract
- target word/page range
- format plan
- Manuscript V1 production plan
