"""Immutable, explicit protected-file hash snapshots for bounded work runs."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


SNAPSHOT_SCHEMA = "abvx-protected-file-snapshot/v1"
DEFAULT_DIRECTORY = Path(".codex/protected-snapshots")
SCOPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _inside(root: Path, value: str | Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError("protected paths must be explicit paths relative to repository root")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    if resolved == resolved_root or not resolved.is_relative_to(resolved_root):
        raise ValueError(f"path escapes repository root: {value}")
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot_path(root: Path, path: str | Path) -> Path:
    resolved = _inside(root, path)
    if not resolved.is_file():
        raise ValueError(f"snapshot does not exist: {path}")
    return resolved


def create_snapshot(root: Path, scope: str, files: Sequence[str]) -> Path:
    """Capture exactly the caller-supplied file list; never infer protected files."""
    if not isinstance(scope, str) or not SCOPE_RE.fullmatch(scope):
        raise ValueError("scope must use letters, digits, dot, underscore, or hyphen")
    if not files:
        raise ValueError("explicit protected-file list is required")
    if any(not isinstance(item, str) or not item.strip() for item in files):
        raise ValueError("protected-file paths must be non-empty strings")
    normalized = [Path(item).as_posix() for item in files]
    if len(set(normalized)) != len(normalized):
        raise ValueError("protected-file list contains duplicates")
    entries: list[dict[str, Any]] = []
    for item in normalized:
        path = _inside(root, item)
        if path.exists() and not path.is_file():
            raise ValueError(f"protected path is not a regular file: {item}")
        relative = path.relative_to(root.resolve()).as_posix()
        entries.append({"path": relative, "sha256": _sha256(path) if path.is_file() else None})
    captured = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    record = {"schema_version": SNAPSHOT_SCHEMA, "scope": scope, "captured_at": captured, "files": entries}
    resolved_root = root.resolve()
    output_dir = resolved_root / DEFAULT_DIRECTORY
    resolved_output_dir = output_dir.resolve()
    if not resolved_output_dir.is_relative_to(resolved_root):
        raise ValueError("snapshot output directory escapes repository root")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = captured.replace(":", "").replace("-", "")
    target = resolved_output_dir / f"{scope}-{stamp}.json"
    payload = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target.relative_to(root.resolve())


def recheck_snapshot(root: Path, snapshot: str | Path) -> dict[str, Any]:
    source = _snapshot_path(root, snapshot)
    try:
        record = json.loads(source.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid snapshot JSON: {error}") from error
    if (not isinstance(record, dict) or record.get("schema_version") != SNAPSHOT_SCHEMA
            or not isinstance(record.get("scope"), str) or not SCOPE_RE.fullmatch(record["scope"])
            or not isinstance(record.get("captured_at"), str)
            or not isinstance(record.get("files"), list) or not record["files"]):
        raise ValueError("invalid protected-file snapshot envelope")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in record["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"} or not isinstance(entry["path"], str):
            raise ValueError("invalid protected-file snapshot entry")
        if entry["path"] in seen:
            raise ValueError("duplicate path in protected-file snapshot")
        seen.add(entry["path"])
        expected = entry["sha256"]
        if expected is not None and (not isinstance(expected, str) or not SHA_RE.fullmatch(expected)):
            raise ValueError("invalid protected-file SHA-256 in snapshot")
        path = _inside(root, entry["path"])
        if not path.is_file():
            status, actual = "MISSING", None
        else:
            actual = _sha256(path)
            status = "UNCHANGED" if expected is not None and actual == expected else "CHANGED"
        results.append({"path": entry["path"], "expected_sha256": expected,
                        "actual_sha256": actual, "status": status})
    return {"snapshot": source.relative_to(root.resolve()).as_posix(), "scope": record["scope"],
            "captured_at": record["captured_at"], "files": results}


def gate_status(requested: str, required: bool, snapshot: str | Path | None,
                missing_policy: str, *, root: Path, run_started_at: str | None = None) -> str:
    """Prevent PASS when a required pre-run snapshot is absent or no longer clean."""
    if requested not in {"PASS", "REVIEW", "HOLD", "FAIL"}:
        raise ValueError("requested status must be PASS, REVIEW, HOLD, or FAIL")
    if missing_policy not in {"REVIEW", "HOLD"}:
        raise ValueError("missing snapshot policy must be REVIEW or HOLD")
    if not required or requested != "PASS":
        return requested
    if (snapshot is None or not isinstance(run_started_at, str)):
        return missing_policy
    try:
        start = datetime.fromisoformat(run_started_at.replace("Z", "+00:00"))
        if start.tzinfo is None:
            return missing_policy
        result = recheck_snapshot(root, snapshot)
        captured_at = datetime.fromisoformat(result["captured_at"].replace("Z", "+00:00"))
    except (OSError, ValueError):
        return missing_policy
    if captured_at.tzinfo is None or captured_at > start:
        return missing_policy
    if any(entry["status"] != "UNCHANGED" for entry in result["files"]):
        return "HOLD"
    return "PASS"
