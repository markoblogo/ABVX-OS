#!/usr/bin/env python3
"""Apply the single owner-approved lexical disposition and gate Text Lock."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/jekyll-toki-pona-full-v1"
V3_MANUSCRIPT = BASE / "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_V3.md"
V3_LEDGER = BASE / "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V3.json"
V4_MANUSCRIPT = BASE / "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_V4.md"
V4_LEDGER = BASE / "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V4.json"
TEXT_LOCK = BASE / "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_TEXT_LOCK_V1.md"
QA_JSON = BASE / "JEKYLL_TOKI_PONA_V4_DETERMINISTIC_QA.json"
QA_REPORT = BASE / "JEKYLL_TOKI_PONA_EDITORIAL_QA_V4.md"
LOCK_REPORT = BASE / "JEKYLL_TOKI_PONA_TEXT_LOCK_REPORT_V1.md"
MANIFEST = BASE / "JEKYLL_FINAL_462_BLOCK_MANIFEST_V1.json"
TARGET_ID = "jekyll-full-v1:chapter-10:block-0112"
OLD_PHRASE = "ijo pi lon ala"
NEW_PHRASE = "ijo pi kon ala"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jload(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tp_english_tripwire(rows):
    tp_words = set("a akesi ala alasa ale anpa ante anu awen e en esun ijo ike ilo insa jaki jan jelo jo kala kalama kama kasi ken kepeken kili kiwen ko kon kule kulupu kute la lape laso lawa len lete li lili linja lipu loje luka lukin lupa ma mama mani meli mi mije moku moli monsi monsuta mu mun musi mute nanpa nasa nasin nena ni noka o olin ona open pakala pali palisa pana pi pilin pimeja pini pipi poka poki pona pu sama seli selo seme sewi sijelo sike sin sina sinpin sitelen sona soweli suli suno supa suwi tan taso tawa telo tenpo toki tomo tu unpa uta utala walo wan waso wawa weka wile oko lon nimi epiku jasima kijetesantakalu kin kipisi kokosila ku leko namako n tonsi pomotolo misikeke majuna pake powe".split())
    candidates = {w.lower() for w in "the and with from into when while where what which that have has had was were are is be being been this these those your you he she they them his her their but not only very then than because through after before about should would could shall will did does do of to for in on at by as if or an a it its we us our my me I".split()}
    tripwires = candidates - tp_words
    hits = []
    for row in rows:
        for token in re.findall(r"(?<![A-Za-z])[A-Za-z]+(?![A-Za-z])", row["revisedTranslation"]):
            if token.lower() in tripwires:
                hits.append({"blockId": row["blockId"], "token": token})
    return hits


def prepare_v4():
    v3_bytes = V3_MANUSCRIPT.read_bytes()
    v3_sha = sha(v3_bytes)
    v3_text = v3_bytes.decode("utf-8")
    v3_ledger = jload(V3_LEDGER)
    ledger = copy.deepcopy(v3_ledger)
    rows = ledger["blocks"]
    assert len(rows) == 462
    target = next(r for r in rows if r["blockId"] == TARGET_ID)
    assert target["classification"] == "BLOCKER"
    assert target["revisedTranslation"].count(OLD_PHRASE) == 1
    revised = target["revisedTranslation"].replace(OLD_PHRASE, NEW_PHRASE, 1)
    # Exact local phrase substitution only; all other text in this block stays fixed.
    target["priorAdjudication"] = copy.deepcopy(target.get("adjudication"))
    target["priorClassification"] = "BLOCKER"
    target["revisedTranslation"] = revised
    target["classification"] = "SEMANTIC_REPAIR"
    target["sourceMeaningAtIssue"] = (
        "Owner-approved contextual rendering of inorganic as non-living matter / matter without life. "
        "The modern technical organic/inorganic chemistry distinction is not preserved exactly."
    )
    target["reason"] = (
        "Resolved by explicit owner lexical decision: ijo pi kon ala. This is a contextual Toki Pona "
        "semantic circumlocution, not a technical one-to-one chemistry translation. It supersedes the "
        "previous HOLD because of owner approval, not because GPT-6 Luna endorsed the phrase."
    )
    target["reviewStatus"] = "RESOLVED_OWNER_LEXICAL_DECISION"
    target["adjudication"] = "OWNER_APPROVED_LEXICAL_DECISION"
    target["approvedPhrase"] = NEW_PHRASE
    target["intendedReading"] = "non-living matter / matter without life"
    target["technicalLimitation"] = (
        "The modern technical organic/inorganic chemistry distinction is not preserved exactly; "
        "the translation preserves the contextually relevant distinction of non-living matter."
    )
    target["ownerApproval"] = "Explicit approval in the attached owner instruction."
    target["previousLunaResult"] = "NO_SAFE_REPLACEMENT"
    target["holdOverrideReason"] = "Explicit project lexical decision, not model confidence."

    rows_by_id = {r["blockId"]: r for r in rows}
    expected_v3_text = rows_by_id[TARGET_ID]["revisedTranslation"].replace(NEW_PHRASE, OLD_PHRASE, 1)
    assert v3_text.count(expected_v3_text) == 1
    v4_text = v3_text.replace(expected_v3_text, revised, 1)
    assert v4_text.count(NEW_PHRASE) >= 1
    assert sha(V3_MANUSCRIPT.read_bytes()) == v3_sha
    V4_MANUSCRIPT.write_text(v4_text, encoding="utf-8")

    manifest = jload(MANIFEST)
    manifest_rows = manifest["orderedBlocks"]
    assert len(manifest_rows) == len(rows) == 462
    assert len(rows_by_id) == 462
    assert [r["blockId"] for r in rows] == [m["blockId"] for m in manifest_rows]
    assert [r["ordinal"] for r in rows] == list(range(1, 463))
    source_hash_failures = []
    for item, row in zip(manifest_rows, rows, strict=True):
        source_sha = hashlib.sha256(row["source"].encode("utf-8")).hexdigest()
        if row["sourceSha256"] != item["sourceHash"] or source_sha != item["sourceHash"]:
            source_hash_failures.append(row["blockId"])
        assert row["source"] and row["revisedTranslation"]
    assert not source_hash_failures

    paragraphs = [p for p in re.split(r"\n\s*\n", v4_text.strip()) if p and not p.startswith("#") and not p.startswith("*")]
    assert len(paragraphs) == 462
    assert paragraphs == [r["revisedTranslation"] for r in rows]
    text_diff_ids = [r["blockId"] for r, old in zip(rows, v3_ledger["blocks"], strict=True)
                     if r["revisedTranslation"] != old["revisedTranslation"]]
    assert text_diff_ids == [TARGET_ID], text_diff_ids
    assert rows_by_id[TARGET_ID]["sourceSha256"] == next(m["sourceHash"] for m in manifest_rows if m["blockId"] == TARGET_ID)

    counts = Counter(r["classification"] for r in rows)
    assert counts == {"SAFE": 306, "STYLE_REVIEW": 30, "SEMANTIC_REPAIR": 126}, counts
    ledger.update({
        "schemaVersion": "1.2",
        "artifact": "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V4",
        "parentLedger": "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V3.json",
        "parentManuscript": V3_MANUSCRIPT.name,
        "parentManuscriptSha256": v3_sha,
        "v3ToV4ChangedTranslationBlockIds": text_diff_ids,
        "classificationCounts": dict(counts),
        "blocksChanged": 155,
    })
    write_json(V4_LEDGER, ledger)

    # Confirm the only touched passage and its immediate narrative boundary.
    near = [rows_by_id[f"jekyll-full-v1:chapter-10:block-{n:04d}"] for n in (111, 112, 113)]
    assert near[0]["ordinal"] == 449 and near[2]["ordinal"] == 451
    assert "jan Hata" in near[0]["revisedTranslation"] and "jan Hata" in near[1]["revisedTranslation"]
    assert near[0]["revisedTranslation"] == next(r["revisedTranslation"] for r in v3_ledger["blocks"] if r["blockId"] == near[0]["blockId"])
    assert near[2]["revisedTranslation"] == next(r["revisedTranslation"] for r in v3_ledger["blocks"] if r["blockId"] == near[2]["blockId"])
    assert "ona li pilin e ni:" in near[1]["revisedTranslation"]
    assert "ijo pi kon ala" in near[1]["revisedTranslation"]
    assert "ijan pi kon ala" not in near[1]["revisedTranslation"]
    assert near[2]["source"].startswith("This was the shocking thing")

    # Script audit: same accepted Latin-script set as V3 QA; target change is ASCII.
    punctuation = set(" \t\n\r.,;:!?()[]{}<>/\\-–—_“”‘’\"'…*#=|`~")
    unapproved_unicode = sorted({(c, unicodedata.name(c, "UNKNOWN")) for c in v4_text
                                 if not (c.isascii() or c in punctuation)})
    non_latin = [(c, name) for c, name in unapproved_unicode if "LATIN" not in name]
    assert not unapproved_unicode
    leakage_hits = tp_english_tripwire(rows)
    assert not leakage_hits, leakage_hits[:10]

    note_records = manifest.get("processNotesExcludedFromManuscript", [])
    note_exclusions = []
    for note in note_records:
        row = rows_by_id[note["blockId"]]
        assert "NOTES:" not in row["revisedTranslation"]
        assert note["note"] not in v4_text
        note_exclusions.append(note["blockId"])

    v4_bytes = V4_MANUSCRIPT.read_bytes()
    result = {
        "schemaVersion": "1",
        "status": "DETERMINISTIC_QA_PASS",
        "v3Sha256": v3_sha,
        "v4Sha256": sha(v4_bytes),
        "changedTranslationBlockIds": text_diff_ids,
        "blockIds": 462,
        "uniqueBlockIds": 462,
        "canonicalOrder": True,
        "sourceHashesValid": 462,
        "emptyBlocks": 0,
        "paragraphAlignment": True,
        "classificationCounts": dict(counts),
        "semanticBlockers": sum(1 for r in rows if r["classification"] == "BLOCKER"),
        "entityConsistency": "PASS_BY_INHERITANCE_AND_DIFF_PROOF; no entity-bearing content changed",
        "approvedUnicodeScript": "PASS",
        "nonLatinCharacters": non_latin,
        "englishLeakageTripwireHits": len(leakage_hits),
        "processNotesExcluded": note_exclusions,
        "boundaryBlocks": [r["blockId"] for r in near],
        "boundaryContinuity": "PASS",
        "wordCount": len(v4_text.split()),
        "v4Path": str(V4_MANUSCRIPT),
        "ledgerPath": str(V4_LEDGER),
    }
    write_json(QA_JSON, result)
    return result


def finalize_lock(result):
    focused = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_jekyll_*.py", "-q"],
        cwd=ROOT, env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True, text=True,
    )
    try:
        focused_summary = focused.stdout + focused.stderr
        match = re.search(r"Ran (\d+) tests? in", focused_summary)
        focused_count = int(match.group(1)) if match else 0
    except Exception:
        focused_count = 0
        focused_summary = focused.stdout + focused.stderr
    validate = subprocess.run(
        ["./bin/abvx", "validate"], cwd=ROOT, capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
    )
    try:
        validate_obj = json.loads(validate.stdout)
        validate_pass = validate.returncode == 0 and validate_obj.get("status") == "PASS"
        validated_count = len(validate_obj.get("checked", []))
    except Exception:
        validate_pass = False
        validated_count = 0
    assert focused.returncode == 0 and focused_count > 0, focused_summary[-2500:]
    assert validate_pass, (validate.returncode, validate.stderr[-1000:], validate.stdout[-1000:])
    assert result["status"] == "DETERMINISTIC_QA_PASS"
    assert result["changedTranslationBlockIds"] == [TARGET_ID]
    assert result["semanticBlockers"] == 0
    assert result["boundaryContinuity"] == "PASS"

    v4_bytes = V4_MANUSCRIPT.read_bytes()
    v4_sha = sha(v4_bytes)
    TEXT_LOCK.write_bytes(v4_bytes)
    lock_sha = sha(TEXT_LOCK.read_bytes())
    assert v4_sha == lock_sha

    def mark(label, status):
        return f"- {label}: **{status}**"
    report = f"""# Jekyll Toki Pona — Editorial QA V4 / Text Lock Gate

## Final status

- BLOCK 112: **RESOLVED** by owner lexical decision.
- Approved rendering: **`{NEW_PHRASE}`** — contextual “non-living matter / matter without life”; not a technical one-to-one chemistry translation.
- Semantic blockers remaining: **0**.
- Text Lock: **PASS**.
- API calls this run: **0**; API cost this run: **$0**.

## Verification

{mark('V3 → V4 diff scope', 'PASS — only chapter 10/block 112')}
{mark('Boundary QA, blocks 111–113', 'PASS — continuity/referent preserved; adjacent blocks unchanged')}
{mark('462-block integrity / unique IDs / order / coverage', 'PASS')}
{mark('Source hashes', 'PASS — all 462 match canonical manifest')}
{mark('Entity consistency', 'PASS — inherited V3 result; diff introduces no entity change')}
{mark('Approved Unicode/script', 'PASS — no unapproved or non-Latin characters')}
{mark('English leakage tripwire', 'PASS — zero configured common-English hits')}
{mark('Process-note exclusion', 'PASS — excluded process note remains outside reader-facing manuscript')}
{mark('Jekyll-focused tests', f'PASS — {focused_count} tests')}
{mark('ABVX validator', f'PASS — {validated_count} files checked')}

The earlier GPT-6 Luna adjudication returned `NO_SAFE_REPLACEMENT`. V4 does not rewrite that history: the new phrase is used solely because the owner explicitly approved it as a contextual project convention and accepted the stated technical limitation.

## Text Lock identity

- V4 SHA-256: `{v4_sha}`
- Text Lock SHA-256: `{lock_sha}`
- Byte-for-byte identical: **YES**

No Kindle, EPUB, KPF, paperback PDF, sitelen pona, illustration, cover, metadata, or KDP listing production was started.

Next gate: **LATIN TOKI PONA PRODUCTION PLANNING**. Not started.
"""
    QA_REPORT.write_text(report, encoding="utf-8")
    LOCK_REPORT.write_text(report, encoding="utf-8")
    result.update({
        "focusedJekyllTests": {"status": "PASS", "count": focused_count},
        "abvxValidate": {"status": "PASS", "checked": validated_count},
        "textLockSha256": lock_sha,
        "textLockByteIdenticalToV4": True,
        "textLock": "PASS",
    })
    write_json(QA_JSON, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize-text-lock", action="store_true")
    args = parser.parse_args()
    result = prepare_v4()
    if args.finalize_text_lock:
        result = finalize_lock(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
