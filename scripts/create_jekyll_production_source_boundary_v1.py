#!/usr/bin/env python3
"""Verify and materialize the immutable Jekyll production source boundary."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/jekyll-toki-pona-production-v1"
FULL = ROOT / "artifacts/jekyll-toki-pona-full-v1"
SOURCE = ROOT / "artifacts/jekyll-toki-pona-preproduction-v1/source"
RAW = SOURCE / "gutenberg-42-2026-09-21.txt"
NORMALIZED = SOURCE / "jekyll-hyde-gutenberg-42-normalized.txt"
SOURCE_MANIFEST = FULL / "source-manifest.json"
SEGMENTATION = FULL / "segmentation-manifest.json"
LEDGER = FULL / "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V4.json"
TEXT_LOCK = FULL / "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_TEXT_LOCK_V1.md"
EXPECTED_TEXT_LOCK_SHA = "a174999649808399aa49e5b8ff3319b89e30f39a78118be83d53bc93e37fd5ef"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_words(text: str) -> str:
    return " ".join(text.split())


def locked_paragraphs(markdown: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for section in re.split(r"(?m)^## ", markdown)[1:]:
        lines = section.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        for paragraph in re.split(r"\n\s*\n", body):
            paragraph = paragraph.strip()
            if paragraph and not paragraph.startswith("#"):
                result.append((title, paragraph))
    return result


def main() -> None:
    raw_bytes, normalized_bytes = RAW.read_bytes(), NORMALIZED.read_bytes()
    raw_sha, normalized_sha = sha256(raw_bytes), sha256(normalized_bytes)
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    segmentation = json.loads(SEGMENTATION.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    lock_bytes = TEXT_LOCK.read_bytes()

    if raw_sha != source_manifest["rawSha256"]:
        raise SystemExit("Gutenberg raw source hash mismatch")
    if normalized_sha != source_manifest["normalizedSha256"]:
        raise SystemExit("Normalized Gutenberg source hash mismatch")
    lock_sha = sha256(lock_bytes)
    if lock_sha != EXPECTED_TEXT_LOCK_SHA:
        raise SystemExit(f"Text Lock hash mismatch: {lock_sha}")

    rows = ledger["blocks"]
    source_rows = segmentation["blocksData"]
    if len(rows) != 462 or len(source_rows) != 462:
        raise SystemExit(f"Expected 462 rows in both maps, got ledger={len(rows)} source={len(source_rows)}")
    ids = [row["blockId"] for row in rows]
    if len(set(ids)) != 462:
        raise SystemExit("Duplicate block IDs in V4 ledger")

    chapter_titles = []
    chapters: dict[int, list[dict]] = {}
    for row, source_row in zip(rows, source_rows):
        if row["blockId"] != source_row["blockId"]:
            raise SystemExit(f"Block ID/order mismatch: {row['blockId']} vs {source_row['blockId']}")
        if row["source"] != source_row["sourceText"]:
            raise SystemExit(f"Source text mismatch: {row['blockId']}")
        source_hash = sha256(row["source"].encode("utf-8"))
        if source_hash != row["sourceSha256"] or source_hash != source_row["sourceHash"]:
            raise SystemExit(f"Source hash mismatch: {row['blockId']}")
        if row["chapterTitle"] != source_row["chapterTitle"]:
            raise SystemExit(f"Chapter title mismatch: {row['blockId']}")
        chapter = int(source_row["chapter"])
        if not chapter_titles or chapter_titles[-1] != row["chapterTitle"]:
            chapter_titles.append(row["chapterTitle"])
        chapters.setdefault(chapter, []).append(row)

    expected_orders = list(range(1, 11))
    if sorted(chapters) != expected_orders or len(chapter_titles) != 10:
        raise SystemExit("Expected exactly 10 ordered chapters")
    all_ordinals = [int(row["ordinal"]) for row in rows]
    if all_ordinals != list(range(1, len(rows) + 1)):
        raise SystemExit("Global source ordinals are not contiguous from 1 through 462")

    titles = [chapters[number][0]["chapterTitle"] for number in expected_orders]
    source_lines = NORMALIZED.read_text(encoding="utf-8").splitlines()
    nonblank = [(index + 1, line.strip()) for index, line in enumerate(source_lines) if line.strip()]
    contents = nonblank[:10]
    if [line for _, line in contents] != titles:
        raise SystemExit("The first 10 nonblank lines are not the ordered contents headings")
    contents_words = sum(len(line.split()) for _, line in contents)
    if contents_words != 44:
        raise SystemExit(f"Expected 44 contents/preamble words, got {contents_words}")

    first_title = titles[0]
    body_start = next(
        (index for index, line in enumerate(source_lines)
         if index + 1 > contents[-1][0] and line.strip() == first_title),
        None,
    )
    if body_start is None:
        raise SystemExit("Could not locate the actual narrative start heading")
    heading_set = set(titles)
    removed_headings: list[dict] = [{"line": body_start + 1, "text": first_title}]
    narrative_lines: list[str] = []
    for index, line in enumerate(source_lines[body_start + 1 :], start=body_start + 2):
        stripped = line.strip()
        if stripped in heading_set:
            removed_headings.append({"line": index, "text": stripped})
        else:
            narrative_lines.append(line)
    if [item["text"] for item in removed_headings] != titles:
        raise SystemExit("Expected each of the 10 chapter headings once, in order, in the narrative body")
    heading_words = sum(len(item["text"].split()) for item in removed_headings)
    if heading_words != 44:
        raise SystemExit(f"Expected 44 narrative heading words, got {heading_words}")

    narrative_body = normalized_words(" ".join(narrative_lines))
    mapped_body = normalized_words(" ".join(row["source"] for row in rows))
    if narrative_body != mapped_body:
        raise SystemExit("Narrative after the documented exclusions does not exactly match ordered mapped blocks")
    if len(narrative_body.split()) != 25534:
        raise SystemExit(f"Expected 25,534 mapped English words, got {len(narrative_body.split())}")

    locked = locked_paragraphs(lock_bytes.decode("utf-8"))
    if len(locked) != 462:
        raise SystemExit(f"Expected 462 locked TP paragraphs, got {len(locked)}")
    for row, (title, paragraph) in zip(rows, locked):
        if title.casefold() != row["chapterTitle"].casefold():
            raise SystemExit(f"Text Lock chapter order mismatch at {row['blockId']}")
        if normalized_words(paragraph) != normalized_words(row["revisedTranslation"]):
            raise SystemExit(f"Text Lock translation mismatch at {row['blockId']}")

    chapter_summary = []
    manifest_blocks = []
    for chapter in expected_orders:
        chapter_rows = chapters[chapter]
        chapter_summary.append({
            "chapter": chapter,
            "title": chapter_rows[0]["chapterTitle"],
            "blockCount": len(chapter_rows),
            "englishWordCount": sum(len(row["source"].split()) for row in chapter_rows),
            "firstBlockId": chapter_rows[0]["blockId"],
            "lastBlockId": chapter_rows[-1]["blockId"],
        })
    for row in rows:
        manifest_blocks.append({
            "blockId": row["blockId"],
            "chapter": int(source_rows[len(manifest_blocks)]["chapter"]),
            "chapterTitle": row["chapterTitle"],
            "ordinal": int(row["ordinal"]),
            "blockType": source_rows[len(manifest_blocks)]["blockType"],
            "sourceSha256": row["sourceSha256"],
            "englishSource": row["source"],
        })

    output = {
        "schemaVersion": "1.0",
        "artifact": "JEKYLL_PRODUCTION_SOURCE_BOUNDARY_V1",
        "source": {
            "work": source_manifest["title"],
            "author": source_manifest["author"],
            "gutenbergId": source_manifest["gutenbergId"],
            "recordUrl": source_manifest["recordUrl"],
            "selectedSourceUrl": source_manifest["selectedSourceUrl"],
            "rawArtifact": str(RAW.relative_to(ROOT)),
            "rawSha256": raw_sha,
            "normalizedArtifact": str(NORMALIZED.relative_to(ROOT)),
            "normalizedSha256": normalized_sha,
            "rightsStatusFromHistoricalManifest": source_manifest["rightsStatus"],
            "rightsConditionsFromHistoricalManifest": source_manifest["rightsConditions"],
        },
        "exclusions": {
            "contentsPreamble": {
                "normalizedSourceLines": [contents[0][0], contents[-1][0]],
                "headingCount": len(contents),
                "wordCount": contents_words,
                "texts": [line for _, line in contents],
            },
            "chapterHeadings": {
                "count": len(removed_headings),
                "wordCount": heading_words,
                "linesAndTexts": removed_headings,
            },
            "totalExcludedStructureWords": contents_words + heading_words,
            "note": "Historical normalized file includes contents and chapter headings despite its historical manifest's exclusion wording. Historical inputs were not modified.",
        },
        "proof": {
            "mappedStoryBlockCount": len(rows),
            "uniqueBlockIds": len(set(ids)),
            "mappedEnglishWordCount": len(mapped_body.split()),
            "orderedSourceHashesMatch": True,
            "ledgerAndSegmentationIdsAndTextMatchInOrder": True,
            "normalizedNarrativeEqualsConcatenatedMappedEnglishAfterOnlyDocumentedExclusions": True,
            "noMissingUnits": True,
            "noDuplicateMappings": True,
            "noReorderedUnits": True,
            "noAmbiguousUnits": True,
            "textLockArtifact": str(TEXT_LOCK.relative_to(ROOT)),
            "textLockSha256": lock_sha,
            "textLockParagraphsMatchLedgerInOrder": True,
            "ledgerArtifact": str(LEDGER.relative_to(ROOT)),
            "ledgerSha256": sha256(LEDGER.read_bytes()),
            "segmentationArtifact": str(SEGMENTATION.relative_to(ROOT)),
            "segmentationSha256": sha256(SEGMENTATION.read_bytes()),
        },
        "chapters": chapter_summary,
        "units": manifest_blocks,
    }
    json_path = ART / "JEKYLL_PRODUCTION_SOURCE_BOUNDARY_V1.json"
    md_path = ART / "JEKYLL_PRODUCTION_SOURCE_BOUNDARY_V1.md"
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Jekyll Production Source Boundary V1",
        "",
        "## Verification result",
        "",
        "**PASS:** exactly 462 unique, ordered story-unit mappings; no missing, duplicate mapping, reordered, or ambiguous unit was found. The concatenated English body equals the normalized Gutenberg narrative after only the documented contents and chapter-heading exclusions.",
        "",
        "- Work: Robert Louis Stevenson, *The Strange Case of Dr. Jekyll and Mr. Hyde* (Project Gutenberg #42).",
        f"- Raw source SHA-256: `{raw_sha}`.",
        f"- Normalized source SHA-256: `{normalized_sha}`.",
        f"- Contents/preamble excluded: {len(contents)} heading lines, {contents_words} words (normalized-source lines {contents[0][0]}–{contents[-1][0]}).",
        f"- Narrative chapter headings excluded from the 462 triple-layer units: {len(removed_headings)} lines, {heading_words} words.",
        f"- Mapped story body: {len(rows)} blocks, {len(mapped_body.split())} English words.",
        f"- Text Lock SHA-256: `{lock_sha}`; its 462 TP paragraphs match V4 ledger translations and chapter order.",
        "- Historical source files/manifests remain unchanged. This production-only manifest records the corrected boundary; do not patch the historical manifest in place.",
        "- Historical rights status remains **CONDITIONAL**; re-check territory and KDP public-domain differentiation requirements before release.",
        "",
        "## Chapter map",
        "",
        "| Chapter | Heading | Blocks | English words | First / last block |",
        "|---:|---|---:|---:|---|",
    ]
    for chapter in chapter_summary:
        summary.append(
            f"| {chapter['chapter']} | {chapter['title']} | {chapter['blockCount']} | {chapter['englishWordCount']} | `{chapter['firstBlockId']}` / `{chapter['lastBlockId']}` |"
        )
    summary.extend(["", "## Excluded chapter-heading lines", ""])
    summary.extend(f"- Normalized source line {item['line']}: `{item['text']}`" for item in removed_headings)
    summary.extend(["", "Full block IDs, text, and per-block source hashes are in the companion JSON manifest.", ""])
    md_path.write_text("\n".join(summary), encoding="utf-8")
    print(f"PASS: {len(rows)} blocks; {len(mapped_body.split())} words; exclusions {contents_words}+{heading_words}; wrote {json_path.name} and {md_path.name}")


if __name__ == "__main__":
    main()
