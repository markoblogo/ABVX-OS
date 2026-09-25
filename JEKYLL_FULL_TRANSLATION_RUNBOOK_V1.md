# Jekyll full translation V1 runbook

## Preflight result

- canonical normalized source: PASS
- normalized source words: 25,622
- chapters: 10
- deterministic blocks: 462
- average words/block: 55.46
- source hashes and stable IDs: PASS
- entity ledger: PASS (loaded and included in every prompt)
- spoiler metadata: PASS (knowledge boundary constraint attached to identity-sensitive blocks)
- dry run: PASS

The actual segmentation is 462 blocks, not the earlier 561 projection. No artificial padding was added.

## Local commands

```sh
cd /Volumes/Work/Work/ABVX-OS
python3 scripts/run_jekyll_full_translation_v1.py --dry-run
python3 scripts/run_jekyll_full_translation_v1.py
python3 scripts/run_jekyll_full_translation_v1.py --resume
```

Optional bounded diagnostics:

```sh
python3 scripts/run_jekyll_full_translation_v1.py --chapter 1
python3 scripts/run_jekyll_full_translation_v1.py --block 'jekyll-full-v1:chapter-01:block-0001'
```

## Runtime contract

OpenAI Responses API, `gpt-5.6-sol`, low reasoning, 3000 output tokens, `store=false`, sequential calls, and `OPENAI_API_KEY` from the environment. A single 5000-token retry is used only for `incomplete/max_output_tokens`. Partial or empty output never succeeds. Atomic block files make Ctrl+C and `--resume` safe.

## Artifacts and gates

The runner writes `artifacts/jekyll-toki-pona-full-v1/` with source/segmentation/run manifests, block checkpoints, combined output, failures, and usage summary. This task does not execute the 462 API calls from Codex, does not generate sitelen, and does not build PDF/EPUB. After local completion: full risk QA → targeted second pass → chapter-level editorial review → human review → prose freeze.
