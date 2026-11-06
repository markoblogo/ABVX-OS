#!/usr/bin/env python3
"""Process one agent/browser-acquired Radar run using existing offline providers.

This command does not browse or authenticate. The scheduled Codex agent performs
acquisition first and supplies a dated receipt. Canonical records remain read-only.
"""
import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'src'), str(REPO / '.tmp/book-core-runtime')]
from abvx_harness import book_radar_markets as markets
from abvx_harness import book_radar_learning as learning


def run(args):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', args.run_id):
        raise ValueError('run-id must be a short filesystem-safe identifier')
    receipt = json.loads(args.acquisition.read_text())
    attempts = receipt['attempts']
    if set(a['marketplace'] for a in attempts) != set(markets.MARKETS):
        raise ValueError('Attempt all four markets; report concrete failures')
    live, retained = [], []
    for a in attempts:
        if not a.get('source_url', '').startswith('https://') or not a.get('evidence_ref'):
            raise ValueError('Each attempt needs a source and retained evidence reference')
        source = markets.proof_path(args.acquisition.parent, {'evidence_path': a['evidence_ref'],
                                    'evidence_sha256': a['evidence_sha256']})
        retained.append((a['evidence_ref'], source))
        captured = datetime.fromisoformat(a['captured_at_utc'].replace('Z', '+00:00'))
        if captured.tzinfo is None or captured.astimezone(timezone.utc).date().isoformat() != args.as_of:
            raise ValueError('Acquisition receipt must be explicitly timed on the run date')
        if a['status'] not in {'AVAILABLE', 'ACCESS_FAILED', 'ACCESS_BLOCKED', 'AUTH_REQUIRED'}:
            raise ValueError('Unknown source status')
        if a['status'] == 'AVAILABLE':
            if a.get('method') != 'LIVE_BROWSER':
                raise ValueError('Cached retrievals cannot certify live acquisition')
            live.append(a['marketplace'])
        elif not a.get('blocker'):
            raise ValueError('A failed source needs a concrete blocker')
    if not live:
        raise ValueError('At least one real live source is required for a completed run')
    packet = markets.check(args.input)
    ranking = markets.read(args.ranking) if getattr(args, 'ranking', None) else None
    markets.research_priorities(ranking, {o['id'] for o in packet['opportunities']})
    observed = {a['marketplace'] for a in attempts if a['status'] == 'AVAILABLE'}
    acquired_proofs = {(a['marketplace'], a['source_url'], a['evidence_sha256'])
                      for a in attempts if a['status'] == 'AVAILABLE'}
    if not observed <= {r['marketplace'] for r in packet['observations'] if r['availability'] == 'AVAILABLE'}:
        raise ValueError('Each successful acquisition needs a processed observation')
    for row in packet['observations']:
        if row['observed_at'] != args.as_of:
            raise ValueError('Do not import historical observations as current')
        if row['availability'] == 'AVAILABLE' and row['marketplace'] not in observed:
            raise ValueError('A failed acquisition cannot supply available observations')
        if row['availability'] == 'AVAILABLE':
            if (row['marketplace'], row['source_url'], row['evidence_sha256']) not in acquired_proofs:
                raise ValueError('Every available observation needs its own live source/proof receipt')
            if not any(s['status'] != 'MISSING' for s in row['metrics'].values()):
                raise ValueError('Available acquisition must supply an actual observed metric')
    from abvx_harness import book_radar_wide as wide, book_readiness
    readiness_snapshot = book_readiness.weekly_handoff(REPO, args.as_of)
    book_review = wide.weekly_book_review(REPO, args.as_of, readiness_snapshot=readiness_snapshot)
    destination = REPO / '.tmp/multi-market-radar/runs' / args.run_id
    if destination.exists():
        raise ValueError('Use a new run-id; existing execution records are immutable')
    destination.mkdir(parents=True)
    for relative, source in retained:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    def save(name, value):
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    save('acquisition.json', receipt)
    save('input.json', packet)
    save('import-result.json', markets.import_bundle(destination / 'radar-root', args.input))
    comparison = markets.report(destination / 'radar-root', args.as_of, readiness_root=REPO, readiness_snapshot=readiness_snapshot)
    save('book-readiness.json', comparison['book_readiness'])
    save('markets.json', comparison)
    (destination / 'markets.md').write_text(markets.render(comparison) + '\n')
    weekly = markets.weekly(destination / 'radar-root', args.as_of,
                            amazon_committed=None, hours=args.hours, research_ranking=ranking, readiness_root=REPO, readiness_snapshot=readiness_snapshot)
    if book_review is not None:
        weekly['book_discovery'] = book_review
        save('book-discovery.json', book_review)
    save('weekly.json', weekly)
    (destination / 'weekly.md').write_text(markets.render(weekly) + '\n')
    result = {'execution': 'COMPLETE', 'source_coverage': 'FULL' if len(set(live)) == 4 else 'PARTIAL',
              'live_markets': sorted(set(live)), 'output': str(destination),
              'canonical_state_written': False, 'production_authorized': False,
              'completed_at_utc': datetime.now(timezone.utc).isoformat()}
    if book_review is not None:
        result['book_discovery'] = {'status':'READY_FOR_RESEARCH_REVIEW' if book_review['current_acquisition'] else 'ACQUISITION_REQUIRED',
            'report_path':str(destination/'book-discovery.json'),
            'owner_research_recommendation_count':len(book_review['owner_research_recommendations']),
            'method_review':book_review['method_review']}
    save('execution.json', result)
    if ranking is not None:
        save('ranking.json', ranking)
    result['learning'] = summarize_learning(learning.learn_run(destination, getattr(args, 'history', learning.DEFAULT_HISTORY)))
    return result


def summarize_learning(result):
    report = result['report']
    return {'status': 'COMPLETE', 'report_path': result['report_path'],
            'research_progress': report['research_progress'],
            'production_policy': report['production_policy'], 'production_authorized': False}


def execute(args):
    if getattr(args, 'method_event', None):
        event = learning.method_event(args.history, markets.read(args.method_event),
                                      args.evidence_base or args.method_event.parent)
        report = learning.retrospective(args.history)
        return {'event_digest': event['record_digest'], 'recorded_at': event['recorded_at'],
                'measurements': event['measurements'], 'report_digest': report['state_digest'],
                'production_authorized': False}
    if getattr(args, 'method_report', False):
        return learning.method_comparison(args.history)
    if args.learn_run:
        return summarize_learning(learning.learn_run(args.learn_run, args.history))
    if args.learn_history:
        runs = [p.parent for p in (REPO / '.tmp/multi-market-radar/runs').glob('*/execution.json')
                if markets.read(p).get('execution') == 'COMPLETE']
        runs.sort(key=lambda p: (markets.read(p / 'execution.json').get('completed_at_utc', ''), p.name))
        if not runs:
            raise ValueError('No completed retained runs')
        for path in runs:
            result = learning.learn_run(path, args.history)
        return {'mode': 'RETAINED_HISTORY_REPLAY', **summarize_learning(result)}
    if args.learning_event:
        event = learning.add_event(args.history, markets.read(args.learning_event), args.evidence_base or args.learning_event.parent)
        report = learning.retrospective(args.history)
        return {'event_digest': event['record_digest'], 'status': event['status'], 'report_digest': report['state_digest']}
    if args.bind_outcomes:
        if not args.actuals or not args.evidence_base:
            raise ValueError('Outcome binding requires --actuals and --evidence-base')
        linked = learning.bind_outcomes(args.history, args.bind_outcomes, args.actuals, args.evidence_base)
        report = learning.retrospective(args.history)
        return {'linked_records': len(linked), 'report_digest': report['state_digest'], 'production_authorized': False}
    if not all((args.input, args.acquisition, args.run_id, args.as_of)):
        raise ValueError('Research requires input, acquisition, run-id and as-of')
    return run(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--acquisition', type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--as-of')
    parser.add_argument('--hours', type=float, default=4)
    parser.add_argument('--ranking', type=Path)
    parser.add_argument('--history', type=Path, default=learning.DEFAULT_HISTORY)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--learn-run', type=Path)
    mode.add_argument('--learn-history', action='store_true')
    mode.add_argument('--learning-event', type=Path)
    mode.add_argument('--bind-outcomes', type=Path)
    mode.add_argument('--method-event', type=Path)
    mode.add_argument('--method-report', action='store_true')
    parser.add_argument('--actuals', type=Path)
    parser.add_argument('--evidence-base', type=Path)
    try:
        print(json.dumps(execute(parser.parse_args()), ensure_ascii=False))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'Radar execution blocked: {error}\n')
