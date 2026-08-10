from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .context import assemble_context_pack, load_context_request
from .harness import ValidationError, load_json, now_iso, validate


def _schema_path(root: Path, name: str) -> Path:
    return root / "schemas" / name


def _load_schema(root: Path, name: str) -> dict[str, Any]:
    return load_json(_schema_path(root, name))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _slugify(value: str) -> str:
    return re.sub(r"(^-+|-+$)", "", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")[:80]


def _truncate_words(value: str, limit: int) -> str:
    compact = " ".join(value.split()).strip()
    if len(compact) <= limit:
        return compact
    clipped = compact[: limit + 1]
    boundary = clipped.rfind(" ")
    if boundary < 60:
        boundary = limit
    return compact[:boundary].rstrip(" ,;:-.") + "..."


def _first_sentence(value: str) -> str:
    compact = " ".join(value.split()).strip()
    match = re.match(r"^(.{1,220}?[.!?])(?:\s|$)", compact)
    return match.group(1) if match else compact


def _items_dir(root: Path) -> Path:
    return root / "content" / "items"


def _fixtures_dir(root: Path) -> Path:
    return root / "content" / "fixtures"


def _packets_dir(root: Path) -> Path:
    return root / "content" / "publish-packets"


def _evidence_dir(root: Path) -> Path:
    return root / "evidence" / "content-ops"


def _events_dir(root: Path, project: str) -> Path:
    return root / "events" / "projects" / project


def _load_adapter_registry(root: Path) -> dict[str, Any]:
    path = root / "registries" / "publishing-adapters.json"
    value = load_json(path)
    validate(
        value,
        _load_schema(root, "publishing_adapter.schema.json"),
        schema_path=_schema_path(root, "publishing_adapter.schema.json"),
        root=root,
        location=str(path),
    )
    return value


def _adapter_entry(root: Path, adapter_id: str) -> dict[str, Any]:
    registry = _load_adapter_registry(root)
    for entry in registry["entries"]:
        if entry["id"] == adapter_id:
            return entry
    raise ValidationError(f"unknown publishing adapter: {adapter_id}")


def _load_fixture(root: Path, relative_or_name: str) -> dict[str, Any]:
    path = Path(relative_or_name)
    fixture_path = path if path.is_absolute() else root / relative_or_name
    if not fixture_path.is_file():
        candidate = _fixtures_dir(root) / relative_or_name
        if candidate.is_file():
            fixture_path = candidate
        else:
            raise ValidationError(f"content fixture not found: {relative_or_name}")
    value = load_json(fixture_path)
    validate(
        value,
        _load_schema(root, "content_fixture.schema.json"),
        schema_path=_schema_path(root, "content_fixture.schema.json"),
        root=root,
        location=str(fixture_path),
    )
    return value


def _load_item(root: Path, item_id: str) -> dict[str, Any]:
    path = _items_dir(root) / f"{item_id}.json"
    if not path.is_file():
        raise ValidationError(f"content item not found: {item_id}")
    value = load_json(path)
    validate(
        value,
        _load_schema(root, "content_item.schema.json"),
        schema_path=_schema_path(root, "content_item.schema.json"),
        root=root,
        location=str(path),
    )
    return value


def _write_item(root: Path, item: dict[str, Any]) -> Path:
    path = _items_dir(root) / f"{item['id']}.json"
    validate(
        item,
        _load_schema(root, "content_item.schema.json"),
        schema_path=_schema_path(root, "content_item.schema.json"),
        root=root,
        location=str(path),
    )
    _write_json(path, item)
    return path


def _select_validation_tier(adapter: dict[str, Any], flags: dict[str, bool]) -> str:
    validation = adapter["validation"]
    for trigger in validation.get("escalate_to_critical_on", []):
        if flags.get(trigger):
            return "CRITICAL"
    for trigger in validation.get("escalate_to_full_on", []):
        if flags.get(trigger):
            return "FULL"
    for trigger in validation.get("escalate_to_standard_on", []):
        if flags.get(trigger):
            return "STANDARD"
    return validation["default_tier"]


def _build_validation(adapter: dict[str, Any], *, flags: dict[str, bool], blockers: list[str]) -> dict[str, Any]:
    return {
        "tier": _select_validation_tier(adapter, flags),
        "checks": adapter["validation"]["checks"],
        "blockers": blockers,
        "warnings": adapter.get("warnings", []),
        "exception_flags": flags,
    }


def _status_from_blockers(blockers: list[str]) -> str:
    return "BLOCKED" if blockers else "PREPARED"


def _canonical_url(adapter: dict[str, Any], slug: str, locales: list[str]) -> tuple[str | None, dict[str, str]]:
    route = adapter.get("route_template")
    if not route:
        return None, {}
    hreflang: dict[str, str] = {}
    if "{locale}" in route:
        for locale in locales:
            hreflang[locale] = route.replace("{locale}", locale).replace("{slug}", slug)
        canonical = hreflang.get(locales[0]) if locales else None
    else:
        canonical = route.replace("{slug}", slug)
        for locale in locales:
            hreflang[locale] = canonical
    return canonical, hreflang


def _infer_entities(texts: list[str], tags: list[str], payload: dict[str, Any]) -> list[str]:
    explicit = [value for value in payload.get("entities", []) if isinstance(value, str) and value.strip()]
    if explicit:
        return explicit[:8]
    seen: list[str] = []
    for token in tags + re.findall(r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)?", " ".join(texts)):
        normalized = token.strip()
        if normalized and normalized not in seen:
            seen.append(normalized)
    return seen[:8]


def _context_enrichment(root: Path, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    request_ref = payload.get("context_request_ref")
    if not isinstance(request_ref, str) or not request_ref:
        return None, [], []
    try:
        request = load_context_request(root, (root / request_ref).resolve())
        pack = assemble_context_pack(root, request)
    except (OSError, ValueError, ValidationError) as exc:
        return None, [], [f"Optional Cortex enrichment unavailable: {exc}"]
    project_links = [project["id"] for project in pack.get("relevant_projects", []) if isinstance(project.get("id"), str)]
    proof_links = [asset["title"] if isinstance(asset, dict) and isinstance(asset.get("title"), str) else asset.get("id") for asset in pack.get("proof_assets", []) if isinstance(asset, dict)]
    related = [link for link in project_links + [item for item in proof_links if item] if isinstance(link, str)]
    return {
        "context_request_ref": request_ref,
        "providers": [provider["id"] for provider in pack.get("providers", []) if isinstance(provider, dict) and isinstance(provider.get("id"), str)],
        "related_project_candidates": project_links[:6],
        "proof_asset_candidates": [item for item in proof_links[:6] if isinstance(item, str)],
        "known_gaps": pack.get("known_gaps", []),
    }, related[:6], []


def _build_enrichment(root: Path, fixture: dict[str, Any], adapter: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    payload = fixture["payload"]
    body_lines = payload["body_lines"]
    summary = fixture["summary"]
    title = fixture["title"]
    slug = fixture["slug"] or _slugify(title)
    locales = fixture["locales"]
    canonical_path, hreflang = _canonical_url(adapter, slug, locales)
    first_line = body_lines[0] if body_lines else summary
    meta_description = _truncate_words(
        payload.get("social_description") or payload.get("excerpt") or _first_sentence(summary or first_line),
        165,
    )
    seo_title = _truncate_words(payload.get("seo_title") or title, 70)
    machine_summary = _truncate_words(payload.get("excerpt") or summary or _first_sentence(first_line), 240)
    cover_path = payload.get("cover_image")
    image_alt = payload.get("image_alt") or (f"{title} cover" if cover_path else None)
    cortex, related_from_cortex, cortex_warnings = _context_enrichment(root, payload)
    entities = _infer_entities([title, summary, *body_lines], payload.get("tags", []), payload)
    internal_links = [value for value in payload.get("internal_link_candidates", []) if isinstance(value, str)]
    if not internal_links and related_from_cortex:
        internal_links = [f"project:{value}" for value in related_from_cortex]
    return {
        "slug": slug,
        "seo_title": seo_title,
        "meta_description": meta_description,
        "canonical_path": canonical_path,
        "open_graph": {
            "title": seo_title,
            "description": _truncate_words(payload.get("social_description") or meta_description, 165),
            "image": cover_path,
            "image_alt": image_alt,
        },
        "social_preview": {
            "title": seo_title,
            "description": _truncate_words(payload.get("social_description") or meta_description, 165),
            "image": cover_path,
            "image_alt": image_alt,
        },
        "date_published": payload.get("date_published") or fixture["provenance"]["observed_at"][:10],
        "date_modified": now_iso()[:10],
        "author": payload.get("author") or adapter.get("default_author") or "Anton BV",
        "publisher": payload.get("publisher") or adapter.get("default_publisher") or fixture["project"],
        "tags": payload.get("tags", []),
        "topics": payload.get("topics", payload.get("tags", [])),
        "primary_entities": entities,
        "related_projects": [value for value in payload.get("related_projects", []) if isinstance(value, str)] or related_from_cortex,
        "internal_link_suggestions": internal_links[:8],
        "primary_source_links": payload.get("source_refs", []),
        "hreflang": hreflang,
        "sitemap_state": adapter.get("default_sitemap_state", "INDEXABLE"),
        "indexability": adapter.get("default_indexability", "INDEXABLE"),
        "structured_data": {
            "type": adapter.get("structured_data_type", "Article"),
            "status": "SUPPORTED",
        },
        "machine_summary": machine_summary,
        "cortex": cortex,
    }, cortex_warnings


class ProjectPublishingAdapter(Protocol):
    def prepare(self, root: Path, fixture: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any]: ...

    def build_publish_packet(self, root: Path, item: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class GenericPublishingAdapter:
    def prepare(self, root: Path, fixture: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any]:
        blockers = list(adapter.get("preparation_blockers", []))
        if adapter["readiness"] != "READY":
            blockers.append(adapter["readiness_reason"])
        if adapter.get("required_assets") and not fixture["payload"].get("asset_refs"):
            blockers.append("required assets are not attached to the fixture payload")
        flags = {key: bool(value) for key, value in fixture.get("validation_flags", {}).items()}
        enrichment, enrichment_warnings = _build_enrichment(root, fixture, adapter)
        item = {
            "schema_version": "v1",
            "id": fixture["id"],
            "project": fixture["project"],
            "surface": fixture["surface"],
            "kind": fixture["kind"],
            "title": fixture["title"],
            "slug": enrichment["slug"],
            "summary": fixture["summary"],
            "locales": fixture["locales"],
            "status": _status_from_blockers(blockers),
            "payload": fixture["payload"],
            "adapter": {
                "id": adapter["id"],
                "operation_id": adapter["operation_id"],
                "target_surface": adapter["target_surface"],
                "mechanism": adapter["mechanism"],
                "consumer_repo": adapter["consumer_repo"],
                "target": adapter["target"],
                "publish_strategy": adapter["publish_strategy"],
                "next_commands": adapter["next_commands"],
            },
            "consumer_operation": {
                "id": adapter["operation_id"],
                "target_surface": adapter["target_surface"],
                "dry_run_command": adapter["dry_run_command"],
                "apply_command": adapter["apply_command"],
            },
            "validation": _build_validation(adapter, flags=flags, blockers=blockers),
            "human_gate": {
                "required": True,
                "state": "BLOCKED" if blockers else "PENDING_APPROVAL",
                "approved_by": None,
                "approved_at": None,
            },
            "publication": {
                "mode": "REPORT_ONLY_HANDOFF",
                "packet_ref": None,
                "evidence_ref": None,
                "event_ref": None,
                "published_at": None,
                "result": None,
            },
            "enrichment": {
                **enrichment,
                "warnings": enrichment_warnings,
            },
            "artifact_refs": [],
            "history": [
                {
                    "action": "PREPARE",
                    "timestamp": now_iso(),
                    "actor": "abvx-content-ops",
                    "result": "BLOCKED" if blockers else "PREPARED",
                }
            ],
            "provenance": fixture["provenance"],
        }
        return item

    def build_publish_packet(self, root: Path, item: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "v1",
            "item_id": item["id"],
            "project": item["project"],
            "surface": item["surface"],
            "kind": item["kind"],
            "slug": item["slug"],
            "title": item["title"],
            "mode": "REPORT_ONLY_HANDOFF",
            "consumer_operation": item["consumer_operation"],
            "consumer_repo": adapter["consumer_repo"],
            "target": adapter["target"],
            "mechanism": adapter["mechanism"],
            "required_consumer_steps": adapter["next_commands"],
            "validation_checks": item["validation"]["checks"],
            "validation_tier": item["validation"]["tier"],
            "artifact_refs": item["payload"].get("asset_refs", []),
            "payload": item["payload"],
            "enrichment": item["enrichment"],
            "notes": adapter.get("notes", []),
            "generated_at": now_iso(),
        }


ADAPTER_IMPLEMENTATIONS: dict[str, ProjectPublishingAdapter] = {
    "consumer_command": GenericPublishingAdapter(),
    "playbook_handoff": GenericPublishingAdapter(),
    "future_surface": GenericPublishingAdapter(),
}


def _implementation(adapter: dict[str, Any]) -> ProjectPublishingAdapter:
    publish_strategy = adapter["publish_strategy"]
    if publish_strategy not in ADAPTER_IMPLEMENTATIONS:
        raise ValidationError(f"unsupported adapter publish strategy: {publish_strategy}")
    return ADAPTER_IMPLEMENTATIONS[publish_strategy]


def prepare_content_item(root: Path, fixture_ref: str) -> dict[str, Any]:
    fixture = _load_fixture(root, fixture_ref)
    adapter = _adapter_entry(root, fixture["adapter_id"])
    item = _implementation(adapter).prepare(root, fixture, adapter)
    _write_item(root, item)
    return item


def inspect_content_item(root: Path, item_id: str) -> dict[str, Any]:
    return _load_item(root, item_id)


def approve_content_item(root: Path, item_id: str, *, actor: str = "owner") -> dict[str, Any]:
    item = _load_item(root, item_id)
    if item["status"] == "BLOCKED":
        raise ValidationError(f"content item is blocked: {item_id}")
    if item["status"] not in {"PREPARED", "APPROVED", "PUBLISH_PACKET_EMITTED"}:
        raise ValidationError(f"content item cannot be approved from {item['status']}")
    item["status"] = "APPROVED"
    item["human_gate"] = {
        "required": True,
        "state": "APPROVED",
        "approved_by": actor,
        "approved_at": now_iso(),
    }
    item["history"].append({
        "action": "APPROVE",
        "timestamp": now_iso(),
        "actor": actor,
        "result": "APPROVED",
    })
    _write_item(root, item)
    return item


def publish_content_item(root: Path, item_id: str) -> dict[str, Any]:
    item = _load_item(root, item_id)
    if item["status"] != "APPROVED":
        raise ValidationError(f"content item must be APPROVED before publish: {item_id}")
    adapter = _adapter_entry(root, item["adapter"]["id"])
    if adapter["readiness"] != "READY":
        raise ValidationError(f"publishing adapter is not ready: {adapter['id']}")
    packet = _implementation(adapter).build_publish_packet(root, item, adapter)
    packet_path = _packets_dir(root) / f"{item_id}.json"
    _write_json(packet_path, packet)
    evidence = {
        "id": f"{item_id}-publish-handoff",
        "source": "abvx-content-ops",
        "timestamp": now_iso(),
        "candidate": item["adapter"]["id"],
        "fixture": item_id,
        "result": "CONDITIONAL_PASS",
        "metrics": {
            "execution_mode": "DEEP",
            "validation_tier": item["validation"]["tier"],
            "publish_mode": "REPORT_ONLY_HANDOFF",
            "reasoning_steps": 1,
            "approx_agent_model_usage": "not_metered_locally",
            "consumer_operation": item["consumer_operation"]["id"],
            "enrichment_fields": sorted(
                [
                    "slug",
                    "seo_title",
                    "meta_description",
                    "canonical_path",
                    "open_graph",
                    "social_preview",
                    "date_published",
                    "date_modified",
                    "author",
                    "publisher",
                    "tags",
                    "topics",
                    "primary_entities",
                    "related_projects",
                    "internal_link_suggestions",
                    "primary_source_links",
                    "hreflang",
                    "sitemap_state",
                    "indexability",
                    "structured_data",
                    "machine_summary",
                ]
            ),
        },
        "stdout_ref": "internal:none",
        "stderr_ref": "internal:none",
        "artifact_refs": [str(packet_path.relative_to(root)), *item["payload"].get("asset_refs", [])],
        "provenance": {
            "recorded_by": "CONTENT-OPS-002",
            "source_uri": None,
            "observed_at": now_iso(),
        },
        "environment": {
            "repository_path": str(root),
            "consumer_repo": item["adapter"]["consumer_repo"],
            "publish_strategy": item["adapter"]["publish_strategy"],
            "external_mutation_performed": False,
        },
    }
    evidence_path = _evidence_dir(root) / f"{item_id}.publish.evidence.json"
    validate(
        evidence,
        _load_schema(root, "evidence_record.schema.json"),
        schema_path=_schema_path(root, "evidence_record.schema.json"),
        root=root,
        location=str(evidence_path),
    )
    _write_json(evidence_path, evidence)
    event = {
        "schema_version": "v1",
        "id": f"{item['project']}-content_published-{item['slug']}",
        "type": "CONTENT_PUBLISHED",
        "project": item["project"],
        "object": {
            "kind": item["kind"],
            "id": item["slug"],
            "locator": f"{item['surface']}:{item['slug']}",
        },
        "timestamp": now_iso(),
        "origin": "HUMAN_INITIATED",
        "result": "CONDITIONAL_PASS",
        "execution_mode": "DEEP",
        "validation_tier": item["validation"]["tier"],
        "portfolio_effect": "NONE",
        "artifact_refs": [str(packet_path.relative_to(root)), *item["payload"].get("asset_refs", [])],
        "evidence_ref": str(evidence_path.relative_to(root)),
        "media_event_candidate": item["payload"].get("media_event_candidate"),
        "provenance": {
            "recorded_by": "CONTENT-OPS-002",
            "source_uri": None,
            "observed_at": now_iso(),
        },
    }
    event_path = _events_dir(root, item["project"]) / f"content_published-{item['slug']}.json"
    validate(
        event,
        _load_schema(root, "project_event.schema.json"),
        schema_path=_schema_path(root, "project_event.schema.json"),
        root=root,
        location=str(event_path),
    )
    _write_json(event_path, event)
    item["status"] = "PUBLISH_PACKET_EMITTED"
    item["publication"] = {
        "mode": "REPORT_ONLY_HANDOFF",
        "packet_ref": str(packet_path.relative_to(root)),
        "evidence_ref": str(evidence_path.relative_to(root)),
        "event_ref": str(event_path.relative_to(root)),
        "published_at": now_iso(),
        "result": "CONDITIONAL_PASS",
    }
    item["artifact_refs"] = sorted(set([*item["artifact_refs"], str(packet_path.relative_to(root))]))
    item["history"].append({
        "action": "PUBLISH",
        "timestamp": now_iso(),
        "actor": "abvx-content-ops",
        "result": "PUBLISH_PACKET_EMITTED",
    })
    _write_item(root, item)
    return {
        "status": "PASS",
        "item_id": item_id,
        "packet_path": str(packet_path.relative_to(root)),
        "evidence_path": str(evidence_path.relative_to(root)),
        "event_path": str(event_path.relative_to(root)),
        "result": "CONDITIONAL_PASS",
    }
