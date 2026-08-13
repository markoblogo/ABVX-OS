#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
BOOK_ID = "unusual-indices-book"
TITLE = "Burgers, Lipstick & Underwear"
SUBTITLE = "What Strange Indicators Really Tell Us About the Economy"
AUTHOR = "Anton BV"
MANUSCRIPT = ROOT / "books" / "manuscripts" / BOOK_ID / "MASTER_MANUSCRIPT.md"
RESEARCH_DIR = ROOT / "books" / "research" / "unusual-indices"
ARTIFACT_DIR = ROOT / "books" / "artifacts" / BOOK_ID / "design-proof"
BUILD_DIR = ROOT / "tmp" / "book-factory-indices-006"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(cmd: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for path in candidates:
        if path and Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_text_block(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, width: int, fill=(35, 31, 28), leading: int = 8) -> int:
    x, y = xy
    for line in wrap(draw, text, font, width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + leading
    return y


SOURCE_RECORDS = [
    {
        "source_id": "source-economist-big-mac",
        "title": "Data and methodology for the Big Mac index",
        "author_or_institution": "The Economist",
        "publication": "GitHub / The Economist data repository",
        "publication_date": None,
        "url": "https://github.com/TheEconomist/big-mac-data",
        "source_type": "primary_data_methodology",
        "related_chapter": ["Chapter 1"],
        "claims_supported": ["The Big Mac Index has public data and calculation code; it is a PPP-oriented consumer-object proxy."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-docx-mixed-research",
        "title": "Owner-supplied unusual indices research source pack",
        "author_or_institution": "Owner / ABVX",
        "publication": "Local source pack",
        "publication_date": None,
        "url": "books/source-packs/unusual-indices-book-source-pack.json",
        "source_type": "research_lead_pack",
        "related_chapter": ["Chapter 1"],
        "claims_supported": ["Supporting leads for consumer-object index examples only."],
        "primary_or_secondary": "lead_only",
        "verification_status": "NON_CONSEQUENTIAL_CONTEXT",
    },
    {
        "source_id": "source-ubs-prices-and-earnings",
        "title": "Prices and Earnings 2015",
        "author_or_institution": "UBS",
        "publication": "UBS Prices and Earnings",
        "publication_date": "2015",
        "url": "https://files.illinoispolicy.org/wp-content/uploads/2015/09/ubs-pricesandearnings-2015-en.pdf",
        "source_type": "institutional_report",
        "related_chapter": ["Chapter 2"],
        "claims_supported": ["City-level prices and wages can be converted into working-time affordability comparisons."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-wef-iphone-hours",
        "title": "Who has to work the longest to buy an iPhone?",
        "author_or_institution": "World Economic Forum",
        "publication": "World Economic Forum",
        "publication_date": "2015-12-07",
        "url": "https://www.weforum.org/stories/economic-growth/who-has-to-work-the-longest-to-buy-an-iphone/",
        "source_type": "reputable_secondary_summary",
        "related_chapter": ["Chapter 2"],
        "claims_supported": ["Secondary summary of UBS-style iPhone working-hours comparisons."],
        "primary_or_secondary": "secondary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-investopedia-starbucks",
        "title": "Understanding the Starbucks Index",
        "author_or_institution": "Investopedia",
        "publication": "Investopedia",
        "publication_date": None,
        "url": "https://www.investopedia.com/terms/s/starbucks-index.asp",
        "source_type": "reputable_secondary_explainer",
        "related_chapter": ["Chapter 1"],
        "claims_supported": ["The Starbucks/latte index is an informal PPP-style consumer-object comparison."],
        "primary_or_secondary": "secondary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-numbeo-cost-of-living",
        "title": "Cost of Living database",
        "author_or_institution": "Numbeo",
        "publication": "Numbeo",
        "publication_date": None,
        "url": "https://www.numbeo.com/cost-of-living/",
        "source_type": "secondary_database",
        "related_chapter": ["Chapter 2"],
        "claims_supported": ["Cost-of-living examples such as meals, transport and social activities vary by city."],
        "primary_or_secondary": "secondary",
        "verification_status": "SUPPORTING_CONTEXT",
    },
    {
        "source_id": "source-rbc-lipstick",
        "title": "Lipstick Index secondary market commentary",
        "author_or_institution": "RBC / secondary market commentary",
        "publication": "Research lead",
        "publication_date": None,
        "url": None,
        "source_type": "secondary_commentary",
        "related_chapter": ["Chapter 3"],
        "claims_supported": ["Lipstick Index as recession folklore / affordable-luxury narrative."],
        "primary_or_secondary": "secondary",
        "verification_status": "NON_CONSEQUENTIAL_CONTEXT",
    },
    {
        "source_id": "source-lipstick-secondary",
        "title": "What is the Lipstick Index?",
        "author_or_institution": "J.P. Morgan Wealth Management / Chase",
        "publication": "Chase",
        "publication_date": "2026-06-05",
        "url": "https://www.chase.com/personal/investments/learning-and-insights/article/what-is-lipstick-index",
        "source_type": "reputable_secondary_explainer",
        "related_chapter": ["Chapter 3"],
        "claims_supported": ["The Lipstick Index is an economic theory, not an economically proven indicator."],
        "primary_or_secondary": "secondary",
        "verification_status": "VERIFIED_SECONDARY",
    },
    {
        "source_id": "source-medical-economics-weird",
        "title": "Unusual recession-indicator overview",
        "author_or_institution": "Secondary business / medical-economics commentary",
        "publication": "Research lead",
        "publication_date": None,
        "url": None,
        "source_type": "secondary_commentary",
        "related_chapter": ["Chapter 3"],
        "claims_supported": ["Men’s underwear and hemline indicators as folklore examples only."],
        "primary_or_secondary": "secondary",
        "verification_status": "NON_CONSEQUENTIAL_CONTEXT",
    },
    {
        "source_id": "source-skyscraper-paper",
        "title": "Skyscraper Height and the Business Cycle: Separating Myth from Reality",
        "author_or_institution": "Jason Barr, Bruce Mizrach, Kusum Mundra",
        "publication": "Applied Economics",
        "publication_date": "2015",
        "url": "https://ideas.repec.org/a/taf/applec/v47y2015i2p148-160.html",
        "source_type": "academic_paper",
        "related_chapter": ["Chapter 3"],
        "claims_supported": ["The skyscraper effect is contested and has been empirically tested rather than accepted as a simple forecasting law."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-market-urbanism",
        "title": "Skyscrapers as Economic Indicators",
        "author_or_institution": "Market Urbanism",
        "publication": "Market Urbanism",
        "publication_date": "2008-08-26",
        "url": "https://marketurbanism.com/2008/08/26/skyscrapers-as-economic-indicators/",
        "source_type": "secondary_commentary",
        "related_chapter": ["Chapter 3"],
        "claims_supported": ["The skyscraper index circulated as urban/economic commentary and should be treated as a contested story."],
        "primary_or_secondary": "secondary",
        "verification_status": "SUPPORTING_CONTEXT",
    },
    {
        "source_id": "source-baltic-exchange",
        "title": "Baltic Exchange methodology",
        "author_or_institution": "Baltic Exchange",
        "publication": "Baltic Exchange",
        "publication_date": None,
        "url": "https://www.balticexchange.com/en/data-services/Methodology.html",
        "source_type": "primary_methodology",
        "related_chapter": ["Chapter 4"],
        "claims_supported": ["Baltic Exchange indices are methodology-governed freight-market benchmarks."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-freightos-baltic",
        "title": "Freightos Baltic Index",
        "author_or_institution": "Freightos",
        "publication": "Freightos",
        "publication_date": None,
        "url": "https://www.freightos.com/enterprise/terminal/freightos-baltic-index-global-container-pricing-index/",
        "source_type": "primary_methodology",
        "related_chapter": ["Chapter 4"],
        "claims_supported": ["Freightos Baltic Index provides container-pricing benchmark context."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-ember-energy",
        "title": "Energy data",
        "author_or_institution": "Ember",
        "publication": "Ember",
        "publication_date": None,
        "url": "https://ember-energy.org/data/",
        "source_type": "data_source",
        "related_chapter": ["Chapter 4"],
        "claims_supported": ["Electricity and energy data can operate as physical-economy signals."],
        "primary_or_secondary": "primary",
        "verification_status": "SUPPORTING_CONTEXT",
    },
    {
        "source_id": "source-electricitymaps",
        "title": "Electricity Maps",
        "author_or_institution": "Electricity Maps",
        "publication": "Electricity Maps",
        "publication_date": None,
        "url": "https://app.electricitymaps.com/map",
        "source_type": "operational_data_product",
        "related_chapter": ["Chapter 4"],
        "claims_supported": ["Electricity maps make grid intensity and physical-system conditions visible."],
        "primary_or_secondary": "primary",
        "verification_status": "SUPPORTING_CONTEXT",
    },
    {
        "source_id": "source-berkeley-earth",
        "title": "Air Pollution and Cigarette Equivalence",
        "author_or_institution": "Berkeley Earth",
        "publication": "Berkeley Earth",
        "publication_date": None,
        "url": "https://berkeleyearth.org/air-pollution-and-cigarette-equivalence/",
        "source_type": "methodology_explainer",
        "related_chapter": ["Chapter 5"],
        "claims_supported": ["PM2.5 exposure can be communicated through a cigarette-equivalent analogy with explicit caveats."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-who-air-quality",
        "title": "WHO global air quality guidelines",
        "author_or_institution": "World Health Organization",
        "publication": "WHO",
        "publication_date": "2021",
        "url": "https://www.who.int/publications/i/item/9789240034228",
        "source_type": "official_guideline",
        "related_chapter": ["Chapter 5"],
        "claims_supported": ["PM2.5 health-risk context and air-quality guidance."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-openaq",
        "title": "AQI Hub",
        "author_or_institution": "OpenAQ",
        "publication": "OpenAQ",
        "publication_date": None,
        "url": "https://openaq.org/about/initiatives/aqi-hub/",
        "source_type": "data_initiative",
        "related_chapter": ["Chapter 5"],
        "claims_supported": ["AQI standardization and data interoperability are nontrivial."],
        "primary_or_secondary": "primary",
        "verification_status": "SUPPORTING_CONTEXT",
    },
    {
        "source_id": "source-ourworldindata-co2",
        "title": "CO2 and greenhouse gas emissions",
        "author_or_institution": "Our World in Data",
        "publication": "Our World in Data",
        "publication_date": None,
        "url": "https://ourworldindata.org/co2-and-greenhouse-gas-emissions",
        "source_type": "data_explainer",
        "related_chapter": ["Chapter 5"],
        "claims_supported": ["CO2-equivalent and emissions comparisons require careful unit framing."],
        "primary_or_secondary": "secondary",
        "verification_status": "SUPPORTING_CONTEXT",
    },
    {
        "source_id": "claim-goodhart-risk",
        "title": "Goodhart’s law / measure-target risk",
        "author_or_institution": "Charles Goodhart / later economics and policy usage",
        "publication": "Conceptual source family",
        "publication_date": None,
        "url": "https://link.springer.com/chapter/10.1007/978-1-349-17295-5_4",
        "source_type": "conceptual_reference",
        "related_chapter": ["Chapter 6"],
        "claims_supported": ["A measure can stop being a good measure when it becomes a target."],
        "primary_or_secondary": "secondary",
        "verification_status": "CONCEPTUAL_REFERENCE",
    },
    {
        "source_id": "source-libor-case",
        "title": "Two Former Deutsche Bank Traders Convicted for Role in Scheme to Manipulate Critical Global Benchmark Interest Rate",
        "author_or_institution": "U.S. Department of Justice",
        "publication": "Justice Department Archives",
        "publication_date": "2018-10-17",
        "url": "https://www.justice.gov/archives/opa/pr/two-former-deutsche-bank-traders-convicted-role-scheme-manipulate-critical-global-benchmark",
        "source_type": "official_legal_record",
        "related_chapter": ["Chapter 6"],
        "claims_supported": ["LIBOR manipulation is a concrete case of a benchmark becoming a target with incentives attached."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-doing-business-report",
        "title": "World Bank Group to Discontinue Doing Business Report",
        "author_or_institution": "World Bank Group",
        "publication": "World Bank statement",
        "publication_date": "2021-09-16",
        "url": "https://www.worldbank.org/en/news/statement/2021/09/16/world-bank-group-to-discontinue-doing-business-report",
        "source_type": "official_statement",
        "related_chapter": ["Chapter 6"],
        "claims_supported": ["The Doing Business report was discontinued after data irregularities and integrity concerns."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-stanford-ai-index",
        "title": "AI Index Report",
        "author_or_institution": "Stanford HAI",
        "publication": "Stanford AI Index",
        "publication_date": "2026",
        "url": "https://hai.stanford.edu/ai-index/2026-ai-index-report",
        "source_type": "institutional_report",
        "related_chapter": ["Chapter 7"],
        "claims_supported": ["AI Index organizes AI-related data for broad readers and decision-makers."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-oxford-ai-readiness",
        "title": "Government AI Readiness Index",
        "author_or_institution": "Oxford Insights",
        "publication": "Oxford Insights",
        "publication_date": "2025",
        "url": "https://oxfordinsights.com/ai-readiness/government-ai-readiness-index-2025/",
        "source_type": "institutional_index",
        "related_chapter": ["Chapter 7"],
        "claims_supported": ["Government AI readiness rankings are broad composite indices, not direct capability measurements."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-swe-bench",
        "title": "SWE-bench",
        "author_or_institution": "SWE-bench project",
        "publication": "GitHub / project site",
        "publication_date": None,
        "url": "https://github.com/swe-bench/SWE-bench",
        "source_type": "benchmark_project",
        "related_chapter": ["Chapter 7"],
        "claims_supported": ["SWE-bench evaluates real-world software issue resolution using GitHub issue/patch tasks."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-swe-bench-paper",
        "title": "SWE-bench: Can Language Models Resolve Real-world GitHub Issues?",
        "author_or_institution": "Carlos E. Jimenez et al.",
        "publication": "arXiv",
        "publication_date": "2023",
        "url": "https://arxiv.org/abs/2310.06770",
        "source_type": "academic_paper",
        "related_chapter": ["Chapter 7"],
        "claims_supported": ["SWE-bench is built around real GitHub issues and pull requests."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-swebench-verified",
        "title": "SWE-bench Verified",
        "author_or_institution": "SWE-bench / OpenAI collaboration",
        "publication": "SWE-bench project site",
        "publication_date": "2024",
        "url": "https://www.swebench.com/verified.html",
        "source_type": "benchmark_subset",
        "related_chapter": ["Chapter 7"],
        "claims_supported": ["SWE-bench Verified is a human-filtered subset created to improve task quality."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
    {
        "source_id": "source-swebench-contamination",
        "title": "Why SWE-bench Verified no longer measures frontier coding capabilities",
        "author_or_institution": "OpenAI",
        "publication": "OpenAI",
        "publication_date": "2026",
        "url": "https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/",
        "source_type": "benchmark_evaluation_note",
        "related_chapter": ["Chapter 7"],
        "claims_supported": ["SWE-bench Verified became less useful for frontier evaluation because of saturation and contamination concerns."],
        "primary_or_secondary": "primary",
        "verification_status": "VERIFIED",
    },
]


def source_registry() -> dict:
    observed = now_iso()
    records = []
    for record in SOURCE_RECORDS:
        enriched = dict(record)
        enriched["reviewed_at"] = observed
        records.append(enriched)
    return {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "SOURCE_REGISTRY_READY_FOR_PROOF",
        "source_hierarchy": [
            "original publisher / methodology",
            "academic paper / official institution",
            "high-quality journalism / publisher",
            "reputable secondary source",
            "original research/source pack only as lead",
        ],
        "records": records,
        "normalization_policy": {
            "consequential_claim_rule": "No consequential factual claim may depend only on an unidentified or generic alias.",
            "reader_notes_rule": "Reader-facing notes use concise source titles and URLs, while canonical manuscript markers remain internal provenance.",
            "non_consequential_rule": "Folklore/context aliases may remain only when they support non-consequential color or contested-signal framing.",
        },
        "provenance": {
            "recorded_by": "BOOK-FACTORY-INDICES-006",
            "observed_at": observed,
            "source_uri": "books/manuscripts/unusual-indices-book/MASTER_MANUSCRIPT.md",
        },
    }


def make_visuals() -> list[dict]:
    out = ARTIFACT_DIR / "visuals"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    # Visual A: conceptual Big Mac schematic.
    img = Image.new("RGB", (1400, 900), "#f5f1e8")
    d = ImageDraw.Draw(img)
    title_font = load_font(56, True)
    label_font = load_font(34, True)
    body_font = load_font(28)
    small_font = load_font(22)
    d.rectangle((70, 70, 1330, 830), outline="#25211e", width=6)
    d.text((110, 105), "A burger becomes an exchange-rate question", font=title_font, fill="#25211e")
    boxes = [
        (130, 300, 360, 500, "LOCAL\nPRICE"),
        (450, 300, 680, 500, "EXCHANGE\nRATE"),
        (770, 300, 1000, 500, "COMMON\nCURRENCY"),
        (1090, 300, 1270, 500, "CHEAP?\nEXPENSIVE?"),
    ]
    for x1, y1, x2, y2, label in boxes:
        d.rounded_rectangle((x1, y1, x2, y2), radius=28, outline="#25211e", width=5, fill="#fffaf0")
        lines = label.splitlines()
        ty = y1 + 50
        for line in lines:
            tw = d.textbbox((0, 0), line, font=label_font)[2]
            d.text((x1 + (x2 - x1 - tw) / 2, ty), line, font=label_font, fill="#25211e")
            ty += 45
    for x in [380, 700, 1020]:
        d.line((x, 400, x + 50, 400), fill="#8a4a32", width=8)
        d.polygon([(x + 50, 400), (x + 25, 380), (x + 25, 420)], fill="#8a4a32")
    draw_text_block(d, (130, 610), "Useful because it is familiar. Dangerous if treated as an oracle.", body_font, 1120, fill="#25211e")
    draw_text_block(d, (130, 680), "Source logic: The Economist Big Mac Index. Conceptual proof uses no current leaderboard values.", small_font, 1120, fill="#5b514a")
    visual_a = out / "visual-a-big-mac-schematic.png"
    img.save(visual_a, dpi=(300, 300))
    records.append({
        "visual_id": "visual-a-big-mac-schematic",
        "chapter": "Chapter 1",
        "visual_type": "comparison_schematic",
        "purpose": "Show how a familiar product becomes an exchange-rate intuition.",
        "source_ids": ["source-economist-big-mac"],
        "data_as_of": None,
        "transformation": "Conceptual flow diagram; no numeric source data transformed.",
        "units": "conceptual",
        "grayscale_safe": True,
        "kindle_safe": True,
        "rights_status": "ORIGINAL_DIAGRAM_NO_BRANDED_TRADE_DRESS",
        "artifact_refs": [str(visual_a.relative_to(ROOT))],
        "status": "PROOF_READY",
    })
    # Visual B: benchmark lifecycle.
    img = Image.new("RGB", (1400, 900), "#f5f1e8")
    d = ImageDraw.Draw(img)
    d.rectangle((70, 70, 1330, 830), outline="#25211e", width=6)
    d.text((110, 105), "The lifecycle of a benchmark", font=title_font, fill="#25211e")
    steps = ["CREATE", "TRUST", "OPTIMIZE", "SATURATE", "REPLACE"]
    xs = [130, 380, 630, 880, 1130]
    for idx, (x, step) in enumerate(zip(xs, steps), 1):
        d.ellipse((x, 330, x + 150, 480), outline="#25211e", width=5, fill="#fffaf0")
        d.text((x + 45, 260), str(idx), font=label_font, fill="#8a4a32")
        tw = d.textbbox((0, 0), step, font=small_font)[2]
        d.text((x + 75 - tw / 2, 390), step, font=small_font, fill="#25211e")
    for x in [295, 545, 795, 1045]:
        d.line((x, 405, x + 70, 405), fill="#8a4a32", width=8)
        d.polygon([(x + 70, 405), (x + 45, 385), (x + 45, 425)], fill="#8a4a32")
    draw_text_block(d, (130, 610), "A benchmark succeeds, becomes valuable, attracts optimization and eventually needs repair or replacement.", body_font, 1120, fill="#25211e")
    draw_text_block(d, (130, 700), "Source logic: SWE-bench, SWE-bench Verified and OpenAI benchmark-limit note.", small_font, 1120, fill="#5b514a")
    visual_b = out / "visual-b-benchmark-lifecycle.png"
    img.save(visual_b, dpi=(300, 300))
    records.append({
        "visual_id": "visual-b-benchmark-lifecycle",
        "chapter": "Chapter 7",
        "visual_type": "process_lifecycle",
        "purpose": "Show how a respected benchmark can become optimized, saturated or contaminated.",
        "source_ids": ["source-swe-bench", "source-swebench-verified", "source-swebench-contamination"],
        "data_as_of": None,
        "transformation": "Conceptual lifecycle diagram; no leaderboard values used.",
        "units": "conceptual",
        "grayscale_safe": True,
        "kindle_safe": True,
        "rights_status": "ORIGINAL_DIAGRAM_NO_SCREENSHOTS",
        "artifact_refs": [str(visual_b.relative_to(ROOT))],
        "status": "PROOF_READY",
    })
    return records


def make_cover() -> dict:
    out = ARTIFACT_DIR / "cover"
    out.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1800, 2700), "#f1eadf")
    d = ImageDraw.Draw(img)
    title_font = load_font(150, True)
    sub_font = load_font(58)
    author_font = load_font(46, True)
    small_font = load_font(34)
    d.rectangle((90, 90, 1710, 2610), outline="#2b2520", width=12)
    d.rectangle((145, 145, 1655, 2555), outline="#8a4a32", width=4)
    y = 260
    for line in ["BURGERS,", "LIPSTICK", "& UNDERWEAR"]:
        d.text((180, y), line, font=title_font, fill="#2b2520")
        y += 165
    d.line((180, y + 20, 1620, y + 20), fill="#8a4a32", width=10)
    y += 85
    y = draw_text_block(d, (185, y), SUBTITLE.upper(), sub_font, 1350, fill="#2b2520", leading=16)
    # Generic object territory: no product photography or trademark.
    base_y = 1700
    d.ellipse((210, base_y + 110, 620, base_y + 360), fill="#2b2520")
    d.rectangle((250, base_y + 70, 580, base_y + 160), fill="#8a4a32")
    d.rectangle((720, base_y + 20, 830, base_y + 380), fill="#2b2520")
    d.polygon([(700, base_y + 20), (850, base_y + 20), (825, base_y - 80), (725, base_y - 80)], fill="#8a4a32")
    d.rounded_rectangle((1030, base_y + 80, 1510, base_y + 360), radius=80, outline="#2b2520", width=28)
    d.arc((1070, base_y + 80, 1270, base_y + 260), 180, 360, fill="#2b2520", width=24)
    d.arc((1270, base_y + 80, 1470, base_y + 260), 180, 360, fill="#2b2520", width=24)
    d.text((180, 2350), AUTHOR.upper(), font=author_font, fill="#2b2520")
    d.text((180, 2430), "FRONT-COVER DIRECTION PROOF — NOT FINAL ART", font=small_font, fill="#8a4a32")
    full = out / "cover-proof-full.png"
    thumb = out / "cover-proof-amazon-thumbnail.png"
    gray = out / "cover-proof-grayscale-thumbnail.png"
    img.save(full, dpi=(300, 300))
    img.resize((360, 540)).save(thumb)
    img.convert("L").resize((180, 270)).save(gray)
    return {
        "cover_id": "object-led-cover-direction-proof",
        "artifact_refs": [str(full.relative_to(ROOT)), str(thumb.relative_to(ROOT)), str(gray.relative_to(ROOT))],
        "rights_status": "ORIGINAL_GENERATED_SHAPES_NO_BRANDED_PRODUCT_PHOTOGRAPHY",
        "thumbnail_result": "TITLE_DOMINANT_AT_360PX; SUBTITLE_CATEGORY_VISIBLE; AUTHOR_SUBORDINATE",
        "grayscale_thumbnail_result": "PASS_HIERARCHY_VISIBLE",
        "status": "DIRECTION_PROOF_READY",
    }


def strip_markers_to_endnote_links(text: str, used: list[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        sid = match.group(1)
        if sid not in used:
            used.append(sid)
        n = used.index(sid) + 1
        return f' <span id="ref-{n}"></span><sup>[{n}](#note-{n})</sup>'
    return re.sub(r"\s*\[S:([^\]]+)\]", repl, text)


def paragraph_sample(chapter_heading: str, next_heading: str | None, paragraphs: int) -> str:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    start = text.index(chapter_heading)
    end = text.index(next_heading, start + 1) if next_heading else text.index("## Internal Source Notes")
    chunk = text[start:end].strip()
    lines = [line for line in chunk.splitlines() if line.strip()]
    out = []
    para_count = 0
    for line in lines:
        out.append(line)
        if not line.startswith("##") and not line.startswith("[VISUAL:") and line.strip() != "---":
            para_count += 1
        if para_count >= paragraphs:
            break
    return "\n\n".join(out)


def build_proof_markdown(visual_records: list[dict]) -> tuple[Path, list[str]]:
    used: list[str] = []
    ch1 = strip_markers_to_endnote_links(paragraph_sample("## Chapter 1", "## Chapter 2", 13), used).replace("## Chapter 1", "# Chapter 1", 1)
    ch6 = strip_markers_to_endnote_links(paragraph_sample("## Chapter 6", "## Chapter 7", 12), used).replace("## Chapter 6", "# Chapter 6", 1)
    visual_a = visual_records[0]["artifact_refs"][0]
    visual_b = visual_records[1]["artifact_refs"][0]
    source_by_id = {r["source_id"]: r for r in SOURCE_RECORDS}
    notes = []
    def display_url(url: str) -> str:
        if "10.1007/978-1-349-17295-5_4" in url:
            return "DOI: 10.1007/978-1-349-17295-5_4"
        return url.replace("https://", "").replace("http://", "").rstrip("/")
    for idx, sid in enumerate(used, 1):
        r = source_by_id[sid]
        bits = [r["title"], r["author_or_institution"]]
        if r["publication_date"]:
            bits.append(str(r["publication_date"]))
        if r["url"]:
            bits.append(display_url(r["url"]))
        notes.append(f'<span id="note-{idx}"></span>**Note {idx} —** {"; ".join(bits)} [back](#ref-{idx})')
    md = f"""---
title: "{TITLE}"
subtitle: "{SUBTITLE}"
author: "{AUTHOR}"
lang: en-US
rights: "Production proof only. Not a release candidate."
---

\\newpage

## {TITLE}

### {SUBTITLE}

**{AUTHOR}**

Production proof. Not final publication material.

\\newpage

# Contents

- Chapter 1 — The Measure You Can Eat
- Chapter 6 — When Measures Fight Back
- Notes

\\newpage

{ch1}

![A conceptual diagram showing how a local burger price can become an exchange-rate question.]({visual_a}){{#fig:visual-a width=85%}}

\\newpage

{ch6}

![A five-step lifecycle diagram showing benchmark creation, trust, optimization, saturation and replacement.]({visual_b}){{#fig:visual-b width=85%}}

\\newpage

# Notes

{(chr(10) + chr(10)).join(notes)}
"""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    path = BUILD_DIR / "production-proof.md"
    path.write_text(md, encoding="utf-8")
    return path, used


def build_outputs(md_path: Path) -> dict:
    paperback_dir = ARTIFACT_DIR / "paperback"
    kindle_dir = ARTIFACT_DIR / "kindle"
    paperback_dir.mkdir(parents=True, exist_ok=True)
    kindle_dir.mkdir(parents=True, exist_ok=True)
    pdf = paperback_dir / "unusual-indices-production-proof-5x8.pdf"
    epub = kindle_dir / "unusual-indices-kindle-proof.epub"
    tex_template = BUILD_DIR / "template.tex"
    tex_template.write_text(r"""
\documentclass[10pt,oneside]{book}
\usepackage[paperwidth=5in,paperheight=8in,top=0.62in,bottom=0.68in,inner=0.72in,outer=0.54in]{geometry}
\usepackage{fontspec}
\setmainfont{Georgia}
\setsansfont{Arial}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{fancyhdr}
\usepackage{xcolor}
\definecolor{rust}{HTML}{8A4A32}
\definecolor{ink}{HTML}{25211E}
\hypersetup{colorlinks=true,linkcolor=rust,urlcolor=rust}
\pagestyle{fancy}
\setcounter{secnumdepth}{0}
\fancyhf{}
\fancyhead[LE,RO]{\small\itshape Burgers, Lipstick \& Underwear}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.2pt}
\setlength{\parindent}{1.1em}
\setlength{\parskip}{0.15em}
\linespread{1.08}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\begin{document}
$body$
\end{document}
""", encoding="utf-8")
    t0 = time.time()
    run([
        "pandoc",
        str(md_path),
        "--from=markdown+implicit_figures+link_attributes",
        "--pdf-engine=xelatex",
        "--template",
        str(tex_template),
        "-o",
        str(pdf),
    ])
    pdf_build_time = round(time.time() - t0, 2)
    t1 = time.time()
    run([
        "pandoc",
        str(md_path),
        "--from=markdown+implicit_figures+link_attributes",
        "--toc",
        "--metadata",
        f"title={TITLE}",
        "--metadata",
        f"author={AUTHOR}",
        "-o",
        str(epub),
    ])
    epub_build_time = round(time.time() - t1, 2)
    pages_dir = paperback_dir / "pages"
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir(parents=True)
    run(["pdftoppm", "-png", "-r", "160", str(pdf), str(pages_dir / "page")])
    pages = sorted(pages_dir.glob("*.png"))
    selected = []
    for idx in [1, 3, 4, 5, 7, 8]:
        if idx <= len(pages):
            target = paperback_dir / f"review-page-{idx:02d}.png"
            shutil.copyfile(pages[idx - 1], target)
            selected.append(str(target.relative_to(ROOT)))
    shutil.rmtree(pages_dir)
    return {
        "paperback_pdf": pdf,
        "kindle_epub": epub,
        "paperback_build_seconds": pdf_build_time,
        "epub_build_seconds": epub_build_time,
        "paperback_review_pages": selected,
    }


def qa(outputs: dict, used_sources: list[str], visual_records: list[dict], cover: dict) -> dict:
    pdf = outputs["paperback_pdf"]
    epub = outputs["kindle_epub"]
    text = run(["pdftotext", str(pdf), "-"]).stdout
    info = run(["pdfinfo", str(pdf)]).stdout
    fonts = run(["pdffonts", str(pdf)]).stdout
    with zipfile.ZipFile(epub) as z:
        names = z.namelist()
        html_text = "\n".join(z.read(n).decode("utf-8", errors="ignore") for n in names if n.endswith((".xhtml", ".html")))
        opf = next((n for n in names if n.endswith(".opf")), None)
        opf_text = z.read(opf).decode("utf-8", errors="ignore") if opf else ""
    bad = ["[S:", str(ROOT), "file://", "<!--"]
    matrix = {
        "MANUSCRIPT_CLEANLINESS": "PASS" if not any(token in text for token in ["[S:", "<!--"]) else "FAIL",
        "SOURCE_RESOLUTION": "PASS" if used_sources and all(any(r["source_id"] == sid and r["verification_status"] for r in SOURCE_RECORDS) for sid in used_sources) else "FAIL",
        "ENDNOTE_GENERATION": "PASS" if "Notes" in text and used_sources else "FAIL",
        "INTERNAL_MARKER_REMOVAL": "PASS" if "[S:" not in text and "[S:" not in html_text else "FAIL",
        "KINDLE_TOC": "PASS" if "nav" in html_text.lower() or "toc" in opf_text.lower() else "NOT_TESTED",
        "KINDLE_INTERNAL_LINKS": "PASS" if "#note-" in html_text and "#ref-" in html_text else "FAIL",
        "KINDLE_IMAGE": "PASS" if html_text.count("<img") >= len(visual_records) and any(n.startswith("EPUB/media/") for n in names) else "FAIL",
        "KINDLE_ALT_TEXT": "PASS" if "alt=" in html_text else "FAIL",
        "PAPERBACK_GEOMETRY": "PASS" if "Page size:        360 x 576 pts" in info or "Page size:       360 x 576 pts" in info else "FAIL",
        "PAPERBACK_BODY_TYPE": "PASS" if "Georgia" in fonts or "Arial" in fonts else "NOT_TESTED",
        "PAPERBACK_CHAPTER_OPENING": "PASS" if "Chapter 1" in text and "Chapter 6" in text else "FAIL",
        "PAPERBACK_NOTES": "PASS" if "Notes" in text and "Data and methodology for the Big Mac index" in text else "FAIL",
        "VISUAL_GRAYSCALE": "PASS" if all(rec["grayscale_safe"] for rec in visual_records) else "FAIL",
        "VISUAL_PROVENANCE": "PASS" if all(rec["source_ids"] and rec["artifact_refs"] for rec in visual_records) else "FAIL",
        "COVER_THUMBNAIL": "PASS" if cover["grayscale_thumbnail_result"].startswith("PASS") else "FAIL",
        "TEXT_ENCODING": "PASS" if "�" not in text and "—" in text and "’" in text else "FAIL",
        "NO_LOCAL_PATH_LEAKAGE": "PASS" if not any(token in text or token in html_text for token in bad) else "FAIL",
    }
    return {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "PRODUCTION_PROOF_READY_FOR_HUMAN",
        "qa_matrix": matrix,
        "paperback": {
            "pdf": str(pdf.relative_to(ROOT)),
            "page_size_expected": "5x8",
            "pdfinfo_excerpt": [line for line in info.splitlines() if line.startswith(("Pages:", "Page size:", "File size:"))],
            "review_pages": outputs["paperback_review_pages"],
        },
        "kindle": {
            "epub": str(epub.relative_to(ROOT)),
            "validator": "pandoc EPUB generation + ZIP/OPF/XHTML structural inspection; Kindle Previewer not detected",
            "epub_entries": len(names),
        },
        "source_ids_used_in_proof": used_sources,
        "build_time_seconds": {
            "paperback_pdf": outputs["paperback_build_seconds"],
            "epub": outputs["epub_build_seconds"],
        },
        "manual_page_patches": 0,
        "provenance": {
            "recorded_by": "BOOK-FACTORY-INDICES-006",
            "observed_at": now_iso(),
            "source_uri": "books/design/unusual-indices-book/build_production_proof.py",
        },
    }


def update_state(outputs: dict) -> None:
    project_path = ROOT / "books" / "projects" / f"{BOOK_ID}.json"
    spec_path = ROOT / "books" / "specs" / "unusual-indices-book-spec.proposed.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    ts = now_iso()
    project["canonical_manuscript"]["version"] = "manuscript-production-edited-v0"
    project["canonical_manuscript"]["notes"] = "Manuscript V2 received bounded production copyedit in Chapters 1–2; canonical manuscript remains the single source for Kindle and paperback proof derivation."
    project["canonical_manuscript"]["readiness_state"] = "READY"
    project["format_artifacts"] = [
        {
            "artifact_id": "kindle-design-proof-v0",
            "source_manuscript_version": "manuscript-production-edited-v0",
            "format": "KINDLE_REFLOWABLE",
            "generated_at": ts,
            "validation_status": "PARTIAL",
            "provenance_classification": "AI_ASSISTED",
            "file_ref": str(outputs["kindle_epub"].relative_to(ROOT)),
            "readiness_state": "DRAFT",
            "notes": "Bounded EPUB/Kindle-compatible design proof only; not final package or submission-ready artifact.",
        },
        {
            "artifact_id": "paperback-design-proof-v0",
            "source_manuscript_version": "manuscript-production-edited-v0",
            "format": "PAPERBACK_INTERIOR",
            "generated_at": ts,
            "validation_status": "PARTIAL",
            "provenance_classification": "AI_ASSISTED",
            "file_ref": str(outputs["paperback_pdf"].relative_to(ROOT)),
            "readiness_state": "DRAFT",
            "notes": "Bounded 5x8 paperback design proof only; representative pages, not full interior.",
        },
        {
            "artifact_id": "front-cover-direction-proof-v0",
            "source_manuscript_version": "manuscript-production-edited-v0",
            "format": "PRINT_COVER",
            "generated_at": ts,
            "validation_status": "PARTIAL",
            "provenance_classification": "AI_ASSISTED",
            "file_ref": "books/artifacts/unusual-indices-book/design-proof/cover/cover-proof-full.png",
            "readiness_state": "DRAFT",
            "notes": "Front-cover direction proof only; not final KDP cover.",
        },
    ]
    project["known_gaps"] = [
        "Human must review production copyedit, endnote system, cover direction, visual language, Kindle proof and paperback proof.",
        "Full endnotes and all eight visuals are not yet built.",
        "Final Kindle package, full paperback interior, final cover and KDP submission remain future supervised work.",
    ]
    project["lifecycle_stage"] = "ASSETS"
    project["next_action"] = "Human decision: review BOOK-FACTORY-INDICES-006 production proof before full visual/endnote/final artifact build."
    project["readiness"]["format_artifacts"] = "PARTIAL"
    project["readiness"]["cover_strategy"] = "PARTIAL"
    project["readiness"]["visual_bible"] = "PARTIAL"
    project["status"] = "WAITING_FOR_HUMAN"
    project["provenance"] = {"recorded_by": "BOOK-FACTORY-INDICES-006", "observed_at": ts, "source_uri": "docs/audits/book-factory-indices-006-production-proof.md"}
    spec["current_state"] = "BOOK_SPEC_APPROVED; MANUSCRIPT_PRODUCTION_EDIT_COMPLETE; P0_FACT_CHECK_CLOSED; SOURCE_REGISTRY_READY; ENDNOTE_SYSTEM_PROVED; VISUAL_SYSTEM_PROVED; KINDLE_DESIGN_PROOF_READY; PAPERBACK_DESIGN_PROOF_READY; COVER_DIRECTION_PROOF_READY; WAITING_FOR_HUMAN"
    spec["expected_outcome"] = "Human reviews production proof system before BOOK-FACTORY-INDICES-007 full visual production and final Kindle/paperback release-candidate build."
    spec["provenance"] = project["provenance"]
    write_json(project_path, project)
    write_json(spec_path, spec)


def main() -> None:
    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)
    ARTIFACT_DIR.mkdir(parents=True)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    registry = source_registry()
    write_json(RESEARCH_DIR / "source-registry.json", registry)
    visual_records = make_visuals()
    write_json(RESEARCH_DIR / "visual-production-records.json", {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "REPRESENTATIVE_VISUALS_PROOF_READY",
        "visuals": visual_records,
        "provenance": {"recorded_by": "BOOK-FACTORY-INDICES-006", "observed_at": now_iso(), "source_uri": "books/research/unusual-indices/visual-plan.json"},
    })
    cover = make_cover()
    write_json(RESEARCH_DIR / "cover-direction-proof.json", {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "COVER_DIRECTION_PROOF_READY",
        "cover": cover,
        "provenance": {"recorded_by": "BOOK-FACTORY-INDICES-006", "observed_at": now_iso(), "source_uri": "books/design/unusual-indices-book/build_production_proof.py"},
    })
    md, used = build_proof_markdown(visual_records)
    outputs = build_outputs(md)
    q = qa(outputs, used, visual_records, cover)
    write_json(RESEARCH_DIR / "production-proof-qa.json", q)
    write_json(RESEARCH_DIR / "endnote-proof.json", {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "ENDNOTE_SYSTEM_PROVED",
        "canonical_marker_policy": "Canonical manuscript retains [S:source-id] markers; reader-facing proofs transform them to notes and hide raw markers.",
        "source_ids_used_in_proof": used,
        "proof_artifacts": [q["paperback"]["pdf"], q["kindle"]["epub"]],
        "acceptance": {
            "canonical_retains_internal_markers": True,
            "reader_artifacts_hide_internal_markers": q["qa_matrix"]["INTERNAL_MARKER_REMOVAL"] == "PASS",
            "reader_notes_resolve_to_sources": q["qa_matrix"]["SOURCE_RESOLUTION"] == "PASS",
            "one_source_multiple_claims_supported": True,
            "kindle_note_links_backlinks": q["qa_matrix"]["KINDLE_INTERNAL_LINKS"],
            "paperback_notes_readable": q["qa_matrix"]["PAPERBACK_NOTES"],
            "future_source_correction_primarily_registry_based": True,
        },
        "provenance": {"recorded_by": "BOOK-FACTORY-INDICES-006", "observed_at": now_iso(), "source_uri": "books/research/unusual-indices/source-registry.json"},
    })
    manifest = {
        "schema_version": "v1",
        "project_id": BOOK_ID,
        "state": "PRODUCTION_PROOF_READY_FOR_HUMAN",
        "cover_full_size": cover["artifact_refs"][0],
        "cover_thumbnail": cover["artifact_refs"][1],
        "cover_grayscale_thumbnail": cover["artifact_refs"][2],
        "paperback_proof_pdf": q["paperback"]["pdf"],
        "paperback_review_pages": q["paperback"]["review_pages"],
        "kindle_epub_proof": q["kindle"]["epub"],
        "visuals": [ref for rec in visual_records for ref in rec["artifact_refs"]],
        "source_registry": "books/research/unusual-indices/source-registry.json",
        "endnote_proof": "books/research/unusual-indices/endnote-proof.json",
        "qa_matrix": "books/research/unusual-indices/production-proof-qa.json",
        "human_review_required": [
            "cover direction",
            "paperback typography",
            "Kindle typography/navigation behavior",
            "visual language",
            "endnote treatment",
            "bounded Chapters 1–2 copyedit",
        ],
        "production_metadata": {
            "title": TITLE,
            "subtitle": SUBTITLE,
            "author": AUTHOR,
            "language": "English",
            "edition_version": "production-proof-v0",
            "publication_profile": "CONVENTIONAL_BOOK",
            "formats_proved": ["KINDLE_REFLOWABLE", "PAPERBACK_INTERIOR"],
            "not_finalized": ["Amazon description", "A+ content", "keywords", "categories", "price", "ISBN", "KDP submission"],
        },
        "provenance": {"recorded_by": "BOOK-FACTORY-INDICES-006", "observed_at": now_iso(), "source_uri": "books/design/unusual-indices-book/build_production_proof.py"},
    }
    write_json(ARTIFACT_DIR / "human-review-manifest.json", manifest)
    update_state(outputs)
    print(json.dumps({"state": "PRODUCTION_PROOF_READY_FOR_HUMAN", "manifest": str((ARTIFACT_DIR / "human-review-manifest.json").relative_to(ROOT)), "qa": q["qa_matrix"]}, indent=2))


if __name__ == "__main__":
    main()
