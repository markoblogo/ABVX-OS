# ABVX publication learning cycle v1

Owner-approved NORMAL thin adapter within OS ↔ Cortex scope. Reuses content approval, project checks and private admission/retrieval. No scheduler, new model or publication executor.

## Working cycle

1. `scripts/prepare_abvx_publication.py` prepares supplied native Markdown. A ready Writing or Working Story intake automatically starts an ignored `.tmp/publication-learning/<id>/session.json`. Tracked test fixtures are SYNTHETIC; completed IDs or changed workloads require a new intake ID.
2. Inspect and approve with the existing owner gate. `content publish` emits the project handoff; it does **not** declare production success. Apply, commit, PR and deploy using ABVXsite's own mechanism and permissions.
3. `publication check` invokes the existing site `content:release-check` once, or imports its complete hashed receipt with `--reuse-checks`. This retains content/ecosystem validation, lint, sync/vector tests, build, SEO checks and dependency audit, binding log hashes to the exact site tree and approval. A changed source tree requires another check.
4. `publication complete` checks native source/media, retained check logs, checked tree, HTTPS 200 HTML on `abvx.xyz` without redirects, canonical/title and authored prose. Then it records an immutable outcome and exports the numeric batch. Preview, handoff, merge or Vercel notification alone cannot pass. This verifies visible content, not Google's indexing or the deployed SHA.
5. With `--cortex-root`, completion automatically admits the batch, recalls the same workflow/version and generates a model-free diagnosis. OS independently verifies the return against retained source batches. If Cortex is unavailable, the local outcome/batch stay available for `publication transfer`. Duplicate successful delivery is idempotent.

The operator/agent performs this closeout during the publishing workflow; the owner does not need to copy telemetry. This covers native Writing articles, video companion articles and Working Stories. RSS-only entries are outside the intake. Books can use reviewed outcomes; their automatic lifecycle hook is a later distinct milestone.

## Operator commands

```sh
python scripts/prepare_abvx_publication.py --source /absolute/post.md --id publication-unique-id --asset /absolute/cover.webp=/media/writing/cover.webp
./bin/abvx content inspect publication-unique-id --json
./bin/abvx content approve publication-unique-id
./bin/abvx content publish publication-unique-id
# Apply with the site's existing publisher, then check the final tree.
./bin/abvx publication check --item publication-unique-id --site-root /Volumes/Work/Work/ABVXsite
# Publish through the normal site release flow, wait for production, then close.
./bin/abvx publication complete --item publication-unique-id --site-root /Volumes/Work/Work/ABVXsite --owner-minutes UNKNOWN --rework-count 0 --cortex-root /Volumes/Work/Work/CortexABV-private
# Retry only the handoff if Cortex failed after the outcome was retained.
./bin/abvx publication transfer --item publication-unique-id --cortex-root /Volumes/Work/Work/CortexABV-private
```

Use the selected Python environment. The commands do not install dependencies. Supply the actual rework count, not an assumed zero. No unattended harvesting of arbitrary site changes is enabled.

## Measurement and privacy

Duration covers ready intake → verified production, including deployment/waiting; it excludes writing before intake. Durable publication sessions use millisecond UTC wall time. Same-process maintenance checks use a monotonic high-resolution clock. Legacy integer observations remain accepted alongside bounded finite fractional seconds; old zero-duration rows are not retroactively corrected.

Owner minutes mean active owner participation. Leave UNKNOWN when unmeasured; it blocks efficiency qualification. Start tomorrow with a unique intake ID per publication, count real correction rounds and measure active owner effort when practical.

The stable workload profile includes surface, check tier, asset count, video presence and actual build mode. Its `workload:` name and hash determine cohort comparability; changing production/log hashes remain provenance. Legacy rows without a profile require identical evidence names **and hashes**. A profile is operational comparability, not proof that arbitrary articles have equal complexity or that one successful run establishes a gain.

Only opaque identifiers, numeric metrics, gate states and evidence hashes enter Cortex. No authored text/media, URL, absolute path, log contents or credentials are exported. Sessions, checks, batches and return receipts stay ignored. Full metrics return READY_FOR_ANALYSIS without invoking a model; missing metrics return a cited diagnosis. Optional model synthesis remains separately invoked and operationally unqualified. No result grants adoption, deletion or publication authority.

## Verification and release scope

Tests cover automatic start, approval/handoff separation, altered-tree rejection, preview/wrong production text rejection, immutable metrics and idempotent OS → temporary Cortex → OS exchange. Cross-runtime fixtures never enter the canonical operational ledger.

This small release excludes unreviewed recovered Book Radar, Book Core, psychology and wider maintenance changes from OS PR #2. That recovery remains protected and open for separate review. Cortex PR #4 includes its reviewed ID contract and OS source, with inference, retention, private output and packet-identity boundaries repaired.
