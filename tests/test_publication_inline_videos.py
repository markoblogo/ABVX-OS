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

 def test_video_adjacent_to_code_fences_always_requires_a_player(self):
  link='[Example A launch video](https://youtu.be/aaaaaaaaaaa)'
  code='Command example that must stay visible.'
  cases=[(link+'\n```text\n'+code+'\n```','<p>Example A launch video</p><pre>'+code+'</pre>'),('```text\n'+code+'\n```\n'+link,'<pre>'+code+'</pre><p>Example A launch video</p>')]
  for source,visible in cases:
   item,html=self.fixture();item['payload']['body_lines']=['An original paragraph that must remain verified.\n\n'+source]
   validate_live_html(item,(html+'<pre>'+code+'</pre>').encode())
   self.reject(item,[html.replace(self.player(),'')+visible])
 def test_short_video_next_to_heading_or_list_requires_a_player(self):
  link='[A](https://youtu.be/aaaaaaaaaaa)'
  for source in [link+'\n## Heading', '## Heading\n'+link, link+'\n- List item', '- List item\n'+link]:
   item,html=self.fixture();item['payload']['body_lines']=['An original paragraph that must remain verified.\n\n'+source]
   validate_live_html(item,(html.replace('Example A launch video','A')+'<h2>Heading</h2><p>List item</p>').encode())
   self.reject(item,[html.replace(self.player(),'')+'<h2>Heading</h2><p>List item A</p>'])
 def test_list_links_and_multi_link_paragraphs_do_not_become_players(self):
  item,html=self.fixture()
  for source,text in [('- [List video label](https://youtu.be/aaaaaaaaaaa)','List video label'),('[First link](https://youtu.be/aaaaaaaaaaa)\n[Second link](https://youtu.be/bbbbbbbbbbb)','First link Second link')]:
   item['payload']['body_lines']=[source];validate_live_html(item,(html.replace(self.player(),'')+'<p>'+text+'</p>').encode())
 def test_duplicate_structural_attributes_are_rejected_in_both_orders(self):
  item,html=self.fixture();frame='src="https://www.youtube-nocookie.com/embed/aaaaaaaaaaa?rel=0&amp;playsinline=1"';title='title="Example A launch video"';anchor='href="https://youtu.be/aaaaaaaaaaa"'
  variants=[]
  for good,bad in [(frame,'src="https://example.com/wrong"'),(title,'title="Wrong title"'),(anchor,'href="https://example.com/wrong"')]:
   variants.extend([html.replace(good,bad+' '+good,1),html.replace(good,good+' '+bad,1),html.replace(good,good+' '+good,1)])
  variants.extend([html.replace(frame,'SRC="https://example.com/wrong" '+frame,1),html.replace('<iframe ','<iframe style="display:none" style="display:block" ',1),html.replace('<a ','<a aria-hidden="true" aria-hidden="false" ',1),html.replace('rel="canonical"','rel="other" rel="canonical"',1),html.replace('href="https://abvx.xyz/writing/test-only"','href="https://example.com/wrong" href="https://abvx.xyz/writing/test-only"',1)])
  self.reject(item,variants)
 def test_punctuation_only_labels_cannot_supply_an_accessible_title(self):
  for label in ['---','___','🎬']:
   item,html=self.fixture();item['payload']['body_lines']=['['+label+'](https://youtu.be/aaaaaaaaaaa)']
   for title in ['title="'+label+'"','title=""','']:
    self.reject(item,[html.replace('title="Example A launch video"',title,1)])
 def test_body_implicitly_closes_document_head(self):
  item,html=self.fixture();prefix,body=html.split('<h1>',1)
  implicit='<html><head>'+prefix+'<title>Document metadata</title><body><h1>'+body+'</body></html>'
  validate_live_html(item,implicit.encode())
  validate_live_html(item,implicit.replace('<body>','</head><body>',1).encode())
 def test_fake_body_inside_head_template_stays_hidden(self):
  item,html=self.fixture();prefix,body=html.split('<h1>',1)
  self.reject(item,['<html><head>'+prefix+'<template><body><h1>'+body+'</body></template></head></html>'])

 def test_visible_text_next_to_a_fence_never_substitutes_for_player(self):
  for label in ['A','Example A launch video']:
   link='['+label+'](https://youtu.be/aaaaaaaaaaa)';code='Command example that must stay visible.'
   for source,visible in [(link+'\n```text\n'+code+'\n```','<p>'+label+'</p><pre>'+code+'</pre>'),('```text\n'+code+'\n```\n'+link,'<pre>'+code+'</pre><p>'+label+'</p>')]:
    item,html=self.fixture();item['payload']['body_lines']=['An original paragraph that must remain verified.\n\n'+source]
    self.reject(item,[html.replace(self.player(),'')+visible])

 def test_extended_fence_syntax_preserves_prose_and_code_boundaries(self):
  prose='An original paragraph that must remain verified.'
  code='Command example that must stay visible.'
  link='[A](https://youtu.be/aaaaaaaaaaa)'
  for opening,closing in [('~~~python','~~~'),('````c++','````'),('```c++','````'),('  ~~~~ arbitrary info','   ~~~~~')]:
   for source in [prose+'\n'+opening+'\n'+code+'\n'+closing+'\n'+link,link+'\n'+opening+'\n'+code+'\n'+closing+'\n'+prose]:
    with self.subTest(source=source):
     item,html=self.fixture();item['payload']['body_lines']=[source]
     good=html.replace('Example A launch video','A')+'<pre>'+code+'</pre>'
     validate_live_html(item,good.encode())
     self.reject(item,[good.replace(self.player('A'),'<p>A</p>'),good.replace(prose,'Missing prose')])
 def test_mismatched_and_short_fence_markers_remain_inside_code(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  for opening,wrong,closing in [('````c++','```','````'),('~~~text','```','~~~'),('```text','```not-a-close','```')]:
   source=opening+'\n'+wrong+'\n[Literal video example](https://youtu.be/aaaaaaaaaaa)\n'+closing
   self.assertEqual(list(publication_markdown_blocks([source])),[('code',wrong+'\n[Literal video example](https://youtu.be/aaaaaaaaaaa)')])
 def test_unclosed_extended_fences_remain_code_at_eof(self):
  for opening in ['~~~markdown','````c++']:
   item,html=self.fixture();item['payload']['body_lines']=[opening+'\n[Literal video example](https://youtu.be/aaaaaaaaaaa)']
   validate_live_html(item,(html.replace(self.player(),'')+'<pre>[Literal video example](https://youtu.be/aaaaaaaaaaa)</pre>').encode())
 def test_short_headings_and_list_items_are_required(self):
  prose='An original paragraph that must remain verified.'
  for marker,label in [('## ','Warning'),('### ','A'),('- ','Do this now'),('* ','Go'),('1. ','Stop'),('2) ','Wait')]:
   for separator in ['\n','\n\n']:
    item,html=self.fixture();item['payload']['body_lines']=[prose+separator+marker+label]
    html=html.split('<figure',1)[0]
    validate_live_html(item,(html+'<p>'+label+'</p>').encode())
    self.reject(item,[html])
 def test_indented_markdown_examples_stay_code_and_dedent_restores_video(self):
  prose='An original paragraph that must remain verified.'
  examples=['[Literal video example](https://youtu.be/aaaaaaaaaaa)','## Literal heading example','- Literal list item example']
  for indent in ['    ','\t',' \t']:
   for example in examples:
    item,html=self.fixture();item['payload']['body_lines']=[prose+'\n\n'+indent+example+'\n\n'+indent+'More literal code text.\n[A](https://youtu.be/aaaaaaaaaaa)']
    good=html.replace('Example A launch video','A')+'<pre>'+example+'\n\nMore literal code text.</pre>'
    validate_live_html(item,good.encode())
    self.reject(item,[good.replace(self.player('A'),'<p>A</p>')])

 def test_indented_continuation_cannot_hide_a_video_in_an_existing_paragraph(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  for continuation in ['[Literal continuation](https://youtu.be/aaaaaaaaaaa)','## Literal heading','- Literal item']:
   source='Introductory prose.\n    '+continuation
   self.assertEqual(list(publication_markdown_blocks([source])),[('paragraph','Introductory prose. '+continuation)])
 def test_fence_markers_inside_indented_code_do_not_open_fenced_blocks(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  source='    ~~~markdown\n    [Literal video example](https://youtu.be/aaaaaaaaaaa)\n    ~~~\n[A](https://youtu.be/aaaaaaaaaaa)'
  blocks=list(publication_markdown_blocks([source]))
  self.assertEqual([kind for kind,_ in blocks],['code','paragraph'])
  self.assertEqual(blocks[-1][1],'[A](https://youtu.be/aaaaaaaaaaa)')

 def test_whitespace_only_separators_never_hide_standalone_videos(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  prose='An original paragraph that must remain verified.'
  for blank in [' ', '   ', '    ', '        ', '\t', ' \t ', '\t\t']:
   for newline in ['\n','\r\n']:
    with self.subTest(blank=repr(blank),newline=repr(newline)):
     item,html=self.fixture();item['payload']['body_lines']=[newline.join([prose,blank,'[A](https://youtu.be/aaaaaaaaaaa)'])]
     self.assertEqual(list(publication_markdown_blocks(item['payload']['body_lines'])),[('paragraph',prose),('paragraph','[A](https://youtu.be/aaaaaaaaaaa)')])
     good=html.replace('Example A launch video','A')
     validate_live_html(item,good.encode())
     self.reject(item,[good.replace(self.player('A'),'<p>A</p>')])
 def test_short_plus_list_items_require_visible_text(self):
  prose='An original paragraph that must remain verified.'
  for separator in ['\n','\n\n','\n    \n','\n\t\n']:
   for marker in ['+ ', ' + ', '   +\t']:
    with self.subTest(separator=repr(separator),marker=repr(marker)):
     item,html=self.fixture();item['payload']['body_lines']=[prose+separator+marker+'Go']
     html=html.split('<figure',1)[0]
     validate_live_html(item,(html+'<ul><li>Go</li></ul>').encode())
     self.reject(item,[html])
 def test_whitespace_separators_preserve_code_examples(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  link='[Literal video example](https://youtu.be/aaaaaaaaaaa)'
  for blank in ['    ','\t',' \t ']:
   for source in ['~~~markdown\n'+blank+'\n'+link+'\n~~~','    '+link+'\n'+blank+'\n    More literal code text.']:
    item,html=self.fixture();item['payload']['body_lines']=[source]
    self.assertEqual([kind for kind,_ in publication_markdown_blocks([source])],['code'])
    validate_live_html(item,(html.replace(self.player(),'')+'<pre>'+link+'\nMore literal code text.</pre>').encode())

 def test_list_continuations_require_the_complete_item(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  prose='An original paragraph that must remain verified.'
  for marker in ['- ','* ','+ ','1. ','2) ']:
   for continuation in ['today',' today','  today','    today','\ttoday']:
    with self.subTest(marker=marker,continuation=repr(continuation)):
     source=marker+'Important action\n'+continuation
     self.assertEqual(list(publication_markdown_blocks([source])),[('text','Important action today')])
     item,html=self.fixture();item['payload']['body_lines']=[prose+'\n\n'+source]
     html=html.split('<figure',1)[0]
     validate_live_html(item,(html+'<ul><li>Important action today</li></ul>').encode())
     self.reject(item,[html+'<ul><li>Important action</li></ul>'])
 def test_multiline_short_list_items_remain_required_at_block_boundaries(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  prose='An original paragraph that must remain verified.'
  cases=[('- Do\n this now',[('text','Do this now')]),('- Go\n today\n+ Stop\n tomorrow',[('text','Go today'),('text','Stop tomorrow')]),('- Go\n today\n## Warning',[('text','Go today'),('text','Warning')])]
  for source,blocks in cases:
   with self.subTest(source=source):
    self.assertEqual(list(publication_markdown_blocks([source])),blocks)
    item,html=self.fixture();item['payload']['body_lines']=[prose+'\n\n'+source]
    html=html.split('<figure',1)[0]
    validate_live_html(item,(html+'<p>'+' '.join(text for _,text in blocks)+'</p>').encode())
    self.reject(item,[html+'<p>Do Go Stop Warning</p>'])
 def test_list_continuations_do_not_swallow_separate_video_blocks(self):
  prose='An original paragraph that must remain verified.'
  for boundary in ['\n\n','\n    \n','\n\t\n']:
   item,html=self.fixture();item['payload']['body_lines']=[prose+'\n\n- Important action\n today'+boundary+'[A](https://youtu.be/aaaaaaaaaaa)']
   good=html.replace('Example A launch video','A')+'<ul><li>Important action today</li></ul>'
   validate_live_html(item,good.encode())
   self.reject(item,[good.replace(self.player('A'),'<p>A</p>'),good.replace('Important action today','Important action')])
 def test_list_link_continuations_remain_literal_text(self):
  item,html=self.fixture();item['payload']['body_lines']=['- See this\n useful [video example](https://youtu.be/aaaaaaaaaaa)']
  html=html.split('<figure',1)[0]+'<ul><li>See this useful <a href="https://youtu.be/aaaaaaaaaaa">video example</a></li></ul>'
  validate_live_html(item,html.encode())
  self.reject(item,[html.replace('video example','')])
