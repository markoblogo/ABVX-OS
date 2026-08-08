# CORTEX-INTEGRATION-002A

Date: 2026-08-08

Scope: deepen personal/professional retrieval for opportunity-specific preparation without broad Cortex rewrite and without coupling consumers to Cortex internals.

## Existing professional knowledge inventory

Observed audited CortexABV public/runtime surfaces:

- `ABVXsite/cortex-abv/public-presence-index.v1.json`
- `ABVXsite/cortex-abv/public-project-registry.v1.json`
- `ABVXsite/cortex-abv/private-runtime/data/vector-indexes/turbovec-poc/index-artifact.v1.json`
- `ABVXsite/cortex-abv/private-runtime/src/vector-runtime-controlled-module-harness.mjs`

Inventory classification:

- current projects: `STRONG`
- recent work: `PARTIAL`
- professional roles: `PARTIAL`
- capabilities: `STRONG`
- public writing: `STRONG`
- books/publications: `STRONG`
- GitHub/public proof: `STRONG`
- education/certificates: `MISSING`
- professional goals/current collaboration preference: `MISSING`
- constraints/preferences: `MISSING`

What changed versus `002`:

- the old personal path only exposed a single runtime candidate: `Public presence baseline`
- the improved path reads audited public Cortex professional surfaces directly and synthesizes a bounded preparation pack

## Retrieval changes

Implemented inside `ABVX-OS` only:

- added public professional-surface loading and inventory classification
- added relevance scoring tuned for Product Lead / AI preparation
- added recency weighting and bounded diversity across projects/publications
- added proof-link extraction from public project registry and public links
- kept privacy fail-closed: `PUBLIC` still cannot receive private-only CortexABV retrieval

No Cortex memory write-back was added.
No CoqPi integration was added.
No broad Cortex knowledge rewrite was performed.

## Before / after CoqPi fixture

Before (`CORTEX-INTEGRATION-002`):

- items: `1`
- sources: `1`
- proof assets: `1`
- pack bytes: `4452`
- content: only `Public presence baseline`

After (`002A`, medium pack):

- items: `6`
- sources: `7`
- proof assets: `12`
- pack bytes: `14213`
- content:
  - `Current focus and strongest relevant work`
  - `Relevant capabilities`
  - `MN7R Product Guide`
  - `Decision Map`
  - `ABVX Agent Skills`
  - `Future-Proof Your Productivity`

Small pack:

- items: `4`
- sources: `5`
- proof assets: `7`
- pack bytes: `10350`
- content:
  - `Current focus and strongest relevant work`
  - `Relevant capabilities`
  - `MN7R Product Guide`
  - `Decision Map`

## Proof-linking behavior

Claims now map to concrete public evidence where available:

- capability cluster → project/publication entity
- project entity → GitHub or public site URL from project registry
- publication entity → canonical URL plus public PDF/EPUB/site links when present

This remains selective rather than exhaustive.

## Context budget behavior

- medium pack keeps six knowledge items and marks `available_more=true`
- small pack keeps four knowledge items and preserves proof-backed diversity
- truncation is explicit via provider result and pack constraints

## Privacy behavior

- request stays `PERSONAL_PRIVATE`
- underlying professional evidence may come from public Cortex surfaces
- pack remains private to the authorized consumer context
- `PUBLIC` requests are still denied from the CortexABV private retrieval path

## Remaining gaps

- no audited current collaboration/employment preference
- no education/certification record
- no audited professional constraints/preferences
- some very recent private project execution is still absent from public surfaces

## ABVX.xyz future readiness

Likely `PUBLIC_SAFE`:

- current public projects
- public books/publications
- public writing
- public GitHub/site proof links
- public capability clusters grounded in published work

`PRIVATE_ONLY`:

- opportunity-specific preparation framing
- consumer-specific pack selection
- private operational context

`NEEDS_REVIEW`:

- any future goals/current role preference
- any constraints/preferences once admitted
- any inferred synthesis that goes beyond public proof

## Operational conclusion

Professional retrieval is now materially stronger for `COQPI-003`-type preparation.

It is still incomplete where the upstream audited Cortex knowledge lacks explicit current goals/preferences and richer recent private execution summaries.
