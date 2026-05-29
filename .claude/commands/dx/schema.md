---
description: View task-orchestrator schemas, note requirements, and skill pointers from config.yaml (READ-ONLY)
arguments: "[optional: schema/type name to focus on, e.g. task-packet]"
allowed-tools: Read, Grep
model: claude-sonnet-4-5
---

# /dx:schema — Schema Inspector (READ-ONLY)

**Authority**: task-orchestrator schema config at `.taskorchestrator/config.yaml` is contract-sensitive and ADR-gated per AGENTS.md §6. This command is **strictly read-only** — it VIEWS schemas; it MUST NOT edit them. Adapted from upstream `manage-schemas` skill (TP-CS-101 / Path B), deliberately narrowed to read-only because Dopemux treats schema edits as ADR-gated. To CHANGE a schema, open an ADR + get operator authorization; do not use this command.

## Phase 1 — Parse arguments
`$ARGUMENTS` may name a schema/type (e.g. `task-packet`, `bug-fix`, `audit-pack`) to focus on. Empty → list all schemas.

## Phase 2 — Read (read-only)
1. Locate the config: `.taskorchestrator/config.yaml` (walk up from cwd if in a worktree). If absent, report that and stop (see Error handling).
2. `Read` the file. Parse the `work_item_schemas:`, `traits:`, and `schemas_metadata:` sections.
3. If a name was given, focus on that schema; otherwise enumerate all.

## Phase 3 — Render (ADHD-scannable)
For each schema in scope show:
- Schema/type name + lifecycle mode (from `schemas_metadata`).
- Required notes per phase (queue/work/review), each with its `key` and `skill:` pointer (e.g. `analyze → pal:analyze`, `proof-bundle → verify`).
- Which note gates which transition (notes gate `start`/`complete`).
Render as a compact per-schema table. Highlight the `proof-bundle` complete-gate where present.

## Phase 4 — Footer
`Next actions:` (≤3):
- `/dx:context <id>` — see which notes a specific item still needs
- `/dx:note <id> <key>` — fill a required note
- To CHANGE a schema: open an ADR (contract-sensitive — not editable here)

## Error handling
- `.taskorchestrator/config.yaml` not found → report: "No schema config on this branch — schemas are inactive here; the orchestrator falls back to the default schema (proof-bundle gate only). Config lives on the task-orchestrator-claude-surface series branch." Do not fabricate schema contents.
- Malformed YAML → report the parse error location; do not guess.

## Success criteria
Operator sees the active schemas, their note requirements, and skill pointers, in one read-only view — with zero risk of mutating the contract-sensitive config.

## Notes for Claude
NEVER use Edit/Write on `.taskorchestrator/config.yaml` from this command — it is read-only by design. The `skill:` pointers shown here are the same ones the `skill-enforcement` PreToolUse hook reads to enforce skill invocation on note-filling.
