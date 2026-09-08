# Professional role routing

ABVX-OS routes a request to a small set of professional role profiles before selecting model or tool execution. A role changes the working stance, relevant context, deliverable shape, and escalation boundaries. It does not grant authority, tools, memory, or permission to act.

## Current implementation

The canonical registry is `registries/professional-roles.json`. It currently includes:

- personal assistant as the default coordinator;
- career advisor, personal coach, wellbeing coach, fitness coach, business strategist, and financial advisor;
- researcher, writer, and publishing manager;
- senior software engineer and software architect.

The publishing manager routes justified book and channel visuals through `books/factory/skills/publishing-visual-explainer/SKILL.md`. The skill selects the smallest useful chart, diagram, infographic, or illustration route and keeps source, rights, technical QA, and human visual approval explicit.

Use:

```sh
./bin/abvx role list
./bin/abvx role inspect researcher --json
./bin/abvx role route --text "Исследуй рынок Amazon и помоги написать книгу" --json
```

Routing is deterministic and local. It returns one primary role and up to two supporting roles. It does not call a model, retain the request, load cross-domain memory, or execute the proposed work.

## Interaction model

1. The personal assistant receives an unclassified request.
2. The router selects the smallest useful professional set.
3. Only the selected role profile and task-specific evidence are loaded.
4. The role prepares advice, research, a draft, or an isolated implementation according to its mode.
5. Existing source/action policy determines whether any proposed action may run.
6. A specialist hands back a compact result instead of retaining broad control of the conversation.

For compound work, roles form a bounded sequence. Example: researcher produces a sourced evidence pack, writer uses the approved pack, publishing manager prepares the channel package, and the owner approves publication. One role does not silently inherit another role's context or authority.

## Donor adaptation

Professional prompts from `msitarzewski/agency-agents` are admitted as pattern sources only. ABVX may reuse role decomposition, workflow stages, deliverable templates, and escalation ideas under the MIT license. It does not import the full prompt corpus or accept donor claims, pseudo-memory, tool declarations, fixed KPIs, or authority assumptions without review.

Each promoted role should retain:

- purpose and trigger evidence;
- allowed context and memory scope;
- expected deliverables;
- source/action authority boundaries;
- donor provenance;
- representative routing and outcome fixtures.

Model-backed role execution remains a separate capability. It should be added role by role only when a real workflow requires it and the output can be evaluated.
