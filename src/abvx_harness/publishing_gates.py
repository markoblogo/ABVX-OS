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
    "pricing",
)
HUMAN_TASTE_TRIGGERS = {
    "novel_format", "layout_dependent", "visual_differentiation",
    "prior_knowledge_dependent", "first_in_product_class", "low_automated_quality_confidence",
}
DATA_DRIVEN_CLASSES = {"EXAM_PREP", "PUBLIC_DOMAIN_TRANSFORMATION", "VISUAL_REFERENCE", "COMPARISON_GUIDE"}
FORMAT_STATUSES = {"SUPPORTED", "UNSUPPORTED", "UNVERIFIED"}

def validate_callout_layout(record: dict[str, Any]) -> dict[str, Any]:
    """Keep collision safety and optical spacing as independent gates."""
    collision_failures = []
    optical_failures = []
    if int(record.get("overlap_count", -1)) != 0:
        collision_failures.append("overlap_count.zero")
    if float(record.get("internal_padding_pt", 0)) < 9:
        collision_failures.append("internal_padding_pt.minimum_9")
    for key, minimum in (("space_before_pt", 15), ("space_after_body_pt", 15), ("space_after_heading_pt", 18)):
        if float(record.get(key, 0)) < minimum:
            optical_failures.append(f"{key}.minimum_{minimum}")
    measured = record.get("measured", [])
    if not measured:
        optical_failures.append("measured.required")
    for item in measured:
        if float(item.get("before_gap_pt", 0)) < 15:
            optical_failures.append(f"{item.get('id','UNKNOWN')}.before_gap_pt.minimum_15")
        threshold = 18 if item.get("following_type") == "HEADING" else 15
        if float(item.get("after_gap_pt", 0)) < threshold:
            optical_failures.append(f"{item.get('id','UNKNOWN')}.after_gap_pt.minimum_{threshold}")
    return {
        "collision": {"status": "PASS" if not collision_failures else "FAIL", "failures": collision_failures},
        "optical_spacing": {"status": "PASS" if not optical_failures else "FAIL", "failures": sorted(set(optical_failures))},
    }

def validate_format_layout(record: dict[str, Any]) -> dict[str, Any]:
    """Fail closed on reusable workbook-format evidence and spacing constraints."""
    failures = []
    candidates = record.get("trim_candidates", [])
    selected = record.get("selected_trim")
    if len(candidates) < 2:
        failures.append("trim_candidates.at_least_2")
    if selected not in {c.get("trim") for c in candidates}:
        failures.append("selected_trim.in_candidates")
    callout_result = validate_callout_layout(record.get("callout_layout", {}))
    for gate, result in callout_result.items():
        failures.extend(f"callout_layout.{gate}.{item}" for item in result["failures"])
    forms = record.get("form_layout", {})
    if float(forms.get("short_row_min_pt", 0)) < 26:
        failures.append("form_layout.short_row_min_pt.minimum_26")
    if float(forms.get("long_row_min_pt", 0)) < 44:
        failures.append("form_layout.long_row_min_pt.minimum_44")
    if float(forms.get("three_column_answer_width_in", 0)) < 1.6:
        failures.append("form_layout.three_column_answer_width_in.minimum_1.6")
    if not forms.get("editorial_asymmetry"):
        failures.append("form_layout.editorial_asymmetry")
    if record.get("chapter_end_whitespace_signal_pages"):
        failures.append("chapter_end_whitespace_signal_pages.empty")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}

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
    pricing = package.get("pricing", {})
    price_formats = pricing.get("formats", {}) if isinstance(pricing, dict) else {}
    for fmt in formats:
        key = f"{fmt.lower()}_price"
        if not package.get(key):
            missing.append(key)
        if planned and eligibility.get(fmt) != "SUPPORTED":
            missing.append(f"format_eligibility_status.{fmt}.SUPPORTED")
        price = price_formats.get(fmt, {})
        required_price_fields = (
            "recommended_list_price", "currency", "primary_marketplace",
            "acceptable_test_range", "production_or_delivery_cost",
            "royalty_rate_tier", "estimated_royalty_per_sale",
            "pricing_rationale", "date_checked",
        )
        for field in required_price_fields:
            if price.get(field) is None or price.get(field) == "":
                missing.append(f"pricing.formats.{fmt}.{field}")
        if fmt == "PAPERBACK":
            for field in ("final_trim", "final_page_count", "ink", "paper", "final_printing_cost"):
                if price.get(field) is None or price.get(field) == "":
                    missing.append(f"pricing.formats.{fmt}.{field}")
            settings = package.get("format_settings", {})
            expected = {
                "final_trim": settings.get("trim"),
                "final_page_count": settings.get("kdp_rounded_page_count"),
                "ink": settings.get("ink"),
                "paper": settings.get("paper"),
            }
            for field, value in expected.items():
                if price.get(field) != value:
                    missing.append(f"pricing.formats.{fmt}.{field}.matches_final_format")
    for key in tuple(f"{fmt.lower()}_price" for fmt in formats):
        value = package.get(key)
        if value is not None and (not isinstance(value, (int, float)) or value <= 0):
            missing.append(f"{key}.positive_number")
    if package.get("content_version") != package.get("commercial_package_content_version"):
        missing.append("content_version.match")
    if pricing.get("price_status") != "FINAL":
        missing.append("pricing.price_status.FINAL")
    for version_field in ("final_price_version", "final_content_version", "final_layout_version"):
        if pricing.get(version_field) != package.get("content_version"):
            missing.append(f"pricing.{version_field}.matches_content_version")
    if package.get("open_content_or_layout_correction_gates") != 0:
        missing.append("open_content_or_layout_correction_gates.zero")
    dependency_mismatch = any("matches_final_format" in item or "matches_content_version" in item for item in missing)
    return {"status": "PASS" if not missing else "FAIL", "price_status": "RECALCULATION_REQUIRED" if dependency_mismatch else pricing.get("price_status", "MISSING"), "missing": sorted(set(missing))}

def validate_commercial_artifacts(package: dict[str, Any], artifacts: dict[str, str]) -> dict[str, Any]:
    """Require the final recommendation in every operational pricing artifact."""
    failures = []
    required = ("commercial_package", "metadata_card", "kdp_upload_card", "pricing_analysis", "book_radar_record")
    for name in required:
        if not artifacts.get(name):
            failures.append(f"artifacts.{name}.required")
    for fmt in package.get("planned_formats", []):
        price = package.get("pricing", {}).get("formats", {}).get(str(fmt).upper(), {}).get("recommended_list_price")
        if not isinstance(price, (int, float)):
            failures.append(f"pricing.formats.{str(fmt).upper()}.recommended_list_price")
            continue
        tokens = {f"{price:.2f}", f"${price:.2f}", str(price)}
        for name in required:
            text = artifacts.get(name, "")
            if text and not any(token in text for token in tokens):
                failures.append(f"artifacts.{name}.{str(fmt).upper()}.final_price")
    return {"status":"PASS" if not failures else "FAIL","failures":sorted(set(failures))}

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
