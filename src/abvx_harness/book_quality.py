"""Reusable, advisory product-quality gate for visual/reference books."""

from __future__ import annotations

from typing import Any


DIMENSIONS = (
    "information_density",
    "perceived_value",
    "editorial_enrichment",
    "target_reader_advantage",
    "page_purpose",
    "learning_value",
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
    flagged = [
        p["page"] for p in pages
        if not p.get("intentional_sparse", False)
        and (p.get("usable_area_fill", 1) < 0.32 or p.get("isolated_groupable_entry", False))
    ]
    average = round(sum(scores.values()) / len(DIMENSIONS), 2)
    passed = average >= 4 and min(scores.values()) >= 3 and not flagged
    return {
        "status": "PASS" if passed else "FAIL",
        "average": average,
        "scores": scores,
        "density_signal": {"flagged_pages": flagged, "advisory": True},
        "technical_preflight_independent": True,
    }
