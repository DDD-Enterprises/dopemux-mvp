# DMX-DCP-MODEL-ROUTING-MVP-0000 — UNKNOWN_AND_CONFLICT_LEDGER.md

## UNKNOWNs (Preserved — Not Inferred)

| ID | Surface | Claim | Authority | Reason | Evidence |
|----|---------|-------|-----------|--------|----------|
| U001 | Task Orchestrator | Write authority | UNKNOWN | No runtime path verified; server.py exists but write contract not exercised | services/task-orchestrator/server.py |
| U002 | PR Steward | Mutation semantics | UNKNOWN | Workflow exists but execution not observed; forbidden in allowlist test | .github/workflows/pr-steward.yml + DCP test |
| U003 | ConPort | Write contract enforcement | UNKNOWN | HTTP/MCP surfaces exist; write behavior not verified | compose.yml:conport + conport_mcp_stdio.py |
| U004 | Dope-Memory | Append/reflection writes | UNKNOWN | Service exists; hard block prevents verification | .mcp.json + hard blocks |
| U005 | Desktop Commander | Terminal/FS mutation | UNKNOWN | Registered; mutation surface not exercised | registry.yaml |
| U006 | Agent Runtime | Authority across services/agents | UNKNOWN | Per AGENTS.md §6: "Repo-wide agent runtime authority remains UNKNOWN" | AGENTS.md + services/agents/ + src/dopemux/agent_orchestrator.py |
| U007 | dopecon-bridge | Event mutation authority | UNKNOWN | Bridge/proxy surface; not canonical authority per AGENTS.md | services/dopecon-bridge/ |
| U008 | Codex/AGY/Gemini CLI | Runtime invocation | UNKNOWN | Configs not observed; invocation paths not verified | No .codex/, no AGY config, Gemini via litellm only |
| U009 | Slash command write posture | /dx:save, /sc:implement, extract_commands | UNKNOWN | Commands exist; write behavior not verified | .claude/commands/ + src/dopemux/commands/ |
| U010 | DCP top-level commands | dopemux dcp/compile/run/collect/gate/promote/feedback/loop | UNKNOWN | Not present in CLI surface; only under kernel subcommand | uv run dopemux --help |

## CONFLICTs (Preserved — Not Normalized)

| ID | Surface | Conflict | Evidence | Impact |
|----|---------|----------|----------|--------|
| C001 | Current worktree | gemini-review.yml modified (forbidden prefix) | git status + pytest test_16 failure | DCP allowlist test fails; worktree violates red lane |
| C002 | Dopemux binary shim | mise shim points to itself (broken) | ls -la $(which dopemux) | Direct dopemux command fails; requires uv run |
| C003 | DCP test vs worktree | test_16 expects clean allowlist; worktree has gemini-review.yml | pytest failure message | Current branch cannot pass DCP contract test |
| C004 | Task Orchestrator authority | Claimed in docs; runtime path conflicted across app/main.py, task_orchestrator/app.py, Docker wiring | AGENTS.md §10 + TASK_ORCH_INTEGRATION_REPO_INVENTORY.md | Authority conflicted; not resolved |

## Summary

**UNKNOWNs**: 10
**CONFLICTs**: 4
**All preserved per packet rules. No normalization applied.**
