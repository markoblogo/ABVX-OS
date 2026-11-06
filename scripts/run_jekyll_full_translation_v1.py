#!/usr/bin/env python3
"""Local, resumable full Jekyll translation runner. Dry-run is safe in Codex."""
import argparse, hashlib, json, os, re, sys, time, urllib.error, importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'artifacts/jekyll-toki-pona-preproduction-v1/source/jekyll-hyde-gutenberg-42-normalized.txt'; SM=ROOT/'artifacts/jekyll-toki-pona-preproduction-v1/source/source-manifest.json'; LEDGER=ROOT/'artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json'; OUT=ROOT/'artifacts/jekyll-toki-pona-full-v1'
HEADINGS=['STORY OF THE DOOR','SEARCH FOR MR. HYDE','DR. JEKYLL WAS QUITE AT EASE','THE CAREW MURDER CASE','INCIDENT OF THE LETTER','REMARKABLE INCIDENT OF DR. LANYON','INCIDENT AT THE WINDOW','THE LAST NIGHT','DR. LANYON’S NARRATIVE','HENRY JEKYLL’S FULL STATEMENT OF THE CASE']
MODEL='gpt-5.6-sol'; PROMPT_VERSION='jekyll-full-v1-prompt-v1'; MODEL_CONFIG={'reasoning':'low','primaryMaxOutputTokens':3000,'retryMaxOutputTokens':5000,'store':False}
spec=importlib.util.spec_from_file_location('v7runner',ROOT/'scripts/run_jekyll_openai_regression_v7.py'); v7=importlib.util.module_from_spec(spec); spec.loader.exec_module(v7)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def atomic(p,v): p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n'); t.replace(p)
def source_hash_check():
 m=json.loads(SM.read_text()); text=SRC.read_text();
 if sha(text)!=m['normalizedSha256']: raise RuntimeError('canonical normalized source hash mismatch')
 return text,m
def classify_provider_error(exc):
 """Classify provider failures without retaining raw response text or secrets."""
 if isinstance(exc,urllib.error.HTTPError):
  status=exc.code; body={}
  try:
   parsed=json.loads(exc.read(8192).decode('utf-8','replace'))
   body=parsed.get('error') if isinstance(parsed,dict) else {}
   if not isinstance(body,dict): body={}
  except Exception: body={}
  finally:
   try: exc.close()
   except Exception: pass
  safe=lambda value: value if isinstance(value,str) and re.fullmatch(r'[a-zA-Z0-9_.-]{1,64}',value) else None
  code=safe(body.get('code')); error_type=safe(body.get('type'))
  metadata={'httpStatus':status}
  if error_type: metadata['errorType']=error_type
  if code: metadata['errorCode']=code
  if code in {'insufficient_quota','billing_hard_limit_reached'} or error_type in {'insufficient_quota','billing_hard_limit_reached'}:
   return {'category':'PERSISTENT_QUOTA','hardStop':True,'retryable':False,'metadata':metadata}
  if code in {'account_deactivated','account_disabled','access_terminated'}:
   return {'category':'PERSISTENT_ACCOUNT','hardStop':True,'retryable':False,'metadata':metadata}
  if code in {'invalid_api_key','missing_api_key'} or status in {401,403}:
   return {'category':'PERSISTENT_AUTH','hardStop':True,'retryable':False,'metadata':metadata}
  if code in {'model_not_found','unsupported_model','invalid_model'}:
   return {'category':'PERSISTENT_MODEL','hardStop':True,'retryable':False,'metadata':metadata}
  if status==429:
   if code in {'rate_limit_exceeded','requests','tokens'} or error_type=='rate_limit_error':
    return {'category':'TRANSIENT_RATE_LIMIT','hardStop':False,'retryable':True,'metadata':metadata}
   return {'category':'PERSISTENT_UNKNOWN_429','hardStop':True,'retryable':False,'metadata':metadata}
  if status>=500:
   return {'category':'TRANSIENT_SERVER','hardStop':False,'retryable':True,'metadata':metadata}
  return {'category':'PERSISTENT_PROVIDER_ERROR','hardStop':True,'retryable':False,'metadata':metadata}
 if isinstance(exc,(urllib.error.URLError,TimeoutError)):
  return {'category':'TRANSIENT_NETWORK','hardStop':False,'retryable':True,'metadata':{}}
 return {'category':'PERSISTENT_UNKNOWN','hardStop':True,'retryable':False,'metadata':{}}
def budget_stop_reason(args,usage):
 if args.max_calls is not None and usage['apiCalls']>=args.max_calls: return 'MAX_CALLS_BUDGET_REACHED'
 if args.max_input_tokens is not None and usage['inputTokens']>=args.max_input_tokens: return 'MAX_INPUT_TOKENS_BUDGET_REACHED'
 if args.max_output_tokens_total is not None and usage['outputTokens']>=args.max_output_tokens_total: return 'MAX_OUTPUT_TOKENS_BUDGET_REACHED'
 return None
def segment(text):
 lines=text.splitlines(); chapters=[]; current=None; body=[]
 # The normalized source begins with a ten-heading contents list; start at the
 # second occurrence of the first canonical chapter heading.
 first=next((i for i,l in enumerate(lines) if l.strip()==HEADINGS[0]),None)
 if first is not None:
  second=next((i for i in range(first+1,len(lines)) if lines[i].strip()==HEADINGS[0]),None)
  if second is not None: lines=lines[second:]
 def flush():
  if current is not None: chapters.append((current,'\n'.join(body).strip()))
 for line in lines:
  s=line.strip()
  if s in HEADINGS and (not body or current is None):
   if current is not None: flush(); body.clear()
   current=s; continue
  if s in HEADINGS and current is not None and len('\n'.join(body))>50:
   flush(); body.clear(); current=s; continue
  if current is not None: body.append(line)
 flush()
 blocks=[]; ordinal=0
 for ci,(heading,content) in enumerate(chapters,1):
  paras=[p.strip().replace('\n',' ') for p in re.split(r'\n\s*\n',content) if p.strip()]
  chunks=[]; buf=''
  for p in paras:
   sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z“])',p) if len(p.split())>80 else [p]
   for sent in sentences:
    if buf and len((buf+' '+sent).split())>70: chunks.append(buf); buf=''
    buf=(buf+' '+sent).strip()
  if buf: chunks.append(buf)
  for si,c in enumerate(chunks,1):
   ordinal+=1; bid=f'jekyll-full-v1:chapter-{ci:02d}:block-{si:04d}'
   blocks.append({'bookId':'jekyll-full-v1','chapter':ci,'chapterTitle':heading,'section':f'chapter-{ci:02d}','blockId':bid,'sourceText':c,'sourceHash':sha(c),'blockType':'DIALOGUE' if '“' in c or '”' in c else ('DOCUMENT' if re.search(r'\b(letter|will|note|statement)\b',c,re.I) else 'NARRATION'),'ordinal':ordinal,'speaker':None,'knowledgeType':'UNKNOWN_AMBIGUOUS','entities':[],'spoilerConstraints':['PRESERVE_SOURCE_KNOWLEDGE_BOUNDARY'] if re.search(r'Jekyll|Hyde|identity|disappear|letter|will',c,re.I) else []})
 return blocks,chapters
def prompt(b,ledger): return f'''Translate ONLY TARGET SOURCE BLOCK into natural readable Toki Pona. Preserve semantic fidelity, narrative event, knowledge state, conditionality, uncertainty, speaker/document status, temporal relation, character relation and spoiler boundary. Never turn claim into fact, opinion into narrator fact, inference into fact, possibility into certainty, condition into unconditional event, question into statement, fear into observed fact, document claim into narrator fact, or reveal Jekyll/Hyde identity prematurely. Use canonical vocabulary and entity ledger. Return exactly: TRANSLATION: <text> and NOTES: <brief risk or NONE>.\nCHAPTER: {b['chapterTitle']}\nBLOCK TYPE: {b['blockType']}\nCONSTRAINTS: {b['spoilerConstraints']}\nENTITY LEDGER: {json.dumps(ledger,ensure_ascii=False)}\nTARGET SOURCE BLOCK [{b['blockId']}]:\n{b['sourceText']}'''
def main(argv=None):
 ap=argparse.ArgumentParser(description='Run the canonical full Jekyll Toki Pona translation locally.'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--resume',action='store_true'); ap.add_argument('--chapter',type=int); ap.add_argument('--block'); ap.add_argument('--max-calls',type=int,help='Hard cap on provider calls for this invocation.'); ap.add_argument('--max-input-tokens',type=int,help='Stop before the next call once observed cumulative input reaches this cap (one-call overshoot is possible).'); ap.add_argument('--max-output-tokens-total',type=int,help='Stop before the next call once observed cumulative output reaches this cap (one-call overshoot is possible).'); args=ap.parse_args(argv)
 for name,value in (('--max-calls',args.max_calls),('--max-input-tokens',args.max_input_tokens),('--max-output-tokens-total',args.max_output_tokens_total)):
  if value is not None and value<1: ap.error(f'{name} must be a positive integer')
 text,manifest=source_hash_check(); blocks,chapters=segment(text); ledger=json.loads(LEDGER.read_text()); OUT.mkdir(parents=True,exist_ok=True)
 atomic(OUT/'source-manifest.json',manifest); atomic(OUT/'segmentation-manifest.json',{'sourceSha256':manifest['normalizedSha256'],'sourceWords':len(text.split()),'chapters':len(chapters),'blocks':len(blocks),'averageWordsPerBlock':len(text.split())/len(blocks),'blocksData':blocks})
 selected=[b for b in blocks if (not args.chapter or b['chapter']==args.chapter) and (not args.block or b['blockId']==args.block)]; existing={p.stem:json.loads(p.read_text()) for p in (OUT/'blocks').glob('*.json')} if args.resume else {}; pending=[b for b in selected if not (existing.get(b['blockId'].replace(':','__'),{}).get('sourceHash')==b['sourceHash'] and existing.get(b['blockId'].replace(':','__'),{}).get('success'))]
 print(json.dumps({'sourceWords':len(text.split()),'chapters':len(chapters),'blocks':len(blocks),'selected':len(selected),'pending':len(pending),'provider':'OpenAI Responses API','model':MODEL,'promptVersion':PROMPT_VERSION,'configuration':MODEL_CONFIG,'maxCalls':args.max_calls,'maxInputTokens':args.max_input_tokens,'maxOutputTokensTotal':args.max_output_tokens_total,'output':str(OUT)}))
 if args.dry_run:return 0
 if pending and (args.max_calls is None or (args.max_input_tokens is None and args.max_output_tokens_total is None)):
  print('COST_PREFLIGHT_REQUIRED: set --max-calls and at least one cumulative token budget',file=sys.stderr); return 2
 if not os.environ.get('OPENAI_API_KEY'): print('AUTH_REQUIRED',file=sys.stderr); return 2
 completed=[]; failed=[]; stop_reason=None; usage={'apiCalls':0,'retries':0,'inputTokens':0,'cachedInputTokens':0,'cacheWriteInputTokens':0,'outputTokens':0,'reasoningTokens':0,'visibleTranslationCharacters':0}
 for i,b in enumerate(selected,1):
  key=b['blockId'].replace(':','__'); old=existing.get(key)
  if args.resume and old and old.get('sourceHash')==b['sourceHash'] and old.get('success'): completed.append(old); print(f'[{i:04d}/{len(selected)}] {b["blockId"]} SKIP'); continue
  if budget_stop_reason(args,usage): stop_reason=budget_stop_reason(args,usage); break
  prompt_text=prompt(b,ledger); prompt_hash=sha(prompt_text); rec={'blockId':b['blockId'],'sourceHash':b['sourceHash'],'source':b['sourceText'],'provider':'OpenAI Responses API','model':MODEL,'promptVersion':PROMPT_VERSION,'promptHash':prompt_hash,'configuration':MODEL_CONFIG,'attempts':[]}
  for label,limit in [('primary',3000),('max-token-retry',5000)]:
   for network_try in range(3):
    if budget_stop_reason(args,usage): stop_reason=budget_stop_reason(args,usage); break
    usage['apiCalls']+=1
    try:
     payload=v7.call(prompt_text,MODEL,'low',limit,180); visible,trans,notes,types=v7.extract(payload); response_usage=payload.get('usage') or {}; input_details=response_usage.get('input_tokens_details') or {}; output_details=response_usage.get('output_tokens_details') or {}; usage['inputTokens']+=response_usage.get('input_tokens',0); usage['cachedInputTokens']+=input_details.get('cached_tokens',0); usage['cacheWriteInputTokens']+=input_details.get('cache_write_tokens',0); usage['outputTokens']+=response_usage.get('output_tokens',0); usage['reasoningTokens']+=output_details.get('reasoning_tokens',0); rec['attempts'].append({'label':label,'status':payload.get('status'),'incompleteDetails':payload.get('incomplete_details'),'responseId':payload.get('id'),'promptVersion':PROMPT_VERSION,'promptHash':prompt_hash,'reasoningEffort':'low','maxOutputTokens':limit,'visibleOutput':visible,'translation':trans,'notes':notes,'usage':response_usage,'outputItemTypes':types})
     if payload.get('status')=='completed' and payload.get('incomplete_details') is None and trans: break
     if payload.get('status')!='incomplete' or (payload.get('incomplete_details') or {}).get('reason')!='max_output_tokens': break
     usage['retries']+=1
     break
    except Exception as e:
     policy=classify_provider_error(e)
     rec['attempts'].append({'label':label,'status':'ERROR','errorClass':policy['category'],'errorMetadata':policy['metadata'],'networkTry':network_try+1})
     if policy['hardStop']:
      stop_reason=policy['category']; break
     if network_try<2:
      usage['retries']+=1; time.sleep(2**network_try); continue
     stop_reason=policy['category']+'_RETRIES_EXHAUSTED'; break
   last=rec['attempts'][-1]
   if stop_reason or (last.get('status')=='completed' and last.get('incompleteDetails') is None and last.get('translation')) or last.get('status')!='incomplete' or (last.get('incompleteDetails') or {}).get('reason')!='max_output_tokens': break
  last=rec['attempts'][-1]; rec.update({'status':last.get('status'),'incompleteDetails':last.get('incompleteDetails'),'responseId':last.get('responseId'),'visibleOutput':last.get('visibleOutput',''),'translation':last.get('translation',''),'notes':last.get('notes',''),'usage':last.get('usage')}); rec['success']=rec['status']=='completed' and rec['incompleteDetails'] is None and bool(rec['visibleOutput'].strip()) and bool(rec['translation'].strip());
  if rec['success']: usage['visibleTranslationCharacters']+=len(rec['translation'])
  atomic(OUT/'blocks'/f'{key}.json',rec); (completed if rec['success'] else failed).append(rec); print(f'[{i:04d}/{len(selected)}] {b["blockId"]} '+('PASS' if rec['success'] else 'FAIL'))
  if stop_reason: break
 atomic(OUT/'run-manifest.json',{'sourceBlocks':len(blocks),'selected':len(selected),'completed':len(completed),'failed':len(failed),'unattempted':max(0,len(selected)-len(completed)-len(failed)),'stopReason':stop_reason,'provider':'OpenAI Responses API','model':MODEL,'promptVersion':PROMPT_VERSION,'configuration':MODEL_CONFIG,'updatedAt':time.time()}); atomic(OUT/'combined-primary.json',{'completed':completed,'failures':failed}); atomic(OUT/'failures.json',failed); atomic(OUT/'usage-summary.json',usage); return 0 if not failed and not stop_reason else 2
if __name__=='__main__': raise SystemExit(main())
