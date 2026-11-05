"""Read-only YouTube intelligence. No upload, edit, or monetization operations.

Acquisition is deterministic; external research is an explicitly sourced input.
Private observations live in ignored local state, never in the public registry.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import time

from .process_learning import digest, _write_once
from .schema_validation import load_draft_2020_12_validator

REPO = Path(__file__).resolve().parents[2]
DEFAULT = REPO / '.tmp/youtube-intelligence'
METHOD = 'youtube-intelligence/v1'
BASE_METRICS = 'views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost'
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly',
          'https://www.googleapis.com/auth/yt-analytics.readonly']
MONETARY = 'https://www.googleapis.com/auth/yt-analytics-monetary.readonly'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def stamp():
    return datetime.now(timezone.utc).isoformat()


def validate(kind, value):
    load_draft_2020_12_validator(REPO / 'schemas/youtube_intelligence.schema.json').evolve(
        schema={'$ref': '#/$defs/' + kind,
                '$defs': read(REPO / 'schemas/youtube_intelligence.schema.json')['$defs']}).validate(value)
    return value


def config():
    return validate('config', read(REPO / 'config/youtube-intelligence-v1.json'))


def safe_id(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
        raise ValueError('Use a short filesystem-safe ID')
    return value


@contextmanager
def lock(root):
    root.mkdir(parents=True, exist_ok=True)
    path = root / 'writer.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Another writer or interrupted run holds writer.lock; inspect before recovery') from None
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(str(os.getpid()))
        yield
    finally:
        path.unlink()


def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f)
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def authenticate(root, monetary=False, open_browser=False):
    """Interactive loopback OAuth; caller opens the saved authorization URL."""
    client = root / 'credentials/client.json'
    if not client.is_file():
        raise ValueError('OAUTH_CLIENT_REQUIRED: save a Desktop OAuth client to credentials/client.json')
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ValueError('GOOGLE_DEPENDENCIES_REQUIRED: install requirements-youtube.txt in the optional runtime') from None
    data = read(client)
    if 'installed' not in data:
        raise ValueError('A Desktop OAuth client is required; do not reuse a web client')
    os.chmod(client, 0o600)
    flow = InstalledAppFlow.from_client_config(data, SCOPES + ([MONETARY] if monetary else []))
    # The URL contains no client secret. Keep state-bearing URL in a private file.
    url_path = root / 'credentials/authorization-url.txt'
    def url_sink(url):
        url_path.write_text(url, encoding='utf-8')
        os.chmod(url_path, 0o600)
        return ''
    class Prompt:
        def format(self, **kwargs):
            return url_sink(kwargs['url'])
    root.joinpath('credentials').mkdir(parents=True, exist_ok=True, mode=0o700)
    print('Awaiting Google consent; open credentials/authorization-url.txt in the authorized browser.', flush=True)
    try:
        credentials = flow.run_local_server(host='127.0.0.1', port=0, open_browser=open_browser,
            authorization_prompt_message=Prompt(), timeout_seconds=300,
            success_message='Authorization received. You may close this tab.',
            access_type='offline', prompt='consent')
        private_json(root / 'credentials/token.json', json.loads(credentials.to_json()))
    finally:
        url_path.unlink(missing_ok=True)
    return {'status': 'AUTHORIZED', 'channel_verification': 'PENDING_LIVE_RUN'}


class Google:
    """Only allow-listed read operations, bounded calls/time, sanitized failures."""
    def __init__(self, root, cfg):
        path = root / 'credentials/token.json'
        if not path.is_file():
            raise ValueError('AUTH_REQUIRED: run youtube auth with a Desktop OAuth client')
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            raise ValueError('GOOGLE_DEPENDENCIES_REQUIRED: install requirements-youtube.txt in the optional runtime') from None
        os.chmod(path, 0o600)
        self.credentials = Credentials.from_authorized_user_file(str(path))
        if not self.credentials.has_scopes(SCOPES):
            raise ValueError('AUTH_REQUIRED: both YouTube metadata and Analytics read-only scopes are required')
        if not self.credentials.valid:
            if not self.credentials.refresh_token:
                raise ValueError('AUTH_REQUIRED: missing refresh token')
            try:
                self.credentials.refresh(Request())
            except Exception:
                raise ValueError('AUTH_REFRESH_FAILED: reconnect Google OAuth; no credential details logged') from None
            private_json(path, json.loads(self.credentials.to_json()))
        self.data = build('youtube', 'v3', credentials=self.credentials, cache_discovery=False)
        self.analytics = build('youtubeAnalytics', 'v2', credentials=self.credentials, cache_discovery=False)
        self.cfg, self.calls, self.started = cfg, 0, time.monotonic()

    def call(self, resource, **parameters):
        allowed = {'channels': self.data.channels().list,
                   'playlistItems': self.data.playlistItems().list,
                   'videos': self.data.videos().list,
                   'analytics': self.analytics.reports().query}
        if resource not in allowed:
            raise ValueError('Read operation not allowed')
        if self.calls >= self.cfg['max_api_calls'] or time.monotonic() - self.started > self.cfg['acquisition_seconds']:
            raise ValueError('ACQUISITION_BUDGET_EXHAUSTED')
        self.calls += 1
        try:
            # Fixed timeout prevents a single request defeating the acquisition budget.
            request = allowed[resource](**parameters)
            request.http.timeout = 30
            return request.execute(num_retries=0)
        except Exception as error:
            status = getattr(getattr(error, 'resp', None), 'status', None)
            raise ValueError(f'GOOGLE_READ_FAILED: {resource}; HTTP {status or "UNKNOWN"}; no response body logged') from None


def table(response):
    names = [h['name'] for h in response.get('columnHeaders', [])]
    rows = response.get('rows', [])
    if rows and (not names or any(len(r) != len(names) for r in rows)):
        raise ValueError('Malformed Analytics table')
    return [dict(zip(names, row)) for row in rows]


def interval(end, days):
    return {'start': (end - timedelta(days=days - 1)).isoformat(), 'end': end.isoformat()}


def acquire(api, cfg, end, as_of, tracked_ids=(), checkpoint=None):
    identity = api.call('channels', part='id,contentDetails', mine=True)
    own = [c for c in identity.get('items', []) if c['id'] == cfg['channel_id']]
    if len(own) != 1:
        raise ValueError('CHANNEL_ID_MISMATCH: authorize the configured channel, not another account')
    playlist = own[0]['contentDetails']['relatedPlaylists']['uploads']
    ids, token, seen = [], None, set()
    while True:
        params = dict(part='contentDetails', playlistId=playlist, maxResults=50)
        if token:
            params['pageToken'] = token
        page = api.call('playlistItems', **params)
        ids.extend(i['contentDetails']['videoId'] for i in page.get('items', []))
        token = page.get('nextPageToken')
        if not token:
            break
        if token in seen:
            raise ValueError('Repeated uploads page token')
        seen.add(token)
    ids = list(dict.fromkeys(ids))
    catalog = []
    for i in range(0, len(ids), 50):
        page = api.call('videos', part='snippet,contentDetails,status,statistics', id=','.join(ids[i:i+50]), maxResults=50)
        for v in page.get('items', []):
            snippet = v['snippet']
            eligible = (v['status'].get('privacyStatus') == 'public'
                        and snippet.get('liveBroadcastContent') == 'none'
                        and datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')) <= as_of)
            catalog.append({'video_id': v['id'], 'title': snippet['title'],
                'published_at': snippet['publishedAt'], 'duration': v['contentDetails']['duration'],
                'eligible': eligible, 'statistics_current': v.get('statistics', {})})
    if set(ids) - {v['video_id'] for v in catalog}:
        # Deleted/inaccessible playlist items are explicitly retained, never invented as uploads.
        missing = sorted(set(ids) - {v['video_id'] for v in catalog})
    else:
        missing = []
    reports = []
    def progress():
        if checkpoint:
            checkpoint({'catalog': catalog, 'unavailable_playlist_ids': missing, 'reports': reports,
                        'revenue': {'availability': 'ACQUISITION_IN_PROGRESS'}, 'api_calls': api.calls, 'discovery': 'COMPLETE', 'status': 'IN_PROGRESS'})
    progress()
    def query(label, period, **params):
        result = api.call('analytics', ids='channel==' + cfg['channel_id'],
            startDate=period['start'], endDate=period['end'], **params)
        reports.append({'label': label, 'requested_period': period, 'parameters': params,
                        'rows': table(result), 'response': result,
                        'availability': 'REPORTED' if result.get('rows') else 'NO_REPORTED_ROWS'})
        if len(reports) % 10 == 0 or label == 'revenue_28d':
            progress()
    for days in [7, 28]:
        period = interval(end, days)
        query(f'channel_{days}d', period, dimensions='day', metrics=BASE_METRICS, sort='day')
        eligible = [v['video_id'] for v in catalog if v['eligible']]
        for i in range(0, len(eligible), 25):
            query(f'videos_{days}d', period, dimensions='video,creatorContentType',
                  filters='video==' + ','.join(eligible[i:i+25]), metrics=BASE_METRICS,
                  maxResults=200, sort='-views')
    query('traffic_28d', interval(end, 28), dimensions='insightTrafficSourceType',
          metrics='views,estimatedMinutesWatched')
    query('format_28d', interval(end, 28), dimensions='creatorContentType', metrics=BASE_METRICS)
    # Calendar-day windows for every recent eligible upload, including spontaneous uploads.
    for v in catalog:
        published = datetime.fromisoformat(v['published_at'].replace('Z', '+00:00'))
        # YouTube report days follow America/Los_Angeles, independently of scheduler timezone.
        from zoneinfo import ZoneInfo
        start = published.astimezone(ZoneInfo('America/Los_Angeles')).date()
        if not v['eligible'] or ((end - start).days > cfg['recent_upload_days'] and v['video_id'] not in tracked_ids):
            continue
        for days in [2, 7, 28]:
            finish = start + timedelta(days=days-1)
            if finish <= end:
                query(f'age_{days}d:{v["video_id"]}', {'start': str(start), 'end': str(finish)},
                      dimensions='day', filters='video==' + v['video_id'], metrics=BASE_METRICS, sort='day')
    money = {'availability': 'SCOPE_NOT_GRANTED'}
    if api.credentials.has_scopes([MONETARY]):
        try:
            query('revenue_28d', interval(end, 28), dimensions='day',
                  metrics='estimatedRevenue,estimatedAdRevenue', currency='EUR', sort='day')
            money = {'availability': reports[-1]['availability'], 'supplement_failures': []}
            def supplement(label, period, **params):
                try:
                    query(label, period, **params)
                except ValueError as error:
                    money['supplement_failures'].append({'label': label, 'reason': str(error).split(':')[0]})
            eligible = [v['video_id'] for v in catalog if v['eligible']]
            for i in range(0, len(eligible), 150):
                supplement('video_revenue_28d', interval(end, 28), dimensions='video',
                           filters='video==' + ','.join(eligible[i:i+150]),
                           metrics='estimatedRevenue,estimatedAdRevenue', currency='EUR', maxResults=200, sort='-estimatedRevenue')
            ranked = sorted([row for report in reports if report['label'] == 'video_revenue_28d'
                             for row in report['rows']], key=lambda row: row.get('estimatedRevenue', 0), reverse=True)
            geo_focus = set(tracked_ids) | {row['video'] for row in ranked[:5]}
            recent = [v['video_id'] for v in catalog if v['eligible'] and
                      (end - datetime.fromisoformat(v['published_at'].replace('Z', '+00:00')).date()).days <= cfg['recent_upload_days']]
            focus = list(dict.fromkeys(list(tracked_ids) + recent + [row['video'] for row in ranked[:5]]))
            from zoneinfo import ZoneInfo
            for vid in focus:
                video = next((v for v in catalog if v['video_id'] == vid and v['eligible']), None)
                if not video:
                    continue
                start = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00')).astimezone(ZoneInfo('America/Los_Angeles')).date()
                for days in (7, 28):
                    finish = start + timedelta(days=days-1)
                    if finish <= end:
                        supplement(f'revenue_age_{days}d:{vid}', {'start': str(start), 'end': str(finish)},
                                   dimensions='day', filters='video==' + vid, metrics='estimatedRevenue', currency='EUR', sort='day')
                for label, dimension in ([('country', 'country'), ('traffic', 'insightTrafficSourceType')] if vid in geo_focus else []):
                    supplement(f'{label}_28d:{vid}', interval(end, 28), dimensions=dimension,
                               filters='video==' + vid, metrics='views,estimatedMinutesWatched', maxResults=200)
            money['supplement_scope'] = {'video_revenue': 'ALL_ELIGIBLE_BATCHED',
                'age_revenue': 'ALL_RECENT_PLUS_TRACKED_PLUS_TOP_5',
                'geography_traffic': 'TRACKED_PLUS_TOP_5_REVENUE', 'focus_ids': focus}
        except ValueError as error:
            money = {'availability': 'UNAVAILABLE', 'reason': str(error)}
    return {'catalog': catalog, 'unavailable_playlist_ids': missing, 'reports': reports,
            'revenue': money, 'api_calls': api.calls, 'discovery': 'COMPLETE'}


def events(root):
    return [read(p) for p in sorted((root / 'events').glob('*.json'))]


def event(root, item):
    validate('event', item)
    item = dict(item, recorded_at=stamp())
    key = digest({k: v for k, v in item.items() if k != 'recorded_at'})
    path = root / 'events' / (key + '.json')
    if path.exists():
        return read(path)
    _write_once(path, item)
    return item


def experiments(root):
    return {p.stem: validate('experiment', read(p)) for p in (root / 'experiments').glob('*.json')}


def register(root, item, clock=None):
    validate('experiment', item)
    clock = clock or datetime.now(timezone.utc)
    created = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
    if created > clock:
        raise ValueError('Future experiment creation time')
    # Registration time, not a caller supplied timestamp, proves prospective ordering.
    stored = dict(item, registered_at=clock.isoformat())
    with lock(root):
        _write_once(root / 'experiments' / (safe_id(item['id']) + '.json'), stored)
    return stored


def change(root, item):
    validate('event', item)
    exps = experiments(root)
    if item['experiment_id'] not in exps:
        raise ValueError('Unknown experiment')
    history = [e for e in events(root) if e['experiment_id'] == item['experiment_id']]
    ex = exps[item['experiment_id']]
    kind = item['type']
    if kind == 'APPROVED' and any(e['type'] in {'PUBLISHED', 'CANCELLED'} for e in history):
        raise ValueError('Cannot approve terminal or already published experiment')
    if kind == 'PUBLISHED':
        if not any(e['type'] == 'APPROVED' for e in history) or any(e['type'] == 'CANCELLED' for e in history):
            raise ValueError('Publication binding requires prior approval')
        if any(e['type'] == 'PUBLISHED' and e['video_id'] != item['video_id'] for e in history):
            raise ValueError('Experiment already bound to another upload')
        catalogs = [read(p / 'acquisition.json') for p in (root / 'runs').iterdir()
                    if p.is_dir() and (p / 'acquisition.json').is_file()]
        found = [v for a in catalogs for v in a['catalog'] if v['video_id'] == item['video_id']]
        if not found:
            raise ValueError('Binding requires actual API upload discovery')
        published = min(v['published_at'] for v in found)
        approval_times = [e['recorded_at'] for e in history if e['type'] == 'APPROVED']
        publication_clock = datetime.fromisoformat(published.replace('Z', '+00:00'))
        if datetime.fromisoformat(ex['registered_at']) >= publication_clock or min(datetime.fromisoformat(t) for t in approval_times) >= publication_clock:
            raise ValueError('RETROSPECTIVE_BINDING_REJECTED: keep spontaneous uploads observational')
        for e in events(root):
            if e['type'] == 'PUBLISHED' and e['video_id'] == item['video_id'] and e['experiment_id'] != item['experiment_id']:
                raise ValueError('Upload already bound to a different experiment')
    if kind == 'EVALUATED':
        raise ValueError('Evaluations are generated from mature API evidence, never manual assertions')
    if kind == 'CANCELLED' and any(e['type'] == 'PUBLISHED' for e in history):
        raise ValueError('Published experiment cannot be cancelled')
    return event(root, item)


def research(packet, cfg):
    validate('research', packet)
    if packet['research_seconds'] > cfg['research_seconds']:
        raise ValueError('Research budget exceeded; preserve the attempt outside accepted research')
    seen = set()
    for card in packet['opportunities']:
        if card['id'] in seen:
            raise ValueError('Duplicate opportunity ID')
        seen.add(card['id'])
        if packet['method_version'].startswith('youtube-radar/') and 'selection' not in card:
            raise ValueError('Radar discovery requires explicit external signal, channel filter and novelty review')
        if not any(s['supports'].strip() for s in card['sources']):
            raise ValueError('Every opportunity needs a supported source claim')
    return packet


def editorial_mix(cards):
    counts = {k: sum(c['lane'] == k for c in cards) for k in ['PROVEN', 'EMERGING', 'CREATIVE']}
    return {'target': {'PROVEN': 0.4, 'EMERGING': 0.4, 'CREATIVE': 0.2},
            'actual_counts': counts, 'policy': 'GUIDELINE_NOT_QUOTA; never add filler to meet ratios'}


def analytics_observations(acquisition, cfg, captured_at):
    result = []
    validator = load_draft_2020_12_validator(REPO / 'schemas/analytics_observation.schema.json')
    for report in acquisition['reports']:
        observations = []
        dimensions = report['parameters']['dimensions'].split(',')
        for metric in report['parameters']['metrics'].split(','):
            observations.append({'metric': metric, 'dimension': ','.join(dimensions),
                'observation': {'availability': report['availability'], 'rows': [
                    {k: r[k] for k in dimensions + [metric]} for r in report['rows']]}})
        envelope = {'schema_version': 'v1', 'id': 'youtube:' + digest(report), 'source': 'youtube',
            'project': 'abvx-youtube', 'period': report['requested_period'], 'observations': observations,
            'confidence': 'UNKNOWN', 'captured_at': captured_at,
            'provenance': {'recorded_by': METHOD, 'provider': 'youtubeAnalytics.reports.query',
                'source_uri': 'https://www.youtube.com/channel/' + cfg['channel_id'],
                'raw_ref': 'acquisition.json#' + report['label']}}
        validator.validate(envelope)
        result.append(envelope)
    return result


def import_studio(root, packet, evidence):
    """Owner exports/audits are supplementary and never certify API acquisition."""
    import hashlib
    validate('studio', packet)
    captured = datetime.fromisoformat(packet['captured_at'].replace('Z', '+00:00'))
    if captured > datetime.now(timezone.utc):
        raise ValueError('Future Studio capture time')
    for metric in packet['metrics']:
        if metric['period']['start'] > metric['period']['end']:
            raise ValueError('Invalid Studio period')
    body = evidence.read_bytes()
    proof_digest = hashlib.sha256(body).hexdigest()
    envelope = {'packet': packet, 'evidence_sha256': proof_digest,
                'classification': 'SUPPLEMENTARY_NOT_LIVE_API'}
    with lock(root):
        target = root / 'studio' / digest(envelope)
        target.mkdir(parents=True, exist_ok=True)
        # Text-only, minimized owner exports. Never copy browser profiles or credential files.
        if evidence.suffix.lower() not in {'.csv', '.json', '.md', '.txt'} or len(body) > 5_000_000:
            raise ValueError('Use a minimized text Studio export/audit under 5 MB')
        proof = target / 'proof.txt'
        if proof.exists() and proof.read_bytes() != body:
            raise ValueError('Studio evidence changed')
        if not proof.exists():
            proof.write_bytes(body)
        _write_once(target / 'import.json', envelope)
    return {'status': 'IMPORTED_SUPPLEMENTARY', 'digest': digest(envelope)}


def analyze(acquisition, root, run_id=None):
    by_video, week_by_video = {}, {}
    for report in acquisition['reports']:
        if report['label'] == 'videos_28d':
            for row in report['rows']:
                by_video.setdefault(row['video'], []).append(row)
        elif report['label'] == 'videos_7d':
            for row in report['rows']:
                week_by_video.setdefault(row['video'], []).append(row)
    previous = [p for p in (root / 'runs').glob('*/acquisition.json') if p.parent.name != run_id]
    known = {v['video_id'] for p in previous for v in read(p)['catalog']}
    links = {e['video_id']: e['experiment_id'] for e in events(root) if e['type'] == 'PUBLISHED'}
    rows = []
    for video in acquisition['catalog']:
        if not video['eligible']:
            continue
        measurements = by_video.get(video['video_id'], [])
        # Live API responses use lower/camel-case aliases as well as documented enums.
        aliases = {'shorts': 'SHORTS', 'videoOnDemand': 'VIDEO_ON_DEMAND',
                   'liveStream': 'LIVE_STREAM', 'creatorContentTypeUnspecified': 'UNSPECIFIED'}
        content_types = {aliases.get(r.get('creatorContentType'), r.get('creatorContentType')) for r in measurements}
        duration_match = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', video['duration'])
        seconds = sum(int(n or 0) * factor for n, factor in zip(duration_match.groups(), [3600,60,1])) if duration_match else None
        if content_types == {'SHORTS'}:
            group = 'SHORT'
        elif content_types == {'VIDEO_ON_DEMAND'} and seconds is not None:
            # Descriptive local duration bands, not proof of image orientation.
            group = 'REGULAR_UNDER_3_MIN' if seconds < 180 else 'REGULAR_3_MIN_PLUS'
        else:
            group = 'UNKNOWN_OR_MIXED'
        rows.append(dict(video_id=video['video_id'], title=video['title'],
            published_at=video['published_at'], metrics_28d=measurements,
            metrics_7d=week_by_video.get(video['video_id'], []),
            discovery_status=('PREVIOUSLY_SEEN' if video['video_id'] in known else
                              'NEWLY_DISCOVERED' if previous else 'INITIAL_CATALOG'),
            format_group=group, duration_seconds=seconds,
            availability='REPORTED' if measurements else 'NO_REPORTED_ROWS',
            experiment_id=links.get(video['video_id']),
            hypothesis_status='PROSPECTIVE_REGISTERED' if video['video_id'] in links else 'OBSERVATIONAL_ONLY'))
    return rows


def evaluate(acquisition, root, run_id):
    assessments = []
    exps = experiments(root)
    for link in [e for e in events(root) if e['type'] == 'PUBLISHED']:
        ex = exps[link['experiment_id']]
        label = (f'revenue_age_{ex["window_days"]}d:{link["video_id"]}' if ex['primary_metric'] == 'estimatedRevenue'
                 else f'age_{ex["window_days"]}d:{link["video_id"]}')
        matches = [r for r in acquisition['reports'] if r['label'] == label]
        status, actual = 'IMMATURE_OR_UNAVAILABLE', None
        if matches and matches[0]['rows']:
            report = matches[0]
            observed_days = {r['day'] for r in report['rows']}
            # Sparse or delayed days cannot certify the full observation window.
            expected = {str(date.fromisoformat(report['requested_period']['start']) + timedelta(days=i))
                        for i in range(ex['window_days'])}
            if expected <= observed_days and all(isinstance(r.get(ex['primary_metric']), (int, float)) for r in report['rows']):
                actual = sum(r[ex['primary_metric']] for r in report['rows'])
                status = 'SUPPORTED' if actual >= ex['minimum_result'] else 'NOT_SUPPORTED'
        assessments.append({'experiment_id': ex['id'], 'video_id': link['video_id'],
                            'status': status, 'actual': actual, 'primary_metric': ex['primary_metric'],
                            'selection': ex.get('selection')})
        from .youtube_radar import prediction_result
        assessments[-1]['secondary_predictions'] = [prediction_result(acquisition, link['video_id'], ex['window_days'], p['metric'], p['minimum_result']) for p in ex.get('secondary_predictions', [])]
        if status != 'IMMATURE_OR_UNAVAILABLE':
            event(root, {'type': 'EVALUATED', 'experiment_id': ex['id'], 'video_id': link['video_id'],
                         'evidence_run': run_id, 'assessment': assessments[-1]})
    return assessments


def render(run, acquisition, packet, rows, assessments):
    lines = [f'# YouTube Intelligence: {run["as_of"]}', '',
        f'Статус: {run["status"]}. Канал: {run["channel_id"]}. Источник: официальный API.',
        f'Получено: {run["captured_at"]}. Окончание запрошенных периодов: {run["data_end"]}.', '',
        f'Публичных доступных загрузок проанализировано: {len(rows)}. '
        f'Без зарегистрированной гипотезы: {sum(r["hypothesis_status"] == "OBSERVATIONAL_ONLY" for r in rows)}.', '',
        'Данные и наблюдения', '',
        'Полные ответы и все загрузки: acquisition.json, analysis.json. '
        'NO_REPORTED_ROWS означает отсутствие строк, а не нулевой результат.']
    for days in [7, 28]:
        report = next(r for r in acquisition['reports'] if r['label'] == f'channel_{days}d')
        data = report['rows']
        if data:
            lines.append(f'- {days} дней: {sum(r["views"] for r in data):,} просмотров; '
                         f'{sum(r["estimatedMinutesWatched"] for r in data) / 60:.1f} часа. '
                         f'Фактические строки: {data[0]["day"]} — {data[-1]["day"]}.')
    ranked = sorted(rows, key=lambda v: sum(r.get('views', 0) for r in v['metrics_28d']), reverse=True)
    lines.extend(['', 'Что привлекло просмотры за 28 дней', ''])
    for row in ranked[:5]:
        lines.append(f'- {row["title"]}: ' + (str(sum(r['views'] for r in row['metrics_28d']))
            if row['metrics_28d'] else 'UNKNOWN') + f' https://www.youtube.com/watch?v={row["video_id"]}')
    lines.extend(['', 'Слабые результаты и ограничения', '',
        'Рейтинг просмотров не устанавливает причинность. Молодые видео не сравниваются с архивом по суммарным просмотрам. '
        'Shorts, короткие горизонтальные и длинные видео требуют отдельных сопоставимых групп. '
        'CTR, возвращаемость и пролистывания не выдумываются из других показателей.', '',
        'Возможности и меню контента', '',
        'Ориентир 40% проверенных тем / 40% новых возможностей / 20% творческих экспериментов; не квота.'])
    from .youtube_radar import menu as select_menu, financial_context
    from zoneinfo import ZoneInfo
    weekly = datetime.fromisoformat(run['captured_at'].replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/Paris')).weekday() == 0
    selection = select_menu(packet, weekly)
    menu = selection['cards']
    financial = financial_context(acquisition, rows)
    money_rows = [r for r in financial if r['revenue_28d'] is not None and isinstance(r['revenue_28d'].get('estimatedRevenue'), (int, float))]
    lines.extend(['', 'Доход по видео за запрошенные 28 дней (EUR; оценка, не выплата)', ''])
    for row in sorted(money_rows, key=lambda r: r['revenue_28d'].get('estimatedRevenue', 0), reverse=True)[:10]:
        lines.append(f'- {row["video_id"]}: €{row["revenue_28d"]["estimatedRevenue"]:.3f}; {row["format_group"]}.')
    lines.append('Официальный RPM, география/трафик и периоды Studio: financial-context.json. Отсутствующие строки — UNKNOWN. ' +
                 'Нехватка до недельного ориентира: ' + str(selection['shortfall']) + '; заполнение не добавляется.')
    lines.append(f'Найдено возможностей: {len(packet["opportunities"])}; выбрано для краткого меню: {len(menu)}. Полный список: research.json.')
    for card in sorted(menu, key=lambda c: c['priority']):
        lines.extend(['', f'**{card["priority"]}. {card["title"]}** [{card["lane"]}; {card["format"]}; {card["duration"]}]',
            card['concept'], 'Почему: ' + card['rationale'], 'Hook: ' + card['hook'],
            'Visual: ' + card['visual'], 'Production: ' + card['production'],
            'Сложность: ' + card['complexity'] + '. Гипотеза: ' + card['hypothesis'],
            'Основной показатель: ' + card['primary_metric'],
            'Источники: ' + '; '.join(s['url'] + ' (' + s['supports'] + ')' for s in card['sources'])])
    lines.extend(['', 'Результаты экспериментов', '',
        json.dumps(assessments, ensure_ascii=False) if assessments else 'Оценённых проспективных экспериментов пока нет.', '',
        'Следующие действия', '',
        '- Сохранить PlayMCP и PocketputerDV в редакционном контексте; решения о производстве принимает владелец.',
        '- Проверить свежие загрузки в analysis.json; для спонтанных сохранять только наблюдения.',
        '- Доход: ' + acquisition['revenue']['availability'] + '; первые дни YPP не экстраполировать.',
        '- Выбрать эксперимент и зарегистрировать гипотезу до публикации.'])
    return '\n'.join(lines) + '\n'


def run(root, run_id, packet, api=None, as_of=None):
    cfg = config()
    packet = research(packet, cfg)
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError('Timezone-aware clock required')
    if date.fromisoformat(packet['as_of']) != as_of.date():
        raise ValueError('Fresh research must match actual acquisition date; no baseline-as-live runs')
    for card in packet['opportunities']:
        for source in card['sources']:
            captured = datetime.fromisoformat(source['checked_at'].replace('Z', '+00:00'))
            if captured > as_of or (as_of - captured).total_seconds() > cfg['research_freshness_hours'] * 3600:
                raise ValueError('Stale or future opportunity evidence')
    run_id = safe_id(run_id)
    with lock(root):
        destination = root / 'runs' / run_id
        if destination.exists():
            raise ValueError('Run already exists; use a new ID, never overwrite evidence')
        destination.mkdir(parents=True)
        record = {'schema_version': METHOD, 'run_id': run_id, 'channel_id': cfg['channel_id'],
                  'as_of': as_of.date().isoformat(), 'captured_at': stamp(), 'status': 'STARTED',
                  'data_end': (as_of.date() - timedelta(days=cfg['data_lag_days'])).isoformat()}
        _write_once(destination / 'started.json', record)
        _write_once(destination / 'research.json', packet)
        try:
            api = api or Google(root, cfg)
            tracked = [e['video_id'] for e in events(root) if e['type'] == 'PUBLISHED']
            if (root / 'framewright-exchange.json').exists():
                try:
                    from .youtube_framewright_auto import before_run
                    # Calendar exchange reports reuse the primary acquisition; optional
                    # links must not add age-window queries to its shared budget.
                    before_run(root, cfg['channel_id'])
                except Exception:
                    try:private_json(root / 'framewright-exchange-last.json', {'result':'pending','phase':'receive'})
                    except OSError:pass
            acquisition = acquire(api, cfg, date.fromisoformat(record['data_end']), as_of, tracked,
                                  checkpoint=lambda snapshot: private_json(destination / 'acquisition-progress.json', snapshot))
            _write_once(destination / 'acquisition.json', acquisition)
            _write_once(destination / 'analytics-observations.json', analytics_observations(acquisition, cfg, record['captured_at']))
            rows = analyze(acquisition, root, run_id)
            assessments = evaluate(acquisition, root, run_id)
            from .youtube_radar import financial_context, menu, learning_review
            _write_once(destination / 'learning-review.json', learning_review(assessments))
            _write_once(destination / 'financial-context.json', financial_context(acquisition, rows, [read(p) for p in (root / 'studio').glob('*/import.json')]))
            _write_once(destination / 'radar-menu.json', menu(packet, as_of.astimezone(__import__('zoneinfo').ZoneInfo('Europe/Paris')).weekday() == 0))
            _write_once(destination / 'analysis.json', {'uploads': rows, 'assessments': assessments,
                        'editorial_mix': editorial_mix(packet['opportunities'])})
            has_channel_data = all(any(r['rows'] for r in acquisition['reports'] if r['label'] == f'channel_{d}d') for d in [7,28])
            status = 'COMPLETE' if packet['status'] == 'COMPLETE' else 'PARTIAL_RESEARCH'
            if not has_channel_data or (packet['method_version'].startswith('youtube-radar/') and
                    (acquisition['revenue']['availability'] != 'REPORTED' or acquisition['revenue'].get('supplement_failures'))):
                status = 'PARTIAL_DATA'
            record.update(status=status,
                          acquisition_digest=digest(acquisition), research_digest=digest(packet))
            validate('run', record)
            (destination / 'REPORT.md').write_text(render(record, acquisition, packet, rows, assessments), encoding='utf-8')
            _write_once(destination / 'execution.json', record)
            if (root / 'framewright-exchange.json').exists():
                try:
                    from .youtube_framewright_auto import after_run
                    after_run(root, destination)
                except Exception:
                    try:private_json(root / 'framewright-exchange-last.json', {'result':'pending','phase':'export'})
                    except OSError:pass
            return record | {'report': str(destination / 'REPORT.md')}
        except Exception as error:
            failure = record | {'status': 'BLOCKED', 'error_type': type(error).__name__}
            prefix = str(error).split(':', 1)[0] if isinstance(error, ValueError) else ''
            if prefix in {'AUTH_REQUIRED', 'AUTH_REFRESH_FAILED', 'GOOGLE_DEPENDENCIES_REQUIRED',
                          'ACQUISITION_BUDGET_EXHAUSTED', 'CHANNEL_ID_MISMATCH', 'GOOGLE_READ_FAILED'}:
                failure['blocker'] = prefix
            validate('run', failure)
            # Never serialize provider exception bodies or credentials into public output.
            _write_once(destination / 'execution.json', failure)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-root', type=Path, default=DEFAULT)
    subs = parser.add_subparsers(dest='action', required=True)
    auth = subs.add_parser('auth'); auth.add_argument('--monetary', action='store_true')
    auth.add_argument('--open-browser', action='store_true', help='For an owner-run terminal OAuth flow')
    runner = subs.add_parser('run'); runner.add_argument('--run-id', required=True)
    runner.add_argument('--research', type=Path, required=True)
    reg = subs.add_parser('register'); reg.add_argument('--file', type=Path, required=True)
    evt = subs.add_parser('event'); evt.add_argument('--file', type=Path, required=True)
    studio = subs.add_parser('import-studio'); studio.add_argument('--file', type=Path, required=True)
    studio.add_argument('--evidence', type=Path, required=True)
    subs.add_parser('status')
    subs.add_parser('context')
    subs.add_parser('radar-request')
    stage = subs.add_parser('nantes-stage')
    stage.add_argument('--run-dir', type=Path, required=True)
    stage.add_argument('--mode', choices=['weekly','daily'], required=True)
    stage.add_argument('--token', required=True)
    stage.add_argument('--research', type=Path, help='Independent current review over retained verified acquisition; never overwrites it')
    csv_import = subs.add_parser('radar-csv')
    csv_import.add_argument('--file', type=Path, required=True)
    csv_import.add_argument('--start', required=True); csv_import.add_argument('--end', required=True)
    args = parser.parse_args(argv)
    root = args.state_root.resolve()
    if args.action == 'auth':
        result = authenticate(root, args.monetary, args.open_browser)
    elif args.action == 'run':
        result = run(root, args.run_id, read(args.research))
    elif args.action == 'register':
        result = register(root, read(args.file))
    elif args.action == 'import-studio':
        result = import_studio(root, read(args.file), args.evidence)
    elif args.action == 'event':
        with lock(root):
            result = change(root, read(args.file))
    elif args.action == 'nantes-stage':
        from .youtube_radar import nantes_packet
        result = nantes_packet(args.run_dir, args.mode, args.token, research_file=args.research)
    elif args.action == 'radar-csv':
        from .youtube_radar import studio_csv
        result = studio_csv(args.file, {'start': args.start, 'end': args.end})
    elif args.action in {'context', 'radar-request'}:
        previous = sorted((root / 'runs').glob('*/execution.json'), key=lambda p: read(p)['captured_at'], reverse=True)
        accepted = [p for p in previous if read(p)['status'] in {'COMPLETE', 'PARTIAL_RESEARCH', 'PARTIAL_DATA'}][:3]
        result = {'method': METHOD, 'baseline': str(root / 'baseline.json') if (root / 'baseline.json').is_file() else None,
            'backlog': config()['existing_backlog'], 'editorial_guideline': config()['editorial_guideline'],
            'previous_reports': [str(p.parent / ('REPORT-v2.md' if (p.parent / 'REPORT-v2.md').exists() else 'REPORT.md')) for p in accepted],
            'previous_analyses': [str(p.parent / ('analysis-v2.json' if (p.parent / 'analysis-v2.json').exists() else 'analysis.json')) for p in accepted],
            'experiments': experiments(root), 'events': events(root),
            'policy': 'Read previous evidence before research; spontaneous uploads have no prospective hypothesis.',
            'research_checkpoints_history_only': [str(p) for p in sorted(root.glob('research-*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:3]],
            'external_signal_history': [str(p) for p in sorted(root.glob('signals-*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:3]],
            'learning_reviews': [str(p.parent / 'learning-review.json') for p in accepted if (p.parent / 'learning-review.json').exists()],
            'studio_supplements': [str(p) for p in (root / 'studio').glob('*/import.json')],
            'financial_context': [str(p.parent / 'financial-context.json') for p in accepted if (p.parent / 'financial-context.json').exists()]}
        if args.action == 'radar-request':
            from .youtube_radar import research_request
            from zoneinfo import ZoneInfo
            result = research_request(datetime.now(ZoneInfo('Europe/Paris')).date(), result)
    else:
        result = {'method': METHOD, 'channel_id': config()['channel_id'],
            'oauth_client_present': (root / 'credentials/client.json').is_file(),
            'oauth_token_present': (root / 'credentials/token.json').is_file(),
            'experiments': len(experiments(root)),
            'runs': [read(p) for p in sorted((root / 'runs').glob('*/execution.json'))]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # Errors from Google libraries may contain tokens or request URLs.
        print('YouTube operation failed: ' + (str(error) if isinstance(error, ValueError) else type(error).__name__))
        raise SystemExit(1)
