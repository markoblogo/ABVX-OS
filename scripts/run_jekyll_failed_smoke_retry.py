import json, os, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/jekyll-authenticated-provider-gate-v5-debug'; OUT.mkdir(parents=True,exist_ok=True)
blocks=json.loads((ROOT/'artifacts/jekyll-toki-pona-regression-v2/source-blocks.json').read_text())
profile=json.loads((ROOT/'artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json').read_text())
wanted={'b0005':'A will/conditionality','b0028':'D letter/document claim'}
base='''Translate ONLY this source block into natural readable Toki Pona. Preserve conditionality, uncertainty, speaker/document status, speech act, character knowledge, and spoiler boundary. Do not add explanation or reveal Jekyll/Hyde identity. Use the entity ledger. Return exactly two lines: TRANSLATION: <text> and NOTES: <brief risk or NONE>.\nENTITY LEDGER:\n'''+json.dumps(profile,ensure_ascii=False)+'\nSOURCE:\n'
model='gpt-5.6-sol'; key=os.environ['OPENAI_API_KEY']; result={'provider':'OpenAI Responses API','model':model,'config':{'reasoning_effort':'low','max_output_tokens':3000,'timeout_seconds':120,'retry_policy':'one bounded retry only','extraction':'output[].content[].text'},'blocks':[]}
for b in blocks:
 bid=b['block_id'].split(':')[-1]
 if bid not in wanted: continue
 req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps({'model':model,'input':base+b['source_text'],'reasoning':{'effort':'low'},'max_output_tokens':3000,'store':False}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 rec={'blockId':b['block_id'],'category':wanted[bid]}
 try:
  with urllib.request.urlopen(req,timeout=120) as resp: payload=json.load(resp)
  visible=[]; types=[]
  for item in payload.get('output') or []:
   types.append(item.get('type'))
   for c in item.get('content') or []:
    if c.get('type') in ('output_text','text') and c.get('text'): visible.append(c['text'])
  text='\n'.join(visible); rec.update({'status':payload.get('status'),'incompleteDetails':payload.get('incomplete_details'),'responseId':payload.get('id'),'model':payload.get('model'),'outputItemTypes':types,'outputTextLength':len(text),'visibleText':text,'usage':payload.get('usage')})
 except Exception as e: rec.update({'status':'NETWORK_OR_PROVIDER_ERROR','errorType':type(e).__name__,'error':str(e)[:500]})
 result['blocks'].append(rec)
(OUT/'failed-smoke-retry-low.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'out':str(OUT/'failed-smoke-retry-low.json'),'blocks':len(result['blocks']),'complete':sum(x.get('status')=='completed' and x.get('outputTextLength',0)>0 for x in result['blocks'])}))
