---
description: "ADHD-optimized 25-minute implementation session driven by task-orchestrator"
arguments: "[<item-id>]"
allowed-tools: [
  "Bash", "Read", "Write", "Edit", "Grep", "Glob", "TodoWrite",
  "mcp__task-orchestrator__get_next_item",
  "mcp__task-orchestrator__advance_item",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__manage_notes",
  "mcp__conport__update_active_context",
  "mcp__pal__thinkdeep", "mcp__pal__debug", "mcp__pal__codereview",
  "mcp__pal__apilookup"
]
model: "claude-sonnet-4-5"
---

# /dx:implement — ADHD Implementation Session

Start an ADHD-optimized 25-minute focused implementation session. Drives task selection, session
lifecycle, and completion gate surfacing through the task-orchestrator.

> **Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR
> `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

---

## Phase 1: Argument Parsing + Task Selection

Parse `$ARGUMENTS`:

- **`<item-id>` provided** — treat as orchestrator work-item UUID. Call
  `get_context(itemId=<item-id>)` to confirm the item exists and read its current role, title,
  ancestors, and gate status. Skip the selection prompt.
- **No argument** — call `get_next_item(limit=3, includeAncestors=true, includeDetails=true)` to
  get the top 3 ADHD-ranked queue items, then display them and ask the user to pick one (max 3
  options — ADHD-safe).

**Selection display** (no-arg path):

```
── Next Up ──────────────────────────────────────────
  1. [ab12cd34] Sprint Goal › Task Title
     priority: high · complexity: 5

  2. [ef56gh78] Sprint Goal › Other Task
     priority: medium · complexity: 3

  3. [ij90kl12] Sprint Goal › Yet Another
     priority: medium · complexity: 6
─────────────────────────────────────────────────────
Which task? (1/2/3 or paste UUID)
```

Show the full UUID once (in parentheses) after the short prefix.

### Step 1.2: ADHD Engine Assessment (Optional)

Derive complexity (0.0–1.0) from the item's `complexity` field (divide by 10), then:

```bash
curl -s -X POST http://localhost:8095/api/v1/assess-task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "current_user",
    "task_id": "ITEM_UUID",
    "task_data": {
      "complexity_score": COMPLEXITY,
      "estimated_minutes": 25,
      "description": "ITEM_TITLE",
      "dependencies": []
    }
  }' | python -m json.tool
```

Display results compactly:

```
⚡ Energy Match: XX%    🧠 Cognitive Load: LOW/MED/HIGH    ✅ Suitability: XX%
💡 <recommendation>
```

If suitability < 0.6, warn and offer to select a different task. If the ADHD Engine is
unavailable, show `⚠️ ADHD assessment unavailable — proceeding with standard session` and
continue.

---

## Phase 2: Session Start (Safety & Confirmation)

### Step 2.1: Preflight Read

Call `get_context(itemId=CHOSEN_UUID)` before any transition:

- **role = queue** → proceed to Step 2.2
- **role = work** → item already in progress; skip transition, log "Re-entering active session"
- **role = review or terminal** → warn user; do not start a new session on a closed item

### Step 2.2: Start Transition (queue only)

```
advance_item(transitions=[{
  itemId: CHOSEN_UUID,
  trigger: "start",
  summary: "Session start via /dx:implement"
}])
```

### Step 2.3: Update Session Context

```
mcp__conport__update_active_context:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  patch_content: {
    "current_task": "CHOSEN_UUID",
    "session_start": "ISO_TIMESTAMP",
    "session_type": "implement",
    "target_duration": 25
  }
```

### Step 2.4: Session Banner

```
🚀 Implementation Session Started
═══════════════════════════════════════════════

📋 Task: [ITEM_TITLE]
🆔 ID:   [ab12cd34]  (full UUID shown once)
▸ Role:  work
⏱️  Duration: 25 minutes
🎯 Focus: Stay on this task, minimize context switches

Orchestrator tracking active. Let's build! 💪
═══════════════════════════════════════════════
```

---

## Phase 3: Implementation Work

You are now in focused implementation mode.

### Work Guidelines

- **Stay Focused** — work on this one task only
- **Save Frequently** — after each meaningful change, save work
- **Minimize Switches** — keep lookups brief, return to task

### ADHD Accommodations

- **If stuck**: break the current step into smaller pieces; start with the easiest part
- **If distracted**: acknowledge, gently return focus — no judgment
- **If overwhelmed**: pause, reassess; it's okay to break early and adjust approach

### Progress Checkpoints

After each major step (file created, test passing, feature working), optionally file a running
note:

```
manage_notes(operation="upsert", notes=[{
  itemId: CHOSEN_UUID,
  key: "implementation-evidence",
  role: "work",
  body: "Progress: <what was done, any exit codes>"
}])
```

---

## Phase 4: Session Completion

After 25 minutes or when the task reaches a natural checkpoint, ask:

```
Session checkpoint reached!

1. ✅ DONE          — task complete, ready to close
2. 🔄 IN_PROGRESS   — still working, good progress
3. ⛔ BLOCKED        — hit a blocker
4. 🔀 CONTEXT_SWITCH — switching tasks
```

### DONE Path

Call `get_context(itemId=CHOSEN_UUID)` and inspect `gateStatus.canAdvance` + `gateStatus.missingNotes`:

**If `gateStatus.canAdvance: false`** (gates pending):

```
⚠️ Gates pending before you can complete:

Missing notes:
  • proof-bundle (review) — REQUIRED
  • <other keys from gateStatus.missingNotes>

Run: /dx:note CHOSEN_UUID proof-bundle
Then: /dx:complete CHOSEN_UUID
```

**If `gateStatus.canAdvance: true`** (all gates clear):

```
✅ ✅ ✅ Gates are clear!
Run: /dx:complete CHOSEN_UUID
```

Do **not** call `advance_item(trigger="complete")` from this command — delegate to `/dx:complete`.

### BLOCKED Path

Ask the user for a brief reason, then:

```
advance_item(transitions=[{
  itemId: CHOSEN_UUID,
  trigger: "block",
  summary: "USER_REASON"
}])
```

### IN_PROGRESS / CONTEXT_SWITCH

No orchestrator transition — item stays in `work`. Update session context only (Step 4.1 below).

### All Paths: Close Session Context

```
mcp__conport__update_active_context:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  patch_content: {
    "last_session_end": "ISO_TIMESTAMP",
    "last_task_status": "DONE|BLOCKED|IN_PROGRESS|CONTEXT_SWITCH",
    "session_completed": true
  }
```

### Break Reminder

```
☕ Time for a 5-Minute Break!
═══════════════════════════════════════════════
You've been focused for 25 minutes — great work!

• Walk  · Hydrate  · Stretch  · Deep breathing  · 20-20-20

You've earned this break! 💙
═══════════════════════════════════════════════
```

---

## Error Handling

**task-orchestrator unavailable** — if `get_next_item` or `advance_item` fail:
- Show `⚠️ task-orchestrator unavailable — workflow state won't be updated`
- Offer to continue the session without state tracking
- Suggest running `get_context()` health-check when available

**ADHD Engine unavailable** — handled in Phase 1; session continues without assessment.

**Invalid UUID** — if `get_context(itemId=X)` returns not-found:
- Show `⚠️ Item X not found in orchestrator`
- Fall back to no-arg selection path

**User interrupts mid-session** — ADHD-friendly; work is preserved in edited files.
Resume any time with `/dx:implement <uuid>`.

---

## Success Criteria

- ✅ Task selected from orchestrator queue or confirmed by UUID
- ✅ `advance_item(trigger="start")` called, or re-entry logged (role=work)
- ✅ ConPort `active_context` updated with session metadata
- ✅ User completed focused work
- ✅ Completion gate status surfaced (DONE path)
- ✅ Break reminder shown
- ✅ Encouraging, ADHD-supportive tone maintained throughout
- ✅ Scannable at a glance in <10s

---

## Notes for Claude

**This is a write command.** Always preflight-read with `get_context(itemId)` before any
`advance_item` call (Phase 2.1). Never transition blind.

**DONE path delegates** — do not call `advance_item(trigger="complete")` here. The proof-bundle
gate will reject it until the note is filled. Surface the gate and direct the user to `/dx:note`
then `/dx:complete`.

**Actor-attribution gap** — the deployed `advance_item` schema has no `actor` parameter. Embed
attribution in `summary` if needed (e.g. "Session start via /dx:implement [worktree-dopemux-mvp-…]").

**Role re-entry** — an item already in `work` is a re-entrant session; skip `advance_item(start)`,
don't double-advance.

**Tone** — warm, encouraging, celebratory. Emojis welcome. Adapt flexibly if the user wants a
different session length; 25 min is the default, not a hard rule.

**Next actions**: `/dx:note` to file notes · `/dx:complete` to close · `/dx:blocked` to check
queue blockers · `/dx:next` for next task recommendation.
