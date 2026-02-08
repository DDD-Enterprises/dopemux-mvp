---
id: 05-ORCHESTRATOR-TUI
title: 05 Orchestrator Tui
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
author: '@hu3mann'
date: '2026-02-05'
prelude: 05 Orchestrator Tui (explanation) for dopemux documentation and developer
  workflows.
---
# Implementation Plan: Dopemux Orchestrator TUI

**Task ID**: IP-005
**Priority**: 🟢 NICE TO HAVE (New Feature)
**Duration**: 14 days (33 focus blocks @ 25min each)
**Complexity**: 0.68 (HIGH)
**Dependencies**: IP-001 (ADHD Engine Integration) recommended but not required
**Risk Level**: MEDIUM (new UI component)

---

## Executive Summary

**Goal**: Build beautiful, ADHD-optimized terminal UI for multi-AI orchestration using tmux.

**Solution**: Tmux-based TUI with energy-adaptive pane layouts (2-4 panes), slash command routing, and auto-checkpoint to ConPort.

**Impact**:
- ✅ Unified interface for Claude Code + Gemini + Grok coordination
- ✅ Energy-aware UI (2 panes when low energy, 4 when high)
- ✅ Auto-save every 30s to ConPort (interrupt-safe)
- ✅ Beautiful ADHD-optimized design
- ✅ FREE models (Grok Code Fast 1, Grok 4 Fast)

**Success Criteria**:
- [ ] Tmux layouts adapt to energy state (2-4 panes)
- [ ] Slash commands route to appropriate AI models
- [ ] Auto-checkpoint preserves state during interruptions
- [ ] Session restoration works seamlessly
- [ ] Message bus coordinates between panes

---

## Architecture (From DOPEMUX-ORCHESTRATOR-FINAL-SPEC.md)

### Validated Design (Confidence: 87%)

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOPEMUX ORCHESTRATOR TUI                    │
│                                                                 │
│  Energy-Adaptive Tmux Layout:                                  │
│                                                                 │
│  Low Energy (🔴): 2 panes                                      │
│  ┌────────────────────┬────────────────────┐                  │
│  │  Chat Orchestrator │   Claude Code      │                  │
│  │  (Pane 3)          │   (Pane 0)         │                  │
│  └────────────────────┴────────────────────┘                  │
│                                                                 │
│  Medium Energy (🟡): 3 panes                                   │
│  ┌──────────┬──────────┬──────────┐                          │
│  │   Chat   │  Claude  │  Gemini  │                          │
│  │  (Pane 3)│ (Pane 0) │ (Pane 1) │                          │
│  └──────────┴──────────┴──────────┘                          │
│                                                                 │
│  High Energy (🟢): 4 panes                                     │
│  ┌──────┬──────┬──────┬──────┐                              │
│  │ Chat │Claude│Gemini│ Grok │                              │
│  │(P 3) │(P 0) │(P 1) │(P 2) │                              │
│  └──────┴──────┴──────┴──────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MESSAGE BUS (TmuxCapture)                     │
│                                                                 │
│  - Reads pane outputs via tmux capture-pane                    │
│  - Publishes to Redis for cross-pane awareness                 │
│  - Enables AI-to-AI communication                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTEXT LAYERS (Auto-Save)                    │
│                                                                 │
│  Layer 1: ConPort (Persistent) - Every 30s auto-save          │
│  Layer 2: Serena LSP (Code Intelligence) - Live updates       │
│  Layer 3: Instance-Local (Session) - Per-pane state           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Model Arsenal (27+ models available via Zen MCP)

**Research Phase** → Gemini 2.5 Pro (1M context, intelligence: 18)
**Architecture** → Claude Sonnet 4.5 (architectural thinking, intelligence: 12)
**Implementation** → Grok Code Fast 1 (2M context, intelligence: 18, **FREE!**)
**Validation** → Multi-model consensus

---

## Day-by-Day Implementation Plan

### Week 1: Core Infrastructure

#### Day 1: Tmux Layout Manager (2 focus blocks, 50min)

**Location**: `services/orchestrator/tmux/layout_manager.py` (NEW FILE)

**Tasks**:
1. Create TmuxLayoutManager class
2. Implement energy-adaptive layout switching (2/3/4 panes)
3. Add layout persistence to ConPort
4. Test layout transitions

**Code**:
```python
"""
Tmux Layout Manager - Energy-Adaptive Pane Layouts
"""
import libtmux
from typing import List, Optional
from enum import Enum

class LayoutType(str, Enum):
    TWO_PANE = "2-pane"      # Low energy: Chat + Claude
    THREE_PANE = "3-pane"    # Medium energy: Chat + Claude + Gemini
    FOUR_PANE = "4-pane"     # High energy: Chat + Claude + Gemini + Grok

class TmuxLayoutManager:
    """
    Manages tmux pane layouts with energy-aware adaptation.

    Layouts adapt to user's cognitive capacity:
    - Low energy → 2 panes (reduce decisions)
    - Medium energy → 3 panes (standard)
    - High energy → 4 panes (max coordination)
    """

    def __init__(self, session_name: str = "dopemux"):
        self.session_name = session_name
        self.server = libtmux.Server()
        self.session: Optional[libtmux.Session] = None
        self.current_layout: Optional[LayoutType] = None

    def initialize(self) -> None:
        """Initialize or attach to tmux session."""
        # Create or attach to session
        try:
            self.session = self.server.find_where({"session_name": self.session_name})
        except Exception:
            self.session = self.server.new_session(session_name=self.session_name)

        logger.info(f"✅ Tmux session: {self.session_name}")

    def create_layout(self, layout_type: LayoutType, energy_level: str) -> None:
        """
        Create energy-appropriate tmux layout.

        Args:
            layout_type: 2/3/4 pane layout
            energy_level: Current user energy level for messaging
        """
        if not self.session:
            raise RuntimeError("Session not initialized")

        # Kill existing panes
        for pane in self.session.windows[0].panes[1:]:
            pane.cmd('kill-pane')

        if layout_type == LayoutType.TWO_PANE:
            self._create_two_pane_layout(energy_level)
        elif layout_type == LayoutType.THREE_PANE:
            self._create_three_pane_layout(energy_level)
        elif layout_type == LayoutType.FOUR_PANE:
            self._create_four_pane_layout(energy_level)

        self.current_layout = layout_type

    def _create_two_pane_layout(self, energy_level: str) -> None:
        """
        Create 2-pane layout for low energy.

        Layout:
        ┌──────────────────┬──────────────────┐
        │                  │                  │
        │  Chat            │  Claude Code     │
        │  Orchestrator    │  (Architecture)  │
        │  (Pane 3)        │  (Pane 0)        │
        │                  │                  │
        └──────────────────┴──────────────────┘
        """
        window = self.session.windows[0]

        # Split vertically (50/50)
        pane_chat = window.panes[0]
        pane_claude = window.split_window(vertical=True, percent=50)

        # Launch Chat Orchestrator in pane 3 (actually pane 0)
        pane_chat.send_keys("python services/orchestrator/chat_orchestrator.py")

        # Launch Claude Code in pane 0 (actually pane 1)
        pane_claude.send_keys("# Claude Code - Architecture and reasoning")
        pane_claude.send_keys("# Energy: {energy_level} - Focus on one AI at a time")

        logger.info(f"✅ Created 2-pane layout for LOW energy")

    def _create_three_pane_layout(self, energy_level: str) -> None:
        """
        Create 3-pane layout for medium energy.

        Layout:
        ┌─────────┬─────────┬─────────┐
        │         │         │         │
        │  Chat   │ Claude  │ Gemini  │
        │ (Pane 3)│(Pane 0) │(Pane 1) │
        │         │         │         │
        └─────────┴─────────┴─────────┘
        """
        window = self.session.windows[0]

        # Split into 3 vertical panes (33% each)
        pane_chat = window.panes[0]
        pane_claude = window.split_window(vertical=True, percent=33)
        pane_gemini = window.split_window(vertical=True, percent=50)

        # Launch services
        pane_chat.send_keys("python services/orchestrator/chat_orchestrator.py")
        pane_claude.send_keys("# Claude Code")
        pane_gemini.send_keys("gemini-cli --mode interactive")

        logger.info(f"✅ Created 3-pane layout for MEDIUM energy")

    def _create_four_pane_layout(self, energy_level: str) -> None:
        """
        Create 4-pane layout for high energy.

        Layout:
        ┌─────┬─────┬─────┬─────┐
        │Chat │Claude│Gemini│Grok│
        │(P 3)│(P 0) │(P 1) │(P 2)│
        └─────┴─────┴─────┴─────┘
        """
        window = self.session.windows[0]

        # Split into 4 vertical panes (25% each)
        pane_chat = window.panes[0]
        pane_claude = window.split_window(vertical=True, percent=25)
        pane_gemini = window.split_window(vertical=True, percent=33)
        pane_grok = window.split_window(vertical=True, percent=50)

        # Launch services
        pane_chat.send_keys("python services/orchestrator/chat_orchestrator.py")
        pane_claude.send_keys("# Claude Code")
        pane_gemini.send_keys("gemini-cli --mode interactive")
        pane_grok.send_keys("grok-cli --mode code")  # FREE Grok Code Fast 1!

        logger.info(f"✅ Created 4-pane layout for HIGH energy")

    def adapt_layout_to_energy(self, energy_level: str) -> None:
        """
        Automatically adapt layout based on user's current energy.

        Queries ADHD Engine for user state, then adjusts panes.
        """
        layout_mapping = {
            "very_low": LayoutType.TWO_PANE,
            "low": LayoutType.TWO_PANE,
            "medium": LayoutType.THREE_PANE,
            "high": LayoutType.FOUR_PANE,
            "hyperfocus": LayoutType.FOUR_PANE
        }

        target_layout = layout_mapping.get(energy_level, LayoutType.THREE_PANE)

        if target_layout != self.current_layout:
            logger.info(f"🔄 Adapting layout: {energy_level} → {target_layout.value}")
            self.create_layout(target_layout, energy_level)
```

**Tests** (`tests/test_tmux_layout_manager.py`):
```python
import pytest
from orchestrator.tmux.layout_manager import TmuxLayoutManager, LayoutType

def test_two_pane_layout():
    """Test 2-pane layout for low energy."""
    manager = TmuxLayoutManager(session_name="test-dopemux")
    manager.initialize()
    manager.create_layout(LayoutType.TWO_PANE, "low")

    # Verify 2 panes created
    assert len(manager.session.windows[0].panes) == 2

def test_energy_adaptation():
    """Test layout adapts to energy changes."""
    manager = TmuxLayoutManager()
    manager.initialize()

    # Start with 2 panes (low energy)
    manager.adapt_layout_to_energy("low")
    assert manager.current_layout == LayoutType.TWO_PANE

    # Energy increases → 4 panes
    manager.adapt_layout_to_energy("high")
    assert manager.current_layout == LayoutType.FOUR_PANE
    assert len(manager.session.windows[0].panes) == 4
```

**Deliverables**:
- [ ] TmuxLayoutManager implemented
- [ ] Energy-adaptive layouts working
- [ ] Layout persistence to ConPort
- [ ] Tests passing

---

#### Day 2: Command Parser (2 focus blocks, 50min)

**Location**: `services/orchestrator/commands/parser.py` (NEW FILE)

**Tasks**:
1. Create CommandParser for slash commands
2. Implement command routing logic
3. Add command validation
4. Test parsing

**Code**:
```python
"""
Command Parser for Dopemux Orchestrator

Parses and routes slash commands:
  /research <query>       → Route to Gemini (research specialist)
  /plan <task>            → Route to Claude (planning specialist)
  /implement <feature>    → Route to Grok (code specialist, FREE!)
  /mode <PLAN|ACT>        → Switch between planning/execution modes
  /checkpoint             → Manual save to ConPort
  /restore                → Restore from last checkpoint
"""
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

class CommandType(str, Enum):
    RESEARCH = "research"
    PLAN = "plan"
    IMPLEMENT = "implement"
    MODE = "mode"
    CHECKPOINT = "checkpoint"
    RESTORE = "restore"
    DEBUG = "debug"
    REVIEW = "review"
    CONSENSUS = "consensus"

class TargetAI(str, Enum):
    CLAUDE = "claude"      # Architecture, reasoning
    GEMINI = "gemini"      # Research, analysis
    GROK = "grok"          # Implementation, code
    ALL = "all"            # Broadcast to all

@dataclass
class ParsedCommand:
    """Parsed slash command with routing info."""
    command_type: CommandType
    target_ai: TargetAI
    query: str
    args: Dict[str, Any]
    requires_context: bool
    estimated_complexity: float

class CommandParser:
    """
    Parse and route slash commands to appropriate AI models.

    Uses Zen MCP for routing intelligence and ADHD Engine for
    complexity assessment.
    """

    def __init__(self):
        self.command_patterns = {
            r'^/research\s+(.+)': CommandType.RESEARCH,
            r'^/plan\s+(.+)': CommandType.PLAN,
            r'^/implement\s+(.+)': CommandType.IMPLEMENT,
            r'^/mode\s+(PLAN|ACT)': CommandType.MODE,
            r'^/checkpoint': CommandType.CHECKPOINT,
            r'^/restore': CommandType.RESTORE,
            r'^/debug\s+(.+)': CommandType.DEBUG,
            r'^/review\s*(.*)': CommandType.REVIEW,
            r'^/consensus\s+(.+)': CommandType.CONSENSUS
        }

        # Command → AI routing
        self.routing_map = {
            CommandType.RESEARCH: TargetAI.GEMINI,     # 1M context, research focus
            CommandType.PLAN: TargetAI.CLAUDE,         # Architectural thinking
            CommandType.IMPLEMENT: TargetAI.GROK,      # Code specialist, FREE!
            CommandType.DEBUG: TargetAI.CLAUDE,        # Systematic debugging
            CommandType.REVIEW: TargetAI.CLAUDE,       # Code review
            CommandType.CONSENSUS: TargetAI.ALL        # Multi-model decision
        }

    def parse(self, user_input: str) -> Optional[ParsedCommand]:
        """
        Parse user input into command.

        Returns None if not a slash command (regular chat).
        """
        # Check if slash command
        if not user_input.startswith('/'):
            return None

        # Match against patterns
        for pattern, cmd_type in self.command_patterns.items():
            match = re.match(pattern, user_input)
            if match:
                # Extract query/args
                query = match.group(1) if match.lastindex else ""

                # Determine target AI
                target = self.routing_map.get(cmd_type, TargetAI.CLAUDE)

                # Estimate complexity
                complexity = self._estimate_complexity(cmd_type, query)

                return ParsedCommand(
                    command_type=cmd_type,
                    target_ai=target,
                    query=query,
                    args={},
                    requires_context=self._requires_context(cmd_type),
                    estimated_complexity=complexity
                )

        # Unknown command
        return None

    def _estimate_complexity(self, cmd_type: CommandType, query: str) -> float:
        """Estimate command complexity for ADHD routing."""
        base_complexity = {
            CommandType.RESEARCH: 0.6,      # Research is cognitively demanding
            CommandType.PLAN: 0.7,          # Planning requires deep thinking
            CommandType.IMPLEMENT: 0.8,     # Implementation is complex
            CommandType.DEBUG: 0.75,        # Debugging is hard
            CommandType.REVIEW: 0.65,       # Review requires attention
            CommandType.CONSENSUS: 0.8,     # Multi-model coordination complex
            CommandType.MODE: 0.2,          # Simple mode switch
            CommandType.CHECKPOINT: 0.1,    # Trivial
            CommandType.RESTORE: 0.3        # Moderate (context restoration)
        }

        complexity = base_complexity.get(cmd_type, 0.5)

        # Adjust based on query length (longer = more complex)
        word_count = len(query.split())
        if word_count > 20:
            complexity += 0.1
        elif word_count < 5:
            complexity -= 0.1

        return min(max(complexity, 0.0), 1.0)

    def _requires_context(self, cmd_type: CommandType) -> bool:
        """Check if command needs code/file context."""
        context_required = {
            CommandType.IMPLEMENT,
            CommandType.DEBUG,
            CommandType.REVIEW
        }
        return cmd_type in context_required

    def format_command_for_ai(
        self,
        parsed: ParsedCommand,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format parsed command for AI consumption.

        Adds context, converts to natural language if needed.
        """
        # Base prompt
        prompt = parsed.query

        # Add context if available and required
        if parsed.requires_context and context:
            files = context.get('files', [])
            if files:
                prompt += f"\n\nContext files:\n" + "\n".join(f"- {f}" for f in files)

            active_context = context.get('active_context', {})
            if active_context:
                prompt += f"\n\nCurrent focus: {active_context.get('current_focus', 'N/A')}"

        # Add complexity hint for AI
        if parsed.estimated_complexity > 0.7:
            prompt += f"\n\n[COMPLEX TASK - Complexity: {parsed.estimated_complexity:.2f}]"

        return prompt
```

**Deliverables**:
- [ ] CommandParser implemented
- [ ] Slash commands parsed correctly
- [ ] AI routing logic functional
- [ ] Tests passing

---

#### Day 3-4: Agent Spawner (4 focus blocks, 100min)

**Location**: `services/orchestrator/agents/spawner.py` (NEW FILE)

**Tasks**:
1. Create AgentSpawner class
2. Implement AI CLI launching in tmux panes
3. Add agent health monitoring
4. Test multi-agent coordination

**Code**:
```python
"""
Agent Spawner - Launch AI CLIs in Tmux Panes
"""
import libtmux
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for AI agent."""
    name: str
    cli_command: str
    pane_index: int
    capabilities: List[str]
    cost: str  # "free", "low", "medium", "high"

class AgentSpawner:
    """
    Spawn AI agents in tmux panes with health monitoring.

    Agents:
    - Claude Code (Pane 0): Architecture, reasoning, systematic analysis
    - Gemini CLI (Pane 1): Research, 1M context, analysis
    - Grok CLI (Pane 2): Implementation, 2M context, FREE!
    """

    def __init__(self, session: libtmux.Session):
        self.session = session
        self.agents: Dict[str, AgentConfig] = {}
        self.active_agents: Dict[str, libtmux.Pane] = {}

        # Agent configurations
        self._init_agent_configs()

    def _init_agent_configs(self) -> None:
        """Initialize agent configurations."""
        self.agents = {
            "claude": AgentConfig(
                name="Claude Code",
                cli_command="# Claude Code Interactive",
                pane_index=0,
                capabilities=["architecture", "reasoning", "planning", "review"],
                cost="medium"
            ),
            "gemini": AgentConfig(
                name="Gemini CLI",
                cli_command="gemini-cli --mode interactive",
                pane_index=1,
                capabilities=["research", "analysis", "long-context"],
                cost="low"
            ),
            "grok": AgentConfig(
                name="Grok Code",
                cli_command="grok-cli --mode code --free-tier",
                pane_index=2,
                capabilities=["implementation", "code-generation", "refactoring"],
                cost="free"  # FREE on OpenRouter!
            )
        }

    async def spawn_agent(self, agent_name: str, pane: libtmux.Pane) -> None:
        """
        Spawn AI agent in specified tmux pane.

        Args:
            agent_name: "claude", "gemini", or "grok"
            pane: Tmux pane to launch agent in
        """
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        config = self.agents[agent_name]

        # Send CLI command to pane
        pane.send_keys(config.cli_command)

        # Wait for agent to initialize
        await asyncio.sleep(2)

        # Verify agent is responsive
        pane.send_keys("echo 'Agent ready'")

        # Track active agent
        self.active_agents[agent_name] = pane

        logger.info(f"✅ Spawned {config.name} in pane {config.pane_index}")

    async def spawn_all_agents(self, layout_type: LayoutType) -> None:
        """Spawn appropriate agents for layout."""
        window = self.session.windows[0]
        panes = window.panes

        if layout_type == LayoutType.TWO_PANE:
            # Spawn only Claude
            await self.spawn_agent("claude", panes[1])

        elif layout_type == LayoutType.THREE_PANE:
            # Spawn Claude + Gemini
            await self.spawn_agent("claude", panes[1])
            await self.spawn_agent("gemini", panes[2])

        elif layout_type == LayoutType.FOUR_PANE:
            # Spawn all three
            await self.spawn_agent("claude", panes[1])
            await self.spawn_agent("gemini", panes[2])
            await self.spawn_agent("grok", panes[3])

    async def send_to_agent(
        self,
        agent_name: str,
        message: str,
        wait_for_response: bool = True
    ) -> Optional[str]:
        """
        Send message to agent and optionally wait for response.

        Args:
            agent_name: Target agent
            message: Message to send
            wait_for_response: If True, capture response

        Returns:
            Agent response (if wait_for_response=True)
        """
        if agent_name not in self.active_agents:
            logger.warning(f"Agent not active: {agent_name}")
            return None

        pane = self.active_agents[agent_name]

        # Send message
        pane.send_keys(message)

        # Wait for response
        if wait_for_response:
            await asyncio.sleep(1)  # Give agent time to respond

            # Capture pane output
            response = pane.cmd('capture-pane', '-p').stdout

            return response[-1000:]  # Last 1000 chars

        return None

    async def broadcast_to_all(self, message: str) -> Dict[str, str]:
        """
        Send message to all active agents.

        Returns dict of agent → response.
        """
        responses = {}

        for agent_name in self.active_agents.keys():
            response = await self.send_to_agent(agent_name, message, wait_for_response=True)
            responses[agent_name] = response

        return responses

    async def health_check_agents(self) -> Dict[str, bool]:
        """Check health of all agents."""
        health = {}

        for agent_name, pane in self.active_agents.items():
            try:
                # Send ping command
                pane.send_keys("echo 'ping'")
                await asyncio.sleep(0.5)

                # Check if pane is alive
                is_alive = pane.window.panes  # Will throw if pane dead

                health[agent_name] = True
            except Exception as e:
                logger.error(f"Agent {agent_name} unhealthy: {e}")
                health[agent_name] = False

        return health
```

**Deliverables**:
- [ ] AgentSpawner implemented
- [ ] Can launch Claude, Gemini, Grok in panes
- [ ] Message sending working
- [ ] Health checks functional

---

#### Day 5-6: Message Bus (4 focus blocks, 100min)

**Location**: `services/orchestrator/message_bus/tmux_capture.py` (NEW FILE)

**Tasks**:
1. Create TmuxCaptureMessageBus
2. Implement publish/subscribe via tmux
3. Add Redis pub/sub (optional upgrade)
4. Test cross-pane communication

**Code**:
```python
"""
Message Bus Implementation - TmuxCapture

Enables AI-to-AI communication by capturing pane outputs and
publishing to Redis for other panes to subscribe.
"""
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Callable, List
import libtmux
import redis.asyncio as redis
import asyncio
import json
from datetime import datetime

class MessageBus(ABC):
    """Abstract message bus interface."""

    @abstractmethod
    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish message to channel."""
        pass

    @abstractmethod
    async def subscribe(self, channel: str, handler: Callable) -> None:
        """Subscribe to channel with handler."""
        pass

class TmuxCaptureMessageBus(MessageBus):
    """
    Message bus using tmux capture-pane.

    Polls panes for new content, publishes to Redis for coordination.
    """

    def __init__(
        self,
        session: libtmux.Session,
        redis_client: redis.Redis
    ):
        self.session = session
        self.redis = redis_client
        self.pane_histories: Dict[int, List[str]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False

    async def start_polling(self) -> None:
        """
        Start polling panes for new content.

        Runs in background, captures new output and publishes.
        """
        self.running = True
        logger.info("👂 Message Bus started polling panes...")

        while self.running:
            try:
                # Poll each pane for new content
                for pane in self.session.windows[0].panes:
                    await self._poll_pane(pane)

                # Poll every 500ms for responsiveness
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)

    async def _poll_pane(self, pane: libtmux.Pane) -> None:
        """Poll single pane for new content."""
        pane_id = int(pane.pane_id.replace('%', ''))

        # Capture pane content
        try:
            output = pane.cmd('capture-pane', '-p').stdout
        except Exception as e:
            logger.error(f"Failed to capture pane {pane_id}: {e}")
            return

        # Get lines
        lines = output if isinstance(output, list) else output.split('\n')

        # Initialize history if needed
        if pane_id not in self.pane_histories:
            self.pane_histories[pane_id] = lines
            return

        # Check for new lines
        old_lines = self.pane_histories[pane_id]
        if len(lines) > len(old_lines):
            # New content detected
            new_lines = lines[len(old_lines):]

            # Publish new content
            for line in new_lines:
                if line.strip():  # Ignore empty lines
                    await self._publish_pane_output(pane_id, line)

            # Update history
            self.pane_histories[pane_id] = lines

    async def _publish_pane_output(self, pane_id: int, content: str) -> None:
        """Publish pane output to Redis."""
        message = {
            "pane_id": pane_id,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        # Publish to pane-specific channel
        channel = f"dopemux:pane:{pane_id}:output"
        await self.redis.publish(channel, json.dumps(message))

        # Also publish to broadcast channel
        await self.redis.publish("dopemux:pane:all:output", json.dumps(message))

    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish message to channel."""
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str, handler: Callable) -> None:
        """Subscribe to channel with handler."""
        if channel not in self.subscribers:
            self.subscribers[channel] = []

        self.subscribers[channel].append(handler)

        # Create Redis subscription
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)

        # Start listener
        asyncio.create_task(self._listen_channel(pubsub, channel))

    async def _listen_channel(self, pubsub, channel: str) -> None:
        """Listen to Redis channel and call handlers."""
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])

                # Call handlers
                handlers = self.subscribers.get(channel, [])
                for handler in handlers:
                    try:
                        await handler(data)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")

    async def stop(self) -> None:
        """Stop polling."""
        self.running = False
```

**Deliverables**:
- [ ] TmuxCapture message bus working
- [ ] Cross-pane communication functional
- [ ] Redis pub/sub integration operational
- [ ] Polling efficient (<1% CPU)

---

#### Day 7: Checkpoint Manager (2 focus blocks, 50min)

**Location**: `services/orchestrator/checkpoint/manager.py` (NEW FILE)

**Tasks**:
1. Create CheckpointManager for auto-save
2. Implement 30-second auto-checkpoint
3. Add manual checkpoint support
4. Test checkpoint/restore

**Code**:
```python
"""
Checkpoint Manager - Auto-Save to ConPort Every 30s

Ensures ADHD developers never lose progress during interruptions.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from conport_client import ConPortClient

logger = logging.getLogger(__name__)

class CheckpointManager:
    """
    Automatic checkpoint system for ADHD-safe development.

    Auto-saves every 30 seconds to ConPort for interrupt recovery.
    """

    def __init__(
        self,
        conport_client: ConPortClient,
        user_id: str,
        checkpoint_interval: int = 30
    ):
        self.conport = conport_client
        self.user_id = user_id
        self.checkpoint_interval = checkpoint_interval
        self.running = False
        self.last_checkpoint_time: Optional[datetime] = None

    async def start_auto_checkpoint(self, context_provider: Callable) -> None:
        """
        Start automatic checkpoint loop.

        Args:
            context_provider: Async function that returns current context dict
        """
        self.running = True
        logger.info(f"💾 Auto-checkpoint started (every {self.checkpoint_interval}s)")

        while self.running:
            try:
                # Wait for interval
                await asyncio.sleep(self.checkpoint_interval)

                # Get current context
                context = await context_provider()

                # Save checkpoint
                await self.save_checkpoint(context)

            except Exception as e:
                logger.error(f"Auto-checkpoint error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

    async def save_checkpoint(self, context: Dict[str, Any]) -> None:
        """Save checkpoint to ConPort."""
        try:
            # Add checkpoint metadata
            checkpoint = {
                **context,
                "checkpoint_type": "auto",
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat()
            }

            # Save to ConPort active_context
            await self.conport.update_active_context(
                workspace_id=self.conport.workspace_id,
                patch_content={"last_checkpoint": checkpoint}
            )

            self.last_checkpoint_time = datetime.now()

            logger.debug(f"💾 Checkpoint saved: {context.get('current_focus', 'N/A')}")

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    async def restore_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Restore last checkpoint from ConPort."""
        try:
            # Get active context
            active_context = await self.conport.get_active_context(
                workspace_id=self.conport.workspace_id
            )

            checkpoint = active_context.get('last_checkpoint')

            if checkpoint:
                logger.info(f"✅ Checkpoint restored from {checkpoint['timestamp']}")
                return checkpoint
            else:
                logger.warning("No checkpoint found")
                return None

        except Exception as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            return None

    async def manual_checkpoint(self, description: str, context: Dict[str, Any]) -> None:
        """
        Manual checkpoint with description.

        Used for important milestones or before risky operations.
        """
        checkpoint = {
            **context,
            "checkpoint_type": "manual",
            "description": description,
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat()
        }

        # Save to ConPort
        await self.conport.update_active_context(
            workspace_id=self.conport.workspace_id,
            patch_content={"last_checkpoint": checkpoint}
        )

        # Also log as decision for traceability
        await self.conport.log_decision(
            workspace_id=self.conport.workspace_id,
            summary=f"Checkpoint: {description}",
            rationale="Manual checkpoint before significant operation",
            tags=["checkpoint", "manual"]
        )

        logger.info(f"💾 Manual checkpoint: {description}")

    async def stop(self) -> None:
        """Stop auto-checkpoint loop."""
        self.running = False
```

**Usage in Chat Orchestrator**:
```python
# services/orchestrator/chat_orchestrator.py

async def run_orchestrator():
    # Initialize checkpoint manager
    checkpoint_mgr = CheckpointManager(conport_client, user_id="developer1")

    # Start auto-checkpoint
    async def get_current_context():
        return {
            "current_focus": current_task,
            "active_file": current_file,
            "cursor_position": cursor_pos,
            "conversation_history": recent_messages[-10:]
        }

    asyncio.create_task(checkpoint_mgr.start_auto_checkpoint(get_current_context))

    # Main orchestrator loop...
```

**Deliverables**:
- [ ] Auto-checkpoint every 30s working
- [ ] Manual checkpoint functional
- [ ] Checkpoint restore operational
- [ ] ConPort integration tested

---

### Week 2: Integration & Polish

#### Day 8-9: Command Router (4 focus blocks, 100min)

**Location**: `services/orchestrator/routing/router.py` (NEW FILE)

**Tasks**:
1. Create CommandRouter with AI selection logic
2. Implement complexity-based routing
3. Add ADHD Engine integration for energy matching
4. Test routing decisions

**Code**:
```python
"""
Command Router - Intelligent AI Selection

Routes commands to optimal AI based on:
- Command type and complexity
- User's current energy and attention state
- AI capabilities and costs
- Context requirements
"""
from typing import Optional, List
from commands.parser import ParsedCommand, CommandType, TargetAI
from adhd_config_service import get_adhd_config_service

class CommandRouter:
    """
    Route commands to appropriate AI agents.

    Uses ADHD Engine to match task complexity with user capacity.
    """

    def __init__(self):
        self.adhd_config = None

    async def initialize(self) -> None:
        """Connect to ADHD Engine."""
        self.adhd_config = await get_adhd_config_service()

    async def route_command(
        self,
        parsed: ParsedCommand,
        user_id: str
    ) -> TargetAI:
        """
        Route command to optimal AI.

        Takes into account:
        - Default routing (research→Gemini, implement→Grok, etc.)
        - User's cognitive capacity
        - Task complexity
        """
        # Get default routing
        default_target = parsed.target_ai

        # Special case: If command is COMPLEX and user has LOW energy
        if await self._should_defer_command(parsed, user_id):
            # Suggest deferring or breaking down
            return None  # Signals to ask user

        # Check if target AI is appropriate for user's state
        if default_target == TargetAI.ALL:
            # Consensus mode - use all available agents
            return TargetAI.ALL

        # Energy-based optimization
        optimized_target = await self._optimize_for_energy(
            default_target,
            parsed,
            user_id
        )

        return optimized_target

    async def _should_defer_command(
        self,
        parsed: ParsedCommand,
        user_id: str
    ) -> bool:
        """
        Check if command should be deferred due to energy mismatch.

        Complex commands during low energy → suggest break or defer.
        """
        if not self.adhd_config:
            return False

        # Get user state
        energy_level = await self.adhd_config._get_energy_level(user_id)
        complexity = parsed.estimated_complexity

        # Energy capacity scores
        energy_capacity = {
            "very_low": 0.2,
            "low": 0.4,
            "medium": 0.6,
            "high": 0.8,
            "hyperfocus": 1.0
        }

        capacity = energy_capacity.get(energy_level, 0.6)

        # If task complexity exceeds capacity by 50%+
        if complexity > capacity * 1.5:
            logger.warning(
                f"⚠️ Task complexity ({complexity:.2f}) exceeds "
                f"{energy_level} energy capacity ({capacity:.2f})"
            )
            return True

        return False

    async def _optimize_for_energy(
        self,
        default_target: TargetAI,
        parsed: ParsedCommand,
        user_id: str
    ) -> TargetAI:
        """
        Optimize AI selection based on energy state.

        Low energy: Use faster, simpler AI
        High energy: Use most powerful AI
        """
        if not self.adhd_config:
            return default_target

        energy_level = await self.adhd_config._get_energy_level(user_id)

        # If low energy and complex task, offer to use faster model
        if energy_level in ["very_low", "low"] and parsed.estimated_complexity > 0.7:
            # Suggest using Grok (FREE, fast) instead of Claude/Gemini
            if default_target in [TargetAI.CLAUDE, TargetAI.GEMINI]:
                logger.info(
                    f"💡 Low energy detected - consider using Grok (faster, free) "
                    f"instead of {default_target.value}"
                )
                # Could auto-switch or ask user
                # For now, keep default but log suggestion

        return default_target

    async def get_routing_explanation(
        self,
        parsed: ParsedCommand,
        chosen_target: TargetAI,
        user_id: str
    ) -> str:
        """
        Generate explanation for why command routed to specific AI.

        ADHD benefit: Transparency reduces uncertainty.
        """
        explanations = {
            CommandType.RESEARCH: f"🔬 Routing to {chosen_target.value} (1M context, research specialist)",
            CommandType.PLAN: f"🏗️ Routing to {chosen_target.value} (architectural thinking)",
            CommandType.IMPLEMENT: f"⚡ Routing to {chosen_target.value} (code specialist, FREE!)",
            CommandType.DEBUG: f"🐛 Routing to {chosen_target.value} (systematic debugging)",
            CommandType.REVIEW: f"👁️ Routing to {chosen_target.value} (code review specialist)"
        }

        base = explanations.get(parsed.command_type, f"Routing to {chosen_target.value}")

        # Add energy context if available
        if self.adhd_config:
            energy = await self.adhd_config._get_energy_level(user_id)
            base += f"\n   Current energy: {energy}"

        return base
```

**Deliverables**:
- [ ] CommandRouter implemented
- [ ] Energy-aware routing working
- [ ] ADHD Engine integration functional
- [ ] Routing explanations clear

---

#### Day 10-11: Session Restoration (4 focus blocks, 100min)

**Location**: `services/orchestrator/session/restoration.py` (NEW FILE)

**Tasks**:
1. Create SessionRestoration class
2. Implement context restoration from ConPort
3. Add visual restoration summary
4. Test multi-day restoration

**Code**:
```python
"""
Session Restoration - ADHD-Optimized Context Recovery

Restores full mental model after interruptions.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from conport_client import ConPortClient

logger = logging.getLogger(__name__)

class SessionRestoration:
    """
    Restore development context after interruptions.

    Provides gentle re-orientation with visual summary.
    """

    def __init__(self, conport_client: ConPortClient):
        self.conport = conport_client

    async def restore_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore session from last checkpoint.

        Returns complete context for resuming work.
        """
        try:
            # Get last checkpoint
            active_context = await self.conport.get_active_context(
                workspace_id=self.conport.workspace_id
            )

            checkpoint = active_context.get('last_checkpoint')

            if not checkpoint:
                logger.info("No checkpoint found - starting fresh")
                return None

            # Calculate interruption duration
            checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
            interruption_duration = (datetime.now() - checkpoint_time).total_seconds() / 60

            # Generate restoration summary
            summary = self._generate_restoration_summary(checkpoint, interruption_duration)

            # Display restoration message
            print(summary)

            # Return context for orchestrator
            return checkpoint

        except Exception as e:
            logger.error(f"Session restoration failed: {e}")
            return None

    def _generate_restoration_summary(
        self,
        checkpoint: Dict[str, Any],
        interruption_minutes: float
    ) -> str:
        """
        Generate ADHD-friendly restoration summary.

        Format:
        🔄 Welcome back! Restoring your context...

        🎯 You were working on: [task]
        📁 Active files: [files]
        🧠 Mental model: [summary]
        ⏰ Interrupted: [time] ago

        ✅ Ready to continue!
        Next steps:
        1. [step 1]
        2. [step 2]
        """
        summary = "🔄 Welcome back! Restoring your context...\n\n"

        # Task info
        current_focus = checkpoint.get('current_focus', 'Unknown task')
        summary += f"🎯 You were working on: {current_focus}\n"

        # Active files
        active_file = checkpoint.get('active_file')
        if active_file:
            summary += f"📁 Active file: {active_file}\n"

        # Mental model
        mental_model = checkpoint.get('mental_model', '')
        if mental_model:
            summary += f"🧠 Mental model: {mental_model}\n"

        # Interruption duration
        if interruption_minutes < 60:
            summary += f"⏰ Interrupted: {interruption_minutes:.0f} minutes ago\n"
        elif interruption_minutes < 1440:  # < 24 hours
            summary += f"⏰ Interrupted: {interruption_minutes/60:.1f} hours ago\n"
        else:  # 24+ hours
            summary += f"⏰ Interrupted: {interruption_minutes/1440:.1f} days ago\n"

        summary += "\n✅ Ready to continue!\n"

        # Next steps
        next_steps = checkpoint.get('next_steps', [])
        if next_steps:
            summary += "\nNext steps:\n"
            for i, step in enumerate(next_steps[:3], 1):  # Max 3 for ADHD
                summary += f"{i}. {step}\n"

        return summary

    async def create_manual_checkpoint(
        self,
        description: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Create manual checkpoint before risky operations.

        Use before:
        - Large refactorings
        - Experimental changes
        - Deploying to production
        """
        checkpoint = {
            **context,
            "checkpoint_type": "manual",
            "description": description,
            "timestamp": datetime.now().isoformat()
        }

        await self.conport.update_active_context(
            workspace_id=self.conport.workspace_id,
            patch_content={"last_manual_checkpoint": checkpoint}
        )

        logger.info(f"💾 Manual checkpoint created: {description}")

    async def list_checkpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent checkpoints for restore selection.

        ADHD benefit: See history, choose restore point.
        """
        # Query ConPort history
        history = await self.conport.get_item_history(
            workspace_id=self.conport.workspace_id,
            item_type="active_context",
            limit=limit
        )

        checkpoints = []
        for item in history:
            checkpoint_data = item.get('content', {}).get('last_checkpoint')
            if checkpoint_data:
                checkpoints.append({
                    "timestamp": checkpoint_data['timestamp'],
                    "focus": checkpoint_data.get('current_focus', 'N/A'),
                    "description": checkpoint_data.get('description', 'Auto-checkpoint')
                })

        return checkpoints
```

**Deliverables**:
- [ ] Auto-checkpoint every 30s working
- [ ] Manual checkpoint functional
- [ ] Session restoration with visual summary
- [ ] Checkpoint history queryable

---

#### Day 12-13: Chat Orchestrator (4 focus blocks, 100min)

**Location**: `services/orchestrator/chat_orchestrator.py` (NEW FILE)

**Tasks**:
1. Create main ChatOrchestrator class
2. Integrate all components (layout, commands, agents, message bus, checkpoints)
3. Implement main loop
4. Test complete workflow

**Code**:
```python
"""
Chat Orchestrator - Main Entry Point

Coordinates all Dopemux Orchestrator components.
"""
import asyncio
import sys
from pathlib import Path

from tmux.layout_manager import TmuxLayoutManager, LayoutType
from commands.parser import CommandParser
from agents.spawner import AgentSpawner
from message_bus.tmux_capture import TmuxCaptureMessageBus
from checkpoint.manager import CheckpointManager
from routing.router import CommandRouter
from adhd_config_service import get_adhd_config_service
from conport_client import ConPortClient

class ChatOrchestrator:
    """
    Main orchestrator for Dopemux TUI.

    Provides ADHD-optimized multi-AI development interface.
    """

    def __init__(self, user_id: str = "developer1"):
        self.user_id = user_id

        # Components (initialized in setup())
        self.layout_manager: Optional[TmuxLayoutManager] = None
        self.command_parser: Optional[CommandParser] = None
        self.agent_spawner: Optional[AgentSpawner] = None
        self.message_bus: Optional[TmuxCaptureMessageBus] = None
        self.checkpoint_manager: Optional[CheckpointManager] = None
        self.router: Optional[CommandRouter] = None

        # State
        self.current_energy: str = "medium"
        self.current_focus: str = ""
        self.running = False

    async def setup(self) -> None:
        """Initialize all components."""
        print("🚀 Initializing Dopemux Orchestrator...")

        # Initialize layout manager
        self.layout_manager = TmuxLayoutManager()
        self.layout_manager.initialize()

        # Initialize command parser
        self.command_parser = CommandParser()

        # Initialize agent spawner
        self.agent_spawner = AgentSpawner(self.layout_manager.session)

        # Initialize message bus
        redis_client = await redis.from_url("redis://localhost:6380/6")
        self.message_bus = TmuxCaptureMessageBus(
            self.layout_manager.session,
            redis_client
        )

        # Initialize checkpoint manager
        conport_client = ConPortClient(workspace_id="/Users/hue/code/dopemux-mvp")
        self.checkpoint_manager = CheckpointManager(conport_client, self.user_id)

        # Initialize router
        self.router = CommandRouter()
        await self.router.initialize()

        # Restore previous session
        await self._restore_previous_session()

        # Start background tasks
        await self._start_background_tasks()

        print("✅ Dopemux Orchestrator ready!")

    async def _restore_previous_session(self) -> None:
        """Restore previous session if exists."""
        checkpoint = await self.checkpoint_manager.restore_checkpoint()

        if checkpoint:
            self.current_focus = checkpoint.get('current_focus', '')
            self.current_energy = checkpoint.get('energy_level', 'medium')

            # Adapt layout to restored energy
            self.layout_manager.adapt_layout_to_energy(self.current_energy)

    async def _start_background_tasks(self) -> None:
        """Start all background monitoring tasks."""
        # Auto-checkpoint
        asyncio.create_task(
            self.checkpoint_manager.start_auto_checkpoint(self._get_current_context)
        )

        # Message bus polling
        asyncio.create_task(self.message_bus.start_polling())

        # Energy monitoring (adapt layout dynamically)
        asyncio.create_task(self._monitor_energy())

    async def _monitor_energy(self) -> None:
        """Monitor energy changes and adapt layout."""
        adhd_config = await get_adhd_config_service()

        while self.running:
            try:
                # Get current energy
                energy = await adhd_config._get_energy_level(self.user_id)

                # Adapt layout if energy changed
                if energy != self.current_energy:
                    logger.info(f"⚡ Energy changed: {self.current_energy} → {energy}")
                    self.current_energy = energy
                    self.layout_manager.adapt_layout_to_energy(energy)

                # Check every 2 minutes
                await asyncio.sleep(120)

            except Exception as e:
                logger.error(f"Energy monitoring error: {e}")
                await asyncio.sleep(300)

    async def run(self) -> None:
        """Main orchestrator loop."""
        self.running = True

        print("\n" + "="*60)
        print("  DOPEMUX ORCHESTRATOR - ADHD-Optimized Multi-AI Development")
        print("="*60)
        print(f"\n🎯 Energy: {self.current_energy}")
        print(f"📋 Focus: {self.current_focus or 'Ready for new task'}")
        print(f"\n💡 Type /help for commands\n")

        while self.running:
            try:
                # Get user input
                user_input = input("dopemux> ").strip()

                if not user_input:
                    continue

                # Handle exit
                if user_input.lower() in ['exit', 'quit', '/quit']:
                    await self.shutdown()
                    break

                # Parse command
                parsed = self.command_parser.parse(user_input)

                if parsed:
                    # Route command
                    await self._handle_command(parsed)
                else:
                    # Regular chat - send to Claude
                    await self._handle_chat(user_input)

            except KeyboardInterrupt:
                print("\n⚠️ Interrupted - auto-saving...")
                await self.checkpoint_manager.save_checkpoint(await self._get_current_context())
                continue
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")

    async def _handle_command(self, parsed: ParsedCommand) -> None:
        """Handle parsed slash command."""
        print(f"\n🎯 Command: {parsed.command_type.value}")

        # Route command
        target = await self.router.route_command(parsed, self.user_id)

        if target is None:
            # Deferred due to energy mismatch
            print("⚠️ This task is complex for your current energy level.")
            print("   Options: 1) Take a break  2) Break task down  3) Continue anyway")
            choice = input("   Choice (1/2/3): ")

            if choice == "1":
                print("☕ Good choice! Taking a 10-minute break...")
                return
            elif choice == "2":
                print("💡 Let's break this down...")
                # Use Zen planner to decompose
                parsed.command_type = CommandType.PLAN
                target = TargetAI.CLAUDE

        # Get routing explanation
        explanation = await self.router.get_routing_explanation(parsed, target, self.user_id)
        print(f"   {explanation}\n")

        # Send to target AI
        if target == TargetAI.ALL:
            # Consensus mode - send to all
            await self._handle_consensus(parsed)
        else:
            await self._send_to_agent(target, parsed)

    async def _send_to_agent(self, target: TargetAI, parsed: ParsedCommand) -> None:
        """Send command to specific AI agent."""
        # Format command for AI
        formatted = self.command_parser.format_command_for_ai(parsed)

        # Get context if needed
        if parsed.requires_context:
            # Get code context from Serena
            # (Implementation details...)
            pass

        # Send to agent
        response = await self.agent_spawner.send_to_agent(
            target.value,
            formatted,
            wait_for_response=True
        )

        # Display response
        print(f"\n{target.value.upper()} Response:")
        print(response)

    async def _handle_chat(self, message: str) -> None:
        """Handle regular chat (not slash command)."""
        # Send to Claude by default
        await self._send_to_agent(TargetAI.CLAUDE, message)

    async def _get_current_context(self) -> Dict[str, Any]:
        """Get current context for checkpoint."""
        return {
            "current_focus": self.current_focus,
            "energy_level": self.current_energy,
            "layout_type": self.layout_manager.current_layout.value if self.layout_manager else None,
            "active_agents": list(self.agent_spawner.active_agents.keys()) if self.agent_spawner else [],
            "timestamp": datetime.now().isoformat()
        }

    async def shutdown(self) -> None:
        """Graceful shutdown with final checkpoint."""
        print("\n💾 Saving final checkpoint...")

        await self.checkpoint_manager.save_checkpoint(await self._get_current_context())

        print("👋 Dopemux Orchestrator shut down gracefully")
        self.running = False


# Main entry point
async def main():
    orchestrator = ChatOrchestrator(user_id="developer1")
    await orchestrator.setup()
    await orchestrator.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Deliverables**:
- [ ] Session restoration working
- [ ] Visual restoration summary clear
- [ ] Context restoration from days-old checkpoints
- [ ] Graceful shutdown with auto-save

---

#### Day 14: Integration Testing & Documentation (2 focus blocks, 50min)

**End-to-End Tests** (`tests/integration/test_orchestrator_e2e.py`):
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_full_orchestrator_workflow():
    """
    Test complete workflow:
    1. Start orchestrator
    2. Parse slash command
    3. Route to AI
    4. Auto-checkpoint
    5. Restore session
    """
    # Initialize orchestrator
    orchestrator = ChatOrchestrator(user_id="test_user")
    await orchestrator.setup()

    # Simulate commands
    commands = [
        "/research Redis pub/sub patterns",
        "/plan Implement event bus",
        "/implement EventBus class"
    ]

    for cmd in commands:
        parsed = orchestrator.command_parser.parse(cmd)
        assert parsed is not None

        target = await orchestrator.router.route_command(parsed, "test_user")
        assert target is not None

    # Verify checkpoint created
    checkpoint = await orchestrator.checkpoint_manager.restore_checkpoint()
    assert checkpoint is not None

    print("✅ Full orchestrator workflow successful!")
```

**Documentation**:
- [ ] User guide: How to use Dopemux Orchestrator
- [ ] Slash command reference
- [ ] Energy adaptation explanation
- [ ] Troubleshooting guide

---

## Complete File Structure

```
services/orchestrator/
├── __init__.py
├── chat_orchestrator.py          # Main entry point
├── requirements.txt
├── README.md
│
├── tmux/
│   ├── __init__.py
│   └── layout_manager.py         # Energy-adaptive layouts
│
├── commands/
│   ├── __init__.py
│   └── parser.py                 # Slash command parsing
│
├── agents/
│   ├── __init__.py
│   └── spawner.py                # AI CLI spawning
│
├── message_bus/
│   ├── __init__.py
│   └── tmux_capture.py           # TmuxCapture message bus
│
├── checkpoint/
│   ├── __init__.py
│   └── manager.py                # Auto-checkpoint system
│
├── routing/
│   ├── __init__.py
│   └── router.py                 # Command routing logic
│
├── session/
│   ├── __init__.py
│   └── restoration.py            # Session restoration
│
└── tests/
    ├── test_layout_manager.py
    ├── test_command_parser.py
    ├── test_agent_spawner.py
    ├── test_message_bus.py
    ├── test_checkpoint_manager.py
    ├── test_router.py
    └── integration/
        └── test_orchestrator_e2e.py
```

---

## Success Metrics

**Functionality**:
- [ ] Tmux layouts adapt to energy (2/3/4 panes)
- [ ] Slash commands route correctly
- [ ] AI agents launch successfully
- [ ] Message bus coordinates panes
- [ ] Auto-checkpoint every 30s
- [ ] Session restoration works

**ADHD Optimizations**:
- [ ] Energy-aware UI reduces cognitive load
- [ ] Checkpoints enable interrupt recovery
- [ ] Visual restoration summaries helpful
- [ ] Context preserved across days
- [ ] Gentle guidance throughout

**Performance**:
- [ ] Layout switching <1s
- [ ] Command routing <100ms
- [ ] Checkpoint save <500ms
- [ ] Message bus polling <1% CPU
- [ ] Overall system responsive

---

## Risk Assessment

**Risk 1: Tmux Complexity**
**Probability**: MEDIUM
**Impact**: MEDIUM
**Mitigation**: libtmux library simplifies, extensive testing

**Risk 2: Multi-Agent Coordination**
**Probability**: MEDIUM
**Impact**: MEDIUM
**Mitigation**: Message bus abstraction, clear protocols

**Risk 3: Checkpoint Data Loss**
**Probability**: LOW
**Impact**: HIGH
**Mitigation**: Redundant saves, ConPort reliability, error handling

---

## Rollout Plan

**Week 1**: Build core components
**Week 2**: Integration and testing
**Beta Test**: 3-5 developers for 1 week
**Full Rollout**: After feedback incorporated

---

**Total Effort**: 14 days (33 focus blocks)
**Risk Level**: MEDIUM (new UI component)
**Impact**: HIGH (beautiful multi-AI interface)
**ROI**: 🔥 Medium (significant UX improvement, but not blocking core functionality)
