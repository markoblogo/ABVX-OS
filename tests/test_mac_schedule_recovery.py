import importlib.util
from datetime import datetime
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('recovery', Path(__file__).parents[1] / 'scripts/mac_schedule_recovery.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RecoveryTests(unittest.TestCase):
    def test_missing_volume_never_blocks_internal_receipt_then_emits_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / 'volume/repo'
            state = base / 'internal'
            when = datetime.fromisoformat('2026-10-27T15:00:00+01:00').timestamp()
            first = r.tick(repo, state, base / 'home', when, False, journal_root=base/'journal')
            self.assertFalse(first['repository_ready'])
            self.assertEqual(first['checks'][0]['status'], 'WAITING_FOR_PATHS')
            (repo/'bin').mkdir(parents=True)
            (repo/'bin/mac-operator').write_text('fixture')
            second = r.tick(repo, state, base/'home', when+300, False, journal_root=base/'journal')
            self.assertTrue(second['repository_ready'])
            self.assertEqual(len(second['new_signals']), 1)
            third = r.tick(repo, state, base/'home', when+600, False, journal_root=base/'journal')
            self.assertEqual(third['new_signals'], [])
            self.assertEqual(third['dispatch_status'], 'BLOCKED_NO_SUPPORTED_DISPATCH')

    def test_schedule_respects_paris_dst(self):
        when = datetime.fromisoformat('2026-10-26T11:00:00+01:00').timestamp()
        nominal = r.nominal('RRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0', when)
        self.assertEqual(datetime.fromtimestamp(nominal, r.ZoneInfo('Europe/Paris')).isoformat(), '2026-10-26T08:00:00+01:00')
        self.assertIsNone(r.nominal('FREQ=MINUTELY;INTERVAL=5', when))

    def test_attempt_is_not_completion_and_paused_never_resumes(self):
        now = datetime.fromisoformat('2026-10-27T15:00:00+01:00').timestamp()
        job = {'id':'fixture','kind':'local','status':'ACTIVE','rrule':'FREQ=DAILY;BYHOUR=10;BYMINUTE=0','cwds':[], 'last_run_at': now*1000}
        self.assertEqual(r.assess(job, now)['status'], 'ATTEMPT_RECORDED_COMPLETION_UNKNOWN')
        job['status']='PAUSED'
        self.assertEqual(r.assess(job, now)['status'], 'INACTIVE')

    def test_verified_publication_suppresses_catchup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root/'2026-10-27-weekly/state.json'
            r.save(path, {'publication':{'status':'PUBLISHED'}})
            now = datetime.fromisoformat('2026-10-27T15:00:00+01:00').timestamp()
            result = r.assess(r.RADAR, now, lambda p:True, root)
            self.assertEqual(result['status'], 'DELIVERY_RECORDED')

    def test_manual_check_cannot_replace_scheduled_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            when=datetime.fromisoformat('2026-10-27T15:00:00+01:00').timestamp()
            r.tick(base/'repo',base/'state',base/'home',when,False,journal_root=base/'journal',source='scheduled')
            r.tick(base/'repo',base/'state',base/'home',when+60,False,journal_root=base/'journal',source='manual')
            self.assertEqual(r.read(base/'state/latest.json')['observed_at'],when)
            self.assertEqual(r.read(base/'state/latest-manual.json')['observed_at'],when+60)

    def test_published_partial_still_exposes_recoverable_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            r.save(root/'2026-10-27-weekly/state.json',{'publication':{'status':'PUBLISHED'},
                'stages':{'gmail':{'status':'BLOCKED','retryable':True,'attempts':[{}]}}})
            now=datetime.fromisoformat('2026-10-27T15:00:00+01:00').timestamp()
            self.assertEqual(r.assess(r.RADAR,now,lambda p:True,root)['status'],'READY_TO_RESUME')


if __name__=='__main__':
    unittest.main()
