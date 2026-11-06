import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from abvx_harness import mac_cache_maintenance as m


class MaintenanceTests(unittest.TestCase):
    def test_activity_parser_does_not_treat_shell_text_as_package_job(self):
        result = m.active_managers(['/bin/zsh -c "echo npm install"',
                                    '/opt/homebrew/bin/node /x/npm-cli.js install',
                                    '/opt/homebrew/bin/python3 -m pip install x'])
        self.assertEqual(result, {'npm','pip'})

    def test_nested_symlink_mode_never_reads_or_removes_destination(self):
        keep = self.state/'keep'
        keep.write_text('protected')
        (self.cache/'link').symlink_to(keep)
        evidence=m.fingerprint(self.cache,allow_nested_symlinks=True)
        receipt=self.state/'synthetic.json'
        result=m.remove_snapshot(self.cache,evidence,receipt,'TEST','synthetic')
        self.assertEqual(result['status'],'VERIFIED_REMOVED')
        self.assertEqual(keep.read_text(),'protected')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        self.cache = root/'npm'/'_cacache'
        self.cache.mkdir(parents=True)
        (self.cache/'blob').write_bytes(b'cached package')
        self.state = root/'state'
        self.state.mkdir()
        for p in (patch.object(m,'STATE',self.state),patch.object(m,'INTERNAL',root),
                  patch.object(m,'target',return_value=self.cache),patch.object(m,'idle',return_value=True)):
            p.start()
            self.addCleanup(p.stop)

    def test_exact_approved_plan_removes_only_cache_and_verifies_once(self):
        keep = self.cache.parent/'npmrc'
        keep.write_text('keep')
        plan = m.plan()
        self.assertTrue(self.cache.exists())
        result = m.apply(plan['plan_id'])
        self.assertEqual(result['status'],'VERIFIED_REMOVED')
        self.assertEqual(keep.read_text(),'keep')
        self.assertEqual(m.apply(plan['plan_id'])['status'],'DUPLICATE')

    def test_changed_cache_is_not_approved(self):
        plan = m.plan()
        (self.cache/'new').write_text('new download')
        self.assertEqual(m.apply(plan['plan_id'])['reason'],'CACHE_CHANGED_REPLAN')
        self.assertTrue(self.cache.exists())

    def test_busy_or_unknown_is_blocked(self):
        plan=m.plan()
        with patch.object(m,'idle',return_value=False):
            self.assertEqual(m.apply(plan['plan_id'])['reason'],'PROCESS_CHECK_UNKNOWN_OR_BUSY')
        self.assertTrue(self.cache.exists())

    def test_symlink_entry_is_rejected(self):
        (self.cache/'link').symlink_to(self.state)
        self.assertEqual(m.plan()['status'],'BLOCKED')

    def test_approval_is_required_and_tampered_plan_rejected(self):
        plan=m.plan()
        self.assertEqual(m.apply(None)['reason'],'INVALID_PLAN_ID')
        path=self.state/'maintenance-plans'/(plan['plan_id']+'.json')
        value=m.load(path);value['path']=str(self.state);m.save(path,value)
        self.assertEqual(m.apply(plan['plan_id'])['reason'],'PLAN_MISMATCH')

    def test_expired_plan_requires_new_review(self):
        plan=m.plan()
        with patch.object(m.time,'time',return_value=plan['created_at']+90000):
            self.assertEqual(m.apply(plan['plan_id'])['reason'],'PLAN_EXPIRED')

    def test_failure_is_recorded_without_replay(self):
        plan=m.plan()
        with patch.object(m.shutil,'rmtree',side_effect=PermissionError) as remove:
            remove.avoids_symlink_attacks=True
            self.assertEqual(m.apply(plan['plan_id'])['status'],'FAILED_OR_PARTIAL_NO_AUTORETRY')
            self.assertEqual(m.apply(plan['plan_id'])['status'],'DUPLICATE')
            remove.assert_called_once()
