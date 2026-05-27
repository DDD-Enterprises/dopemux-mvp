---
id: orchestrator-note-filling-protocol
title: Orchestrator Note-Filling Protocol (Cross-Agent Reference)
type: reference
owner: '@hu3mann'
last_review: '2026-05-27'
next_review: '2026-08-25'
status: active
applies_to: [codex, claude-code, copilot, custom-personas]
related:
  - adr-task-orchestrator-as-workflow-authority
  - adr-task-orchestrator-claude-surface-integration
  - AGENTS.md §5 (PAL chains), §9 (Proof and Finality)
---

# Orchestrator Note-Filling Protocol

**Status**: canonical. Linked from `AGENTS.md` (Codex), `.claude/CLAUDE.md` (Claude Code), `.github/copilot-instructions.md` (Copilot), `config/instructions/agents.instructions.md` (custom-agent), and `.claude/personas/*.agent.md` (personas) — all four agent surfaces inherit this protocol.

**Workflow guide reference**: [Task Orchestrator v3 workflow guide §5 + §5.6](https://github.com/jpicklyk/task-orchestrator/wiki/workflow-guide).

---

## What this document is

A single, agent-agnostic specification of how to drive the task-orchestrator MCP through its full work-item lifecycle. The protocol is the same whether you are Codex, Claude Code, Copilot, or a custom persona. Differences in invocation surface (slash commands, raw MCP calls, IDE menus) are vendor-specific; the underlying contract is universal.

If you are an agent: read this once, then act according to the protocol regardless of which environment you're running in.

---

## Core lifecycle

Every work item lives in one of five roles, advanced via explicit triggers:

```
queue → work → review → terminal
                  ↓         ↑
              (blocked) ────┘
                  ↑
               (resume)
```

Triggers (used in `advance_item(transitions=[{itemId, trigger, summary?, actor?}])`):

| Trigger | From | To | Notes |
|---|---|---|---|
| `start` | queue | work | Required queue-phase notes must be filled if schema gates |
| `start` | work | review (or terminal if no review notes) | Required work-phase notes must be filled |
| `start` | review | terminal | Required review-phase notes must be filled |
| `complete` | any non-terminal | terminal | ALL required notes across ALL phases must be filled — this is the gate |
| `block` / `hold` | any non-terminal | blocked | Saves previous role |
| `resume` | blocked | previous role | Restores saved role |
| `cancel` | any non-terminal | terminal (`statusLabel=cancelled`) | Bypasses gates |
| `reopen` | terminal | queue | Bypasses gates; clears statusLabel |

---

## The standard protocol

```
1. get_context(itemId=<uuid>)
   → read `guidancePointer` (and `skillPointer` if present in `schema`)
   → read `gateStatus.missing` (notes still required for this phase)

2. If skillPointer is set (e.g. "pal:analyze", "pal:codereview", "verify"):
   Invoke the named skill / MCP tool to produce content for the note.
     - "pal:*"  → mcp__pal__<name>
     - "verify" → assemble the AGENTS.md §9 proof bundle

3. manage_notes(operation="upsert", notes=[{
     itemId: <uuid>,
     key: <note-key from gateStatus.missing or schema>,
     role: "queue" | "work" | "review",
     body: <skill output or operator-authored content>
   }])

4. Repeat get_context until gateStatus.canAdvance: true
   (or until all required notes for ALL phases are filled, for `complete`)

5. advance_item(transitions=[{
     itemId: <uuid>,
     trigger: "start" | "complete" | "block" | "resume" | "cancel" | "reopen",
     summary: "<one-line summary of what just shipped>",
     actor: { id: <agent-id>, kind: <agent-kind>, parent: <session-id> }
   }])
```

**Idempotency**: (itemId, key) pairs are unique. Upserting the same key twice updates the existing note in place. Safe to retry.

**Iterative pattern**: after every successful `manage_notes(upsert)`, the orchestrator returns an `itemContext.<itemId>.guidancePointer` field. Read it for the NEXT note to fill. The pointer advances through unfilled required notes in role order.

---

## Note schemas you'll encounter

Schemas live in `.taskorchestrator/config.yaml` and are loaded by the orchestrator at startup. Selection rules:

1. **Type-first**: `item.type` matches a key in `work_item_schemas` directly. Set `type` at item creation for reliable selection.
2. **Tag-fallback**: only hits the legacy `note_schemas:` block (if present). For `work_item_schemas:` tag-based items, set `type` explicitly.
3. **Default fallback**: items with no type/tag match get the `default` schema (typically just `proof-bundle` required).

Current schemas in Dopemux (`work_item_schemas` keys):

| Schema | Lifecycle | Notes | Hard-required for `complete` |
|---|---|---|---|
| `task-packet` | AUTO | 6 (PAL chain + impl + proof) | `proof-bundle` |
| `feature-implementation` | MANUAL | 8 (feature brief + plan + PAL + proof) | `proof-bundle` |
| `bug-fix` | AUTO | 9 (repro + root-cause + regression + PAL + proof) | `proof-bundle` |
| `rfc-proposal` | MANUAL | 6 (problem + alternatives + consensus + decision + ADR) | `problem-statement`, `alternatives`, `chosen-approach`, `adr-document` |
| `audit-pack` | AUTO_REOPEN | 4 (prompt + findings + verdict) | `audit-prompt`, `findings-register`, `verdict` |
| `sprint-goal` | PERMANENT | 2 (goal + progress) | `goal-definition` |
| `retrospective` | AUTO | 11 (scope + observations + findings + proposals) | `scope`, `observations`, `findings` |
| `default` | AUTO | 1 (proof-bundle only) | `proof-bundle` |

Lifecycle modes:

- **AUTO** — parent auto-cascades to terminal when all children reach terminal
- **MANUAL** — parent must be completed explicitly (no auto-cascade)
- **AUTO_REOPEN** — auto-cascade, but reopen the parent if a new child is created under a terminal parent (audit re-issues)
- **PERMANENT** — parent never auto-terminates (sprint goals)

---

## PAL chain → required notes (the killer integration)

`AGENTS.md §5` defines two PAL chains. Each stage maps to a note key:

**Codex minimum chain** (`analyze → planner → codereview → precommit`):

| Stage | Note key | Role | PAL tool | Required? |
|---|---|---|---|---|
| analyze | `analyze` | queue | `mcp__pal__analyze` | currently `false` (advisory) |
| planner | `planner` | queue | `mcp__pal__planner` | currently `false` |
| (implement) | `implementation-evidence` | work | — | currently `false` |
| codereview | `codereview` | review | `mcp__pal__codereview` | currently `false` |
| precommit | `precommit` | review | `mcp__pal__precommit` | currently `false` |
| **(proof)** | **`proof-bundle`** | **review** | `verify` skill | **`true` — THE COMPLETE-GATE** |

**Risky / architecture-sensitive chain** (`analyze → thinkdeep → challenge → planner → challenge → implement → codereview → precommit → challenge`):

Adds five more optional notes:

| Note key | Role | PAL tool |
|---|---|---|
| `thinkdeep` | queue | `mcp__pal__thinkdeep` |
| `challenge-pre-plan` | queue | `mcp__pal__challenge` |
| `challenge-post-plan` | queue | `mcp__pal__challenge` |
| `challenge-post-implement` | work | `mcp__pal__challenge` |
| `challenge-post-review` | review | `mcp__pal__challenge` |

Activate the risky chain by tagging the item `risky` or `architecture-sensitive`. The notes themselves are not required by the current schema; treat them as recommended for high-risk work.

**Current posture (Option A — soft gates)**: queue/work notes are `required: false` (advisory). Only `proof-bundle` in review is `required: true`. The chain is observable and auditable via `query_notes`, but advancement is gated only by the proof bundle. Tighter postures (flipping per-trait `required: false → true`) ship in a future revision.

---

## Proof bundle structure (the complete-gate)

`proof-bundle` is the only HARD gate. Without it, `advance_item(trigger="complete")` returns an error. The bundle body must include:

```
TP path/ID:           <orchestrator UUID + TP-CS-NNN designator>
Worktree path:        <absolute path of git worktree>
Branch:               <branch name>
Repo identity:        <e.g. DDD-Enterprises/dopemux-mvp>
Slices completed:     <count + brief description>
Files changed:        <list with line counts>
Validations:          <PASS | FAIL | NOT_RUN buckets with exit codes>
Codereview status:    <PASS / FAIL / NOT_RUN + reference to codereview note>
Precommit status:     <PASS / FAIL / NOT_RUN + reference to precommit note>
Commit SHA(s):        <hash(es)>
PR URL or blocker:    <github URL or specific blocker>
Residual risks:       <known risks not fully mitigated>
UNKNOWNs:             <items marked UNKNOWN per AGENTS.md §2>
Cleanup status:       <worktree removed? temp files deleted?>
```

Per `AGENTS.md §9`: **no proof means incomplete**. The gate is mechanical.

---

## Actor attribution

`advance_item` and `manage_notes` accept an optional `actor` field. Dopemux convention:

```
{
  "id": "worktree-<basename>-<branch>",   // e.g. "worktree-dopemux-mvp-task-orchestrator-claude-surface"
  "kind": "subagent",                      // or "agent", "human", "system"
  "parent": "<session-id>"                 // Claude Code / Codex / Copilot session id
}
```

Currently: `actor_authentication.enabled` is **off** in `.taskorchestrator/config.yaml` — claims are self-reported (Stage 1 trust). Operators can flip to enabled for stricter enforcement later.

---

## Discovery patterns

Common operator queries (Bare-MCP form; vendor-specific surfaces wrap these):

| Goal | MCP call |
|---|---|
| What's next? | `get_next_item(includeAncestors=true, limit=3)` |
| Where was I? | `get_context()` (health-check) or `get_context(since="<timestamp>")` (resume) |
| What's blocked? | `get_blocked_items(includeAncestors=true)` |
| Show me one item's full state | `get_context(itemId="<uuid>")` |
| Show this item's notes | `query_notes(operation="list", itemId="<uuid>")` |
| Read one note's full body | `query_notes(operation="get", id="<note-uuid>")` |
| Find items by content | `query_items(operation="search", query="<words>")` |
| Find notes by content | `query_notes(operation="search", query="<words>", snippet=true)` |
| What blocks REQ-42? | `query_dependencies(operation="backlinks", itemId="<req-42-uuid>")` |
| Preview a transition | `get_next_status(itemId="<uuid>", trigger="start")` |

---

## Vendor-specific wrappers

These four agents call into the same protocol but each has its own command surface:

| Agent | Surface | Wrapper status |
|---|---|---|
| Claude Code | `/dx:next`, `/dx:context`, `/dx:tree`, `/dx:blocked`, `/dx:search`, `/dx:note`, `/dx:start`, `/dx:complete` (etc.) | Phase 2 in flight; foundational read commands shipped, write commands in Phase 4 |
| Codex | Raw MCP calls (no slash commands; Codex reads `AGENTS.md §11`) | This protocol IS the wrapper |
| Copilot | Limited MCP access (typically) — `.github/copilot-instructions.md` orchestrator section | Reference this protocol; do not assume MCP access |
| Custom personas | Inherit from `.claude/CLAUDE.md` floor by default | Override per-persona only when persona has distinct task-management responsibilities |

---

## What this document is NOT

- **Not a tutorial**. See `docs/02-how-to/use-task-orchestrator.md` (coming in TP-CS-090) for step-by-step recipes.
- **Not a tool reference**. See the workflow guide's §3 (Note Schemas) and §10 (Claim Mechanism) for protocol depth beyond what's listed here.
- **Not the bare-MCP escape hatch**. See `docs/02-how-to/use-task-orchestrator-bare-mcp.md` (coming in TP-CS-092) for the no-commands, no-schemas, no-plugin path.

---

## Schema versioning

`.taskorchestrator/config.yaml` carries a `schemas_metadata` block with `version` and `retro_id` (when a retro produces a schema change). Treat schema/trait edits as contract-sensitive per `AGENTS.md §6` — require ADR linkage and operator approval.

Changes to required-note posture (`required: false → true` or vice versa) are NON-breaking-by-default in the orchestrator's runtime, but ARE breaking for in-flight items because gate enforcement changes mid-stream. Always announce posture changes via ConPort decision + ADR + retro reference.

---

## Failure modes and fallbacks

**"Schema didn't match"** (`schemaMatch: false`, `expectedNotes: []`):
- Item's `type` doesn't match a `work_item_schemas` key
- Tags don't match a `note_schemas` key (legacy fallback)
- Falls through to `default` schema (just proof-bundle gate)
- Fix: set `type` explicitly via `manage_items(operation="update", items=[{id, type:"task-packet"}])`

**"Database is locked"** (rare; transient):
- Concurrent writer contention on SQLite WAL
- Per `AGENTS.md §10` and the 2026-05-27 multi-spawn fix, this should be near-zero — only one orchestrator container per workspace at a time
- If it happens: retry the operation. If persistent, check `docker ps` for multiple containers mounting the same `data_dir` (per `scripts/external-references/README.md`).

**"Container won't start"**:
- Check the wrapper script: `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`
- Verify the pinned image digest is reachable: `docker manifest inspect ghcr.io/jpicklyk/task-orchestrator:<version>`
- Check `--print-resolution` output: `<wrapper> --print-resolution` shows resolved workspace_root, project_root, data_dir, config_root

**"Schema changes not taking effect"**:
- Orchestrator caches schemas on first access — must restart for changes to apply
- Stop the orchestrator container; next MCP call respawns with fresh config load
- Verify with `manage_items(create, type="<schema-key>")` — should return `schemaMatch: true` + populated `expectedNotes`

---

## Related documents

- [adr-task-orchestrator-as-workflow-authority.md](../90-adr/adr-task-orchestrator-as-workflow-authority.md) — workflow authority decision
- [adr-task-orchestrator-claude-surface-integration.md](../90-adr/adr-task-orchestrator-claude-surface-integration.md) — Claude-surface integration ADR
- [.taskorchestrator/config.yaml](../../.taskorchestrator/config.yaml) — schema config (the runtime source of truth)
- [scripts/external-references/README.md](../../scripts/external-references/README.md) — external wrapper script snapshots
- `AGENTS.md §5` — PAL chain definitions
- `AGENTS.md §9` — proof bundle structure
- Upstream workflow guide: <https://github.com/jpicklyk/task-orchestrator/wiki/workflow-guide>
