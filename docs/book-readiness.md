# Book Readiness Radar MVP

Local operational reporting under the existing `book-radar` CLI. No public page,
new dashboard, database, scheduler, dependency, manuscript generation or KDP action.

## Baseline and ownership

Sources are ABVXsite native Writing and Working Stories JSON-frontmatter Markdown,
its deployment content index, existing OS intakes, prepared Psychology Notebook posts
and the existing sketchbook artwork registry. External platform titles are not treated
as full manuscripts. Book metadata, source sessions, existing book selection and source
asset references remain linked; no article or publication metadata is rewritten.

The inventory is `.tmp/book-readiness/state.json`; the readable projection is
`.tmp/book-readiness/report.md`. Both are ignored. The state also retains source-bound
editorial assessments and notification delivery receipts: preserve it, not just the
regenerable article metrics. Owner rights declarations stay in the ignored
`.tmp/book-readiness/owner-claims.json`. Unknown rights remain UNKNOWN; explicit owner
confirmation of the psychology source archive and existing sketchbook originals is
retained separately from permission to produce a new book.

The existing psychology book is
https://abvx.xyz/books/fragments-from-a-therapists-notebook.
A shared archive does not establish which fragments appeared in that book. Known
matches and unresolved overlap remain separate from rights and editorial volume.

## Commands

```sh
./bin/abvx book-radar readiness refresh --site-root /absolute/ABVXsite
./bin/abvx book-radar readiness report
./bin/abvx book-radar readiness report --json
./bin/abvx book-radar readiness review --if-due
./bin/abvx book-radar readiness ack MILESTONE_ID
```

The source root is remembered after the first explicit refresh. Source-root changes
fail closed. `review --if-due` refreshes quantities on every call; the deeper local
analysis of topic diversity, overlap and gaps runs after 30 days. Unchanged source
metrics and unchanged monthly candidate analyses are reused. No model or market
request is launched. Lexical topic analysis is not a human assessment of literary
quality or chapter cohesion.

After a verified native publication or update, the existing OS `publication complete`
and `complete-cycle` commands refresh the projection. It runs after the successful
publication receipt, and failure is isolated: old inventory remains intact and
`last-error.json` records the problem. Site releases made outside this existing OS
closeout are discovered at the next refresh/monthly check; no deployment webhook or
second release mechanism is installed.

The existing Monday Multi-Market Radar heartbeat calls `review --if-due`, so the
monthly review occurs on the first normal weekly run after the 30-day boundary,
without another scheduler. Quiet while unchanged; notify only new milestones,
regressions or actionable failures. After actually delivering a milestone, call
`ack ID`; this acknowledges delivery, never book production approval.

## Counts and estimates

Canonical articles are keyed once per URL. Exact body duplicates and substantial
identical paragraphs do not increase a proposed book's unique manuscript volume.
The same article may legitimately appear in two alternative book directions; their
word totals must not be added together as independent inventory. Drafts, non-English
material, excluded book selections and missing assets remain visible separately.
English word counts use declared-English Latin-script prose, omit frontmatter,
URLs, code and Markdown markup, and are planning metrics rather than editorial
copyediting counts. Recipe instructions duplicated in metadata are not counted again.

Visual counts are unique available asset hashes. Source assets, proven originals,
web-publication approval and book-republication rights are distinct evidence.
Artwork inventory can include private prepared derivatives as available material;
its published and draft counts must not be summed again on top of available entries.

Density assumptions in `book-radar/readiness-policy.json`: prose 250–350 words/page;
illustrated prose 180–260 words/page plus 0.5–1 pages per available visual, and 8–16
front matter pages. Ranges round outward to four-page blocks. These are uncertain
planning scenarios, not an actual trim size, image-resolution/print-quality review,
validated pagination or an Amazon minimum. Kitchen targets are 120–180 pages;
Working Stories is 120–200. Art uses a provisional 48–96-page planning reference.

## Milestones and editorial gates

All targets are configurable editorial references, never requests to write to quotas.
Defaults for `outline_ready` are recipe 6 substantial entries/6,000 words/3 topics;
culinary stories 8/10,000/3; professional cases 6/10,000/3; psychology 6/6,000/3;
art 12 available works and an inventory theme. A substantial prose entry has at least
150 counted words. Art is evaluated as visual material, not zero-word prose.

`manuscript_candidate` additionally requires the configured entry/word/diversity and
visual coverage references, estimated pagination overlapping the planning range,
confirmed republication rights for text and the planned visual coverage, and **current-source** editorial confirmation of cohesion and resolved gaps. Recipe
reference: 24 entries/24,000 words; stories: 20/30,000; cases: 16/36,000. More volume
alone does not promote a book. `editorial_review` requires explicit acceptance of
that source-bound candidate for editorial review. None of these stages approves
production. Psychology remains a thematic inventory with rights-confirmed counts;
a new-volume proposal also needs an existing-book overlap decision.

Record a human/editorial assessment with
`readiness assess CANDIDATE --file RECEIPT.json`, then refresh. The receipt needs the
current report's `member_digest`, `cohesion` (`confirmed` or `pending`), an `evidence`
reference, and optional boolean `gaps_resolved`/`accepted_for_editorial_review`.
Changed source hashes invalidate the assessment. Article-specific exclusions or
rights receipts can be configured in `article_annotations`; a rights-clearance entry
requires the exact article `source_hash` and evidence. `visual_rights: "cleared"` records a separate source-bound visual permission. No inference from publication
alone clears book rights.

New cross-collection candidate hypotheses can emerge from configured topic families;
the default checks AI/ChatGPT/Gemini/automation with at least four substantial entries
across two collections. Such overlap is a possible direction, not a cohesive book.

Transitions retain their first **observed** timestamp, not an invented historical
crossing date. Delivered candidate/stage thresholds are not announced again, including
a later recrossing. Notification receipts grant no editorial or publishing authority.

## Multi-Market boundary and validation

`book-radar report markets` and `report weekly` expose
`book_readiness_research_queue` from `outline_ready` onward. Market assessment no
longer waits for complete manuscripts, target pagination, cleared unknown rights or
confirmed cohesion. Those remain explicit editorial/production conditions; their
gates are unchanged. Rights-blocked and editorially excluded source items are not
proposed as usable material. Inventory-only Psychology stays withheld until the
existing-book overlap decision; archive volume alone never proves a new volume.

`research_handoff` returns source dates, absolute report/inventory references,
material/source hashes, source article URLs, usable members and unresolved gaps.
Stable IDs are `readiness:<candidate_id>`. `material_review_digest` changes when
content or relevant editorial/rights context changes, not merely on recapture.
`CURRENT`, `RETAINED_REFRESH_REQUIRED`, `FUTURE_EXCLUDED`, `UNAVAILABLE`, `BLOCKED`
and `REFRESH_BLOCKED` are distinct. A failed refresh cannot promote a retained
same-day snapshot as newly verified; one handoff snapshot is shared by the loader
and both report renderings. Missing or corrupt inventory is not an empty archive. No future
inventory is attached to a historical report.

The existing `weekly_book_review` merges current early material leads into the same
bounded commercial research queue, even without an external discovery manifest.
No opportunity or commercial PASS is created. An existing archive card must retain
`readiness_ref.material_review_digest` from the current handoff; absent, stale or
changed material invalidates its commercial review only in the derived projection.
Historical menus and decisions remain unchanged. Queue-cap deferrals are explicit.
The researcher selects a coherent subset, states a reader/purchase reason and checks
external demand and competitor content before any owner recommendation. Available
material is a production advantage, never evidence of paid demand.

The Multi-Market runner now passes the main repository as `readiness_root` instead
of silently reading its empty isolated market import folder. It freezes
`book-readiness.json` and carries the source-bound queue into `markets.json`,
`weekly.json`, `book-discovery.json` and the readable `weekly.md`. On actual current
dates it refreshes the remembered source root; historical replays do not recapture
current files under old dates. The Monday agent must inspect the readiness report
before market acquisition, not only after completing external research.

Personal/portfolio value, editorial readiness and commercial potential remain
separate; commercial potential starts `NOT_ASSESSED`. Archive leads compete for the
same one or two owner recommendations; they do not reserve a publication slot,
launch research themselves, authorize production or require a second scheduler.

Focused tests: `PYTHONPATH=src python3 -m unittest discover -s tests -p test_book_readiness.py -q`.
Publication regression tests exercise the existing closeout contracts. Generated
reports, manuscript comparison evidence, author text and originals stay private.

## Owner-supplied existing-book manuscript comparison

```sh
./bin/abvx book-radar readiness compare-book --file /absolute/DIGITAL_BOOK_BLOCK --book-url https://abvx.xyz/books/fragments-from-a-therapists-notebook
./bin/abvx book-radar readiness refresh
```

The bounded reader accepts DOCX or a Kindle Create ZIP containing one DOCX. It reads
only Word document text; active resources and the Kindle database are not executed.
An unchanged, hashed DOCX copy and the comparison stay under `.tmp/book-readiness/`.
The source files and manuscript are never edited. This compares the supplied DOCX,
not a downloaded current Amazon edition. No print pagination is inferred.

`existing-book-overlap.md` retains quote pairs and Word paragraph identifiers.
Normalized exact token-sequence matches, lexical near matches for review (>=0.70),
not-matched text and very short unresolved fragments are separate outcomes. Lack of
an exact match is not proof of novelty, especially across translations/paraphrases.
The inventory only accepts comparison records bound to the current article hash;
changing the post invalidates its old comparison. The default psychology direction
remains an inventory until the edition/fragment overlap is reviewed.
