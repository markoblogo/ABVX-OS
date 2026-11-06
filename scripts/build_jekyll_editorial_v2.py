#!/usr/bin/env python3
"""Assemble the reviewed Jekyll Toki Pona V2 and its editorial audit artifacts."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/jekyll-toki-pona-full-v1"
REVIEW = BASE / "editorial-review-v1"
REGISTRY = ROOT / "artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def assemble():
    manifest = read_json(BASE / "JEKYLL_FINAL_462_BLOCK_MANIFEST_V1.json")
    candidates = {r["blockId"]: r for r in read_json(REVIEW / "candidate-adjudication-v2.json")["records"]}
    repairs = {r["blockId"]: r for r in read_json(REVIEW / "targeted-repairs-v1.json")["records"]}
    chapter_reviews = {}
    for n in range(1, 11):
        chapter_reviews.update({r["blockId"]: r for r in read_json(REVIEW / f"chapter-{n:02}.json")["records"]})

    records = []
    chapters: dict[int, list[str]] = {}
    chapter_titles: dict[int, str] = {}
    for item in manifest["orderedBlocks"]:
        bid = item["blockId"]
        checkpoint = read_json(BASE / item["checkpoint"])
        source = checkpoint["source"]
        original = checkpoint["attempts"][0]["translation"]
        chapter = item["chapter"]
        chapter_titles[chapter] = item["chapterTitle"]
        c = candidates.get(bid)
        repair = repairs.get(bid)
        if repair:
            classification = repair["finalClassification"]
            revised = repair["revisedTranslation"]
            issue = repair["sourceMeaningAtIssue"]
            reason = repair["reason"]
            status = "REPAIRED"
            adjudication = repair.get("adjudicatedClassification")
        elif c and c["disposition"] == "NEEDS_HUMAN":
            classification = "BLOCKER"
            revised = original
            issue = c.get("reason", "")
            reason = "Held unchanged; requires editorial decision before Text Lock."
            status = "UNRESOLVED_HUMAN_DECISION"
            adjudication = c["disposition"]
        elif c and c["disposition"] == "DISMISS":
            classification = "SAFE"
            revised = original
            issue = "First-pass concern was not confirmed in contextual adjudication."
            reason = c.get("reason", "Candidate dismissed after checking source and context.")
            status = "DISMISSED_CANDIDATE"
            adjudication = c["disposition"]
        elif c and c["disposition"].startswith("CONFIRMED_"):
            raise ValueError(f"Confirmed candidate missing repair: {bid}")
        else:
            cr = chapter_reviews[bid]
            classification = cr["classification"]
            revised = original
            issue = cr.get("sourceMeaningAtIssue", "")
            reason = cr.get("reason", "No material issue found in source/context comparison.")
            status = "UNCHANGED"
            adjudication = None

        # The proposed repair did not reliably preserve the source's precise
        # spatial relation. Revert and hold for a Toki Pona editorial decision.
        if bid == "jekyll-full-v1:chapter-01:block-0011":
            revised = original
            classification = "BLOCKER"
            issue = "The source locates the courtyard entrance two doors from a corner, on the left while walking east; the proposed repair did not reliably preserve that spatial relation."
            reason = "Reverted the unverified proposed repair to V1 and held this block; do not Text Lock until its location/direction is clear."
            status = "BLOCKER_AFTER_REPAIR_REVIEW"
            adjudication = "MANUAL_QA_ESCALATION"

        # Whole-book entity consistency pass: normalize one established Satan form.
        if bid == "jekyll-full-v1:chapter-02:block-0038":
            before = "jan Setan"
            if before not in revised:
                raise ValueError("Expected Satan spelling not present in chapter 2 block 38")
            revised = revised.replace(before, "jan Satana")
            classification = "STYLE_REVIEW"
            issue = "Recurring entity name Satan had three spellings across the manuscript."
            reason = "Normalized this occurrence to established jan Satana; wording and attributed perception are otherwise unchanged."
            status = "GLOBAL_ENTITY_NORMALIZATION"

        if not source or not original or not revised:
            raise ValueError(f"Empty source/translation for {bid}")
        expected_hash = item["sourceHash"]
        if sha(source) != expected_hash:
            raise ValueError(f"Source hash mismatch: {bid}")
        row = {
            "blockId": bid,
            "ordinal": item["ordinal"],
            "chapter": chapter,
            "chapterTitle": item["chapterTitle"],
            "source": source,
            "sourceSha256": expected_hash,
            "originalTranslation": original,
            "revisedTranslation": revised,
            "classification": classification,
            "sourceMeaningAtIssue": issue,
            "reason": reason,
            "reviewStatus": status,
            "adjudication": adjudication,
        }
        records.append(row)
        chapters.setdefault(chapter, []).append(revised)

    counts = Counter(r["classification"] for r in records)
    assert len(records) == manifest["completedCount"] == 462
    assert len({r["blockId"] for r in records}) == 462
    assert counts == {"SAFE": 306, "STYLE_REVIEW": 29, "SEMANTIC_REPAIR": 124, "BLOCKER": 3}, counts
    assert sum(r["originalTranslation"] != r["revisedTranslation"] for r in records) == 153
    return records, chapters, chapter_titles, counts


def write_artifacts():
    records, chapters, chapter_titles, counts = assemble()
    out = BASE
    title = "# The Strange Case of Dr Jekyll and Mr Hyde\n\n*Toki Pona translation — Latin script*\n\n"
    manuscript = title
    for chapter in sorted(chapters):
        heading = chapter_titles[chapter].title()
        manuscript += f"## {heading}\n\n" + "\n\n".join(chapters[chapter]) + "\n\n"
    (out / "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_V2.md").write_text(manuscript.rstrip() + "\n", encoding="utf-8")

    ledger = {
        "schemaVersion": "1.0",
        "artifact": "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V2",
        "sourceManifest": "JEKYLL_FINAL_462_BLOCK_MANIFEST_V1.json",
        "sourceManuscript": "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_V1.md",
        "reviewMethod": "chapter-level source/context review, candidate adjudication, targeted repair, final local spot audit; post-repair full continuous read incomplete due provider limit",
        "classificationCounts": dict(counts),
        "blocksChanged": 153,
        "blocks": records,
    }
    (out / "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V2.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    process = read_json(BASE / "JEKYLL_FINAL_462_BLOCK_MANIFEST_V1.json")["processNotesExcludedFromManuscript"]
    source_note_block = next(r for r in records if r["blockId"] == "jekyll-full-v1:chapter-08:block-0025")
    assert "NOTES:" not in source_note_block["revisedTranslation"]
    assert source_note_block["source"].startswith("We’ve had nothing else this week back")

    review = f"""# Jekyll Toki Pona — Editorial Review V1

## Result

All 462 source/translation blocks received a source-and-context review. V2 applies targeted edits only; V1 is preserved unchanged. This is an AI-assisted editorial review, not native-speaker certification. The text is **not ready for Text Lock**: three passages remain unresolved, and the post-repair whole-book API read did not complete.

| Classification | Blocks |
|---|---:|
| SAFE (including five dismissed concerns) | {counts['SAFE']} |
| STYLE_REVIEW | {counts['STYLE_REVIEW']} |
| SEMANTIC_REPAIR | {counts['SEMANTIC_REPAIR']} |
| BLOCKER / human decision required | {counts['BLOCKER']} |

Changed blocks: 153. Unchanged blocks: 309. The model returned 153 targeted-repair proposals; 152 were retained after review, one was reverted to V1 after local QA, and one global Satan spelling was normalized.

## Review sequence

1. Compared all chapters against the canonical English source, nearby narrative context, entity registry, and available project lexical/name guidance.
2. Adjudicated the 160 first-pass non-SAFE candidates: 125 semantic repairs confirmed, 28 style changes confirmed, five concerns dismissed, and two left for human choice.
3. Evaluated 153 targeted-repair proposals. Retained 152 after review, reverted one uncertain spatial repair to V1, and applied the separate Satan-name normalization. SAFE and dismissed passages otherwise remain byte-for-byte unchanged.
4. The required post-repair whole-book read was attempted. Its first API request ended incomplete at the output-token limit; a concise retry was rate-limited (HTTP 429). Therefore no successful post-repair continuous-read result is claimed.

## Human decisions still open

1. **Chapter 1, block 11 — street location.** The proposed repair did not reliably preserve “two doors from one corner / left while going east.” V2 reverts to V1 pending a Toki Pona editor.
2. **Chapter 2, block 23 — Hyde/Seek wordplay.** The fixed rendering `jan Hata` preserves the established name but does not reproduce the English hide/seek pun. `jan Alasa` carries “Seek,” while a Toki Pona equivalent that also preserves the proper name has not been established. V2 leaves the passage unchanged. Decide whether to accept partial wordplay loss or authorize a carefully bounded translator’s note/alternative.
3. **Chapter 10, block 112 — “inorganic.”** V1’s `ijo pi lon ala` risks meaning “nonexistent,” not “inorganic.” No approved lexical choice is available in the project materials. V2 leaves it unchanged pending a Toki Pona editorial decision; do not treat this wording as verified.

## Findings not adopted

- A continuous-read suggestion to replace the canonical medicine phrase `telo pi pali sona` was not adopted: it conflicts with the project’s available lexical guidance and relies on an unverified inference that the later powder is necessarily the same referent.
- A suggested date contradiction was not treated as established: a letter dated 10 December can be received on 9 January after a dinner on 8 January. The source dates were preserved.
- The wordplay finding remains a documented limitation, not a silent renaming of Hyde.

## Entity and process notes

- Standardized the remaining Satan rendering to `jan Satana`; the registry’s established character/place spellings otherwise remain intact.
- Guest and Newcomen were checked in context; Guest has stable rendering in reviewed occurrences, and Newcomen has one occurrence (`jan Njukomen`), so no cross-occurrence drift was found.
- The process note attached to `chapter08:block0025` is not narrative text. The source passage is present in V1/V2; the note is excluded from reader-facing prose and retained only in the excluded-note manifest/editorial record.

## Limits

There is no complete approved project lexicon in the artifacts examined; the entity registry does contain limited canonical wording guidance and was used. Mechanical checks establish block coverage, provenance, and unchanged/changed accounting, not literary quality. Open decisions mean the manuscript must remain at editorial review and must not be Text Locked.
"""
    (out / "JEKYLL_TOKI_PONA_EDITORIAL_REVIEW_V1.md").write_text(review, encoding="utf-8")

    qa = f"""# Jekyll Toki Pona — Editorial QA V1

## Required status report

- BLOCKS REVIEWED: **462/462**
- SAFE: **{counts['SAFE']}**
- STYLE_REVIEW: **{counts['STYLE_REVIEW']}**
- SEMANTIC_REPAIR: **{counts['SEMANTIC_REPAIR']}**
- BLOCKER: **{counts['BLOCKER']}**
- BLOCKS CHANGED: **153**
- UNCHANGED BLOCKS: **309**
- FINAL MANUSCRIPT WORD COUNT: **37,885** including title/subtitle/chapter headings; **37,815** translated block words (whitespace-token count)
- ENTITY CONSISTENCY: **PASS** for recorded names/spellings after the Satan normalization; not a general lexicon certification
- JEKYLL-HYDE DISTINCTION: **REVIEW** — identity/spoiler distinction passed the initial continuous read; the Hyde/Seek pun remains an editorial choice
- SEMANTIC FIDELITY: **REVIEW** — targeted repairs applied, but three unresolved blocks remain
- TOKI PONA GRAMMAR/LEXICON: **REVIEW** — no native-speaker certification; “inorganic” remains unresolved
- NARRATIVE CONTINUITY: **REVIEW** — earlier chronology alert was not a source contradiction; post-repair continuous-read API request did not complete (first attempt hit output cap; retry received HTTP 429), so no full post-repair continuity PASS is claimed
- PROCESS NOTE ISSUE: **RESOLVED**
- ENGLISH LEAKAGE: **REVIEW** — automated/mechanical spot checks do not certify all literary language as idiomatic Toki Pona
- TEXT_LOCK_GATE: **HOLD**

## Structural verification

- 462 unique IDs agree with the canonical ordered manifest; source hashes match.
- Every V2 paragraph maps to one source block. Every output ledger row contains original and revised Toki Pona plus issue/reason metadata.
- V1 manuscript was not edited.
- Counts reconcile: 306 SAFE + 29 STYLE_REVIEW + 124 SEMANTIC_REPAIR + 3 BLOCKER = 462.
- The 153 proposals are not 153 retained repairs: 152 were retained; one was reverted, while the independent Satan normalization accounts for one other changed block.
- Manual final QA escalated chapter 1, block 11 to BLOCKER and restored its original V1 translation because the proposed spatial wording was not sufficiently trustworthy.
- Post-repair continuous read: **INCOMPLETE**. One full-book request ended `incomplete/max_output_tokens`; one concise retry was rate-limited (HTTP 429). The source and V2 manuscript were not shortened.
"""
    (out / "JEKYLL_TOKI_PONA_EDITORIAL_QA_V1.md").write_text(qa, encoding="utf-8")

    status = {
        "schemaVersion": "1",
        "status": "INCOMPLETE",
        "reason": "Post-repair whole-book API review did not complete: one request ended incomplete/max_output_tokens; concise retry was rate-limited with HTTP 429.",
        "requestStore": False,
        "humanPermission": "Explicitly granted in chat for source, translation, and editorial metadata review.",
        "textLockGate": "HOLD",
    }
    (REVIEW / "continuous-read-v2-status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": dict(counts), "changed": 153, "unchanged": 309, "manuscriptWords": len(manuscript.split()), "postRepairContinuousRead": "INCOMPLETE"}, ensure_ascii=False))


if __name__ == "__main__":
    write_artifacts()
