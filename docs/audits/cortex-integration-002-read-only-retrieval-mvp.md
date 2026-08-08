# CORTEX-INTEGRATION-002

Date: 2026-08-08

Scope: ABVX-only implementation of a read-only `ContextRequest` → `ContextPack` bridge over already audited `CortexABV` and `Index Cortex` retrieval surfaces.

Observed repositories:

- `ABVX-OS`: working tree changes only for this mission
- `ABVXsite/cortex-abv`: read-only use of `private-runtime` query harness at `fcafd0c89b87ba71956c6d68c8205e518d9eeae8`
- `CortexABV-private`: read-only reference only at `59909c4a23af4fed20976a16e6ac01f76659e6fe`
- `index`: read-only use of bounded context-pack path at `a97d452bca65946d3fe649d6e38a2b2f00cc4385`

Read-only repo status after checks:

- `ABVXsite`: unchanged relative to pre-existing state; still has pre-existing untracked `cortex-abv/author_os/governance/proposals/` and `.../reviews/`
- `CortexABV-private`: unchanged
- `index`: unchanged

## Delivered boundary

ABVX now has a local-only read-only context bridge:

- request contract: `schemas/context_request.schema.json`
- pack contract: `schemas/context_pack.schema.json`
- provider interface and adapters: `src/abvx_harness/context.py`
- CLI: `./bin/abvx context request`, `./bin/abvx context inspect`

The bridge does not merge storage or canonical ownership:

- `ABVX-OS` contributes only compact operational context
- `CortexABV` contributes personal/project/proof knowledge when present
- `Index Cortex` contributes admitted domain/methodology knowledge when present

## Actual retrieval paths used

`CortexABV` adapter:

- runtime: `ABVXsite/cortex-abv/private-runtime`
- artifact: `data/vector-indexes/turbovec-poc/index-artifact.v1.json`
- query seam: `src/vector-runtime-controlled-module-harness.mjs`

`Index Cortex` adapter:

- command: `npm run cortex:context-pack -- --chunks=.cortex/chunk-manifest.json ...`
- source hygiene relies on the fail-closed admission work from `CORTEX-INTEGRATION-001A`

## Fixture outcomes

1. `coqpi-preparation`
   - provider: `cortexabv`
   - result: `CONDITIONAL_PASS`
   - useful context: minimal public-presence baseline plus current ABVX operational state
   - gap: no rich recent-work / professional-profile timeline yet

2. `azurmenton-editorial`
   - provider: `cortexabv`
   - result: `CONDITIONAL_PASS`
   - useful context: compact AzurMenton guide bundle plus current ABVX operational state
   - gap: durable decisions and richer editorial history are still absent

3. `index-pop-methodology`
   - provider: `index-cortex`
   - result: `CONDITIONAL_PASS`
   - useful context: admitted methodology/domain item from Index Cortex
   - gap: bounded retrieval omitted additional matches; no ABVX operational state existed for that request

4. `unusual-indices-book`
   - providers: `cortexabv`, `index-cortex`
   - result: `CONDITIONAL_PASS`
   - useful context: mixed-provider pack with personal/profile context, index-spike context, and Index methodology context
   - gap: personal retrieval is still shallow and Index results remain budget-truncated

## Security and privacy behavior

- request privacy domain is mandatory
- `PUBLIC` request to `CortexABV` is denied
- `EXTERNAL_UNTRUSTED` request to `Index Cortex` is denied
- provider-specific privacy classifications remain attached to each item/source
- no secrets are included in packs
- operational state stays separated from retrieved knowledge

## Failure behavior

- unavailable provider → explicit provider status `unavailable`
- malformed provider result → explicit provider status `malformed`
- denied retrieval → explicit provider status `denied`
- no matches → explicit provider status `gap`
- budget overflow → `truncated: true`, `available_more: true`
- non-admitted Index path → fail closed

The bridge does not silently upgrade partial retrieval into a full authoritative answer.

## Current limits

- `CortexABV` personal retrieval is real but still too thin for high-value preparation use
- `CortexABV` AzurMenton knowledge is present only as a compact bundle
- `Index Cortex` retrieval is bounded and can omit additional relevant matches
- relevant decisions are not yet hydrated into the pack; only projects, operational state, sources and knowledge items are currently normalized

## Operational conclusion

Read-only Cortex retrieval is now operational as an ABVX-local bounded bridge.

It is not yet a sufficient consumer-ready knowledge layer for higher-stakes preparation or richer editorial assistance without additional source depth in the upstream Cortex providers.
