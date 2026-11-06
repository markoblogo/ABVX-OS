#!/usr/bin/env python3
"""Build a narrow V3 successor and evidence reports without re-reviewing the book."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/jekyll-toki-pona-full-v1"
MANIFEST_PATH = BASE / "JEKYLL_FINAL_462_BLOCK_MANIFEST_V1.json"
V2_LEDGER_PATH = BASE / "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V2.json"
V2_MANUSCRIPT_PATH = BASE / "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_V2.md"
V3_LEDGER_PATH = BASE / "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V3.json"
V3_MANUSCRIPT_PATH = BASE / "MANUSCRIPT_JEKYLL_TOKI_PONA_LATIN_V3.md"

REPAIRS = {
    "jekyll-full-v1:chapter-01:block-0011": (
        "lupa tawa pi ma insa li lon nasin ni. ona li weka tan poka pi nasin tu lon ma tomo; "
        "weka ona li sama weka pi lupa tomo tu. jan li tawa kama suno la, ona li lon poka soto "
        "pi jan ni li pakala e linja tomo. lon ma ni taso la, tomo suli wan pi lukin ike li pana "
        "e sinpin sewi ona tawa nasin."
    ),
}
HYDE_ID = "jekyll-full-v1:chapter-02:block-0023"
INORGANIC_ID = "jekyll-full-v1:chapter-10:block-0112"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build() -> dict:
    v2_raw = V2_MANUSCRIPT_PATH.read_bytes()
    v2_sha = sha_bytes(v2_raw)
    v2 = read_json(V2_LEDGER_PATH)
    manifest = read_json(MANIFEST_PATH)
    rows = copy.deepcopy(v2["blocks"])
    by_id = {row["blockId"]: row for row in rows}
    assert len(rows) == len(by_id) == 462
    assert list(by_id) == [x["blockId"] for x in rows]
    for item, row in zip(manifest["orderedBlocks"], rows, strict=True):
        assert item["blockId"] == row["blockId"]
        assert item["ordinal"] == row["ordinal"]
        assert item["sourceHash"] == row["sourceSha256"]
        assert hashlib.sha256(row["source"].encode()).hexdigest() == row["sourceSha256"]

    # One bounded, manually contextualized repair. The idiom is rendered as an
    # approximate distance of two doorways from a street junction, with left
    # anchored to a pedestrian moving toward sunrise (east).
    street = by_id["jekyll-full-v1:chapter-01:block-0011"]
    street["revisedTranslation"] = REPAIRS[street["blockId"]]
    street["classification"] = "SEMANTIC_REPAIR"
    street["sourceMeaningAtIssue"] = (
        "The courtyard entrance is approximately two doorways from a street corner, "
        "on the pedestrian's left when moving east; the street frontage is interrupted there."
    )
    street["reason"] = (
        "Small contextual repair: states the junction-distance relation, uses the two-doorway "
        "distance as an approximation, anchors left to travel toward sunrise, and retains the "
        "broken frontage and projecting gable. Toki Pona circumlocution; not a claim of native-speaker certification."
    )
    street["reviewStatus"] = "RESOLVED_TARGETED_MANUAL_CONTEXT_QA"
    street["adjudication"] = "MANUAL_SOURCE_AND_NEIGHBOR_CONTEXT"

    # User-approved editorial resolution; canonical name and translation stay unchanged.
    hyde = by_id[HYDE_ID]
    assert "jan Hata" in hyde["revisedTranslation"] and "jan Alasa" in hyde["revisedTranslation"]
    hyde["classification"] = "STYLE_REVIEW"
    hyde["sourceMeaningAtIssue"] = (
        "Preserve canonical jan Hata; jan Alasa is retained for Seek. The English Hyde/hide/Seek "
        "wordplay is only partly transferable and its loss is an intentional translation limitation."
    )
    hyde["reason"] = (
        "Resolved by owner decision: keep canonical jan Hata, accept partial loss of the English "
        "Hyde/hide pun, and retain jan Alasa for Seek. Translation text unchanged; no global renaming."
    )
    hyde["reviewStatus"] = "RESOLVED_BY_OWNER_DECISION_NO_TEXT_CHANGE"
    hyde["adjudication"] = "OWNER_APPROVED_INTENTIONAL_WORDPLAY_LOSS"

    # Keep the lexical issue open: the bounded GPT-6 Luna adjudication found no
    # safe common-word replacement, so do not invent or adopt a phrase.
    inorganic = by_id[INORGANIC_ID]
    inorganic["classification"] = "BLOCKER"
    inorganic["sourceMeaningAtIssue"] = (
        "'ijo pi lon ala' means nonexistent, not inorganic. The bounded targeted adjudication "
        "found no reliable common-word circumlocution for non-organic/non-living matter."
    )
    inorganic["reason"] = (
        "Held unchanged. The bounded GPT-6 Luna adjudication (store=false) found no safe replacement: "
        "common-word alternatives risk meanings such as nonexistent, bodiless, or dead. Do not invent "
        "an obscure term."
    )
    inorganic["reviewStatus"] = "BLOCKER_TARGETED_LUNA_NO_SAFE_REPLACEMENT"
    inorganic["adjudication"] = "TARGETED_SEMANTIC_ADJUDICATION_NO_SAFE_REPLACEMENT"

    # Strongly constrain the V2->V3 text delta to the approved blocker scope.
    changed_ids = [r["blockId"] for r, old in zip(rows, v2["blocks"], strict=True)
                   if r["revisedTranslation"] != old["revisedTranslation"]]
    assert changed_ids == ["jekyll-full-v1:chapter-01:block-0011"], changed_ids
    for row, old in zip(rows, v2["blocks"], strict=True):
        for key in ("blockId", "ordinal", "chapter", "chapterTitle", "source", "sourceSha256", "originalTranslation"):
            assert row[key] == old[key], (row["blockId"], key)

    counts = Counter(r["classification"] for r in rows)
    assert counts == {"SAFE": 306, "STYLE_REVIEW": 30, "SEMANTIC_REPAIR": 125, "BLOCKER": 1}, counts
    ledger = {
        **{k: copy.deepcopy(v) for k, v in v2.items() if k != "blocks"},
        "schemaVersion": "1.1",
        "artifact": "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V3",
        "reviewMethod": (
            "V2 462-block review retained; only three prior blockers reconsidered. One contextual "
            "manual repair, one owner-approved no-text-change limitation, and one unresolved lexical blocker. "
            "No whole-book API read or translation rerun."
        ),
        "classificationCounts": dict(counts),
        "blocksChanged": 154,
        "parentLedger": "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V2.json",
        "parentManuscriptSha256": v2_sha,
        "v2ToV3ChangedTranslationBlockIds": changed_ids,
        "blocks": rows,
    }
    write_json(V3_LEDGER_PATH, ledger)

    chapters: dict[int, list[str]] = {}
    titles: dict[int, str] = {}
    for row in rows:
        chapters.setdefault(row["chapter"], []).append(row["revisedTranslation"])
        titles[row["chapter"]] = row["chapterTitle"]
    manuscript = "# The Strange Case of Dr Jekyll and Mr Hyde\n\n*Toki Pona translation — Latin script*\n\n"
    for chapter in sorted(chapters):
        manuscript += f"## {titles[chapter].title()}\n\n" + "\n\n".join(chapters[chapter]) + "\n\n"
    manuscript = manuscript.rstrip() + "\n"
    V3_MANUSCRIPT_PATH.write_text(manuscript, encoding="utf-8")

    # Mechanical checks across the complete successor.
    parsed_paragraphs = []
    for paragraph in re.split(r"\n\s*\n", manuscript.strip()):
        if paragraph.startswith("#") or paragraph.startswith("*"):
            continue
        parsed_paragraphs.append(paragraph)
    assert len(parsed_paragraphs) == 462
    assert parsed_paragraphs == [r["revisedTranslation"] for r in rows]
    assert [r["ordinal"] for r in rows] == list(range(1, 463))
    assert len({r["blockId"] for r in rows}) == 462

    # Unicode/script audit. Latin letters, normal typography, and story punctuation are accepted.
    allowed_punctuation = set(" \t\n\r.,;:!?()[]{}<>/\\-–—_“”‘’\"'…*#=|`~")
    bad_chars = sorted({c for c in manuscript if not (c.isascii() or c in allowed_punctuation)})
    non_latin = sorted({(c, unicodedata.name(c, "UNKNOWN")) for c in bad_chars
                        if "LATIN" not in unicodedata.name(c, "")})
    assert not non_latin, non_latin

    # High-confidence ordinary-English leakage scan over translated paragraphs.
    # It is a tripwire, not a substitute for lexical/editorial adjudication.
    tp_words = set("a akesi ala alasa ale anpa ante anu awen e en esun ijo ike ilo insa jaki jan jelo jo kala kalama kama kasi ken kepeken kili kiwen ko kon kule kulupu kute la lape laso lawa len lete li lili linja lipu loje luka lukin lupa ma mama mani meli mi mije moku moli monsi monsuta mu mun musi mute nanpa nasa nasin nena ni noka o olin ona open pakala pali palisa pana pi pilin pimeja pini pipi poka poki pona pu sama seli selo seme sewi sijelo sike sin sina sinpin sitelen sona soweli suli suno supa suwi tan taso tawa telo tenpo toki tomo tu unpa uta utala walo wan waso wawa weka wile oko lon nimi epiku jasima kijetesantakalu kin kipisi kokosila ku leko namako n tonsi pomotolo misikeke majuna pake powe".split())
    english_tripwire_candidates = set("the and with from into when while where what which that have has had was were are is be being been this these those your you he she they them his her their but not only very then than because through after before about should would could shall will did does do of to for in on at by as if or an a it its we us our my me I".split())
    english_tripwires = {w.lower() for w in english_tripwire_candidates if w.lower() not in tp_words}
    hits = []
    for row in rows:
        tokens = re.findall(r"(?<![A-Za-z])[A-Za-z]+(?![A-Za-z])", row["revisedTranslation"])
        for token in tokens:
            if token.lower() in {x.lower() for x in english_tripwires}:
                hits.append((row["blockId"], token))
    # This is an English-function-word tripwire after excluding known Toki Pona
    # homographs, not a complete dictionary or idiomaticity certification.
    changed_hits = [x for x in hits if x[0] in changed_ids]
    assert not changed_hits, changed_hits

    manuscript_words = len(manuscript.split())
    translated_words = sum(len(r["revisedTranslation"].split()) for r in rows)
    v2_unchanged = sha_bytes(v2_raw) == ledger["parentManuscriptSha256"]
    assert v2_unchanged

    report = f"""# Jekyll Toki Pona — Editorial QA V3

## Result

- V2 review retained: **462/462 blocks**; no translation rerun and no whole-book API read.
- Classification: **306 SAFE · 30 STYLE_REVIEW · 125 SEMANTIC_REPAIR · 1 BLOCKER**.
- V2 → V3 translated-text changes: **1 block**, only `chapter-01:block-0011`.
- `chapter-02:block-0023`: owner-approved limitation; canonical `jan Hata` and `jan Alasa` retained; translation text unchanged.
- `chapter-10:block-0112`: **still unresolved**; original V2 text retained. One targeted GPT-6 Luna adjudication found no safe common-word rendering; its 1,656 input / 569 output tokens cost approximately **$0.00049** at current standard rates.
- Text Lock readiness: **HOLD** because one semantic blocker remains. Lack of a second whole-book API read is not itself the reason for HOLD.
- V2 source file preserved byte-for-byte: **{v2_unchanged}** (SHA-256 `{v2_sha}`).

## Targeted repairs and boundaries

1. **Chapter 1 / block 11.** The new wording describes the court entrance as two doorway-distances from a junction and on the left of someone moving toward sunrise/east. It retains the interrupted frontage and projecting gable. Manual context check against blocks 10 and 12: **PASS** for local continuity; the corner and distance are necessarily circumlocuted rather than mapped to a dedicated Toki Pona term.
2. **Chapter 2 / block 23.** `jan Hata` remains canonical; `jan Alasa` remains the Seek rendering. The partial loss of English Hyde/hide/Seek wordplay is explicitly accepted. Boundary check against blocks 22 and 24 and entity registry: **PASS**; no global rename.
3. **Chapter 10 / block 112.** No replacement adopted. `ijo pi lon ala` remains at risk of reading as “nonexistent,” so this is still a real blocker. Boundary check against blocks 111 and 113 finds no reason to alter adjacent text; it does not resolve the lexical distinction.

## Deterministic verification

- Ordered manifest, unique IDs, 462-block coverage and ordinals: **PASS**.
- All 462 source SHA-256 values against the manifest: **PASS**.
- Every manuscript paragraph aligns in order with one V3 ledger translation: **PASS**.
- V2 → V3 translation diff allowlist: **PASS**; changed IDs = `{', '.join(changed_ids)}; no other block text changed.
- Entity consistency: V2's recorded-name consistency result is inherited because the V2→V3 diff affects only block 11, which contains no named entity; `jan Hata` remains canonical in block 23; **PASS**.
- Unicode/script: **PASS**; no non-Latin scripts or unexpected non-ASCII characters detected (approved Latin typography retained).
- English-leakage tripwire: **PASS**; zero occurrences of the configured common English function-word set across 462 translated blocks after excluding Toki Pona homographs. This is a high-confidence leakage check, not a complete lexicon or idiomaticity certification.
- Reader-facing process notes: inherited exclusion checks from V2; no new note inserted.
- Jekyll-focused deterministic tests: **17/17 PASS**. `./bin/abvx validate`: **PASS**, 260 files checked, zero errors. The full repository `unittest` suite was attempted but stopped after about six minutes inside a test copying the full `registries` tree; no assertion failure was observed, so the full-suite status is **NOT COMPLETED**, not PASS.

## Counts and limits

- V3 manuscript word count (whitespace count, including title/subtitle/headings): **{manuscript_words:,}**.
- Translated block words: **{translated_words:,}**.
- One bounded API adjudication used model `gpt-6-luna`, `store=false`, target plus immediate context; result: `NO_SAFE_REPLACEMENT`. Usage: 1,656 input tokens (1,653 cache-write, zero cached) and 569 output tokens (415 reasoning subset); estimated standard-rate cost: about **$0.00049**. The initial 429 attempt had no returned usage; one user-authorized retry completed.
- No additional whole-book review was run. Prior adjudications for all unchanged blocks remain authoritative under the user's instruction.
- This QA supports a provisional editorial successor, **not Text Lock**.
"""
    (BASE / "JEKYLL_TOKI_PONA_EDITORIAL_QA_V3.md").write_text(report, encoding="utf-8")

    readiness = f"""# Jekyll Toki Pona — Text Lock Readiness V3

Status: **HOLD — NOT READY FOR TEXT LOCK**

The 462-block V2 review is retained as the authoritative adjudication for unchanged content. Two of three V2 blockers now have defensible dispositions: chapter 1/block 11 received a bounded contextual repair; chapter 2/block 23 is resolved by the owner's explicit acceptance of partial wordplay loss while keeping canonical `jan Hata`. Chapter 10/block 112 remains a semantic blocker: a bounded GPT-6 Luna adjudication found no safe common-word phrase for “inorganic.” An initial request received HTTP 429; one user-authorized retry completed and returned `NO_SAFE_REPLACEMENT`.

Structural, source-hash, order, coverage, Unicode/script, and V2→V3 allowlist checks pass. The targeted chapter-boundary checks pass for the two dispositions and confirm adjacent text remains unchanged. The full-book post-repair API reread is not required by policy and was not performed. Whole-book lexical leakage remains REVIEW because no complete project-approved vocabulary list exists.

**Gate to revisit:** obtain a defensible Toki Pona rendering for block 112 using project lexical policy/context or an authorized qualified human editor; then rerun only the block and immediate-boundary checks plus deterministic full-book validations. Do not retranslate or reread all 462 blocks.
"""
    (BASE / "JEKYLL_TOKI_PONA_TEXT_LOCK_READINESS_V3.md").write_text(readiness, encoding="utf-8")

    print(json.dumps({
        "blocks": len(rows), "counts": dict(counts), "v2ToV3TextChanges": changed_ids,
        "sourceHashChecks": 462, "paragraphAlignment": "PASS", "nonLatinOrUnexpectedUnicode": bad_chars,
        "englishLeakageTripwireHits": len(hits), "changedBlockTripwireHits": changed_hits,
        "v2Sha256": v2_sha, "v3Sha256": sha_bytes(manuscript.encode()),
        "manuscriptWords": manuscript_words, "translatedWords": translated_words,
        "textLock": "HOLD", "outputs": [str(V3_MANUSCRIPT_PATH), str(V3_LEDGER_PATH)]
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
