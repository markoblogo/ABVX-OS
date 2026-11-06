"""Research menu ordering must retain the supplied review, without granting GO."""
import hashlib
import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from abvx_harness import book_radar_markets as m
from abvx_harness.harness import ValidationError
from test_book_radar_markets import packet, ASOF


class ResearchOrderTests(unittest.TestCase):
    def test_acquisition_entrypoint_uses_review_order_and_rejects_bad_ranking_before_writing(self):
        spec = importlib.util.spec_from_file_location('radar_research_entry',
            Path(__file__).parents[1] / 'scripts/run_multi_market_radar.py')
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = root / 'proof.txt'
            proof.write_text('SYNTHETIC ONLY')
            sha = hashlib.sha256(proof.read_bytes()).hexdigest()
            bundle = packet('a-low')
            other = packet('z-high')
            bundle['opportunities'] += other['opportunities']
            bundle['observations'] += other['observations']
            for row in bundle['observations']:
                row['assessments']['commercial_validation'].update(value=None, metric_keys=[])
                row.update(evidence_path=proof.name, evidence_sha256=sha)
            source = root / 'input.json'
            source.write_text(json.dumps(bundle))
            receipt = {'attempts': [dict(marketplace=market, source_url='https://www.' + m.PROVIDERS[market].domain,
                evidence_ref=proof.name, evidence_sha256=sha, captured_at_utc=ASOF + 'T12:00:00Z',
                status='AVAILABLE' if market == 'etsy' else 'ACCESS_FAILED', method='LIVE_BROWSER',
                blocker='SYNTHETIC unavailable source') for market in m.MARKETS]}
            receipt['attempts'][1]['source_url'] = bundle['observations'][0]['source_url']
            acquisition = root / 'acquisition.json'
            acquisition.write_text(json.dumps(receipt))
            ranking = root / 'ranking.json'
            ranking.write_text(json.dumps({'opportunities': [{'id': 'z-high', 'rank': 1}]}))
            args = argparse.Namespace(input=source, acquisition=acquisition, ranking=ranking,
                run_id='synthetic-ranked', as_of=ASOF, hours=4, history=root / 'learning')
            with patch.object(entry, 'REPO', root):
                result = entry.run(args)
                menu = json.loads((Path(result['output']) / 'weekly.json').read_text())
                self.assertEqual(menu['actions'][0]['opportunity_id'], 'z-high')
                self.assertFalse(menu['production_authorized'])
                ranking.write_text(json.dumps({'opportunities': [{'id': 'unlinked', 'rank': 1}]}))
                args.run_id = 'synthetic-invalid'
                with self.assertRaises(ValidationError):
                    entry.run(args)
                self.assertFalse((root / '.tmp/multi-market-radar/runs/synthetic-invalid').exists())

    def test_review_priority_orders_research_without_qualifying_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = root / 'proof.txt'
            proof.write_text('SYNTHETIC ONLY')
            for oid in ('a-low', 'z-high'):
                bundle = packet(oid)
                bundle['observations'][0]['assessments']['commercial_validation'].update(value=None, metric_keys=[])
                bundle['observations'][0].update(evidence_path=proof.name,
                    evidence_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
                source = root / (oid + '.json')
                source.write_text(json.dumps(bundle))
                m.import_bundle(root, source)
            ranking = {'opportunities': [{'id': 'z-high', 'rank': 1}, {'id': 'a-low', 'rank': 2}]}
            before = m.state_path(root).read_bytes()
            legacy = m.weekly(root, ASOF)
            self.assertEqual([a['opportunity_id'] for a in legacy['actions']], ['a-low', 'z-high'])
            result = m.weekly(root, ASOF, research_ranking=ranking)
            self.assertEqual([a['opportunity_id'] for a in result['actions']], ['z-high', 'a-low'])
            self.assertTrue(all(a['kind'] == 'RESEARCH' and not a['production_authorized'] for a in result['actions']))
            self.assertEqual(before, m.state_path(root).read_bytes())

    def test_malformed_or_unlinked_priority_is_rejected(self):
        for rows in ([{'id': 'unknown', 'rank': 1}],
                     [{'id': 'a', 'rank': True}],
                     [{'id': 'a', 'rank': 0}],
                     [{'id': 'a', 'rank': 1}, {'id': 'a', 'rank': 2}],
                     [{'id': 'a', 'rank': 1}, {'id': 'z', 'rank': 1}]):
            with self.subTest(rows=rows), self.assertRaises(ValidationError):
                m.research_priorities({'opportunities': rows}, {'a', 'z'})

    def test_research_rank_cannot_overtake_a_qualified_market(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = root / 'proof.txt'
            proof.write_text('SYNTHETIC ONLY')
            for oid in ('a-research', 'z-qualified'):
                bundle = packet(oid)
                if oid == 'a-research':
                    bundle['observations'][0]['assessments']['commercial_validation'].update(value=None, metric_keys=[])
                bundle['observations'][0].update(evidence_path=proof.name,
                    evidence_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
                source = root / (oid + '.json')
                source.write_text(json.dumps(bundle))
                m.import_bundle(root, source)
            result = m.weekly(root, ASOF, research_ranking={'opportunities': [
                {'id': 'a-research', 'rank': 1}, {'id': 'z-qualified', 'rank': 2}]})
            self.assertEqual(result['actions'][0]['opportunity_id'], 'z-qualified')
            self.assertEqual(result['actions'][0]['kind'], 'PRODUCTION_PROPOSAL')
            self.assertFalse(result['production_authorized'])
