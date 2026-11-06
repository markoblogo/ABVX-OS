# ABVX.xyz original Writing pilot

Cost class: NORMAL. Existing content-ops control plane and ABVXsite consumer commands; no new CMS, runtime service, scheduler or dependency.

## Published material

| Material | Canonical URL | ABVX OS item |
| --- | --- | --- |
| Funding research | https://abvx.xyz/writing/ai-startup-funding-trends-7740-companies | `abvx-ai-startup-funding-7740` |
| Author's agent workflow | https://abvx.xyz/writing/how-i-work-with-ai-agents-2026 | `abvx-ai-agents-workflow-2026` |
| SKYFLY watch page and original notes | https://abvx.xyz/writing/40-ai-agents-superman-flight-simulator | `abvx-skyfly-video-pilot` |

Both articles were previously unpublished. The supplied author bodies are preserved exactly (1,397 and 1,753 words), with source/related-reading notes added separately. Funding data provenance is Anysite.io; an exact dataset cutoff and public export were not supplied. Treat figures as the author's research sample, not a current complete market census.

The video is `6q2JG0gCyDg`, uploaded `2026-10-10T15:20:37+00:00` according to the official YouTube feed. Commentary attributes the reported development counts to the video description and architecture/licensing to the linked SKYFLY README. It does not claim independent testing or unrestricted source reuse.

## Release evidence

- OS integration commit: `a95829c` (local only; unrelated OS branch work was not pushed).
- Site source commit: `01aa105efb45016913709c8e27d4b6c3d55d67c7`.
- PR: https://github.com/markoblogo/ABVXsite/pull/46.
- Production merge: `b4c9c9db999dcfa2c3ca7908a72d250d31d54bba`.
- CI: https://github.com/markoblogo/ABVXsite/actions/runs/38066096552, successful default build.
- Vercel deployment: `dpl_BHaWq4xqsyL7CCt4bpU92i41rcb8`, READY, production alias `abvx.xyz`, exact merge SHA verified.
- Local release gate passed: content/ecosystem validation, lint, 104 sync tests, 23 vector-runtime tests, webpack fallback build, SEO QA and dependency audit. OS validation and 14 content-ops tests passed.
- Production SEO QA passed for 191 routes. Additional live browser checks at 390px/1440px confirmed cover proportions, three code blocks, the selected embed and upload metadata, one video card and text-only archive rows.
- All three installed sources match the approved packet SHA-256; both covers retain the supplied bytes. Public machine indexes include all three records.

Follow-up review found timezone-offset sorting and missing validation of direct video edits. Both were fixed in PR https://github.com/markoblogo/ABVXsite/pull/47 (source `8b174ec093b2ebbaa41516df394a6f7daa9d6d1b`, merge `6dee1f07543e35d8c55704714892c7298174f165`). The shared validator covers the loader, content checker and packet consumer; feed timestamps normalize to UTC without changing the supplied article date. The full local gate passed (105 sync tests), and default CI https://github.com/markoblogo/ABVXsite/actions/runs/38067030739 succeeded. Final deployment `dpl_DX9Z85FaRAGgVp66MbmZ6vALJjGP` is READY for that exact merge SHA with production alias `abvx.xyz`. Article content and public indexes remain unchanged by this follow-up.

## Search evidence and evaluation

On October 10 Search Console reported all three canonical URLs unknown to Google, then confirmed each indexing request was accepted into the priority crawl queue. After the Mac was unlocked, the agent-workflow article and SKYFLY watch-page requests were completed; the previously accepted funding request was not repeated. Indexed status remains UNCONFIRMED for all three pages. These confirmations concern page crawling, not separate video indexing.

Local confirmation screenshots: `abvx-index-request-funding.png`, `abvx-index-request-agents.png` and `abvx-index-request-video.png` in `/Users/antonbiletskiy-volokh/.codex/visualizations/2026/10/01/01a0f82d-6e6f-75f2-bdcd-759d246aab9d/`.

Sitemap processing remains a separate unresolved observation: Search Console's refreshed report says processing failed, last processed October 9, zero discovered pages. Public sitemap/discovery QA passed. This does not identify the cause of Google's processing failure or prove it repaired.

Impressions and clicks for this pilot are UNKNOWN until page-filtered Search Console data is available. Do not substitute whole-site analytics or fill missing observations with zeros.

Inspect each exact canonical URL after crawling. For comparable full-day windows, use October 11–November 7 and November 8–December 5 (28 days each), with the same search type and page filters. Record index status, queries, impressions and clicks for each page; keep watch-page/video indexing distinct. Review reader activity separately in Plausible. No recurring monitor was created.

## Subsequent content

Use [the ABVX publication fast path](../abvx-site-publishing.md) for intake and source-specific approval. Native articles and video companions use signed full-source packets and explicit mappings for every local image. Working Stories keep their existing consumer; books/editorial translations retain their project schemas and recipes. Batch relevant incoming links and regenerated indexes with each release. RSS discovery continues, but native commentary is selected and authored rather than automatically generating pages for the archive.
