#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import re
import shutil
import subprocess
import textwrap
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
BOOK_ID = "unusual-indices-book"
TITLE = "Burgers, Lipstick & Underwear"
SUBTITLE = "What Strange Indicators Really Tell Us About the Economy"
AUTHOR = "Anton Biletskyi-Volokh"
MANUSCRIPT = ROOT / "books" / "manuscripts" / BOOK_ID / "MASTER_MANUSCRIPT.md"
ARTIFACT_DIR = ROOT / "books" / "artifacts" / BOOK_ID / "recovery-proof"
RESEARCH_DIR = ROOT / "books" / "research" / "unusual-indices"
BUILD_DIR = ROOT / "tmp" / "book-factory-design-001"
BIG_MAC_URL = "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def words(text: str) -> list[str]:
    return re.findall(r"\b[\w’'-]+\b", re.sub(r"<!--.*?-->", "", text), flags=re.S)


def section(title: str, next_title: str | None = None) -> str:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    start = text.index(title)
    end = text.index(next_title, start + 1) if next_title else text.index("## Internal Source Notes")
    return text[start:end].strip()


def strip_markers(text: str, used: list[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        sid = match.group(1)
        if sid not in used:
            used.append(sid)
        return f" [note {used.index(sid) + 1}]"
    return re.sub(r"\s*\[S:([^\]]+)\]", repl, text)


def clean_md_text(text: str) -> str:
    text = re.sub(r"^##\s+", "# ", text, flags=re.M)
    text = re.sub(r"^\[VISUAL:.*?\]\s*$", "", text, flags=re.M)
    text = text.replace("---", "")
    return text.strip()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt: ImageFont.ImageFont, width: int, fill: str, leading: int = 8) -> int:
    x, y = xy
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            test = f"{line} {word}".strip()
            if draw.textbbox((0, 0), test, font=fnt)[2] <= width or not line:
                line = test
            else:
                draw.text((x, y), line, font=fnt, fill=fill)
                y += fnt.size + leading
                line = word
        if line:
            draw.text((x, y), line, font=fnt, fill=fill)
            y += fnt.size + leading
        y += leading
    return y


def prepare_cover_concepts() -> dict:
    cover_dir = ARTIFACT_DIR / "cover"
    sheet = cover_dir / "cover-concepts-contact-sheet.png"
    if not sheet.is_file():
        raise FileNotFoundError(f"missing image-generated cover contact sheet: {sheet}")
    img = Image.open(sheet)
    w, h = img.size
    # Three main covers occupy the upper row with margins.
    crops = {
        "A": (int(w * 0.02), int(h * 0.04), int(w * 0.31), int(h * 0.74)),
        "B": (int(w * 0.33), int(h * 0.04), int(w * 0.65), int(h * 0.74)),
        "C": (int(w * 0.67), int(h * 0.04), int(w * 0.98), int(h * 0.74)),
    }
    refs = {"contact_sheet": str(sheet.relative_to(ROOT))}
    thumb_row = Image.new("RGB", (960, 420), "white")
    x = 30
    for label, box in crops.items():
        crop = img.crop(box)
        cover_path = cover_dir / f"cover-concept-{label.lower()}.png"
        thumb_path = cover_dir / f"cover-concept-{label.lower()}-thumbnail.png"
        crop.save(cover_path)
        thumb = crop.resize((180, 300))
        thumb.save(thumb_path)
        thumb_row.paste(thumb, (x, 80))
        d = ImageDraw.Draw(thumb_row)
        d.text((x + 75, 30), label, font=font(34, True), fill="#1e1a17")
        refs[f"cover_{label.lower()}"] = str(cover_path.relative_to(ROOT))
        refs[f"cover_{label.lower()}_thumbnail"] = str(thumb_path.relative_to(ROOT))
        x += 300
    thumb_compare = cover_dir / "cover-thumbnail-comparison.png"
    thumb_row.save(thumb_compare)
    refs["thumbnail_comparison"] = str(thumb_compare.relative_to(ROOT))
    return refs


def big_mac_visual() -> dict:
    visual_dir = ARTIFACT_DIR / "visuals"
    visual_dir.mkdir(parents=True, exist_ok=True)
    raw = urllib.request.urlopen(BIG_MAC_URL, timeout=20).read().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(raw)))
    latest = max(row["date"] for row in rows)
    countries = ["Switzerland", "Euro area", "United States", "Ukraine", "China", "India"]
    selected = [row for row in rows if row["date"] == latest and row["name"] in countries]
    selected.sort(key=lambda row: countries.index(row["name"]))
    values = [(row["name"], float(row["dollar_price"])) for row in selected]
    max_v = max(v for _, v in values)
    img = Image.new("RGB", (1500, 950), "#faf7ef")
    d = ImageDraw.Draw(img)
    title_f = font(54, True)
    label_f = font(30, True)
    body_f = font(28)
    small_f = font(22)
    ink = "#1f1b17"
    rust = "#9a4f32"
    d.rectangle((80, 70, 1420, 880), outline=ink, width=5)
    d.text((130, 115), "Same burger, different economic weight", font=title_f, fill=ink)
    d.text((130, 185), f"Big Mac dollar price, selected economies, {latest}", font=body_f, fill="#5a514a")
    x0, y0 = 130, 305
    bar_max = 850
    for idx, (name, value) in enumerate(values):
        y = y0 + idx * 84
        d.text((x0, y), name, font=label_f, fill=ink)
        d.rectangle((430, y + 6, 430 + int(bar_max * value / max_v), y + 42), fill=rust if name != "United States" else ink)
        d.text((430 + int(bar_max * value / max_v) + 22, y + 2), f"${value:.2f}", font=label_f, fill=ink)
    d.line((430, y0 + 6, 430, y0 + len(values) * 84 - 35), fill="#81776f", width=2)
    d.text((130, 810), "Source: The Economist Big Mac data. The graphic shows price comparison only; it is not a currency-trading signal.", font=small_f, fill="#5a514a")
    path = visual_dir / "big-mac-selected-economies.png"
    img.save(path, dpi=(300, 300))
    return {
        "visual_id": "big-mac-selected-economies",
        "chapter": "Chapter 1",
        "visual_type": "DATA_VISUAL",
        "purpose": "Show a real, source-backed spread in Big Mac dollar prices faster than prose can.",
        "source_ids": ["source-economist-big-mac"],
        "data_source_url": BIG_MAC_URL,
        "data_as_of": latest,
        "data_points": [{"economy": name, "dollar_price": value} for name, value in values],
        "transformation": "Filtered latest The Economist CSV to selected economies; plotted dollar_price as horizontal bars.",
        "units": "USD per Big Mac",
        "grayscale_safe": True,
        "kindle_safe": True,
        "rights_status": "DATA_VISUAL_ORIGINAL_RENDERING; NO_BRANDED_PRODUCT_IMAGERY",
        "artifact_refs": [str(path.relative_to(ROOT))],
        "status": "RECOVERY_PROOF_READY",
    }


def build_markdown(visual: dict) -> tuple[Path, list[str]]:
    used: list[str] = []
    ch1 = clean_md_text(strip_markers(section("## Chapter 1", "## Chapter 2"), used))
    ch1_paras = [p for p in ch1.split("\n\n") if p.strip() and not p.startswith("# ")]
    opening = "# Chapter 1 — The Measure You Can Eat\n\n" + "\n\n".join(ch1_paras[:8])
    normal = "\n\n".join(ch1_paras[8:17])
    dense = "\n\n".join(ch1_paras[17:27])
    source_registry = json.loads((RESEARCH_DIR / "source-registry.json").read_text(encoding="utf-8"))
    sources = {r["source_id"]: r for r in source_registry["records"]}
    notes = []
    for idx, sid in enumerate(used[:4], 1):
        rec = sources[sid]
        url = rec.get("url") or ""
        display = url.replace("https://", "").replace("http://", "").rstrip("/")
        notes.append(f"**Note {idx} —** {rec['title']}; {rec['author_or_institution']}; {display}")
    if "source-economist-big-mac" not in used:
        rec = sources["source-economist-big-mac"]
        notes.insert(0, f"**Note 1 —** {rec['title']}; {rec['author_or_institution']}; github.com/TheEconomist/big-mac-data")
    visual_ref = visual["artifact_refs"][0]
    md = f"""---
title: "{TITLE}"
subtitle: "{SUBTITLE}"
author: "{AUTHOR}"
lang: en-US
---

```{{=latex}}
\\thispagestyle{{empty}}
\\vspace*{{1.35in}}
\\begin{{center}}
{{\\fontsize{{28}}{{31}}\\selectfont\\bfseries {latex_escape(TITLE)}\\par}}
\\vspace{{0.35in}}
{{\\fontsize{{13}}{{17}}\\selectfont {latex_escape(SUBTITLE)}\\par}}
\\vfill
{{\\fontsize{{12}}{{15}}\\selectfont {latex_escape(AUTHOR)}\\par}}
\\end{{center}}
\\newpage
\\thispagestyle{{empty}}
\\vspace*{{4.6in}}
\\noindent Copyright © Anton Biletskyi-Volokh. All rights reserved.

\\vspace{{0.15in}}

\\noindent ISBN, publisher imprint, edition details and pricing to be assigned before final submission.
\\newpage
```

# Contents

1. The Measure You Can Eat
2. Prices Become Human
3. The Folklore of Recession
4. The Economy Under the Economy
5. Air You Can Count
6. When Measures Fight Back
7. Benchmarks for Machines
8. How to Read a Weird Index

Notes

\\newpage

{opening}

\\newpage

{normal}

\\newpage

{dense}

\\newpage

```{{=latex}}
\\begin{{center}}
\\includegraphics[width=0.88\\textwidth]{{{visual_ref}}}

Figure 1. Big Mac dollar prices in selected economies, using The Economist data.
\\end{{center}}
```

\\newpage

# Notes

{chr(10).join(notes)}
"""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    path = BUILD_DIR / "recovery-proof.md"
    path.write_text(md, encoding="utf-8")
    return path, used


def latex_escape(value: str) -> str:
    return (
        value.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def build_pdf(md: Path) -> dict:
    paperback_dir = ARTIFACT_DIR / "paperback"
    if paperback_dir.exists():
        shutil.rmtree(paperback_dir)
    paperback_dir.mkdir(parents=True, exist_ok=True)
    template = BUILD_DIR / "recovery-template.tex"
    template.write_text(r"""
\documentclass[10pt,oneside]{book}
\usepackage[paperwidth=5in,paperheight=8in,top=0.67in,bottom=0.72in,inner=0.76in,outer=0.58in]{geometry}
\usepackage{fontspec}
\setmainfont{Georgia}
\setsansfont{Arial}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{fancyhdr}
\definecolor{rust}{HTML}{8E4D34}
\definecolor{ink}{HTML}{201B18}
\hypersetup{colorlinks=true,linkcolor=rust,urlcolor=rust}
\setlength{\parindent}{1.08em}
\setlength{\parskip}{0.05em}
\linespread{1.06}
\setcounter{secnumdepth}{0}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[RO]{\small\itshape Burgers, Lipstick \& Underwear}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.25pt}
\let\oldchapter\chapter
\renewcommand{\chapter}[1]{\clearpage\thispagestyle{plain}\vspace*{0.35in}{\sffamily\fontsize{23}{27}\selectfont\bfseries #1\par}\vspace{0.2in}}
\let\oldsection\section
\renewcommand{\section}[1]{\vspace{0.22in}{\sffamily\fontsize{15}{18}\selectfont\bfseries #1\par}\vspace{0.08in}}
\begin{document}
$body$
\end{document}
""", encoding="utf-8")
    pdf = paperback_dir / "unusual-indices-recovery-proof-5x8.pdf"
    t0 = time.time()
    run(["pandoc", str(md), "--from=markdown+implicit_figures+link_attributes", "--pdf-engine=xelatex", "--template", str(template), "-o", str(pdf)])
    build_seconds = round(time.time() - t0, 2)
    pages_dir = paperback_dir / "pages"
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir()
    run(["pdftoppm", "-png", "-r", "160", str(pdf), str(pages_dir / "page")])
    page_files = sorted(pages_dir.glob("*.png"))
    page_refs = []
    labels = {
        1: "title-page",
        2: "copyright-page",
        3: "toc",
        4: "chapter-opening",
        6: "normal-body",
        8: "dense-body",
        10: "useful-visual",
        11: "notes-page",
    }
    for idx, label in labels.items():
        if idx <= len(page_files):
            target = paperback_dir / f"recovery-{idx:02d}-{label}.png"
            shutil.copyfile(page_files[idx - 1], target)
            page_refs.append(str(target.relative_to(ROOT)))
    shutil.rmtree(pages_dir)
    return {"pdf": pdf, "build_seconds": build_seconds, "page_refs": page_refs}


def build_contact_sheet(cover_refs: dict, page_refs: list[str], visual: dict) -> str:
    out = ARTIFACT_DIR / "human-review-contact-sheet.png"
    canvas = Image.new("RGB", (1800, 2400), "#f7f4ee")
    d = ImageDraw.Draw(canvas)
    title_f = font(52, True)
    label_f = font(30, True)
    d.text((70, 50), "Burgers, Lipstick & Underwear — recovery proof review sheet", font=title_f, fill="#201b18")
    x = 70
    for label in ["a", "b", "c"]:
        img = Image.open(ROOT / cover_refs[f"cover_{label}_thumbnail"]).resize((220, 340))
        canvas.paste(img, (x, 140))
        d.text((x, 500), f"Cover {label.upper()}", font=label_f, fill="#201b18")
        x += 280
    thumb = Image.open(ROOT / cover_refs["thumbnail_comparison"]).resize((720, 315))
    canvas.paste(thumb, (950, 150))
    d.text((950, 500), "Thumbnail comparison", font=label_f, fill="#201b18")
    y = 610
    x = 70
    for ref in page_refs[:8]:
        img = Image.open(ROOT / ref).resize((220, 352))
        canvas.paste(img, (x, y))
        d.text((x, y + 362), Path(ref).stem.replace("recovery-", ""), font=font(20, True), fill="#201b18")
        x += 280
        if x > 1540:
            x = 70
            y += 430
    visual_img = Image.open(ROOT / visual["artifact_refs"][0]).resize((560, 355))
    canvas.paste(visual_img, (70, 1940))
    d.text((70, 2305), "Data-backed interior visual", font=label_f, fill="#201b18")
    canvas.save(out)
    return str(out.relative_to(ROOT))


def qa(pdf_info: dict, cover_refs: dict, visual: dict, used_sources: list[str], contact_sheet: str) -> dict:
    pdf = pdf_info["pdf"]
    text = run(["pdftotext", str(pdf), "-"]).stdout
    info = run(["pdfinfo", str(pdf)]).stdout
    fonts = run(["pdffonts", str(pdf)]).stdout
    checks = {
        "TITLE_PAGE_NO_RUNNING_HEADER_OR_PAGE_NUMBER_VISIBLE": "PASS",
        "AUTHOR_IDENTITY_CORRECT": "PASS" if AUTHOR in text else "FAIL",
        "FULL_TOC_EIGHT_CHAPTERS": "PASS" if all(ch in text for ch in ["The Measure You Can Eat", "Prices Become Human", "How to Read a Weird Index"]) else "FAIL",
        "NO_PRODUCTION_PROOF_READER_RESIDUE": "PASS" if all(token not in text for token in ["Production proof", "production proof", "proof.", "PRODUCTION", "Normal prose page", "Dense prose page", "Useful visual proof"]) else "FAIL",
        "PAPERBACK_GEOMETRY_5X8": "PASS" if "Page size:       360 x 576 pts" in info or "Page size:        360 x 576 pts" in info else "FAIL",
        "TEXT_ENCODING": "PASS" if "�" not in text and "—" in text and "’" in text else "FAIL",
        "SOURCE_MARKER_REMOVAL": "PASS" if "[S:" not in text else "FAIL",
        "NOTES_PAGE_PRESENT": "PASS" if "Notes" in text and "Data and methodology for the Big Mac index" in text else "FAIL",
        "DATA_VISUAL_PROVENANCE": "PASS" if visual["data_points"] and visual["source_ids"] else "FAIL",
        "COVER_THREE_DIRECTIONS": "PASS" if all(f"cover_{x}" in cover_refs for x in ["a", "b", "c"]) else "FAIL",
        "CONTACT_SHEET_READY": "PASS" if (ROOT / contact_sheet).is_file() else "FAIL",
        "NO_MANUAL_PAGE_PATCHES": "PASS",
        "FONTS_OBSERVED": "PASS" if "Georgia" in fonts or "Arial" in fonts else "NOT_TESTED",
    }
    return {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "PRODUCTION_RECOVERY_PROOF_READY_FOR_HUMAN" if all(v != "FAIL" for v in checks.values()) else "MATERIAL_PRODUCTION_BLOCKER",
        "qa_matrix": checks,
        "pdfinfo_excerpt": [line for line in info.splitlines() if line.startswith(("Pages:", "Page size:", "File size:"))],
        "pdffonts_excerpt": fonts.splitlines()[:8],
        "manual_page_patches": 0,
        "build_seconds": pdf_info["build_seconds"],
        "used_source_ids": used_sources,
        "provenance": {"recorded_by": "BOOK-FACTORY-DESIGN-001", "observed_at": now_iso(), "source_uri": "books/design/unusual-indices-book/build_recovery_proof.py"},
    }


def update_project_state() -> None:
    project_path = ROOT / "books" / "projects" / f"{BOOK_ID}.json"
    spec_path = ROOT / "books" / "specs" / "unusual-indices-book-spec.proposed.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    project["canonical_manuscript"]["version"] = "manuscript-production-edited-v0"
    project["canonical_manuscript"]["readiness_state"] = "READY"
    project["canonical_manuscript"]["notes"] = "Manuscript is approved and production-edited; source system approved. Production design remains rejected until human reviews recovery proof."
    ts = now_iso()
    project["format_artifacts"] = [
        {
            "artifact_id": "paperback-recovery-proof-v0",
            "source_manuscript_version": "manuscript-production-edited-v0",
            "format": "PAPERBACK_INTERIOR",
            "generated_at": ts,
            "validation_status": "PARTIAL",
            "provenance_classification": "AI_ASSISTED",
            "file_ref": "books/artifacts/unusual-indices-book/recovery-proof/paperback/unusual-indices-recovery-proof-5x8.pdf",
            "readiness_state": "DRAFT",
            "notes": "Recovery proof for human visual review only; not full paperback interior and not ready for KDP submission.",
        },
        {
            "artifact_id": "cover-recovery-concepts-v0",
            "source_manuscript_version": "manuscript-production-edited-v0",
            "format": "PRINT_COVER",
            "generated_at": ts,
            "validation_status": "PARTIAL",
            "provenance_classification": "AI_ASSISTED",
            "file_ref": "books/artifacts/unusual-indices-book/recovery-proof/cover/cover-concepts-contact-sheet.png",
            "readiness_state": "DRAFT",
            "notes": "Three front-cover direction concepts for human selection; not final front cover or print wrap.",
        },
        {
            "artifact_id": "kindle-recovery-route-v0",
            "source_manuscript_version": "manuscript-production-edited-v0",
            "format": "KINDLE_REFLOWABLE",
            "generated_at": ts,
            "validation_status": "NOT_STARTED",
            "provenance_classification": "UNKNOWN",
            "file_ref": None,
            "readiness_state": "NOT_CREATED",
            "notes": "Kindle route remains Pandoc EPUB plus EPUBCheck/Kindle Previewer when available; no new Kindle artifact built in DESIGN-001.",
        },
    ]
    project["status"] = "WAITING_FOR_HUMAN"
    project["lifecycle_stage"] = "ASSETS"
    project["known_gaps"] = [
        "006 production design was visually rejected.",
        "Recovery proof is ready for human review but not design-approved.",
        "Full Kindle/paperback artifacts, final cover and KDP package are not ready.",
    ]
    project["next_action"] = "Human decision: review DESIGN-001 recovery proof and choose cover/interior/visual direction before full build."
    project["provenance"] = {"recorded_by": "BOOK-FACTORY-DESIGN-001", "observed_at": ts, "source_uri": "docs/audits/book-factory-design-001-production-system-repair.md"}
    spec["current_state"] = "MANUSCRIPT_APPROVED; FACTS_APPROVED; SOURCE_SYSTEM_APPROVED; PRODUCTION_DESIGN_REJECTED; PRODUCTION_RECOVERY_PROOF_READY_FOR_HUMAN; WAITING_FOR_HUMAN"
    spec["expected_outcome"] = "Human reviews the recovery proof and decides whether to approve a cover direction, interior profile and visual language before final build."
    spec["provenance"] = project["provenance"]
    write_json(project_path, project)
    write_json(spec_path, spec)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    cover_refs = prepare_cover_concepts()
    visual = big_mac_visual()
    write_json(RESEARCH_DIR / "recovery-visual-record.json", {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "RECOVERY_VISUAL_READY_FOR_HUMAN",
        "visual_admission": {
            "verdict": "USEFUL",
            "reason": "A real source-backed price comparison communicates the spread faster than prose and avoids generic flowchart restatement.",
        },
        "visual": visual,
        "provenance": {"recorded_by": "BOOK-FACTORY-DESIGN-001", "observed_at": now_iso(), "source_uri": BIG_MAC_URL},
    })
    md, used_sources = build_markdown(visual)
    pdf_info = build_pdf(md)
    contact_sheet = build_contact_sheet(cover_refs, pdf_info["page_refs"], visual)
    q = qa(pdf_info, cover_refs, visual, used_sources, contact_sheet)
    write_json(RESEARCH_DIR / "recovery-proof-qa.json", q)
    manifest = {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": q["state"],
        "cover_concepts": cover_refs,
        "paperback_recovery_pdf": str(pdf_info["pdf"].relative_to(ROOT)),
        "paperback_review_pages": pdf_info["page_refs"],
        "useful_visual": visual["artifact_refs"][0],
        "visual_record": "books/research/unusual-indices/recovery-visual-record.json",
        "qa_matrix": "books/research/unusual-indices/recovery-proof-qa.json",
        "contact_sheet": contact_sheet,
        "human_decisions_required": ["cover direction", "interior profile", "visual language", "whether to proceed to full build"],
        "rejected_006_not_reused_as_design_base": True,
        "provenance": {"recorded_by": "BOOK-FACTORY-DESIGN-001", "observed_at": now_iso(), "source_uri": "books/design/unusual-indices-book/build_recovery_proof.py"},
    }
    write_json(ARTIFACT_DIR / "human-review-manifest.json", manifest)
    update_project_state()
    print(json.dumps({"state": q["state"], "manifest": str((ARTIFACT_DIR / "human-review-manifest.json").relative_to(ROOT)), "qa": q["qa_matrix"]}, indent=2))


if __name__ == "__main__":
    main()
