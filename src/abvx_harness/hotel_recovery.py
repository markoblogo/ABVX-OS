"""Bounded supervisor around the owner's existing, hash-qualified portal adapter."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import ssl
import subprocess
import sys
import time
import urllib.error
from .mac_operator import STATE, ROOT, save, load

ADAPTER = Path.home() / 'Library/Application Support/CodexAwake/hotspot-reconnect.py'
ADAPTER_HASH = '27fa806c7f23bb996336fe2770aff649ebf88fe962dd06ef0f40810e5569535a'
REASONS = {'unapproved_redirect', 'duplicate_login_form', 'expected_email_form_not_present',
           'unsupported_authentication_type', 'additional_required_field', 'custom_consent_form',
           'unapproved_form_destination', 'unapproved_destination'}
OUTCOMES = {'internet_restored', 'already_authenticated', 'form_unavailable',
            'portal_rejected_login', 'login_submitted_internet_unconfirmed',
            'outside_configured_hotel_network'}
CHECK_INTERVAL = 15
RETRY_DELAYS = (0, 60, 120)


def record(state, event, now, cause=None):
    events = list(state.get('events', []))[-19:]
    item = {'time': now, 'event': event}
    if cause:
        item['reason'] = cause
    events.append(item)
    state['events'] = events


def reason(exc):
    if type(exc) is ValueError and len(exc.args) == 1 and exc.args[0] in REASONS:
        return exc.args[0]
    if isinstance(exc, urllib.error.HTTPError):
        return 'http_' + str(exc.code) if type(exc.code) is int else 'http_error'
    if isinstance(exc, ssl.SSLError):
        return 'tls_error'
    if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)):
        return 'timeout'
    if isinstance(exc, urllib.error.URLError):
        return 'network_transport_error'
    return 'unexpected_error'  # No raw exception URLs, form values or tokens.


def step(adapter, state, persist, now):
    """One bounded observation. Persist a spent slot before any login effect."""
    state = dict(state)
    state.update(schema_version='v1', time=now, attempt_limit=3)
    try:
        online = adapter.online()
    except Exception as exc:
        state.update(status='PROBE_ERROR', internet='UNKNOWN', last_reason=reason(exc))
        last = state.get('events', [])[-1:]
        if not last or last[0].get('event') != 'probe_error' or last[0].get('reason') != reason(exc):
            record(state, 'probe_error', now, reason(exc))
        persist(state)
        return state  # Probe execution failure is not permission to submit a login.
    state['internet'] = 'ONLINE' if online else 'UNAVAILABLE'
    if online:
        if state.get('status') != 'ONLINE':
            record(state, 'online', now)
        state.update(status='ONLINE', attempts=0, failed_probes=0, last_reason=None,
                     last_attempt=0, offline_since=None, outside_until=0)
    else:
        if state.get('offline_since') is None:
            state['offline_since'] = now
            record(state, 'offline', now)
        state['failed_probes'] = state.get('failed_probes', 0) + 1
        if state.get('attempts', 0) >= 3:
            state['status'] = 'PAUSED'
        elif state['failed_probes'] >= 2 and now >= state.get('outside_until', 0) and (not state.get('last_attempt') or
                now >= state['last_attempt'] + RETRY_DELAYS[state.get('attempts', 0)]):
            state.update(status='ATTEMPTING', attempts=state.get('attempts', 0) + 1,
                         last_attempt=now, last_reason='interrupted_or_unconfirmed_attempt')
            record(state, 'attempt_started', now)
            persist(state)  # Crash/restart never replenishes the attempt budget.
            try:
                outcome = adapter.reconnect()
                state['last_reason'] = outcome if outcome in OUTCOMES else 'unknown_adapter_result'
                record(state, 'attempt_result', now, state['last_reason'])
                if outcome == 'outside_configured_hotel_network':
                    state['attempts'] -= 1  # No form submitted; leave rate limit in place.
                    state['last_attempt'] = now
                    state['outside_until'] = now + 300
                # Verify independently, including "already authenticated" outcomes.
                if adapter.online():
                    record(state, 'online', now)
                    state.update(status='ONLINE', internet='ONLINE', attempts=0, failed_probes=0,
                                 last_attempt=0, offline_since=None, outside_until=0)
                else:
                    state['status'] = 'PAUSED' if state['attempts'] >= 3 else 'WAITING'
            except Exception as exc:
                state.update(last_reason=reason(exc), status='PAUSED' if state['attempts'] >= 3 else 'WAITING')
                record(state, 'attempt_error', now, state['last_reason'])
        else:
            state['status'] = 'WAITING'
    state['time'] = now
    persist(state)
    return state


def adapter_module():
    if ADAPTER.is_symlink() or hashlib.sha256(ADAPTER.read_bytes()).hexdigest() != ADAPTER_HASH:
        raise ValueError('adapter_changed_requires_review')
    spec = importlib.util.spec_from_file_location('owner_hotel_adapter', ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare():
    adapter_module()  # Verify reviewed source before producing an install packet.
    data = {'Label': 'io.abvx.hotel-wifi-reconnect',
            'ProgramArguments': [sys.executable, '-m', 'abvx_harness.hotel_recovery'],
            'WorkingDirectory': str(ROOT), 'EnvironmentVariables': {'PYTHONPATH': str(ROOT / 'src')},
            'KeepAlive': True, 'RunAtLoad': True, 'ThrottleInterval': 60,
            'ProcessType': 'Background', 'Umask': 63,
            'StandardOutPath': '/dev/null', 'StandardErrorPath': '/dev/null'}
    path = STATE / 'hotel-recovery.plist'
    path.write_bytes(plistlib.dumps(data))
    print(path)


def main():
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ['--prepare-install']:
        prepare()
        return
    if sys.argv[1:]:
        raise SystemExit('Only --prepare-install is supported.')
    # Share the original lock to prevent old/new executors overlapping.
    with (ADAPTER.parent / 'hotspot.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        adapter = adapter_module()
        path = STATE / 'network-recovery.json'
        state = load(path)
        if state is None and path.exists():
            raise SystemExit('Unreadable recovery state; inspect before resetting budget.')
        state = state or {'attempts': 0, 'failed_probes': 0}
        if (state.get('schema_version', 'v1') != 'v1' or
                type(state.get('attempts')) is not int or not 0 <= state['attempts'] <= 3 or
                type(state.get('failed_probes')) is not int or state['failed_probes'] < 0 or
                type(state.get('last_attempt', 0)) not in (int, float)):
            raise SystemExit('Invalid recovery state; inspect before resetting budget.')
        while True:
            state = step(adapter, state, lambda value: save(path, value), time.time())
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
