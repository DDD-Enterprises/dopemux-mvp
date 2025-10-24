"""
Serena Integration for ConPort-KG Event System

Hooks into Serena v2 complexity analysis to emit events when:
- High complexity code is detected (>0.6)
- Refactoring recommendations are generated

Events emitted:
- code.complexity.high: High complexity file detected
- code.refactoring.recommended: Refactoring suggestion with rationale
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class SerenaEventEmitter:
    """
    Event emitter for Serena code intelligence.

    Wraps Serena operations and emits events to Integration Bridge
    for pattern detection and ConPort logging.

    Features:
    - Non-blocking event emission
    - Automatic workspace detection
    - Complexity threshold filtering
    - Circuit breaker integration
    - ADHD-optimized: Zero latency impact on Serena
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        complexity_threshold: float = 0.6,
        enable_events: bool = True
    ):
        """
        Initialize Serena event emitter.

        Args:
            event_bus: EventBus instance for publishing
            workspace_id: Workspace ID for event context
            complexity_threshold: Complexity score to trigger events (default: 0.6)
            enable_events: Enable event emission (default: True)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.complexity_threshold = complexity_threshold
        self.enable_events = enable_events

        # Metrics
        self.events_emitted = 0
        self.high_complexity_events = 0
        self.refactoring_events = 0
        self.emission_errors = 0

    async def emit_complexity_analyzed(
        self,
        file_path: str,
        complexity_score: float,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit event when file complexity is analyzed.

        Args:
            file_path: Path to analyzed file
            complexity_score: Calculated complexity score (0.0-1.0)
            metrics: Optional detailed complexity metrics

        Returns:
            True if event emitted successfully, False otherwise
        """
        if not self.enable_events:
            return False

        try:
            # Only emit for high complexity
            if complexity_score >= self.complexity_threshold:
                event = Event(
                    type="code.complexity.high",
                    data={
                        "file": file_path,
                        "complexity": complexity_score,
                        "workspace_id": self.workspace_id,
                        "metrics": metrics or {},
                        "threshold": self.complexity_threshold
                    },
                    source="serena"
                )

                # Publish to dopemux:events stream (non-blocking)
                msg_id = await self.event_bus.publish("dopemux:events", event)

                if msg_id:
                    self.events_emitted += 1
                    self.high_complexity_events += 1
                    logger.debug(
                        f"📤 Emitted code.complexity.high: {file_path} "
                        f"(score: {complexity_score:.2f})"
                    )
                    return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit complexity event: {e}")

        return False

    async def emit_refactoring_recommended(
        self,
        file_path: str,
        complexity_score: float,
        reasons: list[str],
        recommended_actions: list[str],
        priority: str = "medium"
    ) -> bool:
        """
        Emit event when refactoring is recommended.

        Args:
            file_path: Path to file needing refactoring
            complexity_score: Current complexity score
            reasons: List of reasons for refactoring
            recommended_actions: List of specific recommended actions
            priority: Priority level (low/medium/high/critical)

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="code.refactoring.recommended",
                data={
                    "file": file_path,
                    "complexity": complexity_score,
                    "reasons": reasons,
                    "recommended_actions": recommended_actions,
                    "priority": priority,
                    "workspace_id": self.workspace_id
                },
                source="serena"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.refactoring_events += 1
                logger.info(
                    f"📤 Emitted refactoring.recommended: {file_path} "
                    f"({priority} priority)"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit refactoring event: {e}")

        return False

    async def emit_code_navigation(
        self,
        from_symbol: str,
        to_symbol: str,
        navigation_type: str,
        success: bool = True
    ) -> bool:
        """
        Emit event when code navigation occurs.

        Args:
            from_symbol: Source symbol navigated from
            to_symbol: Target symbol navigated to
            navigation_type: Type of navigation (goto_definition, find_references, etc.)
            success: Whether navigation was successful

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="code.navigation.performed",
                data={
                    "from_symbol": from_symbol,
                    "to_symbol": to_symbol,
                    "navigation_type": navigation_type,
                    "success": success,
                    "workspace_id": self.workspace_id
                },
                source="serena"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.debug(f"Failed to emit navigation event: {e}")

        return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event emission metrics.

        Returns:
            Dictionary with emission stats
        """
        return {
            "agent": "serena",
            "events_emitted": self.events_emitted,
            "high_complexity_events": self.high_complexity_events,
            "refactoring_events": self.refactoring_events,
            "navigation_events": self.events_emitted - self.high_complexity_events - self.refactoring_events,
            "emission_errors": self.emission_errors,
            "complexity_threshold": self.complexity_threshold,
            "events_enabled": self.enable_events
        }

    def reset_metrics(self):
        """Reset emission metrics"""
        self.events_emitted = 0
        self.high_complexity_events = 0
        self.refactoring_events = 0
        self.emission_errors = 0


class SerenaIntegrationManager:
    """
    Manages Serena integration with ConPort-KG event system.

    Provides:
    - Event emitter initialization
    - Lifecycle management
    - Metrics aggregation
    - Configuration management
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_complexity_events: bool = True,
        enable_navigation_events: bool = False,  # Optional, lower priority
        complexity_threshold: float = 0.6
    ):
        """
        Initialize Serena integration manager.

        Args:
            event_bus: EventBus instance
            workspace_id: Workspace ID
            enable_complexity_events: Enable complexity analysis events (default: True)
            enable_navigation_events: Enable navigation events (default: False)
            complexity_threshold: Threshold for high complexity (default: 0.6)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_complexity_events = enable_complexity_events
        self.enable_navigation_events = enable_navigation_events

        # Create event emitter
        self.emitter = SerenaEventEmitter(
            event_bus=event_bus,
            workspace_id=workspace_id,
            complexity_threshold=complexity_threshold,
            enable_events=enable_complexity_events
        )

        logger.info(
            f"✅ Serena integration initialized "
            f"(complexity events: {enable_complexity_events}, "
            f"threshold: {complexity_threshold})"
        )

    async def handle_complexity_result(
        self,
        file_path: str,
        complexity_score: float,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Handle complexity analysis result from Serena.

        Args:
            file_path: Analyzed file path
            complexity_score: Calculated complexity
            metrics: Optional detailed metrics
        """
        if not self.enable_complexity_events:
            return

        # Emit complexity event
        await self.emitter.emit_complexity_analyzed(
            file_path=file_path,
            complexity_score=complexity_score,
            metrics=metrics
        )

        # If very high complexity, also emit refactoring recommendation
        if complexity_score >= 0.7:
            await self.emitter.emit_refactoring_recommended(
                file_path=file_path,
                complexity_score=complexity_score,
                reasons=[
                    f"High complexity score: {complexity_score:.2f}",
                    "Exceeds maintainability threshold",
                    "May cause cognitive overload for ADHD developers"
                ],
                recommended_actions=[
                    "Break down into smaller functions",
                    "Extract complex logic into helper methods",
                    "Add documentation for complex sections",
                    "Consider design pattern refactoring"
                ],
                priority="high" if complexity_score >= 0.8 else "medium"
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics"""
        return self.emitter.get_metrics()
