from __future__ import annotations

import json
import sys
from pathlib import Path

from .content_ops import approve_content_item, inspect_content_item, prepare_content_item, publish_content_item
from .context import inspect_context_pack, request_context
from .harness import ValidationError, load_json, run_bakeoff, validate_repository
from .intake import add_intake_item, decide_intake_item, inspect_intake_item, link_intake_items, list_intake_items, promote_intake_item, review_intake_items, update_clarification
from .intelligence import run_content_enrichment
from .local_model import answer_local_model
from .playbooks import load_playbook, replay_playbook
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


def _print_content(value: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    if isinstance(value, dict) and {"id", "status", "project", "surface"} <= set(value):
        print(f"{value['id']} [{value['status']}] {value['project']}:{value['surface']}")
        print(value["title"])
        blockers = value.get("validation", {}).get("blockers", [])
        if blockers:
            print(f"blockers: {len(blockers)}")
    else:
        print(json.dumps(value, indent=2, sort_keys=True))


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
        if len(argv) >= 3 and argv[:2] == ["content", "prepare"]:
            positional, options = _options(argv[2:])
            fixture_ref = options.get("file")
            intelligence_mode = options.get("intelligence")
            if positional or not isinstance(fixture_ref, str):
                raise ValidationError("usage: ./bin/abvx content prepare --file <path> [--intelligence deterministic|local_llm] [--json]")
            _print_content(prepare_content_item(root, fixture_ref, intelligence_mode=intelligence_mode if isinstance(intelligence_mode, str) else "deterministic"), bool(options.get("json")))
            return 0
        if len(argv) >= 3 and argv[:2] == ["intelligence", "run"]:
            positional, options = _options(argv[2:])
            task = options.get("task")
            fixture_ref = options.get("file")
            provider = options.get("provider")
            if positional or task != "content-enrichment" or not isinstance(fixture_ref, str):
                raise ValidationError("usage: ./bin/abvx intelligence run --task content-enrichment --file <path> [--provider ollama.local|cheap.api] [--json]")
            result = run_content_enrichment(root, fixture_ref, provider=provider if isinstance(provider, str) else None)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if len(argv) >= 3 and argv[:2] == ["content", "inspect"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx content inspect <id> [--json]")
            _print_content(inspect_content_item(root, positional[0]), bool(options.get("json")))
            return 0
        if len(argv) >= 3 and argv[:2] == ["content", "approve"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx content approve <id> [--json]")
            _print_content(approve_content_item(root, positional[0]), bool(options.get("json")))
            return 0
        if len(argv) >= 3 and argv[:2] == ["content", "publish"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx content publish <id> [--json]")
            _print_content(publish_content_item(root, positional[0]), bool(options.get("json")))
            return 0
        if argv == ["validate"]:
            checked = validate_repository(root)
            print(json.dumps({"status": "PASS", "checked": checked}, indent=2))
            return 0
        if len(argv) == 3 and argv[:2] == ["playbook", "inspect"]:
            print(json.dumps(load_playbook(root, argv[2]), indent=2, sort_keys=True))
            return 0
        if len(argv) >= 3 and argv[:2] == ["playbook", "replay"]:
            positional, options = _options(argv[2:])
            replay_input = options.get("input")
            if len(positional) != 1 or not isinstance(replay_input, str):
                raise ValidationError("usage: ./bin/abvx playbook replay <id> --input <path> [--json]")
            result = replay_playbook(root, positional[0], (root / replay_input).resolve())
            print(json.dumps(result, indent=2, sort_keys=True))
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
        if len(argv) >= 3 and argv[:2] == ["context", "request"]:
            positional, options = _options(argv[2:])
            request_file = options.get("file")
            if positional or not isinstance(request_file, str):
                raise ValidationError("usage: ./bin/abvx context request --file <path> [--json]")
            result = request_context(root, (root / request_file).resolve())
            if options.get("json"):
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print(f"{result['pack_id']} [{result['result']}]")
                print(result["pack_path"])
            return 0
        if len(argv) >= 3 and argv[:2] == ["context", "inspect"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx context inspect <pack-id> [--json]")
            pack = inspect_context_pack(root, positional[0])
            print(json.dumps(pack, indent=2, sort_keys=True))
            return 0
        if len(argv) >= 3 and argv[:2] == ["local-model", "answer"]:
            positional, options = _options(argv[2:])
            request_file = options.get("file")
            if positional or not isinstance(request_file, str):
                raise ValidationError("usage: ./bin/abvx local-model answer --file <path> [--url <url>]")
            result = answer_local_model(root, (root / request_file).resolve(), url=options.get("url") if isinstance(options.get("url"), str) else None)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if argv in (["portfolio", "inspect"], ["portfolio", "inspect", "--json"]):
            portfolio = inspect_portfolio(root)
            if argv[-1] == "--json":
                print(json.dumps(portfolio, indent=2, sort_keys=True))
            else:
                print(render_portfolio(portfolio))
            return 0
        print("usage: ./bin/abvx validate | ... | ./bin/abvx context inspect <pack-id> | ./bin/abvx local-model answer --file <path> [--url <url>]", file=sys.stderr)
        return 2
    except (ValidationError, OSError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
