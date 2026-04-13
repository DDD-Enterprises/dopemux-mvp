# /adr:new
Create a new MADR-style Architecture Decision Record and save it under `docs/90-adr/`.

**Usage**
- `/adr:new "Adopt feature hubs for cross-feature docs"`
- `/adr:new "Use microservices architecture"`

**What you do**
1) Generate the next ADR number (look for existing `docs/90-adr/ADR-####-*.md`; if tools cannot list files, ask me to run `python scripts/adr_new.py "<Title>"`).
2) Slugify the title, and create: `docs/90-adr/ADR-####-YYYY-MM-DD-<slug>.md`.
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
7) Remind me to link affected docs and run `python scripts/docs_manifest.py`.
