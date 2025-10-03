---
description: "Quick ADHD task assessment"
arguments: "[task_id_or_description]"
allowed-tools: ["Bash", "mcp__conport__get_progress"]
model: "claude-sonnet-4-5-20250929"
---

# /dx:assess - Quick ADHD Task Assessment

Get rapid ADHD suitability assessment for a task.

## Step 1: Get Task

If $ARGUMENTS provided:
- Use mcp__conport__get_progress to find task
Else:
- Ask user for task description
- Estimate complexity from description

## Step 2: Assess with ADHD Engine

Estimate task parameters:
- Complexity: 0.3 (simple) to 0.8 (complex)
- Duration: 25 minutes default
- Description: From ConPort or user input

Call ADHD Engine:
```bash
curl -s -X POST http://localhost:8095/api/v1/assess-task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "current_user",
    "task_id": "TASK_ID",
    "task_data": {
      "complexity_score": ESTIMATED_COMPLEXITY,
      "estimated_minutes": 25,
      "description": "TASK_DESCRIPTION",
      "dependencies": []
    }
  }' | python -m json.tool
```

## Step 3: Display Results

Show formatted assessment:
```
ADHD Task Assessment
═══════════════════════════════════════════

Task: [DESCRIPTION]

Suitability: ████████░░ [suitability_score]%
Energy Match: ████████░░ [energy_match]%
Cognitive Load: [cognitive_load_level]

Current ADHD State:
⚡ Energy: [from adhd_insights]
👁️ Attention: [from adhd_insights]

Recommendations:
[Loop through recommendations]
💡 [message]
   → [suggested_actions]

Optimal Timing:
[Display optimal_timing recommendations]

═══════════════════════════════════════════

Ready to start? Use /dx:implement [task_id]
```

## Error Handling

If ADHD Engine unavailable:
- Show: "⚠️ ADHD Engine not running. Start with: docker-compose up adhd-engine"
- Provide basic assessment based on complexity only

## Notes

- Quick assessment for task selection
- Visual progress bars for engagement
- Be encouraging regardless of suitability score
