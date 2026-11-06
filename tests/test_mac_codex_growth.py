"""Scheduling and alert tests use synthetic snapshots, no owner workspace scans."""
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from abvx_harness import mac_codex_growth as g
from abvx_harness import mac_operator as op
from abvx_harness import mac_alerts


def stamp(y, m, d, hour=12):
    return datetime(y, m, d, hour, tzinfo=ZoneInfo("Europe/Paris")).timestamp()


def host(pressure="1", free_gib=25, load=2):
    return {"disk_free": free_gib * g._GIB, "load": [load],
            "evidence": {"pressure": {"code": 0, "output": pressure}}}


class GrowthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        self.tue = stamp(2026, 10, 27)
        self.save = op.save
        self.load = op.load

    def complete(self, size, when=None):
        return {"status": "COMPLETE", "path": str(g._WORKSPACE),
                "device": 4, "time": self.tue if when is None else when,
                "allocated_bytes": size}

    def test_baseline_and_large_daily_growth(self):
        before = self.complete(3*g._GIB, self.tue-86400)
        self.save(self.state/"codex-growth-last-complete.json", before)
        mock = Mock(return_value=self.complete(6*g._GIB))
        a = g.run_due(self.state, host(), self.load, self.save,
                      now=self.tue, sample_fn=mock)
        self.assertEqual(a["daily"], "COMPLETE")
        result = self.load(self.state/"codex-growth-scheduled-latest.json")
        self.assertEqual(result["signal"], "HIGH_GROWTH")
        self.assertAlmostEqual(result["gib_per_day"], 3)
        self.assertEqual(g.current(self.state, self.load, self.tue)["signal"], "HIGH_GROWTH")
        # No same-day repeated IO; weekly run uses a separate budget.
        b = g.run_due(self.state, host("2"), self.load, self.save,
                      now=self.tue+300, sample_fn=mock)
        self.assertEqual(b["daily"], "NOT_DUE")
        mock.assert_called_once()

    def test_no_baseline_no_alert(self):
        mock = Mock(return_value=self.complete(6*g._GIB))
        g.run_due(self.state, host(), self.load, self.save,
                  now=self.tue, sample_fn=mock)
        self.assertEqual(g.current(self.state, self.load, self.tue)["signal"], "BASELINE")

    def test_due_light_under_pressure_or_low_disk(self):
        mock = Mock()
        for i, snap in enumerate((host("2"), host("1", free_gib=4), host("1", load=40))):
            light = Mock(return_value=self.complete(2*g._GIB, self.tue+i*86400))
            out = g.run_due(self.state, snap, self.load, self.save,
                            now=self.tue+i*86400, sample_fn=mock, light_fn=light)
            self.assertEqual(out["daily"], "COMPLETE")
            light.assert_called_once()
            self.assertEqual(self.load(self.state/'codex-growth-scheduled-latest.json')['scan_mode'], 'LIGHT')
        mock.assert_not_called()

    def test_critical_pressure_still_defers_without_scan(self):
        light = Mock()
        out = g.run_due(self.state, host('4', free_gib=2), self.load, self.save,
                        now=self.tue, light_fn=light)
        light.assert_not_called()
        self.assertEqual(out['daily'], 'DEFERRED_CRITICAL_OR_UNKNOWN_PRESSURE')

    def test_different_scope_or_selected_paths_cannot_fabricate_growth(self):
        today = dict(self.complete(8*g._GIB), scope='RECENT_DATE_FOLDERS', selected_paths=['a'])
        prior = dict(self.complete(1*g._GIB, self.tue-86400), scope='RECENT_DATE_FOLDERS', selected_paths=['b'])
        self.assertEqual(g._compare(today, prior, self.tue)['signal'], 'BASELINE')
        prior.pop('scope')
        self.assertEqual(g._compare(today, prior, self.tue)['signal'], 'BASELINE')

    def test_matching_categories_still_compare_when_new_date_is_added(self):
        old = dict(self.complete(g._GIB, self.tue-86400), path='date-a')
        new = dict(self.complete(4*g._GIB), path='date-a')
        unknown = dict(self.complete(8*g._GIB), path='date-b')
        changes = g._category_changes({'categories':[new, unknown]}, {'categories':[old]}, self.tue)
        self.assertEqual(changes[0]['signal'], 'HIGH_GROWTH')
        self.assertEqual(changes[1]['signal'], 'BASELINE')

    def test_light_selection_is_bounded_and_excludes_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'Codex'
            root.mkdir()
            for d in ('2026-10-20','2026-10-21','2026-10-22','2026-10-23','2026-10-24'):
                (root/d).mkdir()
            (root/'2026-10-25').symlink_to(root/'2026-10-24', target_is_directory=True)
            with patch.object(g, '_INTERNAL', root), patch.object(g, '_measure', return_value={'status':'COMPLETE','allocated_bytes':100}) as measure:
                result = g._light_measure(root, self.tue)
            self.assertEqual(len(result['selected_paths']), 4)
            self.assertNotIn(str(root/'2026-10-25'),result['selected_paths'])
            self.assertEqual(result['allocated_bytes'], 400)
            self.assertEqual(measure.call_count,4)

    def test_weekly_once_when_daily_already_done(self):
        day, week, _ = g._period(self.tue)
        self.save(self.state/"codex-growth-daily-claim.json", {"period": day})
        weekly = Mock(return_value={"status": "COMPLETE", "time": self.tue,
                                    "review_eligible_allocated_bytes": 2*g._GIB})
        result = g.run_due(self.state, host(), self.load, self.save,
                           now=self.tue, preview_fn=weekly)
        self.assertEqual(result, {"daily":"NOT_DUE", "weekly":"COMPLETE"})
        self.assertEqual(g.current(self.state, self.load, self.tue)["weekly_signal"], "REVIEW")
        again = g.run_due(self.state, host(), self.load, self.save,
                          now=self.tue+300, preview_fn=weekly)
        self.assertEqual(again["weekly"], "NOT_DUE")
        weekly.assert_called_once()

    def test_partial_data_never_raises_growth_alert(self):
        self.save(self.state/"codex-growth-scheduled-latest.json",
                  {"time":self.tue, "status":"TIME_LIMIT", "signal":"HIGH_GROWTH"})
        self.save(self.state/"codex-retention-weekly-latest.json",
                  {"time":self.tue, "status":"PARTIAL",
                   "review_eligible_allocated_bytes": 30*g._GIB})
        out = g.current(self.state, self.load, self.tue)
        self.assertEqual(out["signal"], "UNKNOWN")
        self.assertEqual(out["weekly_signal"], "UNKNOWN")

    def test_signal_stale_after_day_and_half(self):
        self.save(self.state/"codex-growth-scheduled-latest.json",
                  dict(self.complete(3*g._GIB), signal="HIGH_GROWTH", gib_per_day=3.0))
        self.assertEqual(g.current(self.state, self.load, self.tue+37*3600)["signal"], "UNKNOWN")

    def test_claim_limits_retry_after_incomplete_scan(self):
        failed = Mock(return_value={"status":"TIME_LIMIT", "path":str(g._WORKSPACE),
                                    "time":self.tue,"device":4,"allocated_bytes":None})
        g.run_due(self.state, host(), self.load, self.save, now=self.tue, sample_fn=failed)
        g.run_due(self.state, host("2"), self.load, self.save, now=self.tue+600, sample_fn=failed)
        failed.assert_called_once()
        self.assertFalse((self.state/"codex-growth-last-complete.json").exists())

    def test_before_four_does_nothing(self):
        test_time=stamp(2026,10,27,3)
        mock=Mock()
        self.assertEqual(g.run_due(self.state,host(),self.load,self.save,
                                   now=test_time,sample_fn=mock)["daily"], "NOT_DUE")
        mock.assert_not_called()

    def test_growth_alert_reuses_incident_system_without_duplicates(self):
        t=self.tue
        base={"time":t,"issues":[],"unavailable_probes":[],
              "services":{},"workflow_health":{}}
        growth={"signal":"HIGH_GROWTH","gib_per_day":3.25,"weekly_signal":"UNKNOWN"}
        with_growth=dict(base,codex_growth=growth)
        self.assertEqual(mac_alerts.reconcile(self.state,with_growth,self.load,self.save),1)
        self.assertEqual(mac_alerts.reconcile(self.state,with_growth,self.load,self.save),0)
        unknown=dict(base,codex_growth={"signal":"UNKNOWN","weekly_signal":"UNKNOWN"})
        self.assertEqual(mac_alerts.reconcile(self.state,unknown,self.load,self.save),0)
        normal=dict(base,codex_growth={"signal":"NORMAL","weekly_signal":"NORMAL"})
        self.assertEqual(mac_alerts.reconcile(self.state,normal,self.load,self.save),1)

    def test_weekly_review_alert_uses_existing_dedup(self):
        t = self.tue
        base = {"time": t, "issues": [], "unavailable_probes": [],
                "services": {}, "workflow_health": {}}
        review = dict(base, codex_growth={"signal": "UNKNOWN",
                                         "weekly_signal": "REVIEW"})
        self.assertEqual(mac_alerts.reconcile(self.state, review, self.load, self.save), 1)
        self.assertEqual(mac_alerts.reconcile(self.state, review, self.load, self.save), 0)
        partial = dict(base, codex_growth={"signal": "UNKNOWN",
                                          "weekly_signal": "UNKNOWN"})
        self.assertEqual(mac_alerts.reconcile(self.state, partial, self.load, self.save), 0)

    def test_daily_measurement_is_bounded_and_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            root.mkdir()
            content = root / "keep.txt"
            content.write_text("never deleted")
            with patch.object(g, "_INTERNAL", Path(temp)):
                outcome = g._measure(root, now=self.tue, timeout=5)
            self.assertEqual(outcome["status"], "COMPLETE")
            self.assertGreater(outcome["allocated_bytes"], 0)
            self.assertEqual(content.read_text(), "never deleted")
            shortcut = Path(temp) / "link"
            shortcut.symlink_to(root, target_is_directory=True)
            self.assertEqual(g._measure(shortcut)["status"], "UNAVAILABLE")

    def test_manual_tick_never_runs_scheduled_scans(self):
        with (patch.object(op, "STATE", self.state),
              patch.object(op, "diagnose", return_value={}),
              patch.object(op, "poll_telegram", return_value={"status":"NOT_CONNECTED"}),
              patch.object(op.mac_codex_growth, "run_due") as due):
            self.assertEqual(op.tick("manual")["status"], "COMPLETE")
            due.assert_not_called()


if __name__ == "__main__":
    unittest.main()
