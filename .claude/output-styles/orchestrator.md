---
id: orchestrator-output-style
title: Orchestrator-Aware Response Style
type: output-style
owner: "@hu3mann"
date: "2026-05-28"
opt-in: "Add @.claude/output-styles/orchestrator.md to your CLAUDE.md, or set outputStyle: orchestrator in .claude/settings.json (future capability)"
---

# Orchestrator Output Style

**Purpose**: Reshape Claude responses to lead with task-orchestrator context when working on
active work-items. Pairs ADHD progressive-disclosure with orchestrator gate awareness.

> **Authority**: task-orchestrator MCP per `AGENTS.md §6` + `adr-task-orchestrator-as-workflow-authority.md`.

---

## When This Style Applies

Apply these rules when **any** of the following is true:
- An active work-item (role=`work` or `review`) exists in the orchestrator
- The current prompt references a task UUID, `/dx:` command, or orchestrator tool
- A `manage_notes` or `advance_item` call was made in this turn

Otherwise fall back to standard response format.

---

## Response Structure

Every multi-step response under this style follows:

```
┌─────────────────────────────────────────────────────┐
│ [BREADCRUMB]  ▸ gate status  ▸ next action           │
└─────────────────────────────────────────────────────┘

[SUBSTANCE]
```

### 1. Breadcrumb Header (required when work-item is active)

```
▸ <root-title> › <parent-title> › <item-title>  [short-uuid]
  Role: work  ·  Gates: ✅ clear  OR  ⚠️ 2 missing  ·  Next: <trigger>
```

Rules:
- Root → parent → item order (root first, deepest last), truncated at 3 levels
- Short UUID = first 8 chars, shown once per response
- Gate status: `✅ clear` when `canAdvance: true`; `⚠️ N missing` when `canAdvance: false`
- Next action: the recommended trigger from `get_next_status()` if available

### 2. Guidance Pointer (when present)

If `guidancePointer` is non-null on the active item, show it as a callout immediately after
the breadcrumb:

```
💡 Guidance: <guidancePointer text>
   Skill: mcp__pal__<skill>  →  manage_notes(key="<note-key>")
```

### 3. Substance

The actual response content. No change to depth or completeness — only the header changes.

### 4. Next Actions Footer (max 3)

```
Next: /dx:note <id> <key>  ·  /dx:complete <id>  ·  /dx:context <id>
```

Never list more than 3 options. Omit options that are inapplicable (e.g. don't show
`/dx:complete` when `canAdvance: false`).

---

## ADHD Formatting Rules

These apply on top of the structure above:

| Rule | Detail |
|---|---|
| **Progressive disclosure** | Lead with essential (breadcrumb + guidance), details on request |
| **Max 3 options** | Never offer more than 3 next actions in one turn |
| **Short UUIDs** | Display 8-char prefix in the UI; full UUID shown once per item per session |
| **Emoji legend** | `▸` active · `⛔` blocked · `⚠️` stalled/missing · `✅` clear · `💡` guidance |
| **Scannable in <10s** | Header + next actions must fit in one screen-width block |
| **No wall of text** | Break implementation steps into numbered lists ≤ 5 items each |

---

## Opt-In

### Session-level (CLAUDE.md import)

Add to your `.claude/CLAUDE.md` or a session-start message:

```markdown
@.claude/output-styles/orchestrator.md
```

### Settings-level (future)

When Claude Code ships `outputStyle` support, wire via `.claude/settings.json`:

```json
{
  "outputStyle": "orchestrator"
}
```

Until that lands, `@`-import or manual copy-paste into the system prompt is the mechanism.

---

## Compatibility

- **TP-CS-101 (plugin posture)**: if an upstream plugin ships its own output style, choose ONE
  canonical style; do not stack. This style takes precedence if the plugin style conflicts with
  ADHD principles.
- **Standard `/dx:` commands**: these commands already lead with breadcrumb and gate status in
  their render phase — no double-formatting needed within a single `/dx:` response.
- **Bare-MCP mode**: this style is advisory only. Bare-MCP operators can ignore it; the floor
  guarantee (CLAUDE.md + MCP tools) still works without it.

---

## Notes for Claude

This file is a **behavior specification**, not a code file. When loaded as context, apply its
rules to format responses. Do not generate code from it; do not cite it in responses unless the
user asks about output style.

When in doubt about whether this style applies, err toward showing the breadcrumb header
(one line) and omitting it is only correct when the model has confirmed no active work-item.
