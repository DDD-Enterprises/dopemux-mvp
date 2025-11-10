"""
ADHD Engine ConPort MCP Client

Simple client for ConPort integration with circuit breaker protection.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Circuit breaker for ConPort calls
circuit_breaker = None

def get_conport_circuit_breaker():
    """Get or create ConPort circuit breaker"""
    global circuit_breaker
    if circuit_breaker is None:
        try:
            from ..error_handling import CircuitBreaker, CircuitBreakerConfig
            circuit_breaker = CircuitBreaker(
                CircuitBreakerConfig(
                    name="conport_mcp_circuit",
                    failure_threshold=3,
                    recovery_timeout=90,
                    success_threshold=2,
                    timeout=10.0
                )
            )
        except ImportError:
            # Fallback if error handling not available
            circuit_breaker = None
    return circuit_breaker


class ConPortMCPClient:
    """
    ConPort MCP Client for ADHD Engine
    Provides access to ConPort data for pattern learning and task analysis
    """

    def __init__(self):
        self.conport_url = "http://localhost:3010"  # ConPort MCP server
        self.session: Optional[Any] = None

    async def initialize(self):
        """Initialize client (no-op for now)"""
        logger.info("ConPort MCP Client initialized")
        return

    async def close(self):
        """Close client connections"""
        if self.session:
            # await self.session.close()  # Commented out for mock implementation
            self.session = None

    async def get_progress(self, workspace_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent progress entries from ConPort
        Used for task completion pattern analysis
        """
        breaker = get_conport_circuit_breaker()
        if breaker:
            try:
                return await breaker.call(self._get_progress_impl, workspace_id, limit)
            except Exception as e:
                logger.warning(f"Circuit breaker triggered for ConPort progress: {e}")
                return []
        else:
            # Fallback without circuit breaker
            return await self._get_progress_impl(workspace_id, limit)

    async def _get_progress_impl(self, workspace_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Actual implementation of progress retrieval"""
        try:
            logger.info(f"Getting progress from ConPort for {workspace_id}")
            # Mock response - would be actual MCP call in production
            return [
                {
                    "id": 1,
                    "status": "DONE",
                    "description": "Sample task completion",
                    "tags": ["test", "sample"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get ConPort progress: {e}")
            raise

    async def get_decisions(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent decisions from ConPort
        Used for decision pattern analysis
        """
        breaker = get_conport_circuit_breaker()
        if breaker:
            try:
                return await breaker.call(self._get_decisions_impl, workspace_id, limit)
            except Exception as e:
                logger.warning(f"Circuit breaker triggered for ConPort decisions: {e}")
                return []
        else:
            # Fallback without circuit breaker
            return await self._get_decisions_impl(workspace_id, limit)

    async def _get_decisions_impl(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Actual implementation of decisions retrieval"""
        try:
            logger.info(f"Getting decisions from ConPort for {workspace_id}")
            return [
                {
                    "id": 1,
                    "summary": "Sample decision",
                    "rationale": "Sample rationale",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": ["test", "sample"]
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get ConPort decisions: {e}")
            raise

    async def write_custom_data(self, workspace_id: str, category: str, key: str, value: Any) -> None:
        """
        Write custom data to ConPort
        Used for storing ADHD patterns and user preferences
        """
        try:
            logger.info(f"Writing ADHD data to ConPort: {category}/{key}")
            # Mock implementation - would be actual MCP call in production
            return
        except Exception as e:
            logger.error(f"Failed to write ConPort custom data: {e}")

    def get_task_completion_patterns(self, workspace_id: str) -> Dict[str, Any]:
        """
        Analyze task completion patterns for ADHD insights
        """
        # Get progress data and analyze patterns
        progress_entries = asyncio.run(self.get_progress(workspace_id))

        patterns = {
            "total_tasks": len(progress_entries),
            "completion_rate": 0.8,  # Mock for now
            "average_completion_time": 25,
            "peak_productivity_hours": [9, 10, 11, 14, 15, 16],
            "common_blockers": ["context_switch", "low_energy"],
            "energy_patterns": {
                "morning": "high",
                "afternoon": "medium",
                "evening": "low"
            }
        }

        return patterns

    def get_decision_patterns(self, workspace_id: str) -> Dict[str, Any]:
        """
        Analyze decision-making patterns
        """
        decisions = asyncio.run(self.get_decisions(workspace_id))

        patterns = {
            "total_decisions": len(decisions),
            "decisions_per_day": 3.2,
            "common_tags": ["architecture", "implementation", "testing"],
            "decision_complexity_trends": "stable",
            "implementation_success_rate": 0.85
        }

        return patterns