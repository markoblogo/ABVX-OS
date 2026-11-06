"""Synthetic state only: no sends, cleanup executions or owner scans."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from abvx_harness import mac_alerts as a, mac_operator as op, mac_codex_growth as g
from abvx_harness import mac_auto_cleanup as c


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        (self.state/'notifications').mkdir()

    def event(self, name, **kw):
        d = dict(id=name, status='PENDING', created_at=1000, event='OPEN',
                 message=name, attempts=0, next_attempt=0)
        d.update(kw)
        p = self.state/'notifications'/(name+'.json');op.save(p,d)
        return p

    def test_eligible_before_limit_not_hash_tail(self):
        p=self.event('000', created_at=1050)
        for n in range(120):
            self.event(f'f{n:03}', status='DELIVERED')
        local=Mock(return_value={'status':'SUBMITTED_NOT_VISUALLY_VERIFIED'})
        a.deliver(self.state,op.load,op.save,local,lambda _: {'status':'NOT_CONNECTED'},1100)
        self.assertTrue(op.load(p).get('local_attempted'))
        local.assert_called_once()

    def test_oldest_due_first_with_bounded_batch(self):
        self.event('aaa',created_at=1099)
        self.event('zzz',created_at=1000)
        calls=[]
        a.deliver(self.state,op.load,op.save,lambda x:calls.append(x),lambda _: {'status':'NOT_CONNECTED'},1100)
        self.assertEqual(calls[0],'OPEN: zzz')

    def test_disconnected_has_cooldown_and_does_not_repeat_local(self):
        p=self.event('x'); local=Mock(return_value={'status':'SUBMITTED_NOT_VISUALLY_VERIFIED'});remote=Mock(return_value={'status':'NOT_CONNECTED'})
        a.deliver(self.state,op.load,op.save,local,remote,1100)
        a.deliver(self.state,op.load,op.save,local,remote,1200)
        self.assertEqual(remote.call_count,1)
        self.assertEqual(local.call_count,1)
        self.assertEqual(op.load(p)['attempts'],0)

    def test_expiry_precedes_retry_gate(self):
        p=self.event('x',created_at=1,next_attempt=200000)
        a.deliver(self.state,op.load,op.save,Mock(),Mock(),90000)
        self.assertEqual(op.load(p)['status'],'EXPIRED')

    def test_reconcile_replay_after_incident_write_failure_is_idempotent(self):
        snap=dict(time=1000,issues=['disk'],unavailable_probes=[],services={},workflow_health={})
        def fail(p,d):
            if p.name=='incidents.json':raise OSError('simulated crash')
            op.save(p,d)
        with self.assertRaises(OSError):a.reconcile(self.state,snap,op.load,fail)
        a.reconcile(self.state,snap,op.load,op.save)
        self.assertEqual(len(list((self.state/'notifications').glob('*.json'))),1)

    def test_cleanup_unfinished_visible_even_when_disk_sufficient(self):
        op.save(self.state/'latest-scheduled.json',dict(time=1000))
        op.save(self.state/'auto-cleanup-latest.json',dict(status='RUNNING',started_at=1))
        before=(self.state/'auto-cleanup-latest.json').read_bytes()
        with patch.object(op,'STATE',self.state):r=op.health(1100)
        self.assertEqual(r['status'],'ATTENTION')
        self.assertEqual(r['cache_maintenance']['diagnosis']['status'],'INTERRUPTED_REQUIRES_INSPECTION')
        self.assertEqual((self.state/'auto-cleanup-latest.json').read_bytes(),before)

    def test_unfinished_blocks_before_policy_disk_and_interval(self):
        op.save(self.state/'auto-cleanup-latest.json',dict(status='RUNNING',started_at=1000))
        with patch.object(c.shutil,'disk_usage') as disk:
            self.assertEqual(c.run_due(self.state,{},now=1100)['status'],'INTERRUPTED_REQUIRES_INSPECTION')
        disk.assert_not_called()

    def test_sequential_scan_rotates_preserves_partial_and_nondate_entries(self):
        root=self.state/'Codex';root.mkdir()
        for name in ['old','2026-11-02','other']:(root/name).mkdir()
        (root/'loose.txt').write_text('keep')
        results=[]
        def measure(p,now=None,timeout=None):
            results.append(p.name)
            return dict(path=str(p),time=now,device=root.stat().st_dev,
                        status='TIME_LIMIT' if p.name=='old' else 'COMPLETE',
                        allocated_bytes=None if p.name=='old' else 4096)
        with patch.object(g,'_INTERNAL',root),patch.object(g,'_measure',side_effect=measure):
            first=g._sequential_measure(root,self.state,op.load,op.save,now=1000,max_items=2)
            second=g._sequential_measure(root,self.state,op.load,op.save,now=1100,max_items=2)
        self.assertEqual(len(set(results)),4)
        self.assertEqual(second['status'],'PARTIAL')
        self.assertIsNone(second['allocated_bytes'])
        self.assertGreater(second['measured_allocated_bytes'],first['measured_allocated_bytes'])
        self.assertEqual(second['coverage']['discovered_entries'],4)
        self.assertEqual((root/'loose.txt').read_text(),'keep')

    def test_partial_scan_checkpoint_survives_interruption(self):
        root=self.state/'Codex';root.mkdir();(root/'a').mkdir();(root/'b').mkdir()
        def measure(p,now=None,timeout=None):
            if p.name=='b':raise RuntimeError('interrupted')
            return dict(path=str(p),time=now,device=root.stat().st_dev,status='COMPLETE',allocated_bytes=4096)
        with patch.object(g,'_INTERNAL',root),patch.object(g,'_measure',side_effect=measure):
            with self.assertRaises(RuntimeError):g._sequential_measure(root,self.state,op.load,op.save,now=1000)
        self.assertEqual(op.load(self.state/'codex-growth-progress.json')['categories'][0]['status'],'COMPLETE')

    def test_current_exposes_partial_coverage_and_age(self):
        op.save(self.state/'codex-growth-scheduled-latest.json',dict(time=1000,status='PARTIAL',scope='SEQUENTIAL_WORKSPACE',coverage={'complete_entries':1},measured_allocated_bytes=4096))
        r=g.current(self.state,op.load,1100)
        self.assertEqual(r['signal'],'UNKNOWN')
        self.assertEqual(r['measurement_age_seconds'],100)
        self.assertEqual(r['coverage']['complete_entries'],1)

    def test_supersedes_obsolete_legacy_events(self):
        old=self.event('a',message='disk',created_at=1000)
        self.event('b',message='disk',created_at=1100,event='RECOVERED')
        calls=[]
        a.deliver(self.state,op.load,op.save,lambda x:calls.append(x),lambda _: {'status':'NOT_CONNECTED'},1200)
        self.assertEqual(op.load(old)['status'],'SUPERSEDED')
        self.assertEqual(calls,['RECOVERED: disk'])

    def test_local_crash_does_not_repeat_effect(self):
        self.event('x'); calls=[]
        def local(msg):
            calls.append(msg);raise OSError('interrupted')
        with self.assertRaises(OSError):
            a.deliver(self.state,op.load,op.save,local,lambda _: {'status':'NOT_CONNECTED'},1100)
        a.deliver(self.state,op.load,op.save,local,lambda _: {'status':'NOT_CONNECTED'},5000)
        self.assertEqual(len(calls),1)

    def test_flapping_incident_cooldown(self):
        self.event('a',created_at=1000,incident_key='disk')
        calls=[]
        a.deliver(self.state,op.load,op.save,lambda x:calls.append(x),lambda _: {'status':'NOT_CONNECTED'},1100)
        self.event('b',created_at=1200,event='RECOVERED',incident_key='disk')
        a.deliver(self.state,op.load,op.save,lambda x:calls.append(x),lambda _: {'status':'NOT_CONNECTED'},1300)
        self.assertEqual(len(calls),1)
        a.deliver(self.state,op.load,op.save,lambda x:calls.append(x),lambda _: {'status':'NOT_CONNECTED'},4800)
        self.assertEqual(len(calls),2)

    def test_stale_categories_do_not_claim_total(self):
        root=self.state/'Codex';root.mkdir();(root/'a').mkdir()
        record=dict(path=str(root),device=root.stat().st_dev,categories=[dict(path=str(root/'a'),time=1,status='COMPLETE',allocated_bytes=4096)])
        op.save(self.state/'codex-growth-progress.json',record)
        with patch.object(g,'_INTERNAL',root):
            r=g._sequential_measure(root,self.state,op.load,op.save,now=200000,max_items=0)
        self.assertEqual(r['status'],'PARTIAL')
        self.assertIsNone(r['allocated_bytes'])
        self.assertEqual(r['measured_allocated_bytes'],0)

    def test_symlink_and_denied_category_never_complete(self):
        root=self.state/'Codex';root.mkdir();(root/'link').symlink_to(self.state)
        with patch.object(g,'_INTERNAL',root):
            r=g._sequential_measure(root,self.state,op.load,op.save,now=1000)
        self.assertEqual(r['status'],'PARTIAL')
        self.assertEqual(r['categories'][0]['status'],'UNAVAILABLE')
