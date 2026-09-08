from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .harness import ValidationError, load_json, validate


def _load_registry(root: Path) -> list[dict[str, Any]]:
    registry_path = root / "registries" / "professional-roles.json"
    schema_path = root / "schemas" / "professional_roles.schema.json"
    registry = load_json(registry_path)
    validate(registry, load_json(schema_path), schema_path=schema_path, root=root, location=str(registry_path))
    entries = registry["entries"]
    defaults = [role for role in entries if role.get("default")]
    if len(defaults) != 1:
        raise ValidationError("professional role registry must define exactly one default role")
    return entries


def list_roles(root: Path) -> list[dict[str, Any]]:
    return _load_registry(root)


def inspect_role(root: Path, role_id: str) -> dict[str, Any]:
    for role in _load_registry(root):
        if role["id"] == role_id:
            return role
    raise ValidationError(f"unknown professional role: {role_id}")


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[\w+#.-]+", text.casefold(), flags=re.UNICODE))


def _score(role: dict[str, Any], normalized_text: str) -> tuple[int, list[str]]:
    padded = f" {normalized_text} "
    score = 0
    matched: list[str] = []
    for trigger in role["triggers"]:
        term = _normalize(trigger["term"])
        if term and f" {term} " in padded:
            score += trigger["weight"]
            matched.append(trigger["term"])
    return score, matched


def _routed_profile(role: dict[str, Any], score: int, matched: list[str]) -> dict[str, Any]:
    return {
        "id": role["id"],
        "name": role["name"],
        "score": score,
        "matched_triggers": matched,
        "purpose": role["purpose"],
        "default_mode": role["default_mode"],
        "context_scope": role["context_scope"],
        "boundaries": role["boundaries"],
    }


def route_role(root: Path, text: str) -> dict[str, Any]:
    if not text.strip():
        raise ValidationError("role routing text must not be empty")
    roles = _load_registry(root)
    ranked: list[tuple[int, int, dict[str, Any], list[str]]] = []
    normalized = _normalize(text)
    for role in roles:
        score, matched = _score(role, normalized)
        if score:
            ranked.append((score, role["priority"], role, matched))
    ranked.sort(key=lambda item: (item[0], item[1], item[2]["id"]), reverse=True)
    if ranked:
        primary = ranked[0]
        supporting = ranked[1:3]
        reason = "specialist triggers matched"
    else:
        role = next(role for role in roles if role.get("default"))
        primary = (0, role["priority"], role, [])
        supporting = []
        reason = "no specialist trigger matched; use the default coordinator"
    return {
        "schema_version": "professional-role-route/v1",
        "primary_role": _routed_profile(primary[2], primary[0], primary[3]),
        "supporting_roles": [_routed_profile(role, score, matched) for score, _, role, matched in supporting],
        "authority_effect": "none",
        "routing_reason": reason,
        "next_step": "Load only the selected role profile and task-specific evidence before acting.",
    }
