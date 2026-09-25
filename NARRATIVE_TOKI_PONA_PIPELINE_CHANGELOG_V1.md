# Narrative Toki Pona Pipeline Changelog V1

| Change | Previous behavior | New behavior | Public impact | Internal impact | Coverage | Limitation |
|---|---|---|---|---|---|---|
| Mode separation | One short-form contract | Explicit PUBLIC vs INTERNAL config | 500-character limit preserved | Local batched runner | limit tests | Deployment still external |
| Block orchestration | Whole request assumption | Stable section/paragraph blocks | none | Resume and exact mapping | runner tests | No full-book run |
| Proper names | Canonical words only | Ledger-backed allowlist lane | none | Stable Jekyll names | name tests | Human naming review |
| Knowledge/spoilers | No stored state | Review metadata and bounded checker | none | Flags risky claims | QA artifact | Not literary proof |
| Alignment | Word-level implication | ID/hash/order checks | none | Fail-closed reports | alignment tests | Provider output quality remains separate |
| Recovery | Retry would be ad hoc | Manifest/checkpoint/resume | none | Failed block isolation | interruption test | No distributed worker pool |
