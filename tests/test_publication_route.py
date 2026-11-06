import importlib.util,json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class RouteTests(unittest.TestCase):
 def module(self):
  spec=importlib.util.spec_from_file_location('publication_route',ROOT/'scripts/abvx_publication_route.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 def test_fixed_local_plan_reuses_checks_without_release_authority(self):
  module=self.module();plan=module.commands(Path('/os'),Path('/site'),'cycle',['/packet.json'],['item'],'a'*40,'local',None,None,None,True)
  flat=[part for _,argv,_ in plan for part in argv]
  self.assertEqual(flat.count('content:release-check'),1);self.assertIn('--reuse-checks',flat)
  for unsafe in ('approve','commit','push','merge','deploy'):self.assertNotIn(unsafe,flat)
 def test_failure_is_retained_and_stops_following_stages(self):
  module=self.module()
  with TemporaryDirectory() as tmp:
   directory=Path(tmp);commands=[('first',['false'],directory),('second',['true'],directory)]
   with patch.object(module.subprocess,'run') as run:
    run.return_value.returncode=1;run.return_value.stdout='failure evidence'
    with self.assertRaises(RuntimeError):module.execute(commands,directory,'local')
    self.assertEqual(run.call_count,1)
   journal=json.loads((directory/'route-attempts.json').read_text());self.assertEqual(journal[0]['status'],'FAIL')
   self.assertEqual((directory/'route-1-first.log').read_text(),'failure evidence')
 def test_production_closes_cycle_immediately_with_explicit_rework(self):
  plan=self.module().commands(Path('/os'),Path('/site'),'cycle',[],['item'],'a'*40,'production',116,2,Path('/cortex'),False)
  self.assertEqual([name for name,_,_ in plan],['production','close-cycle'])
  self.assertIn('2',plan[1][1]);self.assertIn('--cortex-root',plan[1][1])
 def test_browser_readiness_precedes_writes_and_expensive_checks(self):
  module=self.module()
  for phase in ('local','check'):
   plan=module.commands(Path('/os'),Path('/site'),'cycle',[],['item'],'a'*40,phase,None,None,None,False)
   self.assertEqual(plan[0][0],'browser-preflight')
   self.assertIn('chromium.launch',plan[0][1][-1]);self.assertNotIn('install',plan[0][1])
