"""Synthetic inventory fixtures: no manuscripts, market research or publication."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

class ReadinessTests(unittest.TestCase):
    def test_canonical_and_body_duplicates_do_not_inflate_a_book(self):
        from abvx_harness.book_readiness import refresh
        with TemporaryDirectory() as t:
            root,site=Path(t)/'os',Path(t)/'site'; self.fixture(root,site)
            self.article(site,'one',' '.join(['unique manuscript prose']*90),recipe=True)
            self.article(site,'copy',' '.join(['unique manuscript prose']*90),recipe=True)
            first=refresh(root,site,as_of='2026-10-25')
            c=first['candidates']['kitchen-recipes']
            self.assertEqual(c['entries'],1)
            self.assertEqual(len(c['duplicate_articles']),1)
            self.assertEqual(first['scan']['analyzed'],2)
            self.assertEqual(refresh(root,site,as_of='2026-10-25')['scan']['analyzed'],0)
            self.assertGreater(c['unique_english_words'],0)
            self.assertEqual(c['rights_cleared_words'],0)

    def test_failure_preserves_inventory_and_publication_hook_does_not_raise(self):
        from abvx_harness.book_readiness import refresh,after_publication
        with TemporaryDirectory() as t:
            root,site=Path(t)/'os',Path(t)/'site'; self.fixture(root,site)
            p=self.article(site,'one','A complete short source body.')
            refresh(root,site,as_of='2026-10-25')
            state=root/'.tmp/book-readiness/state.json';before=state.read_bytes()
            p.write_text('broken frontmatter')
            with self.assertRaises(ValueError):refresh(root,site,as_of='2026-10-25')
            self.assertEqual(state.read_bytes(),before)
            self.assertEqual(after_publication(root,site)['status'],'FAILED')
            self.assertEqual(state.read_bytes(),before)

    def test_psychology_rights_are_unknown_until_owner_receipt_and_existing_book_is_not_new(self):
        from abvx_harness.book_readiness import refresh
        with TemporaryDirectory() as t:
            root,site=Path(t)/'os',Path(t)/'site'; self.fixture(root,site)
            p=self.article(site,'psychology-notebook-01','Rights confirmed personal fragments.',tag='psychology-notebook')
            private=site/'exports/psychology-notebook';private.mkdir(parents=True)
            (private/'registry.json').write_text(json.dumps({'sourceSha256':'a'*64}))
            one=refresh(root,site,as_of='2026-10-25');a=next(iter(one['articles'].values()))
            self.assertEqual(a['rights'],'UNKNOWN')
            (root/'.tmp/book-readiness/owner-claims.json').write_text(json.dumps({'psychology_archive_sha256':'a'*64,'existing_book_url':'https://abvx.xyz/books/fragments-from-a-therapists-notebook'}))
            two=refresh(root,site,as_of='2026-10-25');a=next(iter(two['articles'].values()))
            self.assertEqual(a['rights'],'OWNER_CONFIRMED')
            c=two['candidates']['psychology-notebook']
            self.assertGreater(c['rights_cleared_words'],0)
            self.assertIsNone(c['new_book_words'])
            self.assertFalse(c['market_assessment_eligible'])
            self.assertTrue(c['existing_books'])

    def test_draft_canonical_source_is_not_counted_as_published_and_source_separators_are_preserved(self):
        from abvx_harness.book_readiness import refresh
        with TemporaryDirectory() as t:
            root,site=Path(t)/'os',Path(t)/'site'; self.fixture(root,site)
            self.article(site,'one','One paragraph.\n\n---\n\nAnother paragraph.\n\n```python\nignored code words\n```')
            (site/'public/content-index.json').write_text(json.dumps({'items':[]}))
            s=refresh(root,site,as_of='2026-10-25')
            a=next(iter(s['articles'].values()))
            self.assertEqual(a['english_word_count'],4)
            self.assertEqual(a['status'],'draft')
            self.assertEqual(s['candidates']['kitchen-stories']['entries'],0)

    def test_stage_notifications_are_delivered_once_and_stale_editorial_assessments_do_not_promote(self):
        from abvx_harness.book_readiness import refresh,acknowledge,assess,research_queue
        with TemporaryDirectory() as t:
            root,site=Path(t)/'os',Path(t)/'site'; self.fixture(root,site)
            cpath=root/'book-radar/readiness-policy.json';config=json.loads(cpath.read_text())
            for c in config['candidates']:
                c['outline']={'entries':1,'words':1,'themes':1};c['manuscript']={'entries':1,'words':1,'themes':1,'visual_coverage':0};c['target_pages']=[1,200]
            cpath.write_text(json.dumps(config));p=self.article(site,'one',' '.join(['Substantial unique prose from one source.']*30),recipe=True)
            a=refresh(root,site,as_of='2026-10-25',review=True);count=len(a['milestones'])
            self.assertEqual(a['candidates']['kitchen-recipes']['stage'],'outline_ready')
            acknowledge(root,'all');b=refresh(root,site,as_of='2026-10-26',review=True,if_due=True)
            self.assertEqual(b['last_editorial_review'],'2026-10-25')
            self.assertEqual(len(b['milestones']),count)
            self.assertTrue(all(e['delivered_at'] for e in b['milestones']))
            assess(root,'kitchen-recipes',{'member_digest':b['candidates']['kitchen-recipes']['member_digest'],'cohesion':'confirmed','gaps_resolved':True,'evidence':'synthetic human editorial review'})
            held=refresh(root,site,as_of='2026-10-26')
            self.assertEqual(held['candidates']['kitchen-recipes']['stage'],'outline_ready')
            config['article_annotations']={'one':{'source_hash':held['articles']['https://abvx.xyz/writing/one']['source_hash'],'rights':'cleared','evidence':'synthetic owner republication receipt'}}
            cpath.write_text(json.dumps(config))
            c=refresh(root,site,as_of='2026-10-26')
            self.assertEqual(c['candidates']['kitchen-recipes']['stage'],'manuscript_candidate')
            ready = {x['candidate_id']: x for x in research_queue(root)}
            self.assertEqual(ready['kitchen-recipes']['editorial_stage'], 'manuscript_candidate')
            self.assertFalse(ready['kitchen-recipes']['production_authorized'])
            p.write_text(p.read_text()+' An actual source change.')
            d=refresh(root,site,as_of='2026-10-26')
            self.assertEqual(d['candidates']['kitchen-recipes']['stage'],'outline_ready')
            changed = {x['candidate_id']: x for x in research_queue(root)}
            self.assertEqual(changed['kitchen-recipes']['editorial_stage'], 'outline_ready')
            self.assertNotEqual(ready['kitchen-recipes']['material_review_digest'], changed['kitchen-recipes']['material_review_digest'])
            self.assertFalse(changed['kitchen-recipes']['production_authorized'])

    @staticmethod
    def fixture(root,site):
        root.mkdir(parents=True);(root/'book-radar').mkdir();(site/'content/writing').mkdir(parents=True);(site/'public').mkdir()
        config=Path(__file__).parents[1]/'book-radar/readiness-policy.json'
        (root/'book-radar/readiness-policy.json').write_text(config.read_text())
        (site/'public/content-index.json').write_text(json.dumps({'items':[]}))

    @staticmethod
    def article(site,slug,body,recipe=False,tag=None):
        d={'id':slug,'slug':slug,'title':slug,'language':'en','type':'recipe' if recipe else 'article','collection':'kitchen-notes','visibility':'public','status':'live','tags':[tag or 'cooking'],'publishedAt':'2026-10-25'}
        if recipe:d['recipe']={'ingredients':[],'instructions':[]}
        p=site/'content/writing'/f'{slug}.md';p.write_text('---\n'+json.dumps(d)+'\n---\n\n'+body)
        idx=site/'public/content-index.json';data=json.loads(idx.read_text());data['items'].append({'canonicalUrl':'https://abvx.xyz/writing/'+slug});idx.write_text(json.dumps(data))
        return p

if __name__=='__main__':unittest.main()
