# FOUNDATION-002 harness

The harness is a local command surface, not an orchestrator:

```sh
./bin/abvx validate
./bin/abvx bakeoff run foundation-002-baseline
./bin/abvx bakeoff inspect foundation-002-baseline
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Bakeoff manifests live under `fixtures/bakeoffs/<id>/`. Each fixture supplies a bounded argv command and expected exit status. Runs are written to `evidence/bakeoffs/<id>/runs/<run-id>/` with a run manifest, JSON Evidence records, stdout/stderr references, and copied declared artifacts. Run output is intentionally ignored by Git; manifests, fixtures, and directory placeholders remain reviewable.

The baseline provider executes local commands only. It does not invoke shells, remote agents, external candidates, background processes, databases, or persistent state.

## Optional local model check

The MPS worker is an opt-in, read-only consumer of an explicit request file:

```sh
./bin/abvx local-model answer --file docs/examples/local-model-request.json
```

It returns a bounded answer receipt and never treats model output as evidence,
approval, publication, or permission to act. Start the shared worker with
`python3 local_model_worker.py` from the local-models checkout.
