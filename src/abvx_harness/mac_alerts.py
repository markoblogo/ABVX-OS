"""State-transition incidents; no unchanged reminders, bounded channel attempts."""
from . import mac_budget as budget
import fcntl
import hashlib
import time


def reconcile(state, snapshot, load, save):
    path = state / 'incidents.json'
    previous = load(path) or {'schema_version': 'v1', 'incidents': {}}
    incidents = previous['incidents']
    active = {message: message for message in snapshot['issues']}
    memory_policy = snapshot.get('memory_policy') or {}
    if memory_policy.get('status') == 'REVIEW':
        active['memory:swap-growth'] = ('Подкачка растёт, достигла 4 ГиБ или повышено давление RAM. '
            'Сохраните работу, закройте неиспользуемые тяжёлые приложения и проверьте Память в Мониторинге системы. '
            'Системные swap-файлы удалять нельзя.')
    disk_policy = snapshot.get('disk_policy') or {}
    mode = disk_policy.get('mode')
    if mode in ('WATCH', 'WARNING', 'CRITICAL', 'EMERGENCY'):
        active['disk:level:' + mode] = 'Internal disk mode ' + mode + '; inspect disk policy and storage candidates.'
    if (disk_policy.get('hours_to_8_gib') is not None and
            disk_policy['hours_to_8_gib'] <= 24):
        active['disk:rapid-decline'] = 'Recent disk trend projects less than 24 hours to 8 GiB; estimate may change.'
    maintenance = snapshot.get('cache_maintenance') or {}
    if maintenance.get('status') in ('PARTIAL','RUNNING','FAILED_REQUIRES_INSPECTION','TIME_LIMIT_REQUIRES_INSPECTION') and snapshot.get('disk_free', 0) < 10*1024**3:
        active['cleanup:blocked'] = 'Internal disk is low and cache cleanup is blocked or unfinished; inspect auto-cleanup status. No unsafe fallback deletion is allowed.'
    recovery = snapshot.get('services', {}).get('network_recovery', {}).get('bounded_recovery', {})
    if recovery.get('status') == 'PAUSED':
        active['network:recovery'] = 'Hotel internet recovery paused after three failed attempts. Inspect services for the redacted failure reason; no further logins until connectivity returns.'
    network = snapshot.get('services', {}).get('network_recovery', {})
    if recovery.get('status') == 'STALE' or (network.get('service_status') == 'UNKNOWN_OR_STOPPED' and recovery.get('status') != 'NOT_ACTIVATED'):
        active['network:service'] = 'Hotel reconnect service evidence is stale or unavailable; inspect launchctl and recovery state.'
    if recovery.get('current_internet') == 'UNAVAILABLE' and (recovery.get('offline_seconds') or 0) >= 180:
        active['network:outage'] = 'Internet unavailable for at least three minutes; bounded recovery is active or paused. Inspect services for details.'
    if recovery.get('status') == 'PROBE_ERROR':
        active['network:probe'] = 'Hotel connectivity probe failed to execute; internet state is unknown. Inspect services for the redacted reason.'
    growth = snapshot.get('codex_growth') or {}
    if growth.get('signal') == 'HIGH_GROWTH':
        rate = growth.get('gib_per_day')
        if isinstance(rate, (int, float)):
            active['codex:workspace-growth'] = (f'Measured Codex workspace scope grew by {rate:.1f} GiB/day; '
                'review the Codex growth report. No files were changed.')
    if growth.get('weekly_signal') == 'REVIEW':
        active['codex:retention-review'] = ('Old Codex workspace dependencies may be ready for review. '
            'Inspect the weekly report; removal requires explicit approval.')
    for key, value in snapshot.get('workflow_health', {}).items():
        if value['status'] == 'OVERDUE_EVIDENCE':
            active['workflow:' + key] = key + ': expected research evidence is overdue; ' + str(value.get('cause') or 'cause UNKNOWN')
    failed = bool(snapshot['unavailable_probes'])
    failures = previous.get('consecutive_probe_failures', 0) + 1 if failed else 0
    if failures >= 3:
        active['probe-failures'] = 'Three consecutive scheduled samples have unavailable probes; inspect permissions and native command results.'
    events = []
    for key, message in active.items():
        if not incidents.get(key, {}).get('active'):
            events.append(('OPEN', key, message))
        else:
            incidents[key]['message'] = message
    for key, item in list(incidents.items()):
        if item.get('active') and key not in active:
            if key == 'memory:swap-growth' and memory_policy.get('status') != 'NORMAL':
                continue
            if key == 'disk:rapid-decline' and disk_policy.get('trend') == 'UNKNOWN':
                continue
            if key == 'cleanup:blocked' and (maintenance.get('status') != 'COMPLETE' or
                                           snapshot.get('disk_free',0) < 10*1024**3):
                continue
            if key.startswith('network:') and recovery.get('status') != 'ONLINE':
                continue  # Missing/stale evidence cannot claim network recovery.
            if key == 'codex:workspace-growth' and growth.get('signal') != 'NORMAL':
                continue  # Missing/incomplete readings cannot prove recovery.
            if key == 'codex:retention-review' and growth.get('weekly_signal') != 'NORMAL':
                continue  # Partial or stale previews cannot prove recovery.
            if key.startswith('disk:') and not mode:
                continue
            # A denied probe is not evidence that memory/load recovered.
            if snapshot['unavailable_probes'] and key not in ('probe-failures',) and not key.startswith('workflow:'):
                continue
            if key.startswith('workflow:') and snapshot.get('workflow_health', {}).get(key.split(':')[1], {}).get('status') != 'CURRENT_EVIDENCE':
                continue
            events.append(('RECOVERED', key, item['message']))
    for event, key, message in events:
        stamp = f"{snapshot['time']}:{previous.get('transition_sequence', 0)}"
        event_id = hashlib.sha256(f'{key}:{event}:{stamp}'.encode()).hexdigest()
        incident = {'active': event == 'OPEN', 'message': message, 'changed_at': snapshot['time']}
        incidents[key] = incident
        folder = state / 'notifications'
        folder.mkdir(exist_ok=True, mode=0o700)
        event_path = folder / (event_id + '.json')
        if load(event_path):
            continue  # Replay after event persistence but before incident checkpoint.
        save(event_path, {'schema_version': 'v1', 'id': event_id,
              'incident_key': key, 'event': event, 'message': message, 'created_at': snapshot['time'], 'attempts': 0,
              'status': 'PENDING', 'next_attempt': 0})
    previous['transition_sequence'] = previous.get('transition_sequence', 0) + len(events)
    previous.update({'incidents': incidents, 'consecutive_probe_failures': failures})
    save(path, previous)
    return len(events)


def deliver(state, load, save, local_notify, remote_notify, now=None):
    """Serialize consumers; select eligible events chronologically before limiting."""
    now = time.time() if now is None else now
    with (state / 'notification-delivery.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'BUSY'}
        return _deliver(state, load, save, local_notify, remote_notify, now)


def _deliver(state, load, save, local_notify, remote_notify, now):
    pending = []
    for p in (state / 'notifications').glob('*.json'):
        budget.check()
        if p.is_symlink():
            continue
        item = load(p)
        if not isinstance(item, dict) or item.get('status') != 'PENDING':
            continue
        if not all(isinstance(item.get(k), (int, float)) for k in ('created_at', 'next_attempt', 'attempts')):
            item['status'] = 'INVALID'
            save(p, item)
            continue
        if item['created_at'] > now:
            continue  # Future evidence is not deliverable.
        if item['created_at'] < now - 86400:
            item['status'] = 'EXPIRED'
            save(p, item)
            continue
        pending.append((p, item))
    # Suppress obsolete transitions for a known incident, preserving receipts.
    newest = {}
    for p, item in pending:
        key = item.get('incident_key') or hashlib.sha256(item.get('message', '').encode()).hexdigest()
        if key and (key not in newest or item['created_at'] > newest[key]):
            newest[key] = item['created_at']
    eligible = []
    for p, item in pending:
        key = item.get('incident_key') or hashlib.sha256(item.get('message', '').encode()).hexdigest()
        if key and item['created_at'] < newest[key]:
            item['status'] = 'SUPERSEDED'
            save(p, item)
        elif item['next_attempt'] <= now:
            eligible.append((p, item))
    ledger_path = state / 'notification-cooldowns.json'
    ledger = load(ledger_path) or {}
    ledger = {k: v for k, v in ledger.items() if isinstance(v, (int, float)) and now-v < 86400}
    deadline = time.monotonic() + 25
    processed = 0
    for p, item in sorted(eligible, key=lambda pair: (pair[1]['created_at'], pair[0].name))[:100]:
        budget.check()
        if time.monotonic() >= deadline:
            break
        key = item.get('incident_key') or hashlib.sha256(item.get('message', '').encode()).hexdigest()
        last = ledger.get(key)
        if last is not None and now-last < 3600:
            item['next_attempt'] = last + 3600
            save(p, item)
            continue
        ledger[key] = now
        save(ledger_path, ledger)
        if not item.get('local_attempted'):
            item['local_attempted'] = True
            item['local_result'] = {'status': 'ATTEMPTED_DELIVERY_UNKNOWN'}
            save(p, item)  # At most one local effect, even after interruption.
            item['local_result'] = local_notify(item['event'] + ': ' + item['message'])
            save(p, item)
        if item['attempts'] >= 3:
            item['status'] = 'DELIVERY_FAILED'
            save(p, item)
            continue
        # Disconnection must not monopolize each batch, nor consume send quota.
        item['next_attempt'] = now + 3600
        save(p, item)
        result = remote_notify(None)
        if result.get('status') == 'NOT_CONNECTED':
            item['remote_status'] = 'NOT_CONNECTED'
            save(p, item)
            processed += 1
            continue
        item['attempts'] += 1
        item['remote_status'] = 'ATTEMPTED_DELIVERY_UNKNOWN'
        save(p, item)  # Reserve retry before any network effect.
        result = remote_notify(item['event'] + ': ' + item['message'])
        item['remote_status'] = result['status']
        if result['status'] == 'SENT':
            item['status'] = 'DELIVERED'
        elif item['attempts'] >= 3:
            item['status'] = 'DELIVERY_FAILED'
        save(p, item)
        processed += 1
    return {'status': 'COMPLETE', 'processed': processed, 'eligible': len(eligible)}
