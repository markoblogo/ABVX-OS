"""Bounded, local narrative-book pipeline primitives.

The public translator remains a separate bounded product.  This module is a
private orchestration layer: it turns a long source into stable blocks and
persists each result so a failed block can be resumed without rebuilding the
book.  It deliberately does not claim literary approval.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping


PIPELINE_VERSION = "narrative-toki-pona-pipeline-v1"
PUBLIC_MAX_CHARS = 500
INTERNAL_DEFAULT_BLOCK_CHARS = 1800


@dataclass
class PipelineConfig:
    mode: str = "INTERNAL_BOOK_PIPELINE"
    max_block_chars: int = INTERNAL_DEFAULT_BLOCK_CHARS
    max_context_chars: int = 600
    max_retries: int = 2
    concurrency: int = 1

    def __post_init__(self) -> None:
        if self.mode not in {"PUBLIC", "INTERNAL_BOOK_PIPELINE"}:
            raise ValueError("mode must be PUBLIC or INTERNAL_BOOK_PIPELINE")
        if self.mode == "PUBLIC" and self.max_block_chars > PUBLIC_MAX_CHARS:
            raise ValueError("public mode cannot exceed the public request limit")
        if self.max_block_chars < 40 or self.max_retries < 0:
            raise ValueError("invalid pipeline limits")


@dataclass
class SourceBlock:
    book_id: str
    section_id: str
    block_id: str
    source_text: str
    source_hash: str
    block_type: str
    ordinal: int
    speaker: str | None = None
    knowledge_type: str = "UNKNOWN_AMBIGUOUS"
    entities: list[str] = field(default_factory=list)
    spoiler_constraints: list[str] = field(default_factory=list)


@dataclass
class TranslationBlock:
    block_id: str
    source_hash: str
    translation_text: str = ""
    translation_hash: str = ""
    status: str = "PENDING"
    attempts: int = 0
    error: str | None = None
    history: list[dict] = field(default_factory=list)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _block_type(text: str) -> str:
    if text.startswith("##") or text.startswith("**") and text.endswith("**"):
        return "HEADING"
    if re.search(r"^['\"]?[^\n]{0,90}['\"]?\s*(said|replied|asked|cried|returned)", text, re.I):
        return "DIALOGUE"
    if re.search(r"\b(letter|will|document|note)\b", text, re.I):
        return "DOCUMENT"
    return "NARRATION"


def _knowledge_type(text: str) -> str:
    low = text.lower()
    if re.search(r"\b(thought|feared|suspected|believed|judged|wondered)\b", low):
        return "FOCAL_CHARACTER_INFERENCE"
    if re.search(r"\b(i wish|i swear|i am sure|said|replied|asked|cried)\b", low):
        return "DIALOGUE_CLAIM"
    if re.search(r"\b(letter|will|document|note)\b", low):
        return "DOCUMENT_CLAIM"
    return "NARRATOR_FACT"


def segment_source(text: str, book_id: str = "book") -> list[SourceBlock]:
    """Segment markdown/plain source into stable paragraph blocks."""
    section = "section-001"
    ordinal = 0
    blocks: list[SourceBlock] = []
    chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
    for chunk in chunks:
        if chunk.startswith("##") or (chunk.startswith("**") and chunk.endswith("**")):
            section = f"section-{len({b.section_id for b in blocks}) + 1:03d}"
        ordinal += 1
        block_type = _block_type(chunk)
        block_id = f"{book_id}:{section}:b{ordinal:04d}"
        constraints: list[str] = []
        if re.search(r"\b(Jekyll|Hyde|identity|double|disappearance|will|letter)\b", chunk, re.I):
            constraints.append("PRESERVE_SOURCE_KNOWLEDGE_BOUNDARY")
        blocks.append(SourceBlock(
            book_id, section, block_id, chunk, sha256(chunk), block_type, ordinal,
            knowledge_type=_knowledge_type(chunk), spoiler_constraints=constraints,
        ))
    return blocks


def load_entity_registry(path: str | Path) -> dict[str, dict]:
    payload = json.loads(Path(path).read_text())
    return {item["id"]: item for item in payload.get("entities", [])}


def approved_name_tokens(registry: Mapping[str, Mapping]) -> dict[str, str]:
    result: dict[str, str] = {}
    for entity in registry.values():
        strategy = entity.get("tokiPonaStrategy", "")
        match = re.search(r"\bjan\s+([A-Z][A-Za-z-]+)", strategy)
        if match:
            result[entity["sourceForm"]] = f"jan {match.group(1)}"
    return result


def validate_names(text: str, registry: Mapping[str, Mapping]) -> dict:
    allowed = set(approved_name_tokens(registry).values())
    source_names = {"Jekyll", "Hyde", "Utterson", "Lanyon", "Poole", "Carew", "Enfield"}
    unknown = sorted(n for n in re.findall(r"\b[A-Z][a-z]{2,}\b", text) if n not in {"Jan"})
    tp_names = sorted(set(re.findall(r"\bjan\s+[A-Z][A-Za-z-]+", text)))
    invalid = [n for n in tp_names if n not in allowed]
    collisions = []
    if "jan Jekil" in text and "jan Hata" in text and ("Jekyll" in text or "Hyde" in text):
        # Presence of both is allowed; this field exists to make the audit explicit.
        collisions = []
    return {"status": "PASS" if not invalid and not collisions else "FAIL",
            "unknownSourceNameCandidates": sorted(set(unknown) & source_names),
            "invalidTokiNames": invalid, "collisions": collisions,
            "allowedNames": sorted(allowed)}


def alignment_report(source: Iterable[SourceBlock], translated: Iterable[TranslationBlock]) -> dict:
    source = list(source); translated = list(translated)
    expected = [b.block_id for b in source]
    actual = [b.block_id for b in translated]
    duplicates = sorted({x for x in actual if actual.count(x) > 1})
    missing = [x for x in expected if x not in actual]
    unknown = [x for x in actual if x not in expected]
    empty = [b.block_id for b in translated if not b.translation_text.strip()]
    order = expected == actual
    status = "PASS" if not (duplicates or missing or unknown or empty or not order) else "FAIL"
    return {"status": status, "missing": missing, "duplicate": duplicates,
            "unknown": unknown, "emptyTranslation": empty,
            "orderMismatch": not order, "sourceCount": len(expected), "outputCount": len(actual)}


def knowledge_spoiler_report(blocks: Iterable[SourceBlock], translations: Iterable[TranslationBlock]) -> dict:
    by_id = {b.block_id: b for b in blocks}
    reviews = []
    for output in translations:
        source = by_id[output.block_id]
        text = output.translation_text.lower()
        if source.knowledge_type in {"FOCAL_CHARACTER_INFERENCE", "DOCUMENT_CLAIM", "DIALOGUE_CLAIM"}:
            reviews.append({"blockId": source.block_id, "status": "REVIEW",
                            "reason": "claim/inference/document boundary requires editorial review"})
        if "jekil li jan hata" in text or "jekil li sama hata" in text:
            reviews.append({"blockId": source.block_id, "status": "FAIL",
                            "reason": "possible premature Jekyll/Hyde identity disclosure"})
    status = "FAIL" if any(x["status"] == "FAIL" for x in reviews) else ("REVIEW" if reviews else "PASS")
    return {"status": status, "reviews": reviews}


def sitelen_name_representation(text: str) -> str:
    """Deterministic readable fallback until cartouche support is available."""
    return re.sub(r"\bjan\s+([A-Z][A-Za-z-]+)", r"⟦jan \1⟧", text)


class NarrativeRunner:
    def __init__(self, run_dir: str | Path, config: PipelineConfig | None = None):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or PipelineConfig()
        self.manifest_path = self.run_dir / "run-manifest.json"

    def run(self, blocks: list[SourceBlock], provider: Callable[[SourceBlock, str], str],
            *, fail_block_ids: set[str] | None = None, resume: bool = True) -> list[TranslationBlock]:
        old: dict[str, dict] = {}
        if resume and self.manifest_path.exists():
            old = {item["block_id"]: item for item in json.loads(self.manifest_path.read_text()).get("blocks", [])}
        results: list[TranslationBlock] = []
        fail_block_ids = fail_block_ids or set()
        for block in blocks:
            previous = old.get(block.block_id)
            if previous and previous.get("source_hash") != block.source_hash:
                previous = None
            if previous and previous.get("status") == "SUCCESS":
                results.append(TranslationBlock(**{k: previous.get(k) for k in TranslationBlock.__dataclass_fields__}))
                continue
            item = TranslationBlock(block.block_id, block.source_hash)
            for attempt in range(self.config.max_retries + 1):
                item.attempts += 1
                try:
                    if block.block_id in fail_block_ids and attempt == 0:
                        raise RuntimeError("simulated provider failure")
                    item.translation_text = provider(block, "")
                    if not item.translation_text.strip():
                        raise ValueError("TRANSLATION_EMPTY")
                    item.translation_hash = sha256(item.translation_text)
                    item.status = "SUCCESS"
                    item.history.append({"kind": "MODEL_OUTPUT", "attempt": item.attempts})
                    break
                except Exception as exc:  # surfaced in manifest; caller decides release gate
                    item.error = str(exc)
                    item.history.append({"kind": "ERROR", "attempt": item.attempts, "error": str(exc)})
            if item.status != "SUCCESS":
                item.status = "FAILED"
            results.append(item)
            self._write_manifest(blocks, results)
        self._write_manifest(blocks, results)
        return results

    def _write_manifest(self, blocks: list[SourceBlock], results: list[TranslationBlock]) -> None:
        payload = {"schemaVersion": "1.0", "pipelineVersion": PIPELINE_VERSION,
                   "mode": self.config.mode, "runId": self.run_dir.name,
                   "sourceBlockCount": len(blocks), "updatedAt": time.time(),
                   "blocks": [asdict(r) for r in results]}
        self.manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def public_request_allowed(text: str) -> bool:
    return isinstance(text, str) and 0 < len(text) <= PUBLIC_MAX_CHARS


def build_translation_prompt(block: SourceBlock, *, previous: str = "", next_text: str = "",
                            phrasebook: Mapping[str, str] | None = None) -> str:
    """Build a bounded provider prompt; context is evidence, not output."""
    names = ", ".join(block.entities) or "none"
    terms = json.dumps(dict(phrasebook or {}), ensure_ascii=False)
    return ("Translate ONLY TARGET BLOCK into readable natural Toki Pona. "
            "Prioritize source meaning, knowledge state, plot logic, speaker identity, "
            "uncertainty, then style. Do not turn claim into fact, possibility into certainty, "
            "opinion into narrator fact, condition into unconditional event, question into statement, "
            "or fear into observed event. Use approved vocabulary and ledger names only; flag unknown words.\n"
            f"SECTION={block.section_id}; TYPE={block.block_type}; KNOWLEDGE={block.knowledge_type}; "
            f"ENTITIES={names}; CONSTRAINTS={block.spoiler_constraints}; PHRASEBOOK={terms}\n"
            f"PREVIOUS CONTEXT (do not translate): {previous[-600:]}\n"
            f"NEXT CONTEXT (do not translate): {next_text[:600]}\n"
            f"TARGET BLOCK [{block.block_id}]:\n{block.source_text}")


class LocalModelNarrativeProvider:
    """Trusted-local adapter for the existing read-only model worker.

    It never falls back to the public translator and never exposes a remote
    credential.  Unavailable local service is surfaced as a provider failure.
    """

    def __init__(self, url: str | None = None, *, model: str | None = None, timeout: int = 90):
        self.url = url or os.environ.get("ABVX_LOCAL_MODEL_URL", "http://127.0.0.1:8766/v1/answer")
        self.model = model or os.environ.get("ABVX_LOCAL_MODEL_ID", "occ-ai/OCC-RAG-0.6B")
        self.timeout = timeout

    def translate(self, block: SourceBlock, *, previous: str = "", next_text: str = "",
                  phrasebook: Mapping[str, str] | None = None) -> dict:
        prompt = build_translation_prompt(block, previous=previous, next_text=next_text, phrasebook=phrasebook)
        body = json.dumps({"project": "narrative-toki-pona", "request_id": block.block_id,
                           "question": prompt, "context": [{"id": block.block_id, "text": block.source_text}]}).encode()
        try:
            response = urlopen(Request(self.url, data=body, headers={"Content-Type": "application/json"}), timeout=self.timeout)
            payload = json.loads(response.read().decode())
        except (OSError, URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"PROVIDER_UNAVAILABLE: {exc}") from exc
        if not isinstance(payload, dict) or not payload.get("ok"):
            raise RuntimeError(f"PROVIDER_REJECTED: {payload}")
        answer = payload.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("TRANSLATION_EMPTY")
        return {"translation": answer.strip(), "provider": "abvx-local-model-worker",
                "model": payload.get("model", self.model), "requestId": block.block_id}
