# Agent Configuration System

**Purpose**: Specialized AI agents for Two-Plane Architecture coordination
**Design**: ADHD-optimized task specialization with seamless handoffs
**Integration**: Mode-aware coordination between PM and Cognitive planes

## 🤖 Agent Ecosystem Overview

### Core Agent Types

#### Developer Agent
- **Primary Plane**: Cognitive
- **Specialization**: Code implementation, debugging, testing
- **Best For**: ACT mode, focused/hyperfocus attention states
- **Key Strengths**: Rapid iteration, concrete deliverables, technical execution

#### Architect Agent
- **Primary Plane**: PM (strategic)
- **Specialization**: System design, architectural decisions, pattern identification
- **Best For**: PLAN mode, focused/hyperfocus attention states
- **Key Strengths**: Strategic thinking, long-term design, comprehensive analysis

#### Researcher Agent
- **Primary Plane**: Cross-plane
- **Specialization**: Information gathering, documentation analysis, technology evaluation
- **Best For**: Both modes, all attention states (adaptive)
- **Key Strengths**: Authoritative sources, synthesis, decision support

#### Project Manager Agent
- **Primary Plane**: Integration Bridge
- **Specialization**: Sprint coordination, cross-plane orchestration, progress tracking
- **Best For**: PLAN mode (primary), coordination across all states
- **Key Strengths**: Team alignment, authority coordination, progress visibility

## 🎯 Agent Selection Matrix

### By Work Type
```
Code Implementation    → Developer Agent
System Architecture    → Architect Agent
Information Research   → Researcher Agent
Sprint Planning       → Project Manager Agent
Bug Investigation     → Developer + Researcher Agents
Technology Evaluation → Researcher + Architect Agents
```

### By Attention State
```
Scattered Attention:
- Quick fixes         → Developer Agent (gemini-2.5-flash)
- Status updates      → Project Manager Agent
- Quick questions     → Researcher Agent

Focused Attention:
- Feature development → Developer Agent (o3-mini)
- Architecture design → Architect Agent (o3)
- Research analysis   → Researcher Agent (o3-mini)
- Sprint planning     → Project Manager Agent

Hyperfocus State:
- Complex refactoring → Developer Agent (o3/gemini-2.5-pro)
- System redesign     → Architect Agent (o3-pro)
- Deep research       → Researcher Agent (gemini-2.5-pro)
- Strategic planning  → Project Manager Agent
```

### By Mode Context
```
PLAN Mode (Strategic):
Primary: Architect Agent, Project Manager Agent
Support: Researcher Agent

ACT Mode (Implementation):
Primary: Developer Agent
Support: Researcher Agent, Project Manager Agent (coordination)
```

## 🔄 Agent Coordination Patterns

### Standard Handoff Workflows

#### 1. Strategic to Implementation
```
Architect Agent (design)
    → Project Manager Agent (coordination)
    → Developer Agent (implementation)
```

#### 2. Research to Decision
```
Researcher Agent (analysis)
    → Architect Agent (design decision)
    → Project Manager Agent (sprint integration)
```

#### 3. Implementation to Coordination
```
Developer Agent (progress/blockers)
    → Project Manager Agent (coordination)
    → [Resolution path based on issue type]
```

### Cross-Plane Coordination

#### PM Plane → Cognitive Plane
1. **Strategic Requirements** (Task-Master) → **Project Manager Agent**
2. **Coordination Planning** → **Architect Agent** (technical feasibility)
3. **Implementation Specification** → **Developer Agent** (execution)

#### Cognitive Plane → PM Plane
1. **Technical Progress** (Developer Agent) → **Project Manager Agent**
2. **Status Coordination** → **Integration Bridge** → **Leantime**
3. **Decision Logging** → **ConPort** (memory preservation)

## 🧠 ADHD-Optimized Agent Behaviors

### Context Preservation
- All agents automatically save state before handoffs
- Mental model preservation across interruptions
- Clear bridging summaries during agent transitions
- ConPort integration for persistent memory

### Attention Management
- Agents adapt response complexity to user's attention state
- Progressive disclosure: essential info first, details on request
- Visual progress indicators and completion celebrations
- Gentle guidance with encouraging, supportive language

### Cognitive Load Reduction
- Maximum 3 options presented in any decision
- Single clear next action when attention is scattered
- Automatic tool selection based on agent specialization
- Smart context pruning to essential information

## ⚙️ Technical Implementation

### Agent Invocation Patterns
```bash
# Direct agent usage (when agent type is clear)
"I need to implement X feature" → Developer Agent
"What's the best architecture for Y?" → Architect Agent
"Research technology Z" → Researcher Agent
"Plan next sprint" → Project Manager Agent

# Mode-based routing (when work type is ambiguous)
Current Mode: PLAN → Architect/Project Manager Agents prioritized
Current Mode: ACT → Developer Agent prioritized

# Attention-based adaptation (automatic)
Scattered → Fast models, minimal context, single actions
Focused → Balanced models, structured detail, multiple options
Hyperfocus → Premium models, comprehensive analysis, full context
```

### Configuration Integration
- **llms.md**: Multi-model routing and mode-aware selection
- **llm.md**: Agent-specific behaviors and optimizations
- **Individual agent files**: Detailed specialization and coordination patterns

### ConPort Memory Integration
- Automatic decision logging with agent attribution
- Progress tracking across agent handoffs
- Knowledge graph relationships between agent activities
- Sprint coordination through mem4sprint framework

## 📋 Success Metrics

### Individual Agent Performance
- **Developer Agent**: Code quality, implementation speed, test coverage
- **Architect Agent**: Decision quality, long-term maintainability, pattern consistency
- **Researcher Agent**: Information accuracy, source authority, synthesis quality
- **Project Manager Agent**: Sprint success rate, team coordination, blocker resolution

### System-Wide Coordination
- **Handoff Efficiency**: Smooth transitions without context loss
- **Authority Respect**: Clear boundaries and conflict-free coordination
- **ADHD Accommodation**: Reduced cognitive load and preserved attention
- **Progress Visibility**: Clear advancement tracking and completion recognition

### Strategic Alignment
- **Token Efficiency**: 77% reduction through intelligent agent routing
- **Quality Maintenance**: High-quality outputs despite reduced complexity
- **Developer Experience**: ADHD-friendly workflows and interactions
- **System Coherence**: Consistent patterns across all agent interactions

## 🎯 Usage Guidelines

### When to Use Multiple Agents
- **Complex Projects**: Coordinate across agents for comprehensive approach
- **Learning Scenarios**: Research → Architect → Developer progression
- **Quality Assurance**: Developer → Architect review cycles
- **Strategic Planning**: Project Manager orchestration of all agents

### When to Stick with Single Agent
- **Clear Specialization**: Task clearly fits one agent's expertise
- **Scattered Attention**: Minimize handoffs to reduce cognitive load
- **Time Pressure**: Direct path to solution without coordination overhead
- **Simple Tasks**: No need for multi-agent complexity

### Emergency Protocols
- **Agent Unavailable**: Graceful degradation to general capability
- **Context Overflow**: Automatic pruning and essential information preservation
- **Attention Crisis**: Switch to scattered-attention mode with minimal coordination

---

**Agent Excellence**: Specialized expertise with seamless coordination
**ADHD Integration**: Cognitive load management through intelligent agent selection
**System Coherence**: Unified experience across all agent interactions and handoffs