# BOOK-FACTORY-004 — Compact BookSpec + Final Shortlist + Three Sample Pages

Status: STOP_FOR_HUMAN_DECISION
Cost class: NORMAL

## 1. Final proposed title / subtitle

- Title: `Your SaaS Bill Is Ridiculous`
- Subtitle: `A Skeptical Guide to Open-Source Tools That Can Replace Expensive SaaS`

These remain strong enough and do not need SEO-driven changes.

## 2. Compact scope decision

This is no longer a 30k+ word encyclopedia project.

Recommended compact shape:

- 24 repositories total
- 20 full-page entries
- 4 `Rabbit Holes` entries
- target around 12k words
- target around 32 PDF pages

This keeps the first real Book Factory case fast, useful and dense.

## 3. Final shortlist logic

Selected shape:

- 18 repositories from the original audited source corpus as `FULL_PAGE`
- 4 repositories from the original source corpus as `RABBIT_HOLE`
- 2 owner repositories added as `FULL_PAGE`
- no extra non-owner additions beyond the original corpus

The final inventory lives in:

- `books/research/your-saas-bill-is-ridiculous-shortlist.tsv`

## 4. Projects removed from the original 33

Removed from the final compact inventory:

- `Continue`
- `Chatterbox TTS`
- `OpenShorts`
- `ViMax`
- `Open SEO`
- `AppFlowy`
- `Baserow`
- `Plane`
- `Anthropic Agent Skills`
- `Awesome Agent Skills`
- `Awesome Copilot`

Reason pattern:

- too overlapping
- too weak as standalone one-page entries
- too immature / too unclear
- or better treated as surrounding context rather than book-core material

## 5. Owner repositories added

- `ABVX Agent Skills`
- `AGENTS.md Generator`

Both survive the editorial test because they address real costs in agent work:

- prompt drift
- repo-instruction drift
- false completion claims
- undocumented agent process

Neither is treated as a SaaS miracle.

## 6. Proposed compact TOC

1. Cover
2. Title / publication information
3. Introduction
4. Agents and development work
5. Search, voice and media shortcuts
6. Automation and business plumbing
7. Infrastructure you will end up operating
8. Rabbit Holes
9. The Catch: Free Software Isn't Free
10. Final note / links

## 7. Design approach

Keep the first edition cheap and clean:

- strong typographic cover
- restrained layout
- compact fact strips
- minimal diagrams/icons if useful
- very selective screenshots only when they genuinely explain a product
- no screenshot soup
- no one-illustration-per-repo plan

## 8. Three representative sample pages

Created under:

- `books/manuscripts/your-saas-bill-is-ridiculous/samples/twenty.md`
- `books/manuscripts/your-saas-bill-is-ridiculous/samples/agent-reach.md`
- `books/manuscripts/your-saas-bill-is-ridiculous/samples/abvx-agent-skills.md`

Purpose split:

- `Twenty` — CRM / business software skepticism
- `Agent-Reach` — agent infrastructure, web access and "free" operational reality
- `ABVX Agent Skills` — owner-project neutrality test

## 9. Voice assessment

Current direction is materially closer to the requested tone:

- concise
- skeptical
- confident
- practical
- occasionally dry

Important: it does not yet prove full-book consistency. It only proves the page pattern can hold real prose without drifting into generic AI filler or founder promotion.

## 10. Remaining research gaps

- final human approval of the shortlist and TOC
- final decision on whether any one removed project should be restored
- cover concept still not written/designed
- sample quality is adequate for review, but not yet proof of full-manuscript consistency
- some non-sample entries still rely on BOOK-FACTORY-003 bounded audit rather than page-level deep review

## 11. Book Factory state

Human-facing state reached:

- `BOOK_SPEC_PROPOSED`
- `SHORTLIST_PROPOSED`
- `SAMPLES_READY`
- `WAITING_FOR_HUMAN`

Schema-compatible repository state is now represented as:

- BookProject `status = WAITING_FOR_HUMAN`
- `lifecycle_stage = BOOK_SPEC`
- manuscript readiness = partial samples only

## 12. Files changed

- `books/projects/your-saas-bill-is-ridiculous.json`
- `books/specs/your-saas-bill-is-ridiculous-spec.json`
- `books/research/your-saas-bill-is-ridiculous-shortlist.tsv`
- `books/manuscripts/your-saas-bill-is-ridiculous/samples/twenty.md`
- `books/manuscripts/your-saas-bill-is-ridiculous/samples/agent-reach.md`
- `books/manuscripts/your-saas-bill-is-ridiculous/samples/abvx-agent-skills.md`
- `docs/audits/book-factory-004-compact-bookspec-shortlist-samples.md`
