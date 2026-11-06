#!/usr/bin/env python3
"""Internal-disk bootstrap for the EXISTING ABVX Mac observer.

Read-only scheduler inventory, durable readiness signals, no model execution,
no scheduler database writes, no new scheduled task and no fabricated delivery.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import tomllib
from zoneinfo import ZoneInfo

SETTINGS = Path(__file__).with_name('recovery-settings.json')
BASE = Path(json.loads(SETTINGS.read_text())['data_root']) if SETTINGS.exists() else Path(__file__).resolve().parent
REPO = Path('/Volumes/Work/Work/ABVX-OS')
STATE = BASE / 'mac-schedule-recovery'
RADAR = {'id': '6ac7d62767d08191ac7c88cca5455369', 'name': 'Nantes Radar — единый обзор',
         'rrule': 'FREQ=DAILY;BYHOUR=10;BYMINUTE=0;BYSECOND=0', 'status': 'ACTIVE',
         'url': 'https://chatgpt.com/scheduled', 'kind': 'hosted', 'cwds': [str(REPO)],
         'target_thread_id': None}


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.recovery-')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def nominal(rule, now):
    """Only the actual simple fixed local rules are understood; unknown fails closed."""
    text = rule.removeprefix('RRULE:')
    fields = dict(part.split('=', 1) for part in text.split(';') if '=' in part)
    if '\n' in rule or set(fields) - {'FREQ', 'BYDAY', 'BYHOUR', 'BYMINUTE', 'BYSECOND', 'INTERVAL'}:
        return None
    if fields.get('FREQ') not in ('DAILY', 'WEEKLY') or fields.get('INTERVAL', '1') != '1':
        return None
    if fields.get('FREQ') == 'WEEKLY' and 'BYDAY' not in fields:
        return None  # An unspecified DTSTART weekday is not evidence of every day.
    try:
        hour, minute = int(fields['BYHOUR']), int(fields['BYMINUTE'])
        second = int(fields.get('BYSECOND', '0'))
        days = fields.get('BYDAY', 'MO,TU,WE,TH,FR,SA,SU').split(',')
        valid = ('MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU')
        if any(day not in valid for day in days):
            return None
        local = datetime.fromtimestamp(now, ZoneInfo('Europe/Paris'))
        for offset in range(8):
            candidate = (local - timedelta(days=offset)).replace(hour=hour, minute=minute, second=second, microsecond=0)
            if valid[candidate.weekday()] in days and candidate.timestamp() <= now:
                return candidate.timestamp()
    except (ValueError, KeyError):
        return None


def inventory(home):
    jobs = []
    db = None
    try:
        db = sqlite3.connect((home / '.codex/sqlite/codex-dev.db').as_uri() + '?mode=ro', uri=True, timeout=1)
        db.row_factory = sqlite3.Row
        for row in db.execute('SELECT id,name,status,rrule,last_run_at,next_run_nominal_at,target_thread_id,cwds,created_at FROM automations'):
            job = dict(row)
            try:
                job['cwds'] = json.loads(job['cwds'] or '[]')
            except ValueError:
                job['cwds'] = []
                job['dependency_status'] = 'UNKNOWN'
            job['kind'] = 'local'
            jobs.append(job)
    except (sqlite3.Error, OSError):
        # TOML confirms saved configuration but cannot prove an attempt.
        for path in (home / '.codex/automations').glob('*/automation.toml'):
            try:
                item = tomllib.loads(path.read_text())
                jobs.append({k: item[k] for k in ('id', 'name', 'status', 'rrule', 'target_thread_id') if k in item} |
                            {'kind': 'local', 'dependency_status': 'UNKNOWN', 'cwds': []})
            except (OSError, ValueError):
                continue
    finally:
        if db:
            db.close()
    return jobs


def assess(job, now, exists=lambda path: Path(path).is_dir(), journal_root=BASE / 'nantes-radar-journal'):
    expected = nominal(job.get('rrule', ''), now)
    missing = [p for p in job.get('cwds', []) if not exists(p)]
    result = {k: job.get(k) for k in ('id', 'name', 'kind', 'target_thread_id')}
    result.update(expected_at=expected, missing_paths=missing, observed_at=now)
    if job.get('status') != 'ACTIVE':
        result['status'] = 'INACTIVE'
    elif expected is not None and job.get('created_at', 0) / 1000 > expected:
        result['status'] = 'NOT_YET_DUE'
    elif expected is None or job.get('dependency_status') == 'UNKNOWN':
        result['status'] = 'UNKNOWN_SCHEDULE_OR_DEPENDENCIES'
    elif missing:
        result['status'] = 'WAITING_FOR_PATHS'
    elif now < expected + 900:
        result['status'] = 'WITHIN_GRACE'
    elif job['kind'] == 'hosted':
        date = datetime.fromtimestamp(expected, ZoneInfo('Europe/Paris')).date().isoformat()
        weekly = datetime.fromtimestamp(expected, ZoneInfo('Europe/Paris')).weekday() == 0
        run = date + ('-weekly' if weekly or date == '2026-10-27' else '-daily')
        saved = read(journal_root / run / 'state.json')
        pub = (saved or {}).get('publication', {}).get('status')
        retry_pending = any(item.get('status') in ('NOT_STARTED', 'IN_PROGRESS') or
                            (item.get('status') in ('PARTIAL', 'BLOCKED', 'FAILED') and item.get('retryable') is True
                             and len(item.get('attempts', [])) < 2)
                            for item in (saved or {}).get('stages', {}).values())
        result['run_id'] = run
        result['status'] = ('READY_TO_RESUME' if retry_pending else 'DELIVERY_RECORDED') if pub == 'PUBLISHED' else ('VERIFY_DELIVERY' if pub == 'PREPARED' else 'READY_TO_RESUME')
        result['retry_pending'] = retry_pending
    elif job.get('last_run_at') is None:
        result['status'] = 'ATTEMPT_UNKNOWN'
    elif job['last_run_at'] / 1000 >= expected:
        result['status'] = 'ATTEMPT_RECORDED_COMPLETION_UNKNOWN'
    else:
        result['status'] = 'READY_TO_RESUME'
    result['dispatch'] = 'BLOCKED_NO_SUPPORTED_HOSTED_TRIGGER' if job['kind'] == 'hosted' else 'BLOCKED_NO_CONNECTED_APP_SERVER'
    return result


def tick(repo=REPO, state=STATE, home=None, now=None, run_observer=True, notify=False, journal_root=BASE / 'nantes-radar-journal', source='manual'):
    home, now = home or Path.home(), now or time.time()
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / 'bootstrap.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'ALREADY_RUNNING'}
        ready = (repo / 'bin/mac-operator').is_file()
        jobs = inventory(home)
        jobs.append(RADAR | {'cwds': [str(repo)]})
        checks = [assess(job, now, journal_root=journal_root) for job in jobs]
        latest = state / ('latest.json' if source == 'scheduled' else 'latest-manual.json')
        previous = read(latest) or {}
        signals = []
        for check in checks:
            key = hashlib.sha256(f"{check['id']}:{check['expected_at']}".encode()).hexdigest()
            path = state / 'signals' / (key + '.json')
            if check['status'] == 'DELIVERY_RECORDED' and path.exists():
                prior = read(path)
                if prior and prior.get('delivery') == 'PENDING_OPERATOR_REVIEW':
                    save(path, prior | {'delivery': 'REPORT_RECEIPT_OBSERVED', 'resolved_at': now})
            if check['status'] not in ('READY_TO_RESUME', 'VERIFY_DELIVERY'):
                continue
            if not path.exists():
                save(path, check | {'signal_id': key, 'created_at': now, 'delivery': 'PENDING_OPERATOR_REVIEW',
                                    'research_started': False})
                signals.append(key)
        snapshot = {'version': 1, 'source': source, 'observed_at': now, 'repository_ready': ready,
                    'previous_observed_at': previous.get('observed_at'),
                    'observation_gap_seconds': now - previous['observed_at'] if previous.get('observed_at') else None,
                    'checks': checks, 'new_signals': signals,
                    'dispatch_status': 'BLOCKED_NO_SUPPORTED_DISPATCH', 'new_scheduled_tasks': 0}
        # Persist readiness before invoking any external-volume code.
        save(latest, snapshot)
        if notify and signals:
            # Existing observer notification channel, one notification per occurrence.
            text = f'ABVX: Mac и проекты доступны. Задач для восстановления: {len(signals)}. Сигнал сохранён; автоматическая передача в ChatGPT пока недоступна.'
            try:
                subprocess.run(['/usr/bin/osascript', '-e', 'on run argv\ndisplay notification (item 1 of argv) with title "ABVX — восстановление задач"\nend run', text], timeout=10, capture_output=True)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if ready and run_observer:
            env = dict(os.environ, PYTHONPATH=str(repo / 'src'))
            try:
                proc = subprocess.run([sys.executable, '-m', 'abvx_harness.mac_operator', 'daemon'], cwd=repo, env=env, timeout=150, capture_output=True)
                snapshot['observer'] = {'exit_code': proc.returncode, 'checked_at': time.time()}
            except (OSError, subprocess.TimeoutExpired) as exc:
                snapshot['observer'] = {'error_type': type(exc).__name__, 'checked_at': time.time()}
        else:
            snapshot['observer'] = {'status': 'NOT_RUN' if ready else 'WAITING_FOR_VOLUME'}
        save(latest, snapshot)
        return snapshot


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--state', type=Path, default=STATE)
    parser.add_argument('--observe-only', action='store_true')
    args = parser.parse_args()
    source = 'scheduled' if os.environ.get('XPC_SERVICE_NAME') == 'xyz.abvx.mac-operator' else 'manual'
    result = tick(args.repo, args.state, run_observer=not args.observe_only, notify=not args.observe_only, source=source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
