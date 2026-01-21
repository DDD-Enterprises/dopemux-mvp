"""
Timeout Manager - Operation-Specific Timeout Configuration
Manages different timeout values for different operation types

Architecture:
- Fixed timeouts per operation type (simple, predictable)
- User-configurable via agents.yaml
- Sensible defaults for 90% case
"""

from typing import Dict, Optional

import logging

logger = logging.getLogger(__name__)

from enum import Enum


class OperationType(Enum):
    """Types of operations with different timeout needs."""
    SPAWN = "spawn"                    # Starting an AI agent (10s)
    QUICK_RESPONSE = "quick_response"  # Simple queries (30s)
    ANALYSIS = "analysis"              # Code analysis (120s)
    RESEARCH = "research"              # Deep research (600s)
    HEALTH_CHECK = "health_check"      # Health ping (5s)


class TimeoutManager:
    """
    Manage operation-specific timeouts.

    Provides timeout values based on operation type with configurable defaults.
    """

    # Default timeouts (seconds)
    DEFAULT_TIMEOUTS = {
        OperationType.SPAWN: 10,
        OperationType.QUICK_RESPONSE: 30,
        OperationType.ANALYSIS: 120,
        OperationType.RESEARCH: 600,
        OperationType.HEALTH_CHECK: 5,
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize timeout manager.

        Args:
            config: Optional configuration dict from agents.yaml
                   Format: {'advanced': {'timeouts': {...}}}
        """
        self.timeouts = self.DEFAULT_TIMEOUTS.copy()

        # Override with config if provided
        if config and 'advanced' in config and 'timeouts' in config['advanced']:
            user_timeouts = config['advanced']['timeouts']
            self._apply_user_timeouts(user_timeouts)

    def _apply_user_timeouts(self, user_timeouts: Dict[str, int]):
        """Apply user-configured timeouts."""
        # Map string keys to OperationType enum
        mapping = {
            'spawn': OperationType.SPAWN,
            'quick_response': OperationType.QUICK_RESPONSE,
            'response': OperationType.QUICK_RESPONSE,  # Alias
            'analysis': OperationType.ANALYSIS,
            'research': OperationType.RESEARCH,
            'health_check': OperationType.HEALTH_CHECK,
            'health': OperationType.HEALTH_CHECK,  # Alias
        }

        for key, value in user_timeouts.items():
            if key in mapping:
                self.timeouts[mapping[key]] = value
                logger.info(f"ℹ️  Timeout override: {key} = {value}s")

    def get_timeout(
        self,
        operation_type: OperationType,
        default: Optional[int] = None
    ) -> int:
        """
        Get timeout for operation type.

        Args:
            operation_type: Type of operation
            default: Optional default if not configured

        Returns:
            Timeout in seconds

        Example:
            >>> timeout = manager.get_timeout(OperationType.SPAWN)
            >>> agent.start(timeout=timeout)
        """
        if default is not None:
            return self.timeouts.get(operation_type, default)
        return self.timeouts.get(operation_type, 30)  # Fallback default

    def get_all_timeouts(self) -> Dict[OperationType, int]:
        """
        Get all configured timeouts.

        Returns:
            Dictionary of operation type -> timeout seconds
        """
        return self.timeouts.copy()

    def set_timeout(self, operation_type: OperationType, seconds: int):
        """
        Set timeout for operation type.

        Args:
            operation_type: Operation type
            seconds: Timeout in seconds
        """
        self.timeouts[operation_type] = seconds
        logger.info(f"✅ Updated {operation_type.value} timeout: {seconds}s")


# Convenience function
def create_timeout_manager(config: Optional[Dict] = None) -> TimeoutManager:
    """
    Create timeout manager from configuration.

    Args:
        config: Optional configuration dict

    Returns:
        Configured TimeoutManager instance

    Example:
        >>> from src.config_loader import load_agent_config
        >>> config = load_agent_config()
        >>> timeout_mgr = create_timeout_manager(config)
    """
    return TimeoutManager(config)


if __name__ == "__main__":
    """Test timeout manager."""
    logger.info("🧪 Testing Timeout Manager")
    logger.info("=" * 60)

    # Test 1: Default timeouts
    logger.info("\n1. Testing default timeouts...")
    manager = TimeoutManager()

    for op_type in OperationType:
        timeout = manager.get_timeout(op_type)
        logger.info(f"   {op_type.value}: {timeout}s")

    # Test 2: Custom configuration
    logger.info("\n2. Testing custom configuration...")
    custom_config = {
        'advanced': {
            'timeouts': {
                'spawn': 15,      # Override: 15s instead of 10s
                'response': 45,   # Override: 45s instead of 30s
                'research': 900,  # Override: 15min instead of 10min
            }
        }
    }

    manager2 = TimeoutManager(custom_config)

    logger.info(f"   spawn: {manager2.get_timeout(OperationType.SPAWN)}s (was 10s)")
    logger.info(f"   quick_response: {manager2.get_timeout(OperationType.QUICK_RESPONSE)}s (was 30s)")
    logger.info(f"   research: {manager2.get_timeout(OperationType.RESEARCH)}s (was 600s)")

    # Test 3: Runtime updates
    logger.info("\n3. Testing runtime timeout updates...")
    manager.set_timeout(OperationType.SPAWN, 20)
    logger.info(f"   Updated spawn timeout: {manager.get_timeout(OperationType.SPAWN)}s")

    # Test 4: Get all timeouts
    logger.info("\n4. Getting all timeouts...")
    all_timeouts = manager.get_all_timeouts()
    logger.info(f"   Total configured: {len(all_timeouts)}")

    logger.info("\n✅ Timeout manager test complete!")
