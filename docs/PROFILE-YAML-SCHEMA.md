---
id: PROFILE-YAML-SCHEMA
title: Profile Yaml Schema
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Profile YAML Schema Specification

**Version**: 1.0.0
**Date**: 2025-10-05
**Status**: Reference Implementation

---

## Schema Definition

### Required Fields

```yaml
name: string              # Unique profile identifier (lowercase, no spaces)
display_name: string      # Human-readable name for UI display
description: string       # Brief description of profile purpose
mcps: array[string]       # List of MCP server names to load
```

### Optional Fields

```yaml
adhd_config:              # ADHD optimization settings
  energy_preference: enum # Preferred energy level: any, low, medium, high, hyperfocus
  attention_mode: enum    # Preferred attention: any, scattered, focused, hyperfocused
  session_duration: int   # Recommended session length in minutes (default: 50)

auto_detection:           # Auto-detection rules
  git_branches: array[string]     # Git branch patterns (supports wildcards)
  directories: array[string]      # Directory path patterns
  file_patterns: array[string]    # File extension patterns
  time_windows: array[string]     # Time ranges in HH:MM-HH:MM format
```

---

## MCP Server Names

Valid MCP server names (must match Claude settings.json keys):

- `conport` - **REQUIRED** in all profiles (memory authority)
- `serena-v2` - Code navigation and LSP
- `zen` - Multi-model reasoning (thinkdeep, planner, consensus, debug, codereview)
- `context7` - Official library documentation
- `gpt-researcher` - Deep web research
- `dope-context` - Hybrid code search
- `desktop-commander` - Desktop automation and control
- `morph-llm` - Code transformation and bulk edits
- `magic-mcp` - UI component generation
- `playwright` - Browser automation and testing
- `tavily` - Web search API
- `mas-sequential-thinking` - Multi-agent sequential thinking
- `sequential_thinking` - Multi-step reasoning (deprecated, use zen)

---

## Validation Rules

### Critical Rules

1. **ConPort Required**: `conport` MUST be present in every profile's `mcps` array
2. **Unique Name**: Profile `name` must be unique across all profiles
3. **Valid MCPs**: All MCP names in `mcps` array must exist in Claude config
4. **Energy Values**: energy_preference must be one of: any, low, medium, high, hyperfocus
5. **Attention Values**: attention_mode must be one of: any, scattered, focused, hyperfocused

### Format Rules

- **name**: lowercase, alphanumeric with hyphens only (no spaces)
- **time_windows**: Must be in HH:MM-HH:MM format (24-hour time)
- **git_branches**: Supports glob patterns (e.g., "feature/*", "fix/*")
- **directories**: Relative or absolute paths
- **session_duration**: Integer minutes (typical: 25, 50, 90)

---

## Example Profiles

### Minimal Profile (Required Fields Only)

```yaml
name: minimal
display_name: "Minimal"
description: "Bare minimum profile for testing"
mcps:
  - conport
```

### Full Profile (All MCP Servers)

```yaml
name: full
display_name: "Full Stack"
description: "All MCP servers for complex multi-domain tasks"
mcps:
  - conport
  - serena-v2
  - zen
  - context7
  - gpt-researcher
  - claude-context
  - dope-context

adhd_config:
  energy_preference: any
  attention_mode: any
  session_duration: 50
```

### Developer Profile

```yaml
name: developer
display_name: "Developer"
description: "Code implementation and debugging"
mcps:
  - conport          # Memory (required)
  - serena-v2        # LSP navigation
  - dope-context     # Semantic search

adhd_config:
  energy_preference: medium-high
  attention_mode: focused
  session_duration: 50

auto_detection:
  git_branches:
    - "feature/*"
    - "fix/*"
    - "refactor/*"

  directories:
    - "src/"
    - "tests/"
    - "lib/"

  file_patterns:
    - "*.py"
    - "*.ts"
    - "*.js"
    - "*.go"

  time_windows:
    - "09:00-12:00"    # Morning focus
    - "14:00-17:00"    # Afternoon focus
```

### Researcher Profile

```yaml
name: researcher
display_name: "Researcher"
description: "Deep investigation and analysis"
mcps:
  - conport
  - zen
  - gpt-researcher
  - context7

adhd_config:
  energy_preference: high
  attention_mode: hyperfocused
  session_duration: 90

auto_detection:
  git_branches:
    - "research/*"
    - "analysis/*"
    - "docs/*"

  directories:
    - "docs/"
    - "research/"

  file_patterns:
    - "*.md"
    - "*.pdf"

  time_windows:
    - "10:00-12:00"
    - "14:00-17:00"
```

### Architect Profile

```yaml
name: architect
display_name: "Architect"
description: "System design and architectural planning"
mcps:
  - conport
  - zen
  - serena-v2
  - dope-context

adhd_config:
  energy_preference: high
  attention_mode: focused
  session_duration: 50

auto_detection:
  git_branches:
    - "design/*"
    - "arch/*"
    - "spike/*"

  directories:
    - "docs/architecture/"
    - "docs/design/"

  file_patterns:
    - "*.md"
    - "*.yaml"

  time_windows:
    - "09:00-11:00"    # Early morning clarity
```

---

## Schema Versioning

**Current Version**: 1.0.0

**Version History**:
- 1.0.0 (2025-10-05): Initial schema definition

**Future Extensions** (Post-MVP):
- Custom MCP server configurations per profile
- Profile-specific environment variable overrides
- Tool-level filtering (not just MCP-level)
- Profile inheritance/composition
- Cloud profile sync metadata

---

## Validation Error Messages

### Missing ConPort
```
Error: Profile 'developer' is invalid
Reason: 'conport' is required in all profiles (memory authority)
Fix: Add 'conport' to mcps array
```

### Invalid MCP Name
```
Error: Profile 'custom' is invalid
Reason: MCP server 'unknown-mcp' not found in Claude config
Available: conport, serena-v2, zen, context7, gpt-researcher, claude-context, dope-context
Fix: Use only valid MCP server names
```

### Invalid Energy Value
```
Error: Profile 'test' is invalid
Reason: adhd_config.energy_preference 'super-high' is not valid
Valid values: any, low, medium, high, hyperfocus
Fix: Use one of the valid energy values
```

### Invalid Time Window
```
Error: Profile 'custom' is invalid
Reason: time_window '9am-5pm' must be in HH:MM-HH:MM format
Valid example: "09:00-17:00"
Fix: Use 24-hour time format
```

---

## Implementation Notes

### Loading Priority
1. Validate YAML syntax
2. Check required fields (name, display_name, description, mcps)
3. Validate ConPort presence
4. Validate MCP names against Claude config
5. Validate enum values (energy, attention)
6. Validate format (time windows, patterns)

### Default Values
- `adhd_config`: Not required (omit if not used)
- `auto_detection`: Not required (manual-only profile)
- `energy_preference`: Defaults to "any" if adhd_config provided but energy omitted
- `attention_mode`: Defaults to "any" if adhd_config provided but attention omitted
- `session_duration`: Defaults to 50 minutes

---

**Next Steps**: Implement Pydantic models in `src/dopemux/profile_manager.py`
