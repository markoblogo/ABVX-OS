# CORTEX-INTEGRATION-001

Date: 2026-08-08

Scope: read-only discovery of `CortexABV` and `Index Cortex`, then ABVX-only audit artifacts.

Observed repositories:

- `CortexABV` public adapter: `/Volumes/Work/Work/ABVXsite/cortex-abv` at `fcafd0c89b87ba71956c6d68c8205e518d9eeae8`
- `CortexABV-private`: `/Volumes/Work/Work/CortexABV-private` at `59909c4a23af4fed20976a16e6ac01f76659e6fe`
- `Index Cortex`: `/Volumes/Work/Work/index` at `9912bf15b85fd80726ac295771550dfa957c52cc`

Read-only repo status after checks:

- `ABVXsite`: unchanged relative to pre-existing state; still had pre-existing untracked `cortex-abv/author_os/governance/proposals/` and `.../reviews/`
- `CortexABV-private`: unchanged
- `index`: unchanged

## 1. CortexABV current state

Purpose:

- personal, portfolio and cross-project knowledge/memory layer
- private canonical maintainer of approved personal/project facts
- proposal-only bridge toward public surfaces
- future read-only compact context export source for CoqPi

Architecture:

- two-surface project, not one repo:
  - public adapter/docs boundary in `ABVXsite/cortex-abv`
  - local private runtime in `CortexABV-private`
- explicit separation between private memory/runtime and public proposal surface
- inbound-only source model; no return authority to source systems

Storage model:

- append-only JSONL import ledger in `CortexABV-private/data/import-ledger.jsonl`
- plan-level tenant memory-bank contracts with deterministic shadow retrieval
- no database, no HTTP service, no scheduler, no remote store
- no encryption-at-rest guarantee documented; privacy relies on local repository separation and Git-ignore discipline

Ingestion:

- admission-policy-backed import packets only
- allowlisted sources: `base-cortex`, `monitor`, `index/spike`, `cropto`
- real local source adapters exist for `monitor-mn7r`, `index-spike`, `cropto`
- CoqPi ingress is contract-defined and append-only in concept, but not activated as a live bridge

Retrieval:

- tenant-scoped deterministic `scoped_token_overlap` retrieval in the memory-bank shadow runner
- claim evidence required
- hard deny on cross-tenant access
- no production retrieval endpoint observed in `CortexABV-private`
- private vector retrieval exists only as staged private pilots/dry runs in the `ABVXsite/cortex-abv/private-runtime` snapshot

Embeddings/vector search:

- observed only as private staged pilot/readiness/wiring artifacts in the public snapshot
- actual activated vector runtime: UNKNOWN
- public evidence shows no active endpoint or enabled runtime integration

Graph/entity relations:

- explicit tenant, source, packet, proposal, promotion and review relations
- no general-purpose graph DB observed
- entity retrieval beyond these contracts: UNKNOWN

Memory model:

- tenant memory-bank contract per tenant and memory class
- direct personal bank plus import-backed project banks
- bounded retention/promotion/source-scope policy tiers
- memory is contract-first, not an open-ended knowledge lake

APIs/CLI/MCP surfaces:

- Node CLI scripts only in `CortexABV-private`
- public adapter npm checks in `ABVXsite/cortex-abv/private-runtime`
- no MCP server observed
- no HTTP API observed in `CortexABV-private`

Project awareness:

- strong awareness of owner-controlled tenants: `personal`, `azur-menton`, `monitor-mn7r`, `index-spike`, `cropto`
- project-local isolation is explicit

Personal-context model:

- strongest among the audited repos
- personal tenant + personal facts + proposal eligibility + CoqPi compact-pack contract

Provenance/evidence support:

- strong
- SHA-256 digests on packets/provenance refs
- append-only ledger hash chain
- proposal/review/receipt chain
- source-pack digests for bounded corpora

Source admission rules:

- explicit and strong
- exact source IDs, data kinds, classification policies, retention TTLs, promotion eligibility

Write/update semantics:

- append-only ledger write exists
- public update path remains `proposal_only`
- future write executor intent is non-executing and owner-trigger-only

Security/privacy boundaries:

- tenant isolation is strong in contract surface
- inbound-only / no-return boundary is explicit
- protected payloads must stay out of public adapters, logs, and artifacts
- no endpoint exposure observed

Secret handling:

- no secrets committed in the observed repos
- docs repeatedly forbid credentials and token-like exports
- no runtime secret manager observed

Deployment/runtime assumptions:

- local-only private runtime
- public adapter snapshot is auditable but not the deployed private runtime

Test/build status:

- `CortexABV-private`: `npm test` passed `78/78`
- `CortexABV-private`: `npm run tenant:check`, `npm run memory-bank:check`, `npm run azur-menton:check`, `npm run coqpi:context-pack:check ...` passed
- `ABVXsite/cortex-abv/private-runtime`: contracts and receipts are present, but I did not run its full script ladder because it includes many staged dry-run receipt writers; read-only inspection only

Current documentation:

- strong and contract-heavy
- public adapter README is clear
- private runtime README is clear
- many narrow boundary docs exist for CoqPi, AzurMenton, proposal governance, memory banking and retrieval observability

Active vs abandoned:

- active:
  - import admission + ledger
  - tenant contract
  - tenant memory bank
  - proposal governance chain
  - AzurMenton source-pack/shadow contracts
  - CoqPi ingress/context-pack contracts
- experimental but active:
  - vector pilot/readiness/wiring chain
- explicitly abandoned components: none observed

Visible technical debt:

- dual-repo split increases audit overhead
- public snapshot and private runtime have overlapping contract surfaces that can drift
- vector/runtime stage ladder is extensive and governance-heavy relative to current near-term ABVX need
- no small read-only retrieval bridge for external consumers such as ABVX exists yet

## 2. Index Cortex current state

Purpose:

- index / market / methodology / source / observation domain intelligence layer for the 1D3X ecosystem
- bounded context assembly for internal Cortex assistant/report workflows
- artifact and evidence layer over Index, MediaHub, MN7R and Cropto ecosystem inputs

Architecture:

- lives inside the main `/Volumes/Work/Work/index` application
- mixes:
  - `.cortex/*.json` local artifacts
  - library contracts in `src/lib/cortex-*`
  - internal API routes under `src/app/api/internal/cortex/*`
  - scripts for source scan, chunking, context packs, governance evals and artifact build/publish

Storage model:

- file artifacts in `.cortex/`
- runtime/internal ledgers in the index application layer
- internal DB-backed evidence for some report/governance slices

Ingestion:

- source scanning across local ecosystem roots
- artifact build/source scan/chunking pipeline
- ecosystem evidence context packs
- DB-backed SSI and monitoring evidence for some report flows

Retrieval:

- internal context-pack route exists
- retrieval over chunk manifests with filters and token budgets
- ecosystem evidence pack merged into the response
- no cross-project canonical-owner separation at the ABVX level

Embeddings/vector search:

- no real embeddings/vector database observed in `index` Cortex current path
- current pack builder uses search over chunk manifests and bounded selection logic

Graph/entity relations:

- project/source/material/report/evidence vocabulary is documented
- some ecosystem/project relations are encoded
- no explicit general graph runtime observed

Memory model:

- operational ecosystem memory, not personal memory
- strong domain/history/evidence orientation
- not a suitable canonical personal or portfolio memory store

APIs/CLI/MCP surfaces:

- internal API routes for context pack, assistant, workforce and governance receipts
- many local scripts
- no MCP server observed

Project awareness:

- strong awareness of `index`, `mn7r`, `cropto`, `1d3x`, `mediahub`
- not designed for arbitrary portfolio-wide project state

Personal-context model:

- weak / absent
- this is ecosystem/domain memory, not personal owner memory

Provenance/evidence support:

- strong in principle
- manifests, ledgers, chunks, context packs, receipts and tests exist

Source admission rules:

- weaker than CortexABV-private
- concrete gap observed: `.cortex/source-manifest.json` includes noisy session/cache/build artifacts such as `.whatsapp-session*` and `.wwebjs_cache/*`

Write/update semantics:

- internal artifact generation and internal runtime routes exist
- no evidence that it is a general outbound action engine
- some routes interact with protected internal services and external model handoff for bounded assistant/report paths

Security/privacy boundaries:

- internal bearer-token-protected Cortex routes exist
- protected/internal visibilities are encoded
- but source-scan hygiene currently admits noisy artifacts into the corpus, which weakens retrieval trust and minimization

Secret handling:

- internal API secret/environment requirements exist for runtime checks
- secret-management discipline beyond repo/runtime envs: UNKNOWN

Deployment/runtime assumptions:

- part of a deployed Next.js application
- internal Cortex routes assume runtime env vars and manifest availability

Test/build status:

- targeted tests passed:
  - `src/lib/cortex-source-scanner.test.ts`
  - `src/lib/cortex-memory-context-pack.test.ts`
  - `src/app/api/internal/cortex/context-pack/route.test.ts`
- JSON parse validation of key `.cortex` artifacts passed

Current documentation:

- extensive
- `README.md`, `docs/cortex-agent-flow-contract.md`, `docs/commodity-intelligence-layer.md`, `docs/media-hub-domain-model.md`

Active vs abandoned:

- active:
  - source scan/chunking/context packs
  - internal context-pack API
  - governance/evaluation layers
  - workforce and evidence ledgers
  - ecosystem evidence path
- experimental but active:
  - autonomy/governance readiness layers
- explicitly abandoned components: none observed

Visible technical debt:

- source admission/scope hygiene is the biggest concrete issue
- `.cortex` source corpus is too broad for a high-trust context source
- internal runtime and offline artifact generation are coupled inside one product repo
- broad ecosystem scope risks overloading retrieval with irrelevant operational debris

## 3. Ownership boundary matrix

| Concept | Canonical owner |
| --- | --- |
| Project operational status | `ABVX_OS_OWNS` |
| Mission state | `ABVX_OS_OWNS` |
| Human queue | `ABVX_OS_OWNS` |
| Intake item | `ABVX_OS_OWNS` |
| Project event | `ABVX_OS_OWNS` |
| Strategy | `ABVX_OS_OWNS` |
| Decision evidence | `SHARED_WITH_CLEAR_CANONICAL_OWNER` |
| Long-term project history | `CORTEX_ABV_OWNS` |
| Cross-project relationships | `CORTEX_ABV_OWNS` |
| Professional proof/history | `CORTEX_ABV_OWNS` |
| Research corpus | `CORTEX_ABV_OWNS` |
| Source documents | `REFERENCE_ONLY` |
| Domain observations | `INDEX_CORTEX_OWNS` |
| Index methodologies | `INDEX_CORTEX_OWNS` |
| Market facts | `INDEX_CORTEX_OWNS` |
| Media content knowledge | `INDEX_CORTEX_OWNS` |

Interpretation:

- ABVX owns canonical operational control-plane state
- CortexABV owns durable owner/project memory and cross-project knowledge
- Index Cortex owns domain-specific market/index/source intelligence
- evidence may be referenced across boundaries, but one canonical owner must stay explicit

## 4. Integration gap analysis

Current smallest safe gap list:

1. ABVX has no read-only retrieval bridge into CortexABV.
2. CortexABV has no small generic `ContextRequest -> ContextPack` consumer boundary for ABVX.
3. Index Cortex source admission is not strict enough for high-trust downstream reuse.
4. No existing bridge selects what routine ABVX events deserve durable Cortex admission.
5. CoqPi compact pack is contract-defined but not wired to an approved read path.

## 5. Knowledge admission policy proposal

Admission path:

`raw event/intake/result -> admission review -> normalized durable knowledge`

Admit by default only for:

- major project decision
- major project milestone
- capability learned
- durable relationship
- reusable lesson
- publication/book
- research result
- proof/reputation asset

Do not admit by default:

- routine `MEDIA_ASSETS_ATTACHED`
- routine playbook replays
- low-signal operational chatter
- ephemeral failures without durable lesson value

Rule:

- ABVX emits compact events
- CortexABV admission remains selective and reviewable
- aggregation can promote patterns later

## 6. ContextRequest / ContextPack contract

Recommended conceptual request:

```json
{
  "task": "string",
  "project": "string|null",
  "intent": "string",
  "required_domains": ["operational", "project_knowledge", "domain_knowledge"],
  "freshness_requirement": "strict|normal|historical_ok",
  "token_budget": 1200
}
```

Recommended conceptual pack:

```json
{
  "operational_state": [],
  "strategy": [],
  "decisions": [],
  "project_knowledge": [],
  "playbooks": [],
  "constraints": [],
  "sources_evidence": [],
  "unresolved_risks": []
}
```

Readiness:

- ABVX can already provide operational state, strategy, playbooks, events, evidence
- CortexABV can already provide selective private/project knowledge primitives
- Index Cortex can already provide bounded domain context artifacts
- no repo currently provides the combined compiler/orchestrator, which is correct for this stage

## 7. Token economics findings

AZURMENTON-005 showed the cost of reconstructing:

- current project purpose and boundaries
- prior publication workflow
- human-only editorial gates
- durable project-specific facts
- what already happened vs what remained pending

Best future split:

- playbook: deterministic steps and routine validations
- ABVX: current operational state, human gates, events, evidence, decisions
- CortexABV: durable project history, reusable lessons, cross-project context, professional proof

Observed conclusion:

- manual reconstruction is the expensive part
- the next win is not more orchestration
- the next win is a small read-only context retrieval boundary

No numeric token-savings claim is made because it was not instrumented.

## 8. Intake integration readiness

Status: `PARTIAL`

What current CortexABV can support:

- project association through tenant/source IDs
- previous similar items only where they already entered the private memory/admission path
- selective relatedness only inside bounded tenant memory

What is missing:

- general semantic relatedness service for arbitrary new ABVX intake items
- explicit entity retrieval API for ABVX consumers
- read-only related-item lookup bridge

## 9. CoqPi integration readiness

Status: `PARTIAL_TO_STRONG_CONTRACT`, `NOT_READY_FOR_LIVE_BRIDGE`

What exists:

- shared ingress contract
- compact CoqPi context-pack contract
- explicit private/read-only/approved boundary

What is missing:

- actual approved export pipeline from CortexABV to CoqPi
- owner-selected pack management/runtime path

## 10. ABVX.xyz integration readiness

Status: `PARTIAL`

What exists:

- proposal governance boundary
- public surface proposal contract
- non-executing write-executor intent
- target surfaces include `abvxsite`

What is missing:

- small curated public projection policy over combined ABVX + Cortex material
- approval workflow that chooses what becomes public

## 11. Index Cortex bridge design

Future bridge rule:

- Index Cortex remains canonical for market/domain knowledge
- CortexABV may ingest only reviewed, bounded, classified packets from Index
- ABVX should reference Index facts/evidence, not store them canonically

Example flow:

`Index observation/methodology/source result -> reviewed packet -> CortexABV project/domain memory -> ABVX reference only when operationally relevant`

For a request like `write a book about unusual indices`:

- CortexABV should provide owner/project/book context
- Index Cortex should provide methodology, observations, index taxonomy, market evidence
- ABVX should provide only current operational mission state, decisions and constraints

## 12. External candidate gap mapping

Local evidence observed:

- `HyperResearch` is already present as an intake item and fits a possible deep-research/provider pattern source, but not the core canonical-memory boundary.

Other named candidates in the mission brief were not found as existing ABVX registry/intake records during this audit, so I am not promoting any additional gap mappings from repository evidence alone.

Result:

- candidate gap mapping recorded only for `HyperResearch` as a possible future research-provider pattern source
- no complexity added for the others in this pass

## 13. Security / trust-domain findings

Trust domains:

- personal/private
- project-private
- corporate/domain-private
- public
- external/untrusted

Concrete findings:

1. `CortexABV-private` has the clearest trust-domain boundaries.
2. `Index Cortex` currently mixes internal/protected corpus generation with noisy local artifacts in `.cortex` scans, which weakens minimization and retrieval trust.
3. `ABVX` must not become the long-term knowledge store; its role should stay operational/canonical.
4. `CortexABV` should never receive routine ABVX operational noise by default.
5. `Index Cortex` and `CortexABV` should not share canonical ownership of the same fact class.

## Recommended next slice

Choice: `D. fix a blocking Cortex deficiency first`

Why:

- `Index Cortex` currently admits noisy session/cache/build artifacts into `.cortex` source manifests and chunk manifests
- any bridge or context compiler built now would amplify contaminated retrieval scope
- a small source-admission hygiene fix is a narrower and safer prerequisite than building a bridge on top of low-trust manifests

Specifically:

- tighten `Index Cortex` source-scan allowlists/excludes
- regenerate bounded manifests
- then evaluate `A. ABVX-OS ↔ CortexABV read-only retrieval bridge`

STOP_FOR_HUMAN_DECISION.
