# Codex workspace retention preview v1

Status: **read-only, human review only**. Cost class **CHEAP/NORMAL** (bounded local file metadata and Git inspection). Added to the existing Mac operator. No extra scheduler, background job, file relocation, or deletion is enabled.

## Command

```sh
cd /Volumes/Work/Work/ABVX-OS
./bin/mac-operator codex-retention
```

Results are returned as JSON and also stored privately at `.tmp/mac-operator/codex-retention-preview.json`. Standard Mac operator request-ID idempotency and seven-day result redaction apply; each manual call should use a distinct ID. The existing five-minute monitor runs the expensive scan **only once per ISO week when a low-load guard passes**, never every five minutes. Manual previews remain separately invocable; see [Codex growth monitoring](CODEX_GROWTH_MONITOR_V1.md).

## Scope and policy

- Scan only date/session/work project directories under the **internal** `~/Documents/Codex` directory, requiring an existing `.git` directory. Respect mounted-device boundaries.
- Default threshold: **14 days** since the newest observed repository or tracked-file modification. This is an age hint, not proof a project is complete or unused.
- Candidate kinds: **`node_modules` and `.next` only**. Nested dependencies in apps are included, but scans never enter dependencies, Git internals, archives, builds, assets, output, virtual environments or unrelated folders. `dist` is deliberately excluded.
- Require clean Git status, readable tracked-file inventory (max 5,000 entries), an existing standard JS lockfile, and no evidence of process arguments or current working directories referencing the repository.
- Process-check failure, Git errors/dirty trees, missing lockfile, recent activity, or incomplete candidate measurement all prevent the `REVIEW_ELIGIBLE` status. Even that status **does not authorize deletion**.
- No symlink following; bounded discovery (60 repositories / 80 candidates), depth and per-candidate scan limits; explicit `partial` status on truncation. Scan is also bounded by a wall-clock budget. Sizes are estimates of allocated bytes; APFS may reclaim a different amount.
- Does not inspect `~/.codex/sessions`, `~/.codex/archived_sessions`, the external volume, or general user Documents beyond the Codex workspace layout.

## Interpretation and safeguards

`REVIEW_ELIGIBLE` means **eligible for a further human-approved, revalidated cleanup step**, not proven safe for automatic removal. Some ignored directories can contain manually edited files; filesystem timestamps, Git cleanliness and process checks do not establish semantic disposability.

No future deletion may depend on this report alone. A separate implementation needs a fresh recheck, exact-path owner approval, action journal, APFS before/after measurements, explicit exclusions and a way to stop if projects become active. Moving archived projects to external `Work` additionally needs a verified copy/integrity step and an independent backup plan for unique data.

## Tests

Run:

```sh
cd /Volumes/Work/Work/ABVX-OS
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mac_codex_retention.py' -v
```

Synthetic fixtures cover git-dirty/clean, activity guard, symlink exclusions, missing lockfile, partial measurement, budget, preview-only behavior and Mac operator integration. Tests do not delete any of the owner's files.
