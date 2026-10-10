# Complete Tool Inventory & Role Mapping

## Overview

This document provides a comprehensive inventory of all MCP servers, their tools, and role-based access patterns. The tool census is automated via MetaMCP discovery and maintained in ConPort for live tracking.

## MCP Server Inventory

### 1. Task-Orchestrator (Kotlin MCP)
**Source**: https://github.com/jpicklyk/task-orchestrator
**Status**: Available, Docker-ready
**Tools**: 37 total

#### Core Project Management
```yaml
project_tools:
  - create_project
  - update_project
  - list_projects
  - get_project_details
  - archive_project

feature_tools:
  - create_feature
  - update_feature
  - list_features
  - get_feature_details
  - link_feature_to_project

task_tools:
  - create_task
  - update_task
  - list_tasks
  - get_task_details
  - assign_task
  - complete_task
  - add_task_dependency
  - validate_dependencies
```

#### Templates (9 available)
- Requirements Template
- Technical Approach Template
- Testing Strategy Template
- Bug Triage Template
- Feature Specification Template
- Architecture Decision Record (ADR) Template
- Risk Assessment Template
- Implementation Plan Template
- Documentation Template

#### Workflows (5 available)
- task_breakdown_workflow
- implement_feature_workflow
- bug_triage_workflow
- code_review_workflow
- release_planning_workflow

### 2. Task-Master AI
**Source**: https://github.com/eyaltoledano/claude-task-master
**Status**: Available, NPM installable
**Strength**: Code-aware when using Claude Code provider

#### Core Tools
```yaml
task_generation:
  - parse_prd: "Convert PRD document into structured tasks"
  - expand_task: "Break down high-level task into subtasks"
  - analyze_complexity: "Estimate effort and complexity"
  - validate_dependencies: "Check for circular dependencies"

research_tools:
  - research_topic: "Deep research with web search"
  - analyze_requirements: "Extract technical requirements"
  - competitive_analysis: "Compare solutions and approaches"

integration:
  - list_tasks: "Get current task state"
  - update_task: "Modify task details and status"
  - sync_with_codebase: "Analyze current code for context"
```

### 3. Claude-Context (Existing)
**Source**: https://github.com/zilliztech/claude-context
**Status**: Production-ready
**Backend**: Milvus vector database

#### Tools
```yaml
code_search:
  - search: "Semantic search across codebase"
  - get_context: "Retrieve relevant code context"
  - refresh_index: "Update embeddings for changed files"
  - get_file_summary: "High-level file purpose and structure"
  - analyze_dependencies: "Map code dependencies"
```

### 4. Doc-Context (To Build)
**Status**: Specification complete, needs implementation
**Pattern**: Mirror Claude-Context for documents

#### Planned Tools
```yaml
document_search:
  - search_hybrid: "Dense + sparse search with fusion"
  - get_snippets: "Extract relevant document sections"
  - cite: "Generate citations for retrieved content"
  - refresh_index: "Update document embeddings"
  - analyze_document_structure: "Extract headings and sections"

hybrid_retrieval:
  - dense_search: "Vector similarity search"
  - sparse_search: "BM25 full-text search"
  - fuse_results: "RRF or weighted score combination"
  - rerank: "Apply Voyage rerank-2.5"
```

### 5. ConPort (Context Portal)
**Status**: Available
**Purpose**: Structured project memory

#### Tools
```yaml
memory_management:
  - log_decision: "Record architectural or product decision"
  - get_decisions: "Query decision history"
  - update_context: "Store structured project context"
  - query_graph: "Graph traversal queries"
  - learn_user_traits: "Record ADHD patterns and preferences"

project_knowledge:
  - store_artifact: "Save designs, specs, etc."
  - get_artifact: "Retrieve project artifacts"
  - link_artifacts: "Create relationships between items"
  - search_context: "Full-text search across project memory"
```

### 6. Sequential-Thinking (MAS Extended)
**Source**: Custom extension of MAS sequential-thinking
**Status**: Available with custom thought modes

#### Tools
```yaml
reasoning:
  - think: "Multi-step sequential reasoning"
  - stage_transition: "Move between reasoning stages"
  - summarize: "Synthesize findings across stages"
  - backtrack: "Return to earlier reasoning stage"

custom_modes:
  - deep_analysis: "Extended investigation mode"
  - architecture_reasoning: "Systems design thinking"
  - problem_solving: "Debug and troubleshoot mode"
```

### 7. Zen MCP (Multi-tool Suite)
**Status**: Available
**Strength**: Meta-reasoning and validation

#### Tools (Limited selection to avoid token bloat)
```yaml
meta_reasoning:
  - consensus: "Multi-model agreement analysis"
  - planner: "Interactive planning with revision"
  - codereview: "Systematic code review"
  - debug: "Root cause analysis"
  - precommit: "Change validation"
  - challenge: "Critical thinking verification"
```

### 8. Serena & Desktop Commander
**Status**: Available
**Purpose**: System operations and file management

#### Tools
```yaml
file_operations:
  - edit: "Advanced file editing"
  - search: "File system search"
  - navigate: "Directory traversal"

system_commands:
  - execute_command: "System command execution"
  - manage_processes: "Process monitoring"
  - file_operations: "Advanced file manipulations"
```

### 9. Morph/Fast-Apply
**Status**: Available
**Purpose**: Code refactoring and bulk changes

#### Tools
```yaml
refactoring:
  - refactor: "Structural code changes"
  - bulk_edit: "Multiple file modifications"
  - pattern_replace: "Pattern-based replacements"
  - apply_codemod: "Automated code transformations"
```

## Role-Based Tool Access Matrix

### Product Owner
**Primary Tools**:
- Task-Orchestrator: create_project, Requirements Template
- Task-Master: parse_prd, analyze_requirements
- ConPort: log_decision, update_context

**Context Budget**: 20% system prompt, 50% business context, 30% retrieved docs

### Researcher
**Primary Tools**:
- Task-Master: research_topic, competitive_analysis
- Doc-Context: search_hybrid, get_snippets, cite
- ConPort: store_artifact, link_artifacts
- Sequential-Thinking: deep_analysis

**Context Budget**: 15% system prompt, 35% research queries, 40% retrieved evidence, 10% memory

### Product Architect
**Primary Tools**:
- Task-Orchestrator: Requirements Template, Feature Specification Template
- Task-Master: analyze_requirements
- ConPort: log_decision, get_decisions
- Doc-Context: search_hybrid

**Context Budget**: 20% system prompt, 40% requirements context, 30% retrieved specs, 10% memory

### Engineering Architect
**Primary Tools**:
- Task-Orchestrator: Technical Approach Template, ADR Template, validate_dependencies
- Claude-Context: search, get_context, analyze_dependencies
- ConPort: log_decision, query_graph
- Sequential-Thinking: architecture_reasoning

**Context Budget**: 20% system prompt, 30% technical requirements, 40% code context, 10% memory

### Planner / Task Planner
**Primary Tools**:
- Task-Orchestrator: task_breakdown_workflow, create_task, add_task_dependency
- Task-Master: expand_task, analyze_complexity
- Zen MCP: planner

**Context Budget**: 25% system prompt, 45% task context, 20% retrieved planning info, 10% memory

### TDD Engineer / Implementer
**Primary Tools**:
- Claude-Context: search, get_context, refresh_index
- Task-Orchestrator: implement_feature_workflow, Testing Strategy Template
- Morph: refactor, bulk_edit
- Serena: edit, navigate

**Context Budget**: 15% system prompt, 35% task specification, 45% code context, 5% memory

### Validator
**Primary Tools**:
- Claude-Context: search, analyze_dependencies
- Task-Orchestrator: Testing Strategy Template, complete_task
- Zen MCP: codereview, debug
- Sequential-Thinking: problem_solving

**Context Budget**: 20% system prompt, 30% test requirements, 40% code/test context, 10% memory

### Docs Writer
**Primary Tools**:
- Doc-Context: search_hybrid, get_snippets
- Task-Orchestrator: Documentation Template
- ConPort: get_artifact, search_context
- Serena: edit

**Context Budget**: 20% system prompt, 30% documentation requirements, 40% existing docs context, 10% memory

### PR/QA
**Primary Tools**:
- Zen MCP: precommit, codereview
- Claude-Context: search, analyze_dependencies
- Task-Orchestrator: code_review_workflow
- Sequential-Thinking: problem_solving

**Context Budget**: 25% system prompt, 25% PR context, 40% code review context, 10% memory

### Scrum Master
**Primary Tools**:
- Task-Orchestrator: list_projects, list_tasks, release_planning_workflow
- ConPort: query_graph (for impediments and dependencies)
- Task-Master: analyze_complexity (for estimation)

**Context Budget**: 30% system prompt, 40% project status, 20% team metrics, 10% memory

## Tool Census Automation

### MetaMCP Discovery Integration
```python
# Automated tool inventory
async def refresh_tool_census():
    servers = await metamcp.list_servers()
    for server in servers:
        tools = await server.list_tools()
        resources = await server.list_resources()
        prompts = await server.list_prompts()

        # Store in ConPort for tracking
        await conport.store_artifact({
            "type": "mcp_server_inventory",
            "server_name": server.name,
            "tools": tools,
            "resources": resources,
            "prompts": prompts,
            "timestamp": datetime.utcnow()
        })
```

### Change Detection
```python
# Generate diff reports on tool changes
def generate_tool_diff(old_inventory, new_inventory):
    return {
        "added_tools": new_inventory.tools - old_inventory.tools,
        "removed_tools": old_inventory.tools - new_inventory.tools,
        "modified_schemas": detect_schema_changes(old_inventory, new_inventory),
        "role_access_impact": analyze_role_impact(changes)
    }
```

## Token Budget Management

### Schema Size Monitoring
Current MCP tool schemas consume significant tokens:
- **Zen MCP**: ~25k tokens (full suite) - **limit to 5-6 tools per role**
- **Task-Orchestrator**: ~8k tokens (37 tools) - **acceptable**
- **Claude-Context**: ~3k tokens - **efficient**
- **Sequential-Thinking**: ~3.2k tokens - **acceptable**

### Optimization Strategies
1. **Role-Specific Whitelisting**: Only expose relevant tools per role
2. **Dynamic Loading**: Load tool schemas on-demand
3. **Schema Compression**: Shorter descriptions, essential parameters only
4. **Tool Grouping**: Composite operations to reduce schema count

## Integration Testing Matrix

| Role | Primary MCP | Secondary MCPs | Integration Points | Test Coverage |
|------|-------------|----------------|-------------------|---------------|
| Product Owner | Task-Orchestrator | Task-Master, ConPort | PRD → Tasks sync | ✅ |
| Researcher | Task-Master | Doc-Context, ConPort | Evidence gathering | 🔄 |
| TDD Engineer | Claude-Context | Task-Orchestrator, Morph | Code → Test flow | ✅ |
| Validator | Zen MCP | Claude-Context, Task-Orchestrator | Review workflow | 🔄 |

**Legend**: ✅ Tested, 🔄 In Progress, ❌ Not Started

---

Generated: 2025-09-24
Status: Complete inventory with role mappings
Next: Integration requirements and cross-client support