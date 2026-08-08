# Universal artifact intake

The canonical local boundary is `intake/items/<id>.json`. An IntakeItem preserves the raw text or URL, a small advisory classification, related entities, possible routes, suggested actions, clarification state, explicit links to related intake, status, and provenance.

The local CLI is intentionally narrow:

```text
./bin/abvx intake add --text "..."
./bin/abvx intake add --url "https://..." [--context "..." ]
./bin/abvx intake list [--json]
./bin/abvx intake inspect <id> [--json]
./bin/abvx intake clarify <id> --answer "..."
./bin/abvx intake link <id> <related-id>
```

URL intake stores the URL and supplied context without fetching it. Classification is advisory: low-confidence material becomes `NEEDS_CLARIFICATION` with one concise question. A clarification answer is persisted as evidence and moves the item to `PROPOSED`.

Routes name possible future destinations only. Intake does not change portfolio priority, create projects or tasks, publish content, run external candidates, or invoke any missing downstream system. Explicit `related_item_ids` provide the first deduplication/relationship mechanism; semantic or vector search is intentionally absent.

Future sources may include manual text, URLs, screenshots, documents, Telegram, email, LinkedIn, YouTube comments, project support channels, and GitHub discovery feeds. They are source concepts, not implemented integrations.
