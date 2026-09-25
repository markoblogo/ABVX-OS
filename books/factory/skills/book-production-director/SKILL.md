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

When an interior or promotional visual is justified, load [Publishing Visual Explainer](../publishing-visual-explainer/SKILL.md) and approve one representative visual before producing a set.

## Fiction and publication gates

- Keep `STRUCTURE_COMPLETE` separate from `PRODUCT_COMPLETE`; a coherent short structural draft is not automatically a commercially complete manuscript. Scan for development labels, placeholders, duplicate alternate scenes, and test scaffolding before editorial acceptance.
- Keep one machine-readable manifest for manuscript, world bible, continuity, illustration placement, and production artifacts. Mark older working files `SUPERSEDED` or `PROTOTYPE`; retain history. A locked manuscript is `TEXT_LOCK` and the sole prose source for production.
- Illustration assets may be explored before text lock; finalize placement only after structural/editorial lock. Preserve a Pictiq source→English Composer input→Composer output→final composite chain, with versions and hashes.
- Before Amazon packaging, record provenance per visual asset using `books/factory/contracts/asset-provenance-v1.schema.json`. Unknown origin is `UNRESOLVED`, never inferred.
- Print preflight must inspect footer/attribution against the live-area boundary. Keep barcode zones background-only unless using a real publisher barcode. Build wraps from the actual KDP template after trim, paper, ink, and final page count are fixed; check spine constraints.
- Treat effective resolution below 300 DPI as a human visual/print-risk review, not automatic rejection or upscaling. `EPUB_VALID` does not imply `KINDLE_RENDER_VERIFIED`; complete target Kindle/KDP preview before release.
- After `TEXT_LOCKED`, prose edits are limited to a typo, demonstrated factual error, or production-formatting defect; record the reason and rerun affected checks. Freeze launch metadata after product/text lock and capture D0, D7, D14, and D30 observations.

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
