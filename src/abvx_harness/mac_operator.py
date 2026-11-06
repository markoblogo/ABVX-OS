"""Bounded, model-free macOS observer. No shell, deletion or arbitrary tasks."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import plistlib
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
import tempfile
from . import mac_budget as budget
from . import mac_workflows, mac_storage, mac_alerts, mac_network, mac_codex_retention, mac_codex_growth, mac_disk_policy

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.tmp/mac-operator'
LABEL = 'xyz.abvx.mac-operator'
ALIASES = {'как там mac?': 'status', 'почему тормозит?': 'slow',
           'проверь radar': 'services', 'что можно почистить?': 'cleanup',
           'запусти недельное исследование': 'weekly', 'проверь youtube': 'services',
           'запусти исследование youtube': 'youtube'}


def command(argv, timeout=12):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=budget.timeout(timeout),
                           env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(Path.home()), 'LC_ALL': 'C'})
        output = (p.stdout + p.stderr)[:18000]
        return {'code': p.returncode if 'Error:' not in output else -1, 'output': output}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'code': None, 'output': type(e).__name__}


def save(path, data):
    fd, name = tempfile.mkstemp(prefix=path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load(path):
    return mac_workflows.read(path)


def services():
    jobs = []
    for p in sorted((Path.home() / 'Library/LaunchAgents').glob('*.plist')):
        try:
            d = plistlib.loads(p.read_bytes())
            label = d.get('Label', '')
            if 'abvx' in label.lower():
                jobs.append({'label': label, 'schedule': {k: d[k] for k in ('StartInterval', 'StartCalendarInterval', 'KeepAlive') if k in d},
                             'evidence': command(['/bin/launchctl', 'print', f'gui/{os.getuid()}/{label}'])})
        except (ValueError, OSError):
            continue
    automations = []
    import tomllib
    for p in (Path.home() / '.codex/automations').glob('*/automation.toml'):
        try:
            d = tomllib.loads(p.read_text())
            if any(x in str(d).lower() for x in ('radar', 'youtube-intelligence')):
                automations.append({k: d[k] for k in ('id', 'name', 'status', 'rrule') if k in d})
        except (ValueError, OSError):
            continue
    runs = ROOT / '.tmp/multi-market-radar/runs'
    receipts = sorted(runs.glob('*/execution.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    return {'launch_agents': jobs, 'network_recovery': mac_network.inspect(jobs), 'codex_schedules': automations,
            'radar_receipts': [{'path': str(p), 'receipt': load(p) or {'status': 'UNREADABLE'}} for p in receipts],
            'note': 'Saved schedules are not proof of punctual execution. No schedule is changed.'}


def diagnose(source="manual"):
    now = time.time()
    internal_path = Path('/System/Volumes/Data') if Path('/System/Volumes/Data').exists() else Path('/')
    disk = shutil.disk_usage(internal_path)
    external = shutil.disk_usage(ROOT)
    disk_identity = str(internal_path)
    probes = {
        'boot': ['/usr/sbin/sysctl', '-n', 'kern.bootsessionuuid'],
        'pressure': ['/usr/sbin/sysctl', '-n', 'kern.memorystatus_vm_pressure_level'],
        'swap': ['/usr/sbin/sysctl', 'vm.swapusage'],
        'vm': ['/usr/bin/vm_stat'],
        'cpu': ['/usr/bin/top', '-l', '1', '-n', '0'],
        'processes': ['/bin/ps', '-axo', 'pid,pcpu,rss,comm', '-r'],
        'thermal': ['/usr/bin/pmset', '-g', 'therm'],
        'network': ['/usr/sbin/scutil', '--nwi'],
    }
    evidence = {k: command(v) for k, v in probes.items()}
    evidence['processes']['output'] = '\n'.join(evidence['processes']['output'].splitlines()[:16])
    memory = command(['/bin/ps', '-axo', 'pid,pcpu,rss,comm', '-m'])
    memory['output'] = '\n'.join(memory['output'].splitlines()[:16])
    evidence['memory_processes'] = memory
    previous = []
    for p in sorted(STATE.glob(f'sample-{source}-*.json'))[-12:]:
        try:
            previous.append(json.loads(p.read_text()))
        except (ValueError, OSError):
            pass
    load = os.getloadavg()
    sustained = len(previous) >= 3 and now - previous[-3].get('time', now) >= 600 and now - previous[-1].get('time', 0) < 600 and all(s['load'][0] > (os.cpu_count() or 1) for s in previous[-3:]) and load[0] > (os.cpu_count() or 1)
    issues = []
    pressure = evidence['pressure']
    if pressure['code'] == 0 and pressure['output'].strip() in ('2', '4'):
        issues.append('Memory pressure elevated; inspect memory_processes and swap trend. Do not kill applications automatically.')
    if sustained:
        issues.append('Load exceeds logical CPU count across four samples; inspect CPU processes before intervention.')
    if disk.free < 10 * 1024**3 or disk.free / disk.total < 0.10:
        issues.append('Internal macOS disk has less than 10 GiB or 10% free; review cleanup preview.')
    unknown = [k for k, v in evidence.items() if v['code'] != 0]
    result = {'schema_version': 'v1', 'time': now, 'source': source, 'pid': os.getpid(), 'load': load,
              'disk_free': disk.free, 'disk_path': disk_identity,
              'disk_total': disk.total,
              'disk_delta': disk.free - previous[-1]['disk_free'] if previous and previous[-1].get('disk_path') == disk_identity else None,
              'repository_disk': {'path': str(ROOT), 'free': external.free, 'total': external.total,
                                  'same_device_as_internal': ROOT.stat().st_dev == internal_path.stat().st_dev},
              'issues': issues, 'unavailable_probes': unknown, 'evidence': evidence,
              'status': 'ATTENTION' if issues else ('PARTIAL' if unknown else 'OK'), 'services': services()}
    result['workflow_health'] = mac_workflows.project(ROOT)
    result['cache_maintenance'] = mac_workflows.read(STATE / 'auto-cleanup-latest.json')
    from . import mac_auto_cleanup
    result['cache_maintenance_diagnosis'] = mac_auto_cleanup.diagnosis(STATE, mac_workflows.read, now)
    boot = evidence['boot']
    result['boot_id'] = boot['output'].strip() if boot['code'] == 0 and boot['output'].strip() else None
    result['disk_policy'] = mac_disk_policy.assess(disk.free, disk_identity, now,
        previous if result['boot_id'] else [], boot_id=result['boot_id'])
    result['memory_policy'] = mac_disk_policy.memory(evidence, result['boot_id'], now, previous)
    if source == 'scheduled':
        result['codex_growth'] = mac_codex_growth.current(STATE, mac_workflows.read)
    save(STATE / f'sample-{source}-{time.time_ns()}.json', result)
    save(STATE / f'latest-{source}.json', result)
    if source == 'scheduled':
        save(STATE / 'latest.json', result)  # Compatibility projection owned by scheduled ticks only.
        if not unknown:
            save(STATE / 'last-complete-scheduled.json', result)
        write_summary(STATE / 'summary.txt', result)
    else:
        write_summary(STATE / 'summary-manual.txt', result)
    result['last_complete_scheduled'] = complete_reference(now)
    return result


def complete_reference(now=None):
    last = load(STATE / 'last-complete-scheduled.json')
    return {'time': last['time'], 'age_seconds': (now or time.time()) - last['time'],
            'path': str(STATE / 'last-complete-scheduled.json'), 'historical_not_current': True} if last else None


def write_summary(path, result):
    disk, external = result['disk_free'], result['repository_disk']['free']
    text = (f"Mac ({result['source']}): {result['status']}. Internal disk free: {disk / 1024**3:.1f} / "
            f"{result['disk_total'] / 1024**3:.1f} GiB. Repository volume free: {external / 1024**3:.1f} GiB. "
            f"Load: {result['load'][0]:.2f}.\n" + '\n'.join(result['issues']) +
            f"\nUnavailable probes: {', '.join(result['unavailable_probes']) or 'none'}.\n")
    last = complete_reference()
    if result['unavailable_probes'] and last:
        text += f"Last complete scheduled evidence: {last['age_seconds']:.0f}s old (historical).\n"
    text += '\n'.join(f"{k}: {v['status']}" for k, v in result['workflow_health'].items()) + '\n'
    recovery = result.get('services', {}).get('network_recovery')
    if recovery:
        text += f"Hotel reconnect: {recovery['service_status']}; current internet {recovery['current_internet']}.\n"
        bounded = recovery.get('bounded_recovery', {})
        text += f"Bounded recovery: {bounded.get('status', 'UNKNOWN')}; reason: {bounded.get('last_reason') or 'none'}.\n"
        last = recovery.get('last_connectivity_event')
        if last:
            text += f"Last logged connectivity event (historical, local time): {last['local_timestamp']} {last['event']}.\n"
    path.write_text(text)


def cleanup():
    return mac_storage.preview()


def health(now=None):
    """Inspect retained evidence without running probes or changing projections."""
    now = time.time() if now is None else now
    sample = load(STATE / 'latest-scheduled.json') or {}
    stamp = sample.get('time')
    age = now - stamp if isinstance(stamp, (int, float)) else None
    freshness = ('UNKNOWN' if age is None or age < 0 else
                 'FRESH' if age <= 900 else 'STALE')
    tick = load(STATE / 'tick-scheduled.json') or {}
    problems = []
    if freshness != 'FRESH':
        problems.append('No valid scheduled sample within 15 minutes; sleep, unmounted volume or launch failure require inspection.')
    if tick.get('status') in ('FAILED', 'TIME_LIMIT') or (tick.get('status') == 'RUNNING' and
                                        now - tick.get('started_at', now) > 300):
        problems.append('Last tick is failed or unfinished; inspect its phase and launchctl exit status before any retry.')
    from . import mac_auto_cleanup
    cleanup_diagnosis = mac_auto_cleanup.diagnosis(STATE, mac_workflows.read, now)
    if cleanup_diagnosis['status'] in ('INTERRUPTED_REQUIRES_INSPECTION', 'FAILED_REQUIRES_INSPECTION', 'TIME_LIMIT_REQUIRES_INSPECTION'):
        problems.append('Cache cleanup is unfinished; inspect preserved receipt and lock. Automatic retry remains blocked.')
    return {'schema_version': 'v1', 'status': 'ATTENTION' if problems else 'OK',
            'sample_freshness': freshness, 'sample_age_seconds': age,
            'host_status': sample.get('status', 'UNKNOWN'), 'last_tick': tick,
            'issues': problems, 'automatic_repair': False,
            'cache_maintenance': {'diagnosis': cleanup_diagnosis, 'policy':load(STATE / 'auto-cleanup-policy.json'),
                                  'latest':load(STATE / 'auto-cleanup-latest.json')},
            'codex_storage': {
                'signals': mac_codex_growth.current(STATE, load, now),
                'daily_claim': load(STATE / 'codex-growth-daily-claim.json'),
                'weekly_claim': load(STATE / 'codex-retention-weekly-claim.json')},
            'note': 'Freshness is evidence only; stale data does not prove a crash. No independent watchdog is installed.'}


@budget.bounded(130)
def tick(source):
    """Checkpoint phases so a subsequent inspection can locate interrupted work."""
    path = STATE / f'tick-{source}.json'
    receipt = {'schema_version': 'v1', 'source': source, 'pid': os.getpid(),
               'started_at': time.time(), 'status': 'RUNNING', 'phase': 'diagnose'}
    receipt['budget_seconds'] = 130
    def phase(name):
        receipt.update(phase=name, phase_started_at=time.time(),
                       budget_remaining_seconds=budget.remaining())
        save(path, receipt)
        budget.check()
    try:
        phase('diagnose')
        snapshot = diagnose(source)
        if source == 'scheduled':
            phase('incidents')
            mac_alerts.reconcile(STATE, snapshot, load, save)
            phase('notifications')
            mac_alerts.deliver(STATE, load, save, local_notify, notify_remote)
        phase('transport')
        save(STATE / 'transport-status.json', poll_telegram())
        if source == 'scheduled':
            phase('authorized-cache-cleanup')
            receipt['cache_cleanup'] = {'status': 'SUSPENDED_OWNER_INSTRUCTION'}
            save(path, receipt)
            phase('storage-category-observation')
            receipt['storage_category'] = mac_disk_policy.observe_storage(STATE, snapshot, load, save)
            save(path, receipt)
            phase('codex-retention-cycle')
            try:
                receipt['codex_retention'] = mac_codex_growth.run_due(STATE, snapshot, load, save)
            except budget.Expired:
                raise
            except Exception as retention_exc:
                # Maintenance must not interrupt the existing five-minute monitor.
                receipt['codex_retention'] = {'status': 'FAILED', 'error_type': type(retention_exc).__name__}
            save(path, receipt)
        budget.check()
    except budget.Expired:
        receipt.update(status='TIME_LIMIT', finished_at=time.time(), budget_remaining_seconds=budget.remaining())
        save(path, receipt)
        return receipt
    except Exception as exc:
        # Exception text can contain credentials or private paths.
        receipt.update(status='FAILED', finished_at=time.time(), error_type=type(exc).__name__)
        save(path, receipt)
        raise
    receipt.update(status='COMPLETE', phase='done', finished_at=time.time())
    save(path, receipt)
    return receipt


def handoffs():
    return [load(p) for p in sorted((STATE / 'handoffs').glob('*.json'))]


def execute(action, request_id):
    if action not in {'status', 'slow', 'services', 'cleanup', 'weekly', 'restart-monitor', 'validate', 'handoffs', 'youtube', 'health', 'disk-overview', 'codex-retention', 'maintenance-plan', 'docker-storage'}:
        return {'status': 'CLARIFY', 'message': 'Choose an explicitly supported scenario; arbitrary commands are forbidden.'}
    db = sqlite3.connect(STATE / 'requests.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, action TEXT, result TEXT, created REAL)')
    db.execute("UPDATE requests SET result='REDACTED_AFTER_7_DAYS' WHERE created < ?", (time.time() - 7 * 86400,))
    try:
        db.execute('INSERT INTO requests VALUES (?, ?, ?, ?)', (request_id, action, 'IN_PROGRESS', time.time()))
        db.commit()  # Claim before effects. Crash leaves UNKNOWN, never automatic replay.
    except sqlite3.IntegrityError:
        db.close()
        return {'status': 'DUPLICATE', 'message': 'Not executed again; inspect original receipt.'}
    try:
        if action in ('status', 'slow'):
            result = diagnose()
        elif action == 'health':
            result = health()
        elif action == 'services':
            result = {**services(), 'workflow_health': mac_workflows.project(ROOT)}
        elif action == 'cleanup':
            result = cleanup()
        elif action == 'maintenance-plan':
            from .mac_cache_maintenance import plan
            result = plan()
        elif action == 'docker-storage':
            from .mac_docker_report import collect
            result = collect()
        elif action == 'disk-overview':
            result = mac_storage.disk_overview()
            save(STATE / 'disk-overview.json', result)
        elif action == 'codex-retention':
            result = mac_codex_retention.preview()
            save(STATE / 'codex-retention-preview.json', result)
        elif action in ('weekly', 'youtube'):
            result = mac_workflows.enqueue(ROOT, STATE, 'radar' if action == 'weekly' else 'youtube', request_id, save)
        elif action == 'handoffs':
            result = handoffs()
        elif action == 'restart-monitor':
            result = command(['/bin/launchctl', 'kickstart', '-k', f'gui/{os.getuid()}/{LABEL}'])
            result['verification'] = command(['/bin/launchctl', 'print', f'gui/{os.getuid()}/{LABEL}'])
        else:
            result = command([str(ROOT / 'bin/abvx'), 'validate'], timeout=120)
        db.execute('UPDATE requests SET result=? WHERE id=?', (json.dumps(result), request_id))
        db.commit()
        return result
    finally:
        db.close()


def local_notify(message):
    script = 'on run argv\n display notification (item 1 of argv) with title "ABVX OS"\nend run'
    result = command(['/usr/bin/osascript', '-e', script, message], timeout=8)
    return {'status': 'SUBMITTED_NOT_VISUALLY_VERIFIED' if result['code'] == 0 else 'UNAVAILABLE'}


def telegram_config():
    config = STATE / 'telegram.json'
    if not config.exists():
        return None
    if config.is_symlink() or config.stat().st_mode & 0o077 or config.stat().st_uid != os.getuid():
        raise ValueError('config permissions')
    d = json.loads(config.read_text())
    if set(d) != {'token', 'user_id', 'chat_id'} or type(d['user_id']) is not int or type(d['chat_id']) is not int:
        raise ValueError('config schema')
    if not isinstance(d['token'], str) or not d['token'] or not all(c.isalnum() or c in ':_-' for c in d['token']):
        raise ValueError('token format')
    return d


def telegram_api(d, method, payload):
    req = urllib.request.Request('https://api.telegram.org/bot' + d['token'] + '/' + method,
                                 data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=budget.timeout(15)) as response:
        value = json.load(response)
    if not value.get('ok'):
        raise ValueError('Telegram rejected request')
    return value['result']


def notify_remote(message):
    try:
        d = telegram_config()
        if d is None:
            return {'status': 'NOT_CONNECTED'}
        if message is None:
            return {'status': 'READY'}
        telegram_api(d, 'sendMessage', {'chat_id': d['chat_id'], 'text': message[:3500]})
        return {'status': 'SENT'}
    except Exception as exc:
        return {'status': 'UNAVAILABLE', 'error_type': type(exc).__name__}


def poll_telegram():
    """Optional outbound-only transport. Config is provisioned by owner, never Git."""
    try:
        d = telegram_config()
        if d is None:
            return {'status': 'NOT_CONNECTED'}
    except Exception:
        return {'status': 'BLOCKED_CONFIG_PERMISSIONS_OR_SCHEMA'}
    def api(method, payload):
        return telegram_api(d, method, payload)
    offset_path = STATE / 'telegram-offset.json'
    offset = json.loads(offset_path.read_text())['offset'] if offset_path.exists() else 0
    try:
        updates = api('getUpdates', {'offset': offset, 'timeout': 0, 'limit': 20, 'allowed_updates': ['message']})
        for update in updates:
            if update['update_id'] < offset:
                continue
            m = update.get('message', {})
            authorized = (m.get('from', {}).get('id') == d['user_id'] and
                          m.get('chat', {}).get('id') == d['chat_id'] and
                          m.get('chat', {}).get('type') == 'private' and
                          0 <= time.time() - m.get('date', 0) <= 600)
            # Claim delivery before effects. Interrupted delivery is never replayed.
            save(offset_path, {'offset': update['update_id'] + 1})
            if not authorized:
                continue
            action = ALIASES.get(m.get('text', '').strip().lower(), 'unknown')
            result = execute(action, 'telegram-' + str(update['update_id']))
            if action in ('status', 'slow') and result.get('status') != 'DUPLICATE':
                reply = (STATE / 'summary-manual.txt').read_text()
            elif action == 'services':
                reply = json.dumps(result.get('workflow_health', result), ensure_ascii=False)[:3500]
            else:
                reply = json.dumps(result, ensure_ascii=False)[:3500]
            api('sendMessage', {'chat_id': d['chat_id'], 'text': reply})
        return {'status': 'POLLED'}
    except Exception as exc:
        # URLs contain credentials. Never record exception text or traceback.
        return {'status': 'UNAVAILABLE', 'error_type': type(exc).__name__}


def plist():
    bootstrap = Path.home() / 'Library/Application Support/ABVX/mac-operator/abvx_schedule_recovery.py'
    if bootstrap.is_file():
        return {'Label': LABEL, 'ProgramArguments': [sys.executable, str(bootstrap)],
                'WorkingDirectory': str(bootstrap.parent),
                'RunAtLoad': True, 'KeepAlive': {'SuccessfulExit': False}, 'ThrottleInterval': 60,
                'StartInterval': 300, 'ProcessType': 'Background', 'Umask': 63,
                'StandardOutPath': '/dev/null', 'StandardErrorPath': '/dev/null'}
    return {'Label': LABEL, 'ProgramArguments': [sys.executable, '-m', 'abvx_harness.mac_operator', 'daemon'],
            'WorkingDirectory': str(ROOT), 'EnvironmentVariables': {'PYTHONPATH': str(ROOT / 'src')},
            'RunAtLoad': True, 'KeepAlive': {'SuccessfulExit': False}, 'ThrottleInterval': 60,
            'StartInterval': 300, 'ProcessType': 'Background', 'Umask': 63,
            'StandardOutPath': '/dev/null', 'StandardErrorPath': '/dev/null'}


def main():
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'slow', 'services', 'cleanup', 'weekly', 'restart-monitor', 'validate', 'daemon', 'prepare-launchd', 'ask', 'handoffs', 'youtube', 'claim-handoff', 'complete-handoff', 'cancel-handoff', 'health', 'disk-overview', 'codex-retention', 'maintenance-plan', 'docker-storage'])
    parser.add_argument('--text', default='')
    parser.add_argument('--request-id', default=None)
    parser.add_argument('--handoff-id')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    if args.action in ('claim-handoff', 'complete-handoff', 'cancel-handoff'):
        print(json.dumps(mac_workflows.transition(ROOT, STATE, args.handoff_id or '',
                         {'claim-handoff': 'claim', 'complete-handoff': 'complete', 'cancel-handoff': 'cancel'}[args.action], save, args.run_id), ensure_ascii=False, indent=2))
        return
    if args.action == 'prepare-launchd':
        p = STATE / f'{LABEL}.plist'
        p.write_bytes(plistlib.dumps(plist()))
        print(p)
        return
    if args.action == 'daemon':
        with (STATE / 'monitor.lock').open('w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return
            # launchd supplies interval scheduling; a crash is retried no faster than 60s.
            source = 'scheduled' if os.environ.get('XPC_SERVICE_NAME') == LABEL else 'manual'
            tick(source)
        return
    action = ALIASES.get(args.text.strip().lower(), 'unknown') if args.action == 'ask' else args.action
    print(json.dumps(execute(action, args.request_id or f'local-{time.time_ns()}'), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
