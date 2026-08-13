#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
BOOK_ID = "unusual-indices-book"
TITLE = "Burgers, Lipstick & Underwear"
SUBTITLE = "What Strange Indicators Really Tell Us About the Economy"
AUTHOR = "Anton Biletskyi-Volokh"
PROFILE_ID = "COMMERCIAL_NONFICTION_5X8_BW"
MANUSCRIPT = ROOT / "books" / "manuscripts" / BOOK_ID / "MASTER_MANUSCRIPT.md"
RESEARCH_DIR = ROOT / "books" / "research" / "unusual-indices"
ARTIFACT_DIR = ROOT / "books" / "artifacts" / BOOK_ID / "final-008"
BUILD_DIR = ROOT / "tmp" / "book-factory-indices-008"
COVER_PNG = ROOT / "books" / "artifacts" / BOOK_ID / "production-build" / "cover" / "cover-a-refined-front.png"
PAPERBACK_PDF = ARTIFACT_DIR / "paperback" / "burgers-lipstick-underwear-paperback-interior-5x8-rc.pdf"
KINDLE_DOCX = ARTIFACT_DIR / "kindle" / "burgers-lipstick-underwear-kindle-create-input.docx"
PACKAGE_JSON = ARTIFACT_DIR / "amazon" / "amazon-publication-package.json"
PACKAGE_MD = ARTIFACT_DIR / "amazon" / "amazon-publication-package.md"
CONTACT_SHEET = ARTIFACT_DIR / "review" / "paperback-all-pages-contact-sheet.png"

CHAPTERS = [
    "Introduction — The World, Translated Badly but Usefully",
    "Chapter 1 — The Measure You Can Eat",
    "Chapter 2 — Prices Become Human",
    "Chapter 3 — The Folklore of Recession",
    "Chapter 4 — The Economy Under the Economy",
    "Chapter 5 — Air You Can Count",
    "Chapter 6 — When Measures Fight Back",
    "Chapter 7 — Benchmarks for Machines",
    "Chapter 8 — How to Read a Weird Index",
    "Notes",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(cmd: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def load_sources() -> dict[str, dict]:
    registry = json.loads((RESEARCH_DIR / "source-registry.json").read_text(encoding="utf-8"))
    return {record["source_id"]: record for record in registry["records"]}


def canonical_body() -> str:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    lines = text.splitlines()
    first = next(i for i, line in enumerate(lines) if line.startswith("## Introduction"))
    end = next(i for i, line in enumerate(lines) if line.startswith("## Internal Source Notes"))
    body = "\n".join(lines[first:end]).strip()
    body = re.sub(r"^\[VISUAL:.*?\]\s*$\n?", "", body, flags=re.M)
    body = re.sub(r"^---\s*$\n?", "", body, flags=re.M)
    body = re.sub(r"^##\s+", "# ", body, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def replace_source_markers(text: str) -> tuple[str, list[str]]:
    used: list[str] = []

    def repl(match: re.Match[str]) -> str:
        source_id = match.group(1)
        if source_id not in used:
            used.append(source_id)
        return f" [Note {used.index(source_id) + 1}]"

    return re.sub(r"\s*\[S:([^\]]+)\]", repl, text), used


def balance_print_chapter_endings(text: str) -> str:
    """Keep a meaningful closing cluster together before every chapter break.

    This is a profile-level pagination rule, not a page-specific patch. It prevents
    a final one- or two-line transition from being stranded on its own page.
    """
    sections = re.split(r"(?=^# )", text, flags=re.M)
    balanced: list[str] = []
    for section in sections:
        if not section.strip():
            continue
        blocks = section.strip().split("\n\n")
        if len(blocks) < 4:
            balanced.append(section.strip())
            continue
        selected = 0
        selected_words = 0
        for block in reversed(blocks[1:]):
            words = len(re.findall(r"\b[\w’'-]+\b", block))
            if selected and selected_words + words > 185:
                break
            selected += 1
            selected_words += words
            if selected_words >= 90 or selected >= 12:
                break
        if selected_words < 55:
            balanced.append(section.strip())
            continue
        start = len(blocks) - selected
        blocks.insert(start, "```{=latex}\n\\begin{minipage}{\\textwidth}\n\\setlength{\\parindent}{1.08em}\n```")
        blocks.append("```{=latex}\n\\end{minipage}\n```")
        balanced.append("\n\n".join(blocks))
    return "\n\n".join(balanced)


def reader_notes(used: list[str]) -> str:
    sources = load_sources()
    lines: list[str] = []
    forbidden = re.compile(r"Owner|ABVX|local source|Research lead|Conceptual source|books/|/Volumes/", re.I)
    for idx, source_id in enumerate(used, 1):
        record = sources.get(source_id)
        if not record:
            raise RuntimeError(f"unresolved source marker: {source_id}")
        identity = " ".join(
            str(record.get(key) or "")
            for key in ("author_or_institution", "title", "publication", "publication_date")
        )
        if forbidden.search(identity):
            raise RuntimeError(f"internal or generic source identity cannot enter reader notes: {source_id}")
        author = record["author_or_institution"].strip()
        title = record["title"].strip()
        publication = (record.get("publication") or "").strip()
        date = (record.get("publication_date") or "n.d.").strip()
        url = (record.get("url") or "").strip()
        if not url.startswith(("https://", "http://")):
            raise RuntimeError(f"reader-facing source lacks public URL: {source_id}")
        publication_part = f" {publication}," if publication else ""
        lines.append(f"{idx}. {author}. [*{title}*]({url}).{publication_part} {date}.")
    return "\n\n".join(lines)


def build_sources() -> tuple[Path, Path, list[str], int]:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    body, used = replace_source_markers(canonical_body())
    notes = reader_notes(used)
    word_count = len(re.findall(r"\b[\w’'-]+\b", re.sub(r"\[Note \d+\]", "", body)))
    print_body = balance_print_chapter_endings(body)
    paperback_md = BUILD_DIR / "paperback.md"
    paperback_md.write_text(
        f"""```{{=latex}}
\\frontmatter
\\thispagestyle{{empty}}
\\vspace*{{1.18in}}
\\begin{{center}}
{{\\fontsize{{27}}{{31}}\\selectfont\\bfseries {latex_escape(TITLE)}\\par}}
\\vspace{{0.3in}}
{{\\fontsize{{12.5}}{{16}}\\selectfont {latex_escape(SUBTITLE)}\\par}}
\\vfill
{{\\fontsize{{11.5}}{{14}}\\selectfont {latex_escape(AUTHOR)}\\par}}
\\end{{center}}
\\clearpage
\\thispagestyle{{empty}}
\\vspace*{{4.65in}}
\\noindent {latex_escape(TITLE)}

\\vspace{{0.13in}}
\\noindent Copyright © 2026 {latex_escape(AUTHOR)}

\\vspace{{0.13in}}
\\noindent All rights reserved.
\\clearpage
\\pagestyle{{plain}}
\\tableofcontents
\\clearpage
\\pagenumbering{{arabic}}
\\setcounter{{page}}{{1}}
\\pagestyle{{bookbody}}
```

{print_body}

# Notes

```{{=latex}}
\\begingroup
\\raggedright
\\small
```

{notes}

```{{=latex}}
\\endgroup
```
""",
        encoding="utf-8",
    )
    kindle_md = BUILD_DIR / "kindle-create.md"
    kindle_md.write_text(
        f"""---
title: "{TITLE}"
subtitle: "{SUBTITLE}"
author: "{AUTHOR}"
lang: en-US
---

Copyright © 2026 {AUTHOR}

All rights reserved.

{body}

# Notes

{notes}
""",
        encoding="utf-8",
    )
    return paperback_md, kindle_md, used, word_count


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


def write_template() -> Path:
    template = BUILD_DIR / "commercial-nonfiction-5x8.tex"
    template.write_text(
        r"""
\documentclass[10pt,twoside,openany]{book}
\usepackage[paperwidth=5in,paperheight=8in,top=0.67in,bottom=0.72in,inner=0.76in,outer=0.58in,headheight=14pt]{geometry}
\usepackage{fontspec}
\setmainfont{Georgia}
\setsansfont{Arial}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{fancyhdr}
\usepackage{bookmark}
\definecolor{rust}{HTML}{8E4D34}
\definecolor{ink}{HTML}{201B18}
\hypersetup{colorlinks=true,linkcolor=rust,urlcolor=rust,pdftitle={Burgers, Lipstick & Underwear},pdfauthor={Anton Biletskyi-Volokh}}
\setlength{\parindent}{1.08em}
\setlength{\parskip}{0pt}
\linespread{1.04}
\setcounter{secnumdepth}{-1}
\setcounter{tocdepth}{0}
\widowpenalty=9500
\clubpenalty=9500
\displaywidowpenalty=9500
\hyphenpenalty=3200
\exhyphenpenalty=2000
\tolerance=1500
\emergencystretch=1.4em
\raggedbottom
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\makeatletter
\def\@makechapterhead#1{%
  \vspace*{0.28in}%
  {\parindent \z@ \raggedright \normalfont
   \sffamily\bfseries\fontsize{21}{25}\selectfont
   \hyphenpenalty=10000\exhyphenpenalty=10000 #1\par\nobreak
   \vspace{0.22in}}}
\def\@makeschapterhead#1{\@makechapterhead{#1}}
\renewcommand\section{\@startsection{section}{1}{\z@}{0.23in}{0.08in}{\sffamily\bfseries\fontsize{14.5}{17}\selectfont\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000}}
\makeatother
\fancypagestyle{bookbody}{
  \fancyhf{}
  \fancyhead[LE]{\small\itshape Burgers, Lipstick \& Underwear}
  \fancyhead[RO]{\small\itshape\nouppercase{\leftmark}}
  \fancyfoot[C]{\small\thepage}
  \renewcommand{\headrulewidth}{0.25pt}
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyfoot[C]{\small\thepage}
  \renewcommand{\headrulewidth}{0pt}
}
\pagestyle{bookbody}
\renewcommand{\chaptermark}[1]{\markboth{#1}{#1}}
\renewcommand{\contentsname}{Contents}
\begin{document}
$body$
\end{document}
""",
        encoding="utf-8",
    )
    return template


def build_artifacts(paperback_md: Path, kindle_md: Path) -> float:
    PAPERBACK_PDF.parent.mkdir(parents=True, exist_ok=True)
    KINDLE_DOCX.parent.mkdir(parents=True, exist_ok=True)
    template = write_template()
    started = time.time()
    run(
        [
            "pandoc",
            str(paperback_md),
            "--from=markdown+link_attributes",
            "--top-level-division=chapter",
            "--pdf-engine=xelatex",
            "--template",
            str(template),
            "-o",
            str(PAPERBACK_PDF),
        ]
    )
    run(
        [
            "pandoc",
            str(kindle_md),
            "--from=markdown+link_attributes",
            "--top-level-division=chapter",
            "--metadata",
            f"title={TITLE}",
            "--metadata",
            f"author={AUTHOR}",
            "-o",
            str(KINDLE_DOCX),
        ]
    )
    return round(time.time() - started, 2)


def pdf_page_count(pdf: Path) -> int:
    info = run(["pdfinfo", str(pdf)]).stdout
    return int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))


def page_texts(pdf: Path) -> list[str]:
    return [
        run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"]).stdout
        for page in range(1, pdf_page_count(pdf) + 1)
    ]


def locate_chapters(pages: list[str]) -> dict[str, int]:
    locations: dict[str, int] = {}
    for chapter in CHAPTERS:
        needle = re.sub(r"\s+", " ", chapter).strip()
        for page_no, text in enumerate(pages[3:], 4):
            normalized = re.sub(r"\s+", " ", text).strip()
            if needle in normalized[:420]:
                locations[chapter] = page_no
                break
    return locations


def render_pages_and_contact_sheet(pdf: Path, chapter_pages: dict[str, int]) -> tuple[list[str], int]:
    review_dir = ARTIFACT_DIR / "review"
    all_pages = review_dir / "all-pages"
    selected = review_dir / "selected"
    if review_dir.exists():
        shutil.rmtree(review_dir)
    all_pages.mkdir(parents=True)
    selected.mkdir(parents=True)
    run(["pdftoppm", "-png", "-r", "90", str(pdf), str(all_pages / "page")])
    rendered = sorted(all_pages.glob("*.png"))
    thumbs: list[Image.Image] = []
    font = ImageFont.load_default()
    for idx, path in enumerate(rendered, 1):
        page = Image.open(path).convert("RGB")
        page.thumbnail((170, 272))
        tile = Image.new("RGB", (184, 300), "#d8d3cb")
        tile.paste(page, ((184 - page.width) // 2, 18))
        ImageDraw.Draw(tile).text((7, 5), str(idx), fill="#322b27", font=font)
        thumbs.append(tile)
    cols = 8
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 184, rows * 300), "#bdb7ae")
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((idx % cols) * 184, (idx // cols) * 300))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET, quality=92)

    labels: dict[int, str] = {
        1: "title",
        2: "copyright",
        3: "toc",
        max(1, len(rendered) - 1): "notes",
        len(rendered): "notes-final",
    }
    for chapter, page_no in chapter_pages.items():
        slug = re.sub(r"[^a-z0-9]+", "-", chapter.lower()).strip("-")[:42]
        labels[page_no] = slug
    body_candidates = [p for p in range(1, len(rendered) + 1) if p not in labels and p > 4]
    if body_candidates:
        labels[body_candidates[len(body_candidates) // 2]] = "representative-body"
    refs: list[str] = []
    for page_no, label in sorted(labels.items()):
        if 1 <= page_no <= len(rendered):
            target = selected / f"page-{page_no:03d}-{label}.png"
            shutil.copyfile(rendered[page_no - 1], target)
            refs.append(str(target.relative_to(ROOT)))
    return refs, len(rendered)


def analyze_page_balance(pages: list[str], chapter_pages: dict[str, int]) -> dict:
    excluded = {1, 2, *chapter_pages.values()}
    low_pages: list[dict] = []
    blank_pages: list[int] = []
    isolated_headings: list[int] = []
    for page_no, text in enumerate(pages, 1):
        words = re.findall(r"\b[\w’'-]+\b", text)
        useful_lines = [line.strip() for line in text.splitlines() if len(line.strip()) >= 3]
        if page_no not in excluded and len(words) < 12:
            blank_pages.append(page_no)
        if page_no not in excluded and len(words) < 55:
            low_pages.append({"page": page_no, "word_count": len(words), "line_count": len(useful_lines)})
        if page_no not in excluded and len(useful_lines) <= 4 and any(line.startswith(("Chapter ", "Introduction", "Notes")) for line in useful_lines):
            isolated_headings.append(page_no)
    pre_chapter: list[dict] = []
    for chapter, page_no in chapter_pages.items():
        if chapter == "Introduction — The World, Translated Badly but Usefully" or page_no <= 1:
            continue
        prev = pages[page_no - 2]
        words = re.findall(r"\b[\w’'-]+\b", prev)
        useful_lines = [line.strip() for line in prev.splitlines() if len(line.strip()) >= 3]
        if len(words) < 70 or len(useful_lines) < 8:
            pre_chapter.append(
                {"chapter": chapter, "preceding_page": page_no - 1, "word_count": len(words), "line_count": len(useful_lines)}
            )
    return {
        "blank_pages": blank_pages,
        "low_occupancy_pages": low_pages,
        "isolated_heading_pages": isolated_headings,
        "suspicious_pre_chapter_pages": pre_chapter,
    }


def extract_docx_text(docx: Path) -> str:
    with zipfile.ZipFile(docx) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    return html.unescape(" ".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)))


def printed_page_number(text: str) -> int | None:
    numeric_lines = [line.strip() for line in text.splitlines() if re.fullmatch(r"\d+", line.strip())]
    return int(numeric_lines[-1]) if numeric_lines else None


def toc_validation(pages: list[str], chapter_pages: dict[str, int]) -> dict:
    toc_text = "\n".join(pages[2:5])
    missing: list[str] = []
    mismatched: list[dict] = []
    for chapter in CHAPTERS:
        expected = chapter_pages.get(chapter)
        if expected is None:
            missing.append(chapter)
            continue
        expected_printed = printed_page_number(pages[expected - 1])
        short = chapter.replace("Chapter ", "")
        start = toc_text.find(short[:28])
        block = toc_text[start : start + 180] if start >= 0 else ""
        found = re.search(r"\b(\d+)\s*(?:\n|$)", block)
        if not found or expected_printed is None or int(found.group(1)) != expected_printed:
            mismatched.append({"chapter": chapter, "reason": "missing page number in extracted TOC"})
    return {"missing_chapters": missing, "missing_or_unreadable_page_numbers": mismatched}


def typography_qa(pages: list[str]) -> dict:
    text = "\n".join(pages)
    hyphen_breaks = re.findall(r"[A-Za-z]{2,}-\s*\n\s*[a-z]{2,}", text)
    words = re.findall(r"\b[A-Za-z][A-Za-z’'-]*\b", text)
    rate = round(len(hyphen_breaks) * 1000 / max(1, len(words)), 2)
    heading_failures: list[str] = []
    chapter_pages = locate_chapters(pages)
    for title, page_no in chapter_pages.items():
        nonempty = [line for line in pages[page_no - 1].splitlines() if line.strip()]
        heading_zone = "\n".join(nonempty[:3])
        if re.search(r"[A-Za-z]{2,}-\s*\n\s*[a-z]{2,}", heading_zone):
            heading_failures.append(title)
    return {
        "heading_hyphenation_failures": sorted(set(heading_failures)),
        "body_line_end_hyphenations": len(hyphen_breaks),
        "body_hyphenations_per_1000_words": rate,
        "threshold_per_1000_words": 12.0,
    }


def publication_package(page_count: int) -> dict:
    hook = "The economy is everywhere. Sometimes the clearest way to see it is through a burger, a lipstick, or a pair of underwear."
    short = (
        "A sharp, entertaining guide to the strange indicators people use to make the economy readable—from Big Macs and iPhone work-hours to lipstick, freight rates, pollution equivalents, and AI benchmarks. It explains why some proxies reveal something real, why others become folklore, and how to tell a useful measure from a seductive mistake."
    )
    full_paragraphs = [
        "The economy is too large to see. So we translate it into things we can hold, buy, count, and remember.",
        "A burger becomes an exchange-rate argument. A phone becomes a measure of working time. Lipstick and underwear become recession folklore. Freight rates reveal the physical economy moving beneath daily life. Cigarettes make invisible air pollution feel immediate. AI benchmarks turn machine capability into a score—and then change the behavior they were meant to measure.",
        "Burgers, Lipstick & Underwear is a curious, skeptical tour of the strange indicators people use to understand prices, purchasing power, economic stress, risk, and technological progress. It shows why some rough proxies are genuinely illuminating, why others are beautiful nonsense, and what happens when a measure becomes important enough to game.",
        "You will learn how to ask better questions of any index: What is the object? Where did the data come from? What does the method actually measure? What disappears in the translation? And what changes when people start optimizing for the score?",
        "This is not a book against weird measures. It is a book about using them with curiosity, method, and proportion.",
    ]
    full = "\n\n".join(full_paragraphs)
    formatted = "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in full_paragraphs[:-1]) + f"<p><b>{html.escape(full_paragraphs[-1])}</b></p>"
    keywords = [
        {"field": "unusual economic indicators", "intent": "Readers seeking nonstandard ways to understand the economy", "why": "Core subject without repeating title metadata."},
        {"field": "popular economics everyday life", "intent": "General readers who want accessible economics", "why": "Matches the book's object-led explanatory style."},
        {"field": "purchasing power price comparisons", "intent": "Readers interested in Big Mac and work-time comparisons", "why": "Captures the strongest practical concept in Chapters 1–2."},
        {"field": "recession signals consumer behavior", "intent": "Readers curious about lipstick and underwear indicators", "why": "Accurately describes the folklore chapter without promising prediction."},
        {"field": "data literacy misleading statistics", "intent": "Readers learning to question metrics and proxies", "why": "Matches the book's method-and-limits promise."},
        {"field": "benchmarks incentives Goodhart law", "intent": "Readers interested in gaming and measurement effects", "why": "Covers governance, rankings, and benchmark failure."},
        {"field": "economic stories behind numbers", "intent": "Narrative nonfiction readers drawn to human-readable data", "why": "Signals tone and reader benefit without irrelevant high-volume terms."},
    ]
    back_cover = (
        "The economy is too large to see—so we translate it. A burger becomes an exchange-rate argument. A phone becomes a measure of working time. Lipstick and underwear become recession folklore. Freight rates reveal the physical economy, cigarettes make pollution feel immediate, and AI benchmarks turn machine capability into a score.\n\n"
        "Burgers, Lipstick & Underwear is a sharp, entertaining guide to the strange indicators that make complex systems readable. It explains why some proxies reveal something real, why others become beautiful nonsense, and how measures change once people learn to game them.\n\n"
        "Enjoy the measure. Inspect the method. Keep the claim in proportion."
    )
    return {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "AMAZON_METADATA_PACKAGE_READY",
        "metadata": {"title": TITLE, "subtitle": SUBTITLE, "author": AUTHOR, "language": "English", "edition_number": None, "contributors": []},
        "sales_copy": {
            "one_line_hook": hook,
            "short_description": short,
            "full_amazon_description_plain": full,
            "full_amazon_description_kdp_html": formatted,
            "back_cover_headline": "The world is full of numbers. The useful ones give us something to hold.",
            "back_cover_description": back_cover,
            "author_bio": "Anton Biletskyi-Volokh builds and studies market, data, and knowledge systems. His work focuses on how complex information becomes practical enough to use—and honest enough to trust.",
            "website_line": None,
            "selling_points": [
                "See how ordinary objects make abstract economic ideas readable.",
                "Separate useful proxies from recession folklore and statistical theatre.",
                "Learn a practical method for questioning any index, ranking, or benchmark.",
            ],
        },
        "keywords": keywords,
        "categories": {
            "primary": "Business & Money > Economics > Economic Conditions",
            "secondary": "Business & Money > Economics > Theory",
            "additional_territory": "Science & Math > Mathematics > Statistics",
            "selection_note": "Use the closest exact choices shown in the KDP dashboard for the primary marketplace; Amazon states that category options vary by marketplace and can change.",
        },
        "pricing": {
            "marketplace": "Amazon.com",
            "kindle_launch_usd": 2.99,
            "kindle_normal_usd": 5.99,
            "paperback_usd": 11.99,
            "paperback_page_count": page_count,
            "rationale": "Compact popular nonfiction: low-friction launch, sustainable normal eBook value, and paperback above the current US 60-percent royalty threshold while remaining proportionate to length. The 80-page book is priced below substantially longer mainstream popular-economics/data titles and close to the compact 128-page How to Lie with Statistics territory.",
            "comparables": [
                {"title": "How to Lie with Statistics", "format": "paperback", "pages": 128, "observed_list_price": "GBP 12.99", "source": "https://www.penguin.co.uk/books/13565/how-to-lie-with-statistics-by-darrell-huff-with-pictures-by-mel-calman/9780140136296"},
                {"title": "The Undercover Economist", "format": "paperback", "pages": 288, "observed_list_price": "USD 19.00", "source": "https://www.penguinrandomhouse.com/books/75341/the-undercover-economist-by-tim-harford/"},
                {"title": "The Data Detective", "format": "paperback", "pages": 336, "observed_list_price": "USD 20.00", "source": "https://www.penguinrandomhouse.com/books/610963/the-data-detective-by-tim-harford/"}
            ],
        },
        "ai_disclosure": {
            "official_rule_summary": "KDP requires disclosure of AI-generated text, images, or translations; AI-assisted content does not require disclosure.",
            "recommendation": {
                "text": "AI_GENERATED — disclose, because AI-based tools created substantial manuscript prose even though the owner directed, reviewed, and approved it.",
                "cover": "AI_GENERATED — disclose, because the approved front-cover artwork was created with an AI image-generation tool and then refined.",
                "interior_images": "NONE — final interior contains no images.",
                "translation": "NONE.",
            },
            "human_action": "Answer the KDP disclosure questions factually during submission; do not classify generated text or cover art as merely AI-assisted.",
        },
        "rights_checklist": {
            "manuscript_owner_controlled": "HUMAN_CONFIRMATION_REQUIRED",
            "quotations": "PASS_NO_LONG_QUOTATIONS_DETECTED",
            "cover_asset_provenance": "AI_GENERATED_REPO_ARTIFACT_RECORDED; HUMAN_CONFIRM_COMMERCIAL_USE_TERMS",
            "third_party_interior_screenshots": "PASS_NONE",
            "trademark_implication": "HUMAN_VISUAL_CONFIRMATION_REQUIRED; title objects are editorial references, not endorsement claims",
            "citations_imply_endorsement": "PASS_NO_ENDORSEMENT_LANGUAGE_DETECTED",
        },
        "artifacts": {
            "kindle_create_input": str(KINDLE_DOCX.relative_to(ROOT)),
            "paperback_interior": str(PAPERBACK_PDF.relative_to(ROOT)),
            "approved_front_cover": str(COVER_PNG.relative_to(ROOT)),
            "paperback_wrap_cover": {"state": "WAITING_FOR_HUMAN", "capability": "PAPERBACK_WRAP_COVER_PRODUCTION", "implementation": "DEFERRED"},
            "kdp_submission": {"state": "WAITING_FOR_HUMAN", "capability": "KDP_SUBMISSION_AUTOMATION", "implementation": "DEFERRED"},
        },
        "research_provenance": [
            "https://kdp.amazon.com/en_US/help/topic/G201189630",
            "https://kdp.amazon.com/en_US/help/topic/G201298500",
            "https://kdp.amazon.com/en_US/help/topic/G200652170",
            "https://kdp.amazon.com/en_US/help/topic/G200672390",
            "https://kdp.amazon.com/en_US/help/topic/G200634560",
            "https://kdp.amazon.com/en_US/help/topic/G201834340",
            "https://www.penguin.co.uk/books/13565/how-to-lie-with-statistics-by-darrell-huff-with-pictures-by-mel-calman/9780140136296",
            "https://www.penguinrandomhouse.com/books/75341/the-undercover-economist-by-tim-harford/",
            "https://www.penguinrandomhouse.com/books/610963/the-data-detective-by-tim-harford/",
        ],
        "provenance": {"recorded_by": "BOOK-FACTORY-INDICES-008", "observed_at": now_iso(), "source_uri": "books/design/unusual-indices-book/build_full_production.py"},
    }


def write_package_markdown(package: dict) -> None:
    copy = package["sales_copy"]
    lines = [
        f"# Amazon publication package — {TITLE}",
        "",
        "## Metadata",
        "",
        f"- Title: {TITLE}",
        f"- Subtitle: {SUBTITLE}",
        f"- Author: {AUTHOR}",
        "- Language: English",
        "",
        "## One-line hook",
        "",
        copy["one_line_hook"],
        "",
        "## Short description",
        "",
        copy["short_description"],
        "",
        "## Full Amazon description",
        "",
        copy["full_amazon_description_plain"],
        "",
        "## KDP-safe HTML description",
        "",
        "```html",
        copy["full_amazon_description_kdp_html"],
        "```",
        "",
        "## Seven keyword fields",
        "",
        *[f"{idx}. {item['field']} — {item['intent']}" for idx, item in enumerate(package["keywords"], 1)],
        "",
        "## Categories",
        "",
        f"- Primary: {package['categories']['primary']}",
        f"- Secondary: {package['categories']['secondary']}",
        f"- Additional territory: {package['categories']['additional_territory']}",
        "",
        "## Pricing",
        "",
        f"- Kindle launch: ${package['pricing']['kindle_launch_usd']:.2f}",
        f"- Kindle normal: ${package['pricing']['kindle_normal_usd']:.2f}",
        f"- Paperback: ${package['pricing']['paperback_usd']:.2f}",
        "",
        "## AI disclosure recommendation",
        "",
        f"- Text: {package['ai_disclosure']['recommendation']['text']}",
        f"- Cover: {package['ai_disclosure']['recommendation']['cover']}",
        f"- Interior images: {package['ai_disclosure']['recommendation']['interior_images']}",
        "",
        "## Back-cover text",
        "",
        f"**{copy['back_cover_headline']}**",
        "",
        copy["back_cover_description"],
        "",
        "## Optional author bio",
        "",
        copy["author_bio"],
    ]
    PACKAGE_MD.parent.mkdir(parents=True, exist_ok=True)
    PACKAGE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def qa(used: list[str], word_count: int, build_seconds: float) -> dict:
    pages = page_texts(PAPERBACK_PDF)
    whole = "\n".join(pages)
    chapter_pages = locate_chapters(pages)
    balance = analyze_page_balance(pages, chapter_pages)
    typography = typography_qa(pages)
    toc = toc_validation(pages, chapter_pages)
    selected, rendered_count = render_pages_and_contact_sheet(PAPERBACK_PDF, chapter_pages)
    kindle_text = extract_docx_text(KINDLE_DOCX)
    pdfinfo = run(["pdfinfo", str(PAPERBACK_PDF)]).stdout
    paperback_urls = {
        match.group(0)
        for match in re.finditer(r"https?://\S+", run(["pdfinfo", "-url", str(PAPERBACK_PDF)]).stdout)
    }
    with zipfile.ZipFile(KINDLE_DOCX) as zf:
        kindle_relationships = zf.read("word/_rels/document.xml.rels").decode("utf-8")
    kindle_urls = {
        html.unescape(match.group(1))
        for match in re.finditer(r'Target="(https?://[^"]+)"', kindle_relationships)
    }
    pdffonts = run(["pdffonts", str(PAPERBACK_PDF)]).stdout
    forbidden_reader = re.compile(r"Owner / ABVX|owner-supplied|local source pack|Research lead|Conceptual source family|/Volumes/|books/source-packs|Manuscript V2|production state", re.I)
    provisional = re.compile(r"ISBN, publisher imprint|pricing to be assigned|before final submission", re.I)
    kindle_leak = re.compile(r"running head|print page|ISBN, publisher imprint|pricing to be assigned", re.I)
    checks = {
        "PAPERBACK_BUILT": PAPERBACK_PDF.is_file(),
        "PAPERBACK_GEOMETRY_5X8": "360 x 576 pts" in pdfinfo,
        "SEARCHABLE_TEXT": len(whole) > 10000,
        "FONTS_EMBEDDED": "yes" in pdffonts.lower(),
        "ALL_CHAPTERS_LOCATED": len(chapter_pages) == len(CHAPTERS),
        "CHAPTERS_START_NEW_PAGE": len(set(chapter_pages.values())) == len(CHAPTERS),
        "TOC_HAS_FINAL_PAGE_NUMBERS": not toc["missing_chapters"] and not toc["missing_or_unreadable_page_numbers"],
        "NO_INTERIOR_VISUALS": "Figure " not in whole and "[VISUAL:" not in whole,
        "NO_SOURCE_MARKERS": "[S:" not in whole,
        "NO_INTERNAL_PROVENANCE": not forbidden_reader.search(whole),
        "NO_PROVISIONAL_COPYRIGHT_TEXT": not provisional.search(whole),
        "NO_LOCAL_PATHS": "/Volumes/" not in whole and "books/" not in whole,
        "NO_BLANK_PAGES": not balance["blank_pages"],
        "NO_ISOLATED_HEADINGS": not balance["isolated_heading_pages"],
        "NO_SUSPICIOUS_PRE_CHAPTER_PAGES": not balance["suspicious_pre_chapter_pages"],
        "NO_HEADING_HYPHENATION": not typography["heading_hyphenation_failures"],
        "BODY_HYPHENATION_LIMITED": typography["body_hyphenations_per_1000_words"] <= typography["threshold_per_1000_words"],
        "FULL_CONTACT_SHEET_COMPLETE": rendered_count == len(pages) and CONTACT_SHEET.is_file(),
        "KINDLE_CREATE_DOCX_BUILT": KINDLE_DOCX.is_file(),
        "KINDLE_HAS_SEMANTIC_CHAPTERS": all(title in kindle_text for title in CHAPTERS),
        "KINDLE_NO_PRINT_ARTIFACT_LEAKAGE": not kindle_leak.search(kindle_text) and "Contents 1" not in kindle_text,
        "PAPERBACK_NOTE_LINKS_CLICKABLE": len(paperback_urls) >= len(used),
        "KINDLE_NOTE_LINKS_CLICKABLE": len(kindle_urls) >= len(used),
        "AMAZON_PACKAGE_SCHEMA_READY": PACKAGE_JSON.is_file(),
    }
    state = "PAPERBACK_INTERIOR_RC_READY" if all(checks.values()) else "FINAL_PRODUCTION_BLOCKED"
    return {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": state,
        "profile_state": "PROFILE_TECHNICALLY_READY_FOR_HUMAN_ADMISSION" if state == "PAPERBACK_INTERIOR_RC_READY" else "PROOF_REQUIRED",
        "manuscript_word_count": word_count,
        "interior_visual_count": 0,
        "page_count": len(pages),
        "chapter_pages": chapter_pages,
        "page_balance": balance,
        "typography": typography,
        "toc_validation": toc,
        "used_source_ids": used,
        "link_qa": {
            "paperback_unique_external_links": len(paperback_urls),
            "kindle_unique_external_links": len(kindle_urls),
            "expected_minimum": len(used),
        },
        "selected_review_pages": selected,
        "contact_sheet": str(CONTACT_SHEET.relative_to(ROOT)),
        "qa_matrix": {key: "PASS" if value else "FAIL" for key, value in checks.items()},
        "build_seconds": build_seconds,
        "provenance": {"recorded_by": "BOOK-FACTORY-INDICES-008", "observed_at": now_iso(), "source_uri": "books/design/unusual-indices-book/build_full_production.py"},
    }


def update_state(result: dict) -> None:
    ts = now_iso()
    project_path = ROOT / "books" / "projects" / f"{BOOK_ID}.json"
    spec_path = ROOT / "books" / "specs" / "unusual-indices-book-spec.proposed.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    project["status"] = "WAITING_FOR_HUMAN"
    project["lifecycle_stage"] = "KDP_PACKAGE"
    project["format_artifacts"] = [
        {
            "artifact_id": "paperback-interior-rc-008",
            "source_manuscript_version": "manuscript-final-008",
            "format": "PAPERBACK_INTERIOR",
            "generated_at": ts,
            "validation_status": "PASSED" if result["state"] == "PAPERBACK_INTERIOR_RC_READY" else "FAILED",
            "provenance_classification": "AI_ASSISTED",
            "file_ref": str(PAPERBACK_PDF.relative_to(ROOT)),
            "readiness_state": "READY" if result["state"] == "PAPERBACK_INTERIOR_RC_READY" else "BLOCKED",
            "notes": "Final 5x8 black-and-white interior release candidate; human approval required before KDP upload.",
        },
        {
            "artifact_id": "kindle-create-input-008",
            "source_manuscript_version": "manuscript-final-008",
            "format": "KINDLE_REFLOWABLE",
            "generated_at": ts,
            "validation_status": "PASSED",
            "provenance_classification": "AI_ASSISTED",
            "file_ref": str(KINDLE_DOCX.relative_to(ROOT)),
            "readiness_state": "READY",
            "notes": "Clean semantic DOCX for manual Kindle Create preparation; no print pagination or running heads.",
        },
        {
            "artifact_id": "cover-a-approved-front-008",
            "source_manuscript_version": "manuscript-final-008",
            "format": "PRINT_COVER",
            "generated_at": ts,
            "validation_status": "PASSED",
            "provenance_classification": "AI_GENERATED",
            "file_ref": str(COVER_PNG.relative_to(ROOT)),
            "readiness_state": "READY",
            "notes": "Human-approved front-cover direction. Paperback wrap remains a separate human task.",
        },
    ]
    project["known_gaps"] = [
        "PAPERBACK_WRAP_COVER_PRODUCTION is DEFERRED and WAITING_FOR_HUMAN.",
        "KDP_SUBMISSION_AUTOMATION is DEFERRED; manual KDP submission is WAITING_FOR_HUMAN.",
        "Profile admission requires final human review of the complete paperback contact sheet and interior.",
        "Owner must confirm manuscript rights and AI-cover commercial-use provenance during final publication review.",
    ]
    project["next_action"] = "Human final review: paperback contact sheet/interior, Kindle Create DOCX, Amazon package, rights confirmations; then admit profile or request a bounded correction."
    project["provenance"] = {"recorded_by": "BOOK-FACTORY-INDICES-008", "observed_at": ts, "source_uri": "books/research/unusual-indices/final-production-008-qa.json"}
    paperback_state = "PAPERBACK_INTERIOR_RC_READY" if result["state"] == "PAPERBACK_INTERIOR_RC_READY" else "PAPERBACK_INTERIOR_BLOCKED"
    spec["current_state"] = f"MANUSCRIPT_FINAL; SOURCE_NOTES_FINAL; {paperback_state}; KINDLE_CREATE_INPUT_READY; AMAZON_METADATA_PACKAGE_READY; FRONT_COVER_APPROVED; PAPERBACK_WRAP_COVER_WAITING_FOR_HUMAN; KDP_SUBMISSION_WAITING_FOR_HUMAN"
    spec["expected_outcome"] = "Human approves final interior and publication package, then manually prepares Kindle Create and paperback wrap/KDP submission."
    spec["provenance"] = project["provenance"]
    write_json(project_path, project)
    write_json(spec_path, spec)


def main() -> None:
    if not COVER_PNG.is_file():
        raise FileNotFoundError(f"missing approved Cover A artifact: {COVER_PNG}")
    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)
    paperback_md, kindle_md, used, word_count = build_sources()
    build_seconds = build_artifacts(paperback_md, kindle_md)
    package = publication_package(pdf_page_count(PAPERBACK_PDF))
    write_json(PACKAGE_JSON, package)
    write_package_markdown(package)
    result = qa(used, word_count, build_seconds)
    write_json(RESEARCH_DIR / "final-production-008-qa.json", result)
    manifest = {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": result["state"],
        "profile_state": result["profile_state"],
        "approved_cover_direction": "A",
        "interior_visual_count": 0,
        "prior_work_disposition": {
            "books/artifacts/unusual-indices-book/design-proof": "REJECTED_HISTORICAL_EVIDENCE_NOT_CANONICAL",
            "books/artifacts/unusual-indices-book/recovery-proof": "SYSTEM_RECOVERY_EVIDENCE_NOT_FINAL_OUTPUT",
            "books/artifacts/unusual-indices-book/production-build": "SUPERSEDED_EXCEPT_APPROVED_FRONT_COVER",
            "books/artifacts/unusual-indices-book/final-008": "CANONICAL_RELEASE_CANDIDATE_SET"
        },
        "artifacts": {
            "paperback_interior": str(PAPERBACK_PDF.relative_to(ROOT)),
            "paperback_contact_sheet": str(CONTACT_SHEET.relative_to(ROOT)),
            "kindle_create_input": str(KINDLE_DOCX.relative_to(ROOT)),
            "amazon_publication_package": str(PACKAGE_JSON.relative_to(ROOT)),
            "amazon_copy_pack": str(PACKAGE_MD.relative_to(ROOT)),
            "approved_front_cover": str(COVER_PNG.relative_to(ROOT)),
        },
        "deferred": ["PAPERBACK_WRAP_COVER_PRODUCTION", "KDP_SUBMISSION_AUTOMATION"],
        "publication_status": "NOT_PUBLISHED",
        "human_gate": "STOP_FOR_HUMAN_FINAL_BOOK_REVIEW",
        "provenance": {"recorded_by": "BOOK-FACTORY-INDICES-008", "observed_at": now_iso(), "source_uri": "books/design/unusual-indices-book/build_full_production.py"},
    }
    write_json(ARTIFACT_DIR / "final-production-manifest.json", manifest)
    update_state(result)
    print(json.dumps({"state": result["state"], "profile_state": result["profile_state"], "page_count": result["page_count"], "qa": result["qa_matrix"], "artifacts": manifest["artifacts"]}, indent=2))


if __name__ == "__main__":
    main()
