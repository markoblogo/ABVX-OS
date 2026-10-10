"""Manual provider adapters and an offline multi-market overlay for Book Radar.

No network clients, LLM calls, schedules, product creation, or canonical state writes.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import unicodedata
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from .book_radar import _append_unique, _write_json, load_state as load_amazon
from .harness import ValidationError
from .schema_validation import load_draft_2020_12_validator

MARKETS = ('amazon', 'etsy', 'udemy', 'kickstarter')
VERSION = 'book-radar-multi-market-state/v1'
RANKING = 'multi-market-commercial-bands/v1'
TIER_ORDER = {'STRONG': 0, 'MODERATE': 1, 'INSUFFICIENT_EVIDENCE': 2}
SCHEMA = Path(__file__).resolve().parents[2] / 'schemas/book_radar_multi_market.schema.json'


def fail(message):
    raise ValidationError('Multi-market Radar: ' + message)


def norm(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def host(url):
    return (urlsplit(url).hostname or '').lower().removeprefix('www.')


def is_domain(url, domain):
    h = host(url)
    return h == domain or h.endswith('.' + domain)


@dataclass(frozen=True)
class ManualProvider:
    market: str
    domain: str
    demand: tuple[str, ...]
    competition: tuple[str, ...]
    purchases: tuple[str, ...]
    extra: tuple[str, ...]
    freshness_days: int = 30

    @property
    def metrics(self):
        return set(self.demand + self.competition + self.purchases + self.extra)

    def normalize(self, record):
        """Validate a supplied authorized observation; never acquire remote data."""
        if record['marketplace'] != self.market:
            fail('provider / marketplace mismatch')
        if set(record['metrics']) - self.metrics:
            fail(f'{self.market}: unsupported metrics {sorted(set(record["metrics"]) - self.metrics)}')
        if record['source_kind'] != 'LICENSED_ANALYTICS' and not is_domain(record['source_url'], self.domain):
            fail(f'{self.market}: official observation requires the marketplace source URL')
        if record['source_kind'] != 'LICENSED_ANALYTICS' and not is_domain(record['upstream_url'], self.domain):
            fail(f'{self.market}: official observation cannot claim an unrelated upstream origin')
        if record['source_kind'] == 'LICENSED_ANALYTICS' and record['access_basis'] != 'LICENSED_EXPORT':
            fail('third-party analytics require a licensed export')
        if record['source_kind'] == 'OFFICIAL_MANUAL' and record['access_basis'] != 'MANUAL':
            fail('official manual observations require MANUAL access')
        if record['source_kind'] == 'USER_EXPORT' and record['access_basis'] != 'AUTHORIZED_EXPORT':
            fail('user exports require AUTHORIZED_EXPORT access')
        for key, signal in record['metrics'].items():
            if signal['status'] == 'VERIFIED' and record['source_kind'] == 'LICENSED_ANALYTICS':
                fail('third-party analytics cannot be labelled VERIFIED')
            if isinstance(signal['value'], (int, float)) and not isinstance(signal['value'], bool) and signal['value'] < 0:
                fail(f'{key}: negative commercial measurement')
        numeric = {'searches', 'listing_count', 'paid_orders', 'paid_revenue', 'price', 'search_volume', 'course_count', 'median_revenue', 'top_revenue', 'paid_enrollments', 'rating', 'backers', 'pledged', 'goal', 'comparable_count', 'bsr', 'reviews'}
        money = {'paid_revenue', 'price', 'median_revenue', 'top_revenue', 'pledged', 'goal'}
        for key, signal in record['metrics'].items():
            v = signal['value']
            if key in numeric and v is not None:
                if isinstance(v, bool) or not isinstance(v, (int, float)): fail(key + ': requires numeric observation')
                if key in money and (not signal['unit'] or len(signal['unit']) != 3 or not signal['unit'].isupper()):
                    fail(key + ': requires currency code')
                if key not in money and key != 'rating' and int(v) != v: fail(key + ': count/rank requires an integer')
        for dimension, allowed in [('demand', self.demand), ('competition_weakness', self.competition), ('commercial_validation', self.purchases)]:
            assessment = record['assessments'][dimension]
            keys = assessment['metric_keys']
            if assessment['value'] is not None and (not keys or set(keys) - set(allowed)):
                fail(f'{dimension}: requires appropriate marketplace metrics')
            if assessment['value'] is None and keys: fail('unrated assessments must use an empty metric_keys list')
            if any(k not in record['metrics'] or record['metrics'][k]['status'] == 'MISSING' for k in keys):
                fail(f'{dimension}: unavailable metric reference')
        return copy.deepcopy(record)

    def describe(self):
        return {'marketplace': self.market, 'mode': 'MANUAL_IMPORT_ONLY',
                'network_requests': 0, 'credentials_required_by_radar': False,
                'metrics': sorted(self.metrics), 'freshness_days': self.freshness_days}


class EtsyProvider(ManualProvider):
    def __init__(self):
        super().__init__('etsy', 'etsy.com', ('searches', 'search_interest'), ('listing_count', 'competition_quality'),
                         ('paid_orders', 'paid_revenue'), ('price', 'category', 'product_types', 'seasonality', 'emerging_keywords', 'customer_activity', 'trend_dynamics'))


class UdemyProvider(ManualProvider):
    def __init__(self):
        super().__init__('udemy', 'udemy.com', ('search_volume', 'topic_demand'), ('course_count', 'competition_quality'),
                         ('median_revenue', 'top_revenue', 'paid_enrollments'), ('category', 'price', 'course_quality', 'rating', 'quality_gaps', 'emerging_subjects', 'trend_dynamics'))


class KickstarterProvider(ManualProvider):
    def __init__(self):
        super().__init__('kickstarter', 'kickstarter.com', ('backers', 'pledged'), ('comparable_count', 'competition_quality'),
                         ('pledged',), ('category', 'goal', 'campaign_status', 'campaign_timing', 'product_format', 'creator_audience', 'fulfillment_complexity', 'trend_dynamics'), 180)


PROVIDERS = {p.market: p for p in (
    ManualProvider('amazon', 'amazon.com', ('search_interest', 'bsr', 'book_traction'), ('listing_count', 'competition_quality'),
                   ('paid_orders', 'paid_revenue'), ('price', 'reviews', 'delivery_country', 'marketplace_domain', 'trend_dynamics')),
    EtsyProvider(), UdemyProvider(), KickstarterProvider())}


@lru_cache(maxsize=1)
def validator():
    return load_draft_2020_12_validator(SCHEMA)


def read(path):
    path = Path(path)
    if path.stat().st_size > 16 * 1024 * 1024:
        fail('input exceeds 16 MiB')
    try:
        return json.loads(path.read_text(encoding='utf-8'), parse_constant=lambda _: fail('non-finite number'))
    except (ValueError, UnicodeDecodeError) as error:
        fail(str(error))


def digest(path):
    if path.stat().st_size > 16 * 1024 * 1024:
        fail('retained evidence exceeds 16 MiB')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proof_path(base, item):
    rel = Path(item['evidence_path'])
    path = (base / rel).resolve()
    if rel.is_absolute() or '..' in rel.parts or not path.is_relative_to(base.resolve()):
        fail('evidence path escapes import / cache directory')
    if not path.is_file() or digest(path) != item['evidence_sha256']:
        fail('retained evidence missing or hash mismatch')
    return path


def cluster_key(o):
    # Same topic alone never merges different buyers, jobs, languages or countries.
    return tuple(norm(o[k]) for k in ('topic', 'audience', 'motivation', 'language', 'geography'))


def validate(value, base=None):
    def finite(node):
        if isinstance(node, float) and not math.isfinite(node): fail('non-finite numeric value')
        if isinstance(node, dict):
            for v in node.values(): finite(v)
        elif isinstance(node, list):
            for v in node: finite(v)
    finite(value)
    errors = list(validator().iter_errors(value))
    if errors:
        e = errors[0]
        fail('/' + '/'.join(map(str, e.absolute_path)) + ': ' + e.message)
    if len(value['opportunities']) > 1000 or len(value['observations']) > 5000:
        fail('bounded V1 limit: 1000 opportunities / 5000 observations')
    known = {}
    for collection in ('opportunities', 'observations', 'decisions'):
        ids = [r['id'] for r in value[collection]]
        if len(ids) != len(set(ids)):
            fail('duplicate ' + collection + ' IDs')
    for o in value['opportunities']:
        key = cluster_key(o)
        if key in known:
            fail(f'duplicate buyer/topic cluster: reuse opportunity ID {known[key]}')
        known[key] = o['id']
        for p in o['proposals'].values():
            for field in ('effort_hours', 'first_step_hours', 'production_cost', 'funding_goal', 'fulfillment_budget'):
                s = p[field]
                signal_valid(s)
                if s['value'] is not None and field.endswith('hours') and s['unit'] != 'hours':
                    fail('effort must use hours')
                if s['value'] is not None and not field.endswith('hours') and (not s['unit'] or len(s['unit']) != 3 or not s['unit'].isupper()):
                    fail('cost/funding units must be currency codes')
                if s['status'] not in ('ESTIMATED', 'MISSING'):
                    fail('production budgets are estimates, not market facts')
                if s['value'] is not None and (isinstance(s['value'], bool) or not isinstance(s['value'], (int, float)) or s['value'] < 0):
                    fail('production budgets require nonnegative numbers or MISSING')
            total, step = p['effort_hours']['value'], p['first_step_hours']['value']
            if step is not None and (step <= 0 or total is None or step > total):
                fail('first step must be positive and no larger than known total effort')
            if p['policy_review'] == 'CLEAR' and (not p['policy_review_date'] or not p['policy_sources']):
                fail('policy clearance requires dated source references')
    opportunities = {o['id']: o for o in value['opportunities']}
    for r in value['observations']:
        if r['opportunity_id'] not in opportunities:
            fail('unknown observation opportunity')
        if r['period_start'] and r['period_end'] and r['period_start'] > r['period_end']:
            fail('observation period reversed')
        if r['period_end'] and r['period_end'] > r['observed_at']:
            fail('data period cannot follow observation date')
        for s in r['metrics'].values():
            signal_valid(s)
        if r['availability'] != 'AVAILABLE' and any(s['status'] != 'MISSING' for s in r['metrics'].values()):
            fail('unavailable source cannot supply observed metrics')
        has_data = any(s['status'] != 'MISSING' for s in r['metrics'].values())
        if has_data and r['storage_permission'] != 'RETAINED_AUTHORIZED':
            fail('retained evidence requires declared storage permission')
        if bool(r['evidence_path']) != bool(r['evidence_sha256']): fail('evidence path/hash must be supplied together')
        if has_data and (not r['evidence_path'] or not r['evidence_sha256']):
            fail('non-missing signals require retained evidence and SHA256')
        if r['evidence_path'] and base is not None:
            proof_path(base, r)
        provider = PROVIDERS[r['marketplace']]
        if r['marketplace'] == 'amazon' and is_domain(r['source_url'], 'amazon.fr'):
            provider = ManualProvider('amazon', 'amazon.fr', provider.demand, provider.competition, provider.purchases, provider.extra)
        provider.normalize(r)
    seen_revisions = set()
    for r in value.get('revisions', []):
        if r['id'] in seen_revisions or r['opportunity_id'] not in opportunities or r['previous']['id'] != r['opportunity_id']: fail('invalid revision identity/link')
        seen_revisions.add(r['id'])
        validate({'schema_version': VERSION, 'opportunities': [r['previous']], 'observations': [], 'decisions': []})
    for d in value['decisions']:
        if d['opportunity_id'] not in opportunities:
            fail('unknown tracking opportunity')
        if d['marketplace'] != 'ALL' and d['marketplace'] not in opportunities[d['opportunity_id']]['proposals']:
            fail('tracking market must have an explicit proposal')


def signal_valid(s):
    if (s['status'] == 'MISSING') != (s['value'] is None):
        fail('MISSING requires null; observed zero requires an evidence status')
    if isinstance(s['value'], (int, float)) and not isinstance(s['value'], bool) and not s['unit']:
        fail('numeric observations require explicit units')


def state_path(root):
    return root / 'book-radar/multi-market/state.json'


def empty():
    return {'schema_version': VERSION, 'opportunities': [], 'observations': [], 'decisions': [], 'revisions': []}


def load(root):
    path = state_path(root)
    value = read(path) if path.exists() else empty()
    value.setdefault('revisions', [])
    validate(value, path.parent)
    return value


def fingerprint(record):
    canonical = {k: v for k, v in record.items() if k not in ('id', 'evidence_path')}
    for key in ('query', 'language', 'geography', 'audience', 'motivation', 'format'):
        canonical[key] = norm(canonical[key])
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def check(path):
    value = read(path)
    if value.get('schema_version') != 'book-radar-multi-market-import/v1':
        fail('check/import require a multi-market import bundle')
    validate(value, Path(path).parent)
    return value


def import_bundle(root, path):
    packet = check(path)
    state = load(root)
    result = {'opportunities': _append_unique(state, 'opportunities', packet['opportunities']), 'observations': 0}
    ids = {r['id']: r for r in state['observations']}
    seen = {fingerprint(r) for r in state['observations']}
    copies = {}
    retained_bytes = 0
    for item in packet['observations']:
        r = copy.deepcopy(item)
        fp = fingerprint(r)
        if r['evidence_path']:
            source = proof_path(Path(path).parent, r)
            r['evidence_path'] = 'evidence/' + r['evidence_sha256'] + '.bin'
            if r['evidence_path'] not in copies:
                retained_bytes += source.stat().st_size
                if retained_bytes > 64 * 1024 * 1024: fail('import evidence exceeds 64 MiB')
            copies[r['evidence_path']] = source
        if r['id'] in ids and ids[r['id']] != r:
            fail('conflicting observation ID')
        if fp not in seen:
            result['observations'] += _append_unique(state, 'observations', [r])
            seen.add(fp)
            ids[r['id']] = r
    apply_decisions(state, packet['decisions'])
    _append_unique(state, 'revisions', packet.get('revisions', []))
    validate(state)
    # Validate everything before persisting. Cache is content-addressed and bounded.
    for rel, source in copies.items():
        target = state_path(root).parent / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    _write_json(state_path(root), state)
    return {'status': 'IMPORTED', 'added': result, 'network_requests': 0}


def track(root, path):
    packet = read(path)
    if packet.get('schema_version') != 'book-radar-multi-market-import/v1': fail('track requires an import bundle')
    errors = list(validator().iter_errors(packet))
    if errors: fail(errors[0].message)
    if packet['observations']:
        fail('track bundle must not contain observations')
    state = load(root)
    # Supplied opportunity definitions only establish references; cannot alter them.
    for o in packet['opportunities']:
        if o not in state['opportunities']:
            fail('track references an unknown or changed opportunity')
    added = apply_decisions(state, packet['decisions'])
    validate(state, state_path(root).parent)
    _write_json(state_path(root), state)
    return {'status': 'TRACKED', 'added': added, 'production_authorized': False}


def apply_decisions(state, records):
    added = 0
    for d in records:
        affected = MARKETS if d['marketplace'] == 'ALL' else (d['marketplace'],)
        past = [x for x in state['decisions'] if x['opportunity_id'] == d['opportunity_id'] and x['marketplace'] in (*affected, 'ALL')]
        if d not in state['decisions'] and past and d['date'] < max(x['date'] for x in past):
            fail('tracking is chronological; backdated events cannot override history')
        for market in affected:
            prior = latest_decision(state, d['opportunity_id'], market, d['date'])
            if prior and prior['status'] in ('PRODUCED', 'PUBLISHED', 'TESTED', 'REJECTED', 'RESEARCHED') and d['status'] in ('ACCEPTED', 'APPROVED', 'PLANNED', 'IN_DEVELOPMENT'):
                fail('explicit REOPENED with a reason required before reconsideration')
        added += _append_unique(state, 'decisions', [copy.deepcopy(d)])
    return added


def latest_decision(state, oid, market, as_of):
    rows = [d for d in state['decisions'] if d['opportunity_id'] == oid and d['marketplace'] in (market, 'ALL') and d['date'] <= as_of]
    return sorted(rows, key=lambda d: (d['date'], state['decisions'].index(d)))[-1] if rows else None


def freshness(r, as_of):
    if r['observed_at'] > as_of:
        return 'FUTURE'
    if r['period_end'] is None:
        return 'UNKNOWN'
    age = (date.fromisoformat(as_of) - date.fromisoformat(r['period_end'])).days
    return 'FRESH' if 0 <= age <= PROVIDERS[r['marketplace']].freshness_days else 'STALE'


def relevant(r, o, p):
    return all(norm(r[k]) == norm(o[k]) for k in ('language', 'geography', 'audience', 'motivation')) and norm(r['format']) == norm(p['format'])


def measured(r, dimension):
    a = r['assessments'][dimension]
    eligible = [r['metrics'][k] for k in a['metric_keys'] if r['metrics'][k]['status'] in ('VERIFIED', 'ESTIMATED')]
    if a['value'] is None or not eligible or len(eligible) != len(a['metric_keys']):
        return None
    if r['marketplace'] == 'kickstarter' and dimension == 'commercial_validation':
        state = r['metrics'].get('campaign_status', {})
        goal = r['metrics'].get('goal', {})
        pledged = r['metrics'].get('pledged', {})
        if state.get('status') != 'VERIFIED' or goal.get('status') != 'VERIFIED' or not isinstance(goal.get('value'), (int, float)) or goal['value'] <= 0:
            return None
        if state.get('value') != 'successful': return 1
        if pledged.get('unit') != goal.get('unit') or not isinstance(pledged.get('value'), (int, float)) or pledged['value'] < goal['value']: return 1
    if dimension in ('demand', 'commercial_validation') and any(s['value'] == 0 for s in eligible):
        return 1  # observed absence never becomes a positive demand claim
    return a['value']


def policy_blockers(p, market, as_of):
    blocked = []
    if p['rights_status'] != 'CLEAR': blocked.append('rights/licensing review')
    if p['policy_review'] != 'CLEAR' or p['policy_review_date'] is None or not 0 <= (date.fromisoformat(as_of) - date.fromisoformat(p['policy_review_date'])).days <= 90:
        blocked.append('current platform/AI disclosure policy review')
    if market != 'amazon' and p['reuse_mode'] in ('SAME_DIGITAL_CONTENT', 'ADAPTED') and p['kdp_select_status'] not in ('NOT_ENROLLED', 'NOT_APPLICABLE'):
        blocked.append('KDP Select exclusivity check')
    if market == 'udemy' and p['course_design'] != 'STRUCTURED_DEMONSTRATIONS':
        blocked.append('lessons, demonstrations and learning-material design')
    if market == 'kickstarter':
        if p['new_project'] is not True: blocked.append('new/distinct project')
        for f in ('funding_goal', 'fulfillment_budget'):
            if p[f]['value'] is None or p[f]['value'] <= 0: blocked.append(f)
        if not p['shipping_plan']: blocked.append('shipping/delivery plan')
        if not p['audience_plan']: blocked.append('creator audience acquisition plan')
    return blocked


def origin_group(url):
    h = host(url)
    for domain, group in [('amazon.com', 'amazon'), ('amazon.fr', 'amazon'), ('etsy.com', 'etsy'), ('udemy.com', 'udemy'), ('kickstarter.com', 'kickstarter')]:
        if is_domain(url, domain): return group
    return h


def assess_market(state, o, market, as_of):
    p = o['proposals'].get(market)
    raw = [r for r in state['observations'] if r['opportunity_id'] == o['id'] and r['marketplace'] == market]
    common = {'marketplace': market, 'ranking_policy': RANKING, 'eligible': False,
              'commercial_tier': 'INSUFFICIENT_EVIDENCE', 'confidence': 'LOW', 'source_origins': [],
              'observations': [{**r, 'freshness': freshness(r, as_of)} for r in raw],
              'source_urls': sorted({r['source_url'] for r in raw})}
    if p is None:
        return {**common, 'status': 'NOT_ASSESSED', 'missing': ['format suitability proposal'], 'blockers': []}
    evidence = [r for r in raw if r['availability'] == 'AVAILABLE' and freshness(r, as_of) == 'FRESH' and relevant(r, o, p)]
    context_warning = None
    if market == 'amazon':
        domain, country = ('amazon.com', 'US') if o['language'].upper() == 'EN' else ('amazon.fr', 'FR') if o['language'].upper() == 'FR' else (None, None)
        official = [r for r in evidence if domain and r['source_kind'] != 'LICENSED_ANALYTICS' and host(r['source_url']) == domain and o['geography'].upper() == country and r['metrics'].get('delivery_country', {}).get('status') == 'VERIFIED' and r['metrics']['delivery_country']['value'] == country]
        # Secondary licensed research can supplement a verified retailer context;
        # its country/domain declarations and metrics stay estimates.
        secondary = [r for r in evidence if official and r['source_kind'] == 'LICENSED_ANALYTICS' and r['metrics'].get('delivery_country', {}).get('value') == country and r['metrics'].get('marketplace_domain', {}).get('value') == domain]
        evidence = official + secondary
        if raw and not evidence: context_warning = 'Amazon target-domain/delivery-country/language or freshness mismatch'
    values, supporting = {}, {}
    for dimension in ('demand', 'competition_weakness', 'commercial_validation'):
        rows = [(measured(r, dimension), r) for r in evidence]
        rows = [(v, r) for v, r in rows if v is not None]
        values[dimension] = min((v for v, r in rows), default=None)
        supporting[dimension] = [{'id': r['id'], 'interpretation': 'INFERRED', 'rating': v,
                                  'reason': r['assessments'][dimension]['reason']} for v, r in rows]
    values.update(format_fit=p['format_fit'], reusability=p['reuse'], risk=p['risk'])
    missing = [k for k, v in values.items() if v is None]
    for field in ('effort_hours', 'production_cost', 'first_step_hours'):
        if p[field]['value'] is None: missing.append(field)
    if not evidence: missing.append('fresh relevant own-market evidence')
    blockers = policy_blockers(p, market, as_of)
    if context_warning: blockers.append(context_warning)
    origins = sorted({origin_group(r['upstream_url']) for r in evidence})
    # Official observed paid metrics are distinct from estimates/proxies.
    purchase_rows = [r for r in evidence if measured(r, 'commercial_validation') is not None and
                     r['assessments']['commercial_validation']['value'] >= 3 and
                     all(r['metrics'][k]['status'] == 'VERIFIED' and isinstance(r['metrics'][k]['value'], (int, float)) and not isinstance(r['metrics'][k]['value'], bool) and r['metrics'][k]['value'] > 0
                         for k in r['assessments']['commercial_validation']['metric_keys'])]
    if not purchase_rows: missing.append('observed positive paid/crowdfunding indicator')
    if market == 'amazon' and len(origins) < 2: missing.append('two independent origins for Amazon commercial assessment')
    gate = not missing and all(values[k] >= 3 for k in ('demand', 'competition_weakness', 'commercial_validation', 'format_fit', 'risk'))
    tier = 'STRONG' if gate and values['demand'] >= 4 and values['commercial_validation'] >= 4 and len(origins) >= 2 else 'MODERATE' if gate else 'INSUFFICIENT_EVIDENCE'
    statuses = [r['metrics'][k]['status'] for r in evidence for a in r['assessments'].values() for k in a['metric_keys']]
    quality = 'VERIFIED_OBSERVATIONS' if statuses and all(x == 'VERIFIED' for x in statuses) else 'MIXED_OR_ESTIMATED' if statuses else 'MISSING'
    confidence = 'HIGH' if gate and quality == 'VERIFIED_OBSERVATIONS' and len(origins) >= 2 else 'MODERATE' if gate else 'LOW'
    return {**common, 'status': 'READY_FOR_OWNER_VALIDATION' if gate and not blockers else 'RESEARCH_OR_REVIEW',
            'eligible': gate and not blockers, 'commercial_tier': tier, 'ratings': values,
            'supporting_evidence': supporting, 'confidence': confidence, 'evidence_quality': quality,
            'missing': missing, 'blockers': blockers, 'source_origins': origins, 'proposal': p,
            'observations': [{**r, 'freshness': freshness(r, as_of), 'relevant': relevant(r, o, p)} for r in raw],
            'commercial_scope': 'CROWDFUNDING_ONLY' if market == 'kickstarter' else 'MARKET_SPECIFIC'}


def catalog_context(legacy, o):
    ref = o.get('catalog_ref')
    products = [p for p in legacy['products'] if p.get('opportunity_id') == o['amazon_opportunity_id']] if o['amazon_opportunity_id'] else []
    if ref:
        rows = [p for p in legacy[ref['collection']] if p['id'] == ref['id']]
        if not rows: return {'status': 'UNKNOWN', 'products': [], 'performance': []}
        products += [p for p in rows if p not in products]
    ids = {p['id'] for p in products}
    # Raw observed actuals remain labelled; no sales or royalty estimate invented.
    return {'status': 'LINKED' if products else 'NOT_REQUESTED',
            'products': products, 'performance': [a for a in legacy['actuals'] if a.get('product_id') in ids],
            'performance_note': 'Historical snapshots only; preserve period, estimate status, applicability and source. No cross-market demand transfer.'}


def market_order(row, m):
    p = row['opportunity']['proposals'][m]
    a = row['markets'][m]
    return (TIER_ORDER[a['commercial_tier']], p['effort_hours']['value'], p['first_step_hours']['value'], m)


def report(root, as_of, market=None, opportunity=None):
    date.fromisoformat(as_of)
    if market is not None and market not in MARKETS: fail('unknown marketplace filter')
    state = load(root)
    legacy = load_amazon(root)
    legacy_ids = {o['id'] for o in legacy['opportunities']}
    result = []
    for current in state['opportunities']:
        o = current
        for revision in reversed(state.get('revisions', [])):
            if revision['opportunity_id'] == current['id'] and revision['date'] > as_of:
                o = revision['previous']
        if opportunity and o['id'] != opportunity: continue
        if market and market not in o['proposals'] and not any(r['marketplace'] == market and r['opportunity_id'] == o['id'] for r in state['observations']): continue
        markets = {m: assess_market(state, o, m, as_of) for m in MARKETS}
        context = catalog_context(legacy, o)
        qualified = sorted((m for m in MARKETS if markets[m]['eligible']), key=lambda m: market_order({'opportunity': o, 'markets': markets}, m))
        if context['products']:
            qualified = [m for m in qualified if m != 'amazon' and o['proposals'][m]['reuse_mode'] == 'ADAPTED']
        first = qualified[0] if qualified else None
        secondary = [m for m in qualified[1:] if not set(markets[m]['source_origins']) & set(markets[first]['source_origins'])] if first else []
        strategy = 'RESEARCH_ONLY' if not first else 'SINGLE_MARKET' if not secondary else {'amazon': 'AMAZON_FIRST', 'etsy': 'ETSY_FIRST', 'udemy': 'COURSE_FIRST', 'kickstarter': 'KICKSTARTER_FIRST'}[first]
        legacy_id = o['amazon_opportunity_id']
        linked = legacy_id is not None and legacy_id in legacy_ids
        produced = linked and any(p.get('opportunity_id') == legacy_id for p in legacy['products'])
        result.append({'opportunity': o, 'markets': markets, 'strategy': strategy, 'first_market': first,
                       'secondary_markets': secondary, 'cross_market_confirmation': 'INDEPENDENT_RELEVANT' if secondary else 'NOT_ESTABLISHED',
                       'research_date': max((r['observed_at'] for r in state['observations'] if r['opportunity_id'] == o['id'] and r['observed_at'] <= as_of and r['availability'] == 'AVAILABLE' and any(s['status'] != 'MISSING' for s in r['metrics'].values())), default=None),
                       'legacy_amazon_link': 'LINKED' if linked else 'UNKNOWN' if legacy_id else 'NOT_REQUESTED',
                       'legacy_product_exists': bool(produced or context['products']), 'catalog_context': context,
                       'tracking': {m: latest_decision(state, o['id'], m, as_of) for m in MARKETS},
                       'expansion_gate': 'Validate paid buyer response against the initial product target; collect independent format-specific demand and review adaptation, rights, Select and unit economics before expansion.',
                       'revision_history': [r for r in state.get('revisions', []) if r['opportunity_id'] == o['id'] and r['date'] <= as_of],
                       'production_authorized': False})
    if opportunity and not result: fail('unknown opportunity')
    return {'report': 'markets', 'as_of': as_of, 'market_filter': market, 'opportunities': result,
            'ranking_policy': RANKING, 'providers': [p.describe() for p in PROVIDERS.values()], 'network_requests': 0}


def weekly(root, as_of, amazon_committed=None, hours=8):
    if amazon_committed is not None and (isinstance(amazon_committed, bool) or not isinstance(amazon_committed, int) or amazon_committed < 0): fail('amazon committed must be a nonnegative integer')
    if not math.isfinite(hours) or not 0 < hours <= 168: fail('weekly hours must be in (0,168]')
    data, state = report(root, as_of), load(root)
    week = date.fromisoformat(as_of).isocalendar()[:2]
    tracked = len({d['opportunity_id'] for d in state['decisions'] if d['marketplace'] == 'amazon' and d['status'] in ('PLANNED', 'IN_DEVELOPMENT', 'PRODUCED', 'PUBLISHED') and d['date'] <= as_of and date.fromisoformat(d['date']).isocalendar()[:2] == week})
    remaining = 0 if amazon_committed is None else max(0, 2 - max(amazon_committed, tracked))
    actions, skipped, candidates = [], [], []
    for row in data['opportunities']:
        o = row['opportunity']
        if row['legacy_amazon_link'] == 'UNKNOWN' or row['catalog_context']['status'] == 'UNKNOWN':
            skipped.append({'id': o['id'], 'reason': 'unresolved Amazon opportunity link'}); continue
        first = row['first_market']
        research_markets = [m for m in o['proposals'] if not row['legacy_product_exists'] or m != 'amazon']
        if not first and not research_markets:
            skipped.append({'id': o['id'], 'reason': 'existing catalog product: add a distinct adaptation proposal'}); continue
        m = first or research_markets[0]
        decision = row['tracking'][m]
        if decision and decision['status'] in ('REJECTED', 'RESEARCHED', 'PLANNED', 'IN_DEVELOPMENT', 'PRODUCED', 'PUBLISHED', 'TESTED'):
            skipped.append({'id': o['id'], 'reason': decision['status'] + ': explicit reasoned REOPENED required'}); continue
        candidates.append((row, m))
    candidates.sort(key=lambda item: (item[0]['first_market'] is None, market_order(item[0], item[1]) if item[0]['first_market'] else (2, 0, 0, item[1]), item[0]['opportunity']['id']))
    used_markets, spent = set(), 0
    for row, m in candidates:
        if len(actions) >= 5: break
        o, assessment = row['opportunity'], row['markets'][m]
        p = o['proposals'].get(m)
        valid = row['first_market'] is not None
        if valid and m == 'amazon' and remaining == 0:
            skipped.append({'id': o['id'], 'reason': 'Amazon weekly capacity unknown or exhausted'}); continue
        if valid and m != 'amazon' and m in used_markets: continue
        effort = p['first_step_hours']['value'] if valid else 0.5
        if spent + effort > hours:
            skipped.append({'id': o['id'], 'reason': 'first step exceeds remaining effort budget'}); continue
        kind = 'FEASIBILITY' if valid and m == 'kickstarter' else 'PRODUCTION_PROPOSAL' if valid else 'RESEARCH'
        reason = f'Own-market demand, competition and paid-response evidence pass; tier {assessment["commercial_tier"]}, confidence {assessment["confidence"]}' if valid else 'Missing/stale/unmatched evidence or policy/rights review: ' + ', '.join(assessment.get('missing', []) + assessment.get('blockers', []))
        actions.append({'opportunity_id': o['id'], 'name': o['topic'], 'marketplace': m, 'kind': kind,
                        'format': p['format'] if p else 'UNDETERMINED', 'language': o['language'], 'buyer': o['audience'],
                        'reason': reason, 'supporting_evidence': assessment.get('supporting_evidence', {}), 'estimated_hours': effort, 'effort_status': 'ESTIMATED',
                        'cost': p['production_cost'] if p else missing_signal('Cost not researched'),
                        'required_inputs': p['required_inputs'] if valid else ['Authorized relevant source observation', 'Retained evidence', 'Format and rights review'],
                        'commercial_hypothesis': f'{o["audience"]} will pay for {o["motivation"]} in this format; untested hypothesis.',
                        'validation_target': p['validation_target'] if valid else 'Resolve decisive missing data; do not authorize production from a listing or trend alone.',
                        'next_step': p['first_step'] if valid else 'Collect one bounded authorized observation and reassess.',
                        'owner_approval_required': valid, 'production_authorized': False})
        spent += effort
        if valid:
            used_markets.add(m)
            if m == 'amazon': remaining -= 1
    return {'report': 'weekly', 'as_of': as_of, 'iso_week': list(week), 'max_new_amazon_books': 2,
            'amazon_committed_total': amazon_committed, 'amazon_tracked_this_week': tracked,
            'capacity_note': 'Confirm total already planned/produced Amazon books before proposing Amazon work.' if amazon_committed is None else 'Declared total includes tracked books; maximum of declared/tracked is used.',
            'hours_budget': hours, 'estimated_hours': spent, 'actions': actions, 'skipped': skipped,
            'production_authorized': False, 'network_requests': 0}


def missing_signal(note):
    return {'status': 'MISSING', 'value': None, 'unit': None, 'note': note}


def template(market, amazon=None):
    if market not in MARKETS: fail('unknown provider')
    p = {'format': 'REPLACE_WITH_FORMAT', 'format_fit': None, 'reuse': None, 'risk': None,
         **{k: missing_signal('Not researched') for k in ('effort_hours', 'first_step_hours', 'production_cost', 'funding_goal', 'fulfillment_budget')},
         'rationale': 'Not researched', 'first_step': 'Define a bounded validation step', 'required_inputs': [],
         'validation_target': 'Define paid response threshold and time window', 'rights_status': 'REVIEW',
         'policy_review': 'REVIEW', 'policy_review_date': None, 'policy_sources': [], 'kdp_select_status': 'UNKNOWN',
         'reuse_mode': 'ORIGINAL', 'course_design': 'UNKNOWN', 'new_project': None, 'shipping_plan': None, 'audience_plan': None}
    o = {'id': amazon['id'] if amazon else 'replace-opportunity-id', 'topic': 'UNRESEARCHED OPPORTUNITY',
         'audience': 'REPLACE_WITH_BUYER', 'motivation': 'REPLACE_WITH_BUYER_JOB', 'keywords': [],
         'language': 'EN', 'geography': 'US', 'amazon_opportunity_id': amazon['id'] if amazon else None, 'catalog_ref': None,
         'proposals': {market: p}}
    if amazon:
        o['topic'] = amazon.get('topic') or amazon.get('title') or amazon.get('niche') or o['topic']
        o['language'] = amazon.get('language', 'EN')
    return {'schema_version': 'book-radar-multi-market-import/v1', 'opportunities': [o], 'observations': [], 'decisions': []}


def render(value):
    def amount(signal):
        return 'MISSING' if signal['value'] is None else f"{signal['value']} {signal['unit'] or ''} ({signal['status']})".strip()
    if value['report'] == 'weekly':
        lines = [f"BOOK RADAR WEEKLY ({value['as_of']})", f"Amazon ceiling: 2; committed: {value['amazon_committed_total'] if value['amazon_committed_total'] is not None else 'UNKNOWN'}. Effort budget: {value['hours_budget']}h.", value['capacity_note']]
        for a in value['actions']:
            lines.extend([f"\n{a['name']} / {a['marketplace']} / {a['kind']} ({a['estimated_hours']}h ESTIMATED)", f"Format: {a['format']}; language: {a['language']}; buyer: {a['buyer']}", 'Production cost: ' + amount(a['cost']), 'Why: ' + a['reason'], 'Inputs: ' + '; '.join(a['required_inputs']), 'Hypothesis: ' + a['commercial_hypothesis'], 'Validate: ' + a['validation_target'], 'Next: ' + a['next_step'], 'Production requires owner approval.'])
        if not value['actions']: lines.append('No work recommended within the available evidence and capacity.')
        for s in value['skipped']: lines.append(f"Skipped {s['id']}: {s['reason']}")
        return '\n'.join(lines)
    lines = [f"BOOK RADAR MULTI-MARKET ({value['as_of']})"]
    for row in value['opportunities']:
        o = row['opportunity']
        lines.extend([f"\nOPPORTUNITY: {o['topic']} [{o['id']}]", f"Buyer: {o['audience']}; job: {o['motivation']}; {o['language']}/{o['geography']}", f"Research date: {row['research_date'] or 'MISSING'}"])
        context = row['catalog_context']
        lines.append(f"Catalog: {context['status']}; linked products: {len(context['products'])}; historical performance records: {len(context['performance'])}. No demand transfer.")
        for m, a in row['markets'].items():
            lines.append(f"{m}: {a['status']} / {a['confidence']} confidence / {a['commercial_tier']}")
            p = a.get('proposal')
            if p:
                lines.append(f"  Format: {p['format']}; reuse: {p['reuse_mode']}; total effort: {amount(p['effort_hours'])}; first step: {amount(p['first_step_hours'])}; cost: {amount(p['production_cost'])}")
                lines.append('  Format rationale: ' + p['rationale'])
            decision = row['tracking'][m]
            lines.append('  Tracking: ' + (f"{decision['status']} ({decision['date']}): {decision['reason']}" if decision else 'UNRESEARCHED'))
            lines.append('  Missing: ' + ', '.join(a['missing']))
            for r in a['observations']:
                lines.append(f"  {r['id']}: {r.get('freshness', freshness(r, value['as_of']))}; {r['availability']}; captured {r['observed_at']}; period {r['period_start'] or 'UNKNOWN'} to {r['period_end'] or 'UNKNOWN'}; {r['source_url']}")
                missing_metrics = [k for k, s in r['metrics'].items() if s['status'] == 'MISSING']
                for k, s in r['metrics'].items():
                    if s['status'] != 'MISSING': lines.append(f"    {k}: {amount(s)}; {s['note']}")
                if missing_metrics: lines.append('    MISSING metrics: ' + ', '.join(missing_metrics))
                if r['limitations']: lines.append('    Limits: ' + '; '.join(r['limitations']))
            for reasons in a.get('supporting_evidence', {}).values():
                for r in reasons: lines.append(f"  Why [{r['id']}]: {r['reason']} (INFERRED rating {r['rating']})")
            if a.get('blockers'): lines.append('  Review: ' + '; '.join(a['blockers']))
        lines.extend(['Recommended: ' + row['strategy'], 'First: ' + (row['first_market'] or 'Further research'), 'Secondary: ' + (', '.join(row['secondary_markets']) or 'None supported'), 'Expansion: ' + row['expansion_gate'], 'Production requires owner approval.'])
    if not value['opportunities']: lines.append('No multi-market observations imported. Existing Amazon reports remain available.')
    return '\n'.join(lines)


def observation_template(market, opportunity, as_of):
    provider = PROVIDERS[market]
    return {'id': f'replace-observation-{market}', 'opportunity_id': opportunity['id'],
            'marketplace': market, 'source_kind': 'OFFICIAL_MANUAL', 'access_basis': 'MANUAL',
            'authorization_note': 'UNRESEARCHED: enter permitted access and retained-source basis',
            'storage_permission': 'NONE', 'source_url': 'https://' + provider.domain,
            'upstream_url': 'https://' + provider.domain, 'query': 'REPLACE_WITH_QUERY',
            **{k: opportunity[k] for k in ('language', 'geography', 'audience', 'motivation')},
            'format': opportunity['proposals'][market]['format'], 'observed_at': as_of,
            'period_start': None, 'period_end': None, 'availability': 'NOT_AVAILABLE',
            'limitations': ['No research observation collected'],
            'metrics': {k: missing_signal('Not observed') for k in sorted(provider.metrics)},
            'assessments': {k: {'value': None, 'metric_keys': [], 'reason': 'Not researched'} for k in ('demand', 'competition_weakness', 'commercial_validation')},
            'evidence_path': None, 'evidence_sha256': None}


def import_template(root, market, as_of, amazon_id=None, catalog_id=None):
    if amazon_id and catalog_id: fail('choose either an Amazon opportunity or catalog product link')
    legacy = load_amazon(root)
    amazon = None
    if amazon_id:
        amazon = next((o for o in legacy['opportunities'] if o['id'] == amazon_id), None)
        if amazon is None: fail('unknown existing Amazon opportunity')
    packet = template(market, amazon)
    o = packet['opportunities'][0]
    if catalog_id:
        matches = [(collection, p) for collection in ('products', 'portfolio_products') for p in legacy[collection] if p['id'] == catalog_id]
        if len(matches) != 1: fail('unknown or ambiguous catalog product ID')
        collection, product = matches[0]
        o['id'] = 'adapt:' + product['id']
        o['topic'] = product.get('title') or 'Existing catalog adaptation'
        o['catalog_ref'] = {'collection': collection, 'id': product['id']}
        o['proposals'][market]['reuse_mode'] = 'ADAPTED'
    packet['observations'] = [observation_template(market, o, as_of)]
    validate(packet)
    return packet


def export(root, destination):
    if destination.resolve() == (root / 'book-radar/state.json').resolve():
        fail('export cannot overwrite canonical Amazon state')
    state = load(root)
    if destination.resolve() == state_path(root).resolve(): fail('export must use a separate destination')
    # Portable bundle with retained evidence in a sibling, content-addressed folder.
    folder = destination.with_suffix(destination.suffix + '.evidence')
    output = copy.deepcopy(state)
    output['schema_version'] = 'book-radar-multi-market-import/v1'
    for r in output['observations']:
        if r['evidence_path']:
            source = proof_path(state_path(root).parent, r)
            target = folder / (r['evidence_sha256'] + '.bin')
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists(): target.write_bytes(source.read_bytes())
            r['evidence_path'] = str(target.relative_to(destination.parent))
    validate(output, destination.parent)
    _write_json(destination, output)
    return {'status': 'EXPORTED', 'destination': str(destination), 'records': len(output['opportunities'])}


def revise(root, source, reason, as_of):
    """Explicit, auditable metadata/proposal revision; observations stay immutable."""
    date.fromisoformat(as_of)
    if not reason.strip(): fail('revision requires a reason')
    packet = check(source)
    if len(packet['opportunities']) != 1 or packet['observations'] or packet['decisions']:
        fail('revise requires exactly one opportunity and no observations/decisions')
    state = load(root)
    new = packet['opportunities'][0]
    index = next((i for i, o in enumerate(state['opportunities']) if o['id'] == new['id']), None)
    if index is None: fail('revise requires an existing opportunity')
    previous = state['opportunities'][index]
    if previous == new: return {'status': 'UNCHANGED', 'id': new['id']}
    revisions = state.setdefault('revisions', [])
    if any(r['opportunity_id'] == new['id'] and r['date'] > as_of for r in revisions): fail('revision cannot precede existing revision history')
    rid = hashlib.sha256(json.dumps([previous, new, reason, as_of], sort_keys=True).encode()).hexdigest()
    revisions.append({'id': 'revision:' + rid, 'opportunity_id': new['id'], 'date': as_of, 'reason': reason, 'previous': previous})
    state['opportunities'][index] = new
    validate(state, state_path(root).parent)
    _write_json(state_path(root), state)
    return {'status': 'REVISED', 'id': new['id'], 'revision_id': 'revision:' + rid}
