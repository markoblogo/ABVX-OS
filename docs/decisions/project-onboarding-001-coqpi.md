# PROJECT-ONBOARDING-001: CoqPi

## Result

CoqPi is onboarded as an independent active local MVP. Its canonical facts remain
in the CoqPi repository; ABVX records only a provenance-linked registry summary,
capability map, security boundary, and mission evidence.

## First bounded slice

The first technical slice prevents the readiness surface from claiming
`ready_for_real_mic` while the realtime path is not ready. The change is local to
CoqPi's readiness pack and has a regression test. It does not claim that a real
microphone or network call has been validated.

## Mission boundary

`COQPI-CALL-READY-001` was created through
`abvx_harness.mission_state.LoopXMissionStateProvider`. LoopX is used only for
mission-local state. The pilot proved normalized export, fail-closed corruption
handling, snapshot recovery, a closed human gate, terminal state, and no
accidental restart. No scheduler, daemon, agent execution, deployment, or
external call was started.

## Human gate

The pilot's local gate was approved only to verify the provider mechanics. A real
call remains `STOP_FOR_HUMAN_DECISION` pending explicit consent, device/provider
readiness, and live evidence.
