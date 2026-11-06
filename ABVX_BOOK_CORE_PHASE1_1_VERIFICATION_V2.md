# Book Core Phase 1.1 — Follow-up Verification V2

Date: 2026-09-30. Preserves the historical `ABVX_BOOK_CORE_PHASE1_1_HARDENING_V1.md`, which correctly recorded an unavailable dependency in its original run. This successor records the owner-authorized runtime/transition repair and subsequent Gate A start, not a retroactive rewrite of that result.

## Verified runtime

FULL_DRAFT_2020_12_SCHEMA_VALIDATION: YES. Real `jsonschema.Draft202012Validator` checks the state meta-schema and valid/invalid synthetic fixtures. ABVX semantic validation remains independent; a schema-valid semantic-invalid state is still rejected. Tests cover enum, required field, conditional, bad local ref and rejected external reference. Runtime reference retrieval fails closed, does not download schemas.

Exact runtime closure in `requirements-dev.txt`: jsonschema 4.25.1, attrs 25.3.0, jsonschema-specifications 2025.9.1, referencing 0.36.2, rpds-py 0.27.1 (MIT). Additionally typing_extensions 4.15.0 (PSF-2.0), conditional on Python <3.13, completes referencing's declared dependency for the repository's supported older Python versions. Current verification used Python 3.14, so that conditional package was not installed or exercised; no claim of a Python 3.11 acceptance run.

Graph: jsonschema → attrs, jsonschema-specifications, referencing, rpds-py; jsonschema-specifications → referencing; referencing → attrs, rpds-py, conditional typing_extensions. Optional format extras are not adopted as an unpinned dependency set. Validation's applicable built-in format checks are not a claim to all optional format implementations.

The five active packages were installed from the package index into ignored `.tmp/book-core-runtime`; the existing CLI launcher includes that directory after repository source. Missing runtime fails explicitly. Packages are not vendored/committed. Runtime requires no network. Installation did require network reads. Source is PyPI; existing repository policy does not require downloaded-artifact checksums, so none are invented.

## Tests

Recorded executed suites: existing GD3 regression 44/44 PASS; Book Core 36/36 PASS; real-schema acceptance 7/7 PASS; protected snapshots 9/9 PASS; bounded Gate A transitions 8/8 PASS. Total 104/104. The changed tests preserve fail assertions while accepting real-validator diagnostic wording; the live GD3 compatibility assertion follows recorded state rather than assuming the project stays NOT_STARTED forever.

The core optional stage-metric shape is aligned to the actual state schema. No new rendering, EPUB/translation donor spike, STALE DAG, build manifest or historical book migration was implemented.

## Protected discipline and authorized state changes

PROTECTED SNAPSHOT HELPER: PASS. PRE-RUN SNAPSHOT POLICY: ENFORCED. The explicit nine-file Gate A snapshot predates edits and creative work. Its canon, locks, manifest, pipeline and gate-model entries remain immutable. GD3 state and ledger were deliberately changed only through the owner-authorized start/review workflow, not asserted unchanged.

New bounded command:

```text
./bin/abvx book gate-a gd3 start|review --authorization <project-relative-evidence> --snapshot <repo-relative-snapshot>
```

It requires local explicit start authorization, a real pre-run snapshot, full Draft 2020-12 checks, current event/state agreement, unchanged immutable inputs and (for review) all three decision packets. Review checks the original ledger prefix and original state/snapshot provenance. It never approves the engine or permits drafting. The generic snapshot gate still returns HOLD for changed protected files; this is not a global waiver.

Writer discipline: exclusive cooperating-writer lock; errors during write restore exact pre-transition bytes; fsync for both writes. A process crash between the two files is NOT claimed atomically recoverable; subsequent state/ledger mismatch fails closed and requires investigation. Non-cooperating writers are not prevented by this local lock.

TECHNICAL REPAIR: PASS within this bounded scope.
BOOK THREE: concept Gate A only, not drafting.
OWNER ENGINE APPROVAL: PENDING.
EXTERNAL WRITES: 0 consequential writes.
No commits or pushes.
