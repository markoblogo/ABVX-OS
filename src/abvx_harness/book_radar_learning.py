"""Offline, append-only MMR research learning. Never produces or publishes products."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from functools import lru_cache
from urllib.parse import urlsplit

from . import book_radar_markets as markets
from . import book_radar_outcomes as outcomes
from .process_learning import _write_once, digest
from .schema_validation import load_draft_2020_12_validator

VERSION = 'multi-market-learning/v1'
METHOD = 'typed-source-retrospective/v1'
REPO = Path(__file__).resolve().parents[2]
DEFAULT_HISTORY = REPO / '.tmp/multi-market-radar/learning'
PROPOSAL = 'matched-product-t7-v1'
FACETS = {'buyer', 'paid_demand', 'advantage', 'channel', 'economics'}
METHOD_PROTOCOL = 'discovery-method-comparison/v1'


def read(path):
    return markets.read(Path(path))


def now():
    return datetime.now(timezone.utc).isoformat()


@lru_cache(maxsize=1)
def validator():
    return load_draft_2020_12_validator(REPO / 'schemas/book_radar_learning.schema.json')


def validate(record):
    validator().validate(record)
    expected = digest({k: v for k, v in record.items() if k not in {'recorded_at', 'record_digest'}})
    if record['record_digest'] != expected:
        raise ValueError('Learning record integrity mismatch')
    return record


def write(history, group, key, body):
    """Immutable identity; timestamps are metadata, not a new result on retry."""
    record = dict(schema_version=VERSION, **body)
    record['record_digest'] = digest(record)
    path = Path(history) / group / (key + '.json')
    if path.exists():
        previous = read(path)
        if {k: v for k, v in previous.items() if k != 'recorded_at'} != record:
            raise ValueError('Frozen learning identity changed: ' + str(path))
        validate(previous)
        return previous
    record['recorded_at'] = now()
    validate(record)
    _write_once(path, record)
    return record


def records(history, group):
    result = []
    for path in sorted((Path(history) / group).glob('*.json')):
        result.append(validate(read(path)))
    return result


def text_once(path, payload):
    """Atomic derivative installation; an interrupted write never freezes half a report."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.learning-')
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_text() != payload:
                raise ValueError('Frozen report text changed')
    finally:
        Path(temporary).unlink(missing_ok=True)


def retain(history, path):
    raw = Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    _write_once(Path(history) / 'proofs' / (sha + '.json'),
                {'sha256': sha, 'base64': base64.b64encode(raw).decode('ascii')})
    return sha


def proof(history, sha):
    if not re.fullmatch('[a-f0-9]{64}', sha):
        raise ValueError('Invalid proof hash')
    envelope = read(Path(history) / 'proofs' / (sha + '.json'))
    raw = base64.b64decode(envelope['base64'], validate=True)
    if envelope['sha256'] != sha or hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError('Learning proof hash mismatch')
    return raw


def hypothesis_key(candidate):
    return '|'.join(str(candidate[k]) for k in ('id', 'language', 'geography'))


def observation_key(row):
    # IDs, paths and prose annotations are ingestion metadata. Typed facts and
    # retained source identity define an observation, even in a processing replay.
    return digest({k: row.get(k) for k in ('marketplace', 'source_url', 'upstream_url',
        'language', 'geography', 'observed_at', 'period_start', 'period_end',
        'availability', 'source_kind', 'evidence_sha256')} | {
        'metrics': {k: {n: v.get(n) for n in ('status', 'value', 'unit')}
                    for k, v in row['metrics'].items()}})


def product_key(row):
    """Only direct product pages; shelves and searches cannot form trajectories."""
    url = urlsplit(row['source_url'])
    domain, path = (url.hostname or '').lower().removeprefix('www.'), url.path
    expressions = {'amazon': r'/dp/([A-Z0-9]{10})(?:/|$)',
                   'etsy': r'/listing/(\d+)(?:/|$)',
                   'udemy': r'/course/([^/]+)(?:/|$)',
                   'kickstarter': r'/projects/([^/]+/[^/]+)(?:/|$)'}
    match = re.search(expressions[row['marketplace']], path)
    if not match:
        return None
    # Udemy is intrinsically a course. Other markets need an explicit sampled
    # format; do not infer paperback or SKU format from the proposed product.
    family = 'course' if row['marketplace'] == 'udemy' else row['format'].casefold()
    return (row['marketplace'], domain, match[1], row['language'], row['geography'], family)


def typed_signals(history, row):
    result = copy.deepcopy(row['metrics'])
    try:
        facts = json.loads(proof(history, row['evidence_sha256'])).get('facts', {})
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        facts = {}
    # Retain cumulative fields as separate, explicitly non-paid observations.
    for key in ('students_cumulative', 'ratings_cumulative', 'item_reviews', 'item_rating', 'shop_reported_sales'):
        if key in facts:
            result['source:' + key] = {'status': 'OBSERVED_SOURCE_FACT', 'value': facts[key],
                                     'unit': 'cumulative_proxy', 'note': 'NOT_CONFIRMED_PAID_ORDERS'}
    return result


def learn_run(run, history=DEFAULT_HISTORY):
    run, history = Path(run).resolve(), Path(history)
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', run.name):
        raise ValueError('Unsafe research run ID')
    if read(run / 'execution.json').get('execution') != 'COMPLETE':
        raise ValueError('Learning requires a completed research execution')
    if (run / 'input.json').exists():
        packet, base = markets.check(run / 'input.json'), run
    else:
        # First activation retained a validated provider state, not input.json.
        packet = markets.load(run / 'radar-root')
        base = run / 'radar-root/book-radar/multi-market'
    ranking = read(run / 'ranking.json') if (run / 'ranking.json').exists() else None
    stage = 'REVIEWED' if ranking is not None else 'ACQUIRED'
    research_digest = digest(packet)
    proposed = {'kind': 'snapshot', 'run_id': run.name, 'stage': stage,
                'method_version': METHOD, 'research_digest': research_digest,
                'source_run': str(run), 'opportunities': packet['opportunities'],
                'observations': packet['observations'], 'original_ranking': ranking,
                'commercial_review': read(run / 'commercial-review.json') if (run / 'commercial-review.json').exists() else None}
    # Validate all source bytes before committing a snapshot; no network IO.
    for row in packet['observations']:
        source = markets.proof_path(base, row)
        retain(history, source)
    # A reviewed stage may add assessment, never rewrite the acquired packet.
    for old in records(history, 'snapshots'):
        if old['run_id'] == run.name and old['research_digest'] != research_digest:
            raise ValueError('Original research changed under a frozen run ID')
    snapshot = write(history, 'snapshots', run.name + '--' + stage, proposed)
    proposal(history)
    report = retrospective(history)
    return {'snapshot': snapshot, 'report': report,
            'report_path': str(history / 'reports' / (report['state_digest'] + '.md'))}


def proposal(history):
    return write(history, 'proposals', PROPOSAL, {
        'kind': 'proposal', 'id': PROPOSAL, 'change_class': 'RESEARCH_METHOD',
        'limitation': 'Cumulative proxy counts and a one-day panel cannot establish entrant paid demand or trends.',
        'hypothesis': 'A matched T7 direct-product panel resolves more decision evidence gaps per research minute than adding niches.',
        'expected_benefit': 'More comparable follow-ups; commercial accuracy gain remains UNKNOWN.',
        'cost': {'research_minutes_cap': 20, 'candidates': 3, 'products_per_candidate': 2, 'paid_services': False},
        'validation_plan': {'dataset': 'Same six direct products at baseline and T7; same currency/format/context.',
            'measurements': ['matched_followups/6', 'newly_resolved_evidence_questions', 'research_minutes', 'proxy_to_paid_substitutions'],
            'pass_rule': 'At least 4/6 comparable follow-ups, >=1 predeclared question resolved, <=20 minutes, zero proxy substitutions; this validates research coverage only.',
            'historical_test': 'Replay retained history for duplicate exclusion and matching; no backdated commercial forecasts.'},
        'risks': ['Selection bias in six products', 'Public pages may still hide paid orders', 'Discount/geo changes may break comparability'],
        'automatic_adoption': False})


def add_event(history, event, evidence_base):
    """Record a preregistered experiment and its results, never execute adoption."""
    event = copy.deepcopy(event)
    if event.get('proposal_id') != PROPOSAL:
        raise ValueError('Unknown proposal')
    prior = [e for e in records(history, 'events') if e.get('proposal_id') == PROPOSAL]
    status = event.get('status')
    if status not in {'VALIDATION_REGISTERED', 'VALIDATED', 'INSUFFICIENT_DATA', 'REJECTED', 'ADOPTED'}:
        raise ValueError('Unknown learning status')
    for ref in event.get('evidence', []):
        retain(history, markets.proof_path(Path(evidence_base), {'evidence_path': ref['path'], 'evidence_sha256': ref['sha256']}))
    if status == 'VALIDATION_REGISTERED':
        if not event.get('plan') or not event.get('experiment_id'):
            raise ValueError('Preregister a plan and experiment ID')
    else:
        if not any(x['status'] == 'VALIDATION_REGISTERED' and x.get('experiment_id') == event.get('experiment_id') for x in prior):
            raise ValueError('Register validation before reporting a result')
        if not event.get('measurements') or not event.get('evidence'):
            raise ValueError('Validation needs measurements and retained proof')
        if status in {'VALIDATED', 'ADOPTED'} and event.get('dataset_kind') != 'REAL_HISTORY':
            raise ValueError('Synthetic tests cannot validate a commercial research method')
        if status == 'VALIDATED':
            m = event['measurements']
            fields = {'panel_size', 'matched_followups', 'questions_resolved', 'research_minutes',
                      'proxy_to_paid_substitutions', 'minimum_followup_days'}
            if not fields <= m.keys() or any(isinstance(m[k], bool) or not isinstance(m[k], (int, float)) or m[k] < 0 for k in fields):
                raise ValueError('Supply all preregistered numeric T7 measurements')
            if not (m['panel_size'] == 6 and 4 <= m['matched_followups'] <= 6 and m['questions_resolved'] >= 1 and
                    m['research_minutes'] <= 20 and m['proxy_to_paid_substitutions'] == 0 and m['minimum_followup_days'] >= 7):
                raise ValueError('T7 coverage experiment did not meet its pass rule')
        if status == 'ADOPTED':
            valid = [x for x in prior if x['status'] == 'VALIDATED' and x.get('experiment_id') == event.get('experiment_id')]
            approval = event.get('owner_approval')
            if not valid or not approval:
                raise ValueError('Adoption requires validated evidence and explicit owner approval evidence')
            retain(history, markets.proof_path(Path(evidence_base), {'evidence_path': approval['path'], 'evidence_sha256': approval['sha256']}))
    event['kind'] = 'event'
    event['automatic_action'] = False
    return write(history, 'events', digest(event), event)


def _method_records(history):
    return [e for e in records(history, 'events') if e.get('proposal_id') == METHOD_PROTOCOL]


def _method_time(value):
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('UTC-aware timestamp required')
    return stamp


def _method_refs(history, value, base=None):
    if isinstance(value, dict):
        if 'sha256' in value and 'path' in value:
            if base is None:
                proof(history, value['sha256'])
            else:
                retain(history, markets.proof_path(Path(base),
                       {'evidence_path': value['path'], 'evidence_sha256': value['sha256']}))
        for v in value.values():
            _method_refs(history, v, base)
    elif isinstance(value, list):
        for v in value:
            _method_refs(history, v, base)


def method_event(history, payload, evidence_base):
    """Prospective method records in the existing journal. Never execute a trial.

    Stable action identities prevent forecast mutation and duplicate attribution.
    Local chronology is enforced; hashes establish provenance, not source truth.
    """
    data = copy.deepcopy(payload)
    action, block = data['action'], data['id']
    actions = {'REGISTER_PROTOCOL', 'START_ARM', 'FREEZE_HYPOTHESIS', 'LINK_DISCOVERY',
               'CLOSE_ARM', 'START_REVIEW', 'CLOSE_REVIEW', 'REGISTER_TRIAL', 'BIND_OUTCOME'}
    if action not in actions or not isinstance(block, str) or not block.strip():
        raise ValueError('Unknown method action or block')
    extra = {a: ('method_id',) for a in ('START_ARM', 'CLOSE_ARM')}
    extra.update(FREEZE_HYPOTHESIS=('hypothesis_id',), LINK_DISCOVERY=('hypothesis_id', 'method_id'),
                 REGISTER_TRIAL=('trial_id',), BIND_OUTCOME=('trial_id', 'actual_id'))
    identity = [action, block] + [data[k] for k in extra.get(action, ())]
    key = 'method--' + digest(identity)
    existing = Path(history) / 'events' / (key + '.json')
    if existing.exists():
        old = validate(read(existing))
        if old['data'] != data:
            raise ValueError('Frozen method identity changed')
        _method_refs(history, old)
        return old
    prior = _method_records(history)
    local = [e for e in prior if e['experiment_id'] == block]
    def find(kind, **fields):
        return [e for e in local if e['data']['action'] == kind and
                all(e['data'].get(k) == v for k, v in fields.items())]
    measured = {}
    if action == 'REGISTER_PROTOCOL':
        profiles = data['profiles']
        if len(profiles) < 2 or len({p['id'] for p in profiles}) != len(profiles):
            raise ValueError('At least two distinct versioned profiles required')
        for p in profiles:
            if not re.fullmatch(r'[A-Za-z0-9_-]+/v[1-9][0-9]*', p['id']) or not p['birth'] or not p['stop']:
                raise ValueError('Each method needs version, birth and stop predicates')
            for old in prior:
                if old['data']['action'] == 'REGISTER_PROTOCOL':
                    for old_p in old['data']['profiles']:
                        if old_p['id'] == p['id'] and old_p != p:
                            raise ValueError('Changed method definition requires a new version')
        if data['cohort']['market'] not in markets.MARKETS or not all(data['cohort'].get(k) for k in ('geography', 'language', 'format')):
            raise ValueError('Explicit market/geography/language/format required')
        for k in ('qualifier', 'context', 'method_forecast'):
            if not data.get(k):
                raise ValueError('Missing preregistration field: ' + k)
        forecasts = data['method_forecast']
        if not isinstance(forecasts, dict) or set(forecasts) != {p['id'] for p in profiles}:
            raise ValueError('Every selected method needs its own preregistered forecast')
        for forecast in forecasts.values():
            if not isinstance(forecast, dict) or not all(forecast.get(k) for k in
                    ('hypothesis', 'commercial_effect', 'range', 'confidence')):
                raise ValueError('Method forecast needs hypothesis, effect, range and confidence; UNKNOWN is allowed')
        for k in ('arm_seconds', 'review_seconds', 'cards_per_arm'):
            n = data['budget'][k]
            if isinstance(n, bool) or not isinstance(n, (float, int)) or not 0 < n < float('inf'):
                raise ValueError('Finite positive budget required')
        if data['context'].get('portfolio_seeds') is not False:
            raise ValueError('Independent discovery excludes portfolio seeds')
    else:
        registered = find('REGISTER_PROTOCOL')
        if len(registered) != 1:
            raise ValueError('Register method protocol first')
        protocol = registered[0]['data']
        method = data.get('method_id')
        if method is not None and method not in {p['id'] for p in protocol['profiles']}:
            raise ValueError('Method not in frozen protocol')
        if action == 'START_ARM':
            if find('START_REVIEW') or any(not find('CLOSE_ARM', method_id=e['data']['method_id']) for e in find('START_ARM')):
                raise ValueError('Arms must run sequentially before review')
        if action in {'FREEZE_HYPOTHESIS', 'LINK_DISCOVERY', 'CLOSE_ARM'}:
            start = find('START_ARM', method_id=method)
            if not start or find('CLOSE_ARM', method_id=method) or find('START_REVIEW'):
                raise ValueError('Requires an open research arm before comparison')
            seconds = (_method_time(now()) - _method_time(start[0]['recorded_at'])).total_seconds()
            if seconds < 0:
                raise ValueError('Clock moved backwards')
            measured = {'elapsed_seconds': seconds, 'budget_seconds': protocol['budget']['arm_seconds'],
                        'budget_status': 'WITHIN_CAP' if seconds <= protocol['budget']['arm_seconds'] else 'OVERRUN'}
            if action != 'CLOSE_ARM' and seconds > protocol['budget']['arm_seconds']:
                raise ValueError('Research cap exceeded; close arm with failure retained')
        if action == 'FREEZE_HYPOTHESIS':
            count = len(find('FREEZE_HYPOTHESIS', method_id=method)) + len(find('LINK_DISCOVERY', method_id=method))
            if count >= protocol['budget']['cards_per_arm']:
                raise ValueError('Frozen card cap exceeded')
            for k in ('hypothesis_id', 'niche_id', 'buyer', 'unmet_need_or_motive', 'alternatives',
                      'supply_gap_cause', 'encounter_route', 'product', 'confidence', 'next_falsification', 'cost_estimate'):
                if not data.get(k):
                    raise ValueError('Missing hypothesis field: ' + k)
            for k in ('birth_assessment', 'preliminary_demand'):
                if data[k] not in {'SUPPORTED', 'INSUFFICIENT_EVIDENCE', 'REFUTED'}:
                    raise ValueError('Unknown evidence assessment')
            if (data['birth_assessment'] == 'SUPPORTED' or data['preliminary_demand'] == 'SUPPORTED') and not data.get('evidence'):
                raise ValueError('Positive gate needs source evidence')
            f = data['forecast']
            if f['anchor'] != 'PUBLICATION_DATE' or not f['rationale'] or not f['basis'] or not f['metric']:
                raise ValueError('Explicit frozen forecast contract required')
            if not isinstance(f['horizon_days'], int) or isinstance(f['horizon_days'], bool) or f['horizon_days'] <= 0:
                raise ValueError('Positive forecast horizon required')
            r = f['range']
            if r != 'UNKNOWN' and (not isinstance(r, list) or len(r) != 2 or
                    any(isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v < float('inf') for v in r) or r[0] > r[1]):
                raise ValueError('Forecast range must be finite or UNKNOWN')
            # Same niche may have multiple hypotheses; trial count remains niche-wide.
            measured['first_seen'] = now()
        if action == 'LINK_DISCOVERY':
            h = find('FREEZE_HYPOTHESIS', hypothesis_id=data['hypothesis_id'])
            if len(h) != 1 or method == h[0]['data']['method_id']:
                raise ValueError('Link an existing hypothesis to a different method')
            if data['role'] not in {'INDEPENDENT_REDISCOVERY', 'CORROBORATION'} or not data.get('evidence'):
                raise ValueError('Explicit discovery role and evidence required')
            if len(find('FREEZE_HYPOTHESIS', method_id=method)) + len(find('LINK_DISCOVERY', method_id=method)) >= protocol['budget']['cards_per_arm']:
                raise ValueError('Card cap includes shared discoveries')
            measured['first_seen'] = now()
        if action == 'CLOSE_ARM' and (not data.get('trace') or 'limitations' not in data):
            raise ValueError('Retain failed searches, trace and limitations')
        if action == 'START_REVIEW' and len(find('CLOSE_ARM')) != len(protocol['profiles']):
            raise ValueError('Freeze every arm before review')
        if action == 'CLOSE_REVIEW':
            starts = find('START_REVIEW')
            if not starts or not data.get('findings') or not data.get('evidence'):
                raise ValueError('Review needs frozen arms, findings and evidence')
            seconds = (_method_time(now()) - _method_time(starts[0]['recorded_at'])).total_seconds()
            if seconds < 0:
                raise ValueError('Clock moved backwards')
            measured = {'elapsed_seconds': seconds, 'budget_seconds': protocol['budget']['review_seconds'],
                        'budget_status': 'WITHIN_CAP' if seconds <= protocol['budget']['review_seconds'] else 'OVERRUN'}
        if action == 'REGISTER_TRIAL':
            hs = find('FREEZE_HYPOTHESIS', hypothesis_id=data['hypothesis_id'])
            if len(hs) != 1 or not find('CLOSE_REVIEW'):
                raise ValueError('Trial needs a frozen hypothesis and closed review')
            h = hs[0]['data']
            if data['niche_id'] != h['niche_id']:
                raise ValueError('Trial cannot rename niche to reset its budget')
            trials = [e['data'] for e in prior if e['data']['action'] == 'REGISTER_TRIAL']
            if len([t for t in trials if t['niche_id'] == data['niche_id']]) >= 3:
                raise ValueError('Maximum three initial products per niche, not a quota')
            if any(t['product_family_id'] == data['product_family_id'] or t['book_id'] == data['book_id'] for t in trials):
                raise ValueError('Formats/revisions share a product family; no new independent trial')
            if not data.get('owner_approval') or not data.get('trial_plan') or not data.get('identity_evidence'):
                raise ValueError('Owner-approved bounded plan and product identity evidence required')
            if not all(data['trial_plan'].get(k) for k in ('total_loss_cap', 'rights_quality', 'route', 'checkpoints')):
                raise ValueError('Bounded trial requires loss, rights/quality, route and checkpoints')
            launch = _method_time(data['planned_publication_at'])
            if launch <= _method_time(now()):
                raise ValueError('Register future trial before publication/outcomes; no historical credit')
            for k in ('production_minutes', 'maintenance_minutes', 'owner_minutes', 'rework_minutes', 'cash_cost'):
                if k not in data['costs']:
                    raise ValueError('Track full costs; use UNKNOWN when unmeasured')
                n = data['costs'][k]
                if n != 'UNKNOWN' and (isinstance(n, bool) or not isinstance(n, (int, float)) or not 0 <= n < float('inf')):
                    raise ValueError('Costs must be finite nonnegative or UNKNOWN')
        if action == 'BIND_OUTCOME':
            ts = find('REGISTER_TRIAL', trial_id=data['trial_id'])
            if len(ts) != 1 or protocol['cohort']['market'] != 'amazon':
                raise ValueError('Only existing KDP adapter available; other markets need a reviewed real export adapter')
            t = ts[0]['data']
            actual, book = data['actual'], data['book']
            outcomes.validate_record(actual, 'actuals')
            outcomes.validate_record(book, 'observed_books')
            if (actual['id'] != data['actual_id'] or actual['book_id'] != t['book_id'] or
                    book['id'] != t['book_id'] or actual['product_id'] != t['product_family_id'] or
                    book['product_id'] != t['product_family_id']):
                raise ValueError('Exact actual/book/product binding required')
            if book['publication_date'] == 'UNKNOWN' or book['publication_date'] < t['planned_publication_at'][:10] or not book['date_evidence']:
                raise ValueError('Verify publication after prospective registration')
            if actual['observed_date'] < book['publication_date']:
                raise ValueError('Outcome predates launch')
            if actual['observed_date'] > _method_time(now()).date().isoformat():
                raise ValueError('Future observations cannot be results')
            if actual['book_age_days'] != (date.fromisoformat(actual['observed_date']) - date.fromisoformat(book['publication_date'])).days:
                raise ValueError('Observed age must match verified publication date')
            if any(e['data']['action'] == 'BIND_OUTCOME' and e['data']['actual_id'] == data['actual_id'] for e in prior):
                raise ValueError('Outcome already attributed; shared methods use one trial')
            if data.get('organic_attribution') not in {'OBSERVED', 'OWNER_REPORTED_NO_PAID_PROMOTION', 'UNKNOWN'}:
                raise ValueError('Organic attribution must be explicit')
            if data['organic_attribution'] != 'UNKNOWN' and not data.get('attribution_evidence'):
                raise ValueError('Attribution needs proof; no ads alone is not organic proof')
    _method_refs(history, data, evidence_base)
    body = {'kind': 'event', 'proposal_id': METHOD_PROTOCOL, 'experiment_id': block,
            'validation_scope': 'PRODUCT_OUTCOME' if action in {'REGISTER_TRIAL', 'BIND_OUTCOME'} else 'METHOD_COMPARISON',
            'status': 'VALIDATION_REGISTERED' if action in {'REGISTER_PROTOCOL', 'FREEZE_HYPOTHESIS', 'REGISTER_TRIAL'} else 'INSUFFICIENT_DATA',
            'automatic_action': False, 'production_authorized': False, 'data': data, 'measurements': measured}
    return write(history, 'events', key, body)


def method_comparison(history):
    """Descriptive cohorts, never an automatic winner or adoption decision."""
    events = _method_records(history)
    _method_refs(history, events)
    rows, trials_summary = [], []
    for p in [e for e in events if e['data']['action'] == 'REGISTER_PROTOCOL']:
        block, protocol = p['experiment_id'], p['data']
        local = [e for e in events if e['experiment_id'] == block]
        def actions(kind):
            return [e for e in local if e['data']['action'] == kind]
        hypotheses = {e['data']['hypothesis_id']: e for e in actions('FREEZE_HYPOTHESIS')}
        memberships = {hid: {h['data']['method_id']} for hid, h in hypotheses.items()}
        for e in actions('LINK_DISCOVERY'):
            if e['data']['role'] == 'INDEPENDENT_REDISCOVERY':
                memberships[e['data']['hypothesis_id']].add(e['data']['method_id'])
        trials = actions('REGISTER_TRIAL')
        bound = actions('BIND_OUTCOME')
        for t in trials:
            d = t['data']; h = hypotheses[d['hypothesis_id']]['data']
            observed = [e for e in bound if e['data']['trial_id'] == d['trial_id']]
            results = []
            for e in observed:
                a, b = e['data']['actual'], e['data']['book']
                f = h['forecast']
                scope_ok = (a['marketplace_scope'] == 'AMAZON_COM' and protocol['cohort']['geography'] == 'US' and
                            protocol['cohort']['format'] == 'paperback' and
                            len(b['formats']) == 1 and b['formats'][0]['format'] == 'paperback' and b['formats'][0]['evidence'] and
                            a['windows']['lifetime']['ebook_paid'] == 0)
                claim = dict(f, id=h['hypothesis_id'], evidence=h.get('evidence', []), source_kind='PREPUBLICATION')
                calibrated = outcomes.calibrate(claim, a, b)
                status = 'NOT_FORECASTABLE' if f['range'] == 'UNKNOWN' else calibrated['status'] if scope_ok else 'INCOMPARABLE'
                results.append({'actual_id': a['id'], 'scope_comparable': scope_ok,
                    'forecast_status': status, 'calibration': calibrated if scope_ok else 'INCOMPARABLE',
                    'paid_units': a['windows']['lifetime']['paid_units'],
                    'window': a['windows']['lifetime'], 'income': a['windows']['money'],
                    'funnel_diagnosis': outcomes.classify(a), 'costs': a['economics'],
                    'organic_attribution': e['data']['organic_attribution']})
            trials_summary.append({'protocol_id': block, 'trial_id': d['trial_id'], 'hypothesis_id': d['hypothesis_id'],
                'niche_id': d['niche_id'], 'joint_methods': sorted(memberships[d['hypothesis_id']]),
                'results': results, 'trial_costs': d['costs'], 'repeated_niche_response': 'NOT_ADJUDICATED'})
        for profile in protocol['profiles']:
            mid = profile['id']; selected = [h['data'] for hid, h in hypotheses.items() if mid in memberships[hid]]
            selected_ids = {h['hypothesis_id'] for h in selected}
            ts = [t for t in trials_summary if t['protocol_id'] == block and mid in t['joint_methods']]
            statuses = {}
            for h in selected:
                candidates = [r for t in ts if t['hypothesis_id'] == h['hypothesis_id'] for r in t['results']]
                status = 'NOT_FORECASTABLE' if h['forecast']['range'] == 'UNKNOWN' else 'PENDING'
                if candidates:
                    # Show all outcomes separately below; no aggregate error across mismatched windows.
                    status = candidates[-1]['forecast_status'] if len(candidates) == 1 else 'MULTIPLE_WINDOWS_REVIEW_REQUIRED'
                statuses[status] = statuses.get(status, 0) + 1
            closed = [e for e in actions('CLOSE_ARM') if e['data']['method_id'] == mid]
            rows.append({'protocol_id': block, 'method_id': mid, 'cohort': protocol['cohort'],
                'hypotheses': len(selected), 'hypothesis_ids': sorted(selected_ids),
                'shared_hypotheses': sum(len(memberships[h]) > 1 for h in selected_ids),
                'preliminary_demand_supported': sum(h['preliminary_demand'] == 'SUPPORTED' for h in selected),
                'registered_trials': len(ts),
                'observed_launches': sum(bool(t['results']) for t in ts),
                'products_with_paid_response': sum(any(r['scope_comparable'] and isinstance(r['paid_units'], (int, float)) and r['paid_units'] > 0 for r in t['results']) for t in ts),
                'repeated_niche_response': 'NOT_ADJUDICATED', 'income': 'SEE_TYPED_TRIAL_WINDOWS_NO_AGGREGATION',
                'forecast_results': statuses, 'research_time': closed[0]['measurements'] if closed else 'PENDING',
                'owner_minutes': 'UNKNOWN', 'return_per_hour': 'UNKNOWN', 'commercial_result': 'UNPROVEN'})
    return {'protocol_version': METHOD_PROTOCOL, 'events': len(events), 'methods': rows, 'trials': trials_summary,
            'unique_trial_count': len(trials_summary), 'winner': 'NOT_ADJUDICATED',
            'attribution': 'Shared discoveries are memberships, never additive independent successes',
            'limitations': ['Source hashes are provenance, not verification of paid orders',
                'No historical attribution backfill; no automatic winner, score change, production or budget allocation',
                'No sales without measured exposure cannot establish no demand; incomplete costs preclude return/hour',
                'Commercial comparison requires matched market, format, horizon, mature windows and reviewed interpretation'],
            'production_authorized': False}


def bind_outcomes(history, links_path, actuals_path, evidence_base):
    """Explicitly attach delayed own results without touching canonical outcomes."""
    keys = {hypothesis_key(o) for s in records(history, 'snapshots') for o in s['opportunities']}
    actuals = read(actuals_path)['actuals']
    added = []
    for link in read(links_path)['links']:
        found = [a for a in actuals if a['id'] == link['actual_id']]
        if link['hypothesis_key'] not in keys or len(found) != 1:
            raise ValueError('Unknown hypothesis or nonunique actual ID')
        actual = found[0]
        if actual.get('schema_version') != 'book-radar-observed-actual/v1' or actual['book_id'] != link['book_id']:
            raise ValueError('Require a versioned actual and exact book identity')
        outcomes.validate_record(actual, 'actuals')
        def retain_refs(value):
            if isinstance(value, dict):
                if 'path' in value and 'sha256' in value:
                    retain(history, markets.proof_path(Path(evidence_base), {'evidence_path': value['path'], 'evidence_sha256': value['sha256']}))
                for child in value.values():
                    retain_refs(child)
            elif isinstance(value, list):
                for child in value:
                    retain_refs(child)
        retain_refs(actual)
        body = {'kind': 'outcome', 'binding': link, 'actual': actual,
                'attribution': 'EXPLICIT_OWNER_BINDING', 'commercial_success': 'UNPROVEN'}
        added.append(write(history, 'outcomes', digest(body), body))
    return added


def decision(snapshot, candidate, rows):
    original = next((x for x in (snapshot['original_ranking'] or {}).get('opportunities', []) if x.get('id') == candidate['id']), None)
    relevant = [r for r in rows if r['availability'] == 'AVAILABLE' and
                any(s['status'] != 'MISSING' for s in r['metrics'].values())]
    status, reason = 'HOLD', 'No usable source evidence or concrete buyer/job.'
    question = 'Confirm a specific buyer and job, then acquire direct product evidence.'
    concrete_job = all(str(candidate.get(k, '')).strip().upper() not in {'', 'UNKNOWN', 'MISSING', 'NOT_AVAILABLE'}
                       for k in ('audience', 'motivation'))
    if relevant and concrete_job:
        status, reason = 'VALIDATE', f"{candidate['audience']}: {candidate['motivation']}. Observed offer/activity; commercial viability remains unproven."
        question = (original or {}).get('next_commercial_validation') or 'Obtain format-matched product paid units in a dated window and test buyer willingness to pay; price/reviews/students are insufficient.'
    review = snapshot.get('commercial_review') or {}
    item = review.get('candidates', {}).get(candidate['id'], {})
    if relevant and concrete_job and review.get('research_digest') == snapshot['research_digest'] and set(item.get('facets', {})) == FACETS:
        refs = item['facets']
        available_hashes = {r['evidence_sha256'] for r in relevant}
        facets_ok = all(v.get('conclusion') == 'SUPPORTED' and v.get('proof_sha256') in available_hashes and v.get('reason') for v in refs.values())
        state = {'opportunities': snapshot['opportunities'], 'observations': snapshot['observations']}
        for row in relevant:
            paid = row['metrics'].get('paid_orders', row['metrics'].get('paid_enrollments', {}))
            if facets_ok and product_key(row) and row.get('period_start') and row.get('period_end') and paid.get('status') == 'VERIFIED' and isinstance(paid.get('value'), (int, float)) and paid['value'] > 0:
                assessment = markets.assess_market(state, candidate, row['marketplace'], row['observed_at'])
                if assessment['eligible']:
                    status, reason, question = 'GO', 'Source-bound commercial review and existing eligibility gates passed; owner decision required.', 'Owner reviews evidence and decides whether to lift production HOLD.'
    return {'id': candidate['id'], 'hypothesis_key': hypothesis_key(candidate), 'status': status,
            'reason': reason, 'next_validation': question, 'production_authorized': False,
            'decision_change_rule': 'GO review requires dated product paid demand plus supported buyer, advantage, acquisition, economics and existing eligibility; owner still decides.',
            'last_observation': max((r['observed_at'] for r in rows), default='UNKNOWN'),
            'original_assessment': original}


def retrospective(history):
    implementation = {name: retain(history, REPO / name) for name in (
        'src/abvx_harness/book_radar_learning.py', 'schemas/book_radar_learning.schema.json',
        'src/abvx_harness/book_radar_markets.py', 'src/abvx_harness/book_radar_outcomes.py',
        'src/abvx_harness/process_learning.py', 'src/abvx_harness/schema_validation.py')}
    snapshots = records(history, 'snapshots')
    latest = {}
    for s in snapshots:
        if s['run_id'] not in latest or s['stage'] == 'REVIEWED':
            latest[s['run_id']] = s
    observations, total = {}, 0
    hypotheses = {}
    for s in sorted(latest.values(), key=lambda x: (min((r['observed_at'] for r in x['observations']), default=''), x['run_id'])):
        for row in s['observations']:
            total += 1
            key = observation_key(row)
            observations.setdefault(key, row)
            proof(history, row['evidence_sha256'])
        for o in s['opportunities']:
            hypotheses.setdefault(hypothesis_key(o), []).append((s, o))
    changes, panel = [], {}
    for row in observations.values():
        product = product_key(row)
        if product is None or row['availability'] != 'AVAILABLE':
            continue
        for metric, signal in typed_signals(history, row).items():
            if signal['status'] not in {'VERIFIED', 'OBSERVED_SOURCE_FACT'} or isinstance(signal['value'], bool) or not isinstance(signal['value'], (int, float)):
                continue
            if metric == 'price' and row['geography'].upper() in {'UNKNOWN', 'MISSING', ''}:
                continue  # Unknown delivery/pricing context is not a matched price trajectory.
            period = (row.get('period_start'), row.get('period_end'))
            key = (*product, metric, signal.get('unit'), *period)
            panel.setdefault(key, []).append((row, signal))
    for key, series in panel.items():
        dates = sorted({r['observed_at'] for r, _ in series})
        if len(dates) < 2:
            continue
        old = [(r, s) for r, s in series if r['observed_at'] == dates[0]]
        new = [(r, s) for r, s in series if r['observed_at'] == dates[-1]]
        # Same-day conflicting measurements need a reviewer; never pick one.
        if len({digest(s) for _, s in old}) != 1 or len({digest(s) for _, s in new}) != 1:
            continue
        a, b = old[0], new[0]
        if a[1]['value'] == b[1]['value']:
            continue
        changes.append({'product': list(key[:6]), 'metric': key[6], 'unit': key[7],
            'period': list(key[8:]), 'before': a[1]['value'], 'after': b[1]['value'],
            'dates': [dates[0], dates[-1]], 'proofs': [a[0]['evidence_sha256'], b[0]['evidence_sha256']],
            'interpretation': 'TYPED_SOURCE_CHANGE_ONLY; paid-sales trend UNKNOWN'})
    candidates, continuity = [], []
    latest_date = max((r['observed_at'] for r in observations.values()), default='UNKNOWN')
    for key, versions in hypotheses.items():
        snapshot, candidate = versions[-1]
        rows = [r for r in snapshot['observations'] if r['opportunity_id'] == candidate['id']]
        candidates.append(decision(snapshot, candidate, rows))
        contexts = {digest({k: o.get(k) for k in ('topic', 'audience', 'motivation', 'proposals')}) for _, o in versions}
        continuity.append({'key': key, 'runs': [s['run_id'] for s, _ in versions],
                           'context': 'CHANGED_REVIEW_REQUIRED' if len(contexts) > 1 else 'UNCHANGED',
                           'follow_up': 'OBSERVED_IN_LATEST_DATE' if any(r['observed_at'] == latest_date for r in rows) else 'NOT_REOBSERVED_IN_LATEST_RUN',
                           'forecast_result': 'UNPROVEN'})
    all_events = sorted(records(history, 'events'), key=lambda x: (x['recorded_at'], x['record_digest']))
    events = [e for e in all_events if e.get('proposal_id') == PROPOSAL]
    bound = records(history, 'outcomes')
    def verify_refs(value):
        if isinstance(value, dict):
            if 'sha256' in value and 'path' in value:
                proof(history, value['sha256'])
            for v in value.values():
                verify_refs(v)
        elif isinstance(value, list):
            for v in value:
                verify_refs(v)
    verify_refs(all_events)
    verify_refs(bound)
    state_digest = digest({'snapshots': snapshots, 'events': all_events, 'outcomes': bound,
                           'method': METHOD, 'implementation': implementation})
    report = {'kind': 'report', 'state_digest': state_digest, 'method_version': METHOD,
        'implementation_proofs': implementation,
        'research_progress': {'retained_runs': len(latest), 'unique_observations': len(observations),
            'duplicate_observations_excluded': total - len(observations),
            'observation_dates': sorted({r['observed_at'] for r in observations.values()}),
            'independent_commercial_trials': 'UNKNOWN', 'fresh_acquisition_performed_by_learning': False,
            'hypothesis_continuity': continuity, 'typed_source_changes': changes,
            'commercial_predictions_confirmed': 'UNPROVEN', 'commercial_predictions_failed': 'UNPROVEN',
            'missing': ['Product-specific recent paid sales', 'Entrant acquisition cost and conversion', 'Validated differentiation', 'Production return per hour'],
            'return_per_production_hour': 'UNKNOWN'},
        'methodology_review': 'Replays and cumulative audience/activity counts cannot establish repeated paid demand; changed hypothesis contexts need review.',
        'proposed_improvement': proposal(history),
        'proposed_validation_panel': {
            'candidate_ids': [c['id'] for c in sorted(
                [c for c in candidates if c['last_observation'] == latest_date and c['status'] == 'VALIDATE'],
                key=lambda c: ((c['original_assessment'] or {}).get('rank', 999), c['id']))[:3]],
            'products_per_candidate': 2,
            'instruction': 'Preregister exact product URLs, context and evidence questions before T7 follow-up; research only.'},
        'validation': {'status': events[-1]['status'] if events else 'INSUFFICIENT_DATA',
            'scope': 'T7 records, when present, test research coverage only; commercial predictive accuracy remains UNKNOWN.'},
        'learning_history': {'proposals': records(history, 'proposals'), 'events': events,
                             'adopted_effect': 'UNKNOWN; events do not execute algorithm changes'},
        'method_comparison': method_comparison(history),
        'delayed_outcomes': [{'binding': o['binding'], 'observed_date': o['actual']['observed_date'],
            'windows': o['actual']['windows'], 'funnel': o['actual']['funnel'],
            'commercial_success': o['commercial_success']} for o in bound],
        'production_policy': 'HOLD', 'production_authorized': False, 'candidates': candidates,
        'limitations': ['Retained historical replay, not fresh market research', 'No preregistered commercial forecast is adjudicated', 'Missing/no-exposure outcomes are not failures']}
    saved = write(history, 'reports', state_digest, report)
    path = Path(history) / 'reports' / (state_digest + '.md')
    text_once(path, render(saved) + '\n')
    return saved


def render(report):
    p = report['research_progress']
    latest_date = max(p['observation_dates'], default='UNKNOWN')
    current = [c for c in report['candidates'] if c['last_observation'] == latest_date]
    archived = len(report['candidates']) - len(current)
    lines = ['# RADAR LEARNING REPORT', '',
        f"Research progress: {p['retained_runs']} retained runs; {p['unique_observations']} unique source observations; {p['duplicate_observations_excluded']} replay duplicates excluded. Dates: {', '.join(p['observation_dates'])}.",
        'Historical replay only. Paid-demand forecasts remain UNPROVEN; independent commercial trials and return/hour UNKNOWN.', '',
        'Methodology review: ' + report['methodology_review'], '',
        'Proposed improvement: T7 matched panel — three candidates, two direct products each, maximum 20 research minutes; no paid services.',
        'Proposed candidate panel: ' + ', '.join(report['proposed_validation_panel']['candidate_ids']) + '; preregister exact products and questions before follow-up.',
        'Validation: >=4/6 comparable follow-ups; >=1 predeclared evidence question resolved; zero proxy-to-paid substitutions. Coverage benefit only, not commercial accuracy.',
        'Validation status: ' + report['validation']['status'] + '. Commercial prediction accuracy UNKNOWN; see retained event measurements.', '',
        f"Learning history: {len(report['learning_history']['proposals'])} proposal; {len(report['learning_history']['events'])} validation/adoption events. Adoption never changes algorithms automatically.",
        f"Delayed own outcome records explicitly bound: {len(report['delayed_outcomes'])}; missing results are not failures.", '',
        'Production decision: global HOLD. All candidate statuses are proposals for owner review; no production authorization.', '']
    lines.extend(f"- {c['id']}: **{c['status']}** — {c['next_validation']}" for c in current)
    lines += ['', f'{archived} earlier candidates were not reobserved on the latest date; their preserved proposals and full reasoning remain in JSON. Absence of follow-up is not failure.']
    lines += ['', 'Typed comparable source changes (not paid-demand confirmation):']
    lines.extend(f"- {c['product'][0]} / {c['product'][2]}: {c['metric']} {c['before']} → {c['after']} {c['unit']} ({' → '.join(c['dates'])})." for c in p['typed_source_changes'])
    lines += ['', 'Full original assessments, proof hashes, context changes, outcome windows and event history are in the adjacent JSON.']
    comparison = report.get('method_comparison', {})
    if comparison.get('events'):
        lines += ['', '## Prospective discovery methods', '',
                  'No winner is adjudicated. Candidate counts describe research yield, not commercial effectiveness. Shared-method rows must not be summed as independent successes.']
        for row in comparison['methods']:
            lines.append(f"- {row['protocol_id']} / {row['method_id']}: {row['hypotheses']} hypotheses; {row['registered_trials']} registered trials; {row['products_with_paid_response']} products with comparable paid response; commercial effectiveness UNPROVEN.")
        lines += ['Frozen profiles, forecasts, cohort, actual time, typed outcome windows and limitations are in method_comparison in JSON. Production HOLD.']
    return '\n'.join(lines)
