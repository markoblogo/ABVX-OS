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


# v5 is opt-in: historical v3/v4 cards and decisions retain their meaning.
BOOK_MARKETS = {
    "FICTION", "BUSINESS", "POPULAR_NONFICTION", "HOBBY",
    "CHILDREN_EDUCATION", "GIFT_VISUAL", "PRACTICAL_REFERENCE",
}
COMMERCIAL_TIERS = {"UNKNOWN": 0, "WEAK": 1, "MODERATE": 2, "STRONG": 3}
PRODUCTION_EFFORT = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
COMMERCIAL_CLAIMS = ("book_demand", "reader_choice", "reachability", "unit_economics")


def validate_commercial_candidate(card: dict[str, Any]) -> None:
    """Validate reader value, not a mandatory functional problem or market gap."""
    required = (
        "id", "market", "buyer", "reading_motivation", "reader_promise",
        "book_format", "discovery_path", "claims", "observations",
        "commercial_tier", "commercial_rationale", "production_effort",
        "production_plan", "quality_gate", "rights_status", "delivery_status",
        "demand_window",
    )
    if any(card.get(field) in (None, "", []) for field in required):
        raise ValidationError("commercial candidate missing required fields")
    if card["market"] not in BOOK_MARKETS:
        raise ValidationError("invalid book market")
    if card["commercial_tier"] not in COMMERCIAL_TIERS:
        raise ValidationError("invalid commercial tier")
    if card["production_effort"] not in PRODUCTION_EFFORT:
        raise ValidationError("invalid production effort")
    if card["rights_status"] not in {"CLEAR", "BLOCKED", "UNKNOWN"}:
        raise ValidationError("invalid rights status")
    if card["delivery_status"] not in {"FEASIBLE", "INFEASIBLE", "UNKNOWN"}:
        raise ValidationError("invalid delivery status")
    if set(card["claims"]) != set(COMMERCIAL_CLAIMS):
        raise ValidationError("commercial claims must cover demand, choice, reachability and economics")
    sources = {}
    for obs in card["observations"]:
        for field in ("source_id", "independence_key", "observed_at", "observation",
                      "interpretation", "alternative_explanation", "evidence_kind"):
            if not obs.get(field):
                raise ValidationError(f"commercial observation missing {field}")
        date.fromisoformat(obs["observed_at"])
        if obs["source_id"] in sources:
            raise ValidationError("duplicate commercial source id")
        if obs["evidence_kind"] not in {
            "PURCHASE", "TRACTION_PROXY", "READER_REQUEST", "LISTING", "TREND", "COST"
        }:
            raise ValidationError("invalid commercial evidence kind")
        sources[obs["source_id"]] = obs
    for claim in card["claims"].values():
        if claim.get("status") not in EVIDENCE_STATUSES or not claim.get("rationale"):
            raise ValidationError("commercial claim requires status and rationale")
        ids = claim.get("source_ids")
        if not isinstance(ids, list) or any(source not in sources for source in ids):
            raise ValidationError("commercial claim has unresolved sources")
        if claim["status"] != "UNKNOWN" and not ids:
            raise ValidationError("commercial claim requires evidence")
    window = card["demand_window"]
    days = window.get("preparation_days")
    if type(days) is not int or days < 0:
        raise ValidationError("commercial window requires preparation_days")
    if window.get("closes"):
        date.fromisoformat(window["closes"])


def commercial_discovery_decision(card: dict[str, Any], *, as_of: date) -> str:
    """Commercial evidence first; no novelty, unmet-task or utility-book requirement."""
    validate_commercial_candidate(card)
    claims = card["claims"]
    if card["rights_status"] == "BLOCKED" or any(
        claim["status"] == "NEGATIVE" for claim in claims.values()
    ):
        return "REJECTED_ON_EVIDENCE"
    if card["rights_status"] == "UNKNOWN" or any(
        claim["status"] == "UNKNOWN" for claim in claims.values()
    ):
        return "INSUFFICIENT_EVIDENCE"
    sources = {obs["source_id"]: obs for obs in card["observations"]}
    demand_origins = {
        sources[source]["independence_key"].strip().casefold()
        for source in claims["book_demand"]["source_ids"]
        if sources[source]["evidence_kind"] in {"PURCHASE", "TRACTION_PROXY"}
    }
    if len(demand_origins) < 2 or COMMERCIAL_TIERS[card["commercial_tier"]] < 2:
        return "INSUFFICIENT_EVIDENCE"
    if card["delivery_status"] == "INFEASIBLE" or not demand_window_viable(
        card["demand_window"], as_of=as_of
    ):
        return "ATTRACTIVE_BUT_NOT_FOR_US"
    if card["delivery_status"] == "UNKNOWN":
        return "INSUFFICIENT_EVIDENCE"
    return "DEEP_SCAN_ELIGIBLE"


def rank_commercial_candidates(cards: list[dict[str, Any]], *, as_of: date) -> list[dict[str, Any]]:
    """Rank only eligible cards: commercial tier first, effort second, stable ties.

    Tiers are documented research judgments, not estimated sales or probabilities.
    This does not authorize production or modify historical portfolio scoring.
    """
    eligible = [card for card in cards if commercial_discovery_decision(card, as_of=as_of)
                == "DEEP_SCAN_ELIGIBLE"]
    return sorted(eligible, key=lambda card: (
        -COMMERCIAL_TIERS[card["commercial_tier"]],
        PRODUCTION_EFFORT[card["production_effort"]],
    ))


def validate_listing_pattern_scan(scan: dict[str, Any]) -> None:
    """Validate a current-market packaging scan without treating correlation as causation."""
    required = (
        "id", "market", "observed_at", "source_url", "snapshot_type",
        "sampled_listings", "detail_checks", "observed_patterns",
        "package_contract", "limitations",
    )
    if any(scan.get(field) in (None, "", []) for field in required):
        raise ValidationError("listing pattern scan missing required fields")
    date.fromisoformat(scan["observed_at"])
    listings = scan["sampled_listings"]
    if len(listings) < 8:
        raise ValidationError("listing pattern scan requires at least eight ranked listings")
    ranks = set()
    asins = set()
    for item in listings:
        for field in ("rank", "asin", "title", "format", "rating_count"):
            if item.get(field) in (None, ""):
                raise ValidationError(f"sampled listing missing {field}")
        if type(item["rank"]) is not int or item["rank"] < 1:
            raise ValidationError("listing rank must be a positive integer")
        if type(item["rating_count"]) is not int or item["rating_count"] < 0:
            raise ValidationError("rating count must be a nonnegative integer")
        if item["rank"] in ranks or item["asin"] in asins:
            raise ValidationError("listing sample ranks and ASINs must be unique")
        ranks.add(item["rank"])
        asins.add(item["asin"])
    if len(scan["detail_checks"]) < 2:
        raise ValidationError("listing pattern scan requires at least two detail pages")
    for pattern in scan["observed_patterns"]:
        for field in ("id", "observation", "application", "evidence_basis", "causal_status"):
            if not pattern.get(field):
                raise ValidationError(f"listing pattern missing {field}")
        if pattern["causal_status"] != "CORRELATIONAL_ONLY":
            raise ValidationError("listing patterns may not be labeled causal")
    contract = scan["package_contract"]
    if not contract.get("required_fields") or contract.get("max_keyword_fields") != 7:
        raise ValidationError("listing package contract is incomplete")
    if contract.get("max_category_targets") != 3:
        raise ValidationError("listing package contract must respect the KDP category limit")


def validate_listing_package(package: dict[str, Any], scan: dict[str, Any]) -> None:
    """Check a proposed package against the market-scan contract before production."""
    validate_listing_pattern_scan(scan)
    contract = scan["package_contract"]
    for field in contract["required_fields"]:
        if package.get(field) in (None, "", []):
            raise ValidationError(f"listing package missing {field}")
    if len(package["keyword_fields"]) > contract["max_keyword_fields"]:
        raise ValidationError("listing package exceeds keyword-field limit")
    if len(package["category_targets"]) > contract["max_category_targets"]:
        raise ValidationError("listing package exceeds category-target limit")
    searchable = " ".join((package["title"], package["subtitle"], package["description"])).casefold()
    for required_term in contract.get("required_discovery_terms", []):
        if required_term.casefold() not in searchable:
            raise ValidationError(f"listing package missing discovery term: {required_term}")
