from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = ROOT / "books" / "design" / "your-saas-bill-is-ridiculous"
MANUSCRIPT = ROOT / "books" / "manuscripts" / "your-saas-bill-is-ridiculous" / "MASTER_MANUSCRIPT.md"
SPEC = ROOT / "books" / "specs" / "your-saas-bill-is-ridiculous-spec.json"
DESIGN_PROOF_DIR = ROOT / "books" / "artifacts" / "your-saas-bill-is-ridiculous" / "design-proof"
FINAL_DIR = ROOT / "books" / "artifacts" / "your-saas-bill-is-ridiculous" / "final"
TMP_DIR = ROOT / "tmp" / "pdfs" / "your-saas-bill-is-ridiculous"
PREAMBLE = PROJECT_ROOT / "preamble.tex"

FULL_PAGE_TITLES = [
    "Agent-Reach",
    "OpenHands",
    "Composio",
    "Langfuse",
    "ABVX Agent Skills",
    "AGENTS.md Generator",
    "Vane",
    "Meetily",
    "Chatterbox TTS",
    "Presenton",
    "MoneyPrinterTurbo",
    "yt-dlp",
    "Activepieces",
    "NocoDB",
    "Twenty",
    "Chatwoot",
    "Listmonk",
    "Plausible Analytics",
    "Immich",
]

RABBIT_HOLE_TITLES = [
    "free-for-dev",
    "Awesome MCP Servers",
    "Official MCP Servers",
]

CANONICAL_URLS = {
    "Agent-Reach": "https://github.com/Panniantong/Agent-Reach",
    "OpenHands": "https://github.com/OpenHands/OpenHands",
    "Composio": "https://github.com/ComposioHQ/composio",
    "Langfuse": "https://github.com/langfuse/langfuse",
    "ABVX Agent Skills": "https://github.com/markoblogo/abvx-agent-skills",
    "AGENTS.md Generator": "https://github.com/markoblogo/AGENTS.md_generator",
    "Vane": "https://github.com/ItzCrazyKns/Vane",
    "Meetily": "https://github.com/Zackriya-Solutions/meetily",
    "Chatterbox TTS": "https://github.com/resemble-ai/chatterbox",
    "Presenton": "https://github.com/presenton/presenton",
    "MoneyPrinterTurbo": "https://github.com/harry0703/MoneyPrinterTurbo",
    "yt-dlp": "https://github.com/yt-dlp/yt-dlp",
    "Activepieces": "https://github.com/activepieces/activepieces",
    "NocoDB": "https://github.com/nocodb/nocodb",
    "Twenty": "https://github.com/twentyhq/twenty",
    "Chatwoot": "https://github.com/chatwoot/chatwoot",
    "Listmonk": "https://github.com/knadh/listmonk",
    "Plausible Analytics": "https://github.com/plausible/analytics",
    "Immich": "https://github.com/immich-app/immich",
    "free-for-dev": "https://github.com/ripienaar/free-for-dev",
    "Awesome MCP Servers": "https://github.com/punkpeye/awesome-mcp-servers",
    "Official MCP Servers": "https://github.com/modelcontextprotocol/servers",
}

CATEGORY_MAP = {
    "Agent-Reach": "AGENT OUTREACH",
    "OpenHands": "AGENT INFRASTRUCTURE",
    "Composio": "AGENT INFRASTRUCTURE",
    "Langfuse": "AI OBSERVABILITY",
    "ABVX Agent Skills": "AGENT INFRASTRUCTURE",
    "AGENTS.md Generator": "AGENT INFRASTRUCTURE",
    "Vane": "ANSWER ENGINE",
    "Meetily": "MEETING TOOLS",
    "Chatterbox TTS": "VOICE",
    "Presenton": "AI MEDIA",
    "MoneyPrinterTurbo": "AI MEDIA",
    "yt-dlp": "MEDIA UTILITY",
    "Activepieces": "AUTOMATION",
    "NocoDB": "CRM",
    "Twenty": "CRM",
    "Chatwoot": "CRM",
    "Listmonk": "CRM",
    "Plausible Analytics": "ANALYTICS",
    "Immich": "PHOTO STORAGE",
}


@dataclass
class Section:
    level: int
    title: str
    body: str
    children: list["Section"]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=ROOT)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def split_paragraphs(section: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", section.strip()) if part.strip()]


def heading_sections(text: str) -> list[Section]:
    matches = list(re.finditer(r"^(#{1,3}) (.+)$", text, re.M))
    raw: list[tuple[int, str, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        raw.append((level, title, body))

    top: list[Section] = []
    stack: list[Section] = []
    for level, title, body in raw:
        section = Section(level=level, title=title, body=body, children=[])
        while stack and stack[-1].level >= level:
            stack.pop()
        if not stack:
            top.append(section)
        else:
            stack[-1].children.append(section)
        stack.append(section)
    return top


def parse_book() -> dict:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    sections = heading_sections(text)
    book = sections[0]
    subtitle = book.children[0]
    rabbit_holes = next(child for child in book.children if child.title == "Rabbit Holes")
    closing = next(child for child in book.children if child.title == "The Bill Moves")
    entries = [child for child in book.children[1:] if child.title not in {"Rabbit Holes", "The Bill Moves"}]
    return {
        "title": book.title,
        "subtitle": subtitle.title,
        "introduction": subtitle.body,
        "entries": entries,
        "rabbit_holes": rabbit_holes,
        "closing": closing.body,
    }


def parse_fact_lines(section: str) -> tuple[list[str], list[tuple[str, str]]]:
    prose: list[str] = []
    facts: list[tuple[str, str]] = []
    for block in split_paragraphs(section):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        fact_lines = [line for line in lines if line.startswith("**")]
        if fact_lines:
            for line in fact_lines:
                fact_match = re.match(r"^\*\*(.+?)\*\*\s+(.*)$", line)
                if not fact_match:
                    raise ValueError(f"unparsed fact line: {line}")
                facts.append((fact_match.group(1), fact_match.group(2)))
        else:
            prose.append(block)
    return prose, facts


def display_url(url: str) -> str:
    return re.sub(r"^https?://", "", url)


def paragraph_markdown(paragraphs: Iterable[str]) -> str:
    return "\n\n".join(paragraphs)


def compress_quote(text: str) -> str:
    return "THE SUBSCRIPTION INVOICE MAY DISAPPEAR.\nAND BE REPLACED BY HOSTING."


def chapter_entries(book: dict) -> list[tuple[str, str]]:
    return [(entry.title, entry.body) for entry in book["entries"]]


def build_repo_page(title: str, body: str) -> str:
    prose, facts = parse_fact_lines(body)
    url = CANONICAL_URLS.get(title)
    category = CATEGORY_MAP.get(title, "OPEN SOURCE TOOL")
    fact_lines = []
    verdict = None
    for key, value in facts:
        if key == "VERDICT":
            verdict = value
            continue
        if key == "URL":
            href = url or value
            shown = display_url(href)
            fact_lines.append(rf"\facturl{{{href}}}{{{latex_escape(shown)}}}")
        else:
            fact_lines.append(rf"\factrow{{{latex_escape(key)}}}{{{latex_escape(value)}}}")
    if url and not any(key == "URL" for key, _ in facts):
        fact_lines.append(rf"\facturl{{{url}}}{{{latex_escape(display_url(url))}}}")
    verdict_block = rf"\verdictblock{{{latex_escape(verdict or 'TRY IT FIRST')}}}"
    return f"""```{{=latex}}
\\clearpage
\\eyebrow{{{latex_escape(category)}}}
\\pagetitle{{{latex_escape(title)}}}
```

{paragraph_markdown(prose)}

```{{=latex}}
\\repofactstripstart
{chr(10).join(fact_lines)}
{verdict_block}
\\repofactstripend
```
"""


def build_rabbit_holes_page(book: dict) -> str:
    children = book["rabbit_holes"].children
    left = children[:2]
    right = children[2:]

    def rabbit_column(items: list[Section]) -> str:
        chunks = []
        for item in items:
            chunks.append(
                rf"\rabbititem{{{latex_escape(item.title)}}}{{{latex_escape(' '.join(' '.join(p.split()) for p in split_paragraphs(item.body)))}}}"
            )
        return "\n".join(chunks)

    links = [
        rf"\rabbitlink{{{latex_escape(item.title)}}}{{{CANONICAL_URLS[item.title]}}}{{{latex_escape(display_url(CANONICAL_URLS[item.title]))}}}"
        for item in children
    ]
    return f"""```{{=latex}}
\\clearpage
\\pagetitle{{Rabbit Holes}}
\\noindent
\\begin{{minipage}}[t]{{0.455\\linewidth}}
{rabbit_column(left)}
\\end{{minipage}}\\hfill
\\begin{{minipage}}[t]{{0.455\\linewidth}}
{rabbit_column(right)}
\\end{{minipage}}

\\vfill
\\rabbitlinkslabel{{GO GET LOST $\\rightarrow$}}
{chr(10).join(links)}
```
"""


def build_intro_pages(book: dict, proof: bool) -> str:
    intro_paragraphs = split_paragraphs(book["introduction"])
    quote = compress_quote(book["introduction"])
    return f"""```{{=latex}}
\\clearpage
```

{paragraph_markdown(intro_paragraphs)}

```{{=latex}}
\\vfill
\\pullquote{{{latex_escape(quote)}}}
```
"""


def build_front_matter(book: dict) -> str:
    return """```{=latex}
\\bookcover
```
"""


def build_closing_page(book: dict) -> str:
    return f"""```{{=latex}}
\\clearpage
\\pagetitle{{The Bill Moves}}
```

{paragraph_markdown(split_paragraphs(book["closing"]))}
"""


def build_markdown(book: dict, mode: str) -> str:
    blocks = [build_front_matter(book), build_intro_pages(book, proof=mode == "proof")]
    entries = chapter_entries(book)
    if mode == "proof":
        title, body = next(row for row in entries if row[0] == "MoneyPrinterTurbo")
        blocks.append(build_repo_page(title, body))
        blocks.append(build_rabbit_holes_page(book))
    else:
        for title, body in entries:
            blocks.append(build_repo_page(title, body))
        blocks.append(build_rabbit_holes_page(book))
        blocks.append(build_closing_page(book))
    return "\n\n".join(blocks) + "\n"


def run_pandoc(markdown_path: Path, pdf_path: Path) -> None:
    run(
        [
            "pandoc",
            str(markdown_path),
            "--from",
            "markdown+raw_tex",
            "--pdf-engine=xelatex",
            "-H",
            str(PREAMBLE),
            "-V",
            "papersize:a4",
            "-V",
            "fontsize=11pt",
            "-o",
            str(pdf_path),
        ]
    )


def render_pdf_pages(pdf_path: Path, output_dir: Path, prefix: str) -> list[Path]:
    temp_prefix = TMP_DIR / prefix
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*.png"):
        stale.unlink()
    for stale in TMP_DIR.glob(f"{prefix}-*.png"):
        stale.unlink()
    run(["pdftoppm", "-png", str(pdf_path), str(temp_prefix)])
    rendered = sorted(TMP_DIR.glob(f"{prefix}-*.png"))
    copied = []
    for image in rendered:
        target = output_dir / image.name.replace(f"{prefix}-", "")
        shutil.copy2(image, target)
        copied.append(target)
    return copied


def extract_pdf_text(pdf_path: Path) -> str:
    return subprocess.check_output(["pdftotext", str(pdf_path), "-"], cwd=ROOT).decode("utf-8", errors="replace")


def html_link_targets(pdf_path: Path) -> list[str]:
    xml = subprocess.check_output(["pdftohtml", "-xml", str(pdf_path), "-stdout"], cwd=ROOT, stderr=subprocess.DEVNULL).decode(
        "utf-8", errors="replace"
    )
    return re.findall(r'<a href="([^"]+)">', xml)


def validate_text_layer(text: str) -> dict:
    disallowed_controls = sorted({ord(ch) for ch in text if ord(ch) < 32 and ch not in "\n\t\r\f"})
    replacement_chars = sorted({hex(ord(ch)) for ch in text if ch in "\ufffd\ufffe\uffff"})
    ligatures = sorted({hex(ord(ch)) for ch in text if 0xFB00 <= ord(ch) <= 0xFB06})
    return {
        "disallowed_controls": disallowed_controls,
        "replacement_chars": replacement_chars,
        "ligatures": ligatures,
        "text_layer_clean": not disallowed_controls and not replacement_chars and not ligatures,
    }


def split_pdf_pages(text: str) -> list[str]:
    return text.split("\f")


def normalize_for_match(value: str) -> str:
    value = value.replace("’", "'").replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def locate_page(pages: list[str], needle: str) -> int | None:
    normalized_needle = normalize_for_match(needle)
    for index, page in enumerate(pages, start=1):
        normalized_lines = [normalize_for_match(line) for line in page.splitlines() if line.strip()]
        if normalized_needle in normalized_lines:
            return index
    for index, page in enumerate(pages, start=1):
        if normalized_needle in normalize_for_match(page):
            return index
    return None


def build_proof_report(pdf_path: Path) -> dict:
    text = extract_pdf_text(pdf_path)
    links = html_link_targets(pdf_path)
    pages = split_pdf_pages(text)
    return {
        "page_count": len(pages) - (1 if pages and not pages[-1].strip() else 0),
        "text_layer": validate_text_layer(text),
        "proof_checks": {
            "cover_title_found": "YOUR SAAS" in text and "RIDICULOUS" in text,
            "intro_found": "SaaS subscriptions pile up so gradually" in text,
            "money_printer_turbo_found": locate_page(pages, "MoneyPrinterTurbo") is not None,
            "rabbit_holes_found": locate_page(pages, "Rabbit Holes") is not None,
            "money_link_present": CANONICAL_URLS["MoneyPrinterTurbo"] in links,
            "rabbit_links_present": all(CANONICAL_URLS[name] in links for name in RABBIT_HOLE_TITLES),
        },
    }


def build_full_report(pdf_path: Path) -> dict:
    text = extract_pdf_text(pdf_path)
    links = html_link_targets(pdf_path)
    pages = split_pdf_pages(text)
    info = subprocess.check_output(["pdfinfo", str(pdf_path)], cwd=ROOT).decode("utf-8", errors="replace")
    page_count_match = re.search(r"Pages:\s+(\d+)", info)
    file_size_match = re.search(r"File size:\s+(.+)", info)
    content_integrity = {
        "full_page_entries_present": [title for title in FULL_PAGE_TITLES if locate_page(pages, title) is not None],
        "rabbit_hole_entries_present": [title for title in RABBIT_HOLE_TITLES if locate_page(pages, title) is not None],
        "introduction_present": "SaaS subscriptions pile up so gradually" in text,
        "closing_present": locate_page(pages, "The Bill Moves") is not None,
    }
    page_map = {title: locate_page(pages, title) for title in FULL_PAGE_TITLES + ["Rabbit Holes", "The Bill Moves"]}
    return {
        "page_count": int(page_count_match.group(1)) if page_count_match else None,
        "file_size": file_size_match.group(1).strip() if file_size_match else None,
        "text_layer": validate_text_layer(text),
        "link_targets": sorted(set(links)),
        "required_links": {name: CANONICAL_URLS[name] in links for name in ["MoneyPrinterTurbo", "Twenty", "Plausible Analytics", "ABVX Agent Skills", "AGENTS.md Generator", "Chatterbox TTS", "Activepieces"] + RABBIT_HOLE_TITLES},
        "content_integrity": {
            "full_page_entry_count": len(content_integrity["full_page_entries_present"]),
            "rabbit_hole_count": len(content_integrity["rabbit_hole_entries_present"]),
            **content_integrity,
        },
        "page_map": page_map,
        "title_found": "Your SaaS Bill Is Ridiculous" in text,
        "subtitle_found": "A Skeptical Guide to Open-Source Tools That Can Replace Expensive SaaS" in text,
        "author_found": "Anton Biletskyi-Volokh" in text,
        "text_excerpt_checks": {
            "moneyprinterturbo_url_display": display_url(CANONICAL_URLS["MoneyPrinterTurbo"]) in text,
            "plausible_present": "Plausible Analytics" in text,
            "agentsmd_present": "AGENTS.md Generator" in text,
        },
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_publication_packet(book: dict, final_pdf: Path, final_cover: Path) -> Path:
    spec = read_json(SPEC)
    packet_path = ROOT / "content" / "publish-packets" / "book-factory-006c-your-saas-bill-is-ridiculous.json"
    packet = {
        "schema_version": "v1",
        "item_id": "book-factory-006c-your-saas-bill-is-ridiculous",
        "project": "abvxsite",
        "surface": "work",
        "kind": "work",
        "slug": "your-saas-bill-is-ridiculous",
        "title": book["title"],
        "consumer_repo": "/Volumes/Work/Work/ABVXsite",
        "target": "scripts/publish-project.mjs",
        "mode": "REPORT_ONLY_HANDOFF",
        "mechanism": "Consumer-side publish command for ABVX project/work content",
        "consumer_operation": {
            "id": "abvx.publish-project",
            "target_surface": "abvx.work",
            "dry_run_command": "cd /Volumes/Work/Work/ABVXsite && node scripts/publish-project.mjs --packet <packet> --dry-run",
            "apply_command": "cd /Volumes/Work/Work/ABVXsite && node scripts/publish-project.mjs --packet <packet> --write",
        },
        "required_consumer_steps": [
            "Run ABVXsite publish-project command in dry-run mode.",
            "Run npm run content:validate in /Volumes/Work/Work/ABVXsite.",
            "Run npm run build in /Volumes/Work/Work/ABVXsite.",
            "Publish only after human approval."
        ],
        "artifact_refs": [
            str(final_pdf.relative_to(ROOT)),
            str(final_cover.relative_to(ROOT)),
        ],
        "payload": {
            "asset_refs": [str(final_pdf.relative_to(ROOT)), str(final_cover.relative_to(ROOT))],
            "body_lines": [
                "A curated discovery booklet about open-source tools that are interesting enough to send to someone with: look what I found.",
                "Free downloadable DIGITAL_PDF for ABVX Books."
            ],
            "cover_image": str(final_cover.relative_to(ROOT)),
            "excerpt": "A curated discovery booklet about open-source tools that may replace expensive SaaS, while moving the bill into operations, APIs, and attention.",
            "image_alt": "Cover of Your SaaS Bill Is Ridiculous",
            "media_event_candidate": None,
            "source_refs": [str(MANUSCRIPT.relative_to(ROOT))],
            "cta_label": "Free PDF",
            "publication_type": "DISCOVERY_BOOKLET",
            "tags": ["ABVX", "books", "open source", "saas alternatives", "digital pdf", "discovery booklet"],
            "topics": ["book publication", "open source tools", "self hosting", "software costs", "editorial zine"],
        },
        "enrichment": {
            "author": "Anton Biletskyi-Volokh",
            "publisher": "ABVX",
            "slug": "your-saas-bill-is-ridiculous",
            "canonical_path": "/work/your-saas-bill-is-ridiculous",
            "date_published": None,
            "date_modified": "2026-08-12",
            "seo_title": "Your SaaS Bill Is Ridiculous — A Curated Discovery Booklet of Open-Source Finds",
            "meta_description": "A curated ABVX discovery booklet of open-source tools worth knowing about, with blunt verdicts on what they replace and what they still make you pay for.",
            "machine_summary": "Publication-ready DIGITAL_PDF discovery booklet for ABVX Books, pending final human release decision.",
            "open_graph": {
                "title": "Your SaaS Bill Is Ridiculous",
                "description": "A curated discovery booklet of open-source tools worth knowing about.",
                "image": str(final_cover.relative_to(ROOT)),
                "image_alt": "Cover of Your SaaS Bill Is Ridiculous",
            },
            "social_preview": {
                "title": "Your SaaS Bill Is Ridiculous",
                "description": "A curated discovery booklet of open-source tools worth knowing about.",
                "image": str(final_cover.relative_to(ROOT)),
                "image_alt": "Cover of Your SaaS Bill Is Ridiculous",
            },
            "structured_data": {"status": "SUPPORTED", "type": "CreativeWork"},
            "indexability": "INDEXABLE",
            "sitemap_state": "INDEXABLE",
            "hreflang": {"en": "/work/your-saas-bill-is-ridiculous"},
            "primary_entities": ["ABVX", "Anton Biletskyi-Volokh", "Open source", "SaaS", "Self hosting"],
            "primary_source_links": [str(MANUSCRIPT.relative_to(ROOT))],
            "related_projects": ["abvxsite", "1d3x", "pop"],
            "internal_link_suggestions": ["project:abvxsite", "project:pop", "project:1d3x"],
            "tags": ["ABVX", "books", "open source", "saas alternatives", "digital pdf", "discovery booklet"],
            "topics": ["book publication", "open source tools", "self hosting", "software costs", "editorial zine"],
            "warnings": ["Public release remains human-gated."],
        },
        "generated_at": "2026-08-12T00:00:00Z",
        "validation_tier": "STANDARD",
        "validation_checks": [
            "Book Factory tests",
            "build script validation",
            "full PDF build",
            "PDF text-layer validation",
            "link validation",
            "./bin/abvx validate",
        ],
    }
    write_json(packet_path, packet)
    return packet_path


def build(mode: str) -> dict:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    book = parse_book()
    markdown = build_markdown(book, mode)
    target_dir = DESIGN_PROOF_DIR if mode == "proof" else FINAL_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = TMP_DIR / f"{mode}.md"
    pdf_path = target_dir / ("your-saas-bill-is-ridiculous-design-proof.pdf" if mode == "proof" else "your-saas-bill-is-ridiculous.pdf")
    markdown_path.write_text(markdown, encoding="utf-8")
    run_pandoc(markdown_path, pdf_path)
    render_pdf_pages(pdf_path, target_dir if mode == "proof" else (target_dir / "pages"), mode)
    if mode == "proof":
        manifest = {
            "artifact": str(pdf_path.relative_to(ROOT)),
            "pages": [
                str((target_dir / "1.png").relative_to(ROOT)),
                str((target_dir / "2.png").relative_to(ROOT)),
                str((target_dir / "3.png").relative_to(ROOT)),
                str((target_dir / "4.png").relative_to(ROOT)),
            ],
            "compiler": {
                "path": "pandoc+xelatex",
                "donor": "vpuna/markdown-to-book",
                "donor_role_for_this_mission": "PATTERN_SOURCE",
            },
        }
        renamed = {
            "1.png": "sample-1-cover.png",
            "2.png": "sample-2-introduction-page.png",
            "3.png": "sample-3-repository-page.png",
            "4.png": "sample-4-rabbit-holes-page.png",
        }
        for old_name, new_name in renamed.items():
            src = target_dir / old_name
            if src.exists():
                src.replace(target_dir / new_name)
        manifest["pages"] = [str((target_dir / renamed[key]).relative_to(ROOT)) for key in ["1.png", "2.png", "3.png", "4.png"]]
        write_json(target_dir / "manifest.json", manifest)
        report = build_proof_report(pdf_path)
        write_json(target_dir / "qa-report.json", report)
        return {"pdf": pdf_path, "report": report}
    cover_png = target_dir / "cover.png"
    page_candidates = sorted((target_dir / "pages").glob("*.png"))
    if page_candidates:
        shutil.copy2(page_candidates[0], cover_png)
    report = build_full_report(pdf_path)
    packet = build_publication_packet(book, pdf_path, cover_png)
    write_json(target_dir / "qa-report.json", report)
    write_json(
        target_dir / "manifest.json",
        {
            "artifact": str(pdf_path.relative_to(ROOT)),
            "cover": str(cover_png.relative_to(ROOT)),
            "qa_report": str((target_dir / "qa-report.json").relative_to(ROOT)),
            "publication_packet": str(packet.relative_to(ROOT)),
            "compiler": {
                "path": "pandoc+xelatex",
                "donor": "vpuna/markdown-to-book",
                "donor_role_for_this_mission": "PATTERN_SOURCE",
            },
        },
    )
    return {"pdf": pdf_path, "report": report, "packet": packet}


def main() -> None:
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "proof"
    if mode not in {"proof", "full"}:
        raise SystemExit("usage: build_design_proof.py [proof|full]")
    build(mode)


if __name__ == "__main__":
    main()
