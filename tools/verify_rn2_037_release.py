#!/usr/bin/env python3
"""Independent release verifier for RN2-037 generated artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "books" / "rn2-037"
POOL = BASE / "data" / "question-pool-2026-2030.json"
CROSSWALK = BASE / "data" / "crosswalk.json"
LEDGER = BASE / "data" / "claim-ledger.json"
MANUSCRIPT = BASE / "manuscript" / "ham-radio-technician-visual-cram-map.md"
PDF = ROOT / "output" / "pdf" / "ham-radio-technician-visual-cram-map-2026-2030-interior.pdf"
EPUB = ROOT / "output" / "epub" / "ham-radio-technician-visual-cram-map-2026-2030.epub"
RAW_TEXT = BASE / "sources" / "raw" / "ncvec-technician-pool-2026-2030-corrected-2026-02-19.txt"
OUT = BASE / "qa" / "independent-release-verification.json"


def command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main() -> None:
    pool = json.loads(POOL.read_text())
    crosswalk = json.loads(CROSSWALK.read_text())["mappings"]
    ledger = json.loads(LEDGER.read_text())
    manuscript = MANUSCRIPT.read_text()
    raw = RAW_TEXT.read_text(errors="replace")
    questions = pool["questions"]
    ids = [q["id"] for q in questions]
    mapped = [m["question_id"] for m in crosswalk]
    claim_ids = {c["question_id"] for c in ledger["claims"] if "question_id" in c}

    # PDF text extraction splits some headers across columns/pages; the official
    # identifiers themselves remain stable and independently countable.
    raw_ids = sorted(set(re.findall(r"\b(T[0-9][A-Z][0-9]{2})\b", raw)))
    diagram_refs = {q["id"]: q["diagram_refs"] for q in questions if q["diagram_refs"]}
    expected_diagram_ids = {
        "T6A09", "T6C02", "T6C03", "T6C04", "T6C05", "T6C06",
        "T6C07", "T6C08", "T6C09", "T6C10", "T6C11", "T6D10",
    }

    pdfinfo = command("pdfinfo", str(PDF))
    pdffonts = command("pdffonts", str(PDF))
    pdftext = command("pdftotext", str(PDF), "-")
    page_match = re.search(r"^Pages:\s+(\d+)", pdfinfo, re.M)
    size_match = re.search(r"^Page size:\s+([0-9.]+) x ([0-9.]+) pts", pdfinfo, re.M)
    font_rows = [line for line in pdffonts.splitlines()[2:] if line.strip()]

    with zipfile.ZipFile(EPUB) as z:
        names = z.namelist()
        zip_ok = z.testzip() is None
        mimetype_ok = names[0] == "mimetype" and z.read("mimetype") == b"application/epub+zip"
        xml_names = [n for n in names if n.endswith((".xhtml", ".opf", ".xml", ".svg"))]
        xml_ok = True
        for name in xml_names:
            try:
                ET.fromstring(z.read(name))
            except ET.ParseError:
                xml_ok = False
        xhtml = "\n".join(z.read(n).decode("utf-8") for n in names if n.endswith(".xhtml"))
        nav_text = z.read("OEBPS/nav.xhtml").decode("utf-8")
        opf_text = z.read("OEBPS/content.opf").decode("utf-8")
        nav_targets = re.findall(r'<a href="([^"]+)"', nav_text)
        image_refs = re.findall(r"<img\s+[^>]*src=", xhtml)
        alt_refs = re.findall(r"<img\s+[^>]*alt=\"[^\"]+\"", xhtml)
        official_figures = {f"OEBPS/images/figure-t{i}.png" for i in range(1, 4)}

    checks = {
        "canonical_409_unique": len(ids) == len(set(ids)) == 409,
        "raw_source_409_unique": len(raw_ids) == len(set(raw_ids)) == 409,
        "canonical_matches_raw_ids": set(ids) == set(raw_ids),
        "answer_key_integrity": all(q["correct_option"] in q["options"] and q["correct_answer"] == q["options"][q["correct_option"]] for q in questions),
        "crosswalk_exact_coverage": len(mapped) == len(set(mapped)) == 409 and set(mapped) == set(ids),
        "claim_ledger_exact_coverage": claim_ids == set(ids) and ledger["unresolved_claims"] == 0,
        "manuscript_all_ids_present": all(qid in manuscript for qid in ids),
        "pdf_all_ids_present": all(qid in pdftext for qid in ids),
        "diagram_reference_set": set(diagram_refs) == expected_diagram_ids,
        "official_diagrams_present": all((BASE / "visuals" / "official-pool" / f"figure-t{i}.png").is_file() for i in range(1, 4)),
        "pdf_pages_208": bool(page_match and int(page_match.group(1)) == 208),
        "pdf_trim_8x10": bool(size_match and abs(float(size_match.group(1)) - 576) < 0.1 and abs(float(size_match.group(2)) - 720) < 0.1),
        "pdf_fonts_embedded": bool(font_rows) and all(" yes " in f" {row} " for row in font_rows),
        "pdf_visible_contents_with_page_numbers": "Contents" in pdftext and all(f"{title} {page}" in re.sub(r"\s+", " ", pdftext) for title, page in [("Electricity without intimidation", 9), ("Rules as decision paths", 131), ("Complete 409-ID crosswalk", 181)]),
        "epub_zip_valid": zip_ok,
        "epub_mimetype_valid": mimetype_ok,
        "epub_xml_valid": xml_ok,
        "epub_every_image_has_alt": len(image_refs) == len(alt_refs) and len(image_refs) > 0,
        "epub_official_diagrams_present": official_figures.issubset(set(names)),
        "epub_interactive_toc_present": bool(nav_targets) and all(f"OEBPS/{target}" in names for target in nav_targets),
        "epub_toc_visible_in_reading_order": '<itemref idref="nav"/>' in opf_text,
        "epub_ncx_compatibility_toc": "OEBPS/toc.ncx" in names and 'toc="ncx"' in opf_text,
        "independent_notice_present": "not affiliated with or endorsed" in manuscript.lower(),
        "no_pass_promise": not bool(re.search(r"guarantee(?:d)? (?:you will )?pass|pass guarantee", manuscript, re.I)),
    }
    payload = {
        "schema_version": "rn2-037-independent-release-verification/v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "counts": {
            "canonical_questions": len(ids), "raw_question_ids": len(raw_ids),
            "crosswalk_rows": len(mapped), "question_claims": len(claim_ids),
            "diagram_referenced_questions": len(diagram_refs), "epub_images": len(image_refs),
            "epub_alt_texts": len(alt_refs), "pdf_pages": int(page_match.group(1)) if page_match else None,
        },
        "hashes": {
            "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
            "epub_sha256": hashlib.sha256(EPUB.read_bytes()).hexdigest(),
            "pool_json_sha256": hashlib.sha256(POOL.read_bytes()).hexdigest(),
        },
        "limitation": "EPUB structural validation is deterministic; representative device rendering remains a KDP Previewer publishing-gate check.",
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if payload["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
