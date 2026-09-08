This repository is governed by .claude/PROJECT_INSTRUCTIONS.md.
Investigations and redesigns must follow .claude/PRIMER.md

# Agent-Specific Model Configuration

**Purpose**: Individual agent behavior and model specialization
**Scope**: Single-agent optimization for specific task types
**Coordination**: Works with llms.md for multi-agent orchestration

<!-- CONTROL_TOWER_ENTRY_BEGIN -->
## Control Tower Supervision

For supervised engineering packets, follow [Control Tower Packet Workflow](../AGENTS.md#control-tower-packet-workflow).
Read the installed kit contracts and project configuration through that entry point.
For supervised packets, model selection is packet-specific. Attention accommodations affect presentation and pacing, not execution authority.
<!-- CONTROL_TOWER_ENTRY_END -->

## Model Routing Authority

For supervised packets, use the validated packet routing decision and preserve
its model, effort, retry bounds and required reviewer independence. For ordinary
unsupervised work, follow existing user/repository model-selection authority and
use the cheapest adequate authorized available route. Ordinary work does not
require creating a packet or routing record. This policy applies to every agent
and attention-state example below; presentation preferences grant no authority.

## 🤖 Specialized Agent Configurations

### Developer Agent

**Primary Use**: Code implementation, debugging, testing
**Model Route**: Follow Model Routing Authority above for the current work scope
**Context Limits**:

- Scattered: 15k tokens max
- Focused: 25k tokens max
- Hyperfocus: 50k tokens max

**Behavior Patterns**:

- Always check PAL apilookup for library documentation first
- Log all implementation decisions in ConPort
- Use progressive disclosure for complex explanations
- Provide one clear next action when attention is scattered

### Architect Agent

**Primary Use**: System design, decision analysis, pattern identification
**Model Route**: Follow Model Routing Authority above for the current work scope
**Context Limits**:

- Focused: 25k tokens max
- Hyperfocus: 100k tokens max

**Behavior Patterns**:

- Enable thinking mode for complex architectural decisions
- Use ConPort semantic search for relevant context
- Create decision records with detailed rationale
- Provide multiple implementation approaches (max 3)

### Researcher Agent

**Primary Use**: Information gathering, documentation analysis
**Model Route**: Follow Model Routing Authority above for the current work scope
**Context Limits**: 15k tokens max (controlled information gathering)

**Behavior Patterns**:

- Use MCP servers for authoritative sources
- Synthesize findings into digestible summaries
- Prefer official documentation over general knowledge
- Provide source attribution for all information

## 🧠 ADHD-Optimized Agent Behaviors

### Attention State Detection

```yaml
scattered:
  response_length: concise (1-3 paragraphs)
  actions: single clear next step
  complexity: minimal
  model_preference: authorized_route_for_work_scope

focused:
  response_length: structured (3-5 sections)
  actions: prioritized list (max 3 items)
  complexity: moderate
  model_preference: authorized_route_for_work_scope

hyperfocus:
  response_length: comprehensive (detailed analysis)
  actions: full implementation plan
  complexity: high
  model_preference: authorized_route_for_work_scope
```

### Context Switch Handling

**Trigger Patterns**:

- "Actually, let me..." → Save current context, bridge to new task
- "Quick question..." → Lightweight response, maintain previous context
- "Can we switch to..." → Formal context handoff with summary

**Response Adaptation**:

- Provide orientation: "You were working on X, now Y"
- Preserve mental model in ConPort active context
- Offer to resume previous work after new task

### Memory Integration

**Automatic Triggers**:

- Decision made → Log in ConPort with rationale
- Task started → Create progress entry
- Pattern identified → Add to system patterns
- Term defined → Add to project glossary

## 🔧 Tool Usage Optimization

### High-Frequency Patterns

**Code Tasks**:

1. PAL apilookup documentation check
2. Read relevant files
3. Generate/modify code
4. Log decision reasoning
5. Update progress tracking

**Research Tasks**:

1. Web search for current information
2. PAL apilookup for official docs
3. Synthesize and summarize
4. Store findings in ConPort

**Planning Tasks**:

1. Get current ConPort context
2. Use sequential thinking for complex analysis
3. Create sprint/goal structures
4. Link related items in knowledge graph

### Error Recovery

**Common Failures**:

- Model timeout → Record the failure; follow applicable user/repository retry authority and any supervised packet's explicit bounds
- Context overflow → Prune context, focus on essentials
- Tool unavailable → Graceful degradation, inform user

**ADHD Considerations**:

- Never apologize excessively for errors
- Provide clear recovery steps
- Maintain encouraging tone
- Preserve user's mental model

## 🎯 Task-Specific Optimizations

### Code Review Agent

- **Model**: Follow Model Routing Authority above; preserve required reviewer independence
- **Context**: Include style guides and patterns
- **Output**: Structured findings with severity levels
- **Memory**: Log code quality patterns

### Sprint Planning Agent

- **Model**: Follow Model Routing Authority above for the current work scope
- **Context**: Recent decisions and active goals
- **Output**: Organized sprint structure
- **Memory**: Track planning decisions and rationale

### Debugging Agent

- **Model**: Follow Model Routing Authority above; escalation requires applicable user/repository authority and any supervised packet's explicit permission
- **Context**: Error logs, relevant code sections
- **Output**: Step-by-step investigation plan
- **Memory**: Log root causes and solutions

---

**Philosophy**: Each agent specializes in specific cognitive tasks while maintaining ADHD accommodations
**Coordination**: Seamless handoffs between agents preserve context and mental models
**Efficiency**: Optimized model selection reduces cost while maximizing effectiveness
