import json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'book-radar/runs/rn5/representative-sample-v2'

class RN5PrototypeV2Tests(unittest.TestCase):
    def test_internal_qa_and_paid_value_layers(self):
        qa=json.loads((BASE/'prototype-v2-qa.json').read_text())
        thesis=json.loads((BASE/'product-thesis-v2.json').read_text())
        self.assertEqual(qa['status'],'PASS')
        self.assertEqual(qa['pages'],14)
        for key in ('paid_value_layer','proposal_decoding','claim_red_flag_decoder','calculation_layer','decision_scenario','question_generator','free_alternative_differentiation'):
            self.assertEqual(thesis['prototype_2'][key],'PASS')

    def test_full_production_is_authorized(self):
        thesis=json.loads((BASE/'product-thesis-v2.json').read_text())
        self.assertTrue(thesis['production_authorized'])
        self.assertEqual(thesis['human_gate_2']['result'],'PASS')
        self.assertEqual(thesis['next_gate'],'FULL PRODUCTION')

    def test_pdf_and_visual_qa_artifacts_exist(self):
        for name in ('solar-proposal-decoder-buyer-decision-system-prototype-v2.pdf','contact-sheet.png','high-risk-contact-sheet.png'):
            self.assertTrue((BASE/name).exists())

if __name__=='__main__': unittest.main()
