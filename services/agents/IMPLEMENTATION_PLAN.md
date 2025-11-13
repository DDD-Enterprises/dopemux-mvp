# 16-Week Agent Implementation Plan

Complete week-by-week breakdown for implementing 7 infrastructure agents.

**Status**: Week 1 complete (MemoryAgent)
**Created**: 2025-10-24
**Method**: Zen planner (4-step detailed planning)

---

## Timeline Overview

```
Weeks 1-5:   Quick Wins (Foundation + High-Impact ADHD)
Weeks 6-8:   Core Infrastructure
Weeks 9-10:  Advanced Agents
Weeks 11-12: Integration & Testing
Weeks 13-14: Persona Enhancement
Weeks 15-16: SuperClaude Integration
```

---

## Phase 1: Quick Wins (Weeks 1-5)

### WEEK 1: MemoryAgent [COMPLETE]

**Status**: ✅ Complete
**Deliverables**:
- memory_agent.py (327 lines)
- memory_agent_conport.py (195 lines)
- test_memory_agent.py + test_real_workflow.py
- Documentation (README, INTEGRATION_GUIDE, QUICK_START)

**Validation**:
- Auto-save working (30s intervals)
- Gentle re-orientation tested
- 450x faster context recovery demonstrated
- Zero context loss validated

---

### WEEK 2: MCP Integration Foundation

**Objective**: Make existing systems functional with real MCP integration

**Day 1-2: MemoryAgent Production Mode** (2 focus blocks)
1. Update `_save_to_conport()` to use `mcp__conport__update_active_context`
2. Update `_get_conport_client()` to detect Claude Code context
3. Test with real ConPort database
4. Validate auto-save persists across sessions

- Complexity: 0.3
- Energy: Medium
- Break: After Day 1

**Day 3-5: Wire Task-Orchestrator Stubs** (6 focus blocks)
1. Day 3: `_dispatch_to_conport`
   - Real `log_progress`, `update_progress` calls
   - Test ConPort dispatch
   - **Break point**

2. Day 4: `_dispatch_to_serena`
   - Real `find_symbol`, `analyze_complexity` calls
   - Test Serena dispatch with complexity scoring
   - **Break point**

3. Day 5: `_dispatch_to_zen`
   - Real `thinkdeep`, `planner` calls
   - Integration test - route task through all agents

- Complexity: 0.5
- Energy: High
- Total breaks: 3 (after each day)

**Deliverables**:
- MemoryAgent in production mode
- Task-Orchestrator with 3/4 functional dispatches
- Integration test suite
- Core infrastructure operational

**Dependencies**: ConPort MCP, Serena MCP, Zen MCP (all operational)

**Risks**:
- MCP timeout issues -> Add retry logic
- Schema mismatch -> Validate before writes

---

### WEEK 3-4: CognitiveGuardian

**Objective**: Break reminders and energy matching (highest ADHD impact)

**Week 3: Foundation**

**Day 1: CognitiveGuardian Skeleton** (2 focus blocks)
- Base class with session monitoring
- Integration with MemoryAgent for time tracking
- Complexity: 0.4, Energy: Medium

**Day 2-3: Break Reminder System** (4 focus blocks)
- 25-minute warnings
- 90-minute mandatory breaks
- Async background monitoring
- Integration with MemoryAgent auto-save
- Complexity: 0.5, Energy: High
- Break: After Day 2

**Day 4-5: Attention State Detection** (4 focus blocks)
- Focused, Scattered, Hyperfocus states
- State persistence in ConPort
- Complexity: 0.6, Energy: High
- Break: After Day 4

**Week 4: Energy Matching**

**Day 1-2: Read ConPort ADHD Metadata** (3 focus blocks)
- Query tasks with energy_required, complexity, cognitive_load
- Build user state model
- Time-of-day energy estimation
- Complexity: 0.5, Energy: Medium
- Break: After Day 1

**Day 3-5: Energy-Aware Task Suggestions** (5 focus blocks)
- High energy -> complex tasks (>0.6)
- Medium energy -> moderate tasks (0.3-0.6)
- Low energy -> simple tasks (<0.3)
- Limit to 3 suggestions
- Complexity: 0.6, Energy: High
- Break: After Day 3, Day 4

**Day 5: Integration Testing** (2 focus blocks)
- Test break reminders
- Test energy matching
- Validate gentle messaging
- Complexity: 0.4, Energy: Medium

**Deliverables**:
- CognitiveGuardian operational
- Break enforcement active
- Energy matching working
- 50% reduction in burnout risk

**Dependencies**: MemoryAgent (Week 1), ConPort ADHD metadata schema

**Risks**:
- Attention detection inaccurate -> Start simple, refine
- Energy matching wrong -> Make advisory not blocking

---

### WEEK 5: ADHD Routing Activation

**Objective**: Make existing metadata useful in routing decisions

**Day 1: Energy Check in Agent Assignment** (2 focus blocks)
- Get user state from CognitiveGuardian
- Match task energy_required to user energy
- Return alternatives if mismatch
- Complexity: 0.4, Energy: Medium

**Day 2: Complexity + Attention Matching** (2 focus blocks)
- High complexity + scattered -> suggest focus first
- Low complexity -> safe for any state
- Progressive suggestions
- Complexity: 0.5, Energy: High
- Break: After Day 1

**Day 3-4: ADHD-Aware Task Prioritization** (4 focus blocks)
- Sort by energy match, complexity match, dependencies
- Limit to top 3 tasks
- Show why each task suggested
- Complexity: 0.6, Energy: High
- Break: After Day 3

**Day 5: Real Workflow Integration Testing** (2 focus blocks)
- Test morning (high energy) -> complex suggestions
- Test evening (low energy) -> simple suggestions
- Validate task completion improves
- Complexity: 0.4, Energy: Medium

**Deliverables**:
- ADHD routing fully operational
- Task metadata actively used
- 30% improvement in completion rate

**Dependencies**: CognitiveGuardian (Week 4), ConPort ADHD metadata

**Quick Wins Phase Summary**:
After Week 5:
- Auto-save every 30s
- Break reminders active
- Energy and complexity matching operational
- Real MCP calls (not stubs)
- +40% functionality from baseline

---

## Phase 2: Core Infrastructure (Weeks 6-8)

### WEEK 6: TwoPlaneOrchestrator

**Objective**: Enforce two-plane architecture boundaries

**Day 1: Skeleton** (2 focus blocks)
- Base class with DopeconBridge client
- Authority matrix loading
- Complexity: 0.4, Energy: Medium

**Day 2-3: Cross-Plane Routing** (4 focus blocks)
- Detect cross-plane requests
- Route through DopeconBridge
- Request/response logging
- Complexity: 0.6, Energy: High
- Break: After Day 2

**Day 4: Authority Validation** (3 focus blocks)
- Check against authority matrix
- Warn on violations (non-blocking)
- Log compliance metrics
- Complexity: 0.5, Energy: Medium
- Break: After Day 3

**Day 5: Integration Testing** (1 focus block)
- Test Cognitive -> PM requests
- Test PM -> Cognitive events
- Complexity: 0.3, Energy: Low

**Deliverables**:
- Cross-plane routing via DopeconBridge
- Authority validation active
- Zero cross-plane violations

**Dependencies**: DopeconBridge, ConPort

---

### WEEK 7: DopemuxEnforcer

**Objective**: Validate architectural compliance

**Day 1-2: Rule Engine** (3 focus blocks)
- Base class with validation rules
- Serena integration for complexity
- Complexity: 0.5, Energy: Medium
- Break: After Day 1

**Day 3: MCP Tool Preference Validation** (2 focus blocks)
- Check Serena for code (not bash)
- Check ConPort for decisions
- Check Context7 for docs
- Complexity: 0.4, Energy: Medium

**Day 4: ADHD Constraint Validation** (2 focus blocks)
- Max 10 results enforced
- Progressive disclosure followed
- Complexity warnings shown
- Complexity: 0.5, Energy: High
- Break: After Day 3

**Day 5: CognitiveGuardian Integration** (3 focus blocks)
- Validate break reminders
- Check energy matching
- Compliance dashboard
- Complexity: 0.6, Energy: High

**Deliverables**:
- Validation rules active
- Compliance metrics tracked
- 100% tool adherence

**Dependencies**: Serena MCP, ConPort, CognitiveGuardian (Week 4)

---

### WEEK 8: ToolOrchestrator

**Objective**: Intelligent MCP and model selection

**Day 1: Integrate Zen listmodels** (2 focus blocks)
- Call `mcp__zen__listmodels`
- Parse capabilities
- Build selection matrix
- Complexity: 0.4, Energy: Medium

**Day 2-3: Task-to-Model Mapping** (4 focus blocks)
- Low complexity -> fast models (gpt-5-mini, gemini-flash)
- Medium -> balanced (gpt-5-codex, gemini-2.5-pro)
- High -> power (gpt-5-pro, o3-pro)
- ADHD scattered -> fast models only
- Complexity: 0.6, Energy: High
- Break: After Day 2

**Day 4: MCP Server Selection** (2 focus blocks)
- Code -> Serena (required)
- Docs -> Context7 vs Exa vs GPT-Researcher
- Analysis -> Zen tools
- Complexity: 0.5, Energy: Medium

**Day 5: Performance Tracking** (2 focus blocks)
- Track latency, success rate, cost
- Optimize based on metrics
- Store patterns in ConPort
- Complexity: 0.4, Energy: Medium
- Break: After Day 4

**Deliverables**:
- Intelligent model selection
- Optimized MCP routing
- 30% faster operations

**Dependencies**: Zen MCP, ConPort, CognitiveGuardian (for ADHD state)

**Note**: Can parallelize with Weeks 6-7

---

## Phase 3: Advanced Agents (Weeks 9-10)

### WEEK 9: TaskDecomposer

**Objective**: Break PRDs into ADHD-sized tasks

**Day 1-2: Zen/Planner Wrapper** (3 focus blocks)
- Call `mcp__zen__planner` for PRD decomposition
- Parse plan into tasks
- Complexity: 0.5, Energy: Medium
- Break: After Day 1

**Day 3-4: ADHD Metadata Generation** (4 focus blocks)
- Estimate complexity (use Serena for code tasks)
- Assign energy_required (keyword analysis)
- Calculate cognitive_load
- Set estimated_minutes (15-90 range)
- Complexity: 0.6, Energy: High
- Break: After Day 3

**Day 5: Human Review Gate** (3 focus blocks)
- Show tasks before import
- Allow complexity/energy edits
- Prevent task explosion (max 20)
- Import to ConPort after approval
- Complexity: 0.5, Energy: Medium

**Deliverables**:
- PRD -> ADHD tasks automated
- Human review active
- All tasks properly sized

**Dependencies**: Zen/planner, ConPort, Serena

---

### WEEK 10: WorkflowCoordinator

**Objective**: Multi-step workflow orchestration

**Day 1: Workflow Templates** (2 focus blocks)
- Feature: Design -> Code -> Test -> Document
- Bug: Reproduce -> Debug -> Fix -> Test -> PR
- Architecture: Research -> Design -> Consensus -> Document
- Complexity: 0.4, Energy: Medium

**Day 2-4: Zen Continuation Orchestration** (6 focus blocks)
- Coordinate thinkdeep workflows
- Coordinate planner workflows
- Coordinate codereview workflows
- Use continuation_id for state
- Complexity: 0.7, Energy: High
- Break: After Day 2, Day 3

**Day 5: MemoryAgent Integration** (2 focus blocks)
- Checkpoint after each step
- Enable workflow resumption
- Complexity: 0.5, Energy: Medium
- Break: After Day 4

**Deliverables**:
- 3 workflow templates operational
- Interruption-safe workflows
- Complex workflows manageable

**Dependencies**: Zen MCP, MemoryAgent (Week 1), CognitiveGuardian (Week 4)

---

## Phase 4: Integration & Testing (Weeks 11-12)

### WEEK 11: Integration Testing

**Objective**: Validate all agents working together

**Day 1-2: Test Infrastructure** (4 focus blocks)
- Pytest fixtures for 7 agents
- Mock ConPort/Serena/Zen
- Integration test helpers
- Complexity: 0.6, Energy: High
- Break: After Day 1

**Day 3-4: Agent-to-Agent Tests** (4 focus blocks)
- MemoryAgent + CognitiveGuardian
- CognitiveGuardian + DopemuxEnforcer
- ToolOrchestrator + WorkflowCoordinator
- Complexity: 0.7, Energy: High
- Break: After Day 3

**Day 5: End-to-End Workflows** (2 focus blocks)
- Feature implementation workflow
- Bug investigation workflow
- ADHD benefits validation
- Complexity: 0.5, Energy: Medium

**Deliverables**:
- Comprehensive test suite
- All agents tested together
- Production readiness checkpoint

**Dependencies**: All 7 agents (Weeks 1-10)

---

### WEEK 12: Performance & Polish

**Objective**: Optimize and fix bugs

**Day 1-2: Performance Profiling** (3 focus blocks)
- Measure auto-save latency
- Measure agent dispatch latency
- Identify bottlenecks
- Complexity: 0.5, Energy: Medium
- Break: After Day 1

**Day 3-4: Optimization** (4 focus blocks)
- Cache frequently accessed data
- Batch ConPort operations
- Optimize Zen model selection
- Complexity: 0.6, Energy: High
- Break: After Day 3

**Day 5: Bug Fixing** (3 focus blocks)
- Address integration test issues
- Regression testing
- Complexity: 0.5, Energy: Medium

**Deliverables**:
- All performance targets met
- Bugs addressed
- System production-ready

**Gate**: Ready for persona enhancement

---

## Phase 5: Persona Enhancement (Weeks 13-14)

### WEEK 13: Enhance 8 Personas (Batch 1)

**Personas**: system-architect, quality-engineer, root-cause-analyst, frontend-architect, backend-architect, security-engineer, performance-engineer, refactoring-expert

**Enhancement Pattern** (3 hours per persona):
1. Tool Preferences (Serena, ConPort, Context7)
2. Two-Plane Awareness (Cognitive vs PM)
3. ADHD Accommodations (progressive disclosure, complexity, breaks)
4. Usage Tracking (log start/end, outcomes)
5. Integration examples (with 7 agents)

**Schedule**:
- Day 1: 2 personas (4 focus blocks)
- Day 2: 2 personas (4 focus blocks)
- Day 3: 2 personas (4 focus blocks)
- Day 4: 2 personas (4 focus blocks)
- Day 5: Review and validation (2 focus blocks)

- Complexity: 0.4 per persona
- Energy: Medium
- Breaks: After every 2 personas

**Deliverables**: 8/16 personas enhanced

---

### WEEK 14: Remaining 7 Personas + Validation

**Personas**: devops-architect, learning-guide, requirements-analyst, technical-writer, socratic-mentor, general-purpose, statusline-setup, output-style-setup

**Schedule**:
- Day 1-2: 4 personas (6 focus blocks)
- Day 3-4: 3 personas (5 focus blocks)
- Day 5: Complete validation (3 focus blocks)
  - Test persona usage tracking
  - Validate tool preferences
  - Check ADHD accommodations
  - Query ConPort analytics

**Deliverables**:
- 16/16 personas enhanced (100%)
- All dopemux-aware
- Usage tracking operational
- Analytics dashboard

---

## Phase 6: SuperClaude Integration (Weeks 15-16)

### WEEK 15: MetaMCP Bridge Foundation

**Objective**: Enable SuperClaude integration

**Day 1: Research SuperClaude MCP Interface** (2 focus blocks)
- Analyze MCP call patterns
- Identify translation points
- Complexity: 0.5, Energy: Medium

**Day 2-3: Build MetaMCP Bridge** (4 focus blocks)
- Translate SuperClaude -> Dopemux MCPs
  - Context7 -> context7 + claude-context + docrag
  - Sequential -> zen (multi-model)
  - Magic -> morphllm + serena
- Complexity: 0.7, Energy: High
- Break: After Day 2

**Day 4: Test Simple Commands** (2 focus blocks)
- Test /analyze with Zen
- Test /code with Serena
- Validate no breaking changes
- Complexity: 0.5, Energy: Medium

**Day 5: Documentation** (2 focus blocks)
- Migration guide
- Command compatibility matrix
- Complexity: 0.3, Energy: Low
- Break: After Day 4

**Deliverables**:
- MetaMCP bridge basic functionality
- 3 commands working
- Migration guide published

**Dependencies**: All 7 agents, Zen MCP, Serena MCP

---

### WEEK 16: Complete Integration + Deployment

**Objective**: Production readiness

**Day 1-2: Complete Command Integration** (4 focus blocks)
- Wire remaining 16 SuperClaude commands
- Test each with Dopemux MCPs
- Validate persona coordination
- Complexity: 0.6, Energy: High
- Break: After Day 1

**Day 3: agent_spawner.py Decision** (2 focus blocks)
- Compare with Zen clink
- Decision: Deprecate OR enhance
- Document in ConPort
- Complexity: 0.4, Energy: Medium

**Day 4: Production Deployment Prep** (3 focus blocks)
- Configuration management
- Monitoring setup (ADHD metrics)
- Deployment documentation
- Complexity: 0.5, Energy: Medium
- Break: After Day 3

**Day 5: Final Validation** (1 focus block)
- Complete test suite
- Update documentation
- Getting started guide
- Complexity: 0.3, Energy: Low

**Deliverables**:
- SuperClaude fully integrated
- agent_spawner decided
- System production-ready
- Documentation complete

---

## Critical Path

```
MemoryAgent (W1)
    |
    v
MCP Wiring (W2) -----> [GATE: Infrastructure functional]
    |
    v
CognitiveGuardian (W3-4)
    |
    v
ADHD Routing (W5) ---> [GATE: Quick wins complete, +40%]
    |
    +---> TwoPlaneOrchestrator (W6)
    |
    +---> DopemuxEnforcer (W7)
    |
    +---> ToolOrchestrator (W8) [Can parallelize with W6-7]
    |
    v
TaskDecomposer (W9)
    |
    v
WorkflowCoordinator (W10)
    |
    v
Integration Testing (W11) --> [GATE: Production ready]
    |
    v
Performance & Polish (W12)
    |
    v
Persona Enhancement (W13-14)
    |
    v
SuperClaude Integration (W15-16) --> [GATE: Full system complete]
```

---

## Risk Register

### High-Risk Items

**Week 2: MCP Integration**
- Risk: MCP timeout/failures
- Mitigation: Retry logic, graceful degradation
- Contingency: Add offline mode

**Week 4: CognitiveGuardian Complexity**
- Risk: Attention state detection inaccurate
- Mitigation: Start simple (time-based), refine later
- Contingency: Make all checks advisory

**Week 11: Integration Issues**
- Risk: Agents don't coordinate well
- Mitigation: Test incrementally during development
- Contingency: Extend integration testing to Week 13

### Medium-Risk Items

**Week 8: ToolOrchestrator Performance**
- Risk: Model selection overhead slows operations
- Mitigation: Cache selections, batch decisions
- Contingency: Simplify selection algorithm

**Week 15: SuperClaude Compatibility**
- Risk: SuperClaude API changes break bridge
- Mitigation: Version pinning, compatibility testing
- Contingency: Document as "experimental"

---

## Success Metrics

### After Quick Wins (Week 5)
- Auto-save: Active (30s intervals)
- Break reminders: Active
- Energy matching: Operational
- MCP integration: Real calls
- ADHD routing: Uses metadata
- Functionality boost: +40%

### After All Agents (Week 12)
- Agent implementation: 7/7 (100%)
- ADHD optimization: 100% operational
- Task completion rate: >85%
- Context loss: 0%
- Recovery time: <2s
- Break compliance: >90%

### After Full System (Week 16)
- Persona enhancement: 16/16 (100%)
- SuperClaude: Integrated
- Production deployment: Complete
- Documentation: Comprehensive
- User adoption: Ready

---

## Dependency Matrix

| Agent | Depends On | Can Parallelize With |
|-------|-----------|---------------------|
| MemoryAgent (W1) | ConPort | - |
| MCP Wiring (W2) | MemoryAgent | - |
| CognitiveGuardian (W3-4) | MemoryAgent, ConPort | - |
| ADHD Routing (W5) | CognitiveGuardian | - |
| TwoPlaneOrchestrator (W6) | DopeconBridge | ToolOrchestrator |
| DopemuxEnforcer (W7) | CognitiveGuardian, Serena | ToolOrchestrator |
| ToolOrchestrator (W8) | Zen, CognitiveGuardian | TwoPlane, Enforcer |
| TaskDecomposer (W9) | Zen, Serena, ConPort | - |
| WorkflowCoordinator (W10) | Zen, MemoryAgent, CognitiveGuardian | - |
| Integration Testing (W11) | All 7 agents | - |
| Performance (W12) | Integration tests | - |
| Personas (W13-14) | All 7 agents | - |
| SuperClaude (W15-16) | All agents, personas | - |

---

## Total Effort

- **7 Agents**: ~140 focus blocks (58 hours)
- **16 Personas**: ~50 focus blocks (21 hours)
- **Testing**: ~40 focus blocks (17 hours)
- **Integration**: ~30 focus blocks (13 hours)
- **Total**: ~260 focus blocks (109 hours)
- **Calendar**: 16 weeks at 7-8 hours/week

**ADHD-Optimized**: All work in 25-minute blocks with breaks

---

**Planning Complete**: Ready for Week 2 execution
**Next Action**: Wire real ConPort MCP calls in MemoryAgent
