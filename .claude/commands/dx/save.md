---
description: "Save current session context to ConPort"
allowed-tools: ["mcp__conport__update_active_context", "mcp__conport__log_decision"]
model: "claude-sonnet-4-5-20250929"
---

# /dx:save - Save Session Context

Save your current work session to ConPort for later restoration.

## Step 1: Gather Session Info

Ask user:
```
Save Session to ConPort
═══════════════════════════════════════════

What were you working on? (brief summary)
>

What did you accomplish?
>

What's next when you return?
>
```

## Step 2: Update Active Context

```
mcp__conport__update_active_context with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  patch_content: {
    "current_focus": "USER_SUMMARY",
    "completed_tasks": ["USER_ACCOMPLISHMENTS"],
    "next_steps": ["USER_NEXT_STEPS"],
    "session_saved": "CURRENT_TIMESTAMP"
  }
```

## Step 3: Optional Decision Logging

Ask: "Any architectural or important decisions to log? (y/n)"

If yes:
- Ask for decision summary
- Ask for rationale
- Use mcp__conport__log_decision with provided info

## Step 4: Confirmation

Show:
```
✅ Session Saved to ConPort
═══════════════════════════════════════════

Your work context is preserved.

Next session:
• /dx:load - Restore this context
• You'll see exactly where you left off

Safe to close! Your progress won't be lost. 💙
═══════════════════════════════════════════
```

## ADHD Support

- Make saving quick and painless
- Don't ask for too much detail
- Celebrate the act of saving (good habit!)
- Reassure that context is preserved
