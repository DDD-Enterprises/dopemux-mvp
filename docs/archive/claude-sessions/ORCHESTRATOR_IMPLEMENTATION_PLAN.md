---
id: ORCHESTRATOR_IMPLEMENTATION_PLAN
title: Orchestrator_Implementation_Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Orchestrator_Implementation_Plan (explanation) for dopemux documentation
  and developer workflows.
---
# Dopemux Multi-AI Orchestrator - Implementation Plan

**Version**: 1.0
**Date**: 2025-10-16
**Status**: Ready to Execute
**ConPort**: Saved as `implementation_plans/orchestrator_phase1_roadmap`

---

## 🎯 Phase 1 MVP Goal

**Build**: Production-ready tmux-based multi-AI orchestrator
**Timeline**: Weeks 1-2 (33 focus blocks, ~825 minutes)
**Confidence**: 87% (Zen multi-model validated)

### Success Criteria
- ✅ Launch 2-4 AI instances in tmux panes
- ✅ Route commands to appropriate agents
- ✅ Auto-save context every 30 seconds
- ✅ Resume sessions after interruption
- ✅ ADHD-optimized energy-based layouts

---

## 📋 Implementation Steps (7 Steps)

### Step 1: Create tmux 4-pane layout manager
**Duration**: 4 focus blocks (100 minutes)
**Complexity**: 0.35 (Low-Medium)
**Energy**: Medium
**Dependencies**: None

**Files to Create**:
- `services/orchestrator/src/tmux_manager.py`
- `services/orchestrator/src/layouts/adaptive_layout.py`
- `services/orchestrator/tests/test_tmux_manager.py`
- `services/orchestrator/config/layouts.yaml`

**Key Features**:
- Adaptive layouts based on energy (low=2 panes, medium=3, high=4)
- Pane ID tracking for agent management
- Layout persistence to ConPort

**Validation**:
```bash
pytest services/orchestrator/tests/test_tmux_manager.py -v
python -m orchestrator.tmux_manager --energy=low --agents=2
tmux list-panes -t dopemux  # Should show correct count
```

---

### Step 2: Implement chat command parser (slash commands)
**Duration**: 5 focus blocks (125 minutes)
**Complexity**: 0.45 (Medium)
**Energy**: Medium-High
**Dependencies**: Step 1

**Files to Create**:
- `services/orchestrator/src/command_parser.py`
- `services/orchestrator/src/commands/` (directory with 5 command modules)
- `services/orchestrator/tests/test_command_parser.py`

**Command Types**:
- `/research` → Claude + Gemini (parallel)
- `/plan` → Grok zen/planner + Claude validation
- `/implement` → Grok code gen + Claude review
- `/delegate` → All agents parallel
- `/debug` → Claude zen/debug

**Validation**:
```bash
pytest services/orchestrator/tests/test_command_parser.py -v
echo "/research Next.js patterns" | python -m orchestrator.command_parser
# Expected: {mode: RESEARCH, agents: ["claude", "gemini"]}
```

---

### Step 3: Build agent spawner (launch Claude/Gemini/Grok in panes)
**Duration**: 6 focus blocks (150 minutes)
**Complexity**: 0.65 (Medium-High)
**Energy**: High
**Dependencies**: Step 1, Step 2

**Files to Create**:
- `services/orchestrator/src/agent_spawner.py`
- `services/orchestrator/src/agents/` (directory with base + 3 agent classes)
- `services/orchestrator/config/agent_configs.yaml`
- `services/orchestrator/tests/test_agent_spawner.py`

**Key Features**:
- BaseAgent abstraction for polymorphism
- ClaudeAgent, GeminiAgent, GrokAgent implementations
- Health check system (30s interval)
- Graceful failure handling

**ADHD Note**: ⚠️ **Implement one agent per day** to reduce context switching

**Validation**:
```bash
pytest services/orchestrator/tests/test_agent_spawner.py -v
python -m orchestrator.agent_spawner --spawn=claude --pane=0
tmux capture-pane -t dopemux:0 -p | grep "Claude"  # Should see Claude prompt
```

---

### Step 4: Implement TmuxCapture message abstraction
**Duration**: 5 focus blocks (125 minutes)
**Complexity**: 0.55 (Medium)
**Energy**: Medium-High
**Dependencies**: Step 1, Step 3

**Files to Create**:
- `services/orchestrator/src/message_bus.py`
- `services/orchestrator/src/capture/tmux_capture.py`
- `services/orchestrator/src/capture/message_extractor.py`
- `services/orchestrator/tests/test_message_bus.py`
- `services/orchestrator/config/message_patterns.yaml`

**Key Features**:
- MessageBusProtocol abstraction (future Redis upgrade path)
- TmuxMessageBus implementation (in-memory for MVP)
- Incremental capture (only new output)
- Message routing (target-specific or broadcast)

**Design Decision**: Start without Redis, add only if needed (>1000 messages/hour)

**Validation**:
```bash
pytest services/orchestrator/tests/test_message_bus.py -v
python -m orchestrator.message_bus --test-publish
tmux capture-pane -t dopemux:0 -p | tail -5  # Verify message appears
```

---

### Step 5: Integrate ConPort for auto-save checkpoints
**Duration**: 4 focus blocks (100 minutes)
**Complexity**: 0.40 (Medium)
**Energy**: Medium
**Dependencies**: Step 3, Step 4

**Files to Create**:
- `services/orchestrator/src/checkpoint_manager.py`
- `services/orchestrator/src/integrations/conport_client.py`
- `services/orchestrator/tests/test_checkpoint_manager.py`

**Key Features**:
- Auto-save every 30 seconds (background async loop)
- Checkpoint data: active agents, message history, command state, energy level, layout
- ConPort HTTP client wrapper
- Restore logic for session recovery

**ADHD Benefit**: 🎯 **HIGH** - Prevents 23-minute context switching cost

**Validation**:
```bash
pytest services/orchestrator/tests/test_checkpoint_manager.py -v

# Manual test:
# 1. Start orchestrator, send command, wait 35s
# 2. Check ConPort:
curl http://localhost:5455/mcp/conport/get_active_context?workspace_id=/Users/hue/code/dopemux-mvp
# Should see orchestrator_checkpoint with recent timestamp

# 3. Kill orchestrator, restart with --restore
python -m orchestrator.main --restore
# Should show: "Restored session from [timestamp]"
```

---

### Step 6: Build basic command routing (research/plan/implement modes)
**Duration**: 5 focus blocks (125 minutes)
**Complexity**: 0.50 (Medium)
**Energy**: Medium-High
**Dependencies**: Step 2, Step 3, Step 4

**Files to Create**:
- `services/orchestrator/src/router.py`
- `services/orchestrator/src/modes/` (directory with 4 mode handlers)
- `services/orchestrator/config/routing_rules.yaml`
- `services/orchestrator/tests/test_router.py`

**Routing Logic**:
- **RESEARCH**: Claude + Gemini (parallel consensus)
- **PLAN**: Grok zen/planner primary, Claude validation
- **IMPLEMENT**: Grok code gen + Claude review
- **DELEGATE**: All agents in parallel
- **DEBUG**: Claude zen/debug primary

**Validation**:
```bash
pytest services/orchestrator/tests/test_router.py -v
# Test each mode routes correctly
```

---

### Step 7: Create resume flow for session restoration
**Duration**: 4 focus blocks (100 minutes)
**Complexity**: 0.35 (Low-Medium)
**Energy**: Medium
**Dependencies**: Step 5

**Files to Create**:
- `services/orchestrator/src/session_manager.py`
- `services/orchestrator/src/restore/checkpoint_restore.py`
- `services/orchestrator/tests/test_session_manager.py`

**Key Features**:
- Gentle re-orientation message on resume
- "Where you left off" summary with visual formatting
- Recreate tmux layout exactly
- Re-spawn agents in same panes
- Restore last 10 messages for context
- Option to resume interrupted command

**Re-orientation Example**:
```
═══════════════════════════════════════════════
  Welcome back! Here's where you left off:
═══════════════════════════════════════════════
  📍 Working on: Authentication system
  🕐 Last active: 45 minutes ago
  ⚡ Energy level: Medium
  🎯 Suggested next: Implement JWT validation
═══════════════════════════════════════════════
```

**Validation**:
```bash
pytest services/orchestrator/tests/test_session_manager.py -v
# Test full restore workflow end-to-end
```

---

## 📊 Total Effort Breakdown

### Time Estimates
- **Total Focus Blocks**: 33
- **Total Minutes**: 825 minutes (13.75 hours)
- **ADHD Sessions**: 28 sessions (25 min work + 5 min break)
- **Calendar Days**: 10-14 days (1-2 hours per day)

### Complexity Distribution
- **Low (0.3-0.4)**: Steps 1, 7 (200 minutes)
- **Medium (0.4-0.6)**: Steps 2, 4, 5, 6 (475 minutes)
- **High (0.6+)**: Step 3 (150 minutes)

### Energy Distribution
- **Medium**: Steps 1, 5, 7 (300 minutes)
- **Medium-High**: Steps 2, 4, 6 (375 minutes)
- **High**: Step 3 (150 minutes)

---

## 🏗️ What's Already Built

### ✅ Orchestrator Foundation (Phase 2 Complete)
- **HTTP Client**: 806 lines (sync + async, circuit breaker)
- **ConPort Integration**: checkpoint_manager.py + context_protocol.py
- **Tests**: 41/41 passing (100%)
- **Status**: READY_TO_SHIP marker added
- **Commits**: 9e83991, 383ed82, 277d0fa, b3038ff

### ✅ Supporting Systems
- **ConPort MCP**: Decision logging, knowledge graph, active context
- **Serena v2**: LSP navigation, complexity scoring, ADHD features
- **Dope-Context**: Semantic search (NOW with BM25 hybrid!)
- **Zen MCP**: Multi-model reasoning (thinkdeep, planner, consensus, debug, codereview)

---

## 🚀 How to Start

### Quick Start (Recommended)
```bash
# 1. Retrieve plan from ConPort
mcp__conport__get_custom_data(
    workspace_id="/Users/hue/code/dopemux-mvp",
    category="implementation_plans",
    key="orchestrator_phase1_roadmap"
)

# 2. Start with Step 1
cd services/orchestrator
mkdir -p src/layouts tests config
touch src/tmux_manager.py src/layouts/adaptive_layout.py

# 3. Follow the roadmap step-by-step
# Each step has clear files, validation, and ADHD considerations
```

### Use with /sc:implement or /dx:implement
```bash
# ADHD-optimized 25-minute implementation session
/dx:implement "Step 1: tmux layout manager"

# Or manual with Zen planner
mcp__zen__planner(
    step="Breaking down Step 1: tmux layout manager into substeps",
    step_number=1, total_steps=5,
    next_step_required=True,
    model="gpt-5-codex"
)
```

---

## 📚 Reference Documents

### Research Foundation (120K words)
- `claudedocs/multi-agent-ai-systems-research-2025-10-15.md` (2,517 lines)
- `claudedocs/research_adhd_interface_optimization_20251015.md` (1,149 lines)
- `claudedocs/research_multi-pane_layout_patterns_2025-10-15.md` (913 lines)

### Design Documents (5,578 lines)
- `docs/DOPEMUX-UI-COMPLETE-MASTER-PLAN.md` (2,227 lines) - **THE DEFINITIVE GUIDE**
- `docs/DOPEMUX-UNIFIED-DESIGN-PHILOSOPHY.md` (1,275 lines)
- `docs/DOPEMUX-ORCHESTRATOR-FINAL-SPEC.md` (788 lines)
- `docs/DOPEMUX-MULTI-AI-ORCHESTRATOR-DESIGN.md` (749 lines)
- `claudedocs/dopemux-orchestrator-roadmap.md` (1,408 lines)

### Technical Deep-Dives
- `claudedocs/dope-context-ultrathink-summary-2025-10-16.md` (570 lines)
- `services/dope-context/PRODUCTION_IMPROVEMENTS.md` (660 lines)

---

## 🎓 ADHD Optimization Features

### Built Into Plan
1. **Focus Blocks**: 25-minute work sessions with clear break points
2. **Complexity Scoring**: 0.0-1.0 scale for cognitive load estimation
3. **Energy Matching**: Low/Medium/High energy requirements per step
4. **Progressive Complexity**: Steps ordered from simple → complex
5. **Context Switching**: Warnings for high-risk steps (Step 3)
6. **One-Agent-Per-Day**: Recommendation for Step 3 implementation

### Built Into System
1. **Auto-Save**: 30-second checkpoints prevent 23-minute recovery cost
2. **Adaptive Layouts**: 2-4 panes based on energy state
3. **Gentle Re-orientation**: "Where you left off" summaries
4. **Progressive Disclosure**: 3-tier information architecture
5. **Visual Progress**: Clear status indicators throughout

---

## 🔗 ConPort Integration

### Plan Retrieval
```python
# Get the full plan anytime
plan = mcp__conport__get_custom_data(
    workspace_id="/Users/hue/code/dopemux-mvp",
    category="implementation_plans",
    key="orchestrator_phase1_roadmap"
)

# Parse for current step
current_step = plan["value"]["steps"][0]  # Step 1
print(f"Next: {current_step['name']}")
print(f"Files: {current_step['files']}")
print(f"Time: {current_step['minutes']} minutes")
```

### Progress Tracking
```python
# Log progress for each step
mcp__conport__log_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    status="IN_PROGRESS",
    description=f"Step 1: {current_step['name']}",
    linked_item_type="custom_data",
    linked_item_id="orchestrator_phase1_roadmap"
)

# Update when complete
mcp__conport__update_progress(
    workspace_id="/Users/hue/code/dopemux-mvp",
    progress_id=task_id,
    status="DONE"
)
```

---

## 🎯 Next Actions

### Immediate
1. ✅ Plan extracted and saved to ConPort
2. ✅ Reference file created (`claudedocs/ORCHESTRATOR_IMPLEMENTATION_PLAN.md`)
3. ⏳ Ready to start Step 1 when you're ready

### When Ready to Code
1. Read Step 1 details from ConPort
2. Create file structure
3. Implement with 25-minute focus sessions
4. Validate with provided test commands
5. Log decision and progress to ConPort
6. Move to Step 2

---

## 📈 Success Metrics

### Per Step
- ✅ All tests pass (>90% coverage)
- ✅ Validation commands succeed
- ✅ Complexity within estimate (±20%)
- ✅ Time within estimate (±30%)

### Phase 1 Complete
- ✅ All 7 steps complete
- ✅ End-to-end workflow tested
- ✅ ADHD features validated
- ✅ Documentation updated
- ✅ Ready for user testing

---

**Status**: 📦 **PLAN READY** - All steps defined, validated, and trackable via ConPort

**ConPort ID**: `implementation_plans/orchestrator_phase1_roadmap`
**Related Decisions**: #71, #72, #73, #75
**Research Foundation**: 120,000 words, 87% confidence
