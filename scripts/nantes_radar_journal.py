#!/usr/bin/env python3
"""Private six-stage Nantes report journal. No research, scheduler or transport.

Atomic run state is authoritative. REPORT.md is a regenerable projection.
Publication receipts record externally verified delivery, never send anything.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

STAGES = ('youtube', 'gmail', 'kdp_markets', 'jobs', 'udemy', 'creative_assets')
TERMINAL = {'COMPLETE', 'EMPTY', 'PARTIAL', 'BLOCKED', 'FAILED', 'SKIPPED'}
LABELS = dict(zip(STAGES, ('YouTube', 'Gmail', 'KDP / рынки', 'Вакансии', 'Udemy', 'Творческие возможности / активы')))


def now():
    return datetime.now(timezone.utc).isoformat()


def stamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp requires timezone')
    return parsed


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.journal-')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def runpath(root, run):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}-(weekly|daily)', run):
        raise ValueError('Run ID must be YYYY-MM-DD-weekly or -daily')
    datetime.fromisoformat(run[:10])
    return Path(root) / run


@contextmanager
def locked(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / '.lock').open('a') as lock:
        os.chmod(root / '.lock', 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def load(root, run):
    state = json.loads((runpath(root, run) / 'state.json').read_text())
    if state.get('version') != 1 or state.get('run_id') != run or set(state.get('stages', {})) != set(STAGES):
        raise ValueError('Invalid journal; restore verified state; do not reinitialize')
    return state


def save(root, state):
    atomic(runpath(root, state['run_id']) / 'state.json', json.dumps(state, ensure_ascii=False, indent=2) + '\n')


def context(root, run):
    """Read at most three earlier runs; historical claims grant no authority."""
    runpath(root, run)  # Validate the requested cutoff without creating a run.
    root = Path(root)
    if not root.is_dir():
        raise ValueError('Journal unavailable; history is UNKNOWN')
    previous = []
    for path in root.iterdir():
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}-(weekly|daily)', path.name) and path.name[:10] < run[:10]:
            runpath(root, path.name)
            previous.append(path.name)
    runs = []
    for name in sorted(previous, reverse=True)[:3]:
        state = load(root, name)  # Missing/corrupt selected history must not disappear.
        stages = {}
        for stage in STAGES:
            item = state['stages'][stage]
            summary = item.get('summary', '')
            reason = item.get('failure_reason', '')
            sources = item.get('sources', [])
            if (item.get('status') not in TERMINAL | {'NOT_STARTED', 'IN_PROGRESS'} or
                    not isinstance(summary, str) or not isinstance(reason, str) or
                    not isinstance(sources, list)):
                raise ValueError('Invalid historical stage')
            for source in sources:
                if not isinstance(source, dict) or not isinstance(source.get('ref'), str):
                    raise ValueError('Invalid historical source')
                stamp(source['checked_at'])
            stages[stage] = {
                'status': item['status'], 'finished_at': item.get('finished_at'),
                'summary': summary[:600], 'failure_reason': reason[:300],
                'sources': [{'ref': s['ref'][:1000], 'checked_at': s['checked_at']} for s in sources[:3]],
                'truncated': len(summary) > 600 or len(reason) > 300 or len(sources) > 3 or
                             any(len(s['ref']) > 1000 for s in sources[:3])}
        runs.append({'run_id': name, 'state_file': str(runpath(root, name) / 'state.json'),
                     'state_content_sha256': hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest(),
                     'publication_status': state['publication']['status'], 'stages': stages})
    return {'status': 'HISTORICAL_CONTEXT' if runs else 'NO_HISTORY',
            'as_of_run': run, 'generated_at': now(), 'runs': runs,
            'historical_claims_are_current_verification': False,
            'owner_decisions_inferred': False, 'external_actions': 'NONE'}


def init(root, run, mode):
    with locked(root):
        path = runpath(root, run) / 'state.json'
        if mode not in ('weekly', 'daily') or not run.endswith('-' + mode):
            raise ValueError('Run ID/mode mismatch')
        if path.exists():
            return load(root, run)
        state = {'version': 1, 'run_id': run, 'mode': mode, 'created_at': now(),
                 'publication': {'status': 'NOT_PUBLISHED'},
                 'stages': {s: {'status': 'NOT_STARTED', 'attempts': []} for s in STAGES}}
        save(root, state)
        return state


def begin(root, run, stage):
    with locked(root):
        state = load(root, run)
        if stage not in STAGES:
            raise ValueError('Unknown stage')
        if state['publication']['status'] != 'NOT_PUBLISHED':
            raise ValueError('Publication frozen; resume publication, not research')
        item = state['stages'][stage]
        if item['status'] in ('COMPLETE', 'EMPTY', 'SKIPPED'):
            return {'status': 'ALREADY_SAVED', 'stage': stage}
        if item['status'] == 'IN_PROGRESS':
            attempt = item['attempts'][-1]
            if (stamp(now()) - stamp(attempt['started_at'])).total_seconds() < 300:
                raise ValueError('Stage already running; wait for 300-second lease')
            attempt.update(status='INTERRUPTED', finished_at=now(), failure_reason='Lease expired after interruption')
            item.update(status='FAILED', retryable=True, failure_reason='Interrupted stage')
            save(root, state)  # Persist terminal failure even when the retry budget is exhausted.
        if len(item['attempts']) >= 2:
            raise ValueError('Retry budget exhausted (two attempts per stage/run)')
        if item['attempts'] and not item.get('retryable', False):
            raise ValueError('Non-retryable failure; continue other stages')
        token = str(uuid.uuid4())
        item['attempts'].append({'token': token, 'started_at': now(), 'status': 'IN_PROGRESS'})
        item['status'] = 'IN_PROGRESS'
        save(root, state)
        return {'stage': stage, 'token': token, 'attempt': len(item['attempts']),
                'packet_file': str(runpath(root, run) / (stage + '-packet.json'))}


def finish(root, run, stage, packet):
    with locked(root):
        state = load(root, run)
        item = state['stages'][stage]
        if state['publication']['status'] != 'NOT_PUBLISHED':
            raise ValueError('Publication frozen')
        if item['status'] != 'IN_PROGRESS' or packet.get('token') != item['attempts'][-1]['token']:
            raise ValueError('Stale or missing stage token')
        status = packet.get('status')
        if status not in TERMINAL or not isinstance(packet.get('summary'), str) or not packet['summary'].strip():
            raise ValueError('Terminal status and nonempty summary required')
        if status not in ('COMPLETE', 'EMPTY') and not packet.get('failure_reason'):
            raise ValueError('Partial/blocked/failed/skipped stage requires failure_reason')
        sources = packet.get('sources', [])
        if not isinstance(sources, list) or (status in ('COMPLETE', 'EMPTY') and not sources):
            raise ValueError('Evidence required for COMPLETE/EMPTY')
        for source in sources:
            if not isinstance(source, dict) or not source.get('ref'):
                raise ValueError('Source reference required')
            stamp(source['checked_at'])
        if packet.get('retryable', False) not in (True, False):
            raise ValueError('retryable must be boolean')
        receipt = {k: packet[k] for k in ('status', 'summary', 'sources', 'failure_reason', 'retryable') if k in packet}
        receipt.update(finished_at=now(), token=packet['token'])
        item['attempts'][-1].update(receipt)
        item.update(receipt)
        save(root, state)
    result = assemble(root, run)
    result.pop('text')
    result.update(stage=stage, saved_status=status)
    return result


def render(state):
    lines = ['# Nantes Radar — ' + state['run_id'], '', 'Режим: ' + state['mode'],
             'Публикация: ' + state['publication']['status'], '', '| Блок | Статус | Попытки |', '|---|---|---|']
    if state.get('publication_history'):
        previous = state['publication_history'][-1]
        lines[4:4] = ['Дополнение к ранее доставленному выпуску: ' + previous['chat_ref'], '']
    for stage in STAGES:
        item = state['stages'][stage]
        lines.append(f"| {LABELS[stage]} | {item['status']} | {len(item['attempts'])}/2 |")
    for stage in STAGES:
        item = state['stages'][stage]
        lines.extend(['', '## ' + LABELS[stage], '', item.get('summary', 'Результат не сохранён; этап не завершён.')])
        if item.get('failure_reason'):
            lines.extend(['', 'Ограничение: ' + item['failure_reason']])
        for source in item.get('sources', []):
            lines.append(f"\nИсточник: {source['ref']} · проверка {source['checked_at']}")
    for review in state.get('book_reviews', [])[-1:]:
        lines.extend(['', '## Книжное исследовательское обновление', '', review['summary'],
                      'Карточки: ' + ', '.join(review['candidate_ids']),
                      'Сохранённый пакет: ' + review['path'],
                      'SHA256: ' + review['sha256'],
                      'Дополнение исследования; прежние этапы и доставка не изменены.'])
    return '\n'.join(lines) + '\n'


def assemble(root, run):
    with locked(root):
        state = load(root, run)
        text = render(state)
        atomic(runpath(root, run) / 'REPORT.md', text)
        return {'status': 'COMPLETE' if all(s['status'] in ('COMPLETE', 'EMPTY') for s in state['stages'].values()) else 'PARTIAL',
                'report_file': str(runpath(root, run) / 'REPORT.md'), 'text': text}


def attach_book_review(root, run, path):
    """Append a verified research review; preserve all stages and delivery receipts."""
    source = Path(path).resolve()
    raw = source.read_bytes()
    review = json.loads(raw)
    if review.get('schema_version') != 'book-radar-owner-review/v1' or review.get('run_id') != run or review.get('as_of') != run[:10] or review.get('production_authorized') is not False:
        raise ValueError('Book review must match this run and grant no production authority')
    if not isinstance(review.get('summary'), str) or not review['summary'].strip() or not isinstance(review.get('recommendations'), list) or len(review['recommendations']) > 2:
        raise ValueError('Book review needs a summary and at most two recommendations')
    ids = []
    for card in review['recommendations']:
        if not isinstance(card, dict) or not card.get('id') or not card.get('title') or card.get('production_authorized') is not False:
            raise ValueError('Invalid book recommendation or production authority')
        ids.append(card['id'])
    if len(set(ids)) != len(ids): raise ValueError('Duplicate book recommendation')
    sources = review.get('sources', [])
    if not isinstance(sources, list) or not sources: raise ValueError('Book review needs dated sources')
    for item in sources:
        if not isinstance(item, dict) or not isinstance(item.get('ref'), str) or not item['ref'].startswith('https://'):
            raise ValueError('Book review needs public source URLs')
        if stamp(item['checked_at']).date().isoformat() > review['as_of']:
            raise ValueError('Future book review source')
    sha = hashlib.sha256(raw).hexdigest()
    with locked(root):
        state = load(root, run)
        entries = state.setdefault('book_reviews', [])
        if any(e['sha256'] == sha for e in entries):
            return {'status':'ALREADY_ATTACHED', 'sha256':sha, 'publication_unchanged':True}
        target = runpath(root, run) / ('book-review-' + sha + '.json')
        atomic(target, raw.decode('utf-8'))
        entries.append({'sha256':sha, 'path':str(target.resolve()), 'as_of':review['as_of'],
                        'summary':review['summary'], 'candidate_ids':ids,
                        'status':'RESEARCH_ONLY_NOT_DELIVERED', 'attached_at':now()})
        save(root, state)
        atomic(runpath(root, run) / 'REPORT.md', render(state))
    return {'status':'ATTACHED', 'sha256':sha, 'path':str(target.resolve()),
            'candidate_ids':ids, 'publication_unchanged':True}


def prepare(root, run):
    with locked(root):
        state = load(root, run)
        if state['publication']['status'] != 'NOT_PUBLISHED':
            return state['publication']
        if any(s['status'] == 'IN_PROGRESS' for s in state['stages'].values()):
            raise ValueError('Finish running stage before preparing publication')
        if state.get('resume_base') == content_digest(state):
            raise ValueError('No changed stage result; do not republish')
        report = render(state)
        sha = hashlib.sha256(report.encode()).hexdigest()
        revision = state['publication'].get('revision', 1)
        final = runpath(root, run) / ('FINAL.md' if revision == 1 else f'FINAL-{revision}.md')
        atomic(final, report)
        state['publication'] = {'status': 'PREPARED', 'sha256': sha, 'prepared_at': now(),
                                'revision': revision, 'report_file': str(final)}
        save(root, state)
        return state['publication']


def ack(root, run, sha, chat_ref):
    if not re.fullmatch(r'https://chatgpt.com/c/[0-9a-f-]+\?messageId=[0-9a-f-]+', chat_ref):
        raise ValueError('Exact verified ChatGPT conversation/message URL required')
    with locked(root):
        state = load(root, run)
        receipt = state['publication']
        if receipt['status'] == 'PUBLISHED':
            if receipt['sha256'] == sha and receipt['chat_ref'] == chat_ref:
                return receipt
            raise ValueError('Already published; duplicate delivery rejected')
        if receipt['status'] != 'PREPARED' or receipt['sha256'] != sha:
            raise ValueError('Unprepared or mismatched publication')
        revision = receipt.get('revision', 1)
        final = runpath(root, run) / ('FINAL.md' if revision == 1 else f'FINAL-{revision}.md')
        if hashlib.sha256(final.read_bytes()).hexdigest() != sha:
            raise ValueError('Final report integrity mismatch')
        receipt.update(status='PUBLISHED', chat_ref=chat_ref, verified_at=now())
        save(root, state)
        return receipt


def content_digest(state):
    values = {k: {field: item.get(field) for field in ('status', 'summary', 'failure_reason')}
              for k, item in state['stages'].items()}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def resume(root, run, reason):
    """Explicit source-recovery revision; never discard prior delivery/history."""
    if not reason or not reason.strip():
        raise ValueError('Observed recovery reason required')
    with locked(root):
        state = load(root, run)
        if state['publication']['status'] != 'PUBLISHED':
            raise ValueError('Verify prior delivery before opening a recovery revision')
        pending = [stage for stage, item in state['stages'].items()
                   if item['status'] in ('NOT_STARTED', 'IN_PROGRESS') or
                   (item['status'] in ('PARTIAL', 'BLOCKED', 'FAILED') and
                    item.get('retryable') is True and len(item['attempts']) < 2)]
        if not pending:
            return {'status': 'NOTHING_TO_RESUME'}
        state.setdefault('publication_history', []).append(dict(state['publication']))
        state['resume_base'] = content_digest(state)
        state['publication'] = {'status': 'NOT_PUBLISHED',
                                'revision': state['publication'].get('revision', 1) + 1,
                                'resume_reason': reason, 'resumed_at': now()}
        save(root, state)
        return {'status': 'RECOVERY_REVISION_OPENED', 'pending_stages': pending,
                'revision': state['publication']['revision']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, default=Path(__file__).with_name('nantes-radar-journal'))
    parser.add_argument('action', choices=('init', 'status', 'context', 'begin', 'finish', 'assemble', 'prepare', 'ack', 'resume', 'attach-book-review'))
    parser.add_argument('--run', required=True)
    parser.add_argument('--mode', choices=('weekly', 'daily'))
    parser.add_argument('--stage', choices=STAGES)
    parser.add_argument('--packet', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--chat-ref')
    parser.add_argument('--reason')
    args = parser.parse_args()
    try:
        if args.action == 'init':
            result = init(args.journal, args.run, args.mode)
        elif args.action == 'status':
            result = load(args.journal, args.run)
        elif args.action == 'context':
            result = context(args.journal, args.run)
        elif args.action == 'begin':
            result = begin(args.journal, args.run, args.stage)
        elif args.action == 'finish':
            result = finish(args.journal, args.run, args.stage, json.loads(args.packet.read_text()))
        elif args.action == 'assemble':
            result = assemble(args.journal, args.run)
        elif args.action == 'prepare':
            result = prepare(args.journal, args.run)
        elif args.action == 'attach-book-review':
            if args.packet is None: raise ValueError('Book review packet required')
            result = attach_book_review(args.journal, args.run, args.packet)
        elif args.action == 'resume':
            result = resume(args.journal, args.run, args.reason)
        else:
            result = ack(args.journal, args.run, args.sha256, args.chat_ref)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, AttributeError, TypeError) as exc:
        parser.exit(2, 'JOURNAL_BLOCKED: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
