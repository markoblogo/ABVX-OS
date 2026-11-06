#!/usr/bin/env python3
"""Add final-page-number Contents and PDF outlines to the immutable Jekyll V1.1 interior."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter

import build_jekyll_sitelen_master_v1 as v1
import build_jekyll_sitelen_master_v1_1 as v11

ROOT = v1.ROOT
PROD = ROOT / "artifacts/jekyll-toki-pona-production-v1-2"
PDF = ROOT / "output/pdf/jekyll-toki-pona-sitelen-pona-paperback-interior-v1-2.pdf"
V11_PDF = v11.PDF
V11_MANIFEST = v11.PROD / "JEKYLL_SITELEN_PAPERBACK_BUILD_MANIFEST_V1_1.json"
JOB = "jekyll-toki-pona-sitelen-paperback-v1-1"  # isolated V1.2 workdir; reused validator's job name


def canonical_entries(chapters: list[dict]) -> list[tuple[str, str]]:
    front = [("A Note on This Translation", "front:note"),
             ("Recurring Anchors and Terms", "front:terms"),
             ("Name Guide", "front:names")]
    return front + [(chapter["title"], f"chapter:{chapter['chapter']}") for chapter in chapters]


def tex_with_contents(blocks: list[dict], chapters: list[dict],
                      terms: list[tuple[str, str]], names: list[tuple[str, str]]) -> str:
    source = v11.make_tex(blocks, chapters, terms, names)
    replacements = [
        (r"\chapter*{A Note on This Translation}\markboth",
         r"\chapter*{A Note on This Translation}\addcontentsline{toc}{chapter}{A Note on This Translation}\markboth"),
        (r"\chapter*{Recurring Anchors and Terms}\markboth",
         r"\chapter*{Recurring Anchors and Terms}\addcontentsline{toc}{chapter}{Recurring Anchors and Terms}\markboth"),
        (r"\chapter*{Name Guide}\markboth",
         r"\chapter*{Name Guide}\addcontentsline{toc}{chapter}{Name Guide}\markboth"),
    ]
    for old, new in replacements:
        if source.count(old) != 1:
            raise SystemExit(f"FAIL CLOSED: V1.1 front-matter heading changed: {old}")
        source = source.replace(old, new, 1)
    for chapter in chapters:
        heading = v1.tex(chapter["title"])
        old = (r"\clearpage\thispagestyle{plain}\markboth{" + heading + "}{" + heading + "}")
        new = (r"\clearpage\thispagestyle{plain}\addcontentsline{toc}{chapter}{"
               + heading + r"}\markboth{" + heading + "}{" + heading + "}")
        if source.count(old) != 1:
            raise SystemExit(f"FAIL CLOSED: locked chapter heading changed: {chapter['title']}")
        source = source.replace(old, new, 1)
    old = r"\normalsize\clearpage" + "\n" + r"\chapter*{Recurring Anchors and Terms}"
    new = (r"\normalsize\clearpage" + "\n" + r"\tableofcontents\label{front:contents}\clearpage"
           + "\n" + r"\chapter*{Recurring Anchors and Terms}")
    if source.count(old) != 1:
        raise SystemExit("FAIL CLOSED: V1.1 note-to-guide boundary changed.")
    source = source.replace(old, new, 1)
    return source


def add_outlines(source: Path, output: Path, entries: list[tuple[str, str]], labels: dict[str, int]) -> None:
    reader = PdfReader(str(source))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    for title, label in entries:
        writer.add_outline_item(title, labels[label]-1)
    writer.write(str(output))


def validate_contents(pdf: Path, entries: list[tuple[str, str]], labels: dict[str, int],
                      pages: int) -> dict:
    toc_path = PROD / f"{JOB}.toc"
    toc_source = toc_path.read_text(encoding="utf-8", errors="replace")
    source_entries = re.findall(r"\\contentsline\s*\{chapter\}\{([^}]*)\}\{(\d+)\}", toc_source)
    expected = [(title, labels[label]) for title, label in entries]
    if source_entries != [(title, str(page)) for title, page in expected]:
        raise SystemExit(f"FAIL: TeX Contents differs from final page labels: {source_entries!r}")
    first = labels["front:note"]+1
    last = labels["front:terms"]-1
    if not (1 <= first <= last < pages):
        raise SystemExit("FAIL: Contents is not between note and glossary.")
    extraction = subprocess.run(["pdftotext", "-f", str(first), "-l", str(last),
                                 "-layout", str(pdf), "-"], text=True, capture_output=True, check=True)
    if extraction.stderr.strip():
        raise SystemExit("FAIL: Poppler warning on Contents: " + extraction.stderr[:300])
    visible = extraction.stdout
    from abvx_harness.book_preflight import audit_print_toc_parity
    parity = audit_print_toc_parity(
        visible,
        [{"title": title, "page": page} for title, page in expected],
        {title: labels[label] for title, label in entries},
    )
    if parity["status"] != "PASS":
        raise SystemExit(f"FAIL: reusable print Contents parity check: {parity['failures']}")
    if not re.search(r"(?m)^\s*Contents\s*$", visible):
        raise SystemExit("FAIL: visible Contents heading missing.")
    normalized = re.sub(r"\s+", " ", visible)
    cursor = 0
    rows = []
    for title, page in expected:
        index = normalized.find(title, cursor)
        if index < 0:
            raise SystemExit(f"FAIL: visible Contents entry absent or out of order: {title}")
        remainder = normalized[index+len(title):]
        number = re.search(r"\b(\d+)\b", remainder)
        if not number or int(number.group(1)) != page:
            raise SystemExit(f"FAIL: printed Contents page number wrong for {title}: {remainder[:60]!r}")
        cursor = index + len(title) + number.end()
        destination = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page),
                                      "-layout", str(pdf), "-"], text=True, capture_output=True, check=True)
        if destination.stderr.strip() or title not in re.sub(r"\s+", " ", destination.stdout):
            raise SystemExit(f"FAIL: Contents destination page {page} does not show {title}")
        rows.append({"title": title, "printedPage": page, "actualDestinationPage": page,
                     "sourceLabel": label_for_title(title, entries)})
    reader = PdfReader(str(pdf))
    if len(reader.outline) != len(entries):
        raise SystemExit("FAIL: PDF outline count differs from Contents entries.")
    for item, (title, page) in zip(reader.outline, expected):
        if item.title != title or reader.get_destination_page_number(item) != page-1:
            raise SystemExit(f"FAIL: PDF outline mismatch: {title}")
    return {"status": "PASS", "visibleContents": "PASS", "contentsParity": "PASS",
            "pdfBookmarks": "PASS", "tocPages": list(range(first,last+1)),
            "entryCount": len(rows), "entries": rows}


def label_for_title(title: str, entries: list[tuple[str, str]]) -> str:
    return next(label for name, label in entries if name == title)


def extra_contacts(pdf: Path, labels: dict[str, int], pages: int) -> dict:
    selected = PROD / "renders/selected"
    sheets = PROD / "contact-sheets"
    selected.mkdir(parents=True, exist_ok=True)
    sheets.mkdir(parents=True, exist_ok=True)
    chapter_images = []
    for index in range(1, 11):
        page = labels[f"chapter:{index}"]
        image = selected / f"chapter-{index:02d}-p{page:03d}.png"
        v1.render_page(pdf, page, image, dpi=125)
        chapter_images.append(image)
    chapters_path = sheets / "all-chapter-openings.png"
    v1.contact(chapter_images, chapters_path, cols=5, cell=(300,465))
    art_images = []
    for name, page in (("J-OPEN",labels["plate:open"]),("J-CLOSE",labels["plate:close"])):
        image = selected / f"{name}-p{page:03d}.png"
        v1.render_page(pdf, page, image, dpi=125)
        art_images.append(image)
    art_path = sheets / "J-OPEN-and-J-CLOSE.png"
    v1.contact(art_images, art_path, cols=2, cell=(510,790))
    return {"chapterOpenings": str(chapters_path.relative_to(ROOT)),
            "illustrations": str(art_path.relative_to(ROOT))}


def main() -> None:
    previous = json.loads(V11_MANIFEST.read_text(encoding="utf-8"))
    previous_hash = v11.digest(V11_PDF)
    v1_hash = v11.digest(v11.V1_PDF)
    if previous_hash != previous["pdfSha256"]:
        raise SystemExit("FAIL CLOSED: V1.1 PDF differs from its manifest.")
    if v1_hash != json.loads(v11.V1_MANIFEST.read_text())["pdfSha256"]:
        raise SystemExit("FAIL CLOSED: V1 PDF differs from its manifest.")
    blocks, chapters = v1.read_blocks()
    terms, names = v1.glossary_entries()
    art = v11.checked_art()
    entries = canonical_entries(chapters)
    PROD.mkdir(parents=True, exist_ok=True)
    PDF.parent.mkdir(parents=True, exist_ok=True)
    tex_file = PROD / f"{JOB}.tex"
    tex_file.write_text(tex_with_contents(blocks, chapters, terms, names), encoding="utf-8")
    for _ in range(3):
        result = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                                 "-file-line-error", tex_file.name], cwd=PROD, text=True,
                                capture_output=True)
        if result.returncode:
            raise SystemExit("FAIL: XeLaTeX compilation failed:\n" + result.stdout[-1800:])
    aux = (PROD / f"{JOB}.aux").read_text(encoding="utf-8", errors="replace")
    labels = v1.page_labels(aux)
    for _, label in entries:
        if label not in labels:
            raise SystemExit(f"FAIL: Contents destination label missing: {label}")
    raw = PROD / f"{JOB}.pdf"
    marked = PROD / "jekyll-v1-2-page-local-artifacts.pdf"
    artifact = v1.close_artifact_spans_at_page_breaks(raw, marked)
    add_outlines(marked, PDF, entries, labels)
    # Reuse the established V1.1 paperback preflight against isolated V1.2 artifacts.
    v11.PROD = PROD
    check = v11.verify_pdf(PDF, raw, blocks, terms, names, artifact, v1_hash)
    contents = validate_contents(PDF, entries, labels, check["pages"])
    from abvx_harness.publishing_gates import local_production_authorization
    gate = local_production_authorization({"technical":"PASS","visible_contents":"PASS",
                                           "contents_parity":"PASS"})
    if gate["status"] != "LOCAL_PRODUCTION_PASS":
        raise SystemExit("FAIL: reusable local production Contents gate blocked the build.")
    contacts = v11.render_contacts(PDF, check)
    contacts["extra"] = extra_contacts(PDF, labels, check["pages"])
    if v11.digest(V11_PDF) != previous_hash or v11.digest(v11.V1_PDF) != v1_hash:
        raise SystemExit("FAIL: V1 or V1.1 changed during build.")
    old_blocks = previous["blocks"]
    if len(old_blocks) != 462 or any(
        any(left[key] != right[key] for key in ("english", "tpLatin", "glyphInput"))
        for left,right in zip(old_blocks, blocks)
    ):
        raise SystemExit("FAIL: V1.1-to-V1.2 locked story content changed.")
    manifest = {
        "schemaVersion":"1.0", "artifact":"JEKYLL_SITELEN_PAPERBACK_BUILD_V1_2",
        "status":"LOCAL_PRODUCTION_PASS_AWAITING_HUMAN_REVIEW", "profile":"paperback",
        "outputPdf":str(PDF.relative_to(ROOT)), "pdfSha256":v11.digest(PDF),
        "v1PdfSha256":v1_hash, "v1_1PdfSha256":previous_hash,
        "textLockSha256":v11.digest(v1.TEXT_LOCK), "v4LedgerSha256":v11.digest(v1.LEDGER),
        "sourceBoundarySha256":v11.digest(v1.BOUNDARY), "fontSha256":v11.digest(v1.FONT),
        "titleMetadata":previous["titleMetadata"], "pageCount":check["pages"],
        "trimPt":{"width":396,"height":612}, "counts":{"english":462,"tpLatin":462,
             "glyphInput":462,"existingLogicalGlyphUnits":481,"glossaryTerms":len(terms),
             "nameGuideEntries":len(names)},
        "illustrations":art, "preflight":{k:v for k,v in check.items() if k not in {"labels","fontRows"}},
        "contents":contents, "localProductionContentsGate":gate,
        "pageLabels":labels, "contactSheets":contacts,
        "blocks":[{**block,"page":labels[f"blk:{block['ordinal']:03d}"]} for block in blocks],
        "v1_1ToV1_2ContentIdentity":"PASS",
        "kindleCreate":"NOT_STARTED", "kdp":"NOT_STARTED"}
    manifest_path = PROD / "JEKYLL_SITELEN_PAPERBACK_BUILD_MANIFEST_V1_2.json"
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    toc_report = ["# Jekyll V1.2 — Contents validation", "",
                  "**VISIBLE CONTENTS: PASS; CONTENTS PARITY: PASS; PDF BOOKMARKS: PASS.**", "",
                  "Source of headings: ten exact locked chapter headings; three existing reader guides.",
                  "The request's uppercase examples are display shorthand; the final Contents keeps the locked title-case headings, including the curly apostrophe in Chapters 9 and 10.", "",
                  f"Contents pages: {', '.join(map(str,contents['tocPages']))}; entries: {contents['entryCount']}.", "",
                  "| Section | Printed page | Actual heading page |",
                  "| --- | ---: | ---: |"]
    toc_report.extend(f"| {row['title']} | {row['printedPage']} | {row['actualDestinationPage']} |"
                      for row in contents["entries"])
    toc_report += ["", "Each number was checked against the final TeX label and the heading extracted from that exact PDF page; PDF outline destinations were verified separately.", ""]
    toc_path = PROD / "JEKYLL_CONTENTS_VALIDATION_V1_2.md"
    toc_path.write_text("\n".join(toc_report),encoding="utf-8")
    report = ("# Jekyll paperback interior V1.2 — preflight\n\n"
              "**LOCAL_PRODUCTION_PASS — awaiting owner Contents/pagination review.**\n\n"
              f"- PDF: `{manifest['outputPdf']}`; SHA-256 `{manifest['pdfSha256']}`.\n"
              f"- Pages: {check['pages']}; trim: 5.5 × 8.5 in. J-OPEN p.{labels['plate:open']}; J-CLOSE final p.{labels['plate:close']}.\n"
              f"- Visible Contents: PASS; {contents['entryCount']} entries; final page-number parity: PASS; PDF bookmarks: PASS.\n"
              "- Text Lock, English/TP Latin/glyph inputs: 462/462/462 unchanged; existing logical glyph units: 481.\n"
              f"- Page-local Artifact pairs: {artifact['physicalSpans']}/{artifact['physicalSpans']}; recomputed continuations: {artifact['pageBreakContinuations']}.\n"
              "- Title, Name Guide, Recurring Anchors, J-OPEN, J-CLOSE, fonts, qpdf, illustration safe area: PASS.\n"
              "- Poppler warnings: 0; overfull boxes: 0; placeholders: 0; Reader Kit service page: absent.\n"
              f"- V1 preserved `{v1_hash}`; V1.1 preserved `{previous_hash}`.\n"
              "- Kindle Create and KDP: NOT STARTED. No API/LLM calls.\n")
    report_path = PROD / "JEKYLL_SITELEN_PAPERBACK_PREFLIGHT_V1_2.md"
    report_path.write_text(report,encoding="utf-8")
    print(json.dumps({"status":"LOCAL_PRODUCTION_PASS","pdf":str(PDF),
                      "sha256":manifest["pdfSha256"],"pages":check["pages"],
                      "tocEntries":contents["entryCount"],"tocReport":str(toc_path),
                      "manifest":str(manifest_path),"preflight":str(report_path)},ensure_ascii=False))


if __name__ == "__main__":
    main()
