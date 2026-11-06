# Working Stories 002/003 — batch publication

Cost class: NORMAL. Owner requested the supplied Sweetheart Bottle case, then explicitly added the SMS vodka case and requested both in one pass. Reused the existing ABVX OS prepared-Markdown/media approval flow and independent ABVXsite consumer. No new subsystem, dependency or private runtime coupling.

## Sources and approved handoff

- Sweetheart Bottle input: attachment `b7419e03-c518-4aff-afde-4fcfa9f701a2/Вставлений текст.txt`; source `ws-002`, cluster `project-002`, period `2021`. Product-range photograph is the cover; close-up photograph follows the label section. Requested Behance reference is attached to that section through the existing case-study field.
- SMS vodka input: attachment `4579c82e-bfbc-4582-b8c1-d2938901957f/Вставлений текст.txt`; source `ws-003`, cluster `project-003`, period `Early 2000s`. Uses the supplied illustrative cover and an inline Gestalt Marketing link to verified existing `/books/dark-gestalt`. No related-book UI exists in Working Stories, so no additional block was introduced.
- Publication-safe JSON-frontmatter sources were prepared in `.tmp/abvx-publication-sources/`. Complete author narratives were preserved; source metadata/instructions and duplicate H1 were excluded from the body. The supplied Sweetheart subtitle became an introductory italic line; the vodka story's requested internal link replaces the original bold phrase.
- Source-specific owner authorization was recorded through `content approve` and `content publish`: `abvx-story-002` and `abvx-story-003`. These commands emitted handoff packets, not deployment proof. Approved Markdown SHA-256 values: `06472aee370d8daf3321ddc9b75d560fdb19923a49bf46f2b448d0a380288144` and `c82dd72f6ae8b62f40f7b7daf1f5580e21a3c81081cabf42d17c314c60679d2a`.
- Consumer dry-runs checked both ready/public sources and every asset descriptor. Applied sources and all three copied images matched approved hashes. No image bytes were altered.

## Website implementation

- `/writing/working-stories/baking-mixes-in-milk-bottles-branding-case-study`
- `/writing/working-stories/vodka-bottle-sms-marketing-storytelling`
- Added optional, validated `seoTitle` and `seoDescription` to the existing Working Stories schema/loader/route. Existing stories keep their defaults; visible headings, feed excerpts, Article headlines and manuscript exports retain author-facing content.
- Regenerated `public/llms.txt` and `public/content-index.json`. First-addition registry records both items at the same batch-registration time, `2026-10-10T17:31:23.749Z`; a stable tie-breaker determines their display order. No original publication dates were changed to manufacture an ordering difference.
- Both cases appear in the Working Stories collection, newest Writing positions and the two existing homepage publication slots. No design, navigation, CSS or unrelated content changes.

## Checks and release

- Full release gate passed: content/ecosystem validation, lint, 117 sync tests, 23 vector tests, production webpack build, 193-route SEO/discovery QA and dependency audit (0 vulnerabilities). CI separately checks the default build.
- Local browser checks passed at 390px and 1440px: correct visible/SEO titles, self-canonical URLs, metadata, Article JSON-LD, loaded images, secure Behance link, Dark Gestalt link, newest Writing/home slots, text-only archive and no horizontal overflow. Captured and inspected representative screenshots.
- Behance rejected automated page fetch with HTTP403. The supplied URL, placement and new-tab attributes are verified; destination content access is not claimed.
- [PR51](https://github.com/markoblogo/ABVXsite/pull/51), source `d654f350c3205445f54bd4857866ff64122271a2`. CI 38072279303 passed; merged as `6b73337d8fc4a21a1f49b3d2aed22b2f2cb4f489` at 17:35:56Z. GitHub production deployment 6984430354 reported success at 17:36:40Z, environment `https://abv-xsite-pi3qltpz9-abvcreative.vercel.app`. Canonical HTML identified Vercel `dpl_GuC2ErZ99SsqEjtGscqbztZiwTqF`; CLI inspection initially failed with a network fetch error. Final canonical verification follows the homepage release below.

Search Console indexing and traffic changes remain separate from successful publication.

## Owner-added homepage corrections

The two-case PR had already merged when the owner added four homepage corrections; those were consolidated into a single subsequent release rather than modifying or republishing the cases. [PR52](https://github.com/markoblogo/ABVXsite/pull/52), source `0693bc6a0e8dd78d52c01c267072eaabfd8e7796`.

- Existing six-card layout retained: three chronological Writing entries replace the two Writing plus MN7R slots. The same feed/order supplies /writing and the home cards; destination labels remain source-aware. No CSS or navigation changes.
- Focus, Systems and Books selection now uses immutable first-addition times in the site-owned public catalogue registry. Prebuild registers new public work/book/series records; CI requires registry changes committed. Edits, GitHub activity and later releases do not renew existing timestamps. Original source dates are untouched.
- Migration: 91 catalogue records, including 25 unknown legacy dates retained as null; known source dates are explicitly fallback provenance. Four Good Dogs/Jekyll additions use GitHub production deployment 6886400376 at 2026-10-06T14:16:40Z for PR26 merge `61c1d06af2462a2546ab240143bc0e2e4b09c67d`. Equal batch dates use existing rank/title ties. Current selections: AMI Books: Physical Commodity Markets, TDM Enduro Tours, Good Dog, Bad System.
- Local content/ecosystem checks, lint, 121 sync tests, 23 vector tests and production webpack build passed. SEO server was initially blocked by sandbox EPERM; the permitted rerun passed all 193 routes. Audit found 0 vulnerabilities. 390px/1440px browser checks passed both stories, metadata/images/links, three matching home/Writing entries, expected catalogue cards, text-only archive and no horizontal overflow. Repeat registry generation made no changes.
- Bounded [editorial-card reference](https://www.lazyweb.com/agentic-search/e39eaabd-6a6b-417c-9178-952fb159850a) was consulted under the local Lazyweb policy. Existing ABVX layout and components were retained. No Growth Report, redesign, dependency or service was introduced.

PR52 CI 38073304930 passed the default build and registry drift check; Preview succeeded and no inline review comments were present. Merged as `698731c61d39f3373ca7f92ea966bdc61687d299` at 2026-10-10T17:51:41Z. GitHub production deployment 6984613170 for that SHA reported provider success at 17:52:35Z, environment `https://abv-xsite-7rrujb3hy-abvcreative.vercel.app`. Canonical homepage HTML identifies Vercel `dpl_7ogxro8J5AD3mceRHDZdaCDAFZis` and contains the requested cards. Direct CLI inspection remained unavailable with a network fetch error under both Node runtimes; no CLI READY result is claimed.

From the checkout at the merge SHA, canonical production SEO/discovery QA passed for 193 routes. Production browser checks passed at 390px and 1440px: both cases and their original visible titles, custom SEO metadata, loaded media, secure Behance link and internal Dark Gestalt link; collection/Writing discovery; all six home cards with AMI/TDM/Good Dog selections and the three most recent Writing URLs in matching order; text-only archive and no horizontal overflow. The first browser run timed out waiting for network idle on the collection; rerun waited for document/content and actual image completion instead, and passed. Final screenshots are saved in the task visualization directory. Re-running catalogue registration from the merge checkout was unchanged.

Public results: both case routes and the corrected main homepage are live. This does not establish search indexing or traffic impact.
