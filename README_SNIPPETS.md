# README Snippets (AI)

<!-- AGENTSGEN:START section=readme_snippets -->
## Suggested snippet: AI docs

```md
## AI / LLMO docs

- Manifest: `llms.txt` (or `LLMS.md`)
- Runbook for agents: `docs/ai/how-to-run.md`
- Test guide for agents: `docs/ai/how-to-test.md`
- Architecture: `docs/ai/architecture.md`
- Data contracts: `docs/ai/data-contracts.md`
- ID repo handoff: `docs/ai/id-context.json`
```

## Suggested snippet: local checks

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -q
./bin/abvx validate
```
<!-- AGENTSGEN:END section=readme_snippets -->
