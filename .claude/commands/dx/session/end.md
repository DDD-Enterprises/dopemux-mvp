---
description: "End session and update task status"
allowed-tools: ["Bash", "mcp__conport__get_active_context", "mcp__conport__update_progress", "mcp__conport__update_active_context", "mcp__conport__get_progress"]
model: "sonnet-4.5"
---

# /dx:session end - Complete Session

End your current work session with progress tracking and break recommendation.

## Step 1: Get Current Session

Use mcp__conport__get_active_context to retrieve session info.

Get task details using current_task ID.

## Step 2: Check Completion Status

Ask user:
```
Session Checkpoint
═══════════════════════════════════════════

How did it go?

Task status:
1. ✅ DONE (task completed!)
2. 🔄 IN_PROGRESS (good progress, need more time)
3. ⏸️ BLOCKED (encountered blocker)
4. 📝 TODO (didn't start yet)

Select status (1-4):
```

## Step 3: Get Progress Notes

Ask user: "Any progress notes to add? (brief summary of what you accomplished)"

## Step 4: Update ConPort

```
mcp__conport__update_progress with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  progress_id: TASK_ID
  status: SELECTED_STATUS
  description: "ORIGINAL_DESCRIPTION [Progress: USER_NOTES]"
```

## Step 5: Break Recommendation

Call ADHD Engine:
```bash
curl -s -X POST http://localhost:8095/api/v1/recommend-break \
  -H "Content-Type: application/json" \
  -d '{"user_id": "current_user", "work_duration": 25}' | python -m json.tool
```

Show break suggestion with recommendations from response.

## Step 6: Celebration (if DONE)

If status is DONE, show celebration:
```
✅ ✅ ✅ AWESOME! TASK COMPLETE! ✅ ✅ ✅
═══════════════════════════════════════════

[TASK_DESCRIPTION]

🎉 You did it! Excellent work!

Progress: [USER_NOTES]

Take that well-deserved break, then:
• /dx:implement - Start next task
• /dx:stats - See your progress
• /dx:save - Save session notes

Keep crushing it! 💪
═══════════════════════════════════════════
```

## Step 7: Update Active Context

```
mcp__conport__update_active_context with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  patch_content: {
    "last_session_end": "CURRENT_TIMESTAMP",
    "last_task_status": "SELECTED_STATUS",
    "session_completed": true,
    "current_task": null
  }
```

## ADHD Support

- Celebrate all progress (not just completion)
- Encourage break-taking
- Non-judgmental about incomplete tasks
- Supportive tone throughout
