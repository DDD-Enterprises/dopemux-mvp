# Dopemux Phase 1 Implementation Guide
## Claude-flow + Leantime + Task-Master in Tmux

---

## Context & Goal

**Phase 1 Objective**: Create a working tmux-multiplexed development environment that orchestrates Claude-flow's 64-agent system with Leantime project management and Task-Master AI, while building towards a custom agent system.

**Success Criteria**:
- Working tmux-style interface with dopemux CLI
- Claude-flow hive-mind orchestration operational
- Leantime ↔ Task-Master ↔ Claude-flow pipeline working
- All MCP servers correctly integrated
- Letta memory system storing decisions

---

## 1. Week 1 Sprint Plan

### Day 1-2: Foundation Setup

#### Install and Configure Claude-flow

```bash
# 1. Install Claude-flow globally
npm install -g claude-flow@alpha

# 2. Initialize Claude-flow with memory
claude-flow init --with-memory --with-mcp

# 3. Verify installation
claude-flow --version
claude-flow list-agents  # Should show 64 agents

# 4. Test basic workflows
npx claude-flow@alpha sparc "create a hello world function"
npx claude-flow@alpha hive-mind spawn "research Python async patterns" --agents 3
```

#### Configure Letta Memory System

```python
# letta_config.py
import letta
from letta import Client, Agent

LETTA_CONFIG = {
    "api_key": "your-api-key",
    "base_url": "https://api.letta.ai/v1",
    "tier": "plus",  # $39/month for 10k requests
    "features": {
        "self_editing": True,
        "persistence": True,
        "multi_agent": True
    }
}

class DopemuxMemory:
    def __init__(self):
        self.client = Client(**LETTA_CONFIG)
        self.agents = {}
        
    def create_memory_agent(self, name, role):
        """Create a Letta agent for specific memory role"""
        agent = self.client.create_agent(
            name=f"dopemux_{name}",
            system_prompt=f"You manage {role} memory for Dopemux",
            memory_config={
                "type": "hierarchical",
                "tiers": ["working", "session", "persistent"]
            }
        )
        self.agents[name] = agent
        return agent
        
    def store(self, agent_name, key, value, tier="session"):
        """Store memory in specific tier"""
        agent = self.agents[agent_name]
        return agent.add_memory(
            key=key,
            value=value,
            metadata={"tier": tier}
        )
```

#### Setup MCP Servers with Correct Capabilities

```javascript
// mcp_config.json
{
  "mcpServers": {
    "zen": {
      "command": "python",
      "args": ["/Users/hue/code/zen-mcp-server/server.py"],
      "capabilities": {
        "description": "Multi-model orchestration and consensus",
        "models": ["claude-3-opus", "gpt-5", "gemini-ultra", "o3-mini"],
        "features": {
          "consensus": "Get agreement from multiple models",
          "debug": "Deep debugging with model collaboration",
          "review": "Multi-model code review",
          "planning": "DISABLED when Claude-flow active"
        }
      }
    },
    "claude-context": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "capabilities": {
        "description": "Semantic code search using embeddings",
        "NOT": "This is NOT for context management",
        "features": {
          "semantic_search": "Search code by meaning not keywords",
          "embedding_index": "ChromaDB-backed code embeddings",
          "codebase_navigation": "Find implementations and usages"
        }
      }
    },
    "conport": {
      "command": "uvx",
      "args": ["--from", "context-portal-mcp", "conport-mcp", "--mode", "stdio"],
      "capabilities": {
        "description": "Project memory and decision tracking",
        "storage": "SQLite or Graph DB backend",
        "features": {
          "log_decision": "Record architectural decisions",
          "get_decisions": "Retrieve past decisions",
          "search_patterns": "Find decision patterns"
        }
      }
    },
    "task-master-ai": {
      "command": "npx",
      "args": ["-y", "task-master-ai"],
      "capabilities": {
        "description": "PRD parsing and task management",
        "features": {
          "parse_prd": "Convert PRDs to task hierarchies",
          "task_breakdown": "Decompose complex tasks",
          "complexity_analysis": "Estimate task complexity",
          "dependency_detection": "Find task dependencies"
        }
      }
    },
    "serena": {
      "command": "uv",
      "args": ["run", "--directory", "/Users/hue/code/serena", "serena", "start-mcp-server"],
      "capabilities": {
        "description": "LSP-based code editing and refactoring",
        "features": {
          "find_symbol": "Symbol-based navigation",
          "safe_editing": "Controlled code modifications",
          "refactoring": "IDE-like refactoring operations"
        }
      }
    }
  }
}
```

### Day 3-4: Tmux Interface Implementation

#### Create Dopemux CLI Core

```python
#!/usr/bin/env python3
# dopemux.py - Main CLI entry point

import click
import libtmux
import json
import asyncio
from pathlib import Path
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live

console = Console()

class DopemuxSession:
    """Manages tmux session for Dopemux"""
    
    def __init__(self, session_name="dopemux"):
        self.server = libtmux.Server()
        self.session_name = session_name
        self.session = None
        self.config_path = Path.home() / ".dopemux"
        self.config_path.mkdir(exist_ok=True)
        
    def create_layout(self):
        """Create the standard Dopemux tmux layout"""
        # Kill existing session if present
        try:
            old_session = self.server.find_where({"session_name": self.session_name})
            if old_session:
                old_session.kill_session()
        except:
            pass
            
        # Create new session
        self.session = self.server.new_session(self.session_name)
        
        # Window 0: Orchestration
        win0 = self.session.windows[0]
        win0.rename_window("orchestration")
        pane0_0 = win0.panes[0]
        pane0_1 = win0.split_window(vertical=False)  # Split horizontally
        
        # Window 1: Execution
        win1 = self.session.new_window("execution")
        pane1_0 = win1.panes[0]
        pane1_1 = win1.split_window(vertical=False)
        
        # Window 2: Memory
        win2 = self.session.new_window("memory")
        pane2_0 = win2.panes[0]
        pane2_1 = win2.split_window(vertical=False)
        
        # Window 3: Project
        win3 = self.session.new_window("project")
        pane3_0 = win3.panes[0]
        pane3_1 = win3.split_window(vertical=False)
        
        # Start services in panes
        self.start_services({
            pane0_0: "claude-flow start --master --memory ~/.dopemux/memory.db",
            pane0_1: "claude-flow monitor",
            pane1_0: "python ~/.dopemux/active_agent.py",
            pane1_1: "pytest --watch --cov",
            pane2_0: "python ~/.dopemux/letta_monitor.py",
            pane2_1: "sqlite3 ~/.dopemux/conport.db",
            pane3_0: "leantime-mcp serve",
            pane3_1: "task-master-ai serve"
        })
        
    def start_services(self, pane_commands):
        """Start services in their respective panes"""
        for pane, command in pane_commands.items():
            pane.send_keys(command)

@click.group()
def cli():
    """Dopemux - Multiplexed AI Development Orchestration"""
    pass

@cli.command()
@click.option('--session', '-s', default='dopemux', help='Session name')
def start(session):
    """Start a new Dopemux session"""
    console.print("[bold green]Starting Dopemux session...[/bold green]")
    
    dmux = DopemuxSession(session)
    dmux.create_layout()
    
    console.print(f"[bold cyan]Session '{session}' created![/bold cyan]")
    console.print("Attach with: [yellow]tmux attach -t dopemux[/yellow]")
    
@cli.command()
@click.argument('workflow')
@click.option('--agents', '-a', default=8, help='Number of agents')
def run(workflow, agents):
    """Run a Claude-flow workflow"""
    workflows = {
        'sparc': f"npx claude-flow@alpha sparc",
        'tdd': f"npx claude-flow@alpha sparc tdd",
        'hive': f"npx claude-flow@alpha hive-mind spawn --agents {agents}",
        'swarm': f"npx claude-flow@alpha swarm --strategy consensus"
    }
    
    if workflow in workflows:
        import subprocess
        subprocess.run(workflows[workflow], shell=True)
    else:
        console.print(f"[red]Unknown workflow: {workflow}[/red]")

if __name__ == '__main__':
    cli()
```

#### Status Line Implementation

```python
# status_line.py - Real-time status monitoring
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
import asyncio
import json

class DopemuxStatus:
    def __init__(self):
        self.console = Console()
        self.metrics = {
            "active_agents": 0,
            "tokens_used": 0,
            "token_budget": 100000,
            "current_task": "Idle",
            "progress": 0,
            "coverage": 0
        }
        
    def create_layout(self):
        """Create status layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["header"].update(
            Panel(f"[bold cyan]DOPEMUX[/bold cyan] - AI Development Orchestration")
        )
        
        layout["body"].split_row(
            Layout(name="agents"),
            Layout(name="tasks"),
            Layout(name="memory")
        )
        
        return layout
        
    async def update_metrics(self):
        """Fetch metrics from various sources"""
        # Query Claude-flow for active agents
        # Query Task-Master for current tasks
        # Query Letta for memory usage
        # This would connect to actual services
        pass
        
    def render_agents_panel(self):
        """Render active agents panel"""
        table = Table(title="Active Agents")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Tokens", style="yellow")
        
        # Add active agents (would be dynamic)
        table.add_row("Coder-1", "Writing", "1,234")
        table.add_row("Tester-1", "Running", "567")
        table.add_row("Reviewer-1", "Idle", "0")
        
        return Panel(table, title="Claude-flow Agents")
```

### Day 5: Integration Testing

#### End-to-End Workflow Test

```python
# test_integration.py
import pytest
import asyncio
from dopemux import DopemuxSession
from letta_config import DopemuxMemory

@pytest.fixture
async def dopemux_session():
    """Create test Dopemux session"""
    session = DopemuxSession("test-dopemux")
    session.create_layout()
    yield session
    # Cleanup
    session.session.kill_session()

async def test_prd_to_implementation_flow():
    """Test complete PRD to implementation workflow"""
    
    # 1. Parse PRD with Task-Master
    prd_content = """
    Build a REST API endpoint for user authentication
    - POST /api/auth/login
    - Validate email and password
    - Return JWT token
    - 90% test coverage required
    """
    
    # Send to Task-Master
    tasks = await parse_prd_with_taskmaster(prd_content)
    assert len(tasks) > 0
    
    # 2. Create Leantime milestone
    milestone = await create_leantime_milestone(
        "User Authentication API",
        tasks
    )
    
    # 3. Execute with Claude-flow
    for task in tasks:
        result = await execute_with_claude_flow(
            task,
            method="tdd" if "test" in task.lower() else "sparc"
        )
        assert result.success
        
    # 4. Verify test coverage
    coverage = await check_test_coverage()
    assert coverage >= 90
    
    # 5. Store decisions in ConPort
    await store_decision(
        "authentication_method",
        "JWT with RS256 signing"
    )

async def test_multi_agent_coordination():
    """Test multiple agents working together"""
    
    # Spawn research agents
    research_result = await spawn_hive_mind(
        "Research best practices for JWT authentication",
        agents=3
    )
    
    # Implementation based on research
    implementation = await implement_with_research(
        research_result,
        agents=5
    )
    
    # Review with multiple models via Zen
    review = await multi_model_review(
        implementation,
        models=["claude", "gpt-5", "gemini"]
    )
    
    assert review.consensus_reached
```

---

## 2. Week 2 Sprint Plan

### Enhancement Tasks

```yaml
week_2_goals:
  monitoring:
    - "Real-time token usage dashboard"
    - "Agent activity visualization"
    - "Memory tier usage graphs"
    - "Error rate tracking"
    
  workflow_templates:
    - "Bug fix workflow"
    - "Feature development workflow"
    - "Code review workflow"
    - "Documentation workflow"
    
  error_recovery:
    - "Automatic Claude-flow restart"
    - "MCP server health checks"
    - "Memory sync recovery"
    - "Session restoration"
    
  performance:
    - "Response time optimization"
    - "Token usage optimization"
    - "Cache implementation"
    - "Parallel execution tuning"
```

---

## 3. Awesome-Claude-Code Patterns Integration

### Key Patterns to Implement

```yaml
from_awesome_claude_code:
  session_management:
    - "Git worktree isolation per session"
    - "Complete state restoration"
    - "Cost tracking per session"
    
  agent_patterns:
    queen_agent:
      description: "Master coordinator pattern"
      implementation: "Use Claude-flow's queen for orchestration"
      
    byzantine_consensus:
      description: "Multi-agent agreement"
      implementation: "Zen MCP for consensus operations"
      
  memory_patterns:
    crdt:
      description: "Conflict-free replicated data types"
      implementation: "Claude-flow's distributed memory"
      
    hierarchical:
      description: "Multi-tier memory"
      implementation: "Letta's tier system"
      
  workflow_patterns:
    sparc:
      stages: ["Specification", "Pseudocode", "Architecture", "Refinement", "Code"]
      
    tdd:
      stages: ["Test", "Implement", "Refactor"]
      
    swarm:
      description: "Distributed problem solving"
      consensus: "Required for completion"
```

### Hook System from ChatX

```python
# hooks.py - Implement ChatX-style hooks
import subprocess
from pathlib import Path

class DopemuxHooks:
    """ChatX-inspired hook system"""
    
    def __init__(self):
        self.hooks_dir = Path.home() / ".dopemux" / "hooks"
        self.hooks_dir.mkdir(exist_ok=True)
        
    async def pre_tool_use(self, tool_name, params):
        """Run before any tool execution"""
        # Security checks
        if self.is_dangerous_operation(tool_name, params):
            raise SecurityError(f"Blocked dangerous operation: {tool_name}")
            
        # Token budget check
        if self.would_exceed_budget(tool_name):
            raise BudgetError("Token budget exceeded")
            
    async def post_tool_use(self, tool_name, result):
        """Run after tool execution"""
        # Quality gates
        if tool_name in ["write_file", "edit_file"]:
            await self.run_linter(result.file_path)
            await self.run_tests()
            
        # Update memory
        await self.update_memory(tool_name, result)
        
    def is_dangerous_operation(self, tool, params):
        """Check for dangerous operations"""
        dangerous = [
            "rm -rf",
            "sudo rm",
            "chmod 777",
            "/etc/",
            ".env"
        ]
        return any(d in str(params) for d in dangerous)
```

---

## 4. Production Configuration

### Environment Setup

```bash
# .env.dopemux
# Claude-flow Configuration
CLAUDE_FLOW_MEMORY_PATH=~/.dopemux/memory.db
CLAUDE_FLOW_MODE=master
CLAUDE_FLOW_MAX_AGENTS=64

# Letta Configuration
LETTA_API_KEY=your-key-here
LETTA_TIER=plus
LETTA_ENDPOINT=https://api.letta.ai/v1

# MCP Servers
MCP_ZEN_PATH=/Users/hue/code/zen-mcp-server
MCP_SERENA_PATH=/Users/hue/code/serena
MCP_TIMEOUT=30

# Leantime
LEANTIME_URL=https://your-leantime-instance.com
LEANTIME_TOKEN=lt_username_hash

# Model API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Performance
TOKEN_BUDGET_DAILY=1000000
MAX_PARALLEL_AGENTS=10
CACHE_TTL=3600
```

### Docker Compose (Optional)

```yaml
# docker-compose.yml
version: '3.9'

services:
  dopemux-orchestrator:
    build: .
    environment:
      - DOPEMUX_MODE=orchestrator
    volumes:
      - ~/.dopemux:/home/dopemux/.dopemux
      - ./projects:/projects
    networks:
      - dopemux-net
      
  letta-memory:
    image: letta/memory-server:latest
    environment:
      - LETTA_API_KEY=${LETTA_API_KEY}
    volumes:
      - letta-data:/data
    networks:
      - dopemux-net
      
  redis-cache:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    networks:
      - dopemux-net
      
networks:
  dopemux-net:
    driver: bridge
    
volumes:
  letta-data:
  redis-data:
```

---

## 5. Validation Checklist

### Phase 1 Completion Criteria

```yaml
must_have:
  ✓ Claude-flow operational with 64 agents
  ✓ Letta memory system connected
  ✓ All MCP servers running with correct capabilities
  ✓ Tmux interface with dopemux CLI
  ✓ Leantime ↔ Task-Master ↔ Claude-flow pipeline
  ✓ Basic monitoring dashboard
  ✓ Session persistence
  ✓ Error recovery mechanisms
  
nice_to_have:
  ○ Full ChatX hook system
  ○ Complete Awesome-Claude-Code patterns
  ○ Docker deployment
  ○ Advanced visualization
  ○ Custom agent prototypes
```

---

## 6. Troubleshooting Guide

### Common Issues and Solutions

```yaml
issues:
  claude_flow_not_starting:
    symptom: "Claude-flow fails to initialize"
    check:
      - "npm install -g claude-flow@alpha"
      - "Node.js version >= 18"
      - "~/.dopemux/memory.db writable"
    solution: "Reinstall with npm cache clean"
    
  mcp_server_timeout:
    symptom: "MCP servers not responding"
    check:
      - "Server processes running"
      - "Correct paths in config"
      - "Dependencies installed"
    solution: "Restart with debug logging"
    
  memory_sync_issues:
    symptom: "Letta not persisting data"
    check:
      - "API key valid"
      - "Network connectivity"
      - "Rate limits not exceeded"
    solution: "Fallback to local SQLite"
    
  tmux_layout_broken:
    symptom: "Panes not arranged correctly"
    check:
      - "libtmux version >= 0.10"
      - "Terminal size adequate"
    solution: "dopemux reset-layout"
```

---

## Next Actions

### Immediate (Today)
1. Install all dependencies
2. Configure MCP servers
3. Test Claude-flow workflows
4. Create basic tmux layout
5. Verify Leantime connection

### This Week
1. Complete Phase 1 implementation
2. Run integration tests
3. Document workflows
4. Train on system usage
5. Gather feedback

---

## Document Metadata

```yaml
version: "1.0.0"
type: "Implementation Guide"
phase: "1"
focus: "Integration and orchestration"
status: "Ready for implementation"
```
