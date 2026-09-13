# Contributing

ABVX-OS is an active personal operating-system reference implementation. Small fixes to the reusable core, schemas, validation, and documentation are welcome.

Before opening a pull request:

1. Read `AGENTS.md`, `ARCHITECTURE.md`, and the task-specific contract.
2. Check `registries/capabilities.json` and `registries/donor-capability-matrix.json` before adding a capability.
3. Keep personal data, credentials, generated state, and third-party copyrighted material out of the change.
4. Add focused regression coverage for behavior changes.
5. Run:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -q
./bin/abvx validate
agentsgen pack --autodetect --check --format=json
```

Describe the changed boundary, retained evidence, human gate, and any schema compatibility impact in the pull request.
