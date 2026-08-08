# ADR FOUNDATION-003A: Conditional LoopX admission

## Status

Accepted conditionally by human decision: `CONDITIONAL_ADOPT`.

## Decision

LoopX is admitted only as the **long-running development mission state provider** for future development missions. This decision records a provider role, not a general integration or automatic runtime adoption.

LoopX may own mission-local:

- objective and work state;
- gates and waiting-for-human state;
- bounded retry state and quota metadata;
- evidence references;
- resume/handoff state;
- terminal mission state.

LoopX must not own portfolio priorities, project strategy, canonical project facts, Personal Cortex, Universal Inbox, Opportunity Engine, Media Resource, generic personal task management, code execution, deployment authorization, or external writes.

## Boundary

ABVX exposes the normalized `MissionStateProvider` contract in `src/abvx_harness/mission_state.py`. The conceptual operations are create, inspect, record/update, wait for gate, approve/reject, resume, complete, export, and explicit recovery. The backend is injected; ABVX does not import LoopX types or recreate LoopX’s internal model.

The normalized export is versioned by `schemas/mission_state_export.schema.json`. It is sufficient to replace the backend without reconstructing mission history from provider-internal data.

The FOUNDATION-002 native baseline remains the reference implementation, diagnostic fallback, and migration target. It is not being expanded into a second full mission system.

## Integrity and recovery

For a known mission:

- valid state proceeds;
- missing state is an `INTEGRITY_ERROR`;
- unreadable/corrupt state is an `INTEGRITY_ERROR`;
- schema or structure mismatch is an `INTEGRITY_ERROR`.

Only an explicit `create_mission` call may initialize empty state. Every valid state is captured as an atomic snapshot with a SHA-256 digest. `recover` restores only the newest snapshot whose schema and digest validate, and writes recovery evidence. Failed recovery writes failed evidence and stops for intervention. Recovery never reopens a gate or restarts a terminal mission.

## Guardrails

No scheduler, daemon, web UI, database, sibling-project integration, code execution, deployment authorization, Prime Agent evaluation, or new bakeoff is part of this decision. LoopX remains conditional and must be used only through the boundary after a separate operational approval for a real development mission.
