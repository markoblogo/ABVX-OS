import json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class DiscoveryEffectivenessAuditTests(unittest.TestCase):
 def test_reconciled_funnel_and_no_history_mutation(self):
  audit=json.loads((ROOT/'book-radar/audits/discovery-effectiveness-rn4-rn6-audit.json').read_text())
  self.assertEqual(audit['totals']['broad'],810)
  self.assertEqual(audit['totals']['deep'],69)
  self.assertEqual(audit['totals']['finalists'],22)
  self.assertEqual(audit['totals']['authorized'],1)
  self.assertEqual(audit['conclusion'],'MINOR_GENERATION_CALIBRATION_JUSTIFIED')
  for run in ('rn4','rn5','rn6'):
   self.assertTrue((ROOT/f'book-radar/runs/{run}/broad-opportunities.json').exists())

 def test_strategy_is_experimental_and_preserves_exploration(self):
  s=json.loads((ROOT/'book-radar/strategies/candidate-generation-v2.json').read_text())
  self.assertEqual(s['status'],'ACTIVE_EXPERIMENT')
  self.assertEqual(s['mix']['exploratory_weak_prior_target_pct'],25)
  self.assertIn('permanent scoring weights unchanged',s['explicit_non_changes'])
  self.assertIn('commercial_intent_confidence',s['experimental_fields'])
  self.assertIn('source_origin',s['experimental_fields'])

if __name__=='__main__': unittest.main()
