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
  for source in [link+'\n## Heading', '## Heading\n'+link, link+'\n- List item']:
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
     if source.startswith(link):good=good.replace('<p>'+prose+'</p>','')+'<p>'+prose+'</p>'
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
    if marker=='2) ' and separator=='\n':continue
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

 def test_standalone_link_continuations_stay_with_the_list_item(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  for marker in ['- ','* ','+ ','1. ','2) ']:
   for indent in ['', ' ', '  ', '   ', '    ', '\t']:
    with self.subTest(marker=marker,indent=repr(indent)):
     source=marker+'See below\n'+indent+'[A](https://youtu.be/aaaaaaaaaaa)'
     self.assertEqual(list(publication_markdown_blocks([source])),[('text','See below [A](https://youtu.be/aaaaaaaaaaa)')])
     item,html=self.fixture();item['payload']['body_lines']=[source]
     html=html.split('<figure',1)[0]+'<ul><li>See below <a href="https://youtu.be/aaaaaaaaaaa">A</a></li></ul>'
     validate_live_html(item,html.encode());self.reject(item,[html.replace('>A</a>','></a>')])
 def test_all_six_atx_heading_levels_are_required(self):
  prose='An original paragraph that must remain verified.'
  for level in range(1,7):
   for suffix in ['', ' ###']:
    for separator in ['\n','\n\n','\n    \n']:
     with self.subTest(level=level,suffix=suffix,separator=repr(separator)):
      item,html=self.fixture();item['payload']['body_lines']=[prose+separator+'#'*level+' Warning'+suffix]
      html=html.split('<figure',1)[0]
      validate_live_html(item,(html+f'<h{level}>Warning</h{level}>').encode())
      self.reject(item,[html])
 def test_implicit_body_elements_close_the_document_head(self):
  item,html=self.fixture();prefix,body=html.split('<h1>',1)
  for start in ['<h1>','<main><h1>','<div><h1>','<hr><h1>','<img src="unused"><h1>']:
   implicit='<html><head>'+prefix+'<title>Hidden metadata</title>'+start+body+'</html>'
   validate_live_html(item,implicit.encode())
 def test_implicit_body_text_closes_head_but_metadata_remains_hidden(self):
  item,html=self.fixture();prefix,body=html.split('<h1>',1)
  implicit='<html><head>'+prefix+'<meta name="description" content="metadata"><title>Hidden metadata</title>Visible introduction<h1>'+body+'</html>'
  validate_live_html(item,implicit.encode())
  item['payload']['body_lines']=['Hidden metadata is not authored evidence.']
  self.reject(item,[implicit])
 def test_fake_implicit_body_inside_nonrendered_head_content_stays_hidden(self):
  item,html=self.fixture();prefix,body=html.split('<h1>',1)
  for tag in ['template','noscript','title','script','style']:
   self.reject(item,['<html><head>'+prefix+f'<{tag}><h1>'+body+f'</{tag}></head></html>'])
 def test_html_comment_blocks_do_not_require_editorial_notes(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  prose='An original paragraph that must remain verified.'
  for comment in ['<!--\n## Note\n- Go\n[A](https://youtu.be/aaaaaaaaaaa)\n-->', '<!-- ## Note -->', '  <!--\n~~~python\n## Note\n-->','<!-- Unclosed editorial note\n###### Warning']:
   for separator in ['\n','\n\n']:
    with self.subTest(comment=comment,separator=repr(separator)):
     item,html=self.fixture();item['payload']['body_lines']=[prose+separator+comment]
     self.assertEqual(list(publication_markdown_blocks(item['payload']['body_lines'])),[('paragraph',prose)])
     validate_live_html(item,html.encode())
 def test_comment_blocks_restore_real_video_and_heading_checks(self):
  item,html=self.fixture();item['payload']['body_lines']=['<!--\n## Editorial note\n-->\n###### Warning\n\n[A](https://youtu.be/aaaaaaaaaaa)']
  good=html.replace('Example A launch video','A')+'<h6>Warning</h6>'
  validate_live_html(item,good.encode())
  self.reject(item,[good.replace(self.player('A'),'<p>A</p>'),good.replace('<h6>Warning</h6>','')])
 def test_comment_markers_in_code_remain_literal(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  literal='<!--\n## Literal code heading\n-->'
  for source in ['```html\n'+literal+'\n```','    '+literal.replace('\n','\n    ')]:
   with self.subTest(source=source):
    self.assertEqual(list(publication_markdown_blocks([source])),[('code',literal)])
    item,html=self.fixture();item['payload']['body_lines']=[source]
    validate_live_html(item,(html+'<pre>&lt;!--\n## Literal code heading\n--&gt;</pre>').encode())

 def test_list_relative_fences_exclude_info_strings_from_required_text(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  for marker,base in [('- ',2),('* ',2),('+ ',2),('1. ',3),('10) ',4),('  - ',4),('   1. ',6),('-\t',4),('1.\t',4)]:
   for extra in [0,1,2,3]:
    for opener,closer in [('```python','```'),('~~~~c++','~~~~~')]:
     for separator in ['\n','\n\n']:
      with self.subTest(marker=marker,extra=extra,opener=opener,separator=repr(separator)):
       indent=' '*(base+extra);code='An exact nested code example.'
       source=marker+'Required action'+separator+indent+opener+'\n'+' '*base+code+'\n'+indent+closer
       self.assertEqual(list(publication_markdown_blocks([source])),[('text','Required action'),('code',code)])
       item,html=self.fixture();item['payload']['body_lines']=[source];html=html.split('<figure',1)[0]
       good=html+'<ul><li>Required action<pre><code>'+code+'</code></pre></li></ul>'
       validate_live_html(item,good.encode());self.reject(item,[good.replace(code,'Wrong code'),good.replace('>Required action<','><')])
 def test_list_fences_do_not_swallow_dedented_real_videos(self):
  code='An exact nested code example.';link='[A](https://youtu.be/aaaaaaaaaaa)'
  for closer in ['    ```\n','']:
   item,html=self.fixture();item['payload']['body_lines']=['- Example\n    ```python\n    '+code+'\n'+closer+link]
   good=html.replace('Example A launch video','A')+'<ul><li>Example<pre>'+code+'</pre></li></ul>'
   validate_live_html(item,good.encode());self.reject(item,[good.replace(self.player('A'),'<p>A</p>')])
 def test_list_relative_fences_keep_literal_video_examples_inside_code(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  literal='[Literal video example](https://youtu.be/aaaaaaaaaaa)'
  source='- Example\n    ~~~~markdown\n  ~~~\n  '+literal+'\n    ~~~~~'
  self.assertEqual(list(publication_markdown_blocks([source])),[('text','Example'),('code','~~~\n'+literal)])
  item,html=self.fixture();item['payload']['body_lines']=[source]
  validate_live_html(item,(html.split('<figure',1)[0]+'<ul><li>Example<pre>~~~\n'+literal+'</pre></li></ul>').encode())
 def test_deep_indentation_does_not_turn_literal_fences_into_openers(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  source='- Example\n      ```python\n      Literal continuation text.'
  self.assertEqual(list(publication_markdown_blocks([source])),[('text','Example ```python Literal continuation text.')])

 def test_dedented_headings_end_the_fence_list_container(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  literal='```python\nAn exact literal code example.\n```'
  source='- Required action\n## Next\n    '+literal.replace('\n','\n    ')
  self.assertEqual(list(publication_markdown_blocks([source])),[('text','Required action'),('text','Next'),('code',literal)])

 def test_loose_list_video_paragraphs_use_relative_indentation(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  link='[A](https://youtu.be/aaaaaaaaaaa)'
  for marker,base in [('- ',2),('* ',2),('+ ',2),('1. ',3),('10) ',4),('  - ',4),('-\t',4)]:
   for extra in range(4):
    with self.subTest(marker=marker,extra=extra):
     source=marker+'See below\n\n'+' '*(base+extra)+link
     self.assertEqual(list(publication_markdown_blocks([source])),[('text','See below'),('paragraph',link)])
     item,html=self.fixture();item['payload']['body_lines']=[source]
     good=html.split('<figure',1)[0]+'<ul><li><p>See below</p>'+self.player('A')+'</li></ul>'
     validate_live_html(item,good.encode())
     self.reject(item,[good.replace(self.player('A'),'<p><a href="https://youtu.be/aaaaaaaaaaa">A</a></p>')])
 def test_loose_list_indented_code_uses_relative_four_columns(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  literal='[Literal code example](https://youtu.be/aaaaaaaaaaa)'
  for marker,base in [('- ',2),('1. ',3),('10) ',4),('  - ',4)]:
   for extra in [4,5]:
    source=marker+'See below\n\n'+' '*(base+extra)+literal+'\n'+' '*(base+extra)+'More literal code.'
    blocks=list(publication_markdown_blocks([source]))
    self.assertEqual(blocks,[('text','See below'),('code',' '*(extra-4)+literal+'\n'+' '*(extra-4)+'More literal code.')])
    item,html=self.fixture();item['payload']['body_lines']=[source]
    validate_live_html(item,(html.split('<figure',1)[0]+'<ul><li>See below<pre>'+literal+'\nMore literal code.</pre></li></ul>').encode())
 def test_non_one_ordered_markers_cannot_interrupt_prose(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  prose='Forecast summary remains unchanged.'
  for number in ['2','2026','0002']:
   for delimiter in ['.',')']:
    for indent in ['', ' ', '   ']:
     with self.subTest(number=number,delimiter=delimiter,indent=repr(indent)):
      tail=number+delimiter+' Revenue must remain visible'
      source=prose+'\n'+indent+tail
      self.assertEqual(list(publication_markdown_blocks([source])),[('paragraph',prose+' '+tail)])
      item,html=self.fixture();item['payload']['body_lines']=[source]
      good=html.split('<figure',1)[0]+'<p>'+prose+' '+tail+'</p>'
      validate_live_html(item,good.encode())
      self.reject(item,[good.replace(number+delimiter+' ','')])
 def test_ordered_list_starts_and_siblings_remain_supported(self):
  from abvx_harness.publication_learning import publication_markdown_blocks
  prose='Forecast summary remains unchanged.'
  for delimiter in ['.',')']:
   for number in ['1','2','2026']:
    source=prose+'\n\n'+number+delimiter+' Go\n'+str(int(number)+1)+delimiter+' Stop'
    self.assertEqual(list(publication_markdown_blocks([source])),[('paragraph',prose),('text','Go'),('text','Stop')])
   self.assertEqual(list(publication_markdown_blocks([prose+'\n1'+delimiter+' Go'])),[('paragraph',prose),('text','Go')])
   source='- Required action\n  2026'+delimiter+' Revenue stays'
   self.assertEqual(list(publication_markdown_blocks([source])),[('text','Required action 2026'+delimiter+' Revenue stays')])
  self.assertEqual(list(publication_markdown_blocks(['1. Required action\n2) Keep delimiter'])),[('text','Required action 2) Keep delimiter')])
  self.assertEqual(list(publication_markdown_blocks([prose+'\n1234567890. Keep number'])),[('paragraph',prose+' 1234567890. Keep number')])
 def test_self_closing_nonvoid_containers_keep_content_hidden(self):
  item,html=self.fixture();prefix,body=html.split('<h1>',1)
  for tag,attrs in [('template',''),('div',' hidden'),('div',' inert'),('details',''),('dialog','')]:
   for leading in ['', '<head>']:
    with self.subTest(tag=tag,attrs=attrs,leading=leading):
     self.reject(item,[prefix+leading+f'<{tag}{attrs}/><body><h1>'+body])
 def test_explicit_nonvoid_closures_and_self_closing_voids_restore_evidence(self):
  item,html=self.fixture();prefix,body=html.split('<h1>',1)
  for leading in ['<head><template/></template><body>', '<template/></template>', '<div hidden/></div>', '<img src="unused"/>', '<br/>']:
   validate_live_html(item,(prefix+leading+'<h1>'+body).encode())

 def test_inline_html_in_short_headings_and_list_items_matches_rendered_text(self):
  for marker in ['## ', '###### ', '- ', '+ ', '1. ']:
   for source,rendered in [('<em>Go</em>','<em>Go</em>'),('Go <!-- note -->','Go <!-- note -->'),('<span class="editorial-label">Go</span>','<span class="editorial-label">Go</span>'),('Go<!-- private note --> now','Go<!-- private note --> now')]:
    with self.subTest(marker=marker,source=source):
     item,html=self.fixture();item['payload']['body_lines']=[marker+source]
     good=html.split('<figure',1)[0]+'<h2>'+rendered+'</h2>'
     validate_live_html(item,good.encode());self.reject(item,[good.replace('Go','')])
 def test_inline_comments_and_hidden_html_do_not_require_invisible_words(self):
  item,html=self.fixture();item['payload']['body_lines']=['An original paragraph that must remain verified.','## Go <!-- editorial note -->','- Now <span hidden>private draft</span>']
  good=html+'<h2>Go</h2><ul><li>Now</li></ul>'
  validate_live_html(item,good.encode());self.reject(item,[good.replace('>Now<','><'),good.replace('>Go<','><')])
 def test_literal_html_in_code_and_escaped_text_is_still_required(self):
  import html as html_module
  for marker in ['## ', '- ', '']:
   for literal in ['<em>Required wording</em>','<!-- required literal note -->']:
    for source in ['`'+literal+'`','``'+literal+'``',html_module.escape(literal)]:
     with self.subTest(marker=marker,source=source):
      item,html=self.fixture();item['payload']['body_lines']=[marker+source]
      good=html.split('<figure',1)[0]+'<p>'+html_module.escape(literal)+'</p>'
      validate_live_html(item,good.encode());self.reject(item,[html.split('<figure',1)[0]+'<p>Required wording</p>'])
 def test_self_closing_foreign_elements_do_not_capture_real_players(self):
  for foreign in ['<svg/>','<math/>','<svg><path/></svg>','<math><mi/></math>','<svg><iframe/></svg>','<svg><foreignObject><svg/></foreignObject></svg>']:
   with self.subTest(foreign=foreign):
    item,html=self.fixture()
    good=html.replace('<figure class="youtube-figure">','<figure class="youtube-figure">'+foreign)
    validate_live_html(item,good.encode());self.reject(item,[good.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc')])
 def test_foreign_integration_points_keep_html_templates_inert(self):
  for wrapper in ['<svg><foreignObject>','<svg><desc>','<math><mtext>','<math><annotation-xml encoding="text/html">']:
   item,html=self.fixture();prefix,body=html.split('<h1>',1)
   self.reject(item,[prefix+wrapper+'<template/><h1>'+body])
 def test_foreign_elements_cannot_claim_html_player_structure(self):
  item,html=self.fixture()
  self.reject(item,[html.replace(self.player(),'<svg>'+self.player()+'</svg>'),html.replace(self.player(),'<math>'+self.player()+'</math>')])

 def test_inline_code_boundaries_and_block_code_preserve_literal_html(self):
  item,html=self.fixture();item['payload']['body_lines']=['## `<em>Required wording</em>`now']
  good=html.split('<figure',1)[0]+'<h2><code>&lt;em&gt;Required wording&lt;/em&gt;</code>now</h2>'
  validate_live_html(item,good.encode());self.reject(item,[good.replace('&lt;em&gt;','')])
  for source in ['```html\n<em>Required wording</em>\n```','    <em>Required wording</em>']:
   item['payload']['body_lines']=[source]
   good=html.split('<figure',1)[0]+'<pre>&lt;em&gt;Required wording&lt;/em&gt;</pre>'
   validate_live_html(item,good.encode());self.reject(item,[good.replace('&lt;em&gt;','')])
 def test_foreign_integration_points_allow_real_html_players(self):
  for opening,closing in [('<svg><foreignObject>','</foreignObject></svg>'),('<math><mtext>','</mtext></math>'),('<math><annotation-xml encoding="application/xhtml+xml">','</annotation-xml></math>')]:
   item,html=self.fixture()
   good=html.replace(self.player(),opening+self.player()+closing)
   validate_live_html(item,good.encode());self.reject(item,[good.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc')])

 def test_trailing_comments_never_remove_standalone_video_proof(self):
  prose='An original paragraph that must remain verified.'
  for suffix in [' <!-- editorial -->','<!-- first --><!-- second -->',' \n<!-- editorial -->']:
   item,html=self.fixture();item['payload']['body_lines']=[prose+'\n\n[A](https://youtu.be/aaaaaaaaaaa)'+suffix]
   good=html.replace('Example A launch video','A');validate_live_html(item,good.encode())
   self.reject(item,[good.replace(self.player('A'),'<p>A</p>'),good.replace(self.player('A'),'')])
 def test_markdown_autolinks_remain_required_visible_text(self):
  prose='An original paragraph that must remain verified.'
  for marker in ['## ','- ']:
   for address in ['https://example.com','mailto:test@example.com','test@example.com','custom:required-value']:
    item,html=self.fixture();item['payload']['body_lines']=[prose,marker+'<'+address+'>']
    good=html+'<h2><a href="'+address+'">'+address+'</a></h2>'
    validate_live_html(item,good.encode());self.reject(item,[html])
 def test_duplicate_namespace_encoding_cannot_qualify_a_foreign_player(self):
  item,html=self.fixture()
  for attrs in ['encoding="application/xml" encoding="text/html"','encoding="text/html" encoding="application/xml"']:
   bad=html.replace(self.player(),'<math><annotation-xml '+attrs+'>'+self.player()+'</annotation-xml></math>')
   self.reject(item,[bad])
 def test_block_starts_implicitly_close_html_paragraphs(self):
  item,html=self.fixture()
  for paragraph in ['<p hidden/>','<p hidden><em>','<p aria-hidden="true">']:
   good=html.replace(self.player(),paragraph+self.player())
   validate_live_html(item,good.encode());self.reject(item,[good.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc')])
  self.reject(item,[html.replace(self.player(),'<p hidden><template/>'+self.player())])

 def test_short_paragraphs_after_headings_and_fences_remain_required(self):
  prose='An original paragraph that must remain verified.'
  for boundary,rendered in [('## Warning','<h2>Warning</h2>'),('```text\nCode example remains visible.\n```','<pre>Code example remains visible.</pre>')]:
   item,html=self.fixture();item['payload']['body_lines']=[prose+'\n'+boundary+'\nGo']
   good=html+rendered+'<p>Go</p>';validate_live_html(item,good.encode());self.reject(item,[html+rendered])
 def test_text_blocks_require_source_order_and_each_occurrence(self):
  prose='An original paragraph that must remain verified.'
  item,html=self.fixture();item['payload']['body_lines']=[prose+'\n\n- Repeat important action\n- Repeat important action\n- Final required instruction']
  good=html+'<ul><li>Repeat important action</li><li>Repeat important action</li><li>Final required instruction</li></ul>'
  validate_live_html(item,good.encode())
  self.reject(item,[good.replace('<li>Repeat important action</li>','',1),html+'<ul><li>Final required instruction</li><li>Repeat important action</li><li>Repeat important action</li></ul>'])
 def test_minimized_list_items_close_prior_hidden_paragraphs_and_items(self):
  item,html=self.fixture();item['payload']['body_lines']=['- Required']
  for good in ['<ul><li><p hidden/><li>Required</ul>','<ul><li hidden><p/><li>Required</ul>','<dl><dt><p hidden/><dd>Required</dl>','<dl><dd hidden><p/><dt>Required</dl>']:
   validate_live_html(item,(html+good).encode());self.reject(item,[html+good.replace('Required','')])
 def test_html_breakout_tags_restore_namespace_outside_foreign_content(self):
  item,html=self.fixture()
  for foreign in ['<svg>','<math>','<svg><g>']:
   for opening,closing in [('<div>','</div>'),('<p>','</p>'),('<table><tr><td>','</td></tr></table>')]:
    good=html.replace(self.player(),foreign+opening+self.player()+closing)
    validate_live_html(item,good.encode());self.reject(item,[good.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc')])

 def test_leading_comments_cannot_replace_standalone_video_proof(self):
  prose='An original paragraph that must remain verified.'
  for prefix in ['<!-- editorial --> ', '<!-- first --><!-- second --> ', '<!-- editorial\n note --> ']:
   item,html=self.fixture();item['payload']['body_lines']=[prose+'\n\n'+prefix+'[A](https://youtu.be/aaaaaaaaaaa)']
   good=html.replace('Example A launch video','A');validate_live_html(item,good.encode());self.reject(item,[good.replace(self.player('A'),'<p>A</p>')])
 def test_reference_definitions_are_invisible_but_their_labels_remain_required(self):
  prose='An original paragraph that must remain verified.'
  for usage in ['[Go][x]','[Go][X]','[Go][]','[Go]']:
   key='Go' if usage in ('[Go][]','[Go]') else 'x'
   item,html=self.fixture();item['payload']['body_lines']=[prose,'## '+usage,'['+key+']: /a']
   good=html+'<h2><a href="/a">Go</a></h2>';validate_live_html(item,good.encode());self.reject(item,[html])
 def test_new_heading_implicitly_closes_a_self_closing_html_heading(self):
  item,html=self.fixture()
  for first in ['h1','h2','h6']:
   validate_live_html(item,html.replace('<h1>',f'<{first} hidden/><h1>',1).encode())
  self.reject(item,[html.replace('<h1>','<template/><h1 hidden/><h1>',1)])
 def test_ignored_select_markup_cannot_qualify_a_player(self):
  item,html=self.fixture()
  self.reject(item,[html.replace(self.player(),'<select><p hidden>'+self.player()+'</select>'),html.replace(self.player(),'<select>'+self.player()+'</select>')])
  good=html.replace(self.player(),'<select><option>Choice</select>'+self.player());validate_live_html(item,good.encode())

 def test_reference_examples_inside_code_remain_literal(self):
  item,html=self.fixture();item['payload']['body_lines']=['## `[Go][x]`','[x]: /a']
  good=html+'<h2><code>[Go][x]</code></h2>';validate_live_html(item,good.encode());self.reject(item,[html+'<h2>Go</h2>'])
  item['payload']['body_lines']=['```markdown\n[Required code reference]: /a\n```'];validate_live_html(item,(html+'<pre>[Required code reference]: /a</pre>').encode())
 def test_ignored_select_tokens_do_not_invalidate_a_real_sibling_player(self):
  item,html=self.fixture();good=html.replace('<figure class="youtube-figure">','<figure class="youtube-figure"><select><iframe/><option>Choice</select>')
  validate_live_html(item,good.encode());self.reject(item,[good.replace('/embed/aaaaaaaaaaa','/embed/ccccccccccc')])

 def test_multiline_reference_definition_titles_are_not_visible_prose(self):
  prose='An original paragraph that must remain verified.'
  for title in [' "Short"', " 'Short'", ' (Short)', ' "Long title\ncontinued"']:
   item,html=self.fixture();item['payload']['body_lines']=[prose,'## [Go][x]','[x]: /a\n'+title]
   good=html+'<h2><a href="/a" title="title">Go</a></h2>';validate_live_html(item,good.encode());self.reject(item,[html])
 def test_resolved_shortcut_reference_images_do_not_require_alt_prose(self):
  item,html=self.fixture();prose='An original paragraph that must remain verified.'
  item['payload']['body_lines']=[prose,'![Go]','[Go]: /image']
  validate_live_html(item,(html+'<img src="/image" alt="Go">').encode())
  item['payload']['body_lines']=[prose,'![Undefined]','[Go]: /image'];self.reject(item,[html])
 def test_escaped_opening_backticks_are_not_code_spans(self):
  item,html=self.fixture()
  for source in [r'\`<em>Go</em>\`',r'\`<em>Go</em>`']:
   item['payload']['body_lines']=['## '+source];good=html+'<h2>`<em>Go</em>`</h2>';validate_live_html(item,good.encode());self.reject(item,[html])
  for source in [r'\\`<em>Go</em>`',r'`<em>Go</em>\`']:
   item['payload']['body_lines']=['## '+source];good=html+'<h2><code>&lt;em&gt;Go&lt;/em&gt;</code></h2>';validate_live_html(item,good.encode());self.reject(item,[html+'<h2>Go</h2>'])

 def test_escaped_reference_markup_keeps_its_visible_words(self):
  item,html=self.fixture();prose='An original paragraph that must remain verified.'
  for source,visible in [(r'\![Go]','!Go'),(r'\![Go][x]','!Go'),(r'\[Go][x]','[Go][x]')]:
   item['payload']['body_lines']=[prose,source,'[Go]: /image\n[x]: /a'];good=html+'<p>'+visible+'</p>'
   validate_live_html(item,good.encode());self.reject(item,[html])

 def test_invalid_reference_destinations_remain_required_visible_text(self):
  item,html=self.fixture()
  for source in ['[important-label]: /required-visible-text(foo','[important-label]: /required-visible-text)foo','[important-label]: <required<visible>']:
   item['payload']['body_lines']=['An original paragraph that must remain verified.',source]
   self.reject(item,[html])
  item['payload']['body_lines']=['An original paragraph that must remain verified.','[important-label]: /required-visible-text(foo']
  validate_live_html(item,(html+'<p>[important-label]: /required-visible-text(foo</p>').encode())
 def test_balanced_escaped_and_angle_reference_destinations_stay_invisible(self):
  item,html=self.fixture()
  for destination in ['/a(b(c)d)e',r'/a\(b',r'/a\)b','<a b>','<>']:
   item['payload']['body_lines']=['[Go][x]','[x]: '+destination]
   validate_live_html(item,(html+'<p><a>Go</a></p>').encode())
 def test_reference_destinations_can_start_on_the_next_line(self):
  item,html=self.fixture()
  for definition in ['[x]:\n/a','[x]:\n  /a\n  "Short"','[x]:\n/a "Short"','[x]:\n/a\n "Long\n title"']:
   item['payload']['body_lines']=['[Go][x]',definition]
   validate_live_html(item,(html+'<p><a>Go</a></p>').encode())
   self.reject(item,[html])
 def test_backslash_escaped_html_delimiters_keep_visible_tag_names(self):
  item,html=self.fixture()
  for source in [r'## \<em>Go\</em>',r'- \<em>Go\</em>']:
   item['payload']['body_lines']=['An original paragraph that must remain verified.',source]
   validate_live_html(item,(html+'<h2>&lt;em&gt;Go&lt;/em&gt;</h2>').encode())
   self.reject(item,[html+'<h2>Go</h2>'])
 def test_character_references_are_decoded_exactly_once(self):
  item,html=self.fixture()
  for source,rendered in [('## &amp;copy;','&amp;copy;'),('- &amp;lt;em&amp;gt;','&amp;lt;em&amp;gt;'),('## `&copy;`','&amp;copy;')]:
   item['payload']['body_lines']=['An original paragraph that must remain verified.',source]
   validate_live_html(item,(html+'<h2>'+rendered+'</h2>').encode())
   self.reject(item,[html])

 def test_inline_links_allow_balanced_and_escaped_destinations(self):
  item,html=self.fixture()
  for source in ['## [Go](/a(b)c)',r'- [Go](/a\(b\)c)','## [Go](</a(b)c>)','## [Go](/a(b)c "Optional title")']:
   item['payload']['body_lines']=[source];good=html+'<h2><a href="/a(b)c">Go</a></h2>'
   validate_live_html(item,good.encode());self.reject(item,[html])
 def test_reference_labels_allow_escaped_closing_brackets(self):
  item,html=self.fixture()
  for label in [r'x\]',r'x\\\]',r'x\[y\]']:
   item['payload']['body_lines']=['[Go]['+label+']','['+label+']: /a']
   validate_live_html(item,(html+'<p><a href="/a">Go</a></p>').encode());self.reject(item,[html])

 def test_literal_code_keeps_balanced_link_destinations_visible(self):
  item,html=self.fixture();item['payload']['body_lines']=['## `[Go](/required-path(foo)tail)`']
  good=html+'<h2><code>[Go](/required-path(foo)tail)</code></h2>'
  validate_live_html(item,good.encode());self.reject(item,[html+'<h2>Go</h2>',good.replace('/required-path(foo)tail','/other-path')])
