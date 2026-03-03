# Dopemux Implementation Blueprint v1.0
## Consolidated Guide from Research to Production

---

## What We're Building

**Dopemux**: A complete CLI application that serves as an AI-powered operating system for developers and creators, with five integrated platforms managed through a tmux-style interface and orchestrated by Claude-flow's 64-agent ecosystem.

---

## 1. Confirmed Technology Stack

### Core Decisions (FINAL)

```yaml
orchestration:
  primary: "Claude-flow v2.0.0-alpha"
  agents: 64 specialized agents
  performance: "84.8% SWE-Bench solve rate"
  
memory:
  primary: "Letta framework"
  pricing: "$39/month Plus tier (10k requests)"
  fallback: "SQLite + ConPort"
  
interface:
  style: "tmux multiplexed sessions"
  implementation: "Python with Rich/Textual"
  persistence: "Session state across restarts"
  
project_management:
  strategic: "Leantime MCP Server"
  tactical: "Claude-Task-Master AI"
  integration: "Two-tier task management"
  
execution:
  multi_model: "zen-mcp (NO planning mode)"
  reasoning: "sequential-thinking-mcp"
  future_content: "CrewAI (Phase 3)"
  future_blockchain: "Eliza (Phase 4)"
```

### MCP Server Stack (Corrected)

| Server | Actual Purpose | Command |
|--------|---------------|----------|
| **zen** | Multi-model orchestration (Claude, GPT-5, Gemini, O3) | `python /path/zen-mcp-server/server.py` |
| **claude-context** | Semantic code search with embeddings | `npx -y @zilliz/claude-context-mcp@latest` |
| **conport** | Project memory and decision tracking | `uvx --from context-portal-mcp conport-mcp --mode stdio` |
| **task-master-ai** | PRD parsing and task management | `npx -y task-master-ai` |
| **serena** | LSP-based code editing | `uv run --directory /path/serena serena start-mcp-server` |
| **sequential-thinking** | Deep reasoning chains | `npx -y @modelcontextprotocol/server-sequential-thinking` |
| **context7** | Library documentation | `npx -y @upstash/context7-mcp` |
| **exa** | High-signal web research | `npx -y exa-mcp` |
| **cli** | Command execution | `uvx cli-mcp-server` |
| **playwright** | Browser automation | `npx -y @playwright/mcp@latest` |
| **morphllm-fast-apply** | Fast code patches | `npx -y @morph-llm/morph-fast-apply` |
| **magic** | Utility functions | `npx -y @21st-dev/magic@latest` |

---

## 2. System Architecture (Complete)

### Five Integrated Platforms

```yaml
dopemux_platforms:
  1_development:
    status: "Phase 1-2 (immediate)"
    orchestrator: "Claude-flow"
    tools: ["UltraSlicer", "MergeOrgy", "Code review"]
    
  2_life_automation:
    status: "Phase 3 (month 2)"
    features: ["Calendar", "Email", "Health", "ADHD support"]
    tool: "ChatX conversations"
    
  3_social_media:
    status: "Phase 4 (month 3)"
    orchestrator: "CrewAI"
    features: ["Content creation", "Scheduling", "Analytics"]
    
  4_research:
    status: "Phase 2-3"
    primary: "Exa MCP"
    features: ["Web research", "Academic", "Content analysis"]
    
  5_monitoring:
    status: "Phase 5 (month 4)"
    features: ["System metrics", "Personal analytics", "Security"]
```

### Memory Architecture with Letta

```python
# Letta Integration
class DopemuxMemory:
    def __init__(self):
        self.letta = LettaClient(
            api_key=os.getenv("LETTA_API_KEY"),
            tier="plus"  # $39/month
        )
        
        self.layers = {
            "L1_working": "8K tokens, real-time",
            "L2_session": "32K tokens, 24hr TTL",
            "L3_persistent": "Unlimited, permanent"
        }
        
    async def cross_platform_store(self, platform, key, value):
        """Store with platform namespacing"""
        return await self.letta.store(f"{platform}:{key}", value)
```

---

## 3. Implementation Path (Week by Week)

### Week 1: Foundation Sprint

#### Day 1-2: Environment Setup
```bash
#!/bin/bash
# setup_dopemux.sh

# 1. Install core dependencies
npm install -g claude-flow@alpha
pip install letta rich textual libtmux
brew install tmux  # or apt-get install tmux

# 2. Create project structure
mkdir -p ~/.dopemux/{config,memory,sessions,mcp-tools}
mkdir -p ~/dopemux-project/src/{core,platforms,agents,memory}

# 3. Initialize Claude-flow
cd ~/dopemux-project
npx claude-flow@alpha init --with-memory --with-mcp --hive-mind

# 4. Configure Letta
export LETTA_API_KEY="your-key-here"
python -c "from letta import Client; Client().test_connection()"
```

#### Day 3-4: Core CLI Implementation
```python
# dopemux.py - Main CLI entry
import click
import libtmux
from pathlib import Path
from rich.console import Console

@click.group()
@click.pass_context
def cli(ctx):
    """Dopemux - AI-Powered Developer OS"""
    ctx.ensure_object(dict)
    ctx.obj['console'] = Console()
    
@cli.group()
def dev():
    """Software development platform"""
    pass
    
@dev.command()
@click.argument('task')
def code(task):
    """Start coding with Claude-flow"""
    subprocess.run([
        "npx", "claude-flow@alpha", "sparc", task
    ])
    
@dev.command()
def slice():
    """Start UltraSlicer workflow"""
    # Implement slice-based development
    pass

if __name__ == '__main__':
    cli()
```

#### Day 5: Integration Testing
```python
# test_integration.py
import pytest
import asyncio

async def test_claude_flow_connection():
    """Test Claude-flow is operational"""
    result = await run_command("npx claude-flow@alpha status")
    assert "ready" in result.lower()
    
async def test_leantime_connection():
    """Test Leantime MCP server"""
    # Connect to Leantime
    pass
    
async def test_memory_persistence():
    """Test Letta memory storage"""
    memory = DopemuxMemory()
    await memory.store("test", "key", "value")
    result = await memory.retrieve("test", "key")
    assert result == "value"
```

### Week 2: Enhanced Capabilities

#### Tasks
1. **Add all MCP servers** with correct configurations
2. **Implement tmux layout manager**
3. **Create workflow templates**
4. **Add monitoring dashboard**

```yaml
# tmux_layout.yaml
windows:
  orchestration:
    panes:
      - command: "claude-flow start --master"
        size: 70
      - command: "claude-flow monitor"
        size: 30
        
  execution:
    panes:
      - command: "dopemux dev watch"
        size: 60
      - command: "pytest --watch"
        size: 40
        
  memory:
    panes:
      - command: "dopemux memory monitor"
      - command: "sqlite3 ~/.dopemux/memory.db"
```

### Month 2: Life Automation Platform

```python
# platforms/life.py
class LifeAutomationPlatform:
    def __init__(self):
        self.agents = {
            'calendar': CalendarAgent(),
            'email': EmailAgent(),
            'health': HealthAgent()
        }
        
    async def sync_calendar(self):
        """Google Calendar integration"""
        pass
        
    async def process_email(self):
        """Gmail automation"""
        pass
        
    async def adhd_support(self):
        """ADHD-specific features"""
        return {
            'medication_reminder': self.check_medication(),
            'focus_timer': self.pomodoro_timer(),
            'energy_level': self.track_energy()
        }
```

---

## 4. Critical Implementation Details

### Routing Logic (MUST IMPLEMENT)

```python
def route_task(task, context):
    """
    CRITICAL: This is the master routing logic
    """
    # Deep reasoning tasks
    if any(keyword in task for keyword in ['prove', 'analyze why', 'root cause']):
        return {
            'pre_processor': 'sequential-thinking-mcp',
            'executor': 'claude-flow',
            'method': 'sparc'
        }
    
    # Project management
    if task.startswith('plan') or 'milestone' in task:
        return {
            'planner': 'leantime',
            'breakdown': 'task-master-ai',
            'executor': 'claude-flow'
        }
    
    # Cost-sensitive routine tasks
    if is_routine(task) and context.get('optimize_cost'):
        return {
            'handler': 'zen-mcp',
            'model': 'gemini-flash',
            'planning': False  # CRITICAL: Never enable
        }
    
    # Default: Claude-flow
    return {
        'handler': 'claude-flow',
        'method': 'tdd' if 'test' in task else 'sparc'
    }
```

### Session Management

```python
class DopemuxSession:
    """Persistent session management"""
    
    def __init__(self, name="dopemux"):
        self.name = name
        self.tmux = libtmux.Server()
        self.state_file = Path(f"~/.dopemux/sessions/{name}.json")
        
    def save_state(self):
        """Save session state for recovery"""
        state = {
            'windows': self.get_window_configs(),
            'agents': self.get_active_agents(),
            'memory_snapshot': self.memory.snapshot(),
            'timestamp': datetime.now().isoformat()
        }
        self.state_file.write_text(json.dumps(state))
        
    def restore(self):
        """Restore from saved state"""
        if self.state_file.exists():
            state = json.loads(self.state_file.read_text())
            self.restore_windows(state['windows'])
            self.restore_agents(state['agents'])
            self.memory.restore(state['memory_snapshot'])
```

### ADHD Features

```python
class ADHDSupport:
    """Neurodivergent-friendly features"""
    
    def __init__(self):
        self.focus_timer = None
        self.energy_tracker = EnergyTracker()
        self.distraction_blocker = DistractionBlocker()
        
    async def start_focus_session(self, duration=25):
        """Pomodoro-style focus session"""
        await self.distraction_blocker.enable()
        await self.save_context()
        
        # Start timer with visual progress
        self.focus_timer = Timer(duration * 60)
        self.focus_timer.on_complete = self.celebrate_completion
        
    async def track_energy(self):
        """Monitor energy levels"""
        current = await self.energy_tracker.get_level()
        
        if current < 30:
            return {
                'suggestion': 'Low energy - consider simple tasks',
                'recommended_tasks': self.get_low_energy_tasks()
            }
        elif current > 70:
            return {
                'suggestion': 'High energy - tackle complex work',
                'recommended_tasks': self.get_complex_tasks()
            }
```

---

## 5. Performance Optimization

### Token Optimization

```yaml
optimization_strategies:
  caching:
    - "Cache Claude-flow responses"
    - "Semantic similarity matching"
    - "70% hit rate target"
    
  model_routing:
    simple_tasks: "gemini-flash via zen"
    complex_tasks: "claude-opus"
    code_generation: "claude-sonnet"
    
  context_compression:
    - "Sliding window with decay"
    - "Remove redundant information"
    - "40-60% reduction target"
```

### Parallel Execution

```python
async def parallel_agent_execution(tasks):
    """Execute multiple agents in parallel"""
    
    # Claude-flow handles up to 64 agents
    batches = chunk_tasks(tasks, size=10)
    
    results = []
    for batch in batches:
        batch_results = await asyncio.gather(*[
            execute_with_agent(task) for task in batch
        ])
        results.extend(batch_results)
        
    return synthesize_results(results)
```

---

## 6. Monitoring & Debugging

### Real-time Dashboard

```python
# monitoring/dashboard.py
from rich.live import Live
from rich.table import Table

class DopemuxDashboard:
    def create_layout(self):
        table = Table(title="Dopemux Status")
        table.add_column("Component")
        table.add_column("Status")
        table.add_column("Metrics")
        
        table.add_row(
            "Claude-flow",
            "✅ Active",
            f"{self.active_agents}/64 agents"
        )
        table.add_row(
            "Memory",
            "✅ Connected",
            f"{self.memory_usage}MB"
        )
        table.add_row(
            "Tokens",
            "⚠️ 75% used",
            f"{self.tokens_used}/{self.token_budget}"
        )
        
        return table
```

### Debug Commands

```bash
# Debugging toolkit
dopemux debug --component claude-flow
dopemux debug --memory-stats
dopemux debug --agent-status
dopemux debug --session-trace

# Recovery commands  
dopemux recover --last-session
dopemux recover --from-checkpoint
dopemux rollback --to-timestamp
```

---

## 7. Production Checklist

### Pre-Launch Requirements

- [ ] Claude-flow v2.0.0-alpha installed and tested
- [ ] Letta API key configured and working
- [ ] All 12 MCP servers operational
- [ ] Leantime integration tested
- [ ] Task-Master AI connected
- [ ] Tmux session persistence working
- [ ] Memory system storing/retrieving
- [ ] Basic workflows executing
- [ ] Error recovery tested
- [ ] Monitoring dashboard active

### Quality Gates

- [ ] 90% test coverage on core modules
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Documentation complete

---

## 8. Common Pitfalls & Solutions

### Pitfall Prevention

| Issue | Solution |
|-------|----------|
| zen-mcp planning conflicts | ALWAYS disable planning mode |
| Memory sync failures | Use Letta fallback to SQLite |
| Token exhaustion | Implement aggressive caching |
| Session loss | Enable tmux persistence |
| Agent deadlocks | Set timeouts and fallbacks |

### Emergency Recovery

```bash
#!/bin/bash
# emergency_recovery.sh

# 1. Kill stuck processes
pkill -f claude-flow
pkill -f mcp-server

# 2. Clear corrupted state
rm -rf ~/.dopemux/sessions/*.lock

# 3. Restore from backup
sqlite3 ~/.dopemux/memory.db ".backup ~/.dopemux/memory.backup.db"

# 4. Restart with recovery mode
dopemux start --recover --safe-mode
```

---

## Next Steps (Immediate Actions)

1. **Today**: Install all dependencies
2. **Tomorrow**: Create basic CLI structure
3. **Day 3**: Test Claude-flow integration
4. **Day 4**: Connect MCP servers
5. **Day 5**: Run end-to-end test

---

## Success Metrics

- **Week 1**: Basic orchestration working
- **Week 2**: All dev platform features operational
- **Month 1**: Production-ready dev platform
- **Month 2**: Life automation integrated
- **Month 3**: All platforms operational

---

## Document Metadata

```yaml
version: "1.0.0"
type: "Implementation Blueprint"
status: "Ready for Execution"
combines:
  - "All research documents"
  - "Architecture decisions"
  - "Integration patterns"
  - "Production requirements"
```

*This blueprint consolidates all research and decisions into a single, actionable implementation guide.*
