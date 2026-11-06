# ABVX Book Core Architecture V1

Status: READY FOR REVIEW, design only. Decision: **B, implemented as a thin hybrid** — generalize the existing GD3 mechanics into a universal core; GD3 becomes its first consumer. Preserve its state/history and working CLI until compatibility is proved. Do not discard the foundation or build a parallel universal workflow engine.

## Twelve core capabilities

| ID | Capability | Reuse / boundary |
|---|---|---|
| C1 | IDENTITY | Stable book ID, source type/refs, languages, optional ordered series, initial rights/target policy; title may be UNKNOWN. Shared across all inspected cases. |
| C2 | STATE | Current stage/gate, applicability, blockers, canonical pointers; status is a generated view, not prose authority. GD3 is the starting implementation. |
| C3 | EVENTS | Append-only decisions/observations/transitions, replayable state, expected revision and evidence. No automatic owner impersonation. |
| C4 | LOCKS | Immutable accepted inputs, conditional source/canon/translation/text/art/build locks; successor/supersedes chain. |
| C5 | PROVENANCE | Byte refs, transformation params, accepted AI outputs, dependencies and STALE propagation; no duplicated storage. |
| C6 | VALIDATION | Five-state results, issue lifecycle, exact inputs/outputs/proof and required checks; semantic validation remains modular. |
| C7 | BUILD_MANIFEST | Versioned deterministic fingerprint, execution attempts, tools/config/command/output evidence; renderer adapters own build work. |
| C8 | FORMAT_TARGETS | Target configs/applicability, Contents requirements and adapter versions; no universal renderer. |
| C9 | METADATA | Surface-specific credits, rights/AI disclosure decisions, cover/pricing completeness and inherited authority; retailer-specific field mapping stays outside. |
| C10 | RETAILER_STATE | Independent per-target observed/authorized states and external constraints; upload identity and LIVE evidence separate. |
| C11 | METRICS | Prospective stage/attention/cost/rework/defect measurements and budget reservations, unknown preserved. |
| C12 | LEARNING | Promotion index into existing learning register, implementation/coverage status, regression destination, Radar handoff. |

Top ten implementation priorities: C1 identity; C2 state; C3 events/owner records; C4 conditional locks; C5 dependency/staleness; C6 evidence-bound validators/issues; C7 build manifests; C8 target/Contents policies; C9 inherited metadata/rights; C11 prospective metrics/cost caps. C10's submission/retailer checks must nevertheless be enforced before any release; C12 measurement hooks start early rather than requiring late historical reconstruction.

## Storage and source of truth

Future new-book folder: `identity.json` optional initial view, `state.json`, `events.jsonl`, `issues.jsonl`, `builds/<fingerprint>/<attempt>/manifest.json`. Identity lives once in canonical state; a start manifest can use the schema's identity definition and later become the same identity, not competing authority. Generated reports are disposable views. Module configuration, templates and references are reused by path/hash; no copies of locked books or generic chat dumps.

The state schema in this package is a versioned design contract. It is not installed in runtime validation or registries. Required envelope fields are small; optional stage lanes exist only if applicable. Namespaced `extensions` require a module schema when activated; an opaque extension cannot establish QA PASS. No secrets, arbitrary external commands or cloud dependency in state.

Canonical events: OWNER_DECISION, STAGE_STARTED, STAGE_COMPLETED, LOCK_CREATED, VALIDATION_PASS, VALIDATION_FAIL, BUILD_CREATED, ASSET_APPROVED, RETAILER_WARNING, RETAILER_PREVIEW_PASS, SUBMITTED, STATUS_OBSERVED, LIVE_OBSERVED, PROCESS_LEARNING. A provider error is a failed run/result event, not implicit authority to spend/retry.

Future transaction: single-writer/exclusive lock → validate expected revision/evidence/allowed transition → append event with prior event hash and post-state hash → fsync → atomically replace state projection. Crash after ledger append: replay committed events; crash before append: no transition. Read-only status reports mismatch; it never silently repairs the cache. Initial event has null predecessor. Duplicate IDs, broken chain, wrong book, invalid timestamps, revision gaps or changed proof fail closed. Owner evidence must be authenticated by the trusted workflow; an `actor: OWNER` string is not authentication. Exact reducer/JSON Pointer rules are implementation acceptance work, not claimed implemented here.

## Locks and STALE dependency graph

Lock lanes are conditional: SOURCE_LOCK for imported witnesses; CANON_LOCK for series/world policy; TRANSLATION_LOCK for accepted aligned translation; TEXT_LOCK for final reader text; ILLUSTRATION_LOCK where assets exist; RENDER_INPUT_LOCK for synchronized Latin/glyph inputs; PRODUCTION_BUILD_LOCK per approved output. Absence is NOT_APPLICABLE only with an applicability policy, otherwise UNKNOWN/unstarted.

Every artifact/lock node records exact refs plus dependency IDs/hashes. DAG must reject cycles/missing dependencies. Changed upstream bytes or config/tool/module version mark dependent nodes STALE transitively, including QA, cover-wrap geometry, metadata packaging and retailer release-candidate linkage. Old published records retain the hashes they observed; they do not become evidence for a new build.

Selective repair: changed dialogue span invalidates its affected comic/script/Composer approval and downstream build if exact dependencies exist. If scope is uncertain, invalidate the whole related asset manifest conservatively. A metadata-only correction need not alter text/art; a placement-only correction invalidates that PDF's geometry/parity/build QA, not the Kindle DOCX. Source block changes invalidate block + dependent context/semantic QA. Never silently relabel an old lock CURRENT. Locked bytes are never edited; accept a new successor under the relevant owner authority.

Fingerprint: sorted canonical UTF-8 JSON of book ID, target ID, ordered lock/asset refs, full config, template/adapter/tool/module versions and environment reference. Exclude observation timestamps/output paths. Build ID is full SHA-256; attempt ID is separate. Record command as argv (no shell interpolation), input/config/tool hashes, outputs, deterministic claim and reproducibility limits. Existing attempts cannot be overwritten. Same fingerprint with differing deterministic outputs is a discrepancy requiring diagnosis, not silent cache reuse. AI generation is not deterministic; accepted output hash is deterministic downstream input.

Deprecation is explicit: SUPERSEDED/HISTORICAL_WORKAROUND inputs and routes remain inspectable but cannot be selected as current production policy. Selection requires a current replacement ref or a scoped owner exception; no deletion of the old EPUB/KPF route or silent promotion of a temporary Jekyll workaround.

## Validator / issue / decision contracts

States: PASS, FAIL, UNKNOWN, NOT_APPLICABLE, OWNER_ACCEPTED_EXCEPTION. PASS needs input/output hashes and immutable local proof. No proof → UNKNOWN/FAIL, never PASS. N/A needs an explicit reason/policy. Exceptions need scoped owner proof and accepted risk; they are not PASS or reusable defaults. Validator records include version/tool, observed/expected, time and target; stale proof does not clear current checks. JSON Schema covers record shape; code must verify refs, hash equality, applicability, DAG, temporal/transition rules and numeric finiteness.

Issue statuses: OPEN, BOUNDED_REPAIR, RESOLVED, OWNER_ACCEPTED, WONT_FIX, SUPERSEDED. Include severity/location/source span, missing function or factual defect, introduced/detected layers, evidence, repair scope, regression and resolution authority. A genuinely creative issue can carry prose without pretending it is machine-proven. One issue ledger replaces repeated status narratives, not useful editorial analysis.

Decision packets batch related choices: concept/architecture; editorial/lock; illustration program + per-comic Composer; commercial/cover; final per-format release. Never merge technical self-check with semantic/visual/commercial/release approval. Pin inherited defaults with value, source ref, authority, scope and override evidence. Re-ask only conflict/deviation/expired external policy, not each title's unmodified defaults.

Eight owner actions removable within authorized scope: manual hash comparison; chapter/count/empty/duplicate checking; finding the current canonical file; re-entering inherited print/series defaults; manually noticing missing/stale Contents; first discovering measurable safe-area errors; retyping/conflating author surfaces; selecting valid cached/pending translation IDs within already approved budget. Do not remove owner release authority, spending ceiling, source ambiguity, native translation judgment, story decisions, final editorial lock, visual approval, Pictiq Composer meaning, rights/disclosure attestations, price/cover decisions or retailer submission authorization.

## Production/format contract

VISIBLE_CONTENTS, CONTENTS_PARITY and DIGITAL_NAVIGATION are independent target checks. Default visible Contents required follows `docs/book-production-policy.md`. Waiver is title-specific owner evidence, not silent module configuration. Print parity uses final printed labels + actual destination pages; reflowable parity uses heading/anchor coverage without print-page numbers. Bookmarks alone cannot satisfy visible Contents. Kindle conversion/device navigation is separate from DOCX source navigation. Existing `release_authorization` accepts HUMAN_PENDING preview while naming output KDP_READY: adapt that to LOCAL_READY_FOR_PREVIEW, never authorized submission.

Image envelope: original bytes/hash/rights/origin/owner approval → optional deterministic derivative/hash/full transformation params → target placement + extracted output image identity + effective DPI + safe rectangle/clearance. Same source can feed Kindle original and print derivative. PDF adapters inventory all text/images/vector decorations/footers through actual CTMs; generator-declared boxes alone cannot claim full extraction. Standard envelope uses points, bottom-left origin, xyxy bounds with page rotation/crop transform recorded. Convert existing GD3 xywh explicitly. Safe-area policy is retailer/version/config data; do not bake current KDP measurements into timeless core.

Use existing ReportLab/DOCX/TeX/LibreOffice export paths via thin adapters. Independent PDF gates: fonts, annotations, qpdf/structure, page size/count, narrative parity (documented normalization only), art hashes/DPI/bounds, visible Contents/parity, representative/full render cost and visual proof. Subset embedding is valid; full embedding is not universally required. Do not rasterize body text or use generative art repair. Pictiq semantic/source/Composer chain belongs to its optional language module, not pixel infrastructure. Rendered glyph/continuation fidelity belongs to TP/sitelen adapter.

Templates: versioned title/copyright/translation note/visible Contents/glossary/name guide/chapter opener/series/reader-kit and metadata mapping. Selected templates and parameter hashes enter builds. They carry layout structure, not generic replacement prose/blurb or a fixed art count.

## Retailer, constraints and post-publication

Per target: LOCAL_QA_PASS → RETAILER_PREVIEW_PENDING → RETAILER_PREVIEW_PASS → SUBMISSION_AUTHORIZED → SUBMITTED → IN_REVIEW/PUBLISHING → LIVE. HOLD/REJECTED may interrupt. Normal readiness transitions need current proofs/owner authority. Independently observed historical LIVE may be recorded without reconstructing missing submission hashes; use observation events, retain UNKNOWN upload provenance, never invent a passed preview.

External constraints (e.g. KDP_TITLE_CREATION_LIMIT) block affected operations without erasing local QA. Record observed time, scope, evidence, estimated reset if known; passage of time alone does not clear it. KDP adapter owns ASIN/ISBN/Select/marketplaces/disclosure fields, Previewers and processed-page-count template. Core owns evidence, state and authority. Local page count is not KDP template approval. No external write is scheduled by this design.

On evidenced LIVE, hand off a local observation packet to existing Book Radar: identifiers, market, observed price, first Live observation, exact-upload provenance separately, rights to collect metrics and desired D+1/7/14/30 windows. Unknown true release date means windows are observation-relative and labelled. Actual retailer availability/indexing/sales/KENP/royalties/ranks/reviews remain UNKNOWN until sourced. Do not mutate Radar scores or diagnose demand from zero sales without visibility evidence.

## Cost, continuous review and measurement

Tier 0 deterministic; Tier 1 cheap bounded language/risk triage; Tier 2 strong-model ambiguity; Tier 3 expensive unresolved high-value review; human adjudicates meaning/rights/creative decisions. No hardcoded model prices: pin an approved provider/model policy and dated price evidence. The inspected registries did not expose a unified book model-price registry; Jekyll currently pins model/config in its runner. Reuse existing provider/broker boundaries, then add only the thin versioned policy ref needed by a future authorized API task. Missing model policy is a planning blocker, not permission to invent rates. Broker credential boundary stays unchanged; no raw error bodies/secrets in state or logs.

Each AI task declares purpose, context refs/scope, estimate input/output, maximum spend/calls, tier, fallback/retry/cache policy, QA required. Reserve conservative worst-case call cost before dispatch, bounded output and retry reservation; reconcile retained usage afterward. Unknown available balance is explicit, not zero or assumed funded. Stop before unreserved work, persistent auth/quota/model/unknown429, or ceiling exhaustion; explicit owner override required to extend. Prior Jekyll token caps check after response and may overshoot one call; do not label that a strict spend reservation.

Cache key: source bytes/block ID and normalization version + selected adjacent/global context hashes + language/module/Bible/name/knowledge policy versions + model/provider/config + prompt version/hash + QA policy. Output hash and accepted QA must verify. Provider prefix caching is separate from local output reuse: unchanged approved blocks reuse without a call; cached-input savings require observed usage. Historical Jekyll 351/111 was safely resumed unchanged; do not retroactively mix prompts or resegment it.

Continuous novel reading is required after substantial development/compression and final translation assembly before lock, not replaced by block QA. Bounded repairs with proven scope rerun local and boundary checks; uncertain scope escalates. Full rereads are not automatic for punctuation fixes, and short chapters do not trigger expansion.

Prospective scorecard dimensions: calendar speed, owner attention, model/tool cost, rework, escaped defects/quality. Stage start/end and requested/approved timestamps support calendar duration/wait; owner minutes only if measured. Record stage agent runs, revisions, generation attempts, QA runs/failures, API usage/cost, build/preview/submission attempts, introduced/detected defect layer. Null remains unknown; cost estimate is distinct from invoice; reasoning tokens are not double-counted where included in output. No arbitrary quality aggregate or reconstructed historical savings.

Learning promotions must name validator/test/default/tool change/accepted exception or reason for non-action. Implementation status requires actual code/test/default evidence and consumer coverage. Existing append-only record IDs remain authority; the new registry indexes proposed promotions. A recurring defect opens the question: was the rule documentation-only, unbound to current output, optional, duplicated, not persisted, or missing extraction coverage?
