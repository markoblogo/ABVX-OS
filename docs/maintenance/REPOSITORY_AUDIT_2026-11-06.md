# Accumulated development audit — 2026-11-06

## Result and scope

The public-source consolidation uses a dedicated branch from current origin/main (ad27716), instead of pushing a divergent personal branch and its private historical commits. It carries reusable code, schemas, generic operating contracts, documentation and synthetic fixtures. Manuscripts, retailer captures, real outcomes, publication packets, credential inventories, recovery snapshots and the owner-specific production-learning journal remain local. No book publication, account write, paid provider call, Cortex transfer, deployment or merge is part of this audit.

The initial normal Git status summarized 888 entries; the full untracked-file inventory contained 5,318 paths. Approximately 1.9 GiB of new owner working material was identified, including PDFs beyond GitHub's ordinary blob limit. These are retention decisions, not obsolete-file deletion decisions. The reviewed source export is about 5 MiB.

## Corrections and optimization

- Updated README, architecture, changelog, development checks and the release-hygiene guide; closed the stale weekly instruction to repeat the completed six-product T7.
- Preserved newer main-branch source checks at approval and YouTube acquisition-budget/partial-status regression coverage while integrating accumulated changes.
- Made three native Keychain lifecycle cases explicit opt-in. Fake-key, budget, redaction, integrity and replay tests remain portable.
- Replaced private manuscript/retailer/protocol dependencies in unit tests with labeled synthetic data. Three source-bound historical acceptance cases remain separate opt-in checks. Unit translation budgets exercise generated 462-block input; they do not claim canonical manuscript acceptance.
- Made the disk-growth regression inject its test volume. Existing production protection against scanning non-internal volumes remains unchanged.
- Defaulted new operational journals and generated media to local retention. Existing tracked historical data is not removed from Git history by ignore rules.

## Verification

Python 3.12, requirements-dev.txt installed in an isolated environment on Work:
- Repository contracts PASS.
- Full suite: 1,140 tests, OK, 9 skipped; logs retained privately.
- Guarded book suite: 138 tests, OK; operational books/ and book-radar/ access denied.
- AST syntax checks PASS; no eval/exec/unsafe shell=True calls found by the bounded call scan.
- Public-file scan: one explicitly synthetic key canary in a test; no other provider-token/private-key matches, no symlinks or binaries, no new blob above 10 MiB.
- 4,977 protected owner files compared to the pre-audit hash manifest with no changes.

This is a bounded maintenance audit, not an independent penetration review or proof of unattended runtime readiness. Pattern scans do not establish absence of every possible secret. Native Keychain and private historical acceptance were not run. No performance or commercial-success claim is derived from passing tests.

## Retention and follow-up

The source owner workspace retains its unpublished private history and operational data. Maintenance corrections are applied back without changing real book/research records. The public task branch must remain separate until reviewed; push verification and CI evidence are recorded at closeout. Internal-disk cleanup and any owner-approved archive relocation have separate private path/hash receipts; they are not public research evidence.
