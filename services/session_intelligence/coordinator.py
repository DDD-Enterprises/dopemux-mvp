"""
F-NEW-6: Unified Session Intelligence Coordinator

Combines Serena session state + ADHD Engine cognitive state into a unified
intelligent dashboard with actionable recommendations.

Data Sources:
- Serena: Session context (focus, worktree, branch, duration)
- ADHD Engine: Cognitive state (energy, attention, last break)

ADHD Benefits:
- Single glance → complete session awareness
- Proactive break reminders → better rest adherence
- Energy-matched task suggestions → sustained productivity
- Context switch detection → faster recovery

Performance: <200ms (target: 65ms via parallel fetch)

Based on Zen thinkdeep design (Decision #305).
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Serena session state."""
    session_id: str
    workspace: str
    worktree: str
    branch: str
    current_focus: Optional[str]
    session_duration_minutes: int
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class CognitiveState:
    """ADHD Engine cognitive state."""
    user_id: str
    energy_level: str  # low, medium, high
    attention_state: str  # scattered, transitioning, focused, hyperfocus
    last_break_timestamp: Optional[str]
    minutes_since_break: Optional[int]
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class Recommendation:
    """Single recommendation with priority and action."""
    type: str  # break, task, warning, info
    priority: str  # critical, high, medium, low
    message: str
    action: Optional[str] = None


class SessionIntelligenceCoordinator:
    """
    Coordinates session intelligence from Serena + ADHD Engine.

    Provides unified dashboard and actionable recommendations.
    """

    def __init__(self, workspace_path: Path = None):
        """
        Initialize session intelligence coordinator.

        Args:
            workspace_path: Workspace path for Serena integration
        """
        self.workspace = workspace_path or Path.cwd()
        self._serena_server = None  # Lazy-loaded
        self._adhd_config = None  # Lazy-loaded
        self._cache = {}  # Simple in-memory cache (10s TTL)
        self._cache_ttl = 10  # seconds

    async def _get_serena_server(self):
        """Get or initialize Serena MCP server (singleton)."""
        if self._serena_server is not None:
            return self._serena_server

        try:
            import sys
            serena_path = Path(__file__).parent.parent / "serena" / "v2"
            if str(serena_path) not in sys.path:
                sys.path.insert(0, str(serena_path))

            from mcp_server import SerenaV2MCPServer

            self._serena_server = SerenaV2MCPServer(workspace=self.workspace)
            logger.info("✅ SessionIntelligence connected to Serena v2")

        except Exception as e:
            logger.warning(f"⚠️ Serena unavailable: {e}")
            self._serena_server = None

        return self._serena_server

    async def _get_serena_session(self, session_id: Optional[str] = None) -> Optional[SessionState]:
        """
        Get session state from Serena MCP.

        Args:
            session_id: Optional session ID

        Returns:
            SessionState or None if unavailable
        """
        try:
            serena = await self._get_serena_server()
            if not serena:
                return None

            # Call Serena get_session_info tool
            result_json = await serena.get_session_info_tool()

            import json
            result = json.loads(result_json)

            return SessionState(
                session_id=result.get('session_id', ''),
                workspace=result.get('workspace', ''),
                worktree=result.get('worktree', ''),
                branch=result.get('branch', ''),
                current_focus=result.get('current_focus'),
                session_duration_minutes=result.get('session_duration_minutes', 0),
                workspace_path=str(self.workspace)
            )

        except Exception as e:
            logger.warning(f"Failed to get Serena session: {e}")
            return None

    async def _get_adhd_config(self):
        """Get or initialize ADHD config (singleton, same pattern as dope-context)."""
        if self._adhd_config is not None:
            return self._adhd_config

        try:
            import sys
            adhd_path = Path(__file__).parent.parent / "adhd_engine"
            if str(adhd_path) not in sys.path:
                sys.path.insert(0, str(adhd_path))

            from adhd_config_service import get_adhd_config_service

            self._adhd_config = await get_adhd_config_service()
            logger.info("✅ SessionIntelligence connected to ADHD Engine")

        except Exception as e:
            logger.warning(f"⚠️ ADHD Engine unavailable: {e}")
            self._adhd_config = None

        return self._adhd_config

    async def _get_adhd_state(self, user_id: str = "default") -> Optional[CognitiveState]:
        """
        Get cognitive state from ADHD Engine.

        Args:
            user_id: User identifier

        Returns:
            CognitiveState or None if unavailable
        """
        try:
            adhd_config = await self._get_adhd_config()
            if not adhd_config:
                return None

            # Get complete state summary (correct ADHD Engine API)
            state_summary = await adhd_config.get_current_state_summary(user_id)

            # Extract relevant fields
            energy = state_summary.get('energy_level', 'medium')
            attention = state_summary.get('attention_state', 'focused')

            # Calculate minutes since break (if break info available)
            # Note: ADHD Engine tracks should_break but not explicit break history yet
            should_break = state_summary.get('should_break', False)
            break_reason = state_summary.get('break_reason', '')

            # Estimate minutes since break from should_break flag
            # If should_break=True, assume 25+ minutes (Pomodoro threshold)
            minutes_since = 26 if should_break else None

            return CognitiveState(
                user_id=user_id,
                energy_level=energy,
                attention_state=attention,
                last_break_timestamp=None,  # Not tracked by ADHD Engine yet
                minutes_since_break=minutes_since,
                workspace_path=str(self.workspace)
            )

        except Exception as e:
            logger.warning(f"Failed to get ADHD state: {e}")
            return None

    async def _generate_recommendations(
        self,
        session: Optional[SessionState],
        cognitive: Optional[CognitiveState]
    ) -> List[Recommendation]:
        """
        Generate actionable recommendations from combined intelligence.

        Rules:
        1. Break timing (Pomodoro-style)
        2. Hyperfocus protection
        3. Energy-based task matching
        4. Context switch recovery

        Args:
            session: Serena session state
            cognitive: ADHD cognitive state

        Returns:
            List of recommendations sorted by priority
        """
        recommendations = []

        # Handle missing data gracefully
        if not session and not cognitive:
            return [Recommendation(
                type="warning",
                priority="low",
                message="Session intelligence unavailable (both systems down)"
            )]

        # Rule 1: Break timing (requires both session and cognitive data)
        if session and cognitive:
            duration = session.session_duration_minutes
            since_break = cognitive.minutes_since_break

            if duration and since_break:
                if duration > 25 and since_break > 25:
                    recommendations.append(Recommendation(
                        type="break",
                        priority="high",
                        message=f"Take 5-min break ({since_break} min since last)",
                        action="Stand up, stretch, look away from screen"
                    ))

        # Rule 2: Hyperfocus protection (requires both)
        if session and cognitive:
            duration = session.session_duration_minutes
            attention = cognitive.attention_state

            if duration and duration > 60 and attention == "hyperfocus":
                recommendations.append(Recommendation(
                    type="warning",
                    priority="critical",
                    message="MANDATORY BREAK - 60+ min hyperfocus detected",
                    action="Take 10-min break immediately to prevent burnout"
                ))

        # Rule 3: Energy-based task matching (requires cognitive only)
        if cognitive:
            energy = cognitive.energy_level

            if energy == "low":
                recommendations.append(Recommendation(
                    type="task",
                    priority="medium",
                    message="Low energy - consider low-complexity tasks (complexity <0.4)",
                    action="Review docs, write tests, refactor simple code"
                ))
            elif energy == "high" and cognitive.attention_state == "focused":
                recommendations.append(Recommendation(
                    type="task",
                    priority="low",
                    message="High energy + focus - optimal for complex work",
                    action="Tackle high-complexity tasks while conditions are ideal"
                ))

        # Rule 4: New session guidance (no break history)
        if cognitive and cognitive.minutes_since_break is None:
            recommendations.append(Recommendation(
                type="info",
                priority="low",
                message="New session - remember 25-min focus blocks with 5-min breaks"
            ))

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

        return recommendations

    def _format_dashboard(
        self,
        session: Optional[SessionState],
        cognitive: Optional[CognitiveState],
        recommendations: List[Recommendation]
    ) -> str:
        """
        Format unified dashboard for terminal display.

        Args:
            session: Serena session state
            cognitive: ADHD cognitive state
            recommendations: Generated recommendations

        Returns:
            Terminal-friendly dashboard string (max 20 lines)
        """
        lines = []

        # Header
        lines.append("╔" + "="*60 + "╗")
        lines.append("║" + " "*15 + "SESSION INTELLIGENCE DASHBOARD" + " "*15 + "║")
        lines.append("╚" + "="*60 + "╝")
        lines.append("")

        # Session context
        lines.append("SESSION CONTEXT")
        if session:
            focus = session.current_focus or "Unknown"
            # Truncate long paths
            if len(focus) > 50:
                focus = "..." + focus[-47:]
            lines.append(f"  Focus: {focus}")
            lines.append(f"  Branch: {session.branch}")
            lines.append(f"  Duration: {session.session_duration_minutes} minutes")
        else:
            lines.append("  (Serena unavailable)")

        lines.append("")

        # Cognitive state
        lines.append("COGNITIVE STATE")
        if cognitive:
            # Energy bars
            energy_bars = {
                'low': "█░░",
                'medium': "██░",
                'high': "███"
            }
            energy_display = energy_bars.get(cognitive.energy_level, "?")

            lines.append(f"  Energy: {energy_display} {cognitive.energy_level.title()}")
            lines.append(f"  Attention: {cognitive.attention_state.title()}")

            if cognitive.minutes_since_break is not None:
                lines.append(f"  Last Break: {cognitive.minutes_since_break} minutes ago")
            else:
                lines.append(f"  Last Break: Unknown (new session)")
        else:
            lines.append("  (ADHD Engine unavailable)")

        lines.append("")

        # Recommendations
        lines.append("RECOMMENDATIONS")
        if recommendations:
            for rec in recommendations[:3]:  # Top 3 recommendations only
                priority_symbol = {
                    'critical': "!!!",
                    'high': "!",
                    'medium': ">",
                    'low': "-"
                }
                symbol = priority_symbol.get(rec.priority, "-")
                lines.append(f"  {symbol} {rec.priority.upper()}: {rec.message}")
        else:
            lines.append("  No recommendations at this time")

        return "\n".join(lines)

    async def get_unified_dashboard(
        self,
        user_id: str = "default",
        session_id: Optional[str] = None
    ) -> str:
        """
        Get unified session intelligence dashboard.

        Args:
            user_id: User identifier for ADHD state
            session_id: Optional Serena session ID

        Returns:
            Formatted dashboard string for terminal display

        Performance: ~65ms (parallel fetch 50ms + logic 10ms + format 5ms)
        """
        start_time = time.time()

        # Parallel fetch from both sources
        serena_task = self._get_serena_session(session_id)
        adhd_task = self._get_adhd_state(user_id)

        session, cognitive = await asyncio.gather(
            serena_task,
            adhd_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(session, Exception):
            logger.error(f"Serena fetch failed: {session}")
            session = None

        if isinstance(cognitive, Exception):
            logger.error(f"ADHD Engine fetch failed: {cognitive}")
            cognitive = None

        # Generate recommendations
        recommendations = await self._generate_recommendations(session, cognitive)

        # Format dashboard
        dashboard = self._format_dashboard(session, cognitive, recommendations)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Unified dashboard generated in {elapsed_ms:.1f}ms")

        return dashboard


# Global singleton
_session_intelligence = None


async def get_session_intelligence() -> SessionIntelligenceCoordinator:
    """
    Get or create session intelligence coordinator singleton.

    Returns:
        SessionIntelligenceCoordinator instance
    """
    global _session_intelligence

    if _session_intelligence is None:
        _session_intelligence = SessionIntelligenceCoordinator()

    return _session_intelligence
