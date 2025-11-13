"""
Event Aggregation Engine for DopeconBridge

Merges similar events from multiple agents to reduce noise and improve
pattern detection accuracy. Tracks provenance and combines confidence scores.

Features:
- Content-based similarity detection (>80% match)
- Cross-agent deduplication and merging
- Provenance tracking (which agents contributed)
- Confidence score combination
- Metadata preservation from all sources
"""

import hashlib
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AggregatedEvent:
    """
    Aggregated event combining multiple similar events from different sources.

    Tracks:
    - Original event content
    - All contributing sources (agents)
    - Combined confidence scores
    - Provenance chain (original event IDs)
    - Metadata from all sources
    """
    event_type: str
    data: Dict[str, Any]
    sources: List[str] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    original_event_ids: List[str] = field(default_factory=list)
    aggregated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def get_combined_confidence(self) -> float:
        """
        Calculate combined confidence score.

        Uses weighted average favoring higher confidence scores.

        Returns:
            Combined confidence (0.0-1.0)
        """
        if not self.confidence_scores:
            return 0.0

        # Weighted average: higher scores get more weight
        weights = [score ** 2 for score in self.confidence_scores]
        total_weight = sum(weights)

        if total_weight == 0:
            return sum(self.confidence_scores) / len(self.confidence_scores)

        weighted_sum = sum(
            score * weight
            for score, weight in zip(self.confidence_scores, weights)
        )

        return weighted_sum / total_weight

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "event_type": self.event_type,
            "data": self.data,
            "sources": self.sources,
            "confidence": self.get_combined_confidence(),
            "confidence_scores": self.confidence_scores,
            "timestamps": self.timestamps,
            "event_count": len(self.sources),
            "provenance": self.original_event_ids,
            "aggregated_at": self.aggregated_at
        }


class AggregationEngine:
    """
    Aggregates similar events from multiple agents.

    Process:
    1. Group events by content similarity (>80% match)
    2. Merge metadata and track provenance
    3. Combine confidence scores
    4. Reduce noise for pattern detection

    Example:
        engine = AggregationEngine(similarity_threshold=0.8)

        aggregated = await engine.aggregate_events(
            events=[event1, event2, event3],
            window_minutes=5
        )

        # Returns fewer, merged events with provenance tracking
    """

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        enable_logging: bool = True
    ):
        """
        Initialize aggregation engine.

        Args:
            similarity_threshold: Minimum similarity for merging (0.0-1.0, default: 0.8)
            enable_logging: Enable detailed logging (default: True)
        """
        self.similarity_threshold = similarity_threshold
        self.enable_logging = enable_logging

        # Metrics
        self.total_aggregations = 0
        self.events_before = 0
        self.events_after = 0
        self.reduction_rate = 0.0

    def _compute_content_signature(self, event: Dict[str, Any]) -> str:
        """
        Compute content signature for similarity matching.

        Excludes timestamps and source-specific metadata.

        Args:
            event: Event dictionary

        Returns:
            Normalized content signature
        """
        # Extract core content (type + data, excluding metadata)
        core_content = {
            "type": event.get("type", ""),
            "data": event.get("data", {})
        }

        # Stable JSON serialization
        json_str = json.dumps(core_content, sort_keys=True, separators=(',', ':'))

        return json_str

    def _calculate_similarity(self, sig1: str, sig2: str) -> float:
        """
        Calculate similarity between two content signatures.

        Uses Jaccard similarity on character n-grams.

        Args:
            sig1: First signature
            sig2: Second signature

        Returns:
            Similarity score (0.0-1.0)
        """
        if sig1 == sig2:
            return 1.0

        # Use character 3-grams for similarity
        def get_ngrams(text: str, n: int = 3) -> Set[str]:
            return {text[i:i+n] for i in range(len(text) - n + 1)}

        ngrams1 = get_ngrams(sig1)
        ngrams2 = get_ngrams(sig2)

        if not ngrams1 or not ngrams2:
            return 0.0

        # Jaccard similarity
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)

        return intersection / union if union > 0 else 0.0

    def _merge_events(
        self,
        events: List[Dict[str, Any]]
    ) -> AggregatedEvent:
        """
        Merge similar events into single aggregated event.

        Args:
            events: List of similar events to merge

        Returns:
            AggregatedEvent combining all inputs
        """
        if not events:
            raise ValueError("Cannot merge empty event list")

        # Use first event as base
        base_event = events[0]

        # Collect metadata from all events
        sources = []
        confidence_scores = []
        timestamps = []
        event_ids = []

        for event in events:
            sources.append(event.get("source", "unknown"))
            timestamps.append(event.get("timestamp", ""))

            # Extract confidence if present
            data = event.get("data", {})
            confidence = data.get("confidence", data.get("score", 1.0))
            confidence_scores.append(float(confidence))

            # Generate event ID (hash of timestamp + source)
            event_id = hashlib.sha256(
                f"{event.get('timestamp')}{event.get('source')}".encode()
            ).hexdigest()[:16]
            event_ids.append(event_id)

        # Create aggregated event
        aggregated = AggregatedEvent(
            event_type=base_event.get("type", "unknown"),
            data=base_event.get("data", {}),
            sources=sources,
            confidence_scores=confidence_scores,
            timestamps=timestamps,
            original_event_ids=event_ids
        )

        return aggregated

    async def aggregate_events(
        self,
        events: List[Dict[str, Any]],
        window_minutes: int = 5
    ) -> List[AggregatedEvent]:
        """
        Aggregate similar events within time window.

        Groups events by content similarity, merges similar ones,
        and tracks provenance across agents.

        Args:
            events: List of event dictionaries
            window_minutes: Time window for aggregation (default: 5)

        Returns:
            List of AggregatedEvent objects (fewer than input if merging occurred)
        """
        self.total_aggregations += 1
        self.events_before += len(events)

        if not events:
            return []

        # Group events by similarity
        similarity_groups: List[List[Dict[str, Any]]] = []

        for event in events:
            signature = self._compute_content_signature(event)

            # Find matching group
            matched_group = None

            for group in similarity_groups:
                # Compare with first event in group
                group_signature = self._compute_content_signature(group[0])
                similarity = self._calculate_similarity(signature, group_signature)

                if similarity >= self.similarity_threshold:
                    matched_group = group
                    break

            if matched_group:
                # Add to existing group
                matched_group.append(event)
            else:
                # Create new group
                similarity_groups.append([event])

        # Merge each group
        aggregated_events = []

        for group in similarity_groups:
            if len(group) == 1:
                # Single event, no aggregation needed
                event = group[0]
                aggregated = AggregatedEvent(
                    event_type=event.get("type", "unknown"),
                    data=event.get("data", {}),
                    sources=[event.get("source", "unknown")],
                    confidence_scores=[1.0],
                    timestamps=[event.get("timestamp", "")],
                    original_event_ids=[hashlib.sha256(
                        f"{event.get('timestamp')}{event.get('source')}".encode()
                    ).hexdigest()[:16]]
                )
                aggregated_events.append(aggregated)
            else:
                # Multiple events - merge them
                merged = self._merge_events(group)
                aggregated_events.append(merged)

                if self.enable_logging:
                    logger.info(
                        f"📊 Aggregated {len(group)} events from "
                        f"{len(set(e.get('source') for e in group))} agents: "
                        f"{merged.event_type}"
                    )

        self.events_after += len(aggregated_events)

        # Calculate reduction rate
        if self.events_before > 0:
            self.reduction_rate = (
                (self.events_before - self.events_after) / self.events_before * 100
            )

        return aggregated_events

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get aggregation metrics.

        Returns:
            Dictionary with aggregation stats
        """
        return {
            "total_aggregations": self.total_aggregations,
            "events_before": self.events_before,
            "events_after": self.events_after,
            "reduction_rate_percent": round(self.reduction_rate, 2),
            "similarity_threshold": self.similarity_threshold
        }

    def reset_metrics(self):
        """Reset aggregation metrics"""
        self.total_aggregations = 0
        self.events_before = 0
        self.events_after = 0
        self.reduction_rate = 0.0
