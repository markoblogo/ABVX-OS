"""Low-frequency Codex workspace growth observations. No deletion or migration.

Run from the existing mac-operator LaunchAgent, never in every 5-minute probe.
"""
from __future__ import annotations

from datetime import datetime
import os
import re
from pathlib import Path
import subprocess
import time
from zoneinfo import ZoneInfo

from . import mac_codex_retention
from . import mac_budget as budget

_GIB = 1024 ** 3
_ZONE = ZoneInfo("Europe/Paris")
_DAILY_THRESHOLD = 2 * _GIB
_WEEKLY_THRESHOLD = 1 * _GIB
_WORKSPACE = Path.home() / "Documents" / "Codex"
_INTERNAL = Path("/System/Volumes/Data")
_DAILY_LIMIT = 48
_WEEKLY_LIMIT = 115


def _light_measure(root, now=None):
    """Up to four newest date folders, max 3s each, never a full workspace scan."""
    now = time.time() if now is None else now
    out = {"schema_version": "v1", "time": now, "path": str(root),
           "status": "UNAVAILABLE", "allocated_bytes": None, "device": None,
           "scope": "RECENT_DATE_FOLDERS", "categories": [], "selected_paths": []}
    try:
        if root.is_symlink() or root.parent.is_symlink() or not root.is_dir():
            return out
        device = root.stat().st_dev
        if device != _INTERNAL.stat().st_dev:
            return dict(out, status="NOT_INTERNAL_VOLUME")
        out['device'] = device
        choices = []
        with os.scandir(root) as entries:
            for i, entry in enumerate(entries):
                if i >= 500:
                    return dict(out, status="DIRECTORY_LIMIT")
                if (re.fullmatch(r'20\d{2}-\d{2}-\d{2}', entry.name) and
                        not entry.is_symlink() and entry.is_dir(follow_symlinks=False)):
                    choices.append(Path(entry.path))
        for path in sorted(choices, reverse=True)[:4]:
            out['selected_paths'].append(str(path))
            out['categories'].append(_measure(path, now=now, timeout=3))
        complete = bool(out['categories']) and all(c['status'] == 'COMPLETE' for c in out['categories'])
        return dict(out, status='COMPLETE' if complete else 'PARTIAL',
                    allocated_bytes=sum(c['allocated_bytes'] for c in out['categories']) if complete else None,
                    note='Only selected recent date folders, not total Codex size. Partial categories remain unknown.')
    except budget.Expired:
        raise
    except OSError:
        return out


def _period(now):
    local = datetime.fromtimestamp(now, _ZONE)
    iso = local.isocalendar()
    return local.date().isoformat(), f"{iso.year}-W{iso.week:02d}", local.hour


def _measure(root, now=None, timeout=_DAILY_LIMIT):
    """One exact bounded du, no traversal across mounts or symlinks."""
    now = time.time() if now is None else now
    out = {"schema_version": "v1", "time": now, "path": str(root),
           "status": "UNAVAILABLE", "allocated_bytes": None, "device": None}
    try:
        if (root.is_symlink() or not (root.is_dir() or root.is_file()) or
                (root.parent.is_symlink()) or not _INTERNAL.exists()):
            return out
        st = root.stat()
        if st.st_dev != _INTERNAL.stat().st_dev:
            return dict(out, status="NOT_INTERNAL_VOLUME")
        out["device"] = st.st_dev
        proc = subprocess.run(("/usr/bin/du", "-skx", str(root)),
                              capture_output=True, timeout=budget.timeout(timeout), check=False)
        if proc.returncode != 0:
            return dict(out, status="PARTIAL_OR_DENIED")
        value = proc.stdout.split(maxsplit=1)
        if len(value) != 2 or not value[0].isdigit():
            return dict(out, status="PARSE_ERROR")
        return dict(out, status="COMPLETE", allocated_bytes=int(value[0]) * 1024)
    except subprocess.TimeoutExpired:
        return dict(out, status="TIME_LIMIT")
    except budget.Expired:
        raise
    except OSError:
        return dict(out, status="UNAVAILABLE")


def _sequential_measure(root, state, load, save, now=None, *, seconds=48, max_items=500):
    """One bounded sequential slice; persist each result, rotate oldest attempts.

    Category sums are allocated-block estimates, not unique APFS physical usage.
    Complete coverage is explicitly limited to a 36-hour freshness window.
    """
    now = time.time() if now is None else now
    deadline = time.monotonic() + budget.timeout(seconds)
    progress_path = state / 'codex-growth-progress.json'
    out = dict(schema_version='v1', time=now, path=str(root), device=None,
               scope='SEQUENTIAL_WORKSPACE', status='UNAVAILABLE',
               allocated_bytes=None, measured_allocated_bytes=0, categories=[],
               coverage={'discovered_entries': 0, 'complete_entries': 0},
               inventory_complete=False, errors=[])
    try:
        if root.is_symlink() or root.parent.is_symlink() or not root.is_dir():
            return out
        device = root.stat().st_dev
        if device != _INTERNAL.stat().st_dev:
            return dict(out, status='NOT_INTERNAL_VOLUME')
        out['device'] = device
        paths = []
        with os.scandir(root) as entries:
            for i, entry in enumerate(entries):
                if i >= 500 or time.monotonic() >= deadline:
                    out['errors'].append('INVENTORY_LIMIT')
                    break
                paths.append(Path(entry.path))
            else:
                out['inventory_complete'] = True
        previous = load(progress_path) or {}
        prior = {c['path']: c for c in previous.get('categories', [])
                 if isinstance(c, dict) and 'path' in c} if (
                     previous.get('path') == str(root) and previous.get('device') == device) else {}
        categories = {str(p): prior.get(str(p), dict(path=str(p), time=None,
                     status='NOT_MEASURED', allocated_bytes=None)) for p in paths}
        def project():
            fresh = [c for c in categories.values() if c.get('status') == 'COMPLETE'
                     and isinstance(c.get('time'), (int, float)) and 0 <= now-c['time'] <= 36*3600]
            complete = out['inventory_complete'] and len(fresh) == len(paths)
            measured = sum(c['allocated_bytes'] for c in fresh)
            ages = [now-c['time'] for c in fresh]
            return dict(out, status='COMPLETE' if complete else 'PARTIAL',
                        measured_allocated_bytes=measured,
                        allocated_bytes=measured + root.stat().st_blocks*512 if complete else None,
                        categories=list(categories.values()),
                        coverage={'discovered_entries': len(paths), 'complete_entries': len(fresh),
                                  'unmeasured_or_failed_entries': len(paths)-len(fresh),
                                  'error_entries': sum(c.get('status') not in ('COMPLETE', 'NOT_MEASURED') for c in categories.values()),
                                  'oldest_measurement_age_seconds': max(ages) if ages else None,
                                  'freshness_window_seconds': 36*3600},
                        note='Sequential category estimates; partial subtotal is not total Codex size. Hardlinks across categories/APFS shared blocks can overcount physical use; not reclaimable bytes.')
        # Unattempted first, then oldest. A large timed-out category cannot starve others.
        ordered = sorted(paths, key=lambda p: (categories[str(p)].get('time') or 0, str(p)))
        save(progress_path, project())
        for path in ordered[:max_items]:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                break
            old = categories[str(path)]
            measured = _measure(path, now=now, timeout=min(3, remaining))
            if measured.get('status') != 'COMPLETE':
                historical = old if old.get('status') == 'COMPLETE' else old.get('previous_complete')
                if historical:
                    measured['previous_complete'] = historical
            categories[str(path)] = measured
            save(progress_path, project())
        result = project()
        save(progress_path, result)
        return result
    except budget.Expired:
        raise
    except OSError as exc:
        out['errors'].append(type(exc).__name__)
        return dict(out, status='PARTIAL')


def _compare(today, previous, now):
    """Only comparable complete readings within a bounded actual-time window."""
    result = dict(today, signal="UNKNOWN", delta_bytes=None, gib_per_day=None,
                  compared_to_time=None)
    if today.get("status") != "COMPLETE":
        return result
    if not isinstance(previous, dict) or previous.get("status") != "COMPLETE":
        return dict(result, signal="BASELINE")
    if today.get('scope') == 'SEQUENTIAL_WORKSPACE':
        return dict(result, signal='BASELINE')
    dt = today.get('time', now) - previous.get("time", 0)
    if (previous.get("path") != today["path"] or
            previous.get("device") != today["device"] or
            previous.get("scope", "FULL_WORKSPACE") != today.get("scope", "FULL_WORKSPACE") or
            previous.get("selected_paths") != today.get("selected_paths") or
            not 18 * 3600 <= dt <= 72 * 3600):
        return dict(result, signal="BASELINE")
    delta = today["allocated_bytes"] - previous["allocated_bytes"]
    rate = round(delta * 86400 / dt / _GIB, 3)
    return dict(result, signal="HIGH_GROWTH" if rate >= 2 else "NORMAL",
                delta_bytes=delta, gib_per_day=rate,
                compared_to_time=previous["time"])


def _category_changes(today, previous, now):
    """Compare matching dates even if new work changes the selected folder set."""
    prior = {c['path']: c for c in (previous or {}).get('categories', [])}
    return [_compare(c, prior.get(c['path']), now) for c in today.get('categories', [])]


def _low_load(snapshot):
    """Skip expensive IO when memory pressure, CPU load or disk space is bad."""
    if (snapshot.get('memory_policy') or {}).get('status') == 'REVIEW':
        return False
    try:
        probe = snapshot["evidence"]["pressure"]
        pressure = probe["output"].strip()
        load = float(snapshot["load"][0])
        free = int(snapshot["disk_free"])
        return (probe["code"] == 0 and pressure == "1" and
                load < (os.cpu_count() or 1) * 0.7 and free >= 15 * _GIB)
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def current(state, load, now=None):
    """Read-only signal for incident reconciliation, with freshness checks."""
    now = time.time() if now is None else now
    day, week, hour = _period(now)
    daily = load(state / "codex-growth-scheduled-latest.json") or {}
    weekly = load(state / "codex-retention-weekly-latest.json") or {}
    signal = (daily.get("signal") if
              daily.get("status") == "COMPLETE" and
              isinstance(daily.get("time"), (int, float)) and
              0 <= now - daily["time"] <= 36 * 3600 else "UNKNOWN")
    weekly_signal = ("REVIEW" if weekly.get("status") == "COMPLETE" and
                     weekly.get("review_eligible_allocated_bytes", 0) >= _WEEKLY_THRESHOLD
                     and isinstance(weekly.get("time"), (int, float)) and
                     0 <= now - weekly["time"] <= 8 * 86400 else "UNKNOWN")
    if (weekly.get("status") == "COMPLETE" and
            weekly.get("review_eligible_allocated_bytes", 0) < _WEEKLY_THRESHOLD and
            isinstance(weekly.get("time"), (int, float)) and
            0 <= now - weekly["time"] <= 8 * 86400):
        weekly_signal = "NORMAL"
    return {"signal": signal, "gib_per_day": daily.get("gib_per_day") if signal != "UNKNOWN" else None,
            "scope": daily.get('scope', 'FULL_WORKSPACE'),
            "category_changes": daily.get('category_changes', []) if signal != 'UNKNOWN' else [],
            "measurement_freshness": ('UNKNOWN' if not isinstance(daily.get('time'), (int, float)) or now < daily['time'] else 'FRESH' if now-daily['time'] <= 36*3600 else 'STALE'),
            "coverage_as_of": daily.get('time'),
            "measurement_status": daily.get('status', 'UNKNOWN'),
            "measurement_age_seconds": now-daily['time'] if isinstance(daily.get('time'), (int, float)) else None,
            "coverage": daily.get('coverage'),
            "inventory_complete": daily.get('inventory_complete'),
            "measured_allocated_bytes": daily.get('measured_allocated_bytes'),
            "measurement_errors": daily.get('errors', []),
            "weekly_signal": weekly_signal,
            "review_eligible_allocated_bytes": weekly.get("review_eligible_allocated_bytes", 0)
            if weekly_signal != "UNKNOWN" else None}


def run_due(state, snapshot, load, save, now=None, *,
            sample_fn=None, preview_fn=None, light_fn=None):
    """One daily and one weekly attempt per calendar period; fail closed.

    Daily and weekly receipts are claimed BEFORE expensive IO, so an interrupted
    job cannot repeatedly saturate the Mac. Missing or partial data never alerts.
    """
    now = time.time() if now is None else now
    day, week, hour = _period(now)
    output = {"daily": "NOT_DUE", "weekly": "NOT_DUE"}
    if hour < 4:
        return output
    daily_claim = state / "codex-growth-daily-claim.json"
    weekly_claim = state / "codex-retention-weekly-claim.json"
    if (load(daily_claim) or {}).get("period") != day:
        # Reduced mode is independent of free-space threshold. Critical or unknown
        # pressure still avoids directory IO; the enclosing tick retains deferral.
        full = _low_load(snapshot)
        probe = snapshot.get('evidence', {}).get('pressure', {})
        light_ok = probe.get('code') == 0 and probe.get('output', '').strip() in ('1', '2')
        if not full and not light_ok:
            output["daily"] = "DEFERRED_CRITICAL_OR_UNKNOWN_PRESSURE"
        else:
            budget.check(5)
            save(daily_claim, {"period": day, "started_at": now, "status": "RUNNING"})
            prior = (load(state / "codex-growth-previous-slice.json") or
                     load(state / "codex-growth-last-complete.json"))
            sampler = sample_fn if full else light_fn
            measured = (sampler(_WORKSPACE, now=now) if sampler is not None else
                        _sequential_measure(_WORKSPACE, state, load, save, now=now,
                                            seconds=_DAILY_LIMIT if full else 12))
            result = _compare(measured, prior, now)
            if not full or measured.get('scope') == 'SEQUENTIAL_WORKSPACE':
                result['category_changes'] = _category_changes(measured, prior, now)
                growth = [c for c in result['category_changes'] if c['signal'] == 'HIGH_GROWTH']
                if measured['status'] == 'COMPLETE' and growth:
                    result.update(signal='HIGH_GROWTH', gib_per_day=max(c['gib_per_day'] for c in growth),
                                  signal_scope='SINGLE_DATE_FOLDER')
            result['scan_mode'] = 'FULL' if full else 'LIGHT'
            save(state / "codex-growth-scheduled-latest.json", result)
            if result["status"] == "COMPLETE":
                save(state / "codex-growth-last-complete.json", result)
            # Keep category evidence across partial slices without replacing the complete baseline.
            save(state / "codex-growth-previous-slice.json", result)
            save(state / f"codex-growth-scheduled-{day}.json", result)
            save(daily_claim, {"period": day, "started_at": now, "status": result["status"]})
            output["daily"] = result["status"]
            # Retain own complete/partial growth receipts for up to 35 days.
            for p in state.glob("codex-growth-scheduled-????-??-??.json"):
                if p.stat().st_mtime < now - 35 * 86400:
                    p.unlink()
    # A weekly preview is admitted only when daily IO isn't running this tick.
    if (load(weekly_claim) or {}).get("period") != week:
        if output["daily"] != "NOT_DUE" or not _low_load(snapshot):
            output["weekly"] = "DEFERRED_LOAD_OR_DAILY"
        else:
            budget.check(5)
            save(weekly_claim, {"period": week, "started_at": now, "status": "RUNNING"})
            if preview_fn is None:
                preview_fn = mac_codex_retention.preview
            result = preview_fn(now=now, seconds=budget.timeout(_WEEKLY_LIMIT))
            save(state / "codex-retention-weekly-latest.json", result)
            budget.check(5)
            save(weekly_claim, {"period": week, "started_at": now,
                                "status": result.get("status", "UNKNOWN")})
            output["weekly"] = result.get("status", "UNKNOWN")
    return output
