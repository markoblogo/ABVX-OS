# Operational Playbooks

Operational playbooks are compiled procedures for routine operations that have already been proven by deeper project work. They are not a workflow engine, scheduler, or autonomous agent layer.

## Model

Each playbook records:

- `id`, `project`, `purpose`
- required inputs
- deterministic steps and commands
- validation tier and escalation triggers
- expected outputs
- allowed and prohibited changes
- compact event emitted on success
- provenance and version

## Validation tiers

- `QUICK`:
  deterministic, low-risk operations with unchanged code and known structure
- `STANDARD`:
  normal content publication and other project operations that need targeted proof but not a full repository sweep
- `FULL`:
  code changes, structural exceptions, targeted-check failure, or explicit request for broader validation
- `CRITICAL`:
  security, infrastructure, or other consequential operations requiring the full path plus an explicit approval gate

For AzurMenton:

- prepared image attachment defaults to `QUICK`
- normal guide publication defaults to `STANDARD`
- code or architecture changes escalate to `FULL`
- security or infrastructure-sensitive work escalates to `CRITICAL`

## Periodic consolidation principle

Routine operations emit compact project events only.

- routine operation
  -> compact event
- periodic consolidation
  -> portfolio lesson
  -> strategy change
  -> capability promotion

No scheduler or background agent is implied by this model. Consolidation remains an explicit human-directed pass.
