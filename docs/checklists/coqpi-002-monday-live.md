# COQPI-002 Monday live validation checklist

Scheduled not before: **Monday 2026-08-10**
Gate: **WAITING_FOR_HUMAN**
Input/output preference: **macOS system default**
Fallback: manual input selection in CoqPi Debug / Mic controls

## Before Start

- [ ] Open CoqPi; do not open a real third-party call.
- [ ] Confirm macOS input and output are the intended system-default devices.
- [ ] In CoqPi, confirm the key/config indicator is actionable and the readiness card is not falsely reporting a completed live call.
- [ ] Prepare one synthetic owner script, for example: “Bonjour, I am testing the call assistant. Can you summarize the next step?”
- [ ] Confirm no confidential or third-party conversation data will be spoken.

## Controlled smoke: 30–90 seconds

- [ ] Start realtime once.
- [ ] Observe connection state: connecting → connected/listening.
- [ ] Speak the synthetic text.
- [ ] Record time to first usable transcript, continuity, and obvious quality issues.
- [ ] Observe the assistant/context response and whether it is fresh, concise, and relevant.
- [ ] Trigger one safe recoverable interruption if available; do not corrupt credentials or configuration.
- [ ] Verify failure is visible and the UI does not remain falsely READY.
- [ ] Verify recovery or record the actionable error.
- [ ] Stop realtime.

## Evidence and decision

- [ ] Record device, provider, duration, transmitted data, persistence, and artifact locations.
- [ ] Confirm no raw audio or raw transcript was added to Git/evidence.
- [ ] Classify exactly one: `READY_FOR_CONTROLLED_REAL_CALL`, `CONDITIONALLY_READY`, or `NOT_READY`.
- [ ] Keep the mission gate closed until the owner explicitly accepts the classification.
