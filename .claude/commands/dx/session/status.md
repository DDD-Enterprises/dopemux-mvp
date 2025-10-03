---
description: "Show current session status and ADHD metrics"
allowed-tools: ["Bash", "mcp__conport__get_active_context", "mcp__conport__get_progress"]
model: "sonnet-4.5"
---

# /dx:session status - Current Session State

Display current session information and ADHD metrics.

## Step 1: Get Session Info

Use mcp__conport__get_active_context to get current session.

If current_task exists, get task details with mcp__conport__get_progress.

## Step 2: Get ADHD Metrics

Query ADHD Engine:
```bash
curl -s http://localhost:8095/api/v1/energy-level/current_user | python -m json.tool
curl -s http://localhost:8095/api/v1/attention-state/current_user | python -m json.tool
```

## Step 3: Display Status

Show formatted status:
```
Session Status
═══════════════════════════════════════════

Current Task: [description OR "No active session"]

Session Info:
⏱️ Started: [session_start OR "N/A"]
🎯 Duration: [calculated minutes OR "N/A"]
📊 Status: [task status OR "No task"]

ADHD State:
⚡ Energy: [energy_level]
👁️ Attention: [attention_state]
☕ Last Break: [from active_context OR "Unknown"]

Actions:
• /dx:session end - Complete current session
• /dx:session break - Take a break
• /dx:implement - Start new task
═══════════════════════════════════════════
```

## Error Handling

If no active session:
- Show: "No active session. Use /dx:implement or /dx:session start to begin."

If ADHD Engine unavailable:
- Show energy/attention as "Unknown"
- Continue with rest of status display
