# Protected snapshot gate

For bounded runs that declare `PROTECTED_SNAPSHOT_REQUIRED = TRUE`, record the UTC run start before edits and explicitly list every protected repository-relative file. The helper does not discover or infer protected files.

```sh
./bin/abvx protect snapshot <scope> <protected-file> [<protected-file> ...]
./bin/abvx protect recheck <snapshot-path>
./bin/abvx protect gate <PASS|REVIEW|HOLD|FAIL> \
  --required true --started-at <UTC-run-start> --snapshot <snapshot-path> \
  --missing-policy <REVIEW|HOLD>
```

Snapshots are timestamped, created with exclusive-create semantics, stored under `.codex/protected-snapshots/`, and written read-only. `UNCHANGED` for every listed file is required for an eligible `PASS`. A snapshot captured after run start or a missing snapshot downgrades a candidate `PASS` to the selected `REVIEW`/`HOLD`; any changed or missing protected file returns `HOLD`. Other candidate states are never upgraded. No snapshot or gate command performs network access.
