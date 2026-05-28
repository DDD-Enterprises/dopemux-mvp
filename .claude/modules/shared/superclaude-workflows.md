# SuperClaude + Dopemux Workflow Integration

**Purpose**: Integration patterns for using SuperClaude commands with Dopemux's enhanced MCP stack
**Audience**: Developers using Dopemux with SuperClaude framework
**Last Updated**: 2025-10-03 (Decision #142-144)

---

## Overview

SuperClaude provides 25 slash commands, 7 behavioral modes, and 16 specialized agents. Dopemux enhances these with superior MCPs (Zen multi-model reasoning, ConPort knowledge graph, Serena v2 code intelligence, Exa neural search, GPT-Researcher deep research).

**Integration Philosophy**: Use SuperClaude's command framework with Dopemux's advanced tooling for ADHD-optimized development workflows.

---

## Primary Development Flow

###  Standard Development Session

```
1. Session Start
   /sc:load                          # Restore from ConPort active_context
   └─> ConPort: get_active_context   # Retrieves: current_focus, next_steps, session_notes

2. Task Selection
   ConPort query                     # Get TODO tasks with ADHD metadata
   └─> Filters: energy_level, complexity, cognitive_load

3. Code Navigation
   Serena LSP navigation             # Semantic code intelligence
   └─> Features: symbol search, complexity scoring, progressive disclosure

4. Implementation
   /sc:implement <feature>           # Coordinates: Context7 + Zen + Magic + Playwright
   └─> Context7: Framework patterns (ALWAYS FIRST)
   └─> Zen planner: Break down complex features
   └─> Magic: UI component generation
   └─> Playwright: Test generation

5. Quality Validation
   /sc:test                          # Run tests with Playwright
   Zen codereview                    # Multi-model review
   Zen precommit                     # Pre-commit validation

6. Session End
   /sc:save                          # Persist session state
   └─> ConPort: update_active_context
   ConPort log_decision              # Document architectural choices
   └─> Knowledge graph tracking
```

---

## ConPort + Serena + SuperClaude Integration

### Three-Layer Architecture

```
Layer 1: ConPort (Knowledge & Memory)
├─ Stores: Decisions, progress, patterns, relationships
├─ Provides: Context restoration, ADHD metadata, semantic search
└─ Tools: log_decision, log_progress, get_active_context

Layer 2: Serena (Code Intelligence)
├─ Provides: LSP navigation, semantic analysis, complexity scoring
├─ Caches: Navigation paths, frequently accessed code
└─ Tools: find_symbol, navigate, complexity analysis

Layer 3: SuperClaude (Coordination)
├─ Coordinates: Multi-agent collaboration, workflow orchestration
├─ Commands: 25 /sc: commands for different tasks
└─ Agents: 16 specialists (Frontend, Backend, Security, etc.)
```

### Data Flow

```
User Request
    │
    ├─> /sc:load ───────────> ConPort: Restore context
    │
    ├─> /sc:implement ──────> Context7: Get framework patterns
    │                    └──> Zen planner: Break down feature
    │                    └──> Serena: Navigate existing code
    │                    └──> Magic: Generate UI components
    │
    ├─> Implementation ─────> Code changes
    │
    ├─> /sc:test ───────────> Playwright: Run tests
    │                    └──> Zen codereview: Validate quality
    │
    └─> /sc:save ───────────> ConPort: Persist session
                         └──> ConPort: Log decisions
```

---

## Command Selection Guide

### /sc: Commands (SuperClaude Standard)

**When to use /sc: commands**:
- Standard workflows (implement, test, build)
- Multi-agent coordination needed
- Following established patterns
- Quick, focused tasks

**Available Commands** (25 total):

**Analysis & Planning**:
- `/sc:analyze` - Code analysis (uses Zen thinkdeep)
- `/sc:brainstorm` - Requirements discovery (uses Zen consensus)
- `/sc:estimate` - Development estimation
- `/sc:design` - Architecture design

**Implementation**:
- `/sc:implement` - Feature development
- `/sc:improve` - Code quality enhancement
- `/sc:cleanup` - Dead code removal
- `/sc:build` - Build and packaging

**Research & Documentation**:
- `/sc:research` - Deep research (Exa + GPT-Researcher + Zen)
- `/sc:document` - Documentation generation
- `/sc:explain` - Educational explanations

**Session Management**:
- `/sc:load` - Restore context (from ConPort)
- `/sc:save` - Persist session (to ConPort)
- `/sc:reflect` - Task validation (with Serena)

**Workflow**:
- `/sc:workflow` - PRD to implementation (uses Zen planner)
- `/sc:task` - Complex task management

[Full command reference](.claude/commands/sc/)

### /dx: Commands (Dopemux Custom)

**When to use /dx: commands**:
- Dopemux-specific workflows
- Direct MCP integration needed
- ADHD-optimized sessions
- Custom automation

**Planned Commands**:

- `/dx:prd-parse` - PRD decomposition with Zen planner + ConPort import
- `/dx:implement` - ADHD-optimized 25min sessions with auto-save
- `/dx:analyze` - Direct Zen thinkdeep integration
- `/dx:review` - Direct Zen codereview with multi-model validation
- `/dx:session` - Focus session management with timers
- `/dx:switch-role` - MetaMCP role switching (QUICKFIX, ACT, PLAN, RESEARCH, ALL)

**Status**: Specifications complete, implementation pending

---

## MCP Selection by Task Type

### Research Tasks

**Simple Lookup** (< 5 seconds):
```
Use: Exa neural search
Example: "Find React hooks documentation"
Command: /sc:research (uses Exa by default)
```

**Complex Investigation** (5+ minutes):
```
Use: GPT-Researcher (4-engine coordination)
Example: "Compare PostgreSQL vs MongoDB for e-commerce"
Command: /sc:research --deep
Tools: GPT-Researcher deep_research
```

### Planning Tasks

**Simple Breakdown** (linear steps):
```
Use: Zen planner
Example: "Break down authentication feature"
Command: /sc:workflow
```

**Complex Planning** (alternatives, branching):
```
Use: Zen planner with revision/branching
Example: "Migration strategy with multiple approaches"
Direct: zen/planner with is_branch_point
```

**Multi-Perspective Decision**:
```
Use: Zen consensus
Example: "Should we use microservices or monolith?"
Direct: zen/consensus with 3 models (for/against/neutral)
```

### Implementation Tasks

**Feature Development**:
```
Use: /sc:implement
Flow: Context7 (patterns) → Zen (planning) → Magic (UI) → Playwright (tests)
Example: "/sc:implement user profile component --framework react"
```

**Code Navigation**:
```
Use: Serena LSP
Tools: find_symbol, get_symbols_overview, find_referencing_symbols
Example: Navigate from API endpoint to database layer
```

**Code Quality**:
```
Use: /sc:improve + Zen codereview
Flow: Identify issues → Zen multi-model validation → Apply fixes
Example: "/sc:improve --focus performance"
```

### Debugging Tasks

**Systematic Investigation**:
```
Use: Zen debug
Flow: Hypothesis → Evidence gathering → Root cause → Fix validation
Example: "Why does memory usage grow unbounded?"
```

**Quick Troubleshooting**:
```
Use: /sc:troubleshoot
Flow: Error analysis → Serena navigation → Fix suggestion
Example: "/sc:troubleshoot authentication failing intermittently"
```

---

## ADHD Session Workflow

### 25-Minute Focus Session

```
Session Start (2 min)
├─ /sc:load                   # Restore from ConPort
├─ Review next_steps          # From active_context
├─ Check energy level         # Match task to current state
└─ Select optimal task        # Based on complexity + energy

Implementation (20 min)
├─ /sc:implement or /sc:fix   # Primary work
├─ Auto-save every 5 min      # Context preservation
├─ Progress tracking          # Update ConPort progress_entry
└─ Focus maintenance          # Minimize context switches

Session End (3 min)
├─ /sc:save                   # Persist to ConPort
├─ Log decisions              # ConPort log_decision
├─ Update progress            # Mark tasks complete
└─ Plan next session          # Set next_steps in active_context

Break (5 min)
└─ Mandatory after 25 min     # ADHD accommodation
```

### Hyperfocus Protection

```
Warning at 60 min
└─> "You've been coding for 60 minutes. Consider a break soon."

Mandatory at 90 min
└─> "90 minutes elapsed. Taking a break now to prevent burnout."
    ├─ /sc:save (forced)
    ├─ Session pause
    └─ 15-minute minimum break
```

### Context Switch Recovery

```
Interrupted During Work
├─ Auto-save triggered        # .dopemux/context.db updated
├─ Session snapshot created   # .dopemux/sessions/session-<id>.json
└─ ConPort context preserved  # active_context unchanged

Resume After Interruption
├─ /sc:load                   # Restore context
├─ Review session notes       # "You were working on X"
├─ Check open files           # Restore file positions
└─ Gentle re-orientation      # Clear next action
```

---

## Documentation Workflow

### Adding New Documentation

**Step 1: Determine Type**
```
Learning guide     → docs/01-tutorials/tutorial-<topic>.md
Task recipe        → docs/02-how-to/<verb>-<object>.md
API/CLI reference  → docs/03-reference/<component>-reference.md
Concept explanation → docs/04-explanation/<concept>.md
Decision record    → docs/90-adr/ADR-<NNNN>-<date>-<title>.md
Proposal           → docs/91-rfc/rfc-<YYYY>-<NNN>-<title>.md
```

**Step 2: Use Template**
```bash
# Copy appropriate template
cp docs/templates/adr-template.md docs/90-adr/ADR-0145-<title>.md
```

**Step 3: Add Frontmatter**
```yaml
---
id: unique-kebab-case-id
title: Human Readable Title
type: adr|rfc|how-to|explanation|reference
owner: '@github-handle'
last_review: '2025-10-03'
next_review: '2025-12-03'
status: active|draft|deprecated
tags: [relevant, tags]

# ADHD-specific (recommended)
cognitive_load: low|medium|high
attention_state: focused|scattered|any
reading_time: <N>
---
```

**Step 4: Write Content**
Follow [documentation-standards.md](../../03-reference/documentation-standards.md):
- Progressive disclosure (essential → details)
- Visual structure (tables, bullets, diagrams)
- Maximum 3 options per decision
- Clear next actions

**Step 5: Cross-Reference**
- Link from feature hubs (docs/features.yaml)
- Update _manifest.yaml if major doc
- Reference from relevant module docs

### Updating Existing Documentation

**Before Making Changes**:
1. Check if doc is active or archived
2. Review current frontmatter and status
3. Use git blame to understand context
4. Check for cross-references (grep)

**Making Updates**:
1. Update `last_review` date in frontmatter
2. Preserve ADHD accommodations
3. Maintain consistent voice and structure
4. Update cross-references if paths change

**After Changes**:
1. Validate frontmatter with scripts/docs/check_frontmatter.sh
2. Check cross-references still work
3. Update _manifest.yaml if metadata changed
4. Log significant changes in ConPort (if architectural)

---

## Script Management

### Script Organization

**Categories**:
```
scripts/
├── backup/        Backup and restore operations
├── docs/          Documentation generation and validation
├── memory/        Memory system utilities
├── mcp/           MCP server management
└── ui/            Dashboard and UI scripts
```

### Script Standards

**Header Template**:
```bash
#!/usr/bin/env bash
#
# Script: <name>.sh
# Purpose: One-line description
#
# Usage:
#   ./<name>.sh [options]
#
# ADHD Note: Complexity <low|medium|high>
# Status: production | experimental | TEMP
# Dependencies: [list required tools]
#

# TEMP: Remove after <reason> (if temporary)
```

**Production Scripts**:
- Full documentation in header
- Error handling and validation
- Progress indicators for long operations
- ADHD-friendly output (color, emojis, progress bars)

**Temporary Scripts**:
- Tag with `# TEMP: Remove after <reason>`
- Minimal documentation
- Move to scripts/deprecated/ when obsolete

### Script Cleanup Process

```bash
# Tag temporary scripts
grep -r "TEMP:" scripts/

# Review quarterly
scripts/audit_temporary_scripts.sh

# Archive when done
mv scripts/<temp>.sh scripts/deprecated/
# Add explanation in deprecation comment
```

---

## ConPort Workflow Patterns

### Decision Logging

**When to Log Decisions**:
- Architectural choices
- Technology selections
- Process changes
- Major refactorings
- ADHD accommodation additions

**How to Log**:
```bash
# Via ConPort MCP
conport/log_decision:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  summary: "One-line decision description"
  rationale: "Why this decision was made (detailed)"
  implementation_details: "How it will be implemented"
  tags: ["category", "feature", "adhd"]
```

**Then Create ADR**:
```bash
# Link decision to formal documentation
1. Create ADR in docs/90-adr/
2. Reference ConPort decision ID
3. Link from feature hub
```

### Progress Tracking

**Task Hierarchy**:
```
Parent Task (Epic)
├─ Subtask 1 (parent_id set)
├─ Subtask 2 (parent_id set)
└─ Subtask 3 (parent_id set)
```

**With ADHD Metadata**:
```bash
conport/log_progress:
  status: "TODO"
  description: "Implement user authentication"

# Add metadata via custom_data:
conport/log_custom_data:
  category: "task_metadata"
  key: "task-<id>"
  value: {
    complexity_score: 0.6,
    energy_required: "medium",
    cognitive_load: 0.5,
    estimated_minutes: 45,
    files_affected: ["auth.py", "session.py"]
  }
```

### Knowledge Graph

**Creating Relationships**:
```bash
# Link decision to implementation task
conport/link_conport_items:
  source_item_type: "decision"
  source_item_id: "144"
  target_item_type: "progress_entry"
  target_item_id: "225"
  relationship_type: "implements"
```

**Relationship Types**:
- `builds_upon` - Decision builds on previous
- `validates` - Confirms or tests another item
- `extends` - Enhances existing decision
- `implements` - Task implements decision
- `depends_on` - Dependency relationship
- `supersedes` - Replaces previous decision

---

## Serena Workflow Patterns

### Code Navigation

**Finding Code**:
```bash
# Symbol search
serena/find_symbol:
  name_path: "authenticate"
  include_body: false

# Get file overview
serena/get_symbols_overview:
  relative_path: "src/auth/authentication.py"

# Find all callers
serena/find_referencing_symbols:
  name_path: "authenticate"
  relative_path: "src/auth/authentication.py"
```

**ADHD Navigation**:
- Max 10 results per query (prevents overwhelm)
- 3-level depth limit (prevents rabbit holes)
- Progressive disclosure (signature → params → implementation)
- Complexity scoring (0.0-1.0 to estimate cognitive load)

### Complexity-Aware Development

```
Check complexity before reading
└─> complexity < 0.3: Read immediately
└─> complexity 0.3-0.6: Schedule focused time
└─> complexity > 0.6: Break into smaller pieces

Example:
serena/find_symbol returns: complexity_score: 0.7
└─> "High complexity. Consider reviewing in focused session."
```

---

## Zen MCP Workflow Patterns

### Multi-Model Reasoning

**Deep Analysis**:
```
Use: zen/thinkdeep
When: Complex problem investigation
Flow:
  1. State hypothesis
  2. Gather evidence (files_checked)
  3. Test hypothesis (findings)
  4. Adjust or confirm (confidence)
  5. Expert validation (optional)

Example:
Step 1: "Hypothesis: Memory leak in event listeners"
Step 2: Check component lifecycle code
Step 3: Find missing cleanup in useEffect
Step 4: Confidence: high
Step 5: Expert confirms root cause
```

**Interactive Planning**:
```
Use: zen/planner
When: Breaking down complex features
Flow:
  1. Describe task
  2. Get phase breakdown
  3. Revise if needed (is_revision: true)
  4. Explore alternatives (branch_from_step)
  5. Finalize plan

Example:
Step 1: "Implement OAuth authentication"
Step 2: Phases: Setup → Token flow → Refresh logic → Testing
Step 3: Revise: Add security audit phase
Step 4: Branch: Compare JWT vs opaque tokens
Step 5: Choose JWT, document in ConPort
```

**Consensus Building**:
```
Use: zen/consensus
When: Important architectural decisions
Flow:
  1. State question
  2. Consult model 1 (for stance)
  3. Consult model 2 (against stance)
  4. Consult model 3 (neutral)
  5. Synthesize recommendation

Example:
Question: "Use microservices or monolith?"
Models: o3-mini (for), gpt-5-mini (against), o3-mini (neutral)
Result: Balanced recommendation with trade-offs
Log: ConPort decision with consensus score
```

---

## Agent Activation Patterns

### Automatic Agent Selection

**SuperClaude automatically activates agents based on**:

**Command Context**:
- `/sc:implement` → Frontend + Backend + Security
- `/sc:troubleshoot` → Root Cause Analyst
- `/sc:research` → Deep Research Agent
- `/sc:document` → Technical Writer

**File Type**:
- `*.py` files → Python Expert
- `*.tsx` files → Frontend Architect
- `Dockerfile` → DevOps Architect

**Keywords**:
- "security audit" → Security Engineer
- "performance" → Performance Engineer
- "refactor" → Refactoring Expert

### Multi-Agent Coordination

**Complex Features** (Multiple Agents):
```
/sc:implement payment system
├─> System Architect: Overall design
├─> Backend Architect: API and database
├─> Frontend Architect: UI components
├─> Security Engineer: PCI compliance
└─> QA Engineer: Test strategy
```

**Agent Output**:
Each agent provides:
- Domain-specific analysis
- Recommendations aligned with expertise
- Code examples following best practices
- Validation criteria

---

## MCP Documentation Reference

**Quick MCP Selection**:

| Task Type | Primary MCP | Alternative | Reference |
|-----------|-------------|-------------|-----------|
| Multi-model reasoning | Zen | - | [MCP_Zen.md](~/.claude/MCP_Zen.md) |
| Knowledge graph | ConPort | - | [MCP_ConPort.md](~/.claude/MCP_ConPort.md) |
| Code navigation | Serena | - | [MCP_Serena.md](~/.claude/MCP_Serena.md) |
| Simple search | Exa | Context7 | [MCP_Exa.md](~/.claude/MCP_Exa.md) |
| Deep research | GPT-Researcher | Exa | [MCP_GPTResearcher.md](~/.claude/MCP_GPTResearcher.md) |
| Official docs | Context7 | Exa | SuperClaude default |
| UI generation | Magic | - | SuperClaude default |
| Testing | Playwright | - | SuperClaude default |
| Code transforms | Morphllm | - | SuperClaude default |

**Full MCP Documentation**: All @ imported via ~/.claude/CLAUDE.md

---

## Common Workflows

### Feature Implementation (Context7-First)

```
1. MANDATORY: Check Documentation
   Context7: get-library-docs for framework
   └─> ALWAYS query Context7 before writing any code

2. Plan Implementation
   /sc:workflow → Zen planner breakdown
   └─> Creates phased approach

3. Navigate Existing Code
   Serena: find similar patterns
   └─> Complexity scoring helps estimate effort

4. Implement
   /sc:implement with Context7 patterns
   └─> Frontend + Backend agents coordinate
   └─> Magic generates UI components

5. Test
   /sc:test → Playwright automated testing
   └─> Validates against requirements

6. Review
   Zen codereview → Multi-model validation
   └─> Quality, security, performance check

7. Document
   Log decision in ConPort
   Update relevant docs
   Create ADR if architectural
```

### Bug Investigation

```
1. Reproduce
   Capture error details, logs, context

2. Systematic Investigation
   Zen debug → Hypothesis-driven analysis
   └─> Gather evidence from code/logs
   └─> Test hypotheses systematically

3. Navigate to Root Cause
   Serena: find_symbol from stack trace
   └─> Navigate to implementation
   └─> Check callers and dependencies

4. Validate Fix
   Implement solution
   Zen codereview → Verify correctness
   Add regression test

5. Document
   ConPort log_decision (why bug occurred)
   Update relevant documentation
```

### Research & Decision Making

```
1. Initial Research
   Exa: Quick search for overview
   └─> Get recent articles, official docs

2. Deep Investigation (if needed)
   /sc:research → GPT-Researcher
   └─> Multi-engine synthesis
   └─> Comprehensive report with citations

3. Multi-Perspective Analysis
   Zen consensus → Compare approaches
   └─> Get for/against/neutral perspectives
   └─> Balanced recommendation

4. Document Decision
   ConPort log_decision
   └─> Rationale + implementation details
   Create ADR in docs/90-adr/
   └─> Link to ConPort decision ID
```

---

## Integration Points

### SuperClaude → ConPort

**Session Commands**:
- `/sc:load` calls `conport/get_active_context`
- `/sc:save` calls `conport/update_active_context`
- `/sc:reflect` queries `conport/get_progress`

**Decision Workflow**:
- Major /sc: decisions logged via `conport/log_decision`
- Knowledge graph tracks decision genealogy
- Semantic search enables context recovery

### SuperClaude → Serena

**Code Commands**:
- `/sc:implement` uses `serena/find_symbol` for navigation
- `/sc:improve` uses `serena` complexity analysis
- `/sc:reflect` validates with `serena` semantic analysis

**Navigation Flow**:
- Serena provides code context
- SuperClaude agents use context for implementation
- Changes tracked for learning patterns

### SuperClaude → Zen

**Reasoning Commands**:
- `/sc:analyze` uses `zen/thinkdeep`
- `/sc:workflow` uses `zen/planner`
- `/sc:brainstorm` uses `zen/consensus`
- `/sc:troubleshoot` uses `zen/debug`

**Quality Commands**:
- Implicit `zen/codereview` on major changes
- `zen/precommit` before git commits
- `zen/challenge` on user disagreements

---

## Best Practices

### ADHD Accommodations

**Always Apply**:
- Save frequently (every 5 min during work)
- Break complex tasks into 25-min chunks
- Use visual progress indicators
- Provide clear next actions
- Limit options to maximum 3
- Progressive disclosure (essential first)

**Session Management**:
- Start with /sc:load (restore context)
- End with /sc:save (preserve progress)
- Log decisions in ConPort
- Track energy levels and breaks

**Task Selection**:
- Match complexity to current energy
- Avoid high-complexity when scattered
- Use ConPort ADHD metadata for smart routing

### Quality Standards

**Before Committing Code**:
1. Run tests (/sc:test)
2. Code review (zen/codereview)
3. Pre-commit validation (zen/precommit)
4. Update documentation
5. Log architectural decisions

**Before Merging**:
1. All tests passing
2. Documentation updated
3. ADR created if architectural
4. ConPort decision logged
5. Cross-references validated

---

## Troubleshooting

### Command Not Working

**Check**: Is the MCP operational?
```bash
# View MCP status
claude mcp list

# Test specific MCP
# Try simple operation
```

**SuperClaude Command Issues**:
```bash
# Verify installation
SuperClaude --version

# Check component installation
cat ~/.claude/.superclaude-metadata.json

# Validate command file exists
ls ~/.claude/commands/sc/<command>.md
```

### Context Not Restoring

**Check ConPort**:
```bash
# Verify active context
conport/get_active_context

# Check recent activity
conport/get_recent_activity_summary --hours_ago 24
```

**Check Dopemux Context**:
```bash
# List sessions
ls .dopemux/sessions/

# Check database
sqlite3 .dopemux/context.db "SELECT * FROM session_metadata ORDER BY last_active DESC LIMIT 5"
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│          Dopemux + SuperClaude Quick Reference          │
├─────────────────────────────────────────────────────────┤
│ Session Start:      /sc:load                            │
│ Feature Impl:       /sc:implement <feature>             │
│ Deep Research:      /sc:research <question>             │
│ Code Analysis:      /sc:analyze --focus <area>          │
│ Bug Fix:            /sc:troubleshoot <issue>            │
│ Session End:        /sc:save                            │
│                                                          │
│ Log Decision:       conport/log_decision                │
│ Track Progress:     conport/log_progress                │
│ Navigate Code:      serena/find_symbol                  │
│ Multi-Model:        zen/consensus or zen/thinkdeep      │
│                                                          │
│ Break Reminder:     Every 25 minutes                    │
│ Auto-Save:          Every 5 minutes during work         │
│ Hyperfocus Warn:    At 60 minutes                       │
│ Mandatory Break:    At 90 minutes                       │
└─────────────────────────────────────────────────────────┘
```

---

**For MCP details**, see `~/.claude/MCP_*.md` (auto-imported)
**For command details**, see `.claude/commands/sc/<command>.md`
**For agent details**, see `.claude/agents/<agent>.md`
