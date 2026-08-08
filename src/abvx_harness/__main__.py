from __future__ import annotations

import json
import sys
from pathlib import Path

from .harness import ValidationError, load_json, run_bakeoff, validate_repository
from .intake import add_intake_item, decide_intake_item, inspect_intake_item, link_intake_items, list_intake_items, promote_intake_item, review_intake_items, update_clarification
from .portfolio import inspect_portfolio, render_portfolio


ROOT = Path(__file__).resolve().parents[2]


def _options(tokens: list[str]) -> tuple[list[str], dict[str, str | bool]]:
    positional: list[str] = []
    options: dict[str, str | bool] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("--"):
            positional.append(token)
            index += 1
            continue
        name = token[2:]
        if name == "json":
            options[name] = True
            index += 1
            continue
        if index + 1 >= len(tokens) or tokens[index + 1].startswith("--"):
            raise ValidationError(f"missing value for --{name}")
        options[name] = tokens[index + 1]
        index += 2
    return positional, options


def _print_intake(value: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    if isinstance(value, list):
        if not value:
            print("No intake items.")
        for item in value:
            classification = item["classification"]
            print(f"{item['id']} [{item['status']}] {classification['primary_type']} ({classification['confidence']:.2f})")
    else:
        print(f"{value['id']} [{value['status']}] {value['classification']['primary_type']} ({value['classification']['confidence']:.2f})")
        print(value["raw_input"]["value"])


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    try:
        if len(argv) >= 2 and argv[:2] == ["intake", "add"]:
            _, options = _options(argv[2:])
            item = add_intake_item(root, text=options.get("text") if isinstance(options.get("text"), str) else None, url=options.get("url") if isinstance(options.get("url"), str) else None, context=options.get("context") if isinstance(options.get("context"), str) else None, title=options.get("title") if isinstance(options.get("title"), str) else None, summary=options.get("summary") if isinstance(options.get("summary"), str) else None, explicit_type=options.get("type") if isinstance(options.get("type"), str) else None, item_id=options.get("id") if isinstance(options.get("id"), str) else None)
            _print_intake(item, bool(options.get("json")))
            return 0
        if len(argv) >= 2 and argv[:2] == ["intake", "list"]:
            _, options = _options(argv[2:])
            _print_intake(list_intake_items(root), bool(options.get("json")))
            return 0
        if len(argv) >= 3 and argv[:2] == ["intake", "inspect"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: intake inspect <id> [--json]")
            _print_intake(inspect_intake_item(root, positional[0]), bool(options.get("json")))
            return 0
        if len(argv) >= 3 and argv[:2] == ["intake", "clarify"]:
            positional, options = _options(argv[2:])
            answer = options.get("answer")
            if len(positional) != 1 or not isinstance(answer, str):
                raise ValidationError("usage: intake clarify <id> --answer <text> [--json]")
            _print_intake(update_clarification(root, positional[0], answer), bool(options.get("json")))
            return 0
        if len(argv) >= 4 and argv[:2] == ["intake", "link"]:
            positional, options = _options(argv[2:])
            if len(positional) != 2:
                raise ValidationError("usage: intake link <id> <related-id> [--json]")
            linked = link_intake_items(root, positional[0], positional[1])
            _print_intake(list(linked), bool(options.get("json")))
            return 0
        if len(argv) >= 2 and argv[:2] == ["intake", "review"]:
            _, options = _options(argv[2:])
            _print_intake(review_intake_items(root), bool(options.get("json")))
            return 0
        if len(argv) >= 3 and argv[:2] in (["intake", "accept"], ["intake", "reject"], ["intake", "watch"], ["intake", "keep"], ["intake", "archive"]):
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx intake <accept|reject|watch|keep|archive> <id> [--reason <text>] [--json]")
            action = argv[1].upper()
            _print_intake(decide_intake_item(root, positional[0], action, options.get("reason") if isinstance(options.get("reason"), str) else None), bool(options.get("json")))
            return 0
        if len(argv) >= 3 and argv[:2] == ["intake", "promote"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx intake promote <id> [--json]")
            _print_intake(promote_intake_item(root, positional[0]), bool(options.get("json")))
            return 0
        if argv == ["validate"]:
            checked = validate_repository(root)
            print(json.dumps({"status": "PASS", "checked": checked}, indent=2))
            return 0
        if len(argv) == 3 and argv[:2] == ["bakeoff", "run"]:
            run_dir = run_bakeoff(root, argv[2])
            print(json.dumps({"status": "PASS", "run_dir": str(run_dir.relative_to(root))}, indent=2))
            return 0
        if len(argv) == 3 and argv[:2] == ["bakeoff", "inspect"]:
            runs = sorted((root / "evidence" / "bakeoffs" / argv[2] / "runs").glob("*/result.json"))
            if not runs:
                raise ValidationError(f"no runs found for {argv[2]}")
            print(json.dumps(load_json(runs[-1]), indent=2, sort_keys=True))
            return 0
        if argv in (["portfolio", "inspect"], ["portfolio", "inspect", "--json"]):
            portfolio = inspect_portfolio(root)
            if argv[-1] == "--json":
                print(json.dumps(portfolio, indent=2, sort_keys=True))
            else:
                print(render_portfolio(portfolio))
            return 0
        print("usage: ./bin/abvx validate | ./bin/abvx intake add --text <text> | ./bin/abvx intake add --url <url> | ./bin/abvx intake inspect <id> | ./bin/abvx intake list | ./bin/abvx intake review [--json] | ./bin/abvx intake clarify <id> --answer <text> | ./bin/abvx intake <accept|reject|watch|keep|archive> <id> | ./bin/abvx intake promote <id> | ./bin/abvx intake link <id> <related-id> | ./bin/abvx portfolio inspect [--json] | ./bin/abvx bakeoff run <id> | ./bin/abvx bakeoff inspect <id>", file=sys.stderr)
        return 2
    except (ValidationError, OSError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
