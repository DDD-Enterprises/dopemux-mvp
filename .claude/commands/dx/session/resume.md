---
description: "Resume session after break with context restoration"
allowed-tools: ["mcp__conport__get_active_context", "mcp__conport__update_active_context", "mcp__conport__get_progress"]
model: "sonnet-4.5"
---

# /dx:session resume - Resume After Break

Resume your work session with gentle context restoration.

## Step 1: Get Session Context

Use mcp__conport__get_active_context to retrieve current session state.

Get current task details:
```
mcp__conport__get_progress --workspace_id "/Users/hue/code/dopemux-mvp" --limit 100
```
Find the task matching current_task ID from active_context.

## Step 2: Show Context Restoration

Display:
```
Welcome Back! 💙
═══════════════════════════════════════════

You were working on:
📋 [task description]

Session started: [session_start time]
Break duration: [calculated duration]

Ready to continue?
═══════════════════════════════════════════
```

## Step 3: Update Context

Use mcp__conport__update_active_context:
```
--workspace_id "/Users/hue/code/dopemux-mvp"
--patch_content '{"on_break": false, "resume_time": "CURRENT_TIMESTAMP"}'
```

## Step 4: Gentle Re-Orientation

Show:
```
🎯 Let's continue where you left off.

Take a moment to:
1. Review your last changes
2. Recall what you were doing
3. Identify your next step

Then dive back in! You've got this! 💪
```

## ADHD Support

- Gentle re-orientation (not abrupt)
- Allow mental transition time
- Supportive, non-judgmental tone
- Acknowledge break was beneficial
