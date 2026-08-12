# BOOK-FACTORY-003 — Your SaaS Bill Is Ridiculous

Status: STOP_FOR_HUMAN_DECISION
Cost class: NORMAL

## 1. Source intake result

Real source intake created from:

- `/Users/antonbiletskiy-volokh/Downloads/gh_ru.pdf`

Observed source identity:

- title/cover claim: `33 бесплатных репозитория вместо подписок на $25 000 в год`
- visible attribution handle: `@unicodef1wn`
- visible translation note: `Перевод для @prompt_design`
- observable framing: open-source alternatives to expensive SaaS across agents, automation, CRM, analytics, media and productivity

This source is now registered as:

- intake item: `intake/items/your-saas-bill-is-ridiculous-pdf.json`
- BookProject: `books/projects/your-saas-bill-is-ridiculous.json`
- BookSourcePack: `books/source-packs/your-saas-bill-is-ridiculous-source-pack.json`

## 2. Rights verdict

Verdict:

- `SOURCE_USE = RESEARCH_LEADS_ONLY`

Why:

- the PDF identifies itself as a translated compilation
- attribution is present
- an obvious derivative republication license was not observed
- no explicit permission to republish or translate the source prose was observed
- no clearly identified original English publication/source chain was observed from the material reviewed here

Implication:

- the future English book can proceed
- it must be independently written from primary repository and documentation sources
- expressive source prose from the PDF should not be copied or translated into the book

## 3. 33-repo extraction result

All 33 source repositories were extracted into a machine-readable matrix:

- `books/research/your-saas-bill-is-ridiculous-repos.tsv`

The source categories normalize to:

- `free_tools` — 1
- `ai_agents_coding` — 2–6
- `ai_search_voice_meetings` — 7–10
- `content_factories` — 11–15
- `automation` — 16–17
- `productivity_business` — 18–24
- `backend_analytics_storage` — 25–28
- `meta_repositories` — 29–33

## 4. Repository health summary

Conservative summary from current first-party GitHub surfaces:

- maintained: 31
- alive but weaker than the source framing implies: 1
- unclear due unstable current fetch / incomplete first-party signal: 1
- archived: 0 observed

Most of the list is materially active. The bigger problem is not decay; it is category inflation and replacement overclaiming.

## 5. Materially outdated or misleading source claims

Most important corrections:

1. `Perplexica` source identity is outdated.
   Current canonical repo resolves to `ItzCrazyKns/Vane`, not the older `ItzCrazyKns/Perplexica` identity.

2. The meta section (`Anthropic Agent Skills`, `Awesome Agent Skills`, `Awesome MCP Servers`, `Official MCP Servers`, `Awesome Copilot`) is not a list of SaaS replacements.
   These are catalogs, examples and protocol references.

3. `free-for-dev` is not a replacement product.
   It is a catalog of free tiers and developer offers.

4. Several “replaces X” claims are directionally true but too broad:
   - `Continue` vs Cursor/Copilot
   - `Twenty` vs Salesforce
   - `AppFlowy` vs Notion
   - `Plane` vs Jira/Linear/ClickUp
   - `Supabase` vs Pinecone

5. Some content/media tools can replace subscription spend, but only after shifting the bill into:
   - GPU
   - external model APIs
   - rendering time
   - maintenance
   - your own operator time

This is the core factual correction ledger the future book needs.

## 6. Strongest ABVX donor discoveries

Best current ABVX-relevant discoveries from this list:

### `Agent-Reach`

- gap fit: `external_actions`, `research_engine`
- verdict: `PILOT_WHEN_NEEDED`
- value: bounded external reach without per-platform API contracts

### `Composio`

- gap fit: `external_actions`, `opportunity_engine`
- verdict: `PILOT_WHEN_NEEDED`
- value: authenticated integrations/tool substrate for future agent actions

### `Langfuse`

- gap fit: `project_intelligence`, `research_engine`
- verdict: `PILOT_WHEN_NEEDED`
- value: serious observability/eval donor if ABVX ever needs that layer

### `n8n`

- gap fit: `external_actions`
- verdict: `PILOT_WHEN_NEEDED`
- value: strongest broad automation donor in the list, but must not be imported as a general workflow engine

### `Twenty`

- gap fit: `opportunity_engine`
- verdict: `PILOT_WHEN_NEEDED`
- value: one of the stronger CRM candidates when ABVX reaches real contact/deal operations

### `Listmonk`

- gap fit: `media_resource`, `opportunity_engine`
- verdict: `PILOT_WHEN_NEEDED`
- value: strong owned-email distribution donor

Already operationally known/proven outside this mission:

- `Plausible Analytics`
- `Supabase` as a general ecosystem option, though not automatically for every ABVX need

## 7. Donor registry changes made

Added:

- `registries/external-candidates/book-factory-003.json`

This records bounded proposals only. No donor was adopted or installed in this mission.

## 8. Recommended final project count

Recommended range:

- 20–24 projects in the final book

Why not 33:

- 29–33 are reference catalogs rather than direct replacement products
- several entries overlap too heavily
- some replacement claims are too weak to justify full standalone treatment
- a shorter list will produce a sharper free book and a better first Book Factory acceptance case

Suggested candidates to cut or demote:

- `free-for-dev` as a scene-setting appendix/reference, not a main chapter project
- at least 3 of the 5 meta repositories as appendix/reference only
- one of `NocoDB` / `Baserow`
- one of `n8n` / `Activepieces`
- `OpenShorts` unless later audit strengthens its maturity and licensing confidence

## 9. Proposed title / subtitle options

### Option A

`Your SaaS Bill Is Ridiculous`
`33 Open-Source Projects That Would Like a Word`

### Option B

`Stop Renting Your Software Stack`
`What Open Source Actually Replaces, and What It Still Makes You Pay For`

### Option C

`Open Source Would Like a Word`
`A Skeptical Guide to Escaping Expensive SaaS Without Lying to Yourself`

Recommended direction:

- keep Option A as the lead
- but write the book with the skepticism promised by Option C

## 10. Proposed book structure

Do not translate the Russian section names directly.

Recommended English TOC shape:

1. `The Bill`
   Why SaaS sprawl feels cheap until it suddenly does not

2. `Before You Cancel Anything`
   Hosting, models, maintenance, upgrades, security and operator time

3. `The Agent Gold Rush`
   Coding agents, integrations and observability

4. `Search, Voice and Meetings`
   What actually works locally and what still leaks cost elsewhere

5. `Content Factories and GPU Dreams`
   Video, decks, SEO and the real price of “free”

6. `Automation Without a Zap Tax`
   What self-hosted workflow tools buy you and what they demand

7. `CRM, Workspaces and Business Plumbing`
   The seductive middle of the stack

8. `Infrastructure, Analytics and the Things You Will End Up Operating`
   Databases, analytics, storage and boring reality

9. `Catalogs, Protocols and Rabbit Holes`
   Repositories that are useful but are not products

10. `Should You Actually Self-Host This, or Just Pay the 20 Dollars?`
    The recurring decision framework

## 11. Proposed repository-entry format

Use this as the repeatable project-section template:

### PROJECT

What it is

What the source claim says it replaces

What it actually replaces

What is genuinely free

What you still have to pay for

Setup / maintenance reality

Who should use it

Who absolutely should not

ABVX verdict / editorial verdict

Primary links

This format should stay elastic; not every project deserves the same length.

## 12. Scope estimate

Recommended first real Book Factory acceptance case:

- final project count: 20–24
- chapter count: 8–10
- target word count: 28,000–36,000
- approximate page count: 110–150
- screenshot strategy: selective only

Screenshot recommendation:

- use very few screenshots, if any
- they will stale quickly
- they increase maintenance cost without reliably increasing long-term value
- prefer diagrams, short comparison tables and a few carefully chosen interface proof images only where they materially help

Expected production complexity:

- `NORMAL`

Remaining Book Factory stages after this mission:

- final concept selection
- bounded BookSpec
- chapter-level research packs
- manuscript drafting
- editorial QA
- ABVX Books publication packet

## 13. Research gaps

- original English source chain for the translated compilation remains unresolved
- explicit derivative republication permission remains unresolved
- some repositories use `NOASSERTION`, AGPL or fair-code-like licensing patterns that need deeper operational review before real adoption
- hands-on setup cost is still unproven for the heaviest media/agent/video tools
- a few activity checks were conservative because first-party fetches were unstable mid-audit

## 14. ABVX publication plan

Target publication surface:

- `abvx.xyz` via the existing Books/project surface

Future packet must include:

- title
- subtitle
- description
- cover
- downloadable PDF artifact
- optional repository/source links
- tags
- publication date
- SEO/LLMO metadata

No new ABVX Books architecture is needed for this mission.

## 15. Book Factory state after this mission

Desired state achieved:

- `SOURCE_INGESTED`
- `RIGHTS_REVIEWED`
- `REPOSITORIES_AUDITED`
- `CONCEPT_PROPOSED`
- `WAITING_FOR_HUMAN`

Explicitly not started:

- `MANUSCRIPT_STARTED`
