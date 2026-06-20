# Orchestrator Load — TP-DMX-CLAUDE-AUTO-VALIDATION-001

## Prerequisite

```bash
cd /Users/hue/code/dopemux-mvp
DOPEMUX_PROJECT_ROOT=/Users/hue/code/dopemux-mvp \
DOPEMUX_WORKSPACE_ROOT=/Users/hue/code/dopemux-mvp \
TASK_ORCHESTRATOR_HTTP_PORT=7890 \
  bash scripts/mcp-wrappers/task-orchestrator-http-singleton.sh

# Wait until healthy:
curl -sf http://127.0.0.1:7890/health
```

## Load command

Invoke `create_work_tree` via task-orchestrator MCP (or Claude `/dx:` session) with:

```json
{
  "actor": {
    "id": "dmx-claude-auto-validation-2026-06-16",
    "kind": "user"
  },
  "requestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "root": {
    "title": "DMX-CLAUDE-AUTO — Claude Code automation validation & design",
    "priority": "high",
    "tags": "dopemux,claude,automation,validation,supervised-only",
    "summary": "Validate unified Claude automation catalog; design spec + deferred impl plan; gate future MVP scaffold. Proof: proof/TP-DMX-CLAUDE-AUTO-VALIDATION-001/. Spec: claudedocs/spec-claude-code-automation-design-2026-06-16.md"
  },
  "children": [
    {"ref": "c_catalog", "title": "Compile unified automation catalog", "priority": "high", "tags": "dopemux,claude,catalog", "summary": "Merge platform surface + child-repo gaps; map to evidence."},
    {"ref": "c_pal_arch", "title": "PAL analyze: platform automation architecture", "priority": "high", "tags": "dopemux,claude,pal,analyze", "summary": "pal/01_ANALYZE.md"},
    {"ref": "c_pal_integrate", "title": "PAL thinkdeep: TaskX + orchestrator alignment", "priority": "high", "tags": "dopemux,claude,pal,thinkdeep", "summary": "pal/02_THINKDEEP.md"},
    {"ref": "c_pal_security", "title": "PAL secaudit: hooks + MCP exposure", "priority": "high", "tags": "dopemux,claude,pal,secaudit", "summary": "pal/03_SECAUDIT.md"},
    {"ref": "c_pal_challenge", "title": "PAL challenge: contested choices", "priority": "medium", "tags": "dopemux,claude,pal,challenge", "summary": "pal/04_CHALLENGE.md"},
    {"ref": "c_pal_plan", "title": "PAL planner: phased rollout", "priority": "medium", "tags": "dopemux,claude,pal,planner", "summary": "pal/05_PLANNER.md"},
    {"ref": "c_spec", "title": "Write design spec", "priority": "high", "tags": "dopemux,claude,design", "summary": "claudedocs/spec-claude-code-automation-design-2026-06-16.md"},
    {"ref": "c_impl_plan", "title": "Write deferred implementation plan", "priority": "medium", "tags": "dopemux,claude,plan", "summary": "claudedocs/plan-claude-code-automation-2026-06-16.md"},
    {"ref": "c_load_json", "title": "Finalize validation matrix + load-plan JSON", "priority": "medium", "tags": "dopemux,claude,proof", "summary": "VALIDATION_MATRIX.md + task-packets/load-plan-claude-automation.json"},
    {"ref": "c_orchestrator", "title": "Confirm orchestrator work tree loaded", "priority": "low", "tags": "dopemux,orchestrator", "summary": "query_items for DMX-CLAUDE-AUTO root."}
  ],
  "deps": [
    {"from": "c_catalog", "to": "c_pal_arch", "type": "BLOCKS"},
    {"from": "c_catalog", "to": "c_pal_integrate", "type": "BLOCKS"},
    {"from": "c_catalog", "to": "c_pal_security", "type": "BLOCKS"},
    {"from": "c_pal_arch", "to": "c_pal_challenge", "type": "BLOCKS"},
    {"from": "c_pal_integrate", "to": "c_pal_challenge", "type": "BLOCKS"},
    {"from": "c_pal_security", "to": "c_pal_challenge", "type": "BLOCKS"},
    {"from": "c_pal_challenge", "to": "c_pal_plan", "type": "BLOCKS"},
    {"from": "c_pal_plan", "to": "c_spec", "type": "BLOCKS"},
    {"from": "c_spec", "to": "c_impl_plan", "type": "BLOCKS"},
    {"from": "c_impl_plan", "to": "c_load_json", "type": "BLOCKS"},
    {"from": "c_load_json", "to": "c_orchestrator", "type": "BLOCKS"}
  ],
  "createNotes": true
}
```

## Status (2026-06-16)

| Step | Result |
|------|--------|
| HTTP singleton fix (`MCP_HTTP_PORT`, `MCP_HTTP_HOST=0.0.0.0`) | PASS |
| MCP `initialize` + `serverInfo` | PASS |
| `create_work_tree` | PASS — root `edfcd4e6-abbf-465f-8d3e-a7b55c08d6fa`, 10 children, 11 deps |

**Root cause fixed:** script used `MCP_PORT` but JVM reads `MCP_HTTP_PORT`. `MCP_HTTP_HOST=127.0.0.1` inside Docker caused empty HTTP replies on macOS.

## Retry / idempotency

Re-use the same `requestId` within ~10 minutes for idempotent `create_work_tree` retries.