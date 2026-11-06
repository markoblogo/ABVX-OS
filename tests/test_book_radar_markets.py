"""Synthetic fixtures test gates; they are never real market evidence or demo results."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from abvx_harness import book_radar_markets as m
from abvx_harness.book_radar import empty_state, _write_json, report as amazon_report
from abvx_harness.__main__ import main
from abvx_harness.harness import ValidationError

ASOF = '2026-10-08'


def signal(v, unit='count', status='VERIFIED'):
    return {'status': status, 'value': v, 'unit': unit, 'note': 'SYNTHETIC TEST ONLY'}


def packet(oid='test-one', market='etsy'):
    b = m.template(market)
    o = b['opportunities'][0]
    o.update(id=oid, topic='Synthetic topic ' + oid, audience='Synthetic buyer', motivation='Synthetic buyer job')
    p = o['proposals'][market]
    p.update(format='printable' if market == 'etsy' else 'book' if market == 'amazon' else 'course' if market == 'udemy' else 'edition', format_fit=4, reuse=3, risk=4,
             effort_hours=signal(4, 'hours', 'ESTIMATED'), first_step_hours=signal(1, 'hours', 'ESTIMATED'),
             production_cost=signal(10, 'USD', 'ESTIMATED'), rights_status='CLEAR', policy_review='CLEAR',
             policy_review_date=ASOF, policy_sources=['https://example.org/test-policy'], kdp_select_status='NOT_APPLICABLE',
             course_design='STRUCTURED_DEMONSTRATIONS', new_project=True, funding_goal=signal(1000, 'USD', 'ESTIMATED'),
             fulfillment_budget=signal(800, 'USD', 'ESTIMATED'), shipping_plan='Synthetic shipping plan', audience_plan='Synthetic audience test')
    r = m.observation_template(market, o, ASOF)
    r.update(id='obs:' + oid + ':' + market, storage_permission='RETAINED_AUTHORIZED', availability='AVAILABLE', period_start='2026-10-01', period_end=ASOF)
    demand, competition, commercial = {'etsy': ('searches', 'listing_count', 'paid_orders'), 'amazon': ('book_traction', 'listing_count', 'paid_orders'), 'udemy': ('search_volume', 'course_count', 'median_revenue'), 'kickstarter': ('backers', 'comparable_count', 'pledged')}[market]
    r['metrics'] = {demand: signal(10), competition: signal(10), commercial: signal(1500 if market == 'kickstarter' else 10, 'USD' if commercial in ('pledged', 'median_revenue') else 'count')}
    if market == 'amazon': r['metrics']['delivery_country'] = signal('US', None)
    if market == 'kickstarter':
        r['metrics'].update(goal=signal(1000, 'USD'), campaign_status=signal('successful', None))
    r['assessments'] = {k: {'value': 4, 'metric_keys': [metric], 'reason': 'SYNTHETIC test judgment'} for k, metric in [('demand', demand), ('competition_weakness', competition), ('commercial_validation', commercial)]}
    b['observations'] = [r]
    return b


class MultiMarketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, b, name='input.json'):
        b = copy.deepcopy(b)
        proof = self.root / 'synthetic-proof.txt'
        proof.write_text('SYNTHETIC UNIT TEST; NOT A MARKET OBSERVATION\n')
        for r in b['observations']:
            if any(s['status'] != 'MISSING' for s in r['metrics'].values()):
                r.update(evidence_path=proof.name, evidence_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
        path = self.root / name
        path.write_text(json.dumps(b))
        return path

    def ingest(self, b, name='input.json'):
        return m.import_bundle(self.root, self.write(b, name))

    def row(self):
        return m.report(self.root, ASOF)['opportunities'][0]

    def test_all_three_providers_and_existing_amazon_are_available(self):
        self.assertEqual(set(m.PROVIDERS), set(m.MARKETS))
        self.assertTrue(all(p.describe()['network_requests'] == 0 for p in m.PROVIDERS.values()))
        for market in m.MARKETS:
            m.validate(m.import_template(self.root, market, ASOF))
        self.assertFalse(m.state_path(self.root).exists())

    def test_import_is_idempotent_and_deduplicates_alias_query(self):
        b = packet(); path = self.write(b)
        self.assertEqual(m.import_bundle(self.root, path)['added']['observations'], 1)
        self.assertEqual(m.import_bundle(self.root, path)['added']['observations'], 0)
        b['observations'][0]['id'] = 'another-id'
        b['observations'][0]['query'] = ' replace_with_query  '
        self.assertEqual(self.ingest(b)['added']['observations'], 0)

    def test_conflicting_id_fails_without_changing_state(self):
        b = packet(); self.ingest(b); before = m.state_path(self.root).read_bytes()
        b['observations'][0]['metrics']['paid_orders']['value'] = 20
        with self.assertRaises(ValidationError): self.ingest(b)
        self.assertEqual(before, m.state_path(self.root).read_bytes())

    def test_retained_hash_and_escape_are_checked(self):
        b = packet(); path = self.write(b)
        (self.root/'synthetic-proof.txt').write_text('changed')
        with self.assertRaises(ValidationError): m.check(path)
        b = json.loads(path.read_text()); b['observations'][0]['evidence_path'] = '../outside.txt'
        path.write_text(json.dumps(b))
        with self.assertRaises(ValidationError): m.check(path)

    def test_missing_null_and_observed_zero_are_distinct(self):
        b = packet(); b['observations'][0]['metrics']['paid_orders']['value'] = 0
        self.ingest(b)
        self.assertEqual(self.row()['markets']['etsy']['ratings']['commercial_validation'], 1)
        self.assertFalse(self.row()['markets']['etsy']['eligible'])
        b['observations'][0]['metrics']['paid_orders']['status'] = 'MISSING'
        with self.assertRaises(ValidationError): self.ingest(b)

    def test_inferred_or_estimated_sales_do_not_pass_observed_purchase_gate(self):
        for status in ('INFERRED', 'ESTIMATED'):
            b = packet('test-' + status); b['observations'][0]['metrics']['paid_orders']['status'] = status
            self.ingest(b, status+'.json')
        self.assertTrue(all(not r['markets']['etsy']['eligible'] for r in m.report(self.root, ASOF)['opportunities']))

    def test_licensed_analytics_cannot_be_verified(self):
        b = packet(); r = b['observations'][0]
        r.update(source_kind='LICENSED_ANALYTICS', access_basis='LICENSED_EXPORT', source_url='https://example.org/analytics')
        with self.assertRaises(ValidationError): self.ingest(b)

    def test_language_geo_buyer_and_format_mismatch_never_transfer_demand(self):
        b = packet(); b['observations'][0]['language'] = 'FR'; self.ingest(b)
        self.assertFalse(self.row()['markets']['etsy']['eligible'])
        self.assertFalse(self.row()['markets']['amazon']['eligible'])
        self.assertEqual(self.row()['strategy'], 'RESEARCH_ONLY')

    def test_stale_unknown_and_future_periods_lower_confidence(self):
        for suffix, end in [('stale', '2025-01-01'), ('unknown', None), ('future', '2026-10-09')]:
            b = packet('test-'+suffix); r = b['observations'][0]; r['period_start'] = None; r['period_end'] = end
            if suffix == 'future': r['observed_at'] = end
            self.ingest(b, suffix+'.json')
        self.assertTrue(all(r['markets']['etsy']['confidence'] == 'LOW' for r in m.report(self.root, ASOF)['opportunities']))

    def test_partial_provider_failure_does_not_break_other_market(self):
        b = packet(); o = b['opportunities'][0]; other = m.template('udemy')['opportunities'][0]['proposals']['udemy'];o['proposals']['udemy'] = other
        r = m.observation_template('udemy', o, ASOF);r['availability'] = 'MISSING_CREDENTIALS';b['observations'].append(r)
        self.ingest(b)
        self.assertTrue(self.row()['markets']['etsy']['eligible'])
        self.assertFalse(self.row()['markets']['udemy']['eligible'])

    def test_cross_market_confirmation_uses_independent_upstream_not_platform_count(self):
        b = packet(); c = packet(market='udemy');o = b['opportunities'][0];o['proposals'].update(c['opportunities'][0]['proposals']);b['observations'] += c['observations']
        mirror=copy.deepcopy(c['observations'][0]);mirror.update(id='mirror',source_kind='LICENSED_ANALYTICS',access_basis='LICENSED_EXPORT',source_url='https://example.org/vendor',upstream_url='https://etsy.com')
        for s in mirror['metrics'].values():s['status']='ESTIMATED'
        b['observations'].append(mirror)
        self.ingest(b)
        self.assertEqual(self.row()['strategy'], 'SINGLE_MARKET')
        self.assertEqual(self.row()['markets']['etsy']['confidence'], 'MODERATE')
        self.assertTrue(self.row()['markets']['udemy']['eligible'])

    def test_independent_qualified_markets_allow_a_sequence(self):
        b = packet(); c = packet(market='udemy');b['opportunities'][0]['proposals'].update(c['opportunities'][0]['proposals']); b['observations'] += c['observations'];self.ingest(b)
        self.assertEqual(self.row()['strategy'], 'ETSY_FIRST')
        self.assertEqual(self.row()['secondary_markets'], ['udemy'])

    def test_policy_select_and_course_narration_block_production(self):
        b = packet(market='udemy');p = b['opportunities'][0]['proposals']['udemy'];p.update(reuse_mode='ADAPTED',kdp_select_status='ENROLLED',course_design='NARRATION_ONLY')
        self.ingest(b)
        a = self.row()['markets']['udemy']
        self.assertFalse(a['eligible']);self.assertEqual(len(a['blockers']), 2)
        self.assertEqual(m.weekly(self.root, ASOF)['actions'][0]['kind'], 'RESEARCH')

    def test_kickstarter_requires_success_and_funding_fulfillment(self):
        b = packet(market='kickstarter');b['observations'][0]['metrics']['campaign_status']['value']='failed'
        self.ingest(b)
        self.assertFalse(self.row()['markets']['kickstarter']['eligible'])
        self.assertEqual(self.row()['markets']['kickstarter']['commercial_scope'], 'CROWDFUNDING_ONLY')

    def test_amazon_english_france_delivery_is_not_us_evidence(self):
        b = packet(market='amazon');b['observations'][0]['metrics']['delivery_country']['value']='FR';self.ingest(b)
        self.assertFalse(self.row()['markets']['amazon']['eligible'])

    def test_weekly_two_book_ceiling_and_known_existing_capacity(self):
        for i in range(4):
            b = packet('amazon-'+str(i), 'amazon');r=copy.deepcopy(b['observations'][0]);r.update(id=r['id']+':second',source_kind='LICENSED_ANALYTICS',access_basis='LICENSED_EXPORT',source_url='https://example.org/research',upstream_url='https://example.org/independent-origin')
            for s in r['metrics'].values():s['status']='ESTIMATED'
            r['metrics']['marketplace_domain']=signal('amazon.com',None,'ESTIMATED')
            b['observations'].append(r);self.ingest(b,str(i)+'.json')
        self.assertEqual(len(m.weekly(self.root,ASOF,0)['actions']),2)
        self.assertEqual(len(m.weekly(self.root,ASOF,1)['actions']),1)
        self.assertEqual(len(m.weekly(self.root,ASOF,2)['actions']),0)
        self.assertEqual(len(m.weekly(self.root,ASOF)['actions']),0)

    def test_weak_evidence_generates_research_not_quota(self):
        self.ingest(m.template('etsy'))
        plan=m.weekly(self.root,ASOF,0)
        self.assertTrue(all(a['kind']=='RESEARCH' for a in plan['actions']))
        self.assertEqual(m.weekly(self.root,ASOF,0,hours=0.1)['actions'],[])
        with self.assertRaises(ValidationError):m.weekly(self.root,ASOF,0,hours=float('nan'))

    def test_rejected_researched_and_produced_need_explicit_reopen(self):
        b=packet();self.ingest(b)
        track={'schema_version':b['schema_version'],'opportunities':[],'observations':[],'decisions':[{'id':'decision-1','opportunity_id':'test-one','marketplace':'etsy','status':'RESEARCHED','date':ASOF,'reason':'Synthetic research done'}]}
        path=self.write(track,'track.json');m.track(self.root,path)
        self.assertEqual(m.weekly(self.root,ASOF,0)['actions'],[])
        track['decisions'][0].update(id='decision-2',status='APPROVED')
        with self.assertRaises(ValidationError):m.track(self.root,self.write(track,'track2.json'))
        track['decisions'][0].update(status='REOPENED',reason='New independent evidence')
        m.track(self.root,self.write(track,'reopen.json'))
        self.assertEqual(len(m.weekly(self.root,ASOF,0)['actions']),1)
        self.assertFalse(m.weekly(self.root,ASOF,0)['actions'][0]['production_authorized'])

    def test_export_roundtrip_preserves_evidence_and_history(self):
        b=packet();self.ingest(b)
        d={'schema_version':b['schema_version'],'opportunities':[],'observations':[],'decisions':[{'id':'d','opportunity_id':'test-one','marketplace':'etsy','status':'ACCEPTED','date':ASOF,'reason':'Synthetic owner selection'}]}
        m.track(self.root,self.write(d,'decision.json'))
        dest=self.root/'export.json';m.export(self.root,dest)
        other=self.root/'other';m.import_bundle(other,dest)
        self.assertEqual(m.load(other),m.load(self.root))

    def test_revise_preserves_prior_proposal_and_requires_reason(self):
        b=m.template('etsy');self.ingest(b)
        changed=copy.deepcopy(b);changed['opportunities'][0]['proposals']['etsy']['rationale']='New research'
        path=self.write(changed,'revision.json')
        with self.assertRaises(ValidationError):m.revise(self.root,path,'',ASOF)
        m.revise(self.root,path,'Owner changed research scope',ASOF)
        s=m.load(self.root);self.assertEqual(len(s['revisions']),1)
        self.assertEqual(s['revisions'][0]['previous'],b['opportunities'][0])

    def test_revision_does_not_change_historical_report(self):
        b=m.template('etsy');self.ingest(b)
        changed=copy.deepcopy(b);changed['opportunities'][0]['topic']='Revised topic'
        m.revise(self.root,self.write(changed,'revision.json'),'New scope','2026-10-09')
        self.assertEqual(self.row()['opportunity']['topic'],b['opportunities'][0]['topic'])
        self.assertEqual(m.report(self.root,'2026-10-09')['opportunities'][0]['opportunity']['topic'],'Revised topic')

    def test_all_market_decision_cannot_bypass_rejection(self):
        self.ingest(packet())
        state=m.load(self.root)
        decision={'id':'d1','opportunity_id':'test-one','marketplace':'etsy','status':'REJECTED','date':ASOF,'reason':'Synthetic rejection'}
        m.apply_decisions(state,[decision])
        decision.update(id='d2',marketplace='ALL',status='APPROVED')
        with self.assertRaises(ValidationError):m.apply_decisions(state,[decision])

    def test_official_observation_cannot_invent_independent_origin(self):
        b=packet();b['observations'][0]['upstream_url']='https://example.org/unrelated'
        with self.assertRaises(ValidationError):self.ingest(b)

    def test_unresearched_catalog_adaptation_can_receive_research_only(self):
        legacy=empty_state();legacy['products']=[{'id':'old-book','title':'Old book'}]
        _write_json(self.root/'book-radar/state.json',legacy)
        b=m.import_template(self.root,'udemy',ASOF,catalog_id='old-book');self.ingest(b)
        self.assertIsNone(self.row()['research_date'])
        actions=m.weekly(self.root,ASOF,0)['actions']
        self.assertEqual(len(actions),1)
        self.assertEqual(actions[0]['kind'],'RESEARCH')
        self.assertEqual(actions[0]['marketplace'],'udemy')

    def test_duplicate_topic_clusters_do_not_merge_different_buyers(self):
        b=m.template('etsy');o=copy.deepcopy(b['opportunities'][0]);o['id']='two';b['opportunities'].append(o)
        with self.assertRaises(ValidationError):self.ingest(b)
        o['audience']='Different buyer';self.ingest(b)
        self.assertEqual(len(m.load(self.root)['opportunities']),2)

    def test_catalog_adaptation_uses_own_market_evidence_and_performance_readonly(self):
        legacy=empty_state();legacy['opportunities']=[{'id':'old'}];legacy['products']=[{'id':'old-book','opportunity_id':'old','title':'Old book','status':'LIVE'}];legacy['actuals']=[{'id':'a','product_id':'old-book','units':2}]
        _write_json(self.root/'book-radar/state.json',legacy);before=(self.root/'book-radar/state.json').read_bytes()
        b=packet();o=b['opportunities'][0];o['catalog_ref']={'collection':'products','id':'old-book'};o['proposals']['etsy']['reuse_mode']='ADAPTED';self.ingest(b)
        row=self.row();self.assertEqual(row['first_market'],'etsy');self.assertEqual(row['catalog_context']['performance'][0]['units'],2)
        self.assertEqual(len(m.weekly(self.root,ASOF,0)['actions']),1)
        self.assertEqual((self.root/'book-radar/state.json').read_bytes(),before)

    def test_cli_and_existing_reports_remain_available_without_state_mutation(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(main(['book-radar','markets','template','etsy','--as-of',ASOF],self.root),0)
            self.assertEqual(main(['book-radar','report','markets','--json','--as-of',ASOF],self.root),0)
            self.assertEqual(main(['book-radar','report','weekly','--amazon-committed','0'],self.root),0)
        self.assertEqual(amazon_report(self.root,'pipeline')['product_statuses'],{})
        self.assertFalse((self.root/'book-radar/state.json').exists())
        self.assertFalse(m.state_path(self.root).exists())

    def test_malformed_dates_nonfinite_metrics_and_bad_types_fail_closed(self):
        for bad in ['date','infinite','type']:
            b=packet()
            if bad=='date':b['observations'][0]['period_end']='2026-02-30'
            elif bad=='infinite':b['observations'][0]['metrics']['paid_orders']['value']=float('inf')
            else:b['observations'][0]['metrics']['paid_orders']['value']='many'
            with self.assertRaises(ValidationError):self.ingest(b,bad+'.json')
