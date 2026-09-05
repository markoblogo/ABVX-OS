from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .harness import ValidationError, load_json

STATE_VERSION = "book-radar-state/v1"
STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
COLLECTIONS = ("radar_runs", "opportunities", "evidence", "scores", "decisions", "products", "portfolio_products", "similarity_results", "launches", "actuals", "calibrations")
DEFAULT_MODEL = {
    "id": "radar-native-v1", "version": 1, "scale": {"minimum": 1, "maximum": 5},
    "weights": {"demand": 20, "momentum": 8, "competition_weakness": 10, "newcomer_viability": 8, "production_feasibility": 15, "shelf_life": 8, "economics": 12, "new_entrant_evidence": 10, "evidence_quality": 9},
    "penalties": ["paid_ads", "rights_trademark_compliance"],
    "hard_gates": ["observable_demand", "newcomer_path", "production_within_budget", "acceptable_rights_and_compliance_risk"],
    "formula": "weighted 1-5 score normalized to 100, minus declared penalties",
}


def empty_state() -> dict[str, Any]:
    return {"schema_version": STATE_VERSION, **{name: [] for name in COLLECTIONS}}


def _path(root: Path) -> Path:
    return root / "book-radar" / "state.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_state(root: Path) -> dict[str, Any]:
    path = _path(root)
    state = load_json(path) if path.is_file() else empty_state()
    # Backwards-conscious v1 extension: older state files gain empty collections.
    for collection in COLLECTIONS:
        state.setdefault(collection, [])
    validate_state(state)
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    validate_state(state)
    _write_json(_path(root), state)


def validate_state(state: dict[str, Any]) -> None:
    if state.get("schema_version") != STATE_VERSION:
        raise ValidationError(f"book radar state must use {STATE_VERSION}")
    ids: dict[str, set[str]] = {}
    for collection in COLLECTIONS:
        records = state.get(collection)
        if not isinstance(records, list):
            raise ValidationError(f"book radar {collection} must be an array")
        ids[collection] = set()
        for record in records:
            rid = record.get("id") if isinstance(record, dict) else None
            if not isinstance(rid, str) or not STABLE_ID.fullmatch(rid):
                raise ValidationError(f"invalid {collection} record id: {rid}")
            if rid in ids[collection]:
                raise ValidationError(f"duplicate {collection} id: {rid}")
            ids[collection].add(rid)
    for item in state["opportunities"]:
        _linked(item, "radar_run_id", ids["radar_runs"])
    for item in state["evidence"] + state["scores"] + state["decisions"]:
        _linked(item, "opportunity_id", ids["opportunities"])
    for item in state["products"]:
        _linked(item, "opportunity_id", ids["opportunities"])
    for item in state["launches"] + state["actuals"]:
        _linked(item, "product_id", ids["products"])
    for item in state["similarity_results"]:
        _linked(item, "opportunity_id", ids["opportunities"])
        _linked(item, "portfolio_product_id", ids["portfolio_products"])


def _linked(record: dict[str, Any], field: str, known: set[str]) -> None:
    value = record.get(field)
    if value is not None and value not in known:
        raise ValidationError(f"{record['id']}: unknown {field} {value}")


def register_scoring_model(root: Path, model: dict[str, Any]) -> Path:
    model_id = model.get("id")
    if not isinstance(model_id, str) or not STABLE_ID.fullmatch(model_id):
        raise ValidationError("scoring model requires a stable id")
    path = root / "book-radar" / "scoring-models" / f"{model_id}.json"
    if path.exists():
        if load_json(path) != model:
            raise ValidationError(f"scoring model {model_id} is immutable")
        return path
    _write_json(path, model)
    return path


def score_values(values: dict[str, Any], penalties: dict[str, Any], model: dict[str, Any]) -> float:
    weights = model["weights"]
    missing = sorted(set(weights) - set(values))
    if missing:
        raise ValidationError(f"missing score metrics: {missing}")
    for key in weights:
        if not 1 <= float(values[key]) <= 5:
            raise ValidationError(f"{key} must be between 1 and 5")
    weighted = sum(float(values[key]) * weight for key, weight in weights.items())
    penalty = sum(float(penalties.get(key, 0)) for key in model.get("penalties", []))
    return round((weighted / (model["scale"]["maximum"] * sum(weights.values()))) * 100 - penalty, 1)


def assess_portfolio_similarity(facets: dict[str, Any], weights: dict[str, Any], confidence: str = "HIGH") -> dict[str, Any]:
    """Score structured product-thesis dimensions; titles are intentionally excluded."""
    required = {"buyer", "jtbd", "trigger", "promise", "format", "information_architecture", "search_intent", "audience", "differentiation"}
    if set(facets) != required or set(weights) != required:
        raise ValidationError(f"portfolio similarity requires exactly {sorted(required)}")
    if sum(float(value) for value in weights.values()) != 100:
        raise ValidationError("portfolio similarity weights must sum to 100")
    for name, value in facets.items():
        if not 0 <= float(value) <= 100:
            raise ValidationError(f"similarity facet {name} must be between 0 and 100")
    score = round(sum(float(facets[key]) * float(weights[key]) for key in required) / 100, 1)
    core = (float(facets["buyer"]) + 2 * float(facets["jtbd"]) + 2 * float(facets["promise"]) + float(facets["trigger"])) / 6
    surface = (float(facets["format"]) + float(facets["search_intent"]) + float(facets["differentiation"])) / 3
    if score >= 75:
        classification = "EXISTING_PRODUCT_MATCH"
    elif core >= 72 and surface < 60:
        classification = "REPACKAGE_CANDIDATE"
    elif score >= 60:
        classification = "CANNIBALIZATION_RISK"
    elif score >= 35:
        classification = "ADJACENT"
    else:
        classification = "NOVEL"
    blocked = confidence == "HIGH" and classification in {"EXISTING_PRODUCT_MATCH", "REPACKAGE_CANDIDATE"}
    return {"overlap_score": score, "classification": classification, "confidence": confidence, "production_eligible": not blocked, "route": "EXISTING_PRODUCT_AUDIT" if blocked else "PRODUCTION_ELIGIBLE_WITH_WARNING" if classification in {"ADJACENT", "CANNIBALIZATION_RISK"} else "PRODUCTION_ELIGIBLE"}


def import_catalog(root: Path, source: Path) -> dict[str, Any]:
    payload = load_json(source)
    if payload.get("schema_version") != "book-radar-catalog/v1" or not isinstance(payload.get("portfolio_products"), list):
        raise ValidationError("catalog import must use book-radar-catalog/v1")
    state = load_state(root)
    added = _append_unique(state, "portfolio_products", payload["portfolio_products"])
    save_state(root, state)
    return {"status": "CATALOG_IMPORTED", "source": str(source), "added": added}


def _append_unique(state: dict[str, Any], collection: str, records: list[dict[str, Any]]) -> int:
    existing = {item["id"]: item for item in state[collection]}
    added = 0
    for record in records:
        prior = existing.get(record["id"])
        if prior is not None:
            if prior != record:
                raise ValidationError(f"{collection} {record['id']} already exists with different content")
            continue
        state[collection].append(record)
        existing[record["id"]] = record
        added += 1
    return added


def import_bundle(root: Path, source: Path) -> dict[str, Any]:
    payload = load_json(source)
    if payload.get("radar_run_id") and isinstance(payload.get("opportunities"), list):
        bundle, model = _adapt_radar_native_2(payload, source)
    elif payload.get("schema_version") == "book-radar-import/v1":
        bundle, model = payload, payload.get("scoring_model")
    else:
        raise ValidationError("unsupported Book Radar import format")
    if model:
        register_scoring_model(root, model)
    state = load_state(root)
    counts = {name: _append_unique(state, name, bundle.get(name, [])) for name in COLLECTIONS}
    save_state(root, state)
    return {"status": "IMPORTED", "source": str(source), "added": counts}


def _adapt_radar_native_2(payload: dict[str, Any], source: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    run_id, observed = payload["radar_run_id"], payload.get("research_date")
    method = payload["score_method"]
    model = {**DEFAULT_MODEL, "weights": method["weights"], "formula": method["formula"]}
    opportunities, evidence, scores, decisions = [], [], [], []
    for raw in payload["opportunities"]:
        oid = raw["id"]
        opportunities.append({"id": oid, "radar_run_id": run_id, "buyer_job": raw["buyer_job"], "query_cluster": raw["query_cluster"], "format": raw["format"], "price_band": raw["price_band"], "concept": raw["concept"], "group": raw.get("group"), "source": "radar-native-2"})
        evidence.append({"id": f"evidence:{oid}", "opportunity_id": oid, "observed_at": observed, "summary": raw.get("evidence", ""), "details": raw.get("detailed_evidence"), "source_ref": str(source)})
        calculated = score_values(raw["scores"], raw.get("penalties", {}), model)
        if calculated != float(raw["score"]):
            raise ValidationError(f"{oid}: stored score {raw['score']} != reproducible score {calculated}")
        scores.append({"id": f"score:{oid}:{model['id']}", "opportunity_id": oid, "scoring_model_id": model["id"], "metrics": raw["scores"], "penalties": raw.get("penalties", {}), "total": calculated})
        decisions.append({"id": f"decision:{oid}:screen", "opportunity_id": oid, "decision": raw["decision"], "reason": raw.get("rejection_reason"), "decided_at": observed})
    final = payload.get("final_decision", {})
    if final.get("winner_id"):
        decisions.append({"id": f"decision:{final['winner_id']}:final", "opportunity_id": final["winner_id"], "decision": "winner", "reason": final.get("winner"), "decided_at": observed, "production_authorized": bool(final.get("production_should_start"))})
    return ({"radar_runs": [{"id": run_id, "name": "Radar-Native Discovery #2", "observed_at": observed, "status": "DECIDED", "scoring_model_id": model["id"]}], "opportunities": opportunities, "evidence": evidence, "scores": scores, "decisions": decisions}, model)


def add_records(root: Path, collection: str, source: Path) -> dict[str, Any]:
    if collection not in COLLECTIONS:
        raise ValidationError(f"unknown Book Radar collection: {collection}")
    value = load_json(source)
    records = value if isinstance(value, list) else [value]
    state = load_state(root)
    added = _append_unique(state, collection, records)
    save_state(root, state)
    return {"status": "RECORDED", "collection": collection, "added": added}


def export_state(root: Path, destination: Path) -> dict[str, Any]:
    state = load_state(root)
    _write_json(destination, state)
    return {"status": "EXPORTED", "path": str(destination), "records": sum(len(state[name]) for name in COLLECTIONS)}


def report(root: Path, kind: str) -> dict[str, Any]:
    state = load_state(root)
    if kind == "pipeline":
        statuses: dict[str, int] = {}
        for product in state["products"]:
            status = product.get("status", "UNKNOWN")
            statuses[status] = statuses.get(status, 0) + 1
        return {"report": kind, "product_statuses": statuses, "products": state["products"]}
    if kind == "experiments":
        return {"report": kind, "experiments": [{**product, "actuals": [item for item in state["actuals"] if item["product_id"] == product["id"]]} for product in state["products"]]}
    if kind == "backlog":
        closed = {item["opportunity_id"] for item in state["decisions"] if item.get("decision") in {"winner", "reject", "reject_after_deep_scan"}}
        return {"report": kind, "opportunities": [item for item in state["opportunities"] if item["id"] not in closed]}
    raise ValidationError("report must be pipeline, experiments, or backlog")


def render_report(value: dict[str, Any]) -> str:
    if value["report"] == "pipeline":
        return "\n".join(["BOOK RADAR PIPELINE"] + [f"{key}: {count}" for key, count in sorted(value["product_statuses"].items())])
    if value["report"] == "experiments":
        return "\n".join(["BOOK RADAR EXPERIMENTS"] + [f"{item['id']} [{item.get('status', 'UNKNOWN')}] {item.get('title', '')} — actual snapshots: {len(item['actuals'])}" for item in value["experiments"]])
    return f"BOOK RADAR BACKLOG\nOpen opportunities: {len(value['opportunities'])}"
