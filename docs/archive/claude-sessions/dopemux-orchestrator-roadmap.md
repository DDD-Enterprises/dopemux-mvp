---
id: dopemux-orchestrator-roadmap
title: Dopemux Orchestrator Roadmap
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopemux Orchestrator Roadmap (explanation) for dopemux documentation and
  developer workflows.
---
# Dopemux Multi-AI Orchestrator - Implementation Roadmap

**Architecture Decision**: Hybrid (tmux TUI primary + optional web dashboard)
**Planning Method**: Incremental zen/planner methodology
**Target Model**: gpt-5 / grok-code
**Planning Date**: 2025-10-15

---

## 📋 PHASE 1: Tmux TUI MVP (Weeks 1-2) - MUST DELIVER

**Goal**: Production-ready tmux-based multi-AI orchestrator with core functionality
**Success Criteria**:
- ✅ Launch 2-4 AI instances in tmux panes
- ✅ Route commands to appropriate agents
- ✅ Auto-save context every 30 seconds
- ✅ Resume sessions after interruption
- ✅ ADHD-optimized energy-based layouts

---

### Step 1: Create tmux 4-pane layout manager

**File Paths**:
- `services/orchestrator/src/tmux_manager.py` (new)
- `services/orchestrator/src/layouts/adaptive_layout.py` (new)
- `services/orchestrator/tests/test_tmux_manager.py` (new)
- `services/orchestrator/config/layouts.yaml` (new)

**Implementation Details**:

```python
# services/orchestrator/src/tmux_manager.py
from typing import Literal
import subprocess

class TmuxLayoutManager:
    """ADHD-optimized adaptive tmux layout manager"""

    def __init__(self, session_name: str = "dopemux"):
        self.session_name = session_name
        self.panes: dict[str, str] = {}  # pane_id -> agent_type

    def create_layout(self,
                     energy_level: Literal["low", "medium", "high"],
                     num_agents: int = 2) -> dict[str, str]:
        """
        Create adaptive layout based on ADHD energy level

        Energy levels:
        - low: 2 panes (1 active, 1 context)
        - medium: 3 panes (2 active, 1 context)
        - high: 4 panes (3 active, 1 monitoring)
        """
        layout_config = self._get_layout_config(energy_level, num_agents)
        return self._apply_layout(layout_config)

    def _get_layout_config(self, energy: str, num: int) -> dict:
        """Load layout from config based on energy and agent count"""
        pass

    def _apply_layout(self, config: dict) -> dict[str, str]:
        """Apply tmux layout and return pane mappings"""
        pass
```

**Dependencies**:
- **Required Before**: None (first step)
- **External Dependencies**:
  - tmux installed on system
  - Python 3.11+ with subprocess module
  - PyYAML for config parsing

**Effort Estimate**:
- **Focus Blocks**: 4 blocks (100 minutes)
  - Block 1: Layout manager class structure (25 min)
  - Block 2: Energy-based layout logic (25 min)
  - Block 3: Tmux command integration (25 min)
  - Block 4: Unit tests and validation (25 min)

**ADHD Considerations**:
- **Complexity Score**: 0.35 (Low-Medium)
- **Energy Required**: Medium
- **Mental Model**: Clear (tmux pane creation)
- **Break Points**: After each focus block
- **Context Switching Risk**: Low (isolated module)

**Validation Criteria**:
```bash
# Success indicators:
✅ Can create tmux session with 2-4 panes
✅ Layout adapts to energy level input
✅ Pane IDs are tracked and retrievable
✅ Tests pass with >90% coverage

# Test commands:
pytest services/orchestrator/tests/test_tmux_manager.py -v
python -m orchestrator.tmux_manager --energy=low --agents=2
tmux list-panes -t dopemux  # Should show correct count
```

**Risk Assessment**:
- **⚠️ Risk**: Tmux not installed or incompatible version
  - **Mitigation**: Add version check (tmux >= 3.0)
  - **Fallback**: Provide installation instructions

- **⚠️ Risk**: Pane creation fails on some terminals
  - **Mitigation**: Test on iTerm2, Terminal.app, Alacritty
  - **Fallback**: Graceful degradation to 2-pane layout

- **⚠️ Risk**: Energy level detection unclear for users
  - **Mitigation**: Provide visual indicators and defaults
  - **Fallback**: Always default to "medium" if uncertain

**Branch Points**:
- **Decision Point**: Layout persistence strategy
  - Option A: Store in ConPort (recommended)
  - Option B: Local config file
  - **Recommendation**: ConPort for cross-session consistency

---

### Step 2: Implement chat command parser (slash commands)

**File Paths**:
- `services/orchestrator/src/command_parser.py` (new)
- `services/orchestrator/src/commands/` (new directory)
  - `__init__.py`
  - `research_commands.py`
  - `plan_commands.py`
  - `implement_commands.py`
  - `delegate_commands.py`
- `services/orchestrator/tests/test_command_parser.py` (new)

**Implementation Details**:

```python
# services/orchestrator/src/command_parser.py
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class CommandMode(Enum):
    RESEARCH = "research"
    PLAN = "plan"
    IMPLEMENT = "implement"
    DELEGATE = "delegate"
    DEBUG = "debug"

@dataclass
class ParsedCommand:
    mode: CommandMode
    target_agents: list[str]  # ["claude", "gemini", "grok"]
    command: str
    context: dict
    parallel: bool = False

class CommandParser:
    """Parse user slash commands and route to appropriate agents"""

    COMMAND_PATTERNS = {
        "/research": CommandMode.RESEARCH,
        "/plan": CommandMode.PLAN,
        "/implement": CommandMode.IMPLEMENT,
        "/delegate": CommandMode.DELEGATE,
        "/debug": CommandMode.DEBUG,
    }

    def parse(self, user_input: str) -> ParsedCommand:
        """
        Parse slash command and return routing info

        Examples:
        - /research "Next.js 14 best practices" → claude + gemini
        - /implement @ui-component → grok (Magic MCP)
        - /delegate --parallel [task1, task2] → all agents
        """
        pass

    def route_to_agents(self, parsed: ParsedCommand) -> dict[str, str]:
        """Determine which agents should receive command"""
        pass
```

**Dependencies**:
- **Required Before**: Step 1 (need pane IDs for routing)
- **External Dependencies**:
  - Python dataclasses
  - Regex for command parsing
  - ConPort MCP for context retrieval

**Effort Estimate**:
- **Focus Blocks**: 5 blocks (125 minutes)
  - Block 1: Command parser core (25 min)
  - Block 2: Routing logic (25 min)
  - Block 3: Research/Plan/Implement commands (25 min)
  - Block 4: Delegate command with parallel support (25 min)
  - Block 5: Tests and edge cases (25 min)

**ADHD Considerations**:
- **Complexity Score**: 0.45 (Medium)
- **Energy Required**: Medium-High
- **Mental Model**: Moderate (parsing + routing logic)
- **Break Points**: After each command type implementation
- **Context Switching Risk**: Medium (multiple command types)

**Validation Criteria**:
```bash
# Success indicators:
✅ Parse all 5 command types correctly
✅ Route to correct agents based on mode
✅ Handle parallel flag for delegation
✅ Extract context from user input

# Test commands:
pytest services/orchestrator/tests/test_command_parser.py -v

# Manual validation:
echo "/research Next.js patterns" | python -m orchestrator.command_parser
# Expected: {mode: RESEARCH, agents: ["claude", "gemini"]}
```

**Risk Assessment**:
- **⚠️ Risk**: Command syntax too complex for ADHD users
  - **Mitigation**: Provide autocomplete and examples
  - **Fallback**: Simple natural language fallback

- **⚠️ Risk**: Ambiguous routing (multiple valid agents)
  - **Mitigation**: Use ConPort decision history for precedent
  - **Fallback**: Prompt user for clarification

- **⚠️ Risk**: Context extraction fails for complex queries
  - **Mitigation**: Use Zen consensus for ambiguous inputs
  - **Fallback**: Pass raw input to most capable agent

**Branch Points**:
- **Decision Point**: Autocomplete implementation
  - Option A: Readline-based (CLI)
  - Option B: fzf integration (recommended for tmux)
  - **Recommendation**: fzf for visual ADHD-friendly selection

---

### Step 3: Build agent spawner (launch Claude/Gemini/Grok in panes)

**File Paths**:
- `services/orchestrator/src/agent_spawner.py` (new)
- `services/orchestrator/src/agents/` (new directory)
  - `__init__.py`
  - `claude_agent.py`
  - `gemini_agent.py`
  - `grok_agent.py`
  - `base_agent.py`
- `services/orchestrator/config/agent_configs.yaml` (new)
- `services/orchestrator/tests/test_agent_spawner.py` (new)

**Implementation Details**:

```python
# services/orchestrator/src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Optional

class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, pane_id: str, config: dict):
        self.pane_id = pane_id
        self.config = config
        self.process: Optional[subprocess.Popen] = None

    @abstractmethod
    def launch(self) -> bool:
        """Launch agent in tmux pane"""
        pass

    @abstractmethod
    def send_command(self, cmd: str) -> None:
        """Send command to agent via tmux"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify agent is responsive"""
        pass

# services/orchestrator/src/agent_spawner.py
from agents.base_agent import BaseAgent
from agents.claude_agent import ClaudeAgent
from agents.gemini_agent import GeminiAgent
from agents.grok_agent import GrokAgent

class AgentSpawner:
    """Spawn and manage AI agents in tmux panes"""

    AGENT_CLASSES = {
        "claude": ClaudeAgent,
        "gemini": GeminiAgent,
        "grok": GrokAgent,
    }

    def __init__(self, tmux_manager):
        self.tmux_manager = tmux_manager
        self.active_agents: dict[str, BaseAgent] = {}

    def spawn(self, agent_type: str, pane_id: str) -> BaseAgent:
        """Spawn agent in specified pane"""
        agent_class = self.AGENT_CLASSES[agent_type]
        agent = agent_class(pane_id, self._load_config(agent_type))

        if agent.launch():
            self.active_agents[pane_id] = agent
            return agent
        else:
            raise RuntimeError(f"Failed to launch {agent_type} in {pane_id}")

    def spawn_default_layout(self, energy_level: str) -> dict[str, BaseAgent]:
        """Spawn agents based on energy level"""
        # Low energy: Claude + Gemini
        # Medium: Claude + Gemini + Grok
        # High: Claude + Gemini + Grok + monitoring pane
        pass
```

**Dependencies**:
- **Required Before**:
  - Step 1 (tmux layout manager)
  - Step 2 (command parser for agent routing)
- **External Dependencies**:
  - Claude API key (ANTHROPIC_API_KEY)
  - Gemini API key (GOOGLE_API_KEY)
  - Grok API key (XAI_API_KEY)
  - API client libraries

**Effort Estimate**:
- **Focus Blocks**: 6 blocks (150 minutes)
  - Block 1: BaseAgent abstraction (25 min)
  - Block 2: ClaudeAgent implementation (25 min)
  - Block 3: GeminiAgent implementation (25 min)
  - Block 4: GrokAgent implementation (25 min)
  - Block 5: AgentSpawner orchestration (25 min)
  - Block 6: Tests and health checks (25 min)

**ADHD Considerations**:
- **Complexity Score**: 0.65 (Medium-High)
- **Energy Required**: High
- **Mental Model**: Complex (multiple agents, API interactions)
- **Break Points**: After each agent implementation
- **Context Switching Risk**: High (3 different APIs)
- **Recommendation**: Implement one agent per day

**Validation Criteria**:
```bash
# Success indicators:
✅ All 3 agents launch successfully in panes
✅ Health checks pass for each agent
✅ Agents respond to test commands
✅ Graceful failure if API key missing

# Test commands:
pytest services/orchestrator/tests/test_agent_spawner.py -v

# Manual validation:
python -m orchestrator.agent_spawner --spawn=claude --pane=0
tmux capture-pane -t dopemux:0 -p | grep "Claude"  # Should see Claude prompt
```

**Risk Assessment**:
- **🚨 CRITICAL**: API keys not configured
  - **Mitigation**: Check for keys on startup, provide clear error messages
  - **Fallback**: Spawn only agents with valid keys

- **⚠️ Risk**: Agent crashes or becomes unresponsive
  - **Mitigation**: Implement health checks every 30 seconds
  - **Fallback**: Auto-restart with exponential backoff

- **⚠️ Risk**: Tmux pane communication fails
  - **Mitigation**: Use tmux send-keys with error handling
  - **Fallback**: Log failures to ConPort for debugging

- **⚠️ Risk**: Resource exhaustion (too many agents)
  - **Mitigation**: Limit to 4 concurrent agents max
  - **Fallback**: Queue additional agents

**Branch Points**:
- **Decision Point**: Agent communication protocol
  - Option A: Tmux send-keys (simple, recommended for MVP)
  - Option B: Unix sockets (more robust, future enhancement)
  - **Recommendation**: Tmux send-keys for MVP, socket upgrade in Phase 2

---

### Step 4: Implement TmuxCapture message abstraction

**File Paths**:
- `services/orchestrator/src/message_bus.py` (new)
- `services/orchestrator/src/capture/tmux_capture.py` (new)
- `services/orchestrator/src/capture/message_extractor.py` (new)
- `services/orchestrator/tests/test_message_bus.py` (new)
- `services/orchestrator/config/message_patterns.yaml` (new)

**Implementation Details**:

```python
# services/orchestrator/src/message_bus.py
from typing import Protocol, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    """Universal message format for cross-agent communication"""
    source: str  # "claude", "gemini", "grok", "user"
    target: Optional[str]  # None = broadcast
    content: str
    timestamp: datetime
    message_type: str  # "command", "response", "status", "error"
    metadata: dict

class MessageBusProtocol(Protocol):
    """Abstract message bus interface"""
    def publish(self, message: Message) -> None: ...
    def subscribe(self, agent_id: str, callback) -> None: ...
    def get_history(self, agent_id: str, limit: int = 50) -> list[Message]: ...

class TmuxMessageBus:
    """
    In-memory message bus using tmux capture-pane

    Design: Start simple (no Redis), add Redis only if needed
    """

    def __init__(self, tmux_manager):
        self.tmux_manager = tmux_manager
        self.history: list[Message] = []
        self.subscribers: dict[str, list[callable]] = {}

    def publish(self, message: Message) -> None:
        """Publish message to subscribers"""
        self.history.append(message)

        # Route to target or broadcast
        if message.target:
            self._send_to_agent(message.target, message)
        else:
            self._broadcast(message)

    def _send_to_agent(self, agent_id: str, message: Message) -> None:
        """Send message to specific agent's pane"""
        pane_id = self.tmux_manager.get_pane_id(agent_id)
        formatted = self._format_message(message)
        self.tmux_manager.send_to_pane(pane_id, formatted)

    def _format_message(self, message: Message) -> str:
        """Format message for agent consumption"""
        # Simple format for MVP, can enhance later
        return f"[{message.source}]: {message.content}"

# services/orchestrator/src/capture/tmux_capture.py
import subprocess
import re

class TmuxCapture:
    """Capture and parse tmux pane output"""

    def __init__(self, pane_id: str):
        self.pane_id = pane_id
        self.last_capture_line = 0

    def capture_new_output(self) -> str:
        """Capture only new lines since last capture"""
        full_output = subprocess.check_output([
            "tmux", "capture-pane", "-t", self.pane_id, "-p"
        ]).decode("utf-8")

        lines = full_output.split("\n")
        new_lines = lines[self.last_capture_line:]
        self.last_capture_line = len(lines)

        return "\n".join(new_lines)

    def extract_agent_response(self, output: str) -> Optional[str]:
        """Extract structured response from agent output"""
        # Pattern matching for Claude/Gemini/Grok responses
        # This will need to be tuned per agent
        pass
```

**Dependencies**:
- **Required Before**:
  - Step 1 (tmux pane management)
  - Step 3 (agents must be spawned to capture output)
- **External Dependencies**:
  - tmux capture-pane functionality
  - Python regex for response parsing

**Effort Estimate**:
- **Focus Blocks**: 5 blocks (125 minutes)
  - Block 1: Message data structure (25 min)
  - Block 2: TmuxMessageBus implementation (25 min)
  - Block 3: TmuxCapture with incremental parsing (25 min)
  - Block 4: Message extraction patterns (25 min)
  - Block 5: Tests and validation (25 min)

**ADHD Considerations**:
- **Complexity Score**: 0.55 (Medium)
- **Energy Required**: Medium-High
- **Mental Model**: Moderate (message routing concepts)
- **Break Points**: After each major component
- **Context Switching Risk**: Medium (parsing multiple agent formats)

**Validation Criteria**:
```bash
# Success indicators:
✅ Capture new output from tmux panes incrementally
✅ Parse agent responses correctly
✅ Route messages to correct targets
✅ Maintain message history

# Test commands:
pytest services/orchestrator/tests/test_message_bus.py -v

# Manual validation:
python -m orchestrator.message_bus --test-publish
# Send message to pane, verify it appears
tmux capture-pane -t dopemux:0 -p | tail -5
```

**Risk Assessment**:
- **⚠️ Risk**: Agent response format changes unexpectedly
  - **Mitigation**: Use flexible regex patterns, version detection
  - **Fallback**: Capture raw output if parsing fails

- **⚠️ Risk**: High message volume causes memory issues
  - **Mitigation**: Implement rolling history (keep last 500 messages)
  - **Fallback**: Persist to ConPort if memory exceeds threshold

- **⚠️ Risk**: Tmux capture-pane latency
  - **Mitigation**: Capture only new content, not full pane
  - **Fallback**: Reduce capture frequency if system load high

**Branch Points**:
- **Decision Point**: When to add Redis?
  - Trigger: Message volume > 1000/hour OR multi-process orchestrator needed
  - **Current Plan**: Start without Redis, monitor performance
  - **Future Enhancement**: Add RedisMessageBus as drop-in replacement

---

### Step 5: Integrate ConPort for auto-save checkpoints

**File Paths**:
- `services/orchestrator/src/checkpoint_manager.py` (new)
- `services/orchestrator/src/integrations/conport_client.py` (new)
- `services/orchestrator/tests/test_checkpoint_manager.py` (new)

**Implementation Details**:

```python
# services/orchestrator/src/checkpoint_manager.py
from typing import Optional
from datetime import datetime, timedelta
import asyncio

class CheckpointManager:
    """
    ADHD-optimized auto-save checkpoint system

    Auto-save every 30 seconds to preserve context during interruptions
    """

    CHECKPOINT_INTERVAL = 30  # seconds

    def __init__(self, conport_client, message_bus):
        self.conport = conport_client
        self.message_bus = message_bus
        self.last_checkpoint: Optional[datetime] = None
        self.checkpoint_task: Optional[asyncio.Task] = None

    async def start_auto_checkpoint(self):
        """Start background checkpoint loop"""
        self.checkpoint_task = asyncio.create_task(self._checkpoint_loop())

    async def _checkpoint_loop(self):
        """Background task to checkpoint every 30 seconds"""
        while True:
            await asyncio.sleep(self.CHECKPOINT_INTERVAL)
            await self.save_checkpoint()

    async def save_checkpoint(self):
        """Save current orchestrator state to ConPort"""
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "active_agents": self._get_active_agents(),
            "message_history": self.message_bus.get_history(limit=50),
            "current_command": self._get_current_command(),
            "energy_level": self._detect_energy_level(),
            "layout": self._get_layout_state(),
        }

        # Save to ConPort active_context
        await self.conport.update_active_context(
            workspace_id="/Users/hue/code/dopemux-mvp",
            patch_content={
                "orchestrator_checkpoint": checkpoint_data,
                "last_checkpoint": datetime.now().isoformat()
            }
        )

        self.last_checkpoint = datetime.now()

    async def restore_checkpoint(self) -> Optional[dict]:
        """Restore orchestrator state from ConPort"""
        context = await self.conport.get_active_context(
            workspace_id="/Users/hue/code/dopemux-mvp"
        )

        return context.get("orchestrator_checkpoint")

    def _get_active_agents(self) -> list[dict]:
        """Get current agent states"""
        pass

    def _get_current_command(self) -> Optional[str]:
        """Get last user command"""
        pass

    def _detect_energy_level(self) -> str:
        """Infer current energy level from activity patterns"""
        # Could analyze message frequency, command complexity
        pass

# services/orchestrator/src/integrations/conport_client.py
import httpx
from typing import Optional

class ConPortClient:
    """Async client for ConPort MCP"""

    def __init__(self, base_url: str = "http://localhost:5455"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def update_active_context(self, workspace_id: str, patch_content: dict):
        """Update active context with patch"""
        response = await self.client.post(
            f"{self.base_url}/mcp/conport/update_active_context",
            json={
                "workspace_id": workspace_id,
                "patch_content": patch_content
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_active_context(self, workspace_id: str) -> dict:
        """Get current active context"""
        response = await self.client.get(
            f"{self.base_url}/mcp/conport/get_active_context",
            params={"workspace_id": workspace_id}
        )
        response.raise_for_status()
        return response.json()
```

**Dependencies**:
- **Required Before**:
  - Step 3 (agents to checkpoint)
  - Step 4 (message bus to save history)
- **External Dependencies**:
  - ConPort MCP running (port 5455)
  - httpx for async HTTP
  - asyncio for background tasks

**Effort Estimate**:
- **Focus Blocks**: 4 blocks (100 minutes)
  - Block 1: ConPort client wrapper (25 min)
  - Block 2: Checkpoint data collection (25 min)
  - Block 3: Auto-save loop (25 min)
  - Block 4: Restore logic and tests (25 min)

**ADHD Considerations**:
- **Complexity Score**: 0.40 (Medium)
- **Energy Required**: Medium
- **Mental Model**: Clear (save/restore concept)
- **Break Points**: After each component
- **Context Switching Risk**: Low (async but isolated)
- **ADHD Benefit**: HIGH - enables interruption recovery

**Validation Criteria**:
```bash
# Success indicators:
✅ Checkpoint saved every 30 seconds
✅ ConPort active_context updated
✅ Restore retrieves last checkpoint
✅ No data loss during interruptions

# Test commands:
pytest services/orchestrator/tests/test_checkpoint_manager.py -v

# Manual validation:
# 1. Start orchestrator, send command
# 2. Wait 35 seconds
# 3. Check ConPort:
curl http://localhost:5455/mcp/conport/get_active_context?workspace_id=/Users/hue/code/dopemux-mvp
# Should see orchestrator_checkpoint with recent timestamp

# 4. Kill orchestrator
# 5. Restart and verify restore:
python -m orchestrator.main --restore
# Should show: "Restored session from 2025-10-15 14:30:15"
```

**Risk Assessment**:
- **⚠️ Risk**: ConPort unavailable during checkpoint
  - **Mitigation**: Retry with exponential backoff (max 3 attempts)
  - **Fallback**: Cache locally, sync when ConPort returns

- **⚠️ Risk**: Checkpoint data too large (>1MB)
  - **Mitigation**: Limit message history to 50 recent messages
  - **Fallback**: Compress with gzip before saving

- **⚠️ Risk**: Auto-save interrupts user during flow state
  - **Mitigation**: Make saves non-blocking (async)
  - **Fallback**: None needed - async prevents interruption

**Branch Points**:
- **Decision Point**: Checkpoint granularity
  - Option A: 30-second interval (recommended for ADHD)
  - Option B: On-command basis (more efficient but risky)
  - **Recommendation**: 30-second for MVP, make configurable later

---

### Step 6: Build basic command routing (research/plan/implement modes)

**File Paths**:
- `services/orchestrator/src/router.py` (new)
- `services/orchestrator/src/modes/` (new directory)
  - `__init__.py`
  - `research_mode.py`
  - `plan_mode.py`
  - `implement_mode.py`
  - `delegate_mode.py`
- `services/orchestrator/config/routing_rules.yaml` (new)
- `services/orchestrator/tests/test_router.py` (new)

**Implementation Details**:

```python
# services/orchestrator/src/router.py
from typing import Optional
from command_parser import ParsedCommand, CommandMode
from message_bus import Message, MessageBusProtocol

class CommandRouter:
    """
    Route commands to appropriate agents based on mode

    Routing Rules:
    - RESEARCH: Claude + Gemini (parallel consensus)
    - PLAN: Grok (zen/planner) primary, Claude validation
    - IMPLEMENT: Grok (code generation) + Claude (review)
    - DELEGATE: All agents in parallel
    - DEBUG: Claude (zen/debug) primary
    """

    def __init__(self, message_bus: MessageBusProtocol, agent_spawner):
        self.message_bus = message_bus
        self.agent_spawner = agent_spawner
        self.routing_rules = self._load_routing_rules()

    def route(self, parsed_command: ParsedCommand) -> list[Message]:
        """
        Route parsed command to appropriate agent(s)

        Returns: List of messages sent to agents
        """
        mode_handler = self._get_mode_handler(parsed_command.mode)
        messages = mode_handler.create_messages(parsed_command)

        for message in messages:
            self.message_bus.publish(message)

        return messages

    def _get_mode_handler(self, mode: CommandMode):
        """Get appropriate mode handler"""
        handlers = {
            CommandMode.RESEARCH: ResearchModeHandler,
            CommandMode.PLAN: PlanModeHandler,
            CommandMode.IMPLEMENT: ImplementModeHandler,
            CommandMode.DELEGATE: DelegateModeHandler,
        }
        return handlers[mode](self.agent_spawner)

# services/orchestrator/src/modes/research_mode.py
class ResearchModeHandler:
    """
    Research mode: Parallel consensus between Claude and Gemini

    Workflow:
    1. Send research query to Claude and Gemini in parallel
    2. Collect responses
    3. Use Zen consensus to synthesize findings
    4. Return synthesized result to user
    """

    def __init__(self, agent_spawner):
        self.agent_spawner = agent_spawner

    def create_messages(self, parsed_command: ParsedCommand) -> list[Message]:
        """Create parallel research messages"""
        claude_msg = Message(
            source="orchestrator",
            target="claude",
            content=f"Research: {parsed_command.command}",
            timestamp=datetime.now(),
            message_type="command",
            metadata={"mode": "research", "parallel_id": "research-1"}
        )

        gemini_msg = Message(
            source="orchestrator",
            target="gemini",
            content=f"Research: {parsed_command.command}",
            timestamp=datetime.now(),
            message_type="command",
            metadata={"mode": "research", "parallel_id": "research-1"}
        )

        return [claude_msg, gemini_msg]

# services/orchestrator/src/modes/plan_mode.py
class PlanModeHandler:
    """
    Plan mode: Grok (zen/planner) primary, Claude validation

    Workflow:
    1. Send to Grok for incremental planning (zen/planner)
    2. Grok builds plan step-by-step
    3. Claude reviews final plan for completeness
    4. Return validated plan to user
    """

    def create_messages(self, parsed_command: ParsedCommand) -> list[Message]:
        """Create planning message for Grok"""
        grok_msg = Message(
            source="orchestrator",
            target="grok",
            content=f"Use zen/planner: {parsed_command.command}",
            timestamp=datetime.now(),
            message_type="command",
            metadata={"mode": "plan", "validator": "claude"}
        )

        return [grok_msg]

# services/orchestrator/src/modes/implement_mode.py
class ImplementModeHandler:
    """
    Implement mode: Grok (code gen) + Claude (review)

    Workflow:
    1. Grok generates implementation
    2. Claude reviews for quality/security
    3. If approved, apply changes
    4. If issues found, Grok revises
    """

    def create_messages(self, parsed_command: ParsedCommand) -> list[Message]:
        """Create implementation messages"""
        # Implementation details
        pass
```

**Dependencies**:
- **Required Before**:
  - Step 2 (command parser)
  - Step 3 (agent spawner)
  - Step 4 (message bus)
- **External Dependencies**: None (uses existing components)

**Effort Estimate**:
- **Focus Blocks**: 5 blocks (125 minutes)
  - Block 1: Router core logic (25 min)
  - Block 2: Research mode handler (25 min)
  - Block 3: Plan mode handler (25 min)
  - Block 4: Implement mode handler (25 min)
  - Block 5: Tests and routing validation (25 min)

**ADHD Considerations**:
- **Complexity Score**: 0.50 (Medium)
- **Energy Required**: Medium
- **Mental Model**: Moderate (routing logic)
- **Break Points**: After each mode handler
- **Context Switching Risk**: Medium (3 different modes)

**Validation Criteria**:
```bash
# Success indicators:
✅ Commands route to correct agents based on mode
✅ Parallel execution for research/delegate modes
✅ Sequential validation for plan/implement modes
✅ Routing rules configurable via YAML

# Test commands:
pytest services/orchestrator/tests/test_router.py -v

# Manual validation:
# Send research command:
echo "/research Next.js patterns" | python -m orchestrator.main
# Expected: Messages sent to both Claude and Gemini panes

# Send plan command:
echo "/plan authentication system" | python -m orchestrator.main
# Expected: Message sent to Grok pane with zen/planner prefix
```

**Risk Assessment**:
- **⚠️ Risk**: Agent not available when routing
  - **Mitigation**: Health check before routing, spawn if needed
  - **Fallback**: Route to available agent with capability

- **⚠️ Risk**: Mode detection incorrect for ambiguous commands
  - **Mitigation**: Use ConPort decision history for precedent
  - **Fallback**: Prompt user for mode clarification

- **⚠️ Risk**: Routing rules become too complex
  - **Mitigation**: Keep rules simple and explicit in YAML
  - **Fallback**: Default to Claude for unknown modes

**Branch Points**:
- **Decision Point**: Dynamic routing based on agent load
  - Option A: Static routing (MVP)
  - Option B: Load-aware routing (future enhancement)
  - **Recommendation**: Static for MVP, add load balancing in Phase 2

---

### Step 7: Create resume flow for session restoration

**File Paths**:
- `services/orchestrator/src/session_manager.py` (new)
- `services/orchestrator/src/resume/` (new directory)
  - `__init__.py`
  - `state_restorer.py`
  - `pane_restorer.py`
  - `agent_restorer.py`
- `services/orchestrator/tests/test_session_manager.py` (new)

**Implementation Details**:

```python
# services/orchestrator/src/session_manager.py
from typing import Optional
from checkpoint_manager import CheckpointManager
from agent_spawner import AgentSpawner
from tmux_manager import TmuxLayoutManager

class SessionManager:
    """
    ADHD-optimized session management with resume capability

    Features:
    - Restore exact pane layout
    - Re-spawn agents in same panes
    - Restore message history
    - Resume interrupted commands
    - Gentle re-orientation message
    """

    def __init__(self, checkpoint_manager: CheckpointManager,
                 agent_spawner: AgentSpawner,
                 tmux_manager: TmuxLayoutManager):
        self.checkpoint_manager = checkpoint_manager
        self.agent_spawner = agent_spawner
        self.tmux_manager = tmux_manager

    async def start_session(self, resume: bool = True) -> dict:
        """
        Start new session or resume previous

        Args:
            resume: If True, attempt to restore last checkpoint

        Returns:
            Session info including restored state
        """
        if resume:
            checkpoint = await self.checkpoint_manager.restore_checkpoint()
            if checkpoint:
                return await self._restore_session(checkpoint)

        return await self._start_fresh_session()

    async def _restore_session(self, checkpoint: dict) -> dict:
        """
        Restore session from checkpoint

        Steps:
        1. Recreate tmux layout
        2. Re-spawn agents in same panes
        3. Restore message history
        4. Show re-orientation message
        5. Resume interrupted command if any
        """
        print("🔄 Restoring session...")

        # 1. Recreate layout
        layout = checkpoint.get("layout")
        self.tmux_manager.recreate_layout(layout)

        # 2. Re-spawn agents
        agents_info = checkpoint.get("active_agents", [])
        for agent_info in agents_info:
            await self.agent_spawner.spawn(
                agent_type=agent_info["type"],
                pane_id=agent_info["pane_id"]
            )

        # 3. Restore message history (display last 10 messages)
        history = checkpoint.get("message_history", [])
        self._display_history_summary(history[-10:])

        # 4. Re-orientation message
        self._show_reorientation(checkpoint)

        # 5. Resume interrupted command
        current_command = checkpoint.get("current_command")
        if current_command:
            print(f"\n💡 You were working on: {current_command}")
            resume_choice = input("Resume this command? (y/n): ")
            if resume_choice.lower() == "y":
                # Re-route command
                pass

        return {
            "status": "restored",
            "checkpoint_time": checkpoint.get("timestamp"),
            "agents_restored": len(agents_info),
            "messages_restored": len(history)
        }

    def _show_reorientation(self, checkpoint: dict):
        """
        Gentle re-orientation message for ADHD context recovery

        Example:
        ╔═══════════════════════════════════════════════╗
        ║  Welcome back! Here's where you left off:    ║
        ║                                               ║
        ║  📍 Working on: Authentication system         ║
        ║  🕐 Last active: 45 minutes ago               ║
        ║  ⚡ Energy level: Medium                      ║
        ║  🎯 Next step: Implement JWT validation      ║
        ╚═══════════════════════════════════════════════╝
        """
        from datetime import datetime, timedelta

        checkpoint_time = datetime.fromisoformat(checkpoint["timestamp"])
        time_ago = datetime.now() - checkpoint_time

        print("\n" + "═" * 50)
        print("  Welcome back! Here's where you left off:")
        print("═" * 50)
        print(f"  📍 Working on: {checkpoint.get('current_command', 'Unknown')}")
        print(f"  🕐 Last active: {self._format_time_ago(time_ago)}")
        print(f"  ⚡ Energy level: {checkpoint.get('energy_level', 'Unknown')}")

        # Suggest next step based on context
        next_step = self._suggest_next_step(checkpoint)
        if next_step:
            print(f"  🎯 Suggested next: {next_step}")
        print("═" * 50 + "\n")

    def _suggest_next_step(self, checkpoint: dict) -> Optional[str]:
        """Infer next step from checkpoint context"""
        # Could use ConPort to find related tasks
        # Or analyze message history for incomplete items
        pass

    async def _start_fresh_session(self) -> dict:
        """Start new session from scratch"""
        print("🚀 Starting fresh session...")

        # Prompt for energy level
        energy = input("Energy level? (low/medium/high) [medium]: ") or "medium"

        # Create default layout
        layout = self.tmux_manager.create_layout(
            energy_level=energy,
            num_agents=2 if energy == "low" else 3
        )

        # Spawn default agents
        if energy == "low":
            await self.agent_spawner.spawn("claude", layout["panes"][0])
            await self.agent_spawner.spawn("gemini", layout["panes"][1])
        else:
            await self.agent_spawner.spawn("claude", layout["panes"][0])
            await self.agent_spawner.spawn("gemini", layout["panes"][1])
            await self.agent_spawner.spawn("grok", layout["panes"][2])

        print(f"✅ Session started with {energy} energy layout\n")

        return {
            "status": "new",
            "energy_level": energy,
            "agents_spawned": 2 if energy == "low" else 3
        }
```

**Dependencies**:
- **Required Before**: ALL previous steps (1-6)
  - Step 5 (checkpoint manager for restore)
  - Step 3 (agent spawner)
  - Step 1 (tmux layout manager)
- **External Dependencies**: ConPort for checkpoint retrieval

**Effort Estimate**:
- **Focus Blocks**: 4 blocks (100 minutes)
  - Block 1: Session start/restore logic (25 min)
  - Block 2: Re-orientation UI (25 min)
  - Block 3: Agent/layout restoration (25 min)
  - Block 4: Tests and edge cases (25 min)

**ADHD Considerations**:
- **Complexity Score**: 0.45 (Medium)
- **Energy Required**: Medium
- **Mental Model**: Clear (save/resume concept familiar)
- **Break Points**: After each restoration component
- **Context Switching Risk**: Low (linear restoration flow)
- **ADHD Benefit**: CRITICAL - primary ADHD feature

**Validation Criteria**:
```bash
# Success indicators:
✅ Restore session from checkpoint
✅ Re-spawn agents in correct panes
✅ Display last 10 messages
✅ Show gentle re-orientation message
✅ Resume interrupted command option

# Test commands:
pytest services/orchestrator/tests/test_session_manager.py -v

# Manual validation:
# 1. Start session, send command, wait 35 seconds for checkpoint
python -m orchestrator.main

# 2. Kill orchestrator (Ctrl-C or tmux kill-session)

# 3. Restart with resume flag:
python -m orchestrator.main --resume

# Expected output:
# 🔄 Restoring session...
# ═══════════════════════════════════════════════════
#   Welcome back! Here's where you left off:
#   📍 Working on: /research Next.js patterns
#   🕐 Last active: 2 minutes ago
#   ⚡ Energy level: medium
# ═══════════════════════════════════════════════════
# ✅ Restored 3 agents, 10 messages
```

**Risk Assessment**:
- **⚠️ Risk**: Checkpoint corrupted or incomplete
  - **Mitigation**: Validate checkpoint structure before restore
  - **Fallback**: Start fresh session if validation fails

- **⚠️ Risk**: Agent fails to re-spawn
  - **Mitigation**: Retry with exponential backoff
  - **Fallback**: Spawn remaining agents, warn user

- **⚠️ Risk**: User confusion during restore
  - **Mitigation**: Clear re-orientation message with context
  - **Fallback**: Offer "fresh start" option if disoriented

- **⚠️ Risk**: Tmux session no longer exists
  - **Mitigation**: Check for session, create if missing
  - **Fallback**: Fresh session creation

**Branch Points**:
- **Decision Point**: Auto-resume vs manual prompt
  - Option A: Always auto-resume (recommended for ADHD)
  - Option B: Prompt user (adds friction)
  - **Recommendation**: Auto-resume with clear messaging

---

## 📊 Phase 1 Summary

**Total Effort**:
- **Focus Blocks**: 33 blocks (825 minutes = 13.75 hours)
- **Calendar Time**: 2 weeks (accounting for breaks, context switching, testing)
- **ADHD-Adjusted**: 3-4 weeks realistic (energy fluctuations)

**Complexity Distribution**:
- Low (0.0-0.4): Steps 1, 5, 7 (3 steps)
- Medium (0.4-0.6): Steps 2, 4, 6 (3 steps)
- High (0.6-1.0): Step 3 (1 step)

**Energy Requirements**:
- Low Energy: Step 1 (layout manager)
- Medium Energy: Steps 2, 4, 5, 6, 7
- High Energy: Step 3 (agent spawner)

**Dependencies**:
```
Step 1 (Tmux Layout)
  ├─→ Step 2 (Command Parser)
  │     └─→ Step 6 (Router)
  └─→ Step 3 (Agent Spawner)
        ├─→ Step 4 (Message Bus)
        │     └─→ Step 5 (Checkpoint)
        │           └─→ Step 7 (Resume)
        └─→ Step 6 (Router)
              └─→ Step 7 (Resume)
```

**Deliverables**:
- ✅ Tmux TUI with 2-4 pane adaptive layout
- ✅ Slash command parser and router
- ✅ Claude/Gemini/Grok agent spawner
- ✅ Message bus with tmux capture
- ✅ 30-second auto-checkpoint to ConPort
- ✅ Research/Plan/Implement mode routing
- ✅ Session restore with re-orientation

**Success Metrics**:
- Launch 3 AI agents in < 10 seconds
- Route commands to correct agents 95%+ accuracy
- Checkpoint every 30 seconds without lag
- Restore session in < 5 seconds
- Zero data loss during interruptions

---

## ⚙️ PHASE 2: API Layer (Week 3) - CONDITIONAL

**Trigger Conditions**:
- Phase 1 validated and stable
- User requests dashboard monitoring
- Need for external tool integration

**Goals**:
- REST API for orchestrator data
- WebSocket for real-time updates
- Authentication and authorization
- API documentation (OpenAPI)

**Estimated Effort**: 20 focus blocks (500 minutes)

**Key Steps**:
1. FastAPI setup and routing
2. WebSocket server for live updates
3. JWT authentication
4. OpenAPI documentation
5. Integration tests

**Branch Point**: If monitoring not needed, skip to Phase 3 or declare MVP complete

---

## 🌐 PHASE 3: Web Dashboard (Weeks 4-5) - CONDITIONAL

**Trigger Conditions**:
- Phase 2 API layer complete
- User explicitly requests visual dashboard
- Team collaboration features needed

**Goals**:
- React/Vue frontend
- Real-time agent status display
- Message history visualization
- Command input interface
- Analytics and insights

**Estimated Effort**: 30 focus blocks (750 minutes)

**Key Steps**:
1. Frontend framework setup (React recommended)
2. Real-time WebSocket integration
3. Agent status components
4. Message history display
5. Command input UI
6. Analytics dashboard

**Branch Point**: If visual interface not needed, declare Phase 1 as complete MVP

---

## 🎯 Recommended Implementation Sequence

**Week 1**:
- Day 1: Step 1 (Tmux Layout Manager)
- Day 2: Step 2 (Command Parser)
- Day 3: Step 3.1 (BaseAgent + ClaudeAgent)
- Day 4: Step 3.2 (GeminiAgent + GrokAgent)
- Day 5: Step 4 (Message Bus)

**Week 2**:
- Day 1: Step 5 (Checkpoint Manager)
- Day 2: Step 6.1 (Router + Research Mode)
- Day 3: Step 6.2 (Plan + Implement Modes)
- Day 4: Step 7 (Session Restoration)
- Day 5: Integration testing and bug fixes

**Week 3** (CONDITIONAL):
- Phase 2 API Layer OR declare MVP complete

**Weeks 4-5** (CONDITIONAL):
- Phase 3 Web Dashboard OR enhancement iteration

---

## 🚨 Risk Mitigation Strategy

**Critical Risks**:
1. **API Key Issues** → Check all keys on Day 1, provide clear setup docs
2. **Tmux Compatibility** → Test on 3 terminals early (iTerm2, Terminal.app, Alacritty)
3. **Agent Responsiveness** → Implement health checks in Step 3
4. **ConPort Availability** → Add retry logic and local caching fallback
5. **ADHD Context Loss** → Prioritize Step 5 (checkpoint) and Step 7 (resume)

**Contingency Plans**:
- If agent fails: Spawn backup agent type
- If ConPort fails: Local file checkpoint fallback
- If tmux fails: Fallback to terminal multiplexer (screen)
- If parsing fails: Raw command passthrough to Claude

---

## 📈 Success Indicators

**Phase 1 MVP Complete When**:
- ✅ Can launch orchestrator with `/dopemux start`
- ✅ Send `/research "topic"` → Both Claude and Gemini respond
- ✅ Send `/plan "feature"` → Grok uses zen/planner
- ✅ Checkpoint saves every 30 seconds
- ✅ Kill session → restart → resume exactly where left off
- ✅ Re-orientation message shows context clearly
- ✅ Zero crashes during 1-hour session

**Phase 2 API Complete When**:
- ✅ REST API serves orchestrator data
- ✅ WebSocket pushes real-time updates
- ✅ JWT auth protects endpoints
- ✅ OpenAPI docs generated

**Phase 3 Dashboard Complete When**:
- ✅ Web UI shows agent status
- ✅ Message history visible
- ✅ Commands sendable from web
- ✅ Analytics provide insights

---

## 🧠 ADHD Metadata

**Complexity Scores**:
- Phase 1 Average: 0.48 (Medium)
- Phase 2 Average: 0.60 (Medium-High)
- Phase 3 Average: 0.70 (High)

**Energy Matching**:
- Low Energy Days: Work on Steps 1, 5, 7 (low complexity)
- Medium Energy Days: Steps 2, 4, 6 (moderate complexity)
- High Energy Days: Step 3 (high complexity), integration testing

**Break Schedule**:
- 25-minute focus blocks with 5-minute breaks
- 2-hour checkpoint (15-minute break)
- 4-hour limit per day on high-complexity steps

**Context Preservation**:
- Commit after each step completion
- Update ConPort decision log daily
- Use TodoWrite to track progress visually

---

## 📝 Next Actions

**Immediate (Today)**:
1. Review this roadmap for completeness
2. Decide: Proceed with Phase 1 implementation?
3. Set up development environment (API keys, tmux, ConPort)
4. Create project structure: `services/orchestrator/`
5. Start Step 1: Tmux Layout Manager

**Decision Points**:
- After Phase 1: Continue to Phase 2 OR declare MVP complete?
- After Phase 2: Continue to Phase 3 OR iterate on Phase 1?

**Questions to Resolve**:
- Which terminal emulator is primary target? (iTerm2 recommended)
- Preferred API framework for Phase 2? (FastAPI recommended)
- Preferred frontend framework for Phase 3? (React recommended)
- ConPort instance location? (localhost:5455 assumed)

---

**END OF ROADMAP**
**Status**: Ready for implementation
**Validation**: Pending user review and approval
