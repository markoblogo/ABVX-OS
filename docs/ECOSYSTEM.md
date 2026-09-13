# ABVX ecosystem contracts

ABVX-OS remains independently useful. Companion projects own separate layers and exchange reviewable files rather than sharing hidden authority.

| Project | Owns | ABVX-OS relationship |
| --- | --- | --- |
| [ID 0.5.2](https://github.com/markoblogo/ID) | Human preferences, privacy policy, portable human context | Optional policy-filtered owner context; ABVX-OS must not bypass ID export policy |
| [agentsgen 0.5.1](https://github.com/markoblogo/AGENTS.md_generator) | Repository instructions and compact agent context | Generates and checks the repo-local context pack from `.agentsgen.json` |
| [SET 0.5.0](https://github.com/markoblogo/SET) | Review-first workflow planning | Reads `.set.json` and exports a proposal; it does not execute ABVX operations |
| [ABVX Agent Skills](https://github.com/markoblogo/abvx-agent-skills) | Reusable agent work disciplines | Supplies optional role routing, role-pack design, verification, and context-control skills |
| [Git Tweet](https://github.com/markoblogo/git-tweet) | Release-to-social drafting and publication workflow | May observe a public ABVX-OS GitHub release; it receives no private portfolio or evidence data |

## Context composition

1. ID supplies the smallest policy-allowed human context when explicitly configured.
2. agentsgen supplies repository facts and commands from the current checkout.
3. ABVX-OS selects the smallest relevant professional role and task context.
4. SET may export a reviewed workflow plan around those layers.
5. Existing ABVX policy still decides whether any action is allowed.

No companion installs another, grants tool access, owns ABVX portfolio priorities, or converts a proposed plan into authority.
