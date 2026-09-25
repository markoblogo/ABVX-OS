# Jekyll & Hyde Toki Pona Pre-Production V1

**Project:** *The Strange Case of Dr Jekyll and Mr Hyde — Toki Pona Edition with Sitelen Pona*  
**Branch:** validated / partially validated Toki Pona product system; not RN7  
**Decision:** **MODIFY_PIPELINE_THEN_GO**  
**Scope:** pre-production gate only. No complete translation, final interior, cover, KDP package, listing, or upload was made.

## Decision

The candidate remains the right next narrative-fiction experiment. The named Project Gutenberg source is usable subject to territory and release checks; no complete competing Toki Pona edition surfaced in the targeted recheck; the layered reading object and black-ink paperback economics are viable.

Full production must not start on the present factory path. The existing translator contract is a short-form lexical tool: it caps a request at 500 characters, accepts only frozen lowercase dictionary words, has no proper-name lane, and the tested deployed endpoint returned `NOT_FOUND`. Narrative fiction requires stable names, chunk identity, section-aware spoiler controls, and a recoverable batch run. These are bounded pipeline changes, not a reason to discard the candidate.

The existing catalogue’s live sales are relevant product evidence: they show that transformed Toki Pona classics can be sold from this account. They do not establish that a newly generated narrative translation has passed this book’s literary, technical, or current-release-policy checks.

## Existing Factory

The reusable system is distributed rather than a single “book factory” executable.

- **Toki Pona Toolkit:** source-language-to-Toki-Pona web/API translation contract, with a frozen canonical lexical profile.
- **sitelen-emoji:** versioned Toki Pona mapping and deterministic helpers.
- **sitelen-layer-plugin / sitelen-layer-static:** a display layer and an OFL sitelen pona font asset. It renders Toki Pona; it is not a translator.
- **toki-pona-formatting-pass:** read-only ODT/PDF mechanical audit for layered manuscripts, glossary anchors, canonical forms, fonts, and extraction anomalies.
- **Odyssey ODT/LibreOffice material:** an established human-operated English / Latin-script Toki Pona / sitelen workflow with KDP layout variants.
- **ABVX book tooling:** generic PDF/EPUB and quality checks, but no dedicated Toki Pona narrative source-to-book runner.

### Actual current sequence

`Project Gutenberg source → manual/one-off normalization → chapter or paragraph selection → short API/model translation → manual layered manuscript assembly → font application / sitelen rendering → LibreOffice or LaTeX layout → PDF inspection → manual KDP/Kindle review`

### Stage status

- **Automated:** source retrieval, checksum, raw text normalization, frozen-profile lookup, basic sitelen font rendering, and mechanical ODT/PDF extraction checks.
- **Semi-automated:** chapter segmentation, profile validation, PDF rendering, layout compilation, and existing ODT consistency audit.
- **Manual:** semantic/entity ledger, literary rendering, proper-name choices, paragraph correspondence, spoiler judgement, production pagination, KDP Previewer, and final release decisions.
- **Missing:** a book-scale batch orchestrator; stable source/block IDs; proper-name handling; paragraph alignment validation; narrative knowledge/spoiler checks; source/output completeness diff; reproducible EPUB pipeline for the three-layer architecture.

## Reusable Components

Reusable without modification: Project Gutenberg ingestion conventions, SHA-256 provenance capture, the frozen lexical profile, the OFL sitelen font, existing PDF rendering/visual inspection, and the ODT editorial-audit principles.

Reusable with a thin adapter: source normalization, canonical section segmentation, entity-ledger JSON, profile validation, three-layer block records, and black-ink 6 × 9 layout tokens.

Not reusable as-is: the 500-character web translation endpoint, a lexical contract with no proper names, and any claim that a fixed three-column page automatically becomes a usable Kindle edition.

## Previous Production Lessons

The retained formatting workflow establishes several constraints that Jekyll must keep:

- source prose, readable Latin Toki Pona, and sitelen pona must be kept as distinct layers;
- Latin and sitelen copies must carry the same normalized Toki Pona text; PDF extraction artefacts are not source typos;
- font changes need span-level inspection; a broad font substitution can contaminate neighbouring prose;
- glossary/name anchors must not silently deduplicate the readable and rendered forms;
- mechanical audit can find consistency and layout anomalies but cannot certify translation quality.

Jekyll adds risks that philosophy and aphorism collections do not: a focal witness can be wrong, documents can make claims rather than state facts, and explanation can reveal the story too early.

## Canonical Source

- **Title:** *The Strange Case of Dr. Jekyll and Mr. Hyde*
- **Author:** Robert Louis Stevenson
- **Record:** Project Gutenberg eBook #42
- **Record URL:** `https://www.gutenberg.org/ebooks/42`
- **Selected source:** UTF-8 plain text, `https://www.gutenberg.org/files/42/42-0.txt`
- **Retrieval date:** 2026-09-21
- **Raw file SHA-256:** `c77c386664a308ff0e0a7ce33714da0856facd6e183b7bc6ae82c1cbb137120b`
- **Normalized source SHA-256:** `dd95f97826b4688f1e5c66534bc69523c24dc651605945533add1bab17a73984`
- **Normalized source length:** 25,622 words

The normalizer starts at the first canonical section, removes duplicated title/contents and Project Gutenberg boilerplate, and preserves the ten-section text. It does not ingest introductions, annotations, later covers, or illustrations. The manifest and normalizer live with the isolated sample artifacts.

## Rights / Territory Gate

**RIGHTS_GATE = CONDITIONAL**

The source record identifies the English text as public domain in the USA and states that readers outside the United States must check their local law. The 1886 original supports use of this named English source; it does not clear another translation, a modern edited edition, artwork, cover, or illustration.

Conditions before release:

1. Recheck intended KDP territories immediately before publication; do not claim worldwide clearance now.
2. Use only the checksum-identified English source and original or separately licensed visual assets.
3. Keep the font’s SIL Open Font License notice/provenance with the production record; documents created with the font are permitted by that license.
4. Meet KDP’s then-current public-domain differentiation, contributor-credit, disclosure, and content rules. KDP currently treats an original translation as a possible differentiated public-domain edition and requires original author/translator contributor information; formatting alone is not differentiation. [KDP public-domain policy](https://kdp.amazon.com/en_US/help/topic/G200743940)

## Competition Recheck

**Status: NO_DISCOVERABLE_COMPLETE_EDITION — low-to-medium confidence.**

Targeted searches across web, Project Gutenberg, lipu/community-oriented results, GitHub-oriented results, and Amazon-oriented query language found no discoverable complete Toki Pona edition of *Jekyll & Hyde*. Search results included unrelated “Jekyll” software uses and general Toki Pona material, not a competing translation. This is an absence observation, not proof that an unindexed community rendering does not exist.

If a complete version is later found, compare source completeness, language quality, sitelen treatment, name strategy, physical-book usefulness, and publication date before deciding whether this edition remains differentiated.

## Product Definition

The product is a complete, traceable, three-layer reading edition:

`English source block → readable Latin-script Toki Pona → sitelen pona rendering of that same Toki Pona`

Paperback is the primary object. The reader aid should be short and non-interpretive: section navigation, a character/name guide that does not reveal relationships, a recurring-anchor guide, and source/provenance note. No explanatory matter may reveal the final relation, later letters, chemical outcome, or a character’s later knowledge.

The product is not a generic public-domain reprint, a Toki Pona glossary, or a sitelen illustration book.

## Narrative Translation Risks

- **Identity:** Jekyll and Hyde must be separate entities until the source changes the reader’s knowledge.
- **Focal knowledge:** narrator description, Utterson’s inference, Lanyon’s opinion, Poole’s testimony, and a document’s claim must remain distinct.
- **Legal logic:** the will’s death, disappearance, duration, and succession conditions cannot be compressed into an unconditional handover.
- **Document logic:** letters and sealed statements must retain writer, recipient, opening condition, and evidential status.
- **Dialogue:** speaker, hesitation, denial, social status, and question/answer relationship are plot-bearing.
- **Register:** Victorian science, medicine, law, and reputation must be simplified without inventing modern diagnoses or legal conclusions.
- **Objects/places:** door, key, laboratory, theatre, cabinet, powder, draught, and writing must remain reliably distinct.
- **Violence and moral ambiguity:** do not euphemise away causal responsibility or turn an observer’s disgust into narrator fact.

## Entity / Semantic Ledger

The structured ledger is [JEKYLL_ENTITY_LEDGER_V1.json](JEKYLL_ENTITY_LEDGER_V1.json). It contains 24 controlled people, places, objects, documents, actions, identity terms, medical terms, and legal/social terms. Nine records are classified critical for spoiler handling.

The ledger’s core rule is deliberately conservative: a name is not a lexical gloss, and a role is not a substitute for a name. `jan Jekil` and `jan Hata` must stay visibly distinct without encoding their eventual relation.

## Proper-Name Strategy

### Proposed policy for evaluation, not final approval

- English source retains canonical English forms.
- Latin Toki Pona uses `jan` plus one fixed phonetic form per character.
- Sitelen uses either a fixed name cartouche or an explicitly designed Latin-name fallback within the sitelen line.
- A role phrase may support recognition but never replace the proper name where identity matters.
- The ledger records the one approved form and each spelling/visual form is linted against it.

### Result of the sample

Core sitelen glyphs rendered in the existing OFL font. Proper names did not have a supported canonical-profile lane, so the sample uses a conspicuous Latin fallback. This is readable, but it is not a finished strategy. The required solution is a stable, auditable name-token extension plus a printed visual rule; do not rely on ad hoc font switching chapter by chapter.

## Representative Sample

**Selected source volume:** 1,785 words in the source-sample artifact (including headings); source portions from Chapters II, VI, and VIII. It includes normal narration, dialogue, Utterson, Jekyll, Hyde, Lanyon, Poole, legal/document structure, laboratory/cabinet vocabulary, uncertain inference, a letter, fear, and action-oriented urgency. The paired Toki Pona draft artifact is 1,624 words including headings and translator notes.

It avoids the final confession and therefore tests difficult mechanics without unnecessarily exposing the final revelation in a development artifact.

Artifacts are isolated in [jekyll-toki-pona-preproduction-v1](artifacts/jekyll-toki-pona-preproduction-v1/): exact source sample, model-draft Toki Pona sample, sitelen input, three-page interior PDF, source manifest/normalizer, and QA reports.

## Translation Sample Assessment

**Assessment: WORKABLE, requiring rewrite and human literary review.**

The sample demonstrates that the three layers can carry narrator, dialogue, document, uncertainty, and names without automatically revealing the central relation. The first model draft also exposed recurring editorial failures: a legal condition became too unconditional; a character’s judgement became narrator fact; “safe” was rendered as morally “okay”; confidence/trust did not survive cleanly; and the initial frozen profile rejected unapproved vocabulary and all names.

The model editorial pass corrected the obvious profile and semantic issues and records the remaining judgement calls. It is not human linguistic certification. See [model editorial review](artifacts/jekyll-toki-pona-preproduction-v1/qa/model-editorial-review.md).

## Sitelen Pona Assessment

**Assessment: WORKABLE.**

The existing `sitelen-seli-kiwen-asuki` font rendered core Toki Pona as visible glyphs in a 6 × 9 XeLaTeX test. The font is licensed under SIL OFL 1.1. The PDF’s text extraction does not semantically recover the sitelen layer, which is expected for this font/rendering route and must not be treated as manuscript corruption.

The unresolved issue is not basic glyph availability; it is names. A book-scale name fallback/cartouche rule must be fixed before translation batching.

## Layout Assessment

**Assessment: WORKABLE for paperback, not yet validated for full narrative density.**

The sample tested sequential English, Latin Toki Pona, then sitelen blocks on 6 × 9 pages. The first compile created six over/underfull warnings; a ragged-right sitelen block eliminated them. The final test PDF rendered visually without clipping. Its lower-page whitespace is acceptable for a test but would be too expensive if reproduced mechanically through 25,000 source words.

The full layout must use paragraph/block alignment rather than line-by-line parallelism. Narrative paragraphs have unequal compression across layers. The sample therefore supports a constrained sequential spread pattern, not a three-column layout.

## Paperback Model

**Recommended primary format:** 6 × 9 in, black ink, white or cream paper, no interior colour by default.

The source is 25,622 normalized English words. Sample density and three-layer sequential layout imply **approximately 180–230 paperback pages**, including modest front/back matter. This range must be recalculated from a full, aligned block ledger; it is not a page-count promise.

For Amazon.com regular-trim black-ink paperbacks above 110 pages, current KDP guidance lists a US$1.00 fixed cost plus US$0.012 per page. That models roughly US$3.16 at 180 pages and US$3.76 at 230 pages. Standard colour would be roughly US$5.59–6.87 in the same range and offers no demonstrated reader value. [KDP printing-cost policy](https://kdp.amazon.com/en_US/help/topic/G201834340)

Result: black ink is commercially reasonable for a small-market evergreen object; colour is not justified. Price must be set only after final page count and local marketplace calculator output. A likely commercially viable paperback band is US$14.99–17.99, subject to the final calculator and catalogue positioning.

## Kindle Feasibility

**Recommended direction: REFLOWABLE, conditional on a dedicated proof.**

For Kindle, serialise each source block as English → Latin Toki Pona → accessible labelled sitelen representation or optional rendering. Do not attempt print-page alignment or three columns. That route can preserve navigation, resizing, and reading continuity.

Do **not** use Print Replica merely to preserve the paperback page. KDP says it should be used only where exact layout is essential and is not compatible with Kindle e-readers or accessibility features. [KDP format comparison](https://kdp.amazon.com/en_US/help/topic/G42HENP2VHSN8VW8)

No EPUB sample was generated: the current three-layer source is insufficient to certify a reflowable reading order, font embedding, selectable proper names, accessibility semantics, and device behaviour. If the reflowable proof fails, the correct outcome is **NO KINDLE**, not a forced print replica.

## Automation Audit

- Source retrieval and SHA capture: **AUTOMATED SUCCESS**.
- Gutenberg boilerplate removal: **AUTOMATED SUCCESS** via a bounded normalizer.
- Section detection: **AUTOMATED WITH MANUAL REVIEW**; contents duplicates must not become chapters.
- Entity / semantic ledger: **MANUAL BECAUSE PIPELINE IS MISSING**.
- Translation API: **FAILED**; deployed endpoint returned `NOT_FOUND`.
- Translation contract: **FAILED FOR NARRATIVE USE**; 500-character limit and lexical-only response cannot preserve names or block identity.
- Sitelen glyph rendering: **AUTOMATED WITH MANUAL REVIEW**.
- Proper-name rendering: **MANUAL BECAUSE PIPELINE IS MISSING**.
- Layout compilation and visual PDF check: **AUTOMATED WITH MANUAL REVIEW**.
- Source/output completeness and block alignment: **MISSING**.
- EPUB validation: **NOT RUN / NOT YET JUSTIFIED**.

## QA Results

The machine-readable result is [sample-qa-results.json](artifacts/jekyll-toki-pona-preproduction-v1/qa/sample-qa-results.json).

- Source completeness and boilerplate removal: pass.
- Sample selection: pass; it is documented and avoids the final revelation.
- Name consistency: fail until a name extension exists.
- Toki Pona literary quality and semantic drift: human QA required.
- Spoiler preservation: partial pass; the selected text is safe, but the future full-book checker is missing.
- Sitelen/font: pass with limitation; names are a fallback, PDF extraction is not semantic evidence.
- Revised PDF layout: pass for the three-page test only.
- EPUB: not run.

## Human Gates

Keep human attention narrowly focused on what automation cannot verify:

1. approve name forms and their sitelen representation;
2. review each identity-sensitive / document-sensitive passage for reader knowledge and ambiguity;
3. review the Toki Pona literary rendering, voice, dialogue, and semantic compression;
4. approve the short non-spoiler character/anchor guide;
5. recheck source/territory/asset/KDP conditions immediately before release;
6. approve final cover, price, and KDP Previewer results.

No human gate is needed for source hashing, boilerplate removal, page-overflow scanning, profile validation, duplicate/missing-block checks, or visual-contact-sheet generation once those adapters exist.

## Factory Improvements

### Must fix before full Jekyll

1. Build a local batch runner that divides normalized source into stable paragraph/block IDs, retries safely, and stores source → output correspondence.
2. Add a proper-name extension lane: approved names are exempt from the frozen lexical response validator but remain allowlisted, case-preserving, and visual-width checked.
3. Add ledger-driven checks for names, documents, section numbers, and source/output missing or duplicated blocks.
4. Restore or explicitly retire the deployed translation endpoint; full production must use a tested local/provider path rather than an assumed URL.
5. Add a minimal narrative spoiler policy: per-section reader-knowledge constraints and a review queue for identity, letter, and confession terms.

### Should fix during Jekyll

- generate sequential three-layer layout from the block ledger;
- add a sitelen name-fallback/cartouche component;
- run layout overflow and font-embedding checks on every build;
- create a reflowable EPUB proof with accessible reading order and TOC.

### Reusable future improvement

- source-normalisation adapters keyed by source family;
- entity-ledger extraction proposals with mandatory human acceptance;
- comparison of full-book source/output IDs, word ratios, QA findings, page counts, and human-review minutes across Odyssey and later books.

### Nice to have

- a visual entity map or restrained chapter motifs; neither is required for this text-first edition.

## Production Economics

Machine work is low-cost once the missing batch/name/alignment steps exist: 25,622 source words is a compact narrative test, and black-ink print cost remains viable at the modeled page range. The meaningful cost driver is literary and identity-sensitive review, not printing.

Expected complexity after the fixes is **MEDIUM**: roughly a normal narrative source run plus a concentrated final review of all ledger-critical blocks. Do not treat this as a zero-human automated conversion. The current system has live catalogue evidence for small evergreen demand, but no causally reliable sales forecast for this title.

## Blocking Issues

1. no tested book-scale translation path;
2. no supported proper-name strategy in the translator/profile/render path;
3. no source/output block-completeness or narrative spoiler checker;
4. no reflowable Kindle proof.

These are finite implementation and verification requirements. Rights, competition, basic sitelen rendering, sample paperback layout, and black-ink economics do not block the candidate.

## Recommendation

**MODIFY_PIPELINE_THEN_GO.** Implement only the five “must fix before full Jekyll” items, rerun this exact representative sample through the repaired path, and require the revised QA to pass before authorising complete translation. Do not start the complete book or another candidate in this gate.
