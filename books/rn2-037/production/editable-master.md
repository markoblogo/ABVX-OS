# RN2-037 editable production master

The paperback master is deterministic rather than tied to a proprietary layout file.

- Reader-facing source: `books/rn2-037/manuscript/ham-radio-technician-visual-cram-map.md`
- Canonical question data and crosswalk: `books/rn2-037/data/`
- Editable original diagrams: `books/rn2-037/visuals/svg/`
- Exact public-domain pool figures: `books/rn2-037/visuals/official-pool/`
- Layout/generation source: `tools/build_rn2_037_book.py`

Rebuild with the bundled workspace Python runtime, then run `tools/verify_rn2_037_release.py`. The build emits the 8 × 10 paperback PDF and semantic EPUB. The generator fixes the intentional 208-page pagination and bookmarks; edit source content or layout code, never the exported PDF.
