# Native publication preparation and stage handoff

This is a thin operator shortcut over the existing [learning cycle](PUBLICATION_LEARNING_CYCLE_V1.md), content approval and ABVXsite commands. It grants no approval, Git, merge or deployment authority. Engineering changes finish before the next observed cycle starts.

## Source preparation

Apply the [recurring-defect preflight](PUBLICATION_RECURRENCE_PREVENTION.md) before formatting. In particular, a numbered recipe needs browser proof of visible sequential labels; a syntactically valid list alone is insufficient with the current site styles.

Begin one cycle before formatting. The existing ready JSON-frontmatter `--source` path remains supported. For a supplied H1/body followed by `---` and `### SEO и метаданные для ABVX` (or the English equivalent `SEO and metadata for ABVX`), use:

```sh
./bin/abvx publication begin --run <cycle> --item <item> --trial early-input
python3 scripts/prepare_abvx_publication.py --draft /absolute/draft.txt --id <item> --run <cycle> --cover /absolute/cover.png --image-alt '<reviewed alt>' --supplement /absolute/reviewed.json
```

The supported suffix consists of `**Key:** value` fields: Title, SEO title, Slug, Meta description, Excerpt, Collection, Content type, Topics, Language, Preparation time, Cooking time, Cooling time, Servings and Yield. Unknown or duplicate fields stop preparation. Inspect the normalized article and retained body hash before approval. Preamble and service suffix are excluded; article prose is preserved. Other source formats use the existing reviewed `--source` path, never a guessed conversion.

Supplement JSON accepts only `recipe` and `media`. Recipe ingredients/instructions must be supplied as reviewed structured data; the helper never infers quantities or steps from prose. Yield and Servings are aliases and must agree when both are present; supplied cooling details remain visible timing text. Only existing Kitchen Notes is supported as a collection. PNG dimensions are read without modifying cover bytes; other supported images need reviewed width/height. Media cannot override the generated path. Preparation never approves or publishes.

## Stage handoff

Inspect and approve the item through the existing owner gate, then emit its packet with `content publish`. Start from a clean site branch at the full main SHA. Preview any stage plan first (omit `--execute`):

```sh
python3 scripts/abvx_publication_route.py --run <cycle> --site-root /absolute/site --base <full-sha> --phase local --execute
# Review, commit, push and create the PR through the site's existing process.
python3 scripts/abvx_publication_route.py --run <cycle> --site-root /absolute/site --base <full-sha> --phase preview --pr <number> --execute
# Merge only within the owner's publication authorization; check out its exact clean merge SHA.
python3 scripts/abvx_publication_route.py --run <cycle> --site-root /absolute/site --base <full-sha> --phase production --pr <number> --rework-count <actual-count> --cortex-root /Volumes/Work/Work/CortexABV-private --execute
```

`local` first verifies that the installed Playwright headless browser can launch, before any consumer writes or expensive checks. This uses the actual launch path, so a headless-only installation is supported; it never downloads software automatically. The explicit `check` repair path has the same preflight. Then `local` uses consumer dry-run/write, one prebuild, boundary check, Kitchen Notes export when needed, one release check and import of its hashed receipt. Checks are selected by the site's classifier, never manually omitted. `production` runs readiness then immediately closes the OS cycle. It does not create a deployment.

Every attempt retains timestamps, step durations and logs under the ignored cycle directory. Failed attempts remain in the denominator and do not reset the cycle. A partially failed local phase requires inspection and repair rather than blind replay of writes; `--phase check` explicitly reruns release checks/import after repair. A completed cycle cannot rerun; use `publication transfer` for a pending Cortex return. Do not add step times to the cycle total: stages/closeout clocks may overlap.

The first held-out post is an observed engineering test, not a preregistered formal comparison. Compare preparation and total latency descriptively with comparable workloads; one faster run does not establish causal speedup. Owner effort stays UNKNOWN.
