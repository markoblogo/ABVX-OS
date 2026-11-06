import importlib.util,json,os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('vercel_hotel',Path(__file__).resolve().parents[1]/'scripts/vercel_hotel.py');module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(module)
class SecureVercelDnsTests(unittest.TestCase):
 def test_only_public_exact_host_ipv4_answers_are_accepted(self):
  row=lambda ip,name='api.vercel.com':{'Status':0,'Answer':[{'name':name,'type':1,'data':ip}]}
  self.assertEqual(module.addresses(row('76.76.21.21')),['76.76.21.21'])
  for response in [row('127.0.0.1'),row('10.0.0.1'),row('169.254.169.254'),row('76.76.21.21','other.example'),{'Status':2},row('invalid')]:
   with self.assertRaises(ValueError):module.addresses(response)
 def test_disabled_tls_is_rejected_before_any_resolution(self):
  with patch.dict(os.environ,{'NODE_TLS_REJECT_UNAUTHORIZED':'0'}),patch.object(module,'resolve') as resolve:
   with self.assertRaises(RuntimeError):module.main(['--probe'])
   resolve.assert_not_called()
 def test_preload_scopes_lookup_and_supports_fetch_address_lists(self):
  with tempfile.TemporaryDirectory() as tmp:
   loader=Path(tmp)/'lookup.cjs';loader.write_text(module.preload(['76.76.21.21']))
   script="""const assert=require('node:assert/strict'),dns=require('node:dns');dns.lookup=(host,options,cb)=>{if(typeof options==='function')cb=options;cb(null,'127.0.0.7',4);};require(process.argv[1]);dns.lookup('api.vercel.com',{all:true},(err,rows)=>{assert.ifError(err);assert.deepEqual(rows,[{address:'76.76.21.21',family:4}]);});dns.lookup('unrelated.example',(err,address)=>{assert.ifError(err);assert.equal(address,'127.0.0.7');});dns.lookup('api.vercel.com',{family:6},err=>assert.equal(err.code,'ENOTFOUND'));dns.promises.lookup('api.vercel.com').then(row=>assert.equal(row.address,'76.76.21.21'));"""
   subprocess.run(['node','-e',script,str(loader)],check=True,capture_output=True,text=True)
if __name__=='__main__':unittest.main()
