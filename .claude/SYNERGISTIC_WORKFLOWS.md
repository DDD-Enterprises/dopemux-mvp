# Synergistic MCP Workflow Examples

**Purpose**: Real-world workflows showing how Serena-v2, Dope-Context, Context7, ConPort, and Zen MCPs work together synergistically for maximum productivity with minimal cognitive load.

## Core Principle: Tool Synergy

Each MCP server has a specialized role. **Synergy** means using them together so each tool's output enhances the next tool's effectiveness:

- **Dope-Context** finds WHAT exists (code, patterns, complexity)
- **Serena** shows WHERE and HOW (LSP navigation, references)
- **Context7** provides CORRECT patterns (official docs)
- **ConPort** remembers WHY (decisions, context, knowledge graph)
- **Zen** validates and analyzes (multi-model reasoning)

---

## Workflow 1: Feature Implementation

**Scenario**: Add OAuth authentication to existing Node.js app

### Step-by-Step with Synergy

```python
# 1. SEARCH: Find existing patterns (reduces reinvention)
mcp__dope-context__search_code(
    query="authentication middleware session management",
    profile="implementation"
)
# Returns: Existing auth patterns, complexity scores, similar code
# SYNERGY: Informs WHERE to integrate and WHAT patterns exist

# 2. DOCS: Get official patterns (ensures correctness)
mcp__context7__resolve-library-id(libraryName="passport")
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/jaredhanson/passport",
    topic="OAuth 2.0 strategy setup"
)
# Returns: Official Passport.js OAuth patterns
# SYNERGY: Validates patterns from search, provides missing details

# 3. NAVIGATE: Understand current implementation (reduces context switching)
mcp__serena-v2__find_symbol(query="login", symbol_type="function")
mcp__serena-v2__goto_definition(file_path="src/auth.js", line=42, column=10)
mcp__serena-v2__find_references(file_path="src/auth.js", line=42, column=10)
# Returns: Current login flow, all callers, integration points
# SYNERGY: Shows exactly WHERE OAuth fits in existing architecture

# 4. DECIDE: Log architectural decision (preserves context)
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Use Passport.js OAuth 2.0 for Google/GitHub auth",
    rationale="Existing app uses Passport local strategy, OAuth extends naturally",
    implementation_details="Add GoogleStrategy and GitHubStrategy, reuse session middleware",
    tags=["authentication", "oauth", "passport"]
)
# SYNERGY: Future developers understand WHY this approach

# 5. PLAN: Multi-step implementation (reduces overwhelm)
mcp__zen__planner(
    step="Plan OAuth integration: 1) Install deps 2) Configure strategies 3) Add routes 4) Test",
    step_number=1,
    total_steps=3,
    next_step_required=True,
    model="gpt-5-mini"
)
# SYNERGY: Zen breaks down complex task using context from search + docs

# 6. IMPLEMENT: Follow discovered patterns + official docs
# (Use patterns from Dope-Context search + Context7 docs)

# 7. TRACK: Log progress (ADHD context preservation)
mcp__conport__log_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    status="IN_PROGRESS",
    description="OAuth Google/GitHub authentication with Passport.js",
    linked_item_type="decision",
    linked_item_id="decision_id_from_step_4"
)
# SYNERGY: Links task to decision for full context chain

# 8. REVIEW: Security audit (catches issues early)
mcp__zen__codereview(
    step="Security review of OAuth implementation",
    relevant_files=["/Users/hue/code/dopemux-mvp/src/auth/oauth.js"],
    review_type="security",
    focus_on="OAuth token handling, session security, CSRF protection",
    findings="Implemented OAuth flow with Passport strategies",
    step_number=1,
    total_steps=2,
    next_step_required=True,
    model="gpt-5-codex"
)
# SYNERGY: Reviews code informed by all previous context
```

### ADHD Benefits
- ✅ **Search-first** eliminates "where do I start?" paralysis
- ✅ **Official docs** reduce decision fatigue and guesswork
- ✅ **LSP navigation** minimizes context switching time
- ✅ **Decision logging** removes memory burden
- ✅ **Automated review** reduces anxiety about mistakes
- ✅ **Progress tracking** provides accomplishment dopamine

---

## Workflow 2: Debugging Production Issue

**Scenario**: API endpoint returns 500 errors intermittently

### Step-by-Step with Synergy

```python
# 1. SEARCH: Find error handling patterns
mcp__dope-context__search_code(
    query="error handling middleware try catch",
    profile="debugging"
)
# SYNERGY: Finds HOW errors are currently handled

# 2. NAVIGATE: Jump to error source from stack trace
mcp__serena-v2__find_symbol(query="handleApiError", symbol_type="function")
mcp__serena-v2__find_references(file_path="src/middleware/errors.js", line=15, column=8)
# SYNERGY: Shows WHERE error occurs and WHO calls it

# 3. INVESTIGATE: Systematic root cause analysis
mcp__zen__debug(
    step="Investigate intermittent 500 errors in /api/users endpoint",
    hypothesis="Race condition in database connection pool",
    findings="Error occurs under high load, connection pool exhausted",
    confidence="medium",
    files_checked=["src/api/users.js", "src/db/pool.js"],
    relevant_files=["src/db/pool.js", "src/middleware/errors.js"],
    step_number=1,
    total_steps=3,
    next_step_required=True,
    model="gemini-2.5-pro"
)
# SYNERGY: Uses context from search + navigation for investigation

# 4. SEARCH: Find connection pool patterns
mcp__dope-context__search_code(
    query="database connection pool configuration",
    profile="implementation"
)
# SYNERGY: Finds existing pool config to understand settings

# 5. DOCS: Check official recommendations
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/pg-pool/pg-pool",
    topic="connection pool sizing best practices"
)
# SYNERGY: Official guidance for pool configuration

# 6. LOG: Document root cause and fix
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Increase DB connection pool size from 10 to 50 connections",
    rationale="500 errors caused by pool exhaustion under load (100+ concurrent requests)",
    implementation_details="Update pool config: {max: 50, idleTimeoutMillis: 30000}",
    tags=["bugfix", "database", "performance", "production"]
)
# SYNERGY: Future debugging knows exactly WHY this was changed

# 7. TRACK: Bug fix progress
mcp__conport__update_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    progress_id=previous_task_id,
    status="DONE"
)
```

### ADHD Benefits
- ✅ **Systematic debugging** prevents panic and random changes
- ✅ **Evidence-based** reduces "try random things" frustration
- ✅ **Context preservation** aids interruption recovery
- ✅ **Decision logging** prevents repeat bugs

---

## Workflow 3: Refactoring High-Complexity Code

**Scenario**: Code complexity score > 0.7, needs refactoring

### Step-by-Step with Synergy

```python
# 1. SEARCH: Find high-complexity code
mcp__dope-context__search_code(
    query="complex business logic calculations",
    profile="exploration"
)
# Returns: Functions with complexity scores, ranked
# SYNERGY: Dope-Context highlights WHAT needs refactoring (complexity > 0.6)

# 2. NAVIGATE: Understand complex function
mcp__serena-v2__get_context(
    file_path="src/business/pricing.js",
    line=150,
    context_lines=20,
    include_complexity=True
)
# Returns: Function with surrounding context + complexity score
# SYNERGY: Shows full context for understanding

# 3. ANALYZE: Get refactoring suggestions
mcp__zen__thinkdeep(
    step="Analyze calculateDiscount() function complexity and suggest refactoring",
    step_number=1,
    total_steps=2,
    next_step_required=True,
    findings="Function has 8 nested conditions, 150 lines, complexity 0.82",
    confidence="high",
    model="gpt-5-codex"
)
# SYNERGY: Uses complexity data for focused analysis

# 4. SEARCH: Find similar refactorings
mcp__dope-context__search_code(
    query="strategy pattern discount calculation",
    profile="implementation"
)
# SYNERGY: Finds existing patterns to follow

# 5. DOCS: Verify pattern correctness
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/facebook/react",
    topic="strategy pattern implementation"
)

# 6. REFACTOR: Apply strategy pattern (reduces complexity 0.82 → 0.35)

# 7. LOG: Document refactoring decision
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Refactor calculateDiscount using strategy pattern",
    rationale="Complexity 0.82 → 0.35, improved testability and maintainability",
    implementation_details="Extract 8 discount strategies into separate classes",
    tags=["refactoring", "complexity-reduction", "design-pattern"]
)

# 8. REVIEW: Validate refactoring
mcp__zen__codereview(
    step="Review refactored pricing module for quality and maintainability",
    relevant_files=["/Users/hue/code/dopemux-mvp/src/business/pricing.js"],
    review_type="full",
    findings="Reduced complexity from 0.82 to 0.35 using strategy pattern",
    step_number=1,
    total_steps=2,
    next_step_required=True,
    model="gpt-5-codex"
)
```

### ADHD Benefits
- ✅ **Complexity scoring** removes guesswork about refactoring priority
- ✅ **Systematic approach** reduces anxiety about breaking things
- ✅ **Pattern discovery** reduces "how should I do this?" decision fatigue

---

## Workflow 4: Learning New Codebase

**Scenario**: Onboarding to unfamiliar project

### Step-by-Step with Synergy

```python
# 1. DOCS: Read project documentation
mcp__dope-context__docs_search(
    query="architecture overview getting started",
    filter_doc_type="md"
)
# Returns: README, architecture docs, ADRs
# SYNERGY: Start with high-level understanding

# 2. SEARCH: Find entry points
mcp__dope-context__search_code(
    query="main application entry point server start",
    profile="exploration"
)
# SYNERGY: Identifies WHERE application starts

# 3. NAVIGATE: Follow execution flow
mcp__serena-v2__find_symbol(query="main", symbol_type="function")
mcp__serena-v2__goto_definition(...)
mcp__serena-v2__find_references(...)
# SYNERGY: Trace execution path from entry point

# 4. SEARCH: Find patterns by complexity (start simple)
mcp__dope-context__search_code(
    query="simple utility functions helpers",
    profile="exploration"
)
# SYNERGY: Complexity scores guide learning path (simple → complex)

# 5. UNIFIED SEARCH: Complete understanding
mcp__dope-context__search_all(
    query="authentication authorization flow",
    top_k=10
)
# Returns: Auth code + auth documentation together
# SYNERGY: Code + docs = complete picture

# 6. LOG: Capture learning insights
mcp__conport__log_system_pattern(
    workspace_id="/Users/hue/code/dopemux-mvp",
    name="Two-Plane Architecture Pattern",
    description="PM plane (Leantime) + Cognitive plane (Serena/ConPort) coordinated via DopeconBridge",
    tags=["architecture", "learning", "pattern"]
)

# 7. TRACK: Learning progress
mcp__conport__log_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    status="IN_PROGRESS",
    description="Learn Dopemux two-plane architecture and MCP integration"
)
```

### ADHD Benefits
- ✅ **Progressive complexity** prevents overwhelming (start simple)
- ✅ **Docs + code together** reduces context switching
- ✅ **Pattern capture** externalizes memory burden
- ✅ **Visual progress** provides motivation

---

## Workflow 5: Architecture Decision

**Scenario**: Choose between microservices vs monolith

### Step-by-Step with Synergy

```python
# 1. RESEARCH: Gather information
mcp__gpt-researcher__deep_research(
    query="microservices vs monolith for 10-person team SaaS product trade-offs"
)
# Returns: Comprehensive research from multiple sources
# SYNERGY: Broad context for decision

# 2. ANALYZE: Current codebase state
mcp__dope-context__search_code(
    query="service boundaries module dependencies",
    profile="exploration"
)
# SYNERGY: Understand current architecture

# 3. CONSENSUS: Multi-model decision
mcp__zen__consensus(
    step="Evaluate: Should we use microservices or monolith for our 10-person team?",
    models=[
        {"model": "gpt-5", "stance": "for"},      # Pro-microservices
        {"model": "gpt-5-mini", "stance": "against"},  # Pro-monolith
        {"model": "gemini-2.5-pro", "stance": "neutral"}  # Balanced view
    ],
    findings="Research shows team size and deployment complexity are key factors",
    step_number=1,
    total_steps=4,
    next_step_required=True
)
# SYNERGY: Multiple perspectives prevent bias

# 4. LOG: Document decision with full rationale
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Start with modular monolith, extract services later if needed",
    rationale="Team of 10 lacks DevOps capacity for microservices. Modular design enables future extraction.",
    implementation_details="Use clear module boundaries, interface-based communication, separate databases per module",
    tags=["architecture", "consensus", "team-size", "pragmatic"]
)

# 5. LINK: Connect to research
mcp__conport__link_conport_items(
    workspace_id="/Users/hue/code/dopemux-mvp",
    source_item_type="decision",
    source_item_id="architecture_decision_id",
    target_item_type="custom_data",
    target_item_id="research_findings",
    relationship_type="informed_by"
)
# SYNERGY: Full decision genealogy for future reference
```

### ADHD Benefits
- ✅ **Multi-source research** reduces "did I miss something?" anxiety
- ✅ **Multi-model consensus** prevents impulsive decisions
- ✅ **Full documentation** enables confident execution
- ✅ **Knowledge graph** preserves decision context forever

---

## Key Synergy Patterns

### Pattern 1: Search → Docs → Implement
**Why**: Existing code shows patterns, official docs validate correctness
**Tools**: Dope-Context → Context7 → Your editor
**Benefit**: Reduces both reinvention AND errors

### Pattern 2: Navigate → Analyze → Refactor
**Why**: LSP shows structure, Zen suggests improvements
**Tools**: Serena → Zen thinkdeep/codereview → Edit
**Benefit**: Systematic improvement vs random changes

### Pattern 3: Research → Decide → Log
**Why**: Information gathering → multi-model decision → context preservation
**Tools**: GPT-Researcher/Exa → Zen consensus → ConPort
**Benefit**: Evidence-based decisions with full auditability

### Pattern 4: Implement → Track → Review
**Why**: Build → monitor progress → validate quality
**Tools**: Code → ConPort progress → Zen codereview
**Benefit**: Completion visibility + quality assurance

---

## Anti-Patterns to Avoid

### ❌ Implementing Without Searching
**Problem**: Reinvents wheels, misses existing patterns
**Solution**: ALWAYS `search_code()` before implementing

### ❌ Using Frameworks Without Docs
**Problem**: Outdated patterns, incorrect usage
**Solution**: ALWAYS `get-library-docs()` before using APIs

### ❌ Making Decisions Without Logging
**Problem**: Future confusion, repeated discussions
**Solution**: ALWAYS `log_decision()` for architectural choices

### ❌ Sequential Tool Calls
**Problem**: Wastes time, increases cognitive load
**Solution**: Parallel MCP calls when independent

### ❌ Skipping Code Review
**Problem**: Security issues, bugs in production
**Solution**: ALWAYS `zen__codereview()` for critical code

---

## Quick Reference: Tool Selection

| Task | Primary Tool | Secondary | Tertiary |
|------|-------------|-----------|----------|
| Find code patterns | Dope-Context search | Serena find_symbol | - |
| Navigate to definition | Serena goto_definition | - | - |
| Get official docs | Context7 | - | - |
| Log decisions | ConPort log_decision | - | - |
| Track tasks | ConPort log_progress | - | - |
| Debug issues | Zen debug | Dope-Context search | Serena navigate |
| Review code | Zen codereview | - | - |
| Plan complex work | Zen planner | - | - |
| Make decisions | Zen consensus | GPT-Researcher | ConPort log |
| Learn codebase | Dope-Context search_all | Serena | ConPort patterns |

---

**Remember**: Each tool makes the next tool more effective. Use them together, not in isolation.
