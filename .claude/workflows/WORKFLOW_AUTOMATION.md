# MCP Workflow Automation Rules
**Purpose**: Automatic MCP server selection based on workflow context
**Status**: Active - Used by Claude Code for intelligent tool routing

## 🎯 Core Principle

**Right Tool, Right Time**: Automatically select optimal MCP servers based on:
- Current workflow phase (research → design → plan → implement → review → commit)
- Task complexity (simple, moderate, complex, critical)
- User intent keywords
- File types being worked on
- Previous tool success patterns

## 🔄 Workflow Detection Rules

### Trigger Keywords → Phase Mapping

```yaml
RESEARCH:
  keywords: ["how to", "what is", "find", "search", "lookup", "docs", "documentation", "api", "library"]
  file_patterns: []
  auto_activate: ["pal apilookup", "dope-context"]

DESIGN:
  keywords: ["design", "architect", "decide", "choose", "approach", "strategy", "plan feature"]
  file_patterns: ["*.md", "*.txt", "docs/*", "ADR-*"]
  auto_activate: ["pal planner", "pal consensus", "conport"]

PLANNING:
  keywords: ["break down", "decompose", "tasks", "subtasks", "steps", "checklist"]
  file_patterns: []
  auto_activate: ["task-orchestrator", "conport"]

IMPLEMENTATION:
  keywords: ["implement", "code", "write", "create", "add", "build", "develop"]
  file_patterns: ["*.py", "*.js", "*.ts", "*.tsx", "*.go", "*.rs"]
  auto_activate: ["serena-v2", "dope-context", "pal apilookup"]

REVIEW:
  keywords: ["review", "check", "audit", "analyze", "inspect", "quality"]
  file_patterns: []
  auto_activate: ["pal codereviewer", "serena-v2"]

DEBUGGING:
  keywords: ["bug", "error", "fix", "debug", "troubleshoot", "investigate"]
  file_patterns: []
  auto_activate: ["serena-v2", "dope-context", "pal debug"]

COMMIT:
  keywords: ["commit", "ready", "done", "finished", "complete"]
  file_patterns: []
  auto_activate: ["pal codereviewer", "conport"]
```

## 🧠 Smart Selection Logic

### By Complexity Score

```yaml
SIMPLE: # 1-2 steps, single file
  prefer: ["pal apilookup", "serena-v2"]
  avoid: ["pal consensus", "task-orchestrator"]

MODERATE: # 3-5 steps, 2-3 files
  prefer: ["pal planner", "dope-context", "serena-v2"]
  suggest: ["task-orchestrator"]

COMPLEX: # 6-10 steps, 4+ files
  prefer: ["task-orchestrator", "pal planner", "pal consensus"]
  require: ["conport"]

CRITICAL: # 11+ steps, architectural impact
  require: ["task-orchestrator", "pal consensus", "conport"]
  suggest: ["pal thinkdeep"]
```

### By File Type

```yaml
python_files:
  patterns: ["*.py"]
  activate: ["serena-v2", "pal apilookup"]
  search_for: "Python APIs, type hints, pytest patterns"

javascript_files:
  patterns: ["*.js", "*.jsx", "*.ts", "*.tsx"]
  activate: ["serena-v2", "pal apilookup"]
  search_for: "React, TypeScript, Node.js patterns"

documentation:
  patterns: ["*.md", "*.rst", "*.txt", "docs/*"]
  activate: ["dope-context"]
  search_for: "Existing project docs, ADRs, RFCs"

config_files:
  patterns: ["*.yaml", "*.json", "*.toml", "*.env*"]
  activate: ["dope-context"]
  search_for: "Configuration patterns, environment setup"
```

## 🎬 Automatic Workflow Sequences

### Feature Implementation Flow
```yaml
sequence:
  1_research:
    phase: RESEARCH
    tools: ["pal apilookup", "dope-context"]
    output: "Library APIs and existing similar features"

  2_design:
    phase: DESIGN
    tools: ["pal planner", "pal consensus"]
    output: "Feature design with trade-offs"
    decision_log: "conport"

  3_planning:
    phase: PLANNING
    tools: ["task-orchestrator"]
    output: "Task breakdown with complexity scores"

  4_implement:
    phase: IMPLEMENTATION
    tools: ["serena-v2", "dope-context", "pal apilookup"]
    output: "Working code"
    progress_log: "conport"

  5_review:
    phase: REVIEW
    tools: ["pal codereviewer", "serena-v2"]
    output: "Code quality report"

  6_commit:
    phase: COMMIT
    tools: ["pal codereviewer", "conport"]
    output: "Clean commit with updated task status"
```

### Bug Fix Flow
```yaml
sequence:
  1_investigate:
    phase: DEBUGGING
    tools: ["serena-v2", "dope-context"]
    action: "Find error location and related code"

  2_analyze:
    phase: DEBUGGING
    tools: ["pal debug", "serena-v2"]
    action: "Root cause analysis"

  3_plan_fix:
    phase: PLANNING
    tools: ["task-orchestrator"]
    action: "Simple breakdown if needed"

  4_implement_fix:
    phase: IMPLEMENTATION
    tools: ["serena-v2", "pal apilookup"]
    action: "Apply fix"

  5_review:
    phase: REVIEW
    tools: ["pal codereviewer"]
    action: "Verify fix doesn't break anything"

  6_commit:
    phase: COMMIT
    tools: ["conport"]
    action: "Log fix and close task"
```

### Architecture Decision Flow
```yaml
sequence:
  1_research:
    phase: RESEARCH
    tools: ["gpt-researcher", "pal apilookup", "dope-context"]
    action: "Gather options and prior art"

  2_analyze:
    phase: DESIGN
    tools: ["pal consensus"]
    action: "Multi-perspective trade-off analysis"

  3_decide:
    phase: DESIGN
    tools: ["conport"]
    action: "Log decision with full rationale"
    required: true

  4_document:
    phase: DESIGN
    tools: []
    action: "Create ADR in docs/90-adr/"
```

## 🎯 Tool Selection Matrix

### Primary vs Fallback Tools

```yaml
documentation_lookup:
  primary: "pal apilookup"
  fallback: "exa"
  never: "gpt-researcher"  # Too slow for simple lookups

code_search:
  primary: "dope-context"
  fallback: "serena-v2"
  never: "exa"  # Not for local code

code_navigation:
  primary: "serena-v2"
  fallback: "dope-context"
  never: "pal apilookup"  # Not for navigation

task_breakdown:
  primary: "task-orchestrator"
  fallback: "pal planner"
  never: "manual breakdown"  # Always use tools

code_review:
  primary: "pal codereviewer"
  fallback: "serena-v2 complexity check"
  never: "skip review"  # Always review

decision_logging:
  primary: "conport"
  fallback: "markdown file"
  never: "skip logging"  # Always log architectural decisions
```

## ⚡ Performance Optimization Rules

### Parallel vs Sequential

```yaml
PARALLEL_SAFE:
  # These can run simultaneously
  - "pal apilookup" + "dope-context" (research phase)
  - "serena-v2" + "dope-context" (code exploration)
  - Multiple "pal apilookup" calls (different libraries)

MUST_SEQUENTIAL:
  # These must run in order
  - "pal planner" → "task-orchestrator" (design before breakdown)
  - "task-orchestrator" → implementation (plan before execute)
  - implementation → "pal codereviewer" (code before review)
  - "pal codereviewer" → "conport" (review before logging)
```

### On-Demand vs Always-On

```yaml
ALWAYS_ON:
  # Keep these running for instant response
  - serena-v2  # Code navigation needed anytime
  - conport    # Decision logging needed anytime
  - qdrant     # Vector DB for dope-context
  - redis-primary  # Caching for multiple servers

START_ON_DEMAND:
  # Start these when needed, stop when idle
  - gpt-researcher  # Only for deep research
  - exa             # Only when pal apilookup lacks info
  - task-master-ai  # Unclear if needed with task-orchestrator

OPTIONAL:
  # Can be disabled for resource constraints
  - activity-capture  # ADHD metrics (nice-to-have)
  - desktop-commander # Desktop automation (optional)
```

## 🔧 Configuration Integration

### Claude Code Integration
These rules are automatically applied when using Claude Code in this project. The workflow phase is detected from:
- User's natural language request
- File being edited
- Previous tool usage in session
- Task complexity assessment

### Override Mechanisms
```yaml
explicit_override:
  # User can override auto-selection
  command: "Use [tool-name] to..."
  precedence: "User explicit > Auto-selection > Default"

context_override:
  # Project-specific overrides in .claude/project.yaml
  example:
    for_react_project:
      IMPLEMENTATION:
        prefer: ["pal apilookup[react]", "serena-v2"]
```

## 📊 Success Metrics

Track these to improve auto-selection:
- **Tool Selection Accuracy**: % of auto-selections that weren't overridden
- **Workflow Completion Rate**: % of workflows that reached commit phase
- **Average Tools Per Task**: Lower is better (fewer wrong selections)
- **Time to First Useful Result**: Faster = better tool selection

## 🎓 Learning System

```yaml
pattern_learning:
  track:
    - User overrides (which tools did they choose instead?)
    - Successful workflows (which tool sequences worked well?)
    - Failed attempts (which tools didn't help?)

  adapt:
    - Update primary/fallback preferences
    - Adjust complexity thresholds
    - Refine keyword detection
    - Personalize to user patterns
```

## 📝 Examples

### Example 1: "How do I use React hooks?"
```yaml
detected_phase: RESEARCH
detected_keywords: ["how", "use"]
detected_file_type: null
complexity: SIMPLE

auto_selected:
  - pal apilookup (primary for docs)
  - topic: "React hooks documentation"

workflow:
  1. Query pal apilookup for React hooks
  2. Return official React documentation
  3. No other tools needed
```

### Example 2: "Implement user authentication"
```yaml
detected_phase: IMPLEMENTATION
detected_keywords: ["implement"]
detected_file_type: null
complexity: COMPLEX

auto_selected:
  - pal apilookup (research auth patterns)
  - task-orchestrator (break down implementation)
  - dope-context (find existing auth code)
  - serena-v2 (navigate codebase)
  - pal codereviewer (review before commit)
  - conport (log implementation decisions)

workflow:
  1. Research: pal apilookup "authentication best practices"
  2. Find examples: dope-context "authentication implementation"
  3. Design: pal planner "auth system design"
  4. Log decision: conport log_decision
  5. Plan: task-orchestrator "break down auth implementation"
  6. Implement: serena-v2 + pal apilookup
  7. Review: pal codereviewer
  8. Commit: conport update_progress
```

### Example 3: "Fix bug in login.py"
```yaml
detected_phase: DEBUGGING
detected_keywords: ["fix", "bug"]
detected_file_type: "python"
complexity: MODERATE

auto_selected:
  - serena-v2 (navigate to login.py and find issue)
  - dope-context (find similar error handling)
  - pal debug (systematic debugging)

workflow:
  1. Navigate: serena-v2 find_symbol "login"
  2. Analyze: serena-v2 analyze_complexity
  3. Search context: dope-context "login error handling"
  4. Debug: pal debug "login failure analysis"
  5. Fix: implement
  6. Review: pal codereviewer
  7. Commit: conport log fix
```

---

**Status**: Active
**Last Updated**: 2026-02-05
**Next Review**: After 100 workflow executions to refine auto-selection
