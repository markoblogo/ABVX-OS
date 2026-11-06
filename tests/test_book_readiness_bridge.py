"""Synthetic end-to-end archive routing; no market claims, manuscripts or publication."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import test_book_readiness as inventory_fixtures
import test_book_radar_learning as market_fixtures
from abvx_harness import book_readiness as readiness
from abvx_harness import book_radar_markets as markets
from abvx_harness import book_radar_wide as wide

DAY = '2026-11-05'


class ReadinessBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root, self.site = self.base/'os', self.base/'site'
        inventory_fixtures.ReadinessTests.fixture(self.root, self.site)
        self.policy_path = self.root/'book-radar/readiness-policy.json'
        policy = json.loads(self.policy_path.read_text())
        for item in policy['candidates']:
            item['outline'] = {'entries': 1, 'words': 1, 'themes': 1}
        self.policy_path.write_text(json.dumps(policy))
        self.article('first')

    def article(self, slug, **kwargs):
        return inventory_fixtures.ReadinessTests.article(
            self.site, slug, ' '.join([slug + ' meaningful original material']*50), **kwargs)

    def snapshot(self, day=DAY):
        return readiness.refresh(self.root, self.site, as_of=day)

    def test_early_unknown_rights_enters_research_not_manuscript_or_production(self):
        state = self.snapshot()
        c = state['candidates']['kitchen-stories']
        self.assertEqual(c['stage'], 'outline_ready')
        self.assertTrue(c['market_assessment_eligible'])
        self.assertEqual(c['rights_cleared_words'], 0)
        handoff = readiness.research_handoff(self.root, DAY)
        row = handoff['candidates'][0]
        self.assertEqual(row['id'], 'readiness:kitchen-stories')
        self.assertEqual(row['commercial_potential'], 'NOT_ASSESSED')
        self.assertFalse(row['production_authorized'])
        self.assertTrue(any('rights' in x for x in row['gaps']))
        self.assertTrue(Path(row['source_report']).is_absolute())
        self.assertEqual(row['source_refs'][0]['url'], 'https://abvx.xyz/writing/first')

    def test_explicitly_blocked_and_excluded_material_is_not_offered(self):
        self.article('blocked'); self.article('excluded')
        policy = json.loads(self.policy_path.read_text())
        policy['article_annotations'] = {'blocked': {'rights': 'blocked'}, 'excluded': {'exclude': True}}
        self.policy_path.write_text(json.dumps(policy))
        self.snapshot()
        row = readiness.research_queue(self.root, DAY)[0]
        self.assertEqual([x['id'] for x in row['source_refs']], ['first'])
        self.assertEqual(row['available_entries'], 1)

    def test_large_archive_is_researchable_without_fitting_a_page_quota(self):
        policy = json.loads(self.policy_path.read_text())
        for item in policy['candidates']: item['target_pages'] = [1, 4]
        self.policy_path.write_text(json.dumps(policy))
        self.snapshot(); row = readiness.research_queue(self.root, DAY)[0]
        self.assertTrue(any('pagination' in gap for gap in row['gaps']))
        self.assertFalse(row['production_authorized'])

    def test_inventory_only_psychology_is_not_a_new_book_recommendation(self):
        self.article('psychology-notebook-test', tag='psychology-notebook')
        self.snapshot(); handoff = readiness.research_handoff(self.root, DAY)
        self.assertNotIn('psychology-notebook', [x['candidate_id'] for x in handoff['candidates']])
        self.assertIn({'candidate_id': 'psychology-notebook', 'reason': 'EXISTING_BOOK_OVERLAP_REVIEW_REQUIRED'}, handoff['withheld'])

    def test_future_retained_missing_and_corrupt_inventory_are_distinct(self):
        self.assertEqual(readiness.research_handoff(self.root, DAY)['status'], 'UNAVAILABLE')
        self.snapshot()
        future = readiness.research_handoff(self.root, '2026-11-04')
        self.assertEqual(future['status'], 'FUTURE_EXCLUDED'); self.assertFalse(future['candidates'])
        old = readiness.research_handoff(self.root, '2026-11-09')
        self.assertEqual(old['status'], 'RETAINED_REFRESH_REQUIRED')
        self.assertEqual(old['candidates'][0]['observed_as_of'], DAY)
        (self.root/'.tmp/book-readiness/state.json').write_text('{invalid')
        bad = readiness.research_handoff(self.root, DAY)
        self.assertEqual(bad['status'], 'BLOCKED'); self.assertFalse(bad['candidates'])

    def test_failed_refresh_is_shared_and_cannot_admit_same_day_retained_material(self):
        self.snapshot()
        with patch.object(readiness, 'refresh_for_weekly', return_value={'status': 'BLOCKED', 'reason': 'Synthetic missing source'}):
            handoff = readiness.weekly_handoff(self.root, DAY)
        self.assertEqual(handoff['status'], 'REFRESH_BLOCKED')
        review = wide.weekly_book_review(self.root, DAY, readiness_snapshot=handoff)
        weekly = markets.weekly(self.base/'isolated', DAY, readiness_snapshot=handoff)
        self.assertEqual(review['commercial_intake'], [])
        self.assertEqual(weekly['book_readiness']['status'], 'REFRESH_BLOCKED')
        self.assertIn('retained material is not freshly verified', markets.render(weekly))
        self.assertFalse(review['owner_production_review_candidates'])

    def test_material_digest_changes_with_content_not_capture_date(self):
        self.snapshot(); a = readiness.research_queue(self.root, DAY)[0]
        self.snapshot('2026-11-06'); b = readiness.research_queue(self.root, '2026-11-06')[0]
        self.assertEqual(a['material_review_digest'], b['material_review_digest'])
        p = self.site/'content/writing/first.md'; p.write_text(p.read_text() + '\nA substantive changed conclusion.')
        self.snapshot('2026-11-06'); c = readiness.research_queue(self.root, '2026-11-06')[0]
        self.assertNotEqual(b['material_review_digest'], c['material_review_digest'])

    def test_archive_enters_existing_commercial_queue_without_external_manifest(self):
        self.snapshot(); state = self.root/'.tmp/book-readiness/state.json'; before = state.read_bytes()
        result = wide.weekly_book_review(self.root, DAY)
        self.assertEqual(result['commercial_pipeline']['next_checks'][0]['id'], 'readiness:kitchen-stories')
        self.assertEqual(result['commercial_pipeline']['next_checks'][0]['next_stage'], 'demand')
        self.assertEqual(result['owner_production_review_candidates'], [])
        self.assertFalse(result['current_acquisition'])
        self.assertEqual(state.read_bytes(), before)
        self.assertFalse((self.root/'book-radar/state.json').exists())

    def test_current_bound_review_deduplicates_and_changed_material_invalidates_only_projection(self):
        self.snapshot(); handoff = readiness.research_handoff(self.root, DAY); row = handoff['candidates'][0]
        card = {'id': row['id'], 'status': 'RESEARCH', 'production_authorized': False,
                'readiness_ref': {'material_review_digest': row['material_review_digest']}}
        menu = {'as_of': DAY, 'cards': [card], 'research_queue': [], 'top_owner_review': [],
                'commercial_reviews': {row['id']: {'demand': {'status': 'REVIEW', 'reason': 'synthetic'}}}}
        original = copy.deepcopy(menu)
        merged, notes = wide.merge_readiness_menu(menu, handoff)
        self.assertEqual(merged['research_queue'], [])
        self.assertEqual(merged['commercial_reviews'], original['commercial_reviews'])
        handoff['candidates'][0]['material_review_digest'] = 'changed'
        changed, notes = wide.merge_readiness_menu(menu, handoff)
        self.assertEqual(changed['commercial_reviews'][row['id']], {})
        self.assertEqual(menu, original)
        self.assertEqual(notes[0]['reason'], 'MATERIAL_MISSING_STALE_OR_CHANGED_RECHECK')

    def test_queue_cap_and_stale_source_never_promote_or_silently_disappear(self):
        self.snapshot(); handoff = readiness.research_handoff(self.root, DAY)
        menu = {'as_of': DAY, 'cards': [], 'research_queue': [
            {'id': 'external-' + str(i), 'production_authorized': False} for i in range(24)]}
        merged, notes = wide.merge_readiness_menu(menu, handoff)
        self.assertEqual(len(merged['research_queue']), 24)
        self.assertEqual(notes[0]['reason'], 'EXISTING_QUEUE_CAP_REVIEW_NEXT_BATCH')
        handoff = readiness.research_handoff(self.root, '2026-11-09')
        merged, notes = wide.merge_readiness_menu({'cards': []}, handoff)
        self.assertEqual(merged['research_queue'], [])
        self.assertEqual(notes[0]['reason'], 'REFRESH_MATERIAL_BEFORE_CURRENT_RESEARCH')

    def test_separate_market_root_receives_real_inventory_without_a_copy(self):
        self.snapshot(); isolated = self.base/'isolated-market-root'
        report = markets.report(isolated, DAY, readiness_root=self.root)
        weekly = markets.weekly(isolated, DAY, readiness_root=self.root)
        self.assertEqual(report['book_readiness_research_queue'][0]['id'], 'readiness:kitchen-stories')
        self.assertEqual(weekly['book_readiness_research_queue'], report['book_readiness_research_queue'])
        self.assertIn('Kitchen Notes', markets.render(weekly))
        self.assertIn('market NOT_ASSESSED', markets.render(weekly))
        self.assertFalse((isolated/'.tmp/book-readiness/state.json').exists())
        self.assertEqual(weekly['actions'], [])

    def test_real_runner_path_freezes_handoff_and_renders_weekly_with_synthetic_market_evidence(self):
        self.snapshot()
        fixture = market_fixtures.LearningTests(); fixture.setUp(); self.addCleanup(fixture.tmp.cleanup)
        source = fixture.run_fixture('synthetic-source', day=DAY)
        proof = source/'proof.json'; sha = hashlib.sha256(proof.read_bytes()).hexdigest()
        receipt = {'attempts': [dict(marketplace=m, status='AVAILABLE' if m=='udemy' else 'ACCESS_FAILED',
            source_url='https://www.udemy.com/course/synthetic/' if m=='udemy' else 'https://example.org/'+m,
            evidence_ref=proof.name, evidence_sha256=sha, captured_at_utc=DAY+'T12:00:00Z',
            method='LIVE_BROWSER', blocker='SYNTHETIC unavailable source') for m in markets.MARKETS]}
        acquisition = source/'acquisition.json'; acquisition.write_text(json.dumps(receipt))
        spec = importlib.util.spec_from_file_location('readiness_runner', Path(__file__).parents[1]/'scripts/run_multi_market_radar.py')
        entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
        args = Namespace(input=source/'input.json', acquisition=acquisition, ranking=None,
                         run_id='synthetic-readiness-bridge', as_of=DAY, hours=4, history=self.base/'learning')
        with patch.object(entry, 'REPO', self.root): result = entry.run(args)
        output = Path(result['output'])
        weekly = json.loads((output/'weekly.json').read_text())
        self.assertEqual(weekly['book_readiness_research_queue'][0]['id'], 'readiness:kitchen-stories')
        self.assertTrue((output/'book-readiness.json').is_file())
        self.assertIn('Kitchen Notes', (output/'weekly.md').read_text())
        self.assertFalse(weekly['production_authorized'])
        self.assertFalse((output/'radar-root/.tmp/book-readiness/state.json').exists())


if __name__ == '__main__':
    unittest.main()
