# ABVX Mac monitor and Nantes Radar recovery, 2026-10-27

The existing `xyz.abvx.mac-operator` LaunchAgent is retained. No research
scheduler, task, account, notification transport or agent daemon is created.

## Corrected fault

The old LaunchAgent used an external-volume WorkingDirectory and PYTHONPATH.
Consequently it could not observe the absence or return of that same volume.
Its bootstrap now lives in `~/Library/Application Support/ABVX/mac-operator/`.
The five-minute interval and existing label remain. Volume readiness is checked on that same interval; no filesystem write watch is used to avoid self-triggering on observer receipts.
Before importing ABVX code it records readiness on the internal disk, and invokes
the existing observer only when `bin/mac-operator` is present. An unavailable
volume yields WAITING_FOR_VOLUME rather than loss of the host observation.

Source: `scripts/mac_schedule_recovery.py`; installed mirror:
`~/Library/Application Support/ABVX/mac-operator/abvx_schedule_recovery.py`.
`recovery-settings.json` beside that mirror points to the single internal
data root. Preserve it during source-mirror updates.

Current data root:
`/Users/antonbiletskiy-volokh/Documents/Codex/2026-10-27/referenced-chatgpt-conversation-this-is-an/outputs`.

## Signals and limits

`mac-schedule-recovery/latest.json` is the scheduled readiness projection;
`latest-manual.json` is separate. `signals/` retains one signal per task and
nominal occurrence. The observer reads saved local schedules and scheduler
metadata read-only, never writes scheduler databases. Fixed DAILY/WEEKLY rules
are evaluated in Europe/Paris; unsupported/ambiguous rules remain UNKNOWN.
An attempt timestamp is not successful completion. Inactive tasks are not
resumed; created-after-occurrence tasks are not declared missed.

Nantes's hosted ID and 10:00 schedule were independently verified in the browser.
Its hosted schedule entry here is an observed configuration, not a live hosted
scheduler API. If that hosted configuration is changed later, update the observer
binding as well. Local tasks are discovered from the installed scheduler.

Automatic dispatch is **BLOCKED_NO_SUPPORTED_DISPATCH**. The installed Codex
CLI exposes queue/proxy methods, but its app-server control socket is absent.
The hosted ChatGPT automation has no verified local event-trigger interface.
Neither a saved readiness signal nor an exit code is reported as a resumed or
published report. No hidden database writes, new agent daemon, token extraction,
browser background injection or replacement scheduler is used.

Signals can be consumed by an already active owner-authorized agent, which must
inspect actual task status and completion evidence before using the existing
task's Run now control. This delivery path remains manual pending a verified
supported local/hosted trigger. A local notification states that limitation.

## Nantes report checkpoints

`nantes_radar_journal.py` / source `scripts/nantes_radar_journal.py` is a
dependency-free report journal, not a source collector, opportunity tracker,
scheduler or publisher. It preserves independent youtube/gmail/kdp_markets/jobs/
udemy/creative_assets results in atomic run state, with two attempts per stage,
300-second stage leases, stale-token rejection and retained attempt history.
`REPORT.md` is regenerated after each saved stage, including unavailable stages.
`FINAL.md` is frozen at prepare; delivery acknowledgement requires its hash and
an independently observed exact ChatGPT message URL. The script itself cannot
verify the truth of a source or whether that message exists. The caller must.

Same-date init resumes existing state; corrupt state is never silently reset.
Publication states NOT_PUBLISHED/PREPARED/PUBLISHED remain separate. Ambiguous
delivery requires inspection instead of automatic replay. A partial report may
be published with explicit gaps. Complete checkpoint coverage is not complete
source coverage or proof of future scheduled execution.

`resume --run RUN --reason source_recovered` opens a recovery revision only
after the prior delivery was verified and only when retryable/unreached stages
remain. It retains the publication receipt, successful stages and attempt budget.
An unchanged retry result cannot prepare another publication. A changed block
uses a new frozen `FINAL-2.md` (or later revision) with the prior message link;
the original `FINAL.md` and its hash remain intact. The monitor does not suppress
a retryable unfinished stage merely because the partial report was delivered.

The hosted prompt was updated in place. Its original text is preserved in
`radar-prompt-before.txt`; the old separate Monday task is paused, not deleted.
10:00 Europe/Paris and the existing task ID are preserved.

## Rollback

Stop only the existing LaunchAgent, restore `mac-operator.before.plist`, and
bootstrap that same label. Revert only the added `plist()` bootstrap branch in
`mac_operator.py`; preserve other dirty work. The internal runtime and evidence
can remain inert. Restoring the old hosted prompt is an explicit owner decision;
it reintroduces the no-file/checkpoint conflict. Do not delete journal/history.

## Validation boundary

Synthetic tests cover state survival, source failure isolation, bounded retries,
stale workers, corruption, publication fencing, missing-volume/return transitions,
Paris DST, pause handling, exact-once signal creation and manual/scheduled separation.
No physical disk disconnection, reboot, unattended ChatGPT dispatch or future
10:00 run is simulated as live success. The real LaunchAgent and existing observer
were started and their exit/status receipts inspected separately.
