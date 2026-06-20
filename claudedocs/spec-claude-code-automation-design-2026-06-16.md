# Claude Code Automation — Platform + Child-Repo Design

**Date:** 2026-06-16  
**Status:** DESIGN_APPROVED (validation tree)  
**Repo:** dopemux-mvp  
**Proof:** `proof/TP-DMX-CLAUDE-AUTO-VALIDATION-001/`  
**Related:** `claudedocs/design-dcp-mcp-skills-hooks-2026-06-10.md`

---

## 1. Context

dopemux-mvp is the **Claude automation platform** for ADHD-optimized development. It already ships:

- Central hook dispatcher (`native_hooks.py`)
- 10 hook modules, 121 slash commands, 6 subagents
- DCP skills/hooks (2026-06-10 design — fully implemented)
- MCP catalog with singleton + per-worktree servers
- Task-orchestrator `/dx:*` surface

Child repos (e.g. adOps) inherit MCP via `dopemux mcp init` but lack `.claude/skills/` templates for TaskX workflows.

This spec defines the **validated unified catalog** and the **platform/child split** for future implementation.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│ dopemux-mvp (platform)                                   │
│  native_hooks → DCP guards → orchestrator enforcement    │
│  mcp_catalog.yaml → dopemux mcp init → child .mcp.json   │
│  templates/init/.claude/skills/  (NEW — phase 1)         │
└──────────────────────────┬──────────────────────────────┘
                           │ worktree init
                           ▼
┌─────────────────────────────────────────────────────────┐
│ child repo (e.g. adOps)                                  │
│  .mcp.json (conport, dope-memory, task-orchestrator)     │
│  .claude/skills/ from template                           │
│  CLAUDE.md TaskX directives (repo-owned)                 │
└─────────────────────────────────────────────────────────┘
```

**Invariant:** Never duplicate `/dx:*` or DCP hook logic in child templates.

---

## 3. MCP servers (validated)

### Platform (live)

| Server | Scope | Install |
|--------|-------|---------|
| conport | per-worktree | `dopemux mcp init` |
| dope-memory | per-worktree | `dopemux mcp init` |
| task-orchestrator | per-worktree HTTP | `task-orchestrator-http-singleton.sh` |
| pal-stdio | singleton | `docker compose up -d pal-stdio` |
| dope-context | singleton | `~/.claude.json` via `dopemux mcp sync-globals` |
| serena | singleton | same |
| gpt-researcher | singleton | docker exec |
| MCP_DOCKER | singleton | docker mcp gateway |
| grok_com_github | session | GitHub PR workflow |

### Child-repo optional (phase 2+)

| Server | When |
|--------|------|
| context7 | SDK-heavy repos (Textual, FastAPI, LiteLLM) |
| PostgreSQL MCP | Raw DB debugging (adOps `psycopg`) |

### Deferred

Playwright MCP, Sentry MCP, Memory MCP

---

## 4. Skills

### Platform (live — do not recreate)

| Command | Path |
|---------|------|
| `/proof:bundle` | `.claude/commands/proof/bundle.md` |
| `/mcp:doctor` | `.claude/commands/mcp/doctor.md` |
| `/dcp:doctor` | `.claude/commands/dcp/doctor.md` |
| `/dcp:denylist-check` | `.claude/commands/dcp/denylist-check.md` |
| `/tp:validate` | `.claude/commands/tp/validate.md` |
| `/dx:*` | `.claude/commands/dx/*.md` |

### Template skills (phase 1 — child scaffold)

| Skill | Invocation | Purpose |
|-------|------------|---------|
| task-packet | both | Execute scoped TP with verification gates |
| project-conventions | claude-only | Repo determinism + test commands |
| verify-gates | user-only | Mirror CI (pytest, ruff, mypy) |
| pal-routing | claude-only | Map task → PAL tool or `/dx:*` |

### Child-only

| Skill | Repo | Notes |
|-------|------|-------|
| adops-design | adOps | Symlink from `~/.agents/skills/adops-design/` |
| operator-runbook | adOps | Wrap `docs_operator/` |

---

## 5. Hooks

### Platform (live)

All wired via `native_hooks.py` try-import block — **no new settings.json entries**.

| Module | Role |
|--------|------|
| orchestrator_enforcement | Actor attribution, skill warnings |
| dcp_surface_guard | Red-lane hard block |
| dcp_denylist_nudge | Facade route advisory |
| mcp_health_probe | SessionStart MCP doctor |
| proof_tracking_guard | Proof write tracking |

### Child template snippet (phase 1)

`settings.json` fragment for PreToolUse block on `.env`, `.env.*`, `uv.lock` — injected at `dopemux init` when child has those files.

### Deferred

- packet-scope-guard (phase 2)
- module-scoped pytest PostToolUse (phase 2, perf-validated)
- permission-notify (optional macOS)

---

## 6. Subagents

### Platform (live)

`project-manager`, `developer`, `architect`, `researcher`, `python-mcp-expert`

### Template additions (phase 1)

| Agent | Role |
|-------|------|
| task-packet-reviewer | Diff vs TP allowlist |
| security-reviewer | Secrets + API auth (child repos with auth code) |

---

## 7. Plugins (recommended install)

```
/plugin install pyright-lsp
/plugin install pr-review-toolkit
/plugin install security-guidance
/plugin install commit-commands
```

Optional phase 2: `hookify` (encode DCP rules)

---

## 8. PAL routing skill (template content)

```yaml
---
name: pal-routing
description: Route analysis tasks to PAL tools or existing dx commands. Claude-only.
user-invocable: false
---
| Task type | Tool / command |
|-----------|----------------|
| Architecture review | pal.analyze |
| Complex debugging | pal.thinkdeep or pal.debug |
| Security audit | pal.secaudit |
| Pre-commit validation | pal.precommit |
| Plan breakdown | pal.planner |
| Challenge assumptions | pal.challenge |
| Next orchestrator item | /dx:next |
| Complete item | /dx:complete |
```

---

## 9. Orchestrator integration

- Load plan: `task-packets/load-plan-claude-automation.json`
- Binding: dopemux-mvp-rooted session
- Prerequisite: `curl http://127.0.0.1:7890/health` returns 200
- Idempotency: `actor` + `requestId` on `create_work_tree`

---

## 10. Risks & deferred items

| Item | Status |
|------|--------|
| packet-scope-guard | DEFER phase 2 |
| auto-pytest hook | DEFER (module-scoped only if added) |
| Playwright MCP | DEFER |
| PAL live re-run | Remediation: bind pal-stdio in Claude session |
| Orchestrator health | Remediation: JVM startup / logs investigation |

---

## 11. Acceptance (validation tree)

- [x] VALIDATION_MATRIX.md committed
- [x] PAL evidence substitutes in `proof/.../pal/`
- [x] This spec committed
- [x] Deferred impl plan committed
- [x] load-plan JSON committed
- [ ] create_work_tree executed (blocked on orchestrator health)