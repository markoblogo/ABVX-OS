#!/usr/bin/env python3
"""Build a bounded typography/glyph prototype from the immutable Jekyll Text Lock."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "jekyll-toki-pona-production-v1"
LOCKED = ROOT / "artifacts/jekyll-toki-pona-full-v1/MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_TEXT_LOCK_V1.md"
LEDGER = ROOT / "artifacts/jekyll-toki-pona-full-v1/JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V4.json"
SEGMENTATION = ROOT / "artifacts/jekyll-toki-pona-full-v1/segmentation-manifest.json"
SOURCE_MANIFEST = ROOT / "artifacts/jekyll-toki-pona-full-v1/source-manifest.json"
EXPECTED_LOCK_SHA = "a174999649808399aa49e5b8ff3319b89e30f39a78118be83d53bc93e37fd5ef"
SAMPLES = [
    "jekyll-full-v1:chapter-01:block-0001",
    "jekyll-full-v1:chapter-01:block-0011",
    "jekyll-full-v1:chapter-02:block-0011",
    "jekyll-full-v1:chapter-02:block-0012",
    "jekyll-full-v1:chapter-05:block-0003",
    "jekyll-full-v1:chapter-10:block-0112",
]
SAMPLE_GROUP_STARTS = {SAMPLES[1], SAMPLES[4], SAMPLES[5]}


def tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(char, char) for char in value)


def tex_sitelen(value: str) -> str:
    """Add layout-only break opportunities while preserving the manifest input."""
    words = value.split()
    return r" \linebreak[4] ".join(
        tex_escape(" ".join(words[start : start + 12]))
        for start in range(0, len(words), 12)
    )


def locked_paragraphs(markdown: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    sections = __import__("re").split(r"(?m)^## ", markdown)
    for section in sections[1:]:
        lines = section.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        for paragraph in __import__("re").split(r"\n\s*\n", body):
            paragraph = paragraph.strip()
            if paragraph and not paragraph.startswith("#"):
                result.append((title, paragraph))
    return result


def main() -> None:
    lock_bytes = LOCKED.read_bytes()
    lock_sha = hashlib.sha256(lock_bytes).hexdigest()
    if lock_sha != EXPECTED_LOCK_SHA:
        raise SystemExit(f"Text Lock SHA mismatch: {lock_sha}")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = {row["blockId"]: row for row in ledger["blocks"]}
    if len(rows) != 462 or not set(SAMPLES) <= rows.keys():
        raise SystemExit("Editorial ledger must contain all 462 blocks and all selected samples")
    locked_rows = locked_paragraphs(lock_bytes.decode("utf-8"))
    locked_text_by_id: dict[str, str] = {}
    if len(locked_rows) != 462:
        raise SystemExit(f"Text Lock paragraph count mismatch: {len(locked_rows)}")
    for row, (chapter_title, paragraph) in zip(ledger["blocks"], locked_rows):
        normalize = lambda value: " ".join(value.split())
        if normalize(row["revisedTranslation"]) != normalize(paragraph):
            raise SystemExit(f"Text Lock text mismatch: {row['blockId']}")
        if row["chapterTitle"].casefold() != chapter_title.casefold():
            raise SystemExit(f"Text Lock chapter order mismatch: {row['blockId']}")
        locked_text_by_id[row["blockId"]] = paragraph
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    normalized_source_path = ROOT / "artifacts/jekyll-toki-pona-preproduction-v1/source/jekyll-hyde-gutenberg-42-normalized.txt"
    normalized_source_sha = hashlib.sha256(normalized_source_path.read_bytes()).hexdigest()
    if normalized_source_sha != source["normalizedSha256"]:
        raise SystemExit("Normalized Gutenberg source hash mismatch")
    source_rows = json.loads(SEGMENTATION.read_text(encoding="utf-8"))["blocksData"]
    if len(source_rows) != len(ledger["blocks"]):
        raise SystemExit("Source segmentation block count mismatch")
    for row, source_row in zip(ledger["blocks"], source_rows):
        if row["blockId"] != source_row["blockId"] or row["source"] != source_row["sourceText"]:
            raise SystemExit(f"English source alignment/order mismatch: {row['blockId']}")
        if hashlib.sha256(row["source"].encode("utf-8")).hexdigest() != row["sourceSha256"]:
            raise SystemExit(f"English source hash mismatch: {row['blockId']}")
    normalized_source = normalized_source_path.read_text(encoding="utf-8")
    first_title = ledger["blocks"][0]["chapterTitle"]
    body_start = normalized_source.find(first_title, 1)
    if body_start < 0:
        raise SystemExit("Could not locate the start of the canonical story body")
    source_body_lines = normalized_source[body_start:].splitlines()
    chapter_titles = {row["chapterTitle"] for row in ledger["blocks"]}
    mapped_body = " ".join(
        " ".join(line for line in source_body_lines if line.strip() not in chapter_titles).split()
    )
    segmented_body = " ".join(" ".join(row["source"] for row in ledger["blocks"]).split())
    if mapped_body != segmented_body:
        raise SystemExit("Full English source body does not exactly match the 462 source blocks in order")
    contents_words = len(normalized_source[:body_start].split())
    chapter_title_words = sum(len(title.split()) for title in chapter_titles)

    parts = [
        r"\documentclass[11pt,openany]{book}",
        r"\usepackage[paperwidth=5.5in,paperheight=8.5in,inner=0.72in,outer=0.58in,top=0.62in,bottom=0.68in]{geometry}",
        r"\usepackage{fontspec,microtype}",
        r"\setmainfont{Georgia}",
        r"\newfontfamily\sitelen[Path=/Users/antonbiletskiy-volokh/Library/Fonts/,Extension=.otf]{NasinSitelenPuMono}",
        r"\setlength{\parskip}{0.55em}",
        r"\setlength{\parindent}{0pt}",
        r"\raggedbottom",
        r"\newcommand{\layer}[1]{\vspace{0.35em}{\small\bfseries #1}\par\vspace{0.15em}}",
        r"\clubpenalty=10000\widowpenalty=10000\brokenpenalty=10000\emergencystretch=2em",
        r"\newcommand{\sample}[4]{\begin{samepage}\layer{ENGLISH SOURCE — #1}\noindent #2\par\layer{TOKI PONA — LOCKED LATIN}\noindent\textit{#3}\par\layer{SITELEN PONA — SAME LOCKED INPUT}\noindent{{\sloppy\raggedright\sitelen\fontsize{12}{17}\selectfont #4}\par}\vspace{0.75em}\hrule\vspace{0.45em}\end{samepage}}",
        r"\begin{document}",
        r"\thispagestyle{empty}",
        r"\begin{center}{\Large\bfseries THE STRANGE CASE OF DR. JEKYLL AND MR. HYDE}\\[0.25em]{\small Toki Pona Edition with Sitelen Pona — pagination prototype only}\end{center}",
        r"\vspace{0.3em}\hrule\vspace{0.55em}{\small Selected, non-contiguous source blocks are shown to test typography. The glyph layer receives the exact locked Latin string; it is not a new translation.}",
    ]
    manifest = []
    for block_id in SAMPLES:
        row = rows[block_id]
        en = tex_escape(row["source"])
        tp = tex_escape(row["revisedTranslation"])
        if block_id in SAMPLE_GROUP_STARTS:
            parts.append(r"\newpage")
        parts.append(r"\sample{" + tex_escape(block_id) + "}{" + en + "}{" + tp + "}{" + tex_sitelen(row["revisedTranslation"]) + "}")
        manifest.append(
            {
                "blockId": block_id,
                "sourceSha256": row["sourceSha256"],
                "english": row["source"],
                "tokiPonaLatin": row["revisedTranslation"],
                "sitelenPonaInput": row["revisedTranslation"],
                "sitelenInputEqualsLockedLatin": row["revisedTranslation"]
                == locked_text_by_id[block_id],
            }
        )
    parts.extend([r"\end{document}", ""])
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "jekyll-production-prototype-v1.tex").write_text(
        "\n".join(parts), encoding="utf-8"
    )
    (ARTIFACTS / "prototype-sample-manifest.json").write_text(
        json.dumps(
            {
                "textLockPath": str(LOCKED.relative_to(ROOT)),
                "textLockSha256": lock_sha,
                "selectedBlockCount": len(manifest),
                "alignedFullBookBlocks": len(ledger["blocks"]),
                "englishSourceBlocksInOrder": len(source_rows),
                "sourceBlocksHashVerified": len(source_rows),
                "lockedLatinBlocksVerified": len(locked_rows),
                "englishBodyWordCount": len(segmented_body.split()),
                "excludedContentsWordCount": contents_words,
                "excludedChapterHeadingWordCount": chapter_title_words,
                "englishBodySha256AfterWhitespaceNormalization": hashlib.sha256(
                    mapped_body.encode("utf-8")
                ).hexdigest(),
                "fullEnglishBodyOrderMatchesBlocks": True,
                "missingEnglishBlocks": 0,
                "duplicateEnglishBlocks": 0,
                "reorderedEnglishBlocks": 0,
                "ambiguousEnglishBlocks": 0,
                "sourceManifestClaimMismatch": "Normalized source still contains the contents-heading preamble despite metadata saying it was excluded; preamble and chapter-heading words are intentionally excluded from production mapping.",
                "samples": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Text Lock SHA-256: {lock_sha}")
    print(f"Prototype source: {ARTIFACTS / 'jekyll-production-prototype-v1.tex'}")
    print(f"Sample blocks: {len(manifest)}")


if __name__ == "__main__":
    main()
