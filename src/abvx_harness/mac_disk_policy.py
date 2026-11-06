"""Bounded advisory disk policy. No filesystem mutation or deletion."""
GIB = 1024 ** 3
import re


def observe_storage(state, snapshot, load, save):
    """One fixed category per half-hour, at most three seconds of directory IO."""
    from pathlib import Path
    from .mac_codex_growth import _measure
    now = snapshot.get('time')
    if not isinstance(now, (int, float)):
        return {'status': 'UNAVAILABLE_TIME'}
    pressure = snapshot.get('evidence', {}).get('pressure', {})
    if pressure.get('code') != 0 or pressure.get('output', '').strip() != '1':
        return {'status': 'DEFERRED_PRESSURE'}
    path = state / 'storage-category-progress.json'
    progress = load(path) or {'schema_version': 'v1', 'categories': {}}
    last = progress.get('attempted_at', 0)
    if now < last or now-last < 1800:
        return {'status': 'NOT_DUE'}
    roots = ['Documents/Codex', '.cache/codex-runtimes', '.npm',
             'Library/Caches/com.openai.codex', 'Library/Caches/Codex',
             'Library/Containers/com.docker.docker', '.cache/huggingface',
             '.ollama/models', 'Library/Caches/Google', 'Library/Caches/Comet']
    categories = progress['categories']
    selected = min(roots, key=lambda k: categories.get(k, {}).get('time', 0))
    progress.update(attempted_at=now, active_category=selected)
    save(path, progress)  # Claim before IO; interrupted attempts do not loop.
    old = categories.get(selected, {})
    measured = _measure(Path.home()/selected, now=now, timeout=3)
    measured['growth_bytes_per_day'] = None
    if (measured['status'] == 'COMPLETE' and old.get('status') == 'COMPLETE'
            and measured.get('device') == old.get('device') and 1800 <= now-old['time'] <= 86400):
        measured['growth_bytes_per_day'] = (measured['allocated_bytes']-old['allocated_bytes'])*86400/(now-old['time'])
    categories[selected] = measured
    progress['active_category'] = None
    save(path, progress)
    save(state / ('storage-category-' + str(int(now)) + '.json'), measured)
    return {'status': measured['status'], 'category': selected}


def memory(evidence, boot_id, now, samples):
    """Swap is disk-backed memory, RSS is only a partial resident-memory metric."""
    probe = evidence.get('swap', {})
    match = re.search(r'total = ([\d.]+)M\s+used = ([\d.]+)M', probe.get('output', ''))
    result = dict(schema_version='v1', status='UNKNOWN', total_bytes=None,
                  used_bytes=None, growth_gib_per_hour=None, action='INSPECT_NATIVE_MEMORY')
    if probe.get('code') != 0 or not match:
        return result
    total, used = (int(float(v)*1024**2) for v in match.groups())
    result.update(total_bytes=total, used_bytes=used, status='NORMAL', action='NONE')
    prior = [s for s in samples if boot_id and s.get('boot_id') == boot_id
             and isinstance(s.get('time'), (int, float)) and 1800 <= now-s['time'] <= 7200
             and isinstance((s.get('memory_policy') or {}).get('used_bytes'), int)]
    if prior:
        old = max(prior, key=lambda s: s['time'])
        result['growth_gib_per_hour'] = round((used-old['memory_policy']['used_bytes'])/GIB*3600/(now-old['time']), 2)
    pressure = evidence.get('pressure', {})
    elevated = pressure.get('code') == 0 and pressure.get('output', '').strip() in ('2','4')
    if total >= 4*GIB or elevated or (result['growth_gib_per_hour'] or 0) >= 1:
        result.update(status='REVIEW', action='SAVE_WORK_AND_CLOSE_UNUSED_HEAVY_APPS; REVIEW_ACTIVITY_MONITOR_MEMORY')
    return result


def assess(free, path, now, samples, boot_id=None):
    mode = next((name for limit, name in ((8, 'EMERGENCY'), (15, 'CRITICAL'),
                (25, 'WARNING'), (40, 'WATCH')) if free < limit * GIB), 'NORMAL')
    valid = [(s.get('time'), s.get('disk_free')) for s in samples
             if isinstance(s, dict) and s.get('disk_path') == path
             and (boot_id is None or s.get('boot_id') == boot_id)
             and isinstance(s.get('time'), (int, float))
             and isinstance(s.get('disk_free'), int)
             and 0 < now - s['time'] <= 7200 and s['disk_free'] >= 0]
    valid.sort()
    result = dict(schema_version='v1', mode=mode, free_bytes=free,
                  rate_gib_per_day=None, hours_to_8_gib=None, trend='UNKNOWN',
                  samples=len(valid) + 1, note='Trend is a short-window estimate, not a guarantee.')
    if len(valid) < 2 or now - valid[0][0] < 1800:
        return result
    seconds = now - valid[0][0]
    rate = (free - valid[0][1]) * 86400 / seconds / GIB
    result.update(rate_gib_per_day=round(rate, 2), trend='FALLING' if rate < 0 else 'STABLE_OR_RISING')
    if rate < 0 and free > 8 * GIB:
        result['hours_to_8_gib'] = round((free / GIB - 8) / -rate * 24, 1)
    return result
