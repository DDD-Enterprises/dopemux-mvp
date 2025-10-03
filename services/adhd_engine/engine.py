"""
ADHD Accommodation Engine - Core Logic

Extracted from task-orchestrator/adhd_engine.py as part of Path C migration (Decision #140).

Week 1: Standalone service with ActivityTracker stubs
Week 3: Full ConPort integration via ActivityTracker

Features:
- Real-time energy level and attention state monitoring
- Personalized accommodation recommendations
- Intelligent task routing based on cognitive capacity
- Break timing and hyperfocus protection
- Context switching minimization
- Cognitive load balancing across all systems
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import redis.asyncio as redis

from models import (
    EnergyLevel,
    AttentionState,
    CognitiveLoadLevel,
    ADHDProfile,
    AccommodationRecommendation
)
from config import settings
from activity_tracker import ActivityTracker

logger = logging.getLogger(__name__)


class ADHDAccommodationEngine:
    """
    Comprehensive ADHD accommodation engine for seamless development workflow.

    Features:
    - Real-time energy level and attention state monitoring
    - Personalized accommodation recommendations
    - Intelligent task routing based on cognitive capacity
    - Break timing and hyperfocus protection
    - Context switching minimization
    - Cognitive load balancing across all systems
    """

    def __init__(self):
        """Initialize ADHD accommodation engine with settings-based configuration."""
        self.redis_url = settings.redis_url
        self.workspace_id = settings.workspace_id

        # Redis connection for state persistence
        self.redis_client: Optional[redis.Redis] = None

        # ADHD state tracking
        self.user_profiles: Dict[str, ADHDProfile] = {}
        self.current_energy_levels: Dict[str, EnergyLevel] = {}
        self.current_attention_states: Dict[str, AttentionState] = {}
        self.active_accommodations: Dict[str, List[AccommodationRecommendation]] = {}

        # Cognitive load monitoring
        self.cognitive_load_history: List[Tuple[datetime, float]] = []
        self.context_switch_history: List[Tuple[datetime, str, str]] = []
        self.break_history: List[Tuple[datetime, str, int]] = []

        # Accommodation statistics
        self.accommodation_stats = {
            "recommendations_made": 0,
            "breaks_suggested": 0,
            "energy_optimizations": 0,
            "cognitive_load_reductions": 0,
            "context_switch_preventions": 0,
            "hyperfocus_protections": 0
        }

        # Background monitoring
        self.monitoring_tasks: List[asyncio.Task] = []
        self.running = False

        # Activity tracker (initialized in initialize())
        self.activity_tracker: Optional[ActivityTracker] = None

    async def initialize(self) -> None:
        """Initialize ADHD accommodation engine."""
        logger.info("🧠 Initializing ADHD Accommodation Engine...")

        # Initialize Redis connection
        self.redis_client = redis.from_url(
            self.redis_url,
            db=settings.redis_db,
            decode_responses=True
        )
        await self.redis_client.ping()

        # Initialize ActivityTracker with ConPort database
        conport_db_path = settings.workspace_id + "/context_portal/context.db"
        self.activity_tracker = ActivityTracker(
            redis_client=self.redis_client,
            conport_db_path=conport_db_path
        )
        logger.info("✅ ActivityTracker initialized with ConPort SQLite")

        # Load existing user profiles
        await self._load_user_profiles()

        # Start background monitoring
        await self._start_accommodation_monitoring()

        self.running = True
        logger.info("✅ ADHD Accommodation Engine ready!")

    async def _load_user_profiles(self) -> None:
        """Load ADHD profiles from persistent storage."""
        try:
            # Load profiles from Redis
            profile_keys = await self.redis_client.keys("adhd:profile:*")

            for key in profile_keys:
                user_id = key.split(":")[-1]
                profile_data = await self.redis_client.get(key)

                if profile_data:
                    profile = ADHDProfile(**json.loads(profile_data))
                    self.user_profiles[user_id] = profile

            logger.info(f"📋 Loaded {len(self.user_profiles)} ADHD profiles")

        except Exception as e:
            logger.error(f"Failed to load ADHD profiles: {e}")

    async def _start_accommodation_monitoring(self) -> None:
        """Start background monitoring tasks."""
        monitors = [
            self._energy_level_monitor(),
            self._attention_state_monitor(),
            self._cognitive_load_monitor(),
            self._break_timing_monitor(),
            self._hyperfocus_protection_monitor(),
            self._context_switch_analyzer()
        ]

        self.monitoring_tasks = [asyncio.create_task(monitor) for monitor in monitors]
        logger.info("👥 ADHD monitoring systems started")

    # Core Accommodation Methods

    async def assess_task_suitability(
        self,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess if task is suitable for user's current ADHD state."""
        try:
            # Get current user state
            current_energy = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
            current_attention = self.current_attention_states.get(user_id, AttentionState.FOCUSED)
            user_profile = self.user_profiles.get(user_id)

            if not user_profile:
                # Create default profile
                user_profile = ADHDProfile(user_id=user_id)
                self.user_profiles[user_id] = user_profile

            # Calculate task cognitive load
            task_complexity = task_data.get("complexity_score", 0.5)
            estimated_duration = task_data.get("estimated_minutes", 25)

            cognitive_load = self._calculate_task_cognitive_load(
                task_complexity, estimated_duration, task_data
            )

            # Energy matching assessment
            energy_match_score = self._assess_energy_match(
                current_energy, cognitive_load, user_profile
            )

            # Attention state compatibility
            attention_compatibility = self._assess_attention_compatibility(
                current_attention, task_data, cognitive_load
            )

            # Overall suitability score
            suitability_score = (energy_match_score * 0.5 + attention_compatibility * 0.5)

            # Generate recommendations
            recommendations = await self._generate_task_recommendations(
                user_profile, current_energy, current_attention, task_data, cognitive_load
            )

            return {
                "suitability_score": suitability_score,
                "energy_match": energy_match_score,
                "attention_compatibility": attention_compatibility,
                "cognitive_load": cognitive_load,
                "cognitive_load_level": self._categorize_cognitive_load(cognitive_load),
                "recommendations": [
                    {
                        "accommodation_type": r.accommodation_type,
                        "urgency": r.urgency,
                        "message": r.message,
                        "action_required": r.action_required,
                        "suggested_actions": r.suggested_actions,
                        "cognitive_benefit": r.cognitive_benefit,
                        "implementation_effort": r.implementation_effort
                    } for r in recommendations
                ],
                "accommodations_needed": self._identify_needed_accommodations(
                    user_profile, cognitive_load, suitability_score
                ),
                "optimal_timing": self._suggest_optimal_timing(user_profile, current_energy),
                "adhd_insights": {
                    "hyperfocus_risk": self._assess_hyperfocus_risk(user_profile, task_data),
                    "distraction_risk": self._assess_distraction_risk(user_profile, current_attention),
                    "context_switch_impact": self._assess_context_switch_impact(user_profile)
                }
            }

        except Exception as e:
            logger.error(f"Task suitability assessment failed: {e}")
            return {"error": str(e)}

    def _calculate_task_cognitive_load(
        self,
        complexity: float,
        duration: int,
        task_data: Dict[str, Any]
    ) -> float:
        """Calculate cognitive load for task."""
        try:
            # Base load from complexity
            base_load = complexity * 0.4

            # Duration factor (longer tasks = higher load)
            duration_factor = min(duration / 60.0, 0.3)  # Max 0.3 for duration

            # Task type factor
            task_type_loads = {
                "research": 0.2,
                "implementation": 0.3,
                "debugging": 0.4,
                "architecture": 0.3,
                "testing": 0.2,
                "documentation": 0.1
            }

            task_description = task_data.get("description", "").lower()
            task_type_load = 0.2  # Default

            for task_type, load in task_type_loads.items():
                if task_type in task_description:
                    task_type_load = load
                    break

            # Dependencies factor (more dependencies = higher load)
            dependencies = task_data.get("dependencies", [])
            dependency_load = min(len(dependencies) * 0.05, 0.1)

            # Total cognitive load
            total_load = min(
                base_load + duration_factor + task_type_load + dependency_load,
                1.0
            )

            return total_load

        except Exception:
            return 0.5  # Default moderate load

    def _assess_energy_match(
        self,
        current_energy: EnergyLevel,
        cognitive_load: float,
        profile: ADHDProfile
    ) -> float:
        """Assess how well task matches current energy level."""
        try:
            energy_scores = {
                EnergyLevel.VERY_LOW: 0.1,
                EnergyLevel.LOW: 0.3,
                EnergyLevel.MEDIUM: 0.6,
                EnergyLevel.HIGH: 0.8,
                EnergyLevel.HYPERFOCUS: 1.0
            }

            current_capacity = energy_scores[current_energy]

            # Perfect match gets highest score
            if abs(current_capacity - cognitive_load) < 0.2:
                return 1.0

            # Penalize mismatches
            mismatch_penalty = abs(current_capacity - cognitive_load)
            energy_match = max(0.0, 1.0 - (mismatch_penalty * 2))

            # Apply profile adjustments
            if current_energy == EnergyLevel.HYPERFOCUS and profile.hyperfocus_tendency > 0.8:
                # High hyperfocus tendency - can handle higher loads
                energy_match += 0.2

            return min(energy_match, 1.0)

        except Exception:
            return 0.5

    def _assess_attention_compatibility(
        self,
        attention_state: AttentionState,
        task_data: Dict[str, Any],
        cognitive_load: float
    ) -> float:
        """Assess task compatibility with attention state."""
        try:
            compatibility_matrix = {
                AttentionState.SCATTERED: {
                    "max_cognitive_load": 0.3,
                    "preferred_duration": 10,
                    "complexity_penalty": 0.5
                },
                AttentionState.TRANSITIONING: {
                    "max_cognitive_load": 0.4,
                    "preferred_duration": 15,
                    "complexity_penalty": 0.3
                },
                AttentionState.FOCUSED: {
                    "max_cognitive_load": 0.8,
                    "preferred_duration": 25,
                    "complexity_penalty": 0.0
                },
                AttentionState.HYPERFOCUSED: {
                    "max_cognitive_load": 1.0,
                    "preferred_duration": 90,
                    "complexity_penalty": -0.2  # Bonus for complex tasks
                },
                AttentionState.OVERWHELMED: {
                    "max_cognitive_load": 0.1,
                    "preferred_duration": 5,
                    "complexity_penalty": 0.8
                }
            }

            state_config = compatibility_matrix.get(attention_state, compatibility_matrix[AttentionState.FOCUSED])

            # Check cognitive load compatibility
            max_load = state_config["max_cognitive_load"]
            if cognitive_load > max_load:
                load_compatibility = max_load / max(cognitive_load, 0.1)
            else:
                load_compatibility = 1.0

            # Check duration compatibility
            task_duration = task_data.get("estimated_minutes", 25)
            preferred_duration = state_config["preferred_duration"]
            duration_compatibility = 1.0 - abs(task_duration - preferred_duration) / max(preferred_duration, task_duration)

            # Apply complexity penalty/bonus
            complexity_adjustment = state_config["complexity_penalty"]
            adjusted_compatibility = max(0.0, min(1.0, (load_compatibility + duration_compatibility) / 2 - complexity_adjustment))

            return adjusted_compatibility

        except Exception:
            return 0.5

    async def _generate_task_recommendations(
        self,
        profile: ADHDProfile,
        energy: EnergyLevel,
        attention: AttentionState,
        task_data: Dict[str, Any],
        cognitive_load: float
    ) -> List[AccommodationRecommendation]:
        """Generate ADHD-specific task recommendations."""
        recommendations = []

        try:
            # Energy-based recommendations
            if energy in [EnergyLevel.VERY_LOW, EnergyLevel.LOW] and cognitive_load > 0.4:
                recommendations.append(AccommodationRecommendation(
                    accommodation_type="energy_mismatch",
                    urgency="soon",
                    message="💙 This task might be challenging at your current energy level",
                    action_required=False,
                    suggested_actions=[
                        "Take a 10-minute energizing break",
                        "Switch to a simpler task first",
                        "Break this task into smaller pieces"
                    ],
                    cognitive_benefit="Prevents frustration and preserves energy",
                    implementation_effort="minimal"
                ))

            # Attention state recommendations
            if attention == AttentionState.SCATTERED and task_data.get("estimated_minutes", 0) > 15:
                recommendations.append(AccommodationRecommendation(
                    accommodation_type="attention_fragmentation",
                    urgency="immediate",
                    message="🌀 Consider breaking this task down - attention seems scattered",
                    action_required=True,
                    suggested_actions=[
                        "Use 10-minute focus blocks",
                        "Start with the simplest part",
                        "Enable focus mode to reduce distractions"
                    ],
                    cognitive_benefit="Improves focus and reduces overwhelm",
                    implementation_effort="low"
                ))

            # Hyperfocus protection
            if energy == EnergyLevel.HYPERFOCUS and task_data.get("estimated_minutes", 0) > 60:
                recommendations.append(AccommodationRecommendation(
                    accommodation_type="hyperfocus_protection",
                    urgency="when_convenient",
                    message="🚀 Hyperfocus detected - setting up protection boundaries",
                    action_required=False,
                    suggested_actions=[
                        "Automatic break reminders every 30 minutes",
                        "Hydration reminders",
                        "Eye rest breaks"
                    ],
                    cognitive_benefit="Prevents hyperfocus burnout and maintains health",
                    implementation_effort="minimal"
                ))

            # Task complexity recommendations
            complexity_level = self._categorize_cognitive_load(cognitive_load)
            if complexity_level == CognitiveLoadLevel.HIGH and attention != AttentionState.HYPERFOCUSED:
                recommendations.append(AccommodationRecommendation(
                    accommodation_type="complexity_warning",
                    urgency="soon",
                    message="🧠 High complexity task - consider optimal timing",
                    action_required=False,
                    suggested_actions=[
                        "Schedule during peak energy hours",
                        "Ensure minimal distractions",
                        "Prepare supporting resources"
                    ],
                    cognitive_benefit="Sets up conditions for success",
                    implementation_effort="low"
                ))

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []

    # Helper methods for assess_task_suitability (Week 1 stubs)

    def _identify_needed_accommodations(
        self,
        profile: ADHDProfile,
        cognitive_load: float,
        suitability_score: float
    ) -> List[str]:
        """Identify specific accommodations needed for task."""
        accommodations = []

        if suitability_score < 0.6:
            accommodations.append("energy_optimization")
        if cognitive_load > 0.7:
            accommodations.append("complexity_reduction")
        if profile.break_resistance > 0.7:
            accommodations.append("break_reminders")

        return accommodations

    def _suggest_optimal_timing(
        self,
        profile: ADHDProfile,
        current_energy: EnergyLevel
    ) -> Dict[str, Any]:
        """Suggest optimal timing for task execution."""
        if profile.peak_hours:
            current_hour = datetime.now().hour
            is_peak = current_hour in profile.peak_hours

            return {
                "is_optimal_time": is_peak and current_energy in [EnergyLevel.HIGH, EnergyLevel.HYPERFOCUS],
                "suggested_hours": profile.peak_hours,
                "reason": "peak_energy_hours" if is_peak else "consider_rescheduling"
            }

        return {"is_optimal_time": True, "reason": "no_preference"}

    def _assess_hyperfocus_risk(
        self,
        profile: ADHDProfile,
        task_data: Dict[str, Any]
    ) -> str:
        """Assess risk of entering hyperfocus state."""
        if profile.hyperfocus_tendency > 0.7:
            task_duration = task_data.get("estimated_minutes", 25)
            if task_duration > 60:
                return "high"
            elif task_duration > 30:
                return "medium"
        return "low"

    def _assess_distraction_risk(
        self,
        profile: ADHDProfile,
        attention: AttentionState
    ) -> str:
        """Assess risk of distraction during task."""
        if attention in [AttentionState.SCATTERED, AttentionState.OVERWHELMED]:
            return "high"
        elif profile.distraction_sensitivity > 0.7:
            return "medium"
        return "low"

    def _assess_context_switch_impact(self, profile: ADHDProfile) -> str:
        """Assess impact of context switching on this user."""
        if profile.context_switch_penalty > 0.7:
            return "high"
        elif profile.context_switch_penalty > 0.4:
            return "medium"
        return "low"

    # Monitoring Systems

    async def _energy_level_monitor(self) -> None:
        """Monitor and track user energy levels."""
        logger.info("⚡ Started energy level monitoring")

        while self.running:
            try:
                # Monitor energy indicators across all users
                for user_id in self.user_profiles.keys():
                    await self._assess_current_energy_level(user_id)

                # Check every N minutes (from settings)
                await asyncio.sleep(settings.energy_monitor_interval)

            except Exception as e:
                logger.error(f"Energy level monitoring error: {e}")
                await asyncio.sleep(600)

    async def _assess_current_energy_level(self, user_id: str) -> EnergyLevel:
        """Assess current energy level for user."""
        try:
            # Get recent activity indicators
            activity_data = await self._get_recent_activity(user_id)

            # Analyze patterns
            task_completion_rate = activity_data.get("completion_rate", 0.5)
            context_switches = activity_data.get("context_switches", 0)
            break_compliance = activity_data.get("break_compliance", 1.0)
            time_since_last_break = activity_data.get("minutes_since_break", 0)

            # Energy assessment algorithm
            energy_score = 0.6  # Base energy level

            # Task completion indicates energy
            if task_completion_rate > 0.8:
                energy_score += 0.3
            elif task_completion_rate < 0.3:
                energy_score -= 0.4

            # High context switching indicates scattered energy
            if context_switches > 5:
                energy_score -= 0.3

            # Break compliance indicates energy management
            if break_compliance < 0.5:
                energy_score -= 0.2

            # Time since break affects energy
            if time_since_last_break > 60:  # More than 1 hour
                energy_score -= 0.3

            # Map score to energy level
            if energy_score >= 0.9:
                current_energy = EnergyLevel.HYPERFOCUS
            elif energy_score >= 0.7:
                current_energy = EnergyLevel.HIGH
            elif energy_score >= 0.4:
                current_energy = EnergyLevel.MEDIUM
            elif energy_score >= 0.2:
                current_energy = EnergyLevel.LOW
            else:
                current_energy = EnergyLevel.VERY_LOW

            # Update tracking
            previous_energy = self.current_energy_levels.get(user_id)
            self.current_energy_levels[user_id] = current_energy

            # Log energy change if significant
            if previous_energy and previous_energy != current_energy:
                await self._log_energy_change(user_id, previous_energy, current_energy)

            return current_energy

        except Exception as e:
            logger.error(f"Energy assessment failed for {user_id}: {e}")
            return EnergyLevel.MEDIUM

    async def _attention_state_monitor(self) -> None:
        """Monitor attention state patterns."""
        logger.info("👁️ Started attention state monitoring")

        while self.running:
            try:
                for user_id in self.user_profiles.keys():
                    await self._assess_attention_state(user_id)

                await asyncio.sleep(settings.attention_monitor_interval)

            except Exception as e:
                logger.error(f"Attention monitoring error: {e}")
                await asyncio.sleep(300)

    async def _assess_attention_state(self, user_id: str) -> AttentionState:
        """Assess current attention state for user."""
        try:
            # Get attention indicators
            indicators = await self._get_attention_indicators(user_id)

            rapid_switching = indicators.get("context_switches_per_hour", 0) > 10
            task_abandonment = indicators.get("abandoned_tasks", 0) > 2
            focus_duration = indicators.get("average_focus_duration", 25)
            distraction_events = indicators.get("distraction_events", 0)

            # Assess attention state
            if task_abandonment > 3 or distraction_events > 10:
                attention_state = AttentionState.OVERWHELMED
            elif rapid_switching and focus_duration < 10:
                attention_state = AttentionState.SCATTERED
            elif focus_duration > 60 and distraction_events < 2:
                attention_state = AttentionState.HYPERFOCUSED
            elif focus_duration > 20 and distraction_events < 5:
                attention_state = AttentionState.FOCUSED
            else:
                attention_state = AttentionState.TRANSITIONING

            # Update tracking
            previous_state = self.current_attention_states.get(user_id)
            self.current_attention_states[user_id] = attention_state

            # Log state change
            if previous_state and previous_state != attention_state:
                await self._log_attention_change(user_id, previous_state, attention_state)

            return attention_state

        except Exception as e:
            logger.error(f"Attention assessment failed for {user_id}: {e}")
            return AttentionState.FOCUSED

    async def _cognitive_load_monitor(self) -> None:
        """Monitor overall cognitive load across all tasks."""
        logger.info("🧠 Started cognitive load monitoring")

        while self.running:
            try:
                # Calculate system-wide cognitive load
                total_load = await self._calculate_system_cognitive_load()

                # Store in history
                self.cognitive_load_history.append((datetime.now(timezone.utc), total_load))

                # Keep only recent history (last 24 hours)
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                self.cognitive_load_history = [
                    (timestamp, load) for timestamp, load in self.cognitive_load_history
                    if timestamp > cutoff_time
                ]

                # Check for cognitive overload
                if total_load > 2.0:  # High system-wide load
                    await self._handle_cognitive_overload()

                await asyncio.sleep(settings.cognitive_monitor_interval)

            except Exception as e:
                logger.error(f"Cognitive load monitoring error: {e}")
                await asyncio.sleep(300)

    async def _break_timing_monitor(self) -> None:
        """Monitor break timing and compliance."""
        logger.info("☕ Started break timing monitor")

        while self.running:
            try:
                for user_id, profile in self.user_profiles.items():
                    await self._check_break_timing(user_id, profile)

                await asyncio.sleep(settings.break_monitor_interval)

            except Exception as e:
                logger.error(f"Break timing monitoring error: {e}")
                await asyncio.sleep(300)

    async def _check_break_timing(self, user_id: str, profile: ADHDProfile) -> None:
        """Check if user needs break recommendation."""
        try:
            # Get last break time
            last_break_key = f"adhd:last_break:{user_id}"
            last_break_str = await self.redis_client.get(last_break_key)

            if last_break_str:
                last_break = datetime.fromisoformat(last_break_str)
                time_since_break = (datetime.now(timezone.utc) - last_break).total_seconds() / 60
            else:
                time_since_break = profile.optimal_task_duration + 5  # Force initial break check

            # Check if break is needed
            break_needed = False
            break_reason = ""

            if time_since_break >= profile.max_task_duration:
                break_needed = True
                break_reason = "maximum_duration_reached"
            elif time_since_break >= profile.optimal_task_duration * 2:
                break_needed = True
                break_reason = "extended_work_period"

            # Check current energy level
            current_energy = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
            if current_energy == EnergyLevel.VERY_LOW and time_since_break >= 15:
                break_needed = True
                break_reason = "low_energy_recovery"

            if break_needed:
                await self._recommend_break(user_id, break_reason, time_since_break)

        except Exception as e:
            logger.error(f"Break timing check failed for {user_id}: {e}")

    async def _recommend_break(self, user_id: str, reason: str, work_duration: float) -> None:
        """Recommend break with personalized ADHD messaging."""
        try:
            profile = self.user_profiles.get(user_id)

            # Customize break message based on profile and reason
            break_messages = {
                "maximum_duration_reached": f"🛡️ You've been focused for {work_duration:.0f} minutes - time for a healthy break!",
                "extended_work_period": f"☕ Great work! After {work_duration:.0f} minutes, a break will help maintain productivity",
                "low_energy_recovery": f"💙 Low energy detected - a short break might help recharge",
                "hyperfocus_protection": f"🚀 Hyperfocus mode detected - protecting your wellbeing with a break reminder"
            }

            message = break_messages.get(reason, f"☕ Break recommended after {work_duration:.0f} minutes of work")

            # Personalize break suggestions
            break_suggestions = ["5-minute walk", "Hydrate", "Stretch"]

            if profile and profile.break_activity_suggestions:
                break_suggestions.extend([
                    "Deep breathing exercise",
                    "Look away from screen (20-20-20 rule)",
                    "Quick snack if needed"
                ])

            # Create break recommendation
            break_recommendation = AccommodationRecommendation(
                accommodation_type="break_timing",
                urgency="soon",
                message=message,
                action_required=not profile.break_resistance > 0.7 if profile else True,
                suggested_actions=break_suggestions,
                cognitive_benefit="Prevents burnout and maintains sustained productivity",
                implementation_effort="minimal"
            )

            # Store recommendation
            if user_id not in self.active_accommodations:
                self.active_accommodations[user_id] = []

            self.active_accommodations[user_id].append(break_recommendation)

            # Store in Redis for UI consumption
            break_data = {
                "user_id": user_id,
                "reason": reason,
                "work_duration": work_duration,
                "message": message,
                "suggestions": break_suggestions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await self.redis_client.lpush(
                f"adhd:break_recommendations:{self.workspace_id}",
                json.dumps(break_data)
            )

            # Trim to keep recent recommendations
            await self.redis_client.ltrim(
                f"adhd:break_recommendations:{self.workspace_id}",
                0, 9  # Keep 10 most recent
            )

            self.accommodation_stats["breaks_suggested"] += 1
            logger.info(f"☕ Break recommended for {user_id}: {reason}")

        except Exception as e:
            logger.error(f"Break recommendation failed: {e}")

    async def _hyperfocus_protection_monitor(self) -> None:
        """Monitor for hyperfocus states and provide protection."""
        logger.info("🛡️ Started hyperfocus protection monitor")

        while self.running:
            try:
                for user_id, profile in self.user_profiles.items():
                    current_attention = self.current_attention_states.get(user_id)

                    if current_attention == AttentionState.HYPERFOCUSED:
                        await self._apply_hyperfocus_protection(user_id, profile)

                await asyncio.sleep(settings.hyperfocus_monitor_interval)

            except Exception as e:
                logger.error(f"Hyperfocus protection error: {e}")
                await asyncio.sleep(600)

    async def _apply_hyperfocus_protection(self, user_id: str, profile: ADHDProfile) -> None:
        """Apply hyperfocus protection measures."""
        try:
            # Get hyperfocus session duration
            session_start_key = f"adhd:hyperfocus_start:{user_id}"
            session_start_str = await self.redis_client.get(session_start_key)

            if session_start_str:
                session_start = datetime.fromisoformat(session_start_str)
                session_duration = (datetime.now(timezone.utc) - session_start).total_seconds() / 60
            else:
                # Start tracking hyperfocus session
                await self.redis_client.setex(
                    session_start_key,
                    7200,  # 2 hours
                    datetime.now(timezone.utc).isoformat()
                )
                session_duration = 0

            # Apply protection based on duration
            if session_duration > profile.max_task_duration:
                # Force break recommendation
                await self._recommend_break(user_id, "hyperfocus_protection", session_duration)

                # Temporarily reduce task complexity recommendations
                await self._adjust_task_recommendations_for_protection(user_id)

                self.accommodation_stats["hyperfocus_protections"] += 1

            elif session_duration > profile.optimal_task_duration * 1.5:
                # Gentle warning
                warning_data = {
                    "user_id": user_id,
                    "message": "🎯 You've been in hyperfocus for a while - consider a brief break soon",
                    "session_duration": session_duration,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                await self.redis_client.lpush(
                    f"adhd:hyperfocus_warnings:{self.workspace_id}",
                    json.dumps(warning_data)
                )

        except Exception as e:
            logger.error(f"Hyperfocus protection failed for {user_id}: {e}")

    async def _context_switch_analyzer(self) -> None:
        """Analyze and track context switching patterns."""
        logger.info("🔄 Started context switch analyzer")

        while self.running:
            try:
                # Track context switches for all users
                for user_id in self.user_profiles.keys():
                    # Get recent context switches from history
                    recent_switches = [
                        switch for switch in self.context_switch_history
                        if switch[0] > datetime.now(timezone.utc) - timedelta(hours=1)
                    ]

                    # Analyze patterns and provide recommendations
                    if len(recent_switches) > 10:
                        logger.warning(f"⚠️ High context switching detected for {user_id}: {len(recent_switches)} switches in 1 hour")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Context switch analysis error: {e}")
                await asyncio.sleep(600)

    # Utility Methods

    def _categorize_cognitive_load(self, load: float) -> CognitiveLoadLevel:
        """Categorize cognitive load into ADHD-friendly levels."""
        if load <= 0.2:
            return CognitiveLoadLevel.MINIMAL
        elif load <= 0.4:
            return CognitiveLoadLevel.LOW
        elif load <= 0.6:
            return CognitiveLoadLevel.MODERATE
        elif load <= 0.8:
            return CognitiveLoadLevel.HIGH
        else:
            return CognitiveLoadLevel.EXTREME

    # Activity data methods (integrated with ActivityTracker)

    async def _get_recent_activity(self, user_id: str) -> Dict[str, Any]:
        """
        Get recent activity indicators for user from ConPort + Redis.

        Queries real data via ActivityTracker for accurate ADHD assessments.
        """
        try:
            if self.activity_tracker:
                return await self.activity_tracker.get_recent_activity(user_id)
            else:
                # Fallback if tracker not initialized
                logger.warning("ActivityTracker not initialized, using defaults")
                return {
                    "completion_rate": 0.7,
                    "context_switches": 3,
                    "break_compliance": 0.8,
                    "minutes_since_break": 20
                }
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return {
                "completion_rate": 0.5,
                "context_switches": 0,
                "break_compliance": 0.8,
                "minutes_since_break": 30
            }

    async def _get_attention_indicators(self, user_id: str) -> Dict[str, Any]:
        """
        Get attention state indicators from ConPort activity patterns.

        Analyzes real activity log data for accurate attention state detection.
        """
        try:
            if self.activity_tracker:
                return await self.activity_tracker.get_attention_indicators(user_id)
            else:
                logger.warning("ActivityTracker not initialized, using defaults")
                return {
                    "context_switches_per_hour": 5,
                    "abandoned_tasks": 1,
                    "average_focus_duration": 22,
                    "distraction_events": 3
                }
        except Exception as e:
            logger.error(f"Failed to get attention indicators: {e}")
            return {
                "context_switches_per_hour": 3,
                "abandoned_tasks": 0,
                "average_focus_duration": 25,
                "distraction_events": 2
            }

    async def _calculate_system_cognitive_load(self) -> float:
        """
        Calculate system-wide cognitive load.

        Week 1: Uses in-memory history
        Week 3: Will aggregate across users via ConPort
        """
        if not self.cognitive_load_history:
            return 1.0

        # Calculate from recent history (last hour)
        recent_loads = [load for timestamp, load in self.cognitive_load_history[-10:]]
        if recent_loads:
            return sum(recent_loads) / len(recent_loads)
        return 1.0

    async def _handle_cognitive_overload(self) -> None:
        """
        Handle system-wide cognitive overload.

        Week 1: Logs warning
        Week 3: Will create recommendations in ConPort
        """
        total_load = await self._calculate_system_cognitive_load()
        logger.warning(f"⚠️ COGNITIVE OVERLOAD DETECTED: {total_load:.2f}")

    async def _adjust_task_recommendations_for_protection(self, user_id: str) -> None:
        """
        Adjust task recommendations for hyperfocus protection.

        Week 1: Logs action
        Week 3: Will update ConPort ADHD state
        """
        logger.info(f"🛡️ Adjusting recommendations for {user_id} (hyperfocus protection)")

    # Health and Performance

    async def get_accommodation_health(self) -> Dict[str, Any]:
        """Get ADHD accommodation engine health status."""
        try:
            # Monitor health
            active_monitors = len([t for t in self.monitoring_tasks if not t.done()])
            redis_healthy = await self.redis_client.ping() if self.redis_client else False

            # Accommodation effectiveness
            total_recommendations = self.accommodation_stats["recommendations_made"]
            if total_recommendations > 0:
                accommodation_rate = total_recommendations / max(1, len(self.user_profiles))
            else:
                accommodation_rate = 0.0

            # Overall status
            if redis_healthy and active_monitors == len(self.monitoring_tasks):
                if accommodation_rate > 5:  # Active accommodation
                    status = "🧠 Highly Active"
                else:
                    status = "✅ Ready"
            else:
                status = "⚠️ Degraded"

            return {
                "overall_status": status,
                "components": {
                    "redis_persistence": "🟢 Connected" if redis_healthy else "🔴 Disconnected",
                    "monitors_active": f"{active_monitors}/{len(self.monitoring_tasks)}",
                    "user_profiles": len(self.user_profiles)
                },
                "accommodation_stats": self.accommodation_stats,
                "current_state": {
                    "energy_levels": {uid: level.value for uid, level in self.current_energy_levels.items()},
                    "attention_states": {uid: state.value for uid, state in self.current_attention_states.items()},
                    "active_accommodations": {uid: len(accs) for uid, accs in self.active_accommodations.items()}
                },
                "effectiveness_metrics": {
                    "accommodation_rate": f"{accommodation_rate:.1f} per user",
                    "cognitive_load_reductions": self.accommodation_stats["cognitive_load_reductions"],
                    "break_compliance": "monitoring_active"
                }
            }

        except Exception as e:
            logger.error(f"ADHD accommodation health check failed: {e}")
            return {"overall_status": "🔴 Error", "error": str(e)}

    # Placeholder log methods
    async def _log_energy_change(self, user_id: str, previous: EnergyLevel, current: EnergyLevel) -> None:
        """Log energy level change."""
        logger.info(f"⚡ Energy change for {user_id}: {previous.value} → {current.value}")

    async def _log_attention_change(self, user_id: str, previous: AttentionState, current: AttentionState) -> None:
        """Log attention state change."""
        logger.info(f"👁️ Attention change for {user_id}: {previous.value} → {current.value}")

    async def close(self) -> None:
        """Shutdown ADHD accommodation engine."""
        logger.info("🛑 Shutting down ADHD Accommodation Engine...")

        self.running = False

        # Cancel monitoring tasks
        if self.monitoring_tasks:
            for task in self.monitoring_tasks:
                task.cancel()
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ ADHD Accommodation Engine shutdown complete")
