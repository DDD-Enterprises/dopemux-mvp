# /adr:new
Create a new MADR-style Architecture Decision Record and save it under `docs/90-adr/`.

**Usage**
- `/adr:new "Adopt feature hubs for cross-feature docs"`
- `/adr:new "Use microservices architecture"`

**What you do**
1) Choose the next ADR number from existing `docs/90-adr/adr-###-*.md` (named authority records use a descriptive `adr-<slug>.md` name with no number).
2) Slugify the title, and create: `docs/90-adr/adr-###-<slug>.md`.
3) YAML front-matter:
   ```yaml
   id: adr-####
   title: <Title>
   type: adr
   status: proposed
   date: today
   owner: @hu3mann
   derived_from: # if derived from an RFC, reference it here
   ```
4) Body sections:
   - **Context**: Current situation and problem
   - **Decision Drivers**: Forces that influence the decision
   - **Considered Options**: Alternative approaches with pros/cons
   - **Decision Outcome**: Chosen option and rationale
   - **Consequences**: Positive and negative outcomes
5) If file-write is available via MCP, CREATE the file. Otherwise return the Markdown.
6) If derived from an RFC, set `derived_from:` in front-matter.
7) Remind me to link affected docs and run `pre-commit run -a`.
