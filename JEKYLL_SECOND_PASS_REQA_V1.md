# Jekyll V7 targeted second-pass semantic re-QA

The five real second-pass calls completed locally with no retries. This review compares source, original V7 translation, recorded defect, and revised output. Provider `NOTES` were not treated as QA evidence.

## Results

- `b0005`: **IMPROVED_BUT_REVIEW** — exactly three months is now represented more clearly and succession remains conditional, but the sentence still needs literary verification for the absence/death alternative.
- `b0013`: **IMPROVED_BUT_REVIEW** — Lanyon remains the speaker and the judgement remains his; the more-than-ten-years cadence is still awkward.
- `b0014`: **FIXED** — Utterson's inference is explicitly marked as possibility/thought; no narrator-fact promotion detected.
- `b0028`: **IMPROVED_BUT_REVIEW** — letter status, signature, benefactor, safety/escape claim and Utterson's reaction are clearer; ordinary literary review remains.
- `b0038`: **FIXED** — Poole's fear and cabinet context remain character-level; the fearful dialogue beat is clearer, with ordinary style editing still appropriate.

Repair counts: FIXED 2/5, IMPROVED_BUT_REVIEW 3/5, NOT_FIXED 0/5, REGRESSED 0/5. Targeted repair success rate: **100%** under the defined rule.

## Updated sample burden

The successor classification is PASS 15, PASS_WITH_REVIEW 25, SECOND_PASS_REQUIRED 0, CRITICAL_FAIL 0. The material semantic repair queue is resolved for this sample. The remaining 25 blocks are ordinary chapter-level literary/editorial review, not automatic provider rewrites.

## Production architecture

**VIABLE:** `gpt-5.6-sol / low / 3000` primary translation → automatic mechanical and risk QA → targeted second pass only for material semantic defects → chapter-level literary editing → human final review → sitelen/layout QA.

Low reasoning is now approved for this Jekyll pipeline. This approval is scoped to Jekyll and is not generalized to all Toki Pona titles. Medium remains rejected as default because it caused output starvation in smoke testing.

## Decision

**GO_FULL_JEKYLL**

This authorizes the next production gate only: prepare and execute the full-book pipeline under the documented architecture. It does not itself start full-book translation in this task.

Machine result: [JEKYLL_SECOND_PASS_REQA_V1.json](JEKYLL_SECOND_PASS_REQA_V1.json).
