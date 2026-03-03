Looking at your dopemux architecture and the need to integrate claude-squad's multiplexing, git worktree, and multi-agent capabilities, I'll create a comprehensive design document that leverages the best patterns from both systems.

## Context & Goal

**Objective**: Integrate claude-squad's core innovations (git worktree isolation, multiplexed agent sessions, and coordinated multi-agent tooling) into dopemux's existing Claude-flow orchestration architecture.

**Key Integration Points**:
- Git worktree-based session isolation for parallel agent work
- Multiplexed tmux panes with agent-specific contexts
- Coordinated multi-agent tool execution patterns
- Memory synchronization across isolated workspaces

## Assumptions

1. Claude-squad provides session isolation patterns worth adopting
2. Dopemux's Claude-flow orchestration remains the primary coordinator
3. Git worktrees provide superior isolation vs. shared directories
4. The integration should be additive, not replacing existing functionality

## Proposed Design

### Component Architecture

```yaml
claude_squad_integration:
  session_management:
    implementation: "Git worktree per agent session"
    benefits:
      - Complete isolation between agents
      - Parallel non-conflicting work
      - Clean rollback capabilities
      - Branch-based experimentation
    
  multiplexing_architecture:
    tmux_layout:
      master_session: "dopemux-squad-{project}"
      windows:
        - orchestration: "Claude-flow master + monitor"
        - squad_agents: "4-8 agent panes per window"
        - worktrees: "Git status per worktree"
        - memory: "Shared memory view"
    
  agent_tool_coordination:
    pattern: "Leader-follower with consensus"
    implementation:
      leader: "Claude-flow queen agent"
      followers: "Squad agents in worktrees"
      consensus: "zen-mcp for multi-model agreement"
```

### Session Isolation Architecture

```python
# squad_session_manager.py
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import libtmux

class SquadSessionManager:
    """Manages isolated git worktree sessions for agent squads"""
    
    def __init__(self, project_root: Path, squad_size: int = 4):
        self.project_root = project_root
        self.squad_size = squad_size
        self.worktrees: Dict[str, Path] = {}
        self.tmux_server = libtmux.Server()
        self.base_branch = "main"
        
    async def spawn_squad(self, task_id: str, agents: List[str]) -> Dict:
        """Spawn a new agent squad with isolated worktrees"""
        
        squad_session = {
            "task_id": task_id,
            "worktrees": {},
            "tmux_windows": {},
            "agents": {}
        }
        
        for i, agent_name in enumerate(agents[:self.squad_size]):
            # Create worktree for each agent
            worktree_path = await self._create_agent_worktree(
                agent_name, 
                task_id
            )
            
            # Create tmux pane for agent
            pane = await self._create_agent_pane(
                agent_name,
                worktree_path,
                window_index=i // 2  # 2 agents per window
            )
            
            squad_session["worktrees"][agent_name] = worktree_path
            squad_session["agents"][agent_name] = {
                "worktree": worktree_path,
                "pane": pane,
                "status": "active"
            }
            
        return squad_session
    
    async def _create_agent_worktree(self, agent_name: str, task_id: str) -> Path:
        """Create isolated git worktree for an agent"""
        
        branch_name = f"squad/{task_id}/{agent_name}"
        worktree_dir = self.project_root / ".dopemux" / "worktrees" / branch_name
        
        # Create new worktree
        subprocess.run([
            "git", "worktree", "add",
            "-b", branch_name,
            str(worktree_dir),
            self.base_branch
        ], cwd=self.project_root)
        
        # Initialize agent context
        context_file = worktree_dir / ".agent_context.json"
        context_file.write_text(json.dumps({
            "agent": agent_name,
            "task_id": task_id,
            "created": datetime.now().isoformat(),
            "parent_commit": self._get_current_commit()
        }))
        
        return worktree_dir
```

### Multi-Agent Tool Coordination

```python
# squad_tool_coordinator.py
from enum import Enum
from dataclasses import dataclass
import asyncio
from typing import Any, List, Optional

class CoordinationStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONSENSUS = "consensus"
    LEADER_FOLLOWER = "leader_follower"

@dataclass
class ToolInvocation:
    tool_name: str
    params: Dict[str, Any]
    agent: str
    worktree: Path
    strategy: CoordinationStrategy

class SquadToolCoordinator:
    """Coordinates tool usage across agent squad"""
    
    def __init__(self, squad_session: Dict):
        self.session = squad_session
        self.tool_queue = asyncio.Queue()
        self.execution_lock = asyncio.Lock()
        
    async def execute_tool(self, invocation: ToolInvocation) -> Any:
        """Execute tool with appropriate coordination strategy"""
        
        if invocation.strategy == CoordinationStrategy.SEQUENTIAL:
            return await self._execute_sequential(invocation)
            
        elif invocation.strategy == CoordinationStrategy.PARALLEL:
            return await self._execute_parallel(invocation)
            
        elif invocation.strategy == CoordinationStrategy.CONSENSUS:
            return await self._execute_with_consensus(invocation)
            
        elif invocation.strategy == CoordinationStrategy.LEADER_FOLLOWER:
            return await self._execute_leader_follower(invocation)
    
    async def _execute_with_consensus(self, invocation: ToolInvocation):
        """Execute tool with multi-agent consensus"""
        
        # Get proposals from multiple agents
        proposals = await asyncio.gather(*[
            self._get_agent_proposal(agent, invocation)
            for agent in self.session["agents"].keys()
        ])
        
        # Use zen-mcp for consensus
        consensus_result = await self._achieve_consensus(proposals)
        
        # Execute in appropriate worktree
        return await self._execute_in_worktree(
            consensus_result,
            invocation.worktree
        )
    
    async def _execute_in_worktree(self, command: str, worktree: Path):
        """Execute command in specific worktree context"""
        
        # Ensure we're in the right directory
        original_dir = os.getcwd()
        try:
            os.chdir(worktree)
            
            # Execute with proper isolation
            result = await asyncio.create_subprocess_exec(
                *command.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=worktree
            )
            
            stdout, stderr = await result.communicate()
            return {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "returncode": result.returncode
            }
        finally:
            os.chdir(original_dir)
```

## Workflows

### Squad Initialization Workflow

```yaml
squad_initialization:
  trigger: "Complex task requiring multiple agents"
  
  steps:
    1_analyze_task:
      actor: "Claude-flow planner"
      action: "Determine optimal squad composition"
      output: "Agent list with specializations"
      
    2_create_worktrees:
      actor: "SquadSessionManager"
      action: "Create isolated git worktrees"
      parallel: true
      output: "Worktree paths"
      
    3_spawn_tmux_layout:
      actor: "Tmux orchestrator"
      action: "Create squad-specific window layout"
      output: "Tmux session with panes"
      
    4_initialize_agents:
      actor: "Claude-flow"
      action: "Start agents in their worktrees"
      parallel: true
      output: "Active agent sessions"
      
    5_sync_memory:
      actor: "Letta"
      action: "Share initial context to all agents"
      output: "Synchronized memory state"
```

### Multi-Agent Development Workflow

```yaml
development_workflow:
  pre_hooks:
    - "Save current state to memory"
    - "Create worktree snapshots"
    
  main_flow:
    1_decompose:
      agent: "Leader (Claude-flow queen)"
      action: "Break task into subtasks"
      distribution: "Assign to squad members"
      
    2_parallel_implementation:
      agents: "Squad members"
      strategy: "Parallel in isolated worktrees"
      coordination: "Message passing via IPC"
      
    3_integration_check:
      agent: "Integration specialist"
      action: "Check compatibility across worktrees"
      tool: "MergeOrgy for conflict detection"
      
    4_consensus_review:
      agents: "All squad members"
      strategy: "Consensus via zen-mcp"
      output: "Approved changes"
      
    5_merge_changes:
      agent: "Leader"
      action: "Merge worktree branches"
      strategy: "Octopus merge or rebase"
      
  post_hooks:
    - "Update shared memory"
    - "Clean up worktrees"
    - "Archive session state"
```

## Quality Gates & Acceptance Criteria

```yaml
integration_requirements:
  performance:
    - "Worktree creation < 2 seconds"
    - "Agent coordination overhead < 15%"
    - "Memory sync latency < 500ms"
    
  isolation:
    - "No file conflicts between agents"
    - "Independent tool execution"
    - "Clean rollback capability"
    
  coordination:
    - "Consensus achieved in < 30 seconds"
    - "Tool conflicts properly queued"
    - "Deadlock detection and recovery"
    
  memory:
    - "Context shared across worktrees"
    - "Session state persisted"
    - "Pattern learning functional"
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Worktree proliferation | Disk space exhaustion | Auto-cleanup after 24h, max 20 worktrees |
| Agent coordination deadlock | Task stalls | Timeout + fallback to sequential |
| Memory sync conflicts | Inconsistent state | CRDT-based resolution |
| Git conflicts on merge | Integration failures | Pre-merge validation + MergeOrgy |
| Tmux session complexity | UI confusion | Progressive disclosure, focus mode |

## Open Questions

1. Should we maintain a single git repository or support multiple repos per squad?
2. How should we handle binary files and large assets across worktrees?
3. What's the optimal squad size for different task types?

## Next Actions

1. **Implement SquadSessionManager** class with worktree management
2. **Create tmux layout templates** for different squad sizes
3. **Build coordination protocols** for tool execution
4. **Integrate with existing Claude-flow** orchestration
5. **Add monitoring for worktree resource usage**
6. **Create cleanup routines** for abandoned sessions
7. **Test with real development workflows**

## Implementation Code Examples

### Configuration Schema

```yaml
# ~/.dopemux/squad_config.yaml
squad_settings:
  default_size: 4
  max_size: 8
  
  worktree_settings:
    base_path: ".dopemux/worktrees"
    auto_cleanup: true
    cleanup_after_hours: 24
    max_worktrees: 20
    
  coordination:
    default_strategy: "leader_follower"
    consensus_timeout: 30
    parallel_limit: 4
    
  memory_sync:
    strategy: "crdt"
    sync_interval: 5  # seconds
    conflict_resolution: "last_write_wins"
    
  tmux_layout:
    panes_per_window: 2
    status_refresh: 1  # seconds
    show_git_status: true
```

### Integration with Dopemux CLI

```python
# Extend dopemux CLI with squad commands
@cli.group()
def squad():
    """Claude-squad multi-agent commands"""
    pass

@squad.command()
@click.argument('task')
@click.option('--agents', '-a', default=4)
@click.option('--strategy', '-s', default='parallel')
def spawn(task, agents, strategy):
    """Spawn an agent squad with isolated worktrees"""
    
    manager = SquadSessionManager(Path.cwd(), agents)
    session = asyncio.run(manager.spawn_squad(task, agent_list))
    
    console.print(f"[green]Squad spawned: {session['task_id']}[/green]")
    console.print(f"Worktrees: {list(session['worktrees'].keys())}")
    
@squad.command()
def status():
    """Show active squads and their worktrees"""
    # Implementation
    pass

@squad.command()
@click.argument('squad_id')
def merge(squad_id):
    """Merge squad worktrees back to main"""
    # Implementation
    pass
```

## Self-Check

✓ **Git worktree isolation** properly designed for parallel work  
✓ **Tmux multiplexing** integrated with squad management  
✓ **Multi-agent coordination** patterns specified  
✓ **Memory synchronization** across isolated contexts  
✓ **Integration with Claude-flow** maintains compatibility  
✓ **Resource management** prevents worktree proliferation  
✓ **Clear workflows** for squad lifecycle management

This design leverages claude-squad's best patterns while maintaining dopemux's existing architecture, providing true parallel agent execution with proper isolation and coordination.
