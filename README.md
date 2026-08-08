# ABVX-OS

ABVX-OS is the planned local-first control and integration layer for independently deployable projects, AI-assisted workflows, media and revenue assets, and a personal operational assistant.

## Operating principles

- Projects remain deployable and useful when ABVX-OS is unavailable.
- Evidence, provenance, and explicit ownership come before automation.
- Reuse internal capabilities and qualify external capabilities before building.
- Prefer a small modular monolith and local state until scale proves otherwise.
- Automation is bounded by source/action policy and human approval gates.
- Minimize dependencies, cost, secrets, and generated state.

## Current scope: FOUNDATION-004

This repository defines the FOUNDATION-001 architecture, the FOUNDATION-002 local bakeoff harness, the FOUNDATION-003A conditional mission-state provider boundary, and FOUNDATION-004’s development-harness efficiency fixtures/evidence. LoopX remains isolated behind a normalized, fail-closed interface; external skill packs remain uninstalled and unpromoted. It contains no sibling-project integration, production writes, paid infrastructure, or general workflow engine.

## Future scope

Future work may add an event intake and routing implementation, local stores, provider adapters, project intelligence, mission state, and carefully approved integrations. Those decisions remain intentionally open and must be supported by experiments and evidence.

Start with [ARCHITECTURE.md](ARCHITECTURE.md), then [docs/harness.md](docs/harness.md) and [docs/next-bakeoffs.md](docs/next-bakeoffs.md).
