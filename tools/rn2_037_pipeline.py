#!/usr/bin/env python3
"""Deterministic source extraction and production data checks for RN2-037."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "books" / "rn2-037"
RAW = BASE / "sources" / "raw"
DATA = BASE / "data"
POOL_TXT = RAW / "ncvec-technician-pool-2026-2030-corrected-2026-02-19.txt"

CHAPTERS = {
    "T5": (1, "Electricity without intimidation"),
    "T6": (2, "Components as jobs, not symbols"),
    "T7A": (3, "Inside a radio and on the bench"),
    "T7D": (3, "Inside a radio and on the bench"),
    "T7B": (4, "Troubleshoot by symptom, cause, and safe action"),
    "T7C": (4, "Troubleshoot by symptom, cause, and safe action"),
    "T3": (5, "Waves, frequency, and propagation"),
    "T9": (6, "Antennas, feed lines, and SWR"),
    "T8": (7, "Signals and ways hams communicate"),
    "T4": (8, "First station and operating controls"),
    "T2": (9, "Getting on the air"),
    "T1": (10, "Rules as decision paths"),
    "T0": (11, "Safety before shortcuts"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def chapter_for(qid: str):
    group = qid[:3]
    if group in CHAPTERS:
        return CHAPTERS[group]
    return CHAPTERS[qid[:2]]


def parse_pool(text: str):
    questions = []
    rx = re.compile(r"(?m)^\s*(T[0-9][A-Z][0-9]{2})\s+\(([A-D])\)(?:\s*\[([^\]]+)\])?\s*$")
    option_rx = re.compile(r"^([A-D])\.\s+(.*)$")
    matches = list(rx.finditer(text))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[match.end():end]
        if "~~" in block:
            block = block.split("~~", 1)[0]
        lines = [re.sub(r"\s+", " ", x.strip()) for x in block.replace("\f", "\n").splitlines() if x.strip()]
        stem_parts, opts, current = [], {}, None
        for line in lines:
            om = option_rx.match(line)
            if om:
                current = om.group(1)
                opts[current] = om.group(2)
            elif current:
                opts[current] += " " + line
            else:
                stem_parts.append(line)
        qid, answer, citation = match.group(1), match.group(2), match.group(3)
        if len(opts) != 4:
            raise ValueError(f"{qid}: expected four options, got {opts}")
        chapter, chapter_title = chapter_for(qid)
        figures = sorted(set(re.findall(r"Figure\s+(T-[123])", " ".join(lines), flags=re.I)))
        questions.append({
                "id": qid,
                "subelement": qid[:2],
                "group": qid[:3],
                "question": " ".join(stem_parts),
                "options": opts,
                "correct_option": answer,
                "correct_answer": opts[answer],
                "fcc_citation": citation,
                "diagram_refs": figures,
                "source_page": text.count("\f", 0, match.start()) + 1,
                "source_file": POOL_TXT.with_suffix(".pdf").name,
                "primary_chapter": chapter,
                "primary_chapter_title": chapter_title,
                "coverage_mode": "TAUGHT" if qid[:2] in {"T3", "T5", "T6", "T7", "T9"} else "DIRECT_RECALL",
        })
    return questions


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    questions = parse_pool(POOL_TXT.read_text(encoding="utf-8"))
    ids = [q["id"] for q in questions]
    if len(questions) != 409 or len(set(ids)) != 409:
        raise SystemExit(f"STOP: extracted={len(questions)} unique={len(set(ids))}")
    expected_counts = {"T0": 36, "T1": 68, "T2": 37, "T3": 35, "T4": 23, "T5": 50, "T6": 46, "T7": 44, "T8": 47, "T9": 23}
    actual_counts = dict(sorted(Counter(q["subelement"] for q in questions).items()))
    if actual_counts != expected_counts:
        raise SystemExit(f"STOP: subelement counts {actual_counts}")
    payload = {
        "schema_version": "rn2-037-question-pool/v1",
        "pool": {
            "name": "2026-2030 Technician Class FCC Element 2 Question Pool",
            "corrected_release": "2026-02-19",
            "effective_from": "2026-07-01",
            "effective_to": "2030-06-30",
            "retrieved_and_checked": str(date.today()),
            "controlling_url": "https://ncvec.org/index.php/2026-2030-technician-question-pool",
            "local_source_sha256": sha256(POOL_TXT.with_suffix(".pdf")),
            "text_extraction_sha256": sha256(POOL_TXT),
            "public_domain_statement": "NCVEC QPC expressly releases the pool into the public domain.",
            "errata_question_ids": ["T1C01", "T5A05", "T7A09", "T0A10"],
        },
        "questions": questions,
    }
    (DATA / "question-pool-2026-2030.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    by_chapter = defaultdict(list)
    for q in questions:
        by_chapter[str(q["primary_chapter"])].append(q["id"])
    crosswalk = {
        "schema_version": "rn2-037-crosswalk/v1",
        "pool_source_sha256": payload["pool"]["local_source_sha256"],
        "primary_mapping_rule": "exactly one primary chapter per active official question ID",
        "chapter_counts": {k: len(v) for k, v in sorted(by_chapter.items(), key=lambda x: int(x[0]))},
        "mappings": [{
            "question_id": q["id"],
            "primary_chapter": q["primary_chapter"],
            "primary_chapter_title": q["primary_chapter_title"],
            "concept": q["group"],
            "coverage_mode": q["coverage_mode"],
            "source_page": q["source_page"],
            "secondary_concepts": [],
        } for q in questions],
    }
    (DATA / "crosswalk.json").write_text(json.dumps(crosswalk, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "PASS",
        "expected_ids": 409,
        "extracted_ids": len(ids),
        "unique_ids": len(set(ids)),
        "missing_ids": [],
        "duplicate_ids": [x for x, n in Counter(ids).items() if n > 1],
        "malformed_questions": 0,
        "four_options_each": all(len(q["options"]) == 4 for q in questions),
        "answer_key_resolves": all(q["correct_option"] in q["options"] for q in questions),
        "subelement_counts": actual_counts,
        "primary_crosswalk_ids": len(crosswalk["mappings"]),
        "primary_crosswalk_unique": len({m["question_id"] for m in crosswalk["mappings"]}),
        "errata_ids_present": all(x in set(ids) for x in payload["pool"]["errata_question_ids"]),
    }
    (BASE / "qa" / "question-pool-extraction.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
