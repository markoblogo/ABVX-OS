"""Small, fail-closed publishing gate model independent from Book Radar scoring."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

PRODUCT_CONTRACT_FIELDS = (
    "buyer", "buyer_job", "prior_knowledge", "confusions", "better_or_faster",
    "paid_value", "specific_advantage", "intentionally_not", "primary_format",
    "secondary_formats", "format_eligibility_status", "format_specific_commercial_role",
)
RELEASE_GATES = (
    "market", "product_thesis", "representative_product", "factual_source",
    "language", "editorial", "product_quality", "technical", "toc_navigation",
    "commercial_package", "kdp_external_preview",
)
COMMERCIAL_PACKAGE_FIELDS = (
    "title", "subtitle", "author", "description", "keywords", "categories",
    "primary_marketplace", "format_settings",
    "cover_brief", "content_version", "commercial_package_content_version",
)
HUMAN_TASTE_TRIGGERS = {
    "novel_format", "layout_dependent", "visual_differentiation",
    "prior_knowledge_dependent", "first_in_product_class", "low_automated_quality_confidence",
}
DATA_DRIVEN_CLASSES = {"EXAM_PREP", "PUBLIC_DOMAIN_TRANSFORMATION", "VISUAL_REFERENCE", "COMPARISON_GUIDE"}
FORMAT_STATUSES = {"SUPPORTED", "UNSUPPORTED", "UNVERIFIED"}

def assess_format_eligibility(*, language: str, marketplace: str, formats: list[str], support_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve KDP format support from dated records; unknown combinations fail closed."""
    resolved: dict[str, Any] = {}
    for requested in formats:
        fmt = requested.upper()
        matches = [r for r in support_records if r.get("platform", "KDP").upper() == "KDP"
                   and str(r.get("language", "")).upper() == language.upper()
                   and str(r.get("format", "")).upper() == fmt
                   and r.get("marketplace") in {marketplace, "ALL"}]
        record = matches[-1] if matches else {}
        status = record.get("status", "UNVERIFIED")
        if status not in FORMAT_STATUSES:
            status = "UNVERIFIED"
        resolved[fmt] = {
            "status": status,
            "production_allowed": status == "SUPPORTED",
            "source": record.get("source"),
            "checked_at": record.get("checked_at"),
            "confidence": record.get("confidence", "NONE"),
        }
    return {"language": language.upper(), "marketplace": marketplace, "formats": resolved,
            "status": "PASS" if resolved and all(v["production_allowed"] for v in resolved.values()) else "FAIL"}

def audit_no_bleed_objects(objects: list[dict[str, Any]], *, page_width: float, page_height: float, safe_inset: float) -> dict[str, Any]:
    """Catch generator-owned vector/image objects that a text-bbox audit cannot see."""
    failures = []
    for obj in objects:
        bbox = obj.get("bbox", [])
        valid = len(bbox) == 4 and bbox[0] >= safe_inset and bbox[1] >= safe_inset and bbox[2] <= page_width-safe_inset and bbox[3] <= page_height-safe_inset
        if not valid:
            failures.append({"id": obj.get("id", "UNKNOWN"), "bbox": bbox})
    return {"status": "PASS" if not failures else "FAIL", "failures": failures,
            "objects_checked": len(objects), "safe_inset": safe_inset}

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
    planned = package.get("planned_formats")
    formats = [str(v).upper() for v in planned] if planned else ["PAPERBACK", "KINDLE"]
    eligibility = package.get("format_eligibility_status", {})
    for fmt in formats:
        key = f"{fmt.lower()}_price"
        if not package.get(key):
            missing.append(key)
        if planned and eligibility.get(fmt) != "SUPPORTED":
            missing.append(f"format_eligibility_status.{fmt}.SUPPORTED")
    for key in tuple(f"{fmt.lower()}_price" for fmt in formats):
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
