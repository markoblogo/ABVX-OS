from datetime import datetime, timezone
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness.psychology_editorial import build_crosswalk, reconcile_series, classify_fragment
from abvx_harness.psychology_warehouse import ingest, query
from abvx_harness.harness import ValidationError


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


class PsychologyEditorialTests(unittest.TestCase):
    def test_boundary_parts_keep_both_ids_and_exact_ranges(self):
        notes=[{'note_id':'PHY-one','original_text':'Первый текст\n*** Второй текст\n','current':True}]
        fragments=[{'id':'pn-a','source':'Первый текст'},{'id':'pn-b','source':'Второй текст'}]
        links=build_crosswalk(fragments,notes)
        self.assertEqual(set(links),{'pn-a','pn-b'})
        for f in fragments:
            link=links[f['id']][0]
            self.assertEqual(link['noteId'],'PHY-one')
            self.assertEqual(notes[0]['original_text'][link['start']:link['end']],f['source'])
            self.assertEqual(link['relation'],'EXACT_DELIMITED_PART')

    def test_short_substring_is_not_a_crosswalk_match(self):
        with self.assertRaises(ValidationError):
            build_crosswalk([{'id':'pn-a','source':'текст'}],[{'note_id':'PHY-one','original_text':'Другой текст целиком','current':True}])

    def test_duplicate_occurrences_all_link_to_one_unique_fragment(self):
        links=build_crosswalk([{'id':'pn-a','source':'Первый текст'}],[{'note_id':x,'original_text':'Первый текст\n','current':True} for x in ['PHY-a','PHY-b']])
        self.assertEqual({x['noteId'] for x in links['pn-a']},{'PHY-a','PHY-b'})

    def test_self_pronoun_alone_does_not_dominate_theme(self):
        row=classify_fragment({'source':'Терапия травмы: клиент боится повторения травмы и думает о себе.','reviewFlags':[]})
        self.assertEqual(row['primaryTopic'],'TRAUMA')
        self.assertNotIn('SELF_AND_IDENTITY',row['topics'])

    def test_unflagged_diagnostic_claim_is_sent_for_review(self):
        row=classify_fragment({'source':'Пограничники всегда создают драму.','reviewFlags':[]})
        self.assertIn('DIAGNOSTIC_LANGUAGE',row['reviewReasons'])

    def test_verified_usage_is_idempotent_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);series=root/'series';series.mkdir()
            source=root/'Phy-notes.txt';source.write_text('Заметка про тревогу и страх.\n***\n')
            book=root/'books/projects/fragments-therapists-notebook.json';book.parent.mkdir(parents=True);book.write_text(json.dumps({'id':'fragments-therapists-notebook','title':'Book','canonical_manuscript':{'locator':None}}))
            ingest(root,source)
            f={'id':'pn-one','source':'Заметка про тревогу и страх.','sourceSha256':sha('Заметка про тревогу и страх.'),'reviewFlags':[],'translation':'A note about anxiety and fear.','publishedUrl':'https://abvx.xyz/writing/psychology-notebook-01-test','publishedAt':'2026-10-21T12:00:00Z','deploymentSha':'a'*40}
            registry={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceFile':'source.txt','fragments':[f],'occurrences':[{'fragmentId':'pn-one'}]};(series/'source.txt').write_bytes(source.read_bytes());(series/'registry.json').write_text(json.dumps(registry))
            item={'id':'psychology-notebook-01-test','fragmentIds':['pn-one'],'status':'PUBLISHED_VERIFIED','editorialApproved':True,'sourceReviewApproved':True,'artworkApproved':True,'publishedAt':f['publishedAt'],'verifiedAt':'2026-10-21T12:01:00Z','deploymentSha':'a'*40,'publishedUrl':f['publishedUrl'],'releaseSourceFile':'post.md','publicationReceipt':'receipt.json','draftFile':'draft.md'}
            md='---\n'+json.dumps({'id':item['id'],'slug':item['id']})+'\n---\n\n'+f['translation']+'\n';(series/'post.md').write_text(md);(series/'draft.md').write_text(md);item['sourceSha256']=sha(md);item['releaseSourceSha256']=sha(md);(series/'queue.json').write_text(json.dumps({'enabled':False,'items':[item]}));(series/'plan.json').write_text('[]');(series/'near-duplicates.json').write_text('[]');(series/'receipt.json').write_text(json.dumps({'checks':'PASS','production':'PASS','reviewInspected':True,'merge':'a'*40,'closeout':{'status':'RECORDED'}}))
            original=source.read_bytes();warehouse=(root/'psychology-warehouse/state/warehouse.json').read_bytes();queue=(series/'queue.json').read_bytes()
            dry=reconcile_series(root,series,write=False);self.assertEqual(dry['verifiedPublishedFragments'],1);self.assertEqual(query(root,'used','psychology-notebook')['count'],0)
            usage_file=root/'psychology-warehouse/usage/ledger.json'
            ledger=json.loads(usage_file.read_text());other={'note_id':json.loads(warehouse)['notes'][0]['note_id'],'project_id':'unrelated-book','relation':'EXACT_MATCH'};ledger['usages'].append(other);usage_file.write_text(json.dumps(ledger))
            observed_before=datetime.now(timezone.utc)
            reconcile_series(root,series,write=True)
            recorded=next(u for u in json.loads(usage_file.read_text())['usages'] if u.get('project_id')=='psychology-notebook')['recorded_at']
            self.assertTrue(observed_before<=datetime.fromisoformat(recorded)<=datetime.now(timezone.utc))
            self.assertIn(other,json.loads(usage_file.read_text())['usages'])
            self.assertEqual(query(root,'used','psychology-notebook')['count'],1);self.assertEqual(query(root,'unused')['count'],0)
            usage=root/'psychology-warehouse/usage/ledger.json';first=usage.read_bytes();reconcile_series(root,series,write=True);self.assertEqual(usage.read_bytes(),first)
            self.assertEqual(source.read_bytes(),original);self.assertEqual((series/'queue.json').read_bytes(),queue)
            self.assertEqual([n['original_text'] for n in json.loads(warehouse)['notes']],[n['original_text'] for n in json.loads((root/'psychology-warehouse/state/warehouse.json').read_text())['notes']])
            receipt=json.loads((series/'receipt.json').read_text());receipt['merge']='b'*40;(series/'receipt.json').write_text(json.dumps(receipt))
            with self.assertRaises(ValidationError):reconcile_series(root,series,write=True)
            self.assertEqual(usage.read_bytes(),first)
            receipt['merge']='a'*40;(series/'receipt.json').write_text(json.dumps(receipt))
            original_series=(series/'source.txt').read_bytes();(series/'source.txt').write_text('changed source')
            with self.assertRaises(ValidationError):reconcile_series(root,series,write=True)
            self.assertEqual(usage.read_bytes(),first);(series/'source.txt').write_bytes(original_series)
            decisions=root/'psychology-warehouse/editorial/decisions.json';decisions.write_text(json.dumps({'sourceSha256':registry['sourceSha256'],'overrides':[{'fragmentId':'pn-one','sourceSha256':'0'*64,'topics':['TRAUMA'],'reviewReasons':[]}]}))
            with self.assertRaises(ValidationError):reconcile_series(root,series,write=True)
            self.assertEqual(usage.read_bytes(),first);decisions.unlink()
            bad=json.loads((series/'registry.json').read_text());bad['fragments'][0]['source']='Changed';(series/'registry.json').write_text(json.dumps(bad))
            with self.assertRaises(ValidationError):reconcile_series(root,series,write=True)
            self.assertEqual(usage.read_bytes(),first)

if __name__=='__main__':unittest.main()
