"""
Zen Integration for ConPort-KG Event System

Hooks into Zen MCP multi-model reasoning tools to emit events when:
- Consensus decisions reached
- Architecture choices made
- Complex analysis completed

Events emitted:
- decision.consensus.reached: Multi-model consensus result
- architecture.choice.made: Architectural decision with rationale
- analysis.completed: thinkdeep/debug/codereview completion
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class ZenEventEmitter:
    """
    Event emitter for Zen multi-model reasoning.

    Emits events to DopeconBridge for tracking important
    decisions, consensus results, and architectural choices.

    Features:
    - Non-blocking event emission
    - Consensus tracking across models
    - Architecture decision logging
    - ADHD-optimized: Zero latency impact on Zen operations
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_events: bool = True,
        track_all_analyses: bool = False
    ):
        """
        Initialize Zen event emitter.

        Args:
            event_bus: EventBus instance for publishing
            workspace_id: Workspace ID for event context
            enable_events: Enable event emission (default: True)
            track_all_analyses: Track all analyses, not just consensus (default: False)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_events = enable_events
        self.track_all_analyses = track_all_analyses

        # Metrics
        self.events_emitted = 0
        self.consensus_events = 0
        self.architecture_events = 0
        self.analysis_events = 0
        self.emission_errors = 0

    async def emit_consensus_reached(
        self,
        decision_summary: str,
        models_consulted: List[str],
        final_recommendation: str,
        confidence: float,
        stances: Optional[Dict[str, str]] = None,
        alternatives_considered: Optional[List[str]] = None
    ) -> bool:
        """
        Emit event when multi-model consensus is reached.

        Args:
            decision_summary: Summary of decision being made
            models_consulted: List of models that contributed
            final_recommendation: Final consensus recommendation
            confidence: Consensus confidence (0.0-1.0)
            stances: Optional model stances (for/against/neutral)
            alternatives_considered: Optional list of alternatives

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="decision.consensus.reached",
                data={
                    "decision_summary": decision_summary,
                    "models_consulted": models_consulted,
                    "model_count": len(models_consulted),
                    "final_recommendation": final_recommendation,
                    "confidence": confidence,
                    "stances": stances or {},
                    "alternatives_considered": alternatives_considered or [],
                    "workspace_id": self.workspace_id,
                    "decision_type": "consensus"
                },
                source="zen"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.consensus_events += 1
                logger.info(
                    f"📤 Emitted decision.consensus.reached: {decision_summary[:50]}... "
                    f"({len(models_consulted)} models, confidence: {confidence:.2f})"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit consensus event: {e}")

        return False

    async def emit_architecture_choice(
        self,
        choice_summary: str,
        rationale: str,
        alternatives: List[str],
        trade_offs: Dict[str, Any],
        priority: str = "medium"
    ) -> bool:
        """
        Emit event when architectural choice is made.

        Args:
            choice_summary: Summary of architectural choice
            rationale: Detailed rationale for choice
            alternatives: List of alternatives considered
            trade_offs: Dictionary of trade-offs analyzed
            priority: Priority level (low/medium/high/critical)

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="architecture.choice.made",
                data={
                    "choice_summary": choice_summary,
                    "rationale": rationale,
                    "alternatives": alternatives,
                    "trade_offs": trade_offs,
                    "priority": priority,
                    "workspace_id": self.workspace_id,
                    "recommended_actions": [
                        "Document decision in ADR (Architecture Decision Record)",
                        "Update technical documentation",
                        "Communicate to team",
                        "Plan implementation timeline"
                    ]
                },
                source="zen"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.architecture_events += 1
                logger.info(
                    f"📤 Emitted architecture.choice.made: {choice_summary[:50]}... "
                    f"({priority} priority)"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit architecture event: {e}")

        return False

    async def emit_analysis_completed(
        self,
        analysis_type: str,
        summary: str,
        confidence: float,
        findings: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None
    ) -> bool:
        """
        Emit event when complex analysis completes.

        Args:
            analysis_type: Type of analysis (thinkdeep, debug, codereview, etc.)
            summary: Summary of analysis results
            confidence: Analysis confidence level
            findings: Optional key findings
            recommendations: Optional recommendations

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events or not self.track_all_analyses:
            return False

        try:
            event = Event(
                type="analysis.completed",
                data={
                    "analysis_type": analysis_type,
                    "summary": summary,
                    "confidence": confidence,
                    "findings": findings or [],
                    "recommendations": recommendations or [],
                    "workspace_id": self.workspace_id
                },
                source="zen"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.analysis_events += 1
                logger.debug(f"📤 Emitted analysis.completed: {analysis_type}")
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit analysis event: {e}")

        return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event emission metrics.

        Returns:
            Dictionary with emission stats
        """
        return {
            "agent": "zen",
            "events_emitted": self.events_emitted,
            "consensus_events": self.consensus_events,
            "architecture_events": self.architecture_events,
            "analysis_events": self.analysis_events,
            "emission_errors": self.emission_errors,
            "events_enabled": self.enable_events,
            "track_all_analyses": self.track_all_analyses
        }

    def reset_metrics(self):
        """Reset emission metrics"""
        self.events_emitted = 0
        self.consensus_events = 0
        self.architecture_events = 0
        self.analysis_events = 0
        self.emission_errors = 0


class ZenIntegrationManager:
    """
    Manages Zen integration with ConPort-KG event system.

    Provides:
    - Event emitter initialization
    - Decision tracking and auto-logging
    - Consensus result handling
    - Metrics aggregation
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_consensus_events: bool = True,
        enable_architecture_events: bool = True,
        track_all_analyses: bool = False
    ):
        """
        Initialize Zen integration manager.

        Args:
            event_bus: EventBus instance
            workspace_id: Workspace ID
            enable_consensus_events: Enable consensus events (default: True)
            enable_architecture_events: Enable architecture events (default: True)
            track_all_analyses: Track all Zen analyses (default: False)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_consensus_events = enable_consensus_events
        self.enable_architecture_events = enable_architecture_events

        # Create event emitter
        self.emitter = ZenEventEmitter(
            event_bus=event_bus,
            workspace_id=workspace_id,
            enable_events=True,
            track_all_analyses=track_all_analyses
        )

        logger.info(
            f"✅ Zen integration initialized "
            f"(consensus: {enable_consensus_events}, "
            f"architecture: {enable_architecture_events})"
        )

    async def handle_consensus_result(
        self,
        decision_summary: str,
        models_consulted: List[str],
        final_recommendation: str,
        confidence: float,
        stances: Optional[Dict[str, str]] = None,
        alternatives: Optional[List[str]] = None
    ):
        """
        Handle consensus result from Zen.

        Args:
            decision_summary: Summary of decision
            models_consulted: Models that participated
            final_recommendation: Consensus recommendation
            confidence: Consensus confidence
            stances: Model stances (for/against/neutral)
            alternatives: Alternatives considered
        """
        if not self.enable_consensus_events:
            return

        await self.emitter.emit_consensus_reached(
            decision_summary=decision_summary,
            models_consulted=models_consulted,
            final_recommendation=final_recommendation,
            confidence=confidence,
            stances=stances,
            alternatives_considered=alternatives
        )

    async def handle_architecture_decision(
        self,
        choice: str,
        rationale: str,
        alternatives: List[str],
        trade_offs: Dict[str, Any],
        priority: str = "medium"
    ):
        """
        Handle architecture decision from Zen.

        Args:
            choice: Architectural choice made
            rationale: Rationale for choice
            alternatives: Alternatives considered
            trade_offs: Trade-offs analyzed
            priority: Decision priority
        """
        if not self.enable_architecture_events:
            return

        await self.emitter.emit_architecture_choice(
            choice_summary=choice,
            rationale=rationale,
            alternatives=alternatives,
            trade_offs=trade_offs,
            priority=priority
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics"""
        return self.emitter.get_metrics()
