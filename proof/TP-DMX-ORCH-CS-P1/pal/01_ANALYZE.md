# 01 — Analyze · TP-DMX-ORCH-CS-P1

## Problem framing
The DMX-ORCH-CLAUDE-SURFACE series builds the Claude-facing surface over the task-orchestrator
MCP. P1 was nominally scoped as "surface schema + /dx: command definitions + boundary manifest."

## Key analysis finding (reframe)
Exploration of `origin/main` (HEAD `59b309f27`) established that almost all of the nominal
scope **already exists**:
- 18 `/dx:` command files in `.claude/commands/dx/` (8 read, 9 write, 1 composite).
- `.taskorchestrator/config.yaml` (schemas, traits, gate posture).
- `docs/03-reference/dx-command-authoring.md` (authoring contract).
- `docs/03-reference/orchestrator-note-filling-protocol.md` and two ratifying ADRs.

The 2026-05-28 deletion regression (PR #720) has been restored — all 18 commands are present
at HEAD.

The **single genuine gap**: no artifact catalogs which orchestrator tools the surface exposes,
classifies each read/write/destructive, maps each command to the tools it calls, and states the
read-surface boundary. Precedent exists: `docs/03-reference/systems/{conport,serena}/callable-surface-inventory.md`.

## Authority used
- Live task-orchestrator v3 MCP surface (14 tools) — runtime, outranks captured docs.
- `reports/task-orchestratorrepo-truth-pack/MCP_TOOL_MANIFEST.json` — upstream v2.2.0/13-tool
  `readOnlyHint`/`destructiveHint` annotations (reference for the 13 shared tools).
- `docs/03-reference/dx-command-authoring.md`; the serena/conport inventory precedent.

## Tool classification (from destructiveHint + live surface)
- `safe_read_only` (7): query_items, query_notes, query_dependencies, get_context,
  get_next_status, get_next_item, get_blocked_items.
- `write_non_destructive` (3): advance_item, create_work_tree, claim_item (claim_item inferred).
- `write_destructive` (4): manage_items, manage_notes, manage_dependencies, complete_tree.

## Conclusion
Narrow P1 from "build" to "catalog + bound the existing surface," following the inventory
precedent, with machine enforcement (user-directed): an independent manifest + read-only
validator + test. No edits to existing commands/config/ADRs.
