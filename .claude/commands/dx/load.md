---
description: "Load session context from ConPort"
allowed-tools: ["mcp__conport__get_active_context", "mcp__conport__get_progress", "mcp__conport__get_recent_activity_summary"]
model: "sonnet-4.5"
---

# /dx:load - Load Session Context

Load your last session context from ConPort for easy continuation.

## Step 1: Get Active Context

```
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
```

## Step 2: Get Recent Activity

```
mcp__conport__get_recent_activity_summary --workspace_id "/Users/hue/code/dopemux-mvp" --hours_ago 24
```

## Step 3: Get Recent Progress

```
mcp__conport__get_progress --workspace_id "/Users/hue/code/dopemux-mvp" --limit 10
```

## Step 4: Display Context

Show formatted context:
```
Session Context Loaded
═══════════════════════════════════════════

Last Session:
📌 Focus: [current_focus]
✅ Completed: [completed_tasks]
⏭️ Next Steps: [next_steps]
💾 Saved: [session_saved timestamp]

Recent Activity (24h):
[Display recent_decisions if any]
[Display recent_progress entries]

Recent Tasks:
| Status | Description |
|--------|-------------|
[Loop through last 10 progress entries]

═══════════════════════════════════════════

Ready to continue! 💪
• /dx:implement - Start a task
• /dx:session start - Begin session
```

## ADHD Support

- Show most recent info first
- Limit display (top 10, last 24h)
- Visual formatting for quick scanning
- Gentle reminder of context
- Be encouraging about returning to work
