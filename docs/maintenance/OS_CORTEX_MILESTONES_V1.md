# OS and Cortex: maintenance and learning milestones v1

Status: EXPENSIVE scope explicitly approved by the owner. Maintenance, isolated checks and the operator-mediated OS/Cortex learning contract are implemented; measured efficiency awaits a separate trial.

## Ownership and exchange

ABVX-OS and Cortex ABV are independent systems. OS owns tasks, playbooks, operational facts, approval gates and execution. Cortex owns admission, retained knowledge, retrieval and proposed improvements. Experience flows OS → Cortex; reviewed optimization proposals flow Cortex → OS. A Cortex suggestion does not grant execution authority.

Existing capabilities to reuse: Git inventory, portfolio/human queue, operational playbooks, OS context requests, Cortex admission ledger, private memory governance and held-out skill-quality validation. No new scheduler, database, service or model provider is needed for the first integration.

## Milestones and acceptance

| Milestone | Deliverable | Acceptance evidence | State |
| --- | --- | --- | --- |
| M0 Workspace visibility | `bin/maintain inspect` classifies code, documents, private material and working data; local JSON manifest | Read-only tests, no content/credential scan, no deletion, no publishing | Implemented locally |
| M1 Repeatable checks | Frozen synthetic book fixtures; operational-data access denied during regression run | Book Core, prior, reachability, GD3 and Gate A pass without reading working `books/` or `book-radar/` | 138 tests PASS locally |
| M2 Controlled cleanup and publication | Curated code commit from clean main; path/hash archive manifest for selected obsolete output | Clean-checkout validation; no manuscripts, credentials or real ledgers in publication; recovery proof before deletion | In progress |
| M3 OS experience admission | Explicitly selected process-outcome batch, admitted under an `abvx-os` Cortex source/tenant | Schema, digest, source, retention and idempotence checks; real OS → Cortex → OS measurement diagnosis verified | Implemented; real admission/retrieval/diagnosis pilot |
| M4 Measured optimization loop | Cortex produces private proposal; OS imports it for review and measures a bounded trial | Independent held-out runs; measured time/owner effort/rework; all quality and safety gates preserved; rejection retained | Evaluator implemented; independent trial pending |

## Implemented minimal exchange contract

`AbvxOsProcessOutcome` v1 contains only an opaque run ID, workflow ID/version, origin (`OBSERVED` or `SYNTHETIC`), start/end times, status, elapsed seconds, owner minutes or `UNKNOWN`, rework count, quality/safety gate states, and opaque evidence IDs/digests. Workflows initially cover niche research, book production, site content publication and maintenance. No manuscript text, raw transcripts, credentials, personal notes or absolute paths.

OS exports an explicitly selected batch into the existing `CortexABVImportPacket` envelope: source `owned_project_ecosystem/abvx-os`, classification `protected`, permitted use `private_context`, return authority `none`, payload digest attached. Cortex applies admission/retention policy before ledger append. Duplicate batches are idempotent. Real local payloads remain ignored in both repositories; tracked examples are synthetic.

Cortex returns a separate `AbvxOsOptimizationProposal` v1 with exact workflow/version, input batch digest, scoped change, baseline/held-out evidence and metrics, required checks, limitations, `authority: none`, and mandatory owner review. It never returns commands for automatic execution. OS accepts proposals only for its own workflows, detects stale versions/duplicates and records trial acceptance or rejection separately from knowledge admission.

A proposed initial sufficiency gate is at least five baseline and five independent held-out runs of the same workflow, no overlapping run IDs, all required quality/safety gates passed and lower median elapsed time without increased owner effort or rework. This is an operational pilot threshold, not statistical proof or a substitute for semantic review. Missing metrics retain `UNKNOWN` and cannot establish efficiency. Later thresholds depend on observed variance and workflow risk.

## Cortex status checked

The inspected private runtime already has admission/retention, append-only ledger, tenant memory banks, private proposal governance and a held-out skill-quality protocol. The curated update adds OS to the admitted source and isolated tenant lists. M3/M4 use the owner-approved exception documented in Cortex `docs/ABVX_OS_LEARNING_V1.md`; all other inbound-only boundaries remain in force. Public `ABVXsite/cortex-abv/private-runtime` remains a reviewed snapshot and is not an automatic sync target.

The latest “Cortex ABV” chat also prepared an ID governance handoff in a separate checkout. Its six-file change set was recovered into the curated Cortex branch; its complete ID-backed check passed 107/107 before OS integration. ID preferences are governance candidates, not operational outcomes or public biography.

## Cost gate

The existing three-failure isolation and read-only maintenance wrapper are bounded local work. A broad cleanup of 4,000+ working files, cross-repository M3/M4 implementation and migration of real history is `EXPENSIVE` under `AGENTS.md`; the owner explicitly approved M3/M4 implementation, tests and commit/push. Mass deletion and bulk history migration remain excluded. Keep this gate separate from ordinary commit/push authorization.

## RAG participation and business coordination

Cortex reuses its existing tenant-scoped `tfidf-lite` retrieval over admitted process outcomes. Deterministic analysis returns grounded measurement gaps without an LLM call. Optional explicit local Ollama inference can turn complete retrieved evidence into a cited trial suggestion; model weights are not trained by ingestion. Empty or insufficient evidence cannot establish an efficiency gain. OS independently checks provenance, source batches, current workflow version and the no-execution boundary on return.

Cortex ABV also coordinates the business direction of 1D3X Cortex. Index's existing agent-flow, artifact and runtime-service contracts were inspected. Business runtime supervision is a separate next milestone: approved read-only evaluation summaries, dedicated business tenant and reviewed policy candidates. This pass does not change Index/MN7R/Cropto deployments, customer data or runtime authority, and OS history is not mixed with business history.

## Next operational acceptance

Use the new loop after real publishing, research and production operations by recording reviewed outcomes. Start with one workflow and comparable workload identifiers. Retain five baseline and five disjoint approved-trial observations; known owner effort and preserved quality/safety gates are mandatory. Reject ineffective suggestions and retain the negative evidence. Do not transfer all history or remove code on the basis of an LLM suggestion.

## Verified pilot and model limits

Two actual read-only maintenance checks were recorded and admitted idempotently. Cortex retrieved the selected workflow and returned a cited `INSUFFICIENT_METRICS` diagnosis for unknown owner effort; OS independently recomputed it from its original source batch and returned `NEEDS_MEASUREMENT`. No missing value was replaced by zero and no optimization was applied. This is a real data-quality contribution before expensive inference. Installed Ollama analysis is optional; the initial local inference attempts were blocked by sandbox loopback access; an authorized synthetic probe then timed out, so real grounded model output and measured gains remain unverified. Synthetic adapter/evaluator tests do not establish operational efficacy.

The proposed Phocinae tiny classifier is documented as a candidate only in `PHOCINAE_ROUTER_QUALIFICATION_V1.md`: no installation or activation in this pass. Existing deterministic checks precede any future model route.
