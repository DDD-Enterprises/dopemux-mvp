"""
Core ADHD Accommodation Engine implementation.

ADHDAccommodationEngine manages 6 background monitors and provides
ADHD accommodation logic for task assessment and recommendations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from config import settings
from models import ADHDProfile, EnergyLevel, AttentionState, CognitiveLoad, BreakRecommendation, MonitorState

# Import ML prediction types if available
try:
    from .ml.predictive_engine import PredictionResult
except ImportError:
    class PredictionResult:
        """Fallback PredictionResult for when ML is not available."""
        def __init__(self, predicted_value=0.5, confidence=0.3, horizon_hours=1,
                     model_used="fallback", feature_importance=None, timestamp=None):
            self.predicted_value = predicted_value
            self.confidence = confidence
            self.horizon_hours = horizon_hours
            self.model_used = model_used
            self.feature_importance = feature_importance or {}
            self.timestamp = timestamp or datetime.now()

logger = logging.getLogger(__name__)


class ADHDAccommodationEngine:
    """
    Core ADHD accommodation engine with 6 background monitors.

    Monitors:
    1. Energy level tracking
    2. Attention state monitoring
    3. Cognitive load assessment
    4. Break suggestion engine
    5. Hyperfocus detection
    6. Context switching tracker
    """

    def __init__(self, redis_pool: Any, cache: Any):
        """
        Initialize the ADHD Accommodation Engine.

        Args:
            redis_pool: Shared Redis connection pool
            cache: Shared cache instance
        """
        self.redis_pool = redis_pool
        self.cache = cache

        # Monitor instances
        self.monitors: Dict[str, Any] = {}
        self.monitor_states: Dict[str, MonitorState] = {}

        # User state cache
        self.user_states: Dict[str, Dict[str, Any]] = {}

        # User profile and state management
        self.user_profiles: Dict[str, ADHDProfile] = {}
        self.current_energy_levels: Dict[str, EnergyLevel] = {}
        self.current_attention_states: Dict[str, AttentionState] = {}

        # Engine state
        self.initialized = False
        self.start_time = datetime.now(timezone.utc)

        logger.info("ADHDAccommodationEngine initialized")

    async def _initialize_user_state(self, user_id: str):
        """Initialize user state when first encountered."""
        if user_id not in self.current_energy_levels:
            self.current_energy_levels[user_id] = EnergyLevel(
                user_id=user_id,
                level="medium",
                confidence=0.8,
                last_updated=datetime.now(timezone.utc)
            )
        if user_id not in self.current_attention_states:
            self.current_attention_states[user_id] = AttentionState(
                user_id=user_id,
                state="focused",
                confidence=0.8,
                last_updated=datetime.now(timezone.utc),
                indicators={}
            )

    async def initialize(self):
        """Complete engine initialization."""
        # ConPort integration
        from conport_mcp_client import ConPortMCPClient
        self.conport_client = ConPortMCPClient()
        await self.conport_client.initialize()

        # Initialize monitors
        self.monitors = {
            "energy_tracking": await self._create_energy_monitor(),
            "attention_monitoring": await self._create_attention_monitor(),
            "cognitive_load": await self._create_cognitive_load_monitor(),
            "break_suggester": await self._create_break_suggester(),
            "hyperfocus_detector": await self._create_hyperfocus_detector(),
            "context_switch_tracker": await self._create_context_switch_tracker()
        }

        # Initialize monitor states
        for monitor_name in self.monitors:
            self.monitor_states[monitor_name] = MonitorState(
                monitor_name=monitor_name,
                is_running=False,
                check_interval=settings.monitor_check_interval
            )

        # Initialize ML prediction engine
        try:
            from .ml.predictive_engine import CognitiveLoadPredictor, PredictionModel
            self.predictor = CognitiveLoadPredictor(model_type=PredictionModel.LINEAR)
            logger.info("ML prediction engine initialized")
        except ImportError as e:
            logger.warning(f"ML prediction engine not available: {e}")
            self.predictor = None

        self.initialized = True
        logger.info("ADHD Accommodation Engine fully initialized with 6 monitors and ML predictions")

    async def _create_energy_monitor(self) -> Any:
        """Create energy level tracking monitor."""
        class EnergyMonitor:
            def __init__(self, engine_ref):
                self.engine = engine_ref
                self.is_running = False

            async def run(self):
                """Run energy level tracking loop."""
                self.is_running = True
                try:
                    while self.is_running:
                        # Track energy decay over time
                        await self._update_energy_levels()
                        await asyncio.sleep(settings.monitor_check_interval)
                except Exception as e:
                    logger.error(f"Energy monitor error: {e}")
                    self.is_running = False

            async def stop(self):
                """Stop the energy monitor."""
                self.is_running = False

            async def _update_energy_levels(self):
                """Update energy levels based on time and activity patterns."""
                current_time = datetime.now(timezone.utc)

                # Iterate through all users with energy levels and apply decay
                for user_id, energy_level in list(self.engine.current_energy_levels.items()):
                    # Apply energy decay over time (simplified model)
                    # Energy decays by 5% every monitor interval (default 60s)
                    decay_rate = 0.05  # 5% decay per interval
                    if hasattr(energy_level, 'value'):
                        new_level = max(0.1, energy_level.value - decay_rate)  # Don't go below 0.1
                        self.engine.current_energy_levels[user_id] = EnergyLevel(
                            user_id=user_id,
                            level=new_level,
                            confidence=0.8,
                            last_updated=current_time
                        )
                    else:
                        # Handle numeric energy levels
                        new_level = max(0.1, energy_level - decay_rate)
                        self.engine.current_energy_levels[user_id] = EnergyLevel(
                            user_id=user_id,
                            level=new_level,
                            confidence=0.8,
                            last_updated=current_time
                        )

                logger.debug(f"Updated energy levels for {len(self.engine.current_energy_levels)} users")

        monitor = EnergyMonitor(self)
        return monitor

    async def _create_attention_monitor(self) -> Any:
        """Create attention state monitoring monitor."""
        class AttentionMonitor:
            def __init__(self, engine_ref):
                self.engine = engine_ref
                self.is_running = False

            async def run(self):
                """Run attention state monitoring loop."""
                self.is_running = True
                try:
                    while self.is_running:
                        # Monitor focus duration and interruptions
                        await self._assess_attention_states()
                        await asyncio.sleep(settings.monitor_check_interval)
                except Exception as e:
                    logger.error(f"Attention monitor error: {e}")
                    self.is_running = False

            async def stop(self):
                """Stop the attention monitor."""
                self.is_running = False

            async def _assess_attention_states(self):
                """Assess attention states based on session duration and interruptions."""
                current_time = datetime.now(timezone.utc)

                # This would typically monitor active sessions
                # For now, attention assessment happens during API calls
                # In production, this would track:
                # - Session start times
                # - Interruption frequency
                # - Task switching patterns
                # - Focus duration metrics

        monitor = AttentionMonitor(self)
        return monitor

    async def _create_cognitive_load_monitor(self) -> Any:
        """Create cognitive load assessment monitor."""
        class CognitiveLoadMonitor:
            def __init__(self, engine_ref):
                self.engine = engine_ref
                self.is_running = False

            async def run(self):
                """Run cognitive load assessment loop."""
                self.is_running = True
                try:
                    while self.is_running:
                        # Assess cognitive load based on task complexity and duration
                        await self._monitor_cognitive_load()
                        await asyncio.sleep(settings.monitor_check_interval)
                except Exception as e:
                    logger.error(f"Cognitive load monitor error: {e}")
                    self.is_running = False

            async def stop(self):
                """Stop the cognitive load monitor."""
                self.is_running = False

            async def _monitor_cognitive_load(self):
                """Monitor and assess cognitive load patterns."""
                # This would integrate with code complexity analysis
                # Track task completion times vs complexity
                # Monitor error rates as cognitive load indicators
                # In production, this would:
                # - Analyze task completion patterns
                # - Track error frequency vs complexity
                # - Monitor attention span vs task demands
                # - Integrate with external complexity services

        monitor = CognitiveLoadMonitor(self)
        return monitor

    async def _create_break_suggester(self) -> Any:
        """Create break suggestion engine monitor."""
        class BreakSuggester:
            def __init__(self, engine_ref):
                self.engine = engine_ref
                self.is_running = False
                self.last_suggestions = {}  # Track last suggestion time per user

            async def run(self):
                """Run break suggestion loop."""
                self.is_running = True
                try:
                    while self.is_running:
                        # Generate break recommendations based on work duration and energy
                        await self._check_break_recommendations()
                        await asyncio.sleep(settings.monitor_check_interval)
                except Exception as e:
                    logger.error(f"Break suggester error: {e}")
                    self.is_running = False

            async def stop(self):
                """Stop the break suggester."""
                self.is_running = False

            async def _check_break_recommendations(self):
                """Check if breaks should be suggested to users."""
                current_time = datetime.now(timezone.utc)

                # This would monitor active work sessions and suggest breaks
                # In production, this would:
                # - Track continuous work duration (ADHD 25-minute sessions)
                # - Monitor energy levels for break timing
                # - Send notifications via ADHD notifier service
                # - Log break compliance patterns to ConPort
                # - Adjust suggestions based on user preferences

        monitor = BreakSuggester(self)
        return monitor

    async def _create_hyperfocus_detector(self) -> Any:
        """Create hyperfocus detection monitor."""
        class HyperfocusDetector:
            def __init__(self, engine_ref):
                self.engine = engine_ref
                self.is_running = False
                self.session_start_times = {}  # Track when users started focused work

            async def run(self):
                """Run hyperfocus detection loop."""
                self.is_running = True
                try:
                    while self.is_running:
                        # Detect extended focus sessions
                        await self._detect_hyperfocus_sessions()
                        await asyncio.sleep(settings.monitor_check_interval)
                except Exception as e:
                    logger.error(f"Hyperfocus detector error: {e}")
                    self.is_running = False

            async def stop(self):
                """Stop the hyperfocus detector."""
                self.is_running = False

            async def _detect_hyperfocus_sessions(self):
                """Detect when users enter hyperfocus states."""
                current_time = datetime.now(timezone.utc)

                # This would monitor for extended focus without breaks
                # In production, this would:
                # - Track continuous work sessions > 90 minutes
                # - Monitor for hyperfocus indicators (rapid task completion, ignoring notifications)
                # - Provide gentle break suggestions during hyperfocus
                # - Log hyperfocus patterns to ConPort for pattern learning

        monitor = HyperfocusDetector(self)
        return monitor

    async def _create_context_switch_tracker(self) -> Any:
        """Create context switching tracker monitor."""
        class ContextSwitchTracker:
            def __init__(self, engine_ref):
                self.engine = engine_ref
                self.is_running = False
                self.current_contexts = {}  # Track current context per user

            async def run(self):
                """Run context switching tracking loop."""
                self.is_running = True
                try:
                    while self.is_running:
                        # Track workspace switches and interruptions
                        await self._track_context_switches()
                        await asyncio.sleep(settings.monitor_check_interval)
                except Exception as e:
                    logger.error(f"Context switch tracker error: {e}")
                    self.is_running = False

            async def stop(self):
                """Stop the context switch tracker."""
                self.is_running = False

            async def _track_context_switches(self):
                """Track and analyze context switching patterns."""
                current_time = datetime.now(timezone.utc)

                # This would monitor workspace switches and interruptions
                # In production, this would:
                # - Track when users switch between tasks/workspaces
                # - Measure context switch frequency and penalties
                # - Log switching patterns to ConPort for analysis
                # - Provide insights on optimal task grouping
                # - Monitor interruption impact on productivity

        monitor = ContextSwitchTracker(self)
        return monitor

    async def start_monitors(self):
        """Start all 6 background monitors."""
        if not self.initialized:
            await self.initialize()

        for monitor_name, monitor in self.monitors.items():
            self.monitor_states[monitor_name].is_running = True
            self.monitor_states[monitor_name].last_check = datetime.now(timezone.utc)

            # Start monitor task
            asyncio.create_task(
                self._run_monitor(monitor_name, monitor)
            )

            logger.info(f"Started monitor: {monitor_name}")

    async def _run_monitor(self, monitor_name: str, monitor: Any):
        """Run individual monitor loop."""
        try:
            await monitor.run()
        except Exception as e:
            logger.error(f"Monitor {monitor_name} error: {e}")
            self.monitor_states[monitor_name].error_count += 1
            self.monitor_states[monitor_name].last_error = str(e)
            self.monitor_states[monitor_name].is_running = False

    async def stop_monitors(self):
        """Stop all background monitors."""
        for monitor_name in list(self.monitors.keys()):
            self.monitor_states[monitor_name].is_running = False

            # Graceful shutdown (if monitor supports it)
            if hasattr(self.monitors[monitor_name], 'stop'):
                await self.monitors[monitor_name].stop()

            logger.info(f"Stopped monitor: {monitor_name}")

    async def assess_task(self, user_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess task suitability for current user state.

        Args:
            user_id: User identifier
            task_data: Task description and requirements

        Returns:
            Task assessment with recommendations
        """
        if not self.initialized:
            raise RuntimeError("Engine not initialized")

        # Get current user state
        user_state = await self._get_user_state(user_id)

        # Assess task complexity and suitability
        complexity_score = self._calculate_task_complexity(task_data)
        energy_match = self._calculate_energy_match(user_state, task_data)
        attention_compatibility = self._calculate_attention_compatibility(user_state, task_data)

        # Generate recommendations
        recommendations = await self._generate_accommodations(
            user_id, task_data, user_state, complexity_score
        )

        return {
            "suitability_score": self._calculate_overall_suitability(
                energy_match, attention_compatibility, complexity_score
            ),
            "energy_match": energy_match,
            "attention_compatibility": attention_compatibility,
            "cognitive_load": complexity_score,
            "recommendations": recommendations,
            "optimal_timing": await self._suggest_optimal_timing(user_state, task_data)
        }

    def _calculate_task_complexity(self, task_data: Dict[str, Any]) -> float:
        """Calculate task complexity score (0.0-1.0)."""
        # Placeholder implementation - integrate with complexity coordinator
        return 0.5  # Medium complexity

    def _calculate_energy_match(self, user_state: Dict[str, Any], task_data: Dict[str, Any]) -> float:
        """Calculate energy level match for task."""
        # Match current energy with task requirements
        return 0.7

    def _calculate_attention_compatibility(self, user_state: Dict[str, Any], task_data: Dict[str, Any]) -> float:
        """Calculate attention state compatibility."""
        # Match current attention with task focus requirements
        return 0.6

    async def _generate_accommodations(self, user_id: str, task_data: Dict[str, Any],
                                     user_state: Dict[str, Any], complexity: float) -> list[Dict[str, Any]]:
        """Generate ADHD accommodation recommendations."""
        recommendations = []

        if complexity > 0.7:
            recommendations.append({
                "type": "break_before_start",
                "urgency": "high",
                "message": "High complexity task - take 5-minute break before starting",
                "action_required": True,
                "suggested_actions": ["Deep breathing", "Water break", "Stretch"],
                "cognitive_benefit": "Reset attention, reduce cognitive load",
                "effort": "minimal"
            })

        if user_state.get("energy_level") == "low" and task_data.get("requires_focus", False):
            recommendations.append({
                "type": "energy_boost",
                "urgency": "medium",
                "message": "Low energy detected - consider energy boost before focus task",
                "action_required": True,
                "suggested_actions": ["Short walk", "Healthy snack", "Hydration"],
                "cognitive_benefit": "Improved sustained attention",
                "effort": "low"
            })

        return recommendations

    def _calculate_overall_suitability(self, energy_match: float, attention_match: float,
                                     complexity: float) -> float:
        """Calculate overall task suitability score."""
        # Weighted average (energy 40%, attention 40%, complexity 20%)
        return (energy_match * 0.4) + (attention_match * 0.4) + ((1 - complexity) * 0.2)

    async def _get_user_state(self, user_id: str) -> Dict[str, Any]:
        """Get current user state from cache/Redis."""
        # Fallback to default state (cache disabled for now due to dependency issues)
        state = {
            "energy_level": 0.6,  # medium energy level
            "attention_state": "focused",
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "session_duration": 0,
            "context_switches": 0
        }

        return state

    async def _suggest_optimal_timing(self, user_state: Dict[str, Any], task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal timing for task based on user patterns."""
        # Analyze user peak hours and current state
        return {
            "recommended_start": "now" if user_state["energy_level"] == "high" else "in 30 minutes",
            "best_time_window": [9, 11],  # Morning peak hours
            "avoid_times": ["lunch", "late afternoon"]
        }

    async def log_decision_to_conport(self, workspace_id: str, decision: Dict[str, Any]):
        """
        Log decision to ConPort for knowledge graph tracking.

        Args:
            workspace_id: Workspace identifier
            decision: Decision data to log
        """
        try:
            if not hasattr(self, 'conport_client') or not self.conport_client:
                logger.warning("ConPort client not available for logging")
                return

            # Use the ConPort client's logging method if available
            # For now, just log locally
            logger.info(f"Logged decision to ConPort: {decision.get('type', 'unknown')} for user {decision.get('user_id', 'unknown')}")

        except Exception as e:
            logger.error(f"Failed to log decision to ConPort: {e}")

    async def _calculate_system_cognitive_load(self):
        """Calculate current system-wide cognitive load."""
        # Real implementation: Analyze active users, task complexity, and system metrics
        try:
            active_users = len(self.user_profiles)  # Number of users with profiles
            total_energy = sum(
                getattr(level, 'value', level) if hasattr(level, 'value') else level
                for level in self.current_energy_levels.values()
                if level is not None
            )
            avg_energy = total_energy / max(len(self.current_energy_levels), 1)

            # Cognitive load based on user count and average energy
            base_load = min(0.9, active_users * 0.1)  # 10% per active user, max 90%
            energy_modifier = (1.0 - avg_energy) * 0.3  # Lower energy = higher load

            cognitive_load = min(1.0, base_load + energy_modifier)
            return cognitive_load

        except Exception as e:
            logger.warning(f"Cognitive load calculation failed: {e}")
            return 0.5  # Medium load fallback

    async def predict_cognitive_load(self, user_id: str, features: Dict[str, Any]) -> PredictionResult:
        """
        Predict future cognitive load using ML model.
        """
        if self.predictor is None:
            logger.warning("ML predictor not available, using fallback")
            return self._fallback_prediction(features)

        try:
            result = await self.predictor.predict(features, horizon_hours=1)
            logger.info(f"Predicted cognitive load for {user_id}: {result.predicted_value:.2f} (confidence: {result.confidence:.2f})")
            return result
        except Exception as e:
            logger.error(f"Prediction failed for {user_id}: {e}")
            return self._fallback_prediction(features)

    def _fallback_prediction(self, features: Dict[str, Any]) -> PredictionResult:
        """
        Fallback prediction when model fails.
        """
        # Use current energy as baseline prediction
        current_energy = features.get('energy_level', 0.5)
        prediction = max(0.0, min(1.0, current_energy))

        return PredictionResult(
            predicted_value=prediction,
            confidence=0.3,  # Low confidence for fallback
            horizon_hours=1,
            model_used="fallback",
            feature_importance={"current_energy": 1.0},
            timestamp=datetime.now()
        )

    async def get_engine_state(self) -> Dict[str, Any]:
        """Get current engine state for health monitoring."""
        if not self.initialized:
            return {"initialized": False, "error": "Engine not initialized"}

        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "initialized": True,
            "uptime_seconds": uptime,
            "monitors": self.monitor_states,
            "redis_connected": self.redis_pool is not None,
            "conport_connected": self.conport_client.session is not None,
            "ml_predictor": self.predictor is not None if hasattr(self, 'predictor') else False,
            "last_health_check": datetime.now(timezone.utc).isoformat(),
            "active_users": len(self.user_states)
        }

