# Actual MCP Tools Inventory - Dopemux

**Date**: January 18, 2025
**Status**: Evidence-Based from Working Environment
**Purpose**: Document actual MCP tools currently available in the Dopemux environment

## Currently Loaded MCP Tools (14 Total)

Based on your `/context` output, here are the MCP tools actually loaded and available:

### 1. CLI Tools (2 tools - 1,027 tokens)
```yaml
mcp__cli__run_command:
  tokens: 653
  description: Execute CLI commands in controlled environment

mcp__cli__show_security_rules:
  tokens: 374
  description: Display security restrictions and allowed operations
```

### 2. Exa Research Tools (4 tools - ~2,000 tokens)
```yaml
mcp__exa__search_web:
  tokens: ~500
  description: AI-powered neural web search with autoprompt optimization
  parameters:
    - query: Search query string
    - num_results: Number of results (default: 10)
    - use_autoprompt: Enable AI query enhancement (default: true)
    - include_domains: Domain whitelist
    - exclude_domains: Domain blacklist
    - date_filters: Publication date ranges
    - search_type: neural/keyword search modes

mcp__exa__search_and_contents:
  tokens: ~500
  description: Combined search and content extraction in single operation
  features:
    - Unified search + content retrieval
    - Optimized for research workflows
    - Reduced API calls

mcp__exa__get_contents:
  tokens: ~500
  description: Extract detailed content from specific URLs
  capabilities:
    - Full webpage content extraction
    - Structured text output
    - Configurable content length limits

mcp__exa__find_similar:
  tokens: ~500
  description: Discover similar websites and related resources
  use_cases:
    - Resource discovery
    - Competitive analysis
    - Research breadth expansion

implementation_details:
  server_type: Custom FastMCP server
  api_client: Official exa-py>=1.0.0
  health_monitoring: Built-in /health endpoint
  docker_ready: Python 3.11-slim container
  network_mode: HTTP transport on port 3008
```

### 3. Claude-Context Tools (4 tools - 2,373 tokens)
```yaml
mcp__claude-context__index_codebase:
  tokens: 770
  description: Index repository for semantic code search
  status: Your project is NOT currently indexed

mcp__claude-context__search_code:
  tokens: 769
  description: Natural language code search across codebase

mcp__claude-context__clear_index:
  tokens: 407
  description: Reset/clear codebase index

mcp__claude-context__get_indexing_status:
  tokens: 427
  description: Check indexing progress and status
```

### 4. Context7 Documentation Tools (2 tools - 1,343 tokens)
```yaml
mcp__context7__resolve-library-id:
  tokens: 691
  description: Find correct library identifiers for documentation
  verified_working: ✅ Tested with React - returns 30+ library matches

mcp__context7__get-library-docs:
  tokens: 652
  description: Retrieve official documentation and code examples
  capabilities:
    - Version-specific documentation
    - Current code examples
    - Up-to-date API information
    - Reduces hallucinated information
```

### 5. Morphllm Fast Apply Tools (1 tool - 987 tokens)
```yaml
mcp__morphllm-fast-apply__edit_file:
  tokens: 987
  description: Intelligent code editing with pattern recognition
  note: Pattern-aware editing and bulk transformations
```

### 6. MAS Sequential Thinking Tools (1 tool - 900 tokens)
```yaml
mcp__mas-sequential-thinking__sequentialthinking:
  tokens: 900
  description: Multi-agent reasoning with specialized coordination
  verified_docker_tools:
    - sequentialthinking: Multi-step reasoning process
    - health_check: Server status and diagnostics
    - server_diagnostics: Advanced troubleshooting
  agents: Planner, Researcher, Analyzer, Critic, Synthesizer
```

## Available But Not Currently Loaded

### 7. ConPort (Context Portal) - Priority: HIGH
**Repository**: github.com/GreatScottyMac/context-portal
**Status**: Not installed
**Tools**: 25+ memory management tools

```yaml
context_management:
  - get_product_context: Retrieve project goals and architecture
  - update_product_context: Update project-level information
  - get_active_context: Get current session focus and state
  - update_active_context: Update current working context

decision_tracking:
  - log_decision: Record architectural/implementation decisions
  - get_decisions: Retrieve logged decisions
  - search_decisions_fts: Full-text search across decisions
  - delete_decision_by_id: Remove specific decisions

progress_management:
  - log_progress: Track task status and completion
  - get_progress: Retrieve progress entries
  - update_progress: Modify existing progress
  - delete_progress_by_id: Remove progress entries

system_patterns:
  - log_system_pattern: Record coding/architectural patterns
  - get_system_patterns: Retrieve system patterns
  - delete_system_pattern_by_id: Remove patterns

custom_data:
  - log_custom_data: Store custom key-value data
  - get_custom_data: Retrieve custom data
  - search_custom_data_value_fts: Full-text search custom data
  - search_project_glossary_fts: Search project terminology

knowledge_graph:
  - link_conport_items: Create item relationships
  - get_linked_items: Explore linked items
  - semantic_search_conport: AI-powered conceptual search

session_management:
  - get_recent_activity_summary: Session restoration data
  - export_conport_to_markdown: Backup to markdown
  - import_markdown_to_conport: Restore from markdown
  - get_conport_schema: Tool introspection
```

### 8. Desktop Commander MCP - Priority: MEDIUM
**Repository**: github.com/wonderwhy-er/DesktopCommanderMCP
**Status**: Not installed

```yaml
terminal_operations:
  - execute_terminal_commands: Run commands with output streaming
  - background_execution: Background process management
  - interactive_process_control: Manage interactive processes

file_system:
  - read_write_files: File operations
  - create_list_directories: Directory management
  - move_files_directories: File system organization
  - search_files: File discovery
  - get_file_metadata: File information
  - negative_offset_reading: Read from end of files

code_editing:
  - surgical_text_replacements: Precise code modifications
  - full_file_rewrites: Complete file replacement
  - multiple_file_editing: Bulk editing operations
  - pattern_based_replacements: Regex-based changes
  - recursive_code_search: VSCode ripgrep integration

process_management:
  - list_running_processes: Process discovery
  - kill_processes: Process termination
  - interact_with_processes: SSH, database, server interaction

configuration:
  - get_set_configuration: Settings management
  - update_multiple_settings: Bulk configuration
  - dynamic_configuration: Runtime updates

code_execution:
  - execute_python_memory: In-memory Python execution
  - execute_nodejs_memory: In-memory Node.js execution
  - execute_r_memory: In-memory R execution
  - instant_data_analysis: CSV/JSON analysis

logging:
  - comprehensive_audit_logging: Full activity logs
  - automatic_tool_logging: Tool call tracking
  - log_rotation: 10MB size limit management
```

### 9. OpenMemory (mem0) - Priority: MEDIUM
**Repository**: docs.mem0.ai/openmemory/overview
**Status**: Not installed

```yaml
memory_operations:
  - add_memories: Store new memory objects locally
  - search_memory: Retrieve relevant memories
  - list_memories: View all stored memory
  - delete_all_memories: Clear memory entirely

characteristics:
  - local_execution: Runs entirely on user machine
  - unified_memory_layer: Cross-application memory access
  - cross_client_access: No cloud synchronization needed
  - standardized_apis: Consistent memory interface
```

## Tool Overlap Analysis

### Memory Management
1. **ConPort**: Project-specific, comprehensive knowledge graph
2. **OpenMemory**: Cross-application, simple memory operations
3. **Assessment**: ConPort is more sophisticated for development workflows

### Code Operations
1. **Claude-Context**: Semantic code search and indexing
2. **Morphllm**: Intelligent code editing
3. **Desktop Commander**: File system and direct code manipulation
4. **Assessment**: Complementary rather than overlapping

### Research & Documentation
1. **Exa**: Advanced web research and company analysis
2. **Context7**: Official library documentation
3. **Assessment**: Different research domains, both valuable

### Development Environment
1. **CLI**: Basic command execution with security
2. **Desktop Commander**: Comprehensive desktop automation
3. **Assessment**: Desktop Commander is more comprehensive

## Token Usage Analysis

### Current Load: ~8,630 tokens (4.3% of 200k context)
- Exa: ~2,000 tokens (4 research tools - UPDATED)
- Claude-Context: 2,373 tokens (code analysis)
- Context7: 1,343 tokens (documentation)
- MAS Sequential: 900 tokens (reasoning)
- Morphllm: 987 tokens (editing)
- CLI: 1,027 tokens (commands)

### Recommended Additions (estimated)
- ConPort: ~3,000 tokens (25+ tools)
- Desktop Commander: ~2,500 tokens (20+ tools)
- OpenMemory: ~800 tokens (4 tools)

### Projected Total: ~14,930 tokens (7.5% of context)

## Priority Installation Recommendations

### Phase 1: Essential Memory (Immediate)
1. **ConPort**: Critical for ADHD context preservation
   - Solves memory/context switching challenges
   - Provides project knowledge graph
   - Enables session restoration

### Phase 2: Enhanced Productivity (Next Week)
1. **Desktop Commander**: Comprehensive automation
   - Reduces context switching between applications
   - Enables complex workflows
   - Direct system integration

2. **Index Current Codebase**: claude-context
   - Enable semantic code search
   - Currently NOT indexed (verified)

### Phase 3: Specialized Tools (Evaluate)
1. **OpenMemory**: If cross-application memory needed
   - Simple memory operations
   - Local storage only
   - May overlap with ConPort

## ADHD-Specific Assessment

### Must Have (Reduces Cognitive Load)
- ✅ **MAS Sequential Thinking**: Complex reasoning support
- ✅ **Context7**: Reduces documentation hunting
- ⭐ **ConPort**: Essential context preservation

### High Value (Streamlines Workflow)
- ✅ **Claude-Context**: When indexed, reduces code searching
- ✅ **Morphllm**: Intelligent code editing
- ⭐ **Desktop Commander**: Reduces app switching

### Medium Value (Nice to Have)
- ✅ **Exa**: Research automation
- ⭐ **OpenMemory**: Cross-app memory (if needed)

### Current Gaps
1. **Context Preservation**: ConPort installation critical
2. **Code Search**: Need to index codebase
3. **Desktop Integration**: Desktop Commander for workflow automation

## Next Steps Recommendations

1. **Install ConPort**: Priority #1 for ADHD memory support
2. **Index Codebase**: Enable claude-context search
3. **Test Desktop Commander**: Evaluate complexity vs. benefit
4. **Consider OpenMemory**: Only if cross-app memory needed
5. **Token Budget Management**: Monitor total usage under 10k tokens