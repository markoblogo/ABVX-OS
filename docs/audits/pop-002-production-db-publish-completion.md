# POP-002 production DB publish completion

Date: 2026-08-10

Scope: finish the existing POP/Basket DB-backed ingest → review → publish → public API pipeline with the smallest safe change.

## Clean work line used

- Source branch inspected: `codex/basket-production-demo`
- Divergence from `main`: `313` commits on POP side, `14` commits on `main`
- Clean bounded work line created from commit `25c07e8`:
  - branch: `codex/pop-db-publish-completion`
  - temporary worktree only

Reason: `codex/basket-production-demo` already contains later unrelated SSI movement after the Stage 4 POP persistence commit.

## Actual database/provider

- Intended database type is confirmed: PostgreSQL via `DATABASE_URL`
- Storage model is mixed:
  - Prisma/PostgreSQL for core index platform state
  - raw SQL `ensure*Storage()` tables for Basket persistence
- Repo-visible provider/vendor is **not discoverable** from current local evidence
- Current local evidence shows only:
  - `.env.example` with generic PostgreSQL URL shape
  - `.env.vercel.production` with `DATABASE_URL="[SENSITIVE]"`
  - no real `DATABASE_URL` in shell env
  - no real `DATABASE_URL` in local `.env.local`

Conclusion: the production DB path exists conceptually and is already wired in code, but the actual secret is not locally available in this session.

## Storage/schema status

The Basket branch storage model already covers:

- `BasketSource`
- `BasketRawSnapshot`
- `BasketObservation`
- `BasketPublishCandidate`
- `BasketPublishedValue`
- `BasketExternalSeriesObservation`

This is sufficient for the requested slice without redesign.

## Observed script behavior on the clean work line

### Tests

Passed:

- basket formulas
- basket storage
- Economist Big Mac adapter
- FRED adapter

### Ingest

`basket:ingest` succeeded locally and wrote `.tmp/basket-ingest.json`

Observed counts:

- `bigMac: 3`
- `fredSeries: 3`
- `fredObservations: 26187`

### Review

`basket:review` succeeded locally after ingest and wrote:

- `.tmp/basket-review.json`
- `.tmp/basket-publish-candidates.json`

Observed mode:

- `json-artifact`

That means the review flow worked structurally, but did not persist to DB because no real `DATABASE_URL` was available.

### Publish

`basket:publish` succeeded locally after review and wrote:

- `.tmp/basket-published.json`

Observed mode:

- `json-artifact`

That confirms the publish path remains bounded and does not silently claim DB publication when the database path is unavailable.

## Local vs live verification

### Local clean-line result

- ingest: yes
- review: yes
- publish: yes
- DB-backed persistence: **not proven**
- reason: no real `DATABASE_URL` available locally

### Live pop.1d3x.com result

Confirmed reachable:

- `/api/basket/latest?market=UA`
- `/api/basket/history?market=UA`
- `/api/basket/compare?market=UA`
- `/api/basket/sources`
- `/api/basket/reports/monthly/latest`
- `/embed/basket/chart?market=UA`
- `/embed/basket.js`

Observed live behavior is still coherent, but this audit cannot claim that the live host is currently using the DB-backed Basket publish path because the production secret/config path was not available for re-run verification.

## Exact stop boundary

Human secret/config action is required.

Minimum required action:

1. Provide the existing production/staging PostgreSQL `DATABASE_URL` to the clean POP work line without sending the secret in chat.
2. The safest forms are either:
   - set `DATABASE_URL` in local shell / `.env.local` for the clean POP branch/worktree, or
   - set the same real `DATABASE_URL` on the `day-1d3x` Vercel project if that is the intended production path.

After that, rerun:

- `npm run basket:ingest`
- `npm run basket:review`
- `npm run basket:publish`

Then verify DB-backed local API behavior and compare it with live `pop.1d3x.com`.

## Branch normalization recommendation

Current safest option:

- `B. create stable POP maintenance branch`

Reason:

- `main` does not currently represent POP reality
- `codex/basket-production-demo` already contains unrelated later movement
- merging now would mix POP completion with non-POP changes

Recommended branch base for continuation:

- `25c07e8`

