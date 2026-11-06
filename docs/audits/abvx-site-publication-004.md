# ABVX-PUBLISHING-004 — Repeatable ABVX.xyz publishing

Cost class: NORMAL. Scope: existing content-ops registry/schema, a Markdown intake helper, Working Story consumer seam, and a deterministic release gate. Independent project repositories retain their own rendering and release flows.

## Reuse decision

- Internal capability: `content-ops-control-plane` (`prepare`, `inspect`, `approve`, `publish`).
- Procedure donor: `azurmenton.publish-guide` prepared text/media, consumer checks and distinct approval/production evidence.
- Consumer seams: existing `publish-writing.mjs`, Working Stories parser/validator/collection, index generators and SEO QA.
- Existing gray-matter, content-collections, react-schemaorg, mdx-bundler and Velite assessments remain reference-only. No donor adoption or new dependencies needed for this bounded adapter.

## Result

- Native Writing and Working Stories can be prepared from ready JSON-frontmatter Markdown with `scripts/prepare_abvx_publication.py`.
- Working Story source and mapped local media have approved-byte hashes; application preserves those bytes, validates the real source schema and refuses conflicts/duplicates.
- Approval remains source-specific. ABVX OS emits a handoff packet; it does not mutate consumer repositories or deploy.
- Consumer `content:release-check` reuses the existing checks, generates discovery output with the build and records ignored logs/outcomes. Local webpack fallback is recorded; normal build still requires CI proof.
- Consumer `content:production-check` reuses SEO/discovery QA against the public domain. Deployment SHA, actual media appearance and Search Console remain separate proof.
- Inspectable playbook and short owner/operator recipes replace repeated broad rediscovery. No scheduler, CMS, cross-project renderer or automatic social publication.

## Verification

- Content-ops tests: 11 passed with the existing pinned `jsonschema` runtime on `PYTHONPATH=src:.tmp/book-core-runtime`.
- ABVX OS repository validation and new playbook inspection passed.
- Consumer publication regressions: 8 passed, including exact source/media bytes, dry-run immutability, source tampering, conflicting metadata, duplicate ID/slug, missing/conflicting assets, symlink paths, rollback, language preservation and unsupported native fields.
- Cross-boundary integration passed: prepare → blocked publish without approval → approve → packet → consumer CLI dry-run → consumer apply in a temporary directory; saved source matched the packet exactly. Only synthetic temporary content was written; no test post was deployed.

The full consumer release result and PR/production state belong to the consumer release evidence, not this ABVX OS audit. Do not interpret local tests or the existing `CONDITIONAL_PASS` content event as a website publication.
