# Custom /dx: Commands Reference

**Version**: 2.0.0
**Purpose**: Specifications for 8 ADHD-optimized custom commands (planned)
**Current Status**: /sc: commands implemented (Decision #142-144), /dx: commands specified (implementation pending)
**Location**: `~/.claude/commands/dx/` (when implemented)
**Decision Reference**: #133, #134 (Strategy), #142-144 (SuperClaude integration complete)

**Note**: /sc: standard commands (25 total) are fully operational now. /dx: commands are detailed specifications for future ADHD-specific enhancements. Use /sc: commands for current workflows.

## Command Overview

| Command | Purpose | ADHD Value | Frequency | Priority |
|---------|---------|------------|-----------|----------|
| `/dx:load` | Restore session context | Zero-cost context switch | Multiple/day | 🔴 Critical |
| `/dx:save` | Checkpoint progress | Interruption safety | Multiple/day | 🔴 Critical |
| `/dx:implement` | ADHD-optimized coding | Break management | Daily | 🔴 Critical |
| `/dx:prd-parse` | PRD → tasks | Structured decomposition | Weekly | 🟡 Important |
| `/dx:analyze` | Deep investigation | Reduce overwhelm | As needed | 🟡 Important |
| `/dx:review` | Multi-model code review | Confidence building | Per PR | 🟡 Important |
| `/dx:design` | Architecture decisions | Reduce decision paralysis | As needed | 🟢 Nice-to-have |
| `/dx:research` | Deep research | Comprehensive info gathering | As needed | 🟢 Nice-to-have |

---

## 1. `/dx:load` - Load Session Context

**Priority**: 🔴 **CRITICAL** (implement first)
**Frequency**: Multiple times per day
**ADHD Value**: Gentle re-orientation, reduce context switch cost, restore working memory

### Purpose
Restore context after interruptions (meetings, breaks, overnight). Provides gentle re-orientation instead of forcing user to remember "what was I working on?"

### Implementation

```yaml
# ~/.claude/commands/dx/load.yaml
name: load
description: Load previous session context from ConPort memory
category: session_management
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
      hours_ago: 24  # Last 24 hours

  - step: get_current_tasks
    tool: mcp__conport__get_progress
    params:
      workspace_id: "{workspace_path}"
      status_filter: "IN_PROGRESS"
      limit: 5

  - step: gentle_reorientation
    output_template: |
      ## 📍 **Where You Left Off**

      **Current Focus**: {active_context.current_focus}

      **Last Session Notes**:
      {active_context.session_notes}

      **In-Progress Tasks** (resumed):
      {tasks_in_progress}

      **Recent Activity** (last 24h):
      - {recent_activity.recent_decisions[0].summary}
      - {recent_activity.recent_progress_entries[0].description}

      **Next Steps** (your plan):
      {active_context.next_steps}

      ---

      **Choose One**:
      1. Continue where you left off
      2. Switch to a different task
      3. Review recent decisions first
```

### Usage Examples

```bash
# Morning startup - full context load
/dx:load

# After meeting - quick context restore
/dx:load

# After lunch break
/dx:load
```

### ADHD Accommodations

- ✅ **Visual structure** - Clear headers, bullets, numbered options
- ✅ **Max 3 options** - Reduce decision fatigue
- ✅ **Gentle language** - "Where you left off" not "Resume work"
- ✅ **Time anchors** - "last 24h" helps temporal awareness
- ✅ **Context bridging** - Connect previous state to current

### Output Example

```
## 📍 **Where You Left Off**

**Current Focus**: SuperClaude-Dopemux Integration

**Last Session Notes**:
Completed Decision #134 (all 25 commands valuable). Started documentation
update to remove task-master/orchestrator confusion.

**In-Progress Tasks** (resumed):
- UPDATE DOCS 7: Create custom-commands.md

**Recent Activity** (last 24h):
- Decision #134: Complete SuperClaude Command & Agent Analysis
- Progress: Updated 6/10 documentation files

**Next Steps** (your plan):
- Complete custom-commands.md
- Update sprint.md with ConPort workflow
- Test all docs for consistency

---

**Choose One**:
1. Continue documentation updates
2. Switch to SuperClaude configuration
3. Review recent decisions first
```

---

## 2. `/dx:save` - Save Session State

**Priority**: 🔴 **CRITICAL** (implement first)
**Frequency**: Multiple times per day
**ADHD Value**: Interruption safety, zero-cost context switching

### Purpose
Checkpoint current work before interruptions. Creates safety net for ADHD context switching.

### Implementation

```yaml
# ~/.claude/commands/dx/save.yaml
name: save
description: Save current session state to ConPort for later restoration
category: session_management
agent: developer

prompts:
  - name: current_focus
    description: "What are you currently working on? (1 sentence)"
    required: true

  - name: session_notes
    description: "Quick notes about progress/blockers (2-3 sentences)"
    required: true

  - name: next_steps
    description: "What should you do when you return? (bullet points)"
    required: true

workflow:
  - step: save_to_conport
    tool: mcp__conport__update_active_context
    params:
      workspace_id: "{workspace_path}"
      patch_content:
        current_focus: "{prompts.current_focus}"
        session_notes: "{prompts.session_notes}"
        next_steps: "{prompts.next_steps}"
        session_saved: "{timestamp}"
        mode: "ACT"  # or "PLAN" based on activity

  - step: auto_save_progress
    description: "Save any in-progress tasks"
    tool: mcp__conport__get_progress
    params:
      workspace_id: "{workspace_path}"
      status_filter: "IN_PROGRESS"

  - step: confirmation
    output_template: |
      ✅ **Session Saved Successfully!**

      **Saved at**: {timestamp}
      **Focus**: {prompts.current_focus}

      Safe to switch contexts now. Use `/dx:load` to restore.
```

### Usage Examples

```bash
# Quick save before meeting
/dx:save
# Prompts:
# - Current focus: "Implementing auth OAuth2 flow"
# - Notes: "Got token exchange working, need to add refresh logic"
# - Next steps: "1. Add refresh token endpoint, 2. Test expiration"

# End of day save
/dx:save
# Prompts:
# - Current focus: "Documentation update"
# - Notes: "6/10 docs complete, removed old Two-Plane architecture refs"
# - Next steps: "1. Finish custom-commands.md, 2. Update sprint.md, 3. Test all"
```

### ADHD Accommodations

- ✅ **Minimal friction** - Only 3 prompts (focus, notes, next steps)
- ✅ **Structured prompts** - Clear questions reduce cognitive load
- ✅ **Confirmation** - Visual confirmation builds trust
- ✅ **Time stamping** - Helps temporal awareness

---

## 3. `/dx:implement` - ADHD-Optimized Implementation

**Priority**: 🔴 **CRITICAL** (primary development workflow)
**Frequency**: Daily (multiple sessions)
**ADHD Value**: 25min sessions, energy matching, break management, hyperfocus protection

### Purpose
Structured implementation sessions with automatic break reminders, energy-aware task selection, and context preservation.

### Implementation

```yaml
# ~/.claude/commands/dx/implement.yaml
name: implement
description: ADHD-optimized implementation with 25min focus sessions
category: development
agent: developer

workflow:
  - step: check_adhd_state
    tool: mcp__conport__get_custom_data
    params:
      workspace_id: "{workspace_path}"
      category: "adhd_state"
    description: "Get current energy, attention, cognitive load"

  - step: get_available_tasks
    tool: mcp__conport__get_progress
    params:
      workspace_id: "{workspace_path}"
      status_filter: "TODO"
      limit: 10

  - step: smart_task_selection
    description: "Python ADHD Engine ranks tasks by energy match"
    python_module: "services.adhd_engine.task_selector"
    function: "recommend_tasks"
    params:
      tasks: "{available_tasks}"
      current_energy: "{adhd_state.energy}"
      current_attention: "{adhd_state.attention}"
      current_load: "{adhd_state.cognitive_load}"
      max_recommendations: 3

  - step: user_task_selection
    prompt: |
      ## 🎯 **Recommended Tasks** (matched to your current state)

      **Your Current State**:
      - Energy: {adhd_state.energy} ⚡
      - Attention: {adhd_state.attention} 🧠
      - Cognitive Load: {adhd_state.cognitive_load} 📊

      **Top 3 Matches**:
      1. [{recommended_tasks[0].complexity_score}] {recommended_tasks[0].description}
         Energy: {recommended_tasks[0].energy_required} | Est: {recommended_tasks[0].estimated_minutes}min

      2. [{recommended_tasks[1].complexity_score}] {recommended_tasks[1].description}
         Energy: {recommended_tasks[1].energy_required} | Est: {recommended_tasks[1].estimated_minutes}min

      3. [{recommended_tasks[2].complexity_score}] {recommended_tasks[2].description}
         Energy: {recommended_tasks[2].energy_required} | Est: {recommended_tasks[2].estimated_minutes}min

      **Select**: 1, 2, or 3 (or 'other' to see more)

  - step: start_session
    python_module: "services.adhd_engine.session_manager"
    function: "start_session"
    params:
      task_id: "{selected_task.id}"
      workspace_id: "{workspace_path}"
      session_duration: 25  # minutes

  - step: session_announcement
    output_template: |
      🎯 **Focus Session Started!**

      **Task**: {selected_task.description}
      **Duration**: 25:00 ⏱️
      **Auto-save**: Every 5 minutes
      **Break reminder**: At 25:00

      **Focus Mode Active** - Minimize distractions!

adhd_hooks:
  # Auto-save to ConPort every 5 minutes
  auto_save:
    interval: 300  # seconds
    tool: mcp__conport__update_progress
    params:
      workspace_id: "{workspace_path}"
      progress_id: "{selected_task.id}"
      status: "IN_PROGRESS"

  # Break reminder at 25 minutes
  break_reminder:
    interval: 1500  # 25 minutes
    action: pause_session
    notification: |
      ⏰ **Great work! Time for a 5-minute break**

      You've been focused for 25 minutes. Taking a break helps:
      - Prevent burnout
      - Maintain attention quality
      - Process what you learned

      **Choose**:
      1. Take 5min break (recommended)
      2. Continue for 10 more min (then mandatory break)
      3. Save and switch tasks

  # Hyperfocus warning at 60 minutes
  hyperfocus_warn:
    interval: 3600  # 60 minutes
    notification: |
      ⚠️ **Hyperfocus Alert**: You've been coding for 60 minutes straight!

      Please take a break soon to avoid burnout.

  # Mandatory break at 90 minutes
  hyperfocus_force:
    interval: 5400  # 90 minutes
    action: force_pause
    notification: |
      🛑 **Mandatory Break**: 90 minutes is the limit!

      For your health and code quality, taking a 10-minute break now.
      Your work has been auto-saved.
```

### Usage Examples

```bash
# Start implementation session
/dx:implement
# → Shows recommended tasks based on energy
# → User selects task 1
# → 25min timer starts with auto-save

# After 25min break reminder
# User chooses "Take 5min break"
# → Session pauses, progress saved

# After break, resume
/dx:implement
# → Can continue same task or select new one
```

### ADHD Accommodations

- ✅ **Energy matching** - Tasks recommended based on current energy level
- ✅ **25min sessions** - Prevent burnout, maintain quality attention
- ✅ **Auto-save every 5min** - Never lose work, safe interruptions
- ✅ **Gentle break reminders** - Not punitive, explains benefits
- ✅ **Hyperfocus protection** - Warns at 60min, forces break at 90min
- ✅ **Max 3 options** - Reduce decision paralysis
- ✅ **Visual progress** - Timer, status indicators
- ✅ **Celebration** - "Great work!" positive reinforcement

---

## 4. `/dx:prd-parse` - PRD Decomposition

**Priority**: 🟡 **IMPORTANT** (weekly sprint planning)
**Frequency**: Weekly (per PRD)
**ADHD Value**: Structured decomposition, human quality gate, ADHD metadata injection

### Purpose
Convert PRD documents into ConPort task hierarchy with ADHD-optimized metadata (complexity, energy required, estimated duration, break points).

### Implementation

```yaml
# ~/.claude/commands/dx/prd-parse.yaml
name: prd-parse
description: Parse PRD into ConPort task hierarchy with Zen planner and human review
category: planning
agent: architect

arguments:
  - name: prd_file
    description: "Path to PRD markdown file"
    required: true

workflow:
  - step: analyze_prd
    tool: mcp__zen__planner
    params:
      model: "o3-mini"
      step: |
        Analyze the following PRD and create a complete task breakdown.

        PRD:
        {file_content(prd_file)}

        Requirements:
        1. Break into tasks of 15-90 minute chunks (ADHD optimal)
        2. Add ADHD metadata for each task:
           - complexity_score (0-1, where 0.7+ is high complexity)
           - energy_required (low/medium/high)
           - estimated_minutes (15-90, no larger chunks)
           - cognitive_load (0-1)
        3. Identify dependencies (what blocks what)
        4. Suggest break points for complex tasks
      step_number: 1
      total_steps: 3
      next_step_required: true

  - step: generate_json_hierarchy
    tool: mcp__zen__planner
    params:
      model: "o3-mini"
      step: |
        Convert task breakdown into JSON format:

        {
          "tasks": [
            {
              "id": "task-001",
              "description": "Clear, actionable task description",
              "parent_id": null,
              "dependencies": [],
              "complexity_score": 0.6,
              "energy_required": "medium",
              "cognitive_load": 0.5,
              "estimated_minutes": 45,
              "break_points": [25],
              "files_affected": ["path/to/file.py"],
              "adhd_notes": "Complex logic - best during high energy"
            }
          ]
        }
      step_number: 2
      total_steps: 3
      next_step_required: true

  - step: human_review
    pause: true
    prompt: |
      ## **Review Generated Task Hierarchy**

      **Tasks**: {task_count} tasks generated
      **Estimated Total**: {total_estimated_minutes} minutes ({total_estimated_hours} hours)
      **Complexity Distribution**:
      - Low (0-0.4): {low_complexity_count}
      - Medium (0.4-0.7): {medium_complexity_count}
      - High (0.7-1.0): {high_complexity_count}

      **JSON Output**:
      ```json
      {generated_json}
      ```

      **Actions**:
      1. ✅ **Approve** - Import to ConPort as-is
      2. ✏️ **Edit** - Modify JSON before import
      3. ❌ **Cancel** - Do not import, start over

      **Your choice**:

  - step: validate_json
    if: approved || edited
    python_module: "services.prd_parser.validator"
    function: "validate_task_json"
    params:
      json_data: "{reviewed_json}"
    checks:
      - schema_valid: true
      - no_circular_dependencies: true
      - adhd_chunks_valid: true  # All tasks 15-90min
      - complexity_scores_valid: true  # All 0-1 range

  - step: inject_adhd_metadata
    python_module: "services.adhd_engine.metadata_injector"
    function: "enhance_tasks"
    params:
      tasks: "{validated_json}"
    enhancements:
      - calculate_cognitive_load
      - suggest_optimal_order
      - identify_parallel_tasks
      - add_break_recommendations

  - step: batch_import_to_conport
    tool: mcp__conport__batch_log_items
    params:
      workspace_id: "{workspace_path}"
      item_type: "progress_entry"
      items: "{enhanced_tasks}"

  - step: create_dependency_links
    description: "Create task dependency relationships in ConPort knowledge graph"
    tool: mcp__conport__link_conport_items
    for_each: "{task.dependencies}"
    params:
      workspace_id: "{workspace_path}"
      source_item_type: "progress_entry"
      source_item_id: "{task.id}"
      target_item_type: "progress_entry"
      target_item_id: "{dependency.id}"
      relationship_type: "BLOCKS"
      description: "{task.description} blocks {dependency.description}"

  - step: log_import_decision
    tool: mcp__conport__log_decision
    params:
      workspace_id: "{workspace_path}"
      summary: "PRD '{prd_file}' parsed and imported to ConPort"
      rationale: "Zen planner decomposition validated by human review"
      implementation_details: "{task_count} tasks, {total_estimated_hours}h estimated"
      tags: ["prd-parsing", "task-import", "zen-planner"]

  - step: completion_summary
    output_template: |
      ✅ **PRD Import Complete!**

      **Imported**: {task_count} tasks
      **Total Effort**: {total_estimated_hours} hours
      **Dependencies**: {dependency_count} blocking relationships

      **Next Steps**:
      1. Review tasks: Use ConPort or dashboard
      2. Start implementation: `/dx:implement`
      3. Track progress: Auto-saved to ConPort

      **Tasks are ready for ADHD-optimized workflow!**
```

### ADHD Accommodations

- ✅ **25-90min chunks** - All tasks broken into ADHD-optimal sizes
- ✅ **Human review gate** - Catch errors before committing
- ✅ **Energy metadata** - Enables smart task selection in `/dx:implement`
- ✅ **Complexity scoring** - Know difficulty upfront, reduce surprises
- ✅ **Break point suggestions** - Pre-planned pauses for complex tasks
- ✅ **Dependency visualization** - Understand blocking relationships

---

## 5. `/dx:analyze` - Deep Analysis with Zen Thinkdeep

**Priority**: 🟡 **IMPORTANT**
**Frequency**: As needed
**ADHD Value**: Structured investigation, multiple perspectives, reduce overwhelm

### Implementation

```yaml
# ~/.claude/commands/dx/analyze.yaml
name: analyze
description: Deep analysis using Zen thinkdeep multi-step investigation
category: analysis
agent: analyzer

arguments:
  - name: question
    description: "What do you want to analyze?"
    required: true

workflow:
  - step: thinkdeep_investigation
    tool: mcp__zen__thinkdeep
    params:
      model: "o3"
      step: "{question}"
      step_number: 1
      total_steps: 5
      next_step_required: true
      use_websearch: true
      thinking_mode: "high"  # 67% of model thinking budget

  - step: log_analysis_decision
    tool: mcp__conport__log_decision
    params:
      workspace_id: "{workspace_path}"
      summary: "Analysis: {question}"
      rationale: "{thinkdeep_findings}"
      tags: ["analysis", "zen-thinkdeep"]
```

### ADHD Accommodations

- ✅ **Structured thinking** - Multi-step investigation prevents overwhelm
- ✅ **Expert validation** - Zen uses multiple models for verification
- ✅ **Decision logging** - Automatic capture in ConPort knowledge graph

---

## 6. `/dx:review` - Multi-Model Code Review

**Priority**: 🟡 **IMPORTANT**
**Frequency**: Per pull request
**ADHD Value**: Confidence building, multiple perspectives

### Implementation

```yaml
# ~/.claude/commands/dx/review.yaml
name: review
description: Comprehensive code review using Zen codereview
category: quality
agent: qa_engineer

arguments:
  - name: files
    description: "Files to review (glob pattern or paths)"
    required: true

workflow:
  - step: code_review
    tool: mcp__zen__codereview
    params:
      model: "o3-mini"
      step: "Review {files} for quality, security, performance, ADHD code patterns"
      relevant_files: "{files}"
      review_type: "full"
      step_number: 1
      total_steps: 2
      next_step_required: true
      use_websearch: true  # For best practices lookup
```

---

## 7. `/dx:design` - Architecture Decisions with Consensus

**Priority**: 🟢 **NICE-TO-HAVE**
**Frequency**: As needed
**ADHD Value**: Reduce decision paralysis, validate architectural choices

### Implementation

```yaml
# ~/.claude/commands/dx/design.yaml
name: design
description: Architectural design with multi-model consensus
category: architecture
agent: architect

arguments:
  - name: design_question
    description: "Architecture question to decide"
    required: true

workflow:
  - step: consensus_evaluation
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

---

## 8. `/dx:research` - Neural Search + Multi-Engine Research

**Priority**: 🟢 **NICE-TO-HAVE**
**Frequency**: As needed
**ADHD Value**: Comprehensive information gathering, structured output

### Implementation

```yaml
# ~/.claude/commands/dx/research.yaml
name: research
description: Deep research using Exa neural search + GPT-Researcher
category: research
agent: deep_research

arguments:
  - name: research_query
    description: "What to research?"
    required: true

workflow:
  - step: neural_search
    tool: mcp__exa__search
    params:
      query: "{research_query}"
      num_results: 10
      use_neural_search: true

  - step: multi_engine_research
    tool: mcp__gpt-researcher__deep_research
    params:
      query: "{research_query}"

  - step: synthesize_results
    output_template: |
      ## **Research Results**: {research_query}

      **Exa Neural Search** (10 results):
      {exa_results}

      **GPT-Researcher** (4 engines):
      {gpt_researcher_results}

      **Synthesis**:
      {combined_insights}
```

---

## Installation

```bash
# Create command directory
mkdir -p ~/.claude/commands/dx

# Copy command YAML files
cp .claude/modules/custom-commands/*.yaml ~/.claude/commands/dx/

# Test commands
/dx:load --help
/dx:save --help
/dx:implement --help
```

---

**See Also:**
- `.claude/modules/superclaude-integration.md` - SuperClaude overview
- `.claude/modules/adhd-patterns.md` - ADHD session patterns
- `.claude/modules/coordination/authority-matrix.md` - Authority boundaries
