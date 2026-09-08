import json, unittest
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
class RN7DiscoveryTests(unittest.TestCase):
 def load(self,n):return json.loads((ROOT/'book-radar/runs/rn7'/n).read_text())
 def test_counts_mix_and_fresh_ids(self):
  b=self.load('broad-opportunities.json')
  self.assertEqual(b['count'],360);self.assertEqual(b['generation_mix'],{'commercial_intent':270,'exploratory_weak_prior':90})
  self.assertEqual(len({x['id'] for x in b['opportunities']}),360);self.assertEqual(self.load('deep-scan.json')['count'],30);self.assertEqual(self.load('top-ten.json')['count'],10)
 def test_experimental_fields_persist_but_are_not_permanent_score(self):
  b=self.load('broad-opportunities.json')['opportunities']
  for x in b:self.assertIn('commercial_intent_confidence',x['experimental_signals'])
  model=json.loads((ROOT/'book-radar/scoring-models/radar-native-v1.json').read_text())
  self.assertNotIn('commercial_intent_confidence',model['weights'])
 def test_conditional_gate_and_no_production(self):
  g=self.load('investment-gates.json');c=self.load('production-contract.json')
  self.assertEqual(g['final_decision'],'CONDITIONAL_GO_AWAITING_HUMAN_PRODUCT_GATE');self.assertFalse(g['production_started'])
  self.assertEqual(c['representative_product_gate'],'SAMPLE_CREATED_PENDING_HUMAN_REVIEW')
 def test_representative_sample_is_eight_pages(self):
  p=ROOT/'book-radar/runs/rn7/representative-sample/rn7-001-french-property-ddt-decoder-sample.pdf'
  self.assertEqual(len(PdfReader(str(p)).pages),8)
if __name__=='__main__':unittest.main()
