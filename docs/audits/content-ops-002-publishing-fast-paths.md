# CONTENT-OPS-002 — Publishing Fast Paths + Discovery Enrichment

Date: 2026-08-10
Cost class: NORMAL
Status: READY_FOR_HUMAN_DECISION

## Donor decision

- Donor registry checked first.
- Decision: `NOT_NEEDED` for this slice.
- Reason: existing consumer-native file/code publication seams in `index`, `ABVXsite`, and the proven AzurMenton playbook were simpler and safer than adopting a new donor or external publishing subsystem.

## What was added

### ABVX-OS

- normalized consumer-operation contract in content items and publish packets;
- discovery-enrichment package generation:
  - slug
  - SEO title
  - meta description
  - canonical path
  - OG/social metadata
  - author/publisher
  - tags/topics/entities
  - related-project hints
  - internal-link suggestions
  - hreflang
  - structured-data status
  - machine summary
- validation-tier escalation fields in publishing adapter registry;
- dry-run fixtures for:
  - SSI fast path
  - 1D3X fast path
  - ABVX project fast path
  - ABVX note fast path
  - AzurMenton playbook compatibility handoff

### index

- `scripts/publish-post.mjs`
- `npm run content:publish-post`
- bounded dry-run/apply surface for:
  - `ssi`
  - `1d3x`
- `pop` remains fail-closed / blocked.

### ABVXsite

- minimal file-based `/notes` and `/notes/[slug]` surface;
- `scripts/publish-project.mjs`;
- `scripts/publish-note.mjs`;
- `scripts/new-note.mjs`;
- `npm run content:new-note`;
- `npm run content:publish-project`;
- `npm run content:publish-note`;
- sitemap coverage for notes.

## Validation tiers

- `abvx.publish-note` → QUICK
- `ssi.short-post` → QUICK by default, escalates on structural/validation exceptions
- `1d3x.article` → STANDARD
- `abvx.publish-project` → STANDARD
- `azurmenton.publish-guide` handoff → STANDARD
- `pop` future path → BLOCKED

## Dry-run results

- ABVX emitted publish packets for all five CONTENT-OPS-002 dummy fixtures.
- index dry-run:
  - SSI packet accepted
  - 1D3X packet accepted
- ABVXsite dry-run:
  - project packet accepted
  - note packet accepted
- AzurMenton compatibility proved by packet emission into the existing playbook-handoff contract without creating a second publisher.

## Targeted validation run

- `PYTHONPATH=src python3 -m unittest tests.test_content_ops` → PASS
- `python3 -m py_compile src/abvx_harness/*.py` → PASS
- `./bin/abvx validate` → PASS
- `node scripts/publish-post.mjs --surface ssi ... --dry-run` → PASS
- `node scripts/publish-post.mjs --surface 1d3x ... --dry-run` → PASS
- `node scripts/publish-project.mjs ... --dry-run` → PASS
- `node scripts/publish-note.mjs ... --dry-run` → PASS
- `npm run typecheck` in `index` → PASS
- `npm run build` in `index` → PASS
- `npm run content:validate` in `ABVXsite` → PASS
- `npm run build` in `ABVXsite` → PASS
- `git diff --check` in `ABVX-OS`, `index`, `ABVXsite` → PASS

## What was intentionally not implemented

- no universal renderer;
- no CMS;
- no DB/CMS-backed notes;
- no real publication of planned content;
- no broad donor adoption;
- no autonomous content creation;
- no POP editorial path;
- no broad portfolio reasoning on routine publish events.

## First real publication recommendation

1. first real low-risk path: `abvx.publish-note`
2. next: `ssi.short-post`
3. then: `abvx.publish-project` or `1d3x.article`
4. keep AzurMenton on the existing proven guide playbook

## Remaining DEEP-mode cases

- factual conflicts
- duplicate/overlap judgement
- volatile claims needing verification
- localization exceptions
- new content type / structural exception
- POP editorial path after pipeline stabilization
