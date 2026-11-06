import json, os, time, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/jekyll-authenticated-provider-gate-v5'; OUT.mkdir(parents=True,exist_ok=True)
blocks=json.loads((ROOT/'artifacts/jekyll-toki-pona-regression-v2/source-blocks.json').read_text())
wanted={'b0005':'A will/conditionality','b0007':'B Utterson inference','b0013':'C Lanyon opinion','b0028':'D letter/document claim','b0024':'E identity/spoiler boundary'}
sel=[b for b in blocks if b['block_id'].split(':')[-1] in wanted]
profile=json.loads((ROOT/'artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json').read_text())
prompt_base='''You are a careful literary translator into natural, readable Toki Pona. Translate ONLY the source block below. Preserve semantic fidelity, plot logic, knowledge state, conditionality, speaker/document status, uncertainty, and speech act. Do not turn claims into facts, opinion into narrator fact, possibility into certainty, condition into unconditional event, question into statement, fear into observed event, or character inference into objective truth. Do not reveal Jekyll/Hyde identity beyond the source. Use established entity spellings from the provided ledger; do not expand vocabulary or add explanations. Return exactly: TRANSLATION: <Toki Pona text>\nNOTES: <brief risks or NONE>.\n\nENTITY LEDGER:\n'''+json.dumps(profile,ensure_ascii=False)+'\n\nSOURCE:\n'
model=os.environ.get('JEKYLL_PROVIDER_MODEL','gpt-5.6-sol')
key=os.environ.get('OPENAI_API_KEY')
run={'provider':'OpenAI Responses API','model':model,'snapshot':None,'startedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'blocks':[],'fallbacks':[]}
for b in sel:
    bid=b['block_id']; text=prompt_base+b['source_text']
    req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps({'model':model,'input':text,'reasoning':{'effort':'high'},'max_output_tokens':1200,'store':False}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    rec={'blockId':bid,'category':wanted[bid.split(':')[-1]],'sourceText':b['source_text'],'status':'FAIL'}
    try:
        with urllib.request.urlopen(req,timeout=120) as resp:
            payload=json.load(resp)
        out=payload.get('output_text') or ''
        rec.update({'status':'RECEIVED','output':out,'responseId':payload.get('id'),'usage':payload.get('usage'),'model':payload.get('model')})
        run['snapshot']=payload.get('model') or run['snapshot']
    except Exception as e:
        rec.update({'errorType':type(e).__name__,'error':str(e)[:500]})
        run['blocks'].append(rec); break
    run['blocks'].append(rec)
(OUT/'provider-gate.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'out':str(OUT/'provider-gate.json'),'blocks':len(run['blocks']),'received':sum(x['status']=='RECEIVED' for x in run['blocks']),'model':model},ensure_ascii=False))
