# Validation Matrix — TP-DMX-CLAUDE-AUTO-VALIDATION-001

**Date:** 2026-06-16  
**Repo:** dopemux-mvp @ `/Users/hue/code/dopemux-mvp`  
**Scope:** validate + design only (no `.claude/` implementation)  
**PAL live calls:** NOT_RUN — see §PAL Status

---

## Platform baseline (already shipped)

| Surface | Count | Evidence | Verdict |
|---------|-------|----------|---------|
| Hook modules | 10 | `.claude/hooks/*.py` | PASS — wired via `native_hooks.py` |
| Slash commands | 121 | `.claude/commands/**/*.md` | PASS |
| Subagents | 6 | `.claude/agents/*.md` | PASS |
| Per-worktree MCP | 3 | `.mcp.json`: conport, dope-memory, task-orchestrator | PASS |
| Singleton MCP catalog | 10+ | `mcp_catalog.yaml` | PASS |
| DCP skills (design 2026-06-10) | 5/5 | `/proof:bundle`, `/mcp:doctor`, `/dcp:doctor`, `/dcp:denylist-check`, `/tp:validate` | PASS |
| DCP hooks (design 2026-06-10) | 4/4 | `dcp_surface_guard`, `dcp_denylist_nudge`, `mcp_health_probe`, `proof_tracking_guard` | PASS |

---

## MCP servers

| Server | Priority | Evidence | Verdict | Phase |
|--------|----------|----------|---------|-------|
| conport | P0 | `.mcp.json`, running `mcp-conport` | PASS | live |
| dope-memory | P0 | `.mcp.json`, running container | PASS | live |
| task-orchestrator | P0 | `.mcp.json`, HTTP singleton script | PASS | live @ :7890/mcp |
| pal-stdio | P0 | `mcp_catalog.yaml`, `mcp-pal-stdio` container | PASS | started 2026-06-16 |
| dope-context | P0 | `mcp_catalog.yaml:56-61` | PASS | singleton |
| serena | P1 | `mcp_catalog.yaml:49-54` | PASS | singleton |
| gpt-researcher | P1 | `mcp_catalog.yaml:70-78` | PASS | docker exec |
| GitHub (grok_com_github) | P1 | MCP profile tools present | PASS | PR workflow |
| context7 | P2 | Not in catalog | DEFER | child-repo optional |
| Playwright MCP | P3 | adOps uses Python playwright | DEFER | low ROI on platform |
| Docker MCP (MCP_DOCKER) | P1 | `mcp_catalog.yaml:98-103` | PASS | gateway |

---

## Skills / commands (gaps vs child repos)

| Item | Invocation | Evidence | Verdict | Phase |
|------|------------|----------|---------|-------|
| dx:* orchestrator surface | user | `.claude/commands/dx/` (18 commands) | PASS | live |
| /proof:bundle | user | `.claude/commands/proof/bundle.md` | PASS | live |
| /mcp:doctor | user | `.claude/commands/mcp/doctor.md` | PASS | live |
| /tp:validate | user | `.claude/commands/tp/validate.md` | PASS | live |
| pal-routing (Claude-only) | claude | PACKET_054 pattern; no platform skill yet | CONDITIONAL | MVP template |
| child-repo task-packet skill | both | adOps `docs/task-packets/`; no dopemux template | CONDITIONAL | MVP template |
| child-repo verify-gates | user | adOps CI mirrors; no template in `src/dopemux/templates/` | CONDITIONAL | MVP template |
| child-repo project-conventions | claude | adOps CLAUDE.md TaskX; template gap | CONDITIONAL | MVP template |
| adops-design symlink skill | both | `~/.agents/skills/adops-design/` | CONDITIONAL | child-repo only |

---

## Hooks (platform + extensions)

| Hook | Event | Evidence | Verdict | Phase |
|------|-------|----------|---------|-------|
| native_hooks dispatcher | all lifecycle | `.claude/settings.json`, `native_hooks.py` | PASS | live |
| orchestrator_enforcement | Pre/Post tool | `.claude/hooks/orchestrator_enforcement.py` | PASS | live |
| dcp_surface_guard | PreToolUse | `dcp_surface_guard.py` | PASS | live |
| proof_tracking_guard | PostToolUse | `proof_tracking_guard.py` | PASS | live |
| mcp_health_probe | SessionStart | `mcp_health_probe.py` | PASS | live |
| block .env / uv.lock (child) | PreToolUse | adOps has `.env`; no generic child template | CONDITIONAL | child template |
| pytest-changed (child) | PostToolUse | adOps 206 tests; perf risk | DEFER | challenge: module-scoped only |
| packet-scope-guard (child) | PreToolUse | needs active TP state file | DEFER | phase 2 |
| permission-notify | Notification | not in platform hooks | CONDITIONAL | optional UX |

---

## Subagents

| Agent | Evidence | Verdict | Phase |
|-------|----------|---------|-------|
| project-manager | `.claude/agents/project-manager.md` | PASS | live |
| developer | `.claude/agents/developer.md` | PASS | live |
| architect | `.claude/agents/architect.md` | PASS | live |
| python-mcp-expert | `.claude/agents/python-mcp-expert.agent.md` | PASS | live |
| security-reviewer (child) | adOps `api/auth.py`; no generic agent | CONDITIONAL | child template |
| task-packet-reviewer | orchestrator enforcement exists; no dedicated agent | CONDITIONAL | MVP |

---

## Plugins (Claude Code official)

| Plugin | Verdict | Phase |
|--------|---------|-------|
| pyright-lsp | PASS — Python platform | install |
| pr-review-toolkit | PASS — AGENTS.md PR flow | install |
| hookify | CONDITIONAL — encode DCP rules | MVP |
| security-guidance | PASS — secrets surfaces | install |
| commit-commands | PASS — git workflow | install |

---

## PAL status

| Tool | Status | Reason |
|------|--------|--------|
| analyze | NOT_RUN (live) | Session MCP `pal` server unavailable; evidence substitute in `pal/01_ANALYZE.md` |
| thinkdeep | NOT_RUN (live) | Same; substitute in `pal/02_THINKDEEP.md` |
| secaudit | NOT_RUN (live) | Same; substitute in `pal/03_SECAUDIT.md` |
| challenge | NOT_RUN (live) | Same; substitute in `pal/04_CHALLENGE.md` |
| planner | NOT_RUN (live) | Same; substitute in `pal/05_PLANNER.md` |

**Remediation:** `docker compose up -d pal-stdio` (DONE); invoke via `mcp_catalog.yaml` pal-stdio docker exec transport. Re-run live PAL when Claude session binds pal-stdio.

---

## Orchestrator load status

| Check | Status | Evidence |
|-------|--------|----------|
| HTTP singleton script | PASS | `MCP_HTTP_PORT` + `MCP_HTTP_HOST=0.0.0.0` fix |
| Container port map | PASS | `127.0.0.1:7890->7890/tcp` |
| MCP `initialize` | PASS | `serverInfo` from `mcp-task-orchestrator-current` v3.8.0 |
| `create_work_tree` | PASS | Root `edfcd4e6-abbf-465f-8d3e-a7b55c08d6fa` + 10 children |