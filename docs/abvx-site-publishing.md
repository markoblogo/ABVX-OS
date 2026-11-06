# ABVX.xyz publication fast path

Cost class: NORMAL. Reuses `content-ops-control-plane`, the Azur Menton prepared-text/media playbook pattern, and ABVXsite's own content commands. No new renderer, CMS, scheduler or service dependency. The donor registry's existing publishing tools remain reference-only: the current file/validator seams cover this operation.

## Supported paths

| Input | Adapter | Consumer command | Public route |
| --- | --- | --- | --- |
| Native Writing note/article | `abvx.writing` | `content:publish-writing` | `/writing/<slug>` |
| Working Story | `abvx.working-story` | `content:publish-working-story` | `/writing/working-stories/<slug>` |
| Project/work record | existing `abvx.work` | existing `content:publish-project` | `/work/<slug>` |

Books and editorial translations keep their existing ABVXsite recipes; use the same release check, without forcing them through the Writing schema. YouTube/Medium/Substack feeds retain their existing import rules. The new intake helper accepts ready JSON-frontmatter Markdown for Writing and Working Stories; it does not author, translate, crawl or import the older channel archive.

## Repeatable operation

1. **Prepare in ABVX OS.** Use approved, publication-safe prose with explicit title, slug, summary, publication date and language. A native Writing source must have `primarySection: writing`, `status: live` and `visibility: public`. A story uses the site's Working Stories schema, stable ID and neutral cluster. Next real story after ws-001 is ws-002; never allocate IDs from a synthetic fixture. Source files and intended assets remain authoritative.

   ```sh
   python3 scripts/prepare_abvx_publication.py --source /absolute/story.md --id abvx-story-002 \
     --asset /absolute/cover.webp=/media/working-stories/story-002/cover.webp
   ./bin/abvx content inspect abvx-story-002 --json
   ```

   Repeat `--asset` for every local image referenced by either format, including files already on the site. For reuse, map the absolute existing `ABVXsite/public/media/...` file to its `/media/...` path. The consumer checks its approved SHA-256 and image signature and reuses matching bytes without overwriting the file. Native Writing supports `seoTitle`, `media`/`heroImage` with alt text and dimensions, and a reviewed YouTube `videoUrl` with timezone-aware `videoUploadedAt`. The matching YouTube thumbnail may remain remote; local images always require asset mappings.

2. **Review the concrete packet.** Inspect prose, dates, language, enrichment, media paths and related-link suggestions. Record approval only after a source-specific owner instruction; an instruction already authorizing that publication need not be requested again.

   ```sh
   ./bin/abvx content approve abvx-story-002
   ./bin/abvx content publish abvx-story-002
   ```

   `publish` emits `content/publish-packets/abvx-story-002.json`; it does not deploy or mutate ABVXsite. `CONDITIONAL_PASS` and the existing content event represent the handoff only. Re-running preparation resets the item to pending review. Approval binds the exact publication fields; later changes require reviewing and approving the item again before packet emission. Legacy approved items without an approval fingerprint also require this review. Both Markdown formats and all local media require SHA-256 checks, and the consumer verifies them again. Preserve supplied author prose, code-block indentation and source provenance; add editorial context separately.

3. **Apply in a clean ABVXsite checkout.** Fetch current main and create one `codex/` branch. Execute the consumer command from that project's checkout, never edit the sibling project directly from ABVX OS. Pass the absolute packet path; changing the checkout does not change the packet contract.

   ```sh
   npm run content:publish-working-story -- --packet /absolute/packet.json --dry-run
   npm run content:publish-working-story -- --packet /absolute/packet.json --write
   npm run content:release-check
   ```

   For native posts use `content:publish-writing`. Dry-run validates the source/body, target, ready date, referenced media and file conflicts; Working Stories additionally validate unique IDs and illustration placement. Apply preserves the exact Markdown source and approved image bytes. Existing content is never overwritten. Failure during file creation rolls back newly created files.

4. **Review one PR.** The release check runs content/ecosystem validation, lint, sync/vector tests, production build, SEO QA and dependency audit. Build regenerates the public indexes. Commit intended source, media and generated discovery files together; `exports/editorial-checks/` logs/receipt stay ignored. Resolve failures once, then re-run only affected checks unless another change justifies the complete gate. Fresh checkouts or changed dependencies still require `npm ci`. Release receipts include per-check and total elapsed time; use those measurements to target a slow or failed gate instead of repeating successful checks.

   Native Writing and Working Stories now also register immutable UTC first-addition times in `content/writing-discovery.json` during prebuild; include that registry in the source PR. Keep the author's publication date and video upload time separate. Updating prose, rebuilding or replacing an RSS video with native notes must not renew an existing native page's addition time. Writing and the three homepage publication slots share this chronology. The independent site workflow records new RSS discoveries hourly; it does not require ABVX OS to be running.

   Homepage chronology: all three publication slots use the shared Writing first-addition registry. New public work/book/series entries also require the site prebuild’s `catalogue:register` output in the PR. Catalogue slots use first additions; product edits, GitHub activity and later releases never renew those timestamps. Unknown legacy additions remain unknown instead of being assigned today’s date.

   When GitHub cannot read a provider feed, the sync retries the site's fixed `/api/writing/feed/<source>` metadata endpoint. YouTube availability must come from a complete channel Atom response, not the pinned demonstration item. Failed reads preserve saved records; unchanged data creates no commit or deployment.

   The local `npm run content:release-check -- --webpack` fallback is available when the environment blocks Turbopack worker ports. It is recorded in the receipt; CI must still prove the default build. No deployment build setting changes are implied.

5. **Verify online separately.** Wait for CI and Preview, then use the authorized site release flow. Verify Vercel Production is READY for the merge SHA. From a checkout matching the deployed content, `npm run content:production-check` reuses SEO/discovery QA against `https://abvx.xyz`. Open the changed route and archive, check actual media/embeds at mobile and desktop sizes, and verify external links. Record PR, merge SHA, deployment ID, canonical URL and observations. Search Console processing is a separate state. A packet, PR, preview or local build alone is not an online result.

## Boundaries and troubleshooting

- Draft/private site visibility is not repository confidentiality. No private client/session data in the public repository.
- Only local, explicitly mapped image files are copied; no remote downloads, image rewrites or unattended external distribution.
- Future-dated stories require a later generated-index release; this workflow does not schedule publication.
- A duplicate slug/ID requires reviewing the existing record, not force-overwriting it.
- Do not disable TLS validation to reach Vercel. Use the authenticated connector or authorized browser and keep deployment/source evidence distinct from URL availability.

Reference procedure: `playbooks/abvxsite.publish-content.json` (inspectable runbook, not a new replay handler). Consumer source: `docs/abvx-os-publishing.md` and the site's editorial checklist. Generic intake stays compatible with `./bin/abvx content <prepare|inspect|approve|publish>`.

## Original-content pilot and future intake

Start with two original articles and one selected video with useful authored notes, not a copy of the feed archive. Native video pages replace the matching RSS card in Writing; recent cards use a compact preview and archive rows remain text links. Preserve the feed cutoff and automatic discovery of later videos.

Use ABVX OS as the intake and approval record for subsequent content. Route each type to its existing project-owned recipe; the Markdown helper currently covers Writing and Working Stories, not every book/editorial schema. Batch related content, incoming links and generated indexes into one release.

After production proof, record Search Console URL inspection for the three canonical pages. A submitted indexing request is not an indexed result. Compare page-filtered impressions and clicks across consecutive 28-day periods after enough data accumulates; keep unknown or missing values explicit. Expand the pilot only after reviewing discovery and useful reader activity, without promising traffic from structured data or machine indexes alone.
