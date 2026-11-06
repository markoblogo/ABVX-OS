#!/usr/bin/env python3
"""Local OpenAI second pass for the five approved Jekyll V7 blocks."""
import argparse, hashlib, json, os, sys, time, urllib.error, importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; V7=ROOT/'artifacts/jekyll-toki-pona-real-regression-v7'; QA=V7/'semantic-qa.json'; SRC=ROOT/'artifacts/jekyll-toki-pona-regression-v2/source-blocks.json'; LEDGER=ROOT/'artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json'; OUT=V7/'second-pass'; TARGETS={'b0005','b0013','b0014','b0028','b0038'}
spec=importlib.util.spec_from_file_location('v7runner',ROOT/'scripts/run_jekyll_openai_regression_v7.py'); v7=importlib.util.module_from_spec(spec); spec.loader.exec_module(v7)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n'); tmp.replace(path)
def queue():
 q=json.loads(QA.read_text()); source={x['block_id']:x for x in json.loads(SRC.read_text())}; originals={x['blockId']:x for x in json.loads((V7/'combined-output.json').read_text())['completed']}; rows=[]
 for item in q['records']:
  short=item['blockId'].split(':')[-1]
  if item['classification']=='SECOND_PASS_REQUIRED' and short in TARGETS: rows.append({'qa':item,'source':source[item['blockId']],'original':originals[item['blockId']]})
 if {x['source']['block_id'].split(':')[-1] for x in rows} != TARGETS: raise RuntimeError('second-pass queue mismatch')
 return rows
def make_prompt(row,ledger):
 s=row['source']; o=row['original']; q=row['qa']
 return f'''Revise ONLY the identified defect in this Toki Pona literary translation. Preserve every good semantic choice from the original and do not gratuitously rewrite it. Return exactly two lines: TRANSLATION: <revised Toki Pona> and NOTES: <brief risk or NONE>. Provider NOTES are not QA evidence.
SOURCE BLOCK [{s['block_id']}]:
{s['source_text']}
ORIGINAL V7 TRANSLATION:
{o['translation']}
EXACT QA DEFECT: {q['defect']}
REQUIRED PRESERVATION: {q['requiredPreservation']}
ENTITY / NAME LEDGER: {json.dumps(ledger,ensure_ascii=False)}
KNOWLEDGE TYPE: {s.get('knowledge_type')}
SPOILER CONSTRAINTS: {s.get('spoiler_constraints')}
Specific rules: preserve claims as claims, opinions as opinions, inferences as inferences, document statements as document statements, and do not reveal Jekyll/Hyde identity early.'''
def valid(x): return x.get('status')=='completed' and x.get('incompleteDetails') is None and bool(x.get('visibleOutput','').strip()) and bool(x.get('revisedTranslation','').strip())
def main(argv=None):
 ap=argparse.ArgumentParser(description='Run the approved five-block Jekyll V7 OpenAI second pass locally.'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--resume',action='store_true'); args=ap.parse_args(argv)
 rows=queue(); ledger=json.loads(LEDGER.read_text()); OUT.mkdir(parents=True,exist_ok=True); model=os.environ.get('JEKYLL_PROVIDER_MODEL','gpt-5.6-sol')
 existing={p.stem:json.loads(p.read_text()) for p in OUT.glob('*.json')} if args.resume else {}
 print(json.dumps({'queued':5,'blocks':[r['source']['block_id'] for r in rows],'model':model,'reasoning':'low','maxOutputTokens':3000,'output':str(OUT)}))
 if args.dry_run: return 0
 if not os.environ.get('OPENAI_API_KEY'): print('AUTH_REQUIRED',file=sys.stderr); return 2
 completed=[]; failed=[]; retried=0
 for i,row in enumerate(rows,1):
  s,o,q=row['source'],row['original'],row['qa']; key=s['block_id'].replace(':','__'); source_hash=s['source_hash']; defect_hash=sha(q['defect']); original_hash=sha(o['translation']); old=existing.get(key)
  if args.resume and old and old.get('sourceHash')==source_hash and old.get('originalTranslationHash')==original_hash and old.get('defectHash')==defect_hash and valid(old): completed.append(old); print(f'[{i}/5] {key} SKIP'); continue
  rec={'blockId':s['block_id'],'sourceHash':source_hash,'source':s['source_text'],'originalTranslation':o['translation'],'originalTranslationHash':original_hash,'qaDefect':q['defect'],'defectHash':defect_hash,'requiredPreservation':q['requiredPreservation'],'attempts':[],'model':model,'provider':'OpenAI Responses API'}
  for label,reasoning,limit in [('primary','low',3000),('max-token-retry','low',5000)]:
   for network_try in range(3):
    try:
     payload=v7.call(make_prompt(row,ledger),model,reasoning,limit,180); visible,trans,notes,types=v7.extract(payload); rec['attempts'].append({'label':label,'status':payload.get('status'),'incompleteDetails':payload.get('incomplete_details'),'responseId':payload.get('id'),'model':payload.get('model'),'reasoning':reasoning,'maxOutputTokens':limit,'outputItemTypes':types,'visibleOutput':visible,'revisedTranslation':trans,'notes':notes,'usage':payload.get('usage'),'elapsedMs':payload.get('_elapsed_ms')})
     if valid({'status':payload.get('status'),'incompleteDetails':payload.get('incomplete_details'),'visibleOutput':visible,'revisedTranslation':trans}): break
     if payload.get('status')!='incomplete' or (payload.get('incomplete_details') or {}).get('reason')!='max_output_tokens': break
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
     transient=isinstance(e,(urllib.error.URLError,TimeoutError)) or (isinstance(e,urllib.error.HTTPError) and (e.code==429 or e.code>=500)); rec['attempts'].append({'label':label,'status':'ERROR','errorType':type(e).__name__,'error':str(e)[:400],'networkTry':network_try+1})
     if not transient or network_try==2: break
     time.sleep(2**network_try)
   last=rec['attempts'][-1]
   if valid(last) or last.get('status')!='incomplete': break
   retried+=1
  last=rec['attempts'][-1]; rec.update({'status':last.get('status'),'incompleteDetails':last.get('incompleteDetails'),'responseId':last.get('responseId'),'visibleOutput':last.get('visibleOutput',''),'revisedTranslation':last.get('revisedTranslation',''),'notes':last.get('notes',''),'usage':last.get('usage')}); rec['success']=valid(rec); atomic(OUT/f'{key}.json',rec); (completed if rec['success'] else failed).append(rec); print(f'[{i}/5] {key} '+('PASS' if rec['success'] else 'FAIL'))
 atomic(OUT/'run-summary.json',{'queue':5,'completed':len(completed),'failed':len(failed),'retried':retried,'artifactPath':str(OUT),'blocks':completed,'failures':failed}); print(json.dumps({'completed':len(completed),'failed':len(failed),'retried':retried,'artifactPath':str(OUT)})); return 0 if not failed else 2
if __name__=='__main__': raise SystemExit(main())
