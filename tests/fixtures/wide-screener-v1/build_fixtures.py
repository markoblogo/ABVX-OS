"""Rebuild explicitly SYNTHETIC offline fixtures; performs no acquisition."""
import copy
import hashlib
import json
from pathlib import Path
from abvx_harness.book_radar_wide import cluster_id

HERE=Path(__file__).resolve().parent
def base():
    sha=hashlib.sha256((HERE/'raw.txt').read_bytes()).hexdigest()
    evidence=[{'id':f'e{i}','path':'raw.txt','sha256':sha,'kind':'EXTERNAL','source_uri':f'https://origin-{i}.example/retained','market':'Amazon.com','language':'EN'} for i in (1,2)]
    return {'schema_version':'book-radar-wide-input/v1','run_id':'synthetic','origin':'SYNTHETIC','as_of':'2026-10-03T12:00:00Z','evidence':evidence,'signals':[],'quick_screens':[],'acquisition_costs':{s:{'external_api_usd':0,'machine_usd':0,'manual_minutes':0,'owner_minutes':0} for s in ('RAW','NORMALIZE','CORROBORATE','QUICK_SCREEN','QUEUE')}}

def signals(p,index=0,n=5,reading=True,subject=None):
    bucket=['EVERGREEN_PRACTICAL','PROFESSIONAL_TECHNICAL','HOBBY_ENTHUSIAST','REFERENCE_UTILITY','LANGUAGE_LEARNING'][index%5]
    job={'audience':f'synthetic audience {index}','job':f'synthetic practical job {index}','intent':'BOOK_SERVED_LEARNING_INTENT' if reading else 'GENERAL_INFORMATION_INTENT','query':f'synthetic book guide {index}','subject':subject or f'subject {index}','category':f'category {index%10}','bucket':bucket,'mechanism':['EVERGREEN_PROBLEM','PROFESSIONAL_CHANGE','HOBBY_UTILITY','REFERENCE_UTILITY','LONG_TAIL_SEARCH'][index%5]}
    for j in range(n):
        e=p['evidence'][j%2]
        p['signals'].append({'schema_version':'book-radar-wide-signal/v1','signal_id':f's{index}-{j}','observed_at':'2026-10-03T10:00:00Z','source_family':'BOOK_MARKET' if j%2==0 else 'COMMUNITY','source':e['source_uri'],'market':e['market'],'language':e['language'],'raw_phrase':f'query variant {index}-{j}','evidence_ids':[e['id']],'freshness':{'source_date':'2026-10-02','date_basis':'ACTIVITY'},'initial_intent':job['intent'],'job_support':'SUPPORTS','provenance':{'kind':'EXTERNAL','recorded_by':'fixture-generator'},'buyer_job':copy.deepcopy(job)})
    return job

def quick(p,job,**changes):
    e=p['evidence'][0]
    vals={'book_serving':'PRESENT','activity':'PRESENT','entrants':'PRESENT','incumbent':'ABSENT','sponsored':'ABSENT','query_relevance':'PRESENT',**changes}
    features={k:{'value':v,'evidence_ids':[] if v=='UNKNOWN' else [e['id']],'observation_ids':[] if v=='UNKNOWN' else ['o1']} for k,v in vals.items()}
    q={'cluster_id':cluster_id(job,e['market'],e['language']),'market':e['market'],'language':e['language'],'query':job['query'],'observed_at':'2026-10-03T10:00:00Z','organic_depth_reached':5,'sponsored_depth_reached':1,'sample_complete':True,'context':{'delivery':'SYNTHETIC context','locale':e['language'],'signed_in':'NO','sort':'Featured'},'observations':[{'id':'o1','text':'SYNTHETIC offline observation. Book-serving sample, bounded activity/entrant/incumbent assessments only; no real listing, sales or cold-start assertion. Feature values for this case: '+json.dumps(vals,sort_keys=True),'evidence_ids':[e['id']]}],'features':features,'rights':'NO_OBVIOUS_BLOCK','value_of_information':'HIGH'}
    p['quick_screens'].append(q);return q

def build():
    HERE.mkdir(parents=True,exist_ok=True);(HERE/'raw.txt').write_text('SYNTHETIC test evidence for A-M and scale; fictional origins, no live market observations.\n')
    cases={};packets={}
    for key in 'ABCDEFGHIJKLM':
        p=base();p['run_id']='synthetic-case-'+key;job=signals(p,reading=key!='A');q=None
        if key not in ('A','F','G','H','I'):q=quick(p,job)
        expected={'A':'KILL','B':'KILL','C':'KILL','D':'INVESTIGATE','E':'KILL','F':'PARK','G':'PARK','H':'PARK','I':'MIXED','J':'PARK','K':'PARK','L':'KILL','M':'INVESTIGATE'}[key]
        if key in ('B','L'):q['features']['activity']['value']='ABSENT'
        if key=='C':q['features']['incumbent']['value']='PRESENT'
        if key=='E':q['event']={'event_date':'2026-09-30','information_half_life_days':5,'book_time_to_market_days':20,'evidence_ids':['e1']}
        if key in ('F','H'):
            n=20 if key=='H' else 5;p['signals']=[];job=signals(p,n=n);p['aliases']={}
            for j,s in enumerate(p['signals']):
                alias=f'legal AI workflow variant {j}';s['buyer_job']['job']=alias;p['aliases'][alias]=job['job']
        if key=='I':
            quick(p,job);fr=copy.deepcopy(p['signals'][0]);fr.update(signal_id='fr-1',market='Amazon.fr',language='FR',evidence_ids=['fr-e']);e=copy.deepcopy(p['evidence'][0]);e.update(id='fr-e',market='Amazon.fr',language='FR');p['evidence'].append(e);p['signals'].append(fr)
        if key in ('J','K'):
            q['features']['activity']={'value':'UNKNOWN','evidence_ids':[],'observation_ids':[]};q['value_of_information']='HIGH' if key=='J' else 'LOW'
        if key=='L':q['factory_cost_class']='VERY_LOW'
        if key=='M':q['factory_cost_class']='HIGH'
        filename='case-'+key+'.json';packets[filename]=p;cases[key]={'file':filename,'expected':expected}
    p=base();p['run_id']='synthetic-scale-1000'
    for i in range(200):
        job=signals(p,index=i,reading=i<40)
        if i<40:
            q=quick(p,job)
            if 10<=i<20:q['features']['activity']['value']='ABSENT'
            elif 20<=i<30:q['features']['incumbent']['value']='PRESENT'
            elif 30<=i<40:q['features']['activity']={'value':'UNKNOWN','evidence_ids':[],'observation_ids':[]}
    packets['scale-1000.json']=p;retained=[]
    for filename,packet in packets.items():
        for q in packet['quick_screens']:
            vals={k:v['value'] for k,v in q['features'].items()}
            q['observations'][0]['text']='SYNTHETIC bounded fixture conditions for '+filename+': '+json.dumps({'features':vals,'organic_depth':q['organic_depth_reached'],'rights':q['rights'],'event':q.get('event')},sort_keys=True)+'. No real sales or cold-start assertion.'
            retained.append({'run':packet['run_id'],'cluster_id':q['cluster_id'],'text':q['observations'][0]['text']})
        retained.extend({'run':packet['run_id'],'source':s['source'],'phrase':s['raw_phrase'],'buyer_job':s['buyer_job'],'job_support':s.get('job_support'),'synthetic':True} for s in packet['signals'])
    (HERE/'raw.txt').write_text(json.dumps({'origin':'SYNTHETIC','observations':retained},indent=2)+'\n');sha=hashlib.sha256((HERE/'raw.txt').read_bytes()).hexdigest()
    for filename,packet in packets.items():
        for e in packet['evidence']:e['sha256']=sha
        (HERE/filename).write_text(json.dumps(packet,indent=2)+'\n')
    (HERE/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
if __name__=='__main__':build()
