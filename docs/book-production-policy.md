# Book production policy

## Mandatory table of contents

Every reader-facing book must include a usable table of contents before it can be classified as production-ready or KDP-ready.

- Print PDF: include a visible, normally typeset contents page with final page numbers. Bookmarks may supplement it but do not replace it.
- EPUB or Kindle: include an interactive EPUB navigation document whose links resolve to every primary chapter or section. The contents page must also appear in the reading order. Add a compatibility NCX when the toolchain supports it. Print page numbers must not appear in the reflowable contents.
- Multi-format releases: validate the print and ebook contents independently. A contents page in one format does not satisfy the other format's gate.
- QA: missing, non-resolving, hidden-only, placeholder, or stale contents are release-blocking failures.

This rule applies prospectively to all Book Factory and autonomous KDP production paths, regardless of trim size, genre, renderer, or production profile.

## Publishing gate model

Radar asks: **Is this opportunity worth attempting?** The Product Contract asks: **What exactly are we selling?** It must name the buyer, job, prior knowledge, confusion, paid value, advantage and intentional exclusions. Dataset-driven books must also declare `raw source -> transformation -> buyer value`.

For products whose value depends on visual design, comparison, workbook usability, unusual format, buyer-specific pedagogy or information density, a 6-16 page representative sample precedes full production. Its hardest ordinary experiences matter more than an attractive opener. The contract records whether a 5-15 minute human product-taste gate is required.

Production builds the product. Factual/source, language and editorial QA check correctness. The independent Product Quality Gate asks whether the result fits the buyer, delivers the job, adds paid value, transforms raw inputs, uses space intentionally, avoids template fatigue and makes every ordinary page earn its place. Technical preflight asks whether Amazon can render and manufacture the files correctly. KDP Previewer remains a separate external gate.

`KDP READY` requires explicit PASS states for market, product thesis, factual/source, editorial, product quality, technical, TOC/navigation, and applicable language QA; representative product must be PASS or explicitly WAIVED. KDP external preview may be PASS or HUMAN PENDING. Technical PASS can never overwrite Product Quality FAIL.

Page count is neither production cost nor buyer value. Evaluate value per reader task and track human attention as subject-matter hours, product-taste minutes, cover minutes, upload minutes and correction minutes.
