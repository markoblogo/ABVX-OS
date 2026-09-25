# Read-only context retrieval

Canonical ownership stays split:

- `ABVX-OS` owns operational truth and current mission/project state.
- `CortexABV` owns personal, cross-project and durable project knowledge.
- `Index Cortex` owns index/domain/methodology intelligence.

`CORTEX-INTEGRATION-002` adds a read-only bridge only.

Flow:

`ContextRequest` → explicit provider routing → normalized `ContextPack` → future consumer

Current local interface:

- `./bin/abvx context request --file <request.json> --json`
- `./bin/abvx context inspect <pack-id>`

Provider boundary:

- `capabilities()`
- `health()`
- `retrieve(ContextRequest) -> ProviderContextResult`

The bridge is intentionally bounded:

- no write-back into Cortex
- no consumer-specific coupling to Cortex storage formats
- no automatic consumer integration
- no secrets in packs
- privacy domain must be declared on the request
- retrieval stays budgeted with `max_items` and excerpt limits

Operational context inside a pack must stay visibly separate from retrieved knowledge items.

Expected future consumers:

- `CoqPi`: preparation/context packs for bounded conversation prep
- `AzurMenton`: internal editorial/project context lookup
- `ABVX.xyz`: cross-project/profile context assembly
- `Media Resource`: proof/project context lookup
- `Opportunity Engine`: bounded profile/project/domain retrieval

If a provider is unavailable, denied, malformed, or truncated, that must remain explicit in the `ContextPack` and evidence.

## Owner-governed memory corrections

`abvx_harness.memory_decisions` provides a local, append-only decision overlay for retrieved items. It supports `INVALIDATE` for a confirmed incorrect item and `RESOLVE_CONFLICT` when an owner explicitly selects one item from a set of competing provider/ID references. Every record requires a privacy domain, rationale, and provenance and conforms to `schemas/memory-decision.schema.json`.

Record a reviewed decision from a JSON file with `./bin/abvx memory decision record --file <decision.json>`. The input fields are the schema fields excluding generated `schema_version` and `write_back`; `action`, `target_refs`, `privacy_domain`, `rationale`, and `provenance` are required, while `chosen_ref`, `decision_id`, and `decided_at` are optional. Conflict resolution requires `chosen_ref` to exactly match one of `target_refs`.

Decisions are stored under `evidence/memory-decisions/` and are applied only to ContextPacks in the same privacy domain. Invalidated or non-selected items are omitted from the local pack; applicable decisions remain visible in `relevant_decisions` and a known-gap note explains the filtering. Provider data is never edited, deleted, or written back to Cortex. The overlay is not a second canonical memory: it records owner decisions about specific source references and can be revised only by another explicit, provenance-bearing decision in a future contract revision.

Unknown provider/ID references are retained as decisions but have no retrieval effect until that exact reference appears. No semantic matching, automatic conflict detection, or automatic choice is performed.

For professional preparation requests, `CortexABV` may synthesize a bounded pack from audited public Cortex surfaces such as:

- `public-presence-index.v1.json`
- `public-project-registry.v1.json`
- the audited local runtime artifact/query seam where relevant
- admitted personal professional facts retained through the audited tenant memory bank receipt

That path is still read-only and evidence-backed. It should return compact opportunity-specific context, not a full biography dump.

`PUBLIC` requests may receive only:

- public Cortex professional surfaces;
- admitted owner facts explicitly classified `PUBLIC_SAFE`.

`PUBLIC` requests must not receive:

- `PERSONAL_PRIVATE` communication or preparation preferences;
- ABVX operational state;
- private runtime-only facts lacking public-safe classification.
