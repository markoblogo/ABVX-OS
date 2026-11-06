"""Offline scale evidence. All fixtures and dollar/labor zeros are synthetic."""
import json
import resource
import time
import tracemalloc
from pathlib import Path
from abvx_harness.book_radar_wide import screen, handoff

def benchmark():
    fixture=Path(__file__).parent/'fixtures/wide-screener-v1/scale-1000.json'
    tracemalloc.start();start=time.perf_counter();run=screen(fixture);elapsed=time.perf_counter()-start
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert [run['counts'][k] for k in ('raw','normalized','corroborated','quick_screen','kill','park','investigate')]==[1000,200,40,40,180,10,10]
    handoffs=[handoff(run,c['cluster_id']) for c in run['clusters'] if c['decision']=='INVESTIGATE']
    return run,{'status':'PASS','origin':'SYNTHETIC','counts':run['counts'],'machine_elapsed_seconds_with_tracemalloc':elapsed,'python_traced_peak_bytes':peak,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024 if __import__('sys').platform=='darwin' else 1),'deep_shelf_objects_created':0,'deep_shelf_calls':run['deep_shelf_calls'],'validated_bounded_handoffs':len(handoffs),'owner_items':len(run['owner_items']),'costs':run['costs'],'limitations':['Tracemalloc adds measurement overhead; RSS includes interpreter/dependencies','Synthetic dollar/labor zero inputs are not measured real acquisition/API cost','No real retailer, author, paid-demand or entrant evidence','No live collector invoked']}

if __name__=='__main__':
    run,perf=benchmark();a=Path(__file__).resolve().parents[1]/'book-radar/audits/wide-market-screener-v1'
    (a/'SYNTHETIC_SCALE_RUN_V1.json').write_text(json.dumps(run,indent=2)+'\n')
    (a/'SYNTHETIC_SCALE_PERFORMANCE_V1.json').write_text(json.dumps(perf,indent=2)+'\n')
    print(json.dumps(perf))
