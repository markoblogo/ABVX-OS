# ABVX Book Factory Validation Stack V1

Validation gates are complementary; passing one is not evidence that another passed.

| Layer | Tool / current state | Gate |
|---|---|---|
| Manuscript/source | Existing ABVX editorial, source, claim, and structural contracts | Source boundaries, claims, references, glossary/anchor integrity; human editorial acceptance |
| Build reproducibility | Existing Pandoc + XeLaTeX pipeline | Record inputs/tool versions; verify expected outputs and no unexpected source changes |
| EPUB conformance | **EPUBCheck proposed; not installed/validated here** | Run pinned tool on final EPUB; preserve report; resolve errors and adjudicate warnings |
| EPUB accessibility | **DAISY Ace proposed; not installed/validated here** | Report findings, inspect manually, check metadata/reading order/alt text/semantics; human sign-off |
| EPUB rendering | Existing readers/visual review; automate only if environment supports it | Inspect representative front matter, chapter starts, anchors, glossary, images, special glyphs, and navigation |
| Print PDF structure | Existing qpdf, Ghostscript, Poppler available; factory gates remain authoritative | Open/parse, page count/size, fonts/images, trim/bleed/margins, blank pages, embedded fonts; KDP template constraints |
| Print visual QA | Existing render-to-images workflow | Inspect full document and critical pages at readable scale; retain Previewer evidence |
| KDP platform preview | Manual KDP Previewer | Separate human gate; local PDF checks cannot substitute |
| Listing/publication | Manual/authenticated KDP and public listing verification | Upload, preview approval, review, and public availability remain distinct states |

## Pilot record

Proposed fixture: `books/artifacts/unusual-indices-book/design-proof/kindle/unusual-indices-kindle-proof.epub` (copy before any mutation). Attempt blocked: this host lacks a usable Java runtime and network DNS could not resolve the official GitHub release. Therefore no EPUBCheck or Ace verdict exists. No other artifact was changed.

## Install policy

Use official signed/tagged releases and isolated temporary storage; pin versions and checksums; no project dependency until the tool has demonstrated stable output on valid and intentionally-invalid fixtures. Preserve raw diagnostics. Avoid adding redundant PDF validators without a demonstrated blind spot in current qpdf/Ghostscript/Poppler checks.
