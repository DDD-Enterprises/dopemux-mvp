## Task: Externalize Model Configurations
- **ID**: 20250906-185622
- **Priority**: Low
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: None

### Description
Move hardcoded model configurations to external YAML or JSON files for easier management and deployment.

### Implementation Details
Identify all hardcoded model configs in src/chatx/embeddings/psychology.py (lines 30-48, 51-65). Create YAML/JSON schema for configs. Use PyYAML (>=6.0) or Python’s built-in json module to load configs at runtime. Refactor code to read from external files and validate schema on load.

### Test Strategy
Write unit tests to verify correct loading and validation of configuration files. Test fallback behavior for missing or malformed configs. Ensure backward compatibility where required.

### Migration Notes
- Originally Task ID: 18
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: low
- Status mapping: pending
- Dependencies: []

### Related Files
- Original: .taskmaster/tasks/tasks.json
