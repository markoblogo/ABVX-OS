# Five-minute quick start

## Requirements

- Git
- Python 3.11 or newer
- no API key for validation, portfolio inspection, or role routing

## Clone and verify

```sh
git clone https://github.com/markoblogo/ABVX-OS.git
cd ABVX-OS
./bin/abvx --version
./bin/abvx validate
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

## Inspect the system without changing state

```sh
./bin/abvx role list
./bin/abvx role route --text "Help me compare two product opportunities" --json
./bin/abvx portfolio inspect
./bin/abvx book-radar report pipeline
```

Role routing selects a working stance. It does not call a model, load private context, retain the request, or execute work.

## Commands that change local state

Intake decisions, content preparation/approval, playbook replay, Book Radar imports, and other write paths update versioned local records. Use a branch or disposable clone when learning those paths. Inspect the relevant contract first:

- `docs/intake.md`
- `docs/content-ops.md`
- `docs/provider-contract.md`
- `docs/professional-role-routing.md`

No command should publish, deploy, send a message, spend money, or modify another repository without the explicit policy and approval required by `docs/autonomy-policy.md`.

## Agent-ready repository context

The committed `.agentsgen.json` produces a compact repo context pack. With agentsgen 0.5.1 installed:

```sh
agentsgen pack --autodetect --check --format=json
```

The committed `.set.json` can be used with SET 0.5.0 to export a reviewable workflow proposal. SET does not apply the plan, commit files, or grant permissions.
