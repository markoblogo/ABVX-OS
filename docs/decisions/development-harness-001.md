# FOUNDATION-004 decision report: development harness efficiency

## Decision

**INCONCLUSIVE** — `STOP_FOR_HUMAN_DECISION`.

The local evidence proves that the three deterministic fixtures and the evidence path work. It does not prove that any external skill configuration improves a real agent’s coding outcome, because this repository has no reproducible model-agent execution adapter. No skill pack is installed, promoted, or copied into ABVX-OS.

## Fixtures

- **Bugfix:** preserve explicit `0` in `parse_timeout`; regression tests cover zero, default, and invalid input.
- **Moderate feature:** add label display while reusing `normalize_label`, preserving order and avoiding dependencies.
- **Architecture-affecting change:** carry an optional request identifier through service and transport, preserve legacy callers, reuse `build_headers`, and update architecture documentation.

All fixture validation passed: 4, 2, and 2 tests respectively. The matrix command completed in 446 ms.

## Candidate qualification

| Configuration | Selected subset | Skill text | Setup/stages | Agent result |
|---|---|---:|---:|---|
| Native | none | 0 lines / 0 B | 0 / 0 | NOT_RUN |
| Matt selected | TDD, diagnosing-bugs, code-review | 265 / 19,171 B | 2 / 2 | NOT_RUN |
| Addy selected | TDD, incremental-implementation, code-review-and-quality | 1,043 / 46,521 B | 2 / 3 | NOT_RUN |
| Native + Ponytail | Ponytail | 120 / 6,637 B | 2 / 1 | NOT_RUN |
| Matt + Ponytail | Matt subset + Ponytail | 385 / 25,808 B | 4 / 3 | NOT_RUN |

These are observable prompt/setup proxies, not token counts. Actual agent elapsed time, changed LOC, retries, requirements quality, correctness, and human review burden remain unmeasured.

## Upstream qualification

Matt Pocock’s repository is MIT-licensed and was observed at `84fdeffd12f2ee307994d1eb6feb48173b6e0502` (2026-08-06). Its Codex path uses `npx skills@latest add mattpocock/skills`, allows selecting skills, and then asks for repository setup. The selected subset was limited to TDD, diagnosing-bugs, and code-review; spec/grilling and lifecycle tracker skills were rejected for this already-bounded bakeoff.

Addy Osmani’s repository is MIT-licensed and was observed at `f49337711b7a932b4b338c1d4ad73384df8fd87d` (2026-08-08). It exposes a native Codex plugin installation path and 24 skills. The selected subset was limited to test-driven-development, incremental-implementation, and code-review-and-quality; broader planning, source-driven, security, shipping, and context skills were rejected as unnecessary for these fixtures.

Ponytail is MIT-licensed and was observed at `2ed6c52c9d7e5e56942508591085fd45dea277d3` (2026-08-08). Its Codex plugin uses lifecycle hooks and defaults to full mode; uninstall also requires cleanup of state outside the plugin directory. It remains a selective intervention candidate, not a separate full candidate and not an always-on ABVX dependency.

No upstream files were copied into this repository. Matt’s editable installer would add selected skill files and may add setup conventions; rollback is removing those files/configuration. Addy’s Codex plugin is host-managed; rollback is plugin removal. Ponytail’s rollback is plugin removal plus its documented external mode/config/status-line cleanup. None of these workflows may override AGENTS.md, add issue-tracker state, or widen ABVX’s local-only boundary.

## Recommendation

Use the existing native ABVX flow provisionally:

```text
inspect
→ clarify only if needed
→ reuse-before-build
→ implement the smallest change
→ test focused behavior
→ run full verification
→ review for unnecessary complexity
→ record evidence
```

Retain the fixture pattern, reuse-before-build check, red-green regression check, focused verification, and final simplification/review. Do not install external packs globally or into sibling repositories.

The decision is not ready to authorize a real project onboarding. FOUNDATION-005 may be proposed as the first real project onboarding for CoqPi, but must not begin automatically.
