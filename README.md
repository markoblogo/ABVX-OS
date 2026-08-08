# ABVX-OS

ABVX-OS is the planned local-first control and integration layer for independently deployable projects, AI-assisted workflows, media and revenue assets, and a personal operational assistant.

## Operating principles

- Projects remain deployable and useful when ABVX-OS is unavailable.
- Evidence, provenance, and explicit ownership come before automation.
- Reuse internal capabilities and qualify external capabilities before building.
- Prefer a small modular monolith and local state until scale proves otherwise.
- Automation is bounded by source/action policy and human approval gates.
- Minimize dependencies, cost, secrets, and generated state.

## Current scope: FOUNDATION-001

This repository currently defines the canonical architecture, domain model, schemas, registries, autonomy policy, bakeoff protocol, acceptance fixtures, and next experiments. It contains no integrations, production writes, paid infrastructure, or external framework adoption.

## Future scope

Future work may add an event intake and routing implementation, local stores, provider adapters, project intelligence, mission state, and carefully approved integrations. Those decisions remain intentionally open and must be supported by experiments and evidence.

Start with [ARCHITECTURE.md](ARCHITECTURE.md), then [docs/domain-model.md](docs/domain-model.md) and [docs/next-bakeoffs.md](docs/next-bakeoffs.md).
