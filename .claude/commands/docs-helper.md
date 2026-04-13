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
- `mkdocs serve` - Serve local docs site

Then list common mistakes and quick fixes.
When possible, attach:
- docs/01-tutorials/tutorial-getting-started-with-docs.md
- docs/04-explanation/feature-docs-governance.md
- docs/03-reference/docs-structure-and-naming.md
- docs/templates/rfc.md and docs/templates/adr.madr.md when available
