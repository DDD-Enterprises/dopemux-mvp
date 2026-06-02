# SuperClaude Integration Module

**Module Version**: 2.0.0
**Purpose**: SuperClaude command framework enhanced with Dopemux MCPs
**Decision Reference**: #133, #134 (Strategy), #142-144 (Implementation COMPLETE)
**Status**: ✅ Fully Integrated (2025-10-03)
**SuperClaude Version**: 4.1.5

**Observed runtime support**: `/sc:` command integration, manual `/dx:save`, `dopemux save`, registered lifecycle hook dispatch, and best-effort Stop/energy/progress hook signals.

**Planned/specification behavior**: `/dx:implement` timers, recurring save checkpoints, break prompts, and hyperfocus pause enforcement are not proven wired in observed Claude runtime.

## Why SuperClaude?

SuperClaude provides an **excellent command framework** with 25 commands and 15 specialized agents. However, Dopemux's MCP stack is **superior**:

| Feature | SuperClaude Default | Dopemux MCP Stack | Winner |
|---------|-------------------|-------------------|--------|
| **Multi-model Consensus** | ❌ None | ✅ Zen (GPT-5, O3, Claude) | Dopemux |
| **Knowledge Graph** | ❌ Basic memory | ✅ ConPort PostgreSQL AGE | Dopemux |
| **Code Intelligence** | ❌ Basic LSP | ✅ Serena (LSP + semantic + ADHD) | Dopemux |
| **Neural Search** | ✅ Tavily | ✅ Exa (better neural search) | Dopemux |
| **Research** | ❌ None | ✅ GPT-Researcher (4 engines) | Dopemux |
| **Sequential Thinking** | ✅ Sequential MCP | ✅ Zen (thinkdeep, planner, consensus) | Dopemux |
| **Documentation** | ✅ Context7 | ✅ Context7 | Tie |

**Strategy**: Install SuperClaude for its command framework, configure it to use Dopemux's superior MCPs.

## Implementation Status (Complete)

**Completed Actions** (Decision #142-144):

1. ✅ **Installation** (Decision #142)
   - Upgraded SuperClaude 4.0.9 → 4.1.5
   - Installed components: core (6 files), modes (7 files), commands (25 files), agents (16 files)
   - Total: 56 framework files in `~/.claude/`
   - Skipped: mcp and mcp_docs (using Dopemux MCPs instead)
   - Backups: 4 automatic backups created

2. ✅ **MCP Customization** (Decision #143)
   - Updated 12/25 command frontmatter files
   - Mapping: sequential→zen, tavily→exa+gpt-researcher
   - Kept: magic, playwright, context7, serena, morphllm
   - Key commands updated: implement, research, brainstorm, workflow, task, etc.

3. ✅ **MCP Documentation** (Decision #144)
   - Created MCP_Zen.md (224 lines, 6 tools)
   - Created MCP_ConPort.md (287 lines, 9 capabilities)
   - Created MCP_Serena.md (245 lines, LSP + v2 features)
   - Created MCP_Exa.md (157 lines, neural search)
   - Created MCP_GPTResearcher.md (274 lines, deep research)
   - Total: 1,187 lines of MCP documentation
   - Added @ imports to ~/.claude/CLAUDE.md

**Files Modified**:
- ~/.claude/CLAUDE.md (added workflow integration + MCP imports)
- ~/.claude/commands/sc/*.md (12 command frontmatter updates)
- ~/.claude/MCP_*.md (5 new documentation files)

**Zero Data Loss**: All Dopemux documentation preserved, clean integration verified.

## Integration Architecture

```
┌───────────────────────────────────────────────────────────┐
│              SuperClaude Command Layer                     │
│  ┌─────────────────┐  ┌──────────────────────────────┐   │
│  │ 25 Standard     │  │ 8 Custom /dx: Commands       │   │
│  │ Commands        │  │ (ADHD-optimized workflows)   │   │
│  └─────────────────┘  └──────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
                             │
                             v
┌───────────────────────────────────────────────────────────┐
│              Dopemux MCP Stack (Superior)                  │
│  ┌──────┐  ┌────────┐  ┌────────┐  ┌─────┐  ┌──────────┐│
│  │ Zen  │  │ConPort │  │ Serena │  │ Exa │  │   GPT    ││
│  │Multi │  │  AGE   │  │  LSP   │  │Neura│  │Researcher││
│  │Model │  │  KG    │  │ +ADHD  │  │  l  │  │ 4-engine ││
│  └──────┘  └────────┘  └────────┘  └─────┘  └──────────┘│
└───────────────────────────────────────────────────────────┘
                             │
                             v
┌───────────────────────────────────────────────────────────┐
│              Python ADHD Engine + Dashboard                │
│  Energy tracking │ 25-minute specs │ Break monitoring      │
└───────────────────────────────────────────────────────────┘
```

## 25 Standard Commands (Categorized)

### Category 1: USE AS-IS (5 commands)
No enhancement needed - straightforward automation:

1. **`/sc:build`** - Run build process
2. **`/sc:deploy`** - Deploy to environment
3. **`/sc:cleanup`** - Clean up code/files
4. **`/sc:spec-panel`** - Show spec panel
5. **`/sc:help`** - Show help

### Category 2: ENHANCE with Dopemux MCPs (11 commands)

6. **`/sc:brainstorm`** → **Enhanced with Zen consensus**
   - Original: Single-model brainstorming
   - Enhanced: Multi-model consensus (GPT-5, O3, Claude) via Zen
   - Config: Route to `mcp__zen__consensus` for idea validation

7. **`/sc:estimate`** → **Enhanced with Zen multi-model**
   - Original: Single estimate
   - Enhanced: 3-model consensus on task sizing
   - Config: Use Zen for collaborative estimation

8. **`/sc:test`** → **Enhanced with Serena navigation**
   - Original: Basic test writing
   - Enhanced: Serena LSP for test file navigation and coverage analysis
   - Config: `mcp__serena__find_related_tests`

9. **`/sc:fix`** → **Enhanced with Zen debug**
   - Original: Basic bug fixing
   - Enhanced: `mcp__zen__debug` for systematic root cause analysis
   - Config: Multi-step debugging with hypothesis testing

10. **`/sc:troubleshoot`** → **Enhanced with Zen debug**
    - Original: Troubleshooting
    - Enhanced: Same as `/sc:fix` - Zen debug workflow
    - Config: Deep analysis with multiple models

11. **`/sc:improve`** → **Enhanced with Serena semantic**
    - Original: Code improvement
    - Enhanced: Serena semantic analysis for refactoring suggestions
    - Config: `mcp__serena__semantic_search` for code patterns

12. **`/sc:optimize`** → **Enhanced with Serena profiling**
    - Original: Performance optimization
    - Enhanced: Serena code profiling + performance analysis
    - Config: Identify hot paths and bottlenecks

13. **`/sc:document`** → **Enhanced with Context7 standards**
    - Original: Basic documentation
    - Enhanced: Context7 for framework-specific docs + ADHD progressive disclosure
    - Config: `mcp__context7__get_library_docs` for examples

14. **`/sc:explain`** → **Enhanced with ADHD progressive**
    - Original: Code explanation
    - Enhanced: Progressive disclosure (essential first, details on request)
    - Config: Max 3 levels of detail, visual indicators

15. **`/sc:reflect`** → **Enhanced with ConPort progress**
    - Original: Session reflection
    - Enhanced: ConPort progress tracking and decision logging
    - Config: `mcp__conport__get_progress` + `mcp__conport__get_decisions`

16. **`/sc:index`** → **Enhanced with ConPort graph**
    - Original: Code indexing
    - Enhanced: ConPort knowledge graph for architectural relationships
    - Config: `mcp__conport__link_conport_items` for code-decision links

### Category 3: CUSTOMIZE as /dx: Commands (8 commands)
Completely reimplemented for ADHD workflows:

17. **`/sc:workflow`** → **`/dx:prd-parse`** (PRD decomposition)
18. **`/sc:implement`** → **`/dx:implement`** (ADHD sessions)
19. **`/sc:design`** → **`/dx:design`** (Zen consensus)
20. **`/sc:analyze`** → **`/dx:analyze`** (Zen thinkdeep)
21. **`/sc:review`** → **`/dx:review`** (Zen codereview)
22. **`/sc:load`** → **`/dx:load`** (ConPort context)
23. **`/sc:checkpoint`** → **`/dx:save`** (ConPort persistence)
24. **`/sc:research`** → **`/dx:research`** (Exa + GPT-Researcher)

### Category 4: REPLACE (1 command)

25. **`/sc:task`** → **ConPort `progress_entry` directly**
    - Original: Task management via SuperClaude
    - Replace: Use ConPort MCP tools directly (no wrapper needed)
    - Rationale: Direct access is simpler than command wrapper

## 8 Custom /dx: Commands (Priority Order)

### 1. `/dx:load` - Load Session Context (HIGHEST PRIORITY)
**Purpose**: Restore context after interruptions
**ADHD Value**: Gentle re-orientation, reduce context switch cost

```yaml
# ~/.claude/commands/dx/load.yaml
name: load
description: Load previous session context from ConPort
agent: developer
workflow:
  - step: get_active_context
    tool: mcp__conport__get_active_context
    params:
      workspace_id: "{workspace_path}"

  - step: get_recent_activity
    tool: mcp__conport__get_recent_activity_summary
    params:
      workspace_id: "{workspace_path}"
      hours_ago: 24

  - step: gentle_reorientation
    output: |
      ## 📍 **Where You Left Off**

      **Focus**: {active_context.current_focus}
      **Last Activity**: {active_context.session_notes}

      **Recent Progress** (last 24h):
      {recent_activity.recent_progress_entries}

      **Next Steps**:
      {active_context.next_steps}
```

### 2. `/dx:save` - Save Session State (HIGHEST PRIORITY)
**Purpose**: Checkpoint current work before interruptions
**ADHD Value**: Zero-cost context switching

```yaml
# ~/.claude/commands/dx/save.yaml
name: save
description: Save current session state to ConPort
agent: developer
workflow:
  - step: save_context
    tool: mcp__conport__update_active_context
    params:
      workspace_id: "{workspace_path}"
      patch_content:
        current_focus: "{user_input.focus}"
        session_notes: "{user_input.notes}"
        next_steps: "{user_input.next_steps}"
        session_saved: "{timestamp}"

  - step: confirmation
    output: "✅ Session saved! Safe to switch contexts."
```

### 3. `/dx:implement` - ADHD-Optimized Implementation (PRIMARY DEVELOPMENT)
**Purpose**: 25-minute focus sessions with energy matching
**ADHD Value**: Break management, save checkpoints, hyperfocus protection

```yaml
# ~/.claude/commands/dx/implement.yaml
name: implement
description: ADHD-optimized implementation with 25-minute sessions
agent: developer
workflow:
  - step: check_energy
    tool: mcp__conport__get_custom_data
    params:
      workspace_id: "{workspace_path}"
      category: "adhd_state"
      key: "current_energy"

  - step: select_task
    description: "Query ConPort for tasks matching current energy level"
    tool: mcp__conport__get_progress
    params:
      workspace_id: "{workspace_path}"
      status_filter: "TODO"

  - step: start_session
    description: "Start an operator-managed 25-minute checkpoint with planned save checkpoints"
    output: |
      🎯 **Starting 25-minute focus session**

      **Task**: {selected_task.description}
      **Energy Required**: {selected_task.energy_required}
      **Current Energy**: {current_energy}
      ✅ **Match**: Good fit!

      **Timer**: 25:00 ⏱️
      **Save checkpoint**: Every 5 minutes through a verified save path
      **Break**: Checkpoint at 25 minutes

  - step: implementation
    agent: developer
    mode: focused_implementation
    adhd_hooks:
      - save_checkpoint: 300     # 5 minutes, planned
      - break_checkpoint: 1500   # 25 minutes, planned
      - hyperfocus_alert: 3600   # 60 minutes, planned
      - hyperfocus_pause: 5400   # 90 minutes, planned
```

### 4. `/dx:prd-parse` - PRD Decomposition with Human Review
**Purpose**: Convert PRD to task hierarchy in ConPort
**ADHD Value**: Structured workflow, human quality gate

```yaml
# ~/.claude/commands/dx/prd-parse.yaml
name: prd-parse
description: Parse PRD into ConPort task hierarchy with human review
workflow:
  - step: analyze_prd
    tool: mcp__zen__planner
    params:
      model: "o3-mini"
      step: "Analyze PRD and create task breakdown with ADHD metadata"
      step_number: 1
      total_steps: 3
      next_step_required: true

  - step: generate_json
    description: "Create JSON task hierarchy with ADHD metadata"
    output_format: |
      {
        "tasks": [
          {
            "description": "Task description",
            "parent_id": null,
            "complexity_score": 0.6,
            "energy_required": "medium",
            "estimated_minutes": 45,
            "dependencies": []
          }
        ]
      }

  - step: human_review
    pause: true
    prompt: |
      **Review Generated Task Hierarchy**

      {generated_json}

      **Actions**:
      1. ✅ Approve and import to ConPort
      2. ✏️ Edit JSON before import
      3. ❌ Cancel (do not import)

  - step: validate_and_import
    if: approved
    tool: python_validator
    then:
      - mcp__conport__batch_log_items:
          workspace_id: "{workspace_path}"
          item_type: "progress_entry"
          items: "{validated_tasks}"
```

### 5. `/dx:analyze` - Deep Analysis with Zen Thinkdeep
**Purpose**: Complex problem investigation
**ADHD Value**: Structured thinking, multiple perspectives

```yaml
# ~/.claude/commands/dx/analyze.yaml
name: analyze
description: Deep analysis using Zen thinkdeep multi-step investigation
workflow:
  - step: thinkdeep_analysis
    tool: mcp__zen__thinkdeep
    params:
      model: "o3"
      step: "{user_question}"
      step_number: 1
      total_steps: 5
      next_step_required: true
      use_websearch: true
```

### 6. `/dx:review` - Code Review with Zen Multi-Model
**Purpose**: Comprehensive code review
**ADHD Value**: Multiple perspectives, automated quality checks

```yaml
# ~/.claude/commands/dx/review.yaml
name: review
description: Code review using Zen codereview with multi-model validation
workflow:
  - step: code_review
    tool: mcp__zen__codereview
    params:
      model: "o3-mini"
      step: "Review {file_paths} for quality, security, performance"
      relevant_files: "{file_paths}"
      review_type: "full"
      step_number: 1
      total_steps: 2
      next_step_required: true
```

### 7. `/dx:design` - Architectural Design with Consensus
**Purpose**: Design decisions with multi-model consensus
**ADHD Value**: Reduce decision paralysis, validate choices

```yaml
# ~/.claude/commands/dx/design.yaml
name: design
description: Architectural design using Zen consensus for validation
workflow:
  - step: consensus_design
    tool: mcp__zen__consensus
    params:
      model: "o3-mini"
      step: "{design_question}"
      models:
        - model: "o3"
          stance: "for"
        - model: "o3-mini"
          stance: "against"
        - model: "gpt-5"
          stance: "neutral"
      step_number: 1
      total_steps: 3
      next_step_required: true
```

### 8. `/dx:research` - Neural Search + Multi-Engine Research
**Purpose**: Deep research with Exa neural search + GPT-Researcher
**ADHD Value**: Comprehensive information gathering, structured output

```yaml
# ~/.claude/commands/dx/research.yaml
name: research
description: Deep research using Exa neural search and GPT-Researcher 4-engine
workflow:
  - step: neural_search
    tool: mcp__exa__search
    params:
      query: "{research_query}"
      num_results: 10
      use_neural_search: true

  - step: deep_research
    tool: mcp__gpt-researcher__deep_research
    params:
      query: "{research_query}"

  - step: synthesize
    description: "Combine Exa neural search with GPT-Researcher 4-engine results"
    output: "Comprehensive research report with citations"
```

## 15 Specialized Agents → MetaMCP Role Mapping

| SuperClaude Agent | MetaMCP Role | Tools Mounted | Use Case |
|------------------|--------------|---------------|----------|
| **Deep Research Agent** | RESEARCH | Exa, GPT-Researcher, Zen, Context7 (10 tools) | Investigation, analysis |
| **Analyzer Agent** | RESEARCH | Zen thinkdeep, ConPort, Serena (9 tools) | Problem analysis |
| **Strategic Analyst** | RESEARCH + PLAN | Zen consensus, ConPort decisions (9 tools) | Architecture decisions |
| **Frontend Architect** | ACT | Serena, Context7 (React/Next.js), morphllm (10 tools) | UI implementation |
| **Backend Developer** | ACT | Serena, Context7 (FastAPI/Django), ConPort (10 tools) | API implementation |
| **Developer (General)** | ACT | Full implementation stack (10 tools) | General development |
| **Security Engineer** | ACT | Zen security audit, Context7 (OWASP), Serena (10 tools) | Security review |
| **QA Engineer** | ACT | Serena test nav, ConPort progress, Context7 (10 tools) | Testing |
| **Performance Specialist** | ACT | Serena profiling, Zen analysis, Context7 (10 tools) | Optimization |
| **DevOps Engineer** | ACT | ConPort, Context7 (Docker/K8s) (8 tools) | Deployment |
| **Refactorer** | ACT | Serena semantic, Zen codereview, Context7 (10 tools) | Code improvement |
| **Architect** | PLAN | Zen consensus + planner, ConPort decisions (9 tools) | System design |
| **Technical Writer** | PLAN | Context7, ConPort, Zen (8 tools) | Documentation |
| **Developer (Simple)** | QUICKFIX | Serena basic, ConPort progress (8 tools) | Quick fixes |
| **Mentor** | ALL | All tools (60+) | Teaching, guidance |

## Configuration

### ~/.claude/superclaude.yaml
```yaml
# SuperClaude configuration with Dopemux MCPs
version: "1.0"

# Use Dopemux MCP stack (superior to defaults)
mcp_servers:
  zen:
    enabled: true
    tools:
      - consensus
      - planner
      - thinkdeep
      - debug
      - codereview

  conport:
    enabled: true
    workspace_id: "{auto_detect}"  # Auto-detect from git root

  serena:
    enabled: true
    adhd_mode: true

  exa:
    enabled: true
    neural_search: true

  gpt_researcher:
    enabled: true
    engines: ["google", "bing", "duckduckgo", "searx"]

  context7:
    enabled: true

  # Disable SuperClaude defaults (Dopemux versions are superior)
  tavily:
    enabled: false  # Use Exa instead

# ADHD optimizations
adhd:
  session_duration: 25  # minutes
  save_checkpoint_interval: 5  # minutes, planned unless runtime wiring is verified
  break_checkpoints: true
  hyperfocus_alert: 60     # minutes, planned unless runtime wiring is verified
  hyperfocus_pause: 90    # minutes, planned unless runtime wiring is verified

  # Progressive disclosure
  max_detail_levels: 3
  default_detail_level: 1

  # Decision reduction
  max_options: 3

# Agent configuration
agents:
  default_agent: "developer"
  role_switching: "metamcp"  # Use MetaMCP for role-based tool mounting
```

## Implementation Timeline

**Total**: 5-6 days (revised from 3 days - more realistic)

### Day 1: Install & Configure (6-8 hours)
- ✅ SuperClaude v4.0.9 already installed
- [ ] Create `~/.claude/superclaude.yaml` with Dopemux MCPs
- [ ] Verify all 8 MCP servers accessible
- [ ] Test standard commands with enhanced MCPs

### Days 2-3: Create 8 /dx: Commands (12-16 hours)
Priority order (implement in this sequence):
1. `/dx:load` + `/dx:save` - Session management (most frequent use)
2. `/dx:implement` - Primary development workflow
3. `/dx:prd-parse` - PRD decomposition
4. `/dx:analyze` + `/dx:review` - Code quality
5. `/dx:design` - Architecture decisions
6. `/dx:research` - Investigation

### Days 4-5: Enhance 11 Standard Commands (12-16 hours)
Configure MCP routing for:
- Planning commands (brainstorm, estimate, design) → Zen
- Implementation commands (fix, troubleshoot) → Zen debug
- Quality commands (improve, optimize, review) → Serena + Zen
- Documentation commands (document, explain) → Context7 + ADHD

### Day 6: Testing & Documentation (6-8 hours)
- [ ] Test complete workflows (PRD → Implementation → Review)
- [ ] Verify ADHD accommodations (25-minute sessions, breaks)
- [ ] Document command usage patterns
- [ ] Create troubleshooting guide

## Usage Patterns

### Daily Development Session
```bash
# Morning: Load context
/dx:load

# Start implementation
/dx:implement

# (25 minutes later: planned break checkpoint)
# "Great work! Time for 5min break ☕"

# Continue or switch tasks
/dx:implement  # Resume or select new task

# End of day: Save progress
/dx:save "Completed auth implementation, next: API integration"
```

### PRD to Implementation Workflow
```bash
# Step 1: Parse PRD
/dx:prd-parse "requirements/auth-feature.md"
# → Zen planner generates task hierarchy
# → Human reviews and approves JSON
# → ConPort batch imports tasks

# Step 2: Review architecture
/dx:design "Should we use JWT or session tokens for auth?"
# → Zen consensus (3 models, different stances)
# → Decision logged to ConPort

# Step 3: Implementation
/dx:implement
# → ADHD engine selects optimal task based on energy
# → Operator-managed 25-minute session with planned save checkpoints

# Step 4: Code review
/dx:review "src/auth/*.py"
# → Zen codereview (multi-model validation)
# → Issues logged to ConPort
```

---

**See Also:**
- `.claude/modules/custom-commands.md` - Detailed /dx: command reference
- `.claude/modules/adhd-patterns.md` - ADHD session management patterns
- `.claude/modules/coordination/authority-matrix.md` - Authority boundaries
