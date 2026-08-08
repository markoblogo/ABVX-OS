# Resume COQPI-002

1. Read `state-export.json` and `../../../../../../docs/checklists/coqpi-002-monday-live.md`.
2. Confirm the state is `status=waiting_for_human`, `readiness_status=READY_FOR_LIVE_VALIDATION`, `scheduled_not_before=2026-08-10`, and the gate is open.
3. Do not rerun `record_coqpi_002_pre_live.py`; it is the creation/recording fixture and the mission is already known.
4. On Monday, use the existing `MissionStateProvider` boundary and `boundary/native-state.json` to record the human gate, bounded execution evidence, and outcome.
5. If the boundary reports integrity failure, stop. Do not recreate or bypass the known mission.
6. Keep `audio_transmitted=false` until explicit human approval and the controlled smoke actually begins.
