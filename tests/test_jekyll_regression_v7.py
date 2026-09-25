import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v7',ROOT/'scripts/run_jekyll_openai_regression_v7.py'); v7=importlib.util.module_from_spec(spec); spec.loader.exec_module(v7)

class JekyllV7RunnerTests(unittest.TestCase):
    def test_source_is_exactly_40_and_hashes_validate(self):
        self.assertEqual(len(v7.load_blocks()),40)
    def test_extracts_raw_responses_output_items(self):
        p={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'TRANSLATION: sona\nNOTES: risk'}]}]}
        visible,t,n,types=v7.extract(p); self.assertEqual(t,'sona'); self.assertEqual(n,'risk'); self.assertTrue(v7.valid({'status':'completed','incomplete_details':None,'visibleOutput':visible,'translation':t}))
    def test_incomplete_and_empty_are_not_success(self):
        self.assertFalse(v7.valid({'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},'visibleOutput':'TRANSLATION: x','translation':'x'}))
        self.assertFalse(v7.valid({'status':'completed','incomplete_details':None,'visibleOutput':'','translation':''}))
    def test_dry_run_does_not_require_key_or_call(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(v7.main(['--dry-run','--output',d]),0)

if __name__=='__main__': unittest.main()
