# /adr:new
Scaffold a MADR-style Architecture Decision Record and save it under `docs/90-adr/`.

**Usage**
- `/adr:new "Adopt feature hubs for cross-feature docs"`

**What you do**
1) Generate the next ADR number (look for existing `docs/90-adr/ADR-####-*.md`; if tools cannot list files, ask me to run `python scripts/adr_new.py "<Title>"`).
2) Slugify the title, and create: `docs/90-adr/ADR-####-YYYY-MM-DD-<slug>.md`.
3) YAML front-matter:
   id: adr-####
   title: <Title>
   type: adr
   status: proposed
   date: today
   owner: @hu3mann
4) Body sections: Context, Decision, Consequences.
5) If file-write is available via MCP, CREATE the file. Otherwise return the Markdown.
6) Remind me to link affected docs and run `python scripts/docs_manifest.py`.
