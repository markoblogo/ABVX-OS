from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .harness import load_json


def _today(value: str | None) -> str:
    return value or date.today().isoformat()


def _eligible_human_item(item: dict[str, Any], today: str) -> bool:
    not_before = item.get("not_before")
    return item.get("status") == "WAITING" and (not not_before or not_before <= today)


def inspect_portfolio(root: Path, today: str | None = None) -> dict[str, Any]:
    observed = _today(today)
    state = load_json(root / "portfolio" / "state.json")
    strategy = load_json(root / "portfolio" / "strategy.json")
    queue = load_json(root / "portfolio" / "human-queue.json")
    entries = state["entries"]
    display_names = {entry["project"]: entry["display_name"] for entry in strategy["entries"]}
    actionable = [
        {**entry, "recommendation": "ACTIONABLE"}
        for entry in entries
        if entry["operational_state"] == "ACTIVE" and entry["codex_capacity_demand"] == "ACTIVE"
    ]
    waiting = [entry for entry in entries if entry["operational_state"] == "WAITING_FOR_HUMAN"]
    human_queue = [
        {**item, "eligible_today": _eligible_human_item(item, observed)}
        for item in queue["entries"]
        if item["status"] == "WAITING"
    ]
    return {
        "schema_version": "v1",
        "observed_date": observed,
        "actionable": actionable,
        "waiting_for_human": waiting,
        "human_queue": human_queue,
        "all_projects": entries,
        "display_names": display_names,
        "recommendation": "Available capacity may move to an explicit actionable high-value project; human authority remains unchanged.",
    }


def render_portfolio(portfolio: dict[str, Any]) -> str:
    lines = ["ABVX PORTFOLIO", "", "ACTIONABLE"]
    if not portfolio["actionable"]:
        lines.append("  none")
    for entry in portfolio["actionable"]:
        lines.extend([
            portfolio["display_names"].get(entry["project"], entry["project"]),
            f"  {entry['strategic_priority']}",
            f"  {entry['operational_state']}",
            f"  next: {entry['next_action']}",
        ])

    lines.extend(["", "WAITING FOR YOU"])
    if not portfolio["waiting_for_human"]:
        lines.append("  none")
    for entry in portfolio["waiting_for_human"]:
        lines.extend([
            portfolio["display_names"].get(entry["project"], entry["project"]),
            f"  {entry['strategic_priority']}",
            f"  {entry['current_outcome']}",
            f"  not before: {entry['not_before'] or 'now'}",
        ])

    lines.extend(["", "CAPACITY RULE", portfolio["recommendation"]])
    return "\n".join(lines)
