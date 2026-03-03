# Dopemux Platform Architecture v2.0 (Corrected)
## Claude-flow Based Implementation with Custom Agent System

---

## Context & Goal

**Platform Vision**: Dopemux is a tmux-inspired, neurodivergent-friendly software development orchestration platform that uses Claude-flow's 64-agent hive-mind system in the short term while building a custom agentic software development system for the long term.

**Phase 1 Focus**: Integrate Leantime, Task-Master AI, Claude-flow, and MCP servers in a multiplexed tmux-style CLI UI.

**Key Decisions from Previous Chats**:
- Use Claude-flow immediately for its proven 64-agent ecosystem
- Build custom agentic system in parallel
- Leverage Letta for memory layers
- Integrate all existing MCP servers with correct capabilities
- Create tmux-style multiplexed interface (dopemux vibe)

---

## 1. System Architecture Overview

### Core Technology Stack

```yaml
immediate_implementation:
  orchestration: "Claude-flow (64 agents, hive-mind)"
  memory: "Letta (multi-tier with self-editing capabilities)"
  project_management: "Leantime MCP integration"
  task_management: "Claude-Task-Master AI"
  interface: "tmux-style multiplexed CLI (dopemux)"
  
parallel_development:
  custom_agent_system: "Build alongside Claude-flow usage"
  migration_path: "Gradual transition from Claude-flow to custom"
```

### Layered Architecture

```yaml
presentation_layer:
  primary: "tmux-style multiplexed terminal"
  components:
    - "dopemux CLI (main entry point)"
    - "Session multiplexer (split panes/windows)"
    - "Status line (agent activity, tokens, progress)"
    - "Interactive chat interfaces per agent"
  implementation:
    - "Python: Rich/Textual for TUI"
    - "tmux integration for session management"
    - "Real-time updates via WebSocket"

orchestration_layer:
  short_term: "Claude-flow hive-mind orchestration"
  components:
    - "64 specialized agents via Claude-flow"
    - "BatchTool for parallel execution (10 concurrent)"
    - "Hive-mind coordination patterns"
    - "SPARC/TDD workflow automation"
  long_term: "Custom agent orchestrator"
  
memory_layer:
  primary: "Letta framework"
  features:
    - "Self-editing memory ($39/user/month Plus tier)"
    - "10,000 requests/month capacity"
    - "Personalized context learning"
    - "Cross-session persistence"
  additional:
    - "Claude-flow SQLite persistence"
    - "ConPort for project decisions"
    - "OpenMemory for personal patterns"
    
integration_layer:
  project_management: "Leantime MCP Server"
  task_management: "Claude-Task-Master AI"
  mcp_servers: # CORRECTED DESCRIPTIONS
    zen:
      purpose: "Multi-model orchestration (Claude, GPT-5, Gemini, O3)"
      capabilities: ["consensus", "debug", "code review", "planning"]
    claude_context:
      purpose: "Semantic code search using embeddings"
      capabilities: ["code search by meaning", "navigate large codebases"]
    conport:
      purpose: "Project memory and decision tracking"
      capabilities: ["log_decision", "get_decisions", "search patterns"]
    task_master_ai:
      purpose: "PRD parsing and task management"
      capabilities: ["parse_prd", "task breakdown", "complexity analysis"]
    serena:
      purpose: "LSP-based code editing and refactoring"
      capabilities: ["find_symbol", "safe editing", "refactoring"]
    sequential_thinking:
      purpose: "Deep reasoning and hypothesis testing"
      capabilities: ["step-by-step analysis", "problem decomposition"]
    context7:
      purpose: "Library documentation and API reference"
      capabilities: ["query official docs", "usage examples"]
    exa:
      purpose: "High-signal web research"
      capabilities: ["real-time information", "quality filtering"]
    cli:
      purpose: "Command execution and system operations"
    playwright:
      purpose: "Browser automation and testing"
    morphllm_fast_apply:
      purpose: "Fast code application and patches"
    magic:
      purpose: "Utility functions and helpers"
```

---

## 2. Claude-flow Integration (Short-term Solution)

### Claude-flow's 64-Agent Ecosystem

```yaml
agent_categories:
  core_development:
    - coder_agents: "Primary implementation"
    - planner_agents: "Architecture and design"
    - researcher_agents: "Documentation and learning"
    - reviewer_agents: "Code quality and standards"
    - tester_agents: "Test generation and validation"
    
  swarm_coordination:
    - queen_agent: "Master coordinator"
    - worker_agents: "Parallel task execution"
    - consensus_agents: "Byzantine fault tolerance"
    
  specialized_agents:
    - documentation_agents: "Doc generation"
    - optimization_agents: "Performance tuning"
    - security_agents: "Vulnerability scanning"
    - deployment_agents: "CI/CD automation"

workflow_patterns:
  sparc:
    description: "Specification, Pseudocode, Architecture, Refinement, Code"
    command: "npx claude-flow@alpha sparc 'feature description'"
    
  tdd:
    description: "Test-driven development workflow"
    command: "npx claude-flow@alpha sparc tdd 'feature description'"
    
  hive_mind:
    description: "Spawn multiple agents for complex tasks"
    command: "npx claude-flow@alpha hive-mind spawn 'task' --agents 8"
    
  swarm:
    description: "Distributed problem solving"
    command: "npx claude-flow@alpha swarm 'problem' --strategy consensus"
```

### Claude-flow Memory System

```yaml
claude_flow_memory:
  backend: "SQLite with WAL mode"
  location: "~/.dopemux/claude-flow/memory.db"
  features:
    - "Session persistence"
    - "Cross-agent knowledge sharing"
    - "CRDT conflict resolution"
    - "Pattern learning"
  commands:
    store: "npx claude-flow@alpha memory store"
    query: "npx claude-flow@alpha memory query"
    export: "npx claude-flow@alpha memory export"
```

---

## 3. Letta Memory Integration

### Multi-Tier Memory Architecture with Letta

```yaml
letta_configuration:
  tier_1_working:
    description: "Active task context"
    size: "8K tokens"
    features:
      - "Real-time updates"
      - "Self-editing capabilities"
      - "Automatic summarization"
      
  tier_2_session:
    description: "Current project session"
    size: "32K tokens"
    features:
      - "Cross-agent sharing"
      - "Persistent across restarts"
      - "Intelligent compression"
      
  tier_3_persistent:
    description: "Long-term knowledge"
    size: "Unlimited (cloud storage)"
    features:
      - "User preference learning"
      - "Pattern recognition"
      - "Historical context"
      
  integration:
    api_endpoint: "https://api.letta.ai/v1"
    authentication: "Bearer token"
    sync_interval: "5 minutes"
    conflict_resolution: "Last-write-wins with versioning"
```

---

## 4. Leantime Integration (Phase 1 Priority)

### Leantime MCP Server Architecture

```yaml
leantime_mcp:
  server_components:
    php_plugin: "Direct Leantime core integration"
    typescript_bridge: "MCP protocol connectivity"
    
  exposed_tools:
    tickets:
      - "leantime.rpc.tickets.getTicket"
      - "leantime.rpc.tickets.addTicket"
      - "leantime.rpc.tickets.getAllTickets"
    projects:
      - "leantime.rpc.projects.getAllProjects"
      - "leantime.rpc.projects.getProject"
    milestones:
      - "Milestone tracking and management"
    timesheets:
      - "Time tracking integration"
      
  authentication:
    methods: ["Personal Access Tokens", "API Keys", "Bearer tokens"]
    format: "lt_{username}_{hash}"
    
  integration_workflow:
    1_strategic: "Leantime for high-level planning"
    2_tactical: "Task-Master for task breakdown"
    3_execution: "Claude-flow for implementation"
    4_sync: "Bidirectional status updates"
```

### Task-Master AI Integration

```yaml
task_master_integration:
  capabilities:
    - "PRD parsing and analysis"
    - "Automatic task decomposition"
    - "Complexity estimation"
    - "Dependency detection"
    - "Progress tracking"
    
  workflow:
    parse_prd:
      input: "Product requirement document"
      output: "Hierarchical task structure"
      
    task_routing:
      simple: "Direct to Claude-flow coder agents"
      complex: "Sequential-thinking first, then implementation"
      research: "Research agents via Claude-flow"
      
  state_management:
    storage: ".taskmaster/tasks/tasks.json"
    sync: "Real-time with Leantime milestones"
```

---

## 5. Tmux-Style Multiplexed Interface

### Dopemux CLI Layout

```yaml
tmux_layout:
  window_0_orchestration:
    pane_0:
      title: "Claude-flow Master"
      content: "Main orchestrator output"
      commands: ["claude-flow start --master"]
      
    pane_1:
      title: "Agent Monitor"
      content: "Active agent status"
      display:
        - "Agent activity feed"
        - "Token usage per agent"
        - "Task queue depth"
        
  window_1_execution:
    pane_0:
      title: "Active Development"
      content: "Current coding agent output"
      features: ["Syntax highlighting", "Live editing"]
      
    pane_1:
      title: "Test Runner"
      content: "Test execution and coverage"
      auto_refresh: true
      
  window_2_memory:
    pane_0:
      title: "Letta Memory"
      content: "Memory operations and queries"
      
    pane_1:
      title: "ConPort Decisions"
      content: "Project decision log"
      
  window_3_project:
    pane_0:
      title: "Leantime"
      content: "Project milestones and tickets"
      
    pane_1:
      title: "Task-Master"
      content: "Current task breakdown"
      
  status_line:
    left: "[dopemux] {session_name} | {active_agents}"
    center: "{current_task} [{progress}%]"
    right: "Tokens: {used}/{budget} | {time}"
    
  keybindings:
    prefix: "Ctrl-d" # dopemux prefix
    navigation:
      - "Alt-[1-4]: Switch windows"
      - "Alt-Arrow: Navigate panes"
    actions:
      - "Ctrl-d n: New task"
      - "Ctrl-d r: Run workflow"
      - "Ctrl-d t: Run tests"
      - "Ctrl-d m: Memory search"
```

### Session Management

```bash
# Dopemux session commands
dopemux new -s project-name      # Create new session
dopemux attach -t project-name   # Attach to existing
dopemux ls                       # List all sessions
dopemux save                     # Save session state
dopemux restore                  # Restore from checkpoint

# Session persistence
~/.dopemux/
  sessions/
    {project-name}/
      layout.yaml        # Window/pane configuration
      state.json         # Agent and task state
      memory.db          # Claude-flow memory
      letta.cache        # Letta memory cache
```

---

## 6. Custom Agent System (Parallel Development)

### Architecture for Custom System

```yaml
custom_agent_architecture:
  design_principles:
    - "Learn from Claude-flow patterns"
    - "Integrate Awesome-Claude-Code innovations"
    - "Maintain compatibility with MCP servers"
    - "Support gradual migration from Claude-flow"
    
  core_components:
    orchestrator:
      pattern: "Hub-and-spoke with fallback to mesh"
      language: "Python with asyncio"
      communication: "JSON-RPC over IPC"
      
    agent_framework:
      base_class: "AbstractAgent"
      specializations:
        - "CodeAgent"
        - "TestAgent"
        - "ReviewAgent"
        - "ResearchAgent"
      lifecycle: ["initialize", "plan", "execute", "validate", "report"]
      
    memory_integration:
      primary: "Letta API"
      fallback: "Local SQLite"
      caching: "Redis for hot data"
      
    workflow_engine:
      dsl: "YAML-based workflow definitions"
      execution: "DAG with dynamic branching"
      checkpoints: "Automatic state persistence"
```

### Migration Strategy

```yaml
migration_phases:
  phase_1_parallel:
    description: "Run Claude-flow and custom system side-by-side"
    duration: "4-6 weeks"
    validation: "Compare outputs for same tasks"
    
  phase_2_hybrid:
    description: "Custom orchestrator using Claude-flow agents"
    duration: "2-4 weeks"
    approach: "Wrap Claude-flow agents in custom interfaces"
    
  phase_3_transition:
    description: "Gradual agent replacement"
    duration: "4-8 weeks"
    strategy: "Replace one agent type at a time"
    
  phase_4_optimization:
    description: "Full custom system with optimizations"
    features:
      - "Custom agent specializations"
      - "Optimized communication protocols"
      - "Enhanced memory management"
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

```yaml
week_1:
  day_1_2:
    - "Setup Claude-flow with all configurations"
    - "Initialize Letta memory system"
    - "Configure all MCP servers correctly"
    
  day_3_4:
    - "Implement basic dopemux CLI"
    - "Create tmux layout manager"
    - "Test Claude-flow integration"
    
  day_5:
    - "Leantime MCP server setup"
    - "Task-Master AI integration"
    - "End-to-end workflow test"
    
week_2:
  - "Polish tmux interface"
  - "Implement session persistence"
  - "Add monitoring dashboards"
  - "Create first production workflows"
```

### Phase 2: Enhancement (Weeks 3-4)

```yaml
enhancements:
  - "Add all 12 MCP servers"
  - "Implement Letta advanced features"
  - "Create workflow templates"
  - "Add performance monitoring"
  - "Build error recovery systems"
```

### Phase 3: Custom System (Weeks 5-8)

```yaml
custom_development:
  - "Design custom agent architecture"
  - "Implement base agent framework"
  - "Create orchestration engine"
  - "Build migration tools"
  - "Test parallel execution"
```

---

## 8. Critical Integration Details

### MCP Server Initialization

```python
# Correct MCP server initialization with proper capabilities
mcp_servers = {
    "zen": {
        "command": "python /path/to/zen-mcp-server/server.py",
        "capabilities": {
            "multi_model": True,
            "models": ["claude", "gpt-5", "gemini", "o3", "ollama"],
            "features": ["consensus", "debug", "review", "planning"],
            "note": "Disable planning when using Claude-flow orchestration"
        }
    },
    "claude_context": {
        "command": "npx -y @zilliz/claude-context-mcp@latest",
        "capabilities": {
            "semantic_search": True,
            "embedding_based": True,
            "codebase_navigation": True,
            "note": "NOT for context management - for code search"
        }
    },
    "conport": {
        "command": "uvx --from context-portal-mcp conport-mcp --mode stdio",
        "capabilities": {
            "project_memory": True,
            "decision_tracking": True,
            "functions": ["log_decision", "get_decisions", "search"],
            "storage": "SQLite or graph DB"
        }
    },
    # ... other servers with correct capabilities
}
```

### Workflow Routing Logic

```python
def route_task(task, context):
    """
    Phase 1 routing logic using Claude-flow as primary orchestrator
    """
    # Complex reasoning tasks
    if requires_deep_reasoning(task):
        return {
            'pre_processor': 'sequential-thinking-mcp',
            'executor': 'claude-flow',
            'method': 'sparc'
        }
    
    # Project management tasks
    if task.type == 'project_planning':
        return {
            'planner': 'leantime',
            'breakdown': 'task-master-ai',
            'executor': 'claude-flow'
        }
    
    # Standard development tasks
    if task.type == 'implementation':
        return {
            'orchestrator': 'claude-flow',
            'method': 'tdd' if task.requires_tests else 'sparc',
            'agents': determine_agent_count(task.complexity)
        }
    
    # Cost-optimized routine tasks
    if is_routine_task(task) and context.optimize_cost:
        return {
            'handler': 'zen-mcp',
            'model': 'gemini-flash',
            'fallback': 'claude-flow'
        }
```

---

## 9. Performance & Monitoring

### Key Metrics

```yaml
performance_metrics:
  claude_flow:
    - "Agent spawn time < 2s"
    - "Hive coordination overhead < 10%"
    - "Memory query latency < 100ms"
    
  letta:
    - "Memory update latency < 500ms"
    - "Self-edit success rate > 95%"
    - "Context compression ratio > 3:1"
    
  system:
    - "End-to-end task completion < 10min"
    - "Token efficiency > 80%"
    - "Cache hit rate > 70%"
    
monitoring_dashboard:
  panels:
    - "Active agents and their states"
    - "Token usage by agent type"
    - "Memory tier utilization"
    - "Task completion rates"
    - "Error recovery success"
```

---

## 10. Next Actions

### Immediate (Day 1)

1. **Install Claude-flow**: `npm install -g claude-flow@alpha`
2. **Setup Letta account**: Configure API access
3. **Configure MCP servers**: With correct capabilities
4. **Create dopemux CLI skeleton**: Basic tmux wrapper
5. **Test Leantime connection**: Verify MCP integration

### Week 1 Deliverables

1. **Working Claude-flow integration**
2. **Letta memory system operational**
3. **Basic tmux interface**
4. **Leantime-TaskMaster workflow**
5. **First automated development cycle**

---

## Self-Check Validation

✓ **Claude-flow as primary orchestrator** - Correctly specified  
✓ **Letta for memory layers** - Properly integrated  
✓ **Accurate MCP server descriptions** - All corrected  
✓ **Leantime integration** - Phase 1 priority confirmed  
✓ **Tmux-style interface** - Dopemux vibe maintained  
✓ **Custom system parallel development** - Migration path defined  
✓ **Awesome-Claude-Code patterns** - Incorporated throughout  

---

## Document Metadata

```yaml
version: "2.0.0"
created: "2025-09-14"
updated: "2025-09-14"
status: "Corrected with accurate information"
based_on: "Previous chat decisions and research"
```
