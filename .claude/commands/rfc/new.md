# /rfc:new
Create an RFC skeleton with YAML front-matter and sections.

1) Parse: `/rfc:new "Title" [--feature feat-id]`.
2) Compute next RFC number and path: `docs/91-rfc/rfc-####-<slug>.md`.
3) Write front-matter with fields: id, title, type=rfc, status=draft, author, created, last_review, sunset=+30d, feature_id, tags.
4) Insert sections: Problem, Context, Options (pros/cons table), Proposed Direction, Open Questions, Risks, Timeline, Reviewers.
5) If MCP file-write is available, create the file; otherwise return Markdown for manual paste.
6) Suggest next steps: `/rfc:lint <path>`, `/rfc:promote <path>`.
