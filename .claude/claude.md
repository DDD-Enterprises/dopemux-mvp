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
- **Research → Analysis Pipeline**: GPT-Researcher → Zen consensus → ConPort decision

### 🔬 Deep Research - GPT-Researcher + Ultrathink

**Use for comprehensive research** requiring synthesis across 10-20 sources (5-10 minutes):

```python
# Comprehensive multi-source research
research = mcp__gpt-researcher__deep_research(
    query="PostgreSQL connection pooling best practices for Python microservices"
)
# Returns: research_id, synthesized findings, 10-20 sources with citations

# Zen ultrathink consensus on findings
decision = mcp__zen__consensus(
    step=f"Evaluate: {research['context'][:500]}...",
    models=[
        {"model": "gpt-5-pro", "stance": "for"},
        {"model": "o3-pro", "stance": "against"}
    ],
    findings="Research-backed analysis",
    step_number=1, total_steps=3, next_step_required=True
)

# Log research-backed decision
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Use PgBouncer for connection pooling",
    rationale=f"Research: {research['research_id']}, Consensus: {decision}",
    tags=["research-backed", "postgresql", "ultrathink-validated"]
)
```

**When**: Complex questions, need synthesis, 5-10 min acceptable
**vs Exa**: GPT-Researcher = depth/synthesis (10 min), Exa = speed (< 5 sec)

### ⚡ Quick Search - Exa Neural + Context7

**Use for fast searches** (< 5 seconds):

```python
# Fast neural search
community = mcp__exa__search(
    query="Next.js 14 app router best practices",
    num_results=5, search_type="neural"
)

# Official docs
official = mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/vercel/next.js",
    topic="app router data fetching"
)
# Compare community + official = complete picture
```

**When**: Quick lookups, documentation, recent updates, < 5 sec
**vs GPT-Researcher**: Exa = breadth/speed, GPT-Researcher = depth/synthesis

### 🖥️ Desktop Automation - Desktop-Commander

**Use for visual context, window management**:

```python
# Screenshot + decision logging
mcp__desktop-commander__screenshot(filename="/tmp/arch.png")
mcp__conport__log_decision(summary="Architecture", implementation_details="Diagram: /tmp/arch.png")

# Auto-focus after navigation
mcp__dope-context__search_code(query="auth")
mcp__serena-v2__goto_definition(file_path="src/auth.py", line=42, column=10)
mcp__desktop-commander__focus_window(title="VS Code")
```

**See**: `~/.claude/MCP_DesktopCommander.md` for complete docs
**ADHD**: Visual memory aids, auto window switching, < 2s interrupt recovery

## 🔄 Synergistic Workflows - ADHD-Optimized Multi-MCP

### Workflow: Feature Implementation with Ultrathink

**Research Phase** (10 min):
```python
# Quick overview
exa_results = mcp__exa__search(query="OAuth PKCE examples", num_results=5)

# Deep research
research = mcp__gpt-researcher__deep_research(
    query="OAuth 2.0 PKCE security best practices and patterns"
)

# Official docs
docs = mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/oauth/oauth2", topic="PKCE flow"
)

# Ultrathink consensus
consensus = mcp__zen__consensus(
    step=f"Evaluate approach: Research={research['context'][:200]}...",
    models=[
        {"model": "gpt-5-pro", "stance": "for", "stance_prompt": "Security focus"},
        {"model": "o3-pro", "stance": "against", "stance_prompt": "Complexity focus"}
    ],
    step_number=1, total_steps=3, next_step_required=True
)
```

**Discovery Phase** (5 min):
```python
# Find existing patterns
code = mcp__dope-context__search_code(
    query="authentication flow implementations",
    profile="implementation", top_k=10
)

# Navigate to code
mcp__serena-v2__goto_definition(
    file_path=code[0]["file_path"],
    line=code[0]["start_line"], column=1
)

# Auto-focus editor
mcp__desktop-commander__focus_window(title="VS Code")
```

**Implementation Phase** (25 min):
```python
# Log decision with visual evidence
mcp__desktop-commander__screenshot(filename="/tmp/oauth-flow.png")
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Implement OAuth PKCE",
    rationale=f"Research: {research['research_id']}, Consensus validated",
    implementation_details="Diagram: /tmp/oauth-flow.png",
    tags=["oauth", "research-backed", "ultrathink-validated"]
)

# Track progress
mcp__conport__log_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    status="IN_PROGRESS",
    description="Implement OAuth PKCE flow"
)

# Auto-save every 5 min
mcp__conport__update_active_context(
    workspace_id="/Users/hue/code/dopemux-mvp",
    patch_content={"current_focus": "OAuth PKCE", "progress": "70%"}
)
```

**Validation Phase** (10 min):
```python
# Ultrathink code review
review = mcp__zen__codereview(
    step="Security audit of OAuth PKCE",
    relevant_files=["/Users/hue/code/dopemux-mvp/src/auth/oauth.py"],
    review_type="security",
    model="gpt-5-pro"  # Ultrathink for security
)

# Mark complete
mcp__desktop-commander__screenshot(filename="/tmp/tests-passing.png")
mcp__conport__update_progress(workspace_id="/Users/hue/code/dopemux-mvp", progress_id=task_id, status="DONE")
```

**ADHD Benefits**: Clear phases, visual progress, context preservation, research-backed confidence
**Total Time**: ~50 min (vs 3-4 hours without MCP coordination)

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

### F001 Enhanced: Untracked Work Detection

**ADHD-Critical Feature**: Prevents false-starts and encourages task completion

**MCP Tool**: `mcp__serena-v2__detect_untracked_work_enhanced`

**Purpose**: Detects uncommitted work with no ConPort tracking and provides:
1. **E1 - False-Starts Dashboard**: "Sure you want to make it 48?" gentle awareness
2. **E2 - Design-First Prompting**: ADR/RFC suggestions for substantial features (5+ files, 3+ dirs)
3. **E3 - Abandoned Work Revival**: Suggests resuming relevant abandoned work (relevance scoring)
4. **E4 - Prioritization Context**: Shows current commitments + overcommitment risk

**Usage**:
```python
# Session start detection
result = mcp__serena-v2__detect_untracked_work_enhanced(
    session_number=1,     # 1=first, 2=second, 3+=established
    show_details=False    # Set true for confidence breakdown
)

# Parse results
if result["status"] == "untracked_work_detected":
    # E1: Always shown (false-starts dashboard)
    dashboard = result["false_starts_dashboard"]["message"]

    # E2: If 5+ files OR 3+ dirs OR architecture keywords
    if "design_first_recommendation" in result:
        design_prompt = result["design_first_recommendation"]["message"]

    # E3: If relevant abandoned work found (0.3+ relevance)
    if "revival_suggestions" in result:
        revival = result["revival_suggestions"]["message"]

    # E4: If active ConPort tasks exist
    if "prioritization_context" in result:
        priority = result["prioritization_context"]["message"]
```

**ADHD Benefits**:
- **Reduces false-starts**: Dashboard creates awareness of unfinished work
- **Encourages design**: Prompts for ADR/RFC before diving into complex features
- **Finish vs. start**: Revival suggestions nudge toward completing existing work
- **Overcommitment prevention**: Priority context shows current task load

**Research-Validated**:
- 2025 Cleveland Clinic: Task completion is primary ADHD management paradigm
- 2024 CBT Meta-Analysis: External reminders + task breakdown = 87% improvement
- 2024 Digital Interventions: Self-guided systems effective (g = −0.32)

**Documentation**:
- User Guide: `services/serena/v2/docs/F001_ENHANCED_USER_GUIDE.md`
- Usage Examples: `services/serena/v2/docs/F001_USAGE_EXAMPLES.md`
- Test Results: `services/serena/v2/F001_TEST_RESULTS.md`

**See**: Decision #144 for implementation rationale

---

### Worktree Management

**ADHD-Optimized Parallel Development**: Work on multiple branches without context-switching overhead

**REQUIRED: Shell Integration Setup (One-Time)**
```bash
# Install shell integration (required for worktree switching)
dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc
# OR for zsh:
dopemux shell-setup zsh >> ~/.zshrc && source ~/.zshrc
```

**Usage**:
```bash
# List all worktrees with status
dopemux worktrees list
# OR: dwtls (after shell integration)

# Switch to worktree (REQUIRES shell integration)
dwt <branch-name>        # Fuzzy matching supported
dwt ui                   # Matches "ui-build"
dwt feature              # Matches "feature/test-worktree-isolation"

# Show current worktree
dopemux worktrees current
# OR: dwtcur

# Clean up unused worktrees
dopemux worktrees cleanup [--force] [--dry-run]
```

**Why Shell Integration?**
Python subprocesses cannot change the parent shell's directory (POSIX limitation). The `dwt` command is a shell function that calls `dopemux worktrees switch-path` and executes `cd` in your shell's context.

**ADHD Benefits**:
- **Context Preservation**: Each worktree maintains independent state
- **No Mental Switching**: Physical directory separation = clear mental boundaries
- **Interrupt-Safe**: Pause one worktree, switch to another without losing progress
- **Main Protection**: Built-in protection against direct work on main branch
- **Simple Commands**: 3-letter `dwt` alias reduces cognitive load
- **Fuzzy Matching**: No need to remember exact branch names

**See**: `docs/WORKTREE_SWITCHING_GUIDE.md` for complete installation and troubleshooting

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
