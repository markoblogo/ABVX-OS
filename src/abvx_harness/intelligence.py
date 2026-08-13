from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .content_ops import _canonical_url, _load_adapter_registry, _schema_path, _slugify, _truncate_words  # type: ignore[attr-defined]
from .harness import ValidationError, load_json, now_iso, validate

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_CHEAP_API_MODEL = "gpt-5.6-luna"
GPT_56_LUNA_SHORT_CONTEXT_INPUT_PER_MILLION = 0.20
GPT_56_LUNA_SHORT_CONTEXT_OUTPUT_PER_MILLION = 1.20


def _load_schema(root: Path, name: str) -> dict[str, Any]:
    return load_json(root / "schemas" / name)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _task_registry(root: Path) -> dict[str, Any]:
    path = root / "registries" / "intelligence-tasks.json"
    value = load_json(path)
    validate(value, _load_schema(root, "registry.schema.json"), schema_path=_schema_path(root, "registry.schema.json"), root=root, location=str(path))
    return value


def _task_entry(root: Path, task_id: str) -> dict[str, Any]:
    for entry in _task_registry(root)["entries"]:
        if entry["id"] == task_id:
            return entry
    raise ValidationError(f"unknown intelligence task: {task_id}")


def _task_output_schema(root: Path, task: dict[str, Any]) -> dict[str, Any]:
    schema_ref = task["output_schema"]
    if not isinstance(schema_ref, str):
        raise ValidationError(f"invalid output schema for task: {task['id']}")
    return load_json(root / schema_ref)


def _context_bound_schema(task: dict[str, Any], schema: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if task["id"] != "content-enrichment":
        return schema
    bound = json.loads(json.dumps(schema))
    allowed_links = context.get("allowed_internal_links", [])
    if allowed_links:
        bound["properties"]["internal_link_suggestions"]["items"] = {
            "type": "string",
            "enum": allowed_links,
        }
    return bound


def _intelligence_runtime_path(root: Path, stem: str) -> Path:
    return root / "evidence" / "intelligence" / f"{stem}.runtime.json"


def _intelligence_evidence_path(root: Path, stem: str) -> Path:
    return root / "evidence" / "intelligence" / f"{stem}.evidence.json"


def _load_adapter(root: Path, adapter_id: str) -> dict[str, Any]:
    registry = _load_adapter_registry(root)
    for entry in registry["entries"]:
        if entry["id"] == adapter_id:
            return entry
    raise ValidationError(f"unknown publishing adapter: {adapter_id}")


def _build_content_enrichment_context(root: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    payload = fixture["payload"]
    adapter = _load_adapter(root, fixture["adapter_id"])
    deterministic_slug = fixture.get("slug") or _slugify(fixture["title"])
    _, hreflang = _canonical_url(adapter, deterministic_slug, fixture["locales"])
    surface_links = {
        ("abvxsite", "writing"): ["/writing", "/about", "/books", "/work"],
        ("1d3x", "blog"): ["https://pop.1d3x.com/", "https://spike.1d3x.com/", "https://1d3x.com/methodology"],
        ("ssi", "blog"): ["/en/blog", "/en/context", "/en/methodology"],
        ("mn7r", "blog"): ["/blog", "/research", "/about"],
    }
    return {
        "content_id": fixture["id"],
        "project": fixture["project"],
        "surface": fixture["surface"],
        "kind": fixture["kind"],
        "language": payload.get("language") or fixture["locales"][0],
        "title": fixture["title"],
        "summary": fixture["summary"],
        "body_lines": payload["body_lines"],
        "source_refs": payload.get("source_refs", []),
        "locales": fixture["locales"],
        "suggest_title_if_missing": not bool(fixture.get("title")),
        "allowed_internal_links": surface_links.get((fixture["project"], fixture["surface"]), []),
        "deterministic_slug": deterministic_slug,
        "hreflang": hreflang,
    }


def _select_local_model() -> str | None:
    preferred = os.environ.get("ABVX_INTELLIGENCE_MODEL")
    if preferred:
        return preferred
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    available = {model.get("name") for model in payload.get("models", []) if isinstance(model, dict)}
    for candidate in ("qwen3.5:4b", "gemma4:12b", "gpt-oss:20b", "qwen2.5-coder-3b-continue:latest"):
        if candidate in available:
            return candidate
    return next(iter(sorted(available))) if available else None


def _reasoning_policy(task: dict[str, Any], policy: dict[str, Any] | None) -> dict[str, Any]:
    cost_guard = task.get("cost_guard", {})
    merged = {
        "allow_external": False,
        "preferred_tier": task["preferred_tier"],
        "max_input_chars": task["input_bounds"]["max_chars"],
        "max_body_lines": task["input_bounds"]["max_body_lines"],
        "timeout_seconds": task.get("timeout_seconds", 180),
        "cheap_api_model": cost_guard.get("model", DEFAULT_CHEAP_API_MODEL),
        "max_output_tokens": cost_guard.get("max_output_tokens", 900),
        "reasoning_effort": cost_guard.get("reasoning_effort", "low"),
        "expected_cost_class": cost_guard.get("expected_cost_class", "CHEAP"),
        "max_estimated_cost_usd": cost_guard.get("max_estimated_cost_usd", 0.01),
    }
    if policy:
        merged.update(policy)
    return merged


def _build_prompt(task: dict[str, Any], context: dict[str, Any]) -> str:
    if task["id"] != "content-enrichment":
        raise ValidationError(f"unsupported intelligence prompt task: {task['id']}")
    body_lines = context["body_lines"][: task["input_bounds"]["max_body_lines"]]
    body_text = "\n".join(body_lines)
    payload = {
        "task": "Generate bounded semantic enrichment for publication metadata.",
        "rules": [
            "Use only the supplied content.",
            "Do not rewrite the body.",
            "Do not invent facts, links, entities or projects.",
            "Use only allowed_internal_links when suggesting internal links.",
            "If the title is already present, proposed_title must be null.",
            "Return concise, publication-ready metadata.",
        ],
        "input": {
            "language": context["language"],
            "title": context["title"],
            "summary": context["summary"],
            "body": body_text,
            "source_refs": context["source_refs"],
            "allowed_internal_links": context["allowed_internal_links"],
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _run_ollama_generate(*, model: str, prompt: str, schema: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    started = time.monotonic()
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0},
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = json.load(response)
    payload["_elapsed_ms"] = int((time.monotonic() - started) * 1000)
    return payload


def _response_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    return ""


def _estimate_openai_cost_usd(model: str, usage: dict[str, Any] | None) -> float | None:
    if model != DEFAULT_CHEAP_API_MODEL or not usage:
        return None
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    return round(
        (input_tokens / 1_000_000 * GPT_56_LUNA_SHORT_CONTEXT_INPUT_PER_MILLION)
        + (output_tokens / 1_000_000 * GPT_56_LUNA_SHORT_CONTEXT_OUTPUT_PER_MILLION),
        8,
    )


def _run_openai_responses(*, model: str, prompt: str, schema: dict[str, Any], timeout_seconds: int, max_output_tokens: int, reasoning_effort: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValidationError("OPENAI_API_KEY is not configured")
    started = time.monotonic()
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(
            {
                "model": model,
                "input": prompt,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "content_enrichment",
                        "schema": schema,
                        "strict": True,
                    }
                },
                "reasoning": {"effort": reasoning_effort},
                "max_output_tokens": max_output_tokens,
                "store": False,
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = json.load(response)
    payload["_elapsed_ms"] = int((time.monotonic() - started) * 1000)
    return payload


def _validate_content_enrichment_output(output: dict[str, Any], context: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if output.get("proposed_title") not in (None, context["title"]):
        warnings.append("title was already present; proposed_title should normally remain null")
    allowed_links = set(context["allowed_internal_links"])
    invalid_links = [link for link in output.get("internal_link_suggestions", []) if link not in allowed_links]
    if invalid_links:
        raise ValidationError(f"model returned unsupported internal links: {', '.join(invalid_links)}")
    if not output.get("tags"):
        raise ValidationError("model returned no tags")
    if not output.get("machine_summary"):
        raise ValidationError("model returned empty machine summary")
    return warnings


def execute_intelligence_task(
    root: Path,
    *,
    task_id: str,
    context: dict[str, Any],
    policy: dict[str, Any] | None = None,
    provider_override: str | None = None,
    runtime_stem: str | None = None,
) -> dict[str, Any]:
    task = _task_entry(root, task_id)
    task_policy = _reasoning_policy(task, policy)
    schema = _context_bound_schema(task, _task_output_schema(root, task), context)
    context_json = json.dumps(context, ensure_ascii=False)
    if len(context_json) > task_policy["max_input_chars"]:
        return {
            "schema_version": "v1",
            "task_id": task_id,
            "status": "ESCALATION_REQUIRED",
            "provider": None,
            "model": None,
            "execution_tier": "CODEX_ESCALATION",
            "latency_ms": 0,
            "usage": None,
            "locality": "LOCAL",
            "validation": {
                "schema": "NOT_RUN",
                "checks": [],
                "warnings": [],
            },
            "failure_reason": f"task input exceeds max_input_chars={task_policy['max_input_chars']}",
            "output": None,
            "policy": task_policy,
            "captured_at": now_iso(),
        }
    provider = provider_override or ("cheap.api" if task_policy["preferred_tier"] == "CHEAP_API" else task["allowed_providers"][0])
    if provider == "ollama.local":
        model = _select_local_model()
        if not model:
            result = {
                "schema_version": "v1",
                "task_id": task_id,
                "status": "ESCALATION_REQUIRED",
                "provider": provider,
                "model": None,
                "execution_tier": "CODEX_ESCALATION",
                "latency_ms": 0,
                "usage": None,
                "locality": "LOCAL",
                "validation": {
                    "schema": "NOT_RUN",
                    "checks": [],
                    "warnings": [],
                },
                "failure_reason": "no local Ollama model available",
                "output": None,
                "policy": task_policy,
                "captured_at": now_iso(),
            }
        else:
            try:
                raw = _run_ollama_generate(model=model, prompt=_build_prompt(task, context), schema=schema, timeout_seconds=int(task_policy["timeout_seconds"]))
                response_text = raw.get("response")
                if not isinstance(response_text, str) or not response_text.strip():
                    raise ValidationError("empty model response")
                output = json.loads(response_text)
                validate(output, schema, schema_path=root / task["output_schema"], root=root, location=f"intelligence:{task_id}")
                warnings = _validate_content_enrichment_output(output, context) if task_id == "content-enrichment" else []
                result = {
                    "schema_version": "v1",
                    "task_id": task_id,
                    "status": "SUCCEEDED",
                    "provider": provider,
                    "model": model,
                    "execution_tier": "LOCAL_LLM",
                    "latency_ms": raw["_elapsed_ms"],
                    "usage": {
                        "prompt_eval_count": raw.get("prompt_eval_count"),
                        "eval_count": raw.get("eval_count"),
                        "total_duration": raw.get("total_duration"),
                    },
                    "locality": "LOCAL",
                    "validation": {
                        "schema": "PASS",
                        "checks": ["json-schema", "allowlisted-internal-links", "non-empty-tags", "non-empty-summary"],
                        "warnings": warnings,
                    },
                    "failure_reason": None,
                    "output": output,
                    "policy": task_policy,
                    "captured_at": now_iso(),
                }
            except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValidationError) as exc:
                result = {
                    "schema_version": "v1",
                    "task_id": task_id,
                    "status": "ESCALATION_REQUIRED",
                    "provider": provider,
                    "model": model,
                    "execution_tier": "CODEX_ESCALATION",
                    "latency_ms": 0,
                    "usage": None,
                    "locality": "LOCAL",
                    "validation": {
                        "schema": "FAIL",
                        "checks": [],
                        "warnings": [],
                    },
                    "failure_reason": str(exc),
                    "output": None,
                    "policy": task_policy,
                    "captured_at": now_iso(),
                }
    elif provider == "cheap.api":
        model = str(task_policy.get("cheap_api_model") or DEFAULT_CHEAP_API_MODEL)
        try:
            raw = _run_openai_responses(
                model=model,
                prompt=_build_prompt(task, context),
                schema=schema,
                timeout_seconds=int(task_policy["timeout_seconds"]),
                max_output_tokens=int(task_policy["max_output_tokens"]),
                reasoning_effort=str(task_policy["reasoning_effort"]),
            )
            response_text = _response_output_text(raw)
            if not response_text.strip():
                raise ValidationError("empty model response")
            output = json.loads(response_text)
            validate(output, schema, schema_path=root / task["output_schema"], root=root, location=f"intelligence:{task_id}")
            warnings = _validate_content_enrichment_output(output, context) if task_id == "content-enrichment" else []
            usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
            estimated_cost = _estimate_openai_cost_usd(model, usage)
            if estimated_cost is not None and estimated_cost > float(task_policy["max_estimated_cost_usd"]):
                raise ValidationError(f"estimated cost {estimated_cost} exceeds max_estimated_cost_usd={task_policy['max_estimated_cost_usd']}")
            result = {
                "schema_version": "v1",
                "task_id": task_id,
                "status": "SUCCEEDED",
                "provider": provider,
                "model": model,
                "execution_tier": "CHEAP_API",
                "latency_ms": raw["_elapsed_ms"],
                "usage": {
                    **usage,
                    "estimated_cost_usd": estimated_cost,
                    "pricing_source": "OpenAI pricing, gpt-5.6-luna short context",
                },
                "locality": "EXTERNAL",
                "validation": {
                    "schema": "PASS",
                    "checks": ["json-schema", "allowlisted-internal-links", "non-empty-tags", "non-empty-summary", "bounded-cost"],
                    "warnings": warnings,
                },
                "failure_reason": None,
                "output": output,
                "policy": task_policy,
                "captured_at": now_iso(),
            }
        except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValidationError) as exc:
            result = {
                "schema_version": "v1",
                "task_id": task_id,
                "status": "ESCALATION_REQUIRED",
                "provider": provider,
                "model": model,
                "execution_tier": "CODEX_ESCALATION",
                "latency_ms": 0,
                "usage": None,
                "locality": "EXTERNAL",
                "validation": {
                    "schema": "FAIL",
                    "checks": [],
                    "warnings": [],
                },
                "failure_reason": str(exc),
                "output": None,
                "policy": task_policy,
                "captured_at": now_iso(),
            }
    else:
        result = {
            "schema_version": "v1",
            "task_id": task_id,
            "status": "ESCALATION_REQUIRED",
            "provider": provider,
            "model": None,
            "execution_tier": "CODEX_ESCALATION",
            "latency_ms": 0,
            "usage": None,
            "locality": "EXTERNAL" if provider.endswith(".api") else "LOCAL",
            "validation": {
                "schema": "NOT_RUN",
                "checks": [],
                "warnings": [],
            },
            "failure_reason": f"provider not configured: {provider}",
            "output": None,
            "policy": task_policy,
            "captured_at": now_iso(),
        }
    validate(result, _load_schema(root, "intelligence_result.schema.json"), schema_path=_schema_path(root, "intelligence_result.schema.json"), root=root, location=f"intelligence-result:{task_id}")
    if runtime_stem:
        _write_json(_intelligence_runtime_path(root, runtime_stem), result)
    return result


def run_content_enrichment(root: Path, fixture_ref: str, *, runtime_stem: str | None = None, provider: str | None = None) -> dict[str, Any]:
    from .content_ops import _load_fixture  # local import to avoid circular import at module load time

    fixture = _load_fixture(root, fixture_ref)
    if fixture["adapter_id"] != "abvx.writing":
        raise ValidationError("content-enrichment acceptance path currently expects an ABVX writing fixture")
    return execute_intelligence_task(
        root,
        task_id="content-enrichment",
        context=_build_content_enrichment_context(root, fixture),
        provider_override=provider,
        runtime_stem=runtime_stem or fixture["id"],
    )


def build_content_item_enrichment(root: Path, fixture: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime = execute_intelligence_task(
        root,
        task_id="content-enrichment",
        context=_build_content_enrichment_context(root, fixture),
        provider_override="ollama.local",
        runtime_stem=fixture["id"],
    )
    adapter = _load_adapter(root, fixture["adapter_id"])
    deterministic_slug = fixture.get("slug") or _slugify(fixture["title"])
    canonical_path, hreflang = _canonical_url(adapter, deterministic_slug, fixture["locales"])
    payload = fixture["payload"]
    if runtime["status"] != "SUCCEEDED" or not isinstance(runtime.get("output"), dict):
        raise ValidationError(runtime["failure_reason"] or "intelligence runtime failed")
    output = runtime["output"]
    machine_summary = _truncate_words(output["machine_summary"], 240)
    meta_description = _truncate_words(output["meta_description"], 165)
    seo_title = _truncate_words(output["seo_title"] or fixture["title"], 70)
    cover_path = payload.get("cover_image")
    image_alt = payload.get("image_alt") or (f"{fixture['title']} cover" if cover_path else None)
    enrichment = {
        "slug": deterministic_slug,
        "seo_title": seo_title,
        "meta_description": meta_description,
        "canonical_path": canonical_path,
        "open_graph": {
            "title": seo_title,
            "description": meta_description,
            "image": cover_path,
            "image_alt": image_alt,
        },
        "social_preview": {
            "title": seo_title,
            "description": meta_description,
            "image": cover_path,
            "image_alt": image_alt,
        },
        "date_published": payload.get("date_published") or fixture["provenance"]["observed_at"][:10],
        "date_modified": now_iso()[:10],
        "author": payload.get("author") or adapter.get("default_author") or "Anton BV",
        "publisher": payload.get("publisher") or adapter.get("default_publisher") or fixture["project"],
        "tags": output["tags"],
        "topics": output["topics"],
        "primary_entities": output["primary_entities"],
        "related_projects": [],
        "internal_link_suggestions": output["internal_link_suggestions"],
        "primary_source_links": payload.get("source_refs", []),
        "hreflang": hreflang,
        "sitemap_state": adapter.get("default_sitemap_state", "INDEXABLE"),
        "indexability": adapter.get("default_indexability", "INDEXABLE"),
        "structured_data": {
            "type": adapter.get("structured_data_type", "Article"),
            "status": "SUPPORTED",
        },
        "machine_summary": machine_summary,
        "cortex": None,
        "warnings": list(runtime["validation"]["warnings"]),
    }
    evidence = {
        "id": f"{fixture['id']}-intelligence-runtime",
        "source": "abvx-intelligence",
        "timestamp": now_iso(),
        "candidate": runtime["provider"] or "none",
        "fixture": fixture["id"],
        "result": "PASS" if runtime["status"] == "SUCCEEDED" else "FAIL",
        "metrics": {
            "task_id": runtime["task_id"],
            "execution_tier": runtime["execution_tier"],
            "latency_ms": runtime["latency_ms"],
            "locality": runtime["locality"],
            "model": runtime["model"],
            "usage": runtime["usage"],
            "validation": runtime["validation"],
        },
        "stdout_ref": "internal:none",
        "stderr_ref": "internal:none",
        "artifact_refs": [str(_intelligence_runtime_path(root, fixture["id"]).relative_to(root))],
        "provenance": {
            "recorded_by": "ABVX-INTELLIGENCE-001",
            "source_uri": None,
            "observed_at": now_iso(),
        },
        "environment": {
            "repository_path": str(root),
            "project": fixture["project"],
            "surface": fixture["surface"],
            "external_mutation_performed": False,
        },
    }
    validate(evidence, _load_schema(root, "evidence_record.schema.json"), schema_path=_schema_path(root, "evidence_record.schema.json"), root=root, location=f"evidence:intelligence:{fixture['id']}")
    _write_json(_intelligence_evidence_path(root, fixture["id"]), evidence)
    return enrichment, runtime
