# Local Mac operator v1

Updated 2026-10-20. Cost NORMAL. Owner-authorized native monitoring and bounded local control. No root, model loop, public listener, arbitrary shell, application termination or deletion. Stage 2 adds source-separated observations, workflow health, incident delivery and explicit research handoffs.

## Actual activation and verification

The owner ran `bin/mac-operator-install` from Terminal after sandbox bootstrap failed. User LaunchAgent `xyz.abvx.mac-operator` is loaded with a 300-second interval. A fresh stage-2 scheduled invocation completed with exit code 0 and all diagnostic probes available. A subsequent sandbox manual invocation left the scheduled snapshot byte-identical. This verifies real background invocation, not reboot/lock-screen or crash recovery.

24 targeted tests pass across `tests/test_mac_operator.py` and `tests/test_mac_operations_integration.py`. Coverage includes manual/scheduled isolation, request deduplication, blocked arbitrary commands, handoff claim/cancel/evidence checks, future/changed-source rejection, incident transitions, unknown-not-recovered semantics, notification cooldown/attempt cap, symlink/scan limits, sender authorization, stale/duplicate Telegram updates and redacted transport errors. Native local notification requests returned success; visible delivery has NOT been verified. Telegram remains NOT_CONNECTED.

## Ownership and reuse

Native Apple launchd owns invocation and failure throttling. Existing Codex heartbeats own browser research. Existing Radar and YouTube commands own domain validation, reporting and learning. The operator joins evidence references without replacing these systems. Existing `process_learning.digest` binds read-only workflow evidence; host samples are not business outcomes and are not exported to Cortex. No shared workflow engine/database/cloud dependency was added.

Native provider references: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html and https://core.telegram.org/bots/api . Existing n8n/Activepieces donors remain deferred: they add an unnecessary parallel workflow runtime. Review: [process integration](LOCAL_OPERATIONS_INTEGRATION_V1.md).

## Available scenarios

| CLI | Allowed action | Evidence / recovery |
| --- | --- | --- |
| `status`, `slow` | Native pressure, swap, VM, CPU, process names without arguments, thermal, network, internal disk capacity/trend | Manual sample and last complete scheduled reference with age; no automatic intervention |
| `services` | Read ABVX user LaunchAgents, selected Codex schedules, workflow receipts and target attempt event metadata | Saved schedule, attempt and domain evidence remain distinct |
| `cleanup` | Preview fixed Help, pip, Homebrew and npm caches | Allocated-byte estimate, scan completeness, consequences and specific approval requirement; no deletion |
| `restart-monitor` | One kickstart of this fixed user LaunchAgent | launchctl print; no automatic repeated repair |
| `validate` | Existing `bin/abvx validate`, timeout 120 seconds | Exit code and bounded output; no repair |
| `weekly`, `youtube` | Persist one pending handoff for the existing domain playbook | WAITING_FOR_CODEX means queued, not started; no automatic model spend or retry |
| `handoffs` | Read handoff state | Claim, evidence bind and cancellation described below |

`ask --text 'Как там Mac?'`, `Почему тормозит?`, `Проверь Radar`, `Что можно почистить?`, `Запусти недельное исследование`, `Проверь YouTube`, and `Запусти исследование YouTube` map exact phrases to bounded scenarios. Unknown phrases ask for clarification; no semantic model is enabled. Remote phrase routing does not expose restart, validation or handoff lifecycle commands.

All actions claim a unique SQLite request ID before effects. Duplicate IDs never execute again. Interrupted effects stay IN_PROGRESS and require inspection; there is no automatic replay. Raw request results are redacted after seven days on the next request; ID tombstones persist. Same-user hostile code is outside the OS permission boundary.

## Measurements and retention

- `latest-scheduled.json` and compatibility `latest.json` belong only to launchd invocations identified by the service environment. `summary.txt` is the scheduled summary.
- `latest-manual.json` and `summary-manual.txt` hold manual/sandbox observations.
- `last-complete-scheduled.json` preserves the last scheduled sample without unavailable native probes. Its age is explicit; it is historical evidence, never substituted for current values.
- Samples carry source, timestamp, PID, return codes and evidence. Samples are retained for seven days; generated state stays ignored under `.tmp/mac-operator`.
- Atomic JSON writes avoid partial projections. The daemon lock prevents overlapping ticks. Manual and scheduled sample histories are separate.

Occupied RAM alone does not trigger a warning. Elevated memory pressure does; swap is evidence, not an independent failure. Load warning requires four same-source samples spanning at least ten minutes, all above logical CPU count and with a recent last sample. Thermal warnings are not temperature measurements; denied probes remain unavailable.

Primary disk is `/System/Volumes/Data`, fallback `/`. Repository volume is secondary. Alert below 10 GiB or 10 percent free. Deltas require matching paths and sample source; old external-disk samples cannot fabricate internal-disk change. Current observations show approximately 14.9 GiB free out of 228.3 GiB internally, versus 363.2 GiB on the repository volume.

## Workflow health and Radar investigation

The fixed projection distinguishes CURRENT_EVIDENCE, WITHIN_GRACE, OVERDUE_EVIDENCE, NOT_SCHEDULED and UNKNOWN_OR_INACTIVE_SCHEDULE. Radar's known Monday 08:00 Europe/Paris window has six hours of grace; custom/unsupported schedule forms remain unknown. Paris DST is applied when constructing expected windows. YouTube currently has no admitted weekly schedule.

Schedule TOML and optional local Codex SQLite metadata are read-only evidence. App database schema/access failures remain unknown, not a reason to edit app internals. The last attempt timestamp does not establish completion. Only selected target-thread event types/timestamps are retained; conversation contents are not copied. Transcript inspection is bounded to its final 4 MiB and may therefore be incomplete.

On 19 October, Radar recorded an attempt at 07:55:57 Paris, followed by a task-start event and `turn_aborted` at 11:19:13 Paris. No newer ordinary research receipt was found beyond 12 October. The supported diagnosis is INTERRUPTED_CODEX_TURN, not a proven network or scheduler bug; the cause of interruption remains unknown. The current saved next run is 26 October, but a saved date is not punctual-execution proof. No replacement schedule was created.

Radar evidence requires COMPLETE execution receipt, acquisition, ranking, report and a hash-bound matching REVIEWED learning snapshot. YouTube evidence requires its COMPLETE receipt, acquisition/research digests, analysis and report. EVIDENCE_PRESENT is a structural/hash projection, not independent revalidation of every domain claim or analyst acceptance. Original domain validators and playbooks still apply. Future/invalid timestamps are rejected.

## Incident notifications

Scheduled observations create OPEN and RECOVERED events. Unchanged incidents do not create new notifications. Three consecutive scheduled samples with denied probes create one failure incident. Unknown measurements cannot close a previously observed memory problem. Overdue workflows close only after current domain evidence arrives.

Events are retained privately under `notifications/`, with current state in `incidents.json`. Local macOS notification submission is attempted once per event. Telegram delivery is optional: no token means NOT_CONNECTED. When connected, at most three attempts per event, at least one hour apart; messages expire after one day and old receipts are removed after seven days of inactivity. A network interruption can leave uncertain delivery, so remote alerts are best effort; no exactly-once external delivery is promised. Command effects retain separate deduplication.

No account data, process command-line arguments, credentials or raw exception URLs are sent in alerts. No notification delivery is claimed solely from generating an event. OS permissions, Focus or lock-screen settings can affect visible notifications. There is no general service auto-repair.

## Cleanup preview

Only fixed regenerable cache locations are measured. No symlinked candidate or parent is accepted; traversal does not follow symlinks or cross device boundaries. Per candidate: maximum three seconds / 25,000 entries. Partial scans and errors are visible. Allocated bytes can overstate reclaimable APFS/shared/hardlinked storage. Do not clear package caches during active installs.

The real preview found about 830 MiB total, mainly npm (about 711 MiB). This cannot resolve the full internal storage constraint. Projects, documents, browser profiles/caches, keys, backups, app data, applications, Downloads and Trash are excluded. No removal endpoint exists; a concrete deletion action still requires explicit owner approval and implementation/review.

## Research handoff and remaining dispatch blocker

```sh
./bin/mac-operator weekly --request-id owner-radar-unique-id
./bin/mac-operator handoffs
./bin/mac-operator claim-handoff --handoff-id <64-character-id>
# Existing Codex agent follows the packet's fixed playbook, preserving all domain gates.
./bin/mac-operator complete-handoff --handoff-id <id> --run-id <fresh-domain-run-id>
# If interrupted or no longer wanted:
./bin/mac-operator cancel-handoff --handoff-id <id>
```

One open handoff per workflow, including across distinct command IDs. Claim is single-use; no automatic redispatch. Completion binding rejects missing evidence, altered hashes and results older than the request. RESULT_EVIDENCE_BOUND is not independent domain QA. Cancellation does not stop an already-running external task; the owner must stop it through Codex if necessary.

The local background process has no admitted authenticated Codex dispatch interface. In-session automation view and target-thread read both returned `Codex app tool request failed`. `codex` is not on the normal CLI PATH. Writing raw Codex queue/database state or bypassing its API is prohibited. The prepared handoff therefore waits for an existing agent to claim it; fully automatic remote research start remains BLOCKED. No extra polling LLM job or alternative research scheduler is installed.

## Telegram connection

Create a dedicated bot with BotFather. Store the following in owner-only mode 0600 `.tmp/mac-operator/telegram.json`, not chat/Git:

```json
{"token":"BOT_TOKEN_FROM_BOTFATHER","user_id":123456,"chat_id":123456}
```

Both numeric sender and private-chat IDs must match. Messages older than ten minutes are ignored. Offset is persisted before effects, plus SQLite command deduplication. Interrupted command replies may be lost rather than re-executing effects. Polling is outbound HTTPS once per scheduled invocation; response can take five minutes. No public shell/webhook is opened. Token storage is owner-readable plaintext, not Keychain in v1. Remote sender/replay paths have simulated coverage; live connection is unverified.

## Availability, install and stop

```sh
cd /Volumes/Work/Work/ABVX-OS
./bin/mac-operator-install
launchctl print gui/$(id -u)/xyz.abvx.mac-operator
```

Already installed on this machine. Reinstallation is not needed for code updates because each tick loads current repository code. Plist uses an absolute selected Python interpreter and the mounted repository path. Missing Work volume or Python prevents invocation. Native probes require no GUI interaction, but locked-session/reboot behavior remains unverified. Browser research needs its authorized session. No work runs while asleep; no waking or sleep prevention is configured. After reboot the user must log in, including FileVault unlock. Local probes do not need a model/network; Telegram and research acquisition do.

launchd throttles failed invocations to 60 seconds. stdout/stderr use `/dev/null`; native failures are in sample receipts and unexpected process failure is observable through launchctl last exit code. Crashes before incident code runs cannot generate an in-process alert, and there is no independent watchdog. Crash recovery is configured, not yet fault-injection verified.

```sh
launchctl bootout gui/$(id -u)/xyz.abvx.mac-operator
rm "$HOME/Library/LaunchAgents/xyz.abvx.mac-operator.plist"
```

First command unloads, second removes login activation. Neither deletes private diagnostic history or changes system security/network configuration.

## Monitor health and interrupted execution (2026-10-21)

`./bin/mac-operator health` reads retained evidence without running native probes or replacing scheduled observations. Monitor freshness and host health are separate: a fresh monitor can correctly report an unhealthy host. Missing/future timestamps are UNKNOWN; a scheduled sample older than 15 minutes is STALE. Sleep or an unmounted repository can also explain staleness, so this is not a crash diagnosis.

Every daemon invocation now checkpoints source-specific `tick-scheduled.json` or `tick-manual.json`: start, phase (diagnose/incidents/notifications/transport), completion or exception class. Error text is excluded to protect secrets. Failures still propagate to launchd for its existing bounded restart policy. An unfinished tick older than five minutes or a failed tick is visible in health; manual invocations cannot replace scheduled tick evidence. Hard termination may leave RUNNING, and failure before the initial checkpoint cannot be captured. There is still no independent watchdog or automatic repair.

An expired chat approval prompt is not an operator receipt. Inspect `health`, `handoffs`, and the domain result before repeating a state-changing request. Preserve the original request ID to prevent duplicate effects. Do not replay an IN_PROGRESS action until its effects have been inspected. Local diagnostics and scheduled monitoring do not depend on a pending chat approval.

Verification for this increment: 29 targeted Mac tests pass, including stale/future evidence, read-only inspection, redacted failure phases and source isolation. Live invocation evidence must be checked separately; tests alone do not prove launchd execution or visible alert delivery.

## Existing hotel internet recovery bridge (2026-10-21)

The existing `io.abvx.hotel-wifi-reconnect` user LaunchAgent remains the sole executor for hotel portal login. Its private script lives under `~/Library/Application Support/CodexAwake/`. It checks two connectivity endpoints every minute, requires two failed rounds and spaces attempts by at least 300 seconds. The existing gateway and destination restrictions remain unchanged. No second scheduler, portal submission, network-setting change or script modification was added by this integration.

`services` and scheduled summaries now include its launchctl state and a bounded 32 KiB tail projection of recognized log events only. Email, cookies, raw response bodies and arbitrary log text are excluded. Transition logs are historical; even `internet_online` does not prove current connectivity. Current internet is explicitly UNKNOWN in this bridge. Missing logs or stopped/inaccessible service remain unknown and do not trigger automatic restart. Existing agent attempts are not subject to an overall attempt cap; the OS bridge does not broaden that policy.

Observed: service running; the local log recorded internet unavailable at 17:49, a reconnect ValueError at 17:50 and internet online at 17:52 on 21 October. This shows recovery of connectivity after an error, but does not prove that form submission restored it. The specific ValueError cause is not retained and cannot be inferred. 31 targeted Mac tests pass after this integration. No live form submission was triggered by the implementation.

## Bounded hotel recovery supervisor (prepared 2026-10-21)

Owner observation confirms that the existing script restored internet during the observed outage. The earlier log alone could not establish causality; the owner directly saw the script work. The historical ValueError's specific reason is still unknown.

Cost NORMAL. Reuse: the owner's existing portal adapter owns HTTP/form handling, gateway and redirect allowlists, cookies and login data. `hotel_recovery.py` wraps its reviewed SHA-256 source without copying private identity into Git. No new network library, browser driver or monitoring runtime is needed. Modified source fails closed pending review.

The replacement supervisor keeps the same LaunchAgent label and original exclusive lock. It probes every minute, requires two offline samples, spaces reconnect attempts by at least 300 seconds and spends one of three slots BEFORE calling the adapter. Exceptions, unverified outcomes and interrupted attempts consume a slot; outside-hotel skips do not. Three attempts without verified connectivity pause further logins indefinitely. Read-only connectivity probes continue; a successful probe resets the series. Restart/reboot does not reset its private persisted budget. There is no timed reset or automatic consent expansion. A missing state starts a new budget, so do not delete state as a repair. Invalid/unreadable state fails closed.

Known adapter errors retain specific fixed reason codes (redirect/destination rejected, missing/changed form, extra required field, unsupported auth/consent). HTTP status codes, TLS/network failures and timeouts have separate codes. Unexpected exceptions retain only `unexpected_error`. No exception URL, email, form payload or response body is copied. The underlying adapter has no per-request phase receipt, so these codes do not establish the exact HTTP step or root cause for every failure.

The monitor admits fresh (at most three-minute-old) `network-recovery.json` only when launchctl shows the replacement module. A paused series creates one incident notification through existing delivery. Unknown/stale observations cannot close it; fresh ONLINE evidence closes it. Visible macOS delivery remains unverified; Telegram remains unconnected. While offline, local alerts can be submitted, but remote delivery cannot be relied upon.

Activation is pending: this session may write the repository but cannot change `~/Library/LaunchAgents`. Run in the owner's Terminal:

```sh
cd /Volumes/Work/Work/ABVX-OS
./bin/hotel-recovery-install
./bin/mac-operator services
```

The installer validates the pinned adapter, prepares a plist, keeps the original plist privately, unloads the old job and loads its replacement. Bootstrap failure restores the original configuration. It does not edit the portal script. Check for a fresh `bounded_recovery` receipt after one minute; successful bootstrap alone does not prove internet restoration. Do not deliberately disconnect active work to test this.

Rollback to the original unbounded loop, if necessary:

```sh
launchctl bootout gui/$(id -u)/io.abvx.hotel-wifi-reconnect
cp /Volumes/Work/Work/ABVX-OS/.tmp/mac-operator/hotel-recovery-original.plist "$HOME/Library/LaunchAgents/io.abvx.hotel-wifi-reconnect.plist"
launchctl bootstrap gui/$(id -u) "$HOME/Library/LaunchAgents/io.abvx.hotel-wifi-reconnect.plist"
```

Verification: five supervisor tests plus 33 Mac integration tests pass, including slot persistence, interruption, cooldown, outside-hotel skip, independent success verification, redaction, notification deduplication and unknown-not-recovered behavior. Prepared plist passes plutil validation; installer passes shell syntax check. Replacement daemon activation and live failure/recovery are not yet verified. No form was submitted during these checks.

### Activation verified after owner installation

On 21 October the owner ran `bin/hotel-recovery-install`. Subsequent launchctl inspection shows the existing label running `abvx_harness.hotel_recovery` (PID 42704 at verification). A fresh v1 receipt reports ONLINE, zero attempts and attempt_limit 3; the services projection admits it as ONLINE. Installation is now active, superseding the pending status above. No outage was induced. Live three-failure pause and visible notification delivery remain unverified; their bounded behavior has test evidence only.

## One-shot internal storage overview

`./bin/mac-operator disk-overview` inventories fixed top-level Data volume categories and selected home categories. It saves a private `disk-overview.json`, does not run on scheduled ticks and does not delete anything. Native `du -skx` is limited to 20 seconds per category with at most three concurrent scans; symlink roots and other volumes are excluded. Permission errors produce PARTIAL, timeout produces TIME_LIMIT, and missing sizes remain unknown. Only aggregate sizes and diagnostic counts are retained, not raw error paths or file contents. Home detail overlaps Users and must not be added to top-level totals. APFS shared blocks and snapshots prevent treating allocated sizes as exact used or reclaimable space. This implements overview only; candidate selection and cleanup remain separate owner tasks.

## Owner storage-placement requirement (2026-10-21)

Owner wants bidirectional storage recommendations: frequently used, latency-sensitive working material may belong internally; rarely used archives may belong externally. This is an advisory requirement, not authorization to move files or change app storage paths. Current step measures only user Library sizes. Ongoing access-frequency monitoring and automatic moves are NOT activated.

A later bounded pilot should use an explicit owner-selected folder list, observation period and evidence of use; access timestamps alone are not reliable usage evidence. Account for internal free-space reserve, external availability, project independence, backups and supported application relocation. Library containers, app databases, browser profiles, credentials and live service dependencies are not generic movable archives. Any move needs a specific manifest, application-supported method where applicable, verified copy, rollback and separate approval before source removal. Prefer the existing monitor and private receipts over another scheduler. Size inventory is not usage telemetry.

## Codex workspace retention preview (2026-10-25)

`./bin/mac-operator codex-retention` is an explicit, bounded read-only report for regenerable `node_modules` and `.next` directories in the internal `~/Documents/Codex` date/session workspaces. It checks Git, activity evidence and candidate-age policy (14 days by default); incomplete checks fail closed. A private latest preview is saved under `.tmp/mac-operator/`. This command does not run on the existing five-minute monitor and cannot delete, move or archive any data. Full policy and limitations: [Codex retention preview](CODEX_RETENTION_PREVIEW_V1.md).

## Daily Codex growth and weekly retention (2026-10-26)

The existing five-minute LaunchAgent now checks whether a **due** low-load daily Codex workspace size observation or a weekly full regenerable-dependencies preview is allowed. The daily operation is bounded to 48 seconds and runs only once per Europe/Paris calendar day; the weekly operation is bounded to 115 seconds and runs at most once per ISO week, never on the same tick as an attempted daily scan. Both defer when native memory pressure is elevated, CPU is high, or the internal SSD has less than 10 GiB free. The existing notifications pipeline opens a deduplicated review warning for proven growth of at least 2 GiB/day or at least 1 GiB of weekly review-eligible regenerable files. Incomplete measurements cannot trigger false claims or recoveries. All evidence is private, files remain unchanged, and no additional LaunchAgent is installed. Full rules: [Codex growth monitor](CODEX_GROWTH_MONITOR_V1.md).

## Hotel recovery responsiveness update, 2026-10-26

Cost NORMAL; reuse the same hash-qualified portal adapter, existing LaunchAgent, private receipt and monitor incident pipeline. No dependency, second executor, Wi-Fi toggle, interface reset, root or change to portal destinations/consent was introduced.

Investigation found a fresh ONLINE receipt and a running supervisor. The previous receipt kept only last_reason, which successful probes erased, so it cannot identify why the owner's latest outage needed a Wi-Fi toggle. launchctl also retained a previous EX_CONFIG exit and many historical launches; neither identifies the latest incident's cause. Native original log stopped receiving events when the supervisor replaced the original main loop.

The new loop sleeps 15 seconds between checks (probe execution time is additional), still requires two negative rounds before login, and resets last_attempt after verified connectivity. Within a failing series retries are spaced by 60 then 120 seconds, with three consumed slots persisted before effects. Three failures still pause indefinitely until online is confirmed; there is no hidden infinite rearm. Outside-hotel skips retain a five-minute rate limit. Probe execution exceptions produce UNKNOWN/PROBE_ERROR and never authorize login.

Private state retains at most 20 structured transitions/attempt outcomes with fixed redacted reason codes; recovery no longer erases the historical cause. This is bounded incident context, not complete long-term history. Monitor services now projects receipt age, prolonged offline duration, and recent events. Incidents cover outage lasting at least three minutes, stale service receipts and probe execution failures in addition to exhausted attempts. Notifications are evaluated on existing five-minute monitor ticks, not immediately at the threshold. Unknown readings cannot close incidents; verified ONLINE can. Local visible delivery remains unverified, Telegram unconnected.

Validation: eight hotel-recovery tests and 56 Mac tests pass, including new-outage cooldown reset, retry timing/cap, history retained after recovery, probe-error non-execution and incident deduplication. No actual network outage was induced and no form submitted by tests. A native kickstart attempt returned Operation not permitted; the already-running old supervisor remains active until owner restart. Run from normal Terminal:

```sh
launchctl kickstart -k gui/$(id -u)/io.abvx.hotel-wifi-reconnect
```

No reinstall is required because the job references repository code. A fresh receipt with `events` and `offline_since` establishes updated loop execution; service load alone does not prove future recovery. The interval monitor loads its changes on the next scheduled tick. This supersedes the old 60-second/300-second responsiveness description only after supervisor restart.

### Responsive supervisor activation confirmed

After owner kickstart on 26 October, launchctl reports the replacement process running (PID 66797 at inspection). A fresh ONLINE receipt includes new offline_since/outside_until fields and reset last_attempt, proving updated step execution. The events list is created on the next transition; an unchanged inherited ONLINE state does not create an event. Prior restart-pending status is superseded. Live outage recovery and visible alert delivery still require observation.

## First bounded cache-maintenance scenario, 2026-10-26

Reuse decision: existing cache preview, native du/ps/lsof and standard-library descriptor-safe rmtree are sufficient. The thin local adapter adds only exact-plan approval, revalidation and receipts around one fixed npm download-cache target. A new cleanup framework, package-manager integration or orchestration donor would widen authority without improving this acceptance case.

`./bin/mac-operator maintenance-plan` prepares a v1 plan for only `~/.npm/_cacache`. The command never deletes. It snapshots bounded metadata, rejects symlinks/special files/other devices, estimates allocated bytes and records the loss of offline package downloads. Existing installed dependencies, npm configuration, projects and browser data are not targets. The 26 October real plan measured 281,509,888 bytes (about 268 MiB), and live process visibility was UNKNOWN_OR_BUSY in this sandbox. It is not yet approved or executed.

Only `bin/mac-cache-maintenance apply --approve-plan-id <exact-64-character-id>` may remove the fixed cache, after explicit owner approval of that plan. The apply command has no arbitrary path argument, is not exposed over Telegram or scheduled, and never takes a preview signal as permission. It checks plan hash/version/target, 24-hour expiry, exact fresh metadata twice, lsof/process visibility, safe-rmtree support and root inode/device. Unknown/busy/changed data stops execution. Run only while package managers are idle. Same-user hostile mutation is outside the OS permission boundary; process snapshots do not lock out a new installer, so do not start one during approved maintenance.

A separate operation lock serializes CLI applications, and an exclusive IN_PROGRESS result file claims the plan before effects. Interrupted/partial deletion never automatically retries. Removal is descriptor-relative; verification checks the same opened parent. Receipt records before allocated blocks, target absence and observed disk-free delta, which includes concurrent activity and is not a guaranteed causal saving. There is no local undo; package files can be downloaded again when online. This is manual, single-plan approval, not standing cleanup permission.

The terminal wrappers use current repository code and need no LaunchAgent reinstall. Synthetic deletion tests touch only temporary fixtures. No owner cache deletion, Docker restart, prune or storage move occurred in this implementation.

### Docker evidence handoff

`./bin/docker-storage-report` or `./bin/mac-operator docker-storage` collects only context show, system df -v, and container names/status/images, saving a private v1 `docker-storage-report.json`. There are no run/start/prune/stop operations or environment inspection. Failures and output truncation mark the result PARTIAL_OR_BLOCKED; raw error strings are not retained. Docker.raw allocated blocks are reported separately from engine usage.

The 26 October in-session engine calls still fail with Docker access/engine error; a direct read-only call reports socket permission denied. Prior `docker-usage-terminal.txt` is empty, so no image/container/volume/cache breakdown is claimed. Owner Terminal execution of `./bin/docker-storage-report` remains the necessary next step. The previous relocation review still applies; no new relocation implementation was added.

## Owner-authorized emergency and recurring cache cleanup, 2026-10-27

The owner explicitly requested immediate safe cleanup and regular automatic removal. This supersedes preview-only/exact-single-plan restrictions ONLY for a new fixed download-cache allowlist; all project/data/Docker protections stay in force. Cost NORMAL. Reuse: existing native user LaunchAgent, diagnostics/incident pipeline, cache fingerprint and descriptor-safe standard-library remover. No parallel scheduler, cloud service, model loop, package scripts, root or broad filesystem cleaner is added.

`mac_auto_cleanup` is invoked on existing scheduled ticks. Its private v1 policy grants 30 days, is revocable, and never takes paths or shell commands from configuration. Code fixes the only targets: npm `_cacache`, Homebrew `downloads`, pip cache, node-gyp headers, VSCode ShipIt update cache, Apple Help cache and Codex Sparkle Installation update cache. Installed VSCode/Codex, npm configuration and installed dependencies are not targets. Cached files/update payloads may need downloading again; there is no local undo. Browser profiles/caches, Playwright browser binaries, application databases, projects, Git, documents, Downloads, Trash, backups, keys, Docker.raw and Docker volumes remain excluded.

Defaults: evaluate on the existing ticks, at most one pass per six hours below 15 GiB internal free; charge no more than 2 GiB of measured candidate allocations per UTC day. Initial explicit emergency pass accepts caches >=1 MiB; routine passes use >=64 MiB. A fresh explicit `enable` requests one emergency pass; it does not erase failed-target or quota state. Future/expired/malformed grants fail closed. Revocation: `./bin/mac-auto-cleanup disable`; status: `./bin/mac-auto-cleanup status`. No LaunchAgent reinstall is needed.

For each target, a bounded complete metadata inventory, same-device/root-symlink checks, scoped package/updater process checks and native lsof inspection must pass. Unknown visibility or open files block. Process classification checks executable/entry-script tokens; npm activity does not block unrelated pip/Homebrew targets. No process arguments are retained. Filesystem inventory was made linear in pending entries rather than repeatedly sorting the full traversal stack. Nested symlinks may be unlinked inside the allowlisted cache but are never followed; root/parent symlinks and crossed mount devices are rejected. A fresh inventory is checked again immediately before descriptor-relative removal. Starting a new install between observations remains a same-user race, so avoid concurrent installs during emergency maintenance.

Both pass and target operations are serialized. Quota is reserved before deletion. Target result is claimed once before effects; interrupted passes require inspection, partial removal halts that target for future passes, and unchanged blocked conditions never justify a wider deletion. The pass has an 80-second admission budget plus the last admitted target's bounded checks. One attempt can still span several monitor seconds; it is not an immediate interrupt or real-time guarantee. Cached target allocations can overstate reclaimable APFS/shared blocks. Receipts distinguish verified target removal and observed total disk-free change; the latter includes other host activity.

Private policy/results live under ignored `.tmp/mac-operator/auto-cleanup-*`. `health` exposes policy and latest results; scheduled snapshots project the previous cleanup result, with a deduplicated incident if cleanup is blocked while disk is low. Scheduled cleanup remains separate from manual diagnostics, which never trigger it. A completed pass with blocked targets is PARTIAL, not successful cleanup.

The initial live pass was blocked and deleted nothing. It identified overbroad process gating and slow metadata traversal, which were corrected before a controlled second pass. Current activation and actual reclaimed-space evidence must be taken from the latest live receipts, not this implementation description. Existing native notification visible delivery remains unverified. The already-scheduled 2 November Mac audit can review scope, quota, expiry, actual benefit and persistent blockers; no extra automation was created.

Live verification: the controlled pass removed Homebrew downloads (45,744,128 allocated bytes), pip cache (27,885,568), and Apple Help cache (45,748,224): 119,377,920 bytes total, about 114 MiB. Observed host free-space increase during that pass was 112,750,592 bytes and includes concurrent activity. Subsequent checks found those paths absent; npm/node-gyp remained blocked by npm, VSCode ShipIt by open files, and Codex Installation by active updaters. The disk emergency remains unresolved at about 1.9 GiB free. Docker Desktop 4.97 is installed, but its roughly 21 GiB internal image has not been relocated. Relevant Mac tests: 88 passed.

## Operator hardening, 2026-11-02

The existing LaunchAgent and cleanup grant are unchanged. No new cleanup was run for verification.

Notifications now inspect all retained receipts for expiry and eligibility before selecting at most 100 oldest due events, with a 25-second processing budget (one in-flight channel call can exceed it). A separate nonblocking consumer lock prevents concurrent sends. Event identity uses incident, transition, snapshot time and persisted transition sequence, so retrying after an interrupted incident checkpoint reuses the event. Local attempts and remote retry reservations are saved before effects. Unknown remote delivery can still duplicate after a timeout; this is best effort, not exactly-once. Per-incident delivery has a one-hour cooldown; disconnected remote transport uses the same delay without consuming its three-send allowance. Newer pending transitions supersede older pending transitions; legacy receipts use message identity. Receipts are retained rather than deleted during delivery. Suppression can delay recovery notifications; channel submission does not prove visible display.

Cleanup health projects RUNNING_UNCONFIRMED for up to 120 seconds, then INTERRUPTED_REQUIRES_INSPECTION; missing/future start times also require inspection. This is age-based diagnosis, not proof of a dead process. Unfinished passes block before policy, disk, quota and interval checks, never reset or auto-retry. Completed target checkpoints now preserve progress during a later interruption. Existing incomplete receipts remain unchanged for inspection.

Daily Codex measurement now uses sequential slices over all direct entries, including non-date directories and loose files. FULL keeps the existing 48-second budget, LIGHT uses 12 seconds; each du is bounded to three seconds. Each completed/failed category is checkpointed in `codex-growth-progress.json`. The oldest attempted category rotates behind unattempted categories, preventing one timeout or recent-date selection from starving old data. Discovery is capped at 500 direct entries. Timeout, denied, symlink and other-device entries remain errors/unknowns; historical successful category evidence is retained separately after a failed refresh.

`measured_allocated_bytes` is a partial subtotal of successful categories within 36 hours. `allocated_bytes` is populated only with complete inventory and fresh coverage of every discovered entry; categories expose their timestamps and status. Health exposes coverage, measurement age, freshness and inventory completeness. Aggregate growth comparisons across sequential slices are disabled; only comparable category timestamps can support a growth signal. A partial slice cannot prove whole-workspace growth or recovery. Hardlinks across categories and APFS shared blocks can overcount actual physical use; these are allocated-block estimates, never reclaimable space. A very large single category can repeatedly time out, and full coverage may remain unavailable under the existing daily frequency. Further subdivision would need a separate bounded follow-up.

Verification uses synthetic notification callbacks, fixture cache directories and temporary workspaces. Actual channel visibility, live remote delivery and post-reboot recovery remain unverified.

## Shared observer budget and cleanup checkpoints, 2026-11-02

The observer now uses one cooperative monotonic 130-second budget, leaving a nominal 20-second margin inside the existing bootstrap's 150-second subprocess timeout. Cleanup inherits the earlier of that deadline and its existing 80-second ceiling. No phase gets a fresh observer budget. Native diagnostic commands, local notification commands, Telegram requests, cache activity probes, du and weekly-preview admission consume the remaining time. Expensive work is not admitted after exhaustion; tick records TIME_LIMIT, and health exposes it. This does not change launchd settings, cadence, grants, quota, target allowlist or existing unfinished receipts.

Each newly admitted cleanup has PID, unique run ID, phase, fixed target name, wall timestamps, remaining seconds and a bounded phase list. It checkpoints before and after fingerprint/activity/quota/executor/removal boundaries to both latest state and a separate private `auto-cleanup-runs/<run-id>.json` history, so later runs cannot overwrite that run's journal. Atomic state writes and the executor's pre-effect claim are flushed and fsynced. Failure to checkpoint before effects blocks the executor. An exception is recorded by class only, without exception text. Unexpected failure becomes FAILED_REQUIRES_INSPECTION; budget exhaustion within an admitted pass becomes TIME_LIMIT_REQUIRES_INSPECTION. Both retain the no-automatic-retry latch alongside RUNNING. Insufficient time before admission returns DEFERRED_TIME_BUDGET without changing the previous receipt. A hard termination still leaves the last saved RUNNING phase for inspection.

Removal requires at least 15 seconds of shared budget both before quota reservation and after revalidation, immediately before the pre-effect claim. Quota already reserved when a later checkpoint/revalidation fails remains conservatively charged; no automatic refund or retry is inferred from uncertain effects. Completed executor receipts remain independent evidence if a later callback fails. This is cooperative time control, not a real-time guarantee: a blocked filesystem syscall or an in-progress rmtree cannot be forcibly bounded by the helper. The outer bootstrap timeout remains the last boundary; a hard kill or power loss can still interrupt work. The new journal makes the last attempted boundary visible, not a proof that an unrecorded effect was impossible.

Verification uses temporary cache fixtures and inert network callbacks. It includes inherited deadlines, late admission, failure/hard interruption, phase/PID/history retention, no-effect checkpoint failure, shared command timeouts, exhausted revalidation reserve, and unchanged no-retry behavior. The old real RUNNING receipt remains untouched and blocked; no real cleanup was started or unblocked for this change. Live interruption/deletion acceptance remains unverified.
