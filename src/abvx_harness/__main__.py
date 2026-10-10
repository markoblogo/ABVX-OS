from __future__ import annotations

import json
import sys
from pathlib import Path

from .content_ops import approve_content_item, inspect_content_item, prepare_content_item, publish_content_item
from .context import inspect_context_pack, request_context
from .memory_decisions import record_memory_decision
from .harness import ValidationError, load_json, run_bakeoff, validate_repository
from .intake import add_intake_item, decide_intake_item, inspect_intake_item, link_intake_items, list_intake_items, promote_intake_item, review_intake_items, update_clarification
from .intelligence import run_content_enrichment
from .local_model import answer_local_model
from .playbooks import load_playbook, replay_playbook
from .portfolio import inspect_portfolio, render_portfolio
from .roles import inspect_role, list_roles, route_role
from .book_radar import add_records as add_book_radar_records, export_state as export_book_radar_state, import_bundle as import_book_radar_bundle, import_catalog as import_book_radar_catalog, render_report as render_book_radar_report, report as book_radar_report
from . import book_three
from .book_core import status_book, validate_book
from .protected_snapshots import create_snapshot, gate_status, recheck_snapshot
from . import __version__


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
        if name in {"json", "full"}:
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
        if argv[:1] == ["maintenance"]:
            from .maintenance import main as maintenance_main
            return maintenance_main(argv[1:], root=root)
        if argv[:1] == ["learning"]:
            from .process_learning import main as learning_main
            return learning_main(argv[1:], root=root)
        if len(argv) >= 2 and argv[:2] == ["book-radar", "markets"]:
            from datetime import date
            from . import book_radar_markets as markets
            positional, options = _options(argv[2:])
            if not positional:
                raise ValidationError("usage: book-radar markets <providers|template|check|normalize|import|track|revise|export>")
            action = positional[0]
            allowed = {"json", "as-of", "amazon-opportunity", "catalog-product"} if action == "template" else {"json", "reason", "as-of"} if action == "revise" else {"json"}
            if set(options) - allowed:
                raise ValidationError("unsupported markets option")
            if action == "providers" and len(positional) == 1:
                result = {"providers": [p.describe() for p in markets.PROVIDERS.values()]}
            elif action == "template" and len(positional) == 2:
                result = markets.import_template(root, positional[1], str(options.get("as-of", date.today().isoformat())), options.get("amazon-opportunity"), options.get("catalog-product"))
            elif action in {"check", "normalize", "import", "track", "export", "revise"} and len(positional) == 2:
                path = (root / positional[1]).resolve()
                if action == "check":
                    packet = markets.check(path)
                    result = {"status": "VALID", "opportunities": len(packet["opportunities"]), "observations": len(packet["observations"])}
                elif action == "normalize":
                    result = markets.check(path)
                elif action == "import": result = markets.import_bundle(root, path)
                elif action == "track": result = markets.track(root, path)
                elif action == "revise": result = markets.revise(root, path, str(options.get("reason", "")), str(options.get("as-of", date.today().isoformat())))
                else: result = markets.export(root, path)
            else:
                raise ValidationError("invalid markets action or arguments")
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
            return 0
        if len(argv) >= 3 and argv[:2] == ["book-radar", "report"] and argv[2] in {"markets", "weekly"}:
            from datetime import date
            from . import book_radar_markets as markets
            positional, options = _options(argv[2:])
            allowed = {"json", "as-of", "market", "opportunity"} if argv[2] == "markets" else {"json", "as-of", "amazon-committed", "hours"}
            if len(positional) != 1 or set(options) - allowed:
                raise ValidationError("invalid multi-market report arguments")
            as_of = str(options.get("as-of", date.today().isoformat()))
            if argv[2] == "markets": result = markets.report(root, as_of, options.get("market"), options.get("opportunity"))
            else:
                committed = int(str(options["amazon-committed"])) if "amazon-committed" in options else None
                result = markets.weekly(root, as_of, committed, float(str(options.get("hours", 8))))
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) if options.get("json") else markets.render(result))
            return 0
        # Wide screener: offline exports only; independent of canonical Radar state.
        if len(argv) >= 2 and argv[:2] == ["book-radar", "wide"]:
            from . import book_radar_wide as wide
            positional, options = _options(argv[2:])
            if set(options) - {"json", "previous"} or not positional:
                raise ValidationError("usage: ./bin/abvx book-radar wide <check|normalize|screen> <input.json> | report <run.json> | handoff <run.json> <cluster-id> [--json] [--previous run.json]")
            action = positional[0]
            if action not in ("check", "normalize", "screen", "report", "handoff") or len(positional) != (3 if action == "handoff" else 2) or ("previous" in options and action != "screen"):
                raise ValidationError("invalid wide action, arguments or options")
            target = (root / positional[1]).resolve()
            if action == "check":
                result = wide.check(target)
            elif action == "normalize":
                result = wide.normalize(target)
            elif action == "screen":
                previous = (root / str(options["previous"])).resolve() if "previous" in options else None
                result = wide.screen(target, previous)
            elif action == "report":
                result = wide.read_run(target)
            else:
                result = wide.handoff(target, positional[2])
            print(wide.render(result) if action == "report" and not options.get("json") else json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
            return 0
        if len(argv) >= 2 and argv[:2] == ["book-radar", "shelf"]:
            from . import book_radar_shelf as shelf
            positional, options = _options(argv[2:])
            if set(options) - {"json", "origin"} or len(positional) != 2 or positional[0] not in ("check", "import", "report", "compare"):
                raise ValidationError("usage: ./bin/abvx book-radar shelf <check|import> <snapshot.json> | <report|compare> <cluster-id> [--origin RETAINED|SYNTHETIC] [--json]")
            action, target = positional
            if action in ("check", "import"):
                if "origin" in options:
                    raise ValidationError("origin is preserved from the snapshot; --origin is read-only")
                source = (root / target).resolve()
                result = shelf.check_snapshot(source) if action == "check" else shelf.import_snapshot(root, source)
            else:
                operation = shelf.report if action == "report" else shelf.compare
                result = operation(root, target, str(options.get("origin", "RETAINED")))
            if options.get("json") or action in ("check", "import", "compare"):
                print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
            else:
                print(shelf.render(result))
            return 0
        if len(argv) >= 2 and argv[:2] == ["protect", "snapshot"]:
            positional, options = _options(argv[2:])
            if len(positional) < 2 or options:
                raise ValidationError("usage: ./bin/abvx protect snapshot <scope> <protected-file> [<protected-file> ...]")
            snapshot = create_snapshot(root, positional[0], positional[1:])
            print(snapshot.as_posix())
            return 0
        if len(argv) >= 2 and argv[:2] == ["psychology", "ingest"]:
            from .psychology_warehouse import ingest
            positional, options = _options(argv[2:])
            if positional or set(options) - {"source", "full", "json"} or ("full" in options and options["full"] not in (True, "true")):
                raise ValidationError("usage: ./bin/abvx psychology ingest [--source <path>] [--full] [--json]")
            report = ingest(root, Path(str(options["source"])) if "source" in options else None, full="full" in options)
            print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) if options.get("json") else f"{report['source_blocks']} blocks; NEW {report['delta']['new']}, CHANGED {report['delta']['changed']}, UNCHANGED {report['delta']['unchanged']}, REVIEW {report['delta']['review']}; source unchanged: {report['source_unchanged_after_ingest']}")
            return 0
        if len(argv) >= 2 and argv[:2] == ["psychology", "status"]:
            from .psychology_warehouse import query
            positional, options = _options(argv[2:])
            if positional or set(options) - {"json"}:
                raise ValidationError("usage: ./bin/abvx psychology status [--json]")
            result = query(root, "status")
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) if options.get("json") else f"{result['source_block_count']} source blocks; {result['inventory']['note_count']} current notes; last ingest {result['last_ingest_at']}")
            return 0
        if len(argv) >= 2 and argv[:2] == ["psychology", "inventory"]:
            from .psychology_warehouse import query
            positional, options = _options(argv[2:])
            if positional or set(options) - {"json"}:
                raise ValidationError("usage: ./bin/abvx psychology inventory [--json]")
            result = query(root, "inventory")
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) if options.get("json") else f"{result['note_count']} notes; {result['total_words']} words; {result['unclassified']} unclassified; {result['ambiguous']} ambiguous; {len(result['themes'])} themes")
            return 0
        if len(argv) >= 2 and argv[:2] in (["psychology", "unused"], ["psychology", "used"], ["psychology", "topic"], ["psychology", "provenance"], ["psychology", "changes"]):
            from .psychology_warehouse import query
            positional, options = _options(argv[2:])
            action = argv[1]
            if set(options) - {"json", "book"}:
                raise ValidationError("unknown psychology option")
            if action in ("topic",) and len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx psychology topic <label> [--json]")
            if action == "used" and (positional or "book" not in options):
                raise ValidationError("usage: ./bin/abvx psychology used --book <project-id> [--json]")
            if action in ("unused", "provenance", "changes") and (positional or "book" in options):
                raise ValidationError(f"usage: ./bin/abvx psychology {action} [--json]")
            value = positional[0] if action == "topic" else (str(options["book"]) if action == "used" else None)
            result = query(root, action, value)
            if options.get("json"):
                print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
            elif result.get("result") == "BLOCKED":
                print(f"BLOCKED: {result['reason']}")
            elif "count" in result:
                print(f"{result['count']} notes; IDs: " + ", ".join(result["note_ids"][:30]) + (" …" if result["count"] > 30 else ""))
            else:
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0
        if len(argv) >= 2 and argv[:2] == ["protect", "recheck"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1 or options:
                raise ValidationError("usage: ./bin/abvx protect recheck <snapshot-path>")
            result = recheck_snapshot(root, positional[0])
            for entry in result["files"]:
                print(f"{entry['status']}: {entry['path']}")
            return 1 if any(entry["status"] != "UNCHANGED" for entry in result["files"]) else 0
        if len(argv) >= 2 and argv[:2] == ["protect", "gate"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1 or set(options) - {"required", "snapshot", "missing-policy", "started-at"}:
                raise ValidationError("usage: ./bin/abvx protect gate <PASS|REVIEW|HOLD|FAIL> --required <true|false> --started-at <UTC timestamp> [--snapshot <path>] [--missing-policy REVIEW|HOLD]")
            required_text = options.get("required")
            if required_text not in {"true", "false"}:
                raise ValidationError("--required must be true or false")
            snapshot = options.get("snapshot")
            policy = options.get("missing-policy", "REVIEW")
            started_at = options.get("started-at")
            if snapshot is not None and not isinstance(snapshot, str):
                raise ValidationError("--snapshot must be a path")
            if not isinstance(policy, str):
                raise ValidationError("--missing-policy must be REVIEW or HOLD")
            if not isinstance(started_at, str):
                raise ValidationError("--started-at must be the task's UTC start timestamp")
            status = gate_status(positional[0], required_text == "true", snapshot, policy, root=root,
                                 run_started_at=started_at)
            print(f"FINAL STATUS: {status}")
            return 0 if status == positional[0] else 1
        if len(argv) >= 2 and argv[:2] == ["book", "status"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1 or options:
                raise ValidationError("usage: ./bin/abvx book status <book_id>")
            registry = {"gd3": book_three.core_adapter(root / "books" / "rn10-003")}
            status = status_book(positional[0], registry)
            print(status)
            return 1 if status.startswith("BOOK: BLOCKED") else 0
        if len(argv) >= 2 and argv[:2] == ["book", "gate-a"]:
            from .gate_a import transition
            positional, options = _options(argv[2:])
            if len(positional) != 2 or positional[0] != "gd3" or set(options) != {"authorization", "snapshot"}:
                raise ValidationError("usage: ./bin/abvx book gate-a gd3 <start|review|select|architecture-review> --authorization <project-relative-file> --snapshot <repo-relative-snapshot>")
            print(json.dumps(transition(root, positional[1], str(options["authorization"]), str(options["snapshot"])), indent=2))
            return 0
        if len(argv) >= 2 and argv[:2] == ["book", "validate"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1 or set(options) - {"stage"}:
                raise ValidationError("usage: ./bin/abvx book validate <book_id> [--stage all|canon|text|illustrations|kindle|print|metadata|retailer]")
            stage = options.get("stage", "all")
            if not isinstance(stage, str):
                raise ValidationError("--stage must be a stage name")
            registry = {"gd3": book_three.core_adapter(root / "books" / "rn10-003", stage)}
            report = validate_book(positional[0], registry)
            for check in report["checks"]:
                print(f"{check['check_id']}: {check['state']}")
            print(f"OVERALL: {report['overall']}")
            return 1 if report["overall"] == "FAIL" else 0
        if argv in (["--version"], ["version"]):
            print(f"abvx-os {__version__}")
            return 0
        if argv in (["role", "list"], ["role", "list", "--json"]):
            roles = list_roles(root)
            if argv[-1] == "--json":
                print(json.dumps(roles, indent=2, sort_keys=True))
            else:
                for role in roles:
                    print(f"{role['id']} [{role['status']}] {role['name']}")
            return 0
        if len(argv) >= 3 and argv[:2] == ["role", "inspect"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx role inspect <role-id> [--json]")
            role = inspect_role(root, positional[0])
            print(json.dumps(role, indent=2, sort_keys=True) if options.get("json") else f"{role['name']}: {role['purpose']}")
            return 0
        if len(argv) >= 2 and argv[:2] == ["role", "route"]:
            positional, options = _options(argv[2:])
            text = options.get("text")
            if positional or not isinstance(text, str):
                raise ValidationError("usage: ./bin/abvx role route --text <request> [--json]")
            result = route_role(root, text)
            if options.get("json"):
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print(f"primary: {result['primary_role']['id']}")
                if result["supporting_roles"]:
                    print("supporting: " + ", ".join(role["id"] for role in result["supporting_roles"]))
            return 0
        if len(argv) >= 2 and argv[:2] == ["radar", "observe"]:
            from . import book_radar_observe as observe
            # Keep the shared option parser; only these two action switches are boolean.
            tokens = [value for value in argv[2:] if value not in ("--due", "--status")]
            switches = [value[2:] for value in argv[2:] if value in ("--due", "--status")]
            positional, options = _options(tokens)
            if set(options) - {"record", "check", "template", "as-of", "json"}:
                raise ValidationError("Unknown radar observe option")
            actions = switches + [k for k in ("record", "check", "template") if k in options]
            if len(actions) > 1 or len(positional) > 1:
                raise ValidationError("Choose one radar observe action")
            action = actions[0] if actions else "checklist"
            if (action in ("due", "status", "record", "check") and positional) or (action in ("checklist", "template") and len(positional) != 1):
                raise ValidationError("usage: ./bin/abvx radar observe --due | <experiment> | --record <packet> | --status")
            if action == "record" and "as-of" in options:
                raise ValidationError("--as-of is read-only; imports preserve the actual capture date and current clock")
            as_of = options.get("as-of")
            if as_of is not None:
                from datetime import date
                try:
                    date.fromisoformat(str(as_of))
                except ValueError as error:
                    raise ValidationError("--as-of requires YYYY-MM-DD") from error
            if action == "due":
                result = observe.due(root, as_of)
            elif action == "status":
                result = observe.status(root, as_of)
            elif action in ("record", "check"):
                source = Path(str(options[action])).resolve()
                result = observe.record_packet(root, source) if action == "record" else observe.check_packet(root, source, as_of)
            elif action == "template":
                result = observe.template(root, positional[0], str(options["template"]), as_of)
            else:
                result = observe.checklist(root, positional[0], as_of)
            print(json.dumps(result, indent=2, ensure_ascii=False) if options.get("json") or action == "template" else observe.render(result, action))
            return 0
        if len(argv) >= 2 and argv[:2] in (["book-radar", "attribution-enable"], ["book-radar", "attribution-import"]):
            from .book_radar_attribution import enable, import_records
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx book-radar attribution-enable <owner-record> | attribution-import <path>")
            action = enable if argv[1] == "attribution-enable" else import_records
            print(json.dumps(action(root, Path(positional[0]).resolve()), indent=2, sort_keys=True))
            return 0
        if len(argv) >= 2 and argv[:2] == ["book-radar", "outcome-import"]:
            from .book_radar_outcomes import import_foundation
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx book-radar outcome-import <path>")
            print(json.dumps(import_foundation(root, Path(positional[0]).resolve()), indent=2, sort_keys=True))
            return 0
        if len(argv) >= 2 and argv[:2] == ["book-radar", "import"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx book-radar import <path> [--json]")
            result = import_book_radar_bundle(root, Path(positional[0]).resolve())
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if len(argv) >= 2 and argv[:2] == ["book-radar", "catalog-import"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx book-radar catalog-import <path> [--json]")
            print(json.dumps(import_book_radar_catalog(root, Path(positional[0]).resolve()), indent=2, sort_keys=True))
            return 0
        if len(argv) >= 2 and argv[:2] == ["book-radar", "export"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx book-radar export <path> [--json]")
            result = export_book_radar_state(root, Path(positional[0]).resolve())
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if len(argv) >= 2 and argv[:2] == ["book-radar", "report"]:
            positional, options = _options(argv[2:])
            if len(positional) != 1:
                raise ValidationError("usage: ./bin/abvx book-radar report <pipeline|experiments|backlog|outcomes|cohorts|checkpoints|calibration|cards|funnel|series|growth> [--as-of YYYY-MM-DD] [--json]")
            result = book_radar_report(root, positional[0], options.get("as-of"))
            print(json.dumps(result, indent=2, sort_keys=True) if options.get("json") else render_book_radar_report(result))
            return 0
        radar_actions = {"new-run": "radar_runs", "shortlist": "decisions", "decide": "decisions", "product": "products", "launch": "launches", "actuals": "actuals", "calibrate": "calibrations"}
        if len(argv) >= 2 and argv[0] == "book-radar" and argv[1] in radar_actions:
            positional, options = _options(argv[2:])
            source = options.get("file")
            if positional or not isinstance(source, str):
                raise ValidationError(f"usage: ./bin/abvx book-radar {argv[1]} --file <path> [--json]")
            result = add_book_radar_records(root, radar_actions[argv[1]], Path(source).resolve())
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
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
        if len(argv) >= 4 and argv[:3] == ["memory", "decision", "record"]:
            positional, options = _options(argv[3:])
            input_file = options.get("file")
            if positional or not isinstance(input_file, str):
                raise ValidationError("usage: ./bin/abvx memory decision record --file <decision.json>")
            result = record_memory_decision(root, **load_json((root / input_file).resolve()))
            print(json.dumps({"decision_id": result["decision_id"], "path": f"evidence/memory-decisions/{result['decision_id']}.json", "write_back": False}, indent=2))
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
        print("usage: ./bin/abvx validate | ./bin/abvx book <status|validate> gd3 | ./bin/abvx role <list|inspect|route> | ./bin/abvx psychology <ingest|status|inventory|unused|used|topic|provenance|changes> | ... | ./bin/abvx book-radar <import|catalog-import|new-run|shortlist|decide|product|launch|actuals|report|calibrate|export>", file=sys.stderr)
        return 2
    except (ValidationError, OSError, KeyError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
