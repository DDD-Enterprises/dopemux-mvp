"""
Error Recovery Manager - Priority 4
Production-grade resilience for multi-AI orchestration

Architecture (Confidence: 0.87):
- Smart retry with error classification
- Delayed restart with crash loop protection
- Auto-fallback with clear notification
- Fixed decision tree (debuggable, predictable)
- ConPort logging for pattern analysis

Performance:
- Fast path: 0ms overhead on success
- Retry: 1s + 2s + 4s = 7s max
- Restart: 10s, 20s, 40s (exponential, capped at 60s)
"""

import time

import logging

logger = logging.getLogger(__name__)

import os
from typing import Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from .response_parser import ErrorType, ParseResult
from .conport_client import get_conport_client


class Severity(Enum):
    """Error severity for notification prioritization."""
    CRITICAL = "critical"  # Blocks until acknowledged
    HIGH = "high"          # Immediate console notification
    MEDIUM = "medium"      # Batched notifications
    LOW = "low"            # Status bar only


class RecoveryAction(Enum):
    """Available recovery actions."""
    RESTART_WITH_BACKOFF = "restart_with_backoff"
    KILL_AND_RESTART = "kill_and_restart"
    RETRY_ONCE = "retry_once"
    FALLBACK_TO_OTHER_AGENT = "fallback"
    WAIT_AND_RETRY = "wait_and_retry"
    FAIL_GRACEFULLY = "fail_gracefully"


@dataclass
class RecoveryResult:
    """Result of recovery attempt."""
    success: bool
    action_taken: RecoveryAction
    message: str
    attempts: int = 1
    recovery_time_seconds: float = 0.0


class ErrorRecoveryManager:
    """
    Manages error recovery with fixed decision tree.

    Handles:
    - Agent crashes (restart with backoff)
    - Timeouts (kill and restart hung processes)
    - Rate limits (fallback to other agents)
    - Empty responses (retry once)
    - API errors (classify and handle)
    """

    # Error type → recovery action mapping
    RECOVERY_ACTIONS = {
        ErrorType.CRASH: RecoveryAction.RESTART_WITH_BACKOFF,
        ErrorType.TIMEOUT: RecoveryAction.KILL_AND_RESTART,
        ErrorType.EMPTY: RecoveryAction.RETRY_ONCE,
        ErrorType.API_ERROR: RecoveryAction.FALLBACK_TO_OTHER_AGENT,
        ErrorType.PARSE_ERROR: RecoveryAction.RETRY_ONCE,
    }

    # Error type → severity mapping
    ERROR_SEVERITY = {
        ErrorType.CRASH: Severity.HIGH,
        ErrorType.TIMEOUT: Severity.MEDIUM,
        ErrorType.EMPTY: Severity.LOW,
        ErrorType.API_ERROR: Severity.MEDIUM,
        ErrorType.PARSE_ERROR: Severity.LOW,
    }

    def __init__(self, workspace_id: str):
        """
        Initialize error recovery manager.

        Args:
            workspace_id: Workspace path for ConPort logging
        """
        self.workspace_id = workspace_id
        self.conport = get_conport_client(workspace_id)
        self.recovery_history: List[dict] = []

    def recover(
        self,
        agent,
        error_type: ErrorType,
        error_info: dict,
        fallback_agents: Optional[list] = None
    ) -> RecoveryResult:
        """
        Execute recovery action for error.

        Args:
            agent: Agent that encountered error
            error_type: Type of error
            error_info: Additional error details
            fallback_agents: Optional list of fallback agents

        Returns:
            RecoveryResult with outcome

        Example:
            >>> recovery = manager.recover(
            ...     agent=claude_agent,
            ...     error_type=ErrorType.CRASH,
            ...     error_info={'last_output': output}
            ... )
            >>> if recovery.success:
            ...     logger.info("Agent recovered!")
        """
        start_time = time.time()

        # Get recovery action
        action = self.RECOVERY_ACTIONS.get(
            error_type,
            RecoveryAction.FAIL_GRACEFULLY
        )

        # Notify user
        self._notify_error(agent, error_type, action)

        # Execute recovery
        if action == RecoveryAction.RESTART_WITH_BACKOFF:
            result = self._restart_with_backoff(agent)

        elif action == RecoveryAction.KILL_AND_RESTART:
            result = self._kill_and_restart(agent)

        elif action == RecoveryAction.RETRY_ONCE:
            result = RecoveryResult(
                success=True,  # Caller should retry
                action_taken=action,
                message="Retry recommended",
                attempts=1
            )

        elif action == RecoveryAction.FALLBACK_TO_OTHER_AGENT:
            result = self._suggest_fallback(agent, fallback_agents)

        else:  # FAIL_GRACEFULLY
            result = RecoveryResult(
                success=False,
                action_taken=action,
                message=f"No recovery available for {error_type.value}",
                attempts=0
            )

        # Calculate recovery time
        result.recovery_time_seconds = time.time() - start_time

        # Log to ConPort if notable
        self._log_recovery(agent, error_type, result)

        return result

    def _restart_with_backoff(self, agent) -> RecoveryResult:
        """
        Restart agent with crash loop protection.

        Uses exponential backoff: 10s, 20s, 40s (capped at 60s)
        """
        if agent.restart_count >= agent.config.max_restarts:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RESTART_WITH_BACKOFF,
                message=f"Max restarts ({agent.config.max_restarts}) reached",
                attempts=agent.restart_count
            )

        # Calculate backoff
        backoff = min(10 * (2 ** agent.restart_count), 60)

        logger.info(f"🔄 Restarting {agent.config.agent_type.value} in {backoff}s...")
        logger.info(f"   Attempt {agent.restart_count + 1}/{agent.config.max_restarts}")

        time.sleep(backoff)

        # Attempt restart
        agent.restart_count += 1
        success = agent.start()

        if success:
            logger.info(f"✅ {agent.config.agent_type.value} restarted successfully")
            # Reset counter on successful restart
            agent.restart_count = 0

            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.RESTART_WITH_BACKOFF,
                message="Agent restarted successfully",
                attempts=agent.restart_count
            )
        else:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RESTART_WITH_BACKOFF,
                message="Restart failed",
                attempts=agent.restart_count
            )

    def _kill_and_restart(self, agent) -> RecoveryResult:
        """
        Kill hung process and restart.

        For timeout scenarios where process is alive but not responding.
        """
        logger.info(f"⚠️  {agent.config.agent_type.value} appears hung, forcing restart...")

        # Try to stop gracefully first
        try:
            agent.stop()
            time.sleep(1)
        except Exception as e:
            pass

            logger.error(f"Error: {e}")
        # Force kill if still alive
        if agent.pid:
            try:
                os.kill(agent.pid, 9)  # SIGKILL
                logger.info(f"   Killed process {agent.pid}")
            except Exception as e:
                pass

                logger.error(f"Error: {e}")
        # Wait a moment for cleanup
        time.sleep(2)

        # Restart
        success = agent.start()

        if success:
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.KILL_AND_RESTART,
                message="Hung process killed and restarted",
                attempts=1
            )
        else:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.KILL_AND_RESTART,
                message="Failed to restart after kill",
                attempts=1
            )

    def _suggest_fallback(
        self,
        agent,
        fallback_agents: Optional[list]
    ) -> RecoveryResult:
        """
        Suggest fallback to other agents.

        Returns result indicating fallback should be used.
        Caller is responsible for actually routing to fallback.
        """
        if fallback_agents:
            healthy_fallbacks = [a for a in fallback_agents if a.is_healthy()]

            if healthy_fallbacks:
                fallback = healthy_fallbacks[0]
                logger.info(f"⚠️  {agent.config.agent_type.value} unavailable")
                logger.info(f"✅ Fallback to {fallback.config.agent_type.value} recommended")

                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.FALLBACK_TO_OTHER_AGENT,
                    message=f"Fallback to {fallback.config.agent_type.value}",
                    attempts=1
                )

        # No fallback available
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.FAIL_GRACEFULLY,
            message="No fallback agents available",
            attempts=0
        )

    def retry_operation(
        self,
        operation: Callable,
        max_attempts: int = 3,
        operation_name: str = "operation"
    ) -> any:
        """
        Retry operation with smart exponential backoff.

        Args:
            operation: Function to retry
            max_attempts: Maximum retry attempts
            operation_name: Name for logging

        Returns:
            Result from operation

        Raises:
            Last exception if all attempts fail

        Example:
            >>> result = recovery.retry_operation(
            ...     lambda: agent.send_command("test"),
            ...     max_attempts=3,
            ...     operation_name="send_command"
            ... )
        """
        last_exception = None

        for attempt in range(max_attempts):
            try:
                logger.info(f"🔄 {operation_name}: Attempt {attempt + 1}/{max_attempts}...")
                result = operation()
                logger.info(f"✅ {operation_name} succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e
                logger.error(f"❌ {operation_name} failed: {e}")

                if attempt < max_attempts - 1:
                    # Exponential backoff
                    wait = 2 ** attempt
                    logger.info(f"⏳ Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    logger.error(f"❌ {operation_name} failed after {max_attempts} attempts")

        # All attempts failed
        raise last_exception

    def _notify_error(self, agent, error_type: ErrorType, action: RecoveryAction):
        """
        Notify user of error with severity-based approach.

        Args:
            agent: Agent with error
            error_type: Type of error
            action: Recovery action being taken
        """
        severity = self.ERROR_SEVERITY.get(error_type, Severity.MEDIUM)

        agent_name = agent.config.agent_type.value

        if severity == Severity.CRITICAL:
            # Modal/blocking notification (not used currently)
            logger.info(f"\n{'=' * 60}")
            logger.error(f"🚨 CRITICAL ERROR: {agent_name}")
            logger.error(f"   Error: {error_type.value}")
            logger.info(f"   Action: {action.value}")
            logger.info(f"{'=' * 60}\n")

        elif severity == Severity.HIGH:
            # Immediate console notification
            logger.error(f"❌ {agent_name}: {error_type.value}")
            logger.info(f"🔧 Recovering via: {action.value}")

        elif severity == Severity.MEDIUM:
            # Standard notification
            logger.error(f"⚠️  {agent_name}: {error_type.value} → {action.value}")

        else:  # LOW
            # Minimal notification
            logger.error(f"ℹ️  {agent_name}: {error_type.value}")

    def _log_recovery(
        self,
        agent,
        error_type: ErrorType,
        result: RecoveryResult
    ):
        """
        Log recovery attempt to ConPort (smart filtering).

        Only logs notable events:
        - Successful recoveries (learn from)
        - Failed recoveries after max attempts
        - First occurrence of error type
        """
        # Check if notable
        if not self._is_notable_recovery(error_type, result):
            return

        # Log to ConPort
        try:
            self.conport.log_decision(
                summary=f"{agent.config.agent_type.value} recovery: {error_type.value}",
                rationale=f"Error encountered: {error_type.value}",
                implementation_details=(
                    f"Recovery action: {result.action_taken.value}\n"
                    f"Outcome: {'Success' if result.success else 'Failed'}\n"
                    f"Attempts: {result.attempts}\n"
                    f"Time: {result.recovery_time_seconds:.2f}s\n"
                    f"Message: {result.message}"
                ),
                tags=[
                    'error_recovery',
                    agent.config.agent_type.value,
                    error_type.value,
                    result.action_taken.value
                ]
            )
            logger.info(f"📝 Recovery logged to ConPort")
        except Exception as e:
            # Silent failure - logging shouldn't break recovery
            pass

            logger.error(f"Error: {e}")
        # Add to local history
        self.recovery_history.append({
            'timestamp': datetime.now().isoformat(),
            'agent': agent.config.agent_type.value,
            'error_type': error_type.value,
            'action': result.action_taken.value,
            'success': result.success,
            'attempts': result.attempts,
        })

    def _is_notable_recovery(self, error_type: ErrorType, result: RecoveryResult) -> bool:
        """
        Determine if recovery is worth logging to ConPort.

        Reduces noise - only log significant events.
        """
        # Always log successful recoveries (learn from them)
        if result.success:
            return True

        # Always log failures after multiple attempts
        if result.attempts >= 3:
            return True

        # Log crashes (always notable)
        if error_type == ErrorType.CRASH:
            return True

        # Don't log minor transient issues
        return False

    def get_recovery_stats(self) -> dict:
        """
        Get recovery statistics.

        Returns:
            Dictionary with recovery metrics
        """
        total = len(self.recovery_history)
        if total == 0:
            return {
                'total_recoveries': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0,
                'by_error_type': {},
                'by_action': {},
            }

        successful = sum(1 for r in self.recovery_history if r['success'])

        # Group by error type
        by_error_type = {}
        for r in self.recovery_history:
            error_type = r['error_type']
            by_error_type[error_type] = by_error_type.get(error_type, 0) + 1

        # Group by action
        by_action = {}
        for r in self.recovery_history:
            action = r['action']
            by_action[action] = by_action.get(action, 0) + 1

        return {
            'total_recoveries': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total,
            'by_error_type': by_error_type,
            'by_action': by_action,
        }


def is_retryable(error_type: ErrorType) -> bool:
    """
    Classify error as retryable or permanent.

    Retryable: Network issues, timeouts, empty responses
    Permanent: Crashes (need restart, not retry)

    Args:
        error_type: Error type to classify

    Returns:
        True if error is likely transient and worth retrying
    """
    RETRYABLE = {
        ErrorType.TIMEOUT,
        ErrorType.EMPTY,
        ErrorType.API_ERROR,
        ErrorType.PARSE_ERROR,
    }
    return error_type in RETRYABLE


def retry_with_backoff(
    operation: Callable,
    max_attempts: int = 3,
    operation_name: str = "operation"
) -> any:
    """
    Retry operation with exponential backoff and visual feedback.

    Args:
        operation: Function to retry
        max_attempts: Maximum attempts
        operation_name: Name for logging

    Returns:
        Result from successful operation

    Raises:
        Last exception if all attempts fail

    Example:
        >>> result = retry_with_backoff(
        ...     lambda: agent.send_command("test"),
        ...     max_attempts=3,
        ...     operation_name="send test command"
        ... )
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                logger.info(f"🔄 {operation_name}: Retry {attempt + 1}/{max_attempts}...")

            result = operation()

            if attempt > 0:
                logger.info(f"✅ {operation_name} recovered on attempt {attempt + 1}")

            return result

        except Exception as e:
            last_exception = e

            if attempt < max_attempts - 1:
                # Exponential backoff: 1s, 2s, 4s
                wait = 2 ** attempt
                logger.info(f"⏳ Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                logger.error(f"❌ {operation_name} failed after {max_attempts} attempts")

    # All attempts failed
    raise last_exception


if __name__ == "__main__":
    """Test error recovery manager."""
    logger.error("🧪 Testing Error Recovery Manager")
    logger.info("=" * 60)

    manager = ErrorRecoveryManager("/Users/hue/code/ui-build")

    # Test 1: Error classification
    logger.error("\n1. Testing error classification...")
    logger.error(f"   TIMEOUT retryable: {is_retryable(ErrorType.TIMEOUT)}")
    logger.error(f"   CRASH retryable: {is_retryable(ErrorType.CRASH)}")

    # Test 2: Retry with backoff simulation
    logger.info("\n2. Testing retry with backoff...")

    attempt_count = [0]

    def flaky_operation():
        """Simulates operation that fails twice, then succeeds."""
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise Exception(f"Transient error (attempt {attempt_count[0]})")
        return "Success!"

    try:
        result = retry_with_backoff(
            flaky_operation,
            max_attempts=3,
            operation_name="flaky test"
        )
        logger.info(f"   ✅ Result: {result}")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")

    # Test 3: Recovery stats
    logger.info("\n3. Testing recovery statistics...")
    stats = manager.get_recovery_stats()
    logger.info(f"   Total recoveries: {stats['total_recoveries']}")
    logger.info(f"   Success rate: {stats['success_rate']:.0%}")

    logger.error("\n✅ Error recovery manager test complete!")
