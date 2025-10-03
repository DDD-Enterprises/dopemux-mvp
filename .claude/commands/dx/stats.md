---
description: "ADHD metrics dashboard - energy, attention, progress"
allowed-tools: ["Bash", "mcp__conport__get_progress", "mcp__conport__get_active_context"]
model: "claude-sonnet-4-5-20250929"
---

# /dx:stats - ADHD Metrics Dashboard

Display comprehensive ADHD metrics and development progress.

## Step 1: Get ADHD State

Query ADHD Engine:
```bash
curl -s http://localhost:8095/api/v1/energy-level/current_user | python -m json.tool
curl -s http://localhost:8095/api/v1/attention-state/current_user | python -m json.tool
curl -s http://localhost:8095/health | python -m json.tool
```

## Step 2: Get Progress Metrics

Query ConPort for completion data:
```
mcp__conport__get_progress --workspace_id "/Users/hue/code/dopemux-mvp" --limit 50
```

Calculate:
- Total tasks
- Completed tasks (status=DONE)
- In-progress tasks
- Completion rate (last 24h)

## Step 3: Get Session Info

```
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
```

## Step 4: Display Dashboard

Show comprehensive metrics:
```
ADHD Metrics Dashboard
═══════════════════════════════════════════

Current State:
⚡ Energy Level: [energy_level]
👁️ Attention: [attention_state]
🎯 Focus Quality: [based on attention]

Progress (Last 24h):
📊 Tasks Completed: XX / YY ([completion_rate]%)
🔄 In Progress: XX tasks
📋 TODO: XX tasks

Completion Trend: [████████░░] XX%

Session Info:
⏱️ Active Session: [Yes/No]
📝 Current Task: [description OR "None"]
☕ Last Break: [from active_context]

ADHD Engine Status:
🟢 Monitors Active: [monitors_active from health]
📊 Accommodations Made: [from accommodation_stats]

Break Compliance:
[Visual indicator of break adherence]

Recommendations:
[Based on current energy/attention]
💡 [Context-appropriate suggestions]

═══════════════════════════════════════════

Keep up the great work! 💪
```

## Visual Enhancements

- Use progress bars for completion rates
- Color coding (🟢🟡🔴) for status
- Tables for task breakdown
- Celebration for high completion rates

## Error Handling

If ADHD Engine unavailable:
- Show: "⚠️ ADHD metrics unavailable"
- Still show ConPort progress metrics
- Suggest starting engine

## ADHD Support

- Celebrate progress (no matter how small)
- Non-judgmental metrics presentation
- Focus on trends, not absolutes
- Encourage based on current state
