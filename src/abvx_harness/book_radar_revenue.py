"""Revenue V2: external-only discovery contracts and read-only portfolio arbitration.

Operating configuration is separate from canonical Radar observations/history.
There are no KDP, production, advertising or audience-writing operations here.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .harness import ValidationError

U = 'UNKNOWN'
CLASSES = {'EXPLOIT', 'EXPLORE', 'SERIES_BET', 'SCALE'}
FORMATS = {'ebook', 'paperback', 'hardcover'}
LINE_FIELDS = {'commercial_line_id', 'repeat_buyer_potential', 'adjacent_title_map',
               'seriesability', 'second_title_cost', 'production_reuse',
               'audience_capture_path', 'time_to_second_title', 'launch_class'}


def _require(condition, message):
    if not condition:
        raise ValidationError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_external(card):
    """Allowlist prevents portfolio fields at both levels; no state/capability input."""
    keys = {'id', 'lane', 'buying_object', 'purchase_proposition', 'entry_route', 'observations'}
    _require(set(card) == keys, 'External discovery accepts only external card fields')
    _require(card['lane'] in {'A', 'B', 'C', 'D', 'E'}, 'Unknown discovery lane')
    for key in keys - {'observations'}:
        _require(isinstance(card[key], str) and bool(card[key].strip()), f'Missing {key}')
    _require(isinstance(card['observations'], list), 'External observations must be an array')
    for row in card['observations']:
        _require(set(row) == {'product_id', 'url', 'kind', 'observed_at'}, 'External observation contains unsupported context')
        _require(all(isinstance(v, str) and bool(v.strip()) for v in row.values()), 'Invalid external evidence')
        _require(row['url'].startswith('https://') and 'abvx' not in row['url'].lower(), 'External source URL required')
        _require(row['kind'] in {'PAID_ACTIVITY', 'PURCHASE_PROPOSITION', 'ENTRY_ROUTE'}, 'Unsupported external evidence kind')
        date.fromisoformat(row['observed_at'])
    if card['lane'] == 'E':
        paid = {r['product_id'] for r in card['observations'] if r['kind'] == 'PAID_ACTIVITY'}
        _require(len(paid) >= 2, 'Lane E requires repeated externally observed buying objects')


def freeze_qualification(card, result):
    """Record an independently reviewed result; repeated buying alone does not QUALIFY."""
    validate_external(card)
    _require(result in {'QUALIFY', 'PARK', 'KILL', 'INSUFFICIENT_EVIDENCE'}, 'Invalid qualification')
    return {'schema_version': 'book-radar-external-qualification/v1', 'card_id': card['id'],
            'card_sha256': _digest(card), 'result': result, 'basis': 'ZERO_PORTFOLIO_EXTERNAL_ONLY'}


def post_qualification(qualification, card, overlay):
    validate_external(card)
    _require(qualification == freeze_qualification(card, 'QUALIFY'), 'Independent QUALIFY and unchanged external card required')
    _require(not set(overlay) - LINE_FIELDS, 'Unsupported post-qualification field')
    _require(overlay.get('launch_class') in CLASSES, 'Exactly one launch class required')
    return {key: overlay.get(key, U) for key in sorted(LINE_FIELDS)} | {'qualification_sha256': _digest(qualification)}


def _utc(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    _require(parsed.tzinfo is not None, 'Slot timestamps require an explicit timezone')
    return parsed.astimezone(timezone.utc)


def slot_week(timestamp):
    day = _utc(timestamp).date()
    return (day - timedelta(days=(day.weekday() + 1) % 7)).isoformat()


def slot_usage(events, week, fmt, complete=False):
    _require(fmt in FORMATS and slot_week(week + 'T00:00:00Z') == week, 'Invalid format or Sunday quota week')
    counts = {'CREATION': 0, 'FIRST_SUBMISSION': 0}
    submitted, created, ids = set(), set(), set()
    for event in sorted(events, key=lambda e: _utc(e['at'])):
        _require(event['id'] not in ids, 'Duplicate slot event ID')
        ids.add(event['id'])
        _require(event['format'] in FORMATS and event['action'] in {'CREATION', 'FIRST_SUBMISSION', 'UPDATE'}, 'Invalid slot event')
        key = (event['title_id'], event['format'])
        action = event['action']
        if action == 'UPDATE':
            _require(key in submitted, 'UPDATE requires a prior submitted title in the same format')
            continue
        seen = submitted if action == 'FIRST_SUBMISSION' else created
        _require(key not in seen, 'A title-format can only be created/first submitted once; later submissions are UPDATE')
        seen.add(key)
        if slot_week(event['at']) == week and event['format'] == fmt:
            counts[action] += 1
    return counts if complete else {k: U for k in counts}


def slot_gate(proposal, usage, week=U):
    _require(proposal.get('format') in FORMATS and proposal.get('launch_class') in CLASSES, 'Format and single launch class required')
    _require(all(v == U or (isinstance(v, int) and not isinstance(v, bool) and v >= 0) for v in usage.values()), 'Quota usage must be reconciled nonnegative counts or UNKNOWN')
    reasons = []
    if proposal['format'] == 'paperback' and proposal.get('only_one_slot') != 'YES':
        reasons.append('ONLY_ONE_SLOT_ANSWER_MUST_BE_YES')
    if proposal['format'] == 'ebook' and proposal.get('requires_paper'):
        reasons.append('ARTIFICIAL_EBOOK_FOR_PAPER_PRODUCT')
    if not proposal.get('ready') or not proposal.get('qualification_verified'):
        reasons.append('READINESS_OR_QUALIFICATION_REVIEW_REQUIRED')
    if proposal['launch_class'] == 'EXPLOIT' and not proposal.get('prior_paid_evidence'):
        reasons.append('PRIOR_PAID_LINE_EVIDENCE_REQUIRED')
    if proposal['launch_class'] == 'SCALE' and not proposal.get('commercial_validation_evidence'):
        reasons.append('COMMERCIAL_LINE_VALIDATION_REQUIRED')
    actions = ['FIRST_SUBMISSION'] + ([] if proposal.get('already_created') else ['CREATION'])
    if any(usage.get(a, U) == U for a in actions):
        reasons.append('QUOTA_USAGE_UNRECONCILED')
    elif any(usage[a] >= 2 for a in actions):
        reasons.append('WEEKLY_FORMAT_QUOTA_EXHAUSTED')
    return {'KDP_SLOT_CLASS': proposal['launch_class'], 'KDP_SLOT_WEEK': week,
            'KDP_SLOT_STATUS': 'BLOCKED' if reasons else 'ELIGIBLE_FOR_OWNER_REVIEW',
            'KDP_SLOT_OPPORTUNITY_COST': proposal.get('slot_opportunity_cost', U),
            'reasons': reasons, 'submission_authorized': False}


def exposure_review(age_days, paid_orders, impressions, clicks, organic_exposure):
    stage = 'PAID_ORDERS' if isinstance(paid_orders, (int, float)) and paid_orders > 0 else U
    if stage == U and paid_orders == 0:
        if impressions == 0:
            stage = 'NO_IMPRESSIONS'
        elif isinstance(impressions, (int, float)) and impressions > 0 and clicks == 0:
            stage = 'NO_CLICKS'
        elif isinstance(clicks, (int, float)) and clicks > 0:
            stage = 'CLICKS_NO_ORDERS'
    recommendation = 'CONTINUE_OBSERVATION'
    if stage == 'PAID_ORDERS':
        recommendation = 'LINE_EXPLOIT_REVIEW_BEFORE_BROAD_DISCOVERY'
    elif age_days == U or paid_orders == U:
        recommendation = 'COLLECT_PAID_ORDER_EVIDENCE'
    elif age_days < 7:
        recommendation = 'ORGANIC_BASELINE'
    elif paid_orders == 0 and organic_exposure in {U, 'WEAK'}:
        recommendation = 'BOUNDED_PAID_EXPOSURE_TEST_FOR_OWNER_APPROVAL'
    return {'stage': stage, 'demand': 'PAID_SIGNAL' if stage == 'PAID_ORDERS' else U,
            'recommendation': recommendation, 'ads_authorized': False,
            'test_shape': {'queries': 'EXACT_OR_TIGHT_HIGH_INTENT', 'fixed_total_budget': 'OWNER_MUST_SET',
                           'measure': ['impressions', 'clicks', 'orders', 'spend']}}


def _latest(state, bid, as_of):
    rows = [a for a in state['actuals'] if a.get('book_id') == bid and
            a.get('schema_version') == 'book-radar-observed-actual/v1' and a['observed_date'] <= as_of]
    return max(rows, key=lambda a: a['observed_date']) if rows else None


def _sum_window(actuals, window, field, expected=None, money=False):
    if not actuals or any(a is None for a in actuals):
        return U
    rows = [a.get('windows', {}).get(window, {}) for a in actuals]
    if any(not isinstance(r.get(field), (int, float)) or isinstance(r.get(field), bool) for r in rows):
        return U
    dates = {(r.get('start'), r.get('end')) for r in rows}
    if len(dates) != 1 or None in next(iter(dates)) or (expected and dates != {expected}):
        return U
    if money and any(r.get('currency') != 'EUR' for r in rows):
        return U
    return round(sum(r[field] for r in rows), 4)


def readthrough(state, first, second, as_of):
    rows = [s for s in state.get('series_observations', []) if s.get('entry_book_id') == first and
            s.get('continuation_book_id') == second and s.get('cohort_basis', U) != U and
            s.get('method') == 'DIRECT_MATCHED_COHORT' and s.get('evidence') and s.get('identity_evidence') and
            s.get('observed_date', '9999') <= as_of and isinstance(s.get('entrants'), (int, float)) and
            s['entrants'] > 0 and isinstance(s.get('continuers'), (int, float)) and 0 <= s['continuers'] <= s['entrants']]
    if not rows:
        return U
    row = max(rows, key=lambda s: s['observed_date'])
    return round(row['continuers'] / row['entrants'], 4)


def line_view(state, line, as_of, events, complete_slots):
    bids = line['book_ids']
    actuals = [_latest(state, bid, as_of) for bid in bids]
    day = date.fromisoformat(as_of)
    window = ((day - timedelta(days=29)).isoformat(), as_of)
    previous = ((day - timedelta(days=59)).isoformat(), (day - timedelta(days=30)).isoformat())
    royalty = _sum_window(actuals, 'recent_money', 'estimated_royalties', window, True)
    live = len(bids) if line.get('live_basis') in {'OWNER_CONFIRMED_LIVE', 'CANONICAL_PUBLISHED_REGISTRY'} else (0 if not bids else U)
    slots = len([e for e in events if e['action'] == 'FIRST_SUBMISSION' and (line['id'] == 'ALL_OBSERVED_BOOKS' or e.get('commercial_line_id') == line['id']) and
                 window[0] <= _utc(e['at']).date().isoformat() <= window[1]]) if complete_slots else U
    previous_actuals = [_latest(state, bid, previous[1]) for bid in bids]
    prev_royalty = _sum_window(previous_actuals, 'recent_money', 'estimated_royalties', previous, True)
    return {'COMMERCIAL_LINE_ID': line['id'], 'book_ids': bids, 'LINE_LIVE_TITLE_COUNT': live,
            'LINE_30D_PAID_UNITS': _sum_window(actuals, 'recent', 'paid_units', window),
            'LINE_30D_ROYALTY': royalty, 'LINE_LIFETIME_PAID_UNITS': _sum_window(actuals, 'lifetime', 'paid_units'),
            'LINE_LIFETIME_ROYALTY': _sum_window(actuals, 'money', 'estimated_royalties', money=True),
            'ROYALTY_PER_LIVE_TITLE': round(royalty / live, 4) if royalty != U and live != U and live > 0 else U,
            'NEW_TITLE_SLOT_COUNT': slots,
            'ROYALTY_PER_NEW_TITLE_SLOT': round(royalty / slots, 4) if royalty != U and slots != U and slots > 0 else U,
            'FOLLOW_ON_TITLE_COUNT': max(live - 1, 0) if live != U else U,
            'BOOK1_TO_BOOK2_READTHROUGH': readthrough(state, bids[0], bids[1], as_of) if len(bids) >= 2 else U,
            'BOOK2_TO_BOOK3_READTHROUGH': readthrough(state, bids[1], bids[2], as_of) if len(bids) >= 3 else U,
            'KENP_PAGES': _sum_window(actuals, 'kenp', 'kenp_pages'),
            'title_outcomes': [{'book_id': bid, 'actual_id': a['id'] if a else U, 'windows': a.get('windows', {}) if a else U} for bid, a in zip(bids, actuals)],
            'outcome_snapshot_dates': [a['observed_date'] if a else U for a in actuals],
            'royalty_statuses': [a.get('windows', {}).get('money', {}).get('status', U) if a else U for a in actuals],
            'kenp_windows': [a.get('windows', {}).get('kenp', {}).get('start', U) + '/' + a.get('windows', {}).get('kenp', {}).get('end', U) if a else U for a in actuals],
            'previous_30d_royalty': prev_royalty, 'currency': 'EUR', 'window': {'start': window[0], 'end': window[1]},
            'paid_signal_next_review': 'LINE_EXPLOIT_REVIEW_BEFORE_BROAD_DISCOVERY' if any(a and isinstance(a.get('windows', {}).get('lifetime', {}).get('paid_units'), (int, float)) and a['windows']['lifetime']['paid_units'] > 0 for a in actuals) else 'OBSERVE',
            'extension_status': line.get('extension_status', 'OWNER_REVIEW')}


def load_model(root: Path):
    from .schema_validation import draft_2020_12_validator
    model = json.loads((root / 'book-radar/revenue-model-v2.json').read_text())
    schema = json.loads((root / 'schemas/book_radar_revenue_model.schema.json').read_text())
    errors = sorted(draft_2020_12_validator(schema).iter_errors(model), key=lambda e: str(e.path))
    _require(not errors, 'Revenue model schema: ' + '; '.join(e.message for e in errors[:3]))
    ids = [line['id'] for line in model['lines']]
    _require(len(set(ids)) == len(ids), 'Duplicate commercial line')
    members = [bid for line in model['lines'] for bid in line['book_ids']]
    _require(len(set(members)) == len(members), 'Book assigned to multiple commercial lines')
    for p in model['release_queue']:
        _require(p['commercial_line_id'] in ids, 'Queue line does not exist')
    for q in model['external_qualifications']:
        _require(q['qualification'] == freeze_qualification(q['card'], q['qualification']['result']), 'External qualification freeze changed')
    for p in model['release_queue']:
        if p['qualification_verified']:
            qualified = next((q for q in model['external_qualifications'] if q['card']['id'] == p['qualification_card_id']), None)
            _require(qualified is not None and qualified['qualification']['result'] == 'QUALIFY', 'Verified release requires a frozen independent QUALIFY')
            _require(any(o['card_id'] == p['qualification_card_id'] and o['fields'].get('launch_class') == p['launch_class'] and o['fields'].get('commercial_line_id') == p['commercial_line_id'] for o in model['post_qualification_overlays']), 'Release classification must follow qualification')
    for overlay in model['post_qualification_overlays']:
        q = next((q for q in model['external_qualifications'] if q['card']['id'] == overlay['card_id']), None)
        _require(q is not None, 'Overlay requires independently qualified external card')
        post_qualification(q['qualification'], q['card'], overlay['fields'])
    for event in model['slot_events']:
        _require(event['commercial_line_id'] in ids, 'Slot event line does not exist')
    # Validate the ledger even before any week has been reconciled.
    slot_usage(model['slot_events'], slot_week(model['effective_date'] + 'T00:00:00Z'), 'paperback')
    for reconciliation in model['slot_reconciliations']:
        slot_usage(model['slot_events'], reconciliation['week'], reconciliation['format'], reconciliation['complete'])
    return model


def revenue_report(root: Path, as_of: str):
    from .book_radar import load_state
    state, model = load_state(root), load_model(root)
    known = {b['id'] for b in state['observed_books']}
    _require(all(b in known for line in model['lines'] for b in line['book_ids']), 'Unknown canonical line member')
    week = slot_week(as_of + 'T00:00:00Z')
    # The default ledger is not retrospectively fabricated from publication dates.
    completeness = model['slot_history_complete_since']
    start = (date.fromisoformat(as_of) - timedelta(days=29)).isoformat()
    complete = completeness != U and completeness <= start
    _require(all(_utc(e['at']).date().isoformat() <= as_of for e in model['slot_events']), 'Future slot events cannot certify observed capacity')
    views = [line_view(state, line, as_of, model['slot_events'], complete) for line in model['lines']]
    all_line = {'id': 'ALL_OBSERVED_BOOKS', 'book_ids': sorted(known)}
    total = line_view(state, all_line, as_of, model['slot_events'], complete)
    royalty, prev = total['LINE_30D_ROYALTY'], total['previous_30d_royalty']
    usage = {}
    for fmt in sorted(FORMATS):
        reconciled = any(r['week'] == week and r['format'] == fmt and r['complete'] for r in model['slot_reconciliations'])
        usage[fmt] = slot_usage(model['slot_events'], week, fmt, reconciled)
    queue = []
    for p in model['release_queue']:
        paid_refs = [bid for bid in p['prior_paid_evidence'] if (a := _latest(state, bid, as_of)) and isinstance(a.get('windows', {}).get('lifetime', {}).get('paid_units'), (int, float)) and a['windows']['lifetime']['paid_units'] > 0]
        checked_proposal = {**p, 'prior_paid_evidence': paid_refs}
        queue.append({**p, **slot_gate(checked_proposal, usage[p['format']], week)})
    paid_known = [v for v in views if isinstance(v['LINE_30D_PAID_UNITS'], (int, float)) and v['LINE_30D_PAID_UNITS'] > 0]
    active = len(paid_known) if all(v['LINE_30D_PAID_UNITS'] != U for v in views if v['book_ids']) else U
    reviews = []
    for book in state['observed_books']:
        a = _latest(state, book['id'], as_of)
        if a:
            instr = a.get('instrumentation', {})
            # Only same-window instrumentation is interpreted; stale observations cannot trigger ads today.
            fresh = a['observed_date'] == as_of
            comparable = a.get('instrumentation_window') == 'recent'
            age = a.get('book_age_days', U) if fresh else U
            paid = a.get('windows', {}).get('recent', {}).get('paid_units', U) if fresh else U
            review = exposure_review(age, paid, instr.get('impressions', U) if comparable else U,
                                     instr.get('clicks', U) if comparable else U, U)
        else:
            review = exposure_review(U, U, U, U, U)
        reviews.append({'book_id': book['id'], 'snapshot_date': a['observed_date'] if a else U, **review})
    mapped = {b for line in model['lines'] for b in line['book_ids']}
    return {'report': 'growth', 'as_of': as_of, 'owner_decision': model.get('owner_decision', U), 'target_monthly_royalty_eur': 1000, 'target_is_forecast': False,
            'ROLLING_30D_ROYALTY': royalty, 'ROLLING_30D_PAID_UNITS': total['LINE_30D_PAID_UNITS'],
            'ACTIVE_COMMERCIAL_LINES': active, 'known_active_lines_lower_bound': len(paid_known),
            'ROYALTY_BY_LINE': {v['COMMERCIAL_LINE_ID']: v['LINE_30D_ROYALTY'] for v in views},
            'ROYALTY_PER_NEW_KDP_SLOT': total['ROYALTY_PER_NEW_TITLE_SLOT'],
            'MONTH_OVER_MONTH_ROYALTY_CHANGE': round(royalty - prev, 4) if royalty != U and prev != U else U,
            'month_comparison_basis': 'CURRENT_30D_VS_PREVIOUS_NONOVERLAPPING_30D_EUR_DELTA',
            'unassigned_book_ids': sorted(known - mapped), 'lines': views, 'slots': usage,
            'release_queue': queue, 'exposure_reviews': reviews,
            'audience_infrastructure': 'RECOMMEND_ONLY_AFTER_MEANINGFUL_PAID_SIGNAL_OWNER_REVIEW',
            'submission_authorized': False, 'ads_authorized': False}
