---
description: "Start ADHD session with energy check"
arguments: "[task_id]"
allowed-tools: ["Bash", "mcp__conport__get_progress", "mcp__conport__update_progress", "mcp__conport__update_active_context"]
model: "claude-sonnet-4-5-20250929"
---

# /dx:session start - Begin ADHD Session

Start a focused work session with energy and attention state check.

## Step 1: Get Current ADHD State

Use Bash tool to query ADHD Engine:
```bash
curl -s http://localhost:8095/api/v1/energy-level/current_user | python -m json.tool
curl -s http://localhost:8095/api/v1/attention-state/current_user | python -m json.tool
```

Show results:
```
Current ADHD State:
⚡ Energy: [energy_level]
👁️ Attention: [attention_state]
```

## Step 2: Select Task

If $ARGUMENTS has task_id:
- Use mcp__conport__get_progress to find specific task
Else:
- Use mcp__conport__get_progress with status_filter="TODO" and limit=10
- Show top 3 tasks suitable for current energy

## Step 3: Start Session

Update ConPort progress:
```
mcp__conport__update_progress --workspace_id "/Users/hue/code/dopemux-mvp" --progress_id TASK_ID --status "IN_PROGRESS"
```

Update active context:
```
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content '{"current_task": "TASK_ID", "session_start": "TIMESTAMP"}'
```

Show:
```
🚀 Session Started
═══════════════════════════════════════════
Task: [DESCRIPTION]
Duration: 25 minutes recommended
Focus mode activated!
═══════════════════════════════════════════
```

## ADHD Support

- Be encouraging and supportive
- Remind user to minimize context switches
- It's okay to take breaks when needed
- Celebrate starting the session
