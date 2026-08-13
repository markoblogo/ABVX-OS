# BOOK-FACTORY-INDICES-008 — Final production and Amazon package

## Outcome

- `PAPERBACK_INTERIOR_RC_READY`
- `KINDLE_CREATE_INPUT_READY`
- `AMAZON_METADATA_PACKAGE_READY`
- `PROFILE_TECHNICALLY_READY_FOR_HUMAN_ADMISSION`
- Publication remains human-gated.

## Prior uncommitted work boundary

Reusable DESIGN-001 work is preserved: production skill, candidate profile, preflight, visual QA contract, failure map, known-profile playbook, source registry, endnote seam, and production lessons.

Artifact disposition is explicit in the final manifest:

- `design-proof/`: rejected historical evidence, not canonical;
- `recovery-proof/`: system-recovery evidence, not final output;
- `production-build/`: superseded except the approved Cover A front artifact;
- `final-008/`: canonical release-candidate set.

No destructive cleanup or automatic commit was performed.

## Final content and format

- Canonical manuscript: 21,645 words.
- Interior visuals: 0. All reader-facing visual markers and the Big Mac chart/caption were removed; underlying research evidence remains internal.
- Paperback: 5×8 inches, black-and-white, 80 pages, searchable text, embedded fonts.
- Every chapter starts on a new page.
- Generated paperback TOC contains final page numbers; no manual TOC numbers.
- Kindle Create input: semantic DOCX with no running heads, page numbers, print TOC pagination, or forced print layout.
- Copyright page contains only known publication facts.
- Reader Notes use identified public sources with linked titles; internal aliases, local paths, and raw long URLs are absent.

## Pagination and typography QA

- Blank pages: 0.
- Suspicious pre-chapter pages: 0.
- Isolated headings: 0.
- Low-occupancy pages: 0 under the final heuristic.
- Heading hyphenation failures: 0.
- Body line-end hyphenation: 167 occurrences, 7.44 per 1,000 extracted words; threshold 12.0.
- Full contact sheet: all 80 pages rendered.

Page balance uses one reusable chapter-tail rule: a bounded closing paragraph cluster is kept together before each chapter transition. It does not contain slug/page-specific adjustments.

## Amazon/KDP package

The machine-readable package includes title metadata, plain and KDP-safe HTML descriptions, seven keyword fields with intent/rationale, category recommendations, pricing, AI disclosure guidance, rights checklist, artifact references, and deferred wrap/submission state.

Current official KDP rules were checked for description HTML, keywords, categories, pricing/royalties, AI disclosure, Kindle source quality, and print specifications. Comparable positioning used current publisher listings for *How to Lie with Statistics* (128 pages, £12.99), *The Undercover Economist* (288 pages, $19), and *The Data Detective* (336 pages, $20).

Recommendation:

- Kindle launch: $2.99
- Kindle normal: $5.99
- Paperback: $11.99

AI disclosure recommendation:

- text: disclose as AI-generated;
- cover: disclose as AI-generated;
- interior images: none;
- translation: none.

## Remaining human actions

1. Review the 80-page contact sheet and final paperback PDF; approve or request one bounded correction.
2. Open the DOCX in Kindle Create and perform normal Kindle preview/preparation.
3. Confirm manuscript rights and commercial-use provenance for the generated Cover A artwork.
4. Build the paperback wrap in Canva using final KDP-calculator dimensions, then submit both formats manually.

`PAPERBACK_WRAP_COVER_PRODUCTION` and `KDP_SUBMISSION_AUTOMATION` remain separate deferred capabilities.
