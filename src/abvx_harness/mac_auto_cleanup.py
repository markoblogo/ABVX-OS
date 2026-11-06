"""Owner-enabled, bounded download-cache maintenance in the existing monitor.

No arbitrary paths, user data, project dependencies, Docker or browser stores.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import time
from . import mac_cache_maintenance as cache
from . import mac_budget as budget
from .mac_operator import STATE, save, load

class CheckpointError(RuntimeError):
    """The pre-effect journal could not be persisted."""


GIB = 1024**3
DAILY_LIMIT = 2*GIB
INTERVAL = 6*3600
TARGET_FREE = 15*GIB
# Only downloads that can be regenerated; updater copy is a cache, not installed VSCode.
TARGETS = {
    'npm-downloads': '.npm/_cacache',
    'homebrew-downloads': 'Library/Caches/Homebrew/downloads',
    'node-headers': 'Library/Caches/node-gyp',
    'pip-downloads': 'Library/Caches/pip',
    'vscode-update-cache': 'Library/Caches/com.microsoft.VSCode.ShipIt',
    'apple-help-cache': 'Library/Caches/com.apple.helpd',
    'codex-update-cache': 'Library/Caches/com.openai.codex/org.sparkle-project.Sparkle/Installation',
}


def enable(now=None):
    now = time.time() if now is None else now
    value = {'schema_version': 'v1', 'enabled': True, 'approved_at': now,
             'expires_at': now+30*86400, 'actor': 'OWNER_URGENT_AND_RECURRING_CLEANUP_REQUEST_2026_10_27',
             'scope': 'fixed-regenerable-download-caches-v1', 'emergency_pending': True,
             'consequence': 'Cached downloads and pending VSCode update copy may need downloading again. No local undo.'}
    save(STATE/'auto-cleanup-policy.json', value)
    return value


def diagnosis(state, read=load, now=None):
    """Read-only projection. A receipt is evidence, never permission to retry."""
    now = time.time() if now is None else now
    previous = read(state/'auto-cleanup-latest.json') or {}
    status = previous.get('status', 'UNKNOWN')
    started = previous.get('started_at')
    age = now-started if isinstance(started, (int, float)) else None
    if status == 'RUNNING':
        status = ('RUNNING_UNCONFIRMED' if age is not None and 0 <= age <= 120
                  else 'INTERRUPTED_REQUIRES_INSPECTION')
    return {'status': status, 'receipt_status': previous.get('status', 'UNKNOWN'),
            'age_seconds': age, 'automatic_retry': False,
            'note': 'Age does not prove process liveness. Retain receipt and inspect operation lock; never reset an unfinished pass automatically.'}


def run_due(state, snapshot, read=load, write=save, now=None):
    with (state/'auto-cleanup.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status':'BUSY'}
        with budget.limit(80):
            return _run_locked(state, snapshot, read, write, now)


def _run_locked(state, snapshot, read=load, write=save, now=None):
    now = time.time() if now is None else now
    previous = read(state/'auto-cleanup-latest.json') or {}
    if previous.get('status') in ('RUNNING', 'FAILED_REQUIRES_INSPECTION', 'TIME_LIMIT_REQUIRES_INSPECTION'):
        return {'status':'INTERRUPTED_REQUIRES_INSPECTION'}
    policy = read(state/'auto-cleanup-policy.json')
    if (not isinstance(policy, dict) or policy.get('schema_version') != 'v1' or
            policy.get('enabled') is not True or policy.get('scope') != 'fixed-regenerable-download-caches-v1' or
            policy.get('actor') != 'OWNER_URGENT_AND_RECURRING_CLEANUP_REQUEST_2026_10_27' or
            not isinstance(policy.get('approved_at'), (int,float)) or
            not isinstance(policy.get('expires_at'), (int,float)) or
            not 0 <= now-policy['approved_at'] <= 30*86400 or
            not now < policy['expires_at'] <= policy['approved_at']+30*86400):
        return {'status': 'DISABLED_OR_EXPIRED'}
    previous = read(state/'auto-cleanup-latest.json') or {}
    if previous.get('started_at', 0) > now or (now-previous.get('started_at',0) < INTERVAL and policy.get('emergency_pending') is not True):
        return {'status': 'NOT_DUE'}
    if budget.remaining() is not None and budget.remaining() <= 5:
        return {'status': 'DEFERRED_TIME_BUDGET'}
    # Always use fresh disk evidence, not an old host snapshot.
    before = shutil.disk_usage(cache.INTERNAL).free
    if before >= TARGET_FREE:
        return {'status': 'ENOUGH_FREE_SPACE'}
    day = int(now//86400)
    quota_path = state/'auto-cleanup-quota.json'
    quota = read(quota_path) or {'day':day, 'charged_bytes':0}
    if quota.get('day') != day:
        quota = {'day':day, 'charged_bytes':0}
    if type(quota.get('charged_bytes')) is not int or quota['charged_bytes'] < 0:
        return {'status':'BLOCKED_INVALID_QUOTA'}
    if quota['charged_bytes'] >= DAILY_LIMIT:
        return {'status':'DAILY_LIMIT'}
    folder = state/'auto-cleanup-results'
    folder.mkdir(exist_ok=True, mode=0o700)
    emergency = policy.get('emergency_pending') is True
    result = {'schema_version':'v1', 'started_at':now, 'status':'RUNNING',
              'pid': os.getpid(), 'run_id': f'{time.time_ns()}-{os.getpid()}',
              'checkpoints': [], 'phase': 'claimed',
              'mode':'INITIAL_OWNER_EMERGENCY' if emergency else 'SCHEDULED',
              'disk_free_before':before, 'items':[], 'verified_removed_allocated_bytes':0,
              'failed_targets':previous.get('failed_targets',[])}
    history = state/'auto-cleanup-runs'
    history.mkdir(exist_ok=True, mode=0o700)
    history_path = history/(result['run_id']+'.json')
    def checkpoint(phase, target=None):
        result.update(phase=phase, target=target, updated_at=time.time(),
                      budget_remaining_seconds=budget.remaining())
        result['checkpoints'].append({'phase': phase, 'target': target,
                                      'time': result['updated_at'],
                                      'budget_remaining_seconds': result['budget_remaining_seconds']})
        try:
            write(history_path, result)
            write(state/'auto-cleanup-latest.json', result)
        except OSError:
            raise CheckpointError() from None
        budget.check()
    try:
        checkpoint('claimed')
        with (state/'maintenance.lock').open('w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                result.update(status='BUSY', finished_at=time.time())
                checkpoint('busy')
                return result
            for name, relative in TARGETS.items():
                budget.check()
                checkpoint('target-before', name)
                if shutil.disk_usage(cache.INTERNAL).free >= TARGET_FREE:
                    break
                if name in result['failed_targets']:
                    result['items'].append({'name':name,'status':'PREVIOUS_FAILURE_REQUIRES_INSPECTION'})
                    continue
                path = Path.home()/relative
                item = {'name':name,'path':str(path)}
                try:
                    checkpoint('fingerprint-before', name)
                    evidence = cache.fingerprint(path, allow_nested_symlinks=True)
                    checkpoint('fingerprint-after', name)
                    checkpoint('activity-before', name)
                    item['activity'] = cache.activity(path)
                    checkpoint('activity-after', name)
                    if not item['activity']['idle']:
                        item.update(status='BLOCKED', reason=item['activity']['reason'])
                        result['items'].append(item)
                        checkpoint('target-after', name)
                        continue
                    size = evidence['allocated_bytes']
                    item['allocated_bytes'] = size
                    if size < (1024**2 if emergency else 64*1024**2):
                        item['status'] = 'BELOW_THRESHOLD'
                    elif size > DAILY_LIMIT-quota['charged_bytes']:
                        item['status'] = 'QUOTA_LIMIT'
                    else:
                        # Charge before effects. A crash cannot replenish the budget.
                        budget.check(15)
                        checkpoint('quota-before', name)
                        quota['charged_bytes'] += size
                        write(quota_path, quota)
                        key = f'{int(now)}-{name}'
                        checkpoint('execute-before', name)
                        outcome = cache.remove_snapshot(path, evidence, folder/(key+'.json'),
                                                        policy['actor'], key, checkpoint=lambda phase: checkpoint(phase, name))
                        checkpoint('execute-after', name)
                        item['result'] = outcome
                        item['status'] = outcome['status']
                        if outcome['status'] == 'VERIFIED_REMOVED':
                            result['verified_removed_allocated_bytes'] += size
                        elif outcome['status'] in ('FAILED_OR_PARTIAL_NO_AUTORETRY', 'TARGET_RECREATED_OR_REMAINS'):
                            result['failed_targets'].append(name)
                        elif outcome['status'] == 'BLOCKED':
                            # No deletion effect started; release unused reservation.
                            quota['charged_bytes'] -= size
                            write(quota_path, quota)
                except budget.Expired:
                    raise
                except FileNotFoundError:
                    item['status'] = 'ABSENT'
                except (OSError, ValueError) as exc:
                    item.update(status='BLOCKED', error_type=type(exc).__name__,
                                reason=str(exc) if type(exc) is ValueError else type(exc).__name__)
                result['items'].append(item)
                checkpoint('target-after', name)
        policy['emergency_pending'] = False
        checkpoint('finalize-before')
        write(state/'auto-cleanup-policy.json',policy)
        blocked = any(i.get('status') in ('BLOCKED','PREVIOUS_FAILURE_REQUIRES_INSPECTION','PASS_TIME_LIMIT') for i in result['items'])
        status = 'PARTIAL' if blocked else 'COMPLETE'
        result.update(status=status,finished_at=time.time(),
                      disk_free_after=shutil.disk_usage(cache.INTERNAL).free)
        result['observed_disk_free_delta_bytes'] = result['disk_free_after']-before
        result['note'] = 'Verified removal estimates are allocated blocks, not guaranteed free-space gain. Host delta includes concurrent activity. Blocked/absent items are not success.'
        checkpoint('done')
        return result
    except Exception as exc:
        result.update(status='TIME_LIMIT_REQUIRES_INSPECTION' if isinstance(exc, budget.Expired) else 'FAILED_REQUIRES_INSPECTION',
                      error_type=type(exc).__name__, finished_at=time.time())
        write(history_path, result)
        write(state/'auto-cleanup-latest.json', result)
        return result


def main():
    import os
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['enable','run','status','disable'])
    args = parser.parse_args()
    if args.action == 'enable':
        result = enable()
    elif args.action == 'disable':
        policy = load(STATE/'auto-cleanup-policy.json') or {}
        policy['enabled'] = False
        save(STATE/'auto-cleanup-policy.json',policy)
        result = {'status':'DISABLED'}
    elif args.action == 'run':
        result = run_due(STATE,{})
    else:
        result = {'policy':load(STATE/'auto-cleanup-policy.json'), 'latest':load(STATE/'auto-cleanup-latest.json')}
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
