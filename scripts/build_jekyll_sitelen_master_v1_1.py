#!/usr/bin/env python3
"""Build the Jekyll V1.1 paperback without changing the V1 source or artifacts."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ContentStream

import build_jekyll_sitelen_master_v1 as v1

ROOT = v1.ROOT
PROD = ROOT / "artifacts/jekyll-toki-pona-production-v1-1"
PDF = ROOT / "output/pdf/jekyll-toki-pona-sitelen-pona-paperback-interior-v1-1.pdf"
V1_PDF = ROOT / "output/pdf/jekyll-toki-pona-sitelen-pona-paperback-interior-v1.pdf"
V1_MANIFEST = v1.PROD / "JEKYLL_SITELEN_PAPERBACK_BUILD_MANIFEST_V1.json"
TITLE_TP = "lipu pi jan Jekil en jan Hata"
AUTHOR_TP = "jan Lowi Sutiwen"
TITLE_EN = "THE STRANGE CASE OF DR. JEKYLL AND MR. HYDE"
AUTHOR_EN = "ROBERT LOUIS STEVENSON"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)


def checked_art() -> list[dict]:
    art = []
    for art_id, contract in v1.ART.items():
        source = v1.ART_SOURCE / f"{art_id}.png"
        derivative = v1.ART_PRINT / f"{art_id}-gray.png"
        if not source.is_file() or digest(source) != contract["sha256"] or not derivative.is_file():
            raise SystemExit(f"FAIL CLOSED: approved {art_id} art or V1 print derivative missing/changed.")
        with Image.open(source) as image:
            if image.size != (1024, 1536) or image.mode != "RGB":
                raise SystemExit(f"FAIL CLOSED: {art_id} source geometry changed.")
        with Image.open(derivative) as image:
            if image.size != (1024, 1536) or image.mode != "L":
                raise SystemExit(f"FAIL CLOSED: {art_id} print geometry changed.")
        art.append({"id": art_id, "sourceSha256": digest(source),
                    "printSha256": digest(derivative), "printPath": str(derivative.relative_to(ROOT))})
    return art


def make_tex(blocks: list[dict], chapters: list[dict], terms: list[tuple[str, str]],
             names: list[tuple[str, str]]) -> str:
    note = v1.note_tex(v1.simple_markdown(v1.NOTE))
    source = v1.tex_source(blocks, chapters, note, terms, names)
    title = (r"\thispagestyle{plain}\begin{center}\vspace*{0.55in}"
             r"{\large\bfseries THE STRANGE CASE OF DR. JEKYLL\\AND MR. HYDE}\par\vspace{0.65em}"
             r"{\Large\bfseries " + v1.tex(TITLE_TP) + r"}\par\vspace{0.20em}"
             r"{\sitelen\fontsize{17}{23}\selectfont " + v1.layout_glyph(TITLE_TP) + r"}\par\vspace{1.55em}"
             r"{\large\bfseries " + v1.tex(AUTHOR_EN) + r"}\par\vspace{0.20em}"
             r"{\Large\bfseries " + v1.tex(AUTHOR_TP) + r"}\par\vspace{0.15em}"
             r"{\sitelen\fontsize{18}{24}\selectfont " + v1.layout_glyph(AUTHOR_TP) + r"}\par\vspace{1.6em}"
             r"{\large\bfseries Toki Pona Edition\\with Sitelen Pona}\end{center}\clearpage")
    original_title = re.search(r"(?<=\\begin\{document\}\n).*?(?=\n\\plate\{plate:open\})", source, re.S)
    if not original_title or "English source" not in original_title.group():
        raise SystemExit("FAIL CLOSED: V1 title template changed; cannot apply controlled V1.1 patch.")
    source = source[:original_title.start()] + title + source[original_title.end():]
    original_macro = re.search(r"\\newcommand\{\\guideentry\}\[2\]\{[^\n]+", source)
    if not original_macro or r"\par\hspace*" not in original_macro.group():
        raise SystemExit("FAIL CLOSED: V1 guide template changed.")
    inline = (r"\newcommand{\guideentry}[2]{\noindent\textbf{#1}\enspace --- "
              r"\textit{#2}\enspace{\sitelen\fontsize{11}{14}\selectfont"
              r"\special{pdf:literal direct /Artifact BMC}#2"
              r"\special{pdf:literal direct EMC}}\par\vspace{0.32em}}")
    source = source[:original_macro.start()] + inline + source[original_macro.end():]
    ending = (r"\thispagestyle{empty}\vspace*{1.0in}\begin{center}{\Large\bfseries READER KIT}"
              r"\end{center}\vspace{1em}")
    before, sep, after = source.partition(ending)
    if not sep or not after.endswith(r"\end{document}" + "\n"):
        raise SystemExit("FAIL CLOSED: V1 reader-kit template changed.")
    source = before + r"\end{document}" + "\n"
    for art_id in ("J-OPEN", "J-CLOSE"):
        source = source.replace(f"art/print/{art_id}-gray.png",
                                str(v1.ART_PRINT / f"{art_id}-gray.png"))
    if "READER KIT" in source or "English source → Toki Pona Latin" in source:
        raise SystemExit("FAIL: deleted reader-facing scaffolding remains in TeX.")
    return source


def image_bounds(page) -> list[tuple[float, float, float, float]]:
    """Return image placements from the PDF graphics-state matrices, in points."""
    stream = ContentStream(page.get_contents(), page.pdf)
    ctm = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    stack = []
    boxes = []
    xobjects = page["/Resources"].get("/XObject", {})
    for args, op in stream.operations:
        if op == b"q":
            stack.append(ctm)
        elif op == b"Q":
            ctm = stack.pop()
        elif op == b"cm":
            a, b, c, d, e, f = (float(x) for x in args)
            A, B, C, D, E, F = ctm
            ctm = (A*a+C*b, B*a+D*b, A*c+C*d, B*c+D*d, A*e+C*f+E, B*e+D*f+F)
        elif op == b"Do":
            object_name = args[0]
            if object_name in xobjects and xobjects[object_name].get_object().get("/Subtype") == "/Image":
                a, b, c, d, e, f = ctm
                points = ((e, f), (a+e, b+f), (c+e, d+f), (a+c+e, b+d+f))
                boxes.append((min(x for x, _ in points), min(y for _, y in points),
                              max(x for x, _ in points), max(y for _, y in points)))
    return boxes


def verify_pdf(pdf: Path, raw: Path, blocks: list[dict], terms: list[tuple[str, str]],
               names: list[tuple[str, str]], artifact: dict, v1_hash: str) -> dict:
    reader = PdfReader(str(pdf))
    pages = len(reader.pages)
    if digest(V1_PDF) != v1_hash:
        raise SystemExit("FAIL: V1 PDF changed during V1.1 production.")
    if any((float(p.mediabox.width), float(p.mediabox.height)) != (396.0, 612.0)
           for p in reader.pages):
        raise SystemExit("FAIL: trim is not 5.5 x 8.5 inches on every page.")
    if sum(len(p.get("/Annots", [])) for p in reader.pages):
        raise SystemExit("FAIL: unexpected PDF annotations.")
    aux = (PROD / "jekyll-toki-pona-sitelen-paperback-v1-1.aux").read_text(errors="replace")
    labels = v1.page_labels(aux)
    if len([k for k in labels if k.startswith("blk:")]) != 462:
        raise SystemExit("FAIL: 462 block labels not present in V1.1 pagination.")
    if labels.get("plate:open") != 2 or labels.get("plate:close") != pages:
        raise SystemExit(f"FAIL: J-OPEN/J-CLOSE end sequence wrong: {labels.get('plate:open')}, {labels.get('plate:close')}/{pages}.")
    physical_start = physical_end = 0
    for number, page in enumerate(reader.pages, 1):
        depth = 0
        for args, op in ContentStream(page.get_contents(), reader).operations:
            if op == b"BMC" and args and str(args[0]) == "/Artifact":
                depth += 1; physical_start += 1
            elif op == b"EMC":
                depth -= 1; physical_end += 1
            if depth not in (0, 1):
                raise SystemExit(f"FAIL: Artifact nesting malformed on page {number}.")
        if depth:
            raise SystemExit(f"FAIL: unclosed Artifact on page {number}.")
    if artifact["logicalGlyphUnits"] != 481 or physical_start != physical_end != artifact["physicalSpans"]:
        raise SystemExit("FAIL: logical glyph-unit invariant or physical Artifact balance failed.")
    if physical_start != artifact["physicalSpans"]:
        raise SystemExit("FAIL: physical Artifact count differs from repair record.")
    qpdf = run("qpdf", "--check", str(pdf))
    if "warning" in (qpdf.stdout + qpdf.stderr).lower():
        raise SystemExit("FAIL: qpdf reported warnings.")
    fonts = run("pdffonts", str(pdf)).stdout
    font_rows = fonts.splitlines()[2:]
    if any(not re.search(r"\byes\b", row) for row in font_rows if row.strip()):
        raise SystemExit("FAIL: unembedded font.")
    if "Georgia" not in fonts or "nasin" not in fonts.lower():
        raise SystemExit("FAIL: required typefaces missing.")
    text_result = run("pdftotext", "-layout", str(pdf), "-")
    if text_result.stderr.strip():
        raise SystemExit("FAIL: Poppler text warning: " + text_result.stderr[:300])
    all_text = text_result.stdout
    title_text = run("pdftotext", "-f", "1", "-l", "1", "-layout", str(pdf), "-").stdout
    for value in ("THE STRANGE CASE OF DR. JEKYLL", "lipu pi jan Jekil en jan Hata",
                  AUTHOR_EN, AUTHOR_TP, "Toki Pona Edition", "with Sitelen Pona"):
        if value not in title_text:
            raise SystemExit(f"FAIL: title page layer missing: {value}")
    for forbidden in ("English source → Toki Pona Latin", "READER KIT",
                      "This page follows the closing illustration"):
        if forbidden in all_text:
            raise SystemExit(f"FAIL: removed scaffolding still present: {forbidden}")
    if "\\" in title_text and "English source" in title_text:
        raise SystemExit("FAIL: old title legend survives.")
    log = (PROD / "jekyll-toki-pona-sitelen-paperback-v1-1.log").read_text(errors="replace")
    overfull = re.findall(r"Overfull \\[hv]box[^\n]*", log)
    if overfull:
        raise SystemExit(f"FAIL: {len(overfull)} overfull boxes; first: {overfull[0]}")
    images = run("pdfimages", "-list", str(pdf)).stdout.splitlines()[2:]
    if len(images) != 2 or sorted(int(row.split()[0]) for row in images) != [2, pages]:
        raise SystemExit("FAIL: expected two images on opening and closing pages.")
    bounds = {}
    for page_num in (2, pages):
        placements = image_bounds(reader.pages[page_num-1])
        if len(placements) != 1:
            raise SystemExit(f"FAIL: image placement not unique on page {page_num}.")
        x0, y0, x1, y1 = placements[0]
        if min(x0, y0, 396-x1, 612-y1) < 36:
            raise SystemExit(f"FAIL: illustration outside 0.5-inch non-bleed area on page {page_num}: {placements[0]}")
        bounds[str(page_num)] = [round(v, 2) for v in placements[0]]
    if len(blocks) != 462 or len(terms)+len(names) != 19 or artifact["logicalGlyphUnits"] != 462+19:
        raise SystemExit("FAIL: content coverage changed.")
    return {"pages": pages, "labels": labels, "fontRows": font_rows,
            "artifact": artifact, "imageBoundsPt": bounds, "overfullBoxes": len(overfull),
            "popplerWarnings": 0, "qpdf": "PASS", "embeddedFonts": "PASS"}


def render_contacts(pdf: Path, check: dict) -> dict:
    pages, labels = check["pages"], check["labels"]
    renders = PROD / "renders"
    renders.mkdir(parents=True, exist_ok=True)
    all_dir = renders / "full"
    all_dir.mkdir(exist_ok=True)
    result = run("pdftoppm", "-png", "-r", "36", str(pdf), str(all_dir / "page"))
    if result.stderr.strip():
        raise SystemExit("FAIL: Poppler render warning: " + result.stderr[:300])
    all_images = sorted(all_dir.glob("page-*.png"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    if len(all_images) != pages:
        raise SystemExit("FAIL: full-book render coverage mismatch.")
    contacts = PROD / "contact-sheets"
    contacts.mkdir(exist_ok=True)
    full = []
    for start in range(0, pages, 24):
        path = contacts / f"full-book-{start+1:03d}-{min(start+24,pages):03d}.png"
        v1.contact(all_images[start:start+24], path, cols=6, cell=(188, 290))
        full.append(str(path.relative_to(ROOT)))
    selected = renders / "selected"
    selected.mkdir(exist_ok=True)
    groups = {
        "title-front-matter": list(range(1, labels["front:terms"])),
        "recurring-anchors-and-terms": list(range(labels["front:terms"], labels["front:names"])),
        "name-guide": list(range(labels["front:names"], labels["chapter:1"])),
        "final-six-pages": list(range(max(1,pages-5), pages+1)),
    }
    output = {}
    for name, page_numbers in groups.items():
        images = []
        for number in page_numbers:
            dest = selected / f"{name}-p{number:03d}.png"
            v1.render_page(pdf, number, dest, dpi=125)
            images.append(dest)
        if not images:
            raise SystemExit(f"FAIL: no pages found for {name}.")
        sheet = contacts / f"{name}.png"
        v1.contact(images, sheet, cols=min(4,len(images)), cell=(360, 555))
        output[name] = {"pages": page_numbers, "contactSheet": str(sheet.relative_to(ROOT)),
                        "renders": [str(p.relative_to(ROOT)) for p in images]}
    return {"fullBook": full, "required": output}


def main() -> None:
    old = json.loads(V1_MANIFEST.read_text())
    old_hash = digest(V1_PDF)
    if old_hash != old["pdfSha256"]:
        raise SystemExit("FAIL CLOSED: V1 PDF differs from V1 manifest before build.")
    blocks, chapters = v1.read_blocks()
    terms, names = v1.glossary_entries()
    if ("Dr. Henry Jekyll", "jan Jekil") not in names or ("Mr. Edward Hyde", "jan Hata") not in names:
        raise SystemExit("FAIL CLOSED: approved character-name forms differ from the Name Guide.")
    checked = checked_art()
    PROD.mkdir(parents=True, exist_ok=True)
    PDF.parent.mkdir(parents=True, exist_ok=True)
    tex = PROD / "jekyll-toki-pona-sitelen-paperback-v1-1.tex"
    tex.write_text(make_tex(blocks, chapters, terms, names), encoding="utf-8")
    for _ in range(2):
        proc = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                               "-file-line-error", tex.name], cwd=PROD, text=True,
                              capture_output=True)
        if proc.returncode:
            raise SystemExit("FAIL: XeLaTeX compilation failed:\n" + proc.stdout[-1800:])
    raw = PROD / "jekyll-toki-pona-sitelen-paperback-v1-1.pdf"
    artifact = v1.close_artifact_spans_at_page_breaks(raw, PDF)
    check = verify_pdf(PDF, raw, blocks, terms, names, artifact, old_hash)
    contacts = render_contacts(PDF, check)
    if digest(V1_PDF) != old_hash or digest(v1.TEXT_LOCK) != v1.EXPECTED_LOCK:
        raise SystemExit("FAIL: V1 PDF or Text Lock changed after render.")
    old_blocks = old["blocks"]
    invariant = all(a["english"] == b["english"] and a["tpLatin"] == b["tpLatin"]
                    and a["glyphInput"] == b["glyphInput"] for a,b in zip(old_blocks,blocks))
    if len(old_blocks) != 462 or not invariant:
        raise SystemExit("FAIL: V1-to-V1.1 block content identity changed.")
    manifest = {"schemaVersion": "1.0", "artifact": "JEKYLL_SITELEN_PAPERBACK_BUILD_V1_1",
        "status": "PREFLIGHT_PASS_AWAITING_HUMAN_PAPERBACK_REVIEW", "profile": "paperback",
        "outputPdf": str(PDF.relative_to(ROOT)), "pdfSha256": digest(PDF),
        "v1PdfSha256": old_hash, "v1ManifestSha256": digest(V1_MANIFEST),
        "textLockSha256": digest(v1.TEXT_LOCK), "v4LedgerSha256": digest(v1.LEDGER),
        "sourceBoundarySha256": digest(v1.BOUNDARY), "fontSha256": digest(v1.FONT),
        "titleMetadata": {"english": TITLE_EN, "tokiPonaLatin": TITLE_TP,
                          "authorEnglish": AUTHOR_EN, "authorTokiPonaLatin": AUTHOR_TP,
                          "glyphRenderingSource": "same exact title/author Latin strings; existing pinned sitelen font",
                          "glyphMetadataUnitsOutsideContentInvariant": 2},
        "counts": {"english": 462, "tpLatin": 462, "glyphInput": 462,
                   "existingLogicalGlyphUnits": 481, "glossaryTerms": len(terms),
                   "nameGuideEntries": len(names)},
        "pageCount": check["pages"], "trimPt": {"width": 396, "height": 612},
        "illustrations": checked, "preflight": {k:v for k,v in check.items() if k not in {"labels", "fontRows"}},
        "pageLabels": check["labels"], "contactSheets": contacts,
        "blocks": [{**b, "page": check["labels"][f"blk:{b['ordinal']:03d}"]} for b in blocks],
        "v1ToV1_1ContentIdentity": "PASS"}
    manifest_path = PROD / "JEKYLL_SITELEN_PAPERBACK_BUILD_MANIFEST_V1_1.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    report = ("# Jekyll paperback interior V1.1 — preflight\n\n"
              "**PASS — technical paperback preflight; human print review remains separate.**\n\n"
              f"- PDF: `{manifest['outputPdf']}`; SHA-256 `{manifest['pdfSha256']}`.\n"
              f"- V1 PDF preserved: `{old_hash}`. Text Lock preserved: `{manifest['textLockSha256']}`.\n"
              f"- Pages: {check['pages']}; trim: 5.5 × 8.5 in. J-OPEN page 2; J-CLOSE final page {check['pages']}.\n"
              f"- English / TP Latin / glyph inputs: 462 / 462 / 462, exact V1 content identity PASS.\n"
              f"- Existing logical glyph units: 481; page-local physical Artifact pairs: {artifact['physicalSpans']}/{artifact['physicalSpans']}; page-break continuations: {artifact['pageBreakContinuations']}. Two new decorative title-metadata glyph renderings are not included in the 481 content units.\n"
              "- Title page: three-layer title and author PASS; old technical legend absent PASS.\n"
              "- Guides: inline three-layer template applied to every term and name; page-level contact sheets generated.\n"
              "- Reader Kit standalone page absent; closing illustration is the final physical page.\n"
              "- qpdf PASS; Poppler warnings 0; fonts embedded PASS; overfull boxes 0; KDP non-bleed illustration margin ≥ 0.5 in PASS.\n"
              "- No translation, chapter, Text Lock, Kindle, cover, KDP, commit, push, or API changes.\n")
    report_path = PROD / "JEKYLL_SITELEN_PAPERBACK_PREFLIGHT_V1_1.md"
    report_path.write_text(report, encoding="utf-8")
    print(json.dumps({"status": "PASS", "pdf": str(PDF), "sha256": manifest["pdfSha256"],
                      "pages": check["pages"], "artifact": artifact,
                      "manifest": str(manifest_path), "report": str(report_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
