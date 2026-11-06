# Portfolio prior before deep research

Before owner authorization of external Shelf Intelligence, read the external handoff together with the qualitative [portfolio-prior context](../book-radar/audits/portfolio-prior-overlay-v1/BOOK_RADAR_PORTFOLIO_PRIOR_OVERLAY_V1.md) and [current V2 survivor review](../book-radar/audits/portfolio-prior-overlay-v1/BOOK_RADAR_V2_SURVIVOR_PRIOR_REVIEW_V1.md).

The thin read-only overlay uses existing canonical Outcome Foundation actuals, Attribution cards and checkpoints. It neither changes Wide decisions nor updates scoring. Explicit evidence-backed semantic comparisons are required; title matching and automatic absence/novelty claims are unsupported.

Using the normal project Python environment with dependencies available:

```sh
PYTHONPATH=src python -m abvx_harness.book_radar_prior \
  --root /Volumes/Work/Work/ABVX-OS \
  --requests book-radar/audits/portfolio-prior-overlay-v1/review-inputs.json \
  --as-of 2026-10-04
```

This prints a schema-validated report and makes no canonical or external writes. For a later opportunity, provide a new bounded request with current external references and semantic comparisons; never overwrite the frozen V1 requests. Recompute against current canonical actuals, keeping their observed date distinct from report date. No live KDP refresh is implied.

Schema: [BOOK_RADAR_PORTFOLIO_PRIOR_SCHEMA_V1.json](../schemas/BOOK_RADAR_PORTFOLIO_PRIOR_SCHEMA_V1.json). Output: [BOOK_RADAR_PORTFOLIO_PRIOR_MATCHES_V1.json](../book-radar/audits/portfolio-prior-overlay-v1/BOOK_RADAR_PORTFOLIO_PRIOR_MATCHES_V1.json).

Only owner review can select subsequent Shelf work. Positive prior is not GO; zero/unknown paid prior is not an automatic KILL or no-demand verdict. Owner assets and production economics remain future, separate axes.
