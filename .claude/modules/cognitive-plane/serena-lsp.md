# Serena LSP Server Module

**Module Version**: 1.0.0
**Authority**: Code Navigation and Developer Memory
**Modes**: ACT primarily, some PLAN support
**Service**: `/services/serena/server.py`

## Authority Boundaries

**Serena ONLY Authority:**
- Code navigation and semantic understanding
- LSP operations (completion, diagnostics, go-to-definition, find references)
- Symbol search and workspace navigation
- Session memory (navigation breadcrumbs, working context)
- Developer interruption recovery and context restoration

**Serena NEVER:**
- Modifies task data (ConPort progress_entry authority)
- Stores architectural decisions (ConPort decision authority)
- Parses PRDs or decomposes requirements (SuperClaude authority)

## Core LSP Capabilities

### Full Language Server Protocol Support
- **Code Completion**: Intelligent autocomplete with context awareness
- **Diagnostics**: Real-time error detection and warnings
- **Go-to-Definition**: Navigate to symbol definitions
- **Find References**: Locate all symbol usages
- **Symbol Search**: Project-wide symbol discovery
- **Cross-file Analysis**: Understand code relationships

### ADHD-Optimized Features
```bash
# Serena ADHD Configuration
- Max Search Results: Limited to 10 to prevent overwhelming results
- Context Depth: 3 levels max to limit complexity
- Progressive Disclosure: Show essential information first, details on request
- Navigation Breadcrumbs: Track navigation history for context switching
- Intelligent Suggestions: Categorize refactoring by complexity and risk
- Gentle Guidance: Supportive feedback and encouraging language
```

## Memory Architecture

### Persistent Memory Storage
```
.serena/
├── memories/           # Persistent memory files
├── contexts/          # Context configurations
├── embeddings/        # Semantic code embeddings
└── navigation_history/ # Developer exploration patterns
```

### Session Memory Management
```bash
# Automatic context restoration after interruptions
RESTORE_SERENA_CONTEXT() {
    echo "🔄 Welcome back! Continuing from yesterday:"
    echo " → You were exploring: GPTResearcher workflow in server.py"
    echo " → Last function: create_research_prompt() line 28"
    echo " → Related files you examined: utils.py, __init__.py"
    echo " → Suggested next: Test the research prompt function"
}
```

## Integration Commands

### Code Navigation for Task Context
```bash
# When Task-Orchestrator provides file context for current task
LOAD_TASK_CONTEXT() {
    TASK_ID="$1"

    # Task-Orchestrator provides relevant file paths
    # Serena loads semantic context for those files
    # Working memory populated with task-specific symbols and dependencies

    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Serena loaded context for task $TASK_ID" \
      --rationale "LSP server populated with relevant symbols and file relationships for focused development" \
      --tags ["serena", "task-context", "lsp"]
}
```

### Cross-Plane Integration
```bash
# Code change events flow to other systems
HANDLE_CODE_CHANGE() {
    FILE_PATH="$1"
    CHANGE_TYPE="$2"

    # Serena detects code changes through LSP
    # ConPort logs implementation decisions
    # Integration Bridge notifies Leantime

    # Flow: Serena → ConPort → Integration Bridge → Leantime
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Code change detected in $FILE_PATH" \
      --rationale "Serena LSP detected $CHANGE_TYPE change, updating project context" \
      --tags ["code-change", "serena", "implementation"]
}
```

## ADHD Accommodation Patterns

### Attention State Adaptation
```bash
# Adjust behavior based on attention level
ADAPT_TO_ATTENTION() {
    ATTENTION_LEVEL="$1"  # scattered, focused, hyperfocus

    case $ATTENTION_LEVEL in
        "scattered")
            # Minimal context, essential info only
            # Single-file focus, hide complex relationships
            # Quick navigation, immediate feedback
            ;;
        "focused")
            # Full context within current module
            # Show related files and dependencies
            # Detailed diagnostics and suggestions
            ;;
        "hyperfocus")
            # Deep context across entire codebase
            # Full relationship mapping
            # Advanced refactoring suggestions
            ;;
    esac
}
```

### Context Switching Support
```bash
# Preserve mental model across interruptions
SAVE_INTERRUPTION_CONTEXT() {
    CONTEXT_DATA='{
        "session_id": "'$(date +%Y-%m-%d-%H%M)'",
        "current_file": "'$CURRENT_FILE'",
        "current_symbol": "'$CURRENT_SYMBOL'",
        "exploration_path": ['$EXPLORATION_PATH'],
        "next_logical_step": "'$NEXT_STEP'",
        "attention_level": "'$ATTENTION_LEVEL'"
    }'

    # Save to .serena/navigation_history/
    echo $CONTEXT_DATA > .serena/navigation_history/interruption_$(date +%s).json
}
```

## Integration with Other Memory Systems

### Serena ↔ ConPort Coordination
```bash
# Link code exploration to architectural decisions
LINK_EXPLORATION_TO_DECISION() {
    EXPLORATION_CONTEXT="$1"
    DECISION_ID="$2"

    mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
      --source_item_type "custom_data" --source_item_id "serena-session-$SESSION_ID" \
      --target_item_type "decision" --target_item_id "$DECISION_ID" \
      --relationship_type "informed_by"
}
```

### Progressive Disclosure Coordination
```bash
# Coordinate context depth across all memory systems
COORDINATE_CONTEXT_DEPTH() {
    ATTENTION_STATE="$1"

    if [ "$ATTENTION_STATE" = "scattered" ]; then
        # Serena: Show only current function
        # ConPort: Show only essential decisions
        # Task Management: Show single next action
        CONTEXT_DEPTH=1
    elif [ "$ATTENTION_STATE" = "hyperfocus" ]; then
        # Show full context across all memory layers
        CONTEXT_DEPTH=5
    fi

    # Update all systems with coordinated depth
}
```

## Performance Optimizations

- **Symbol Indexing**: Fast symbol lookup and navigation
- **Incremental Analysis**: Only analyze changed files
- **Context Caching**: Cache frequently accessed contexts
- **Lazy Loading**: Load contexts on demand to prevent overwhelm
- **Response Prioritization**: Essential information first, details on request