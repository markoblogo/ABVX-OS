import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness import mac_auto_cleanup as m
from abvx_harness import mac_cache_maintenance as c


class AutoCleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name).resolve()
        self.state=self.home/'state';self.state.mkdir()
        self.now=1800000000.0
        for p in (patch.object(m,'STATE',self.state),patch.object(c,'INTERNAL',self.home),
                  patch.object(Path,'home',return_value=self.home),patch.object(c,'idle',return_value=True),patch.object(c,'activity',return_value={'idle':True,'reason':'VERIFIED_IDLE'}),
                  patch.object(m.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(100*m.GIB,98*m.GIB,2*m.GIB))):
            p.start();self.addCleanup(p.stop)
        self.target=self.home/m.TARGETS['npm-downloads']
        self.target.mkdir(parents=True)
        (self.target/'blob').write_bytes(b'x'*(2*1024**2))

    def enable(self):
        return m.enable(self.now)

    def test_disabled_is_read_only(self):
        self.assertEqual(m.run_due(self.state,{},now=self.now)['status'],'DISABLED_OR_EXPIRED')
        self.assertTrue(self.target.exists())

    def test_enabled_removes_only_fixed_cache_and_retains_protected_data(self):
        keep=self.home/'Documents';keep.mkdir();(keep/'keep').write_text('keep')
        self.enable()
        v=m.run_due(self.state,{},now=self.now)
        self.assertFalse(self.target.exists())
        self.assertEqual((keep/'keep').read_text(),'keep')
        self.assertGreater(v['verified_removed_allocated_bytes'],0)
        self.assertEqual(v['observed_disk_free_delta_bytes'],0)
        self.assertEqual(m.run_due(self.state,{},now=self.now+300)['status'],'NOT_DUE')

    def test_unknown_process_visibility_never_deletes(self):
        self.enable()
        with patch.object(c,'idle',return_value=False):
            v=m.run_due(self.state,{},now=self.now)
        self.assertTrue(self.target.exists())
        self.assertEqual(v['verified_removed_allocated_bytes'],0)
        self.assertEqual(m.load(self.state/'auto-cleanup-quota.json')['charged_bytes'],0)

    def test_quota_limits_effects(self):
        self.enable()
        m.save(self.state/'auto-cleanup-quota.json',{'day':int(self.now//86400),'charged_bytes':m.DAILY_LIMIT})
        self.assertEqual(m.run_due(self.state,{},now=self.now)['status'],'DAILY_LIMIT')
        self.assertTrue(self.target.exists())

    def test_expired_permission_cannot_delete(self):
        self.enable()
        self.assertEqual(m.run_due(self.state,{},now=self.now+31*86400)['status'],'DISABLED_OR_EXPIRED')
        self.assertTrue(self.target.exists())

    def test_good_free_space_stops_cleanup(self):
        self.enable()
        with patch.object(m.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(100*m.GIB,70*m.GIB,30*m.GIB)):
            self.assertEqual(m.run_due(self.state,{},now=self.now)['status'],'ENOUGH_FREE_SPACE')
        self.assertTrue(self.target.exists())

    def test_interrupted_pass_cannot_restart_itself(self):
        self.enable()
        m.save(self.state/'auto-cleanup-latest.json',{'status':'RUNNING','started_at':self.now-7*3600})
        self.assertEqual(m.run_due(self.state,{},now=self.now)['status'],'INTERRUPTED_REQUIRES_INSPECTION')
        self.assertTrue(self.target.exists())

    def test_symlink_root_is_excluded_and_nested_symlink_never_followed(self):
        self.enable()
        protected=self.home/'protected';protected.mkdir();(protected/'keep').write_text('keep')
        (self.target/'link').symlink_to(protected,target_is_directory=True)
        m.run_due(self.state,{},now=self.now)
        self.assertEqual((protected/'keep').read_text(),'keep')
        self.target.symlink_to(protected,target_is_directory=True)
        v=m.run_due(self.state,{},now=self.now+7*3600)
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(v['verified_removed_allocated_bytes'],0)

    def test_prior_partial_failure_requires_inspection(self):
        self.enable()
        m.save(self.state/'auto-cleanup-latest.json',{'status':'COMPLETE','started_at':self.now-7*3600,'failed_targets':['npm-downloads']})
        m.run_due(self.state,{},now=self.now)
        self.assertTrue(self.target.exists())

    def test_policy_cannot_add_arbitrary_targets(self):
        p=self.enable();p['scope']='delete-anything';m.save(self.state/'auto-cleanup-policy.json',p)
        self.assertEqual(m.run_due(self.state,{},now=self.now)['status'],'DISABLED_OR_EXPIRED')
        self.assertTrue(self.target.exists())
