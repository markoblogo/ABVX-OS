# Jekyll full production plan V2

## Evidence basis

- Real V7 primary regression: 40/40 completed, zero retries, low reasoning, 3000-token default.
- Targeted second pass: 5/5 completed, 2 FIXED and 3 IMPROVED_BUT_REVIEW; 0 NOT_FIXED, 0 REGRESSED.
- Current measured sample classification after repair: 15 PASS, 25 PASS_WITH_REVIEW, 0 SECOND_PASS_REQUIRED, 0 CRITICAL_FAIL.
- Projected source: approximately 561 blocks for 25,622 English words.

## Pipeline

1. Primary translation with `gpt-5.6-sol`, low reasoning, 3000 tokens, sequential checkpointing and source-hash resume.
2. Mechanical output validation: status, incomplete details, visible output, translation field, stable IDs, source hashes.
3. Automatic risk QA: alignment, names, profile vocabulary, knowledge state, document/speech act, spoiler boundaries.
4. Targeted second pass only for material semantic defects, bounded to low/3000 with one 5000 max-token retry.
5. Chapter-level literary/editorial review of risk-flagged blocks and surrounding prose. Review is not required to regenerate every PASS_WITH_REVIEW block through the API.
6. Human final review before layout.
7. Sitelen conversion and 6×9 B&W layout only after prose freeze, followed by print/EPUB QA.

## Economics and review burden

Projected primary calls: ~561. Measured token projection: ~1.59M input, ~166k output, ~101k reasoning tokens. The sample's targeted repair rate projects to roughly 70 second-pass candidates, but chapter-level editorial grouping should reduce actual API rework. Dollar cost is intentionally not estimated without a current verified price source.

## Gates

No block with incomplete/empty output enters QA. No full-book release is allowed until source/output alignment, names/profile, knowledge/spoiler, literary review, and final human approval pass. Full sitelen generation remains downstream of prose approval.
