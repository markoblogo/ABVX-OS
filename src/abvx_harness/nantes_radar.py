"""Nantes Radar career adapter: local evidence, drafts and manually recorded outcomes.

Pattern source: ai-job-search-dev/ai-job-search e16acee3 (MIT).
No donor code, agents, permissions, sync or submission tools are executed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone
import fcntl
import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request

from .content_ops import _write_json
from .harness import ValidationError, load_json, now_iso, validate

STATE = Path('opportunities/private/state.json')
LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'native']
EVENTS = {'submitted', 'interview', 'rejected', 'offer', 'hired', 'withdrawn', 'no_response'}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def canonical_url(value):
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValidationError('posting URL must be public HTTP(S), without credentials')
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
             if not k.lower().startswith('utm_') and k.lower() not in {'fbclid', 'gclid'}]
    # Preserve job IDs and application-specific query parameters.
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip('/') or '/', urlencode(sorted(query)), ''))


def plain(value):
    return html.unescape(re.sub('<[^>]*>', ' ', value)).strip()


def norm(value):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', value).casefold()))


def key(job):
    return 'job-' + digest(canonical_url(job['url']))[:20]


def check(root, document, kind):
    path = root / 'schemas/nantes_radar.schema.json'
    schema = load_json(path)
    validate(document, schema['$defs'][kind], schema_path=path, root=root, root_schema=schema)
    if kind == 'profile':
        ids = [f['id'] for f in document['facts']]
        if len(set(ids)) != len(ids):
            raise ValidationError('duplicate candidate fact ID')
    if kind == 'bundle':
        stamp = datetime.fromisoformat(document['captured_at'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValidationError('captured_at requires a timezone')
        for job in document['jobs']:
            canonical_url(job['url'])
            if job.get('deadline'):
                date.fromisoformat(job['deadline'])
            if job.get('work_mode') == 'remote' and not job.get('remote_scope') and not job.get('eligible_countries'):
                # Unknown remote reach remains visible; it is never assumed worldwide.
                job['remote_scope'] = 'UNKNOWN'
    if kind == 'history':
        for record in document['opportunities']:
            observations = record.get('observations', [])
            for observation in observations:
                if observation['source_ref'] not in record['source_refs']:
                    raise ValidationError('observation must bind to a retained source reference')
                if observation.get('occurred_at'):
                    date.fromisoformat(observation['occurred_at'])
            for field in ('owner_decision', 'application_status'):
                if record.get(field, 'UNKNOWN') != 'UNKNOWN' and not any(o['field'] == field and o['source_role'] in {'user', 'tool'} for o in observations):
                    raise ValidationError('assistant suggestions cannot establish owner decisions or application outcomes')
    return document


@contextmanager
def transaction(root):
    path = root / STATE
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_json(path) if path.exists() else {'schema_version': 'v1', 'profiles': {}, 'jobs': {}, 'packets': {}, 'events': [], 'collections': []}
        if state.get('schema_version') != 'v1' or not all(isinstance(state.get(k), dict) for k in ('profiles', 'jobs', 'packets')) or not all(isinstance(state.get(k), list) for k in ('events', 'collections')):
            raise ValidationError('invalid career state; restore a verified local backup')
        yield state
        _write_json(path, state)
        path.chmod(0o600)


def put_profile(root, profile):
    check(root, profile, 'profile')
    with transaction(root) as state:
        state['profiles'][profile['id']] = profile
    return {'profile': profile['id'], 'status': 'SAVED', 'facts': len(profile['facts'])}


def import_jobs(root, bundle):
    check(root, bundle, 'bundle')
    added = updated = 0
    with transaction(root) as state:
        for raw in bundle['jobs']:
            job = dict(raw)
            job['url'] = canonical_url(job['url'])
            job_id = next((i for i, j in state['jobs'].items() if job['url'] in j['urls']), None)
            # Cross-board duplicates need employer + exact title + location + explicit requisition.
            # Without a requisition retain distinct URLs as possible duplicates, never silently merge.
            signature = (norm(job['company']), norm(job['title']), norm(job['location']), job.get('requisition_id'))
            if not job_id and signature[-1]:
                job_id = next((i for i, j in state['jobs'].items() if signature == (norm(j['company']), norm(j['title']), norm(j['location']), j.get('requisition_id'))), None)
            job_id = job_id or key(job)
            old = state['jobs'].get(job_id)
            evidence = {'source': bundle['source'], 'captured_at': bundle['captured_at'], 'url': job['url'], 'record_sha256': digest(raw)}
            if old:
                # Never roll back job detail from an older observation.
                latest = max(datetime.fromisoformat(x['captured_at'].replace('Z', '+00:00')) for x in old['provenance'])
                if datetime.fromisoformat(bundle['captured_at'].replace('Z', '+00:00')) >= latest:
                    old.update(job)
                if job['url'] not in old['urls']:
                    old['urls'].append(job['url'])
                if evidence not in old['provenance']:
                    old['provenance'].append(evidence)
                updated += 1
            else:
                state['jobs'][job_id] = {**job, 'id': job_id, 'urls': [job['url']], 'provenance': [evidence]}
                added += 1
        receipt = {'source': bundle['source'], 'captured_at': bundle['captured_at'], 'status': 'SUCCESS' if bundle['jobs'] else 'NO_RESULT', 'added': added, 'updated': updated, 'bundle_sha256': digest(bundle)}
        if receipt not in state['collections']:
            state['collections'].append(receipt)
    return receipt


def location_gate(job):
    countries = job.get('eligible_countries', [])
    if countries:
        return 'PASS' if 'FR' in countries else 'FAIL'
    if job['work_mode'] != 'remote':
        return 'PASS' if job.get('country') == 'FR' else 'FAIL' if job.get('country') not in {None, 'UNKNOWN'} else 'REVIEW'
    scope = norm(job.get('remote_scope', 'UNKNOWN'))
    if scope in {'worldwide', 'anywhere', 'global', 'france', 'europe', 'eu', 'emea'}:
        return 'PASS'
    return 'FAIL' if scope in {'usa', 'us', 'united states', 'usa only', 'united states only', 'canada', 'uk only', 'united kingdom only'} else 'REVIEW'


def evaluate(job, profile, as_of):
    flags = []
    location = location_gate(job)
    if location != 'PASS':
        flags.append('Location/France remote access: ' + location)
    if job['work_mode'] != 'remote' and norm(job['location']) != norm(profile['location']):
        flags.append('Commute/relocation requires review')
    language = 'PASS' if job.get('required_languages') else 'REVIEW'
    for lang, required in job.get('required_languages', {}).items():
        actual = profile['languages'].get(lang)
        if actual is None or required not in LEVELS or actual not in LEVELS or LEVELS.index(actual) < LEVELS.index(required):
            language = 'REVIEW'
            flags.append(f'Language {lang}: requires {required}; candidate {actual or "UNKNOWN"}')
    rights = 'FAIL' if job.get('eligibility') == 'FAIL' or profile.get('work_eligibility') == 'FAIL' else 'UNKNOWN'
    if job.get('eligibility') == 'PASS' and profile.get('work_eligibility') == 'PASS':
        rights = 'PASS'
    if rights != 'PASS':
        flags.append('Work/contract eligibility: ' + rights)
    if not job.get('description'):
        flags.append('Posting body missing; draft blocked')
    if not job.get('required_languages'):
        flags.append('Working language requirements UNKNOWN')
    if job.get('posted_at'):
        try:
            age = (date.fromisoformat(as_of) - date.fromisoformat(job['posted_at'][:10])).days
            if age > 30: flags.append(f'Posting age {age} days; recheck availability')
        except ValueError:
            flags.append('Posting date unparseable; freshness UNKNOWN')
    status = 'expired' if job.get('deadline') and job['deadline'] < as_of else job.get('status', 'open')
    text = norm(job['title'] + ' ' + job.get('description', '') + ' ' + ' '.join(job.get('tags', [])))
    skills = [s for s in profile['skills'] if re.search(r'(?<!\w)' + re.escape(norm(s)) + r'(?!\w)', text)]
    roles = [r for r in profile['roles'] if norm(r) in norm(job['title'])]
    # Deterministic relevance only; do not invent behavioral or experience percentages.
    score = min(80, len(skills) * 20) + (20 if roles else 0) if job.get('description') else None
    possible = location != 'FAIL' and rights != 'FAIL' and status == 'open'
    return {'id': job['id'], 'company': job['company'], 'title': job['title'], 'url': job['url'], 'source': job['provenance'][-1]['source'], 'score': score, 'score_kind': 'keyword-triage-v1', 'matched_skills': skills, 'location_gate': location, 'language_gate': language, 'eligibility_gate': rights, 'status': status, 'shortlist': possible and score is not None and score >= 40, 'flags': flags}


def ranking(root, profile_id, as_of=None):
    as_of = as_of or date.today().isoformat()
    date.fromisoformat(as_of)
    state = load_json(root / STATE)
    profile = state['profiles'][profile_id]
    rows = [evaluate(j, profile, as_of) for j in state['jobs'].values()]
    for row in rows:
        job = state['jobs'][row['id']]
        row['possible_duplicates'] = [j['id'] for j in state['jobs'].values() if j['id'] != job['id'] and norm(j['company']) == norm(job['company']) and norm(j['title']) == norm(job['title'])]
        row['application_events'] = [e for e in state['events'] if e['job_id'] == row['id'] and e['profile_id'] == profile_id]
        if row['application_events']:
            row['shortlist'] = False
    return sorted(rows, key=lambda r: (not r['shortlist'], -(r['score'] or 0), r['id']))


def bound_snapshot(state, packet):
    return digest({'job': state['jobs'][packet['job_id']], 'profile': state['profiles'][packet['profile_id']]})


def make_draft(root, job_id, profile_id, language='en'):
    with transaction(root) as state:
        job, profile = state['jobs'][job_id], state['profiles'][profile_id]
        assessment = evaluate(job, profile, date.today().isoformat())
        if not job.get('description') or assessment['status'] != 'open' or assessment['location_gate'] == 'FAIL' or assessment['eligibility_gate'] == 'FAIL':
            raise ValidationError('draft blocked: missing posting, closed job, location or eligibility failure')
        facts = [f for f in profile['facts'] if f['confirmed'] and f['language'] == language]
        if not facts:
            raise ValidationError('no confirmed candidate facts in requested language; do not invent translations')
        selected = [f for f in facts if set(map(norm, f['tags'])) & set(map(norm, assessment['matched_skills']))] or facts
        selected = selected[:8]
        body = '\n'.join('- ' + f['text'] for f in selected)
        labels = {'en': ('DRAFT — MANUAL REVIEW REQUIRED', 'Selected experience', 'Dear hiring team,', 'I am interested in the role below. Relevant experience from my existing profile:', 'I would welcome a discussion of the requirements and mutual fit.', 'Kind regards,'), 'fr': ('BROUILLON — VALIDATION MANUELLE REQUISE', 'Expérience sélectionnée', 'Madame, Monsieur,', 'Je vous présente ma candidature au poste ci-dessous. Expérience pertinente issue de mon profil :', 'Je serais heureux de discuter des exigences du poste et de notre adéquation.', 'Cordialement,')}[language]
        header, experience, hello, opening, closing, bye = labels
        cv = f'# {profile["name"]}\n\n{header}\n\n{profile["location"]}\n\n## {experience}\n\n{body}\n\nLanguages (declared): {json.dumps(profile["languages"], ensure_ascii=False)}\n'
        letter = f'{header}\n\n{hello}\n\n{opening}\n\n{job["title"]} — {job["company"]}\n\n{body}\n\n{closing}\n\n{bye}\n{profile["name"]}\n'
        packet = {'job_id': job_id, 'profile_id': profile_id, 'language': language, 'fact_ids': [f['id'] for f in selected], 'source_refs': sorted({f['source_ref'] for f in selected}), 'posting_url': job['url'], 'flags': assessment['flags'], 'cv': cv, 'letter': letter}
        packet['snapshot'] = bound_snapshot(state, packet)
        packet['digest'] = digest(packet)
        packet['id'] = 'draft-' + packet['digest'][:20]
        packet['decision'] = 'PENDING'
        state['packets'].setdefault(packet['id'], packet)
        return state['packets'][packet['id']]


def verify_packet(state, packet):
    payload = {k: v for k, v in packet.items() if k not in {'id', 'digest', 'decision', 'review'}}
    if digest(payload) != packet['digest'] or bound_snapshot(state, packet) != packet['snapshot']:
        raise ValidationError('draft/profile/posting changed; regenerate and review exact new digest')


def review(root, packet_id, decision, reviewer, expected_digest):
    if not reviewer.strip():
        raise ValidationError('human reviewer name required')
    with transaction(root) as state:
        packet = state['packets'][packet_id]
        verify_packet(state, packet)
        if decision not in {'APPROVED', 'REJECTED'}:
            raise ValidationError('unsupported review decision')
        if decision == 'APPROVED':
            assessed = evaluate(state['jobs'][packet['job_id']], state['profiles'][packet['profile_id']], date.today().isoformat())
            if assessed['status'] != 'open' or assessed['location_gate'] == 'FAIL' or assessed['eligibility_gate'] == 'FAIL':
                raise ValidationError('approval blocked by current vacancy gates')
        if packet['digest'] != expected_digest:
            raise ValidationError('review digest differs from displayed draft')
        packet['decision'] = decision
        packet['review'] = {'reviewer': reviewer, 'at': now_iso(), 'digest': expected_digest}
        return {'id': packet_id, 'decision': decision, 'external_action': 'NONE'}


def record_event(root, job_id, profile_id, event, evidence, occurred_at, packet_id=None):
    if event not in EVENTS or not evidence.strip():
        raise ValidationError('supported outcome and human evidence are required')
    date.fromisoformat(occurred_at)
    if occurred_at > date.today().isoformat():
        raise ValidationError('cannot record a future completed outcome')
    with transaction(root) as state:
        if job_id not in state['jobs'] or profile_id not in state['profiles']:
            raise ValidationError('unknown job/profile')
        history = [e for e in state['events'] if e['job_id'] == job_id and e['profile_id'] == profile_id]
        if event == 'submitted':
            if not packet_id:
                raise ValidationError('submitted requires the reviewed packet ID')
            packet = state['packets'][packet_id]
            verify_packet(state, packet)
            if packet['job_id'] != job_id or packet['profile_id'] != profile_id or packet['decision'] != 'APPROVED':
                raise ValidationError('submitted requires an APPROVED matching packet; no send action exists')
        elif not any(e['event'] == 'submitted' for e in history):
            raise ValidationError('record the actual prior submission before its outcome')
        record = {'job_id': job_id, 'profile_id': profile_id, 'event': event, 'evidence': evidence, 'occurred_at': occurred_at, 'packet_id': packet_id, 'recorded_at': now_iso(), 'origin': 'human-recorded'}
        identity = {k: v for k, v in record.items() if k != 'recorded_at'}
        if not any({k: v for k, v in e.items() if k != 'recorded_at'} == identity for e in history):
            state['events'].append(record)
        return record


def import_history(root, bundle):
    check(root, bundle, 'history')
    with transaction(root) as state:
        entries = state.setdefault('opportunities', [])
        history = state.setdefault('history', [])
        for record in bundle['opportunities']:
            if record.get('linked_job_id') and record['linked_job_id'] not in state['jobs']:
                raise ValidationError('historical link references an unknown vacancy')
            existing = next((x for x in entries if x['id'] == record['id']), None)
            if existing and existing != record:
                raise ValidationError('historical opportunity ID conflict; retain original and reconcile explicitly')
            if not existing:
                entries.append(record)
        for record in bundle['events']:
            if record['opportunity_id'] not in {x['id'] for x in entries}:
                raise ValidationError('historical event references an unknown opportunity')
            if record.get('occurred_at'):
                date.fromisoformat(record['occurred_at'])
            entry = {**record, 'origin': 'historical-import', 'verification': 'NOT_INDEPENDENTLY_VERIFIED'}
            if entry not in history:
                history.append(entry)
        return {'opportunities': len(entries), 'historical_events': len(history), 'external_actions': 'NONE'}


def reconcile_history(root, bundle, expected_digest):
    """Explicit source-backed reconciliation; retain previous records and fail stale writers."""
    check(root, bundle, 'history')
    with transaction(root) as state:
        entries = state.setdefault('opportunities', [])
        if digest(entries) != expected_digest:
            raise ValidationError('catalog changed; inspect current opportunities_digest before reconciliation')
        index = {x['id']: n for n, x in enumerate(entries)}
        changed = 0
        for record in bundle['opportunities']:
            if record['id'] not in index:
                raise ValidationError('reconciliation updates existing IDs; import new history separately')
            previous = entries[index[record['id']]]
            if not set(previous['source_refs']) <= set(record['source_refs']):
                raise ValidationError('reconciliation must preserve all prior source references')
            if record.get('linked_job_id') and record['linked_job_id'] not in state['jobs']:
                raise ValidationError('unknown linked vacancy')
            if record != previous:
                state['history'].append({'opportunity_id': record['id'], 'status': record['status'], 'occurred_at': None, 'recorded_at': now_iso(), 'origin': 'historical-reconciliation', 'previous_record': previous, 'source_refs': record['source_refs'], 'notes': 'Source-backed enrichment; no external action or new owner decision implied.'})
                entries[index[record['id']]] = record
                changed += 1
        for record in bundle['events']:
            if record['opportunity_id'] not in index:
                raise ValidationError('historical event references an unknown opportunity')
            if record.get('occurred_at'):
                date.fromisoformat(record['occurred_at'])
            entry = {**record, 'origin': 'historical-import', 'verification': 'NOT_INDEPENDENTLY_VERIFIED'}
            if entry not in state['history']:
                state['history'].append(entry)
        return {'reconciled': changed, 'opportunities': len(entries), 'history_records': len(state['history']), 'opportunities_digest': digest(entries), 'external_actions': 'NONE'}


def decide(root, opportunity_id, status, reason, source_ref):
    if not all(x.strip() for x in (status, reason, source_ref)):
        raise ValidationError('decision needs status, reason and human/source reference')
    with transaction(root) as state:
        record = next((x for x in state.get('opportunities', []) if x['id'] == opportunity_id), None)
        if record is None:
            raise ValidationError('unknown catalog opportunity')
        state.setdefault('history', []).append({'opportunity_id': opportunity_id, 'status': status, 'previous_status': record['status'], 'occurred_at': date.today().isoformat(), 'recorded_at': now_iso(), 'source_refs': [source_ref], 'notes': reason, 'origin': 'human-decision'})
        record['status'] = status
        return {'id': opportunity_id, 'status': status, 'external_action': 'NONE'}


def link(root, opportunity_id, job_id, source_ref):
    if not source_ref.strip():
        raise ValidationError('human reconciliation source required')
    with transaction(root) as state:
        entry = next((x for x in state.get('opportunities', []) if x['id'] == opportunity_id), None)
        if entry is None or job_id not in state['jobs']:
            raise ValidationError('unknown historical opportunity or vacancy')
        if entry.get('linked_job_id') not in {None, job_id}:
            raise ValidationError('opportunity already linked to another vacancy; reconcile first')
        if entry.get('linked_job_id') != job_id:
            state.setdefault('history', []).append({'opportunity_id': opportunity_id, 'linked_job_id': job_id, 'source_refs': [source_ref], 'recorded_at': now_iso(), 'origin': 'human-link'})
            entry['linked_job_id'] = job_id
        return {'id': opportunity_id, 'linked_job_id': job_id, 'external_action': 'NONE'}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValidationError('remote feed redirected; review provider endpoint before retry')


def search(root, query, limit=20):
    if not query.strip() or not 1 <= limit <= 100:
        raise ValidationError('search needs a query and limit 1..100')
    # Six-hour cache caps calls at four per day across all queries (provider guidance).
    cache = root / '.tmp/opportunities/remotive-cache.json'
    with transaction(root) as state:
        cached = load_json(cache) if cache.exists() else None
        stamp = datetime.now(timezone.utc)
        if not cached or (stamp - datetime.fromisoformat(cached['fetched_at'].replace('Z', '+00:00'))).total_seconds() >= 21600:
            url = 'https://remotive.com/api/remote-jobs'
            try:
                with build_opener(NoRedirect).open(Request(url, headers={'User-Agent': 'ABVX-OS Nantes Radar personal research'}), timeout=25) as response:
                    raw = response.read(10_000_001)
                if len(raw) > 10_000_000:
                    raise ValidationError('remote feed exceeds 10 MB limit')
                payload = json.loads(raw)
                if not isinstance(payload, dict) or not isinstance(payload.get('jobs'), list):
                    raise ValidationError('provider response has no jobs array')
                cached = {'fetched_at': now_iso(), 'jobs': payload['jobs']}
                _write_json(cache, cached)
                cache.chmod(0o600)
            except (OSError, ValueError, ValidationError) as exc:
                state['collections'].append({'source': 'Remotive', 'captured_at': now_iso(), 'status': 'COLLECTION_FAILED', 'error': str(exc)[:300]})
                cached = {'error': str(exc)}
    if 'error' in cached:
        raise ValidationError('Remotive collection failed; no-result was not inferred: ' + cached['error'])
    jobs = []
    for item in cached['jobs']:
        if norm(query) not in norm(item['title'] + ' ' + plain(item.get('description', ''))):
            continue
        scope = item.get('candidate_required_location') or 'UNKNOWN'
        job = {'title': item['title'], 'company': item['company_name'], 'url': item['url'], 'location': scope, 'country': 'UNKNOWN', 'work_mode': 'remote', 'remote_scope': scope, 'description': plain(item.get('description', '')), 'tags': item.get('tags', []), 'eligibility': 'UNKNOWN', 'status': 'open', 'posted_at': item.get('publication_date')}
        if location_gate(job) != 'FAIL':
            jobs.append(job)
        if len(jobs) >= limit:
            break
    bundle = {'schema_version': 'v1', 'source': 'Remotive', 'captured_at': cached['fetched_at'], 'jobs': jobs}
    return import_jobs(root, bundle)


def search_plan(root, profile_id):
    state = load_json(root / STATE)
    roles = state['profiles'][profile_id]['roles']
    return {'mode': 'read-only browser research then import', 'queries': [{'role': role, 'france_query': role + ' Nantes France télétravail', 'remote_query': role + ' remote France Europe', 'sources': ['https://candidat.francetravail.fr/offres/recherche', 'https://www.apec.fr/candidat/recherche-emploi.html/emploi', 'https://www.welcometothejungle.com/fr/jobs']} for role in roles], 'remote_command': './bin/abvx career search --query marketing --limit 20', 'import_contract': 'schemas/nantes_radar.schema.json#/$defs/bundle'}


def context_pack(root):
    """Bounded manual bridge to the one ChatGPT review; omit CVs, contacts and draft text."""
    state = load_json(root / STATE)
    fields = ('id', 'name', 'kind', 'status', 'application_status', 'owner_decision', 'next_action', 'blockers', 'source_refs', 'url')
    return {'schema_version': 'v1', 'generated_at': now_iso(), 'primary_chat': 'https://chatgpt.com/c/6ac8a06b-fae0-83ed-b55e-fd23524d85f9', 'local_sync': ('REMOTE_DEVICE_SYNC_CONFIGURED' if (root / 'opportunities/private/sync-config.json').is_file() and load_json(root / 'opportunities/private/sync-config.json').get('enabled') else 'MANUAL_EXPORT_ONLY'), 'catalog_digest': digest(state.get('opportunities', [])), 'opportunities': [{k: v for k, v in x.items() if k in fields} for x in state.get('opportunities', [])], 'local_vacancies': [{k: j[k] for k in ('id', 'title', 'company', 'url')} for j in state['jobs'].values()], 'historical_claims_are_current_verification': False, 'external_actions': 'NONE'}


def main(argv, root):
    parser = argparse.ArgumentParser(prog='abvx opportunities', description='Nantes Radar: private local research, drafts and outcomes. No sending or account sync.')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('catalog')
    sub.add_parser('context-pack')
    sub.add_parser('sync-read')
    p = sub.add_parser('sync-apply'); p.add_argument('--file', required=True)
    p = sub.add_parser('link'); p.add_argument('--id', required=True); p.add_argument('--job', required=True); p.add_argument('--source', required=True)
    p = sub.add_parser('decide'); p.add_argument('--id', required=True); p.add_argument('--status', required=True); p.add_argument('--reason', required=True); p.add_argument('--source', required=True)
    p = sub.add_parser('import-history'); p.add_argument('--file', required=True)
    p = sub.add_parser('reconcile-history'); p.add_argument('--file', required=True); p.add_argument('--expected-digest', required=True)
    for action in ('profile', 'import'):
        p = sub.add_parser(action); p.add_argument('--file', required=True)
    p = sub.add_parser('search'); p.add_argument('--query', required=True); p.add_argument('--limit', type=int, default=20)
    for action in ('plan', 'rank', 'report'):
        p = sub.add_parser(action); p.add_argument('--profile', required=True)
        if action != 'plan': p.add_argument('--as-of')
    p = sub.add_parser('draft'); p.add_argument('--job', required=True); p.add_argument('--profile', required=True); p.add_argument('--language', choices=['en', 'fr'], default='en')
    p = sub.add_parser('packet'); p.add_argument('--id', required=True)
    p = sub.add_parser('review'); p.add_argument('--id', required=True); p.add_argument('--decision', choices=['APPROVED', 'REJECTED'], required=True); p.add_argument('--reviewer', required=True); p.add_argument('--digest', required=True)
    p = sub.add_parser('track'); p.add_argument('--job', required=True); p.add_argument('--profile', required=True); p.add_argument('--event', choices=sorted(EVENTS), required=True); p.add_argument('--evidence', required=True); p.add_argument('--date', required=True); p.add_argument('--packet')
    args = parser.parse_args(argv)
    if args.action in {'sync-read', 'sync-apply'}:
        from . import opportunity_sync
        result = opportunity_sync.read(root) if args.action == 'sync-read' else opportunity_sync.apply(root, load_json(Path(args.file)))
    elif args.action == 'context-pack':
        result = context_pack(root)
    elif args.action == 'link':
        result = link(root, args.id, args.job, args.source)
    elif args.action == 'decide':
        result = decide(root, args.id, args.status, args.reason, args.source)
    elif args.action == 'catalog':
        state = load_json(root / STATE)
        result = {'opportunities': state.get('opportunities', []), 'opportunities_digest': digest(state.get('opportunities', [])), 'vacancies': list(state['jobs'].values()), 'history': state.get('history', []), 'profiles': list(state['profiles']), 'state': str(root / STATE), 'source_system': 'Nantes Radar / ABVX OS', 'notifications': 'NONE'}
    elif args.action == 'reconcile-history':
        result = reconcile_history(root, load_json(Path(args.file)), args.expected_digest)
    elif args.action == 'import-history':
        result = import_history(root, load_json(Path(args.file)))
    elif args.action in {'profile', 'import'}:
        document = load_json(Path(args.file))
        result = put_profile(root, document) if args.action == 'profile' else import_jobs(root, document)
    elif args.action == 'search': result = search(root, args.query, args.limit)
    elif args.action == 'plan': result = search_plan(root, args.profile)
    elif args.action in {'rank', 'report'}:
        rows = ranking(root, args.profile, args.as_of)
        result = rows if args.action == 'rank' else {'profile': args.profile, 'jobs': rows, 'collections': load_json(root / STATE)['collections'], 'external_actions': 'NONE', 'outcomes': 'human-recorded evidence, not verified delivery'}
    elif args.action == 'draft': result = make_draft(root, args.job, args.profile, args.language)
    elif args.action == 'packet': result = load_json(root / STATE)['packets'][args.id]
    elif args.action == 'review': result = review(root, args.id, args.decision, args.reviewer, args.digest)
    else: result = record_event(root, args.job, args.profile, args.event, args.evidence, args.date, args.packet)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
