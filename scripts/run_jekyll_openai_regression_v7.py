#!/usr/bin/env python3
"""Local, resumable real-provider runner for the fixed 40-block Jekyll sample."""
import argparse, hashlib, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'artifacts/jekyll-toki-pona-regression-v2/source-blocks.json'
LEDGER=ROOT/'artifacts/jekyll-toki-pona-regression-v2/entity-name-registry.json'
DEFAULT_OUT=ROOT/'artifacts/jekyll-toki-pona-real-regression-v7'

def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n'); tmp.replace(path)
def load_blocks():
    blocks=json.loads(SOURCE.read_text()); assert len(blocks)==40, f'expected 40 blocks, got {len(blocks)}'
    for b in blocks:
        if b.get('source_hash') != sha(b['source_text']): raise ValueError(f"source hash mismatch: {b['block_id']}")
    json.loads(LEDGER.read_text()); return blocks
def prompt(b, ledger):
    return f'''Translate ONLY TARGET SOURCE BLOCK into natural readable Toki Pona. Preserve semantic fidelity, plot logic, conditionality, uncertainty, speaker/document/claim status, character knowledge, inference, questions, fear, opinion, temporal relations and the spoiler boundary. Never turn claim into fact, opinion into narrator fact, possibility into certainty, condition into unconditional event, question into statement, fear into observed event, character inference into narrator truth, document claim into narrator truth, or reveal Jekyll/Hyde identity prematurely. Use canonical vocabulary and the entity ledger; do not add explanation. Return exactly two lines: TRANSLATION: <Toki Pona text> and NOTES: <brief risk or NONE>.\nBLOCK TYPE: {b.get('block_type')}\nSPEAKER: {b.get('speaker')}\nKNOWLEDGE STATE: {b.get('knowledge_type')}\nSPOILER CONSTRAINTS: {b.get('spoiler_constraints')}\nENTITY LEDGER: {json.dumps(ledger,ensure_ascii=False)}\nTARGET SOURCE BLOCK [{b['block_id']}]:\n{b['source_text']}'''
def extract(payload):
    visible=[]; types=[]
    for item in payload.get('output') or []:
        types.append(item.get('type'))
        for c in item.get('content') or []:
            if c.get('type') in ('output_text','text') and isinstance(c.get('text'),str): visible.append(c['text'])
    text='\n'.join(visible)
    trans=''; notes=''
    for line in text.splitlines():
        if line.startswith('TRANSLATION:'): trans=line.split(':',1)[1].strip()
        elif line.startswith('NOTES:'): notes=line.split(':',1)[1].strip()
    return text, trans, notes, types
def call(prompt_text, model, reasoning, max_tokens, timeout):
    key=os.environ.get('OPENAI_API_KEY')
    if not key: raise RuntimeError('AUTH_REQUIRED: OPENAI_API_KEY is not configured')
    req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps({'model':model,'input':prompt_text,'reasoning':{'effort':reasoning},'max_output_tokens':max_tokens,'store':False}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    started=time.time()
    with urllib.request.urlopen(req,timeout=timeout) as r: payload=json.load(r)
    payload['_elapsed_ms']=round((time.time()-started)*1000); return payload
def valid(rec): return rec.get('status')=='completed' and rec.get('incomplete_details') is None and rec.get('visibleOutput','').strip() and rec.get('translation','').strip()
def main(argv=None):
    ap=argparse.ArgumentParser(description='Run the exact 40-block Jekyll OpenAI regression locally.')
    ap.add_argument('--resume',action='store_true'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--block'); ap.add_argument('--output',type=Path,default=DEFAULT_OUT); ap.add_argument('--mock',action='store_true',help=argparse.SUPPRESS)
    args=ap.parse_args(argv); blocks=load_blocks(); ledger=json.loads(LEDGER.read_text())
    model=os.environ.get('JEKYLL_PROVIDER_MODEL','gpt-5.6-sol'); out=args.output; bdir=out/'blocks'; out.mkdir(parents=True,exist_ok=True)
    existing={p.stem:json.loads(p.read_text()) for p in bdir.glob('*.json')} if args.resume else {}
    selected=[b for b in blocks if not args.block or b['block_id']==args.block]
    pending=[b for b in selected if not (existing.get(b['block_id'].replace(':','__'),{}).get('sourceHash')==b['source_hash'] and valid(existing.get(b['block_id'].replace(':','__'),{})))]
    manifest={'schemaVersion':'1','run':'jekyll-toki-pona-real-regression-v7','source':str(SOURCE),'sourceCount':40,'provider':'OpenAI Responses API','model':model,'defaultConfig':{'reasoning':'low','maxOutputTokens':3000,'timeoutSeconds':180,'store':False},'updatedAt':time.time()}
    atomic(out/'run-manifest.json',manifest)
    if args.dry_run:
        print(json.dumps({'sourceBlocks':40,'pending':len(pending),'provider':'OpenAI Responses API','model':model,'reasoning':'low','maxOutputTokens':3000,'output':str(out)})); return 0
    usage={'apiCalls':0,'primaryAttempts':0,'retries':0,'inputTokens':0,'cachedInputTokens':0,'outputTokens':0,'reasoningTokens':0,'visibleTranslationCharacters':0}
    failures=[]; completed=[]
    for i,b in enumerate(selected,1):
        key=b['block_id'].replace(':','__'); old=existing.get(key)
        if old and old.get('sourceHash')==b['source_hash'] and valid(old): completed.append(old); print(f'[{i:02d}/{len(selected)}] {b["block_id"]} SKIP'); continue
        rec={'blockId':b['block_id'],'sourceText':b['source_text'],'sourceHash':b['source_hash'],'provider':'OpenAI Responses API','model':model,'attempts':[]}
        configs=[('primary','low',3000),('max-token-retry','low',5000)]
        for label,reasoning,limit in configs:
            usage['primaryAttempts']+=label=='primary'; usage['retries']+=label!='primary'
            for network_try in range(3):
             usage['apiCalls']+=1
             try:
                payload=call(prompt(b,ledger),model,reasoning,limit,180); visible,trans,notes,types=extract(payload); u=payload.get('usage') or {}
                rec['attempts'].append({'label':label,'status':payload.get('status'),'incompleteDetails':payload.get('incomplete_details'),'responseId':payload.get('id'),'reasoning':reasoning,'maxOutputTokens':limit,'outputItemTypes':types,'visibleOutput':visible,'translation':trans,'notes':notes,'usage':u,'elapsedMs':payload.get('_elapsed_ms')})
                usage['inputTokens']+=u.get('input_tokens',0); usage['cachedInputTokens']+=(u.get('input_tokens_details') or {}).get('cached_tokens',0); usage['outputTokens']+=u.get('output_tokens',0); usage['reasoningTokens']+=(u.get('output_tokens_details') or {}).get('reasoning_tokens',0)
                if valid(rec['attempts'][-1]): break
                if payload.get('status')!='incomplete' or (payload.get('incomplete_details') or {}).get('reason')!='max_output_tokens': break
                break
             except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
                transient=isinstance(e,urllib.error.URLError) or isinstance(e,TimeoutError) or (isinstance(e,urllib.error.HTTPError) and (e.code==429 or e.code>=500))
                rec['attempts'].append({'label':label,'status':'ERROR','errorType':type(e).__name__,'error':str(e)[:400],'networkTry':network_try+1})
                if not transient or network_try==2: break
                time.sleep(2**network_try)
            if rec['attempts'] and (valid(rec['attempts'][-1]) or rec['attempts'][-1].get('status')=='ERROR' or rec['attempts'][-1].get('status')!='incomplete'): break
        final=rec['attempts'][-1] if rec['attempts'] else {}; rec.update({k:final.get(k) for k in ('status','incompleteDetails','responseId','visibleOutput','translation','notes','usage')}); rec['success']=bool(valid(rec)); atomic(bdir/f'{key}.json',rec)
        if rec['success']: completed.append(rec); usage['visibleTranslationCharacters']+=len(rec.get('translation','')); print(f'[{i:02d}/{len(selected)}] {b["block_id"]} PASS')
        else: failures.append(rec); print(f'[{i:02d}/{len(selected)}] {b["block_id"]} FAIL',file=sys.stderr)
        atomic(out/'usage-summary.json',usage); atomic(out/'failures.json',failures); atomic(out/'combined-output.json',{'sourceCount':40,'completed':completed,'failures':failures})
    print(json.dumps({'completed':len(completed),'failed':len(failures),'retried':usage['retries'],'usage':usage,'artifactPath':str(out)})); return 0 if not failures else 2
if __name__=='__main__': raise SystemExit(main())
