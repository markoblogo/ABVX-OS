import importlib.util, tempfile, unittest, json
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sp',ROOT/'scripts/run_jekyll_second_pass_v7.py'); sp=importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)

class SecondPassTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        ids=[f'synthetic:{x}' for x in sorted(sp.TARGETS)]
        (root/'semantic-qa.json').write_text(json.dumps({'records':[{'blockId':i,'classification':'SECOND_PASS_REQUIRED','defect':'Synthetic test defect'} for i in ids]}))
        source=root/'source.json';source.write_text(json.dumps([{'block_id':i,'source_text':'Synthetic paragraph'} for i in ids]))
        (root/'combined-output.json').write_text(json.dumps({'completed':[{'blockId':i,'translation':'sona'} for i in ids]}))
        ledger=root/'ledger.json';ledger.write_text('{}')
        for name,value in [('V7',root),('QA',root/'semantic-qa.json'),('SRC',source),('LEDGER',ledger),('OUT',root/'second-pass')]:
            p=patch.object(sp,name,value);p.start();self.addCleanup(p.stop)

    def test_queue_is_exactly_approved_five(self):
        self.assertEqual({x['source']['block_id'].split(':')[-1] for x in sp.queue()}, {'b0005','b0013','b0014','b0028','b0038'})
    def test_valid_requires_completed_visible_revision(self):
        self.assertFalse(sp.valid({'status':'incomplete','incompleteDetails':None,'visibleOutput':'TRANSLATION: x','revisedTranslation':'x'}))
        self.assertFalse(sp.valid({'status':'completed','incompleteDetails':None,'visibleOutput':'','revisedTranslation':''}))
    def test_dry_run_is_non_network(self):
        with tempfile.TemporaryDirectory(): self.assertEqual(sp.main(['--dry-run']),0)

if __name__=='__main__': unittest.main()
