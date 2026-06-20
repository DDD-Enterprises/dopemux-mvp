# 05 — Planner · TP-DMX-CLAUDE-AUTO-VALIDATION-001

## Phased rollout (future implementation — DEFERRED)

### Phase 0 — Validation (THIS TREE) ✓

- Catalog + PAL evidence + design spec + load-plan JSON
- No `.claude/` or template code changes

### Phase 1 — Platform docs + template scaffold (MVP)

1. Add `src/dopemux/templates/init/.claude/skills/task-packet/SKILL.md`
2. Add `project-conventions/SKILL.md` (Claude-only)
3. Add `verify-gates/SKILL.md` (user-only, `disable-model-invocation: true`)
4. Add `pal-routing/SKILL.md` (Claude-only)
5. Add `src/dopemux/templates/init/.claude/settings.json.hook-snippet.json` — block `.env`/`uv.lock` only
6. Update `INSTALL.md` / `QUICK_START.md` with automation section
7. Wire `pal_validation.json` routes for automation catalog

**Deps:** none (additive)  
**Verification:** `pytest tests/` + `dopemux mcp doctor` + template dry-run

### Phase 2 — Child-repo pilot (adOps)

1. `dopemux mcp init` in adOps worktree
2. Copy template skills into adOps `.claude/skills/`
3. Symlink `adops-design` from `~/.agents/skills/`
4. Optional: module-scoped pytest hook snippet
5. Proof bundle `TP-ADOPS-CLAUDE-AUTO-PILOT-001`

**Deps:** Phase 1 merged  
**Verification:** adOps `uv run pytest -q` + `uv run ruff check`

### Phase 3 — Advanced (optional)

- packet-scope-guard hook + `ACTIVE_TP.json` convention
- hookify plugin rules export from DCP design
- context7 MCP in child `.mcp.json` for SDK-heavy repos

## Task-orchestrator validation tree

Loaded via `task-packets/load-plan-claude-automation.json` — 10 children, linear PAL → spec → plan → load gate.

## Stop conditions

- DCP-RED-MERGE-SEAM-0001 would be relaxed → STOP
- Orchestrator load without health check → STOP (document NOT_RUN)
- Implementing code in validation-only tree → OUT OF SCOPE