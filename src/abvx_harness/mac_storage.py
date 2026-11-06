"""Bounded internal-disk cleanup preview; never deletes or traverses symlinks."""
import os
from pathlib import Path
import time


def measure(path, *, seconds=3, max_entries=25000):
    start, size, count, errors = time.monotonic(), 0, 0, 0
    stack = [path]
    device = path.stat().st_dev if path.exists() else None
    while stack:
        current = stack.pop()
        if count >= max_entries or time.monotonic() - start > seconds:
            return {'allocated_bytes': size, 'entries': count, 'complete': False, 'errors': errors, 'reason': 'SCAN_BUDGET'}
        try:
            st = current.lstat()
            count += 1
            if current.is_symlink() or st.st_dev != device:
                continue
            size += st.st_blocks * 512
            if current.is_dir():
                with os.scandir(current) as entries:
                    for entry in entries:
                        if len(stack) + count >= max_entries:
                            return {'allocated_bytes': size, 'entries': count, 'complete': False, 'errors': errors, 'reason': 'SCAN_BUDGET'}
                        stack.append(Path(entry.path))
        except OSError:
            errors += 1
    return {'allocated_bytes': size, 'entries': count, 'complete': not errors, 'errors': errors}


def preview(home=None):
    home = home or Path.home()
    specs = [('Library/Caches/com.apple.helpd', 'Apple Help cache', 'Help may be downloaded again.'),
             ('Library/Caches/pip', 'Python package download cache', 'Future installs may need downloads.'),
             ('Library/Caches/Homebrew', 'Homebrew download cache', 'Future installs may need downloads.'),
             ('.npm/_cacache', 'npm content cache', 'Offline installs may fail until cache is rebuilt.')]
    candidates = []
    for rel, reason, consequence in specs:
        path = home / rel
        # Reject symlinks anywhere in the candidate's path, including cache parents.
        if any(p.is_symlink() for p in [path, *path.parents]):
            candidates.append({'path': str(path), 'status': 'EXCLUDED_SYMLINK'})
            continue
        if not path.exists():
            continue
        item = {'path': str(path), 'reason': reason, 'consequence': consequence,
                'measurement': measure(path), 'requires_specific_owner_approval': True}
        candidates.append(item)
    return {'mode': 'PREVIEW_ONLY', 'deletion_authorized': False, 'candidates': candidates,
            'estimated_allocated_bytes': sum(c.get('measurement', {}).get('allocated_bytes', 0) for c in candidates),
            'note': 'Allocated bytes may include shared blocks and scan limits; not guaranteed reclaimable. Do not clear while package installation is active.',
            'excluded': ['projects', 'documents', 'browser profiles and caches', 'keys', 'backups', 'application data', 'applications', 'Downloads', 'Trash']}


def disk_overview():
    """One-shot native inventory. Fixed categories, one filesystem, bounded scans."""
    from concurrent.futures import ThreadPoolExecutor
    import shutil
    import subprocess
    import sys
    if sys.platform != 'darwin':
        return {'status': 'UNSUPPORTED', 'reason': 'macOS only'}
    root = Path('/System/Volumes/Data')
    home = Path.home()
    device = root.stat().st_dev
    specs = [('top_level', name, root / name) for name in
             ('Users', 'Applications', 'Library', 'private', 'usr', 'opt')]
    specs += [('home_breakdown', name, home / name) for name in
              ('Library', 'Documents', 'Downloads', 'Desktop', 'Pictures', 'Movies',
               'Music', '.Trash', '.cache', '.npm', '.local', '.codex')]

    def scan(spec):
        group, label, path = spec
        result = {'group': group, 'category': label, 'path': str(path)}
        try:
            if path.is_symlink():
                return dict(result, status='EXCLUDED_SYMLINK')
            st = path.stat()
            if st.st_dev != device:
                return dict(result, status='EXCLUDED_OTHER_VOLUME')
        except FileNotFoundError:
            return dict(result, status='ABSENT')
        except OSError:
            return dict(result, status='UNAVAILABLE')
        try:
            run = subprocess.run(['/usr/bin/du', '-skx', str(path)],
                                 capture_output=True, text=True, timeout=20,
                                 env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
            first = run.stdout.split('\t', 1)[0].strip()
            result.update(status='COMPLETE' if run.returncode == 0 else 'PARTIAL',
                          allocated_bytes=int(first) * 1024 if first.isdigit() else None,
                          returncode=run.returncode,
                          diagnostic_lines=len(run.stderr.splitlines()))
        except subprocess.TimeoutExpired:
            result.update(status='TIME_LIMIT', allocated_bytes=None)
        except OSError:
            result.update(status='UNAVAILABLE', allocated_bytes=None)
        return result

    with ThreadPoolExecutor(max_workers=3) as pool:
        categories = list(pool.map(scan, specs))
    disk = shutil.disk_usage(root)
    return {'schema_version': 'v1', 'time': time.time(), 'mode': 'READ_ONLY_OVERVIEW',
            'disk_path': str(root), 'total_bytes': disk.total, 'free_bytes': disk.free,
            'used_bytes': disk.used, 'categories': categories,
            'deletion_authorized': False,
            'note': 'Home categories overlap Users; never add the two groups. Partial totals are lower bounds. APFS shared blocks, snapshots, hidden categories and protected files prevent reconciliation with df. Allocated bytes are not reclaimable bytes. No file contents are read; external volumes and symlinks are excluded. Each category has a 20-second limit.'}
