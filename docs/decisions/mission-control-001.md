# FOUNDATION-003 decision report: mission control

## Decision

**CONDITIONAL_ADOPT** — human decision recorded in FOUNDATION-003A.

This is a narrowly bounded provider admission, not a general integration. LoopX may be used only as the optional long-running development mission state provider through the FOUNDATION-003A boundary. Real sibling-project use remains separately blocked.

## Candidates and fixture

- Native baseline: fixture-specific atomic JSON checkpoint; no reusable orchestration layer.
- LoopX: disposable upstream checkout at `ec48bd0052470d32da32517f7d4506f9d03fa2e9`, MIT license, Python 3.11+ package with no runtime dependencies.
- Mission: fictional “Make CoqPi call-ready for a real professional call.” The actual CoqPi repository was not accessed.
- Both candidates ran interruption, fresh-process resume, retry, gate wait, approval, completion, rerun, corruption, and cleanup phases.

## Raw results

| Candidate | Result | Duration | Important observation |
|---|---:|---:|---|
| Native baseline | PASS | 1,703 ms | All checks passed, including fail-closed corrupted-state handling. |
| LoopX | INCONCLUSIVE | 40,425 ms | Interruption/resume, retry, gate, completion, rerun and cleanup passed; malformed state was accepted as an empty todo state. |

Evidence is stored in [evidence/bakeoffs/mission-control-001/](../../evidence/bakeoffs/mission-control-001/), with the exact run under `runs/20260808T125949520017Z/`.

## Qualitative assessment

LoopX solves a real problem the native baseline deliberately does not: reusable provider-neutral mission state across arbitrary development sessions, including todos, gates, quota, evidence, and handoffs. That matters for multi-day engineering/research/experiment missions, not for every short task.

The cost is material. The native fixture took 1.7 seconds and 306 lines of fixture-specific code. The LoopX run took 40.4 seconds and introduced a large upstream surface observed at 703 Python files and about 315k Python LOC, despite zero runtime package dependencies. Its current upstream README exposes optional scheduler/heartbeat, claims/leases, projections, host bridges, and domain capabilities; these are useful patterns but are outside ABVX-OS’s role.

The main unresolved correctness issue is fail-closed state integrity: the fixture’s malformed LoopX state was accepted as an empty state. That makes the result conditional, not a clean pass.

## Proposed ownership boundary if approved

LoopX owns only optional development mission/control-state persistence, mission-scoped todos, human gates, quota metadata, evidence and handoff projection.

LoopX must not own ABVX canonical identity, portfolio prioritization, Cortex knowledge, project strategy, execution providers, Universal Inbox, media/revenue/support workflows, production authorization, or external writes.

## Conditions before any integration

1. Human approval of this report.
2. Fail-closed integrity/corruption handling demonstrated without broad upstream patching.
3. A provider portability check using Prime Agent or another approved execution provider; no candidate installation is authorized by this report.
4. Explicit version pin, isolated project-local state, backup/rollback path, and no scheduler/daemon/host bridge by default.
5. ABVX remains authoritative for registries, decisions, evidence references, and approval policy.

## Retained patterns even without adoption

Explicit human gates; quota checked before continuation; evidence-backed handoffs; provider-neutral state boundaries; read-first inspection; and atomic/file-locked local writes.

No sibling repository, production system, or external candidate source was modified. The next action is one human decision: approve or reject the conditional LoopX scope above. Do not start another bakeoff automatically.
