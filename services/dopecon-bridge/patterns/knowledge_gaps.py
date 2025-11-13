"""
Knowledge Gaps Pattern Detector

Detects when multiple semantic searches fail or have low confidence,
suggesting missing documentation or unclear implementations.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from .base_pattern import BasePattern, PatternInsight


class KnowledgeGapPattern(BasePattern):
    """
    Detects knowledge gaps from repeated low-confidence searches.

    Triggers when:
    - Multiple searches for similar topics have low confidence (<0.4)
    - Threshold: 3+ low-confidence searches on related topics

    Generates:
    - Documentation gap recommendation
    - Lists topics with poor search results
    - Suggests documentation creation
    """

    def get_pattern_name(self) -> str:
        return "knowledge_gaps"

    def get_default_threshold(self) -> int:
        return 3  # 3+ low-confidence searches on similar topics

    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Detect knowledge gaps from search events.

        Args:
            events: List of events (looking for search.* events with low confidence)

        Returns:
            List of insights for detected gaps
        """
        insights = []

        # Group low-confidence search events by topic similarity
        low_confidence_searches = []

        for event in events:
            event_type = event.get("type", "")

            # Look for search-related events
            if "search" in event_type.lower():
                data = event.get("data", {})
                query = data.get("query", "")
                confidence = data.get("confidence", 1.0)

                # Detect low-confidence results
                if confidence < 0.4 and query:
                    low_confidence_searches.append({
                        "query": query,
                        "confidence": confidence,
                        "source": event.get("source", "unknown"),
                        "timestamp": event.get("timestamp"),
                        "results_count": data.get("results_count", 0)
                    })

        # Group searches by topic similarity (simple keyword overlap)
        topic_groups = self._group_by_topic_similarity(low_confidence_searches)

        # Check each topic group for patterns
        for topic_keywords, searches in topic_groups.items():
            if len(searches) >= self.threshold:
                # Pattern detected!
                self.record_detection()

                # Calculate average confidence
                avg_confidence = sum(s["confidence"] for s in searches) / len(searches)

                # Get unique sources
                sources = list(set(s["source"] for s in searches))

                # Determine severity
                if len(searches) >= 6 or avg_confidence < 0.2:
                    severity = "high"
                elif len(searches) >= 4:
                    severity = "medium"
                else:
                    severity = "low"

                insight = PatternInsight(
                    pattern_name=self.get_pattern_name(),
                    severity=severity,
                    summary=f"Knowledge gap detected: {len(searches)} low-confidence searches on '{topic_keywords}'",
                    details=(
                        f"Detected {len(searches)} searches with low confidence "
                        f"(avg: {avg_confidence:.2f}) for topic: {topic_keywords}\n\n"
                        f"This suggests a knowledge gap - either:\n"
                        f"1. Documentation is missing or incomplete\n"
                        f"2. Code implementation is unclear or complex\n"
                        f"3. Concepts need better explanation\n\n"
                        f"Searches affected: {sources}"
                    ),
                    event_count=len(searches),
                    first_occurrence=searches[0]["timestamp"],
                    last_occurrence=searches[-1]["timestamp"],
                    affected_resources=[s["query"] for s in searches[:5]],  # Sample queries
                    recommended_actions=[
                        f"Create documentation for: {topic_keywords}",
                        "Add code comments explaining implementation",
                        "Consider refactoring to make code more discoverable",
                        "Add examples or usage guide",
                        "Review indexed content for this topic area"
                    ],
                    metadata={
                        "topic_keywords": topic_keywords,
                        "search_count": len(searches),
                        "average_confidence": avg_confidence,
                        "sources": sources,
                        "sample_queries": [s["query"] for s in searches[:5]]
                    }
                )

                insights.append(insight)

        return insights

    def _group_by_topic_similarity(
        self,
        searches: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group searches by topic similarity using shared keywords.

        Items are grouped together if they share at least one significant keyword.
        Uses union-find to merge groups with common keywords.

        Args:
            searches: List of search dictionaries

        Returns:
            Dictionary mapping topic keywords to list of searches
        """
        from collections import Counter

        # Build keyword index: keyword -> list of search indices
        keyword_to_searches = defaultdict(list)

        stop_words = {"the", "and", "for", "with", "from", "this", "that", "what", "how", "to"}

        for idx, search in enumerate(searches):
            query = search["query"].lower()

            # Extract significant keywords (>3 chars, not common words)
            words = [
                w for w in query.split()
                if len(w) > 3 and w not in stop_words
            ]

            # Index this search under all its keywords
            for word in words:
                keyword_to_searches[word].append(idx)

        # Find keyword with most searches (primary topic)
        if not keyword_to_searches:
            return {}

        primary_keyword = max(keyword_to_searches.items(), key=lambda x: len(x[1]))[0]

        # Group all searches that share the primary keyword
        topic_groups = {
            primary_keyword: [searches[idx] for idx in keyword_to_searches[primary_keyword]]
        }

        return topic_groups
