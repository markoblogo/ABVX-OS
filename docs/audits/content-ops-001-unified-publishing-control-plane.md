# CONTENT-OPS-001 — Unified Publishing Control Plane

Cost class: `NORMAL`

Scope: add the smallest ABVX-side content control plane that prepares, validates, approves, and hands off publication work into existing consumer publishing mechanisms without mutating sibling repositories.

## Consumer publishing mechanisms discovered

1. `ABVXsite`
   - existing file-based content workflow in `content/work/*.md`, `content/books/*.md`, `content/series/*.md`
   - validation/build path: `npm run content:validate`, `npm run build`
   - current fit for ABVX publication: `work`
   - Notes readiness: blocked because `/notes` and `/notes/[slug]` do not exist yet

2. `index`
   - SSI content currently lives in `src/lib/blog-posts.ts`
   - 1D3X content currently lives in `src/lib/platform-blog-posts.ts`
   - validation/build path: `npm run typecheck`, `npm run build`
   - these are real mechanisms, but still repo-specific and code-defined

3. `AzurMenton`
   - guide publication already has a proven repo-specific workflow
   - ABVX must route future guide work into `azurmenton.publish-guide`
   - no second publisher should be built

## Design decision

ABVX now owns only:

- canonical `ContentItem` preparation state
- human approval state
- publish handoff packet
- compact evidence/event emission

ABVX does not own:

- a renderer
- a CMS
- cross-project content storage
- consumer repo mutation
- automatic deployment

## Publish semantics

`./bin/abvx content publish <id>` is intentionally fail-closed and local-only.

It emits:

- a publish packet under `content/publish-packets/`
- an evidence record under `evidence/content-ops/`
- a compact project event under `events/projects/<project>/`

Result is `CONDITIONAL_PASS`, because ABVX proves the handoff packet and target mechanism, not the public deployment itself.

## ABVX Notes readiness

Current status: `BLOCKED`

Minimum ABVXsite change needed later:

1. add a note content type/loader
2. add `/notes`
3. add `/notes/[slug]`
4. wire the existing validation/build flow

That change was not implemented here.
