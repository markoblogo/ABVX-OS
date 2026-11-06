# Writing chronology and homepage release — 2026-10-10

## Result and boundaries

Cost class: NORMAL. Reused the site's existing RSS parsers, public content recipes, approval records, GitHub token and deployment flow. No new dependency, database or private-runtime coupling.

- Writing and the two existing homepage publication slots use one feed sorted numerically by immutable UTC `addedAt`. All native posts, Working Stories, Medium, Substack and YouTube participate.
- Source publication/upload dates stay separate for article/video metadata. Edits, retries and rebuilds do not renew addition times. Native video notes replace the matching raw YouTube card.
- First registration is committed with publication content, then deployed; it is not an exact Vercel-ready or first-request timestamp. Historical additions without evidence retain source publication dates with `legacy-source` provenance.
- Confirmed production evidence seeded the three pilot pages at `2026-10-10T16:06:30.000Z` and the flour Working Story at `2026-10-10T12:17:48.000Z`. No recovered historical time was fabricated.
- Homepage layout retains six cards and its two publication positions. Labels follow the destination: Read on Medium/Substack/ABVX, Watch on YouTube, or Watch on ABVX for native video notes. Recent videos stay compact; archive rows remain text only.

## Release evidence

1. [PR48](https://github.com/markoblogo/ABVXsite/pull/48): core implementation. Merge `8630a5b243893bab306e2cd672dedadeb897df22`; CI `38069750427` and main `38069859192` succeeded. GitHub production deployment `6983990094` succeeded at `2026-10-10T16:59:41Z`. Vercel `dpl_Hm2YEbJzszbnjYZGgLU4TxcH4YWv` was Ready, Production, alias `abvx.xyz`.
2. [PR49](https://github.com/markoblogo/ABVXsite/pull/49): fixed-source server fallback for runner feed failures. Merge `540dec50172a39dda5ed90cd0340466018119c73`; main CI `38070653994` succeeded. Production deployment `6984123616` succeeded at `2026-10-10T17:11:16Z`; actual public HTML identified Vercel `dpl_Ff2B4tZjnYwvfsZ9Zb9vjCCxHzia`.
3. [PR50](https://github.com/markoblogo/ABVXsite/pull/50): distinguish pinned YouTube metadata from upstream availability; reject truncated, unbalanced or malformed Atom envelopes before skipping fallback. Source `f657555a09948d98b8e961c4bd8bb54ff7c45431`; merge `0eb9019391fa1537c7e498850239540d1673f86a` at `2026-10-10T17:23:30Z`. CI [38071422188](https://github.com/markoblogo/ABVXsite/actions/runs/38071422188), main CI `38071540642` and Vercel Preview passed. GitHub production deployment `6984271619` succeeded at `2026-10-10T17:24:07Z`; actual public HTML identified `dpl_3KMSdfVRDLhMcSdt23DATmdoLRvV`. Authenticated Vercel inspection confirmed Ready, Production and alias `abvx.xyz`.

## Verification

- Full local release gate passed: content/ecosystem validation, lint, 116 sync tests, 23 vector tests, production webpack build, SEO QA for 191 routes and dependency audit (0 vulnerabilities). Existing lint warnings did not become errors. GitHub CI separately proved the default build.
- Public-domain browser checks at 390px and 1440px passed: correct homepage destinations, unchanged six-card layout, no home iframe, correct Writing order, one featured player, text-only archive and no horizontal overflow. Screenshots are saved in the calling task's visualization folder; they are not committed runtime state.
- Top slots after release: native Superman simulator video notes, then AI startup funding analysis; AI agents article follows in Writing. Source dates do not move these materials into the archive.
- [GitHub sync 38070807480](https://github.com/markoblogo/ABVXsite/actions/runs/38070807480) succeeded: `substack: 20 records via ABVX fallback`, `44 records; unchanged`. The production metadata endpoint returned HTTP200 with 20 items. This proves fallback and idempotence, not a specific cause of the runner's direct-fetch failure.
- Final [GitHub sync 38071601195](https://github.com/markoblogo/ABVXsite/actions/runs/38071601195) on the PR50 merge succeeded: Substack 20 records and YouTube 5 records through the ABVX fallback, 44 records unchanged, all 10 chronology tests passed. No registry commit or extra deployment was created. Final public-domain browser checks again passed at both 390px and 1440px.
- The owner-authorized site workflow runs hourly at minute41 UTC, plus manual dispatch. It may update only `content/writing-discovery.json` on main; identical data causes no commit/deployment. GitHub scheduling and deployment delays are not an exact hourly SLA.
- Discovery endpoint sources are fixed to Medium, Substack and YouTube; responses are public metadata with `X-Robots-Tag: noindex`. No arbitrary fetch URL or private content is exposed.

No Google indexing, ranking or traffic improvement is claimed by this release. Search Console observations remain a separate evidence stream.

UI reference used only to preserve an existing featured/grid publication structure: [Lazyweb research](https://www.lazyweb.com/agentic-search/34c784f1-aafe-4877-a77e-47a03d7ead58).
