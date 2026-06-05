---
id: callable-surface-inventory
title: Callable Surface Inventory
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Callable Surface Inventory (reference) for dopemux documentation and developer
  workflows.
---
# Task-Orchestrator Callable Surface Inventory

This inventory catalogs the Claude-facing surface over the task-orchestrator MCP: every tool
the surface can reach, its read/write/destructive classification, and the `/dx:` command that
wraps it. It defines the **read-surface boundary** — the subset of the surface that mutates
nothing.

Unlike the prose-only conport/serena inventories, this surface is **machine-enforced**: the
machine-readable authority is [`.taskorchestrator/surface_manifest.json`](../../../../.taskorchestrator/surface_manifest.json),
and [`scripts/validate_dx_surface.py`](../../../../scripts/validate_dx_surface.py) fails if any
committed `/dx:` command drifts from it (e.g. a read command gaining a write tool).

**Authority**: live task-orchestrator v3 MCP surface (runtime) outranks captured docs. Tool
read/write/destructive annotations cross-referenced to
[`reports/task-orchestratorrepo-truth-pack/MCP_TOOL_MANIFEST.json`](../../../../reports/task-orchestratorrepo-truth-pack/MCP_TOOL_MANIFEST.json).
See also [`AGENTS.md §6`](../../../../AGENTS.md) (workflow authority) and
[`dx-command-authoring.md`](../dx-command-authoring.md) (authoring contract).

## 1. Tool surface classification

The live v3 surface exposes **14 tools**. Classification (`destructiveHint` from the upstream
manifest; `claim_item` inferred — see skew notes):

| tool | operations | classification | wrapped by | notes |
|---|---|---|---|---|
| `query_items` | get · search · overview | `safe_read_only` | tree, search, complete-tree | |
| `query_notes` | get · list · search | `safe_read_only` | notes, context, search, note | |
| `query_dependencies` | query | `safe_read_only` | backlinks, depends | |
| `get_context` | item · session · health | `safe_read_only` | context, next, block, cancel, complete, note, reopen, resume, start | |
| `get_next_status` | check | `safe_read_only` | preview | returns the recommended trigger; takes only `itemId` |
| `get_next_item` | recommend | `safe_read_only` | next | |
| `get_blocked_items` | list | `safe_read_only` | blocked | |
| `advance_item` | advance | `write_non_destructive` | start, complete, block, resume, cancel, complete-tree | no `actor` param (see §4) |
| `create_work_tree` | create | `write_non_destructive` | — | not wrapped by any `/dx:` command |
| `claim_item` | claim | `write_non_destructive` | — | live v3 only; **wrapped by no command** (see §4) |
| `manage_items` | create · update · **delete** | `write_destructive` | — | delete is destructive |
| `manage_notes` | upsert · **delete** | `write_destructive` | note | delete is destructive |
| `manage_dependencies` | create · **delete** | `write_destructive` | depends | delete is destructive |
| `complete_tree` | complete · cancel | `write_destructive` | complete-tree | cascade-terminates a subtree |

The **7 `safe_read_only` tools** are the only tools the read-surface may use.

## 2. `/dx:` command → surface mapping

18 commands live in [`.claude/commands/dx/`](../../../../.claude/commands/dx/). Classification
is by the orchestrator tools each command's frontmatter `allowed-tools` actually lists.

| command | surface_class | orchestrator tools | notes |
|---|---|---|---|
| `backlinks` | read | query_dependencies | |
| `blocked` | read | get_blocked_items | |
| `context` | read | get_context, query_notes | also a ConPort read (non-surface) |
| `next` | read | get_next_item, get_context | also a ConPort read (non-surface) |
| `notes` | read | query_notes | |
| `preview` | read | get_next_status | |
| `search` | read | query_items, query_notes | |
| `tree` | read | query_items | |
| `block` | write | get_context, advance_item | |
| `cancel` | write | get_context, advance_item | |
| `complete` | write | get_context, advance_item | proof-bundle complete-gate |
| `complete-tree` | write | query_items, complete_tree, advance_item | destructive cascade |
| `depends` | write | query_dependencies, manage_dependencies | |
| `note` | write | get_context, manage_notes, query_notes | |
| `resume` | write | get_context, advance_item | |
| `start` | write | get_context, advance_item | |
| `reopen` | write | get_context | **write by intent, currently wired read-only** — the reopen transition was not wrappable at authoring time, so the command only reads today. Classified non-read to keep it out of the read-surface. |
| `implement` | composite | — | composite ADHD session (ConPort/Serena/PAL); not a thin orchestrator wrapper. Uses legacy aliases (`mcp__zen__*`, `mcp__serena__*`) — a pre-existing inconsistency, out of scope here. |

**Totals:** 8 read · 9 write · 1 composite.

## 3. The read-surface boundary

The **P1 read-surface** is exactly:

- **Commands (8):** `backlinks`, `blocked`, `context`, `next`, `notes`, `preview`, `search`, `tree`
- **Tools (7):** `query_items`, `query_notes`, `query_dependencies`, `get_context`,
  `get_next_status`, `get_next_item`, `get_blocked_items`

These mutate no workflow or repo state and are safe to use unsupervised. Everything else is
out of the read-surface.

**Explicitly out of scope for the read-surface (and for this packet):**

- no live task-orchestrator writes (`manage_*`, `advance_item`, `claim_item`,
  `create_work_tree`, `complete_tree`)
- no Dopetask execution
- no bridge writes (dopecon-bridge / ConPort writes)
- no memory/context writes (dope-memory)
- no repo writes (`Write`, `Edit`, and the like)

The boundary covers **both** the orchestrator tools and the non-orchestrator permissions a read
command declares. A read command's `allowed-tools` may only carry the non-orchestrator entries
permitted by the manifest's `read_command_nonorch_allowlist` (read helpers — `Read`/`Grep`/
`Glob`/`LS` — plus explicitly read-only MCP tools such as `mcp__conport__get_active_context`).
The allowlist is **fail-closed**: any non-orchestrator tool not permitted — a repo write
(`Write`/`Edit`) or a bridge/memory write (`mcp__conport__log_decision`) — is a violation.

**Bash is scoped, not bare.** Bare unscoped `Bash` is **rejected** in read commands, because it
can run mutating shell (`git commit`, `rm`, `touch`). Read commands must instead declare a
**scoped** pattern `Bash(<cmd>:*)` whose command is in the manifest's `bash_allowed_commands`.
Only `git rev-parse` is allowlisted today — the canonical read-only detection used by the surface
(`git rev-parse --show-toplevel` for the workspace root, `git rev-parse --abbrev-ref HEAD` for the
current branch); `rev-parse` never mutates, so `Bash(git rev-parse:*)` is safe even under the
`:*` glob. A scoped-but-mutating command such as `Bash(git commit:*)` is rejected. (The 8 read
commands now declare `Bash(git rev-parse:*)`.)

## 4. Provenance & skew notes

Recorded truthfully per governance doctrine (observed vs inferred vs stale):

- **Tool-count skew.** `MCP_TOOL_MANIFEST.json` is upstream **v2.2.0 / 13 tools**; the deployed
  surface is **v3 / 14 tools** (adds `claim_item`). The deployed surface is the authority; the
  manifest is used only for the 13 shared tools' read/write annotations. `claim_item`'s
  classification (`write_non_destructive`) is **inferred**, not annotation-sourced.
- **Stale authoring note.** [`dx-command-authoring.md`](../dx-command-authoring.md) line 72
  (dated 2026-05-27) states `claim_item` "is not yet exposed in the orchestrator's tool
  surface." This is **stale** — `claim_item` is present in the live v3 surface, but wrapped by
  no `/dx:` command. (Fixing that doc is deferred to a separate doc-fix packet.)
- **Actor-attribution gap.** `advance_item` accepts only `{itemId, trigger, summary?}` — no
  `actor`. Structured actor attribution awaits `claim_item` wiring; today, attribution is
  embedded in the `summary` text. `/dx:context` session-resume renders `Actor: —` for
  advance-driven transitions until then.
- **MetaMCP filtering not operationalized.** Role-based tool filtering (MetaMCP) is *proposed*
  but not consumed in-repo — env vars are set but unread. **Inverse-failure risk:** an operator
  may believe write tools are gated when they are not. This inventory + validator is the only
  in-repo enforcement of the read boundary today, and it is **advisory** (it gates the
  committed command files, not live MCP calls).

## 5. Enforcement

- Authority: `.taskorchestrator/surface_manifest.json` (hand-authored; **not** generated from
  frontmatter, so command drift is detectable against an independent contract).
- Validator: `python scripts/validate_dx_surface.py` — read-only; exit 1 if a read command
  lists a write **orchestrator** tool, lists a non-orchestrator tool outside the read allowlist
  (catching `Write`/`Edit`/ConPort-write drift), lists an unknown tool, or drifts from the
  manifest. It also fails if `read_only_tools` diverges from the manifest's
  `safe_read_only` classifications, and it validates the non-orchestrator allowlist itself so a
  write-class tool or mutating Bash command cannot be smuggled into the read set. Full failure
  conditions (a)–(g) are documented in the script header.
- Test: `tests/orchestrator/test_dx_surface_manifest.py` — includes bite tests proving the
  validator catches a read command that gains either a write **orchestrator** tool or a
  non-orchestrator write tool (`Write`, `mcp__conport__log_decision`).

Wiring the validator into CI / pre-commit is deferred to a follow-up packet.
