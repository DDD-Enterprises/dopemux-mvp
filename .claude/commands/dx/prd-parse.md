---
description: "Parse PRD into ADHD-optimized tasks using Zen planner"
arguments: "<prd_file_path>"
allowed-tools: ["Read", "mcp__zen__planner", "mcp__conport__log_progress", "mcp__conport__link_conport_items", "mcp__conport__batch_log_items"]
model: "claude-sonnet-4-5-20250929"
---

# /dx:prd-parse - PRD to ConPort Tasks

Parse a PRD (Product Requirements Document) into ADHD-optimized task breakdown using Zen planner, with human review before importing to ConPort.

**Purpose**: Convert high-level requirements into actionable, ADHD-friendly tasks with proper chunking, complexity assessment, and dependency tracking.

---

## Step 1: Read PRD Document

Use Read tool on $ARGUMENTS (PRD file path).

Validate file exists and is readable.

## Step 2: Call Zen Planner

Use mcp__zen__planner to break down the PRD:

```
Prompt to Zen planner:

"Break down this PRD into ADHD-optimized task hierarchy:

PRD CONTENT:
[Insert full PRD content here]

Requirements:
- Create task hierarchy (epics → stories → subtasks if applicable)
- Estimate complexity for each task (0.0-1.0 scale)
- Chunk tasks to 15-90 minute durations (prefer 25-minute chunks)
- Assign energy requirements (low/medium/high)
- Identify dependencies between tasks
- Add break points for long tasks
- Include acceptance criteria

Format as structured task list with:
- Task ID/sequence
- Description (clear, actionable)
- Complexity score
- Estimated duration (minutes)
- Energy required
- Dependencies (task IDs)
- Parent task (if subtask)
"
```

Continue planner steps until complete task breakdown received.

## Step 3: Enhance with ADHD Metadata

For each task from Zen planner:

Calculate cognitive_load:
```python
cognitive_load = (complexity * 0.4) + (duration/60 * 0.3) + task_type_factor(0.1-0.4)
```

Ensure duration <= 90 minutes (if longer, flag for further chunking).

Add ADHD fields:
- `complexity_score`: From Zen estimate
- `estimated_minutes`: Duration
- `energy_required`: low/medium/high based on complexity
- `cognitive_load`: Calculated value
- `break_points`: Array for tasks >45 min

## Step 4: HUMAN REVIEW (Critical - Approach C)

Display task summary table:
```
PRD Task Breakdown - Review Before Import
═══════════════════════════════════════════

Total Tasks: XX | Estimated Time: XX hours

| # | Description | Dur | Energy | Complexity | Deps |
|---|-------------|-----|--------|------------|------|
| 1 | [desc]      | 25m | Medium | 0.6        | -    |
| 2 | [desc]      | 45m | High   | 0.8        | 1    |
...

═══════════════════════════════════════════

Review tasks carefully.

Options:
1. ✅ Approve - Import all tasks to ConPort
2. ✏️ Edit - Modify specific tasks
3. ❌ Cancel - Abort import

Your choice?
```

If user selects Edit:
- Allow modifications to any task
- Re-display table
- Ask for approval again

If user selects Cancel:
- Show: "Import cancelled. No changes made to ConPort."
- Exit command

## Step 5: Batch Import to ConPort

If approved, use mcp__conport__batch_log_items:

```
--workspace_id "/Users/hue/code/dopemux-mvp"
--item_type "progress_entry"
--items [
  {
    "status": "TODO",
    "description": "TASK_DESCRIPTION | Duration: XXm | Complexity: X.X | Energy: LEVEL"
  },
  ... for each task
]
```

## Step 6: Create Dependency Links

For each task with dependencies:

```
mcp__conport__link_conport_items with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  source_item_type: "progress_entry"
  source_item_id: DEPENDENT_TASK_ID
  target_item_type: "progress_entry"
  target_item_id: DEPENDENCY_TASK_ID
  relationship_type: "BLOCKS"
  description: "Task X blocks Task Y"
```

## Step 7: Success Summary

Show:
```
✅ PRD Import Complete!
═══════════════════════════════════════════

Imported: XX tasks to ConPort
Dependencies: XX links created

Tasks are now available in ConPort:
• /dx:implement - Start first task
• /dx:load - View all tasks
• Query ConPort directly with mcp__conport__get_progress

Happy building! 🚀
═══════════════════════════════════════════
```

## Error Handling

**If Zen planner unavailable**:
- Show: "Zen planner unavailable. Manual task breakdown needed."
- Guide user through manual task creation

**If PRD file not found**:
- Show: "PRD file not found at: [path]"
- Ask for correct path

**If ConPort batch import fails**:
- Show which tasks failed
- Offer to retry or import individually

## Success Criteria

- ✅ PRD parsed and understood
- ✅ Tasks broken down with ADHD metadata
- ✅ Human reviewed and approved
- ✅ Tasks imported to ConPort
- ✅ Dependencies linked
- ✅ Ready for implementation

## Notes

- Always require human review (Approach C quality gate)
- Be patient with review process
- Support task modifications before import
- Celebrate successful import
