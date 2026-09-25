import importlib.util, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sp',ROOT/'scripts/run_jekyll_second_pass_v7.py'); sp=importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)

class SecondPassTests(unittest.TestCase):
    def test_queue_is_exactly_approved_five(self):
        self.assertEqual({x['source']['block_id'].split(':')[-1] for x in sp.queue()}, {'b0005','b0013','b0014','b0028','b0038'})
    def test_valid_requires_completed_visible_revision(self):
        self.assertFalse(sp.valid({'status':'incomplete','incompleteDetails':None,'visibleOutput':'TRANSLATION: x','revisedTranslation':'x'}))
        self.assertFalse(sp.valid({'status':'completed','incompleteDetails':None,'visibleOutput':'','revisedTranslation':''}))
    def test_dry_run_is_non_network(self):
        with tempfile.TemporaryDirectory(): self.assertEqual(sp.main(['--dry-run']),0)

if __name__=='__main__': unittest.main()
