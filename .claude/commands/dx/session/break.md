---
description: "Take 5-minute ADHD-friendly break"
allowed-tools: ["Bash", "mcp__conport__get_active_context", "mcp__conport__update_active_context"]
model: "claude-sonnet-4-5-20250929"
---

# /dx:session break - Take a Break

Pause your current session for a 5-minute rejuvenating break.

## Step 1: Get Current Session

Use mcp__conport__get_active_context to see current task.

## Step 2: Log Break

Optional - call ADHD Engine to log break:
```bash
curl -s -X POST http://localhost:8095/api/v1/recommend-break \
  -H "Content-Type: application/json" \
  -d '{"user_id": "current_user", "work_duration": 25}' | python -m json.tool
```

## Step 3: Update Context

```
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content '{"on_break": true, "break_start": "CURRENT_TIMESTAMP"}'
```

## Step 4: Break Guidance

Show:
```
☕ 5-Minute Break Time!
═══════════════════════════════════════════

You've been focused - time to recharge! 💙

Break Activities (choose one):
• 5-minute walk (get moving)
• Hydrate (grab water/tea)
• Stretch (release tension)
• Deep breathing (3-5 deep breaths)
• Look away from screen (20-20-20 rule)
• Quick snack (if hungry)

Set a 5-minute timer and step AWAY from computer.

Come back refreshed! Use /dx:session resume when ready.
═══════════════════════════════════════════
```

## Notes

- Encourage user to actually step away
- 5 minutes is optimal for ADHD (not too long)
- Be supportive and gentle
