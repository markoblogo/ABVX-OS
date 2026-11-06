"""Offline, immutable shelf evidence; intentionally independent of Radar state/scoring."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from .harness import ValidationError
from .schema_validation import load_draft_2020_12_validator

SCHEMA = Path(__file__).resolve().parents[2] / 'schemas/EXTERNAL_SHELF_SNAPSHOT_SCHEMA_V1.json'
STORE = Path('.tmp/external-shelf-intelligence-v1')
U = 'UNKNOWN'


def fail(message):
    raise ValidationError('External shelf: ' + message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def stamp(value):
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value):
            fail('timestamp requires RFC 3339 date, time and timezone')
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            fail('timestamp requires timezone')
        return result
    except (TypeError, ValueError) as error:
        fail('invalid timestamp: ' + str(error))


@lru_cache(maxsize=1)
def validator():
    return load_draft_2020_12_validator(SCHEMA)


def value(field):
    return field['value'] if field['state'] == 'OBSERVED' else None


def measurements(node):
    if isinstance(node, dict):
        if {'state', 'value', 'evidence_ids'} <= node.keys():
            yield node
        else:
            for child in node.values():
                yield from measurements(child)
    elif isinstance(node, list):
        for child in node:
            yield from measurements(child)


def isbn_valid(s):
    if len(s) == 10:
        return sum((10-i)*(10 if c == 'X' else int(c)) for i,c in enumerate(s)) % 11 == 0
    return sum(int(c)*(1 if i % 2 == 0 else 3) for i,c in enumerate(s)) % 10 == 0


def identity_key(product, marketplace):
    identity = product['identity']
    asin = value(identity['asin'])
    if asin is not None:
        return 'asin:' + marketplace + ':' + asin
    isbn = value(identity['isbn'])
    fmt = value(identity['format'])
    edition = value(identity['edition'])
    if isbn is not None and fmt is not None and edition is not None:
        return 'isbn:' + isbn + ':' + fmt + ':' + edition
    return None  # title is never an identity or a fallback merge key


def validate(packet):
    errors = sorted(validator().iter_errors(packet), key=lambda e: str(list(e.absolute_path)))
    if errors:
        fail('/' + '/'.join(map(str, errors[0].absolute_path)) + ': ' + errors[0].message)
    observed = stamp(packet['observed_at'])
    if stamp(packet['cluster']['frozen_at']) > observed:
        fail('cluster must be frozen before observation')
    routes = packet['cluster']['routes']
    if len({r['id'] for r in routes}) != len(routes) or packet['route_id'] not in {r['id'] for r in routes}:
        fail('unique frozen route required')
    ids = [r['id'] for r in packet['evidence']]
    if len(ids) != len(set(ids)):
        fail('duplicate evidence id')
    for field in measurements(packet['products']):
        if not set(field['evidence_ids']) <= set(ids):
            fail('unknown evidence reference')
    context = packet['context']
    if context['depth_reached'] > context['depth_requested']:
        fail('depth reached exceeds requested depth')
    if context['depth_complete'] and context['depth_reached'] != context['depth_requested']:
        fail('complete depth requires reached = requested')
    slots, orders, keys = set(), set(), set()
    for product in packet['products']:
        order = product['position']['capture_order']
        if product['slot_id'] in slots or order in orders:
            fail('duplicate capture slot/order')
        slots.add(product['slot_id']); orders.add(order)
        if order > context['depth_reached']:
            fail('capture order exceeds observed depth')
        rank = value(product['position']['rank'])
        if rank is not None and rank > context['depth_reached']:
            fail('visible rank exceeds observed depth')
        if rank is not None and value(product['position']['basis']) is None:
            fail('rank requires observed organic/sponsored basis')
        isbn = value(product['identity']['isbn'])
        if isbn is not None and not isbn_valid(isbn):
            fail('ISBN checksum invalid')
        key = identity_key(product, context['marketplace'])
        if key:
            keys.add(key)  # duplicate organic/sponsored appearances remain separate slots
        for name in ('publication_date', 'edition_date'):
            d = value(product[name])
            if d is not None:
                try:
                    date.fromisoformat(d)
                except ValueError:
                    fail('invalid calendar date')
        bsr = value(product['bsr'])
        if bsr and bsr['marketplace'] != context['marketplace']:
            fail('BSR marketplace differs from snapshot')
    if context['depth_complete'] and orders != set(range(1,context['depth_reached']+1)):
        fail('complete depth requires every captured slot; retain unknown slots explicitly')
    if packet['repeat_of'] == packet['id']:
        fail('snapshot cannot repeat itself')
    for absence in packet['absences']:
        if absence['depth'] != context['depth_reached'] or not set(absence['evidence_ids']) <= set(ids):
            fail('absence must refer to actual observed depth/evidence')
        if absence['identity_key'] in keys:
            fail('identity cannot be present and absent')
    return packet


def local_evidence(base, reference):
    relative = Path(reference['path'])
    if relative.is_absolute() or '..' in relative.parts:
        fail('evidence must be a relative path inside the packet directory')
    resolved = (base / relative).resolve()
    if not resolved.is_relative_to(base.resolve()) or not resolved.is_file():
        fail('evidence missing or outside packet directory')
    raw = resolved.read_bytes()
    if digest(raw) != reference['sha256']:
        fail('changed evidence bytes: ' + reference['path'])
    return raw


def checked_source(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    packet = validate(json.loads(raw))
    evidence = {ref['id']: local_evidence(path.parent, ref) for ref in packet['evidence']}
    return packet, raw, evidence


def check_snapshot(path):
    packet, raw, _ = checked_source(path)
    return {'status':'PASS', 'snapshot_id':packet['id'], 'origin':packet['origin'],
            'sha256':digest(raw), 'products':len(packet['products']), 'live_scan':False}


def store_path(root, path):
    if not path.resolve().is_relative_to(Path(root).resolve()):
        fail('store path escapes repository root')
    return path


def domain(root, origin):
    return store_path(root, Path(root) / STORE / origin.lower())


def record_dir(root, origin, snapshot_id):
    return store_path(root, domain(root, origin) / 'snapshots' / digest(snapshot_id.encode()))


def read_record(folder):
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    raw = (folder / 'source.json').read_bytes()
    if digest(raw) != manifest['source_sha256']:
        fail('stored snapshot changed')
    packet = validate(json.loads(raw))
    if folder.parent.parent.name != packet['origin'].lower():
        fail('stored evidence domain changed')
    if manifest['snapshot_id'] != packet['id'] or manifest['origin'] != packet['origin']:
        fail('stored manifest identity changed')
    if folder.name != digest(packet['id'].encode()):
        fail('stored directory identity mismatch')
    expected = {ref['id']: ref for ref in packet['evidence']}
    if set(manifest['evidence']) != set(expected):
        fail('stored evidence manifest mismatch')
    for eid, ref in manifest['evidence'].items():
        if ref['sha256'] != expected[eid]['sha256']:
            fail('stored evidence hash mismatch')
        local_evidence(folder, ref)
    cluster_path = folder.parent.parent / 'clusters' / (digest(packet['cluster']['id'].encode()) + '.json')
    if cluster_path.read_bytes() != encode(packet['cluster']):
        fail('stored frozen cluster changed')
    return packet, {'path':(folder / 'source.json').as_posix(), 'sha256':digest(raw)}


def import_snapshot(root, path):
    packet, raw, evidence = checked_source(path)  # no writes before complete validation
    target = record_dir(root, packet['origin'], packet['id'])
    base = domain(root, packet['origin'])
    cluster_bytes = encode(packet['cluster'])
    cluster_path = store_path(root, base / 'clusters' / (digest(packet['cluster']['id'].encode()) + '.json'))
    if not base.resolve().is_relative_to(Path(root).resolve()):
        fail('store escapes repository root')
    base.mkdir(parents=True, exist_ok=True)
    with (base / '.import.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if cluster_path.exists() and cluster_path.read_bytes() != cluster_bytes:
            fail('frozen cluster changed; use a new cluster id')
        if target.exists():
            old, ref = read_record(target)
            if ref['sha256'] != digest(raw):
                fail('snapshot id reused with changed bytes')
            return {'status':'PASS','added':0,'snapshot_id':old['id'],'origin':old['origin'],
                    'evidence_ref':relative_ref(root,ref),'canonical_state_written':False}
        if packet['repeat_of'] is not None:
            previous_dir = record_dir(root, packet['origin'], packet['repeat_of'])
            if not previous_dir.exists():
                fail('repeat predecessor missing from same evidence domain')
            previous, _ = read_record(previous_dir)
            if previous['cluster']['id'] != packet['cluster']['id'] or previous['route_id'] != packet['route_id']:
                fail('repeat must use same frozen cluster and route')
            if stamp(previous['observed_at']) >= stamp(packet['observed_at']):
                fail('repeat observation must follow predecessor chronologically')
        (base / 'snapshots').mkdir(exist_ok=True)
        cluster_path.parent.mkdir(exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='.import-', dir=base))
        try:
            (staging / 'raw').mkdir()
            refs = {}
            for ref in packet['evidence']:
                name = 'raw/' + ref['sha256']
                (staging / name).write_bytes(evidence[ref['id']])
                refs[ref['id']] = {'path':name,'sha256':ref['sha256']}
            (staging / 'source.json').write_bytes(raw)
            (staging / 'manifest.json').write_bytes(encode({'schema_version':'external-shelf-import/v1',
                'snapshot_id':packet['id'],'origin':packet['origin'],'source_sha256':digest(raw),'evidence':refs}))
            for p in staging.rglob('*'):
                if p.is_file():
                    p.chmod(0o444)
            if not cluster_path.exists():
                with cluster_path.open('xb') as out:
                    out.write(cluster_bytes)
                cluster_path.chmod(0o444)
            os.rename(staging, target)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    return {'status':'PASS','added':1,'snapshot_id':packet['id'],'origin':packet['origin'],
            'evidence_ref':{'path':(target / 'source.json').relative_to(root).as_posix(),'sha256':digest(raw)},
            'canonical_state_written':False}


def relative_ref(root, ref):
    return {'path':Path(ref['path']).relative_to(root).as_posix(),'sha256':ref['sha256']}


def records(root, cluster_id, origin):
    if origin not in ('RETAINED','SYNTHETIC'):
        fail('origin must be RETAINED or SYNTHETIC')
    folder = store_path(root, domain(root,origin) / 'snapshots')
    result = []
    if folder.exists():
        for directory in sorted(folder.iterdir()):
            packet, ref = read_record(directory)
            if packet['cluster']['id'] == cluster_id:
                result.append((packet,relative_ref(root,ref)))
    if not result:
        fail('no imported snapshots for cluster and origin')
    return sorted(result, key=lambda row:(stamp(row[0]['observed_at']),row[0]['id']))


def position_map(packet):
    entries = {}
    for product in packet['products']:
        key = identity_key(product,packet['context']['marketplace'])
        basis = value(product['position']['basis'])
        if key is not None and basis is not None:
            entries.setdefault((key,basis),[]).append(product)
    return entries


def compare_pair(before, after):
    reasons = []
    if before['cluster'] != after['cluster'] or before['route_id'] != after['route_id']:
        reasons.append('FROZEN_CLUSTER_OR_ROUTE_CHANGED')
    if before['origin'] != after['origin']:
        reasons.append('EVIDENCE_DOMAIN_CHANGED')
    for name, item in before['context'].items():
        other = after['context'][name]
        if item != other:
            reasons.append('CONTEXT_DRIFT:' + name)
        if isinstance(item,str) and item in ('UNKNOWN','NOT_VISIBLE','NOT_AVAILABLE','ACCESS_FAILED') or isinstance(other,str) and other in ('UNKNOWN','NOT_VISIBLE','NOT_AVAILABLE','ACCESS_FAILED'):
            reasons.append('UNKNOWN_CONTEXT:' + name)
    route = next(r for r in before['cluster']['routes'] if r['id'] == before['route_id'])
    for packet in (before,after):
        if packet['context']['marketplace'] != route['marketplace'] or packet['context']['route_definition'] != route['definition']:
            reasons.append('CONTEXT_DIFFERS_FROM_FROZEN_ROUTE')
    if not before['context']['depth_complete'] or not after['context']['depth_complete']:
        reasons.append('PARTIAL_DEPTH')
    if stamp(before['observed_at']) >= stamp(after['observed_at']) or after['repeat_of'] != before['id']:
        reasons.append('INVALID_REPEAT_LINK_OR_TIME')
    if reasons:
        return {'before':before['id'],'after':after['id'],'status':'REVIEW',
                'comparability':'BLOCKED','reasons':sorted(set(reasons)),'movement':[]}
    a, b = position_map(before), position_map(after)
    unresolved_before = any(identity_key(p,before['context']['marketplace']) is None or value(p['position']['basis']) is None for p in before['products'])
    unresolved_after = any(identity_key(p,after['context']['marketplace']) is None or value(p['position']['basis']) is None for p in after['products'])
    movement = []
    for key,basis in sorted(set(a) | set(b)):
        prior, current = a.get((key,basis),[]), b.get((key,basis),[])
        status, presence = U, 'UNKNOWN'
        if not prior:
            status, presence = (U if unresolved_before else 'ENTERED'),'FOUND'
        elif not current:
            status, presence = (U if unresolved_after else 'EXITED_WITHIN_DEPTH'),(U if unresolved_after else 'NOT_FOUND_WITHIN_DEPTH_N')
        elif len(prior) == len(current) == 1:
            p, q = prior[0], current[0]
            identity_fields = ('format','edition','isbn')
            if any(value(p['identity'][f]) != value(q['identity'][f]) and
                   value(p['identity'][f]) is not None and value(q['identity'][f]) is not None for f in identity_fields):
                status = 'IDENTITY_CHANGED'
            else:
                x, y = value(p['position']['rank']),value(q['position']['rank'])
                if x is not None and y is not None:
                    status = 'MOVED_UP' if y < x else 'MOVED_DOWN' if y > x else 'STABLE'
            presence = 'FOUND'
        movement.append({'identity_key':key,'basis':basis,'status':status,'presence':presence,
                         'depth':after['context']['depth_reached'],'before_rank':value(prior[0]['position']['rank']) if len(prior)==1 else None,
                         'after_rank':value(current[0]['position']['rank']) if len(current)==1 else None})
    # Explicit evidence-backed cross-identifier relationships; never infer from titles.
    previous_keys = {key for key,_ in a}
    for product in after['products']:
        relation = value(product['identity']['relationship'])
        key = identity_key(product,after['context']['marketplace'])
        if relation and relation['target_key'] in previous_keys and key and key not in previous_keys:
            movement.append({'identity_key':key,'target_key':relation['target_key'],'status':'IDENTITY_CHANGED',
                             'relationship':relation['kind'],'evidence_ids':product['identity']['relationship']['evidence_ids']})
    unresolved = sum(identity_key(p,after['context']['marketplace']) is None or value(p['position']['basis']) is None for p in after['products'])
    return {'before':before['id'],'after':after['id'],'status':'PASS','comparability':'COMPARABLE',
            'reasons':[],'movement':movement,'unresolved_after_slots':unresolved}


def comparison_rows(rows, cluster_id, origin):
    by_id = {p['id']:p for p,_ in rows}
    pairs = [compare_pair(by_id[p['repeat_of']],p) for p,_ in rows if p['repeat_of'] in by_id]
    return {'schema_version':'external-shelf-comparison/v1','cluster_id':cluster_id,'origin':origin,
            'status':'REVIEW' if any(p['status']=='REVIEW' for p in pairs) else 'PASS',
            'pairs':pairs,'unlinked_snapshots':[p['id'] for p,_ in rows if p['repeat_of'] is None],
            'evidence':[ref for _,ref in rows]}


def compare(root, cluster_id, origin='RETAINED'):
    return comparison_rows(records(root,cluster_id,origin),cluster_id,origin)


def distribution(values):
    return {'observed':len(values),'minimum':min(values) if values else None,
            'maximum':max(values) if values else None,
            'mean':sum(values)/len(values) if values else None}


def concentration(products, group):
    counts = Counter(value(p[group]['key']) for p in products if value(p[group]['key']) is not None)
    known = sum(counts.values()); total = len(products)
    return {'unit':'VISIBLE_CAPTURE_SLOT','observed_slots':known,'unknown_slots':total-known,
            'entities':dict(sorted(counts.items())),
            'largest_share_all_slots':max(counts.values())/total if counts and total else None,
            'largest_share_known_slots':max(counts.values())/known if counts else None,
            'limitations':['Evidence-backed entity keys only; no name-based merge; repeated ad/organic slots counted separately.']}


def snapshot_report(packet, source_ref):
    products = packet['products']; total = len(products)
    marketplace = packet['context']['marketplace']
    keys = [identity_key(p,marketplace) for p in products]
    basis = Counter(value(p['position']['basis']) or U for p in products)
    prices = {}
    for p in products:
        price = value(p['price'])
        if price:
            group = price['currency'] + '/' + (value(p['identity']['format']) or U)
            prices.setdefault(group,[]).append(price['amount'])
    age = {}
    for field in ('publication_date','edition_date'):
        dates = [value(p[field]) for p in products if value(p[field]) is not None]
        days = [(stamp(packet['observed_at']).date()-date.fromisoformat(d)).days for d in dates]
        age[field] = {'observed':len(days),'unknown':total-len(days),'future_dated':sum(d<0 for d in days),
                      'recent_0_90_days':sum(0<=d<=90 for d in days),'age_days':distribution(days)}
    entrants = {'recent_new_titles':[],'recent_new_editions':[],'evidence_backed_cold_start_authors':[]}
    for p in products:
        kind = value(p['release_kind'])
        field = 'publication_date' if kind == 'NEW_TITLE' else 'edition_date'
        d = value(p[field])
        if kind and d and 0 <= (stamp(packet['observed_at']).date()-date.fromisoformat(d)).days <=90:
            entrants['recent_new_titles' if kind=='NEW_TITLE' else 'recent_new_editions'].append(p['slot_id'])
        if value(p['author']['history']) == 'COLD_START':
            entrants['evidence_backed_cold_start_authors'].append(p['slot_id'])
    missing = {field:sum(value(p[field]) is None for p in products) for field in ('price','review_count','rating','bsr','publication_date','edition_date','release_kind')}
    missing.update({'identity':sum(k is None for k in keys),'format':sum(value(p['identity']['format']) is None for p in products),
                    'edition':sum(value(p['identity']['edition']) is None for p in products),'position_rank':sum(value(p['position']['rank']) is None for p in products),
                    'position_basis':basis[U],'author_history':sum(value(p['author']['history']) is None for p in products)})
    return {'snapshot_id':packet['id'],'origin':packet['origin'],'observed_at':packet['observed_at'],
            'context':packet['context'],'counts':{'observed_slots':total,'identified_slots':sum(k is not None for k in keys),
            'unique_product_identities':len({k for k in keys if k}),'unknown_identity_slots':sum(k is None for k in keys),
            'organic_slots':basis['ORGANIC'],'sponsored_slots':basis['SPONSORED'],'unknown_basis_slots':basis[U]},
            'prices':{k:distribution(v) for k,v in sorted(prices.items())},
            'review_counts':distribution([value(p['review_count']) for p in products if value(p['review_count']) is not None]),
            'ratings':distribution([value(p['rating']) for p in products if value(p['rating']) is not None]),
            'age_coverage':age,'concentration':{g:concentration(products,g) for g in ('author','publisher','series')},
            'context_coverage':{'author_history':dict(sorted(Counter(value(p['author']['history']) or U for p in products).items())),'publisher_kind':dict(sorted(Counter(value(p['publisher']['kind']) or U for p in products).items())),'series_kind':dict(sorted(Counter(value(p['series']['kind']) or U for p in products).items())),'format':dict(sorted(Counter(value(p['identity']['format']) or U for p in products).items()))},'entrants':entrants,'critical_missing_fields':missing,'bounded_absences':packet['absences'],
            'provenance':{'snapshot':source_ref,'raw_evidence':packet['evidence'],'stored_raw_evidence':[{'id':e['id'],'path':(Path(source_ref['path']).parent/'raw'/e['sha256']).as_posix(),'sha256':e['sha256']} for e in packet['evidence']],'basis':'All metrics are deterministic reductions of this snapshot only.'},
            'limitations':packet['limitations'] + ['Visible retained shelf only; no sales, revenue, impressions, clicks or conversion inference.']}


def report(root, cluster_id, origin='RETAINED'):
    rows = records(root,cluster_id,origin)
    comparison = comparison_rows(rows,cluster_id,origin)
    return {'schema_version':'external-shelf-report/v1','cluster_id':cluster_id,'origin':origin,
            'synthetic_only':origin=='SYNTHETIC','snapshots':[snapshot_report(p,ref) for p,ref in rows],
            'repeat_observation':comparison,'live_scan':False,'canonical_state_written':False,
            'interop':{'evidence':[ref for _,ref in rows] if origin=='RETAINED' else [],
                      'usage':'Existing Radar evidence {path, sha256}; prospective plan.discovery_route may cite frozen route id. No state import or decision.' if origin=='RETAINED' else 'SYNTHETIC QUARANTINE: no canonical evidence handoff.'}}


def render(result):
    lines = ['# External Shelf Intelligence V1', '', 'Origin: ' + result['origin'],
             'Cluster: ' + result['cluster_id'], '', 'Offline evidence only. Synthetic data is not market evidence.', '']
    if 'snapshots' not in result:
        return json.dumps(result,indent=2,sort_keys=True) + '\n'
    for row in result['snapshots']:
        counts = row['counts']
        lines += ['## ' + row['snapshot_id'], '', 'Observed at: ' + row['observed_at'],
            f"Slots: {counts['observed_slots']}; identified: {counts['identified_slots']}; unknown identity: {counts['unknown_identity_slots']}.",
            f"Organic: {counts['organic_slots']}; sponsored: {counts['sponsored_slots']}; unknown basis: {counts['unknown_basis_slots']}.", '',
            '```json', json.dumps({k:row[k] for k in ('context','prices','review_counts','ratings','age_coverage','concentration','context_coverage','entrants','critical_missing_fields','bounded_absences','provenance','limitations')},indent=2,sort_keys=True), '```', '']
    lines += ['## Repeat observation', '', '```json',json.dumps(result['repeat_observation'],indent=2,sort_keys=True),'```','',
              'No scoring, candidate generation, book modification or live collection.']
    return '\n'.join(lines)+'\n'
