"""Synthetic policy fixtures, not market research or a production approval."""
import copy
import unittest
from datetime import date

from abvx_harness.book_radar_discovery import (
    BOOK_MARKETS, commercial_discovery_decision, rank_commercial_candidates,
)
from abvx_harness.harness import ValidationError

TODAY = date(2026, 9, 8)


def candidate(market='FICTION', tier='MODERATE', effort='LOW'):
    return {
        'id': market, 'market': market, 'buyer': 'Genre readers',
        'reading_motivation': 'Pleasure and emotional experience',
        'reader_promise': 'An atmospheric story that meets genre expectations',
        'book_format': 'EBOOK', 'discovery_path': 'Relevant genre category',
        'claims': {key: {'status': 'SUPPORTED', 'source_ids': ['S1', 'S2'],
                        'rationale': 'Synthetic policy test only'}
                   for key in ('book_demand', 'reader_choice', 'reachability', 'unit_economics')},
        'observations': [{'source_id': source, 'independence_key': origin,
                          'observed_at': '2026-09-01', 'observation': 'Synthetic book purchase',
                          'interpretation': 'Comparable demand', 'alternative_explanation': 'Author following',
                          'evidence_kind': 'PURCHASE'}
                         for source, origin in [('S1', 'A'), ('S2', 'B')]],
        'commercial_tier': tier, 'commercial_rationale': 'Synthetic evidence tier',
        'production_effort': effort, 'production_plan': 'Draft, edit, genre reader review',
        'quality_gate': 'Narrative coherence and genre satisfaction',
        'rights_status': 'CLEAR', 'delivery_status': 'FEASIBLE',
        'demand_window': {'closes': None, 'preparation_days': 45},
    }


class CommercialFirstTests(unittest.TestCase):
    def test_all_markets_can_qualify_without_a_practical_task_or_gap(self):
        for market in BOOK_MARKETS:
            with self.subTest(market=market):
                self.assertEqual(commercial_discovery_decision(candidate(market), as_of=TODAY),
                                 'DEEP_SCAN_ELIGIBLE')

    def test_commercial_priority_precedes_production_ease(self):
        strong = candidate('FICTION', 'STRONG', 'HIGH')
        moderate = candidate('BUSINESS', 'MODERATE', 'LOW')
        self.assertEqual(rank_commercial_candidates([moderate, strong], as_of=TODAY),
                         [strong, moderate])

    def test_ease_breaks_commercial_tier_tie(self):
        slow, easy = candidate('FICTION', effort='HIGH'), candidate('BUSINESS')
        self.assertEqual(rank_commercial_candidates([slow, easy], as_of=TODAY), [easy, slow])

    def test_easy_production_cannot_rescue_weak_demand(self):
        self.assertEqual(rank_commercial_candidates([candidate(tier='WEAK')], as_of=TODAY), [])

    def test_unknown_and_negative_are_distinct(self):
        for status, expected in [('UNKNOWN', 'INSUFFICIENT_EVIDENCE'),
                                 ('NEGATIVE', 'REJECTED_ON_EVIDENCE')]:
            c = candidate()
            c['claims']['reachability']['status'] = status
            self.assertEqual(commercial_discovery_decision(c, as_of=TODAY), expected)

    def test_trends_and_requests_do_not_become_purchase_evidence(self):
        for kind in ('TREND', 'READER_REQUEST', 'LISTING'):
            c = candidate()
            c['observations'][1]['evidence_kind'] = kind
            self.assertEqual(commercial_discovery_decision(c, as_of=TODAY), 'INSUFFICIENT_EVIDENCE')

    def test_independence_must_belong_to_demand_sources(self):
        c = candidate()
        c['observations'][1]['independence_key'] = ' a '
        unrelated = copy.deepcopy(c['observations'][0])
        unrelated.update(source_id='S3', independence_key='C')
        c['observations'].append(unrelated)
        self.assertEqual(commercial_discovery_decision(c, as_of=TODAY), 'INSUFFICIENT_EVIDENCE')

    def test_unresolved_citations_fail(self):
        c = candidate()
        c['claims']['reader_choice']['source_ids'] = ['MISSING']
        with self.assertRaises(ValidationError):
            commercial_discovery_decision(c, as_of=TODAY)

    def test_delivery_and_rights_are_not_overridden(self):
        for key, value, expected in [
            ('rights_status', 'UNKNOWN', 'INSUFFICIENT_EVIDENCE'),
            ('rights_status', 'BLOCKED', 'REJECTED_ON_EVIDENCE'),
            ('delivery_status', 'INFEASIBLE', 'ATTRACTIVE_BUT_NOT_FOR_US'),
        ]:
            c = candidate(tier='STRONG')
            c[key] = value
            self.assertEqual(commercial_discovery_decision(c, as_of=TODAY), expected)
        c = candidate()
        c['demand_window']['closes'] = '2026-09-10'
        self.assertEqual(commercial_discovery_decision(c, as_of=TODAY), 'ATTRACTIVE_BUT_NOT_FOR_US')
