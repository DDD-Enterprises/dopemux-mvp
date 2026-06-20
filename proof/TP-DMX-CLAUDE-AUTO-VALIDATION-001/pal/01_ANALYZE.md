# 01 — Analyze · TP-DMX-CLAUDE-AUTO-VALIDATION-001

**Mode:** evidence substitute (PAL live: NOT_RUN — pal MCP not bound in Grok session)  
**analysis_type:** architecture  
**confidence:** high (repo-primary evidence)

## Strategy

Map dopemux-mvp as a **Claude automation platform** (not a single-product repo like adOps):
central dispatcher → hook modules → slash commands → MCP catalog → child-worktree templates.

## Findings

### Strengths

1. **Single dispatcher pattern** — All 11 lifecycle events route through `src/dopemux/claude/native_hooks.py` (`.claude/settings.json` uses one command). Helper modules in `.claude/hooks/` follow try-import + no-op fallback. Matches `design-dcp-mcp-skills-hooks-2026-06-10.md` invariant #2.
2. **DCP seam complete** — Design doc listed 5 skills + 4 hooks; all exist on disk (`proof/bundle.md`, `mcp/doctor.md`, `dcp/doctor.md`, `dcp/denylist-check.md`, `tp/validate.md` + four hook modules).
3. **Orchestrator-native surface** — 18 `/dx:*` commands + task-orchestrator in per-worktree `.mcp.json`. Callable surface inventory precedent (`proof/TP-DMX-ORCH-CS-P1`).
4. **MCP scope model** — `mcp_catalog.yaml` cleanly separates singleton vs per-worktree; `dopemux mcp init/doctor` CLI exists.
5. **Proof discipline** — `/proof:bundle` + `proof_tracking_guard` + CI validator close the silent-drop gap.

### Gaps (child-repo / template layer)

1. **No `src/dopemux/templates/init/.claude/` child scaffold** for TaskX repos (adOps, etc.) with: task-packet skill, verify-gates, project-conventions, block-secrets hook snippets.
2. **`pal_validation.json` is empty** (`routes: []`) — Repo Truth Extractor baseline not wired to automation validation routes.
3. **PAL singleton vs worktree** — PAL in catalog as singleton (`pal-stdio` docker exec); not in worktree `.mcp.json`. Correct for platform; child repos inherit via global `~/.claude.json`.
4. **Duplication risk** — New "skills" must not recreate `/dx:*`, `/proof:bundle`, or DCP hooks. Extension point = templates + Claude-only background skills.

### Issues (severity)

| ID | Severity | Finding |
|----|----------|---------|
| A1 | medium | task-orchestrator HTTP health unreliable (JVM slow/stuck) blocks orchestrator load |
| A2 | low | `pal-mcp-server` container runs `sleep infinity` — not the HTTP PAL service |
| A3 | medium | Child repos (adOps) lack `.claude/` — automation value trapped in platform repo |

## Conclusion

**PASS** for platform automation architecture. **CONDITIONAL** for cross-repo template rollout. Next: thinkdeep on TaskX alignment, secaudit on secrets/MCP, challenge on deferred hooks.