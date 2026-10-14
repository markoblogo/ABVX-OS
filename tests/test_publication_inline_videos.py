"""Pure synthetic HTML probes; no working content, Git, network or Cortex state."""
import unittest
from abvx_harness.publication_learning import validate_live_html

class InlineVideoProbeTests(unittest.TestCase):
 def player(self,label='Example A launch video',video_id='aaaaaaaaaaa',href='https://youtu.be/aaaaaaaaaaa'):
  return f'<figure class="youtube-figure"><iframe src="https://www.youtube-nocookie.com/embed/{video_id}?rel=0&amp;playsinline=1" title="{label}"></iframe><figcaption><a href="{href}">Watch on YouTube</a></figcaption></figure>'
 def fixture(self):
  item={'title':'Synthetic video review','enrichment':{'canonical_path':'/writing/test-only'},'payload':{'body_lines':['An original paragraph that must remain verified.\n\n[Example A launch video](https://youtu.be/aaaaaaaaaaa)\n\n[Example B launch video](https://www.youtube.com/watch?v=bbbbbbbbbbb)']}}
  html='<link rel="canonical" href="https://abvx.xyz/writing/test-only"><h1>Synthetic video review</h1><p>An original paragraph that must remain verified.</p>'
  html+=self.player()+self.player('Example B launch video','bbbbbbbbbbb','https://www.youtube.com/watch?v=bbbbbbbbbbb')
  return item,html
 def reject(self,item,values):
  for value in values:
   with self.subTest(value=value),self.assertRaises(ValueError):validate_live_html(item,value.encode())
 def test_verifies_both_exact_titled_players_and_original_fallback_urls(self):
  item,html=self.fixture();validate_live_html(item,html.encode())
 def test_missing_wrong_or_spoofed_player_and_fallback_never_pass(self):
  item,html=self.fixture()
  self.reject(item,[html.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc'),html.replace('Example A launch video','Wrong launch video'),html.replace('href="https://youtu.be/aaaaaaaaaaa"','href="https://youtu.be/ccccccccccc"'),html.replace('www.youtube-nocookie.com/embed/aaaaaaaaaaa','www.youtube-nocookie.com.evil.test/embed/aaaaaaaaaaa'),html.replace('<iframe src="https://www.youtube-nocookie.com/embed/aaaaaaaaaaa','<iframe src="http://www.youtube-nocookie.com/embed/aaaaaaaaaaa'),html.replace('An original paragraph that must remain verified.','Incorrect text'),html.replace('title="Example A launch video"','title'),html.replace('src="https://www.youtube-nocookie.com/embed/aaaaaaaaaaa?rel=0&amp;playsinline=1"','src=""')])
 def test_ordinary_missing_text_cannot_bypass_via_inline_or_unsafe_links(self):
  item,html=self.fixture()
  for source in ['See [Example A launch video](https://youtu.be/aaaaaaaaaaa) as part of this sentence.', '[Example A launch video](https://youtu.be.evil.test/aaaaaaaaaaa)', '[Example A launch video](https://user@youtu.be/aaaaaaaaaaa)', '[Example A launch video](https://youtu.be:0/aaaaaaaaaaa)']:
   item['payload']['body_lines']=[source];self.reject(item,[html])
 def test_legacy_visible_non_video_link_labels_still_verify(self):
  item,html=self.fixture();item['payload']['body_lines']=['[A visible ordinary link label](https://example.com/)']
  validate_live_html(item,(html+'<a href="https://example.com/">A visible ordinary link label</a>').encode())
 def test_visible_label_never_substitutes_for_player_or_fallback(self):
  item,html=self.fixture();repeated=html+'<h2>Example A launch video</h2>'
  self.reject(item,[repeated.replace(self.player(),''),repeated.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc'),repeated.replace('href="https://youtu.be/aaaaaaaaaaa"','href="https://example.com/"')])
 def test_short_video_labels_always_require_structure(self):
  item,html=self.fixture();item['payload']['body_lines']=['An original paragraph that must remain verified.\n\n[A](https://youtu.be/aaaaaaaaaaa)'];html=html.replace('Example A launch video','A')
  validate_live_html(item,html.encode())
  self.reject(item,[html.replace(self.player('A'),''),html.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc'),html.replace('href="https://youtu.be/aaaaaaaaaaa"','href="https://example.com/"')])
 def test_video_only_short_source_requires_a_real_player(self):
  item,html=self.fixture();item['payload']['body_lines']=['[A](https://youtu.be/aaaaaaaaaaa)'];html=html.replace('Example A launch video','A')
  validate_live_html(item,html.encode());self.reject(item,[html.replace(self.player('A'),'')])
 def test_hidden_players_and_fallbacks_are_not_evidence(self):
  item,html=self.fixture()
  variants=[]
  for attr in ['hidden','hidden="false"','hidden="until-found"','aria-hidden="true"','inert','style="display: none !important"','style="visibility: hidden"','style="content-visibility: hidden"']:
   variants.extend([html.replace('<iframe ',f'<iframe {attr} ',1),html.replace('<a ',f'<a {attr} ',1),html.replace(self.player(),f'<div {attr}>'+self.player()+'</div>')])
  for tag in ['template','script','style','noscript','iframe','details','dialog']:
   variants.append(html.replace(self.player(),f'<{tag}>'+self.player()+f'</{tag}>'))
  self.reject(item,variants)
 def test_unrelated_hidden_content_does_not_hide_later_real_players(self):
  item,html=self.fixture();html=html.replace('<h1>','<template><div hidden>unused</div></template><img hidden src="unused"><h1>',1)
  validate_live_html(item,html.encode())
 def test_unicode_video_ids_cannot_be_structural_evidence(self):
  item,html=self.fixture()
  for invalid in ['é'*11,'а'*11,'𝟘'*11]:
   changed={'title':item['title'],'enrichment':item['enrichment'],'payload':{'body_lines':[item['payload']['body_lines'][0].replace('aaaaaaaaaaa',invalid)]}}
   self.reject(changed,[html.replace('aaaaaaaaaaa',invalid),html.replace('aaaaaaaaaaa',invalid)+'<h2>Example A launch video</h2>'])
 def test_fallback_must_be_in_the_matching_player_caption(self):
  item,html=self.fixture();anchor='<a href="https://youtu.be/aaaaaaaaaaa">Watch on YouTube</a>';detached=html.replace(anchor,'')
  self.reject(item,[detached+'<footer>'+anchor+'</footer>',detached+'<figure><figcaption>'+anchor+'</figcaption></figure>',html.replace(anchor,anchor.replace('>Watch on YouTube<','><')),html.replace('<figcaption>'+anchor+'</figcaption>','<nav>'+anchor+'</nav>')])
 def test_visible_channel_links_and_fenced_video_examples_remain_text(self):
  item,html=self.fixture()
  for source,visible in [('[Our YouTube channel](https://www.youtube.com/@example)','Our YouTube channel'),('```markdown\n\n[Example video](https://youtu.be/aaaaaaaaaaa)\n\n```','[Example video](https://youtu.be/aaaaaaaaaaa)')]:
   item['payload']['body_lines']=[source];validate_live_html(item,(html.replace(self.player(),'')+'<pre>'+visible+'</pre>').encode())

 def test_open_containers_keep_real_players_visible(self):
  item,html=self.fixture()
  for tag in ['details','dialog']:
   validate_live_html(item,html.replace(self.player(),f'<{tag} open>'+self.player()+f'</{tag}>').encode())
 def test_empty_first_watch_id_cannot_use_a_later_query_value(self):
  item,html=self.fixture();item['payload']['body_lines']=[item['payload']['body_lines'][0].replace('watch?v=bbbbbbbbbbb','watch?v=&v=bbbbbbbbbbb')]
  self.reject(item,[html.replace('watch?v=bbbbbbbbbbb','watch?v=&amp;v=bbbbbbbbbbb')])

 def test_self_closing_html_iframe_is_not_a_rendered_projection(self):
  item,html=self.fixture();bad=html.replace('title="Example A launch video"></iframe>','title="Example A launch video"/>')
  self.reject(item,[bad])
 def test_repeated_source_occurrences_require_distinct_players(self):
  item,html=self.fixture();item['payload']['body_lines'][0]+='\n\n[Example A launch video](https://youtu.be/aaaaaaaaaaa)'
  self.reject(item,[html]);validate_live_html(item,(html+self.player()).encode())
