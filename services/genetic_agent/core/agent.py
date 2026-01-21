"""Base agent class for the Genetic Coding Agent system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from .config import AgentConfig
from .state import AgentState, AgentStatus


class BaseAgent(ABC):
    """Abstract base class for all coding agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus()
        self._circuit_breaker_tokens = 0

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a repair task with full lifecycle management."""
        try:
            # Pre-flight checks
            if not self._check_circuit_breaker():
                return {
                    "success": False,
                    "error": "Circuit breaker activated - too many tokens used",
                    "state": self.status.state.value
                }

            # Update status
            self.status.update_state(AgentState.ANALYZING, task)

            # Execute repair
            result = await self._execute_repair(task)

            # Update final status
            self.status.update_state(AgentState.IDLE)

            return result

        except Exception as e:
            self.status.set_error(str(e))
            return {
                "success": False,
                "error": str(e),
                "state": self.status.state.value
            }

            logger.error(f"Error: {e}")
    @abstractmethod
    async def _execute_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual repair logic. Must be implemented by subclasses."""
        pass

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should prevent operation."""
        # Simple token-based circuit breaker
        # In production, this would track actual token usage
        if self._circuit_breaker_tokens >= self.config.max_tokens:
            return False
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return self.status.get_status_dict()

    def reset_circuit_breaker(self):
        """Reset the circuit breaker (for testing/admin purposes)."""
        self._circuit_breaker_tokens = 0