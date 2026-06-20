# 02 — Thinkdeep · TP-DMX-CLAUDE-AUTO-VALIDATION-001

**focus_areas:** architecture, security, TaskX integration

## Hypothesis

dopemux-mvp should own **platform automation**; child repos (adOps) receive **thin templates** via `dopemux init` / worktree scaffold — not duplicate orchestrator or DCP machinery.

## Evidence chain

1. **AGENTS.md truth order** — Task Packet > runtime > docs. Automations that auto-edit outside TP allowlists violate truth order in child repos.
2. **DCP-RED-MERGE-SEAM-0001** — `dcp_surface_guard` hard-blocks red-lane paths. Any child-repo hook must delegate to same scanner CLI, not reimplement.
3. **Orchestrator actor attribution** — `create_work_tree` applies single top-level `actor` to all notes. Validation tree must include `actor: { id, kind: user }` + `requestId` UUID for idempotency.
4. **Superpowers workflow** — dopemux uses `claudedocs/` (not `docs/superpowers/`). Design spec path: `claudedocs/spec-claude-code-automation-design-2026-06-16.md`.

## Integration model

```
dopemux-mvp (platform)
├── native_hooks.py          ← all hook events
├── mcp_catalog.yaml         ← MCP registry
├── .claude/commands/dx/*    ← orchestrator surface
└── src/dopemux/templates/   ← child scaffold (GAP)

child worktree (e.g. adOps)
├── .mcp.json                ← conport, dope-memory, task-orchestrator (from init)
├── .claude/skills/          ← task-packet, project-conventions (TEMPLATE)
└── CLAUDE.md / AGENTS.md    ← TaskX directives (already present in adOps)
```

## Risks

| Risk | Mitigation |
|------|------------|
| Skills bypass TaskX scope | task-packet skill must read active TP allowlist; packet-scope-guard deferred to phase 2 |
| Duplicate dx commands | pal-routing skill points to `/dx:next` not reimplement |
| Orchestrator wrong workspace | Load plan comment: dopemux-mvp-rooted session; `TASK_ORCHESTRATOR_PROJECT_ROOT` set |

## Conclusion

**PASS** — platform/child split is correct. Implement templates in dopemux `src/dopemux/templates/init/`, not in adOps directly from this validation tree.