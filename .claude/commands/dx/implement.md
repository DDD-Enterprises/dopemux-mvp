---
description: "ADHD-optimized 25-minute implementation session with task assessment"
arguments: "[task_id]"
allowed-tools: [
  "Bash", "Read", "Write", "Edit", "Grep", "Glob", "TodoWrite",
  "mcp__conport__*",
  "mcp__serena__*",
  "mcp__pal__apilookup",
  "mcp__zen__thinkdeep", "mcp__zen__debug", "mcp__zen__codereview"
]
model: "claude-sonnet-4-5-20250929"
---

# /dx:implement - ADHD Implementation Session

Start an ADHD-optimized 25-minute focused implementation session with intelligent task assessment and break management.

**Purpose**: Provide structured, supportive implementation sessions that respect ADHD needs for focus, breaks, and progress tracking.

---

## Phase 1: Task Selection & ADHD Assessment

### Step 1.1: Get Task

**If task_id provided in $ARGUMENTS**:

- Query ConPort for specific task:

  ```bash
  Use mcp__conport__get_progress with workspace_id "/Users/hue/code/dopemux-mvp" and limit 100
  ```

- Find task matching provided ID or description substring

**If no task_id provided**:

- Query ConPort for TODO tasks:

  ```bash
  Use mcp__conport__get_progress with:
    workspace_id: "/Users/hue/code/dopemux-mvp"
    status_filter: "TODO"
    limit: 10
  ```

- Show available tasks with brief descriptions

### Step 1.2: Assess Task Suitability (ADHD Engine Integration)

For the selected task:

1. **Estimate task complexity** (0.0-1.0 scale):
   - Simple refactor/docs: 0.3
   - Standard feature: 0.5-0.6
   - Complex architecture/debugging: 0.8
   - Use your judgment based on description

2. **Call ADHD Engine for assessment**:

   ```bash
   Use Bash tool:
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

3. **Display ADHD Assessment Results**:

   ```
   ═══════════════════════════════════════════
   ADHD Task Assessment
   ═══════════════════════════════════════════

   ⚡ Energy Match: [suitability_score as percentage]
   🧠 Cognitive Load: [cognitive_load_level]
   ✅ Suitability: [energy_match as percentage]

   Recommendations:
   [Loop through recommendations array and display each]
   💡 [message]
      → [suggested_actions as bullet points]

   ═══════════════════════════════════════════
   ```

4. **Decision Point**:
   - If suitability_score < 0.6:
     - Show: "⚠️ This task may be challenging right now"
     - Ask: "Continue anyway? (y/n) Or select different task?"
   - If user selects "n": Go back to Step 1.1
   - If suitability >= 0.6 or user confirms: Proceed

**Error Handling**: If ADHD Engine unavailable:

- Show: "⚠️ ADHD assessment unavailable (is adhd-engine running?)"
- Show: "Proceeding with standard 25-minute session"
- Continue to Phase 2

---

## Phase 2: Session Start

### Step 2.1: Update ConPort Task Status

```bash
Use mcp__conport__update_progress with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  progress_id: TASK_ID
  status: "IN_PROGRESS"
  description: "ORIGINAL_DESCRIPTION (session started)"
```

### Step 2.2: Update Active Context

```bash
Use mcp__conport__update_active_context with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  patch_content: {
    "current_task": "TASK_ID",
    "session_start": "CURRENT_TIMESTAMP",
    "session_type": "implement",
    "target_duration": 25
  }
```

### Step 2.3: Display Session Start

Show to user:

```
🚀 Implementation Session Started
═══════════════════════════════════════════

📋 Task: [TASK_DESCRIPTION]
⏱️ Duration: 25 minutes
🎯 Focus: Stay on this task, minimize context switches

ADHD Support Active:
✅ Progress tracked in ConPort
✅ Break reminder at 25 minutes
✅ Energy-optimized task selection

Let's build! 💪
═══════════════════════════════════════════
```

---

## Phase 3: Implementation Work

**Instructions for Implementation Phase**:

You are now in focused implementation mode. Follow these ADHD-supportive guidelines:

### Work Guidelines

- **Stay Focused**: Work on this one task only
- **Save Frequently**: After each meaningful change, save your work
- **Track Progress**: Update your mental progress estimate
- **Minimize Switches**: If you need to look something up, keep it brief and return to task

### ADHD Accommodations

**If Feeling Stuck**:

- Break the current step into even smaller pieces
- Start with the easiest part
- It's okay to make progress incrementally

**If Distracted**:

- Acknowledge the distraction
- Gently return focus to the task
- No judgment - this is normal

**If Overwhelmed**:

- Pause and reassess
- Consider if task complexity was underestimated
- It's okay to break early and adjust approach

### Progress Checkpoints

After each major step (file created, test passing, feature working):

- Briefly note progress
- Optionally save to ConPort with progress note
- Celebrate small wins internally

---

## Phase 4: Session Completion

**After 25 minutes of work OR when task reaches natural checkpoint**:

### Step 4.1: Check Completion Status

Ask user:

```
Session checkpoint reached!

Task status:
- ✅ DONE (task completed)
- 🔄 IN_PROGRESS (still working, good progress)
- ⏸️ BLOCKED (encountered blocker)
- 🔀 CONTEXT_SWITCH (need to switch tasks)

What's the status?
```

### Step 4.2: Update ConPort

```bash
Use mcp__conport__update_progress with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  progress_id: TASK_ID
  status: USER_SELECTED_STATUS
  description: "DESCRIPTION (+ brief progress note)"
```

### Step 4.3: Break Reminder

Show break recommendation:

```
☕ Time for a 5-Minute Break!
═══════════════════════════════════════════

You've been focused for 25 minutes - great work!

Break Suggestions:
• 5-minute walk (get blood flowing)
• Hydrate (water break)
• Stretch (release tension)
• Deep breathing (3-5 breaths)
• Look away from screen (20-20-20 rule)

Set a 5-minute timer and step away.
You've earned this break! 💙

═══════════════════════════════════════════
```

### Step 4.4: Celebration (if DONE)

If status is DONE:

```
✅ ✅ ✅ AWESOME! TASK COMPLETE! ✅ ✅ ✅

[TASK_DESCRIPTION]

🎉 You crushed it!

Next steps:
- Take that well-deserved break
- Then: /dx:implement for next task
- Or: /dx:stats to see your progress

Keep up the great work!
```

### Step 4.5: Update Active Context

```bash
Use mcp__conport__update_active_context with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  patch_content: {
    "last_session_end": "CURRENT_TIMESTAMP",
    "last_task_status": "USER_STATUS",
    "session_completed": true
  }
```

---

## Error Handling

**If ConPort MCP unavailable**:

- Show: "⚠️ ConPort unavailable - progress won't be saved"
- Continue session anyway (user's choice)
- Suggest: "Save work manually and retry later"

**If ADHD Engine unavailable**:

- Already handled in Phase 1
- Session continues without assessment

**If user interrupts mid-session**:

- That's okay! ADHD-friendly design
- Work is saved if user used Write/Edit tools
- Can resume with /dx:session resume

---

## Success Criteria

- ✅ Task selected (with or without ADHD assessment)
- ✅ Session started (ConPort updated to IN_PROGRESS)
- ✅ User completed focused work
- ✅ Progress tracked in ConPort
- ✅ Break reminder shown
- ✅ Supportive, encouraging tone maintained throughout

---

## Notes for Claude

**Tone**: Be warm, encouraging, and supportive. Celebrate progress.
**Visuals**: Use progress bars, boxes, emojis for visual engagement.
**Flexibility**: If user wants to deviate from 25min, that's fine - adjust.
**ADHD First**: Always prioritize user wellbeing over rigid process.
