# Retained YouTube Radar runtime prerequisite

This PR preserves the already locally used read-only Radar runtime needed by the
Framewright exchange. It was absent from this repository's main branch. Only the
runtime, schemas, configuration, wrappers and synthetic tests needed for that
route are included; existing private acquisitions, tokens and intake state stay
outside Git. This is not a new deployment or a claim of autonomous weekly success.

`bin/youtube-intelligence` supports explicit sourced research, read-only YouTube
acquisition, observational analysis and separately preregistered experiments.
It has no upload/edit endpoint. Google client packages are optional in
`requirements-youtube.txt`; JSON Schema runtime dependencies are pinned in
`requirements-dev.txt`. Reuse an existing private environment or install only
when operating this route. OAuth credentials/tokens belong in ignored local state.
`auth` is a separate owner-authorised operation; tests do not authenticate.

The checked-in channel configuration identifies the owner channel; changing it
requires an explicit operator choice. API/research budgets, source freshness,
account/channel checks and retrospective-experiment rejection are retained.
A research menu does not authorise production. Read-only APIs still require
connectivity, valid scopes and actual availability; missing revenue is not zero.

[Exchange and opt-in hooks](framewright-exchange.md) describe the added seam.
No new scheduler is created. Local files and successful synthetic tests do not
establish public visibility, audience outcomes, monetisation or a future run.
