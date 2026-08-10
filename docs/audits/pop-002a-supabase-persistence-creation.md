# POP-002A Supabase persistence creation

Date: 2026-08-10

## Outcome

- Dedicated Supabase project for POP was created successfully.
- Project name: `POP / 1D3X Basket`
- Region: `eu-central-1`
- Status: `ACTIVE_HEALTHY`
- Database host: `db.jezdtvqhmmjcrjonhdaq.supabase.co`
- API URL: `https://jezdtvqhmmjcrjonhdaq.supabase.co`

## What was proven

- The Supabase account/org is now able to create a dedicated POP database.
- The project is reachable through the Supabase connector.
- SQL access through the connector works against the new project.
- Existing Basket storage requirements remain valid for this project:
  - `BasketSource`
  - `BasketRawSnapshot`
  - `BasketObservation`
  - `BasketPublishCandidate`
  - `BasketPublishedValue`
  - `BasketExternalSeriesObservation`

## Exact stop boundary

The local secret boundary was cleared, but the new Supabase project's external PostgreSQL connectivity is not yet usable from this session:

- direct host `db.jezdtvqhmmjcrjonhdaq.supabase.co:5432` does not resolve locally;
- pooler host `aws-0-eu-central-1.pooler.supabase.com` resolves, but both `5432` and `6543` refused TCP connections in repeated checks.

The Supabase connector can execute SQL against the project, so the project itself is alive. The blocker is specifically the external client connection path required by the existing Node/`pg` pipeline.

## Minimum human action required

One of the following external connectivity fixes is required before the existing Node pipeline can be proven DB-backed:

1. Wait briefly and retry once the new Supabase project's external DB endpoints finish provisioning, or
2. Check the project's external connection settings in Supabase Dashboard and provide the correct currently-supported connection string variant for this environment, or
3. Resolve any project/network setting that is causing direct host DNS failure and pooler port refusal.

No further code changes are justified before the external DB connection path is actually usable.

## Next step after connectivity is usable

Run the existing pipeline unchanged:

- `npm run basket:ingest`
- `npm run basket:review`
- `npm run basket:publish`

Then verify readback through the existing storage/API layer and only after that decide the smallest production-env handoff.
