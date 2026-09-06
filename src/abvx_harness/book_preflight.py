"""Reusable fail-closed preflight checks for print and EPUB books."""

from __future__ import annotations

import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def kdp_margins(page_count: int, bleed: bool) -> dict[str, float]:
    if page_count < 24 or page_count > 828:
        raise ValueError("KDP paperback page count must be 24-828")
    if page_count <= 150:
        inside = 27.0
    elif page_count <= 300:
        inside = 36.0
    elif page_count <= 500:
        inside = 45.0
    elif page_count <= 700:
        inside = 54.0
    else:
        inside = 63.0
    outside = 27.0 if bleed else 18.0
    return {"inside": inside, "outside": outside, "top": outside, "bottom": outside}


def audit_page_geometry(pages: list[dict], page_count: int, bleed: bool = False) -> dict:
    """Audit renderer-supplied object/text boxes in PDF points, origin bottom-left."""
    margins = kdp_margins(page_count, bleed)
    failures, near_boundary, dense = [], [], []
    for page in pages:
        number, width, height = page["page"], page["width"], page["height"]
        left = margins["inside"] if number % 2 else margins["outside"]
        right = margins["outside"] if number % 2 else margins["inside"]
        safe = (left, margins["bottom"], width - right, height - margins["top"])
        boxes = page.get("objects", [])
        if len(boxes) >= 18 or page.get("kind") in {"worksheet", "index", "crosswalk", "long_list", "table_graphic"}:
            dense.append(number)
        for obj in boxes:
            x0, y0, x1, y1 = obj["bbox"]
            if x0 < safe[0] or y0 < safe[1] or x1 > safe[2] or y1 > safe[3]:
                failures.append({"page": number, "type": obj.get("type", "object"), "bbox": obj["bbox"], "safe": safe})
            elif min(x0-safe[0], y0-safe[1], safe[2]-x1, safe[3]-y1) < 6:
                near_boundary.append(number)
    return {
        "status": "FAIL" if failures else "PASS",
        "margins_pt": margins,
        "failures": failures,
        "dense_pages": sorted(set(dense)),
        "near_boundary_pages": sorted(set(near_boundary)),
    }


def find_collisions(boxes: list[dict], tolerance: float = 1.0) -> list[dict]:
    collisions = []
    for i, first in enumerate(boxes):
        ax0, ay0, ax1, ay1 = first["bbox"]
        for second in boxes[i + 1:]:
            bx0, by0, bx1, by1 = second["bbox"]
            overlap_x = min(ax1, bx1) - max(ax0, bx0)
            overlap_y = min(ay1, by1) - max(ay0, by0)
            if overlap_x > tolerance and overlap_y > tolerance:
                collisions.append({"first": first.get("id"), "second": second.get("id")})
    return collisions


def audit_svg(path: Path, expected_labels: list[str]) -> dict:
    root = ET.parse(path).getroot()
    labels = ["".join(node.itertext()).strip() for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text"]
    missing = [label for label in expected_labels if labels.count(label) == 0]
    duplicated = [label for label in expected_labels if labels.count(label) > 1]
    boxes = []
    for index, node in enumerate(n for n in root.iter() if n.tag.rsplit("}", 1)[-1] == "text"):
        text = "".join(node.itertext()).strip()
        try:
            x, y = float(node.attrib.get("x", 0)), float(node.attrib.get("y", 0))
            size = float(re.sub(r"[^0-9.]", "", node.attrib.get("font-size", "16")) or 16)
        except ValueError:
            continue
        boxes.append({"id": f"{index}:{text}", "bbox": [x, y-size, x + max(size*.55*len(text), 1), y]})
    collisions = find_collisions(boxes)
    status = "FAIL" if missing or duplicated or collisions else "PASS"
    return {"status": status, "missing": missing, "duplicated": duplicated, "collisions": collisions,
            "raster_label_check": "VISUAL_QA_REQUIRED"}


def audit_print_toc(extracted_text: str, waived: bool = False) -> dict:
    present = bool(re.search(r"(?im)^\s*(contents|table of contents)\s*$", extracted_text))
    return {"status": "PASS" if present or waived else "FAIL", "present": present, "waived": waived}


def audit_epub_toc(path: Path, waived_reader_toc: bool = False) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        opf_name = next((n for n in names if n.endswith(".opf")), None)
        nav_name = next((n for n in names if n.endswith("nav.xhtml")), None)
        if not opf_name or not nav_name:
            return {"status": "FAIL", "navigation": False, "reader_facing": False, "targets_resolve": False}
        opf = archive.read(opf_name).decode("utf-8", "replace")
        nav = archive.read(nav_name).decode("utf-8", "replace")
        targets = re.findall(r'<a\s+[^>]*href="([^"#]+)', nav)
        base = Path(nav_name).parent
        resolve = bool(targets) and all(str((base / target).as_posix()) in names for target in targets)
        id_match = re.search(r'<item[^>]+href="[^"]*nav\.xhtml"[^>]+id="([^"]+)"|<item[^>]+id="([^"]+)"[^>]+href="[^"]*nav\.xhtml"', opf)
        nav_id = next((g for g in id_match.groups() if g), None) if id_match else None
        reader = bool(nav_id and re.search(rf'<itemref[^>]+idref="{re.escape(nav_id)}"', opf))
        ok = resolve and (reader or waived_reader_toc)
        return {"status": "PASS" if ok else "FAIL", "navigation": bool(nav_name), "reader_facing": reader,
                "targets_resolve": resolve, "waived_reader_toc": waived_reader_toc}


def high_risk_pages(page_records: list[dict]) -> list[int]:
    required_kinds = {"front_matter", "toc", "first_chapter", "worksheet", "index", "crosswalk", "last_page"}
    pages = {p["page"] for p in page_records if p.get("kind") in required_kinds or p.get("near_boundary")}
    if page_records:
        pages.add(max(page_records, key=lambda p: p.get("text_density", 0))["page"])
        pages.add(max(page_records, key=lambda p: p.get("visual_density", 0))["page"])
    return sorted(pages)
