# ABVX-OS working-tree review — 2026-10-10

Initial inventory: 4,362 changed files (135 tracked modifications, 4,227 untracked), approximately 1.7 GiB. `books/` accounts for 1,520 MiB, `artifacts/` 104 MiB, Book Radar 60 MiB. GitHub ABVX-OS is public.

## Disposition

- Verify and publish coherent code, schemas and synthetic regression fixtures from an isolated clean checkout.
- Keep manuscript/source assets, retailer observations, operational events, retained research and recovery snapshots locally pending explicit per-workstream review. Their size or untracked status does not establish that they are obsolete.
- Review credential-related and personal-material paths privately; do not include their source contents or real operational ledgers in public commits.
- Treat generated logs as cleanup candidates only after reference/retention review. No deletion or auto-archival has occurred.
- Do not push the current local branch wholesale: it has 14 local-only commits and 690 changed historical files, including 562 publication artifacts. Current remote main also has one independent newer commit. Publish selected changes on a clean branch instead.

## Test diagnosis

Book Core assumed the working GD3 text lock was NONE; prior integration expected stale retained hashes; reachability assumed a proposed policy despite its later approval. Regressions now initialize independent frozen/synthetic data. Their behavior and safety checks remain active; production state and policy were not rewritten.

The guarded run covers 138 tests across Book Core, prior, reachability, GD3 and Gate A and denies all reads/writes to operational `books/` and `book-radar/`.

A full unsandboxed/privileged integration result has not been established. The ordinary sandboxed broad run exposed separate macOS Keychain/Unix-socket integration failures. They must remain distinguishable from portable regression checks; granting credential access is not a way to make this cleanup pass.

## Next review boundary

A complete manuscript/research/credential-workstream audit is a separate EXPENSIVE review. This report is an inventory and bounded code validation, not a claim that all accumulated work is publication-ready.
