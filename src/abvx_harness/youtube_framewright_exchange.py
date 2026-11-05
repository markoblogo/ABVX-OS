"""Optional local Framewright seam; no API, experiment registration or scheduler."""
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from . import framewright_wire as W


def apply_message(data,row):
    if row['producer']!='framewright':raise ValueError('Expected Framewright')
    p=row['payload'];kind=row['kind']
    if kind=='association':
        W.association_payload(p)
        menu=data.get('menus',{}).get(p['research_revision'])
        if menu is None:return 'pending','Research menu not exported by this Radar'
        idea=next((i for i in menu['ideas'] if i['id']==p['radar_idea_id']),None)
        if idea is None:return 'pending','Unknown idea'
        if W.digest(idea)!=p['idea_sha256']:raise ValueError('Frozen idea hash mismatch')
        links=data.setdefault('links',{});old=links.get(p['project_id'])
        if old is not None and old!=p:raise ValueError('Existing project association conflict')
        links[p['project_id']]=copy.deepcopy(p)
        return 'applied','Observational/prospective provenance linked; no experiment events created'
    if kind=='production_status':
        W.status_payload(p);link=data.get('links',{}).get(p['project_id'])
        if link is None:return 'pending','Import association first'
        if (p['radar_idea_id'],p['research_revision'])!=(link['radar_idea_id'],link['research_revision']):raise ValueError('Project association differs')
        statuses=data.setdefault('production',{});old=statuses.get(p['project_id']);rev=row['source_revision']
        if old and rev['sequence']<=old['source_revision']['sequence']:
            if rev['sequence']==old['source_revision']['sequence'] and rev['sha256']!=old['source_revision']['sha256']:raise ValueError('Conflicting production revision')
            return 'applied','Historical status retained; current status unchanged'
        owners=data.setdefault('video_owners',{})
        for pub in p['publications']:
            prior=owners.get(pub['video_id'])
            if prior is not None and prior!=p['project_id']:raise ValueError('Video already belongs to another project')
        for pub in p['publications']:owners[pub['video_id']]=p['project_id']
        statuses[p['project_id']]=copy.deepcopy(row)
        return 'applied','Status/publication recorded with source provenance; visibility not verified'
    raise ValueError('Unsupported inbound kind')


def export_menu(research,root):
    # Own-repository validation; no import from Framewright or live acquisition.
    from .youtube import validate
    raw=Path(research).read_bytes()
    if len(raw)>20*1024*1024:raise ValueError('Research too large')
    packet=json.loads(raw);validate('research',packet)
    ideas=[]
    for item in packet['opportunities']:
        ideas.append({'id':item['id'],'title':item['title'],'question':item.get('hook') or item['concept'],
                      'hypothesis':item['hypothesis'],'format':item['format'],'sources':copy.deepcopy(item['sources']),
                      'constraints':[item['production'],item['selection']['uncertainty']]})
    revision=hashlib.sha256(raw).hexdigest();p={'packet_sha256':revision,'as_of':packet['as_of'],'ideas':ideas};W.menu_payload(p)
    occurred=max((s['checked_at'] for i in ideas for s in i['sources']),default=packet['as_of']+'T00:00:00+00:00')
    row=W.message('idea_menu','radar','menu:'+revision,revision,0,occurred,p)
    with W.locked(W.directory(root,'radar')):
        st=W.state(root,'radar');st['data'].setdefault('menus',{})[revision]=p;W.atomic(W.directory(root,'radar')/'state.json',st)
    W.publish(root,'radar',row);return row


def export_analytics(run_dir,root,project_id,video_id,report_label='videos_7d'):
    """Minimise an existing, hash-verified Radar acquisition; never acquire data.

    Calendar report windows remain calendar windows, not 7/28 days since upload.
    Missing video/metrics is PENDING, never zero. No synthetic CLI export.
    """
    from .process_learning import digest
    run_dir=Path(run_dir);execution=W.read(run_dir/'execution.json');path=run_dir/'acquisition.json'
    if path.is_symlink() or path.stat().st_size>30*1024*1024:raise ValueError('Unsafe/oversized acquisition')
    raw=path.read_bytes();acquisition=json.loads(raw)
    if digest(acquisition)!=execution['acquisition_digest']:raise ValueError('Acquisition receipt mismatch')
    st=W.state(root,'radar')['data'];link=st.get('links',{}).get(project_id)
    if link is None or st.get('video_owners',{}).get(video_id)!=project_id:raise ValueError('Unknown project/video link')
    expected=st.get('expected_channel')
    if not expected or execution['channel_id']!=expected:raise ValueError('Channel not configured/mismatch')
    video=next((v for v in acquisition['catalog'] if v['video_id']==video_id),None)
    reports=[r for r in acquisition['reports'] if r['label']==report_label
             and set(r['parameters'].get('dimensions','').split(',')) in ({'video'},{'video','creatorContentType'})]
    if video is None or not reports:return {'result':'pending','reason':'No matching actual video report'}
    matches=[(report,row) for report in reports for row in report['rows'] if row.get('video')==video_id]
    if len(matches)>1:raise ValueError('Ambiguous report rows; do not sum averages across shards')
    if not matches:return {'result':'pending','reason':'Video missing from report; not zero'}
    report,matched=matches[0];found=[matched]
    src=found[0] if found else {};names={'views':'views','averageViewDuration':'average_view_duration_seconds','averageViewPercentage':'average_percentage_viewed','impressionsCtr':'impressions_ctr_percent','estimatedRevenue':'estimated_revenue'}
    metrics={dest:src.get(source) for source,dest in names.items()};period=report['requested_period']
    payload=dict(project_id=project_id,video_id=video_id,channel_id=expected,as_of=execution['captured_at'],published_at=video['published_at'],period_start=period['start'],period_end=period['end'],timezone='America/Los_Angeles',window='calendar_report',availability=report['availability'],metrics=metrics,currency=report['parameters'].get('currency'),source_sha256=hashlib.sha256(raw).hexdigest(),source_kind='retained_youtube_api',report_label=report_label)
    W.analytics_payload(payload);h=W.digest(payload);row=W.message('analytics_snapshot','radar',project_id,h,0,payload['as_of'],payload);W.publish(root,'radar',row);return row


def attach_intake(root,project_id,intake_id,intake_root=None):
    """Reference an existing own intake record; never create/promote it."""
    W.key(intake_id)
    if ':' in intake_id:raise ValueError('Invalid intake filename')
    intake_root=Path(intake_root) if intake_root else Path(__file__).resolve().parents[2]/'intake/items'
    source=intake_root/(intake_id+'.json');item=W.read(source);summary=json.loads(item['summary'])
    with W.locked(W.directory(root,'radar')):
        st=W.state(root,'radar');data=st['data'];link=data.get('links',{}).get(project_id)
        if link is None or summary.get('candidate_id')!=link['radar_idea_id'] or data.get('video_owners',{}).get(summary.get('video_id'))!=project_id:raise ValueError('Intake/project/video association mismatch')
        if item.get('id')!=intake_id:raise ValueError('Intake identity mismatch')
        record={'id':intake_id,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status_at_reference':item['status']}
        data.setdefault('intake_refs',{})[project_id]=record;W.atomic(W.directory(root,'radar')/'state.json',st)
    return record


def configure(root,channel):
    import re
    if not re.fullmatch(r'UC[A-Za-z0-9_-]{22}',channel):raise ValueError('Invalid channel')
    with W.locked(W.directory(root,'radar')):
        st=W.state(root,'radar');old=st['data'].get('expected_channel')
        if old and old!=channel:raise ValueError('Channel change requires explicit migration')
        st['data']['expected_channel']=channel;W.atomic(W.directory(root,'radar')/'state.json',st)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exchange',type=Path,required=True);p.add_argument('--apply',action='store_true');sub=p.add_subparsers(dest='action',required=True)
    q=sub.add_parser('receive');q.add_argument('message',type=Path)
    q=sub.add_parser('export-menu');q.add_argument('research',type=Path)
    q=sub.add_parser('configure');q.add_argument('--channel-id',required=True)
    q=sub.add_parser('enable-auto');q.add_argument('--radar-root',type=Path,required=True)
    q=sub.add_parser('link-intake');q.add_argument('--project-id',required=True);q.add_argument('--intake-id',required=True)
    q=sub.add_parser('export-analytics');q.add_argument('run_dir',type=Path);q.add_argument('--project-id',required=True);q.add_argument('--video-id',required=True);q.add_argument('--report-label',default='videos_7d')
    sub.add_parser('status');args=p.parse_args()
    if args.action=='status':print(json.dumps(W.state(args.exchange,'radar'),ensure_ascii=False));return
    if not args.apply:print(json.dumps({'status':'PREVIEW_NO_WRITES','action':args.action}));return
    if args.action=='enable-auto':
        from .youtube_framewright_auto import enable
        enable(args.radar_root,args.exchange);print(json.dumps({'result':'auto_run_enabled'}));return
    if args.action=='receive':result=W.receive(args.exchange,'radar',W.read(args.message),apply_message)
    elif args.action=='export-menu':result=export_menu(args.research,args.exchange)
    elif args.action=='link-intake':result=attach_intake(args.exchange,args.project_id,args.intake_id)
    elif args.action=='configure':configure(args.exchange,args.channel_id);result={'result':'configured'}
    else:result=export_analytics(args.run_dir,args.exchange,args.project_id,args.video_id,args.report_label)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
