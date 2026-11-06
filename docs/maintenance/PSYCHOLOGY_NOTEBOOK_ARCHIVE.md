# Psychology Notebook: private archive reconciliation

This adapter reuses the existing Psychology warehouse, series registry and retained native publication receipts. It creates no publisher, scheduler, public category or model integration.

```sh
python3 scripts/reconcile_psychology_series.py --series-root <absolute-private-series-root>
# Inspect the dry-run, then apply the same validated reconciliation:
python3 scripts/reconcile_psychology_series.py --series-root <absolute-private-series-root> --write
```

Run after a Psychology Notebook publication has passed production QA and its existing cycle is closed, and after archive/editorial updates. A local source-specific receipt proves retained history; this command does not make a fresh network verification or claim search indexing. Pending/failed releases never create used records. Original source versions must match; changed source/approval/receipt hashes, missing IDs or conflicting prior usage stop before writes.

The canonical series IDs and warehouse IDs stay distinct, linked by exact normalized source text. A line-leading `***` with following text can split one warehouse block into two series fragments; both links retain exact source ranges and both existing IDs. No fuzzy substring mapping is admitted. Exact duplicate occurrences all remain represented. The source TXT, queue, plan, translations and publication approvals are preserved. Unpublished review flags are additive, not automatic approvals; published usage requires the complete retained production evidence.

Outputs under ignored `psychology-warehouse/editorial/` include `INDEX.md`, full source reading views, topic intersections, repeat candidates, separate review queues and machine-readable `catalogue.json`. Private source-read editorial decisions are hash-bound in `decisions.json`; speculative topics remain marked as rule candidates. Neither a topic label nor an absence of flags grants publication authority. Ordinary unknown notebook provenance is not automatically treated as plagiarism or grounds to block the whole archive. Clinically important advice, recognisable long passages, case context and identifying details receive explicit review flags. A canonical book manuscript is still required to establish book overlap.

The existing `psychology-warehouse/usage/ledger.json` gains idempotent `PUBLISHED_FRAGMENT` rows under project `psychology-notebook`. Existing other-project usage and mappings remain intact. Existing `./bin/abvx psychology used --book psychology-notebook --json` queries include these rows; `unused` means only no usage in that ledger. Native registry entries gain reciprocal warehouse links and evidence-bound editorial topics. The raw warehouse notes and their IDs remain unchanged. The legacy warehouse topic taxonomy is retained; the refined editorial view is separate and explicit.

Each file replacement is atomic. If interrupted between files, rerun the same command: stable usage IDs prevent duplicate use records and unchanged approvals are reused. Optimistic input hashes reject changes detected during planning. This is not a general concurrent transaction manager; do not run two archive writers at the same time. Keep generated source views and decisions out of Git.

Validation:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_psychology_*.py' -q
```

Tests cover boundary ranges, rejection of arbitrary substrings, duplicate source occurrences, topic specificity, extra diagnostic review, evidence-bound usage, idempotence, preservation of unrelated uses, and rejection of changed source versions, altered receipts and stale editorial decisions. A full manual semantic/clinical clearance of all notes is not asserted by these tests or by a catalogue covering every ID.
