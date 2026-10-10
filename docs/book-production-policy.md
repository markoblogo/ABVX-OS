# Book production policy

## Mandatory table of contents

Every reader-facing ABVX book must include a usable table of contents before it can be classified as `LOCAL_PRODUCTION_PASS` or KDP-ready. `VISIBLE_CONTENTS_REQUIRED = TRUE` by default. Only a title-specific, recorded owner decision may disable it; silence, an unusual format, or navigation generated later does not count as a waiver.

- Print PDF: include a visible, normally typeset contents page with final page numbers. Bookmarks may supplement it but do not replace it.
- EPUB or Kindle: include an interactive EPUB navigation document whose links resolve to every primary chapter or section. The contents page must also appear in the reading order. Add a compatibility NCX when the toolchain supports it. Print page numbers must not appear in the reflowable contents.
- Multi-format releases: validate the print and ebook contents independently. A contents page in one format does not satisfy the other format's gate.
- QA: missing, non-resolving, hidden-only, placeholder, or stale contents are release-blocking failures.

Validate three separate facts. None substitutes for another:

1. `VISIBLE_CONTENTS`: a human-readable, reader-facing page exists in the book itself.
2. `CONTENTS_PARITY`: every entry, heading, and print page number matches the final built file and its actual destination.
3. `DIGITAL_NAVIGATION`: PDF bookmarks and/or Kindle navigation exist where supported; Kindle release checks this explicitly after conversion.

A local production build fails closed when either of the first two checks is missing or fails, regardless of a technical or navigation PASS. Paperback PDF bookmarks are supplemental. For the fixed-page Kindle workflow, the PDF source must already have visible Contents; Kindle Create cannot repair missing source content. This rule was reasserted after the Jekyll V1.1 PDF passed technical preflight without a Contents page and was caught by the owner during Kindle Create preparation (Jekyll V1.2 regression).

This rule applies prospectively to all Book Factory and autonomous KDP production paths, regardless of trim size, genre, renderer, or production profile.

## Owner-controlled creative artwork

ABVX book production does not autonomously generate final creative artwork.
Codex may specify and brief artwork, ingest and hash owner-supplied or
owner-approved sources, validate them, create deterministic technical
derivatives, typeset exact approved text, assemble print wraps against exact
platform templates, and run QA. Codex may not generate, redraw, reinterpret,
retouch, or replace final creative artwork. A missing art asset is a blocked
owner/external input, not permission to generate a substitute. This is a
permanent Book Factory production gate; technical derivatives must remain
separate from and traceable to their canonical source.

## Publishing gate model

Radar asks: **Is this opportunity worth attempting?** The Product Contract asks: **What exactly are we selling?** It must name the buyer, job, prior knowledge, confusion, paid value, advantage and intentional exclusions. Dataset-driven books must also declare `raw source -> transformation -> buyer value`.

For products whose value depends on visual design, comparison, workbook usability, unusual format, buyer-specific pedagogy or information density, a 6-16 page representative sample precedes full production. Its hardest ordinary experiences matter more than an attractive opener. The contract records whether a 5-15 minute human product-taste gate is required.

Production builds the product. Factual/source, language and editorial QA check correctness. The independent Product Quality Gate asks whether the result fits the buyer, delivers the job, adds paid value, transforms raw inputs, uses space intentionally, avoids template fatigue and makes every ordinary page earn its place. Technical preflight asks whether Amazon can render and manufacture the files correctly. KDP Previewer remains a separate external gate.

`KDP READY` requires explicit PASS states for market, product thesis, factual/source, editorial, product quality, technical, visible Contents, Contents parity, TOC/navigation, and applicable language QA; representative product must be PASS or explicitly WAIVED. KDP external preview may be PASS or HUMAN PENDING. Technical PASS can never overwrite Product Quality FAIL.

Page count is neither production cost nor buyer value. Evaluate value per reader task and track human attention as subject-matter hours, product-taste minutes, cover minutes, upload minutes and correction minutes.

## Sitelen pona vertical composition

Owner-approved production convention, recorded 2026-10-05 after correction of the Jekyll Toki Pona paperback spine. This is an ABVX layout rule, not a claim of a universal sitelen pona standard.

1. Read a vertical sequence from top to bottom. Keep each glyph upright in its original reading orientation. Never rotate a completed horizontal line, word, or name as a substitute for vertical typesetting.
2. Preserve the approved glyph sequence and semantic grouping. For names, use one vertical cartouche per original name cartouche, with its glyphs upright and ordered from top to bottom. Preserve separate cartouches and place surrounding words and separators in their original order.
3. Use exact approved glyph assets, an approved sitelen pona font, or the canonical internal title-page artwork. For raster references, extract individual glyph masks and keep their shapes, relative proportions, strokes, and internal marks; translate and scale proportionally only. A cartouche outline may be oriented or resized separately from its contents. Do not use AI imitation, redraw, stretch, mirror, or rotate glyphs to make them fit.
4. Check layout against the exact platform template: spine width, fold lines, bleed, live areas, and top/bottom and side clearances. Preserve the approved surrounding design and barcode instructions. Record native/effective resolution; an enlarged 300 dpi canvas does not establish 300 dpi source detail.
5. Before calling the composition locally approved, visually compare a large spine/detail preview against the canonical glyph source and the owner-approved vertical example. Verify upright orientation, every glyph and its order, cartouche grouping, complete strokes, no residual horizontal text, no clipping, and template clearance. Missing or wrong orientation/order/grouping is a blocking layout defect. PDF export and KDP Previewer remain separate checks.

Default scope: spines, narrow titles, vertical cover labels, and other deliberately vertical sitelen pona elements in Book Factory production. Use another orientation only when the owner explicitly approves it for the particular artifact.

Reference case: Jekyll Toki Pona; owner sketch `photo_2026-10-05 15.10.22.jpeg`. The rejected version rotated whole horizontal strings 90 degrees; the corrected version stacked upright source glyphs and vertical name cartouches.
