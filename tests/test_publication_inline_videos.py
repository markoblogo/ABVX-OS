"""Pure synthetic HTML probes; no working content, Git, network or Cortex state."""
import unittest
from abvx_harness.publication_learning import validate_live_html

class InlineVideoProbeTests(unittest.TestCase):
 def fixture(self):
  item={'title':'Synthetic video review','enrichment':{'canonical_path':'/writing/test-only'},'payload':{'body_lines':['An original paragraph that must remain verified.\n\n[Example A launch video](https://youtu.be/aaaaaaaaaaa)\n\n[Example B launch video](https://www.youtube.com/watch?v=bbbbbbbbbbb)']}}
  html='<link rel="canonical" href="https://abvx.xyz/writing/test-only"><h1>Synthetic video review</h1><p>An original paragraph that must remain verified.</p>'
  for label,id,href in [('Example A','aaaaaaaaaaa','https://youtu.be/aaaaaaaaaaa'),('Example B','bbbbbbbbbbb','https://www.youtube.com/watch?v=bbbbbbbbbbb')]:
   html+=f'<iframe src="https://www.youtube-nocookie.com/embed/{id}?rel=0&amp;playsinline=1" title="{label} launch video"></iframe><a href="{href}">Watch on YouTube</a>'
  return item,html
 def test_verifies_both_exact_titled_players_and_original_fallback_urls(self):
  item,html=self.fixture();validate_live_html(item,html.encode())
 def test_missing_wrong_or_spoofed_player_and_fallback_never_pass(self):
  item,html=self.fixture()
  variants=[html.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc'),html.replace('Example A launch video','Wrong launch video'),html.replace('href="https://youtu.be/aaaaaaaaaaa"','href="https://youtu.be/ccccccccccc"'),html.replace('www.youtube-nocookie.com/embed/aaaaaaaaaaa','www.youtube-nocookie.com.evil.test/embed/aaaaaaaaaaa'),html.replace('<iframe src="https://www.youtube-nocookie.com/embed/aaaaaaaaaaa','<iframe src="http://www.youtube-nocookie.com/embed/aaaaaaaaaaa'),html.replace('An original paragraph that must remain verified.','Incorrect text'),html.replace('title="Example A launch video"','title'),html.replace('src="https://www.youtube-nocookie.com/embed/aaaaaaaaaaa?rel=0&amp;playsinline=1"','src=""')]
  for value in variants:
   with self.subTest(value=value),self.assertRaises(ValueError):validate_live_html(item,value.encode())
 def test_ordinary_missing_text_cannot_bypass_via_inline_or_unsafe_links(self):
  item,html=self.fixture()
  for source in ['See [Example A launch video](https://youtu.be/aaaaaaaaaaa) as part of this sentence.', '[Example A launch video](https://youtu.be.evil.test/aaaaaaaaaaa)', '[Example A launch video](https://user@youtu.be/aaaaaaaaaaa)', '[Example A launch video](https://youtu.be:0/aaaaaaaaaaa)' ]:
   item['payload']['body_lines']=[source]
   with self.subTest(source=source),self.assertRaises(ValueError):validate_live_html(item,html.encode())
 def test_legacy_visible_link_labels_still_verify(self):
  item,html=self.fixture();item['payload']['body_lines']=['[A visible ordinary link label](https://example.com/)']
  validate_live_html(item,(html+'<a href="https://example.com/">A visible ordinary link label</a>').encode())
