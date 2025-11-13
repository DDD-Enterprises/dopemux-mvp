"""
Dope-Context Integration for ConPort-KG Event System

Hooks into Dope-Context semantic search to emit events when:
- Knowledge gaps detected (low confidence results <0.4)
- Search patterns discovered (similar queries repeat 3+ times)

Events emitted:
- search.completed: All searches (optional, for analytics)
- knowledge.gap.detected: Low confidence search results
- search.pattern.discovered: Repeated similar searches
"""

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class DopeContextEventEmitter:
    """
    Event emitter for Dope-Context semantic search.

    Emits events to DopeconBridge for pattern detection
    and ConPort logging of search patterns and knowledge gaps.

    Features:
    - Non-blocking event emission
    - Confidence-based knowledge gap detection
    - Search pattern discovery tracking
    - ADHD-optimized: Zero latency impact on search
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        confidence_threshold: float = 0.4,
        enable_events: bool = True,
        enable_search_analytics: bool = False
    ):
        """
        Initialize Dope-Context event emitter.

        Args:
            event_bus: EventBus instance for publishing
            workspace_id: Workspace ID for event context
            confidence_threshold: Confidence score to trigger knowledge gap (default: 0.4)
            enable_events: Enable event emission (default: True)
            enable_search_analytics: Enable search.completed events (default: False)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.confidence_threshold = confidence_threshold
        self.enable_events = enable_events
        self.enable_search_analytics = enable_search_analytics

        # Metrics
        self.events_emitted = 0
        self.knowledge_gap_events = 0
        self.pattern_events = 0
        self.search_events = 0
        self.emission_errors = 0

    async def emit_search_completed(
        self,
        query: str,
        results_count: int,
        avg_confidence: float,
        top_results: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Emit event when search completes (optional analytics).

        Args:
            query: Search query text
            results_count: Number of results returned
            avg_confidence: Average confidence score of results
            top_results: Optional top result details

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events or not self.enable_search_analytics:
            return False

        try:
            event = Event(
                type="search.completed",
                data={
                    "query": query,
                    "results_count": results_count,
                    "confidence": avg_confidence,
                    "workspace_id": self.workspace_id,
                    "top_results": top_results or []
                },
                source="dope-context"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.search_events += 1
                logger.debug(f"📤 Emitted search.completed: {query[:50]}...")
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit search event: {e}")

        return False

    async def emit_knowledge_gap(
        self,
        query: str,
        results_count: int,
        avg_confidence: float,
        reasons: Optional[List[str]] = None
    ) -> bool:
        """
        Emit event when knowledge gap detected (low confidence results).

        Args:
            query: Search query that had low confidence
            results_count: Number of results returned
            avg_confidence: Average confidence score (should be <0.4)
            reasons: Optional reasons for low confidence

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        # Only emit if actually low confidence
        if avg_confidence >= self.confidence_threshold:
            return False

        try:
            event = Event(
                type="knowledge.gap.detected",
                data={
                    "query": query,
                    "results_count": results_count,
                    "confidence": avg_confidence,
                    "threshold": self.confidence_threshold,
                    "reasons": reasons or [
                        "Low average confidence score",
                        "May indicate missing documentation",
                        "Could suggest unclear code implementation"
                    ],
                    "workspace_id": self.workspace_id,
                    "recommended_actions": [
                        f"Create documentation for: {query[:50]}",
                        "Add code comments explaining implementation",
                        "Consider refactoring to improve discoverability",
                        "Review indexed content for this topic"
                    ]
                },
                source="dope-context"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.knowledge_gap_events += 1
                logger.info(
                    f"📤 Emitted knowledge.gap.detected: {query[:50]}... "
                    f"(confidence: {avg_confidence:.2f})"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit knowledge gap event: {e}")

        return False

    async def emit_pattern_discovered(
        self,
        queries: List[str],
        frequency: int,
        topic_keywords: str
    ) -> bool:
        """
        Emit event when search pattern discovered (repeated similar queries).

        Args:
            queries: List of similar queries
            frequency: Number of times pattern occurred
            topic_keywords: Keywords identifying the topic

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="search.pattern.discovered",
                data={
                    "queries": queries,
                    "frequency": frequency,
                    "topic_keywords": topic_keywords,
                    "workspace_id": self.workspace_id,
                    "pattern_type": "repeated_search",
                    "suggested_action": "Create documentation or improve code clarity"
                },
                source="dope-context"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.pattern_events += 1
                logger.info(
                    f"📤 Emitted search.pattern.discovered: {topic_keywords} "
                    f"({frequency} similar searches)"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit pattern event: {e}")

        return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event emission metrics.

        Returns:
            Dictionary with emission stats
        """
        return {
            "agent": "dope-context",
            "events_emitted": self.events_emitted,
            "knowledge_gap_events": self.knowledge_gap_events,
            "pattern_events": self.pattern_events,
            "search_events": self.search_events,
            "emission_errors": self.emission_errors,
            "confidence_threshold": self.confidence_threshold,
            "events_enabled": self.enable_events
        }

    def reset_metrics(self):
        """Reset emission metrics"""
        self.events_emitted = 0
        self.knowledge_gap_events = 0
        self.pattern_events = 0
        self.search_events = 0
        self.emission_errors = 0


class DopeContextIntegrationManager:
    """
    Manages Dope-Context integration with ConPort-KG event system.

    Provides:
    - Event emitter initialization
    - Search history tracking for pattern detection
    - Automatic knowledge gap and pattern detection
    - Metrics aggregation
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_knowledge_gap_events: bool = True,
        enable_pattern_events: bool = True,
        confidence_threshold: float = 0.4,
        pattern_threshold: int = 3,
        history_size: int = 100
    ):
        """
        Initialize Dope-Context integration manager.

        Args:
            event_bus: EventBus instance
            workspace_id: Workspace ID
            enable_knowledge_gap_events: Enable knowledge gap events (default: True)
            enable_pattern_events: Enable pattern discovery events (default: True)
            confidence_threshold: Threshold for low confidence (default: 0.4)
            pattern_threshold: Occurrences needed for pattern (default: 3)
            history_size: Number of recent queries to track (default: 100)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_knowledge_gap_events = enable_knowledge_gap_events
        self.enable_pattern_events = enable_pattern_events
        self.pattern_threshold = pattern_threshold

        # Query history for pattern detection (deque for efficient FIFO)
        self.query_history: deque = deque(maxlen=history_size)

        # Create event emitter
        self.emitter = DopeContextEventEmitter(
            event_bus=event_bus,
            workspace_id=workspace_id,
            confidence_threshold=confidence_threshold,
            enable_events=True
        )

        logger.info(
            f"✅ Dope-Context integration initialized "
            f"(knowledge gaps: {enable_knowledge_gap_events}, "
            f"patterns: {enable_pattern_events})"
        )

    async def handle_search_result(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ):
        """
        Handle search result from Dope-Context.

        Analyzes results for knowledge gaps and search patterns.

        Args:
            query: Search query text
            results: Search results with relevance scores
        """
        # Calculate average confidence/relevance
        confidences = [r.get("relevance_score", r.get("score", 0.5)) for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        results_count = len(results)

        # Emit search completed (optional analytics)
        await self.emitter.emit_search_completed(
            query=query,
            results_count=results_count,
            avg_confidence=avg_confidence
        )

        # Check for knowledge gap (low confidence)
        if self.enable_knowledge_gap_events and avg_confidence < self.emitter.confidence_threshold:
            await self.emitter.emit_knowledge_gap(
                query=query,
                results_count=results_count,
                avg_confidence=avg_confidence
            )

        # Track query for pattern detection
        if self.enable_pattern_events:
            self.query_history.append({
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": avg_confidence
            })

            # Check for patterns
            pattern_detected = self._detect_query_pattern(query)

            if pattern_detected:
                await self.emitter.emit_pattern_discovered(
                    queries=pattern_detected["queries"],
                    frequency=pattern_detected["frequency"],
                    topic_keywords=pattern_detected["topic"]
                )

    def _detect_query_pattern(self, current_query: str) -> Optional[Dict[str, Any]]:
        """
        Detect if current query matches a pattern of repeated searches.

        Args:
            current_query: The current search query

        Returns:
            Dictionary with pattern details if detected, None otherwise
        """
        if len(self.query_history) < self.pattern_threshold:
            return None

        # Extract keywords from current query
        stop_words = {"the", "and", "for", "with", "from", "this", "that", "what", "how", "to"}
        current_words = [
            w.lower() for w in current_query.split()
            if len(w) > 3 and w.lower() not in stop_words
        ]

        if not current_words:
            return None

        # Find similar queries in history (share at least 1 significant keyword)
        similar_queries = []

        for entry in self.query_history:
            query = entry["query"]
            words = [
                w.lower() for w in query.split()
                if len(w) > 3 and w.lower() not in stop_words
            ]

            # Check for shared keywords
            shared = set(current_words) & set(words)

            if shared:
                similar_queries.append(entry["query"])

        # Pattern detected if 3+ similar queries
        if len(similar_queries) >= self.pattern_threshold:
            # Use most common keyword as topic
            topic_keywords = current_words[0] if current_words else "unknown"

            return {
                "queries": similar_queries[-5:],  # Last 5 similar queries
                "frequency": len(similar_queries),
                "topic": topic_keywords
            }

        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics"""
        metrics = self.emitter.get_metrics()
        metrics["query_history_size"] = len(self.query_history)
        return metrics

    def clear_history(self):
        """Clear query history"""
        self.query_history.clear()
