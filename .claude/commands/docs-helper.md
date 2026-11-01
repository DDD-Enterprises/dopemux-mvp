# /docs-helper
You are my short, practical guide to the dopemux-mvp docs system.
Show a 1-page refresher that includes:

**Documentation Structure (Diátaxis)**
- The folder layout and when to use each shelf
- What to write in each phase (brainstorm/design/impl/ship/operate)
- How Feature Hubs & cross-links work
- The rules: one Reference per concept, one How-to per task (+ platform variants), ADR for each decision

**RFC → ADR → arc42 Flow**
- When to write RFCs vs ADRs
- How to promote RFCs to ADRs
- When ADRs should reference arc42 documentation

**Available Commands**
- `/rfc:new "Title"` - Create new RFC for exploration
- `/rfc:lint <path>` - Validate RFC format and content
- `/rfc:promote <path>` - Promote RFC to ADR
- `/adr:new "Title"` - Create MADR-style ADR
- `/doc:pull "<ticket>"` - Pull context from MCP
- `pre-commit run -a` - Run all quality checks

Then list common mistakes and quick fixes.
When possible, attach `docs/03-reference/filesystem-guide.md` and `docs/90-adr/template-adr.md`.
