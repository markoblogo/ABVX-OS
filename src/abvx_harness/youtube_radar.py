"""Research-only extensions to YouTube Intelligence; no scheduler or publisher."""
import csv
from datetime import date, timedelta
import hashlib
import io
import math
import re


def studio_csv(path, period):
    """Keep exported RPM separate from an explicitly labelled derived ratio."""
    if date.fromisoformat(period['start']) > date.fromisoformat(period['end']):
        raise ValueError('Invalid period')
    def number(value):
        if value is None or not value.strip():
            return None
        result = float(value.replace(',', '.'))
        if not math.isfinite(result) or result < 0:
            raise ValueError('Invalid nonnegative metric')
        return result
    result, seen = [], set()
    body = path.read_bytes()
    proof = hashlib.sha256(body).hexdigest()
    for row in csv.DictReader(io.StringIO(body.decode('utf-8-sig'))):
        vid = row['Контент'].strip()
        if vid == 'Итоговое значение':
            continue
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid) or vid in seen:
            raise ValueError('Invalid or duplicate video ID')
        seen.add(vid)
        views, revenue, rpm = (number(row[k]) for k in ['Просмотры', 'Расчетный доход (EUR)', 'Доход на тысячу просмотров (EUR)'])
        result.append({'video_id': vid, 'title': row['Название видео'], 'period': dict(period),
            'estimated_revenue_eur': revenue, 'views': views, 'official_rpm_eur': rpm,
            'official_rpm_denominator': 'EXPORT_UNSPECIFIED_CHECK_STUDIO',
            'derived_revenue_per_1000_views_eur': revenue * 1000 / views if views and revenue is not None else None,
            'format': 'UNKNOWN', 'geography': 'UNKNOWN', 'traffic': 'UNKNOWN',
            'ctr': None, 'retention': None, 'ypp_start': None,
            'sample_status': 'SMALL_SAMPLE' if views is not None and views < 1000 else 'OBSERVATIONAL',
            'classification': 'SUPPLEMENTARY_NOT_LIVE_API',
            'evidence_sha256': proof})
    return result


def financial_context(acquisition, uploads, studio=()):
    """Same-period official API evidence. Never label a computed ratio official RPM."""
    by_video = {}
    for report in acquisition['reports']:
        if report['label'] == 'video_revenue_28d':
            for row in report['rows']:
                by_video[row['video']] = {'period': report['requested_period'], **row}
    result = []
    for upload in uploads:
        vid = upload['video_id']
        money = by_video.get(vid)
        reports = {r['label'].split(':')[0]: r for r in acquisition['reports']
                   if r['label'].endswith(':' + vid) and r['label'].startswith(('country_28d:', 'traffic_28d:', 'revenue_age_'))}
        result.append({'video_id': vid, 'format_group': upload['format_group'],
            'revenue_28d': money, 'official_rpm': None, 'official_rpm_availability': 'STUDIO_SUPPLEMENT_REQUIRED',
            'studio_rpm_observations': [{'metric': m, 'evidence_sha256': e['evidence_sha256']}
                for e in studio for m in e['packet']['metrics'] if m['metric'] == 'rpm' and m['video_id'] == vid],
            'revenue_availability': 'REPORTED' if money else 'UNKNOWN',
            'supplements': reports, 'hypothesis_status': upload['hypothesis_status']})
    return result


def menu(packet, weekly=True):
    """Select supplied, sourced discoveries; discovery itself stays with the researcher."""
    selected, seen = [], set()
    for card in sorted(packet['opportunities'], key=lambda c: c['priority']):
        selection = card.get('selection', {})
        if selection and (selection['niche_fit'] != 'PASS' or selection['novelty_status'] != 'NEW_QUESTION'):
            continue
        key = selection.get('novelty_key') or ' '.join(re.findall(r'\w+', card['title'].casefold()))
        if not card.get('recommended', True) or key in seen:
            continue
        seen.add(key)
        selected.append(card)
        if len(selected) == (20 if weekly else 3):
            break
    return {'cards': selected, 'target': '10–20' if weekly else '0–3',
            'shortfall': max(0, 10-len(selected)) if weekly else 0,
            'policy': 'NO_FILLER; analyst priority is ordinal judgment, not predicted revenue'}


def research_request(as_of, context):
    monday = as_of - timedelta(days=as_of.weekday())
    return {'schema_version': 'youtube-radar-request/v1', 'week_start': str(monday),
        'week_end': str(monday + timedelta(days=6)), 'context': context,
        'instructions': [
            'Use existing Nantes Radar stage only; daily 10:00 Europe/Paris, full Monday menu. No separate schedule.',
            'Read latest uploads including unplanned ones, financial-context.json, frozen hypotheses and 7/28-day outcomes.',
            'Channel catalog defines the niche; internal analytics filters external discovery for reach and monetization. It does not prescribe sequels. Discover fresh viewer questions across external releases, measured momentum, competitor videos and community problems within that niche.',
            'Record selection origin, external signal, niche-fit evidence, novelty key, expected response and uncertainty. Reject repeated viewer questions even under a new title. Check full current uploads; incomplete catalog means novelty remains provisional.',
            'Discover 10–20 supported diverse ideas weekly; fewer when evidence is weak. Separate a new release from measured rising demand. Retain counterevidence, rejected candidates and dated observations.',
            'Compare official RPM separately, estimated revenue, same-age post-YPP windows, confirmed format, geography, traffic, CTR/retention when available. Missing is UNKNOWN.',
            'Rank by observed channel evidence, hypothesized commercial value, Framewright effort/cost and risk. No borrowed RPM, no extrapolation of tiny samples.',
            'Compare frozen reach and revenue predictions with complete 7/28-day outcomes, including failures. Separate wrong demand assumptions, packaging/retention, geography/traffic, costs and unavailable data; reasons remain hypotheses until evidence discriminates them. Propose one evidence-bound selection change and a prospective check; do not automatically promote a method.',
            'Return existing youtube-research/v1 packet with 2–4 detailed English briefs and Russian rationale; no publishing, editing, purchases or automatic experiment bindings.']}


def prediction_result(acquisition, video_id, days, metric, minimum):
    label = (f'revenue_age_{days}d:' if metric == 'estimatedRevenue' else f'age_{days}d:') + video_id
    matches = [r for r in acquisition['reports'] if r['label'] == label]
    if not matches or not matches[0]['rows']:
        return {'metric': metric, 'status': 'IMMATURE_OR_UNAVAILABLE', 'actual': None}
    report = matches[0]
    expected = {str(date.fromisoformat(report['requested_period']['start']) + timedelta(days=i)) for i in range(days)}
    rows = report['rows']
    if not expected <= {r['day'] for r in rows} or not all(isinstance(r.get(metric), (int,float)) and math.isfinite(r[metric]) for r in rows):
        return {'metric': metric, 'status': 'IMMATURE_OR_UNAVAILABLE', 'actual': None}
    actual = sum(r[metric] for r in rows)
    return {'metric': metric, 'minimum_result': minimum, 'actual': actual,
            'status': 'SUPPORTED' if actual >= minimum else 'NOT_SUPPORTED'}


def learning_review(assessments):
    return {'independent_uploads': len({a['video_id'] for a in assessments}),
        'findings': [dict(experiment_id=a['experiment_id'], video_id=a['video_id'],
            prediction_status=a['status'], selection=a.get('selection'),
            secondary_predictions=a.get('secondary_predictions', []),
            causal_status='UNPROVEN', next_check=(
                'Wait for mature complete same-age evidence; do not classify unavailable data as a failed idea.' if a['status']=='IMMATURE_OR_UNAVAILABLE' else
                'Retain this signal for another independent within-niche trial; success does not establish its cause.' if a['status']=='SUPPORTED' else
                'Check exposure, CTR, retention, format, traffic/geography and production cost before blaming the external demand signal.')) for a in assessments],
        'policy': 'Source hypotheses frozen before publication; repeat successes/failures are evidence, not automatic causal proof or method adoption.'}


def momentum(points):
    """Two dated comparable counters show growth, never acceleration or viewer demand."""
    from datetime import datetime
    if len(points) < 2:
        return {'status': 'UNKNOWN', 'reason': 'Two comparable dated observations required'}
    points = sorted(points, key=lambda p: p['observed_at'])
    if len({(p['entity'], p['metric']) for p in points}) != 1:
        raise ValueError('Cannot compare different entities or metrics')
    first, last = points[0], points[-1]
    start, end = [datetime.fromisoformat(p['observed_at'].replace('Z', '+00:00')) for p in (first,last)]
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError('Distinct timezone-aware observations required')
    delta = last['value']-first['value']
    return {'status': 'GROWING' if delta > 0 else 'FLAT_OR_DECLINING', 'delta': delta,
            'per_day': delta * 86400 / (end-start).total_seconds(),
            'acceleration': 'UNKNOWN', 'youtube_demand': 'UNPROVEN'}


def nantes_packet(run_dir, mode, token, clock=None, research_file=None):
    """Read verified run evidence into the existing six-stage journal contract. No send."""
    import json
    from datetime import datetime, timezone
    from .youtube import digest, research, config
    run_dir = run_dir.resolve()
    record = json.loads((run_dir / 'execution.json').read_text())
    if record['status'] == 'BLOCKED':
        return dict(token=token,status='BLOCKED',summary='YouTube acquisition blocked; no fresh conclusions.',sources=[],
                    failure_reason=record.get('blocker','ACQUISITION_BLOCKED'),retryable=False)
    acquisition = json.loads((run_dir / 'acquisition.json').read_text())
    packet = research(json.loads((run_dir / 'research.json').read_text()), config())
    if digest(acquisition) != record['acquisition_digest'] or digest(packet) != record['research_digest']:
        raise ValueError('Run evidence digest mismatch')
    clock = clock or datetime.now(timezone.utc)
    captured = datetime.fromisoformat(record['captured_at'].replace('Z','+00:00'))
    stale = captured > clock or (clock-captured).total_seconds() > 86400
    review_source = None
    if research_file is not None:
        # An independent source-bound review may reuse retained real acquisition.
        # It does not rewrite the original run or certify a new live acquisition.
        packet = research(json.loads(research_file.read_text()), config())
        if packet['as_of'] != clock.date().isoformat():
            raise ValueError('Review research must match current date')
        for card in packet['opportunities']:
            for source in card['sources']:
                checked = datetime.fromisoformat(source['checked_at'].replace('Z','+00:00'))
                if checked > clock or (clock-checked).total_seconds() > config()['research_freshness_hours']*3600:
                    raise ValueError('Stale or future independent research')
        review_source = {'ref': str(research_file.resolve()), 'checked_at': clock.isoformat()}
    selection = menu(packet, mode == 'weekly')
    summary = [f"YouTube Intelligence: {record['status']}; captured {record['captured_at']}; data through {record['data_end']}.",
               f"Uploads: {len(acquisition['catalog'])}; revenue: {acquisition['revenue']['availability']}."]
    money_report = next((r for r in acquisition['reports'] if r['label'] == 'revenue_28d'), None)
    if money_report and money_report['rows']:
        total = sum(r['estimatedRevenue'] for r in money_report['rows'])
        summary.append(f"Estimated revenue: EUR {total:.3f}; requested period {money_report['requested_period']}; estimate, not payout.")
    if mode == 'weekly':
        summary.append(f"Supported menu: {len(selection['cards'])}; target 10–20, no filler. Top priorities:")
        summary.extend(f"{c['priority']}. {c['title']} — {c['rationale']}" for c in selection['cards'][:5])
    else:
        summary.append('Daily metrics/catalog check only. No new external discovery; retained ideas are not new recommendations.')
    summary.append('Full evidence/menu/learning: '+str(run_dir / 'REPORT.md'))
    sources = [{'ref':str(run_dir / 'execution.json'),'checked_at':record['captured_at']}]
    if review_source:
        sources.append(review_source)
        summary.append('Independent review reuses the verified source run; no new live-acquisition claim. Research digest: '+digest(packet))
    if mode == 'weekly':
        sources += [{'ref':s['url'],'checked_at':s['checked_at']} for c in selection['cards'][:5] for s in c['sources']]
    monetary_ready = acquisition['revenue']['availability'] == 'REPORTED'
    complete = record['status'] == 'COMPLETE' and packet['status'] == 'COMPLETE' and not stale and monetary_ready
    result = dict(token=token,status='COMPLETE' if complete else 'PARTIAL',summary='\n'.join(summary),sources=sources,retryable=False)
    if not complete:
        result['failure_reason'] = ('STALE_RETAINED_RUN' if stale else 'MONETARY_DATA_UNAVAILABLE' if not monetary_ready else 'PARTIAL_RESEARCH' if packet['status'] != 'COMPLETE' else record['status'])
    return result
