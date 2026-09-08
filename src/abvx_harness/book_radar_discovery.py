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
EVIDENCE_CARD_FIELDS = (
    "buyer",
    "purchase_reason",
    "specific_task",
    "comparable_book_purchase_evidence",
    "unmet_scenario",
    "accessible_gap",
    "book_format",
    "format_reason",
    "discovery_query_or_channel",
    "observations",
    "source_independence",
    "freshness",
    "production_constraints",
    "main_uncertainty",
    "rights_status",
    "expertise_status",
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


def validate_evidence_card(card: dict[str, Any]) -> None:
    """Validate the short observation-first card used before concept formulation."""
    missing = [field for field in EVIDENCE_CARD_FIELDS if card.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"evidence card missing fields: {missing}")
    for field in ("comparable_book_purchase_evidence", "accessible_gap"):
        claim = card[field]
        if claim.get("status") not in EVIDENCE_STATUSES:
            raise ValidationError(f"{field} has invalid status")
        if not isinstance(claim.get("source_ids"), list):
            raise ValidationError(f"{field} source_ids must be an array")
        if claim["status"] != "UNKNOWN" and not claim["source_ids"]:
            raise ValidationError(f"{field} requires source evidence")
    if not isinstance(card["observations"], list) or not card["observations"]:
        raise ValidationError("evidence card requires observations")
    observation_fields = {
        "source_id",
        "independence_key",
        "observed_at",
        "observation",
        "interpretation",
        "alternative_explanation",
    }
    for observation in card["observations"]:
        missing_observation = [field for field in observation_fields if not observation.get(field)]
        if missing_observation:
            raise ValidationError(f"observation missing fields: {missing_observation}")
        date.fromisoformat(observation["observed_at"])
    independence = card["source_independence"]
    if not isinstance(independence.get("minimum_independent_sources"), int):
        raise ValidationError("source independence requires an integer threshold")
    if independence["minimum_independent_sources"] < 2 or not independence.get("rationale"):
        raise ValidationError("source independence requires at least two origins and a rationale")
    freshness = card["freshness"]
    date.fromisoformat(freshness["as_of"])
    if freshness.get("window_closes"):
        date.fromisoformat(freshness["window_closes"])
    if not isinstance(freshness.get("preparation_days"), int) or freshness["preparation_days"] < 0:
        raise ValidationError("freshness requires non-negative preparation_days")
    if not isinstance(card["production_constraints"], list):
        raise ValidationError("production_constraints must be an array")


def early_discovery_decision(card: dict[str, Any], *, as_of: date) -> str:
    """Apply purchase, scenario, gap, independence, rights, expertise, and time gates early."""
    validate_evidence_card(card)
    if card["rights_status"] != "CLEAR":
        return "REJECTED_ON_EVIDENCE"
    if card["expertise_status"] == "UNAVAILABLE":
        return "ATTRACTIVE_BUT_NOT_FOR_US"
    freshness = card["freshness"]
    if freshness.get("window_closes") and not demand_window_viable(
        {"closes": freshness["window_closes"], "preparation_days": freshness["preparation_days"]},
        as_of=as_of,
    ):
        return "REJECTED_ON_EVIDENCE"
    independent_origins = {item["independence_key"] for item in card["observations"]}
    if len(independent_origins) < card["source_independence"]["minimum_independent_sources"]:
        return "INSUFFICIENT_EVIDENCE"
    purchase = card["comparable_book_purchase_evidence"]
    if purchase["status"] != "SUPPORTED" or not purchase["source_ids"]:
        return "INSUFFICIENT_EVIDENCE"
    gap = card["accessible_gap"]
    if gap["status"] != "SUPPORTED" or not gap["source_ids"]:
        return "INSUFFICIENT_EVIDENCE"
    return "DEEP_SCAN_ELIGIBLE"
