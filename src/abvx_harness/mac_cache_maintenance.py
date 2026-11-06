"""One explicit maintenance scenario: approved npm download-cache removal.

No scheduler, arbitrary path, project file, token or package-script execution.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import stat
import subprocess
import time
from .mac_operator import STATE, save, load
from . import mac_budget as budget
INTERNAL = Path('/System/Volumes/Data')


def target():
    return Path.home() / '.npm/_cacache'


def fingerprint(path, *, allow_nested_symlinks=False):
    start = time.monotonic()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('SYMLINK_REJECTED')
    first = path.lstat()
    if not stat.S_ISDIR(first.st_mode):
        raise ValueError('NOT_DIRECTORY')
    if first.st_dev != INTERNAL.stat().st_dev:
        raise ValueError('NOT_INTERNAL')
    stack, digest, size, count = [path], hashlib.sha256(), 0, 0
    while stack:
        budget.check()
        if count >= 25000 or time.monotonic() - start > 5:
            raise ValueError('SCAN_BUDGET')
        p = stack.pop()
        s = p.lstat()
        if s.st_dev != first.st_dev or not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode) or
                                            (allow_nested_symlinks and stat.S_ISLNK(s.st_mode))):
            raise ValueError('UNSUPPORTED_ENTRY')
        digest.update(json.dumps([str(p.relative_to(path)), s.st_dev, s.st_ino,
                                 s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns], separators=(',', ':')).encode())
        size += s.st_blocks * 512
        count += 1
        if stat.S_ISDIR(s.st_mode):
            children = []
            with os.scandir(p) as entries:
                for e in entries:
                    budget.check()
                    if count + len(stack) + len(children) >= 25000:
                        raise ValueError('SCAN_BUDGET')
                    children.append(Path(e.path))
            stack.extend(sorted(children, reverse=True))
    return {'digest': digest.hexdigest(), 'allocated_bytes': size, 'entries': count,
            'device': first.st_dev, 'inode': first.st_ino,
            'allow_nested_symlinks': allow_nested_symlinks}


def active_managers(lines):
    """Read only executable/entry-script tokens, never shell script body text."""
    found = set()
    for line in lines:
        try:
            words = shlex.split(line)
        except ValueError:
            continue
        if not words:
            continue
        command = Path(words[0]).name
        family = None
        if command in {'npm','npx','pnpm','yarn','node-gyp','brew','ShipIt','helpd','Installer','Autoupdate','Updater'}:
            family = command
        elif re.fullmatch(r'pip(?:3(?:\.\d+)?)?', command):
            family = 'pip'
        elif command.startswith('python') and len(words)>2 and words[1:3] == ['-m','pip']:
            family = 'pip'
        elif command in ('node','nodejs','ruby') and len(words)>1:
            entry = Path(words[1]).name
            family = {'npm-cli.js':'npm','npx-cli.js':'npx','pnpm.cjs':'pnpm',
                      'pnpm.js':'pnpm','yarn.js':'yarn','brew.rb':'brew'}.get(entry)
        if family:
            found.add(family)
    return found


def activity(path):
    """Known open files, scoped package activity, or unknown visibility block."""
    try:
        p = subprocess.run(['/usr/sbin/lsof', '-nP', '+D', str(path)],
                           capture_output=True, timeout=budget.timeout(12))
        if p.returncode != 1 or p.stdout.strip() or p.stderr.strip():
            return {'idle':False, 'reason':'OPEN_FILES_OR_LSOF_UNKNOWN'}
        p = subprocess.run(['/bin/ps','-axo','pid=,command='],capture_output=True,text=True,timeout=budget.timeout(5))
        if p.returncode:
            return {'idle':False,'reason':'PROCESS_LIST_UNKNOWN'}
        commands = []
        for line in p.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and parts[0].isdigit():
                commands.append(parts[1])
        families = active_managers(commands)
        if path.name == '_cacache' or 'node-gyp' in path.parts:
            relevant = {'npm','npx','pnpm','yarn','node-gyp'}
        elif 'Homebrew' in path.parts:
            relevant = {'brew'}
        elif path.name == 'pip':
            relevant = {'pip'}
        elif path.name == 'com.microsoft.VSCode.ShipIt':
            relevant = {'ShipIt'}
        elif path.name == 'com.apple.helpd':
            relevant = {'helpd'}
        elif path.name == 'Installation' and 'com.openai.codex' in path.parts and 'org.sparkle-project.Sparkle' in path.parts:
            relevant = {'Installer','Autoupdate','Updater'}
        else:
            return {'idle':False,'reason':'UNKNOWN_TARGET_ACTIVITY_RULE'}
        blocked = sorted(families & relevant)
        return {'idle':not blocked, 'reason':'PACKAGE_OR_UPDATER_ACTIVE' if blocked else 'VERIFIED_IDLE',
                'families':blocked}
    except budget.Expired:
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'idle':False,'reason':'PROCESS_VISIBILITY_UNAVAILABLE','error_type':type(exc).__name__}


def idle(path):
    return activity(path)['idle']


def identifier(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def plan():
    p = target()
    try:
        evidence = fingerprint(p)
    except budget.Expired:
        raise
    except (OSError, ValueError) as exc:
        return {'status': 'BLOCKED', 'reason': str(exc) if type(exc) is ValueError else type(exc).__name__}
    value = {'schema_version': 'v1', 'scenario': 'npm-download-cache-only',
             'path': str(p), 'created_at': time.time(), 'measurement': evidence,
             'consequence': 'Cached package downloads will be lost; future installs may require internet. Installed dependencies remain in place.',
             'recovery': 'npm can download packages again when online; no local undo.',
             'automatic_execution': False}
    key = identifier(value)
    folder = STATE / 'maintenance-plans'
    folder.mkdir(mode=0o700, exist_ok=True)
    save(folder / (key + '.json'), value)
    return {'status': 'AWAITING_SPECIFIC_OWNER_APPROVAL', 'plan_id': key, **value,
            'process_check': 'VERIFIED_IDLE' if idle(p) else 'UNKNOWN_OR_BUSY',
            'note': 'Apply revalidates age, exact path, fingerprint, idle state and one-use receipt. No deletion performed.'}


def apply(key):
    if not re.fullmatch('[a-f0-9]{64}', key or ''):
        return {'status': 'BLOCKED', 'reason': 'INVALID_PLAN_ID'}
    value = load(STATE / 'maintenance-plans' / (key + '.json'))
    if not isinstance(value, dict) or value.get('schema_version') != 'v1' or identifier(value) != key or value.get('path') != str(target()) or value.get('scenario') != 'npm-download-cache-only':
        return {'status': 'BLOCKED', 'reason': 'PLAN_MISMATCH'}
    if not 0 <= time.time() - value.get('created_at', 0) <= 86400:
        return {'status': 'BLOCKED', 'reason': 'PLAN_EXPIRED'}
    folder = STATE / 'maintenance-results'
    folder.mkdir(mode=0o700, exist_ok=True)
    receipt_path = folder / (key + '.json')
    if receipt_path.exists():
        return {'status': 'DUPLICATE', 'receipt': str(receipt_path)}
    return remove_snapshot(target(), value['measurement'], receipt_path,
                           'LOCAL_EXPLICIT_PLAN_APPROVAL', key)


def remove_snapshot(p, measurement, receipt_path, source, key, *, checkpoint=None):
    """Private shared executor; callers must enforce the fixed target allowlist."""
    def step(phase):
        if checkpoint is not None:
            checkpoint(phase)
        budget.check()
    step('revalidate-before')
    if receipt_path.exists():
        return {'status': 'DUPLICATE', 'receipt': str(receipt_path)}
    try:
        if not shutil.rmtree.avoids_symlink_attacks:
            raise ValueError('UNSAFE_RUNTIME')
        if fingerprint(p, allow_nested_symlinks=measurement.get('allow_nested_symlinks', False)) != measurement:
            raise ValueError('CACHE_CHANGED_REPLAN')
        if not idle(p):
            raise ValueError('PROCESS_CHECK_UNKNOWN_OR_BUSY')
        if fingerprint(p, allow_nested_symlinks=measurement.get('allow_nested_symlinks', False)) != measurement:
            raise ValueError('CACHE_CHANGED_REPLAN')
        step('revalidate-after')
        fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except budget.Expired:
        raise
    except (OSError, ValueError) as exc:
        return {'status': 'BLOCKED', 'reason': str(exc) if type(exc) is ValueError else type(exc).__name__}
    try:
        s = os.stat(p.name, dir_fd=fd, follow_symlinks=False)
        if (s.st_dev, s.st_ino) != (measurement['device'], measurement['inode']):
            return {'status': 'BLOCKED', 'reason': 'TARGET_CHANGED'}
        before = shutil.disk_usage(p).free
        budget.check(15)
        step('remove-before')
        receipt = {'schema_version': 'v1', 'plan_id': key, 'status': 'IN_PROGRESS',
                   'started_at': time.time(), 'source': source,
                   'target': str(p), 'allocated_bytes_before': measurement['allocated_bytes']}
        try:
            with receipt_path.open('x') as stream:
                json.dump(receipt, stream)  # Claim once before destructive effects.
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            return {'status': 'DUPLICATE'}
        try:
            shutil.rmtree(p.name, dir_fd=fd)
            # Verify against the same opened parent, not a replaced pathname.
            try:
                os.stat(p.name, dir_fd=fd, follow_symlinks=False)
                receipt['status'] = 'TARGET_RECREATED_OR_REMAINS'
            except FileNotFoundError:
                receipt['status'] = 'VERIFIED_REMOVED'
            receipt['disk_free_delta_bytes'] = shutil.disk_usage(Path.home()).free - before
            receipt['note'] = 'Disk free delta includes concurrent host activity; not a causal estimate of reclaimed bytes.'
        except OSError as exc:
            receipt.update(status='FAILED_OR_PARTIAL_NO_AUTORETRY', error_type=type(exc).__name__)
        receipt['finished_at'] = time.time()
        save(receipt_path, receipt)
        step('remove-after')
        return receipt
    finally:
        os.close(fd)


def main():
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['plan', 'apply'])
    parser.add_argument('--approve-plan-id')
    args = parser.parse_args()
    with (STATE / 'maintenance.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = plan() if args.action == 'plan' else apply(args.approve_plan_id)
        if args.action == 'apply' and re.fullmatch('[a-f0-9]{64}', args.approve_plan_id or ''):
            folder = STATE / 'maintenance-attempts'
            folder.mkdir(mode=0o700, exist_ok=True)
            save(folder / (args.approve_plan_id + '-last.json'),
                 {'schema_version': 'v1', 'time': time.time(), 'result': result})
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
