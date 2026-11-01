# /rfc:lint
Lint an RFC using the LLM checklist + local linters.

1) Load RFC content; run the RFC/ADR checklist (front-matter, required sections).
2) If MCP shell/file tools are available, run: `pre-commit run -a`.
3) Emit PASS/FAIL with numbered blocking fixes and an auto-fix front-matter block if needed.
