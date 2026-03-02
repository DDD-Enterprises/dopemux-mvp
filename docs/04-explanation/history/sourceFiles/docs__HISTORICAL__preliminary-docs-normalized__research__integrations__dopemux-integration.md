## Context & Goal

    Design clarification for dopemux integration strategy, addressing IPC/wrapper architecture benefits, language choice (Python vs Node.js), claude-flow/Claude Code interaction patterns, and practical implementation of context management and workflow orchestration.

## Assumptions (new/updated)

- User wants dopemux to be a high-level orchestrator that simplifies complex AI workflows
- Python preference exists but integration complexity with Claude ecosystem is a concern
- User needs clarity on the relationship between claude-flow and Claude Code
- Context management and workflow orchestration are critical features requiring detailed specification
- dopemux should abstract complexity while maintaining power-user capabilities

## Proposed Design

### 1. Wrapper/IPC Architecture Benefits

**What it enables:**
- **Process isolation**: Claude Code runs in subprocess, preventing crashes from affecting dopemux
- **Streaming communication**: Real-time output/input handling via JSON-RPC over stdio/IPC
- **State persistence**: dopemux maintains context even if Claude Code sessions fail
- **Multi-session orchestration**: Run multiple Claude Code instances in parallel
- **Hot-reload capability**: Update dopemux code without losing active sessions

**User Experience:**
```bash
# Single command spawns complex workflows
dopemux dev "build authentication system"
# Behind scenes: spawns claude-flow hive → coordinates 5 agents → each uses Claude Code

# Interactive session with context awareness
dopemux chat --memory project
# Maintains conversation history, project context, and learns from interactions

# Simplified hive management
dopemux hive spawn research --agents 8
# Abstracts npx calls, manages sessions, aggregates results
```

### 2. Language Choice: Hybrid Approach Recommended

**Python for dopemux shell (if preferred):**
```python
# dopemux/core/orchestrator.py
class DopemuxOrchestrator:
    def __init__(self):
        self.claude_flow = ClaudeFlowBridge()  # Node.js subprocess
        self.claude_code = ClaudeCodeWrapper()  # Direct subprocess
        self.memory = SQLiteMemory(".dopemux/memory.db")
    
    def spawn_hive(self, task: str, agents: int = 5):
        # Python handles high-level orchestration
        return self.claude_flow.execute([
            "npx", "claude-flow@alpha", "hive-mind", 
            "spawn", task, "--agents", str(agents)
        ])
```

**Node.js bridge layer (required):**
```javascript
// dopemux-bridge/index.js
// Handles claude-flow and Claude Code integration
const { spawn } = require('teen_process');
const { EventEmitter } = require('events');

class DopemuxBridge extends EventEmitter {
    async executeClaudeFlow(command, args) {
        // Manages npx calls with proper error handling
        const { stdout, stderr } = await spawn('npx', 
            ['claude-flow@alpha', ...args], 
            { timeout: 300000 }
        );
        return this.parseResults(stdout);
    }
}
```

### 3. Claude-flow vs Claude Code Relationship

**Architecture clarification:**
- **claude-flow**: High-level orchestrator, runs **independently** of Claude Code
- **Claude Code**: Execution engine for actual coding tasks
- **Relationship**: claude-flow coordinates agents that **spawn Claude Code instances**

```
User → dopemux → claude-flow (orchestration layer)
                       ↓
                 Spawns multiple agents
                       ↓
              Each agent → Claude Code instance
                            (actual code execution)
```

**claude-flow operates in two modes:**
1. **Headless orchestration**: `npx claude-flow@alpha` commands
2. **Claude Code integration**: Agents spawn `claude --dangerously-skip-permissions`

### 4. Context Management Implementation

**Three-tier memory architecture:**

```json
{
  "working_memory": {
    "current_task": "implement auth",
    "active_files": ["auth.py", "test_auth.py"],
    "recent_errors": [],
    "ttl": 3600
  },
  "session_memory": {
    "conversation_history": [...],
    "decisions_made": [...],
    "code_generated": {...}
  },
  "long_term_memory": {
    "project_patterns": {...},
    "user_preferences": {...},
    "learned_optimizations": {...}
  }
}
```

**Benefits for users:**
- **Continuous context**: Never lose progress between sessions
- **Smart suggestions**: Learn from past decisions
- **Error prevention**: Remember what didn't work
- **Faster iterations**: Skip redundant analysis

**Implementation:**
```python
# dopemux/memory/manager.py
class ContextManager:
    def __init__(self):
        self.db = sqlite3.connect(".dopemux/memory.db")
        self.vector_store = Qdrant(":memory:")  # For RAG
        
    def inject_context(self, prompt: str) -> str:
        # Enrich prompts with relevant history
        relevant = self.vector_store.search(prompt, limit=5)
        recent = self.get_recent_decisions()
        return f"{prompt}\n\nContext:\n{relevant}\n{recent}"
```

## Workflows

### Development Workflow with dopemux

```bash
# 1. Initialize project with context
dopemux init --template fastapi --personality roast
→ Creates .dopemux/config.yml
→ Sets up .claude/CLAUDE.md
→ Configures MCP servers

# 2. Start development with orchestration
dopemux dev "implement user authentication"
→ Spawns claude-flow hive-mind (5 agents)
→ Architect agent designs system
→ Coder agents implement in parallel (via Claude Code)
→ Tester agent writes tests
→ Reviewer ensures quality
→ dopemux aggregates results

# 3. Iterative improvement
dopemux improve --self-build
→ dopemux analyzes its own code
→ Suggests improvements
→ Implements them via Claude Code
→ Tests changes
→ Commits if successful
```

### claude-flow → Claude Code execution flow

```
1. User: dopemux sparc "build REST API"
2. dopemux: npx claude-flow@alpha sparc run specification "REST API"
3. claude-flow: Spawns specification agent
4. Agent: claude --dangerously-skip-permissions --print << PROMPT
5. Claude Code: Generates specification
6. Agent: Returns to claude-flow
7. claude-flow: Next phase (pseudocode)
8. Repeat for all SPARC phases
9. dopemux: Aggregates and presents results
```

## Quality Gates & Acceptance Criteria

- **IPC reliability**: <10ms message latency, automatic reconnection
- **Memory efficiency**: <100MB overhead per Claude Code instance
- **Context preservation**: 100% session recovery after crashes
- **Workflow completion**: 90%+ success rate for standard tasks
- **User experience**: Single command for complex operations

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Node.js dependency for claude-flow | High | Create Python wrapper with fallback to direct API |
| Complex subprocess management | Medium | Use battle-tested teen_process, implement circuit breakers |
| Memory/context bloat | Medium | Implement TTL, compression, selective persistence |
| Claude Code API changes | Low | Version pin, compatibility layer |

## Open Questions

1. **Personality integration**: How explicit should the "roast-heavy" personality be in error messages vs normal output?
2. **ADHD features priority**: Which features are most critical - task breakdown, time management, or context switching prevention?
3. **Self-building scope**: Should dopemux modify its core orchestration code or just workflow definitions?
4. **Performance targets**: What's acceptable latency for multi-agent coordination?
5. **Integration depth**: Should dopemux replace claude-flow's npx interface entirely or wrap it?

## Next Actions

1. **Week 1**: Implement Python orchestrator with Node.js bridge for claude-flow
2. **Week 2**: Create IPC layer for Claude Code subprocess management  
3. **Week 3**: Build SQLite memory system with vector search
4. **Week 4**: Implement basic workflow orchestration (dev, test, improve)
5. **Week 5**: Add self-building capability with safety checks
6. **Week 6**: Integrate ADHD-friendly features and personality system

## Self-check

- ✓ Clarified wrapper/IPC benefits with concrete user experience examples
- ✓ Addressed Python vs Node.js with hybrid approach recommendation  
- ✓ Explained claude-flow operates independently, coordinates Claude Code instances
- ✓ Detailed context management with three-tier architecture and benefits
- ✓ Provided workflow orchestration patterns with specific command flows
- ✓ Showed how claude-flow uses Claude Code for implementation tasks
- ✓ Included risk analysis and phased implementation plan
