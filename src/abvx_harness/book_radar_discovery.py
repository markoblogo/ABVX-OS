from __future__ import annotations

from datetime import date
from typing import Any

from .harness import ValidationError


DECISION_STATES = {
    "REJECTED_ON_EVIDENCE",
    "INSUFFICIENT_EVIDENCE",
    "ATTRACTIVE_BUT_NOT_FOR_US",
    "READY_FOR_VALIDATION",
}
EVIDENCE_DIMENSIONS = (
    "problem_evidence",
    "spending_evidence",
    "book_format_demand",
    "competitive_gap",
    "reachability",
    "delivery_fit",
)
EVIDENCE_STATUSES = {"SUPPORTED", "NEGATIVE", "UNKNOWN"}
REQUIRED_SITUATION_FIELDS = (
    "buyer",
    "payer",
    "purchase_trigger",
    "job_to_be_done",
    "deadline",
    "current_solution",
    "current_spend",
    "unmet_need",
    "publishing_format_fit",
    "discovery_channel",
)

BOOK_DEMAND_EVIDENCE_TYPES = {
    "OBSERVED_FORMAT_PURCHASES",
    "CURRENT_BOOK_TRACTION_PROXY",
    "EXPLICIT_BOOK_REQUEST",
    "LISTING_ONLY",
    "TREND_ONLY",
    "SERVICE_SPEND_ONLY",
    "NONE",
}
BOOK_DEMAND_STRENGTHS = {"STRONG", "MODERATE", "WEAK", "UNKNOWN", "NEGATIVE"}
ASSET_FIT_STATUSES = {"PACKAGING_AUDIT", "SCENARIO_ADAPTATION", "NEW_CONTENT_REQUIRED", "NO_FIT"}
TRIGGER_CONFIDENCE = {"CONFIRMED", "LIKELY", "SPECULATIVE", "NONE"}
NEXT_DECISIONS = {
    "VALIDATE_NEW_BOOK",
    "AUDIT_EXISTING_PACKAGING",
    "MONITOR_TRIGGER",
    "COLLECT_VISIBILITY_DATA",
    "STOP",
    "INSUFFICIENT_EVIDENCE",
}
REQUIRED_BOOK_BUYING_FIELDS = (
    "discovery_source",
    "book_demand_evidence",
    "discovery_path",
    "unmet_scenario",
    "external_trigger",
    "demand_window",
    "existing_asset_fit",
    "uncertainties",
    "next_decision",
)


def validate_buyer_situation(candidate: dict[str, Any]) -> None:
    """Validate the evidence-first Book Radar search unit."""
    missing = [field for field in REQUIRED_SITUATION_FIELDS if not candidate.get(field)]
    if missing:
        raise ValidationError(f"buyer situation missing fields: {missing}")
    dimensions = candidate.get("evidence_dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(EVIDENCE_DIMENSIONS):
        raise ValidationError(f"evidence_dimensions must contain exactly {list(EVIDENCE_DIMENSIONS)}")
    for name, evidence in dimensions.items():
        if evidence.get("status") not in EVIDENCE_STATUSES:
            raise ValidationError(f"{name} has invalid evidence status")
        if not isinstance(evidence.get("source_ids"), list):
            raise ValidationError(f"{name} source_ids must be an array")
        if evidence["status"] != "UNKNOWN" and not evidence["source_ids"]:
            raise ValidationError(f"{name} requires source evidence for {evidence['status']}")
    if candidate.get("decision_state") not in DECISION_STATES:
        raise ValidationError("invalid decision_state")


def recommend_decision(
    evidence_statuses: dict[str, str],
    *,
    outside_delivery_boundary: bool = False,
) -> str:
    """Map evidence to a state without confusing missing and negative evidence.

    Strong competitors and free alternatives affect the competitive-gap evidence;
    neither is an automatic rejection on its own.
    """
    if set(evidence_statuses) != set(EVIDENCE_DIMENSIONS):
        raise ValidationError(f"statuses must contain exactly {list(EVIDENCE_DIMENSIONS)}")
    if any(value not in EVIDENCE_STATUSES for value in evidence_statuses.values()):
        raise ValidationError("invalid evidence status")
    if evidence_statuses["problem_evidence"] == "NEGATIVE":
        return "REJECTED_ON_EVIDENCE"
    if outside_delivery_boundary and evidence_statuses["problem_evidence"] == "SUPPORTED":
        return "ATTRACTIVE_BUT_NOT_FOR_US"
    if evidence_statuses["competitive_gap"] == "NEGATIVE":
        return "REJECTED_ON_EVIDENCE"
    if evidence_statuses["delivery_fit"] == "NEGATIVE":
        return "ATTRACTIVE_BUT_NOT_FOR_US"
    if any(value == "UNKNOWN" for value in evidence_statuses.values()):
        return "INSUFFICIENT_EVIDENCE"
    return "READY_FOR_VALIDATION"


def independent_publishers(source_records: list[dict[str, Any]]) -> int:
    """Count independent publishers, not pages or URLs from the same seller."""
    return len({record["publisher"].strip().casefold() for record in source_records if record.get("publisher")})


def validate_book_buying_situation(candidate: dict[str, Any]) -> None:
    """Validate the book-demand-first discovery extension without breaking v3 records."""
    validate_buyer_situation(candidate)
    missing = [field for field in REQUIRED_BOOK_BUYING_FIELDS if candidate.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"book-buying situation missing fields: {missing}")

    demand = candidate["book_demand_evidence"]
    if demand.get("type") not in BOOK_DEMAND_EVIDENCE_TYPES:
        raise ValidationError("invalid book demand evidence type")
    if demand.get("strength") not in BOOK_DEMAND_STRENGTHS:
        raise ValidationError("invalid book demand evidence strength")
    if not isinstance(demand.get("source_ids"), list):
        raise ValidationError("book demand evidence source_ids must be an array")
    if demand["strength"] not in {"UNKNOWN", "NEGATIVE"} and not demand["source_ids"]:
        raise ValidationError("positive book demand evidence requires sources")

    trigger = candidate["external_trigger"]
    if trigger.get("confidence") not in TRIGGER_CONFIDENCE:
        raise ValidationError("invalid external trigger confidence")
    if not isinstance(trigger.get("source_ids"), list):
        raise ValidationError("external trigger source_ids must be an array")

    asset = candidate["existing_asset_fit"]
    if asset.get("status") not in ASSET_FIT_STATUSES or not asset.get("reason"):
        raise ValidationError("invalid existing asset fit")
    if not isinstance(candidate["uncertainties"], list):
        raise ValidationError("uncertainties must be an array")
    if candidate["next_decision"] not in NEXT_DECISIONS:
        raise ValidationError("invalid next decision")

    window = candidate["demand_window"]
    if not isinstance(window.get("preparation_days"), int) or window["preparation_days"] < 0:
        raise ValidationError("demand window requires non-negative preparation_days")
    for field in ("opens", "closes"):
        if window.get(field):
            date.fromisoformat(window[field])


def book_demand_supported(evidence: dict[str, Any]) -> bool:
    """A topic trend, service spend, or listing alone is not evidence that this book is bought."""
    return (
        evidence.get("type")
        in {"OBSERVED_FORMAT_PURCHASES", "CURRENT_BOOK_TRACTION_PROXY", "EXPLICIT_BOOK_REQUEST"}
        and evidence.get("strength") in {"STRONG", "MODERATE"}
        and bool(evidence.get("source_ids"))
    )


def rights_ready(*, original_public_domain: bool, translation_rights: str) -> bool:
    """Public-domain source status never silently grants rights to a translation."""
    return original_public_domain and translation_rights in {"PUBLIC_DOMAIN", "LICENSED", "ORIGINAL_TRANSLATION"}


def diagnose_zero_sales(*, sales: int, impressions: int | None, live_verified: bool) -> str:
    """Separate availability/visibility failure from observed conversion."""
    if not live_verified:
        return "PUBLIC_AVAILABILITY_UNVERIFIED"
    if sales == 0 and impressions is None:
        return "INSUFFICIENT_VISIBILITY_DATA"
    if sales == 0 and impressions == 0:
        return "NO_OBSERVED_VISIBILITY"
    if sales == 0:
        return "ZERO_CONVERSION_IN_OBSERVED_TRAFFIC"
    return "SALES_OBSERVED"


def demand_window_viable(window: dict[str, Any], *, as_of: date) -> bool:
    """Reject a temporary opportunity when preparation finishes after its demand window."""
    closes = date.fromisoformat(window["closes"]) if window.get("closes") else None
    if closes is None:
        return True
    return (closes - as_of).days > window["preparation_days"]


def eligible_for_new_book(candidate: dict[str, Any], *, as_of: date) -> bool:
    """Assets and small-market labels cannot override weak demand or a missed window."""
    validate_book_buying_situation(candidate)
    return book_demand_supported(candidate["book_demand_evidence"]) and demand_window_viable(
        candidate["demand_window"], as_of=as_of
    )
