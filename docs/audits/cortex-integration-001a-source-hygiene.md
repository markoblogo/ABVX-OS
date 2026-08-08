# CORTEX-INTEGRATION-001A

Date: 2026-08-08

Scope: fix the confirmed Index Cortex source-admission blocker before any
ABVX-OS ↔ Cortex read-only retrieval bridge.

Target repositories:

- `ABVX-OS`: evidence and platform feedback only
- `Index Cortex`: `/Volumes/Work/Work/index`

## Defect reproduced before change

The pre-fix `index` source corpus admitted runtime noise into long-term
retrieval inputs.

Source-manifest before rebuild:

- total sources: `414`
- `SESSION`: `16`
- `CACHE`: `2`

Concrete unwanted admitted examples:

- `.whatsapp-session-20260703/session/CertificateRevocation/10624/manifest.json`
- `.whatsapp-session-20260703/session/Default/Service Worker/CacheStorage/.../index.txt`
- `.wwebjs_cache/2.3000.1042607275.html`

Chunk-manifest before rebuild:

- total chunks: `11013`
- `SESSION`: `32`
- `CACHE`: `424`

This confirmed the blocker from `CORTEX-INTEGRATION-001`: retrieval inputs were
not constrained to explicit trusted repository knowledge.

## Admission policy

Index-owned repository scanning is now fail-closed.

Approved top-level directories:

- `docs/`
- `fixtures/`
- `prisma/`
- `public/`
- `scripts/`
- `services/`
- `src/`
- `tests/`

Approved top-level files:

- `AGENTS.md`
- `README.md`
- `package.json`
- `package-lock.json`
- selected repo config files already named in
  `src/lib/cortex-source-scanner.ts`
- top-level `.pdf` knowledge artifacts

Excluded by default:

- hidden/session/cache/build/generated/transient roots
- secret-like files
- any new unapproved top-level directory

Admitted `index-platform` repository entries are recorded as:

- trust level: `canonical`
- canonical status: `canonical`
- provenance expectation: `repo-committed-path`

Imported/generated ecosystem artifacts remain non-canonical and must enter only
through explicit merge steps.

## Implementation changed

Index changed:

- `src/lib/cortex-source-scanner.ts`
- `src/lib/cortex-source-scanner.test.ts`
- `src/lib/cortex-cropto-source-manifest.test.ts`
- `scripts/cortex-source-hygiene-report.ts`
- `docs/cortex-source-admission.md`
- `docs/cortex-artifact-pipeline.md`
- `package.json`

Behavioral change:

- scanner no longer walks arbitrary top-level directories for the `index`
  repository root;
- hidden/noisy runtime roots fail closed;
- each admitted source-manifest entry now carries explicit admission metadata;
- a deterministic hygiene report command exists for before/after corpus checks.

## Before / after counts

Source-manifest:

- before: `414`
- after: `534`

The increase is expected. The new policy removed runtime noise while also
admitting previously omitted approved canonical roots/files such as `tests/`,
additional repo config files, and top-level knowledge PDFs.

Noise counts after rebuild:

- `SESSION`: `0`
- `CACHE`: `0`
- `BUILD_ARTIFACT`: `0`
- `TEMPORARY`: `0`
- `UNKNOWN`: `0`

Chunk-manifest:

- before: `11013`
- after: `1618`

Noise counts after rebuild:

- no session/cache/build/temp chunks observed

## Rejected examples

Rejected after the fix:

- `.whatsapp-session-20260703/session/manifest.json`
- `.wwebjs_cache/session.html`
- any new unapproved top-level directory such as fixture `sandbox/`

## Retained examples

Retained after the fix:

- `docs/cortex-artifact-pipeline.md`
- `docs/commodity-intelligence-layer.md`
- `src/lib/cortex-memory-context-pack.ts`
- `scripts/cortex-source-scan.ts`
- `public/files/uga-index-methodology.pdf`
- top-level `AGENTS.md`, `README.md`, `package.json`

## Existing corpus cleanup path

Existing `.cortex` source/chunk artifacts are reproducible local outputs and may
be safely rebuilt.

Index-only cleanup path:

```bash
npm run cortex:source-ingest -- \
  --root=index:index-platform:/Volumes/Work/Work/index:internal \
  --manifest=.cortex/source-manifest.json \
  --ledger=.cortex/source-ledger.json

npm run cortex:source-chunk -- --all \
  --ledger=.cortex/source-ledger.json \
  --out=.cortex/chunk-manifest.json
```

## Context-pack regression

Representative rebuild check:

- query: `cortex artifact pipeline context pack runtime configuration`
- searched chunks: `1618`
- matched chunks: `16`
- approved evidence: `2`
- excluded evidence: `1`

Approved evidence remained available from:

- `index:docs/cortex-artifact-pipeline.md#0`
- `index:docs/cortex-artifact-pipeline.md#1`

No session/cache paths appeared in the pack.

## Remaining risks

- policy is explicit for the `index` repository root; other ecosystem imports
  still rely on their own source contracts and merge boundaries
- widening approved roots still requires deliberate code/test updates
- read-only bridge work is still unimplemented

## Decision

Blocking deficiency status: `RESOLVED`

Readiness for `CORTEX-INTEGRATION-002`:

- `YES`, from a source-hygiene perspective
- bridge work still requires a separate bounded slice and explicit approval
