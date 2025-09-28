# Agent-Specific Model Configuration

**Purpose**: Individual agent behavior and model specialization
**Scope**: Single-agent optimization for specific task types
**Coordination**: Works with llms.md for multi-agent orchestration

## 🤖 Specialized Agent Configurations

### Developer Agent
**Primary Use**: Code implementation, debugging, testing
**Optimal Models**: `gemini-2.5-flash`, `o3-mini`
**Context Limits**:
- Scattered: 15k tokens max
- Focused: 25k tokens max
- Hyperfocus: 50k tokens max

**Behavior Patterns**:
- Always check Context7 for library documentation first
- Log all implementation decisions in ConPort
- Use progressive disclosure for complex explanations
- Provide one clear next action when attention is scattered

### Architect Agent
**Primary Use**: System design, decision analysis, pattern identification
**Optimal Models**: `o3`, `gemini-2.5-pro`, `o3-pro` (sparingly)
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
**Optimal Models**: `gemini-2.5-flash`, `o3-mini`
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
  model_preference: gemini-2.5-flash

focused:
  response_length: structured (3-5 sections)
  actions: prioritized list (max 3 items)
  complexity: moderate
  model_preference: o3-mini

hyperfocus:
  response_length: comprehensive (detailed analysis)
  actions: full implementation plan
  complexity: high
  model_preference: o3, gemini-2.5-pro
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
1. Context7 documentation check
2. Read relevant files
3. Generate/modify code
4. Log decision reasoning
5. Update progress tracking

**Research Tasks**:
1. Web search for current information
2. Context7 for official docs
3. Synthesize and summarize
4. Store findings in ConPort

**Planning Tasks**:
1. Get current ConPort context
2. Use sequential thinking for complex analysis
3. Create sprint/goal structures
4. Link related items in knowledge graph

### Error Recovery
**Common Failures**:
- Model timeout → Switch to faster model, retry
- Context overflow → Prune context, focus on essentials
- Tool unavailable → Graceful degradation, inform user

**ADHD Considerations**:
- Never apologize excessively for errors
- Provide clear recovery steps
- Maintain encouraging tone
- Preserve user's mental model

## 🎯 Task-Specific Optimizations

### Code Review Agent
- **Model**: `o3` for systematic analysis
- **Context**: Include style guides and patterns
- **Output**: Structured findings with severity levels
- **Memory**: Log code quality patterns

### Sprint Planning Agent
- **Model**: `gemini-2.5-pro` for synthesis
- **Context**: Recent decisions and active goals
- **Output**: Organized sprint structure
- **Memory**: Track planning decisions and rationale

### Debugging Agent
- **Model**: `gemini-2.5-flash` for speed, `o3` for complex issues
- **Context**: Error logs, relevant code sections
- **Output**: Step-by-step investigation plan
- **Memory**: Log root causes and solutions

---

**Philosophy**: Each agent specializes in specific cognitive tasks while maintaining ADHD accommodations
**Coordination**: Seamless handoffs between agents preserve context and mental models
**Efficiency**: Optimized model selection reduces cost while maximizing effectiveness