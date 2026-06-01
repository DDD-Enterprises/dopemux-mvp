# ConPort/note
Use **ConPort** to attach a structured note to the current workspace.

**Args**: `$ARGUMENTS` = `<TITLE> :: <CONTENT>`

**Steps**
1) Ensure ConPort is connected (it may defer DB init until first call). If a workspace_id is required, ask me to provide it.
2) Add a note linked to the current repo/workspace. Include current branch and timestamp.
3) Return the note id and a brief confirmation.

**Tools**: ConPort only.

> Token thrift:
- **ConPort**: prefer summaries/search with small `limit` (3–5) before full context.
