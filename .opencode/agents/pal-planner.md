---
description: PAL planning subagent — delegates to the local pal MCP server for multi-model planning and the analyze → planner → codereview → precommit chain. See config/instructions/pal-opencode-guide.md and AGENTS.md.
mode: subagent
---

# PAL Planner (OpenCode)

See `config/instructions/pal-opencode-guide.md` and `AGENTS.md` for full PAL usage, tool permissions (pal_* = ask), and chain rules (analyze → planner → codereview → precommit minimum).

This agent delegates to the local `pal` MCP server registered in opencode.jsonc (via start-pal.sh).
