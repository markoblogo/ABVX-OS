"""Time-budget and checkpoint regressions: isolated temporary caches only."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness import mac_auto_cleanup as c, mac_operator as op
from abvx_harness import mac_cache_maintenance as cache


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name).resolve();self.state=self.home/'state';self.state.mkdir()
        self.now=1800000000.0
        for p in (patch.object(c,'STATE',self.state),patch.object(op,'STATE',self.state),patch.object(cache,'INTERNAL',self.home),patch.object(Path,'home',return_value=self.home),patch.object(c.shutil,'disk_usage',return_value=type('Disk',(),{'free':2*c.GIB})()),patch.object(cache,'activity',return_value={'idle':True,'reason':'VERIFIED_IDLE'})):
            p.start();self.addCleanup(p.stop)
        c.enable(self.now)
        self.target=self.home/c.TARGETS['npm-downloads'];self.target.mkdir(parents=True);(self.target/'blob').write_bytes(b'x'*(2*1024**2))

    def test_nested_budget_inherits_earlier_deadline(self):
        with patch.object(c.budget.time,'monotonic',return_value=10):
            with c.budget.limit(5):
                with c.budget.limit(80):self.assertEqual(c.budget.remaining(),5)
        self.assertIsNone(c.budget.remaining())

    def test_expired_budget_never_probes_or_removes_cache(self):
        with c.budget.limit(0),patch.object(cache,'fingerprint') as probe:
            r=c.run_due(self.state,{},now=self.now)
        probe.assert_not_called();self.assertEqual(r['status'],'DEFERRED_TIME_BUDGET');self.assertTrue(self.target.exists())

    def test_running_latch_preserved_even_when_budget_expired(self):
        op.save(self.state/'auto-cleanup-latest.json',{'status':'RUNNING','started_at':1})
        before=(self.state/'auto-cleanup-latest.json').read_bytes()
        with c.budget.limit(0):r=c.run_due(self.state,{},now=self.now)
        self.assertEqual(r['status'],'INTERRUPTED_REQUIRES_INSPECTION');self.assertEqual((self.state/'auto-cleanup-latest.json').read_bytes(),before)

    def test_crash_checkpoint_preserves_pid_phase_and_redacted_error(self):
        def fail(*args,**kwargs):
            receipt=op.load(self.state/'auto-cleanup-latest.json')
            self.assertEqual(receipt['phase'],'fingerprint-before');self.assertEqual(receipt['target'],'npm-downloads');self.assertGreater(receipt['pid'],0)
            raise RuntimeError('secret-token')
        with patch.object(cache,'fingerprint',side_effect=fail):r=c.run_due(self.state,{},now=self.now)
        self.assertEqual(r['status'],'FAILED_REQUIRES_INSPECTION');self.assertEqual(r['phase'],'fingerprint-before');self.assertNotIn('secret-token',str(r))
        self.assertEqual(c.run_due(self.state,{},now=self.now+300)['status'],'INTERRUPTED_REQUIRES_INSPECTION')
        history=list((self.state/'auto-cleanup-runs').glob('*.json'));self.assertEqual(len(history),1);self.assertEqual(op.load(history[0])['phase'],'fingerprint-before')

    def test_budget_expiry_during_target_is_latched_and_does_not_charge(self):
        with patch.object(cache,'fingerprint',side_effect=c.budget.Expired()):r=c.run_due(self.state,{},now=self.now)
        self.assertEqual(r['status'],'TIME_LIMIT_REQUIRES_INSPECTION');self.assertTrue(self.target.exists());self.assertFalse((self.state/'auto-cleanup-quota.json').exists())
        self.assertEqual(c.run_due(self.state,{},now=self.now+300)['status'],'INTERRUPTED_REQUIRES_INSPECTION')

    def test_success_records_executor_boundaries_and_history(self):
        with patch.object(cache,'idle',return_value=True):r=c.run_due(self.state,{},now=self.now)
        self.assertEqual(r['status'],'COMPLETE');phases=[v['phase'] for v in r['checkpoints']]
        for phase in ['fingerprint-before','fingerprint-after','activity-before','activity-after','quota-before','execute-before','remove-before','remove-after','done']:self.assertIn(phase,phases)
        self.assertFalse(self.target.exists());self.assertGreater(r['verified_removed_allocated_bytes'],0)

    def test_tick_consumes_same_budget_before_cleanup(self):
        def diagnose(_):raise op.budget.Expired()
        with patch.object(op,'diagnose',side_effect=diagnose),patch.object(c,'run_due') as due:
            r=op.tick('scheduled')
        self.assertEqual(r['status'],'TIME_LIMIT');due.assert_not_called()

    def test_native_command_timeout_clamped_to_shared_budget(self):
        with c.budget.limit(2),patch.object(op.subprocess,'run') as run:
            run.return_value.stdout='';run.return_value.stderr='';run.return_value.returncode=0
            op.command(['/usr/bin/true'],timeout=12)
            self.assertLessEqual(run.call_args.kwargs['timeout'],2)

    def test_checkpoint_failure_prevents_effects(self):
        def write(p,d):
            if d.get('phase')=='execute-before' and d.get('status')=='RUNNING':raise OSError('unwritable')
            op.save(p,d)
        with patch.object(cache,'idle',return_value=True),patch.object(cache,'remove_snapshot') as remove:
            r=c.run_due(self.state,{},write=write,now=self.now)
        remove.assert_not_called();self.assertEqual(r['status'],'FAILED_REQUIRES_INSPECTION');self.assertTrue(self.target.exists())

    def test_hard_interruption_preserves_running_phase_without_auto_retry(self):
        with patch.object(cache,'fingerprint',side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):c.run_due(self.state,{},now=self.now)
        saved=op.load(self.state/'auto-cleanup-latest.json')
        self.assertEqual(saved['status'],'RUNNING');self.assertEqual(saved['phase'],'fingerprint-before')
        self.assertEqual(c.run_due(self.state,{},now=self.now+1)['status'],'INTERRUPTED_REQUIRES_INSPECTION')

    def test_tick_passes_only_remaining_budget_to_maintenance(self):
        clock=[10.0];seen=[]
        def diagnose(_):clock[0]+=110;return {}
        def due(*args):seen.append(c.budget.remaining());return {'status':'DISABLED_OR_EXPIRED'}
        with patch.object(c.budget.time,'monotonic',side_effect=lambda:clock[0]),patch.object(op,'diagnose',side_effect=diagnose),patch.object(op.mac_alerts,'reconcile'),patch.object(op.mac_alerts,'deliver'),patch.object(op,'poll_telegram',return_value={}),patch.object(c,'run_due',side_effect=due),patch.object(op.mac_codex_growth,'run_due',return_value={}):
            r=op.tick('scheduled')
        self.assertEqual(seen,[]);self.assertEqual(r['status'],'COMPLETE')
        self.assertEqual(r['cache_cleanup']['status'],'SUSPENDED_OWNER_INSTRUCTION')

    def test_no_removal_when_revalidation_uses_last_reserve(self):
        clock=[10.0];original=cache.fingerprint
        def slower(*args,**kwargs):
            measurement=original(*args,**kwargs);clock[0]+=10;return measurement
        with patch.object(c.budget.time,'monotonic',side_effect=lambda:clock[0]),c.budget.limit(40),patch.object(cache,'fingerprint',side_effect=slower),patch.object(cache,'idle',return_value=True),patch.object(cache.shutil,'rmtree') as removal:
            r=c.run_due(self.state,{},now=self.now)
        removal.assert_not_called();self.assertEqual(r['status'],'TIME_LIMIT_REQUIRES_INSPECTION');self.assertTrue(self.target.exists())
