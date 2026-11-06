"""Fixed publication-stage commands; no approval, Git write, merge or deployment authority."""
from __future__ import annotations
import argparse,json,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from abvx_harness.publication_learning import folder,utc,_load_item,_approval_fingerprint,markdown_parts


def commands(root,site,run,packets,items,base,phase,pr,rework,cortex,recipe):
    npm=lambda name,*args:['npm','run',name,'--',*args]
    abvx=[str(root/'bin/abvx')]
    # Exercise the actual headless runtime: executablePath() may point to a
    # full browser even when this site's supported headless-only install works.
    preflight=[('browser-preflight',['node','--input-type=module','-e',
                "import {chromium} from 'playwright'; const browser=await chromium.launch({headless:true,timeout:15000}); await browser.close();"],site)]
    checks=[('release-check',npm('content:release-check','--base',base),site)]
    checks += [('reuse-'+item,abvx+['publication','check','--item',item,'--site-root',str(site),'--reuse-checks'],root) for item in items]
    if phase=='local':
        packet_args=[arg for packet in packets for arg in ('--packet',str(packet))]
        plan=[('dry-run',npm('content:publish','--base',base,*packet_args,'--dry-run'),site),
              ('write',npm('content:publish','--base',base,*packet_args,'--write'),site),
              ('prebuild',npm('prebuild'),site),
              ('boundary',npm('content:publication-boundary','--base',base),site)]
        if recipe:plan.append(('recipe-export',npm('export:kitchen-notes'),site))
        return preflight+plan+checks
    if phase=='check':return preflight+checks
    if phase=='preview':return [('preview',npm('content:release-ready','--preview','--pr',str(pr)),site)]
    if phase=='production':
        close=abvx+['publication','complete-cycle','--run',run,'--site-root',str(site),'--rework-count',str(rework)]
        if cortex:close+=['--cortex-root',str(cortex)]
        return [('production',npm('content:release-ready','--production','--pr',str(pr)),site),('close-cycle',close,root)]
    raise ValueError('Unknown phase')


def execute(plan,directory,phase):
    """Retain every attempt, including failure; never reset the publication clock."""
    journal=directory/'route-attempts.json'
    attempts=json.loads(journal.read_text()) if journal.exists() else []
    attempt={'phase':phase,'startedAt':utc(),'status':'RUNNING','steps':[]}
    attempts.append(attempt);number=len(attempts)
    def save():journal.write_text(json.dumps(attempts,indent=2)+'\n')
    save()
    try:
        for name,argv,cwd in plan:
            start=time.monotonic();step={'name':name,'startedAt':utc(),'argv':list(map(str,argv)),'cwd':str(cwd)}
            attempt['steps'].append(step);save()
            result=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            log=directory/f'route-{number}-{name}.log';log.write_text(result.stdout)
            step.update(endedAt=utc(),durationMs=round((time.monotonic()-start)*1000),exitCode=result.returncode,log=log.name);save()
            print(name+(': PASS' if result.returncode==0 else ': FAIL'),flush=True)
            if result.returncode:raise RuntimeError('Stage failed; retained log: '+str(log))
        attempt['status']='PASS'
    except BaseException:
        attempt['status']='FAIL';raise
    finally:
        attempt['endedAt']=utc();save()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True);parser.add_argument('--site-root',required=True,type=Path)
    parser.add_argument('--base',required=True);parser.add_argument('--phase',required=True,choices=['local','check','preview','production'])
    parser.add_argument('--pr',type=int);parser.add_argument('--rework-count',type=int);parser.add_argument('--cortex-root',type=Path)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();site=args.site_root.resolve();directory=folder(ROOT,args.run)
    cycle=json.loads((directory/'cycle.json').read_text())
    if (directory/'outcome.json').exists() or (directory/'aborted.json').exists():parser.error('Cycle is terminal; use transfer for a pending Cortex return')
    if not re.fullmatch('[a-f0-9]{40}',args.base):parser.error('Full base SHA required')
    if args.phase in ('preview','production') and (not args.pr or args.pr<1):parser.error('Positive PR number required')
    if args.phase=='production' and (args.rework_count is None or args.rework_count<0):parser.error('Explicit actual rework count required')
    origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=site,text=True).strip()
    if origin not in ('https://github.com/markoblogo/ABVXsite.git','git@github.com:markoblogo/ABVXsite.git','https://github.com/markoblogo/ABVXsite'):parser.error('ABVXsite checkout required')
    packets=[];recipe=False
    for item_id in cycle['itemIds']:
        item=_load_item(ROOT,item_id)
        if item['status']!='PUBLISH_PACKET_EMITTED' or item['human_gate'].get('approved_content_sha256')!=_approval_fingerprint(item):parser.error('Approved current handoff required')
        packet=(ROOT/item['publication']['packet_ref']).resolve()
        if not packet.is_relative_to(ROOT.resolve()/'content/publish-packets'):parser.error('Packet outside content handoff directory')
        data=json.loads(packet.read_text())
        if data.get('payload')!=item['payload'] or data.get('slug')!=item['slug'] or data.get('item_id')!=item_id:parser.error('Packet differs from approved item')
        packets.append(packet);recipe=recipe or item.get('kind')=='recipe' or markdown_parts(item['payload']['source_markdown'])[0].get('collection')=='kitchen-notes'
    plan=commands(ROOT,site,args.run,packets,cycle['itemIds'],args.base,args.phase,args.pr,args.rework_count,args.cortex_root,recipe)
    if not args.execute:
        print(json.dumps([{'step':name,'argv':argv,'cwd':str(cwd)} for name,argv,cwd in plan],indent=2));return
    previous=json.loads((directory/'route-attempts.json').read_text()) if (directory/'route-attempts.json').exists() else []
    if args.phase=='local' and previous:parser.error('Local route already attempted; inspect evidence and use explicit check after repair, never replay writes blindly')
    if args.phase=='preview' and any(row['phase']=='preview' and row['status']=='PASS' for row in previous):parser.error('Stage already passed; reuse retained evidence')
    execute(plan,directory,args.phase)

if __name__=='__main__':main()
