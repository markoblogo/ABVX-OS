# BOOK-FACTORY-INDICES-006 — Production Proof

Status: `PRODUCTION_PROOF_READY_FOR_HUMAN`
Cost class: `NORMAL`

## 005 closeout

- 005 commit: `45aa1c4`
- 005 push: `origin/main`
- 006 began from a clean work line.

## Production copyedit

- V2 words before copyedit: `22,912`
- Production-edited manuscript words: `22,218`
- Net reduction: `694`
- Chapter 1 words after copyedit: `2,619`
- Chapter 2 words after copyedit: `2,857`

Scope:

- Chapter 1 repetition reduced around communicative seriousness, accessibility, contamination, proxy scope, methodology and burger-as-translation-device.
- Chapter 2 received smaller density cleanup around work-time comparison repetition.
- Chapters 3–8 were not broadly rewritten.

Verdict: `COMPACT_AND_RICH` preserved.

## Source registry / endnote seam

Created:

- `books/research/unusual-indices/source-registry.json`
- `books/research/unusual-indices/endnote-proof.json`

Model proved:

`canonical manuscript marker -> normalized source record -> reader-facing note -> format-specific links/backlinks`

Source marker audit:

- canonical manuscript source markers: `28`
- normalized source records: `28`
- unresolved consequential source markers: `0`

Generic aliases were either resolved to identifiable sources or marked as non-consequential context. Consequential claims no longer depend on unidentified “weird indicator overview” provenance.

## Tool / donor verdict

| Tool / pattern | Role | Classification | Why used | Custom glue | Maintenance burden |
| --- | --- | --- | --- | --- | --- |
| Pandoc | Markdown to PDF/EPUB compiler | `RUNTIME` | Installed, deterministic, handles EPUB and LaTeX PDF without custom engine | one bounded build script | low |
| XeLaTeX | 5×8 PDF proof renderer | `RUNTIME` | Existing local TeX runtime; supports page geometry, fonts, headers and links | small template | medium-low |
| Poppler tools | PDF render/text/font QA | `RUNTIME` | Existing `pdftoppm`, `pdfinfo`, `pdftotext`, `pdffonts` | none | low |
| Pillow | Proof image generation | `RUNTIME` | Existing Python image library; avoids rights-risk third-party graphics | original proof visuals/cover | low |
| Previous Book Factory proof | Production-pattern source | `PATTERN` | Retains the successful `pandoc + XeLaTeX` seam from the first booklet | adapted, not copied wholesale | low |

Kindle Previewer was not detected, so EPUB proof validation used Pandoc generation plus ZIP/OPF/XHTML structural inspection.

## Visual system proof

Created:

- `books/research/unusual-indices/visual-production-records.json`
- `books/research/unusual-indices/cover-direction-proof.json`

Representative visuals:

1. `visual-a-big-mac-schematic` — comparison/equivalence schematic for Chapter 1.
2. `visual-b-benchmark-lifecycle` — process/lifecycle schematic for Chapter 7.

Visual policy:

- black-and-white first
- grayscale-safe
- Kindle-safe
- original diagrams only
- no screenshots
- no trademark/product photography
- conceptual diagrams preferred over stale leaderboard values

## Cover direction proof

Created:

- `books/artifacts/unusual-indices-book/design-proof/cover/cover-proof-full.png`
- `books/artifacts/unusual-indices-book/design-proof/cover/cover-proof-amazon-thumbnail.png`
- `books/artifacts/unusual-indices-book/design-proof/cover/cover-proof-grayscale-thumbnail.png`

Result:

- object-led territory: burger + lipstick + underwear
- title dominates
- subtitle establishes economy/indicator category
- author name subordinate
- no 1D3X/POP/SPIKE branding
- no third-party product photography or trademark-heavy imagery

This is not final cover art.

## Paperback proof

Created:

- `books/artifacts/unusual-indices-book/design-proof/paperback/unusual-indices-production-proof-5x8.pdf`
- selected review pages:
  - `books/artifacts/unusual-indices-book/design-proof/paperback/review-page-01.png`
  - `books/artifacts/unusual-indices-book/design-proof/paperback/review-page-03.png`
  - `books/artifacts/unusual-indices-book/design-proof/paperback/review-page-04.png`
  - `books/artifacts/unusual-indices-book/design-proof/paperback/review-page-05.png`
  - `books/artifacts/unusual-indices-book/design-proof/paperback/review-page-07.png`
  - `books/artifacts/unusual-indices-book/design-proof/paperback/review-page-08.png`

Proof characteristics:

- page count: `8`
- page size: `360 x 576 pt` / `5×8 in`
- non-bleed
- searchable text
- page numbers
- running header
- chapter openings
- visual page
- notes page
- no page-specific manual patches

## Kindle / EPUB proof

Created:

- `books/artifacts/unusual-indices-book/design-proof/kindle/unusual-indices-kindle-proof.epub`

Proved:

- semantic headings
- TOC/nav artifact
- paragraph flow
- two images packaged into EPUB
- image alt text present
- internal note links/backlinks present
- no local filesystem paths
- no raw `[S:source-*]` markers

Limitation:

- Kindle Previewer was not available locally, so this is EPUB/Kindle-compatible proof, not Kindle Previewer acceptance.

## QA matrix

Source:

- `books/research/unusual-indices/production-proof-qa.json`

All recorded checks are `PASS`:

- manuscript cleanliness
- source resolution
- endnote generation
- internal marker removal
- Kindle TOC
- Kindle internal links
- Kindle image
- Kindle alt text
- paperback geometry
- paperback body type
- paperback chapter opening
- paperback notes
- visual grayscale
- visual provenance
- cover thumbnail
- text encoding
- no local path leakage

Build time:

- paperback PDF: approximately `2.19s`
- EPUB: approximately `0.11s`

Manual page-specific patches: `0`

## Human review package

Manifest:

- `books/artifacts/unusual-indices-book/design-proof/human-review-manifest.json`

The manifest points to:

- cover full-size proof
- cover thumbnail
- grayscale thumbnail
- paperback proof PDF
- selected paperback page PNGs
- Kindle/EPUB proof
- visual A
- visual B
- source registry
- endnote proof
- QA matrix

## Format state after 006

Expected conceptual state:

- Canonical manuscript: `PRODUCTION_EDITED`
- Kindle: `DESIGN_PROOF_READY`
- Paperback: `DESIGN_PROOF_READY`
- Endnotes: `PROOF_READY`
- Visual system: `PROOF_READY`
- Cover: `DIRECTION_PROOF_READY`
- Publication: `NOT_SUBMITTED`

Not set:

- `DESIGN_APPROVED`
- `FINAL_ARTIFACT_READY`
- `READY_FOR_SUBMISSION`
- `KDP_READY`

## Book Factory learning

`COMMERCIAL_NONFICTION_5X8_BW` is a candidate reusable profile, not yet final-approved.

Created:

- `books/design/profiles/commercial-nonfiction-5x8-bw.json`

Promotion condition:

- human accepts proof surfaces and 007 succeeds without new design exploration or page-specific patches.

## Next mission

If human approves this proof system:

`BOOK-FACTORY-INDICES-007 — Full Visual Production + Final Kindle/Paperback Build`

Expected 007 scope:

approved templates -> remaining visuals -> complete endnotes -> full EPUB -> full paperback PDF -> technical QA -> release candidates

No KDP action was performed.
