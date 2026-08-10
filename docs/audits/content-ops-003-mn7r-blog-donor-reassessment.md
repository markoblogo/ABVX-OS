# CONTENT-OPS-003 — MN7R Blog + Publishing Donor Reassessment

Status: READY_FOR_HUMAN_DECISION
Cost class: NORMAL

## MN7R blog implementation discovered

- Repository: `/Volumes/Work/Work/MN7R`
- Public surface: `https://mn7r.com/blog`
- Content storage: file-based markdown under `content/blog/*.md`
- Parser/contract: `shared/blogMarkdown.ts`
- Listing/order: `getPublishedBlogPosts()` sorts by `publishedAt` and then `date`, newest first
- Article route: `/blog/:slug` in `client/src/App.tsx`
- Index/list data: generated `client/src/data/blogPostIndex.generated.ts`
- Rendering: `client/src/pages/Mn7rBlog.tsx` with `react-markdown`
- SEO/structured data: `shared/blogSeo.ts`
- RSS/sitemap generation: `scripts/generate_seo_feeds.ts`
- Public validation seam: `scripts/smoke_public_routes.ts`
- Deployment shape: git-based app deploy; no CMS or DB required for the blog itself

## Deterministic publication seam

The smallest seam is:

- write one markdown file in `content/blog/`
- regenerate sitemap/rss/generated blog index files
- keep existing MN7R rendering and SEO helpers

This is now exposed as:

- `mn7r.publish-post`
- consumer command: `npm run content:publish-post -- --packet <packet> --dry-run|--write`

## Consumer-native rules retained

MN7R supports:

- title
- slug
- description/deck via `excerpt`
- body paragraphs as markdown
- cover image + alt
- tags
- canonical URL
- social title/description
- draft state
- newest-first ordering
- structured data / RSS / sitemap generation

MN7R does not currently support as first-class blog fields:

- distinct subtitle separate from excerpt
- first-class external resource action fields
- first-class video/embed fields
- explicit inline media placement metadata
- first-class language field

These fields are fail-closed in `mn7r.publish-post`.

## SSI production pain points used as donor requirements

The SSI acceptance case proved that routine publishing may require:

1. paragraph-preserving body
2. title + deck
3. deterministic newest-first ordering
4. cover handling
5. resource actions distinct from taxonomy
6. optional video/embed
7. media placement inside article flow
8. SEO metadata
9. structured data
10. sitemap/indexability
11. canonical URLs
12. deterministic CLI write path
13. git-compatible deployment
14. low recurring reasoning cost

MN7R already covers most of these natively except first-class resources/video/media-placement/subtitle semantics.

## Donor decision matrix

| Candidate | Classification | Why |
| --- | --- | --- |
| [gray-matter](https://github.com/jonschlinkert/gray-matter) | REFERENCE_ONLY | Battle-tested frontmatter parser/writer, but adopting it now would not remove enough code across `index`, `MN7R`, `ABVXsite`, and AzurMenton to beat the current small native seams. |
| [content-collections](https://github.com/sdorra/content-collections) | REFERENCE_ONLY | Strong typed content-collection model, but it implies a wider migration toward one collection system rather than improving the current mixed consumer-native publication surfaces. |
| [react-schemaorg](https://github.com/google/react-schemaorg) | REFERENCE_ONLY | Useful typed JSON-LD helper for React, but current manual schema helpers are already small and work across the current blog surfaces without adding another library boundary. |
| [mdx-bundler](https://github.com/kentcdodds/mdx-bundler) | NOT_NEEDED | Adds MDX/runtime complexity for first-class embeds, but the proven requirement set does not justify converting current markdown/file paths into MDX pipelines. |
| [Velite](https://github.com/zce/velite) | NOT_NEEDED | Attractive typed content layer, but it is effectively a content-system migration rather than a bounded improvement to existing consumer seams. |

## Donor outcome

No donor clearly wins under the governing rule:

`adoption cost + maintenance cost < maintaining the current small consumer-native fast paths`

Therefore the result for this slice is:

- keep current consumer-native publishing seams
- add MN7R as a new bounded consumer
- record donors as references only for a future Rule-of-Two trigger

## Implemented value

- Added `mn7r.post` to the canonical publishing adapter registry
- Added a bounded `mn7r.publish-post` consumer command with dry-run and write modes
- Added fail-closed checks for unsupported MN7R blog fields
- Added an ABVX dry-run fixture and publish-packet proof path for MN7R

## Impact on Cigarette Index -> 1D3X

No donor decision here changes the recommended path for the next real 1D3X publication.

The next Cigarette Index publication should still use the proven:

- ABVX ContentItem
- discovery enrichment
- `1d3x.article`
- `index.publish-post`
- targeted validation

No CMS or publishing donor migration is justified before that publication.
