# Donor-first architecture and execution-cost policy

## Purpose

ABVX-OS is local-first and evidence-first, but it is not entitled to unlimited custom implementation. Platform work must default to reuse, thin adaptation, and small evidence-backed decisions before new subsystem construction.

Codex/model capacity is also a constrained portfolio resource. Platform work must preserve execution budget for revenue-relevant product work, production fixes, and urgent operational tasks.

## Donor-first decision order

For any non-trivial new capability, use this order:

1. Check whether the capability already exists in an owner-controlled project or approved ABVX implementation.
2. Check whether an already-reviewed external candidate exists in ABVX records.
3. Prefer configuration, wrapping, or a thin adapter over custom implementation.
4. If realistic candidates exist but remain unresolved, run a small bounded bakeoff.
5. Only then consider custom implementation.

Custom implementation must state:

- which internal capabilities were checked first;
- which donor candidates were checked first;
- why a thin wrapper/configuration path is insufficient;
- what concrete portfolio value justifies the custom build.

## Execution cost modes

Every substantial task should be framed up front as one of:

### CHEAP

Typical shape:

- docs
- registries
- configuration
- deterministic playbook use
- narrow adapter

Observable proxies:

- one repository
- narrow focus set
- low file-inspection breadth
- low generated LOC
- targeted validation only

### NORMAL

Typical shape:

- bounded integration
- bounded feature
- small repository-local implementation
- targeted tests plus normal validation

Observable proxies:

- one repository, possibly multiple modules
- moderate file-inspection breadth
- moderate generated LOC
- limited reasoning stages

### EXPENSIVE

Typical shape:

- broad research
- architecture-heavy implementation
- large cross-repository change
- repeated broad agent passes
- large validation surface

Observable proxies:

- multiple repositories
- broad file-inspection breadth
- large generated LOC
- broad external research
- multiple staged reasoning loops
- full-suite or repeated suite execution

`EXPENSIVE` work requires explicit human approval before execution.

Do not pretend to meter exact tokens/cost when the runtime cannot measure them. Use the observable proxies above instead.

## Token and resource reserve principle

Codex/model capacity is a portfolio resource, not a platform entitlement.

ABVX-OS must preserve capacity for:

- production bug fixing;
- Monitor / Index urgent work;
- revenue-relevant product development;
- CoqPi;
- AMI and other commercial surfaces;
- unexpected operational work.

Platform work competes for that capacity. It should not automatically outrank nearer-term economic or operational work.

## Candidate status vocabulary

Use only this small vocabulary in donor planning:

- `ADOPTED`
- `CONDITIONAL`
- `PILOT_WHEN_NEEDED`
- `PATTERN_SOURCE`
- `REFERENCE_ONLY`
- `REJECTED`
- `UNRECORDED`

If a candidate is named but ABVX-OS does not contain enough evidence to assess it, mark it `UNRECORDED` rather than reconstructing analysis from memory.

## Canonical donor matrix

The canonical donor/capability matrix is stored in:

- [registries/donor-capability-matrix.json](/Volumes/Work/Work/ABVX-OS/registries/donor-capability-matrix.json)

That matrix must remain evidence-grounded:

- existing ABVX registry entries;
- existing ABVX intake items;
- existing ABVX decisions/audits/evidence.

It is not a wish list and not a reason to start a new candidate evaluation automatically.

## Protected capability gaps

The current major capability gaps are recorded in:

- [registries/capability-gaps.json](/Volumes/Work/Work/ABVX-OS/registries/capability-gaps.json)

For each gap, ABVX should record:

- what ABVX already has;
- plausible donors;
- what must not be custom-built before donor review;
- the next real trigger that would justify a pilot or implementation.

These gaps are explicitly protected from premature custom builds. “Useful someday” is not a sufficient trigger.

## Platform ROI rule

Platform work should materially improve at least one of:

- revenue potential;
- opportunity creation;
- human attention saved;
- token/execution cost saved;
- distribution;
- knowledge leverage;
- reliability/security.

If none is materially improved, the platform task should normally not be prioritized.

## Operational guardrails for future Codex sessions

Before significant new implementation:

1. Check [registries/capabilities.json](/Volumes/Work/Work/ABVX-OS/registries/capabilities.json).
2. Check [registries/donor-capability-matrix.json](/Volumes/Work/Work/ABVX-OS/registries/donor-capability-matrix.json).
3. Classify the work as `CHEAP`, `NORMAL`, or `EXPENSIVE`.
4. Stop if the work is `EXPENSIVE` and explicit human approval is absent.
5. Prefer a proven playbook when the task is a routine repeated operation.
