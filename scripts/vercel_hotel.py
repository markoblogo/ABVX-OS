#!/usr/bin/env python3
"""Run the existing Vercel CLI with scoped secure DNS; no system/network changes."""
import ipaddress,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

HOST='api.vercel.com'
RESOLVER='https://cloudflare-dns.com/dns-query?name='+HOST+'&type=A'

def addresses(answer):
    if answer.get('Status')!=0:raise ValueError('Resolver did not return success')
    found=[]
    for row in answer.get('Answer',[]):
        if row.get('type')!=1 or row.get('name','').rstrip('.')!=HOST:continue
        ip=ipaddress.ip_address(row['data'])
        if ip.version!=4 or not ip.is_global:raise ValueError('Non-public resolver answer rejected')
        if str(ip) not in found:found.append(str(ip))
    if not found:raise ValueError('No public Vercel IPv4 answer')
    return found

def resolve():
    # Official Cloudflare anycast bootstrap IPs. HTTPS still validates the
    # cloudflare-dns.com certificate and SNI. No credentials enter this request.
    for bootstrap in ('1.1.1.1','1.0.0.1'):
        result=subprocess.run(['curl','--silent','--show-error','--fail','--connect-timeout','4','--max-time','10','--resolve','cloudflare-dns.com:443:'+bootstrap,'-H','accept: application/dns-json',RESOLVER],capture_output=True,text=True)
        if result.returncode==0:return addresses(json.loads(result.stdout))
    raise RuntimeError('Secure DNS unavailable; no insecure/system-DNS fallback attempted')

def preload(ips):
    return r'''const dns=require('node:dns');
const {syncBuiltinESMExports}=require('node:module');
const host='api.vercel.com',addresses=IPS.map(address=>({address,family:4}));
const original=dns.lookup,originalPromise=dns.promises.lookup.bind(dns.promises);
function selected(options){const family=typeof options==='number'?options:options?.family;if(family===6||family==='IPv6'){const e=new Error('No scoped IPv6 answer');e.code='ENOTFOUND';throw e;}return options?.all?addresses.map(x=>({...x})):{...addresses[0]};}
dns.lookup=function(name,options,callback){if(name!==host)return original.apply(this,arguments);if(typeof options==='function'){callback=options;options={};}queueMicrotask(()=>{try{const result=selected(options);if(options?.all)callback(null,result);else callback(null,result.address,result.family);}catch(error){callback(error);}});};
dns.promises.lookup=async(name,options)=>name===host?selected(options):originalPromise(name,options);
syncBuiltinESMExports();
'''.replace('IPS',json.dumps(ips))

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if os.environ.get('NODE_TLS_REJECT_UNAUTHORIZED')=='0':raise RuntimeError('Refusing disabled TLS validation')
    if argv and argv[0]=='--':argv.pop(0)
    probe=argv==['--probe']
    if not argv:raise ValueError('Use --probe or -- <existing vercel CLI arguments>')
    ips=resolve()
    with tempfile.TemporaryDirectory(prefix='abvx-vercel-dns-') as tmp:
        loader=Path(tmp)/'lookup.cjs';loader.write_text(preload(ips))
        env={**os.environ,'NODE_OPTIONS':(os.environ.get('NODE_OPTIONS','')+' --require='+json.dumps(str(loader))).strip()}
        if probe:
            node=shutil.which('node')
            if not node:raise RuntimeError('Existing Node.js required')
            cmd=[node,'-e',"require('node:https').get('https://api.vercel.com/v2/user',r=>{console.log(JSON.stringify({host:'api.vercel.com',tlsAuthorized:r.socket.authorized,httpStatus:r.statusCode}));r.resume();process.exitCode=r.socket.authorized&&r.statusCode===403?0:r.socket.authorized&&r.statusCode===401?0:1;}).on('error',e=>{console.error(e.code||e.message);process.exitCode=1;});"]
        else:
            cli=shutil.which('vercel')
            if not cli:raise RuntimeError('Existing Vercel CLI required; nothing installed automatically')
            cmd=[cli,*argv]
        return subprocess.run(cmd,env=env).returncode

if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,ValueError,json.JSONDecodeError) as error:print(str(error),file=sys.stderr);sys.exit(1)
