"""
Conversation Manager - Context Tracking for Multi-Turn Dialogs
Manages conversation history with dual storage (local + ConPort)

Architecture:
- Local storage (fast access, last 50 exchanges)
- ConPort persistence (survives restarts)
- Per-agent filtering (collaborative workflows)
- ADHD-optimized (bounded memory, clear context assembly)
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
from .conport_client import get_conport_client
from .response_parser import ParseResult


@dataclass
class Exchange:
    """Single conversation exchange (input + output)."""
    timestamp: datetime
    agent_type: str  # claude, gemini, grok
    input: str
    output: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for ConPort storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Exchange':
        """Reconstruct from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ConversationManager:
    """
    Manage conversation context across agents.

    Dual storage strategy:
    - Local: Fast access (last 50 exchanges)
    - ConPort: Persistent storage (survives restarts)

    ADHD Optimization:
    - Bounded memory (prevent overwhelm)
    - Clear context assembly (last N exchanges)
    - Per-agent filtering (focus on relevant history)
    """

    def __init__(self, session_id: str, workspace_id: str):
        """
        Initialize conversation manager.

        Args:
            session_id: Unique session identifier
            workspace_id: Workspace path for ConPort
        """
        self.session_id = session_id
        self.workspace_id = workspace_id
        self.local_history: List[Exchange] = []
        self.conport_client = get_conport_client(workspace_id)

        # Try to restore history from ConPort
        self._restore_from_conport()

    def add_exchange(
        self,
        agent_type: str,
        input_text: str,
        parse_result: ParseResult
    ):
        """
        Add conversation exchange to history.

        Stores locally (fast) and in ConPort (persistent).

        Args:
            agent_type: AI provider name
            input_text: User input/command
            parse_result: Parsed AI response
        """
        exchange = Exchange(
            timestamp=datetime.now(),
            agent_type=agent_type,
            input=input_text,
            output=parse_result.content,
            success=parse_result.success,
            error=parse_result.error_message,
            metadata=parse_result.metadata,
        )

        # Store locally (fast access)
        self.local_history.append(exchange)

        # Keep only last 50 (ADHD: bounded memory)
        if len(self.local_history) > 50:
            self.local_history = self.local_history[-50:]

        # Store in ConPort (persistent)
        self._save_to_conport(exchange)

    def get_recent_context(self, n: int = 10) -> List[Exchange]:
        """
        Get recent conversation exchanges.

        Args:
            n: Number of recent exchanges to return

        Returns:
            List of recent exchanges (newest last)

        ADHD Benefit:
            Quick context assembly - no searching through history
        """
        return self.local_history[-n:]

    def get_agent_context(self, agent_type: str, n: int = 5) -> List[Exchange]:
        """
        Get recent exchanges for specific agent.

        Args:
            agent_type: AI provider to filter by
            n: Number of exchanges to return

        Returns:
            Recent exchanges for this agent

        Use Case:
            Multi-turn conversation with same agent
        """
        agent_exchanges = [
            e for e in self.local_history
            if e.agent_type == agent_type
        ]
        return agent_exchanges[-n:]

    def format_context_for_agent(
        self,
        agent_type: str,
        include_other_agents: bool = False,
        max_exchanges: int = 5
    ) -> str:
        """
        Format conversation context for passing to AI agent.

        Args:
            agent_type: Target agent type
            include_other_agents: Include exchanges from other agents
            max_exchanges: Maximum exchanges to include

        Returns:
            Formatted context string ready for AI

        Example:
            >>> context = manager.format_context_for_agent('claude')
            >>> agent.send_command(f"Context: {context}\n\nNew task: ...")
        """
        if include_other_agents:
            exchanges = self.get_recent_context(max_exchanges)
        else:
            exchanges = self.get_agent_context(agent_type, max_exchanges)

        if not exchanges:
            return ""

        # Format as conversation
        context_parts = []
        for ex in exchanges:
            context_parts.append(f"[{ex.agent_type} at {ex.timestamp.strftime('%H:%M:%S')}]")
            context_parts.append(f"User: {ex.input}")
            context_parts.append(f"AI: {ex.output}")
            context_parts.append("")  # Blank line between exchanges

        return '\n'.join(context_parts)

    def get_conversation_stats(self) -> dict:
        """
        Get conversation statistics.

        Returns:
            Stats dictionary with counts and metrics
        """
        total = len(self.local_history)
        successful = sum(1 for e in self.local_history if e.success)
        errors = total - successful

        # Per-agent stats
        agent_counts = {}
        for exchange in self.local_history:
            agent_counts[exchange.agent_type] = agent_counts.get(exchange.agent_type, 0) + 1

        return {
            'total_exchanges': total,
            'successful': successful,
            'errors': errors,
            'success_rate': successful / total if total > 0 else 0.0,
            'agent_counts': agent_counts,
            'session_id': self.session_id,
        }

    def _save_to_conport(self, exchange: Exchange):
        """
        Save exchange to ConPort.

        Silent failure - local storage is primary.
        """
        try:
            key = f"{self.session_id}_{exchange.timestamp.timestamp()}"
            result = self.conport_client.log_custom_data(
                category="conversation_history",
                key=key,
                value=exchange.to_dict()
            )

            if not result.get('success'):
                # Silent - local storage still works
                pass

        except Exception as e:
            # Silent failure - local history is primary
            pass

    def _restore_from_conport(self):
        """
        Restore recent conversation history from ConPort.

        Called on initialization to resume context after restart.
        """
        try:
            # Query recent conversation history
            results = self.conport_client.get_custom_data(
                category="conversation_history",
                limit=50  # Last 50 exchanges
            )

            # Reconstruct exchanges
            for item in results:
                try:
                    exchange = Exchange.from_dict(item)
                    self.local_history.append(exchange)
                except Exception:
                    # Skip malformed entries
                    continue

            if self.local_history:
                print(f"✅ Restored {len(self.local_history)} exchanges from ConPort")

        except Exception as e:
            # Silent failure - start with empty history
            pass


if __name__ == "__main__":
    """Test conversation manager."""
    print("🧪 Testing Conversation Manager")
    print("=" * 60)

    manager = ConversationManager(
        session_id="test_session",
        workspace_id="/Users/hue/code/ui-build"
    )

    # Simulate some exchanges
    print("\n1. Adding sample exchanges...")

    # Mock ParseResult
    from .response_parser import ParseResult

    manager.add_exchange(
        agent_type="claude",
        input_text="What is 2+2?",
        parse_result=ParseResult(
            success=True,
            content="2 + 2 = 4. Simple arithmetic!",
            metadata={}
        )
    )

    manager.add_exchange(
        agent_type="gemini",
        input_text="Research async Python",
        parse_result=ParseResult(
            success=True,
            content="Asyncio is Python's native async framework...",
            metadata={}
        )
    )

    # Get context
    print("\n2. Getting recent context...")
    recent = manager.get_recent_context(n=5)
    print(f"   Found {len(recent)} recent exchanges")

    # Get agent-specific
    print("\n3. Getting Claude-specific context...")
    claude_context = manager.get_agent_context('claude', n=5)
    print(f"   Found {len(claude_context)} Claude exchanges")

    # Format for agent
    print("\n4. Formatting context for agent...")
    formatted = manager.format_context_for_agent('claude', include_other_agents=True)
    print(f"   Formatted context ({len(formatted)} chars):")
    print(f"   {formatted[:200]}...")

    # Stats
    print("\n5. Getting conversation stats...")
    stats = manager.get_conversation_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ Conversation manager test complete!")
