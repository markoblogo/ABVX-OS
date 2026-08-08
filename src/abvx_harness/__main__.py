from __future__ import annotations

import json
import sys
from pathlib import Path

from .harness import ValidationError, load_json, run_bakeoff, validate_repository
from .portfolio import inspect_portfolio, render_portfolio


ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    try:
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
        print("usage: ./bin/abvx validate | ./bin/abvx portfolio inspect [--json] | ./bin/abvx bakeoff run <id> | ./bin/abvx bakeoff inspect <id>", file=sys.stderr)
        return 2
    except (ValidationError, OSError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
