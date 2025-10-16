# Dopemux Two-Plane Architecture Orchestrator

**Project**: Multi-language ADHD-optimized development platform
**Languages**: Python (all versions), TypeScript, JavaScript, C, C++, Go, PHP
**Architecture**: Two-Plane with Integration Bridge coordination
**Mode**: PLAN/ACT-aware with modular authority boundaries
**Workspace**: `/Users/hue/code/dopemux-mvp`

## 🔧 Mandatory MCP Tool Usage - STRICT ENFORCEMENT

**CRITICAL RULE**: ALL code operations, searches, and memory operations MUST use MCP tools. Native bash/Read/Grep are ONLY for git/docker/system commands.

### 📁 File Operations - Serena-v2 ONLY

**ALWAYS use Serena-v2** for ALL file and code operations:

```python
# Read files (NEVER use Read tool or bash cat)
mcp__serena-v2__read_file(relative_path="src/auth.py")

# List directories (NEVER use bash ls or find)
mcp__serena-v2__list_dir(relative_path="src", recursive=True)

# Navigate code (NEVER use bash grep or Grep tool)
mcp__serena-v2__find_symbol(query="authenticate", symbol_type="function")
mcp__serena-v2__goto_definition(file_path="src/auth.py", line=42, column=10)
mcp__serena-v2__find_references(file_path="src/auth.py", line=42, column=10)
mcp__serena-v2__get_context(file_path="src/auth.py", line=42, context_lines=10)
```

**Why**: LSP-aware, ADHD-optimized (max 10 results, complexity scoring), 78.7ms navigation (2.5x faster than target)

### 🔍 Semantic Search - Dope-Context ALWAYS

**MANDATORY BEFORE** implementing features, debugging, refactoring, or learning codebase:

```python
# Search code (ALWAYS run before implementing)
mcp__dope-context__search_code(
    query="authentication middleware session management",
    profile="implementation",  # or "debugging", "exploration"
    top_k=10
)

# Search documentation
mcp__dope-context__docs_search(
    query="two-plane architecture patterns",
    filter_doc_type="md"
)

# Unified search (code + docs together)
mcp__dope-context__search_all(
    query="SuperClaude MCP integration",
    top_k=10  # 5 code + 5 docs
)
```

**Why**: AST-aware chunking, complexity scoring (0.0-1.0), gpt-5-mini context generation, Voyage embeddings + reranking

**Search-First Workflow** (MANDATORY):
1. **Before implementing**: `search_code("similar feature")` → Find existing patterns
2. **Before debugging**: `search_code("error handling for X")` → Find error patterns
3. **Before refactoring**: `search_code("high complexity")` → Identify targets (complexity > 0.6)
4. **When learning**: `search_all("feature X")` → Complete picture (code + docs)

### 📚 Coding Patterns - Context7 ALWAYS

**ALWAYS query Context7** before implementing with any framework/library:

```python
# Get official documentation and patterns
mcp__context7__resolve-library-id(libraryName="react")
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/facebook/react",
    topic="server components best practices"
)

# For Next.js, Vue, TypeScript, etc.
mcp__context7__resolve-library-id(libraryName="next.js")
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/vercel/next.js",
    topic="app router data fetching"
)
```

**Why**: Official curated docs, pattern guidance, version-specific info

### 🧠 Memory & Knowledge Graph - ConPort IMPLICIT

**ConPort operates IMPLICITLY** - auto-log all decisions, progress, patterns:

**Session Start (AUTOMATIC)**:
```python
# Load context (run at session start)
mcp__conport__get_active_context(workspace_id="/Users/hue/code/dopemux-mvp")
mcp__conport__get_recent_activity_summary(workspace_id="/Users/hue/code/dopemux-mvp", hours_ago=24)
```

**Decision Logging (MANDATORY for architectural choices)**:
```python
# After ANY architectural decision
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Use Zen MCP instead of mas-sequential-thinking",
    rationale="Empirical testing: mas-sequential broken, Zen operational",
    implementation_details="Update all /sc: commands to use Zen tools",
    tags=["mcp-integration", "empirical-testing"]
)

# Link decisions to build knowledge graph
mcp__conport__link_conport_items(
    workspace_id="/Users/hue/code/dopemux-mvp",
    source_item_type="decision", source_item_id="143",
    target_item_type="decision", target_item_id="142",
    relationship_type="extends"
)
```

**Progress Tracking (AUTOMATIC)**:
```python
# Track ALL tasks with ADHD metadata
mcp__conport__log_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    status="IN_PROGRESS",
    description="Update SuperClaude commands with Dopemux MCPs",
    linked_item_type="decision", linked_item_id="143"
)

# Update status as work progresses
mcp__conport__update_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    progress_id=42,
    status="DONE"
)
```

**Pattern Logging (AUTOMATIC)**:
```python
# Capture reusable patterns
mcp__conport__log_system_pattern(
    workspace_id="/Users/hue/code/dopemux-mvp",
    name="ADHD 25-minute Focus Session",
    description="Pomodoro with energy matching, auto-save, break reminders",
    tags=["adhd", "session-management"]
)
```

### 🧘 Deep Analysis - Zen MCP + Ultrathink

**Use Zen tools** for complex analysis, planning, debugging:

```python
# Deep investigation (hypothesis-driven)
mcp__zen__thinkdeep(
    step="Analyze authentication flow and session management",
    step_number=1, total_steps=3,
    next_step_required=True,
    findings="Session cookies not httpOnly, potential XSS vector",
    confidence="medium",
    model="gpt-5-pro"  # or "o3-pro" for max intelligence
)

# Interactive planning (incremental)
mcp__zen__planner(
    step="Plan migration from SQLite to PostgreSQL",
    step_number=1, total_steps=5,
    next_step_required=True,
    model="gpt-5-codex"
)

# Multi-model consensus (architecture decisions)
mcp__zen__consensus(
    step="Evaluate: Should we use microservices or monolith?",
    models=[
        {"model": "gpt-5", "stance": "for"},
        {"model": "o3-pro", "stance": "against"},
        {"model": "gpt-5-mini", "stance": "neutral"}
    ],
    findings="Analyzing trade-offs for 10-person team",
    step_number=1, total_steps=4,
    next_step_required=True
)

# Systematic debugging
mcp__zen__debug(
    step="Investigate why memory usage grows unbounded",
    hypothesis="Memory leak in event listener registration",
    findings="Event listeners not cleaned up in useEffect",
    confidence="high",
    files_checked=["src/components/Dashboard.tsx"],
    relevant_files=["src/hooks/useWebSocket.ts"],
    step_number=2, total_steps=3,
    next_step_required=True,
    model="gemini-2.5-pro"
)

# Comprehensive code review
mcp__zen__codereview(
    step="Security audit of authentication module",
    relevant_files=["/Users/hue/code/dopemux-mvp/src/auth/middleware.ts"],
    review_type="security",
    focus_on="JWT handling, password hashing, session management",
    findings="Found 2 critical issues: timing attacks, weak hash",
    issues_found=[
        {"severity": "critical", "description": "Password comparison vulnerable to timing attacks"},
        {"severity": "high", "description": "bcrypt rounds too low (8, should be 12+)"}
    ],
    step_number=1, total_steps=2,
    next_step_required=True,
    model="gpt-5-codex"
)
```

**Ultrathink Activation**:
- Use `thinking_mode="max"` for critical decisions
- Use `model="gpt-5-pro"` or `model="o3-pro"` for maximum intelligence
- Combine with ConPort decision logging for traceability

### ❌ FORBIDDEN Operations

**NEVER use these tools for code operations**:
- ❌ bash `cat`, `head`, `tail` → Use `mcp__serena-v2__read_file`
- ❌ bash `find`, `ls`, `tree` → Use `mcp__serena-v2__list_dir`
- ❌ bash `grep`, `rg`, `ack` → Use `mcp__dope-context__search_code`
- ❌ Read tool for code → Use `mcp__serena-v2__read_file`
- ❌ Grep tool for code → Use `mcp__dope-context__search_code`
- ❌ Glob tool for code → Use `mcp__serena-v2__list_dir` or `mcp__dope-context__search_code`

**Exceptions (bash ONLY for)**:
- ✅ Git operations: `git status`, `git diff`, `git log`, `git add`, `git commit`, `git push`
- ✅ Docker operations: `docker ps`, `docker logs`, `docker-compose up`
- ✅ System commands: `env`, `which`, `python`, `npm`, `pytest`
- ✅ Process management: `lsof`, `ps`, `kill`

## 🧠 Core ADHD Principles

- **Context Preservation**: Auto-save every 30 seconds, maintain awareness across interruptions
- **Gentle Guidance**: Encouraging, supportive language with clear next steps
- **Progressive Disclosure**: Essential info first, details on request
- **Decision Reduction**: Maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Break work into 25-minute segments with visual progress

## ⚡ Two-Plane Architecture

### Project Management Plane

**Authorities**: Status updates, team visibility, task decomposition, dependencies

- **Leantime**: Status authority (planned→active→blocked→done), team dashboards
- **Task-Master**: PRD parsing, AI task decomposition, subtask hierarchies
- **Task-Orchestrator**: 37 specialized tools, dependency analysis, risk assessment

### Cognitive Plane

**Authorities**: Decisions, code navigation, memory, context preservation, semantic search

- **Serena LSP**: Full LSP server with ADHD accommodations (max 10 results, 3-level context depth)
- **ConPort**: Decision logging, knowledge graph, automatic context preservation
- **Dope-Context**: AST-aware semantic search (code + docs), complexity scoring, ADHD-optimized retrieval

### Coordination Layer

**Integration Bridge**: Cross-plane communication at PORT_BASE+16

- **Authority Enforcement**: No direct cross-plane communication allowed
- **Event Routing**: Task-Master → Integration Bridge → ConPort → Serena
- **Conflict Resolution**: Authoritative systems always win (Leantime for status, ConPort for decisions)

## 🎯 Mode-Aware Operation

**PLAN Mode**: Architecture, sprint planning, story breakdown

- Load PM plane modules + decision modules
- Focus on strategic thinking and synthesis
- Log decisions with rationale in ConPort

**ACT Mode**: Implementation, debugging, testing

- Load cognitive plane + execution modules
- Focus on concrete changes and linking artifacts
- Track progress and create deliverables

**Mode Detection**: Automatic based on activity type and user context

## 🚀 Integration Points

### ConPort Memory Management (AUTOMATIC)

```bash
# Workspace ID for ALL ConPort calls
WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Mandatory session initialization
mcp__conport__get_active_context --workspace_id "$WORKSPACE_ID"
mcp__conport__get_recent_activity_summary --workspace_id "$WORKSPACE_ID" --hours_ago 24
```

### Sprint Management (mem4sprint)

```bash
# Set mode and create sprint structure
mcp__conport__update_active_context --workspace_id "$WORKSPACE_ID" --patch_content '{"mode": "PLAN", "sprint_id": "S-2025.09"}'
mcp__conport__log_custom_data --workspace_id "$WORKSPACE_ID" --category "sprint_goals" --key "S-2025.09-G1" --value '{"type": "sprint_goal", "content": "Goal description", "sprint_id": "S-2025.09", "status": "planned"}'
```

### Authority Routing

- **Status Updates**: Route to Leantime only
- **Task Decomposition**: Route to Task-Master only
- **Decisions**: Log in ConPort only
- **Code Navigation**: Use Serena LSP only
- **Cross-Plane**: Through Integration Bridge only

### Worktree Management

**ADHD-Optimized Parallel Development**: Work on multiple branches without context-switching overhead

```bash
# List all worktrees with status
dopemux worktrees list

# Switch to an existing worktree
dopemux worktrees switch <branch-name>

# Clean up unused worktrees
dopemux worktrees cleanup [--force] [--dry-run]
```

**ADHD Benefits**:
- **Context Preservation**: Each worktree maintains independent state
- **No Mental Switching**: Physical directory separation = clear mental boundaries
- **Interrupt-Safe**: Pause one worktree, switch to another without losing progress
- **Main Protection**: Built-in protection against direct work on main branch

## 📚 Detailed Information Locations

When you need comprehensive details, refer to:

**PM Plane**: `.claude/modules/pm-plane/` (task-master.md, task-orchestrator.md, leantime.md)
**Cognitive Plane**: `.claude/modules/cognitive-plane/` (serena-lsp.md, conport-memory.md)
**Coordination**: `.claude/modules/coordination/` (integration-bridge.md, authority-matrix.md)
**Shared Systems**: `.claude/modules/shared/` (sprint.md, event-patterns.md, adhd-patterns.md)

## 🎖️ Success Metrics

**Target Improvements**: 77% token reduction ✅ | 85% ADHD task completion | Sub-2s context switching | Zero authority violations

---

**MCP Status**: Fully operational with ConPort auto-initialization
**Python Standards**: Type hints, pytest, PEP 8 with Black formatting, src/ layout
**ADHD Support**: Progressive disclosure, gentle guidance, visual progress indicators active
