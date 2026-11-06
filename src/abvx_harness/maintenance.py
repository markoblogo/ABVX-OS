"""Read-only workspace hygiene projection over Git and existing portfolio state.

No content scanning, cleanup, scheduling, external writes or Cortex admission.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from .portfolio import inspect_portfolio


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL)


def category(path: str) -> str:
    parts = Path(path).parts
    if any(p in {'.codex', 'psychology-warehouse'} for p in parts) or 'credential' in path.lower():
        return 'PRIVATE_REVIEW'
    if parts[0] in {'books', 'artifacts', 'book-radar', 'evidence', 'output', 'events', 'content', 'learning'}:
        return 'WORKING_DATA_RETAIN'
    if path.endswith(('.log', '.pyc')) or Path(path).name == '.DS_Store':
        return 'DERIVED_REVIEW'
    if parts[0] in {'src', 'tests', 'schemas', 'scripts', 'bin', '.github'}:
        return 'CODE_REVIEW'
    if parts[0] in {'docs', 'registries', 'playbooks'} or path.endswith('.md'):
        return 'DOC_CONFIG_REVIEW'
    return 'UNCLASSIFIED_RETAIN'


def inspect(root: Path) -> dict:
    root = root.resolve()
    raw = _git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all').split(b'\0')
    files = []
    index = 0
    while index < len(raw) and raw[index]:
        record = raw[index].decode('utf-8', errors='surrogateescape')
        status, path = record[:2], record[3:]
        index += 1
        if 'R' in status or 'C' in status:
            index += 1  # Original name follows a rename/copy destination in -z output.
        target = root / path
        # Do not follow symlinks or inspect working-file contents.
        try:
            size = target.lstat().st_size if not target.is_symlink() else None
        except OSError:
            size = None
        files.append({'path': path, 'git_status': status, 'category': category(path), 'bytes': size})
    groups = defaultdict(lambda: {'files': 0, 'bytes': 0, 'unknown_sizes': 0})
    for item in files:
        group = groups[item['category']]
        group['files'] += 1
        if item['bytes'] is None:
            group['unknown_sizes'] += 1
        else:
            group['bytes'] += item['bytes']
    try:
        counts = _git(root, 'rev-list', '--left-right', '--count', 'origin/main...HEAD').decode().split()
        history = {'remote_only': int(counts[0]), 'local_only': int(counts[1]), 'basis': 'CACHED_ORIGIN_MAIN'}
    except subprocess.CalledProcessError:
        history = {'status': 'UNKNOWN', 'basis': 'NO_ORIGIN_MAIN'}
    try:
        portfolio = inspect_portfolio(root)
        queue = {'status': 'AVAILABLE', 'actionable_projects': len(portfolio['actionable']),
                 'waiting_projects': len(portfolio['waiting_for_human']),
                 'waiting_human_items': len(portfolio['human_queue'])}
    except (OSError, ValueError, KeyError, TypeError):
        queue = {'status': 'UNKNOWN'}
    return {'schema_version': 'abvx-maintenance-report/v1',
            'branch': _git(root, 'branch', '--show-current').decode().strip(),
            'changes': len(files), 'git_status_counts': dict(Counter(f['git_status'] for f in files)),
            'groups': dict(groups), 'history': history, 'portfolio_queue': queue,
            'files': files, 'writes_performed': False, 'deletion_authorized': False,
            'cortex_admission': 'NOT_PERFORMED',
            'next_actions': ['Verify code in an isolated checkout before publication.',
                             'Retain working data; archive only an approved path/hash manifest.',
                             'Review private material before GitHub or Cortex admission.']}


def main(argv=None, root=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect'])
    parser.add_argument('--json', action='store_true', help='Full local manifest; may expose private path names.')
    args = parser.parse_args(argv)
    result = inspect(root or Path(__file__).resolve().parents[2])
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"ABVX maintenance: {result['changes']} changed files; branch {result['branch']}")
        for name, group in sorted(result['groups'].items()):
            print(f"  {name}: {group['files']} files, {group['bytes'] / 1048576:.1f} MiB")
        print('Read-only. No files deleted or published; no knowledge admitted to Cortex.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
