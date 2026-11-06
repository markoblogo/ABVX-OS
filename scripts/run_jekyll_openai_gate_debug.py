import json, os, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'artifacts/jekyll-authenticated-provider-gate-v5/provider-gate.json'
OUT=ROOT/'artifacts/jekyll-authenticated-provider-gate-v5-debug'; OUT.mkdir(parents=True,exist_ok=True)
blocks=json.loads((ROOT/'artifacts/jekyll-toki-pona-regression-v2/source-blocks.json').read_text())
wanted={'b0005':'A will/conditionality','b0007':'B Utterson inference','b0013':'C Lanyon opinion','b0028':'D letter/document claim','b0024':'E identity/spoiler boundary'}
profile=json.loads((ROOT/'artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json').read_text())
base='''Translate ONLY this source block into natural readable Toki Pona. Preserve conditionality, uncertainty, speaker/document status, speech act, character knowledge, and spoiler boundary. Do not add explanation or reveal Jekyll/Hyde identity. Use the entity ledger. Return exactly two lines: TRANSLATION: <text> and NOTES: <brief risk or NONE>.\nENTITY LEDGER:\n'''+json.dumps(profile,ensure_ascii=False)+'\nSOURCE:\n'
model=os.environ.get('JEKYLL_PROVIDER_MODEL','gpt-5.6-sol'); key=os.environ['OPENAI_API_KEY']
run={'provider':'OpenAI Responses API','model':model,'config':{'reasoning_effort':'medium','max_output_tokens':2400,'timeout_seconds':120,'retry_policy':'none','extraction':'output[].content[].text'},'blocks':[]}
for b in blocks:
 bid=b['block_id'].split(':')[-1]
 if bid not in wanted: continue
 req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps({'model':model,'input':base+b['source_text'],'reasoning':{'effort':'medium'},'max_output_tokens':2400,'store':False}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=120) as resp: payload=json.load(resp)
 except Exception as e:
  run['blocks'].append({'blockId':b['block_id'],'category':wanted[bid],'status':'NETWORK_OR_PROVIDER_ERROR','errorType':type(e).__name__,'error':str(e)[:500]})
  break
 items=payload.get('output') or []
 visible=[]; types=[]
 for item in items:
  types.append(item.get('type'))
  for c in item.get('content') or []:
   if c.get('type') in ('output_text','text') and c.get('text'): visible.append(c['text'])
 rec={'blockId':b['block_id'],'category':wanted[bid],'status':payload.get('status'),'responseId':payload.get('id'),'incompleteDetails':payload.get('incomplete_details'),'outputItemTypes':types,'outputTextLength':sum(map(len,visible)),'visibleText':'\n'.join(visible),'usage':payload.get('usage'),'model':payload.get('model')}
 run['blocks'].append(rec)
(OUT/'diagnostic.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'out':str(OUT/'diagnostic.json'),'blocks':len(run['blocks']),'visible':sum(x.get('outputTextLength',0)>0 for x in run['blocks'])}))
