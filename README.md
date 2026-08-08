# ABVX-OS

ABVX-OS is the planned local-first control and integration layer for independently deployable projects, AI-assisted workflows, media and revenue assets, and a personal operational assistant.

## Operating principles

- Projects remain deployable and useful when ABVX-OS is unavailable.
- Evidence, provenance, and explicit ownership come before automation.
- Reuse internal capabilities and qualify external capabilities before building.
- Check donor options and prefer thin wrappers/configuration before custom subsystems.
- Treat token/model capacity as a constrained portfolio resource, not an unlimited platform budget.
- Prefer a small modular monolith and local state until scale proves otherwise.
- Automation is bounded by source/action policy and human approval gates.
- Minimize dependencies, cost, secrets, and generated state.

## Current scope: PLATFORM-REBASE-001

This repository defines the FOUNDATION-001 architecture, the FOUNDATION-002 local bakeoff harness, the FOUNDATION-003A conditional mission-state provider boundary, FOUNDATION-004’s development-harness efficiency fixtures/evidence, PLATFORM-INTAKE-002’s human decision and idempotent promotion loop, and PLATFORM-REBASE-001’s donor-first and cost-policy guardrails. LoopX remains isolated behind a normalized, fail-closed interface; intake remains local and human-triggered; platform work is now explicitly donor-first and cost-aware. It contains no sibling-project integration, production writes, paid infrastructure, Telegram/mobile/web integration, autonomous router, or general workflow engine.

## Future scope

Future work may add an event intake and routing implementation, local stores, provider adapters, project intelligence, mission state, and carefully approved integrations. Those decisions remain intentionally open, must be supported by experiments and evidence, and should prefer donor reuse before new custom builds.

Start with [ARCHITECTURE.md](ARCHITECTURE.md), [docs/product-vision.md](docs/product-vision.md), [docs/donor-first-policy.md](docs/donor-first-policy.md), then [docs/harness.md](docs/harness.md) and [docs/roadmap.md](docs/roadmap.md).
