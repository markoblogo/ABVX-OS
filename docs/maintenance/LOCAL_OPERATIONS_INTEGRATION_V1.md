# Local operations integration review v1

2026-10-20. Cost NORMAL. Documentation and bounded repository analysis; no new runtime, schedule changes, remote connection or automatic remediation authorized by this review.

## Actual process map

| Process | Trigger and owner | Evidence and learning | Current boundary |
| --- | --- | --- | --- |
| Mac monitor | Native user launchd, 300 seconds | Private samples, latest summary, request receipts | Background activation verified; Telegram disconnected; no alerts |
| Multi-Market Radar | Existing Codex `multi-market-radar-monday`, saved ACTIVE Monday 08:00 | Browser acquisition → validated run → external ranking/report → REVIEWED Learning Loop snapshot | Latest ordinary execution receipt found: 12 October; saved status alone does not establish next run/timezone or completion |
| KDP account audit | Existing Codex `kdp`, saved ACTIVE Monday 09:00 | Account/sales evidence | Distinct from external opportunity discovery; do not merge or cancel |
| T7 follow-up | Saved ACTIVE one-off `mmr-t7-u04-m01-b01-24-october` | Scoped panel and research-method learning | Preserve existing scope; not another full weekly Radar |
| YouTube Intelligence | Owner-terminal runner; no matching saved weekly automation found | API + research → report → prospective experiment evaluation | Real COMPLETE receipt `live-20261019T200214Z`; weekly activation still blocked |
| Publication/process learning | Explicit existing CLI/playbooks and approvals | Verified outcomes → selected private numeric export → Cortex review | Host health is not publication success or a trial; no automatic transfer |

This is an inventory of saved configurations and retained local receipts, not proof of punctual scheduling. Radar's missing newer ordinary receipt may mean no run, different evidence layout or incomplete recording. Investigate before classifying failure. Method pilots do not substitute for normal four-market acquisition. Detailed research/publishing contracts stay in their own playbooks.

## Principal findings and proposed sequence

| Priority | Finding and implication | Smallest useful change | Acceptance evidence |
| --- | --- | --- | --- |
| 1 | Manual sandbox samples overwrite a richer background latest projection | Separate scheduled/manual sample provenance and latest projections; present last complete evidence with age, alongside current partial results | A partial manual run cannot erase the last complete scheduled snapshot; no stale data presented as current |
| 1 | Saved ACTIVE schedules have no expected-run/receipt correlation | Read-only fixed workflow inventory with expected window, grace period, last valid receipt, and UNKNOWN/OVERDUE distinction | A missed weekly receipt is surfaced once; stale historical data cannot pass |
| 1 | Internal disk has about 14.9 GiB free out of 228.3 GiB; cleanup preview covers only Help cache | Owner-scoped read-only inventory of internal storage categories and approved cache candidates; no broad deletion | Estimate per candidate, protected-path exclusions, permissions failures shown; explicit concrete deletion gate |
| 2 | User can request weekly research, but there is no admitted trigger from the local operator | Prepare a narrow handoff to the existing Codex workflow, not a second research schedule | Unique command → accepted existing job → verified final report and learning receipt; unavailable browser/network yields BLOCKED |
| 2 | No proactive notification delivery or repeated-failure tracker | Add state-transition alerts through the eventual authenticated channel, with cooldown and recovery notice | One alert per incident, bounded retry, no repeated unchanged warnings; transport failure visible locally |
| 2 | Telegram code exists, but sender/replay behavior has not had full simulated or live coverage | Test wrong sender/chat, stale updates, duplicate delivery, interrupted reply, network loss and offset recovery before connecting | Rejected sender causes no action/reply; duplicates cause no second effect; secrets absent from receipts |
| 3 | Monitor state and executable reside on the external Work volume | Document volume dependency now; consider a user-local installed runtime only if unattended reliability requires it | Explicit owner-approved installation/update/rollback boundary; do not silently copy credentials or projects |
| 3 | Multiple domain learning systems have different contracts | Standardize a compact status projection that references existing domain evidence, leaving original schemas and gates intact | References and hashes preserved; no manufactured universal success score or trial counts |

No broad orchestrator, shared database, new cloud service or permanent model loop is justified. launchd owns host invocation; Codex owns current agent/browser research; each domain owns its completion and learning gates. The operator should join references and expose blockers rather than reproduce those systems.

## Proposed operational contract, not yet implemented

For each fixed workflow expose: workflow ID, trigger owner, observed schedule, last attempt, latest accepted completion, required evidence references, availability/blocker, and next owner action. This is a projection over existing receipts, not a new canonical ledger. Do not infer COMPLETE from an exit code alone. Radar requires report/ranking and reviewed learning, YouTube requires authentic acquisition/research/report, publication requires its original approval and production proof.

Interpretation can later use the existing conditional intelligence runtime only after a bounded command-routing task is admitted. A model may propose an allowed scenario; deterministic code must still enforce arguments, sender policy, approval, deduplication and target scope. Current exact phrase routing has zero model expense and no semantic authority.

## What this update changes

README, architecture, capability registry and Mac operator guide now reflect actual owner-installed monitoring. Existing playbooks are cross-linked below; their schedules and operating contracts are unchanged. No cleanup, automatic repair, new research run, external notification or Cortex export was performed.

## Implementation follow-through, 2026-10-20

Priorities 1–4 are implemented in the existing operator: source-separated observations with preserved last complete scheduled evidence; fixed domain freshness projection and bounded read-only Codex attempt metadata; transition incidents with local notification submission and bounded optional Telegram delivery; four protected cache preview locations. A real scheduled invocation completed with all probes and exit 0; a later manual sandbox run did not overwrite it. 24 targeted tests pass.

Radar's local target transcript records `turn_aborted` on 19 October at 11:19 Paris. The interruption explains the absent completed ordinary run; what caused that interruption remains unknown. Domain receipt integrity remains separate from scheduler attempt metadata.

Priority 5 has a durable handoff lifecycle: enqueue, single claim, fresh domain-evidence binding and cancellation. Automatic dispatch is BLOCKED by the unavailable supported Codex interface, not silently replaced by raw database/queue writes or a second scheduler. No actual research was started during implementation. The initial recommendations above remain historical analysis; the current operational contract is [Mac operator v1](MAC_OPERATOR_V1.md).
