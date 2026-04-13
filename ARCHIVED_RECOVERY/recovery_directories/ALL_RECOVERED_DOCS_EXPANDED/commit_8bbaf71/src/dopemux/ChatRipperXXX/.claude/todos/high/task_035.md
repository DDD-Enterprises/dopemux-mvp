## Task: Build Command Inventory and Mapping (Layer 1 of Consolidation)
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [32], [33]

### Description
Implement initial command discovery and static mapping for file types and slash commands to canonical actions as the first step of Progressive Command Consolidation.

### Implementation Details
Monitor active files and command inputs using hooks. Construct and maintain static mapping tables from file extensions and slash commands to canonical actions defined in ConfigManager. Use watchdog for file system events and regex for command parsing. Optimize for <50ms detection latency. Ensure mappings are deterministic and compatible with subsequent consolidation phases.

### Test Strategy
Unit test detection accuracy, mapping logic correctness, and latency. Snapshot tests to ensure canonical mappings remain stable unless explicitly changed. Validate coverage across a wide variety of file types and command patterns.

### Migration Notes
- Originally Task ID: 35
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [32, 33]

### Related Files
- Original: .taskmaster/tasks/tasks.json
