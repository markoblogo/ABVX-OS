# Jekyll real 40-block semantic and literary QA V7

## Mechanical alignment

`PASS`: 40 canonical source blocks, 40 unique outputs, exact order, matching SHA-256 source hashes, all statuses `completed`, no failures, no empty translations, and no incomplete details.

## Editorial classification

- PASS: 13 (32.5%)
- PASS_WITH_REVIEW: 22 (55.0%)
- SECOND_PASS_REQUIRED: 5 (12.5%)
- CRITICAL_FAIL: 0

The runner's structural PASS is not treated as editorial PASS. The 5-block second-pass queue is `b0005`, `b0013`, `b0014`, `b0028`, and `b0038`. V7 outputs remain immutable.

## Gate findings

- Spoiler control: `PASS`; no premature Jekyll/Hyde identity disclosure was detected.
- Name QA: `REVIEW`; core Jekyll/Hyde/Utterson/Lanyon/Poole forms are consistent, but Edward/Damon/Pythias handling needs policy review.
- Profile QA: `REVIEW`; approved name lane is operational, ordinary Toki Pona still needs lexical/editorial review.
- Literary Toki Pona: `WORKABLE`, not publication-ready without risk-based editing.
- Sitelen readiness: `REVIEW`; text remains structurally compatible, but no sitelen generation is authorized.

Fragile areas requiring attention are exact three-month conditional succession (`b0005`), Lanyon's time/opinion cadence (`b0013`), Utterson's focal inference (`b0014`), document-bound letter claims (`b0028`), and Poole's fear rhythm (`b0038`).

## Low versus medium

The low V7 run is operationally superior: 40/40 completed with zero retries. Medium smoke produced starvation on two of five blocks. Low preserves the key boundaries in the smoke comparison, but is not accepted as linguistically final: `b0005` remains ambiguous and the queued blocks need a targeted second pass. Configuration decision: `LOW_WITH_SECOND_PASS`.

## Full-book projection

The sample contains 1,826 English words / 40 blocks = 45.65 words per block. At 25,622 words this projects to approximately 561 blocks and 561 primary calls. Measured per-block usage projects to approximately 1,590,140 input tokens, 166,070 output tokens, and 101,120 reasoning tokens. Expected second-pass calls are about 70; ordinary editorial-review blocks about 379. These are token projections, not dollar estimates.

## Decision

`TUNE_AND_RERUN`.

The provider is viable, but the second-pass queue and 67.5% editorial-review burden are too material to authorize full-book translation immediately. Run the bounded queue first, then reassess. No full book or sitelen book was generated.

Machine artifact: [semantic-qa.json](artifacts/jekyll-toki-pona-real-regression-v7/semantic-qa.json).
