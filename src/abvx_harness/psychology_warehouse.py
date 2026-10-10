from __future__ import annotations

import difflib
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .harness import ValidationError


SOURCE = Path("/Users/antonbiletskiy-volokh/Downloads/warehouse/Phy-notes.txt")
WAREHOUSE = Path("psychology-warehouse")
TAXONOMY_VERSION = "psychology-warehouse-taxonomy-v1-proposed"
TOPICS: dict[str, tuple[str, ...]] = {
    "TRAUMA": ("травм", "травмат", "травматич", "trauma", "traumatic"),
    "RELATIONSHIPS": ("отношен", "партнер", "партнёр", "близост", "relationship", "partner"),
    "ADDICTION_AND_DEPENDENCE": ("зависим", "аддикц", "addiction", "dependen"),
    "THERAPY_AND_PSYCHOTHERAPY": ("терапи", "психотерап", "терапевт", "psychotherap", "therapy", "therapist"),
    "ADAPTATION_AND_COPING": ("адаптац", "копинг", "справля", "адаптир", "coping", "adaptation"),
    "VIOLENCE_AND_ABUSE": ("насили", "насиль", "абьюз", "оскорблен", "abuse", "violence"),
    "ANXIETY_AND_FEAR": ("тревог", "страх", "беспокой", "паник", "anxiety", "fear", "panic"),
    "GRIEF_AND_LOSS": ("гореван", "утрат", "скорб", "смерт", "потер", "grief", "loss", "death"),
    "SELF_AND_IDENTITY": ("самооцен", "самоотнош", "идентич", "личност", "стыд", "вина", "self-esteem", "identity", "shame", "guilt"),
    "FAMILY_AND_CHILDHOOD": ("семь", "родител", "детств", "ребен", "ребён", "family", "parent", "childhood"),
    "EMOTIONS_AND_MENTAL_HEALTH": ("эмоц", "депресс", "подавлен", "настроен", "психическ", "emotion", "depression", "mental health"),
    "BOUNDARIES_AND_AGENCY": ("границ", "соглас", "выбор", "агентност", "boundary", "consent", "agency"),
    "NARCISSISM_AND_PERSONALITY": ("нарцисс", "расстройств личности", "narciss", "personality disorder"),
}

ASSET_CUES = {
    "QUOTE_OR_EXCERPT": ("цитат", "quote from", "excerpt from", "«", "“"),
    "QUESTION": ("почему", "как ли", "что если", "?"),
    "EXERCISE": ("упражнен", "попробуйте", "практика:", "exercise", "try this"),
    "PRACTICAL_ADVICE": ("нужно", "следует", "стоит", "попробуйте", "важно помнить", "should", "try to"),
    "ANECDOTE_OR_SITUATION": ("случай", "история", "клиент", "пациент", "на сессии", "case", "client"),
    "MODEL_OR_FRAMEWORK": ("модель", "схема", "этап", "компонент", "framework", "model"),
    "THERAPEUTIC_MECHANISM": ("механизм", "процесс", "приводит к", "потому что", "mechanism", "leads to"),
    "METAPHOR": ("как будто", "словно", "метафор", "подобно", "as if", "metaphor"),
    "APHORISM": ("всегда", "никогда", "человек", "жизнь"),
}

PROVENANCE_CUES = {
    "source": (r"\b(?:из книги|в книге|по словам|согласно|лекци[яи]|супервизи[яи]|автор пишет|написал[аи]?|по мнению|according to|from the book|lecture|supervision|quote from)\b",),
    "personal": (r"\b(?:я думаю|мне кажется|я заметил[аи]?|мой опыт|в моей практике|на сессии|мой клиент|my experience|in my practice)\b",),
    "quote": (r"(?:[«“][^»”\n]{8,}[»”]|\"[^\"\n]{12,}\")",),
}
OWN_CUES = ("моя формулировка", "мое наблюдение", "я сформулировал", "я придумал", "my formulation", "my observation")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _norm(text: str) -> str:
    text = text.casefold().replace("ё", "е")
    return " ".join(re.findall(r"[\w'-]+", text, flags=re.UNICODE))


def _fingerprint(text: str) -> str:
    return hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()


def _words(text: str) -> list[str]:
    return re.findall(r"[\w'-]+", _norm(text), flags=re.UNICODE)


def _read_blocks(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8-sig")
    blocks: list[dict[str, Any]] = []
    lines = text.splitlines(keepends=True)
    pending: list[str] = []
    start = 1
    for number, line in enumerate(lines, 1):
        if line.rstrip("\r\n").strip() == "***":
            raw = "".join(pending)
            if raw.strip():
                blocks.append({"text": raw, "line_start": start, "line_end": number - 1})
            pending = []
            start = number + 1
        else:
            pending.append(line)
    raw = "".join(pending)
    if raw.strip():
        blocks.append({"text": raw, "line_start": start, "line_end": len(lines)})
    return blocks


def _classify(text: str) -> dict[str, Any]:
    low = text.casefold().replace("ё", "е")
    words = set(_words(low))
    topic_tags = []
    for label, cues in TOPICS.items():
        hits = sorted({w for w in words if any(w.startswith(cue) for cue in cues if len(cue) >= 4)})
        if hits:
            confidence = 0.84 if len(hits) > 1 else 0.72
            topic_tags.append({"label": label, "confidence": confidence, "evidence": hits[:6], "method": "local_lexical_rule"})
    if not topic_tags:
        topic_tags = []

    asset_hits = []
    for label, cues in ASSET_CUES.items():
        if any(cue in low for cue in cues):
            asset_hits.append(label)
    asset_type = asset_hits[0] if asset_hits else ("OBSERVATION" if len(words) > 8 else "FRAGMENT")

    source_cue = any(re.search(pattern, low) for pattern in PROVENANCE_CUES["source"])
    personal_cue = any(re.search(pattern, low) for pattern in PROVENANCE_CUES["personal"])
    quote_cue = any(re.search(pattern, text) for pattern in PROVENANCE_CUES["quote"])
    own_cue = any(cue in low for cue in OWN_CUES)
    if source_cue and personal_cue and not quote_cue:
        provenance = "MIXED_OR_UNCLEAR"
    elif source_cue and quote_cue:
        provenance = "LIKELY_QUOTE_OR_EXCERPT"
    elif source_cue:
        provenance = "ATTRIBUTED_SOURCE"
    elif own_cue:
        provenance = "LIKELY_OWN"
    elif personal_cue:
        provenance = "PERSONAL_OR_PRACTICE_NOTE"
    else:
        provenance = "UNKNOWN"
    attribution = None
    if source_cue:
        match = re.search(r"(?:из книги|в книге|по словам|согласно|лекци[яи]|супервизи[яи]|автор пишет|according to|from the book|lecture|supervision|quote from)\s+([^\n.!?]{2,90})", text, re.I)
        if match:
            attribution = match.group(0).strip()[:120]
    reuse = "UNKNOWN" if provenance in {"UNKNOWN", "ATTRIBUTED_SOURCE", "LIKELY_QUOTE_OR_EXCERPT"} else "TRANSFORMATIVE_SEED"
    privacy = []
    if re.search(r"\b(?:клиент|пациент|на сессии|в терапии|супервизи|my client|patient|session)\b", low):
        privacy.append("CASE_LIKE_MATERIAL")
    if re.search(r"\b(?:телефон|email|адрес|дата рождения|phone|address)\b", low) or re.search(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|(?:\+?\d[\d ()-]{8,}\d)", text):
        privacy.append("PERSONALLY_IDENTIFYING_DETAIL")
    if re.search(r"\b(?:изнасил|насили|суицид|самоубий|abuse|suicid)\w*", low):
        privacy.append("SENSITIVE_PERSONAL_STORY")
    if asset_type in {"ANECDOTE_OR_SITUATION"}:
        privacy.append("CASE_LIKE_MATERIAL")

    token_count = len(words)
    if token_count < 6:
        quality = "FRAGMENTARY"
    elif len(topic_tags) > 0 and token_count >= 35:
        quality = "CLEAN"
    elif token_count >= 15:
        quality = "MINOR_CLEANUP"
    else:
        quality = "UNCLEAR"
    dev = ["FRAGMENT_ONLY"]
    if token_count >= 25:
        dev.append("EXPANDABLE")
    if asset_type == "ANECDOTE_OR_SITUATION":
        dev.append("STORY_CAPABLE")
    if asset_type == "MODEL_OR_FRAMEWORK":
        dev.append("FRAMEWORK_CAPABLE")
    if asset_type == "EXERCISE":
        dev.append("EXERCISE_CAPABLE")
    if token_count >= 90 and asset_type in {"THERAPEUTIC_MECHANISM", "PRACTICAL_ADVICE", "MODEL_OR_FRAMEWORK"}:
        dev.append("CHAPTER_CAPABLE")
    return {
        "topics": topic_tags,
        "asset_type": {"label": asset_type, "confidence": 0.66 if asset_hits else 0.42, "evidence": asset_hits[:3], "method": "local_lexical_rule"},
        "development_potential": dev,
        "audience_applicability": ["THERAPIST"] if "CASE_LIKE_MATERIAL" in privacy else (["GENERAL_READER"] if topic_tags else ["UNKNOWN"]),
        "provenance": {"status": provenance, "attribution_if_explicit": attribution, "source_hint": attribution, "direct_reuse_risk": "REVIEW" if provenance in {"ATTRIBUTED_SOURCE", "LIKELY_QUOTE_OR_EXCERPT", "UNKNOWN"} else "UNASSESSED"},
        "reuse_mode": reuse,
        "privacy_flags": sorted(set(privacy)),
        "source_quality": quality,
        "classification_review": "UNCLASSIFIED" if not topic_tags else ("AMBIGUOUS" if len(words) <= 4 and any(tag["confidence"] <= 0.72 for tag in topic_tags) else "NONE"),
        "multi_theme_overlap": len(topic_tags) > 3,
    }


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def _paths(root: Path) -> dict[str, Path]:
    base = root / WAREHOUSE
    return {"base": base, "state": base / "state" / "warehouse.json", "taxonomy": base / "taxonomy" / "taxonomy-v1.json", "usage": base / "usage" / "ledger.json", "report": base / "reports" / "first-ingest.json", "latest_report": base / "reports" / "latest-ingest.json", "changes": base / "reports" / "latest-changes.json"}


def _taxonomy() -> dict[str, Any]:
    return {"schema_version": "psychology-warehouse-taxonomy/v1", "version": TAXONOMY_VERSION, "status": "PROPOSED_PENDING_OWNER_REVIEW", "discovery_method": "local deterministic lexical inventory; labels are descriptive, not clinical or commercial", "topics": [{"id": k, "evidence_prefixes": list(v)} for k, v in TOPICS.items()], "dimensions": {"asset_type": sorted(set(ASSET_CUES) | {"OBSERVATION", "FRAGMENT"}), "provenance": ["LIKELY_OWN", "PERSONAL_OR_PRACTICE_NOTE", "ATTRIBUTED_SOURCE", "LIKELY_QUOTE_OR_EXCERPT", "MIXED_OR_UNCLEAR", "UNKNOWN"], "development_potential": ["FRAGMENT_ONLY", "EXPANDABLE", "STORY_CAPABLE", "CHAPTER_CAPABLE", "FRAMEWORK_CAPABLE", "EXERCISE_CAPABLE", "UNKNOWN"], "reuse_mode": ["DIRECT_USE", "TRANSFORMATIVE_SEED", "RESEARCH_LEAD", "UNKNOWN"]}}


def _match_usage(notes: list[dict[str, Any]], book_blocks: list[str], project: str) -> list[dict[str, Any]]:
    normalized_book = [_norm(x) for x in book_blocks if _norm(x)]
    result = []
    for note in notes:
        norm = note["normalized_text_for_matching"]
        exact = next((i for i, candidate in enumerate(normalized_book, 1) if candidate == norm), None)
        if exact:
            relation, score, location = "EXACT_MATCH", 1.0, f"block:{exact}"
        else:
            scores = [(difflib.SequenceMatcher(None, norm, candidate, autojunk=False).ratio(), i) for i, candidate in enumerate(normalized_book, 1)]
            score, idx = max(scores, default=(0.0, 0))
            if score >= 0.78:
                relation, location = "REVIEW", f"block:{idx}"
            elif score >= 0.48:
                relation, location = "POSSIBLE_RELATION", f"block:{idx}"
            else:
                continue
        result.append({"note_id": note["note_id"], "project_id": project, "relation": relation, "score": round(score, 4), "location": location, "recorded_at": _now(), "basis": "deterministic_normalized_text_match", "decision_status": "REVIEW_REQUIRED" if relation != "EXACT_MATCH" else "OBSERVED_MATCH_NOT_EDITORIALLY_APPROVED"})
    return result


def _inventory(state: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    notes = [x for x in state["notes"] if x.get("current", True)]
    uses = defaultdict(list)
    for item in ledger.get("usages", []):
        uses[item["note_id"]].append(item)
    topic_counts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    asset_counts: Counter[str] = Counter()
    provenance = Counter()
    privacy_count = 0
    unclassified = 0
    ambiguous = 0
    for n in notes:
        for tag in n["classification"]["topics"]:
            topic_counts[tag["label"]].append(n)
        asset_counts[n["classification"]["asset_type"]["label"]] += 1
        provenance[n["classification"]["provenance"]["status"]] += 1
        privacy_count += bool(n["classification"]["privacy_flags"])
        unclassified += n["classification"]["classification_review"] == "UNCLASSIFIED"
        ambiguous += n["classification"]["classification_review"] == "AMBIGUOUS"
    topics = []
    for label, members in topic_counts.items():
        topics.append({"topic": label, "total": len(members), "percent_of_corpus": round(100 * len(members) / max(1, len(notes)), 2), "unused_current_ledger": sum(not uses[x["note_id"]] for x in members), "used": sum(bool(uses[x["note_id"]]) for x in members), "expandable": sum("EXPANDABLE" in x["classification"]["development_potential"] for x in members), "story_capable": sum("STORY_CAPABLE" in x["classification"]["development_potential"] for x in members), "provenance_risk": sum(x["classification"]["provenance"]["direct_reuse_risk"] == "REVIEW" for x in members), "example_note_ids": [x["note_id"] for x in members[:3]]})
    topics.sort(key=lambda x: (-x["total"], x["topic"])); cross = []
    labels = [x["topic"] for x in topics]
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            members = [x for x in notes if {a, b} <= {t["label"] for t in x["classification"]["topics"]}]
            if len(members) >= 3:
                cross.append({"topics": [a, b], "total": len(members)})
    return {"note_count": len(notes), "total_words": sum(n["word_count"] for n in notes), "total_characters": sum(n["character_count"] for n in notes), "exact_duplicate_extra_records": sum(1 for n in notes if n.get("duplicate_of")), "near_duplicate_pairs": sum(1 for n in notes for r in n.get("relationships", []) if r["type"] == "NEAR_DUPLICATE" and n["note_id"] < r["related_note_id"]), "unclassified": unclassified, "ambiguous": ambiguous, "provenance_distribution": dict(provenance), "explicit_attributions": sum(bool(n["classification"]["provenance"]["attribution_if_explicit"]) for n in notes), "distinct_source_hints": len({n["classification"]["provenance"]["source_hint"] for n in notes if n["classification"]["provenance"]["source_hint"]}), "direct_reuse_review": sum(n["classification"]["provenance"]["direct_reuse_risk"] == "REVIEW" for n in notes), "privacy_review": privacy_count, "themes": topics, "cross_theme_intersections": cross, "asset_types": [{"type": label, "total": count, "used": sum(bool(uses[n["note_id"]]) for n in notes if n["classification"]["asset_type"]["label"] == label), "unused": sum(not uses[n["note_id"]] for n in notes if n["classification"]["asset_type"]["label"] == label), "likely_own": 0, "unclear_provenance": sum(n["classification"]["provenance"]["status"] in {"UNKNOWN", "MIXED_OR_UNCLEAR"} for n in notes if n["classification"]["asset_type"]["label"] == label)} for label, count in asset_counts.items()]}


def ingest(root: Path, source: Path | None = None, *, full: bool = False) -> dict[str, Any]:
    source = source or SOURCE
    if not source.is_file():
        raise ValidationError(f"psychology source not found: {source}")
    before_stat = source.stat()
    data = source.read_bytes()
    source_before = {"path": str(source.resolve()), "size_bytes": len(data), "mtime_ns": before_stat.st_mtime_ns, "sha256": hashlib.sha256(data).hexdigest()}
    blocks = _read_blocks(data)
    paths = _paths(root)
    old_state = json.loads(paths["state"].read_text(encoding="utf-8")) if paths["state"].exists() else {"notes": []}
    old_notes = [n for n in old_state.get("notes", []) if n.get("current", True)]
    old_by_fp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for n in old_notes:
        old_by_fp[n["source_fingerprint"]].append(n)
    old_sequence = [n["source_fingerprint"] for n in sorted(old_notes, key=lambda n: n.get("source_order", 0))]
    new_fps = [_fingerprint(b["text"]) for b in blocks]
    opcodes = difflib.SequenceMatcher(None, old_sequence, new_fps, autojunk=False).get_opcodes()
    edited_pairs: dict[int, dict[str, Any]] = {}
    if not full:
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "replace" and (i2 - i1) == (j2 - j1):
                for off in range(i2 - i1):
                    previous = old_notes[i1 + off]
                    new_text = blocks[j1 + off]["text"]
                    if difflib.SequenceMatcher(None, previous["normalized_text_for_matching"], _norm(new_text), autojunk=False).ratio() >= 0.30:
                        edited_pairs[j1 + off] = previous
    all_prior = old_state.get("notes", [])
    old_fp_ids: dict[str, list[str]] = defaultdict(list)
    old_by_id = {n["note_id"]: n for n in all_prior}
    for n in all_prior:
        old_fp_ids[n["source_fingerprint"]].append(n["note_id"])
    consumed: Counter[str] = Counter()
    notes: list[dict[str, Any]] = []
    new_count = changed = unchanged = 0
    used_old_ids: set[str] = set()
    for index, block in enumerate(blocks):
        text = block["text"]
        fp = new_fps[index]
        duplicate_idx = consumed[fp]
        consumed[fp] += 1
        prior = None
        prior_ids = old_fp_ids.get(fp, [])
        while duplicate_idx < len(prior_ids):
            candidate = old_by_id.get(prior_ids[duplicate_idx])
            if candidate and candidate["note_id"] not in used_old_ids:
                prior = candidate; break
            duplicate_idx += 1
        if prior is None and index in edited_pairs:
            candidate = edited_pairs[index]
            if candidate["note_id"] not in used_old_ids:
                prior = candidate
        if prior:
            used_old_ids.add(prior["note_id"])
            note_id = prior["note_id"]
            is_edit = prior["source_fingerprint"] != fp
            classification = _classify(text) if (is_edit or full) else prior["classification"]
            history = list(prior.get("versions", []))
            if is_edit:
                history.append({"fingerprint": prior["source_fingerprint"], "original_text": prior["original_text"], "observed_at": prior.get("last_seen_at") or prior.get("first_seen_at"), "status": "SUPERSEDED_BY_SOURCE_EDIT"})
                source_edit = {"type": "SOURCE_EDIT", "related_note_id": note_id, "previous_fingerprint": prior["source_fingerprint"], "current_fingerprint": fp, "decision_status": "DETECTED_SEQUENCE_ALIGNMENT_REVIEW"}
                changed += 1
            else:
                unchanged += 1
            relations = [r for r in prior.get("relationships", []) if r.get("type") not in {"EXACT_DUPLICATE", "NEAR_DUPLICATE"}]
            if is_edit:
                relations.append(source_edit)
        else:
            base = "PHY-" + fp[:12]
            note_id = base if duplicate_idx == 0 else f"{base}-{duplicate_idx + 1:02d}"
            if any(n["note_id"] == note_id for n in all_prior):
                note_id = f"{base}-{index + 1:04d}"
            classification = _classify(text)
            history = []
            relations = []
            new_count += 1
        notes.append({"note_id": note_id, "source_file": str(source.resolve()), "source_block_id": f"BLK-{index+1:05d}", "source_location": {"line_start": block["line_start"], "line_end": block["line_end"]}, "source_order": index + 1, "original_text": text, "normalized_text_for_matching": _norm(text), "source_fingerprint": fp, "ingest_version": 1, "first_seen_at": prior.get("first_seen_at", _now()) if prior else _now(), "last_seen_at": _now(), "current": True, "word_count": len(_words(text)), "character_count": len(text), "classification": classification, "relationships": relations, "duplicate_of": None, "versions": history})

    exact_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for note in notes:
        exact_groups[note["source_fingerprint"]].append(note)
    for group in exact_groups.values():
        if len(group) > 1:
            for note in group[1:]:
                note["duplicate_of"] = group[0]["note_id"]
                note["relationships"].append({"type": "EXACT_DUPLICATE", "related_note_id": group[0]["note_id"]})

    token_sets = {n["note_id"]: set(_words(n["normalized_text_for_matching"])) for n in notes}
    postings: dict[str, list[str]] = defaultdict(list)
    for note in notes:
        for token in token_sets[note["note_id"]]:
            if len(token) >= 5:
                postings[token].append(note["note_id"])
    pair_candidates: set[tuple[str, str]] = set()
    for members in postings.values():
        if 1 < len(members) <= 40:
            for i, left in enumerate(members):
                for right in members[i + 1:]:
                    pair_candidates.add(tuple(sorted((left, right))))
    note_map = {n["note_id"]: n for n in notes}
    for left, right in pair_candidates:
        if note_map[left]["source_fingerprint"] == note_map[right]["source_fingerprint"]:
            continue
        a, b = token_sets[left], token_sets[right]
        score = len(a & b) / max(1, len(a | b))
        if score >= 0.88 and len(a) >= 6 and len(b) >= 6:
            note_map[left]["relationships"].append({"type": "NEAR_DUPLICATE", "related_note_id": right, "similarity": round(score, 4), "decision_status": "REVIEW"})
            note_map[right]["relationships"].append({"type": "NEAR_DUPLICATE", "related_note_id": left, "similarity": round(score, 4), "decision_status": "REVIEW"})

    present_ids = {n["note_id"] for n in notes}
    removed = []
    for old in all_prior:
        if old.get("current", True) and old["note_id"] not in present_ids:
            gone = dict(old); gone["current"] = False; gone["change_status"] = "NOT_PRESENT_IN_SOURCE"; removed.append(gone)
    history_notes = [n for n in all_prior if not n.get("current", True) and n["note_id"] not in present_ids]
    all_notes = notes + history_notes + removed

    after_data = source.read_bytes()
    source_after = {"size_bytes": len(after_data), "mtime_ns": source.stat().st_mtime_ns, "sha256": hashlib.sha256(after_data).hexdigest()}
    source_unchanged = source_before["sha256"] == source_after["sha256"]
    if not source_unchanged:
        raise ValidationError("SOURCE_CHANGED_DURING_INGEST: source hash changed; no warehouse files were written. Re-run ingest safely.")

    existing_usage = json.loads(paths["usage"].read_text(encoding="utf-8")) if paths["usage"].exists() else {"schema_version": "psychology-asset-usage-ledger/v1", "usages": []}
    existing_usage.setdefault("usages", [])
    state = {"schema_version": "psychology-warehouse-state/v1", "created_by": "abvx-psychology-warehouse-v1", "source": {**source_before, "verified_after_ingest": source_unchanged, "encoding": "UTF-8", "separator": "exact_line_***"}, "last_ingest_at": _now(), "taxonomy_version": TAXONOMY_VERSION, "notes": all_notes, "source_block_count": len(blocks), "last_delta": {"new": new_count, "changed": changed, "unchanged": unchanged, "removed_or_not_present": len(removed), "review": sum(n["classification"]["classification_review"] != "NONE" for n in notes)}}
    book = json.loads((root / "books/projects/fragments-therapists-notebook.json").read_text(encoding="utf-8"))
    canonical_locator = book.get("canonical_manuscript", {}).get("locator")
    usage_matches = []
    if canonical_locator:
        candidate = (root / canonical_locator).resolve()
        if candidate.is_file():
            book_text = candidate.read_text(encoding="utf-8")
            usage_matches = _match_usage(notes, [book_text], book["id"])
    current_mapping = {"project_id": book["id"], "title": book["title"], "canonical_book_record": "books/projects/fragments-therapists-notebook.json", "canonical_source_locator": canonical_locator, "mapping_status": "COMPLETE_TEXT_MATCH" if canonical_locator else "PARTIAL_BLOCKED_CANONICAL_SOURCE_LOCATOR_MISSING", "unmatched_means": "UNKNOWN_LINEAGE_NOT_EVIDENCE_OF_NONUSE", "matched_record_count": len(usage_matches)}
    other_mappings = [x for x in existing_usage.get("project_mappings", []) if x.get("project_id") != book["id"]]
    existing_usage["project_mappings"] = other_mappings + [current_mapping]
    usage_keys = {(x.get("note_id"), x.get("project_id"), x.get("relation"), x.get("location")) for x in existing_usage["usages"]}
    existing_usage["usages"].extend(x for x in usage_matches if (x["note_id"], x["project_id"], x["relation"], x["location"]) not in usage_keys)
    inv = _inventory(state, existing_usage)
    inv["top_10_themes"] = inv["themes"][:10]
    inv["long_tail_themes"] = [x for x in inv["themes"] if x["total"] <= 5]
    inv["multi_theme_overlap_count"] = sum(n["classification"].get("multi_theme_overlap", False) for n in notes)
    inv["possible_missing_or_unclear_themes"] = {"unclassified_count": inv["unclassified"], "example_note_ids": [n["note_id"] for n in notes if n["classification"]["classification_review"] == "UNCLASSIFIED"][:10]}
    state["inventory"] = inv
    changes = {"schema_version": "psychology-warehouse-delta/v1", "ingested_at": state["last_ingest_at"], "source_hash": source_before["sha256"], "full_consistency_check": full, "new": new_count, "changed": changed, "unchanged": unchanged, "removed_or_not_present": len(removed), "review": state["last_delta"]["review"], "new_note_ids": [n["note_id"] for n in notes if not any(o["note_id"] == n["note_id"] for o in old_notes)], "changed_note_ids": [n["note_id"] for n in notes if n["versions"]]}
    _atomic_json(paths["taxonomy"], json.loads(paths["taxonomy"].read_text()) if paths["taxonomy"].exists() else _taxonomy())
    _atomic_json(paths["state"], state)
    _atomic_json(paths["usage"], existing_usage)
    _atomic_json(paths["changes"], changes)
    structure = {"separator": "exact standalone line ***", "source_blocks": len(blocks), "multiline_blocks": sum(len(b["text"].rstrip("\r\n").splitlines()) > 1 for b in blocks), "blocks_with_multiple_paragraphs": sum(len([p for p in re.split(r"\n\s*\n", b["text"].strip()) if p.strip()]) > 1 for b in blocks), "date_leading_blocks": sum(bool(re.match(r"^\s*(?:\d{1,4}[./-]){1,2}\d{1,4}", b["text"])) for b in blocks), "heading_like_blocks": sum(bool(re.match(r"^\s*(?:#{1,6}\s|[А-ЯA-Z][^.!?]{1,70}:\s*$)", b["text"])) for b in blocks), "quote_marker_blocks": sum(bool(re.search(r"[«»“”\"]", b["text"])) for b in blocks), "explicit_source_cue_blocks": sum(any(re.search(p, b["text"], re.I) for p in PROVENANCE_CUES["source"]) for b in blocks), "paragraph_grouping": "blocks preserved intact; no sub-block split because internal boundaries were not reliably identifiable", "encoding": "UTF-8; original block strings preserved"}
    report = {"schema_version": "psychology-warehouse-first-ingest-report/v1", "source": source_before, "source_unchanged_after_ingest": source_unchanged, "source_structure": structure, "source_blocks": len(blocks), "atomic_notes": len(notes), "words": inv["total_words"], "characters": inv["total_characters"], "delta": state["last_delta"], "inventory": inv, "fragments_usage": existing_usage["project_mappings"][0], "usage_record_count": len(existing_usage["usages"]), "limitations": ["Deterministic lexical tags are a reviewable inventory aid, not a validated semantic model or clinical assessment.", "The Fragments canonical manuscript locator is null; usage linkage is therefore partial and no unmatched/unused assertion is made about that book.", "UNUSED means no usage recorded in this ledger only; it does not imply ownership, clearance, or publication safety."]}
    existing_first = json.loads(paths["report"].read_text(encoding="utf-8")) if paths["report"].exists() else None
    first_report = {**report, "delta": existing_first["delta"] if existing_first else report["delta"]}
    _atomic_json(paths["report"], first_report)
    _atomic_json(paths["latest_report"], {**report, "delta": changes})
    themes_table = "\n".join(f"| {x['topic']} | {x['total']} | {x['unused_current_ledger']} | {x['used']} | {x['expandable']} | {x['story_capable']} | {x['provenance_risk']} |" for x in inv["themes"])
    asset_table = "\n".join(f"| {x['type']} | {x['total']} | {x['used']} | {x['unused']} | {x['likely_own']} | {x['unclear_provenance']} |" for x in inv["asset_types"])
    md = ["# Psychology Warehouse V1 — First Ingest Report", "", f"Source: `{source_before['path']}`", f"SHA-256: `{source_before['sha256']}`", f"Source unchanged after ingest: **{source_unchanged}**", "", "## Structure", "", f"- Separator: `{structure['separator']}`", f"- Blocks / current notes: {len(blocks)} / {len(notes)}", f"- Words / characters: {inv['total_words']} / {inv['total_characters']}", f"- Multiline blocks: {structure['multiline_blocks']}; multiple paragraphs: {structure['blocks_with_multiple_paragraphs']}; date-leading: {structure['date_leading_blocks']}", f"- Heading-like blocks: {structure['heading_like_blocks']}; quote-marker blocks: {structure['quote_marker_blocks']}; blocks with source cues: {structure['explicit_source_cue_blocks']}", "- Whole source blocks are preserved; no speculative splits.", "", "## Delta", "", f"NEW {new_count} · CHANGED {changed} · UNCHANGED {unchanged} · NOT PRESENT {len(removed)} · REVIEW {state['last_delta']['review']}", "", "## Themes", "", "| Theme | Total | No usage in ledger | Used | Expandable | Story capable | Provenance review |", "|---|---:|---:|---:|---:|---:|---:|", themes_table, "", "## Asset types", "", "| Asset type | Total | Used | No usage in ledger | Likely own | Unclear provenance |", "|---|---:|---:|---:|---:|---:|", asset_table, "", "## Provenance and limits", "", f"- Provenance counts: `{json.dumps(inv['provenance_distribution'], ensure_ascii=False, sort_keys=True)}`", f"- Explicit attributions: {inv['explicit_attributions']}; distinct source hints: {inv['distinct_source_hints']}; privacy review flags: {inv['privacy_review']}.", f"- Fragments mapping: **{existing_usage['project_mappings'][0]['mapping_status']}**. The canonical book record has no manuscript locator, so the ledger makes no lineage or book-unused claim.", "- Taxonomy is proposed and pending owner review. Lexical rules are an inventory aid, not semantic qualification, clinical assessment, ownership evidence, or rights clearance.", "- ‘No usage in ledger’ is not equivalent to never published, owner-original, rights-cleared, or safe to publish."]
    delta_line = f"NEW {new_count} · CHANGED {changed} · UNCHANGED {unchanged} · NOT PRESENT {len(removed)} · REVIEW {state['last_delta']['review']}"
    latest_md_lines = list(md)
    if existing_first:
        old_delta = existing_first["delta"]
        first_line = f"NEW {old_delta['new']} · CHANGED {old_delta['changed']} · UNCHANGED {old_delta['unchanged']} · NOT PRESENT {old_delta['removed_or_not_present']} · REVIEW {old_delta['review']}"
        md = [first_line if line == delta_line else line for line in md]
    (paths["report"].with_suffix(".md")).write_text("\n".join(md) + "\n", encoding="utf-8")
    latest_md = paths["latest_report"].with_suffix(".md")
    latest_md.write_text("\n".join(latest_md_lines) + "\n", encoding="utf-8")
    return report


def load_state(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = _paths(root)
    if not paths["state"].is_file():
        raise ValidationError("psychology warehouse not ingested; run ./bin/abvx psychology ingest")
    state = json.loads(paths["state"].read_text(encoding="utf-8"))
    usage = json.loads(paths["usage"].read_text(encoding="utf-8"))
    return state, usage


def query(root: Path, action: str, value: str | None = None) -> dict[str, Any]:
    state, ledger = load_state(root)
    notes = [n for n in state["notes"] if n.get("current", True)]
    usage_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in ledger["usages"]:
        usage_by_id[item["note_id"]].append(item)
    if action == "status":
        return {k: state.get(k) for k in ("schema_version", "source", "last_ingest_at", "source_block_count", "last_delta", "inventory")}
    if action == "inventory":
        return state["inventory"]
    if action == "changes":
        return json.loads(_paths(root)["changes"].read_text(encoding="utf-8"))
    if action == "provenance":
        return {"distribution": state["inventory"]["provenance_distribution"], "explicit_attributions": state["inventory"]["explicit_attributions"], "distinct_source_hints": state["inventory"]["distinct_source_hints"], "direct_reuse_review": state["inventory"]["direct_reuse_review"], "privacy_review": state["inventory"]["privacy_review"]}
    if action == "topic":
        selected = [n for n in notes if any(t["label"].casefold() == (value or "").casefold() for t in n["classification"]["topics"])]
    elif action == "used":
        requested = (value or "").casefold()
        project_ids = {u["project_id"] for u in ledger.get("usages", []) if requested in u["project_id"].casefold()}
        project_ids.update(m["project_id"] for m in ledger.get("project_mappings", []) if requested in (m["project_id"] + " " + m.get("title", "")).casefold())
        selected = [n for n in notes if any(u["project_id"] in project_ids for u in usage_by_id[n["note_id"]])]
    elif action == "unused":
        selected = [n for n in notes if not usage_by_id[n["note_id"]]]
    else:
        raise ValidationError(f"unknown psychology query: {action}")
    relevant_mappings = [m for m in ledger.get("project_mappings", []) if action == "used" and (value or "").casefold() in (m["project_id"] + " " + m.get("title", "")).casefold()]
    blocked = action == "used" and not selected and any(m["mapping_status"].startswith("PARTIAL_BLOCKED") for m in relevant_mappings)
    return {"action": action, "value": value, "result": "BLOCKED" if blocked else "AVAILABLE", "count": None if blocked else len(selected), "reason": "canonical source locator missing; usage matching was not possible" if blocked else None, "usage_semantics": "no recorded usage in current ledger; not never-published, owner-original, rights-cleared, or safe-to-publish", "source_mapping_status": ledger.get("project_mappings", []), "note_ids": [n["note_id"] for n in selected]}
