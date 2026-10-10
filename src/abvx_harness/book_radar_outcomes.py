"""Observed outcomes only: no ranking, acquisition, or automatic model updates."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Any

from .harness import ValidationError
from .schema_validation import draft_2020_12_validator

UNKNOWN = 'UNKNOWN'
STAGES = ('PUBLISHED', 'INDEXED', 'DISCOVERABLE', 'EXPOSED', 'CLICKED', 'PURCHASED', 'READ')
CHECKPOINTS = (0, 7, 14, 30, 60, 90)
MECHANISMS = ('TOKI_PONA_NICHE', 'ORIGINAL_NONFICTION', 'ORIGINAL_FICTION', 'SERIES_FICTION',
              'PUBLIC_DOMAIN_TRANSFORMATION', 'TRANSLATION', 'REFERENCE', 'TREND_DRIVEN', 'EVERGREEN', 'OTHER')
EXTRA_COLLECTIONS = ('observed_books', 'portfolio_baselines', 'commercial_hypotheses')
VERSIONS = {'observed_books': 'book-radar-observed-book/v1', 'actuals': 'book-radar-observed-actual/v1',
            'portfolio_baselines': 'book-radar-portfolio-baseline/v1',
            'commercial_hypotheses': 'book-radar-commercial-hypothesis/v1',
            'calibrations': 'book-radar-outcome-calibration/v1'}


def evidence(root: Path, path: str) -> dict[str, str]:
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValidationError(f'Invalid evidence path: {path}')
    return {'path': path, 'sha256': sha256(target.read_bytes()).hexdigest()}


def _quantity(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def observed_stage(value: Any, sources: list[dict], *, window: str = UNKNOWN) -> dict:
    if value == UNKNOWN:
        return {'state': UNKNOWN, 'evidence': [], 'window': window}
    if not _quantity(value):
        raise ValidationError('Observed stage requires a nonnegative quantity or UNKNOWN')
    if not sources:
        raise ValidationError('An observed stage requires evidence')
    return {'state': 'OBSERVED_POSITIVE' if value > 0 else 'OBSERVED_ZERO',
            'evidence': sources, 'window': window}


def funnel(actual: dict) -> dict:
    """Never infer exposure/click/order from royalty, KENP or publication."""
    result = {stage: observed_stage(UNKNOWN, []) for stage in STAGES}
    events = actual['retailer_events']
    for stage in ('PUBLISHED', 'INDEXED', 'DISCOVERABLE'):
        result[stage] = deepcopy(events[stage])
    traffic = actual['instrumentation']
    result['EXPOSED'] = observed_stage(traffic['impressions'], actual['instrumentation_evidence'], window=actual['instrumentation_window'])
    result['CLICKED'] = observed_stage(traffic['clicks'], actual['instrumentation_evidence'], window=actual['instrumentation_window'])
    result['PURCHASED'] = observed_stage(actual['windows']['lifetime']['paid_units'], actual['windows']['lifetime']['evidence'], window='lifetime')
    result['READ'] = observed_stage(actual['windows']['kenp']['kenp_pages'], actual['windows']['kenp']['evidence'], window='kenp')
    for stage, applicability in actual['stage_applicability'].items():
        if applicability['state'] == 'NOT_APPLICABLE':
            if not applicability['evidence'] or result[stage]['state'] == 'OBSERVED_POSITIVE':
                raise ValidationError('NOT_APPLICABLE requires evidence and cannot erase a positive observation')
            result[stage] = {'state': 'NOT_APPLICABLE', 'evidence': applicability['evidence'], 'window': UNKNOWN}
    return result


def classify(actual: dict) -> dict:
    """Bounded findings; one query absence is not an exact rank or global cause."""
    findings = [{'classification': 'NOT_FOUND_IN_OBSERVED_DEPTH', 'evidence': d['evidence'],
                 'scope': {'query': d['query'], 'observed_date': d['observed_date'], 'depth': d['depth_inspected']}}
                for d in actual['discovery'] if d['result'] == 'NOT_FOUND_WITHIN_DEPTH']
    f = actual['funnel']; paid = actual['windows']['lifetime']['paid_units']; traffic = actual['instrumentation']
    status = UNKNOWN; refs = []
    # A failed exact identity/indexing test must be recorded explicitly.
    if f['INDEXED']['state'] == 'OBSERVED_ZERO':
        status, refs = 'NOT_INDEXED', f['INDEXED']['evidence']
    same_window = actual['instrumentation_window'] == 'lifetime'
    if same_window and _quantity(paid):
        impressions, clicks = traffic['impressions'], traffic['clicks']
        if _quantity(clicks) and clicks > 0 and paid == 0:
            status, refs = 'CLICK_WITHOUT_PURCHASE', actual['instrumentation_evidence'] + actual['windows']['lifetime']['evidence']
        elif _quantity(impressions) and impressions > 0 and clicks == 0:
            status, refs = 'EXPOSURE_WITHOUT_CLICK', actual['instrumentation_evidence']
        elif impressions == 0:
            status, refs = 'LOW_EXPOSURE', actual['instrumentation_evidence']
    # READ covers a separate KENP window and cannot adjudicate PURCHASE_WITHOUT_READ.
    return {'classification': status, 'evidence': refs, 'findings': findings,
            'unresolved': ['organic exposure', 'click denominator', 'matched read cohort'] if status == UNKNOWN else []}


def checkpoint(publication_date: str, observed_date: str, day: int,
               *, approximate_tolerance: int | None = None) -> dict:
    if isinstance(day, bool) or not isinstance(day, int) or day not in CHECKPOINTS:
        raise ValidationError('Unsupported checkpoint')
    result = {'checkpoint': f'D{day}', 'actual_observation_date': observed_date,
              'actual_book_age_days': UNKNOWN, 'due_date': UNKNOWN, 'status': UNKNOWN,
              'age_basis': 'PUBLICATION_DATE_ONLY_NOT_FIRST_LIVE'}
    if publication_date == UNKNOWN:
        return result
    anchor, observed = date.fromisoformat(publication_date), date.fromisoformat(observed_date)
    age = (observed - anchor).days
    if age < 0:
        raise ValidationError('Observation precedes publication date')
    result.update(actual_book_age_days=age, due_date=(anchor + timedelta(days=day)).isoformat())
    result['status'] = 'EXACT' if age == day else 'PENDING' if age < day else 'LATE'
    if approximate_tolerance is not None:
        if isinstance(approximate_tolerance, bool) or not isinstance(approximate_tolerance, int) or approximate_tolerance < 0:
            raise ValidationError('Approximation tolerance must be nonnegative')
        if age != day and abs(age - day) <= approximate_tolerance:
            result['status'] = 'APPROXIMATE'
            result['declared_tolerance_days'] = approximate_tolerance
    return result


def calibrate(claim: dict, actual: dict, book: dict) -> dict:
    """Compare only commensurate, complete windows; age never scales a forecast."""
    window = actual['windows']['lifetime']; paid = window['paid_units']
    age = actual['book_age_days']; status = UNKNOWN; signal = UNKNOWN
    if claim['metric'] == UNKNOWN or claim['range'] == UNKNOWN:
        status = UNKNOWN
    elif claim['metric'] != 'paid_units' or paid == UNKNOWN:
        status = 'INCOMPARABLE'
    elif claim['horizon_days'] == UNKNOWN or age == UNKNOWN:
        status = 'NOT_YET_ADJUDICABLE'
    elif age < claim['horizon_days']:
        status = 'NOT_YET_ADJUDICABLE'
        signal = UNKNOWN if paid == UNKNOWN else 'NEGATIVE_EARLY_SIGNAL' if paid == 0 else 'POSITIVE_EARLY_SIGNAL'
    elif claim['basis'] != 'PAID_PROCESSED':
        status = 'INCOMPARABLE'
    else:
        # Lifetime cumulative observed after the horizon is not the horizon's total.
        exact = age == claim['horizon_days'] and window['end'] == actual['observed_date']
        covers_launch = book['publication_date'] != UNKNOWN and window['start'] <= book['publication_date']
        if not exact or not covers_launch:
            status = 'INCOMPARABLE'
        else:
            low, high = claim['range']
            status = 'SUPPORTED' if low <= paid <= high else 'NOT_SUPPORTED'
    return {'schema_version': VERSIONS['calibrations'], 'id': f"calibration:{actual['id']}:{claim['id']}",
            'book_id': book['id'], 'product_id': actual['product_id'], 'actual_id': actual['id'],
            'claim': deepcopy(claim), 'observed_date': actual['observed_date'], 'book_age_days': age,
            'observed_paid_units': paid, 'status': status, 'early_signal': signal,
            'evidence': window['evidence'] + claim['evidence'], 'model_update_authorized': False}


@lru_cache(maxsize=5)
def _validator(collection: str):
    import json
    schema = json.loads((Path(__file__).resolve().parents[2] / 'schemas/book_radar_outcome_foundation.schema.json').read_text())
    schema.pop('oneOf', None)
    schema['$ref'] = f'#/$defs/{collection}'
    return draft_2020_12_validator(schema)


def validate_record(record: dict, collection: str) -> None:
    """Validate the versioned extension while accepting legacy v1 records unchanged."""
    version = record.get('schema_version')
    if version not in VERSIONS.values():
        if collection in EXTRA_COLLECTIONS or isinstance(version, str) and version.startswith(('book-radar-observed-', 'book-radar-outcome-', 'book-radar-commercial-hypothesis/', 'book-radar-portfolio-baseline/')):
            raise ValidationError('Unsupported observed record version')
        return
    if version != VERSIONS.get(collection):
        raise ValidationError('Outcome record in wrong collection')
    errors = sorted(_validator(collection).iter_errors(record), key=lambda e: str(e.path))
    if errors:
        raise ValidationError(f"{record.get('id')}: {errors[0].message}")
    if collection == 'calibrations' and record['claim']['range'] != UNKNOWN:
        values = record['claim']['range']
        if not all(_quantity(v) for v in values) or values[0] > values[1]:
            raise ValidationError('Claim range requires ordered numerical bounds')
    if collection == 'observed_books':
        if any(record[k] != UNKNOWN for k in ('publication_date', 'publication_timestamp', 'first_verified_live_date')) and not record['date_evidence']:
            raise ValidationError('Observed dates require evidence')
    if collection == 'commercial_hypotheses' and record['status'] == 'HISTORICAL_PARTIAL':
        if any(f['value'] != UNKNOWN and not f['evidence'] for f in record['fields'].values()):
            raise ValidationError('Historical hypothesis value requires retained evidence')
    if collection == 'actuals':
        for w in record['windows'].values():
            if w['start'] > w['end'] or w['end'] > record['observed_date']:
                raise ValidationError('Invalid reporting window')
            if any(_quantity(v) for k,v in w.items() if k not in ('start','end','evidence')) and not w['evidence']:
                raise ValidationError('Observed metrics require evidence')
        w = record['windows']['lifetime']
        if all(_quantity(w[k]) for k in ('processed_units', 'paid_units', 'free_units')):
            if w['processed_units'] != w['paid_units'] + w['free_units']:
                raise ValidationError('Paid plus free must equal operations')
        for key in ('lifetime', 'recent'):
            w = record['windows'][key]
            if all(_quantity(w[k]) for k in ('paid_units', 'ebook_paid', 'print_paid')) and w['paid_units'] != w['ebook_paid'] + w['print_paid']:
                raise ValidationError('Paid formats must reconcile')
            if all(_quantity(w[k]) for k in ('processed_units','paid_units','free_units')) and w['processed_units'] != w['paid_units']+w['free_units']:
                raise ValidationError('Operations must reconcile')
        if record['funnel'] != funnel(record) or record['classification'] != classify(record):
            raise ValidationError('Funnel/classification must be derived from recorded evidence')
        if any(v != UNKNOWN for v in record['instrumentation'].values()) and not record['instrumentation_evidence']:
            raise ValidationError('Instrumentation requires evidence')
        for d in record['discovery']:
            if d['result'] in ('NOT_FOUND_WITHIN_DEPTH', UNKNOWN) and d['position'] != UNKNOWN:
                raise ValidationError('Absence/UNKNOWN cannot establish rank')
            if d['result'] == 'NOT_FOUND_WITHIN_DEPTH' and d['depth_inspected'] == UNKNOWN:
                raise ValidationError('Absence requires inspected depth')
            if d['result'] == 'FOUND' and (d['position'] == UNKNOWN or not d['evidence']):
                raise ValidationError('Found position requires evidence')
            if d['observed_date'] > record['observed_date']:
                raise ValidationError('Future discovery evidence')
        for stage in record['funnel'].values():
            if stage['state'] in ('OBSERVED_POSITIVE','OBSERVED_ZERO') and not stage['evidence']:
                raise ValidationError('Funnel observation requires evidence')


def validate_links(state: dict) -> None:
    books = {b['id']:b for b in state.get('observed_books',[])}
    actuals = {a['id']:a for a in state['actuals'] if a.get('schema_version') == VERSIONS['actuals']}
    products = {p['id'] for p in state['products']}; decisions = {d['id'] for d in state['decisions']}; runs={r['id'] for r in state['radar_runs']}
    for b in books.values():
        if b['product_id'] != UNKNOWN and b['product_id'] not in products:
            raise ValidationError('Unknown observed product')
        if any(d not in decisions for d in b['decision_ids']) or b['radar_run_id'] != UNKNOWN and b['radar_run_id'] not in runs:
            raise ValidationError('Unknown historical decision/run link')
    for a in actuals.values():
        b=books.get(a['book_id'])
        if b is None or b['product_id'] != a['product_id']:
            raise ValidationError('Actual book/product identity mismatch')
        age = UNKNOWN if b['publication_date']==UNKNOWN else (date.fromisoformat(a['observed_date'])-date.fromisoformat(b['publication_date'])).days
        if age != a['book_age_days']:
            raise ValidationError('Book age must use publication date')
        if a['checkpoint'] != 'AD_HOC' and (age==UNKNOWN or a['checkpoint'] != f'D{age}' or age not in CHECKPOINTS):
            raise ValidationError('Exact checkpoint must match actual age')
    for h in state.get('commercial_hypotheses',[]):
        if h['book_id'] not in books:
            raise ValidationError('Hypothesis book missing')
    for c in state['calibrations']:
        if c.get('schema_version') != VERSIONS['calibrations']:continue
        a=actuals.get(c['actual_id']); b=books.get(c['book_id'])
        if a is None or b is None or a['book_id']!=b['id'] or c != calibrate(c['claim'],a,b):
            raise ValidationError('Calibration does not match actual/claim')
    for baseline in state.get('portfolio_baselines',[]):
        selected=[actuals.get(i) for i in baseline['actual_ids']]
        if any(a is None or a['observed_date']!=baseline['observed_date'] for a in selected) or len({a['book_id'] for a in selected})!=len(selected):
            raise ValidationError('Invalid baseline observation identities')
        for key in ('processed_units','paid_units','free_units','ebook_paid','print_paid'):
            vals=[a['windows']['lifetime'][key] for a in selected]
            if any(v==UNKNOWN for v in vals) or sum(vals)!=baseline['totals'][key]:
                raise ValidationError('Baseline does not reconcile canonical actuals')
        if baseline['title_count']!=len(selected):raise ValidationError('Baseline count mismatch')


def _evidence_refs(value: Any):
    if isinstance(value,dict):
        if set(value)=={'path','sha256'}:yield value
        for child in value.values():yield from _evidence_refs(child)
    elif isinstance(value,list):
        for child in value:yield from _evidence_refs(child)


def import_foundation(root: Path, source: Path) -> dict:
    """Append-only, idempotent local import; verify raw evidence before saving."""
    from .book_radar import load_state, save_state, _append_unique
    from .harness import load_json
    bundle=load_json(source)
    allowed=(*EXTRA_COLLECTIONS,'actuals','calibrations','products','launches')
    if bundle.get('schema_version')!='book-radar-outcome-import/v1' or set(bundle)-set(allowed)-{'schema_version'}:
        raise ValidationError('Unsupported outcome import')
    unique_refs = {(ref['path'], ref['sha256']): ref for ref in _evidence_refs(bundle)}
    for ref in unique_refs.values():
        if evidence(root,ref['path'])!=ref:raise ValidationError(f"Evidence hash mismatch: {ref['path']}")
    state=load_state(root); before=deepcopy(state)
    for collection in allowed:
        records=bundle.get(collection,[])
        if not isinstance(records,list):raise ValidationError('Expected record array')
        for record in records:
            if collection in VERSIONS and record.get('schema_version')!=VERSIONS[collection]:
                raise ValidationError('Foundation import requires typed records')
    added={c:_append_unique(state,c,bundle.get(c,[])) for c in allowed}
    # Older products/runs/forecasts remain exactly as recorded. Generic append is also immutable.
    for c in before:
        if isinstance(before[c],list) and state[c][:len(before[c])]!=before[c]:raise ValidationError('Protected history changed')
    save_state(root,state)
    return {'status':'OUTCOME_IMPORTED','added':added,'external_writes':0}


def cohort_summary(state: dict, baseline: dict) -> dict:
    books={b['id']:b for b in state['observed_books']}; actuals={a['id']:a for a in state['actuals']}
    selected=[actuals[i] for i in baseline['actual_ids']]
    names=('RADAR_PRIMARY','TOKI_PONA','OTHER_TRANSLATION','ORIGINAL_NONFICTION','ORIGINAL_FICTION','SERIES_FICTION')
    result={}
    for name in names:
        rows=[a for a in selected if name in books[a['book_id']]['cohorts']]
        paid=[a['windows']['lifetime']['paid_units'] for a in rows]
        money=[a['windows']['money']['estimated_royalties'] for a in rows]
        def total(field):
            values=[a['windows']['lifetime'][field] for a in rows]
            return sum(values) if all(_quantity(v) for v in values) else UNKNOWN
        result[name]={'title_count':len(rows),'book_ids':[a['book_id'] for a in rows],
                      'paid_units':sum(paid) if all(_quantity(v) for v in paid) else UNKNOWN,
                      'free_units':total('free_units'),
                      'ebook_paid':total('ebook_paid'),
                      'print_paid':total('print_paid'),
                      'estimated_royalties':round(sum(money),2) if all(_quantity(v) for v in money) else UNKNOWN,
                      'currency':baseline['currency'],'paid_median':median(paid) if paid and all(_quantity(v) for v in paid) else UNKNOWN,
                      'paid_range':[min(paid),max(paid)] if paid and all(_quantity(v) for v in paid) else UNKNOWN,
                      'paid_share':sum(paid)/baseline['totals']['paid_units'] if paid and baseline['totals']['paid_units']>0 and all(_quantity(v) for v in paid) else UNKNOWN}
    return {'ontology':'OVERLAPPING_DESCRIPTIVE_TAGS; sums across cohorts are not portfolio totals; unclassified retained',
            'causality':'NOT_ESTABLISHED','scoring_effect':'NONE','cohorts':result}


def outcome_report(root: Path, kind: str, as_of: str) -> dict:
    from .book_radar import load_state
    state=load_state(root); today=date.fromisoformat(as_of); actuals=[a for a in state['actuals'] if a.get('schema_version')==VERSIONS['actuals'] and a['observed_date']<=as_of]
    baselines=[b for b in state['portfolio_baselines'] if b['observed_date']<=as_of]
    if kind=='cohorts':
        if not baselines:return {'report':'cohorts','as_of':as_of,'status':UNKNOWN}
        baseline=max(baselines,key=lambda b:b['observed_date'])
        return {'report':'cohorts','as_of':as_of,'baseline_id':baseline['id'],**cohort_summary(state,baseline)}
    if kind=='calibration':return {'report':'calibration','as_of':as_of,'calibrations':[c for c in state['calibrations'] if c.get('schema_version')==VERSIONS['calibrations'] and c['observed_date']<=as_of]}
    if kind not in ('outcomes','checkpoints'):raise ValidationError('Unknown outcome report')
    result=[]
    for book in state['observed_books']:
        if not book['initial_experiment']:continue
        rows=[a for a in actuals if a['book_id']==book['id']]; latest=max(rows,key=lambda a:a['observed_date']) if rows else None
        schedule=[]
        for day in CHECKPOINTS:
            cp=checkpoint(book['publication_date'],as_of,day)
            exact=[a['id'] for a in rows if a['book_age_days']==day]
            cp['exact_actual_ids']=exact
            cp['collection_status']='RECORDED' if exact else 'DUE_UNRECORDED' if cp['due_date']!=UNKNOWN and cp['due_date']<=as_of else 'PENDING' if cp['due_date']!=UNKNOWN else UNKNOWN
            cp['actual_observation_date']=latest['observed_date'] if latest else UNKNOWN
            cp['actual_book_age_days']=latest['book_age_days'] if latest else UNKNOWN
            cp['status']=checkpoint(book['publication_date'],latest['observed_date'],day)['status'] if latest else UNKNOWN
            schedule.append(cp)
        future=[cp for cp in schedule if cp['due_date']!=UNKNOWN and cp['due_date']>as_of]
        result.append({'book':book,'latest_actual':latest if kind=='outcomes' else latest['id'] if latest else UNKNOWN,
                       'checkpoints':schedule,'next_due':min(future,key=lambda cp:cp['due_date']) if future else UNKNOWN,
                       'too_young_for_D90': book['publication_date']==UNKNOWN or (today-date.fromisoformat(book['publication_date'])).days<90})
    return {'report':kind,'as_of':as_of,'experiments':result,'external_reads':0,'external_writes':0}
