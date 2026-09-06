# Book production policy

## Mandatory table of contents

Every reader-facing book must include a usable table of contents before it can be classified as production-ready or KDP-ready.

- Print PDF: include a visible, normally typeset contents page with final page numbers. Bookmarks may supplement it but do not replace it.
- EPUB or Kindle: include an interactive EPUB navigation document whose links resolve to every primary chapter or section. The contents page must also appear in the reading order. Add a compatibility NCX when the toolchain supports it. Print page numbers must not appear in the reflowable contents.
- Multi-format releases: validate the print and ebook contents independently. A contents page in one format does not satisfy the other format's gate.
- QA: missing, non-resolving, hidden-only, placeholder, or stale contents are release-blocking failures.

This rule applies prospectively to all Book Factory and autonomous KDP production paths, regardless of trim size, genre, renderer, or production profile.
