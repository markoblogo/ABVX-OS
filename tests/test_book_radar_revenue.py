import copy
import unittest
from abvx_harness import book_radar_revenue as r
from abvx_harness.harness import ValidationError


def card():
    return {'id':'external:test','lane':'E','buying_object':'Cutout paperback',
            'purchase_proposition':'Large accessible cutting shapes','entry_route':'Specific accessible crafting use',
            'observations':[{'product_id':'external:a','url':'https://example.org/a','kind':'PAID_ACTIVITY','observed_at':'2026-10-07'},
                            {'product_id':'external:b','url':'https://example.org/b','kind':'PAID_ACTIVITY','observed_at':'2026-10-07'}]}


class RevenueBoundaryTests(unittest.TestCase):
    def test_lane_e_without_portfolio(self):
        c=card(); q=r.freeze_qualification(c,'QUALIFY')
        self.assertEqual(q['result'],'QUALIFY'); self.assertEqual(c,card())

    def test_portfolio_blocked_even_nested(self):
        for change in ({'portfolio_paid_units':12},{'observations':[{**card()['observations'][0],'abvx_sales':9}]}):
            with self.assertRaises(ValidationError): r.freeze_qualification({**card(),**change},'QUALIFY')

    def test_lane_e_requires_repeated_external_object(self):
        c=card(); c['observations']=c['observations'][:1]
        with self.assertRaises(ValidationError): r.freeze_qualification(c,'QUALIFY')

    def test_overlay_after_qualification_and_freeze(self):
        c=card();q=r.freeze_qualification(c,'QUALIFY'); original=copy.deepcopy(q)
        self.assertEqual(r.post_qualification(q,c,{'launch_class':'EXPLORE','commercial_line_id':'TEST'})['launch_class'],'EXPLORE')
        self.assertEqual(q,original)
        for klass in ('EXPLOIT','EXPLORE'):
            with self.assertRaises(ValidationError):r.post_qualification(r.freeze_qualification(c,'PARK'),c,{'launch_class':klass})
        c['entry_route']='Changed'
        with self.assertRaises(ValidationError):r.post_qualification(q,c,{'launch_class':'EXPLOIT'})


class SlotAndExposureTests(unittest.TestCase):
    def event(self, action='FIRST_SUBMISSION', fmt='paperback', title='title:a', when='2026-10-04T01:00:00Z'):
        return {'id':action+fmt+title+when,'action':action,'format':fmt,'title_id':title,'at':when,'commercial_line_id':'TEST'}

    def test_sunday_utc_and_format_separation(self):
        self.assertEqual(r.slot_week('2026-10-04T01:00:00+02:00'),'2026-09-27')
        self.assertEqual(r.slot_week('2026-10-04T00:00:00Z'),'2026-10-04')
        events=[self.event(),self.event(title='title:b'),self.event(fmt='ebook'),self.event(action='CREATION')]
        use=r.slot_usage(events,'2026-10-04','paperback',complete=True)
        self.assertEqual(use,{'CREATION':1,'FIRST_SUBMISSION':2})
        self.assertEqual(r.slot_usage(events,'2026-10-04','ebook',complete=True)['FIRST_SUBMISSION'],1)
        self.assertEqual(r.slot_usage(events,'2026-10-11','paperback',complete=True)['FIRST_SUBMISSION'],0)

    def test_updates_require_prior_submission_and_consume_no_new_slot(self):
        events=[self.event(when='2026-09-27T01:00:00Z'),self.event(action='UPDATE')]
        self.assertEqual(r.slot_usage(events,'2026-10-04','paperback',complete=True)['FIRST_SUBMISSION'],0)
        with self.assertRaises(ValidationError):r.slot_usage(events[1:],'2026-10-04','paperback',complete=True)

    def test_unreconciled_usage_is_unknown(self):
        self.assertEqual(r.slot_usage([],'2026-10-04','paperback')['FIRST_SUBMISSION'],r.U)

    def test_one_slot_no_blocks_and_artificial_ebook_blocks(self):
        p={'format':'paperback','launch_class':'EXPLORE','only_one_slot':'NO','ready':True,'qualification_verified':True,'requires_paper':True}
        self.assertEqual(r.slot_gate(p,{'CREATION':0,'FIRST_SUBMISSION':0})['KDP_SLOT_STATUS'],'BLOCKED')
        p.update(format='ebook',only_one_slot='YES')
        self.assertEqual(r.slot_gate(p,{'CREATION':0,'FIRST_SUBMISSION':0})['KDP_SLOT_STATUS'],'BLOCKED')

    def test_organic_unknown_never_means_zero_demand(self):
        e=r.exposure_review(7,0,r.U,r.U,r.U)
        self.assertEqual(e['demand'],r.U)
        self.assertEqual(e['recommendation'],'BOUNDED_PAID_EXPOSURE_TEST_FOR_OWNER_APPROVAL')
        self.assertEqual(r.exposure_review(6,0,r.U,r.U,r.U)['recommendation'],'ORGANIC_BASELINE')
        self.assertEqual(r.exposure_review(7,r.U,r.U,r.U,r.U)['recommendation'],'COLLECT_PAID_ORDER_EVIDENCE')

    def test_funnel_stages_remain_distinct(self):
        for args, stage in [((8,0,0,0,r.U),'NO_IMPRESSIONS'),((8,0,10,0,r.U),'NO_CLICKS'),
                            ((8,0,10,2,r.U),'CLICKS_NO_ORDERS'),((8,1,10,2,r.U),'PAID_ORDERS')]:
            self.assertEqual(r.exposure_review(*args)['stage'],stage)
        self.assertEqual(r.exposure_review(8,1,r.U,r.U,r.U)['recommendation'],'LINE_EXPLOIT_REVIEW_BEFORE_BROAD_DISCOVERY')


def actual(bid, paid, royalty, start='2026-09-08', end='2026-10-07'):
    return {'id':'actual:'+bid,'book_id':bid,'schema_version':'book-radar-observed-actual/v1','observed_date':end,
            'windows':{'recent':{'start':start,'end':end,'paid_units':paid},
                       'recent_money':{'start':start,'end':end,'estimated_royalties':royalty,'currency':'EUR'},
                       'lifetime':{'start':'2026-01-01','end':end,'paid_units':paid},
                       'money':{'start':'2026-01-01','end':end,'estimated_royalties':royalty,'currency':'EUR'},
                       'kenp':{'start':start,'end':end,'kenp_pages':4}}}


class DerivedOutcomeTests(unittest.TestCase):
    def fixture(self):
        return {'observed_books':[{'id':'a'},{'id':'b'}],'actuals':[actual('a',2,3),actual('b',1,2)],'series_observations':[]}

    def test_derived_from_canonical_without_mutation(self):
        s=self.fixture();before=copy.deepcopy(s)
        view=r.line_view(s,{'id':'TEST','book_ids':['a','b'],'live_basis':'OWNER_CONFIRMED_LIVE'},'2026-10-07',[],False)
        self.assertEqual(view['LINE_30D_PAID_UNITS'],3);self.assertEqual(view['LINE_30D_ROYALTY'],5)
        self.assertEqual(view['ROYALTY_PER_LIVE_TITLE'],2.5);self.assertEqual(view['NEW_TITLE_SLOT_COUNT'],r.U)
        self.assertEqual(s,before)

    def test_missing_member_and_wrong_window_not_zero_filled(self):
        s=self.fixture();s['actuals'][0]=actual('a',9,10,'2026-07-05')
        v=r.line_view(s,{'id':'TEST','book_ids':['a','b'],'live_basis':'OWNER_CONFIRMED_LIVE'},'2026-10-07',[],False)
        self.assertEqual(v['LINE_30D_ROYALTY'],r.U)
        s['actuals']=s['actuals'][:1]
        self.assertEqual(r.line_view(s,{'id':'TEST','book_ids':['a','b']},'2026-10-07',[],False)['LINE_LIFETIME_PAID_UNITS'],r.U)

    def test_currency_and_snapshot_dates_cannot_be_mixed(self):
        s=self.fixture();s['actuals'][1]['windows']['money']['currency']='USD'
        self.assertEqual(r.line_view(s,{'id':'TEST','book_ids':['a','b']},'2026-10-07',[],False)['LINE_LIFETIME_ROYALTY'],r.U)
        s=self.fixture();s['actuals'][1]['windows']['lifetime']['end']='2026-10-06'
        self.assertEqual(r.line_view(s,{'id':'TEST','book_ids':['a','b']},'2026-10-07',[],False)['LINE_LIFETIME_PAID_UNITS'],r.U)

    def test_no_order_ratio_as_readthrough(self):
        s=self.fixture();s['series_observations']=[{'entry_book_id':'a','continuation_book_id':'b','entrants':10,'continuers':2,'cohort_basis':r.U,'method':'AGGREGATE_CATALOG_ONLY'}]
        self.assertEqual(r.readthrough(s,'a','b','2026-10-07'),r.U)

    def test_corrected_good_dogs_not_in_queue(self):
        from pathlib import Path
        m=r.load_model(Path(__file__).resolve().parents[1])
        self.assertEqual([x['title_id'] for x in m['release_queue']],['C01_FIRST_LOGIC_GRIDS','CARMILLA_TOKI_PONA'])
        dogs=next(x for x in m['lines'] if x['id']=='GOOD_DOGS_OF_THE_APOCALYPSE')
        self.assertEqual(len(dogs['book_ids']),3);self.assertEqual(dogs['extension_status'],'HOLD')

    def test_direct_matched_cohort_uses_existing_canonical_contract(self):
        s=self.fixture();s['series_observations']=[{'entry_book_id':'a','continuation_book_id':'b','entrants':10,'continuers':2,'cohort_basis':'MATCHED_READER_COHORT','method':'DIRECT_MATCHED_COHORT','evidence':['source'],'identity_evidence':['identity'],'observed_date':'2026-10-07'}]
        self.assertEqual(r.readthrough(s,'a','b','2026-10-07'),0.2)

    def test_full_report_preserves_every_protected_file(self):
        from pathlib import Path
        from hashlib import sha256
        import json, tempfile
        from abvx_harness.book_radar import empty_state, save_state
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=Path(__file__).resolve().parents[1]
            (root/'schemas').mkdir()
            (root/'schemas/book_radar_revenue_model.schema.json').write_bytes((source/'schemas/book_radar_revenue_model.schema.json').read_bytes())
            model=r.load_model(source)
            model['lines']=[{**model['lines'][0], 'id':'SYNTHETIC_TEST', 'book_ids':['book:test']}]
            for key in ('release_queue','external_qualifications','post_qualification_overlays','slot_events','slot_reconciliations'):
                model[key]=[]
            from test_book_radar_outcomes import fixture
            book,observed,_=fixture(root)
            state=empty_state();state['products']=[{'id':book['product_id']}];state['observed_books']=[book];state['actuals']=[observed];save_state(root,state)
            (root/'book-radar/revenue-model-v2.json').write_text(json.dumps(model))
            sentinel=root/'book-radar/scoring-models/protected.json';sentinel.parent.mkdir();sentinel.write_text('SYNTHETIC protected sentinel')
            files=[root/'book-radar/state.json',sentinel]
            before={str(p):sha256(p.read_bytes()).hexdigest() for p in files}
            report=r.revenue_report(root,'2026-10-07')
            self.assertFalse(report['submission_authorized']);self.assertEqual(report['ROLLING_30D_ROYALTY'],r.U)
            self.assertEqual(before,{str(p):sha256(p.read_bytes()).hexdigest() for p in files})

    def test_reconciled_gate_still_requires_owner_review(self):
        p={'format':'paperback','launch_class':'EXPLOIT','only_one_slot':'YES','ready':True,'qualification_verified':True,'prior_paid_evidence':['known-paid'],'requires_paper':False}
        self.assertEqual(r.slot_gate(p,{'CREATION':0,'FIRST_SUBMISSION':1})['KDP_SLOT_STATUS'],'ELIGIBLE_FOR_OWNER_REVIEW')
        self.assertFalse(r.slot_gate(p,{'CREATION':0,'FIRST_SUBMISSION':1})['submission_authorized'])
        self.assertEqual(r.slot_gate(p,{'CREATION':2,'FIRST_SUBMISSION':0})['KDP_SLOT_STATUS'],'BLOCKED')
        p['already_created']=True
        self.assertEqual(r.slot_gate(p,{'CREATION':2,'FIRST_SUBMISSION':0})['KDP_SLOT_STATUS'],'ELIGIBLE_FOR_OWNER_REVIEW')
