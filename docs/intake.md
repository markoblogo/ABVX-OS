# Universal artifact intake

The canonical local boundary is `intake/items/<id>.json`. An IntakeItem preserves the raw text or URL, a small advisory classification, related entities, possible routes, suggested actions, clarification state, explicit links to related intake, status, and provenance.

The local CLI is intentionally narrow:

```text
./bin/abvx intake add --text "..."
./bin/abvx intake add --url "https://..." [--context "..." ]
./bin/abvx intake list [--json]
./bin/abvx intake inspect <id> [--json]
./bin/abvx intake review [--json]
./bin/abvx intake clarify <id> --answer "..."
./bin/abvx intake accept <id> [--reason "..."]
./bin/abvx intake reject <id> [--reason "..."]
./bin/abvx intake watch <id> [--reason "..."]
./bin/abvx intake archive <id> [--reason "..."]
./bin/abvx intake promote <id>
./bin/abvx intake link <id> <related-id>
```

URL intake stores the URL and supplied context without fetching it. Classification is advisory: low-confidence material becomes `NEEDS_CLARIFICATION` with one concise question. A clarification answer is persisted as evidence and moves the item to `PROPOSED`.

The lifecycle is explicit:

`RECEIVED / NEEDS_CLARIFICATION / PROPOSED -> ACCEPTED | REJECTED | WATCH -> PROMOTED`

`ARCHIVED` is terminal. Acceptance, rejection, keep/watch and archive are human decisions recorded with actor, timestamp, reason and provenance. Promotion is allowed only for `ACCEPTED` items, is human-triggered, and is idempotent.

Existing canonical destinations are deliberately small: content opportunities, project references, portfolio considerations, and the existing external candidate registry. Every promoted record stores `source_intake_id`; the IntakeItem stores the destination type and ID. Portfolio considerations always carry `priority_effect: NONE` and never activate or reprioritize a project.

Routes name possible future destinations only. Intake does not change portfolio priority, create projects or tasks, publish content, run external candidates, or invoke any missing downstream system. Explicit `related_item_ids` provide the first deduplication/relationship mechanism; semantic or vector search is intentionally absent.

Future sources may include manual text, URLs, screenshots, documents, Telegram, email, LinkedIn, YouTube comments, project support channels, and GitHub discovery feeds. They are source concepts, not implemented integrations.
