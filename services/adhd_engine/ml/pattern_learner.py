"""
ADHD Pattern Learning Module

Extracts and persists user-specific ADHD patterns for predictive accommodations.
Inspired by Serena F5 pattern learning but focused on cognitive state patterns.

IP-005 Days 11-12: Machine Learning Component 1/2
"""

import asyncio
import json
import logging
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import math

from models import EnergyLevel, AttentionState
from bridge_integration import ConPortBridgeAdapter

logger = logging.getLogger(__name__)


@dataclass
class EnergyPattern:
    """
    Energy level pattern for specific time/day.

    Captures when user typically experiences specific energy levels,
    enabling predictive energy assessment.
    """
    time_of_day: int        # Hour (0-23)
    day_of_week: int        # (0=Monday, 6=Sunday)
    energy_level: str       # EnergyLevel enum value
    confidence: float       # 0.0-1.0 (based on sample count and consistency)
    sample_count: int       # Number of observations
    last_observed: str      # ISO timestamp of most recent observation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnergyPattern':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class AttentionPattern:
    """
    Attention state pattern based on session context.

    Learns user's typical attention cycles: warmup time, peak duration,
    optimal session length for maximum productivity.
    """
    warmup_minutes: int           # Time to reach peak focus (typically 5-25 min)
    peak_duration_minutes: int    # How long peak focus lasts (typically 20-90 min)
    optimal_session_length: int   # Best total session duration
    confidence: float             # 0.0-1.0
    sample_count: int             # Number of sessions analyzed
    session_type: str            # "morning", "afternoon", "evening"
    last_observed: str           # ISO timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttentionPattern':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class BreakPattern:
    """
    Break effectiveness pattern.

    Learns optimal break timing and duration for individual user based on
    measured productivity outcomes.
    """
    frequency_minutes: int     # Optimal time between breaks (typically 25-90 min)
    duration_minutes: int      # Optimal break duration (typically 5-15 min)
    effectiveness_score: float # 0.0-1.0 (productivity improvement from breaks)
    confidence: float          # 0.0-1.0
    sample_count: int          # Number of break cycles analyzed
    break_type: str           # "short" (5min), "medium" (10-15min), "long" (20-30min)
    last_observed: str        # ISO timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BreakPattern':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


class ADHDPatternLearner:
    """
    ADHD pattern learning engine.

    Extracts patterns from historical activity data and persists to ConPort
    for cross-session pattern learning and predictive capabilities.

    Features:
    - Energy pattern extraction (time-of-day, day-of-week patterns)
    - Attention pattern extraction (session duration, focus cycles)
    - Break effectiveness analysis (optimal timing from outcomes)
    - Time-decay probability (30-day half-life, like Serena F5)
    - ConPort persistence (custom_data category: adhd_patterns)

    Pattern Convergence: Typically 5-7 days of usage for confidence >0.7
    """

    def __init__(self, workspace_id: str):
        """
        Initialize pattern learner.

        Args:
            workspace_id: Workspace path for ConPort integration
        """
        self.workspace_id = workspace_id
        self.conport = ConPortBridgeAdapter(workspace_id)

        # Learning configuration
        self.min_samples_for_confidence = 5   # Minimum observations for reliable pattern
        self.time_decay_half_life_days = 30.0  # 30-day half-life (proven in Serena F5)
        self.confidence_base_multiplier = 0.1  # Base confidence per sample

        # In-memory pattern cache (loaded from ConPort)
        self.energy_patterns: Dict[str, List[EnergyPattern]] = {}
        self.attention_patterns: Dict[str, List[AttentionPattern]] = {}
        self.break_patterns: Dict[str, List[BreakPattern]] = {}

    async def extract_energy_patterns(
        self,
        user_id: str,
        activity_history: List[Dict[str, Any]]
    ) -> List[EnergyPattern]:
        """
        Extract energy level patterns from activity history.

        Groups observations by (hour, day_of_week) and calculates:
        - Most common energy level for each time slot
        - Confidence based on sample count and consistency
        - Time-decay weighting (recent observations count more)

        Args:
            user_id: User identifier
            activity_history: List of activity events with timestamps and energy levels

        Returns:
            List of EnergyPattern objects with confidence scores
        """
        if not activity_history:
            logger.warning(f"No activity history for user {user_id}")
            return []

        # Group by (hour, day_of_week)
        grouped: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}

        for activity in activity_history:
            if 'energy_level' not in activity or 'timestamp' not in activity:
                continue

            timestamp = datetime.fromisoformat(activity['timestamp'])
            hour = timestamp.hour
            day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday

            key = (hour, day_of_week)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(activity)

        # Extract patterns from groups
        patterns = []
        current_time = datetime.now(timezone.utc)

        for (hour, day_of_week), activities in grouped.items():
            if len(activities) < 2:  # Need at least 2 samples
                continue

            # Apply time-decay weighting
            weighted_energy_levels: Dict[str, float] = {}

            for activity in activities:
                timestamp = datetime.fromisoformat(activity['timestamp'])
                energy_level = activity['energy_level']

                # Calculate time decay weight
                days_old = (current_time - timestamp).days
                weight = self._calculate_time_decay_weight(days_old)

                if energy_level not in weighted_energy_levels:
                    weighted_energy_levels[energy_level] = 0.0
                weighted_energy_levels[energy_level] += weight

            # Most common energy level (weighted)
            most_common_energy = max(weighted_energy_levels, key=weighted_energy_levels.get)

            # Calculate confidence
            total_weight = sum(weighted_energy_levels.values())
            dominant_weight = weighted_energy_levels[most_common_energy]
            consistency_ratio = dominant_weight / total_weight if total_weight > 0 else 0.0

            sample_count = len(activities)
            confidence = self._calculate_confidence(sample_count, consistency_ratio)

            # Get most recent observation
            last_observed = max(activities, key=lambda x: x['timestamp'])['timestamp']

            pattern = EnergyPattern(
                time_of_day=hour,
                day_of_week=day_of_week,
                energy_level=most_common_energy,
                confidence=confidence,
                sample_count=sample_count,
                last_observed=last_observed
            )
            patterns.append(pattern)

        logger.info(f"Extracted {len(patterns)} energy patterns for user {user_id}")
        return patterns

    async def extract_attention_patterns(
        self,
        user_id: str,
        session_history: List[Dict[str, Any]]
    ) -> List[AttentionPattern]:
        """
        Extract attention state patterns from session history.

        Analyzes session durations, attention transitions, and productivity
        to determine optimal session characteristics for user.

        Args:
            user_id: User identifier
            session_history: List of work sessions with attention state transitions

        Returns:
            List of AttentionPattern objects by session type (morning/afternoon/evening)
        """
        if not session_history:
            logger.warning(f"No session history for user {user_id}")
            return []

        # Group by session type (time of day)
        grouped: Dict[str, List[Dict[str, Any]]] = {"morning": [], "afternoon": [], "evening": []}

        for session in session_history:
            if 'start_time' not in session:
                continue

            start_time = datetime.fromisoformat(session['start_time'])
            hour = start_time.hour

            # Categorize session
            if 6 <= hour < 12:
                session_type = "morning"
            elif 12 <= hour < 18:
                session_type = "afternoon"
            else:
                session_type = "evening"

            grouped[session_type].append(session)

        # Extract patterns for each session type
        patterns = []
        current_time = datetime.now(timezone.utc)

        for session_type, sessions in grouped.items():
            if len(sessions) < 3:  # Need at least 3 sessions for pattern
                continue

            # Calculate weighted averages with time decay
            warmup_times = []
            peak_durations = []
            total_durations = []
            weights = []

            for session in sessions:
                warmup_time = session.get('warmup_minutes', 15)  # Default 15min
                peak_duration = session.get('peak_duration_minutes', 25)
                total_duration = session.get('total_minutes', 50)

                # Time decay weight
                timestamp = datetime.fromisoformat(session['start_time'])
                days_old = (current_time - timestamp).days
                weight = self._calculate_time_decay_weight(days_old)

                warmup_times.append(warmup_time * weight)
                peak_durations.append(peak_duration * weight)
                total_durations.append(total_duration * weight)
                weights.append(weight)

            # Weighted averages
            total_weight = sum(weights)
            avg_warmup = int(sum(warmup_times) / total_weight) if total_weight > 0 else 15
            avg_peak = int(sum(peak_durations) / total_weight) if total_weight > 0 else 25
            avg_total = int(sum(total_durations) / total_weight) if total_weight > 0 else 50

            # Calculate confidence (consistency of session durations)
            duration_std = statistics.stdev([s.get('total_minutes', 50) for s in sessions]) if len(sessions) > 1 else 0
            consistency_ratio = max(0.0, 1.0 - (duration_std / 60.0))  # Normalize by 60min
            confidence = self._calculate_confidence(len(sessions), consistency_ratio)

            # Most recent session
            last_observed = max(sessions, key=lambda x: x['start_time'])['start_time']

            pattern = AttentionPattern(
                warmup_minutes=avg_warmup,
                peak_duration_minutes=avg_peak,
                optimal_session_length=avg_total,
                confidence=confidence,
                sample_count=len(sessions),
                session_type=session_type,
                last_observed=last_observed
            )
            patterns.append(pattern)

        logger.info(f"Extracted {len(patterns)} attention patterns for user {user_id}")
        return patterns

    async def extract_break_patterns(
        self,
        user_id: str,
        break_history: List[Dict[str, Any]]
    ) -> List[BreakPattern]:
        """
        Extract break effectiveness patterns from break history.

        Analyzes break frequency, duration, and productivity outcomes to
        determine optimal break strategy for user.

        Args:
            user_id: User identifier
            break_history: List of break events with effectiveness metrics

        Returns:
            List of BreakPattern objects by break type (short/medium/long)
        """
        if not break_history:
            logger.warning(f"No break history for user {user_id}")
            return []

        # Group by break type (duration)
        grouped: Dict[str, List[Dict[str, Any]]] = {"short": [], "medium": [], "long": []}

        for break_event in break_history:
            duration = break_event.get('duration_minutes', 10)

            # Categorize break
            if duration <= 7:
                break_type = "short"
            elif duration <= 15:
                break_type = "medium"
            else:
                break_type = "long"

            grouped[break_type].append(break_event)

        # Extract patterns for each break type
        patterns = []
        current_time = datetime.now(timezone.utc)

        for break_type, breaks in grouped.items():
            if len(breaks) < 3:  # Need at least 3 breaks for pattern
                continue

            # Calculate weighted averages
            frequencies = []
            durations = []
            effectiveness_scores = []
            weights = []

            for break_event in breaks:
                frequency = break_event.get('frequency_minutes', 45)  # Time since last break
                duration = break_event.get('duration_minutes', 10)
                effectiveness = break_event.get('effectiveness_score', 0.5)  # 0.0-1.0

                # Time decay weight
                timestamp = datetime.fromisoformat(break_event['timestamp'])
                days_old = (current_time - timestamp).days
                weight = self._calculate_time_decay_weight(days_old)

                frequencies.append(frequency * weight)
                durations.append(duration * weight)
                effectiveness_scores.append(effectiveness * weight)
                weights.append(weight)

            # Weighted averages
            total_weight = sum(weights)
            avg_frequency = int(sum(frequencies) / total_weight) if total_weight > 0 else 45
            avg_duration = int(sum(durations) / total_weight) if total_weight > 0 else 10
            avg_effectiveness = sum(effectiveness_scores) / total_weight if total_weight > 0 else 0.5

            # Confidence from sample count and effectiveness consistency
            effectiveness_std = statistics.stdev([b.get('effectiveness_score', 0.5) for b in breaks]) if len(breaks) > 1 else 0
            consistency_ratio = max(0.0, 1.0 - effectiveness_std)
            confidence = self._calculate_confidence(len(breaks), consistency_ratio)

            # Most recent break
            last_observed = max(breaks, key=lambda x: x['timestamp'])['timestamp']

            pattern = BreakPattern(
                frequency_minutes=avg_frequency,
                duration_minutes=avg_duration,
                effectiveness_score=avg_effectiveness,
                confidence=confidence,
                sample_count=len(breaks),
                break_type=break_type,
                last_observed=last_observed
            )
            patterns.append(pattern)

        logger.info(f"Extracted {len(patterns)} break patterns for user {user_id}")
        return patterns

    def _calculate_time_decay_weight(self, days_old: float) -> float:
        """
        Calculate time-decay weight for pattern observation.

        Uses exponential decay with 30-day half-life (proven in Serena F5).
        Recent observations weighted higher than old observations.

        Args:
            days_old: Age of observation in days

        Returns:
            Weight (0.0-1.0), where 1.0 = today, 0.5 = 30 days ago
        """
        # Exponential decay: weight = 0.5 ^ (days / half_life)
        weight = math.pow(0.5, days_old / self.time_decay_half_life_days)
        return weight

    def _calculate_confidence(self, sample_count: int, consistency_ratio: float) -> float:
        """
        Calculate confidence score for pattern.

        Combines sample count (more samples = higher confidence) with
        consistency ratio (more consistent = higher confidence).

        Args:
            sample_count: Number of observations
            consistency_ratio: Consistency of observations (0.0-1.0)

        Returns:
            Confidence score (0.0-1.0)
        """
        # Sample count factor (logarithmic growth, saturates at ~20 samples)
        sample_factor = min(1.0, sample_count / 20.0)

        # Combined confidence
        confidence = (sample_factor * 0.5) + (consistency_ratio * 0.5)
        return min(1.0, max(0.0, confidence))

    async def persist_patterns_to_conport(
        self,
        user_id: str,
        energy_patterns: Optional[List[EnergyPattern]] = None,
        attention_patterns: Optional[List[AttentionPattern]] = None,
        break_patterns: Optional[List[BreakPattern]] = None
    ) -> bool:
        """
        Persist learned patterns to ConPort custom_data.

        Storage schema:
        - Category: "adhd_patterns"
        - Keys: "{user_id}_energy", "{user_id}_attention", "{user_id}_breaks"
        - Format: JSON array of pattern dictionaries

        Args:
            user_id: User identifier
            energy_patterns: Energy patterns to save
            attention_patterns: Attention patterns to save
            break_patterns: Break patterns to save

        Returns:
            True if all patterns saved successfully
        """
        try:
            success = True

            # Save energy patterns
            if energy_patterns is not None:
                data = [p.to_dict() for p in energy_patterns]
                result = await self.conport.write_custom_data(
                    category="adhd_patterns",
                    key=f"{user_id}_energy",
                    value=data
                )
                if not result:
                    logger.error(f"Failed to save energy patterns for {user_id}")
                    success = False
                else:
                    logger.info(f"Saved {len(energy_patterns)} energy patterns for {user_id}")

            # Save attention patterns
            if attention_patterns is not None:
                data = [p.to_dict() for p in attention_patterns]
                result = await self.conport.write_custom_data(
                    category="adhd_patterns",
                    key=f"{user_id}_attention",
                    value=data
                )
                if not result:
                    logger.error(f"Failed to save attention patterns for {user_id}")
                    success = False
                else:
                    logger.info(f"Saved {len(attention_patterns)} attention patterns for {user_id}")

            # Save break patterns
            if break_patterns is not None:
                data = [p.to_dict() for p in break_patterns]
                result = await self.conport.write_custom_data(
                    category="adhd_patterns",
                    key=f"{user_id}_breaks",
                    value=data
                )
                if not result:
                    logger.error(f"Failed to save break patterns for {user_id}")
                    success = False
                else:
                    logger.info(f"Saved {len(break_patterns)} break patterns for {user_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to persist patterns: {e}")
            return False

    async def load_patterns_from_conport(
        self,
        user_id: str
    ) -> Dict[str, List]:
        """
        Load learned patterns from ConPort custom_data.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with keys: "energy", "attention", "breaks"
            Each containing list of pattern objects
        """
        try:
            result = {
                "energy": [],
                "attention": [],
                "breaks": []
            }

            # Load energy patterns
            energy_data = await self.conport.get_custom_data(
                category="adhd_patterns",
                key=f"{user_id}_energy"
            )
            if energy_data:
                result["energy"] = [EnergyPattern.from_dict(p) for p in energy_data]
                logger.info(f"Loaded {len(result['energy'])} energy patterns for {user_id}")

            # Load attention patterns
            attention_data = await self.conport.get_custom_data(
                category="adhd_patterns",
                key=f"{user_id}_attention"
            )
            if attention_data:
                result["attention"] = [AttentionPattern.from_dict(p) for p in attention_data]
                logger.info(f"Loaded {len(result['attention'])} attention patterns for {user_id}")

            # Load break patterns
            break_data = await self.conport.get_custom_data(
                category="adhd_patterns",
                key=f"{user_id}_breaks"
            )
            if break_data:
                result["breaks"] = [BreakPattern.from_dict(p) for p in break_data]
                logger.info(f"Loaded {len(result['breaks'])} break patterns for {user_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            return {"energy": [], "attention": [], "breaks": []}
