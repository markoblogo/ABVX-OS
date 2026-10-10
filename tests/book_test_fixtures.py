"""Independent initial GD3 fixture; never reads operational books/."""
import hashlib
import json
import shutil
from pathlib import Path
from abvx_harness import book_three


def initial_book_three(project):
    shutil.copytree(Path(__file__).parent / "fixtures/book_three_initial", project, dirs_exist_ok=True)
    state = book_three.initial_state(project)
    (project / book_three.STATE_NAME).write_text(json.dumps(state), encoding="utf-8")
    canon = project / book_three.CANON_NAME
    event = {
        "event_id": "gd3-0001", "book_id": "gd3", "timestamp": "2026-09-30T00:00:00Z",
        "stage": "NOT_STARTED", "event_type": "STATE_INITIALIZED", "actor": "system",
        "input_refs": [book_three.CANON_NAME], "output_refs": [book_three.STATE_NAME],
        "decision": "Synthetic initialization; no production authorization.", "previous_state": {},
        "new_state": book_three.state_projection(state), "owner_gate": "NONE",
        "evidence": [{"path": book_three.CANON_NAME, "sha256": hashlib.sha256(canon.read_bytes()).hexdigest()}],
        "notes": "Synthetic test fixture only."}
    (project / book_three.EVENT_NAME).write_text(json.dumps(event) + "\n", encoding="utf-8")
    return project
