# BOOK-FACTORY-002A — Dify / Cortex RAG Pilot for Unusual Indices

Status: STOP_FOR_HUMAN_DECISION  
Cost class: NORMAL  
Mission type: donor pilot / local report-only

## 1. Verdict

Donor verdict: `PATTERN_SOURCE`

Dify looks technically credible as a self-hosted RAG substrate for isolated book corpora, but this mission did not prove a safe local runtime pilot on the current machine. It should not be admitted as a Cortex RAG provider yet.

Why it does not remain `PILOT_NOW`:

- no Docker runtime is available on this machine
- Dify self-hosting expects Docker Compose and multiple dependent services
- no local embedding model was already prepared for a bounded free-local pilot
- the Knowledge API key scope is broader than one dataset and therefore needs careful containment

## 2. License / practical-use risk

Observed license basis:

- Dify is published under a modified Apache 2.0 license
- commercial use is allowed
- a commercial license is required for multi-tenant operation unless explicitly authorized
- frontend logo/copyright removal is restricted when using the Dify frontend
- those frontend restrictions do not apply to uses that do not involve the frontend

Practical risk for intended ABVX internal use: `MEDIUM`

Reasoning:

- internal single-user self-hosted use appears aligned
- multi-tenant or service-provider use is explicitly constrained
- the producer reserves the right to adjust the open-source agreement, which increases governance risk versus a plain permissive license

This is not a legal conclusion. It is an engineering-risk classification for the intended internal Cortex substrate role.

## 3. Self-hosting / maintenance footprint

Documented Dify self-hosting path is Docker-first.

Minimum observed requirements:

- Docker Desktop / Docker Compose on macOS
- CPU >= 2 cores
- RAM >= 4 GiB, with macOS guidance to configure Docker VM with 8 GiB

Observed dependent services in the documented Docker Compose path include:

- api
- web
- worker
- plugin_daemon
- agent backend
- PostgreSQL
- Redis
- Weaviate
- nginx
- sandbox containers

Engineering implication:

- this is not a tiny local binary or single-process pilot
- startup, cleanup, upgrades and health checks are materially heavier than the current ABVX native retrieval bridge

## 4. Relevant product fit

Dify does map naturally to the bounded question being asked.

Useful observed seams:

- create isolated knowledge bases
- ingest documents by text or file
- asynchronous indexing with explicit status polling
- metadata fields and batch metadata updates
- chunk retrieval / test retrieval endpoint
- model/provider abstraction for embeddings and rerankers
- dataset tags and retrieval configuration inspection
- download original documents and ZIP export of uploaded-file documents

This is enough surface area to support a future:

`BookSourcePack -> ingestion request -> isolated dataset -> retrieval request -> normalized ContextPack`

without making Dify canonical storage.

## 5. Book-specific isolation assessment

Conceptually strong.

Why:

- knowledge bases are first-class and individually addressable
- per-knowledge-base metadata fields and tags exist
- retrieval can target one dataset directly
- document metadata can preserve source-system IDs for deterministic sync/update

This makes a dedicated `BOOK_CONTEXT / unusual-indices-book` dataset plausible without mixing unrelated corpora.

## 6. Pilot corpus selected

A small safe pilot corpus was defined from already-local material:

1. `books/source-packs/unusual-indices-book-source-pack.json`
2. `context/requests/unusual-indices-book.json`
3. `evidence/context-packs/unusual-indices-book.json`
4. `books/projects/unusual-indices-book.json`
5. `books/specs/unusual-indices-book-spec.seed.json`
6. `content/items/content-publish-003-1d3x-popindex-ciggie.json`
7. `content/fixtures/1d3x-cigarette-index-article.json`
8. `intake/items/cigarette-index.json`
9. `docs/audits/book-factory-001-donor-audit-architecture-intake.md`

Why this corpus:

- already local
- already rights-bounded inside ABVX
- directly relevant to unusual-indices-book
- mixes source metadata, public proof, and preparation context
- small enough for a first isolated dataset

## 7. Runtime pilot status

Local deployment status: `NOT_STARTED`

Blocking observations on the current machine:

- `docker` command missing
- no evidence of an already-running Dify instance
- Ollama is installed, but no embedding-specific model was already prepared for a bounded free-local Dify pilot

Observed local model inventory:

- `gemma4:12b`
- `gpt-oss:20b`
- `qwen2.5-coder-3b-continue`
- `qwen3.5:4b`

This was enough to confirm some local inference capacity exists, but not enough to prove a clean Dify knowledge-base pilot without additional setup.

## 8. Retrieval test plan that would have been run

Defined deterministic retrieval intents:

1. Source inventory  
   "What unusual-index examples exist in this corpus?"

2. Specific fact retrieval  
   "What does the corpus say about translating air pollution into cigarette equivalents?"

3. Cross-source synthesis  
   "Which existing sources could support a chapter about indices that make abstract conditions intuitive?"

4. Provenance  
   "For the cigarette-equivalent example, identify the source material supporting the answer."

5. Negative / absence  
   "Does this corpus contain reliable material about happiness indices?"

Expected pass condition:

- chunk-level provenance
- explicit absence handling
- no fabricated coverage outside the selected corpus

Because runtime pilot did not start, these tests remain defined but unexecuted.

## 9. ChapterContext usefulness assessment

Result: `PLAUSIBLE_BUT_UNPROVEN`

The observed API surface is sufficient in principle to support a future bounded ChapterContext-like output containing:

- relevant sources
- extracted snippets
- source IDs / metadata
- coverage gaps
- uncertainty / confidence notes

What remains unproven:

- practical retrieval quality on mixed ABVX JSON + markdown artifacts
- whether default chunking preserves enough structure for book-outline work
- whether provenance remains clean enough after ingestion of ABVX-style machine-readable documents

## 10. Comparison with current ABVX / Cortex native approach

| Dimension | Current ABVX/Cortex native path | Dify |
| --- | --- | --- |
| Ingestion effort | very low for already-coded providers | higher; requires external runtime |
| Heterogeneous document ingestion | limited | materially stronger |
| Retrieval API shape | already bounded around ContextRequest -> ContextPack | rich dataset/document/chunk API |
| Provenance | strong because sources stay explicit in ABVX | plausible, but not yet proven on this corpus |
| Corpus isolation | explicit by request/provider boundary | natural via dedicated knowledge bases |
| Provider flexibility | moderate today | stronger model/provider abstraction |
| Observability | currently evidence-first but simple | richer indexing/retrieval state surface |
| Maintenance | low | materially higher |
| Resource footprint | low | high relative to current ABVX needs |
| Lock-in risk | low | medium |

Bottom line:

- Dify is stronger on ingestion and reusable retrieval substrate features
- current ABVX/Cortex path is lighter, cheaper and safer operationally

## 11. Provider / cost requirements

For a real local Dify pilot, the missing prerequisites are:

- Docker Desktop + Compose
- one embedding provider path
- bounded secret handling for Dify API access

Preferred future pilot path:

- self-hosted only
- isolated local instance
- one dedicated unusual-indices dataset
- free-local embeddings if a small compatible local embedding model is already available

Not acceptable for the next step:

- paid cloud deployment
- public Dify exposure
- committing provider credentials

## 12. Recommended integration boundary

Smallest justified future seam:

`BookSourcePack -> Cortex ingestion request -> Dify knowledge base -> retrieval request -> Dify retrieval result -> Cortex-normalized ContextPack -> Book Factory consumer`

ABVX should own:

- dataset reference
- ingestion state
- source provenance
- retrieval evidence
- human/provider approval boundaries

ABVX should not own:

- vector internals
- chunk store internals
- Dify workflow state as canonical truth

## 13. Failure / exit strategy

Exit feasibility looks acceptable if we keep the boundary narrow.

Preferred rules:

- canonical documents remain outside Dify
- dataset IDs are disposable references, not canonical identities
- ingestion can be rebuilt from BookSourcePack and selected ABVX artifacts
- retrieval evidence is stored in ABVX, not only in Dify
- Book Factory consumers depend on normalized ContextPack output, not Dify-native payloads

This avoids hard lock-in if another retrieval provider later proves cheaper or safer.

## 14. Recommended next step

Recommended Book Factory step remains:

- continue with the deterministic package path already justified by `vpuna/markdown-to-book`

Recommended retrieval follow-up only if/when needed:

- run a second bounded `BOOK-FACTORY-002A` continuation after Docker is available locally and a small local embedding path is explicitly chosen

That continuation should stay strictly report-only and prove:

- isolated dataset creation
- ingestion of the selected corpus
- retrieval quality on the five deterministic tests
- chunk-level provenance quality
- negative/absence behavior

## 15. Files changed in this mission

- `docs/audits/book-factory-002a-dify-cortex-rag-pilot.md`
- `evidence/integration/book-factory-002a-dify-rag-pilot.evidence.json`
- `registries/external-candidates/book-factory-001.json`
- `registries/donor-capability-matrix.json`
- `registries/capability-gaps.json`

