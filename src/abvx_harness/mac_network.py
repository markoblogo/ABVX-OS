"""Read-only bridge to the existing hotel reconnect agent. Never submits forms."""
from pathlib import Path
import json
import re
import time

LABEL = 'io.abvx.hotel-wifi-reconnect'
EVENTS = {'monitor_started', 'internet_online', 'internet_unavailable',
          'internet_restored', 'outside_configured_hotel_network',
          'already_authenticated', 'form_unavailable', 'portal_rejected_login',
          'login_submitted_internet_unconfirmed'}


def inspect(jobs, folder=None, recovery_path=None, now=None):
    folder = folder or Path.home() / 'Library/Application Support/CodexAwake'
    job = next((j for j in jobs if j['label'] == LABEL), None)
    evidence = job.get('evidence', {}) if job else {}
    running = (evidence.get('code') == 0 and
               re.search(r'^\s*state = running\s*$', evidence.get('output', ''), re.M) is not None)
    events = []
    log = folder / 'hotspot.log'
    try:
        if log.is_symlink():
            raise ValueError('symlink')
        with log.open('rb') as stream:
            stream.seek(0, 2)
            size = stream.tell()
            stream.seek(max(0, size - 32768))
            lines = stream.read(32768).decode('utf-8', errors='replace').splitlines()
        for line in lines:
            match = re.fullmatch(r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) (\w+)', line)
            if match and (match[2] in EVENTS or re.fullmatch(r'reconnect_failed_[A-Za-z]+Error', match[2])):
                events.append({'local_timestamp': match[1], 'event': match[2]})
        log_status = 'READ'
    except (OSError, ValueError):
        log_status = 'UNAVAILABLE'
    connectivity = [e for e in events if e['event'] in
                    ('internet_online', 'internet_unavailable', 'internet_restored')]
    recovery = {'status': 'NOT_ACTIVATED', 'current_internet': 'UNKNOWN'}
    if 'abvx_harness.hotel_recovery' in evidence.get('output', ''):
        recovery = {'status': 'UNKNOWN', 'current_internet': 'UNKNOWN'}
        path = recovery_path or Path(__file__).resolve().parents[2] / '.tmp/mac-operator/network-recovery.json'
        try:
            if path.is_symlink() or path.stat().st_size > 8192:
                raise ValueError('invalid state')
            data = json.loads(path.read_text())
            age = (time.time() if now is None else now) - data['time']
            recovery['receipt_age_seconds'] = age
            if age > 180:
                recovery['status'] = 'STALE'
            if data['schema_version'] == 'v1' and 0 <= age <= 180:
                recovery.update({k: data.get(k) for k in ('status', 'attempts', 'attempt_limit', 'last_reason', 'offline_since')})
                recovery['current_internet'] = data.get('internet', 'UNKNOWN')
                recovery['offline_seconds'] = max(0, (time.time() if now is None else now) - data['offline_since']) if isinstance(data.get('offline_since'), (int, float)) else None
                recovery['recent_events'] = data.get('events', [])[-20:]
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return {'service': LABEL, 'service_status': 'RUNNING' if running else 'UNKNOWN_OR_STOPPED',
            'log_status': log_status, 'recent_events': events[-8:],
            'last_connectivity_event': connectivity[-1] if connectivity else None,
            'current_internet': recovery['current_internet'], 'bounded_recovery': recovery,
            'form_submission_by_operator': False,
            'note': 'Transition-only log is historical, not a live connectivity probe. Existing agent alone owns reconnect attempts.'}
