# Jekyll real 40-block regression V7

This is a local-only real-provider regression. It uses the exact 40 source blocks from `artifacts/jekyll-toki-pona-regression-v2/source-blocks.json`, stable IDs, source hashes, the existing entity ledger, and OpenAI Responses API.

## Configuration

- model: `gpt-5.6-sol` (override with `JEKYLL_PROVIDER_MODEL`)
- reasoning: `low`
- max output: `3000`; one bounded `5000` retry only for `incomplete / max_output_tokens`
- timeout: 180 seconds
- store: false
- sequential calls; transient timeout/connection/429/5xx errors receive at most two additional attempts

The runner never prints or persists `OPENAI_API_KEY`. Provider NOTES are retained but are not QA evidence.

## Commands on the connected Mac

```sh
cd /Volumes/Work/Work/ABVX-OS
python3 scripts/run_jekyll_openai_regression_v7.py --dry-run
python3 scripts/run_jekyll_openai_regression_v7.py
python3 scripts/run_jekyll_openai_regression_v7.py --resume
```

For one diagnostic block:

```sh
python3 scripts/run_jekyll_openai_regression_v7.py --block 'jekyll-sample-v2:section-002:b0005'
```

`--help` and `--dry-run` make no API calls. Ctrl+C leaves completed block files intact; rerun with `--resume`.

## Artifacts

Results are written under `artifacts/jekyll-toki-pona-real-regression-v7/`:

- `run-manifest.json`
- `blocks/<stable-id>.json` — atomically checkpointed after each block
- `combined-output.json`
- `failures.json`
- `usage-summary.json`

A block is successful only when status is `completed`, `incomplete_details` is null, visible output is non-empty, and a non-empty `TRANSLATION:` field is extracted. Partial output is never passed to QA. Existing successful blocks are skipped only when their source hash matches.

## Scope boundary

V7 does not translate the full Jekyll book, publish anything, use the public translator, use OCC-RAG, or relabel fixtures as real output. After the local run, perform alignment, names, profile, knowledge/spoiler, semantic, literary, and review-burden QA before any full-book decision.
