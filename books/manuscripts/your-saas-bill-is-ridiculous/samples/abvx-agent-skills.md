# ABVX Agent Skills

Most “AI productivity” systems eventually produce the same quiet disaster: the model can do many things, so nobody bothers to define how it should do them, what counts as proof, or when it should stop claiming success. ABVX Agent Skills exists for that exact mess.

The repository is a small skillpack for coding agents. Its stated purpose is not to add more raw capability, but to make existing capability less sloppy: smaller diffs, evidence-first debugging, shell-output compaction, verification gates, safer browser and release claims, bounded loops, and explicit handoff discipline. The important sentence in the README is the one that says these skills are not replacements for MCP or CLI tools. MCP connects services. CLI executes work. Skills provide the discipline layer that tells an agent which route to use, which checks are mandatory, and when repeated work deserves a reusable gate instead of another prompt.

This is not replacing a glamorous SaaS line item. It is replacing prompt mush, hidden team rituals, and the recurring expense of letting agents invent their own standard of evidence every time they touch a repo. That problem is less visible than a CRM invoice, but for teams already leaning on coding agents it is often more destructive.

I built this after watching agents repeatedly do the expensive part with complete confidence and then improvise the boring part badly. That context matters. It does not make the project automatically good. It merely explains why it exists.

If a team is not serious enough to care about verification, review, and smaller diffs, this will feel like paperwork. If the team is serious, it may feel like the first adult in the room.

**REPLACES** Ad-hoc prompt packs, private agent playbooks and some manual review checklists<br>
**COST** Very low runtime cost; the real cost is maintaining standards and using them consistently<br>
**SETUP** Low<br>
**BEST FOR** Teams already doing serious coding-agent work who need smaller diffs and stronger proof loops<br>
**VERDICT** TRY IT FIRST<br>
**URL** https://github.com/markoblogo/abvx-agent-skills
