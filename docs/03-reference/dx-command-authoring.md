---
id: dx-command-authoring
title: Dopemux dx Slash Command Authoring
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Canonical structure for authoring Dopemux dx slash commands that wrap the task-orchestrator MCP. Codifies frontmatter, phased body, read-vs-write safety, and orchestrator tool contracts.
---
# /dx: Command Authoring Template

The `/dx:` commands are the Claude-Code-facing surface for the task-orchestrator workflow authority (per [`AGENTS.md §6`](../../AGENTS.md) + [adr-task-orchestrator-as-workflow-authority](../90-adr/adr-task-orchestrator-as-workflow-authority.md)). Each command is a Markdown spec the model executes; consistency across them is what keeps the surface learnable. **Author every new `/dx:` command from this template.**

## File location & naming

- Command files live in `.claude/commands/dx/<name>.md` → invoked as `/dx:<name>`.
- **Every `.md` in that directory becomes a command.** Do not put templates, READMEs, or shared partials there — they would register as bogus commands. Reference material (like this file) lives under `docs/`.
- Name files after the verb/noun the operator types: `start.md`, `note.md`, `complete.md`, `depends.md`.

## Required frontmatter

```yaml
---
description: "<one line; shows in command list>"
arguments: "<arg-spec, e.g. \"<id> [--flag]\">"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__<tool>",
  "...only the tools this command actually calls..."
]
model: "claude-sonnet-4-5"
---
```

- `allowed-tools` is a **least-privilege allowlist** — list only the MCP tools the command invokes. Read commands never list write tools.
- `model: claude-sonnet-4-5` is the established default for `/dx:` commands.

## Required body structure

Every command body follows the same phased layout (read `next.md`, `context.md`, `blocked.md` for live exemplars):

1. **Title + one-line purpose** — `# /dx:<name> — <Title>` then the "answer X in one call" framing.
2. **Authority line** — verbatim:
   > **Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.
3. **Phase 1: Argument Parsing** — parse `$ARGUMENTS`; state defaults.
4. **Phase 2: Fetch / Act** — the MCP call(s). Read commands fetch; write commands mutate (see Safety below).
5. **Phase 3: Render** — the output block, ADHD-scannable.
6. **Phase 4: ADHD-Friendly Footer** — `Next actions:` pointing at sibling commands.
7. **Error Handling** — at minimum the orchestrator-unavailable fallback and invalid-UUID cases.
8. **Success Criteria** — `✅` bullets; include "scannable in <10s".
9. **Notes for Claude** — execution caveats, direction footguns, read-only/write declaration.

Target 140–200 lines. ADHD conventions: short-prefix UUIDs are what operators type (show the full UUID once per item); emoji legend `▸` active · `⛔` blocked · `⚠️` stalled · `✅` clear; never present more than ~3 next-action options.

## Read commands vs write commands

**Read commands** (`next`, `context`, `tree`, `blocked`, `search`) end with an explicit declaration:

> This is a read-only wrapper. Never mutate workflow state from this command.

**Write commands** (`start`, `note`, `complete`, `block`, `depends`, …) mutate orchestrator state. They MUST add a **Safety & Confirmation** subsection in Phase 2:

- **Preflight read** — re-fetch current state with `get_context(itemId)` (or `get_next_status`) before mutating. Never transition blind.
- **Gate check** — for transitions, confirm `canAdvance` (or surface the missing required notes and stop). The orchestrator enforces gates server-side, but surfacing them first avoids a confusing failure.
- **Acknowledge before irreversible-ish actions** — `complete`, `cancel`, `complete-tree`, and dependency creation can cascade (completing/cancelling the last non-terminal child auto-terminals its parent). Show what will change and confirm.
- **Idempotency** — note upserts are idempotent on `(itemId, key)`; dependency creation is not — check for an existing edge with `query_dependencies` before creating to avoid duplicate BLOCKS.

## The actor-attribution gap (read before authoring start/complete)

Doctrine (CLAUDE.md, the plan) describes `advance_item(trigger="start", actor={id, kind, parent})`. **The currently deployed `advance_item` MCP schema accepts only `{itemId, trigger, summary?}` — there is no `actor` parameter.** Structured actor attribution lives in `claim_item`, which is not yet exposed in the orchestrator's tool surface.

Consequences for write wrappers:

- Pass only supported fields: `advance_item(itemId, trigger, summary?)`.
- The `summary` field IS supported — use it for the human reason for the transition. Operators who need attribution *now* may include their actor id in the summary text.
- `/dx:context` session-resume mode renders an `Actor:` field; for advance_item-driven transitions it will show `—` until `claim_item` (and its actor plumbing) ships. Document this in the command's Notes so the empty field isn't read as a bug.

**Dopemux actor-id convention** (for the day `claim_item` lands, and for summary-embedded attribution today):

```
{ id: "worktree-<basename>-<branch>", kind: "subagent", parent: "<session-id>" }
```
derived from `git rev-parse --show-toplevel` (basename) + `git branch --show-current`.

## Orchestrator tool contract quick-reference

Verified against the loaded MCP schemas (2026-05-27). Re-verify if the orchestrator image changes.

| Tool | Shape | Notes |
|---|---|---|
| `advance_item` | `{itemId (required), trigger (required), summary?}` | triggers: `start` (queue→work→review→terminal), `complete` (→terminal, requires all required notes), `block`/`hold` (→blocked, saves previousRole), `resume` (blocked→previousRole), `cancel` (→terminal, statusLabel=cancelled). No `actor`. No `reopen` trigger. |
| `manage_notes` | `operation=upsert, notes:[{itemId, key, role:queue\|work\|review, body?}]` | `(itemId, key)` unique → idempotent. `delete` by ids or itemId(+key). |
| `query_notes` | `operation=get(id)` / `list(itemId, role?, includeBody?)` | read-only. |
| `manage_dependencies` | `operation=create, dependencies:[{fromItemId, toItemId, type?, unblockAt?}]` | **`fromItemId` BLOCKS `toItemId`** (toItemId is blocked until fromItemId reaches `unblockAt`). Shared `type` (default `BLOCKS`), `unblockAt` (default `terminal`; values queue/work/review/terminal). Shortcuts: `linear`+`itemIds`, `fan-out`+`source`+`targets`, `fan-in`+`sources`+`target`. Atomic; cycle/duplicate detection. |
| `query_dependencies` | `itemId, direction:incoming\|outgoing\|all, type?, includeItemInfo?` | `outgoing` = what this item blocks; `incoming` = what blocks this item. |
| `get_context` | `()` health-check · `(itemId)` gate status + notes · `(mode="session")` session-resume | read-only. Item mode returns `canAdvance` + missing required notes + `guidancePointer` + `noteProgress`. |
| `get_next_status` | `(itemId)` → `{recommendation: Ready\|Blocked\|Terminal, currentRole, nextRole?, trigger?, blockers?}` | read-only; takes **only `itemId`** (no `trigger` input) and *returns* the recommended next `trigger`. Don't author a wrapper that passes a trigger to it. |

### Gate behavior (task-packet schema)

`start` checks the **current phase's** required notes; `complete` checks **all phases'** required notes. For `task-packet`, the only hard-required note is `proof-bundle` (role=review) — the mechanical complete-gate per [`AGENTS.md §9`](../../AGENTS.md). PAL-chain notes (`analyze`, `planner`, `codereview`, `precommit`) and `implementation-evidence` are advisory (required:false) under the Dopemux Option-A posture.

## Authoring checklist

- [ ] File at `.claude/commands/dx/<name>.md`; nothing non-command in that dir.
- [ ] Frontmatter: description, arguments, least-privilege `allowed-tools`, `model: claude-sonnet-4-5`.
- [ ] Authority line present and verbatim.
- [ ] Phases 1–4 + Error Handling + Success Criteria + Notes for Claude.
- [ ] Read-only declaration (read cmd) **or** Safety & Confirmation subsection (write cmd).
- [ ] Tool params match the contract table above (no invented fields, e.g. no `actor` on `advance_item`).
- [ ] Direction footguns documented (esp. `depends`).
- [ ] ADHD: short-prefix UUIDs, emoji legend, <10s scannable, ≤3 next actions.
