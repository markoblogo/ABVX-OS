# Experimental provider contract

The harness exposes only the four operations needed to compare bounded providers:

```text
prepare(context) -> prepared_context
run(prepared_context, fixture) -> run_result
collect(prepared_context, run_result) -> collected_result
cleanup(prepared_context) -> None
```

`context` contains the bakeoff, candidate, fixture, budget, and evidence destination. A provider must not widen the requested scope, perform remote-agent execution, persist mission state, schedule work, or continue after the bounded run. `run_result` reports exit status, duration, stdout/stderr references, and artifact references. The native baseline provider executes a local argv command supplied by the fixture.

Provider selection is experimental only. A result never adopts, installs, or permanently integrates a provider; the bakeoff result ends with `STOP_FOR_HUMAN_DECISION`.
