# Book and business Cortex exchange rules v1

Status: PREPARED_NOT_ACTIVATED. Cost class: NORMAL. Prepare rules now; widen operational participation only after the first real native-publication cycle is verified. Existing book-quality and process-learning capabilities are reused. No new runtime, model, scheduler, producer, project fetch or deployment is introduced.

## Ownership and activation gates

OS owns book process state, proof and decisions. Cortex ABV is independent and owns private admission/retrieval; 1D3X Cortex remains the business/domain intelligence of Index, MN7R and Cropto. Each business project owns visibility, evaluation and deployment. ABV's coordination does not grant execution authority.

| Milestone | Required evidence | State |
| --- | --- | --- |
| Prepared rules | Versioned rules and synthetic boundary checks | This release |
| First cycle verified | OBSERVED site.content.publish/publication-v1 outcome; approved source and complete checks; deployed merge SHA and matching production page; admission, scoped context and independently validated OS return | Required before expanding participation |
| Book phase pilot | One reviewed phase of one book/research task; original gate proof, numeric observation and grounded OS return | Next; explicit capture |
| Business shadow pilot | One source-owned redacted project summary; separate tenant/project scope, admission/retention and wrong-project tests, cited read-only candidate | Receiver/tenant not implemented or admitted |
| Measured simplification | Five baseline and five disjoint held-out comparable runs; known owner effort, preserved quality/safety, lower median duration and no increased effort/rework | Later; one successful cycle is not proof |

Maintenance observations, test fixtures, previews and handoff packets do not satisfy the first-publication gate. The first cycle may report UNKNOWN owner effort honestly; that validates transport but cannot establish savings. Run `publication verify-first-cycle --item <id> --site-root <clean-checked-site> --cortex-root <private-cortex>` after native closeout and scoped return. It records ignored `.tmp/publication-learning/<id>/first-cycle.json`, binding the exact outcome, source packet, context and independently revalidated OS review to the latest successful GitHub Production deployment, its exact site PR merge SHA, a clean checked checkout and freshly verified public prose. Deployment/merge metadata is queried read-only from GitHub; a rollout change during verification is rejected. `publication complete` alone cannot satisfy this gate. The receipt is a point-in-time GitHub deployment/source/content verification, not perpetual domain-alias or search-indexing proof, and enables no participant automatically. Synthetic tests remain separate from operational history.

## Book results: existing contract

Use `AbvxOsProcessOutcome` v1 and the existing protected `abvx_os_process_outcomes` envelope (`abvx-os`, private_context, returnAuthority none). Use `book.radar.research` for reviewed niche/market evidence and `book.production` for source-rights, editorial, format, publication-package or retailer-verification phases. Select one actual phase; do not silently summarize every book or export the entire archive.

Record opaque run ID, UTC start/end and actual duration; active owner minutes or UNKNOWN; actual corrections; PASS/FAIL/CANCELLED; independent quality/safety gates; opaque proof refs and hashes. Keep manuscript text, titles, customer/market details, prompts, raw logs and paths local. Do not turn missing evaluation into zero/PASS. Technical format success is distinct from editorial quality, rights, commercial qualification, external preview approval and retailer availability.

Keep phases in separate workflow-version cohorts (e.g. book-production-editorial-v1 versus book-production-format-v1). A procedure change changes its version. Require a stage:<controlled_phase> proof hash and a workload:book-phase-profile hash. Retain the profile locally: phase, format/language/size band, required checks and rights class, without titles or private text. Different profile hashes or phases cannot share an efficiency comparison.

After the first-cycle acceptance, use OS `learning export --profile book-phase-v1` -> independent Cortex `os:receive` -> OS `learning inspect-candidate`. The export profile rejects more than 20 outcomes, mixed workflows/versions, missing or foreign phase gates and different workload-profile hashes before writing a packet. Book rows select this guard even if the flag is omitted. The generic in-memory `build_packet`/`validate_packet` contract still allows up to 100 rows for backwards compatibility; it is not the book-export guard. Cortex operator receive separately rejects more than 20 rows or mixed workflows/versions and admits only OBSERVED outcomes. Explicitly select the original packets cited by the context; no direct ledger writes or broad-history scan. Keep real records/proof in OS .tmp/ and private Cortex data/abvx-os/. OS retrieval retention is 90 days; expiry excludes retrieval, deletion remains explicit. Failure/UNKNOWN history is retained as negative evidence and excluded from successful optimization cohorts.

`publication complete` belongs to native site content and is not a book closeout. An automatic book-phase producer is a later adapter; the recovered broad book PR remains subject to its own review. Existing manual numeric contracts do not mean the book workflow is already automatically participating.

## Business supervision: reserved contract

The detailed receiving-side plan lives in independent Cortex `docs/BOOKS_BUSINESS_EXCHANGE_PREPARATION_V1.md` and `config/learning-extension-plan.v1.json`. Its proposed source is base_cortex/base-cortex, dataKind cortex_business_evaluation_summary, reserved tenant business-cortex-supervision. That dataKind is not currently allowlisted and the tenant is not registered. Do not label it as a workforce packet, OS outcome or personal-memory import.

Proposed summaries contain only one project (index, mn7r or cropto), opaque run/runtime-version IDs, actual UTC observation period, availability and separate artifact gate, numeric/UNKNOWN evaluation counts and measured latency, plus opaque proof hashes. The project must provide a reviewed redaction receipt and source artifact/evaluation digest. Health is not semantic quality. Unknown or unavailable facts remain UNKNOWN; small aggregates require source-owner visibility review.

Before any real business handoff, implement strict payload and cross-field validation, a project-owned exporter, whole-payload hashing/idempotency, dedicated protected admission and isolated tenant/project/version retrieval. Proposed retention is 14 days; validate expiry and deletion behavior explicitly. Bound packets to 32 KiB and at most 20 evidence items. No manifests/chunks, customer/deal records, quotes, endpoints, credentials, paths or model prompts/responses are transferred.

Return only a project/version-bound, cited private review candidate: readiness, artifact-coverage or evaluation-gap findings; authority none, executionAuthorized false. Project owners independently verify provenance and choose any change. ABV cannot deploy, publish/promote manifests, trade, delete records or alter permissions/policy through this return. OS and business history never share retrieval; a general-method transfer needs a separate reviewed redacted artifact.

## Fallback and scope

If Cortex is unavailable or a return fails validation, retain local immutable outcome/proof, mark transfer/review pending and continue under the project's own approval gates. Retry the selected handoff only. A future pilot rollback disables its adapter/adoption, preserves evidence and never deletes project content or data.

OS verification covers its book outcome/privacy/UNKNOWN boundaries, guarded book export and first-cycle deployment binding. It rejects business/foreign-tenant data inside an OS envelope; that local rejection does not prove receiving-side admission. Independent Cortex tests check the actual admission allowlist and tenant registry, and invoke its operator CLI against isolated temporary copies to verify oversized/mixed handoff rejection before writes. A future business receiver still needs its own tests and contract. It does not prove a real book pilot, business receiver, model training, measured gain or permission to widen authority. Read-only source review used the existing Index agent-flow, artifact-pipeline and runtime-service contracts; no sibling business source or deployment changed.
