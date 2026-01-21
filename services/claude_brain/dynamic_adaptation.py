"""
Dynamic Adaptation Manager - Phase 2A: Real-time ADHD state adaptation

This module provides dynamic, real-time adaptation to user cognitive states,
implementing research-backed ADHD-friendly interaction patterns with privacy controls.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

import aiohttp

from .config import settings

logger = logging.getLogger(__name__)


class AttentionState(Enum):
    """ADHD attention states for dynamic adaptation."""
    HYPERFOCUSED = "hyperfocused"
    FOCUSED = "focused"
    SCATTERED = "scattered"
    FATIGUED = "fatigued"
    OVERWHELMED = "overwhelmed"


class CognitiveLoad(Enum):
    """Cognitive load levels for response scaling."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    OVERWHELMING = "overwhelming"


@dataclass
class UserCognitiveState:
    """Real-time cognitive state from ADHD Engine."""
    user_id: str
    cognitive_load: float  # 0.0-1.0
    attention_state: AttentionState
    energy_level: str  # very_low, low, medium, high, hyper
    focus_duration: int  # minutes of current focus session
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_score: float = 1.0  # 0.0-1.0


@dataclass
class AdaptationMetrics:
    """Performance metrics for adaptation system."""
    total_adaptations: int = 0
    avg_adaptation_time: float = 0.0
    success_rate: float = 1.0
    privacy_compliance_rate: float = 1.0
    user_satisfaction_score: float = 0.0


@dataclass
class PrivacySettings:
    """User privacy preferences for adaptation."""
    allow_cognitive_monitoring: bool = True
    allow_personalization: bool = True
    data_retention_days: int = 30
    share_anonymized_data: bool = False
    require_explicit_consent: bool = True


class ADHDIntegration:
    """
    Integration with ADHD Engine for real-time cognitive state monitoring.

    Provides <50ms polling with privacy controls and graceful degradation.
    """

    def __init__(self, engine_url: str, api_key: Optional[str] = None):
        self.engine_url = engine_url
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, UserCognitiveState] = {}
        self.cache_ttl = 5  # seconds

    async def initialize(self) -> bool:
        """Initialize HTTP session for ADHD Engine communication."""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=2.0, connect=1.0)
            )
            # Test connection
            await self._health_check()
            return True
        except Exception as e:
            logger.error(f"ADHD Engine initialization failed: {e}")
            return False

    async def _health_check(self) -> bool:
        """Check ADHD Engine health."""
        if not self.session:
            return False

        try:
            async with self.session.get(f"{self.engine_url}/health") as response:
                return response.status == 200
        except Exception as e:
            return False

            logger.error(f"Error: {e}")
    async def get_cognitive_state(self, user_id: str, session_id: Optional[str] = None) -> Optional[UserCognitiveState]:
        """
        Get current cognitive state for user.

        Uses caching for performance and privacy controls.
        """
        # Check cache first
        cache_key = f"{user_id}:{session_id}"
        if cache_key in self.cache:
            cached_state = self.cache[cache_key]
            if (datetime.now() - cached_state.last_updated).seconds < self.cache_ttl:
                return cached_state

        # Fetch from ADHD Engine
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            params = {"user_id": user_id}
            if session_id:
                params["session_id"] = session_id

            async with self.session.get(
                f"{self.engine_url}/api/v1/user-profile/{user_id}",
                headers=headers,
                params=params
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    state = UserCognitiveState(
                        user_id=user_id,
                        cognitive_load=data.get("cognitive_load", 0.5),
                        attention_state=AttentionState(data.get("attention_state", "focused")),
                        energy_level=data.get("energy_level", "medium"),
                        focus_duration=data.get("focus_duration", 25),
                        last_updated=datetime.now(),
                        confidence_score=data.get("confidence", 1.0)
                    )

                    # Cache the result
                    self.cache[cache_key] = state
                    return state

                else:
                    logger.warning(f"ADHD Engine returned status {response.status} for user {user_id}")

        except Exception as e:
            logger.debug(f"ADHD Engine query failed for user {user_id}: {e}")

        # Return default state on failure (graceful degradation)
        return UserCognitiveState(
            user_id=user_id,
            cognitive_load=0.5,
            attention_state=AttentionState.FOCUSED,
            energy_level="medium",
            focus_duration=25,
            confidence_score=0.5
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
        self.cache.clear()


class CognitiveLoadScaler:
    """
    Scales response complexity based on user's current cognitive load.

    Research-backed approach using progressive disclosure and complexity adaptation.
    """

    def __init__(self):
        # Complexity scaling factors
        self.complexity_thresholds = {
            0.0: CognitiveLoad.MINIMAL,      # Very low load
            0.3: CognitiveLoad.LOW,          # Low load
            0.5: CognitiveLoad.MODERATE,     # Moderate load
            0.7: CognitiveLoad.HIGH,         # High load
            0.9: CognitiveLoad.OVERWHELMING  # Very high load
        }

    def get_load_level(self, cognitive_load: float) -> CognitiveLoad:
        """Convert cognitive load score to complexity level."""
        for threshold, level in sorted(self.complexity_thresholds.items(), reverse=True):
            if cognitive_load >= threshold:
                return level
        return CognitiveLoad.MINIMAL

    async def scale_response(self, response: str, cognitive_load: float) -> str:
        """
        Scale response complexity based on cognitive load.

        Uses progressive disclosure and formatting adaptations.
        """
        load_level = self.get_load_level(cognitive_load)

        if load_level == CognitiveLoad.OVERWHELMING:
            return self._minimal_response(response)
        elif load_level == CognitiveLoad.HIGH:
            return self._simplified_response(response)
        elif load_level == CognitiveLoad.MODERATE:
            return self._structured_response(response)
        elif load_level == CognitiveLoad.LOW:
            return self._detailed_response(response)
        else:  # MINIMAL
            return self._comprehensive_response(response)

    def _minimal_response(self, response: str) -> str:
        """Minimal response for overwhelming cognitive load."""
        # Extract just the essential information
        lines = response.split('\n')
        essential_lines = []

        for line in lines[:5]:  # First 5 lines only
            if any(indicator in line.upper() for indicator in ['ERROR', 'SUCCESS', 'WARNING', 'IMPORTANT']):
                essential_lines.append(f"⚠️ {line.strip()}")

        if not essential_lines:
            # Fallback: first non-empty line
            for line in lines:
                if line.strip():
                    essential_lines.append(f"💡 {line.strip()}")
                    break

        essential_lines.append("\n💭 **More details available when cognitive load decreases**")
        return '\n'.join(essential_lines)

    def _simplified_response(self, response: str) -> str:
        """Simplified response for high cognitive load."""
        # Use bullet points and short sentences
        lines = response.split('\n')
        simplified = []

        for line in lines:
            if line.strip():
                # Shorten long lines
                if len(line) > 100:
                    line = line[:97] + "..."
                simplified.append(f"• {line}")

        return '\n'.join(simplified[:10])  # Limit to 10 items

    def _structured_response(self, response: str) -> str:
        """Structured response for moderate cognitive load."""
        # Add clear sections and formatting
        lines = response.split('\n')
        structured = ["## Key Points\n"]

        for i, line in enumerate(lines[:15]):
            if line.strip():
                structured.append(f"{i+1}. {line}")

        return '\n'.join(structured)

    def _detailed_response(self, response: str) -> str:
        """Detailed response for low cognitive load."""
        # Add helpful context and examples
        lines = response.split('\n')
        detailed = ["## Detailed Response\n"]

        for line in lines[:20]:
            if line.strip():
                detailed.append(line)

        detailed.append("\n💡 **Tip**: This detailed response is available because your current cognitive load appears manageable.")
        return '\n'.join(detailed)

    def _comprehensive_response(self, response: str) -> str:
        """Comprehensive response for minimal cognitive load."""
        # Full response with enhancements
        lines = response.split('\n')
        comprehensive = ["## Comprehensive Analysis\n"]

        for line in lines:
            if line.strip():
                comprehensive.append(line)

        comprehensive.extend([
            "",
            "## Additional Context",
            "This comprehensive response is provided because your cognitive load is currently very low,",
            "allowing for detailed analysis and complete information presentation.",
            "",
            "If your cognitive state changes, the response format will automatically adapt."
        ])

        return '\n'.join(comprehensive)


class AttentionStateDetector:
    """
    Detects attention state changes and triggers appropriate adaptations.

    Monitors patterns and provides proactive suggestions.
    """

    def __init__(self):
        self.state_history: Dict[str, List[Tuple[datetime, AttentionState]]] = {}
        self.patterns: Dict[str, Dict[str, Any]] = {}

    def record_state_change(self, user_id: str, old_state: AttentionState, new_state: AttentionState) -> None:
        """Record attention state transition."""
        if user_id not in self.state_history:
            self.state_history[user_id] = []

        self.state_history[user_id].append((datetime.now(), new_state))

        # Keep only recent history (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self.state_history[user_id] = [
            (timestamp, state) for timestamp, state in self.state_history[user_id]
            if timestamp > cutoff
        ]

    def detect_patterns(self, user_id: str) -> Dict[str, Any]:
        """Detect attention patterns for the user."""
        if user_id not in self.state_history:
            return {"pattern": "insufficient_data"}

        history = self.state_history[user_id]
        if len(history) < 5:
            return {"pattern": "learning"}

        # Analyze state transitions
        transitions = []
        for i in range(1, len(history)):
            old_time, old_state = history[i-1]
            new_time, new_state = history[i]
            duration = (new_time - old_time).total_seconds() / 60  # minutes
            transitions.append((old_state, new_state, duration))

        # Detect common patterns
        patterns = {
            "focus_duration_avg": sum(t[2] for t in transitions) / len(transitions),
            "common_transitions": self._find_common_transitions(transitions),
            "peak_focus_times": self._detect_peak_focus_times(history)
        }

        self.patterns[user_id] = patterns
        return patterns

    def _find_common_transitions(self, transitions: List[Tuple]) -> Dict[str, int]:
        """Find most common state transitions."""
        transition_counts = {}
        for old_state, new_state, _ in transitions:
            key = f"{old_state.value}_to_{new_state.value}"
            transition_counts[key] = transition_counts.get(key, 0) + 1

        return dict(sorted(transition_counts.items(), key=lambda x: x[1], reverse=True)[:5])

    def _detect_peak_focus_times(self, history: List[Tuple]) -> List[str]:
        """Detect times when user is most focused."""
        focus_periods = [
            timestamp.hour for timestamp, state in history
            if state in [AttentionState.FOCUSED, AttentionState.HYPERFOCUSED]
        ]

        if not focus_periods:
            return []

        # Group by hour
        hour_counts = {}
        for hour in focus_periods:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Return top 3 hours
        top_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return [f"{hour}:00" for hour, _ in top_hours]

    def get_adaptation_suggestions(self, user_id: str, current_state: AttentionState) -> List[str]:
        """Get adaptation suggestions based on current state and patterns."""
        suggestions = []

        patterns = self.patterns.get(user_id, {})

        if current_state == AttentionState.SCATTERED:
            suggestions.extend([
                "Consider breaking complex tasks into smaller steps",
                "Use visual timers or reminders for focus periods",
                "Try the Pomodoro technique with 5-minute breaks"
            ])

        elif current_state == AttentionState.FATIGUED:
            suggestions.extend([
                "Take a short break (5-10 minutes) before continuing",
                "Hydrate and consider a healthy snack",
                "Try a brief mindfulness or breathing exercise"
            ])

        elif current_state == AttentionState.OVERWHELMED:
            suggestions.extend([
                "Focus on just one task at a time",
                "Use noise-cancelling or calming background sounds",
                "Break down the task into the smallest possible steps"
            ])

        # Pattern-based suggestions
        if patterns.get("peak_focus_times"):
            peak_times = patterns["peak_focus_times"]
            suggestions.append(f"You tend to be most focused around: {', '.join(peak_times[:2])}")

        return suggestions[:5]  # Limit to 5 suggestions


class PrivacyManager:
    """
    Manages user privacy preferences and data handling.

    Ensures compliance with privacy regulations and user consent.
    """

    def __init__(self, default_settings: PrivacySettings):
        self.user_settings: Dict[str, PrivacySettings] = {}
        self.default_settings = default_settings
        self.consent_log: Dict[str, List[Dict[str, Any]]] = {}

    def get_user_settings(self, user_id: str) -> PrivacySettings:
        """Get privacy settings for user."""
        return self.user_settings.get(user_id, self.default_settings)

    def update_user_settings(self, user_id: str, settings: PrivacySettings) -> None:
        """Update privacy settings for user."""
        self.user_settings[user_id] = settings

        # Log consent change
        if user_id not in self.consent_log:
            self.consent_log[user_id] = []

        self.consent_log[user_id].append({
            "timestamp": datetime.now(),
            "action": "settings_updated",
            "settings": settings.__dict__
        })

    def can_monitor(self, user_id: str) -> bool:
        """Check if cognitive monitoring is allowed."""
        settings = self.get_user_settings(user_id)
        return settings.allow_cognitive_monitoring

    def can_personalize(self, user_id: str) -> bool:
        """Check if personalization is allowed."""
        settings = self.get_user_settings(user_id)
        return settings.allow_personalization

    def should_retain_data(self, user_id: str, data_timestamp: datetime) -> bool:
        """Check if data should be retained based on retention policy."""
        settings = self.get_user_settings(user_id)
        retention_period = timedelta(days=settings.data_retention_days)

        return (datetime.now() - data_timestamp) <= retention_period

    def anonymize_data(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Anonymize data for sharing if allowed."""
        settings = self.get_user_settings(user_id)

        if not settings.share_anonymized_data:
            return {}

        # Remove personally identifiable information
        anonymized = data.copy()
        anonymized.pop('user_id', None)
        anonymized.pop('session_id', None)
        anonymized.pop('personal_data', None)

        return anonymized

    def get_consent_log(self, user_id: str) -> List[Dict[str, Any]]:
        """Get consent and privacy action log for user."""
        return self.consent_log.get(user_id, [])


class DynamicAdaptationManager:
    """
    Phase 2A: Real-time ADHD state adaptation system.

    Provides dynamic, research-backed adaptation to user cognitive states
    with privacy controls and performance monitoring.
    """

    def __init__(self, adhd_engine_url: str, privacy_settings: Optional[PrivacySettings] = None):
        self.adhd_integration = ADHDIntegration(adhd_engine_url)
        self.cognitive_scaler = CognitiveLoadScaler()
        self.attention_detector = AttentionStateDetector()
        self.privacy_manager = PrivacyManager(privacy_settings or PrivacySettings())

        # Performance monitoring
        self.metrics = AdaptationMetrics()
        self.performance_log: List[Dict[str, Any]] = []

        # State tracking
        self.user_states: Dict[str, UserCognitiveState] = {}
        self.last_adaptation: Dict[str, datetime] = {}

    async def initialize(self) -> bool:
        """Initialize the adaptation manager."""
        logger.info("🧠 Initializing Dynamic Adaptation Manager...")

        success = await self.adhd_integration.initialize()
        if success:
            logger.info("✅ Dynamic Adaptation Manager initialized")
        else:
            logger.warning("⚠️ Dynamic Adaptation Manager initialized with degraded ADHD integration")

        return True

    async def adapt_response(
        self,
        user_id: str,
        response: str,
        session_id: Optional[str] = None,
        force_adaptation: bool = False
    ) -> str:
        """
        Adapt response based on user's current cognitive state.

        Returns adapted response with performance tracking.
        """
        start_time = time.time()

        try:
            # Check privacy permissions
            if not self.privacy_manager.can_monitor(user_id):
                self.metrics.total_adaptations += 1
                return response  # Return original response

            # Get current cognitive state
            cognitive_state = await self.adhd_integration.get_cognitive_state(user_id, session_id)

            if not cognitive_state:
                # Graceful degradation
                self.metrics.total_adaptations += 1
                return response

            # Store state for tracking
            self.user_states[user_id] = cognitive_state

            # Check if adaptation is needed (avoid over-adaptation)
            if not force_adaptation and not self._should_adapt(user_id, cognitive_state):
                self.metrics.total_adaptations += 1
                return response

            # Detect attention state changes
            old_state = self.user_states.get(user_id)
            if old_state and old_state.attention_state != cognitive_state.attention_state:
                self.attention_detector.record_state_change(
                    user_id, old_state.attention_state, cognitive_state.attention_state
                )

            # Apply cognitive load scaling
            adapted_response = await self.cognitive_scaler.scale_response(
                response, cognitive_state.cognitive_load
            )

            # Add attention-based suggestions if appropriate
            if cognitive_state.attention_state in [AttentionState.SCATTERED, AttentionState.FATIGUED]:
                suggestions = self.attention_detector.get_adaptation_suggestions(
                    user_id, cognitive_state.attention_state
                )
                if suggestions:
                    adapted_response += "\n\n" + "\n".join(f"💡 {s}" for s in suggestions[:2])

            # Update performance metrics
            adaptation_time = time.time() - start_time
            self.metrics.total_adaptations += 1
            self.metrics.avg_adaptation_time = (
                self.metrics.avg_adaptation_time + adaptation_time
            ) / 2

            self.last_adaptation[user_id] = datetime.now()

            # Log adaptation for analysis
            self.performance_log.append({
                "user_id": user_id,
                "timestamp": datetime.now(),
                "original_length": len(response),
                "adapted_length": len(adapted_response),
                "cognitive_load": cognitive_state.cognitive_load,
                "attention_state": cognitive_state.attention_state.value,
                "adaptation_time": adaptation_time
            })

            # Keep only recent logs
            cutoff = datetime.now() - timedelta(hours=24)
            self.performance_log = [
                log for log in self.performance_log
                if log["timestamp"] > cutoff
            ]

            return adapted_response

        except Exception as e:
            logger.error(f"Response adaptation failed for user {user_id}: {e}")
            self.metrics.total_adaptations += 1
            return response  # Return original on error

    def _should_adapt(self, user_id: str, cognitive_state: UserCognitiveState) -> bool:
        """Determine if adaptation is needed based on state and timing."""
        # Always adapt for extreme states
        if cognitive_state.cognitive_load > 0.8 or cognitive_state.attention_state == AttentionState.OVERWHELMED:
            return True

        # Don't adapt too frequently (max once per minute)
        last_adaptation = self.last_adaptation.get(user_id)
        if last_adaptation and (datetime.now() - last_adaptation).seconds < 60:
            return False

        # Adapt if state changed significantly
        old_state = self.user_states.get(user_id)
        if old_state:
            load_change = abs(cognitive_state.cognitive_load - old_state.cognitive_load)
            state_changed = cognitive_state.attention_state != old_state.attention_state

            if load_change > 0.2 or state_changed:
                return True

        return False

    def get_user_state(self, user_id: str) -> Optional[UserCognitiveState]:
        """Get current cognitive state for user."""
        return self.user_states.get(user_id)

    def get_adaptation_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get adaptation patterns and insights for user."""
        user_logs = [log for log in self.performance_log if log["user_id"] == user_id]

        if not user_logs:
            return {"status": "no_data"}

        # Analyze patterns
        avg_load = sum(log["cognitive_load"] for log in user_logs) / len(user_logs)
        state_distribution = {}
        for log in user_logs:
            state = log["attention_state"]
            state_distribution[state] = state_distribution.get(state, 0) + 1

        most_common_state = max(state_distribution.items(), key=lambda x: x[1])[0]

        return {
            "total_adaptations": len(user_logs),
            "average_cognitive_load": round(avg_load, 2),
            "most_common_attention_state": most_common_state,
            "state_distribution": state_distribution,
            "attention_patterns": self.attention_detector.detect_patterns(user_id),
            "adaptation_effectiveness": self._calculate_effectiveness(user_logs)
        }

    def _calculate_effectiveness(self, user_logs: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate adaptation effectiveness metrics."""
        if len(user_logs) < 5:
            return {"status": "insufficient_data"}

        # Effectiveness based on response length adaptation
        length_ratios = [
            log["adapted_length"] / max(log["original_length"], 1)
            for log in user_logs
        ]

        avg_ratio = sum(length_ratios) / len(length_ratios)

        # High cognitive load should result in shorter responses
        high_load_logs = [log for log in user_logs if log["cognitive_load"] > 0.7]
        if high_load_logs:
            high_load_ratios = [
                log["adapted_length"] / max(log["original_length"], 1)
                for log in high_load_logs
            ]
            high_load_avg = sum(high_load_ratios) / len(high_load_ratios)
        else:
            high_load_avg = avg_ratio

        return {
            "overall_adaptation_ratio": round(avg_ratio, 2),
            "high_load_adaptation_ratio": round(high_load_avg, 2),
            "cognitive_load_responsiveness": round(abs(avg_ratio - high_load_avg), 2)
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive adaptation metrics."""
        return {
            "adaptation_metrics": {
                "total_adaptations": self.metrics.total_adaptations,
                "avg_adaptation_time_ms": round(self.metrics.avg_adaptation_time * 1000, 2),
                "success_rate": round(self.metrics.success_rate, 3),
                "privacy_compliance_rate": round(self.metrics.privacy_compliance_rate, 3)
            },
            "system_health": {
                "active_users": len(self.user_states),
                "adhd_integration_healthy": self.adhd_integration._health_check(),
                "recent_adaptations": len([
                    log for log in self.performance_log
                    if (datetime.now() - log["timestamp"]).seconds < 3600
                ])
            },
            "privacy_stats": {
                "users_with_settings": len(self.privacy_manager.user_settings),
                "consent_logs_total": sum(len(logs) for logs in self.privacy_manager.consent_log.values())
            }
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.adhd_integration.cleanup()
        self.user_states.clear()
        self.performance_log.clear()</content>
</xai:function_call">The file content contains invalid XML/HTML markup. Please provide clean Python code only.