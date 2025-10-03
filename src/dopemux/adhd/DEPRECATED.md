# ⚠️ DEPRECATED MODULE

**This ADHD module has been replaced as part of Path C Migration.**

## Deprecated Component

**task_decomposer.py** - DELETED

**Replaced By**:
1. **ConPort progress_entry** - Task storage with ADHD metadata
2. **SuperClaude /dx: commands** - Workflow automation
3. **ADHD Engine Service** - Intelligent task assessment

## Migration Details

**Old**: Standalone TaskDecomposer class with local JSON storage (`.dopemux/tasks/`)

**New**: Distributed architecture:
- Tasks stored in ConPort SQLite database
- ADHD intelligence in services/adhd_engine/
- User interface via SuperClaude /dx: commands

**Data Migrated**: October 3, 2025
- 3 tasks from tasks.json → ConPort progress_entry (IDs 270, 271, 272)
- Original data archived to: `.dopemux/archive/tasks_archived_2025-10-03/`

## Remaining Components in this Module

- `attention_monitor.py` - ACTIVE (still used)
- `context_manager.py` - ACTIVE (still used)
- `task_decomposer.py` - DELETED

## For Developers

Use these instead of TaskDecomposer:

**Create Task**:
```
Use ConPort MCP: mcp__conport__log_progress
```

**List Tasks**:
```
SuperClaude command: /dx:load
Or MCP: mcp__conport__get_progress
```

**ADHD Assessment**:
```
SuperClaude command: /dx:assess
Or HTTP: curl http://localhost:8095/api/v1/assess-task
```

**Implementation Session**:
```
SuperClaude command: /dx:implement
```

## Documentation

- Migration ADR: `docs/90-adr/ADR-XXXX-path-c-migration.md`
- ConPort Decisions: #140, #141, #147, #148, #150, #152
