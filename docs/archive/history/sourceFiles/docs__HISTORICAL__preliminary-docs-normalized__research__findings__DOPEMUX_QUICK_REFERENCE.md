# Dopemux Quick Reference Guide
## Corrected Architecture & Key Decisions

---

## ✅ Key Decisions from Previous Chats

### Technology Stack (CONFIRMED)
- **Short-term Orchestration**: Claude-flow's 64-agent hive-mind system
- **Memory System**: Letta framework ($39/month Plus tier)
- **Project Management**: Leantime MCP Server
- **Task Management**: Claude-Task-Master AI
- **Interface**: tmux-style multiplexed CLI (dopemux vibe)
- **Long-term**: Custom agent system built in parallel

### Phase 1 Focus (IMMEDIATE)
1. Integrate Leantime + Task-Master + Claude-flow
2. Build tmux-style multiplexed interface
3. Configure all MCP servers correctly
4. Implement Letta memory layers
5. Create monitoring dashboards

---

## 🔧 Corrected MCP Server Capabilities

### Critical Corrections

| Server | ACTUAL Purpose | NOT |
|--------|---------------|-----|
| **zen** | Multi-model orchestration (Claude, GPT-5, Gemini, O3) with consensus, debug, review | NOT just orchestration |
| **claude-context** | Semantic code search using embeddings (ChromaDB) | NOT context management |
| **conport** | Project memory and decision tracking (SQLite/GraphDB) | NOT general context |
| **task-master-ai** | PRD parsing, task breakdown, complexity analysis | Fully integrated |
| **serena** | LSP-based code editing with symbol operations | IDE-like refactoring |
| **sequential-thinking** | Deep reasoning, hypothesis testing, problem decomposition | 10+ step chains |
| **context7** | Library documentation and API reference | Official docs source |
| **exa** | High-signal web research | Real-time information |

### MCP Server Commands

```bash
# Correct initialization commands
zen: python /Users/hue/code/zen-mcp-server/server.py
claude-context: npx -y @zilliz/claude-context-mcp@latest
conport: uvx --from context-portal-mcp conport-mcp --mode stdio
task-master-ai: npx -y task-master-ai
serena: uv run --directory /Users/hue/code/serena serena start-mcp-server
cli: uvx cli-mcp-server
sequential-thinking: npx -y @modelcontextprotocol/server-sequential-thinking
context7: npx -y @upstash/context7-mcp
exa: npx -y exa-mcp
playwright: npx -y @playwright/mcp@latest
morphllm-fast-apply: npx -y @morph-llm/morph-fast-apply
magic: npx -y @21st-dev/magic@latest
```

---

## 🚀 Claude-flow Integration

### Key Commands
```bash
# Installation
npm install -g claude-flow@alpha

# Core workflows
npx claude-flow@alpha sparc "feature description"        # Basic development
npx claude-flow@alpha sparc tdd "feature with tests"    # Test-driven
npx claude-flow@alpha hive-mind spawn "task" --agents 8 # Multi-agent
npx claude-flow@alpha swarm "problem" --strategy consensus # Distributed

# Memory operations  
npx claude-flow@alpha memory store
npx claude-flow@alpha memory query
npx claude-flow@alpha memory export
```

### 64-Agent Ecosystem
- **Core**: Coder, Planner, Researcher, Reviewer, Tester agents
- **Swarm**: Queen agent, Worker agents, Consensus agents
- **Specialized**: Documentation, Optimization, Security, Deployment
- **Coordination**: Byzantine fault tolerance, PBFT consensus

---

## 💾 Letta Memory Configuration

### Tier Structure
```yaml
L1_Working:
  size: 8K tokens
  features: [real-time, self-editing, auto-summarization]
  
L2_Session:
  size: 32K tokens
  features: [cross-agent, persistent, compression]
  
L3_Persistent:
  size: Unlimited
  features: [user-preferences, patterns, history]
```

### Integration
```python
# Letta API endpoint
api_endpoint: "https://api.letta.ai/v1"
sync_interval: 5_minutes
pricing: $39/month for 10,000 requests
```

---

## 🖥️ Tmux Layout (Dopemux Style)

### Window Structure
```
Window 0: Orchestration
├── Pane 0: Claude-flow Master
└── Pane 1: Agent Monitor

Window 1: Execution  
├── Pane 0: Active Development
└── Pane 1: Test Runner

Window 2: Memory
├── Pane 0: Letta Memory
└── Pane 1: ConPort Decisions

Window 3: Project
├── Pane 0: Leantime
└── Pane 1: Task-Master
```

### Key Bindings
- **Prefix**: `Ctrl-d` (dopemux)
- **Windows**: `Alt-[1-4]`
- **Actions**: `Ctrl-d n` (new task), `Ctrl-d r` (run), `Ctrl-d t` (test)

---

## 📋 Leantime Integration

### Two-Tier Architecture
1. **Strategic Layer**: Leantime for project management
2. **Tactical Layer**: Task-Master for implementation tasks

### MCP Tools
```yaml
tickets:
  - leantime.rpc.tickets.getTicket
  - leantime.rpc.tickets.addTicket
  - leantime.rpc.tickets.getAllTickets
  
projects:
  - leantime.rpc.projects.getAllProjects
  - leantime.rpc.projects.getProject
```

---

## 🔄 Workflow Routing Logic

### Phase 1 Routing
```python
def route_task(task):
    if requires_deep_reasoning(task):
        return sequential_thinking → claude_flow
        
    if task.type == 'project_planning':
        return leantime → task_master → claude_flow
        
    if task.type == 'implementation':
        return claude_flow(method='tdd' if tests else 'sparc')
        
    if is_routine_task(task):
        return zen_mcp(model='gemini-flash')
```

---

## 📊 Awesome-Claude-Code Patterns

### Key Patterns to Implement
- **Queen Agent Pattern**: Master coordinator (Claude-flow)
- **Byzantine Consensus**: Multi-agent agreement (Zen)
- **CRDT Memory**: Conflict-free replicated data
- **Hierarchical Memory**: Multi-tier with Letta
- **Session Isolation**: Git worktree per session
- **Hook System**: ChatX-style pre/post tool hooks

### Workflow Patterns
- **SPARC**: Specification → Pseudocode → Architecture → Refinement → Code
- **TDD**: Test → Implement → Refactor
- **Swarm**: Distributed problem solving with consensus

---

## 🚦 Implementation Phases

### Week 1 (CURRENT)
- [ ] Install Claude-flow
- [ ] Configure Letta
- [ ] Setup MCP servers
- [ ] Create tmux interface
- [ ] Test Leantime connection

### Week 2
- [ ] Polish interface
- [ ] Add monitoring
- [ ] Create workflows
- [ ] Session persistence

### Month 2-3
- [ ] Build custom agents
- [ ] Create compatibility layer
- [ ] Begin migration
- [ ] Performance optimization

### Month 4
- [ ] Complete migration
- [ ] Full custom system
- [ ] Deprecate Claude-flow
- [ ] Production ready

---

## ⚡ Quick Commands

### Start Dopemux
```bash
dopemux start               # Start new session
dopemux attach              # Attach to existing
dopemux run sparc "task"   # Run Claude-flow workflow
dopemux memory search "query" # Search memory
```

### Development Flow
```bash
# 1. Parse PRD
task-master parse requirements.md

# 2. Create Leantime milestone
leantime create-milestone "Feature X"

# 3. Execute with Claude-flow
claude-flow sparc tdd "implement Feature X"

# 4. Store decision
conport log "Used JWT for auth"
```

---

## 🐛 Common Issues

### Claude-flow not starting
```bash
npm cache clean --force
npm install -g claude-flow@alpha
claude-flow init --with-memory --with-mcp
```

### MCP server timeout
```bash
# Check process
ps aux | grep mcp-server-name
# Restart with debug
MCP_DEBUG=true [server-command]
```

### Memory sync issues
```bash
# Fallback to local
export LETTA_FALLBACK=sqlite
# Check API status
curl https://api.letta.ai/v1/status
```

---

## 📚 Key Documents

1. **Architecture v2**: Complete corrected architecture
2. **Phase 1 Implementation**: Step-by-step guide
3. **Custom Agent R&D**: Parallel development strategy
4. **Component Specs v1**: Detailed specifications

---

## ✨ Remember

- **Claude-flow NOW**: Use immediately for orchestration
- **Custom LATER**: Build in parallel for future
- **Letta ALWAYS**: For memory management
- **MCP CORRECT**: Use accurate capabilities
- **Tmux STYLE**: Dopemux multiplexed interface

---

*Quick Reference v1.0 - Keep this handy during implementation*
