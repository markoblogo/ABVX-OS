#!/usr/bin/env python3
"""One-block, budgeted lexical adjudication for Jekyll chapter 10 block 112."""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/jekyll-toki-pona-full-v1"
OUT = BASE / "editorial-review-v1/lexical-adjudication-ch10b112.json"


def main():
    ledger = json.loads((BASE / "JEKYLL_TOKI_PONA_EDITORIAL_LEDGER_V2.json").read_text(encoding="utf-8"))
    rows = ledger["blocks"]
    i = next(i for i, row in enumerate(rows) if row["blockId"].endswith("chapter-10:block-0112"))
    context = rows[i - 1 : i + 2]
    registry = json.loads((ROOT / "artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json").read_text(encoding="utf-8"))
    relevant_registry = {k: v for k, v in registry.items() if k in {"person-hyde", "object-powder", "object-draught"}}
    prompt = f'''One narrow lexical question only; do not translate or review any other manuscript block. This is a bounded semantic adjudication using source and immediate context, not native-speaker certification.

The English phrase is “not only hellish but inorganic.” The current Toki Pona is `ijo pi lon ala`, which may mean nonexistent. Determine whether a more defensible, comprehensible Toki Pona circumlocution can express non-organic / non-living matter (not nonexistent and not simply dead) using established common/core words. Do not invent an obscure one-word lexeme. If no reliable phrase is available, return NO_SAFE_REPLACEMENT and say the human lexical blocker remains.

Project constraints/context: {json.dumps(relevant_registry, ensure_ascii=False)}

Immediate source + V2 context:
{json.dumps(context, ensure_ascii=False)}

Return JSON only: {{"decision":"RECOMMEND_PHRASE|NO_SAFE_REPLACEMENT","candidate":"... or null","literalReading":"...","whyNotNonexistent":"...","idiomaticityRisk":"...","confidence":"high|medium|low","humanNativeSpeakerReviewStillNeeded":true}}'''
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not configured")
    model = "gpt-6-luna"
    body = {"model": model, "input": prompt, "reasoning": {"effort": "low"}, "max_output_tokens": 1200, "store": False}
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    started = time.time()
    with urllib.request.urlopen(req, timeout=180) as response:
        payload = json.load(response)
    visible = payload.get("output_text") or "\n".join(
        content.get("text", "") for item in payload.get("output", [])
        for content in item.get("content", []) if content.get("type") in ("output_text", "text")
    )
    parsed = None
    try:
        parsed = json.loads(visible)
    except json.JSONDecodeError:
        a, z = visible.find("{"), visible.rfind("}")
        if a >= 0 and z > a:
            parsed = json.loads(visible[a : z + 1])
    record = {
        "schemaVersion": "1",
        "status": payload.get("status"),
        "model": payload.get("model", model),
        "responseId": payload.get("id"),
        "requestStore": False,
        "inputSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "usage": payload.get("usage"),
        "elapsedMs": round((time.time() - started) * 1000),
        "result": parsed,
        "visibleOutput": visible,
    }
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "model": record["model"], "responseId": record["responseId"], "usage": record["usage"], "result": parsed, "outputPath": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
