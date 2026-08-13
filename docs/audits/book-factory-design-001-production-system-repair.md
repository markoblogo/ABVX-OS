# BOOK-FACTORY-DESIGN-001 — Production System Repair

## Status

`STOP_FOR_HUMAN`

Current unusual-indices state:

- `MANUSCRIPT_APPROVED`
- `FACTS_APPROVED`
- `SOURCE_SYSTEM_APPROVED`
- `PRODUCTION_DESIGN_REJECTED`
- `PRODUCTION_RECOVERY_PROOF_READY_FOR_HUMAN`
- `WAITING_FOR_HUMAN`

## What happened in BOOK-FACTORY-001 through 006

The Book Factory successfully moved from donor audit and intake through BookSpec, manuscript generation, structural revision, source normalization, and technical proof generation. That sequence produced useful durable components:

- approved compact commercial package;
- approved manuscript direction and V2 manuscript;
- normalized source registry;
- source/endnote seam;
- format-artifact boundaries;
- PDF/EPUB proof build seams;
- QA records.

The 006 production proof was technically successful but visually rejected. That rejection is binding. It must not be defended as nearly acceptable, patched page-by-page, or admitted as a reusable profile.

## Retrospective failure summary

Primary failure:

Technical artifact production was allowed to get ahead of commercial visual direction.

Repeated avoidable cost came from:

1. reopening donor/tooling questions after the manuscript/source problem was already solved;
2. combining technical QA and visual QA into one implied acceptance path;
3. using primitive generated design elements as if they were cover or interior art direction;
4. producing generic visuals instead of source-backed explanatory visuals;
5. debugging renderer/layout details before an approved visual profile existed.

## Failure-to-rule map

Canonical machine-readable map:

`books/factory/lessons/indices-production-failure-map.json`

Core rules:

- technical PASS never implies visual PASS;
- a new commercial profile starts as `PROOF_REQUIRED`;
- cover direction requires multiple concepts and thumbnail comparison;
- visuals must be `REQUIRED` or `USEFUL`, not decorative filler;
- reader-facing proofs must not expose process labels, fake TOCs, or placeholder identity;
- page-specific manual fixes are not reusable production infrastructure.

## Capability map

Canonical machine-readable map:

`books/factory/capability-map.json`

Summary:

- `PROVED_ONCE`: research, positioning, BookSpec, manuscript generation, structural editing, fact verification, source normalization, deterministic data visualization, post-publish verification.
- `PARTIAL`: endnotes, cover art direction, cover production, interior design, typesetting, EPUB generation, print PDF generation.
- `MISSING`: editorial illustration, KDP preflight.
- `DEFERRED`: supervised KDP submission.

## Donor-first reassessment

Observed local tools:

- Pandoc: available; useful for document conversion and EPUB/PDF pipeline seams.
- XeLaTeX: available; useful for current proof rendering, but not a visual design system by itself.
- Pillow: available; useful for deterministic contact sheets and data visuals.
- PDF tooling: `pdfinfo`, `pdffonts`, `pdftotext`, `pdftoppm` available; useful for technical QA.

Not locally available in this environment:

- Typst
- WeasyPrint
- Chromium/Playwright
- EPUBCheck
- Calibre / `ebook-convert`

Current donor decisions:

- Pandoc + XeLaTeX remain the lowest-friction local proof route.
- Image generation is acceptable for bounded cover-concept exploration, not final unsupervised cover production.
- EPUBCheck and Kindle Previewer remain future format-QA donors.
- Typst and Paged.js are future production-profile candidates, not requirements for this repair.
- Auto-KDP/browser automation remains supervised and out of scope.

External references inspected:

- Pandoc manual: `https://pandoc.org/MANUAL.html`
- Typst documentation: `https://typst.app/docs/tutorial/`
- Paged.js overview: `https://pagedjs.org/en/about/`
- EPUBCheck: `https://www.w3.org/publishing/epubcheck/`

## Profile boundary

Profile candidate:

`books/design/profiles/commercial-nonfiction-5x8-bw.json`

Status:

`PROOF_REQUIRED`

The profile is not admitted. It may be used only for proof/recovery work until human visual approval and a full build prove that it can produce publication-grade output without manual page-specific fixes.

## Consolidated contracts

Preflight contract:

`books/factory/contracts/commercial-nonfiction-preflight.json`

Visual QA contract:

`books/factory/contracts/visual-qa-contract.json`

The contracts separate:

- manuscript/source readiness;
- format-specific artifact readiness;
- cover visual direction;
- interior visual direction;
- technical QA;
- human visual acceptance.

## Skill and playbook

Repo-local production skill:

`books/factory/skills/book-production-director/SKILL.md`

Operational playbook:

`playbooks/book-factory.known-profile-commercial-nonfiction.json`

Design choice:

- Skill is used for the agent behavior boundary: avoid improvising design and stop at visual gates.
- Playbook is used for the deterministic known-profile path.
- Profile is used for reusable render/design tokens.

No second skill was created. The task only justified one production-boundary skill.

## Recovery proof

Recovery proof manifest:

`books/artifacts/unusual-indices-book/recovery-proof/human-review-manifest.json`

Contact sheet:

`books/artifacts/unusual-indices-book/recovery-proof/human-review-contact-sheet.png`

Three cover concepts:

- `books/artifacts/unusual-indices-book/recovery-proof/cover/cover-concept-a.png`
- `books/artifacts/unusual-indices-book/recovery-proof/cover/cover-concept-b.png`
- `books/artifacts/unusual-indices-book/recovery-proof/cover/cover-concept-c.png`

Interior proof:

`books/artifacts/unusual-indices-book/recovery-proof/paperback/unusual-indices-recovery-proof-5x8.pdf`

Representative surfaces:

- title page;
- copyright page;
- complete eight-chapter TOC;
- chapter opener;
- normal body page;
- dense body page;
- useful visual page;
- notes page.

Useful visual:

`books/artifacts/unusual-indices-book/recovery-proof/visuals/big-mac-selected-economies.png`

Visual source record:

`books/research/unusual-indices/recovery-visual-record.json`

The visual uses The Economist Big Mac dataset and renders selected economy prices as an original, grayscale-safe data visualization.

## Recovery proof QA

QA record:

`books/research/unusual-indices/recovery-proof-qa.json`

Observed PASS checks:

- title page has no visible running header or page number;
- author identity is correct;
- TOC contains the eight approved chapters;
- reader-facing proof has no production-proof residue;
- paperback geometry is 5×8;
- text encoding is readable;
- source markers are removed from rendered prose;
- notes page is present;
- data visual has provenance;
- three cover directions exist;
- contact sheet exists;
- no manual page patches were used;
- fonts were observed.

## Future compatible-book target

A compatible future commercial nonfiction book should not rerun the full 001–006 reasoning loop.

Target path:

1. approved BookSpec and manuscript;
2. closed P0/P1 facts;
3. normalized source registry;
4. admitted or proof-required profile;
5. one cover-direction gate;
6. one interior/visual gate;
7. deterministic full production;
8. format-specific QA;
9. supervised external publication gate.

Target reductions:

- no broad donor audit unless a format blocker appears;
- no repeated manuscript architecture debate after approval;
- no renderer exploration for an admitted profile;
- no fake proof surfaces;
- no manual page-specific layout fixes.

## Human decisions required

1. Select one cover direction, request revisions, or reject all three.
2. Approve or reject the recovery interior profile.
3. Approve or reject the Big Mac data-visual style as a useful visual direction.
4. Decide whether to proceed to a full production build mission.

Until those decisions are made, the project remains `WAITING_FOR_HUMAN`.
