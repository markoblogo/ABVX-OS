# Disk prevention: bounded first stage

## Follow-up, 6 November

Preserved scheduled samples show swap allocations reaching 17 GiB, and 13.5 GiB immediately before the restart. After restart a native scheduled probe reported zero swap and pressure level 1. This establishes disk-backed memory as a substantial recurring contributor, not an attribution to a particular application. Top-process RSS does not measure swapped/compressed memory ownership.

Scheduled observations now include boot-session identity, swap bytes and comparable within-boot growth. Disk forecasts do not cross restarts; missing boot evidence suppresses the forecast. A stable incident key requests intervention at 4 GiB allocated swap, elevated pressure, or measured growth of at least 1 GiB/hour over at least 30 minutes. Unknown evidence does not resolve that incident. Full operator-owned retention scans defer when memory review is needed; applications are not terminated.

One fixed storage category is measured every half-hour when pressure is normal, with a three-second per-category timeout inside the shared observer deadline. The persisted pre-scan claim prevents immediate interrupted retries. Ten categories rotate, including Docker, Codex, npm, model locations and browsers. Complete comparable measurements support a growth rate; failed measurements remain unknown. This cadence can miss short bursts and is not a filesystem watcher.

Docker.raw was rechecked: logical size 245106737152 bytes, allocated 22488608768 bytes (about 20.94 GiB). Neither value is an exact APFS reclaim estimate. The existing native Docker relocation plan is still only a plan. No Docker move, application setting change or deletion was performed. Host mutation is blocked by the session's filesystem restrictions; approval alone does not change them.

Practical operating target: retain at least 40 GiB internally, use the existing external Work locations for new projects/models/output, and avoid simultaneous heavy applications/local model sessions. This target covers the observed 17 GiB swap excursion with headroom but cannot guarantee prevention under unrestricted workload. A native Docker relocation, after version/precondition checks and verification, is the largest presently measured structural candidate. Alerts and scan deferral alone are insufficient.

Cost: NORMAL. The existing LaunchAgent and native filesystem measurements are reused. No new service, dependency, cleanup or archive executor is introduced.

The scheduled sample includes `disk_policy` v1 with 40/25/15/8 GiB boundaries. A trend requires at least two prior samples on the same volume within two hours and a span of at least 30 minutes. The time to 8 GiB is a linear, short-window estimate, not a prediction guarantee. Incident transitions use the existing delivery pipeline. Daily/weekly Codex scans defer below 15 GiB; this protects only these operator-owned scans, not unrelated workflows. Automatic cache cleanup is suspended by the owner instruction and the previous cleanup receipt remains untouched. Manual cleanup entry points must not be run without renewed authorization and inspection.

Existing samples are retained for this investigation; this temporarily suspends their former seven-day pruning and must be resolved before indefinite operation. Notification display has not been verified. Volume history cannot identify which process caused a change. `du` allocated bytes are estimates, not unique APFS physical bytes or guaranteed savings. The existing sequential Codex category scanner reports partial coverage honestly.

## Review-only storage categories

* PROTECTED: source, Git, user files, databases, settings, credentials and active projects.
* REBUILDABLE: only individually verified caches, dependencies and builds whose consumers and restoration path are known.
* ARCHIVE_CANDIDATE: individually reviewed inactive content with a known owner and intended destination.
* UNKNOWN: anything not proven to satisfy a category, including uncertain usage and incomplete scans.

No size alone qualifies any path for removal or relocation. Directory modification time is not proof of last use. A review packet should record precise source, device, allocation estimate, last observed use and evidence limits, current activity, destination capacity, reversibility, dependencies and owner decision.

## Future archive gate, not an implemented executor

After a specific candidate and destination are approved, separately design and review a copy-only operation with a stable identity, safe path and symlink checks, destination space check, preserved metadata, resumable journal, integrity verification and source revalidation. No source deletion or application path change follows a copy automatically; each requires explicit approval. Interrupted or uncertain operations remain blocked for inspection. Until an executor is separately implemented and validated, this is a review procedure only.

Post-maintenance free-space comparison must use fresh measurements of the same internal volume and disclose concurrent activity. APFS clones, snapshots and open files can make a candidate's allocated size differ from actual space recovered.
