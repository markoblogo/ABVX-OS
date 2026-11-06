# ABVX Book Factory Donor Search V1

Research date: 2026-09-30. Cost: NORMAL. Status: READY FOR OWNER REVIEW; no dependency admitted. External research and read-only architecture analysis; only this report, its matrix and adoption backlog are outputs. No packages, runtime/registry changes, manuscript edits, spikes, paid/model calls, publication, GD3 creative work or Machine Mind update.

## Decision

Use **Pandoc → EPUBCheck → Ace** behind a thin EPUB_FORMAT_ADAPTER. Keep ABVX identity, locks, evidence, STALE propagation, Contents parity and owner authority. Keep current print renderers. Vivliostyle is the strongest new print *spike candidate*, not a migration recommendation. External deterministic validators provide substantially more leverage than an agent prompt pack.

[EPUBCheck](https://github.com/w3c/epubcheck) supplies authoritative conformance checking and JSON reports. [Ace CLI](https://daisy.github.io/ace/docs/cli/) supplies accessibility findings and manual evaluation support. [Pandoc manual](https://pandoc.org/MANUAL.html) documents EPUB output, metadata, cover and navigation. The choices below are ABVX integration judgments, not claims of successful local execution.

## Local evidence and reuse

Read AGENTS/README/ARCHITECTURE, autonomy policy, both capability registries, `ABVX_BOOK_CORE_ARCHITECTURE_V1.md`, `ABVX_BOOK_CORE_STATE_SCHEMA_V1.json`, implementation plan and cross-pipeline audit. Existing `docs/audits/book-open-source-landscape-v1/` already recommends Pandoc/XeLaTeX, EPUBCheck/Ace and existing PDF tools. This package narrows that landscape to Universal Core mechanics; it does not reopen the earlier broad platform question.

The user's task describes approved architecture; local architecture/plan still say READY FOR REVIEW. This research does not change approval records or infer authority to implement Phase 1 or later work. Existing tracked changes include Jekyll blocks, registry/runtime/tests; they were present before this run and left alone.

Direct observations: `scripts/build_jekyll_sitelen_master_v1_2.py` already uses XeLaTeX, final labels, PDF destinations and `audit_print_toc_parity`. `scripts/run_jekyll_full_translation_v1.py` retains block/source/prompt hashes and usage, but its inspected resume selector checks sourceHash+success, not the full policy/context key proposed by Universal Core. Record this as a future invalidation requirement; do not invalidate/retranslate locked historical Jekyll. Existing `book_preflight` and publishing gates remain first reuse targets.

The earlier landscape records a blocked EPUBCheck pilot (Java/DNS); this is historical evidence, not a current host prerequisite check. This run executed no validators. External GitHub/docs were readable through browsing; shell DNS for a read-only GitHub metadata probe failed. Exact release/commit dates are UNKNOWN unless explicitly observed in the matrix.

## Scope and scorecard

The JSON matrix is the complete donor ledger: exact mechanic; ADOPT/WRAP/ADAPT/BORROW_PATTERN/REJECT; separate relevance, maturity, maintenance, license fit, offline fit, machine output, integration cost, leverage and lock-in; core/module/format mapping; license/ecosystem/dependencies; public interface/output; network/telemetry/upload uncertainty; source links and primary disposition. No opaque score.

“Inspected” means authoritative repository/docs inspected, not a source-code clone, security review or production test. Maintenance maturity is distinct from exact release recency. No exact commit dates are invented. ADOPT/WRAP/ADAPT are proposals contingent on owner decision, license verification and acceptance fixtures. Fixture ADAPT rows are explicitly conditional on individual content rights.

Search coverage:

| Area | Useful mechanics / decision |
|---|---|
| A authoring, B EPUB, M automation | Pandoc conversion; Quarto target/profile pattern; avoid whole Pressbooks/Calibre replacement |
| C print, K assets | Existing TeX/ReportLab/LibreOffice; Vivliostyle, Paged.js, SILE, WeasyPrint comparison; Pillow primitives |
| D EPUB conformance, E accessibility | EPUBCheck, Ace; veraPDF only for declared PDF profiles |
| F structure, O document QA | Pandoc AST, Vale/textlint, existing chapter/Contents/PDF gates; jsonschema |
| G translation | Translate Toolkit interchange/QA; OmegaT memory/glossary; Weblate review state |
| H provenance, L CI | DVC lock/fingerprint and Snakemake DAG patterns; pinned local stages and immutable reports |
| I editorial, P skills | Story Skills review anchors/disposable outputs; post-layout proof process; reject generic writing authority |
| J metadata | ISBN checksum, JSON Schema, conditional onixcheck; no ISBN ownership/retailer acceptance inference |
| N reactualization | PanDiff edition diff + Zotero source records + ABVX claim/time dependency policy |
| Q sales/analytics | Frictionless tabular schema/provenance pattern for owned exports; no retailer scraper or invented sales API |

Seed coverage includes Pressbooks; Vivliostyle CLI/VFM/create-book/themes (four distinct inspected components); Pandoc; Quarto; EPUBCheck; Ace; DAISY Pipeline; Calibre; Sigil; mdBook; Bookdown; Antora; Paged.js; SILE; WeasyPrint as open Prince alternative; Weblate; OmegaT; Translate Toolkit. Broader GitHub searches added document/schema/PDF/asset validators, edition diff, ONIX/ISBN tools, fixtures, DVC/Snakemake, tabular/source provenance, dpub and four agent-workflow donors. Whole-stack rejections can still yield an abstract reference pattern, but counts use one primary disposition each.

## Top 10 things ABVX should stop building itself

1. EPUB standards validator: **WRAP EPUBCheck**; keep scoped ABVX production checks.
2. Automated EPUB accessibility rule engine: **WRAP Ace**; preserve manual checkpoints.
3. Handwritten EPUB ZIP/OPF/spine/navigation writer: **WRAP Pandoc** for conventional reflowable books.
4. Partial JSON Schema standards implementation: **ADOPT python-jsonschema** for shape/meta-schema; retain semantic gates.
5. PDF syntax/object parser: **WRAP existing qpdf/Poppler**; complete transformed bbox coverage is still adapter work.
6. Image decoding/format conversion infrastructure: **ADOPT/reuse Pillow**; rights, approved derivatives and placement DPI stay ABVX.
7. TMX/XLIFF/PO parsers and routine merge/filter engines: **WRAP Translate Toolkit** where interchange is needed.
8. ISBN checksum/normalization library: **ADOPT isbnlib** local functions; never infer ISBN assignment.
9. ONIX XSD validator: **WRAP onixcheck if a real feed is required**; defer speculative ONIX factory.
10. Structure-aware edition redline engine: **WRAP PanDiff after fixture proof**; factual freshness remains human/evidence work.

This is a prevention list, not evidence that all ten currently exist as custom code.

## Top 10 mechanics worth borrowing

1. DVC input/parameter/output lockfile → C5/C7 content-addressed attempts.
2. Snakemake explicit DAG/cycle/missing-input rules → C5 transitive STALE.
3. Quarto profile separation → C7/C8 target configuration without manuscript duplication.
4. Vivliostyle page counters/TOC generation → C8 print inventory; compare against final PDF.
5. mdBook inventory/preprocessor boundary → C6/C8 expected hierarchy with typed adapter output.
6. Weblate changed-source review flags → C2/C5 prevent automatic old-translation acceptance.
7. OmegaT TMX + glossary + fuzzy suggestions → C5/C6 interoperable memory, owner acceptance separate.
8. Zotero source records/snapshots → C1/C5 claim-to-source dependencies with retrieval and validity dates.
9. Frictionless schema/error provenance → C11/C12 owned sales export staging, explicit null/unit/currency.
10. Story Skills citable paragraph anchors/disposable builds → C6/C7/C12 review findings tied to exact revision.

## Top 5 direct dependencies to test

“Direct” here means a concrete externally executable package candidate, including a WRAP; the exclusive ADOPT count in JSON is narrower.

| Dependency | Proposed use | First admission obstacle |
|---|---|---|
| EPUBCheck | WRAP final EPUB conformance JSON | JRE/version/report pin, warning policy |
| Ace | WRAP final EPUB automated accessibility | Browser dependencies, EARL parsing/manual list, network denial |
| Pandoc | WRAP EPUB3 builder, reuse current capability | Exact canonical import/heading/metadata/asset equivalence |
| python-jsonschema | ADOPT official schema mechanics | Explicit formats/local refs; negative schema cases |
| Translate Toolkit | WRAP TM interchange/QA only | GPL subprocess/license review; stable unit/context identity |

## Top 5 patterns to copy without dependency

1. DVC stage lock/fingerprint records; no DVC runtime or remote store.
2. Snakemake explicit dependency graph; no universal scheduler.
3. Weblate needs-review transition after source changes; no server/database.
4. OmegaT exact-vs-fuzzy memory distinction plus glossary; no sentence-level authority over literature.
5. Quarto target/profile configuration and generated-output separation; no second book framework.

## Top 5 donors to reject and why

| Donor | Rejected adoption scope |
|---|---|
| Pressbooks | WordPress multisite/CMS/DB ownership, heavier than a local adapter |
| Calibre | Default conversion/polishing layer duplicates Pandoc and can obscure locked-output changes |
| Sigil | Unattended production adapter: GUI edits cannot silently become canonical manuscript truth |
| Bookdown | R/academic publishing stack duplicates current paths without demonstrated gain |
| Antora | Versioned documentation-site platform has little retailer EPUB/print leverage |

Additionally reject Book writer skill as a factory dependency: broad memory/LLM/pacing claims provide no demonstrated missing deterministic gate. Rejection does not prohibit an owner using a GUI or reference document independently.

## Validator contract: normalization without false PASS

Preserve raw report hash, exact artifact/input hash, tool/package version and checksum, argv, config, environment, execution status, normalized issue IDs/severity/locations, manual-check inventory and attempt ID. Hash-bind normalization policy; changed output/tool/policy makes the proof STALE.

| External observation | ABVX result for that scoped check |
|---|---|
| Valid complete parse, current artifact, no policy-blocking findings | PASS for the tool's declared automated scope only |
| Authoritative error or policy-blocking violation | FAIL; warnings have explicit allow/review/block policy |
| Missing tool, timeout, crash, malformed/truncated/unsupported report, wrong hash | UNKNOWN; required gate blocks progression |
| Target/profile explicitly inapplicable | NOT_APPLICABLE with reason/policy, never inferred from not running tool |
| Actual owner-scoped exception plus immutable proof | OWNER_ACCEPTED_EXCEPTION; tool cannot manufacture it or turn it into PASS |

[Ace](https://daisy.github.io/ace/docs/cli/) default return code distinguishes execution failure from completion; parse findings even when exit 0. `--exiterror2` can assist but does not replace parsing. EPUBCheck standards/version/usage/warning severity must be pinned; report error absence does not certify retailer suitability. A passing Ace automated subcheck can coexist with UNKNOWN manual accessibility and blocked overall readiness.

[veraPDF](https://docs.verapdf.org/validation/) validates declared PDF/A/PDF/UA profiles, including only machine-verifiable PDF/UA checks. It is not a KDP margin validator. [python-jsonschema](https://github.com/python-jsonschema/jsonschema) is a shape validator; C1–C4 hashes, events, ownership and transition authority remain ABVX semantics.

## Contents/navigation: automate generation, keep parity

Generate one ordered chapter/section inventory from the format adapter. Pandoc supplies heading IDs, EPUB nav/spine/TOC; Vivliostyle can generate visible TOC and paged target counters. TeX already generates visible Contents/labels and PDF outlines in current Jekyll. EPUBCheck detects many malformed/broken-reference constraints; it cannot know an intentionally omitted chapter or ABVX visible Contents policy.

Three independent checks remain: **VISIBLE_CONTENTS**, **CONTENTS_PARITY**, **DIGITAL_NAVIGATION**. For reflowable EPUB, compare titles/order/coverage/unique anchors, spine reading order and destination headings, without invented page numbers. For print, compare displayed printed labels to actual final heading pages and PDF outline destinations, accounting for frontmatter numbering. Missing visible Contents must FAIL even if bookmarks work. Preserve local escaped-defect fixtures: missing page, stale numbers, omitted frontmatter, duplicate heading IDs and wrong anchors.

## Print comparison: 5.5 × 8.5 in

396 × 612 pt is the trim rectangle; bleed and safe areas are target policy, not timeless core constants. These are documentation-level capability assessments, not successful ABVX sample builds.

| Route | Page masters/margins/headers/numbers/openings | Full-page images/bleed | Fonts/PDF | Reproducibility and decision |
|---|---|---|---|---|
| Current ABVX TeX/ReportLab/LibreOffice | Existing title-specific mechanisms; Jekyll uses final TeX labels and parity | Current image envelopes/safe-area gates; no new global bleed policy | Existing PDF paths/font checks | Keep; bind tool/template/font hashes and actual output extraction |
| Vivliostyle CLI | CSS @page, named/left/right pages, margin boxes, running content, chapter breaks/counters | CSS size/bleed/crop and explicit placement | Browser-shaped embedded-font PDF; inspect output | Best new print spike; pin browser/core/theme/font packages; no automatic theme fetch |
| Paged.js | CSS paged media plus JS pagination hooks | CSS/browser export; exact box support needs fixture | Browser PDF route | Borrow hooks/counters; compare only if real customization gap |
| SILE | Frame/page-master and Lua typesetting packages | Explicit frames/images; bleed conventions need package proof | Native font shaping/PDF | Reference for difficult typesetting; high custom adapter burden |
| Pandoc-based routes | Depends on selected engine/template; not a PDF renderer itself | TeX/CSS engine-specific | EPUB independent of TeX; PDF via engine | Reuse current TeX route; conversion success is not print preflight |
| WeasyPrint | HTML/CSS page rules, strings/counters/bookmarks | Paged CSS + image layout; printer-profile proof separate | PDF variants/tags/font handling documented | Local Python alternative; version updates can change rendering |

[WeasyPrint API](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html) explicitly warns that new versions can change rendering. Pin all renderer environments; deterministic fingerprint is easier to guarantee than byte-identical PDFs. Two-run byte comparison must measure timestamps, IDs, font subsets and environment effects; never assume deterministic output from tool branding. None of these routes substitutes for final full object extraction, visual review, glyph fidelity or retailer preview.

## EPUB/D2D opportunity

Suggested adapter: exact TEXT_LOCK/canonical import → normalized ordered heading/asset/metadata inventory → pinned Pandoc `epub3` with explicit book identifier/date/language/cover and visible TOC → exact EPUB hash → EPUBCheck JSON → Ace JSON/HTML → independent ABVX Contents/nav/metadata/accessibility gates → local preview packet. A cover image and language field alone do not establish accessibility. Verify meaningful alt text, reading order, semantic headings, language changes and accessibility metadata against retained evidence.

Reuse existing Pandoc instead of adding Quarto/Calibre. Keep locked source untouched; work in disposable output directories. EPUB is a file-format candidate for Kindle conversion, not proof of Kindle device navigation. Sitelen/fixed-page adapters require explicit eligibility, font/licensing and accessible alternative policy; do not assume a conventional reflowable route preserves glyph layout.

[D2D FAQ](https://draft2digital.com/faq/) accepts externally produced EPUB for ebooks and says it preserves that EPUB's formatting. This supports a reusable local adapter; it does not prove D2D account/content eligibility, retailer acceptance or live publication. Retailer policies are dated external evidence and require separate review at actual handoff. No submission or upload is proposed here.

## Translation comparison with Jekyll

Best mechanical dependency: [Translate Toolkit](https://github.com/translate/translate) for format parsing/merge/filter/alignment. Best literary CAT reference: [OmegaT](https://omegat.org/) for TMX/glossary/fuzzy suggestions. [Weblate checks](https://docs.weblate.org/en/latest/user/checks.html) contribute needs-review/terminology workflow, not a new server.

Keep stable ABVX block IDs distinct from sourceHash; splitting/merging needs an explicit predecessor mapping. Use context-aware cache key: source + normalization/segmentation version + ordered surrounding/global context hashes + Bible/name/glossary/module policy + model/provider/prompt/config + QA policy. Source-only exact matching is insufficient; fuzzy reuse can never clear TEXT_LOCK/TRANSLATION_LOCK. A global glossary change may affect many unchanged-source blocks. For uncertain context dependencies, invalidate conservatively.

TMX/XLIFF are exchange representations, not replacements for accepted output hash, owner QA, source witness hierarchy or provider usage ledger. CAT QA can find omitted numbers/tags/terminology; it cannot resolve Toki Pona claim-to-fact, literary voice or sitelen knowledge/name/continuation semantics. Resume/retry reservations and budget ceilings remain ABVX runner concerns. No online MT connectors enabled by default.

## BOOK_REACTUALIZATION

Best bounded donor: [PanDiff](https://github.com/davidar/pandiff), a document-structure redline tool. Use Pandoc AST section anchors and accepted old/new source hashes to identify changed sections. [Zotero](https://github.com/zotero/zotero) contributes citation/source records; DVC/Snakemake contribute invalidation patterns.

Workflow remains PUBLISHED EDITION → FRESHNESS AUDIT → owner-approved BOUNDED UPDATE → successor TEXT_LOCK → NEW EDITION. Proposed freshness record: claim ID/span, source ref/hash, cited edition/page, retrieval time, asserted validity interval/as-of date, confidence/UNKNOWN, dependent section IDs and review decision. Source change or expiry opens a review issue; it does not prove a fact changed. Fact extraction is advisory and unqualified here; no deterministic tool inspected establishes factual truth or temporal freshness automatically.

Keep prior edition immutable, create a bounded correction set, compare semantic/document diff and layout impacts, rerun affected reference/metadata/Contents/build QA, then obtain new owner lock/release authority. No Machine Mind content is processed in this research.

## Skills and test corpora

Best agent-process reference: [Story Skills](https://github.com/danjdewhurst/story-skills), for review anchors and disposable builds. No plugin install or creative workflow adoption. Its claimed CLI/build/check behaviour has not been run. [Book writing workspace](https://github.com/aktsmm/Agent-Skills/blob/master/book-writing-workspace/SKILL.md) usefully asks which revision a proof came from; individual license states a noncommercial condition and an additional AI/ML/data-mining restriction. Keep it reference-only; no text/code copying or skill admission is proposed. [Editorial skills](https://github.com/brycehamrick/editorial-skills) separates post-layout proofreading; process overlap is substantial. Generic “world-class book” prompts are not validators.

Prioritize [EPUBCheck regression scenarios](https://github.com/w3c/epubcheck/wiki/TestSuite), [Ace tests](https://github.com/daisy/ace/tree/master/tests), [W3C EPUB tests](https://github.com/w3c/epub-tests) and [IDPF sample books](https://github.com/IDPF/epub3-samples). Add Vivliostyle samples/themes and SILE tests for pagination/font stress. Record source URL/commit/license, copied-file hashes, intended positive/negative outcome, applicable tool version, expected diagnostic IDs and separately expected reader behaviour. Do not assume all old samples pass the newest specification or that reading-system tests are malformed-EPUB tests.

Fixture selection: malformed ZIP/OPF/spine/nav and missing resources; omitted visible Contents/stale labels/duplicate anchors; missing alt text/language/reading order; RTL/CJK/combining marks/PUA font fallback; full-page images and bad placed DPI; chapter recto blank-page handling. External fixtures supplement synthetic ABVX negatives and local escaped-defect regressions. TP/sitelen and Pictiq semantics still require local fixtures and owner judgement. No external corpus downloaded/copied in this run.

## Supply chain and operational admission

Per donor, the matrix records the observed license, ecosystem, dependency weight and known interface. Exact transitive dependency graph/checksums, telemetry and runtime network behaviour remain UNKNOWN; no installed tool audit occurred. Local processing is the proposed usage, not verified isolation. Provision binaries/fonts separately, pin checksums and versioned local resources, deny network during spikes, prohibit remote image/CSS/MT/sync/upload features and sandbox manuscript-controlled HTML/XML/archive parsing. Preserve raw reports and parser limits; isolate report HTML from trusted app context.

GPL/AGPL subprocess use is different from copying/linking donor code; a WRAP is not an automatic license exemption. Review the actual distribution/modification/service scenario. Fonts/themes/test-book content have independent rights. ONIX/ISBN tools do not clear publication rights. No new hosted service, paid API or unpublished manuscript upload is needed for the proposed mechanics.

## Phase 2 impact and limits

The complete item-level disposition table is in the backlog and JSON. Core fingerprints/STALE/attempt authority, Contents parity, retailer state, TP semantics and provider budget policy remain ABVX-owned. Delegate standards/conversion/parsing mechanics; copy narrow DAG/TM/source-evidence patterns. Defer renderer migration, PDF/UA without a target, and ONIX without a feed. Proposed reactualization is distinguished from the original plan's six phases.

Next gate: **OWNER REVIEWS DONOR ADOPTION BACKLOG**. No spike is executed by this package.

## Final report

| Measure | Count |
|---|---:|
| DONORS INSPECTED | 41 |
| HIGH-PRIORITY DONORS | 9 |
| DIRECT ADOPTION CANDIDATES | 3 |
| WRAP CANDIDATES | 11 |
| ADAPT CANDIDATES | 2 |
| BORROW-PATTERN CANDIDATES | 19 |
| REJECTED | 6 |
| PHASE 2 ITEMS POTENTIALLY REPLACED | 7 |
| PHASE 2+ ITEMS POTENTIALLY REPLACED | 8 |

BEST IMMEDIATE ADOPTION: EPUBCheck wrapper proposal.

BEST VALIDATION DONOR: EPUBCheck (Ace complementary).

BEST EPUB DONOR: existing Pandoc.

BEST PRINT DONOR: Vivliostyle for a new isolated comparison; current ABVX route remains production choice.

BEST TRANSLATION DONOR: Translate Toolkit for interchange/QA; OmegaT for literary CAT patterns.

BEST REACTUALIZATION DONOR: PanDiff for edition redlines, not factual truth.

BEST AGENT/SKILL DONOR: Story Skills for review anchors/disposable builds, not creative authority.

RECOMMENDED FIRST 3 SPIKES: EPUB/validators → synthetic TM invalidation → synthetic print comparison. Definitions and acceptance conditions are in the backlog; none executed.

NEXT GATE: OWNER REVIEWS DONOR ADOPTION BACKLOG.

## Package verification

Strict JSON parsing, 41 unique donor IDs, allowed dispositions/priorities, nine separate scorecard fields, required source/core/module/format fields, all phase donor references and summary counts: PASS. Three nonempty outputs and trailing-whitespace checks: PASS. Seven protected local focus files matched initial SHA-256 hashes. This is a focused preservation check, not a whole-repository audit. No tool/runtime tests, builds or spikes run; no installed dependency or successful donor integration claimed.
