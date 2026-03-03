---
id: runbook-extended-roadmap
title: Runbook — Extended Dopemux Activation Roadmap
type: runbook
owner: @hu3mann
last_review: 2025-09-24
next_review: 2025-12-24
tags: [adhd, roadmap, execution, detailed-planning]
related: [runbook-activation-plan, runbook-project-analysis-backup]
---

# Extended Dopemux Integration Activation Roadmap

## Planning Session Details
- **Extended Planning**: 7 steps completed
- **Continuation ID**: 1f3a6262-13a8-405a-938f-97ffc2f34640
- **Focus**: Comprehensive "Back on Track" strategy with ADHD optimizations

## Execution Priority Matrix

### HIGH IMPACT / LOW EFFORT (Start Here)
1. **Import Testing All Python Modules**
   - Quick diagnostic of environment
   - Reveals immediate blockers
   - No risk of breaking existing code

2. **Basic Instantiation Tests**
   - Test creating instances of core classes
   - Identifies construction/dependency issues
   - Fast feedback on what's actually working

3. **Documentation Audit**
   - Maps the landscape without code changes
   - Builds understanding with zero risk
   - Creates foundation for later decisions

### HIGH IMPACT / HIGH EFFORT (Plan Carefully)
1. **Session Persistence Debugging**
   - Core functionality but potentially complex
   - May require deep dependency investigation

2. **MCP Roles System Redesign**
   - You noted "implementation fundamentally wrong"
   - High impact but requires careful architectural work

3. **Integration Bridge Activation**
   - External dependencies involved
   - Requires coordination with external services

## Detailed Component Testing Strategy

### Session Manager Deep Dive (`src/dopemux/mcp/session_manager.py`)
```
Testing Sequence:
├── Pre-Investigation
│   ├── Check import without errors
│   └── Verify required dependencies (sqlite, json, etc.)
├── Basic Functionality
│   ├── Create SessionManager instance
│   └── Test basic methods (save, load, clear)
├── Save/Load Testing
│   ├── Test with minimal data structure
│   ├── Test with complex nested data
│   └── Test persistence across Python restarts
└── Integration Points
    ├── How it connects to ADHD systems
    └── How it communicates with MCP broker
```

### ADHD Systems Component Analysis

**Context Manager (`src/dopemux/adhd/context_manager.py`)**:
- Test: Can it track current context state?
- Test: Does it preserve context across interruptions?
- Integration: How does it interface with session persistence?

**Task Decomposer (`src/dopemux/adhd/task_decomposer.py`)**:
- Test: Can it break down complex tasks into 25-min chunks?
- Test: Does it generate proper task hierarchies?
- Integration: How does it feed data to attention monitor?

**Attention Monitor (`src/dopemux/adhd/attention_monitor.py`)**:
- Test: Does it track attention patterns?
- Test: Can it detect context switches?
- Integration: How does it coordinate with other ADHD systems?

### MCP System Integration Map

**Component Dependencies:**
- **Broker (`src/dopemux/mcp/broker.py`)**: Central coordination hub
  - Test: Message routing between MCP servers
  - Test: Graceful handling of server failures
  - Dependencies: session_manager, roles, observability

- **Roles (`src/dopemux/mcp/roles.py`)**: Permission and capability management
  - **CRITICAL**: You noted "implementation fundamentally wrong"
  - Deep dive needed: What specific problems are occurring?
  - Test: Role assignment and validation
  - Test: MetaMCP optimization integration

- **Observability (`src/dopemux/mcp/observability.py`)**: System monitoring
  - Test: System health tracking
  - Test: Useful debugging information provision
  - Integration: Should feed data to attention_monitor

### Integration Bridge Testing

**Leantime Bridge (`src/integrations/leantime_bridge.py`)**:
- Pre-Test: Verify Leantime instance availability
- Connection Test: Authentication and basic connectivity
- Data Flow Test: Task/project synchronization
- Error Handling: Connection failure management

**Taskmaster Bridge (`src/integrations/taskmaster_bridge.py`)**:
- Similar testing pattern to Leantime bridge
- Verify taskmaster service running/available
- Test task creation, update, completion workflows

### Documentation System Analysis

**Three-System Landscape:**
- **./docs/**: Appears to be main documentation system
- **./CCDOCS/**: Purpose unclear - needs investigation
- **./dopemux-docuXtractor/**: Separate tool for documentation extraction

**Key Decision Point**: Is docuXtractor meant to BE the documentation system or EXTRACT from other systems?

## Recovery Strategies - ADHD-Optimized

### If You Feel Overwhelmed
- Start with documentation audit (no code risk, builds understanding)
- Focus on ONE component at a time
- Use 15-minute micro-sessions instead of 25-minute chunks
- Remember: This is discovery, not repair

### If Technical Blocks Occur
- Create isolated test environment for each component
- Document exactly what works vs what doesn't
- Don't try to fix everything - focus on one working integration
- Each "failed" test reveals valuable architecture information

### If Attention Fractures
- Return to runbook-project-analysis-backup.md to rebuild context
- Pick smallest possible next action from any phase
- Use TodoWrite to externalize mental state
- Reset expectations: You're discovering, not catching up

## Weekly Milestone Checkpoints

**Week 1**: "What's actually broken vs what I thought was broken?"
**Week 2**: "Do I have ONE working integration between any two systems?"
**Week 3**: "Can I use this system for something real, even if limited?"

## The "Back on Track" Philosophy

### Core Principles
- You're not behind - you're discovering what you actually built
- Every "failed" test reveals valuable architecture information
- Working systems prove your past decisions were sound
- The goal is activation, not perfection
- Each component that works validates months of past effort

### Decision Trees for Common Scenarios

**If imports fail** → Check Python environment and dependencies
**If basic instantiation works but save/load fails** → Focus on data persistence layer
**If individual components work but don't integrate** → Focus on inter-component communication
**If everything works individually but session doesn't persist** → Focus on session lifecycle management

## Immediate Next Steps

### RECOMMENDED STARTING POINT:
**Documentation Audit** (Lowest risk, highest understanding gain)
- Map all three documentation systems
- Identify overlaps and conflicts
- Understand the intended architecture
- No risk of breaking existing functionality

### ALTERNATIVE STARTING POINT:
**Import Testing** (Quick diagnostic)
- Test all major Python modules for import errors
- Identify immediate environment/dependency issues
- Fast feedback on basic system health

---
*Extended Roadmap Generated: 2025-09-24*
*Continuation ID: 1f3a6262-13a8-405a-938f-97ffc2f34640*