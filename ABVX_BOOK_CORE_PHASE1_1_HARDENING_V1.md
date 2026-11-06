# ABVX Book Core Phase 1.1 Hardening

Date: 2026-09-30\
Scope: bounded core hardening only

## Outcome

**PHASE 1.1 HARDENING: REVIEW.** The runtime integration, pinned development dependency set, snapshot helper, fail-closed gate, and tests are implemented. The local Python environment lacks `python-jsonschema`; the package index could not be reached, so the actual Draft 2020-12 acceptance suite could not pass here. No successful package download occurred.

## JSON Schema

- The state validator explicitly constructs `Draft202012Validator`, checks the schema against the Draft 2020-12 meta-schema, applies `FormatChecker`, and resolves schema-local `$ref`s through the library.
- Generic Book Core semantic checks still run after structural validation. A schema-valid unknown extension with `state: PASS` remains rejected by the ABVX semantic validator.
- The development/runtime dependency closure is pinned in `requirements-dev.txt`:

| Package | Version | License |
|---|---:|---|
| `jsonschema` | 4.25.1 | MIT |
| `attrs` | 25.3.0 | MIT |
| `jsonschema-specifications` | 2025.9.1 | MIT |
| `referencing` | 0.36.2 | MIT |
| `rpds-py` | 0.27.1 | MIT |

Dependency edges: `jsonschema → attrs, jsonschema-specifications, referencing, rpds-py`; `jsonschema-specifications → referencing`; `referencing → attrs, rpds-py`. The repository has no package lock or hash-pinning convention (its existing `requirements-dev.txt` uses version ranges), so source artifact checksums were not added. Runtime validation performs no network access; missing dependency raises an explicit error rather than silently falling back.

Verification limit: none of the pinned packages is installed in either available Python environment. A package-index connection attempt failed DNS resolution before any package was downloaded. Therefore `FULL_DRAFT_2020_12_SCHEMA_VALIDATION: NO` in this run; the real validator is wired but not locally executed.

## Protected snapshot helper

Implemented:

- `./bin/abvx protect snapshot <scope> <protected-file> [...]`
- `./bin/abvx protect recheck <snapshot-path>`
- `./bin/abvx protect gate <candidate> --required <true|false> --started-at <UTC> [--snapshot <path>] [--missing-policy REVIEW|HOLD]`

The helper only snapshots the explicit file list. It creates timestamped, exclusive-create, read-only JSON snapshots under `.codex/protected-snapshots/`. Rechecks report `UNCHANGED`, `CHANGED`, or `MISSING`. A required snapshot must predate the supplied run-start timestamp and all protected files must remain unchanged for `PASS` eligibility; missing/late snapshots downgrade `PASS` to the selected policy state, and changed/missing files produce `HOLD`. See `docs/protected-snapshot-policy.md`.

For this run, the explicit pre-edit snapshot was recorded at `2026-09-30T18:30:14Z` for GD3 state and event-ledger bytes, then checked using the new helper. Both report `UNCHANGED`; the gate accepts the candidate PASS. The pre-run snapshot itself was persisted before the first implementation edit.

## Tests and protected state

- Protected snapshot helper: **9/9 PASS**.
- Existing GD3 regression: **44/44 PASS**.
- Existing Book Core suite: **27/36 passed; 9 errored because the pinned dependency is unavailable**.
- New Draft 2020-12 acceptance suite: **0/6 verified; blocked by the same missing dependency**. Tests cover valid state, invalid enum, missing field, conditional failure, bad local ref, and schema-valid/semantic-invalid rejection.
- `py_compile`: PASS for modified Python modules.
- CLI status remains `NOT_STARTED` / `A_PENDING`; CLI validation remains `OVERALL: REVIEW`.
- GD3 state SHA-256: `31dbf80e755533241d754b43048796761df785cb2f3aa3c01bf31be16a877e55` (unchanged).
- GD3 event ledger SHA-256: `8ee2f93754bf95f6fd302881fbe5f2267f9b9896fcc3926ea4c894eec0a0aeb8` (unchanged).
- Book Three creative work, EPUB/translation/print spikes, external API calls, external writes: **not performed**.

## Gate

```text
PHASE 1.1 HARDENING: REVIEW
FULL DRAFT 2020-12 VALIDATION: NO
PROTECTED SNAPSHOT HELPER: PASS
PRE-RUN SNAPSHOT POLICY: ENFORCED
CORE TESTS: 27/36 PASS; 9 BLOCKED BY MISSING DEPENDENCY
GD3 REGRESSION: 44/44 PASS
GD3 STATE: UNCHANGED
GD3 EVENT LEDGER: UNCHANGED
BOOK THREE CREATIVE WORK: NOT STARTED
EXTERNAL API CALLS: 0
EXTERNAL WRITES: 0
NEXT GATE: GOOD DOG BOOK THREE — GATE A
AUTHORIZED: NO
```
