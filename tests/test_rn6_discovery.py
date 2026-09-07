import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class RN6DiscoveryTests(unittest.TestCase):
    def load(self,name):
        return json.loads((ROOT/'book-radar/runs/rn6'/name).read_text())

    def test_counts_ids_and_languages(self):
        broad=self.load('broad-opportunities.json')
        self.assertEqual(broad['count'],330)
        self.assertEqual(len({x['id'] for x in broad['opportunities']}),330)
        self.assertEqual({x['language'] for x in broad['opportunities']},{'EN','FR','UK','PL','RU','BE'})
        self.assertEqual(self.load('deep-scan.json')['count'],27)
        self.assertEqual(self.load('top-ten.json')['count'],10)

    def test_similarity_uses_complete_catalog_and_separate_architecture(self):
        audit=self.load('portfolio-similarity-audit.json')
        self.assertTrue(audit['catalog_complete_for_known_projects'])
        self.assertGreaterEqual(len(audit['catalog_checked']),9)
        for result in audit['results']:
            self.assertIn('topic_similarity',result)
            self.assertIn('product_architecture_similarity',result)

    def test_no_product_is_persisted_and_no_production_started(self):
        gates=self.load('investment-gates.json')
        contract=self.load('production-contract.json')
        self.assertEqual(gates['final_decision'],'NO_PRODUCT')
        self.assertEqual(gates['tested'],10)
        self.assertFalse(gates['production_started'])
        self.assertFalse(contract['production_authorized'])
        self.assertFalse(contract['production_started'])

    def test_evidence_labels_and_economics(self):
        top=self.load('top-ten.json')['candidates']
        for item in top:
            self.assertRegex(item['amazon_evidence'],r'^(OBSERVED|INFERRED|UNKNOWN)')
            self.assertGreater(item['anton_hours'],0)
            self.assertGreaterEqual(item['ev_90_day'],0)

if __name__=='__main__': unittest.main()
