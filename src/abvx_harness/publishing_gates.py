"""Small, fail-closed publishing gate model independent from Book Radar scoring."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

PRODUCT_CONTRACT_FIELDS = (
    "buyer", "buyer_job", "prior_knowledge", "confusions", "better_or_faster",
    "paid_value", "specific_advantage", "intentionally_not",
)
RELEASE_GATES = (
    "market", "product_thesis", "representative_product", "factual_source",
    "language", "editorial", "product_quality", "technical", "toc_navigation",
    "commercial_package", "kdp_external_preview",
)
COMMERCIAL_PACKAGE_FIELDS = (
    "title", "subtitle", "author", "description", "keywords", "categories",
    "paperback_price", "kindle_price", "primary_marketplace", "format_settings",
    "cover_brief", "content_version", "commercial_package_content_version",
)
HUMAN_TASTE_TRIGGERS = {
    "novel_format", "layout_dependent", "visual_differentiation",
    "prior_knowledge_dependent", "first_in_product_class", "low_automated_quality_confidence",
}
DATA_DRIVEN_CLASSES = {"EXAM_PREP", "PUBLIC_DOMAIN_TRANSFORMATION", "VISUAL_REFERENCE", "COMPARISON_GUIDE"}

def validate_product_contract(contract: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in PRODUCT_CONTRACT_FIELDS if not contract.get(key)]
    transformation = contract.get("raw_data_transformation")
    if contract.get("dataset_driven") or contract.get("product_class") in DATA_DRIVEN_CLASSES:
        if not transformation or not all(transformation.get(k) for k in ("raw_source", "transformation", "buyer_value")):
            missing.append("raw_data_transformation.raw_source/transformation/buyer_value")
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}

def representative_product_requirement(contract: dict[str, Any], triggers: list[str]) -> dict[str, Any]:
    active = sorted(set(triggers) & HUMAN_TASTE_TRIGGERS)
    profile_requires = contract.get("product_class") in {"VISUAL_REFERENCE", "WORKBOOK", "ACTIVITY_BOOK", "COMPARISON_GUIDE"}
    required = profile_requires or bool(active)
    return {"required": required, "human_product_gate_required": bool(active), "triggers": active,
            "sample_range_pages": [6, 16] if required else None}

def record_human_product_gate(record: dict[str, Any], *, result: str, finding: str, reviewed_at: str | None = None) -> dict[str, Any]:
    if result not in {"PASS", "FAIL"}: raise ValueError("human product gate result must be PASS or FAIL")
    updated = deepcopy(record); history = updated.setdefault("human_product_gate_history", [])
    history.append({"sequence": len(history)+1, "result": result, "finding": finding,
                    "reviewed_at": reviewed_at or datetime.now(timezone.utc).date().isoformat()})
    updated["representative_product"] = result
    if result == "FAIL": updated["full_production"] = "BLOCKED"
    return updated

def validate_commercial_package(package: dict[str, Any]) -> dict[str, Any]:
    """Fail closed on the copy/paste fields needed to reach a human KDP upload gate."""
    missing = [key for key in COMMERCIAL_PACKAGE_FIELDS if not package.get(key)]
    if package.get("keywords") and len(package["keywords"]) != 7:
        missing.append("keywords.exactly_7")
    if package.get("categories") and len(package["categories"]) != 3:
        missing.append("categories.exactly_3")
    for key in ("paperback_price", "kindle_price"):
        value = package.get(key)
        if value is not None and (not isinstance(value, (int, float)) or value <= 0):
            missing.append(f"{key}.positive_number")
    if package.get("content_version") != package.get("commercial_package_content_version"):
        missing.append("content_version.match")
    if package.get("open_content_or_layout_correction_gates") != 0:
        missing.append("open_content_or_layout_correction_gates.zero")
    return {"status": "PASS" if not missing else "FAIL", "missing": sorted(set(missing))}

def release_authorization(gates: dict[str, str], mandatory: list[str] | None = None) -> dict[str, Any]:
    required = mandatory or list(RELEASE_GATES); failures=[]
    for gate in required:
        state=gates.get(gate)
        allowed={"PASS"}
        if gate=="representative_product": allowed.add("WAIVED")
        if gate=="language": allowed.add("WAIVED")
        if gate=="kdp_external_preview": allowed.add("HUMAN_PENDING")
        if state not in allowed: failures.append({"gate":gate,"state":state or "MISSING"})
    return {"status":"KDP_READY" if not failures else "PRODUCTION_BLOCKED","failures":failures}
