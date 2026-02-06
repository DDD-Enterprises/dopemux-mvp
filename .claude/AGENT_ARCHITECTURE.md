# Dopemux Agent Architecture (Revised)

**Version**: 2.0.0
**Date**: 2025-10-04
**Status**: Validated design ready for implementation
**Revision**: Corrected persona understanding from investigation

---

## Executive Summary

**Total Agents**: 7 infrastructure agents
**Execution Layer**: Claude Code with 16+ dopemux-enhanced persona guidelines
**Integration**: Agents support Claude's persona-guided behavior
**Timeline**: 14-15 weeks implementation

**Key Revision**: Personas are NOT separate agents - they are behavioral guidelines that Claude Code applies contextually. The 7 agents provide infrastructure support for ADHD accommodations, compliance enforcement, and tool orchestration.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: User Commands                                          │
│  /dx:implement, /dx:analyze, /dx:review, etc.                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│  Layer 1: Claude Code (Execution with Persona Guidelines)        │
│                                                                   │
│  Claude applies behavioral guidelines from persona docs:          │
│  - Python Expert → Python implementation patterns                 │
│  - System Architect → Architecture design patterns               │
│  - Quality Engineer → Testing and validation patterns            │
│  - Root Cause Analyst → Debugging and investigation patterns     │
│  [16+ personas total]                                            │
│                                                                   │
│  Personas are behavioral modes, NOT separate agent instances     │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│  Layer 2: Specialized Capability Agents (3)                      │
│  ┌──────────────────┬──────────────────┬──────────────────┐    │
│  │ DopemuxEnforcer  │ ToolOrchestrator │ Workflow         │    │
│  │ Architecture     │ MCP Selection    │ Coordinator      │    │
│  │ Compliance       │ Performance Opt  │ Multi-Step       │    │
│  └──────────────────┴──────────────────┴──────────────────┘    │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│  Layer 3: Infrastructure Agents (4)                              │
│  ┌──────────┬────────────┬──────────────┬─────────────────┐    │
│  │ Memory   │ Cognitive  │ TwoPlane     │ Task            │    │
│  │ Agent    │ Guardian   │ Orchestrator │ Decomposer      │    │
│  │ Context  │ ADHD       │ Cross-Plane  │ Planning        │    │
│  │ Preserve │ Support    │ Coordination │ Breakdown       │    │
│  └──────────┴────────────┴──────────────┴─────────────────┘    │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│  Layer 4: Tools (MCP Servers)                                    │
│  Zen, ConPort, Serena, PAL apilookup, GPT-Researcher, Exa,            │
│  Magic, Playwright, DopeconBridge, Leantime API             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Critical Understanding: Personas vs Agents

### What Personas ARE

**Personas = Behavioral Guidelines for Claude Code**

Personas are documentation sections in `~/.claude/CLAUDE.md` that describe specialized approaches:

```markdown
## Python Expert Persona

When handling Python tasks, apply these patterns:
- Use type hints and dataclasses
- Follow PEP 8 with Black formatting
- Write pytest tests with fixtures
- Use Serena MCP for code navigation
- Log design decisions to ConPort
```

When Claude encounters a Python implementation task, it **applies** Python Expert guidelines contextually - it doesn't "activate a separate Python Expert agent".

### What Personas ARE NOT

❌ **NOT separate agent instances** to delegate to
❌ **NOT discrete activation system** with agent-to-agent communication
❌ **NOT part of the 7-agent architecture**

### How This Changes Our Understanding

**Before (Incorrect Assumption)**:
```
User → /dx:implement → Activate Python Expert Agent → Agent delegates to Infrastructure Agents → Tools
```

**After (Correct Reality)**:
```
User → /dx:implement → Claude applies Python Expert guidelines → Coordinates with Infrastructure Agents → Tools
```

**Implication**: We don't build "persona agents". We enhance persona guidelines with dopemux knowledge and build infrastructure agents that support Claude's work.

---

## The 7 Infrastructure Agents

### Infrastructure Layer (4 Agents)

#### 1. MemoryAgent - Context Preservation Authority

**Purpose**: Solve #1 ADHD pain point (context loss across interruptions)

**Authority**: Exclusive ConPort data management

**Capabilities**:
- Auto-save context every 30 seconds during active work
- Restore mental model after interruptions
- Track session state (current focus, next steps, time invested)
- Maintain decision history and knowledge graph

**Integration with Personas**:
```python
# Claude (applying Python Expert) coordinates with MemoryAgent

# During implementation
async def implement_feature():
    # Claude applies Python Expert patterns
    code = await write_implementation()

    # MemoryAgent auto-saves (background)
    await memory_agent.save_checkpoint(
        context="Implementing JWT auth",
        code_state=code,
        next_steps=["Add tests", "Update docs"]
    )
```

**ADHD Benefit**: User never loses context, can interrupt and resume safely

---

#### 2. CognitiveGuardian - ADHD Support

**Purpose**: Unified ADHD monitoring and guidance

**Components** (internal, not separate agents):
- FocusMonitor: Session tracking, drift detection
- GuidanceEngine: Content transformation, gentle re-orientation
- CognitiveLoadEstimator: 5-factor complexity scoring

**Capabilities**:
- Attention state detection (focused, scattered, hyperfocus)
- Break reminders (25-min intervals, mandatory at 90 min)
- Complexity warnings (task requires focus, schedule dedicated time)
- Gentle re-orientation after interruptions
- Progress visualization

**Integration with Personas**:
```python
# Claude (applying System Architect) checks with CognitiveGuardian

async def design_architecture():
    # Check if user is ready for complex task
    readiness = await cognitive_guardian.check_readiness()

    if not readiness.ready:
        return {
            "message": "⚠️ Architecture design needs focus (complexity 0.8)",
            "suggestion": "Current state: scattered. Try quick task first?",
            "alternatives": ["Debug simple bug", "Update documentation"]
        }

    # Proceed with design, CognitiveGuardian monitors
    design = await create_architecture_design()

    # CognitiveGuardian triggers break reminder at 25 min
```

**ADHD Benefit**: Prevents burnout, maintains attention quality, protects health

---

#### 3. TwoPlaneOrchestrator - Cross-Plane Coordination

**Purpose**: Enforce two-plane architecture boundaries

**Authority**: DopeconBridge coordination, authority enforcement

**Capabilities**:
- Route cross-plane requests through DopeconBridge
- Validate authority matrix (ConPort for decisions, Leantime for status)
- Audit cross-plane communication
- Resolve conflicts between planes

**Integration with Personas**:
```python
# Claude (applying DevOps Architect) routes through TwoPlaneOrchestrator

async def deploy_service():
    # DevOps work (Cognitive Plane)
    deployment_config = await create_deployment_config()

    # Need to update task status (PM Plane)
    # Route through TwoPlaneOrchestrator
    await two_plane_orchestrator.update_task_status(
        task_id="TASK-123",
        status="deployed",
        source="cognitive_plane"
    )
    # → Orchestrator validates authority, routes to Leantime
```

**ADHD Benefit**: Clear boundaries reduce confusion, prevent cross-plane conflicts

---

#### 4. TaskDecomposer - ADHD-Optimized Planning

**Purpose**: Break complex tasks into 15-90 minute chunks

**Tools**: Zen/planner for decomposition, ConPort for storage

**Capabilities**:
- PRD parsing and decomposition
- ADHD metadata (complexity 0-1, energy low/med/high)
- Dependency visualization
- Break point suggestions
- Human review gate (catch errors before import)

**Integration with Personas**:
```python
# Claude (applying Requirements Analyst) uses TaskDecomposer

async def parse_prd(prd_file: str):
    # Requirements Analyst analyzes PRD
    requirements = await analyze_requirements(prd_file)

    # TaskDecomposer breaks into ADHD-sized chunks
    tasks = await task_decomposer.decompose(
        requirements=requirements,
        chunk_size_min=15,
        chunk_size_max=90,
        adhd_optimized=True
    )

    # Returns tasks with metadata:
    # [{
    #   "description": "Implement JWT token generation",
    #   "complexity": 0.6,
    #   "energy_required": "medium",
    #   "estimated_minutes": 45,
    #   "break_points": [25]
    # }, ...]
```

**ADHD Benefit**: All tasks are manageable size, energy-matched, with break plans

---

### Specialized Capability Layer (3 Agents)

#### 5. DopemuxEnforcer - Architectural Compliance

**Purpose**: Validate dopemux-specific architecture rules

**Unique Value**: SuperClaude personas know general best practices, DopemuxEnforcer knows dopemux-specific architecture

**Validation Rules**:
1. Two-plane boundary enforcement (no direct cross-plane)
2. Authority matrix compliance (correct system for each operation)
3. ADHD constraint validation (max 10 results, progressive disclosure)
4. Tool preference enforcement (Serena > bash for code)

**Integration with Personas**:
```python
# Claude (applying Python Expert) validated by DopemuxEnforcer

async def implement_feature():
    # Python Expert creates implementation
    code = await write_python_code()

    # DopemuxEnforcer validates compliance
    compliance = await dopemux_enforcer.validate_change(code)

    if not compliance.compliant:
        # Show warnings
        for violation in compliance.violations:
            print(f"⚠️ {violation.severity}: {violation.message}")

        # Critical violations block
        if compliance.blocking:
            return "Fix critical violations before proceeding"

    # Non-critical warnings logged to ConPort
    await log_warnings(compliance.warnings)
```

**ADHD Benefit**: Gentle guidance, non-blocking warnings, builds good habits

---

#### 6. ToolOrchestrator - Intelligent MCP Selection

**Purpose**: Select optimal MCP servers based on task requirements

**Optimization Factors**:
- Task complexity (simple → gpt-5-mini, complex → o3-mini)
- Performance metrics (latency, success rate, cost)
- Context (caching, rate limits, current tool state)

**Integration with Personas**:
```python
# Claude (any persona) uses ToolOrchestrator for tool selection

async def handle_task(task: Task):
    # ToolOrchestrator selects optimal tools
    tools = await tool_orchestrator.select_tools_for_task(task)

    # Returns: {
    #   "analysis": {"primary": "zen", "method": "thinkdeep", "model": "gpt-5"},
    #   "documentation": {"primary": "PAL apilookup", "fallback": "exa"},
    #   "code_nav": {"primary": "serena", "fallback": None}  # Required
    # }

    # Execute with selected tools
    result = await execute_with_tools(task, tools)
```

**ADHD Benefit**: Invisible optimization, user gets best tools without thinking

---

#### 7. WorkflowCoordinator - Multi-Step Orchestration

**Purpose**: Coordinate complex multi-step workflows

**Workflow Types**:
- Feature implementation → Design → Code → Test → Document
- Bug investigation → Reproduce → Debug → Fix → Test → PR
- Architecture decision → Research → Design → Consensus → Document

**Integration with Personas**:
```python
# Claude uses WorkflowCoordinator for complex workflows

async def feature_workflow(feature_description: str):
    workflow = workflow_coordinator.get_workflow("feature_implementation")

    for step in workflow.steps:
        # Step 1: Design (System Architect persona)
        if step.type == "design":
            design = await apply_persona("system_architect", step.task)

        # Step 2: Implement (Python Expert persona)
        elif step.type == "implement":
            # Check readiness (CognitiveGuardian)
            ready = await cognitive_guardian.check_readiness()
            if ready:
                code = await apply_persona("python_expert", step.task)

        # Step 3: Test (Quality Engineer persona)
        elif step.type == "test":
            tests = await apply_persona("quality_engineer", step.task)

        # Step 4: Validate (DopemuxEnforcer)
        elif step.type == "validate":
            compliance = await dopemux_enforcer.validate(code)

        # Auto-checkpoint after each step (MemoryAgent)
        await memory_agent.save_checkpoint(step.name)
```

**ADHD Benefit**: Breaks complex workflows into manageable steps with automatic checkpointing

---

## How Personas and Agents Work Together

### Execution Flow Example

**User Request**: `/dx:implement auth feature`

```python
# 1. Command parser loads /dx:implement pattern
workflow = load_command_pattern("dx:implement")

# 2. Claude applies appropriate persona based on task
# (Python implementation → Python Expert guidelines)

# 3. CognitiveGuardian checks readiness
readiness = await cognitive_guardian.check_readiness()

if readiness.ready:
    # 4. ToolOrchestrator selects optimal tools
    tools = await tool_orchestrator.select_tools({
        "type": "implementation",
        "language": "python",
        "complexity": 0.6
    })
    # → Returns: Serena (code), PAL apilookup (docs), Zen (analysis)

    # 5. Claude (as Python Expert) implements
    # Uses Python Expert tool preferences:
    # - Serena for code navigation
    # - ConPort for decision logging
    # - PAL apilookup for JWT patterns

    code = await implement_with_tools(tools)

    # 6. MemoryAgent auto-saves (background, every 30s)
    await memory_agent.auto_save()

    # 7. DopemuxEnforcer validates compliance
    compliance = await dopemux_enforcer.validate(code)

    # 8. If 25+ minutes, CognitiveGuardian suggests break
    if duration > 25:
        await cognitive_guardian.suggest_break()

else:
    # User not ready for complex task
    await cognitive_guardian.suggest_alternatives()
```

### Persona Enhancement Requirements

For personas to work effectively with agents, each needs:

1. **Tool Preferences** (for ToolOrchestrator validation):
   ```markdown
   - Code navigation → Serena MCP (NEVER bash)
   - Decisions → ConPort (ALWAYS log)
   - Documentation → PAL apilookup (official docs)
   ```

2. **Two-Plane Awareness** (for TwoPlaneOrchestrator routing):
   ```markdown
   - Cognitive Plane: Serena, ConPort
   - PM Plane: Leantime, Task-Master (route through bridge)
   ```

3. **ADHD Accommodations** (for CognitiveGuardian integration):
   ```markdown
   - Progressive disclosure (essential → details)
   - Complexity scoring (use Serena 0.0-1.0)
   - Break reminders (>0.7 complexity → break every 25 min)
   ```

4. **Usage Tracking** (for validation and optimization):
   ```python
   # Log persona application
   await track_persona_usage("python_expert", task_type="implementation")
   ```

---

## Comparison: Before vs After Understanding

| Aspect | Before (Incorrect) | After (Correct) |
|--------|-------------------|-----------------|
| **Persona Nature** | Separate agent instances | Behavioral guidelines for Claude |
| **Persona Count** | 16+ agents to build | 16+ docs to enhance |
| **Execution Layer** | Persona agents | Claude with persona patterns |
| **Infrastructure Agents** | 7 agents | 7 agents (unchanged) |
| **Total Agents** | 23+ (16 personas + 7 infrastructure) | 7 (infrastructure only) |
| **Implementation Effort** | 30+ weeks (23 agents) | 14-15 weeks (7 agents) |
| **Duplication** | High (persona agents duplicate Claude's capabilities) | None (personas guide Claude's behavior) |
| **Coordination Overhead** | High (23 agent instances) | Low (7 agent instances) |
| **ADHD Cognitive Load** | High (which agent to use?) | Low (invisible support) |

---

## Implementation Timeline

**Total**: 14-15 weeks

### Weeks 1-2: Agent Framework
- Base agent class
- Event bus (Redis Pub/Sub)
- Agent registry
- Communication protocols

### Weeks 3-5: Infrastructure Tier 1
- MemoryAgent (Week 3)
- CognitiveGuardian (Weeks 4-5)

### Weeks 6-7: Infrastructure Tier 2
- TwoPlaneOrchestrator (Week 6)
- DopemuxEnforcer (Week 7)

### Weeks 8-10: Specialized Capabilities
- ToolOrchestrator (Week 8)
- TaskDecomposer (Week 9)
- WorkflowCoordinator (Week 10)

### Weeks 11-13: Integration & Testing
- Agent-to-agent communication testing
- Persona integration testing
- ADHD accommodation validation
- Performance tuning

### Weeks 14-15: Deployment
- Production configuration
- Monitoring setup
- Documentation finalization
- User training

---

## Success Metrics

### Agent Performance
- Agent coordination: <150ms (vs <200ms target)
- Memory operations: <5ms (vs <20ms target)
- Compliance validation: <10ms

### ADHD Effectiveness
- Cognitive load: <0.3 (vs <0.5 target)
- Task completion rate: >85%
- Context preservation: 100% (no lost work)
- Break compliance: >90%

### Architecture Quality
- Two-plane violations: 0
- Authority violations: 0
- Tool adherence: 100% (Serena for code, ConPort for decisions)

### Persona Integration
- Persona guidelines enhanced: 16/16 (100%)
- Usage tracking coverage: 100%
- Dopemux awareness: 100%

---

## Next Steps

1. **Enhance All Personas** (2-3 weeks):
   - Apply Python Expert template to remaining 15 personas
   - Add dopemux tool preferences
   - Add two-plane awareness
   - Add ADHD accommodations
   - Add usage tracking patterns

2. **Implement Persona Tracking** (1 week):
   - Update /dx: commands with tracking
   - Create ConPort schema
   - Implement validation queries

3. **Build 7 Agents** (14-15 weeks):
   - Follow implementation timeline
   - Test integration with persona-enhanced Claude
   - Validate ADHD accommodations

---

**Status**: Architecture validated, ready for implementation
**Key Learning**: Personas are behavioral patterns, not agent instances
**Impact**: Simpler architecture, faster implementation, better ADHD support
