# ABVX Book Factory Adoption Backlog V1

Status: PROPOSED; owner review required. No spike executed. Research date: 2026-09-30.

## Decision queue

| Order | Bounded item | Decision / acceptance |
|---|---|---|
| 1 | EPUB conformance/accessibility wrapper | Review EPUBCheck + Ace + existing Pandoc; demonstrate valid/invalid fixtures and normalized UNKNOWN/manual checks before admission |
| 2 | Schema shape validation | Review jsonschema as a development/validation dependency; no semantic gate replacement or Phase1 changes in this run |
| 3 | Translation memory exchange | Review Toolkit subprocess license/interface and context-aware invalidation with synthetic units |
| 4 | Print alternative | Conditional Vivliostyle comparison only; retain current renderer unless a measured new-title gap justifies change |
| 5 | Edition/sales/reference utilities | PanDiff redlines, owned CSV schema and source-evidence patterns only when a real authorized consumer needs them |

## Phase 2+ disposition

Potential replacement means replacing a narrow standards/conversion/parser implementation with a tool, not replacing an entire phase. Original-plan items only: **7 Phase2**, **8 Phase2+**. Reactualization is a proposed addition, counted separately. KEEP_CUSTOM includes reuse/extraction of existing internal capability. REMOVE below rejects a hypothetical platform addition already excluded by the plan.

| Planned item | Disposition | Donor(s) | Rationale / retained authority |
|---|---|---|---|
| P2 dependency DAG / STALE | BORROW_PATTERN | DVC, Snakemake | Keep ABVX transitive authority and conservative invalidation; copy explicit hashes/params and cycle checks. |
| P2 build manifests / fingerprints / attempts | BORROW_PATTERN | DVC, Quarto | Keep own manifest; fingerprint excludes run timestamp/output path, attempt evidence distinct. |
| P2 visible Contents generation | WRAP_EXTERNAL_TOOL | Pandoc, Vivliostyle CLI | Delegate generation; no new renderer adoption required for existing TeX. |
| P2 visible Contents / nav / destination parity | KEEP_CUSTOM | EPUBCheck | Reuse audit_print_toc_parity; normalize inventories; standards checker does not replace trio. |
| P2 heading / crossref inventories | WRAP_EXTERNAL_TOOL | Pandoc, EPUBCheck | Use AST and standards diagnostics; ABVX verifies expected chapter order/coverage. |
| P2 EPUB_FORMAT_ADAPTER | WRAP_EXTERNAL_TOOL | Pandoc | Existing Pandoc first; thin canonical-input/metadata/asset wrapper; no handwritten ZIP/OPF/nav engine. |
| P2 EPUB conformance | WRAP_EXTERNAL_TOOL | EPUBCheck | External authoritative checker, versioned raw JSON and hash-bound result. |
| P2 EPUB accessibility baseline | WRAP_EXTERNAL_TOOL | Ace by DAISY | Parse EARL assertions/manual checklist; preserve manual gate. |
| P2 PDF production adapter | KEEP_CUSTOM | Vivliostyle CLI, WeasyPrint | Keep current ReportLab/TeX/LibreOffice adapters; renderer bakeoff only if new-title gap proven. |
| P2 PDF syntax/object extraction | WRAP_EXTERNAL_TOOL | qpdf | Reuse current qpdf/Poppler; complete transformed bbox extraction remains custom adapter duty. |
| P2 trim/bleed/DPI/safe-area geometry | KEEP_CUSTOM | Pillow, qpdf | Keep ABVX retailer policy, coordinate transforms and final placement effective DPI. |
| P2 PDF accessibility profile | DEFER | veraPDF | Only when a target requires PDF/UA; do not impose PDF/A on all retail print. |
| P2 metadata/ISBN shape validation | REPLACE_WITH_DEPENDENCY | python-jsonschema, isbnlib | Schema/checksum libraries for mechanics; credits/rights/ISBN assignment stay custom. |
| P2 ONIX adapter | DEFER | onixcheck | No ONIX feed requirement demonstrated for D2D handoff; test only on actual feed need. |
| P2 cover/asset pipeline | KEEP_CUSTOM | Pillow | Wrap bounded image primitives; retain rights/owner art lock, spine geometry and visual gate. |
| P3 GD3 compatibility extraction | KEEP_CUSTOM | Existing ABVX | No donor replaces historical state/series/Pictiq authority; do not start creative work. |
| P4 TM exchange/merge/alignment | WRAP_EXTERNAL_TOOL | Translate Toolkit | TMX interchange adapter with stable ABVX unit IDs; outputs suggestions until accepted. |
| P4 translation cache/context invalidation | BORROW_PATTERN | Weblate, OmegaT | Cache includes source, adjacent/global context, Bible, model/prompt/config and QA versions. |
| P4 provider reservation/retry/provenance | KEEP_CUSTOM | Existing ABVX | Existing bounded runner/broker boundary; CAT does not reserve provider spend. |
| P5 TP/sitelen semantic and glyph alignment | KEEP_CUSTOM | Existing ABVX | Native semantic/knowledge/name/continuation and font/render equivalence remain module-specific. |
| P6 retailer transitions / publication automation | KEEP_CUSTOM | Existing ABVX | Build/upload/preview/live evidence stay distinct; no automatic writes. |
| P6 publication sales exports | BORROW_PATTERN | Frictionless | Versioned owned CSV staging, units/currency provenance, idempotent import; unknown stays null. |
| P6 learning index / defect regression | KEEP_CUSTOM | W3C EPUB tests | Promote lessons only into real validators/tests; external fixtures supplement local escaped defects. |
| Proposed BOOK_REACTUALIZATION edition diff | WRAP_EXTERNAL_TOOL | PanDiff | Not a named original phase; bounded read-only edition comparison, no actual Machine Mind update. |
| Proposed freshness/citation dependencies | BORROW_PATTERN | Zotero | Claim/source/time evidence envelope; human determines meaning/currentness. Not autonomous fact checking. |
| Hypothetical general publishing platform/scheduler | REMOVE | Pressbooks, Antora | Prevent scope addition; original plan already excludes this, so no planned feature is actually removed. |

## Recommended first 3 spikes — definitions only

### 1. EPUB adapter and validator normalization

**Scope/cost:** NORMAL; approximately one bounded work session after prerequisites are available. Synthetic Markdown and DOCX fixtures only; no locked manuscript or retailer account. No paid API.

**Route:** canonical fixture → existing pinned Pandoc EPUB3 → EPUBCheck JSON → Ace JSON/HTML → proposed normalized ABVX result JSON. Explicit stable identifier, language/date, cover, heading inventory and alt text. Work in disposable local output directory.

**Cases:** positive two-chapter book; missing visible Contents despite valid nav; broken href/resource; duplicate heading ID; missing alt text/language; Ace exit 0 with violations; timeout/bad report; mismatch between report hash and current artifact. Include representative Unicode and RTL/CJK fixture if rights verified.

**Acceptance:** valid standard fixture passes scoped automated checks; injected conformance/accessibility defects fail their own check; invisible/omitted Contents fails ABVX even when EPUBCheck succeeds; unavailable/bad report yields UNKNOWN; manual accessibility remains separately unresolved. Raw reports + normalized issues/tool/config/output hashes retained. Two runs compare byte hashes and semantic package inventories; differing output is recorded, not assumed reproducible.

**Admission gate:** owner reviews tool versions, license/dependency evidence, normalization rules, network-denied behaviour and fixtures. No retailer PASS, installation into runtime or submission implied.

### 2. Translation identity and changed-unit invalidation

**Scope/cost:** CHEAP to NORMAL; synthetic bilingual three-block corpus. First compare existing ABVX contracts; optional isolated Toolkit only after approved package/license pin. No translation/model call.

**Route:** stable ABVX block IDs/source hashes → TMX/XLIFF representation → parse/round-trip accepted translations → one changed source block → affected-unit needs-review + dependent context QA invalidation.

**Cases:** one source change; reordering; split/merge; duplicate unit ID; unchanged source with changed Bible/glossary; adjacent context change; malformed unit; fuzzy memory suggestion; failed resume checkpoint.

**Acceptance:** exact unit/order/language/hash mapping round-trips; unchanged *full-context* keys are reusable; changed unit and explicitly dependent context units stale; global policy change invalidates all affected units; fuzzy match never accepted automatically. SourceHash-only hit fails when context/policy differs. Historical Jekyll unchanged.

**Admission gate:** compare Toolkit parsing/QA benefit against thin current adapter; retain local locks, provenance, provider budget and TP semantic/native gates.

### 3. Print renderer comparison

**Scope/cost:** NORMAL; synthetic 5.5 × 8.5 book using an existing authorized sample harness plus isolated pinned Vivliostyle. If prerequisite provisioning/custom fonts or typesetting becomes EXPENSIVE, stop for separate approval. No title rebuild/migration.

**Route:** same chapter/asset inventory → current ABVX print route and Vivliostyle candidate → final PDFs → existing preflight/parity/font/object checks → representative rendered pages.

**Cases:** frontmatter roman/arabic numbering, visible Contents, page destinations/bookmarks, recto chapter opening, running headers, no-bleed and explicit bleed variant, full-page raster/vector art, font subsets/combining marks/PUA fallback, footer safe area and effective placed DPI. Include sitelen only as a synthetic font stress case, not a claim of M4 eligibility.

**Acceptance:** final trim 396 × 612 pt; configured bleed/margins respected; final labels/parity and expected chapter inventory match; all placed object classes have declared extraction coverage; font embedding/glyph rendering checked; output hash/input fingerprint preserved. Two-run deterministic test distinguishes semantic layout stability from byte identity. Offline fonts/CSS/themes only; no automatic theme download.

**Migration rule:** preserve current route unless measurable capability/maintenance gain exceeds added dependencies and title-specific regression cost. Visual preference alone is insufficient.

## Later small spikes, only if needed

- jsonschema: current design schema + synthetic two-type records, arrays/patterns/conditionals/local refs/format negatives; hashes/authority still ABVX.
- PanDiff: synthetic old/new editions with moved sections, tables, citations and images; redline coverage and source normalization proof, no fact-verification claim.
- ONIX/ISBN: only actual feed requirement; invalid checksum, edition identity and invalid XML schema fixtures, rights/assignment handled separately.
- Sales CSV: two owned synthetic exports with duplicate/reversal/missing currency/date/edition fields; idempotency, units and unknown values preserved.
- veraPDF: only requested PDF/UA or archive profile; malformed/untagged fixture and separate human checklist.

## Owner decisions

Approve/reject the dependency shortlist and order of isolated spikes. No runtime admission, project migration, platform build, paid services, source upload or creative task is included. Every future spike must name its exact package version/checksum, selected license, dependency prerequisites, fixture rights, offline strategy, result parser and stop condition.

NEXT GATE: **OWNER REVIEWS DONOR ADOPTION BACKLOG**.
