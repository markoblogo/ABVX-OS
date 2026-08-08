# Portfolio state

ABVX-OS keeps the smallest cross-project state in `portfolio/`:

- `strategy.json` — concise human-confirmed project strategy;
- `state.json` — operational attention and capacity state;
- `human-queue.json` — only owner-gated decisions/actions;
- `lessons.json` — project-to-platform feedback, without automatic extraction.

`./bin/abvx portfolio inspect` renders the actionable and human-waiting views. Add `--json` for machine-readable output.

Strategic priority and Codex capacity demand are separate fields. A project can be HIGH priority and `WAITING_FOR_HUMAN` with `NONE` capacity demand; that state must not block an ACTIVE high-value project from consuming available development capacity. The inspect command reports this as a recommendation, not an autonomous prioritization decision.

The Rule of Two is explicit: the first observed project need is recorded as `CAPABILITY_CANDIDATE`. Shared extraction is considered only after a second real project demonstrates the same need or compelling architecture/economic evidence justifies earlier extraction. This pass promotes nothing into shared ABVX infrastructure.

Only CoqPi and AzurMenton are represented because they have current onboarding evidence. Other projects remain outside portfolio state until properly onboarded.
