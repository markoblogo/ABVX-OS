from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .harness import ValidationError, load_json


def answer_local_model(root: Path, request_path: Path, *, url: str | None = None) -> dict:
    request = load_json(request_path)
    if not isinstance(request, dict) or not isinstance(request.get("question"), str):
        raise ValidationError(f"{request_path}: expected a local model request with question")
    endpoint = url or os.environ.get("ABVX_LOCAL_MODEL_URL", "http://127.0.0.1:8766/v1/answer")
    body = json.dumps({**request, "project": "abvx-os"}).encode()
    try:
        response = urlopen(Request(endpoint, data=body, headers={"Content-Type": "application/json"}), timeout=45)
        payload = json.loads(response.read().decode())
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise ValidationError(f"local model unavailable: {exc}") from exc
    if not isinstance(payload, dict) or not payload.get("ok"):
        raise ValidationError(f"local model rejected request: {payload}")
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("context_mode") != "explicit_only" or evidence.get("live_proof") is not False:
        raise ValidationError("local model receipt is missing the explicit-only/read-only contract")
    return payload
