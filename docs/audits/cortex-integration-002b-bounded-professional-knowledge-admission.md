# CORTEX-INTEGRATION-002B

Date: 2026-08-08

Scope: admit the minimum durable professional knowledge needed to make CortexABV useful for bounded CoqPi opportunity preparation.

## Admission mechanism

Canonical owner facts were admitted only through the existing CortexABV tenant memory bank path:

- source scope: `personal_knowledge_core` / `personal-core`
- bank: `personal-owner-facts`
- memory class: `owner_fact`
- retention: `personal_standard`
- promotion policy: `personal_public_limited`
- retrieval mode: scoped token overlap, claim evidence required, cross-tenant deny

No direct write-around store was introduced.
No new Cortex memory architecture was introduced.

## Facts admitted

Admitted from owner-approved canonical facts:

- current opportunity goals
- current interest areas
- acceptable collaboration models
- written-vs-live communication preference for preparation
- opportunity-preparation constraints favoring recent proof and advance context

Each admitted fact now carries:

- provenance via claim evidence
- privacy classification
- canonical owner
- canonical source
- admitted timestamp
- reviewability metadata

## Privacy split

`PUBLIC_SAFE`

- current opportunity goals
- current interest areas
- acceptable collaboration models

`PERSONAL_PRIVATE`

- written communication currently easier than spontaneous live communication
- CoqPi as support for live-call friction reduction
- preparation constraints/preferences for advance context and recent-proof emphasis

`NEEDS_REVIEW`

- supported by schema, not used in the current admitted set

## Retrieval impact

Compared with `002A`, the CoqPi preparation packs now include admitted current goals/collaboration and, for private requests, preparation constraints.

`PUBLIC` projection no longer fails closed at the provider boundary; it now returns only public professional surfaces plus `PUBLIC_SAFE` admitted facts.

## Intentionally not admitted

- education/certificates without audited evidence
- one-off recruiter or role details
- temporary company research
- call notes
- broad historical biography/CV material

## Remaining gaps

- education/certificates still missing from audited evidence
- recent-work proof remains partly public-surface bounded
- small packs remain budget-truncated by design

## Readiness

CortexABV is now materially more useful for `COQPI-003` style preparation.

It is not a full professional profile system and should still be treated as a bounded preparation source with explicit gaps.
