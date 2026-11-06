import copy,unittest
from abvx_harness import book_radar_wide as w
from abvx_harness.harness import ValidationError

class CommercialPipelineTests(unittest.TestCase):
 def menu(self):
  source={'url':'https://publisher.example/book','observed_date':'2026-11-02'}
  checks={s:{'status':'PASS','reason':'SYNTHETIC evidence only','sources':[source]} for s in w.COMMERCIAL_STAGES}
  checks['competition']['books']=[{'identity':i,'basis':'TOC','source_url':source['url']} for i in ['isbn1','isbn2']]
  checks['differentiation'].update(competitor_already_offers_claim=False,advantage='SYNTHETIC compared difference')
  return {'as_of':'2026-11-02','cards':[{'id':'a','production_authorized':False}], 'commercial_reviews':{'a':checks}}
 def test_missing_legacy_review_cannot_recommend(self):
  m=self.menu();m.pop('commercial_reviews');r=w.commercial_review_pipeline(m)
  self.assertEqual(r['next_checks'][0]['next_stage'],'demand')
 def test_passes_are_research_decisions_not_authorization(self):
  r=w.commercial_review_pipeline(self.menu());self.assertEqual(r['outcomes'][0]['disposition'],'READY_FOR_OWNER_DECISION');self.assertFalse(r['production_authorized'])
 def test_overlap_blocks_unchanged_claim(self):
  m=self.menu();m['commercial_reviews']['a']['differentiation']['competitor_already_offers_claim']=True
  self.assertEqual(w.commercial_review_pipeline(m)['next_checks'][0]['next_stage'],'differentiation')
 def test_validated_revision_can_reach_owner_review(self):
  m=self.menu();m['commercial_reviews']['a']['differentiation'].update(competitor_already_offers_claim=True,revised_advantage_validated=True)
  self.assertEqual(w.commercial_review_pipeline(m)['outcomes'][0]['disposition'],'READY_FOR_OWNER_DECISION')
 def test_failure_advances_to_other_candidate(self):
  m=self.menu();m['commercial_reviews']['a']['demand']['status']='FAIL';m['research_queue']=[{'id':'b','production_authorized':False}]
  r=w.commercial_review_pipeline(m);self.assertEqual(r['outcomes'][0]['disposition'],'REJECTED_ADVANCE_QUEUE');self.assertEqual(r['next_checks'][0]['id'],'b')
 def test_missing_content_and_duplicate_books_fail_closed(self):
  for books in [[],[{'identity':'a','basis':'TOC','source_url':'https://publisher.example/book'}]*2]:
   m=self.menu();m['commercial_reviews']['a']['competition']['books']=books
   with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)
 def test_future_unbound_and_missing_evidence_rejected(self):
  for mutation in ['future','unbound','empty']:
   m=self.menu()
   if mutation=='future':m['commercial_reviews']['a']['demand']['sources'][0]['observed_date']='2026-11-09'
   elif mutation=='unbound':m['commercial_reviews']['a']['competition']['books'][0]['source_url']='https://unbound.example'
   else:m['commercial_reviews']['a']['demand']['sources']=[]
   with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)
 def test_queue_bound_duplicates_unknown_ids_and_authorization_rejected(self):
  for mutation in ['long','duplicate','unknown','authorized']:
   m=self.menu()
   if mutation=='long':m['research_queue']=[{'id':str(i),'production_authorized':False} for i in range(25)]
   elif mutation=='duplicate':m['research_queue']=[{'id':'a','production_authorized':False}]
   elif mutation=='unknown':m['commercial_reviews']['ghost']={}
   else:m['research_queue']=[{'id':'b','production_authorized':True}]
   with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)

 def test_exhausted_budget_does_not_request_unbounded_work(self):
  m=self.menu();m.pop('commercial_reviews');m['research_budget']={'max_checks':16,'used_checks':16}
  self.assertEqual(w.commercial_review_pipeline(m)['action'],'RESEARCH_BUDGET_EXHAUSTED')
  for budget in [{'max_checks':True,'used_checks':0},{'max_checks':2,'used_checks':3}]:
   m['research_budget']=budget
   with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)

 def test_known_later_failure_rejects_without_filling_unknown_demand(self):
  m=self.menu();del m['commercial_reviews']['a']['demand'];m['commercial_reviews']['a']['differentiation']['status']='FAIL'
  self.assertEqual(w.commercial_review_pipeline(m)['outcomes'][0]['disposition'],'REJECTED_ADVANCE_QUEUE')


 def basis(self,kind='REPEAT_ENTERTAINMENT'):
  b={'kind':kind,'reader':'SYNTHETIC adult reader','reason_to_buy':'New original cases in an established format','original_content_plan':'Own cast and cases; copy no competitor text','genre_fit':'Clue-based deduction, same reading context','repeat_purchase_evidence':'Two distinct published volumes, not two formats','discovery_route':'Observed relevant search shelf','quality_plan':'Independent solution verification and language editing','rights_plan':'Original expression only; no borrowed characters or branding','uniqueness_claim_removed':True,'evidence_urls':['https://publisher.example/book']}
  if kind=='PRACTICAL_FIT':b.update(reader_outcome='Complete a first repair',audience_fit='Absolute novice with standard materials',delivery_plan='Tested instructions before release')
  return b
 def test_repeat_entertainment_does_not_need_a_new_mechanic(self):
  m=self.menu();c=m['commercial_reviews']['a']['differentiation'];c.update(competitor_already_offers_claim=True,purchase_basis=self.basis())
  self.assertEqual(w.commercial_review_pipeline(m)['outcomes'][0]['disposition'],'READY_FOR_OWNER_DECISION')
 def test_practical_fit_can_coexist_with_similar_guides(self):
  m=self.menu();m['commercial_reviews']['a']['differentiation'].update(competitor_already_offers_claim=True,purchase_basis=self.basis('PRACTICAL_FIT'))
  self.assertEqual(w.commercial_review_pipeline(m)['outcomes'][0]['disposition'],'READY_FOR_OWNER_DECISION')
 def test_purchase_flag_without_reason_and_evidence_is_not_enough(self):
  for key in ['repeat_purchase_evidence','original_content_plan','rights_plan','evidence_urls']:
   m=self.menu();b=self.basis();del b[key];m['commercial_reviews']['a']['differentiation']['purchase_basis']=b
   with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)
 def test_overlap_must_remove_false_uniqueness_claim(self):
  m=self.menu();b=self.basis();b['uniqueness_claim_removed']=False;m['commercial_reviews']['a']['differentiation'].update(competitor_already_offers_claim=True,purchase_basis=b)
  with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)
 def test_rights_or_impossible_promise_still_blocks(self):
  m=self.menu();m['commercial_reviews']['a']['differentiation']['purchase_basis']=self.basis();m['commercial_reviews']['a']['feasibility']['hard_blockers']=['SYNTHETIC unresolved copyright']
  self.assertEqual(w.commercial_review_pipeline(m)['outcomes'][0]['disposition'],'REJECTED_ADVANCE_QUEUE')
 def test_v2_requires_explained_basis_and_five_factors(self):
  m=self.menu();m['selection_method']='purchase-reason-by-product-type/v2'
  with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)
  m['commercial_reviews']['a']['differentiation']['purchase_basis']=self.basis()
  with self.assertRaises(ValidationError):w.commercial_review_pipeline(m)
  m['commercial_reviews']['a']['compare']['factors']={k:{'argument':'SYNTHETIC explained factor','evidence_urls':['https://publisher.example/book']} for k in ['buyer_signal','market_access','purchase_reason','buyer_route','capability_fit']}
  self.assertEqual(w.commercial_review_pipeline(m)['outcomes'][0]['disposition'],'READY_FOR_OWNER_DECISION')

 def test_valid_selection_can_be_presented_with_reserves_still_pending(self):
  m=self.menu();m['top_owner_review']=['a'];m['research_queue']=[{'id':'reserve','production_authorized':False}]
  self.assertEqual(w.commercial_review_pipeline(m)['action'],'PRESENT_OWNER_DECISIONS')
 def test_unreviewed_top_id_does_not_stop_research(self):
  m=self.menu();m.pop('commercial_reviews');m['top_owner_review']=['a']
  self.assertEqual(w.commercial_review_pipeline(m)['action'],'CONTINUE_RESEARCH_WITHIN_BUDGET')
