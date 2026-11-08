# Reviewed workspace consolidation — 2026-11-08

The source workspace was on a divergent personal branch. The reviewed branch starts at current `origin/main` (`001e7a7`), preserving newer upstream fixes and the managed ecosystem README links. Old local commits are not pushed wholesale. Most reusable implementation in the working directory was already present upstream and needs no duplicate commit.

## Retained thematic blocks

| Block | Reviewed result |
|---|---|
| Nantes journal | Read-only `context` projection of at most three earlier dates; bounded stage excerpts, source timestamps and state digests; missing/corrupt history stays blocked, no inferred owner decision or fresh verification |
| Radar sources | Shared [browser-only Kagi instruction and 5–8-query protocol](../playbooks/kagi-radar-comparison-v1.md), linked from the existing Nantes, Multi-Market and YouTube guides and README |
| Publishing | Production-director guidance separates structure/product completeness and narrative text lock; retains visual provenance, reader-facing front matter and human release gates |
| Operator evidence | Dated [disk-prevention investigation](MAC_DISK_PREVENTION_2026-11-05.md) and [rejected classifier pilot](PHOCINAE_MAC_PILOT_2026-10-10.md); corrected stale summary wording, no new host/model operation |
| Maintenance documentation | This disposition, changelog and macOS temporary-directory guidance for portable checks |

## Rejected, removed and protected

- Rejected the local synthetic publication fixture's timestamp conversion. The canonical intake requires `YYYY-MM-DD`; replaying the timestamp version failed its existing regression. The fixture was restored to current main in both worktrees, with a local before/after receipt. No parser broadening was needed.
- Removed 334 ignored `.pyc` files (6,471,975 bytes) from the source workspace's `src`, `tests` and `scripts`, after retaining a path/hash manifest and verifying they were not tracked. These are reproducible interpreter caches; no source, configuration or research evidence was removed. This is unrelated to the suspended automatic Mac cache-cleanup workflow.
- The inventory found 651 local file-content differences from current main. Ten were selected as useful new public changes; one fixture change was rejected. The remaining 640 historical/private working files stay local, including research/manuscript derivatives, source provenance and operational state. They are not labelled useless merely because they are excluded from public Git. Generated operational packets are not synthetic fixtures.
- Source and state manifests remain local. No mass deletion, history rewrite, private-book upload, credential migration, API purchase, model rerun, Cortex admission or publication is part of this consolidation. The original working branch and research state are retained; the reviewed branch is the commit/push surface.

## Verification

Baseline contracts passed. The original full baseline run executed 1,140 tests with 9 expected opt-in skips; 12 exchange tests rejected the macOS default temporary path's symlink ancestor. Re-running the affected two modules under `TMPDIR=/private/tmp` passed all 16 tests without weakening the runtime path guard. The new journal block passed 16 focused tests. The rejected fixture change failed the existing canonical-markdown replay test and was removed.

Final verification: repository contracts PASS; 1,145 portable tests completed successfully with 9 expected opt-in skips; all 138 isolated-book tests passed while operational book/market paths were denied. Whitespace checks and the per-block reviewed-file credential-pattern/type/size scan passed. These are local checks, not a claim of remote CI or independent model review. Native Keychain/private-source acceptance and fresh operational/model outcomes are not established by portable tests. A branch push does not imply merge or deployment.

Read order remains `AGENTS.md` → `README.md` → `ARCHITECTURE.md` → the relevant operator guide. The [repository hygiene contract](REPOSITORY_HYGIENE_V1.md) continues to exclude private evidence from a public source release. All existing Radar schedules and saved automation prompts are unchanged.
