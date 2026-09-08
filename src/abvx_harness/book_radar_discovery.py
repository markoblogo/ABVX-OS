from __future__ import annotations

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
