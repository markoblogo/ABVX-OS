import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from xml.sax.saxutils import escape
import test_book_readiness as fixtures

class ExistingBookOverlap(unittest.TestCase):
    def test_exact_and_near_matches_remain_distinct_and_sources_are_bound(self):
        from abvx_harness.book_readiness import refresh
        from abvx_harness.book_readiness_overlap import compare_book
        with TemporaryDirectory() as t:
            root,site=Path(t)/'os',Path(t)/'site';fixtures.ReadinessTests.fixture(root,site)
            p=fixtures.ReadinessTests.article(site,'psychology-notebook-01','_A thematic selection._\n\nA stable quoted sentence about human identity.\n\n---\n\nA changing observation about our complex inner world.\n\n---\n\nUnrelated new fragment with no corresponding manuscript passage.',tag='psychology-notebook')
            book=Path(t)/'book.docx'
            with ZipFile(book,'w') as z:
                texts=['A stable quoted sentence about human identity.','A changing observation about the complex inner world.']
                xml='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+''.join('<w:p><w:r><w:t>'+escape(x)+'</w:t></w:r></w:p>' for x in texts)+'</w:body></w:document>'
                z.writestr('word/document.xml',xml)
            one=compare_book(root,site,book,'https://abvx.xyz/books/fragments-from-a-therapists-notebook')
            self.assertEqual(one['summary']['exact'],1)
            self.assertEqual(one['summary']['near_for_review'],1)
            self.assertEqual(one['summary']['not_matched'],1)
            s=refresh(root,site,as_of='2026-10-25');c=s['candidates']['psychology-notebook']
            self.assertEqual(c['known_book_overlap_fragments'],1)
            self.assertIsNone(c['new_book_words'])
            p.write_text(p.read_text()+' Changed current source.')
            s=refresh(root,site,as_of='2026-10-25')
            self.assertEqual(s['candidates']['psychology-notebook']['known_book_overlap_fragments'],0)

if __name__=='__main__':unittest.main()
