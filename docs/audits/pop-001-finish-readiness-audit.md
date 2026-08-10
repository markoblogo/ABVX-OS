# POP-001 finish-readiness audit

Date: 2026-08-10

Scope: current POP reality inside `/Volumes/Work/Work/index`, not historical intent.

## Actual state

- A live public POP/Basket surface exists at `https://pop.1d3x.com/`.
- The implementation line is not on current `main`; it exists on branch `codex/basket-production-demo`.
- That branch contains a dedicated Basket surface with:
  - `src/app/api/basket/*` routes;
  - `src/app/embed/basket/*` embeds plus `src/app/embed/basket.js/route.ts`;
  - `src/components/basket/basket-landing.tsx`;
  - `scripts/basket-ingest.ts`, `basket-review.ts`, `basket-publish.ts`;
  - `src/lib/basket/storage.ts` and tests.
- The real codebase is a shared Next.js/TypeScript index platform with:
  - persisted Prisma/PostgreSQL respondent, basket, calculation, published-index and audit models;
  - shared public latest/history/fx APIs;
  - shared admin calculation/respondent/reporting/integrity surfaces;
  - shared embed surfaces;
  - active Index Cortex internal context/evidence layer.
- The live POP line was deployed through Vercel project `day-1d3x` with tenant/env `1d3x-basket`.
- Current `main` still does not reflect that POP line cleanly; docs/runtime on `main` remain oriented around `uga-ua` and `spike-ua`.

## What is already reusable for POP

- live POP landing and API surface;
- real Big Mac + FRED ingestion path;
- SQL-backed basket storage/publish-candidate module on the POP branch;
- embed delivery pattern already implemented for Basket;
- real basket/respondent/publication persistence;
- calculation and publication pipeline;
- public API and caching pattern;
- embed delivery pattern;
- admin/operator surfaces;
- Index Cortex read-only domain/methodology retrieval.

## What is not complete yet

- production DB-backed completion on the live Vercel project;
- an unambiguous canonical maintenance branch merged back into a stable line;
- broader alternative-index library beyond Big Mac + overlays;
- final human-reviewed publication flow for monitored/seed products such as Starbucks and iPhone.

## Smallest coherent V1

1. Identify the actual code path that serves `pop.1d3x.com`.
2. Configure `DATABASE_URL` for `day-1d3x`.
3. Run `basket:ingest`, `basket:review`, and `basket:publish` against real DB.
4. Verify `/api/basket/latest`, `/api/basket/sources`, and live host behavior on `pop.1d3x.com`.
5. Decide whether to merge the POP line into a stable branch or keep a dedicated POP maintenance branch.

## Blockers

1. POP source-of-truth currently lives on a side branch, not on stable `main`.
2. Production `DATABASE_URL` for `day-1d3x` is still the explicit gate for DB-backed completion.
3. `main` docs/runtime mismatch around `1d3x` support creates maintenance ambiguity.
4. Alternative-index breadth is still narrow and partially review-gated.
5. Current local repo link defaults remain oriented to `spike-ua-index`, so POP deploy operations need deliberate isolation.

## Index Cortex boundary

Index Cortex should supply methodology, domain, source, and editorial context.
POP should own public basket state, raw snapshots, publish candidates, published values, embeds, and release identity.

## External reference

`https://cig-index.vercel.app/` is recorded as the first reference example for the future alternative index library. It is a reference only, not an implementation donor.

## Live surface note

The live page currently presents itself as `1D3X Basket`, with consumer basket indices, analytics, methodology, media, API, and monthly review sections. That confirms product reality, but not yet the local implementation locus.

## Validation from this audit

- ABVX validation: pass.
- POP branch targeted tests: pass (`basket formulas`, `basket storage`, `Big Mac adapter`, `FRED adapter`).
- POP branch ingest CLI: pass, writing `.tmp/basket-ingest.json` with real Big Mac/FRED counts.
- POP branch build: not conclusively validated in the temporary detached worktree because Turbopack rejects a symlinked `node_modules` outside the worktree root.
