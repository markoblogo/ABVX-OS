import tempfile
import shutil
import copy
import hashlib
import json
from pathlib import Path
import unittest

from abvx_harness.book_radar_reachability import assess, validate
from abvx_harness.harness import ValidationError

ROOT = Path(__file__).parent / 'fixtures/reachability'
AUDIT = ROOT


def fixture():
    cases = json.loads((AUDIT / 'cases.json').read_text())['cases']
    c = copy.deepcopy(next(c for c in cases if c['id'] == 'sock'))
    c['origin'] = 'SYNTHETIC'
    c['id'] = 'test:synthetic'
    return c


class ReachabilityCalibrationTests(unittest.TestCase):
    def test_unknown_is_not_fail(self):
        c = fixture(); c['witnesses'] = []
        r = assess(c)
        self.assertEqual(r['ladder']['R1'], 'UNKNOWN')
        self.assertEqual(r['gap_recommendation'], 'PARK')
        self.assertNotIn('FAIL', r['ladder'].values())

    def test_recent_listing_is_not_new_entrant(self):
        r = assess(fixture())
        self.assertEqual(r['ladder']['R1'], 'SUPPORTED')
        self.assertEqual(r['ladder']['R2'], 'UNKNOWN')
        self.assertEqual(r['cold_start_claim'], 'UNKNOWN')

    def test_new_edition_is_not_cold_start(self):
        c = fixture(); c['witnesses'][0].update(creator='NEW_OR_WEAK', release='NEW_EDITION')
        r = assess(c)
        self.assertEqual(r['ladder']['R2'], 'UNKNOWN')
        self.assertEqual(r['cold_start_claim'], 'CONTRADICTED')

    def test_organic_visibility_is_not_sales(self):
        c = fixture(); c['witnesses'][0]['activity'] = 'NONE'
        r = assess(c)
        self.assertEqual(r['ladder']['R3'], 'UNKNOWN')
        self.assertFalse(r['sales_inferred'])
        self.assertEqual(r['gap_recommendation'], 'PARK')

    def test_bsr_is_not_sales(self):
        r = assess(fixture())
        self.assertEqual(r['ladder']['R3'], 'SUPPORTED')
        self.assertFalse(r['sales_inferred'])
        self.assertFalse(r['entrant_activity_supported'])

    def test_ratings_are_not_current_velocity(self):
        c = fixture(); c['witnesses'][0]['activity'] = 'RATINGS'
        r = assess(c)
        self.assertEqual(r['ladder']['R3'], 'UNKNOWN')
        self.assertEqual(r['current_rating_velocity'], 'UNKNOWN')

    def test_r1_r2_are_not_production_go(self):
        c = fixture(); c['witnesses'][0].update(creator='NEW_OR_WEAK', release='NEW_WORK')
        r = assess(c)
        self.assertEqual(r['ladder']['R2'], 'SUPPORTED')
        self.assertFalse(r['production_authorized'])
        self.assertFalse(r['gap_collection_authorized'])

    def test_demand_cannot_rescue_zero_reachability(self):
        for key in ('identity', 'organic', 'context', 'relevance'):
            c = fixture(); c['witnesses'][0][key] = 'UNKNOWN'
            self.assertEqual(assess(c)['gap_recommendation'], 'PARK', key)

    def test_cheap_experiment_is_not_market_evidence(self):
        c = fixture(); c['witnesses'] = []; c['research_cap_minutes'] = 1
        self.assertEqual(assess(c)['ladder']['R1'], 'UNKNOWN')
        self.assertEqual(assess(c)['gap_recommendation'], 'PARK')

    def test_portfolio_success_not_automatic_transfer(self):
        c = fixture(); c['witnesses'] = []; c['own_paid'] = 'SUPPORTED'; c['own_validation_date'] = c['as_of']
        r = assess(c)
        self.assertEqual(r['ladder']['R5_paid'], 'SUPPORTED')
        self.assertEqual(r['ladder']['R1'], 'UNKNOWN')
        self.assertEqual(r['gap_recommendation'], 'PARK')
        self.assertFalse(r['commercial_reachability_pass'])

    def test_portfolio_zero_not_automatic_kill(self):
        c = fixture(); c['repeat_zero_prior'] = True; c['own_paid'] = 'CONTRADICTED'
        self.assertEqual(assess(c)['gap_recommendation'], 'PARK')
        c['material_difference'] = 'SUPPORTED'
        self.assertEqual(assess(c)['gap_recommendation'], 'PROMOTE_TO_GAP_ANALYSIS')

    def test_toki_pona_false_negative_case_retained(self):
        cases = json.loads((AUDIT / 'cases.json').read_text())['cases']
        c = copy.deepcopy(next(c for c in cases if c['id'] == 'toki-pona-before-first'))
        before = assess(c, ROOT)
        c['later_sales'] = 73
        with self.assertRaises(ValidationError): assess(c)
        self.assertEqual(before['ladder']['R1'], 'UNKNOWN')
        self.assertEqual(before['gap_recommendation'], 'PARK')
        self.assertIn('Later73paid not an input', c['rationale'])

    def test_historical_decisions_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT, root, dirs_exist_ok=True)
            (root / "state.json").write_text('{"synthetic":true}')
            paths = list(root.rglob("*"))
            before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
            for c in json.loads((root / "cases.json").read_text())["cases"]:
                assess(c, root)
            self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()})

    def test_repeat_does_not_supply_new_creator_or_sales(self):
        c = fixture(); c['witnesses'][0].update(repeat='SUPPORTED', activity='NONE')
        r = assess(c)
        self.assertEqual(r['ladder']['R4'], 'SUPPORTED')
        self.assertEqual(r['ladder']['R2'], 'UNKNOWN')
        self.assertEqual(r['ladder']['R3'], 'UNKNOWN')

    def test_activity_must_match_nonincumbent_witness(self):
        c = fixture(); new = copy.deepcopy(c['witnesses'][0]); new.update(id='different', creator='NEW_OR_WEAK', release='NEW_WORK', activity='NONE')
        c['witnesses'].append(new)
        r = assess(c)
        self.assertEqual(r['ladder']['R2'], 'SUPPORTED')
        self.assertEqual(r['ladder']['R3'], 'SUPPORTED')
        self.assertFalse(r['entrant_activity_supported'])

    def test_sponsored_or_wrong_context_does_not_qualify(self):
        for key in ('organic', 'context'):
            c = fixture(); c['witnesses'][0][key] = 'CONTRADICTED'
            self.assertEqual(assess(c)['ladder']['R1'], 'UNKNOWN')

    def test_rational_research_cap_required(self):
        c = fixture(); c['research_cap_minutes'] = None
        self.assertEqual(assess(c)['gap_recommendation'], 'PARK')
        c = fixture(); c['information_value'] = 'LOW'
        self.assertEqual(assess(c)['gap_recommendation'], 'PARK')
        c = fixture(); c['history_reviewed'] = False
        self.assertEqual(assess(c)['gap_recommendation'], 'PARK')

    def test_observed_barrier_not_just_missing_entrant_history(self):
        c = fixture(); c['route_barrier'] = 'SUPPORTED'
        self.assertEqual(assess(c)['reason'], 'OBSERVED_ENTRY_BARRIER')
        c['route_barrier'] = 'UNKNOWN'
        self.assertEqual(assess(c)['gap_recommendation'], 'PROMOTE_TO_GAP_ANALYSIS')

    def test_major_brand_or_reissue_alone_not_research_entry_evidence(self):
        for key, value in [('creator', 'DOMINANT'), ('release', 'NEW_EDITION'), ('release', 'NEW_FORMAT')]:
            c = fixture(); c['witnesses'][0][key] = value
            r = assess(c)
            self.assertEqual(r['ladder']['R1'], 'SUPPORTED')
            self.assertEqual(r['gap_recommendation'], 'PARK')

    def test_cutoff_blocks_hindsight(self):
        c = fixture(); c['cutoff'] = '2026-09-01'
        c['own_paid'] = 'SUPPORTED'; c['own_validation_date'] = '2026-10-02'
        r = assess(c)
        self.assertEqual(r['ladder']['R1'], 'UNKNOWN')
        self.assertEqual(r['ladder']['R5_paid'], 'UNKNOWN')

    def test_unknown_future_old_date_not_recent(self):
        for value in (None, '2026-10-05', '2025-10-04'):
            c = fixture(); c['witnesses'][0]['publication_date'] = value
            self.assertEqual(assess(c)['ladder']['R1'], 'UNKNOWN')

    def test_provenance_and_schema_fail_closed(self):
        c = fixture(); c['witnesses'][0]['evidence_ids'] = ['missing']
        with self.assertRaises(ValidationError): validate(c)
        c = fixture(); c['evidence'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValidationError): validate(c, ROOT)

    def test_all_five_same_policy(self):
        cases = json.loads((AUDIT / 'cases.json').read_text())['cases']
        expected = {'qgis': 'PARK', 'solo': 'PROMOTE_TO_GAP_ANALYSIS', 'sock': 'PROMOTE_TO_GAP_ANALYSIS', 'bicycle': 'PARK', 'technician': 'PARK'}
        for c in cases[:5]: self.assertEqual(assess(c, ROOT)['gap_recommendation'], expected[c['id']])

    def test_policy_remains_prospective_owner_gated(self):
        c = fixture()
        c['research_cap_minutes'] = 20
        r = assess(c, ROOT)
        self.assertEqual(r['gap_recommendation'], 'PROMOTE_TO_GAP_ANALYSIS')
        self.assertFalse(r['production_authorized'])
        self.assertFalse(r['gap_collection_authorized'])
        c['research_cap_minutes'] = 21
        with self.assertRaises(ValidationError):
            assess(c, ROOT)



if __name__ == '__main__':
    unittest.main()
