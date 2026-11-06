import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prepare_publication',ROOT/'scripts/prepare_abvx_publication.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

DRAFT="""Publish using the existing collection.
# A supplied title

First paragraph.

## Keep this heading

**Keep** this sentence.

---

### SEO и метаданные для ABVX

**Title:** A supplied title
**SEO title:** A supplied SEO title
**Slug:** `a-supplied-title`
**Meta description:** `A supplied search description.`
**Excerpt:** `A supplied excerpt.`
**Content type:** `note`
**Topics:** `ai`, `workflow`
**Language:** `en`
"""
class DraftPreparationTests(unittest.TestCase):
 def test_supplied_body_and_seo_are_separated_without_rewriting(self):
  source,report=module.normalize_draft(DRAFT,'2026-10-19',{})
  data=json.loads(source.split('---',2)[1]);body=source.split('---',2)[2].strip()
  self.assertEqual(body,'First paragraph.\n\n## Keep this heading\n\n**Keep** this sentence.')
  self.assertEqual(data['title'],'A supplied title');self.assertEqual(data['slug'],'a-supplied-title')
  self.assertEqual(data['seoDescription'],'A supplied search description.');self.assertEqual(data['tags'],['ai','workflow'])
  self.assertTrue(report['bodyPreserved']);self.assertNotIn('Publish using',source);self.assertNotIn('SEO и метаданные',source)

 def test_recipe_requires_reviewed_structure_and_preserves_source_timing(self):
  recipe=DRAFT.replace('**Content type:** `note`','**Collection:** Kitchen Notes\n**Content type:** `recipe`')+'**Servings:** 2\n**Preparation time:** About ten minutes\n'
  with self.assertRaises(module.ValidationError):module.normalize_draft(recipe,'2026-10-19',{})
  source,_=module.normalize_draft(recipe,'2026-10-19',{'recipe':{'ingredients':['Supplied ingredient'],'instructions':['Supplied step']}})
  data=json.loads(source.split('---',2)[1]);self.assertEqual(data['recipe']['recipeYield'],'2')
  self.assertEqual(data['recipe']['ingredients'],['Supplied ingredient'])
  self.assertEqual(data['recipe']['timingText'],'Preparation time: About ten minutes')
  with self.assertRaises(module.ValidationError):module.normalize_draft(recipe,'2026-10-19',{'recipe':{'ingredients':['x'],'instructions':['y'],'recipeYield':'3'}})

 def test_ambiguous_service_metadata_is_not_silently_discarded(self):
  for draft in (DRAFT+'**Unknown:** value\n',DRAFT+'**Language:** fr\n',DRAFT.replace('**Title:** A supplied title','**Title:** Different'),DRAFT.replace('`a-supplied-title`','`../unsafe`')):
   with self.subTest(draft=draft[-80:]),self.assertRaises(module.ValidationError):module.normalize_draft(draft,'2026-10-19',{})

 def test_cli_preserves_body_when_cover_asset_is_present(self):
  import tempfile,struct,sys
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cycle=root/'.tmp/publication-learning/test-cycle';cycle.mkdir(parents=True)
   (cycle/'cycle.json').write_text(json.dumps({'itemIds':['test-item']}))
   draft=root/'draft.txt';draft.write_text(DRAFT.replace('First paragraph.', 'First paragraph.\n\n---\n\nAnother paragraph.'))
   cover=root/'image.png';cover.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II',10,20))
   prepared=[]
   def capture(root,intake):
    prepared.append(json.loads(Path(intake).read_text()));return {'id':'test-item','status':'PREPARED','adapter':{'id':'abvx.writing'}}
   args=['prepare','--draft',str(draft),'--id','test-item','--run','test-cycle','--cover',str(cover),'--image-alt','Supplied image','--date','2026-10-19']
   with patch.object(module,'ROOT',root),patch.object(module,'prepare_content_item',side_effect=capture),patch.object(sys,'argv',args):module.main()
   fixture=prepared[0];self.assertIn('**Keep** this sentence.',fixture['payload']['source_markdown'])
   self.assertEqual(fixture['payload']['body_lines'],['First paragraph.\n\n---\n\nAnother paragraph.\n\n## Keep this heading\n\n**Keep** this sentence.'])
   self.assertEqual(fixture['payload']['media_assets'][0]['source'],str(cover.resolve()))
   self.assertEqual(json.loads((cycle/'article.md').read_text().split('---',2)[1])['media']['height'],20)
   (cycle/'article.md').unlink();cover.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
   with patch.object(module,'ROOT',root),patch.object(module,'prepare_content_item'),patch.object(sys,'argv',args),self.assertRaises(SystemExit):module.main()
   self.assertFalse((cycle/'article.md').exists())

 def test_recipe_yield_and_cooling_service_fields_are_retained(self):
  draft=DRAFT.replace('**Content type:** `note`','**Collection:** `Kitchen Notes`\n**Content type:** `recipe`')+'**Yield:** Approximately 6–10 cookies\n**Cooling time:** Until completely cool; approximately 90 minutes in the experiment.\n'
  supplement={'recipe':{'ingredients':[{'name':'flour','quantityText':'100 g'}],'instructions':['Use the supplied method.']}}
  source,_=module.normalize_draft(draft,'2026-10-19',supplement)
  data=json.loads(source.split('---',2)[1]);self.assertEqual(data['recipe']['recipeYield'],'Approximately 6–10 cookies')
  self.assertIn('Cooling time: Until completely cool; approximately 90 minutes in the experiment.',data['recipe']['timingText'])
  with self.assertRaises(module.ValidationError):module.normalize_draft(draft+'**Servings:** 3\n','2026-10-19',supplement)

 def test_ready_article_requires_all_inline_photo_asset_mappings(self):
  source,_=module.normalize_draft(DRAFT,'2026-10-19',{});front,_,body=source[4:].partition('\n---');data=json.loads(front)
  data['illustrations']=[{'src':'/media/writing/detail.jpeg','alt':'Original photograph','width':964,'height':1280,'caption':'The original photograph.','afterHeading':'Keep this heading'}]
  ready='---\n'+json.dumps(data)+'\n---'+body
  with self.assertRaises(module.ValidationError):module.publication_fixture(ready,'test-item','/approved.md',[])
  asset={'source':'/original.jpeg','target':'/media/writing/detail.jpeg','sha256':'a'*64}
  self.assertEqual(module.publication_fixture(ready,'test-item','/approved.md',[asset])['payload']['media_assets'],[asset])
