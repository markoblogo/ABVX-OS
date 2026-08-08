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

For professional preparation requests, `CortexABV` may synthesize a bounded pack from audited public Cortex surfaces such as:

- `public-presence-index.v1.json`
- `public-project-registry.v1.json`
- the audited local runtime artifact/query seam where relevant

That path is still read-only and evidence-backed. It should return compact opportunity-specific context, not a full biography dump.
