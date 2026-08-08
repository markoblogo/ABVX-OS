# ABVX-OS

ABVX-OS is the local-first Personal Operating System / Personal Operator layer for independently deployable projects, opportunity intake, portfolio state, Cortex-backed context retrieval, donor qualification, and bounded operational execution.

## Operating principles

- Projects remain deployable and useful when ABVX-OS is unavailable.
- Evidence, provenance, and explicit ownership come before automation.
- Reuse internal capabilities and qualify external capabilities before building.
- Check donor options and prefer thin wrappers/configuration before custom subsystems.
- Treat token/model capacity as a constrained portfolio resource, not an unlimited platform budget.
- Prefer a small modular monolith and local state until scale proves otherwise.
- Automation is bounded by source/action policy and human approval gates.
- Minimize dependencies, cost, secrets, and generated state.

## Current scope

Current implemented subsystems:

- Universal Intake: canonical local intake, clarification, human review, and idempotent promotion into small existing registries.
- Portfolio state: project strategy, operational state, human queue, and portfolio lessons.
- Cortex retrieval bridge: bounded `ContextRequest -> ContextPack` retrieval across ABVX operational state, CortexABV knowledge, and Index Cortex domain intelligence.
- Mission-state boundary: optional fail-closed long-running development mission state through the admitted LoopX provider boundary only.
- Playbooks: compact deterministic routines for proven repeated operations.
- Donor-first policy: candidate registry, capability gaps, and cost/approval guardrails for future platform work.
- Evidence model: machine-readable decisions, audits, bakeoffs, project onboarding evidence, and routine replay receipts.

Development Ops is only one subsystem inside this larger Personal Operator shape.

This repository does not provide a general workflow engine, sibling-project runtime dependency, autonomous router, production executor, or SaaS control plane.

## Read first

For a fresh coding session, use this order:

1. [AGENTS.md](AGENTS.md)
2. [README.md](README.md)
3. [ARCHITECTURE.md](ARCHITECTURE.md)
4. [docs/product-vision.md](docs/product-vision.md)
5. [docs/donor-first-policy.md](docs/donor-first-policy.md)

Then load only task-specific docs such as [docs/context-retrieval.md](docs/context-retrieval.md), [docs/intake.md](docs/intake.md), [docs/provider-contract.md](docs/provider-contract.md), or [docs/roadmap.md](docs/roadmap.md).

## Future scope

Future work may add an event intake and routing implementation, local stores, provider adapters, project intelligence, mission state, and carefully approved integrations. Those decisions remain intentionally open, must be supported by experiments and evidence, and should prefer donor reuse before new custom builds.

Current direction of travel is:

- finish documentation sanitation and cheap context maintenance;
- keep Cortex consumer integrations bounded and evidence-backed;
- move next toward Opportunity Engine, Media Resource, and revenue/experiment loops only when concrete triggers justify them.
