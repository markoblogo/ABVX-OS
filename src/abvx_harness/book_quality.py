"""Reusable, advisory product-quality gate for visual/reference books."""

from __future__ import annotations

from typing import Any


DIMENSIONS = (
    "buyer_fit",
    "jtbd_delivery",
    "paid_value",
    "information_density",
    "perceived_value",
    "editorial_enrichment",
    "prior_knowledge_leverage",
    "format_fit",
    "repetition_template_fatigue",
    "page_purpose",
)


def assess_visual_reference_quality(payload: dict[str, Any]) -> dict[str, Any]:
    """Assess editorial product quality separately from technical preflight.

    Scores are human/evidence inputs on a 0-5 scale. Density flags are advisory:
    intentionally sparse title and section-opener pages are excluded.
    """
    scores = payload.get("scores", {})
    if set(scores) != set(DIMENSIONS):
        raise ValueError("all product-quality dimensions are required")
    if any(not isinstance(v, (int, float)) or not 0 <= v <= 5 for v in scores.values()):
        raise ValueError("product-quality scores must be numbers from 0 to 5")
    pages = payload.get("pages", [])
    flagged = []
    for page in pages:
        suspicious = (
            page.get("usable_area_fill", 1) < 0.5
            and page.get("text_amount", 1) < 0.35
            and page.get("visual_amount", 1) < 0.35
        ) or page.get("meaningful_information_units", 2) < 2 \
          or page.get("isolated_groupable_entry", False) \
          or page.get("repeated_template_sparsity", False)
        if suspicious and not page.get("intentional_sparse", False) and not page.get("density_exception_justification"):
            flagged.append(page["page"])
    average = round(sum(scores.values()) / len(DIMENSIONS), 2)
    passed = average >= 4 and min(scores.values()) >= 3 and not flagged
    return {
        "status": "PASS" if passed else "FAIL",
        "average": average,
        "scores": scores,
        "density_signal": {"flagged_pages": flagged, "advisory": True},
        "technical_preflight_independent": True,
    }
