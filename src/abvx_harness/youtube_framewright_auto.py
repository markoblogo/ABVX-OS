"""Opt-in local exchange at existing Radar run boundaries; no own schedule/API."""
from pathlib import Path
from . import framewright_wire as W
from . import youtube_framewright_exchange as E


def enable(radar_root,exchange):
    radar_root=Path(radar_root)
    if not radar_root.is_dir() or radar_root.is_symlink():raise ValueError('Existing Radar root required')
    if not W.state(exchange,'radar')['data'].get('expected_channel'):raise ValueError('Configure exchange channel first')
    W.atomic(radar_root/'framewright-exchange.json',{'version':1,'enabled':True,'exchange_root':str(Path(exchange).absolute())})


def context(radar_root):
    c=W.read(Path(radar_root)/'framewright-exchange.json')
    if c!={'version':1,'enabled':True,'exchange_root':c.get('exchange_root')} or not isinstance(c['exchange_root'],str):raise ValueError('Invalid auto configuration')
    return Path(c['exchange_root'])


def record(radar_root,result):
    try:W.atomic(Path(radar_root)/'framewright-exchange-last.json',result)
    except OSError:pass


def before_run(radar_root,channel):
    if not (Path(radar_root)/'framewright-exchange.json').exists():return []
    try:
        root=context(radar_root)
        if W.state(root,'radar')['data'].get('expected_channel')!=channel:raise ValueError('Configured channel mismatch')
        outcomes=W.drain(root,'radar',E.apply_message)
        videos=sorted(W.state(root,'radar')['data'].get('video_owners',{}))
        if len(videos)>100:raise ValueError('Tracked video limit exceeded')
        record(radar_root,{'result':'received','incoming':[r['result'] for r in outcomes],'tracked_videos':len(videos)})
        return videos
    except (OSError,ValueError,TypeError,KeyError,ImportError) as exc:
        record(radar_root,{'result':'pending','reason':type(exc).__name__});return []


def after_run(radar_root,run_dir):
    if not (Path(radar_root)/'framewright-exchange.json').exists():return {'result':'disabled'}
    try:
        root=context(radar_root);run_dir=Path(run_dir)
        menu=E.export_menu(run_dir/'research.json',root)
        state=W.state(root,'radar')['data'];exports=[]
        if len(state.get('video_owners',{}))>100:raise ValueError('Tracked video limit exceeded')
        for video,project in sorted(state.get('video_owners',{}).items()):
            for window in ['videos_7d','videos_28d']:
                row=E.export_analytics(run_dir,root,project,video,window)
                exports.append({'video_id':video,'window':window,'result':'exported' if row.get('kind')=='analytics_snapshot' else row['result']})
        result={'result':'exported','menu_message_id':menu['message_id'],'analytics':exports}
    except (OSError,ValueError,TypeError,KeyError,ImportError) as exc:
        result={'result':'pending','reason':type(exc).__name__}
    record(radar_root,result);return result
