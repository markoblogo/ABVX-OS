import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from abvx_harness import mac_disk_policy as p


class DiskPolicyTests(unittest.TestCase):
    def test_storage_scan_claim_limits_repetition(self):
        from abvx_harness import mac_operator as op
        with tempfile.TemporaryDirectory() as folder:
            state=Path(folder)
            snapshot=dict(time=10000,evidence={'pressure':{'code':0,'output':'1'}})
            with patch('abvx_harness.mac_codex_growth._measure',return_value={'status':'TIME_LIMIT','time':10000}) as measure:
                self.assertEqual(p.observe_storage(state,snapshot,op.load,op.save)['status'],'TIME_LIMIT')
                self.assertEqual(p.observe_storage(state,snapshot,op.load,op.save)['status'],'NOT_DUE')
                measure.assert_called_once()

    def test_storage_scan_defers_under_pressure(self):
        with patch('abvx_harness.mac_codex_growth._measure') as measure:
            result=p.observe_storage(None,dict(time=10000,evidence={'pressure':{'code':0,'output':'2'}}),None,None)
            self.assertEqual(result['status'],'DEFERRED_PRESSURE')
            measure.assert_not_called()

    def test_boot_boundary_discards_pre_restart_trend(self):
        samples=[dict(time=6000,disk_free=1*p.GIB,disk_path='/',boot_id='old'),
                 dict(time=7000,disk_free=1*p.GIB,disk_path='/',boot_id='old')]
        self.assertEqual(p.assess(20*p.GIB,'/',10000,samples,boot_id='new')['trend'],'UNKNOWN')

    def test_swap_threshold_and_denied_probe(self):
        ev={'swap':{'code':0,'output':'vm.swapusage: total = 4096.00M  used = 3000.00M free = 1096.00M'}}
        self.assertEqual(p.memory(ev,'a',10000,[])['status'],'REVIEW')
        ev['swap']['code']=1
        self.assertEqual(p.memory(ev,'a',10000,[])['status'],'UNKNOWN')

    def test_swap_growth_requires_same_boot(self):
        ev={'swap':{'code':0,'output':'total = 2048M used = 1024M'}}
        samples=[dict(time=8200,boot_id='a',memory_policy={'used_bytes':0})]
        self.assertEqual(p.memory(ev,'a',10000,samples)['growth_gib_per_hour'],2)
        self.assertEqual(p.memory(ev,'a',10000,samples)['status'],'REVIEW')
        self.assertIsNone(p.memory(ev,'b',10000,samples)['growth_gib_per_hour'])

    def test_boundaries(self):
        for free, mode in [(0,'EMERGENCY'), (8,'CRITICAL'), (15,'WARNING'),
                           (25,'WATCH'), (40,'NORMAL')]:
            self.assertEqual(p.assess(free*p.GIB, '/', 10000, [])['mode'], mode)

    def test_trend_requires_matching_volume_and_history(self):
        samples=[{'time': 6300, 'disk_free': 32*p.GIB, 'disk_path': '/'},
                 {'time': 8000, 'disk_free': 31*p.GIB, 'disk_path': '/'}]
        result=p.assess(30*p.GIB, '/', 9900, samples)
        self.assertEqual(result['trend'], 'FALLING')
        self.assertGreater(result['hours_to_8_gib'], 0)
        self.assertEqual(p.assess(30*p.GIB, '/other', 9900, samples)['trend'], 'UNKNOWN')
        self.assertEqual(p.assess(30*p.GIB, '/', 9900, samples[1:])['trend'], 'UNKNOWN')
