# Codex disk growth and weekly retention monitoring v1

Status: owner-authorized, local **read-only** monitoring, cost class **NORMAL**.
Uses the existing `xyz.abvx.mac-operator` LaunchAgent (5-minute cadence)
without creating a new daemon, schedule, external service or deletion interface.

## Frequency and safety limits

- After 04:00 **Europe/Paris**, the first scheduled tick with NORMAL native memory
  pressure (level 1), load below 70% of logical core count, and at least 10 GiB
  free on the internal SSD may perform the **daily** growth scan.
- One calendar-day attempt, recorded **before** scanning. Missed or interrupted
  attempts are not endlessly replayed. If the Mac is asleep, unmounted or under
  pressure, work is deferred to a later eligible existing tick.
- A **weekly** Codex retention preview runs at most once per ISO week, separately
  from the daily scan (never both expensive scans in one tick), and only if the
  same low-load guard permits it.
- The daily scan uses only a bounded `du -skx` of the fixed internal
  `~/Documents/Codex` workspace with a 48-second timeout. It is **not**
  executed every five minutes, and does not follow symlinks or cross volumes.
  If full measurement exceeds the budget, it is marked incomplete and no
  misleading growth calculation or alert is generated.
- Weekly detailed preview calls the existing
  `mac_codex_retention.preview` with a 115-second budget and still has no
  deletion or move capability. Partial results remain visible but do not
  trigger a review-ready notification.

## Signals and alerts

Daily comparison requires complete measurements of the *same* path/device,
separated by 18 to 72 real elapsed hours. The rate is normalized to GiB per
24 hours; the alert threshold is **2 GiB/day**. A first measurement is a
baseline, not evidence of growth. Invalid, old, mismatched, denied or timed-out
measurements never assert growth or recovery.

If a complete weekly retention preview identifies **at least 1 GiB**
in `REVIEW_ELIGIBLE` regenerable dependencies, it creates one review alert,
not an automatic cleanup. Candidate age defaults to 14 days and passing
Git/process checks is not an authorization to delete.

The existing `mac_alerts` incident state machine handles OPEN/RECOVERED
transitions and deduplicates unchanged alerts. When evidence is stale or
unknown, existing growth incidents remain unclosed rather than claiming
recovery. Delivery is best-effort: native OS notification submission does
not prove display, and Telegram remains optional.

## Durable evidence

All receipts are local and excluded from Git under `.tmp/mac-operator`:

- `codex-growth-daily-claim.json`: last claimed day, prevents repeated work
- `codex-growth-scheduled-latest.json`: most recent daily result
- `codex-growth-last-complete.json`: last valid baseline for comparison
- `codex-growth-scheduled-YYYY-MM-DD.json`: per-day audit (retained 35 days)
- `codex-retention-weekly-claim.json`: last claimed ISO week
- `codex-retention-weekly-latest.json`: weekly full preview
- `tick-scheduled.json`: maintenance phase and the outcome of both due checks

Existing manual `codex-retention` preview remains independent. No private
process command lines are stored in growth receipts or alert text. A summary
of the *previous* completed maintenance reading is projected into the next
scheduled host snapshot before incident reconciliation. The read-only
`health` command retains its original meaning: monitor freshness is not
a guarantee the machine is healthy.

## Operational limits

This is not a real-time filesystem watcher. Growth may occur rapidly between
daily scans. Disk-free warnings remain covered by the original five-minute
monitor. Full weekly scans may be repeatedly deferred under ongoing RAM
pressure; lack of a result is not a zero-risk finding. Limited disk space,
failed scans, unplugged `Work` or missing macOS permissions must remain
visible as incomplete evidence, never a reason to delete data.

Do not add automated deletes, symlinks to relocated active caches, a second
scheduler or independent application-killing logic under this module.

## Tests

```sh
cd /Volumes/Work/Work/ABVX-OS
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mac_*.py' -q
```

## Low-space follow-through, 2026-10-26

The first daily-guard description above is superseded as follows. Full scanning retains its low-load/free-space guard. If full scanning is disallowed but native pressure is known NORMAL or elevated (levels 1 or 2), one LIGHT daily attempt measures up to four newest non-symlink date folders on the internal workspace device. Each uses existing native du with at most three seconds, sequentially (about 12 seconds plus metadata overhead). Discovery is capped at 500 direct entries. Critical/unknown pressure defers directory scanning; disk-free observation still runs in the enclosing monitor.

LIGHT results explicitly describe RECENT_DATE_FOLDERS, never total workspace size. Different full/light scopes and changed selection sets cannot produce a fabricated aggregate growth signal. Matching date-folder categories are compared independently across days, even when a new date changes the selected set. A newly observed category is a baseline, not assumed to have had zero prior size. Incomplete results remain UNKNOWN. Old working folders outside the recent four are not covered by this reduced view; weekly/full scans remain separate.

A real scheduled LIGHT attempt completed on 26 October, with a private BASELINE receipt at `codex-growth-scheduled-latest.json`. Manual verification is kept separately at `codex-growth-light-manual.json`. About 9.6 MiB was measured across the selected four dates; this is not a statement about total Codex storage. No new scheduler or model call was added.
