# Book Production Director

Use this repo-local skill when a Book Factory mission moves from approved manuscript/source state into format production.

## Purpose

Prevent Codex from improvising a commercial book design or treating a technically valid PDF/EPUB as publication-ready.

## Required sequence

1. Confirm the BookSpec, manuscript state, source registry, and target formats.
2. Select an admitted production profile. If no admitted profile exists, mark the profile `PROOF_REQUIRED`.
3. Run the consolidated preflight contract before rendering a full artifact.
4. Keep technical QA and visual QA as separate gates.
5. Produce a recovery/production proof contact sheet before full production when a profile is new or previously failed.
6. Stop for human visual approval before admitting or reusing a new profile.
7. For paperback release candidates, generate TOC page numbers from final pagination, start every chapter on a new page, run page-balance and hyphenation QA, and render every page into one contact sheet.
8. Build Kindle Create input separately from print: semantic headings only, with no running heads, page numbers, forced print breaks, or print TOC pagination.

## Admitted-profile fast path

For a compatible book using an admitted profile, start from the existing profile, contracts and toolchain. Do not repeat donor audits, renderer research, typography/front-matter/TOC exploration or manual page patching. The bounded route is: approved BookSpec and manuscript -> admitted profile -> source/notes normalization -> approved cover direction -> representative proof only if needed -> human visual gate -> full build and automatic preflight -> full contact sheet -> human final gate -> publication artifacts.

## Fail-closed rules

- Do not treat `PDF_BUILT` as visual acceptance.
- Technical QA never substitutes for human visual approval.
- Do not leak proof labels, placeholder author identity, or production-state notes into reader-facing pages.
- Do not use fake TOCs for production acceptance.
- Do not use page-specific manual layout patches as a reusable production system.
- Do not create decorative diagrams just because a visual slot exists.
- Do not collapse Kindle, EPUB, paperback, hardcover, and cover QA into one generic manuscript check.
- Do not reopen renderer or design exploration for a compatible book using an admitted profile unless a concrete exception is detected.
- Do not expose internal source aliases, local paths, production-state language, or provisional copyright fields in reader-facing Notes/front matter.
- Interior visuals are opt-in. Zero visuals is a valid final design decision.

## Donor-first defaults

- Prefer Pandoc and the existing LaTeX toolchain for current local proofs.
- Use generated imagery only for bounded cover-concept exploration unless final art direction is approved.
- Treat Typst, Paged.js, EPUBCheck, Kindle Previewer, Canva, and KDP automation as donors to pilot only when the specific format/gate requires them.

## Output contract

A production-proof mission should leave:

- a machine-readable manifest;
- three cover concepts if cover direction is unresolved;
- representative interior proof pages;
- at least one useful visual only when justified;
- technical QA results;
- explicit human decision gates.
