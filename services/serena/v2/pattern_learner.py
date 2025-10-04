"""
F5: Pattern Learning Foundation

Learns from user behavior to improve untracked work detection accuracy.
Tracks patterns like:
- File extensions frequently worked on
- Common directory patterns
- Branch naming preferences
- Work session characteristics

Architecture: Hybrid (ConPort storage + in-memory cache)
Performance Target: <1s response time (ADHD-optimized)
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import json
import math

logger = logging.getLogger(__name__)


class PatternCache:
    """
    In-memory cache for frequently accessed patterns

    ADHD Optimization: Sub-100ms cache hits for instant feedback
    """

    def __init__(self, max_size: int = 1000, ttl_minutes: int = 60):
        """
        Initialize pattern cache

        Args:
            max_size: Maximum cached patterns (default 1000)
            ttl_minutes: Time-to-live for cache entries (default 60 min)
        """
        self.cache: Dict[str, Dict] = {}
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.timestamps: Dict[str, datetime] = {}
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)

    def get(self, pattern_key: str) -> Optional[Dict]:
        """
        Retrieve pattern from cache

        Returns None if not found or expired
        """
        if pattern_key not in self.cache:
            return None

        # Check TTL
        if datetime.now() - self.timestamps[pattern_key] > self.ttl:
            self._evict(pattern_key)
            return None

        # Update access count
        self.access_counts[pattern_key] += 1
        return self.cache[pattern_key]

    def put(self, pattern_key: str, pattern_data: Dict) -> None:
        """
        Store pattern in cache

        Evicts least-recently-used if at capacity
        """
        # Evict if at capacity
        if len(self.cache) >= self.max_size and pattern_key not in self.cache:
            self._evict_lru()

        self.cache[pattern_key] = pattern_data
        self.timestamps[pattern_key] = datetime.now()
        # Initialize access count to 0 (only get() increments)
        self.access_counts[pattern_key] = 0

    def invalidate(self, pattern_key: str) -> None:
        """Remove pattern from cache"""
        self._evict(pattern_key)

    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
        self.access_counts.clear()
        self.timestamps.clear()

    def _evict(self, pattern_key: str) -> None:
        """Remove specific pattern"""
        if pattern_key in self.cache:
            del self.cache[pattern_key]
            del self.access_counts[pattern_key]
            del self.timestamps[pattern_key]

    def _evict_lru(self) -> None:
        """Evict least-recently-used pattern"""
        if not self.cache:
            return

        # Find pattern with lowest access count
        lru_key = min(self.access_counts.items(), key=lambda x: x[1])[0]
        self._evict(lru_key)

    def stats(self) -> Dict:
        """Cache statistics for monitoring"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size,
            "total_accesses": sum(self.access_counts.values()),
            "avg_accesses_per_pattern": (
                sum(self.access_counts.values()) / len(self.cache)
                if self.cache else 0
            )
        }


class PatternLearner:
    """
    F5: Pattern Learning Engine

    Learns from user behavior to improve detection accuracy.
    Uses frequency-based probability with time decay.
    """

    def __init__(self, workspace_id: str, conport_client=None):
        """
        Initialize pattern learner

        Args:
            workspace_id: Workspace ID for ConPort storage
            conport_client: Optional ConPort MCP client
        """
        self.workspace_id = workspace_id
        self.conport_client = conport_client
        self.cache = PatternCache()

        # Time decay configuration (from planning)
        self.decay_half_life_days = 30  # Pattern strength halves every 30 days

    async def extract_patterns(self, git_detection: Dict) -> List[Dict]:
        """
        Extract observable patterns from git detection

        Pattern types:
        1. File extension patterns (e.g., ".py", ".ts")
        2. Directory patterns (e.g., "services/auth")
        3. Branch prefix patterns (e.g., "feature/", "fix/")

        Args:
            git_detection: Detection result from GitWorkDetector

        Returns:
            List of pattern dictionaries
        """
        patterns = []
        files = git_detection.get("files", [])
        branch = git_detection.get("branch", "")

        # Extract file extension patterns
        extensions = defaultdict(int)
        for filepath in files:
            ext = Path(filepath).suffix
            if ext:  # Ignore files without extensions
                extensions[ext] += 1

        for ext, count in extensions.items():
            patterns.append({
                "type": "file_extension",
                "value": ext,
                "frequency": count,
                "context": {
                    "branch": branch,
                    "total_files": len(files)
                }
            })

        # Extract directory patterns
        directories = defaultdict(int)
        for filepath in files:
            parent = str(Path(filepath).parent)
            if parent and parent != ".":
                directories[parent] += 1

        for directory, count in directories.items():
            patterns.append({
                "type": "directory",
                "value": directory,
                "frequency": count,
                "context": {
                    "branch": branch,
                    "total_files": len(files)
                }
            })

        # Extract branch prefix pattern
        if branch and "/" in branch:
            prefix = branch.split("/")[0]
            patterns.append({
                "type": "branch_prefix",
                "value": prefix,
                "frequency": 1,  # Single occurrence per detection
                "context": {
                    "full_branch": branch,
                    "total_files": len(files)
                }
            })

        return patterns

    async def record_pattern_event(
        self,
        event_type: str,
        pattern_data: Dict,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Record pattern event in ConPort for learning

        Event types:
        - pattern_observed: Pattern detected in uncommitted work
        - pattern_confirmed: User acted on suggestion (tracked task)
        - pattern_ignored: User dismissed suggestion

        Args:
            event_type: Type of pattern event
            pattern_data: Pattern information
            metadata: Optional additional context
        """
        if not self.conport_client:
            logger.warning("ConPort client not available, pattern event not recorded")
            return

        try:
            event = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "pattern": pattern_data,
                "metadata": metadata or {}
            }

            # Store in ConPort custom_data with category "pattern_events"
            event_key = f"{event_type}_{datetime.now().timestamp()}"

            # Note: This will be called via MCP in actual integration
            # For now, structured for future ConPort integration
            logger.info(f"Pattern event recorded: {event_type} - {pattern_data.get('type')}")

        except Exception as e:
            logger.error(f"Failed to record pattern event: {e}", exc_info=True)

    async def calculate_pattern_probability(
        self,
        pattern_type: str,
        pattern_value: str,
        lookback_days: int = 90
    ) -> float:
        """
        Calculate probability of pattern occurrence with time decay

        Formula: P(pattern) = Σ(occurrences * decay_factor) / total_events
        Decay: 0.5^(days_ago / half_life)

        Args:
            pattern_type: Type of pattern (file_extension, directory, branch_prefix)
            pattern_value: Pattern value (e.g., ".py", "services/auth")
            lookback_days: Days to look back (default 90)

        Returns:
            Probability score 0.0-1.0
        """
        # Check cache first
        cache_key = f"{pattern_type}:{pattern_value}:{lookback_days}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached["probability"]

        # Query ConPort for pattern events
        # (In full implementation, this queries pattern_events category)
        # For now, return placeholder logic

        # Calculate time-decayed frequency
        weighted_count = 0.0
        total_count = 0

        # Placeholder: In real implementation, iterate over pattern_events
        # For each event:
        #   days_ago = (now - event_timestamp).days
        #   decay_factor = 0.5 ** (days_ago / self.decay_half_life_days)
        #   weighted_count += decay_factor
        #   total_count += 1

        # Calculate probability
        probability = weighted_count / total_count if total_count > 0 else 0.0

        # Cache result
        self.cache.put(cache_key, {
            "probability": probability,
            "sample_size": total_count,
            "calculated_at": datetime.now().isoformat()
        })

        return probability

    async def get_top_patterns(
        self,
        pattern_type: str,
        limit: int = 10,
        min_probability: float = 0.1
    ) -> List[Dict]:
        """
        Get most frequent patterns by type

        ADHD Optimization: Limit to top 10 to prevent overwhelm

        Args:
            pattern_type: Type of pattern to retrieve
            limit: Maximum patterns to return (default 10, max 10 for ADHD)
            min_probability: Minimum probability threshold (default 0.1)

        Returns:
            List of patterns sorted by probability (descending)
        """
        # Enforce ADHD limit
        limit = min(limit, 10)

        # Query ConPort for patterns
        # (In full implementation, queries pattern_learning category)
        # For now, return empty list as placeholder

        patterns = []

        # Filter by probability threshold
        patterns = [p for p in patterns if p.get("probability", 0) >= min_probability]

        # Sort by probability descending
        patterns.sort(key=lambda p: p.get("probability", 0), reverse=True)

        # Limit results
        return patterns[:limit]

    async def suggest_based_on_patterns(
        self,
        current_detection: Dict,
        confidence_boost: float = 0.15
    ) -> Dict:
        """
        Boost detection confidence based on learned patterns

        If current work matches learned patterns, increase confidence.

        Args:
            current_detection: Current git detection result
            confidence_boost: Maximum confidence boost (default 0.15)

        Returns:
            {
                "boosted_confidence": float,
                "boost_applied": float,
                "matching_patterns": List[Dict],
                "explanation": str
            }
        """
        # Extract patterns from current detection
        current_patterns = await self.extract_patterns(current_detection)

        # Find matching learned patterns
        matching_patterns = []
        total_boost = 0.0

        for pattern in current_patterns:
            probability = await self.calculate_pattern_probability(
                pattern["type"],
                pattern["value"]
            )

            if probability > 0.5:  # Pattern seen frequently
                matching_patterns.append({
                    "pattern": pattern,
                    "probability": probability
                })

                # Apply weighted boost
                total_boost += probability * confidence_boost

        # Cap total boost at confidence_boost
        total_boost = min(total_boost, confidence_boost)

        # Generate explanation
        if matching_patterns:
            top_match = max(matching_patterns, key=lambda p: p["probability"])
            explanation = (
                f"Pattern '{top_match['pattern']['value']}' seen frequently "
                f"(P={top_match['probability']:.2f}). Confidence boosted by {total_boost:.2f}."
            )
        else:
            explanation = "No matching patterns found. No confidence boost applied."

        return {
            "boosted_confidence": total_boost,
            "boost_applied": total_boost,
            "matching_patterns": matching_patterns,
            "explanation": explanation
        }

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        return self.cache.stats()
