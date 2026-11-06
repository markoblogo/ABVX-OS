# ABVX Book-Type and Format Modules V1

Design only; five proposed book-type modules, four format adapters and one optional sitelen render adapter. Modules add genuinely unique validation/decision logic; configurations choose values. Existing books are not reclassified or migrated by this file.

## Content/module decision

| Candidate | Decision and adds | Reuses core | Unique validators / owner gates |
|---|---|---|---|
| ORIGINAL_FICTION | Module M1: causal scene/character architecture, development/compression/line-edit prerequisites | Identity/canon/text lock/issues/builds/metadata | Continuity/causal transitions/voice/emotional payoff/continuous read; owner concept, editorial acceptance and lock. Evidence GD/Bracken. |
| SERIES_FICTION | Module M2, composable M1 extension, not duplicate engine: recovered canon/invariants, series chronology/position | Same common locks/events/default inheritance | Against prior volumes' exact accepted canon; RECOVERED/IMPLIED/NEW_INFERENCE tagged; owner material canon changes. GD3 packet remains uncreated. |
| CONVENTIONAL_TRANSLATION | Module M3: witness precedence, aligned units, translation Bible/name/term authority, translation acceptance | Source/translation/text locks, cache/budget/issues | Coverage/order/seams/knowledge/semantic fidelity/native target voice; source corruptions/lacunae preserved; owner unresolved readings and translation lock. Evidence Jeanne/Jekyll block scaffolding. |
| TOKI_PONA_TRANSLATION | Module M4 extending M3: vocabulary/name lane, epistemic boundaries, optional Latin/sitelen synchronization | Translation/block/provenance contracts and target selection | TP lexical/semantic adequacy, referents, claim-vs-fact/spoiler, script/name allowlist, glyph/render continuation coverage; owner genuine lexical ambiguity. Odyssey/Jekyll evidence. No public-translator bypass. |
| PUBLIC_DOMAIN_DIFFERENTIATED_EDITION | Configured rights/source/added-value profile over translation or reference module, not own engine | Identity/source rights/product contract/metadata | Rights/source-witness and differentiated-value policy; human rights/editorial attestation. Public domain is jurisdiction/source evidence, not project-name inference. |
| APHORISM/COLLECTION | Configuration with unit type/order/index policy initially; no standalone module warranted by inspected evidence | Stable item IDs/coverage/duplicates/locks/Contents | Unit provenance/order/repetition and reader-facing navigation; owner selection/arrangement. No complete production case reconstructed, so module readiness is NOT_AVAILABLE. |
| SOURCE_BACKED_REFERENCE | Module M5 justified by RN2/RN3: source validity, transformation→buyer value, representative sample, crosswalk and productization | Identity/source locks/issues/product/format/commercial evidence | Traceability, diagram labels/factual coverage, prior-knowledge fit, normal-page rhythm/paid value; subject expert where needed, human product taste and commercial acceptance. Not a generic fiction requirement. |

Module composition is explicit and versioned; M4 requires M3, M2 requires M1. No implication that all books run all modules. A profile can add a required validator but cannot silently waive existing core/retailer rules.

## Configuration, not modules

Trim, paper, ink, bleed, cover finish, illustration count/placements, price/marketplace, Contents applicability, Kindle route, author surfaces, language/name guide/template choice and inherited series defaults are configuration with provenance. An exceptional route still needs owner evidence. Styles and creative title/blurb are title-specific accepted inputs, not arbitrary core defaults.

Conditional Pictiq module: used by fiction comics, not a mandatory book type. Exact locked source span/speaker/species → panel script → OWNER Composer conversion → approved output bytes/hash → one comic generation → visual/dialogue QA → art lock. DOG→PICTIQ; HUMAN→ENGLISH; SYSTEM→established English typography. No translation/inference/reconstruction of glyph mappings. Future comics one at a time; no retrospective rejection of GD2's owner-accepted atmospheric opening/closing, C02 panel count or limited semantic provenance.

## Four format modules

| ID / requested format | Adds / unique validation | Configuration and applicability |
|---|---|---|
| F1 REFLOWABLE_KINDLE_DOCX | Semantic headings/anchors, readable Contents in flow, no print folios/running heads, text/art identity, DOCX container; actual conversion/navigation/device preview independent | Good Dogs direct DOCX default. Ordinary adaptive Kindle, not Print Replica. TP is not categorically excluded; dated retailer language/script support and real sample decide eligibility. |
| F2 FIXED_PAGE_KINDLE | Page-local content integrity, visible source Contents, supported navigation, readability/zoom/device proof and exact imported source/export chain | Selected explicitly for Jekyll visual-script product where eligible. Do not infer KPF route from a DOCX filename. |
| F3 PAPERBACK_NO_BLEED | Correct trim/folios/Contents, binding-side text/image/vector safe areas, complete extraction, fonts/annotations, render/parity/art checks | GD 5.5×8.5 B&W cream matte defaults; Odyssey 7×10 is separate title config; KDP template uses processed count. |
| F4 PAPERBACK_BLEED | F3 non-bleed content safety plus bleed/media/trim boxes and intentional edge-art validation | Supported design target, no audited full consumer asserted. Never infer bleed solely from an image extending beyond margins. |

SITELEN_PONA_PDF is **R1 optional render adapter**, composed with F3/F4 and optionally F2. It owns approved glyph tokens/font/layer synchronization/name representation/continuations/glyph identity. It does not own rights, retailer states or default every TP book to fixed-page Kindle. Latin TP can use F1 where eligibility is proved; conventional French translation can use F1/F3 without R1.

Shared template interfaces cover title/copyright/translation note/Contents/glossary/name guide/chapter opener/series/reader kit. TeX/ODT/ReportLab implementations remain separate, with semantic fields/template version/hash and narrative exclusion checked by adapters.

## Required acceptance examples before activation

1. Same M1 text can target F1 and F3 without print folios leaking to Kindle.
2. M3 French ambiguity remains an OPEN issue despite structural PASS; no hidden source repair.
3. M4 Latin-only target does not require sitelen lock; R1 activation does.
4. F3 complete inventory includes vectors/footer, rotated image CTMs and binding side; raw xywh cannot masquerade as xyxy.
5. A nonexistent collection pipeline is not marked production-tested; configuration alone does not create evidence.
