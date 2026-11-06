"""Conservative, bounded, read-only preview for Codex-created project workspaces.

Never deletes, moves, executes project scripts, or follows symlinks.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import time

from .mac_storage import measure

_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}\Z")
_REGENERABLE = frozenset(("node_modules", ".next"))
_SKIP = frozenset((".git", ".venv", "venv", ".cache", "dist", "build", "artifacts",
                   "outputs", "public", "docs", "coverage", "test-results"))
_LOCKS = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb")


def _run(args, timeout):
    try:
        return subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _paths_in_use():
    """Never persist process arguments, process IDs, or open-file paths in reports."""
    processes = _run(("/bin/ps", "-axo", "command="), 12)
    working = _run(("/usr/sbin/lsof", "-nP", "-d", "cwd", "-Fn"), 20)
    if processes is None or processes.returncode or working is None or working.returncode:
        return None
    args = processes.stdout.decode(errors="replace").splitlines()
    cwds = [s[1:] for s in working.stdout.decode(errors="replace").splitlines()
            if s.startswith("n/")]
    return args, cwds


def _active(repo, process_data):
    if process_data is None:
        return None
    args, cwds = process_data
    prefix = str(repo)
    return any(prefix in line for line in args) or any(
        path == prefix or path.startswith(prefix + "/") for path in cwds)


def _safe_children(parent, device, limit=150):
    if parent.is_symlink() or not parent.is_dir() or parent.stat().st_dev != device:
        return [], True
    try:
        children = sorted((Path(entry.path) for entry in os.scandir(parent)
                           if not entry.is_symlink() and entry.is_dir(follow_symlinks=False)),
                          key=lambda x: x.name)
    except OSError:
        return [], True
    return children[:limit], len(children) > limit


def _repos(root, device, max_repos):
    """Only fixed date/session/work layouts, not arbitrary user repositories."""
    out, partial = [], False
    dates, skipped = _safe_children(root, device, 150)
    partial |= skipped
    for date in dates:
        if not _DATE.fullmatch(date.name):
            continue
        sessions, truncated = _safe_children(date, device, 100)
        partial |= truncated
        for session in sessions:
            for parent in (session, session / "work"):
                if parent.name == "work" and not parent.is_dir():
                    continue
                projects, truncated = _safe_children(parent, device, 100)
                partial |= truncated
                for project in projects:
                    if project in out or not (project / ".git").exists():
                        continue
                    # Ignore subprojects accidentally located beneath a Git repository.
                    if (parent / ".git").exists():
                        continue
                    out.append(project)
                    if len(out) >= max_repos:
                        return out, True
    return out, partial


def _targets(repo, device, limit=80):
    """At most five directory levels; never enter Git, generated trees or symlinks."""
    queue = [(repo, 0)]
    found, visited, partial = [], 0, False
    while queue:
        parent, depth = queue.pop(0)
        visited += 1
        if visited > 300 or len(found) >= limit:
            partial = True
            break
        children, truncated = _safe_children(parent, device, 150)
        partial |= truncated
        for child in children:
            if child.name in _REGENERABLE:
                found.append(child)
                if len(found) >= limit:
                    partial = True
                    break
            elif depth < 4 and child.name not in _SKIP:
                queue.append((child, depth + 1))
    return found, partial


def _git_observations(repo):
    git = repo / ".git"
    if git.is_symlink() or not git.is_dir():
        return False, None, "GIT_UNSUPPORTED"
    status = _run(("/usr/bin/git", "-C", str(repo), "status", "--porcelain=v1",
                   "--untracked-files=normal"), 12)
    if status is None or status.returncode:
        return False, None, "GIT_UNAVAILABLE"
    if status.stdout.strip():
        return False, None, "DIRTY_REPOSITORY"
    files = _run(("/usr/bin/git", "-C", str(repo), "ls-files", "-z"), 12)
    if files is None or files.returncode:
        return False, None, "TRACKED_FILES_UNKNOWN"
    tracked = [p for p in files.stdout.split(b"\x00") if p]
    if len(tracked) > 5000:
        return False, None, "TRACKED_FILE_BUDGET"
    newest = max(repo.stat().st_mtime, git.stat().st_mtime)
    for path in (git / "index", git / "HEAD", git / "logs" / "HEAD"):
        try:
            newest = max(newest, path.lstat().st_mtime)
        except OSError:
            pass
    for rel in tracked:
        try:
            path = repo / os.fsdecode(rel)
            if path.is_symlink():
                continue
            newest = max(newest, path.stat().st_mtime)
        except OSError:
            # Unknown tracked-file activity means this repo is not a safe candidate.
            return False, None, "TRACKED_FILE_UNAVAILABLE"
    return True, newest, None


def preview(root=None, *, now=None, min_age_days=14, max_repos=60,
            max_candidates=80, seconds=120):
    """Explicit one-shot preview; not invoked during five-minute daemon ticks."""
    started = time.monotonic()
    now = time.time() if now is None else now
    fixed_root = Path.home() / "Documents" / "Codex"
    root = fixed_root if root is None else Path(root)
    report = {"schema_version": "v1", "mode": "PREVIEW_ONLY",
              "deletion_authorized": False, "root": str(root), "time": now,
              "policy": {"inactive_days": min_age_days, "max_repos": max_repos,
                         "max_candidates": max_candidates, "seconds": seconds,
                         "kinds": sorted(_REGENERABLE)},
              "candidates": [], "partial": False, "partial_reasons": [],
              "measurement_incomplete_count": 0, "candidate_count": 0,
              "review_eligible_count": 0, "review_eligible_allocated_bytes": 0,
              "measured_allocated_bytes": 0, "repos_checked": 0,
              "process_check": "UNAVAILABLE",
              "note": "Review only; no deletion endpoint. Reinstall dependencies before builds. "
                      "Sizes are measured allocated blocks, not guaranteed reclaimed space."}
    if (root.is_symlink() or not root.is_dir() or
            (root == fixed_root and (Path.home() / "Documents").is_symlink())):
        return dict(report, status="ROOT_UNAVAILABLE", partial=True)
    try:
        device = root.stat().st_dev
        if sys.platform == "darwin" and root == fixed_root:
            if device != Path("/System/Volumes/Data").stat().st_dev:
                return dict(report, status="NOT_INTERNAL_VOLUME", partial=True)
    except OSError:
        return dict(report, status="ROOT_UNAVAILABLE", partial=True)
    process_data = _paths_in_use()
    repos, discovery_partial = _repos(root, device, max_repos)
    report["partial"] = discovery_partial
    if discovery_partial:
        report["partial_reasons"].append("REPOSITORY_DISCOVERY_LIMIT")
    report["process_check"] = "VERIFIED" if process_data is not None else "UNAVAILABLE"
    report["repos_checked"] = 0
    for repo in repos:
        if time.monotonic() - started > seconds:
            report["partial"] = True
            report["partial_reasons"].append("TIME_BUDGET")
            break
        if len(report["candidates"]) >= max_candidates:
            report["partial"] = True
            report["partial_reasons"].append("CANDIDATE_BUDGET")
            break
        report["repos_checked"] += 1
        active = _active(repo, process_data)
        try:
            clean, last_activity, git_reason = _git_observations(repo)
        except OSError:
            clean, last_activity, git_reason = False, None, "GIT_UNAVAILABLE"
        has_lock = any((repo / name).is_file() and not (repo / name).is_symlink()
                       for name in _LOCKS)
        targets, truncated = _targets(repo, device, max_candidates - len(report["candidates"]))
        report["partial"] |= truncated
        if truncated:
            report["partial_reasons"].append("TARGET_DISCOVERY_LIMIT")
        for target in targets:
            if time.monotonic() - started > seconds:
                report["partial"] = True
                report["partial_reasons"].append("TIME_BUDGET")
                break
            try:
                if target.is_symlink() or target.stat().st_dev != device:
                    continue
                newest = max(target.stat().st_mtime, last_activity or 0)
                age_days = max(0, (now - newest) / 86400)
                size = measure(target, seconds=1, max_entries=12000)
                if not size["complete"]:
                    report["partial"] = True
                    report["measurement_incomplete_count"] += 1
                if active is None:
                    reason = "ACTIVITY_UNKNOWN"
                elif active:
                    reason = "ACTIVE_PROCESS"
                elif not clean:
                    reason = git_reason or "GIT_UNKNOWN"
                elif not has_lock:
                    reason = "NO_LOCKFILE"
                elif age_days < min_age_days:
                    reason = "RECENT_ACTIVITY"
                elif not size["complete"]:
                    reason = "MEASUREMENT_PARTIAL"
                else:
                    reason = "REVIEW_ELIGIBLE"
                report["candidates"].append({
                    "path": str(target), "repo": str(repo), "kind": target.name,
                    "status": reason, "age_days_floor": int(age_days),
                    "allocated_bytes": size["allocated_bytes"],
                    "measurement_complete": size["complete"],
                    "measurement_entries": size["entries"]})
            except OSError:
                report["partial"] = True
                report["partial_reasons"].append("TARGET_METADATA_UNAVAILABLE")
    report["partial_reasons"] = sorted(set(report["partial_reasons"]))
    report["duration_seconds"] = round(time.monotonic() - started, 2)
    report["status"] = "PARTIAL" if report["partial"] else "COMPLETE"
    report["candidate_count"] = len(report["candidates"])
    report["review_eligible_count"] = sum(c["status"] == "REVIEW_ELIGIBLE" for c in report["candidates"])
    report["measured_allocated_bytes"] = sum(c["allocated_bytes"] for c in report["candidates"])
    report["review_eligible_allocated_bytes"] = sum(
        c["allocated_bytes"] for c in report["candidates"] if c["status"] == "REVIEW_ELIGIBLE")
    return report
