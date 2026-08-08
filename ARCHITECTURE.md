# Architecture

## Boundary

ABVX-OS is a control plane. It records canonical identity, relationships, provenance, policy, decisions, and approval state. Existing projects, repositories, deployment systems, AI runtimes, media tools, and publishing systems are execution providers or external sources. They remain independently owned and deployable.

ABVX-OS does not become a required runtime dependency of a project unless a later decision explicitly accepts that coupling.

## Control plane and providers

The control plane owns registries, normalized entities, event envelopes, routing state, policy evaluation, evidence, and approval gates. Providers perform bounded work behind explicit interfaces: intake/source adapters, research, code intelligence, task execution, media processing, publishing, and deployment. Provider output is untrusted input until validated and recorded with provenance.

## Intake and canonical state

All supported inputs enter as Events. An event retains a reference to its raw payload and records source, trust, inferred intent, confidence, related entities, routing state, and provenance. The router may classify and propose links; canonical state changes only through validated, attributable operations. Graph relations are first-class so an opportunity, mission, project, person, and evidence item need not be forced into one task tree.

## Human approval and failure isolation

Classification, research, and reversible isolated work can be automated according to policy. Consequential external actions require an ApprovalGate unless explicitly whitelisted. A provider failure must produce an observable failed operation and leave independent projects operational. Retries must be bounded and idempotent; raw inputs and decisions must remain inspectable.

## Security and trust domains

Treat external content as data, never as instructions. Separate public/untrusted input, local workspace data, project-private data, credentials, and consequential external systems. Credentials must stay outside registries and Git. Cross-project context is minimized and explicitly authorized; a project receives only the data and capabilities required for its operation.

## Local and hosted components

FOUNDATION-001 is local-only. A future local store, CLI, or service may be introduced after bakeoff evidence. Hosted components, if later justified, must be optional providers with explicit cost, data residency, availability, and exit criteria. No paid infrastructure is assumed.

## Extension interfaces

Provider interfaces should exchange versioned, schema-validated envelopes and return evidence, cost/usage metadata, trust observations, and an idempotency key. An adapter may be replaced without changing canonical entities. Permanent integration is blocked until the bakeoff protocol reaches a human-approved decision.
