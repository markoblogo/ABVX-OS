# Next bakeoffs

Evaluate the development system before expensive platform work. FOUNDATION-002 establishes the minimal harness for experiment A; it does not select a provider. The remaining order is a proposal, not a selection:

1. **B — long-running mission/control-state:** compare durable local state patterns for pause/resume, retries, idempotency, and human gates.
2. **C — project/code intelligence:** compare narrow repository indexing and context extraction against a no-index baseline.
3. **D — explicit cross-project context:** compare least-privilege context packages, provenance, and isolation against manual handoff.

Each experiment uses the bakeoff protocol and ends at `STOP_FOR_HUMAN_DECISION`. Do not assume a candidate wins from its feature list.
