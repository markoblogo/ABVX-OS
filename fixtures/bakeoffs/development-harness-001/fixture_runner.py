from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

PROFILES = [
    {"id": "native", "source": "ABVX-OS AGENTS.md + task prompt", "selected_skills": [], "ponytail": False, "skill_lines": 0, "skill_bytes": 0, "setup_commands": 0, "extra_stages": 0},
    {"id": "matt-selected", "source": "mattpocock/skills@84fdeff", "selected_skills": ["tdd", "diagnosing-bugs", "code-review"], "ponytail": False, "skill_lines": 265, "skill_bytes": 19171, "setup_commands": 2, "extra_stages": 2},
    {"id": "addy-selected", "source": "addyosmani/agent-skills@f493377", "selected_skills": ["test-driven-development", "incremental-implementation", "code-review-and-quality"], "ponytail": False, "skill_lines": 1043, "skill_bytes": 46521, "setup_commands": 2, "extra_stages": 3},
    {"id": "native-ponytail", "source": "native + DietrichGebert/ponytail@2ed6c52", "selected_skills": ["ponytail"], "ponytail": True, "skill_lines": 120, "skill_bytes": 6637, "setup_commands": 2, "extra_stages": 1},
    {"id": "matt-selected-ponytail", "source": "mattpocock/skills@84fdeff + ponytail@2ed6c52", "selected_skills": ["tdd", "diagnosing-bugs", "code-review", "ponytail"], "ponytail": True, "skill_lines": 385, "skill_bytes": 25808, "setup_commands": 4, "extra_stages": 3},
]

FIXTURES = [
    ("bugfix", ROOT / "bugfix" / "tests"),
    ("moderate-feature", ROOT / "moderate-feature" / "tests"),
    ("architecture-change", ROOT / "architecture-change" / "tests"),
]


def run_tests(test_dir: Path) -> dict[str, object]:
    completed = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-q"], cwd=ROOT.parent.parent.parent, capture_output=True, text=True, check=False)
    return {"status": "PASS" if completed.returncode == 0 else "FAIL", "exit_status": completed.returncode, "stdout": completed.stdout[-500:], "stderr": completed.stderr[-500:]}


def main() -> int:
    fixture_validation = {fixture_id: run_tests(test_dir) for fixture_id, test_dir in FIXTURES}
    matrix = []
    for profile in PROFILES:
        tests = {fixture_id: fixture_validation[fixture_id]["status"] for fixture_id, _ in FIXTURES}
        matrix.append({
            "profile": profile["id"],
            "source": profile["source"],
            "selected_skills": profile["selected_skills"],
            "ponytail": profile["ponytail"],
            "fixture_validation": tests,
            "agent_task_outcome": "NOT_RUN",
            "quality_result": "INCONCLUSIVE",
            "not_run_reason": "No reproducible model-agent execution adapter is available in FOUNDATION-004; deterministic local checks cannot measure generated solution quality.",
            "observable_efficiency": {
                "skill_prompt_lines": profile["skill_lines"],
                "skill_prompt_bytes": profile["skill_bytes"],
                "setup_commands": profile["setup_commands"],
                "extra_stages": profile["extra_stages"],
                "token_count": None,
                "elapsed_agent_time_ms": None,
                "changed_loc": None,
            },
        })
    print(json.dumps({"schema_version": "v1", "execution_mode": "deterministic_reference_validation", "fixture_validation": fixture_validation, "profiles": matrix}, indent=2, sort_keys=True))
    return 0 if all(item["status"] == "PASS" for item in fixture_validation.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
