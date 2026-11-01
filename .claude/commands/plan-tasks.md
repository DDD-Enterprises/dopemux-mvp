Turn the last spec or prompt into a planned task list in **ConPort**, which holds progress (AGENTS.md §6; workflow transitions stay with task-orchestrator).
Show the proposed tasks first and log only the ones the user confirms. For each confirmed task, call: `mcp__conport__conport_log_progress` {"workspace_id":"<repo-root>","description":"<task>","status":"PLANNED","priority":"medium"}
