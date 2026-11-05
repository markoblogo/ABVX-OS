# Optional Framewright exchange v1

Local development,5November2026. The adapter minimises existing YouTube research,
receives owner-selected project associations and production/publication receipts,
and can export an existing hash-verified analytics report. It makes no API calls,
does not change intake status, register experiments, publish, or add a scheduler.

The two-film control linked `yt-pass2-muscle-scaffold` → `LIbkbgDCgKM` and
`yt-pass2-infradev-falsegreen` → `h3xC5FRlW30` as retrospective observations.
Repeated delivery kept two project links/two video mappings. Existing InfraDev
intake was referenced unchanged. Both analytics exports are pending because the
retained2November acquisition has no reports for these videos. Original project,
master, research, intake and existing adapter hashes were unchanged.

Evidence is private under the external studio's
`records/radar-framewright-contract-2026-11-05/`; runtime exchange state is under
`records/radar-framewright-exchange-v1/`. Neither is committed here.

## Automatic normal-run boundary

The owner subsequently authorised opt-in exchange at existing workflow boundaries.
`enable-auto --radar-root ROOT` writes private local configuration pointing to an
existing, channel-configured exchange. No new schedule/daemon is created.
Before normal `run` acquisition the hook receives Framewright messages and adds
known observational video IDs to the same existing acquisition. After a successful
run it exports research/menu and available per-video7/28-day calendar reports.
No extra acquisition is made, and a hook error leaves the primary run successful.
Run outcome and optional exchange status remain separate. Missing storage stays
pending and creates no internal fallback. Each pull is capped at250 peer outbox
files and100 tracked video IDs; manual rotation is required beyond that bound.
Framewright opts in each already selected project separately and pulls on saved
checkpoints. New ideas never auto-select or start a film.

Synthetic normal-run tests prove the integration with fake API responses, including
optional-hook failure isolation and unchanged API call counts with no linked films.
They do not prove a future autonomous scheduled run or mature audience feedback.

## Explicit commands

Choose an existing owner-controlled external exchange directory. There is no
internal fallback. Commands without `--apply` preview without writes.

```sh
bin/youtube-framewright-exchange --exchange "$EXCHANGE" status
bin/youtube-framewright-exchange --exchange "$EXCHANGE" --apply enable-auto --radar-root "$RADAR_ROOT"
bin/youtube-framewright-exchange --exchange "$EXCHANGE" --apply configure --channel-id "$CHANNEL"
bin/youtube-framewright-exchange --exchange "$EXCHANGE" --apply export-menu "$RESEARCH_JSON"
bin/youtube-framewright-exchange --exchange "$EXCHANGE" --apply receive "$MESSAGE_JSON"
bin/youtube-framewright-exchange --exchange "$EXCHANGE" --apply link-intake --project-id "$PROJECT_ID" --intake-id "$EXISTING_INTAKE_ID"
bin/youtube-framewright-exchange --exchange "$EXCHANGE" --apply export-analytics "$RETAINED_RUN" --project-id "$PROJECT_ID" --video-id "$VIDEO_ID" --report-label videos_7d
```

Each side owns its own outbox/state. Deliver the precise message JSON to the other
side's `receive`, and return the receipt. Delivery can be enabled at existing run/checkpoint boundaries after owner approval.
Existing runtime/schema dependencies are reused; no install or sibling runtime
import is needed. `youtube.py` only adds guarded opt-in run hooks; experiment gates and
`youtube_radar.py` remain unchanged.

[Envelope schema](../../schemas/framewright_exchange.schema.json) provides structural
validation; `framewright_wire.py` adds hashes and kind-specific semantic checks.
The wire/schema copies must match the Framewright counterparts at contract updates.
The1MiB state/message cap fails before commit; rotation is manual future work.
Local hashes detect corruption, not malicious senders: use trusted filesystem
ownership. Invalid envelopes return rejection without persisted acknowledgement.

Apply+processed marker commit together; receipt retries never reapply data and
receipts produce no further receipts. Unknown research/association remains pending;
conflicting identities are rejected; older status cannot overwrite current status.
Freeze changes need a separately reviewed migration, not editing IDs/state markers.

Retrospective bindings never become preregistered experiments. Even a prospective
link is only an owner before-production attestation; existing experiment approval
and `RETROSPECTIVE_BINDING_REJECTED` guards still apply. No automatic intake
promotion or experiment creation occurs.

Analytics exports require exact channel/project/video IDs and verified acquisition
digest. Per-video shards with `video` or `video,creatorContentType` are supported;
ambiguous duplicate rows are rejected. Calendar report periods/Pacific time are
retained; they are not upload-age matched7/28-day outcomes. Missing metrics are
null, missing rows pending. Revenue needs actual currency; channel-level revenue
is never allocated to a video. Synthetic snapshots are test-only and cannot enter
normal receiving state. Owner-reported publication is not independent verification
of visibility, transcode identity, audience response or monetisation.

Only YouTube is implemented, and there is no `started` event yet. Future prospective
production, actual mature reports, interpretation and the first actual scheduled run outcome remain
open. This adapter is not evidence of a closed autonomous learning loop.
