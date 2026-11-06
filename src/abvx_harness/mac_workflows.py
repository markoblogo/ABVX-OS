"""Read-only fixed workflow projections and explicit local handoff receipts."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import re
import fcntl
from .process_learning import digest
import tomllib
from zoneinfo import ZoneInfo

WORKFLOWS = {
    'radar': {'automation': 'multi-market-radar-monday', 'hour': 8,
              'runs': '.tmp/multi-market-radar/runs',
              'playbook': 'docs/playbooks/multi-market-radar-weekly-v1.md'},
    'youtube': {'automation': None, 'hour': 9,
                'runs': '.tmp/youtube-intelligence/runs',
                'playbook': 'docs/playbooks/youtube-intelligence-weekly-v1.md'},
}


def read(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def scheduler(home, automation_id):
    """Private app database is optional evidence only. Never write its schema/state."""
    if not automation_id:
        return {'status': 'NOT_CONFIGURED'}
    try:
        path = home / '.codex/automations' / automation_id / 'automation.toml'
        d = tomllib.loads(path.read_text())
        result = {'status': 'UNKNOWN', **{k: d[k] for k in ('id', 'status', 'rrule') if k in d}}
    except (OSError, ValueError):
        return {'status': 'UNKNOWN'}
    db = None
    try:
        db = sqlite3.connect((home / '.codex/sqlite/codex-dev.db').as_uri() + '?mode=ro', uri=True, timeout=1)
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT last_run_at,next_run_at,target_thread_id FROM automations WHERE id=?', (automation_id,)).fetchone()
        if row:
            result.update(dict(row))
            result['target_attempt'] = attempt_status(home, row['target_thread_id'], row['last_run_at'])
        result['attempt_evidence'] = 'local-app-database; attempt is not completion'
    except sqlite3.Error:
        result['attempt_evidence'] = 'UNAVAILABLE'
    finally:
        if db:
            db.close()
    return result


def attempt_status(home, thread_id, attempt_ms):
    if not thread_id or not attempt_ms:
        return {'status': 'UNKNOWN'}
    db = None
    try:
        db = sqlite3.connect((home / '.codex/state_5.sqlite').as_uri() + '?mode=ro', uri=True, timeout=1)
        row = db.execute('SELECT rollout_path FROM threads WHERE id=?', (thread_id,)).fetchone()
        if not row:
            return {'status': 'UNKNOWN'}
        path = Path(row[0])
        # Read only event types and timestamps, never retain conversation contents.
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 4 * 1024 * 1024))
            lines = stream.read().decode('utf-8', errors='replace').splitlines()
        events = []
        for line in lines:
            try:
                value = json.loads(line)
                payload = value.get('payload', {})
                if value.get('type') != 'event_msg' or payload.get('type') not in ('task_started', 'task_complete', 'turn_aborted'):
                    continue
                stamp = datetime.fromisoformat(value['timestamp'].replace('Z', '+00:00')).timestamp()
                if attempt_ms / 1000 - 60 <= stamp <= attempt_ms / 1000 + 24 * 3600:
                    events.append({'time': stamp, 'event': payload['type']})
            except (ValueError, KeyError, TypeError):
                continue
        last = events[-1] if events else None
        return {'status': {'turn_aborted': 'INTERRUPTED', 'task_complete': 'TURN_FINISHED_NOT_DOMAIN_PROOF',
                           'task_started': 'STARTED_NO_TERMINAL_EVENT'}.get(last['event'], 'UNKNOWN') if last else 'UNKNOWN',
                'events': events[-4:], 'source': 'bounded target-thread event metadata'}
    except (OSError, sqlite3.Error):
        return {'status': 'UNKNOWN'}
    finally:
        if db:
            db.close()


def required_files(root, workflow, run):
    if workflow == 'radar':
        files = [run / n for n in ('execution.json', 'acquisition.json', 'ranking.json', 'REPORT.md')]
        snap = root / '.tmp/multi-market-radar/learning/snapshots' / (run.name + '--REVIEWED.json')
        d = read(snap) or {}
        if d.get('stage') != 'REVIEWED' or d.get('run_id') != run.name or d.get('source_run') != str(run):
            return files, ['matching REVIEWED learning snapshot']
        expected = digest({k: v for k, v in d.items() if k not in {'recorded_at', 'record_digest'}})
        if d.get('record_digest') != expected:
            return files, ['learning snapshot integrity']
        return files + [snap], []
    files = [run / n for n in ('execution.json', 'acquisition.json', 'research.json', 'analysis.json', 'REPORT.md')]
    return files, []


def run_receipt(root, workflow, run, now):
    d = read(run / 'execution.json')
    if not isinstance(d, dict):
        return {'run': run.name, 'status': 'INVALID_RECEIPT', 'completed_at': None}
    value = d.get('completed_at_utc') if workflow == 'radar' else d.get('captured_at')
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp.timestamp() > now + 60:
            raise ValueError('invalid date')
        stamp = stamp.timestamp()
    except (ValueError, TypeError, AttributeError):
        stamp = None
    files, missing = required_files(root, workflow, run)
    missing += [p.name for p in files if not p.is_file() or p.stat().st_size == 0]
    if workflow == 'youtube':
        for filename, field in [('acquisition.json', 'acquisition_digest'), ('research.json', 'research_digest')]:
            payload = read(run / filename)
            if payload is None or digest(payload) != d.get(field):
                missing.append(field + ' integrity')
    complete = d.get('execution' if workflow == 'radar' else 'status') == 'COMPLETE'
    return {'run': run.name, 'path': str(run), 'completed_at': stamp,
            'status': 'EVIDENCE_PRESENT' if complete and not missing and stamp else 'INCOMPLETE_OR_BLOCKED',
            'receipt_status': d.get('execution', d.get('status')), 'missing': missing,
            'note': 'Presence/binding check only; original domain validators and analyst acceptance still apply.'}


def project(root, home=None, now=None):
    home, now = home or Path.home(), now or time.time()
    output = {}
    for key, spec in WORKFLOWS.items():
        schedule = scheduler(home, spec['automation'])
        runs = [run_receipt(root, key, p.parent, now) for p in (root / spec['runs']).glob('*/execution.json')]
        runs.sort(key=lambda r: r['completed_at'] or 0, reverse=True)
        accepted = next((r for r in runs if r['status'] == 'EVIDENCE_PRESENT'), None)
        latest = runs[0] if runs else None
        local = datetime.fromtimestamp(now, ZoneInfo('Europe/Paris'))
        expected = (local - timedelta(days=local.weekday())).replace(hour=spec['hour'], minute=0, second=0, microsecond=0)
        if expected.timestamp() > now:
            expected -= timedelta(days=7)
        # Only the fixed Radar schedule is known. Unknown/custom recurrence fails closed.
        recurrence = str(schedule.get('rrule', '')).upper().removeprefix('RRULE:')
        known = key == 'radar' and all(x in recurrence.split(';') for x in ('FREQ=WEEKLY', 'BYDAY=MO', 'BYHOUR=8', 'BYMINUTE=0'))
        if schedule['status'] == 'NOT_CONFIGURED':
            status = 'NOT_SCHEDULED'
        elif schedule['status'] != 'ACTIVE' or not known:
            status = 'UNKNOWN_OR_INACTIVE_SCHEDULE'
        elif accepted and accepted['completed_at'] >= expected.timestamp():
            status = 'CURRENT_EVIDENCE'
        elif now > expected.timestamp() + 6 * 3600:
            status = 'OVERDUE_EVIDENCE'
        else:
            status = 'WITHIN_GRACE'
        attempt = schedule.get('last_run_at')
        attempt = attempt / 1000 if isinstance(attempt, (int, float)) else None
        output[key] = {'status': status, 'schedule': schedule, 'expected_at': expected.isoformat() if known else None,
                       'grace_hours': 6, 'latest_receipt': latest, 'latest_evidence': accepted,
                       'attempt_without_accepted_completion': bool(attempt and (not accepted or attempt > accepted['completed_at'] + 60)),
                       'cause': ('INTERRUPTED_CODEX_TURN' if schedule.get('target_attempt', {}).get('status') == 'INTERRUPTED' else 'UNKNOWN; inspect target task/app logs') if attempt and (not accepted or attempt > accepted['completed_at'] + 60) else None}
    return output


def _enqueue(root, state, workflow, request_id, save):
    if workflow not in WORKFLOWS:
        raise ValueError('unsupported workflow')
    folder = state / 'handoffs'
    folder.mkdir(exist_ok=True, mode=0o700)
    # One open request per workflow; no repeated expensive research admission.
    for p in folder.glob('*.json'):
        existing = read(p) or {}
        if existing.get('workflow') == workflow and existing.get('status') in ('WAITING_FOR_CODEX', 'CLAIMED'):
            return {'status': 'ALREADY_PENDING', 'handoff': str(p), 'research_started': False}
    key = hashlib.sha256(request_id.encode()).hexdigest()
    item = {'schema_version': 'v1', 'workflow': workflow, 'request_id': request_id, 'created_at': time.time(),
            'status': 'WAITING_FOR_CODEX', 'playbook': WORKFLOWS[workflow]['playbook'],
            'reason': 'No supported authenticated local Codex dispatch API is available to this background process.',
            'research_started': False, 'automatic_retry': False}
    save(folder / (key + '.json'), item)
    return {**item, 'handoff': str(folder / (key + '.json'))}


def enqueue(root, state, workflow, request_id, save):
    with (state / 'handoffs.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _enqueue(root, state, workflow, request_id, save)


def transition(root, state, handoff_id, operation, save, run_id=None):
    if not re.fullmatch('[a-f0-9]{64}', handoff_id):
        raise ValueError('invalid handoff ID')
    with (state / 'handoffs.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = state / 'handoffs' / (handoff_id + '.json')
        item = read(path)
        if not item or item.get('workflow') not in WORKFLOWS:
            raise ValueError('unknown handoff')
        if operation == 'claim':
            if item['status'] != 'WAITING_FOR_CODEX':
                return {'status': 'ALREADY_CLAIMED_OR_TERMINAL', 'research_started': False}
            item.update(status='CLAIMED', claimed_at=time.time(), research_started=False)
        elif operation == 'complete':
            if item['status'] != 'CLAIMED':
                raise ValueError('claim handoff before binding results')
            if not run_id or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]{0,119}', run_id):
                raise ValueError('invalid run ID')
            run = root / WORKFLOWS[item['workflow']]['runs'] / run_id
            if run.is_symlink():
                raise ValueError('symlinked run forbidden')
            receipt = run_receipt(root, item['workflow'], run, time.time())
            if receipt['status'] != 'EVIDENCE_PRESENT' or receipt['completed_at'] < item['created_at']:
                return {'status': 'BLOCKED_RESULT_EVIDENCE', 'receipt': receipt}
            item.update(status='RESULT_EVIDENCE_BOUND', result=receipt, research_started=True)
        elif operation == 'cancel':
            if item['status'] == 'RESULT_EVIDENCE_BOUND':
                raise ValueError('completed handoff cannot be cancelled')
            item.update(status='CANCELLED', cancelled_at=time.time())
        else:
            raise ValueError('invalid operation')
        save(path, item)
        return item
