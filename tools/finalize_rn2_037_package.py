#!/usr/bin/env python3
"""Write final RN2-037 QA, commercial, and Radar production records."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "books" / "rn2-037"
PDF = ROOT / "output/pdf/ham-radio-technician-visual-cram-map-2026-2030-interior.pdf"
EPUB = ROOT / "output/epub/ham-radio-technician-visual-cram-map-2026-2030.epub"
MAN = BASE / "manuscript/ham-radio-technician-visual-cram-map.md"
QA = BASE / "qa"
COMM = BASE / "commercial"
PROD = BASE / "production"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manuscript = MAN.read_text()
    # Match the conventional `wc -w` production count used in handoff reports.
    word_count = len(manuscript.split())
    verifier = json.loads((QA / "independent-release-verification.json").read_text())
    deterministic = json.loads((QA / "deterministic-qa.json").read_text())
    assert verifier["status"] == deterministic["status"] == "PASS"

    factual = f"""# RN2-037 factual and editorial audit

**Status:** PASS  
**Audit date:** 2026-09-06  
**Manuscript words:** {word_count:,}

## Critical and high findings

None unresolved. The canonical pool, raw-source ID set, crosswalk, manuscript, PDF, and claim ledger reconcile to 409 unique IDs. Correct-option resolution passes for every item. The February 19, 2026 corrections to T1C01, T5A05, T7A09, and T0A10 are present.

The 12 items that reference official Figures T-1, T-2, or T-3 have a usable figure route. Exact public-domain NCVEC figures appear on print pages 38–39 and in the EPUB with substantive alt text. The images are 300 ppi source crops and remain above 250 effective ppi at their placed sizes.

## Medium findings resolved

- Removed a potential comprehension gap caused by figure-referenced anchors without the official figure key.
- Kept official question anchors confined to 35 diagnostic pages; the teaching sequence remains concept-first.
- Preserved a separate reflowable EPUB rather than converting the print PDF.

## Editorial and scope pass

The reading path is dependency-based, not pool-order. Each group uses one mental model, two visual views, official-ID anchors, and a quick check. Prose is compact and beginner-facing. Abbreviations receive a glossary. No pass guarantee, invented credential, operating authorization, legal advice, or affiliation claim appears.

## Copyright and trademark pass

NCVEC expressly released the question pool into the public domain. The three official pool figures are reproduced with source attribution. Original teaching diagrams are stored as editable SVG. No ARRL or competitor prose, layouts, mnemonics, artwork, logos, seals, or branding are copied. FCC, NCVEC, ARRL, and Technician Class are used only for factual identification; the independent-study-aid notice is prominent.

## Differentiation regression

**PASS — DIAGRAM-FIRST CONCEPT SYSTEM + COMPLETE 409-ID CROSSWALK.** The book contains 89 editable original SVG assets plus the three required source figures. Official-anchor pages occupy 35 of 208 pages (16.8%); they diagnose misses rather than drive the teaching sequence. The September 6 Amazon packaging refresh remained dominated by complete-pool explanations, practice tests, pass promises, and conventional manuals. No inspected result presented the same diagram-first concept-map plus deterministic 409-ID routing thesis.
"""
    write(QA / "factual-editorial-audit.md", factual)

    preflight = f"""# RN2-037 production preflight

**Overall:** PASS WITH ONE HUMAN PUBLISHING-GATE CHECK

## Paperback

- 208 pages; exact 8 × 10 inch trim; no bleed; black-and-white/grayscale interior.
- KDP safe-area correction verified: the title page has no full-page background object, and the 21-row crosswalk pages 181–199 finish above the bottom content margin.
- Embedded Arial regular and bold fonts; visible contents with final page numbers, bookmarks, page numbers, chapter openers, review, sources, and all 409 crosswalk routes present.
- Automated text/ID checks pass; full-book, chapter-opening, visual-system, and representative-page contact sheets inspected after the correction pass.
- No accidental blank pages, clipping, or overlap found in the rendered 208-page contact sheet. Official figure pages 38–39 and representative anchor pages were inspected at full resolution.
- Final PDF SHA-256: `{sha(PDF)}`.

## Kindle

- EPUB 3 ZIP, mimetype, XML/XHTML/SVG parsing, manifest, interactive navigation targets, visible contents in reading order, NCX compatibility navigation, headings, Unicode, and image references pass.
- 71 instructional image placements carry 71 non-empty alt attributes; essential explanations remain in linear text.
- Final EPUB SHA-256: `{sha(EPUB)}`.
- No local epubcheck, Kindle Previewer CLI, or reliable multi-device renderer was available. Open the EPUB once in KDP Previewer at phone, tablet, and e-reader widths before approving publication. This is visual device QA, not subject-matter review.
"""
    write(QA / "production-preflight.md", preflight)

    commercial = """# RN2-037 final commercial package

## Metadata

**Title:** Ham Radio Technician Visual Cram Map 2026–2030  
**Subtitle:** A Diagram-First Guide to FCC Element 2 Concepts, Rules, Calculations, and All 409 Official Question IDs  
**Author:** Northfield Signal Guides  
**Publisher/imprint treatment:** Use Northfield Signal Guides consistently; keep the bio minimal and credential-free.

## Amazon description

The Technician exam can look like 409 unrelated facts. This book turns the current 2026–2030 Element 2 pool into a smaller set of connected visual models.

Follow plain-English maps for electricity, components, radio blocks, troubleshooting, propagation, antennas, signals, station setup, operating, rules, and safety. Then use the complete question-ID crosswalk to route any missed practice item back to the concept that explains it.

Inside:

- diagram-first explanations for the concepts beginners commonly mix up;
- compact formula, signal-path, operating, rules, and safety review routes;
- exact official T-1, T-2, and T-3 figure keys;
- official-pool anchors for every group;
- a complete, deterministic crosswalk covering all 409 current question IDs.

This is not another pile of practice tests. Use it beside a free randomized exam tool: learn the model here, practise there, and diagnose every miss by ID.

Built for the corrected NCVEC Technician Class Element 2 question pool released February 19, 2026, effective July 1, 2026 through June 30, 2030. Independent study aid; not affiliated with or endorsed by the FCC, NCVEC, ARRL, or any examination provider. No passing result is promised.

## Seven keyword fields

1. technician class visual study guide
2. FCC element 2 concept map
3. ham license exam diagrams
4. amateur radio beginner review
5. electronics formulas antennas safety
6. 409 question ID crosswalk
7. 2026 2030 technician pool

## Category starting points

- Technology & Engineering / Radio
- Study Aids / Professional
- Technology & Engineering / Electronics / General

Choose the closest current KDP category labels during upload; category taxonomies can change.

## Pricing and programs

- Paperback: **US$17.99**, 8 × 10, black ink, white paper, matte cover. Current estimated US print cost: **US$4.54** (US$1.00 + 208 × US$0.017); estimated standard Amazon royalty: **US$6.25** at the 60% tier. Confirm in KDP before publishing.
- Kindle: **US$6.99**. Confirm delivery cost after upload because the image-bearing EPUB affects the 70% royalty calculation.
- KDP Select: **Yes, as a 90-day launch test**, only if no non-Amazon ebook distribution is planned. Measure KU page reads separately from sales.
- DRM: **Off**. It improves legitimate device/accessibility flexibility and does not materially protect a compact study aid from copying.

## Cover brief

**Buyer:** a first-time, nontechnical Technician candidate who feels the pool is fragmented and wants a fast visual map.  
**Thumbnail hierarchy:** `HAM RADIO TECHNICIAN` first; `VISUAL CRAM MAP` second; `2026–2030` as a high-contrast edition badge; subtitle subordinate; `Northfield Signal Guides` small.  
**Visual direction:** disciplined technical field guide; generous whitespace; one original abstract node/path motif suggesting concepts connecting, not a literal radio glamour shot. Strong black, white, and one restrained accent color on the cover; interior remains grayscale.  
**Claims to show:** `DIAGRAM-FIRST`; `ALL 409 OFFICIAL QUESTION IDs MAPPED`; `2026–2030`.  
**Do not show:** FCC/NCVEC/ARRL logos or seals, call signs, fake credentials, “official,” “guaranteed pass,” copied schematics, crowded question bubbles, or generic AI radio imagery.  
**Paperback production:** generate the wrap only after KDP provides the exact 208-page, white-paper cover template and spine width. Leave the barcode area clear.  
**Kindle:** derive a front-only cover from the approved paperback direction after human selection.
"""
    write(COMM / "kdp-commercial-package.md", commercial)

    package = {
        "schema_version": "rn2-037-commercial-package/v1",
        "checked_date": "2026-09-06",
        "title": "Ham Radio Technician Visual Cram Map 2026–2030",
        "subtitle": "A Diagram-First Guide to FCC Element 2 Concepts, Rules, Calculations, and All 409 Official Question IDs",
        "author": "Northfield Signal Guides",
        "paperback_price_usd": 17.99,
        "kindle_price_usd": 6.99,
        "paperback_print_cost_estimate_usd": 4.54,
        "paperback_royalty_estimate_usd": 6.25,
        "kdp_select": "90-day launch test if Amazon-exclusive",
        "drm": False,
        "keyword_fields": [
            "technician class visual study guide", "FCC element 2 concept map",
            "ham license exam diagrams", "amateur radio beginner review",
            "electronics formulas antennas safety", "409 question ID crosswalk",
            "2026 2030 technician pool",
        ],
        "category_starting_points": [
            "Technology & Engineering / Radio", "Study Aids / Professional",
            "Technology & Engineering / Electronics / General",
        ],
        "sources": {
            "amazon_search_observed": "2026-09-06",
            "kdp_print_cost": "https://kdp.amazon.com/en_US/help/topic/G201834340",
            "kdp_royalty": "https://kdp.amazon.com/en_US/help/topic/G201834330",
        },
    }
    write(COMM / "kdp-commercial-package.json", json.dumps(package, indent=2))

    manifest_path = PROD / "production-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update({
        "word_count": word_count,
        "official_pool_figures": 3,
        "pdf_sha256": sha(PDF),
        "epub_sha256": sha(EPUB),
        "independent_verification": "books/rn2-037/qa/independent-release-verification.json",
        "preflight": "books/rn2-037/qa/production-preflight.md",
        "commercial_package": "books/rn2-037/commercial/kdp-commercial-package.md",
        "human_gate": "Cover selection, KDP metadata entry/upload, KDP Previewer device check, pricing confirmation, and publication approval.",
        "table_of_contents": {"print_visible_with_final_page_numbers": True, "epub_interactive_and_in_reading_order": True, "epub_ncx_compatibility": True},
        "kdp_safe_area": {"title_page_full_bleed_object": False, "crosswalk_pages_181_199_compacted": True},
    })
    write(manifest_path, json.dumps(manifest, indent=2))

    source_manifest_path = BASE / "data/source-manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text())
    source_manifest["live_refresh"] = {
        "checked_at": "2026-09-06",
        "ncvec_result": "No later erratum or withdrawal found; controlling page still lists the February 19, 2026 four-question correction and public-domain release.",
        "ecfr_result": "Part 97 remained current and displayed as up to date through September 3, 2026.",
        "content_changes_required": False,
    }
    write(source_manifest_path, json.dumps(source_manifest, indent=2))

    editable = """# RN2-037 editable production master

The paperback master is deterministic rather than tied to a proprietary layout file.

- Reader-facing source: `books/rn2-037/manuscript/ham-radio-technician-visual-cram-map.md`
- Canonical question data and crosswalk: `books/rn2-037/data/`
- Editable original diagrams: `books/rn2-037/visuals/svg/`
- Exact public-domain pool figures: `books/rn2-037/visuals/official-pool/`
- Layout/generation source: `tools/build_rn2_037_book.py`

Rebuild with the bundled workspace Python runtime, then run `tools/verify_rn2_037_release.py`. The build emits the 8 × 10 paperback PDF and semantic EPUB. The generator fixes the intentional 208-page pagination and bookmarks; edit source content or layout code, never the exported PDF.
"""
    write(PROD / "editable-master.md", editable)

    artifact_paths = [
        MAN, PDF, EPUB, BASE / "data/question-pool-2026-2030.json",
        BASE / "data/crosswalk.json", BASE / "data/claim-ledger.json",
        BASE / "data/source-manifest.json", QA / "deterministic-qa.json",
        QA / "independent-release-verification.json", QA / "factual-editorial-audit.md",
        QA / "production-preflight.md", COMM / "kdp-commercial-package.md",
        COMM / "kdp-commercial-package.json", PROD / "editable-master.md",
    ]
    artifacts = []
    for path in artifact_paths:
        artifacts.append({"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)})
    artifact_manifest = {
        "schema_version": "rn2-037-artifact-manifest/v1",
        "status": "KDP_READY_AWAITING_COVER_HUMAN_GATE",
        "generated_at": "2026-09-06",
        "artifacts": artifacts,
        "asset_sets": {
            "editable_original_svgs": {"directory": "books/rn2-037/visuals/svg", "count": len(list((BASE / "visuals/svg").glob("*.svg")))},
            "official_public_domain_figures": {"directory": "books/rn2-037/visuals/official-pool", "count": len(list((BASE / "visuals/official-pool").glob("*.png")))},
            "contact_sheets": {"directory": "books/rn2-037/qa/contact-sheets", "count": len(list((QA / "contact-sheets").glob("*.jpg")))},
        },
    }
    write(PROD / "artifact-manifest.json", json.dumps(artifact_manifest, indent=2))

    radar = {
        "schema_version": "book-radar-import/v1",
        "radar_runs": [], "opportunities": [], "scores": [], "products": [],
        "portfolio_products": [], "launches": [], "actuals": [], "calibrations": [],
        "similarity_results": [],
        "evidence": [{
            "id": "evidence:RN2-037:autonomous-production",
            "opportunity_id": "RN2-037",
            "observed_at": "2026-09-06",
            "summary": "Autonomous production completed as a 208-page diagram-first paperback plus semantic EPUB with a complete verified 409-ID crosswalk.",
            "details": {
                "production_started": "2026-09-06", "production_ended": "2026-09-06",
                "status": "KDP_READY_AWAITING_COVER_HUMAN_GATE", "pages": 208,
                "word_count": word_count, "original_editable_svg_assets": 89,
                "official_public_domain_figures": 3,
                "formats": ["8x10 black-and-white paperback PDF", "reflowable EPUB 3"],
                "question_ids_expected": 409, "question_ids_represented": 409,
                "unresolved_claims": 0, "independent_release_verification": "PASS",
                "major_stages": ["source freeze", "pool extraction", "concept graph", "crosswalk", "manuscript", "visuals", "paperback", "Kindle", "factual audit", "preflight", "commercial packaging", "live source refresh"],
                "blockers": ["NCVEC CDN blocked automated PDF transfer; an independent NCVEC-member VEC mirror supplied the identical corrected release, cross-checked against the controlling NCVEC page."],
                "rework_causes": ["Added exact official T-1/T-2/T-3 figure keys after the independent diagram-reference audit found 12 dependent questions."],
                "contract_deviations": ["Final manuscript is approximately 16k words because the 208-page product is diagram-led; prose was not inflated to meet a word target."],
                "estimated_anton_hours_remaining_pre_upload": [0.75, 1.25],
                "actual_anton_subject_matter_hours": 0,
                "planned_prices_usd": {"paperback": 17.99, "kindle": 6.99},
            },
            "source_ref": "books/rn2-037/production/production-manifest.json",
        }],
        "decisions": [{
            "id": "decision:RN2-037:kdp-ready",
            "opportunity_id": "RN2-037", "decision": "kdp_ready_awaiting_cover_human_gate",
            "reason": "Authoritative-source, rights, 409-ID, crosswalk, claim-ledger, differentiation, print, and EPUB structural gates passed without Anton subject-matter review.",
            "decided_at": "2026-09-06", "production_authorized": True,
        }],
    }
    write(ROOT / "book-radar/imports/rn2-037-production-result.json", json.dumps(radar, indent=2))
    print(json.dumps({"status": "PASS", "word_count": word_count, "pdf_sha256": sha(PDF), "epub_sha256": sha(EPUB)}, indent=2))


if __name__ == "__main__":
    main()
