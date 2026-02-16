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
# Serena Integration (Serena v2)

from .models import (
    EnergyLevel,
    AttentionState,
    CognitiveLoadLevel,
    ADHDProfile,
    AccommodationRecommendation
)
from .config import settings
from ml.data_collector import DataCollector
from .activity_tracker import ActivityTracker
from .conport_mcp_client import ConPortMCPClient
from .bridge_integration import ConPortBridgeAdapter
from .pal_client import ADHDPALClient

# ADHD Detectors (Phase 7: Full I/O Wiring)
from .hyperfocus_guard import HyperfocusGuard
from .overwhelm_detector import OverwhelmDetector
from .procrastination_detector import ProcrastinationDetector
from .working_memory_support import WorkingMemorySupport
from .context_preserver import ContextPreserver
from .social_battery_monitor import SocialBatteryMonitor
from .voice_assistant import VoiceAssistant
from .output_dispatcher import ADHDOutputDispatcher, ADHDFinding

# ConPort-KG Integration (optional)
try:
    from dopecon_bridge_connector import emit_state_update
    CONPORT_KG_INTEGRATION = True
except ImportError:
    CONPORT_KG_INTEGRATION = False

logger = logging.getLogger(__name__)

# Machine Learning (IP-005 Days 11-12)
try:
    from ml.predictive_engine import PredictiveADHDEngine
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML module not available - using rule-based logic only")


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

        # Redis connection for state persistence (now using shared pool)
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pool = None  # Shared Redis connection pool

        # MCP clients
        self.pal_client = ADHDPALClient(settings.pal_url, settings)

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

        # ConPort client for persistent tracking via DopeconBridge
        self.conport: Optional[ConPortBridgeAdapter] = None

        # Machine Learning predictive engine (IP-005 Days 11-12)
        self.predictive_engine: Optional[Any] = None  # PredictiveADHDEngine if ML enabled

        # Phase 6: Cache for statusline endpoint (5-second TTL)
        self._statusline_cache: Dict[str, Any] = {}
        self._statusline_cache_time: Dict[str, float] = {}
        self._statusline_cache_ttl = 5  # seconds
        
        # WebSocket streaming (Dashboard Day 7)
        self._websocket_enabled = True  # Feature flag
        
        # ADHD Detectors (Phase 7: Full I/O Wiring)
        # Instantiated in initialize() after Redis/ConPort are ready
        self.hyperfocus_guard: Optional[HyperfocusGuard] = None
        self.overwhelm_detector: Optional[OverwhelmDetector] = None
        self.procrastination_detector: Optional[ProcrastinationDetector] = None
        self.working_memory_support: Optional[WorkingMemorySupport] = None
        self.context_preserver: Optional[ContextPreserver] = None
        self.social_battery_monitor: Optional[SocialBatteryMonitor] = None
        self.voice_assistant: Optional[VoiceAssistant] = None
        
        # ML Data Collector (Phase 10)
        self.data_collector = DataCollector()
        
        # Output Dispatcher (Phase 10.3)
        self.output_dispatcher = ADHDOutputDispatcher(
            enable_push=settings.enable_mobile_push
        )

    async def initialize(self) -> None:
        """Initialize ADHD accommodation engine."""
        logger.info("🧠 Initializing ADHD Accommodation Engine...")

        # Initialize shared Redis connection pool (performance optimization)
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
        from redis_pool import get_redis_pool

        self.redis_pool = await get_redis_pool()
        # Keep legacy redis_client for backward compatibility, but use pool internally
        async with self.redis_pool.get_client() as client:
            self.redis_client = client
            await self.redis_client.ping()

        # Initialize ActivityTracker with ConPort database
        conport_db_path = settings.workspace_id + "/context_portal/context.db"
        # Initialize ConPort MCP client for real data access
        self.conport_mcp = ConPortMCPClient()
        logger.info("✅ ConPort MCP client initialized")

        self.activity_tracker = ActivityTracker(
            redis_client=self.redis_client,
            conport_db_path=conport_db_path,
            conport_mcp_client=self.conport_mcp  # Pass MCP client for real data
        )
        logger.info("✅ ActivityTracker initialized with ConPort MCP integration")

        # DopeconBridge adapter (falls back to stub automatically)
        self.conport = ConPortBridgeAdapter(
            workspace_id=settings.workspace_id,
            base_url=settings.dopecon_bridge_url,
            token=settings.dopecon_bridge_token,
            source_plane=settings.dopecon_bridge_source_plane,
        )
        logger.info("✅ DopeconBridge adapter initialized for ADHD state persistence")

        # Initialize ML predictive engine (IP-005 Days 11-12)
        if settings.enable_ml_predictions and ML_AVAILABLE:
            self.predictive_engine = PredictiveADHDEngine(settings.workspace_id)
            logger.info("✅ ML Predictive Engine enabled (IP-005 Days 11-12)")
        else:
            logger.info("ℹ️  ML predictions disabled - using rule-based logic only")

        # Initialize background prediction service (Phase 3.4)
        if settings.enable_background_predictions:
            from ..services.background_prediction_service import start_background_prediction_service
            asyncio.create_task(start_background_prediction_service())
            logger.info("✅ Background prediction service started (Phase 3.4)")
        else:
            logger.info("ℹ️  Background prediction service disabled")

        # Initialize trust building service (Phase 3.6)
        from .services.trust_building_service import get_trust_building_service
        self.trust_service = await get_trust_building_service(settings.workspace_id)
        logger.info("✅ Trust building service initialized (Phase 3.6)")
        
        # Initialize ADHD Detectors (Phase 7: Full I/O Wiring)
        self.hyperfocus_guard = HyperfocusGuard()
        self.overwhelm_detector = OverwhelmDetector()
        self.procrastination_detector = ProcrastinationDetector()
        self.working_memory_support = WorkingMemorySupport(
            user_id="default",
            bridge_client=self.conport,
            workspace_id=settings.workspace_id
        )
        self.context_preserver = ContextPreserver(
            conport_client=self.conport,
            storage_path=str(settings.workspace_id) + "/.context_snapshots"
        )
        self.social_battery_monitor = SocialBatteryMonitor(
            user_id="default",
            bridge_client=self.conport
        )
        self.voice_assistant = VoiceAssistant(adhd_engine=self)
        logger.info("✅ ADHD Detectors initialized (Phase 7: HyperfocusGuard, OverwhelmDetector, ProcrastinationDetector, WorkingMemorySupport, ContextPreserver, SocialBatteryMonitor, VoiceAssistant)")

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
            self._context_switch_analyzer(),
            self._start_automated_retraining()  # Phase 10.4
        ]

        self.monitoring_tasks = [asyncio.create_task(monitor) for monitor in monitors]
        logger.info("👥 ADHD monitoring systems started")

    async def _start_automated_retraining(self) -> None:
        """
        Background task for automated ML model retraining (Phase 10.4).
        Runs periodically based on configuration to ensure model adapts to new data.
        """
        if not settings.enable_ml_predictions or not ML_AVAILABLE:
            return
            
        logger.info("🤖 Automated retraining loop started")
        
        while self.running:
            try:
                # Calculate sleep time first (e.g., once every 24h)
                # For development/testing, we'll check hourly if we have enough data
                await asyncio.sleep(settings.ml_retrain_interval_hours * 3600)
                
                # We need a user_id to retrain. For MVP, we'll iterate all known users.
                for user_id in self.user_profiles.keys():
                    await self._retrain_user_model(user_id)
                    
            except Exception as e:
                logger.error(f"Retraining loop error: {e}")
                await asyncio.sleep(3600) # Retry in an hour on failure

    async def _retrain_user_model(self, user_id: str) -> None:
        """Retrain model for specific user if enough data exists."""
        try:
            if not hasattr(self, 'data_collector'):
                return
                
            # Load data (Phase 10.4)
            all_data = await self.data_collector.load_all_data()
            user_data = [d for d in all_data if d.get('user_id') == user_id]
            
            if len(user_data) < settings.min_training_samples:
                logger.debug(f"Skipping retraining for {user_id}: insufficient data ({len(user_data)} samples)")
                return
                
            logger.info(f"🔄 Retraining model for {user_id} with {len(user_data)} samples...")
            
            from ml.energy_predictor import EnergyPatternPredictor
            predictor = EnergyPatternPredictor(user_id, model_path=f"{settings.ml_model_path}/{user_id}_energy_model.pkl")
            
            # Train
            # Warning: EnergyPatternPredictor.train is synchronous sklearn. 
            # Should run in executor to avoid blocking event loop.
            accuracy = await asyncio.get_event_loop().run_in_executor(
                None, 
                predictor.train, 
                user_data
            )
            
            if accuracy > 0.0:
                logger.info(f"✅ Model retrained for {user_id}: Accuracy {accuracy:.1%}")
                # Dispatch notification if accuracy is good
                if self.output_dispatcher and accuracy > 0.7:
                     await self.output_dispatcher.dispatch(ADHDFinding(
                        finding_type="model_updated",
                        severity="low",
                        message=f"ADHD Brain Updated: Learned new patterns with {accuracy:.0%} accuracy.",
                        timestamp=datetime.utcnow().isoformat()
                    ))
            
        except Exception as e:
            logger.error(f"Failed to retrain model for {user_id}: {e}")

    # Core Accommodation Methods

    async def assess_task_suitability(
        self,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess if task is suitable for user's current ADHD state using Pal-enhanced analysis."""
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

            # Use Pal thinkdeep for enhanced task complexity assessment
            pal_task_analysis = await self._analyze_task_with_pal(
                task_data, current_energy, current_attention, user_profile
            )

            # Energy matching assessment (enhanced with Pal insights)
            energy_match_score = self._assess_energy_match(
                current_energy, cognitive_load, user_profile
            )

            # Attention state compatibility (enhanced with Pal insights)
            attention_compatibility = self._assess_attention_compatibility(
                current_attention, task_data, cognitive_load
            )

            # Overall suitability score (weighted with Pal confidence)
            pal_confidence = pal_task_analysis.get('confidence', 0.5)
            suitability_score = (
                energy_match_score * 0.4 +
                attention_compatibility * 0.4 +
                pal_confidence * 0.2
            )

            # Generate recommendations (enhanced with Pal suggestions)
            recommendations = await self._generate_task_recommendations(
                user_profile, current_energy, current_attention, task_data, cognitive_load,
                pal_insights=pal_task_analysis
            )

            result = {
                "suitability_score": suitability_score,
                "energy_match": energy_match_score,
                "attention_compatibility": attention_compatibility,
                "cognitive_load": cognitive_load,
                "pal_task_analysis": pal_task_analysis,
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

            # Record prediction for accuracy tracking
            if self.trust_service:
                await self.trust_service.record_prediction_outcome(
                    user_id=user_id,
                    prediction_type="task_suitability",
                    predicted_value=suitability_score,
                    actual_value=None,  # Actual outcome will be recorded later
                    confidence=pal_confidence
                )

            return result

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

        except Exception as e:
            return 0.5  # Default moderate load

            logger.error(f"Error: {e}")
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

        except Exception as e:
            return 0.5

            logger.error(f"Error: {e}")
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

        except Exception as e:
            return 0.5

            logger.error(f"Error: {e}")
    async def _analyze_task_with_pal(
        self,
        task_data: Dict[str, Any],
        current_energy: EnergyLevel,
        current_attention: AttentionState,
        user_profile: ADHDProfile
    ) -> Dict[str, Any]:
        """Use Pal thinkdeep to analyze task complexity and ADHD accommodations."""
        try:
            task_description = task_data.get('description', 'Unknown task')
            task_complexity = task_data.get('complexity_score', 0.5)
            estimated_duration = task_data.get('estimated_minutes', 25)

            pal_prompt = f"""Analyze this task for ADHD accommodation planning:

Task: {task_description}
Complexity: {task_complexity}
Estimated Duration: {estimated_duration} minutes

User Current State:
- Energy Level: {current_energy.value if hasattr(current_energy, 'value') else str(current_energy)}
- Attention State: {current_attention.value if hasattr(current_attention, 'value') else str(current_attention)}
- Profile: Hyperfocus tendency {getattr(user_profile, 'hyperfocus_tendency', 0.5)}, Distraction sensitivity {getattr(user_profile, 'distraction_sensitivity', 0.5)}

Analyze:
1. True cognitive complexity (beyond surface metrics)
2. ADHD-specific challenges and accommodations needed
3. Optimal timing and break patterns
4. Risk factors for distraction or overwhelm
5. Recommended modifications for success

Format: {{
  "true_complexity": 0.7,
  "adhd_challenges": ["list of specific challenges"],
  "optimal_timing": "best time windows",
  "break_strategy": "recommended break pattern",
  "risk_factors": ["distraction risks"],
  "accommodations": ["specific recommendations"],
  "confidence": 0.8
}}"""

            async with self.pal_client:
                response = await self.pal_client.thinkdeep(
                    step=pal_prompt,
                    step_number=1,
                    total_steps=1,
                    next_step_required=False,
                    findings=f"ADHD task analysis for {task_description}",
                    model="gemini-2.5-pro"
                )

                return response.get('reasoning', {
                    'true_complexity': task_complexity,
                    'adhd_challenges': ['Analysis unavailable'],
                    'optimal_timing': 'Unknown',
                    'break_strategy': 'Standard breaks',
                    'risk_factors': ['Unknown'],
                    'accommodations': ['Standard accommodations'],
                    'confidence': 0.3
                })

        except Exception as e:
            logger.error(f"Pal task analysis failed: {e}")
            return {
                'true_complexity': task_complexity,
                'adhd_challenges': ['Analysis failed'],
                'optimal_timing': 'Fallback to profile',
                'break_strategy': 'Standard breaks',
                'risk_factors': ['Unknown'],
                'accommodations': ['Standard accommodations'],
                'confidence': 0.2
            }

    async def _generate_task_recommendations(
        self,
        profile: ADHDProfile,
        energy: EnergyLevel,
        attention: AttentionState,
        task_data: Dict[str, Any],
        cognitive_load: float,
        pal_insights: Optional[Dict[str, Any]] = None
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

            # Enhanced recommendations using Pal insights
            if pal_insights and pal_insights.get('confidence', 0) > 0.6:
                # Incorporate Pal-specific recommendations
                pal_accommodations = pal_insights.get('accommodations', [])
                for accom in pal_accommodations[:3]:  # Limit to top 3 Pal suggestions
                    recommendations.append(AccommodationRecommendation(
                        accommodation_type="pal_recommended",
                        urgency="when_convenient",
                        message=f"🤖 Pal AI Recommendation: {accom}",
                        action_required=False,
                        suggested_actions=[accom],
                        cognitive_benefit="AI-optimized accommodation",
                        implementation_effort="low"
                    ))

                # Add Pal-specific break recommendations
                if 'break_strategy' in pal_insights:
                    recommendations.append(AccommodationRecommendation(
                        accommodation_type="pal_break_strategy",
                        urgency="when_convenient",
                        message=f"⏰ Pal Break Strategy: {pal_insights['break_strategy']}",
                        action_required=False,
                        suggested_actions=[pal_insights['break_strategy']],
                        cognitive_benefit="AI-optimized break timing",
                        implementation_effort="minimal"
                    ))

                # Add Pal risk factor mitigations
                if 'risk_factors' in pal_insights:
                    for risk in pal_insights['risk_factors'][:2]:  # Top 2 risks
                        recommendations.append(AccommodationRecommendation(
                            accommodation_type="pal_risk_mitigation",
                            urgency="when_convenient",
                            message=f"⚠️ Pal Risk Mitigation: {risk}",
                            action_required=False,
                            suggested_actions=[f"Mitigate: {risk}"],
                            cognitive_benefit="Prevents ADHD-specific challenges",
                            implementation_effort="moderate"
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
                    
                    # Phase 10: Record data for ML training
                    if hasattr(self, 'data_collector') and self.data_collector:
                        await self._record_training_data(user_id)

                # Check every N minutes (from settings)
                await asyncio.sleep(settings.energy_monitor_interval)

            except Exception as e:
                logger.error(f"Energy level monitoring error: {e}")
                await asyncio.sleep(600)

    async def _record_training_data(self, user_id: str) -> None:
        """Record current state for ML training (Phase 10)."""
        try:
            # Gather state
            energy_level = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
            attention_state = self.current_attention_states.get(user_id, AttentionState.FOCUSED)
            
            # Simple feature extraction for MVP
            # TODO: Fetch real metrics from history buffers
            state_vector = {
                "energy_level": energy_level.value if hasattr(energy_level, 'value') else str(energy_level),
                "attention_state": attention_state.value if hasattr(attention_state, 'value') else str(attention_state),
                "minutes_since_break": 30, # Placeholder
                "session_duration": 15,    # Placeholder
                "complexity_avg_30min": 0.5, # Placeholder
                "recent_break_count": 0    # Placeholder
            }
            
            await self.data_collector.log_state(user_id, state_vector)
            
        except Exception as e:
            logger.debug(f"Failed to record training data: {e}")

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
        """Monitor cognitive load and emit events to ConPort-KG."""
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

                # Emit state update to ConPort-KG (buffered, emitted every 30s)
                if CONPORT_KG_INTEGRATION:
                    try:
                        # Get current state for first user (or default)
                        user_id = next(iter(self.user_profiles.keys()), "default")
                        attention_state = self.current_attention_states.get(user_id, AttentionState.FOCUSED)
                        energy_level = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)

                        await emit_state_update(
                            attention_state=attention_state.value,
                            energy_level=energy_level.value,
                            cognitive_load=min(total_load / 2.0, 1.0)  # Normalize to 0-1
                        )
                    except Exception as e:
                        logger.debug(f"Event emission skipped: {e}")

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

            # Send mobile notification via Happy CLI
            try:
                await self._send_mobile_notification(
                    user_id=user_id,
                    notification_type="break",
                    title="Break Time! ⏰",
                    message=f"Time for a {work_duration:.0f}-minute break! Try: {break_suggestions[0] if break_suggestions else 'Take a short break'}",
                    duration=5,
                    activity=break_suggestions[0] if break_suggestions else "Take a short break"
                )
                logger.info(f"📱 Mobile break notification sent for {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send mobile break notification: {e}")

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
        Week 3: Aggregates across users via ConPort custom_data
        """
        # Week 3: Read all users' cognitive load from ConPort
        if self.conport:
            try:
                cognitive_loads = self.conport.get_custom_data(category="cognitive_load")

                if cognitive_loads:
                    # Average across all users' recent loads
                    loads = [data.get("load", 1.0) for data in cognitive_loads.values()]
                    avg_load = sum(loads) / len(loads) if loads else 1.0

                    # Also persist current system load for historical tracking
                    self.conport.write_custom_data(
                        category="system_metrics",
                        key="cognitive_load_avg",
                        value={"load": avg_load, "user_count": len(loads)}
                    )

                    return avg_load

            except Exception as e:
                logger.warning(f"Failed to aggregate cognitive load from ConPort: {e}")

        # Fallback to in-memory (Week 1 behavior)
        if not self.cognitive_load_history:
            return 1.0

        recent_loads = [load for timestamp, load in self.cognitive_load_history[-10:]]
        if recent_loads:
            return sum(recent_loads) / len(recent_loads)
        return 1.0

    async def _handle_cognitive_overload(self) -> None:
        """
        Handle system-wide cognitive overload.

        Week 1: Logs warning
        Week 3: Creates break recommendations in ConPort progress_entries
        """
        total_load = await self._calculate_system_cognitive_load()
        logger.warning(f"⚠️ COGNITIVE OVERLOAD DETECTED: {total_load:.2f}")

        # Week 3: Create break recommendation in ConPort
        # Dispatch alert (Phase 10.3)
        if total_load > 0.8 and self.output_dispatcher:
            await self.output_dispatcher.dispatch(ADHDFinding(
                finding_type="overwhelm_critical",
                severity="critical",
                message=f"Cognitive Overload: {total_load:.1%} - Immediate Break Required",
                recommended_actions=["Step away from screen", "Drink water", "Box breathing"]
            ))

        # Week 3: Create break recommendation in ConPort
        if self.conport and total_load > 0.8:  # Overload threshold
            try:
                # Create high-priority break task
                entry_id = self.conport.log_progress_entry(
                    status="TODO",
                    description=f"🧠 BREAK RECOMMENDED - System cognitive load: {total_load:.1%}. "
                                f"Consider taking a 5-10 minute break to prevent burnout."
                )

                if entry_id:
                    logger.info(f"✅ Created break recommendation #{entry_id} in ConPort")
                    self.accommodation_stats["breaks_suggested"] += 1

            except Exception as e:
                logger.error(f"Failed to create break recommendation in ConPort: {e}")

    async def _adjust_task_recommendations_for_protection(self, user_id: str) -> None:
        """
        Adjust task recommendations for hyperfocus protection.

        Week 1: Logs action
        Week 3: Updates ConPort ADHD state with current energy/attention/accommodations
        """
        logger.info(f"🛡️ Adjusting recommendations for {user_id} (hyperfocus protection)")

        # Week 3: Persist current ADHD state to ConPort
        if self.conport:
            try:
                # Get current user state
                energy_level = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
                attention_state = self.current_attention_states.get(user_id, AttentionState.NORMAL)
                accommodations = self.active_accommodations.get(user_id, [])

                # Build state snapshot
                state_data = {
                    "energy_level": energy_level.value if hasattr(energy_level, 'value') else str(energy_level),
                    "attention_state": attention_state.value if hasattr(attention_state, 'value') else str(attention_state),
                    "hyperfocus_protection_active": True,
                    "active_accommodations": [
                        {
                            "type": acc.accommodation_type,
                            "priority": acc.priority.value if hasattr(acc.priority, 'value') else str(acc.priority)
                        }
                        for acc in accommodations[:5]  # Limit to 5 for space
                    ] if accommodations else [],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }

                # Write to ConPort
                self.conport.write_custom_data(
                    category="adhd_state",
                    key=f"user_{user_id}",
                    value=state_data
                )

                logger.debug(f"✅ Persisted ADHD state for {user_id} to ConPort")
                self.accommodation_stats["hyperfocus_protections"] += 1

            except Exception as e:
                logger.error(f"Failed to persist ADHD state to ConPort: {e}")

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
                    "user_profiles": len(self.user_profiles),
                    "background_prediction": "🟢 Active" if hasattr(self, 'background_service') and self.background_service.running else "🔴 Inactive"
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

    async def get_background_service_status(self) -> Dict[str, Any]:
        """Get background prediction service status."""
        try:
            from .services.background_prediction_service import get_background_prediction_service
            service = await get_background_prediction_service()
            return await service.get_status()
        except Exception as e:
            logger.error(f"Failed to get background service status: {e}")
            return {"error": str(e), "running": False}

    # Placeholder log methods
    async def _log_energy_change(self, user_id: str, previous: EnergyLevel, current: EnergyLevel) -> None:
        """Log energy level change."""
        logger.info(f"⚡ Energy change for {user_id}: {previous.value} → {current.value}")

        # Send mobile notification for significant energy drops
        if (current == EnergyLevel.LOW or current == EnergyLevel.VERY_LOW) and previous != current:
            try:
                suggestions = ["Take a short break", "Hydrate", "Have a snack"] if current == EnergyLevel.LOW else ["Rest", "Consider stopping work", "Get fresh air"]
                await self._send_mobile_notification(
                    user_id=user_id,
                    notification_type="energy",
                    title="Energy Alert ⚡",
                    message=f"Your energy level is {current.value.lower()}. Suggestions: {', '.join(suggestions[:2])}",
                    energy_level=current.value.lower(),
                    suggestions=suggestions
                )
                logger.info(f"📱 Mobile energy alert sent for {user_id}: {current.value}")
            except Exception as e:
                logger.warning(f"Failed to send mobile energy notification: {e}")

        # Broadcast to WebSocket clients (Dashboard Day 7)
        if self._websocket_enabled:
            await self._broadcast_state_update(user_id, "energy_change")

    async def _log_attention_change(self, user_id: str, previous: AttentionState, current: AttentionState) -> None:
        """Log attention state change."""
        logger.info(f"👁️ Attention change for {user_id}: {previous.value} → {current.value}")
        
        # Broadcast to WebSocket clients (Dashboard Day 7)
        if self._websocket_enabled:
            await self._broadcast_state_update(user_id, "attention_change")
    
    async def _send_mobile_notification(self, user_id: str, notification_type: str, title: str, message: str, **kwargs) -> None:
        """
        Send mobile notification via Happy CLI integration.

        In a production environment, this would integrate with:
        - Apple Push Notification service (APNs) for iOS
        - Firebase Cloud Messaging (FCM) for Android
        - Web Push API for web notifications
        - SMS services like Twilio for fallback

        For now, this logs the notification for development/testing.
        """
        notification = {
            "user_id": user_id,
            "type": notification_type,
            "title": title,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }

        # Log notification (would be sent to mobile services in production)
        logger.info(f"📱 Mobile Notification: {title} - {message}")

        # Store notification in Redis for tracking
        try:
            await self.redis_client.lpush(
                f"adhd:notifications:{self.workspace_id}",
                json.dumps(notification)
            )
            # Keep only recent notifications
            await self.redis_client.ltrim(
                f"adhd:notifications:{self.workspace_id}",
                0, 49  # Keep 50 most recent
            )
        except Exception as e:
            logger.warning(f"Failed to store notification in Redis: {e}")

    async def _calculate_cognitive_load(self, user_id: str) -> float:
        """Calculate real-time cognitive load for a specific user."""
        try:
            # Use real-time calculation
            energy_level = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
            attention_state = self.current_attention_states.get(user_id, AttentionState.FOCUSED)

            # Map state to base load
            energy_load_map = {
                EnergyLevel.VERY_LOW: 0.9,
                EnergyLevel.LOW: 0.7,
                EnergyLevel.MEDIUM: 0.5,
                EnergyLevel.HIGH: 0.3,
                EnergyLevel.HYPERFOCUS: 0.8
            }
            attention_load_map = {
                AttentionState.OVERWHELMED: 1.0,
                AttentionState.SCATTERED: 0.8,
                AttentionState.TRANSITIONING: 0.6,
                AttentionState.FOCUSED: 0.4,
                AttentionState.HYPERFOCUSED: 0.7
            }

            base_load = (energy_load_map.get(energy_level, 0.5) + attention_load_map.get(attention_state, 0.4)) / 2.0

            # Add dynamic factors if available (e.g. context switches)
            activity_data = await self._get_recent_activity(user_id)
            context_switches = activity_data.get("context_switches", 0)
            switch_penalty = min(context_switches * 0.05, 0.2)

            return min(1.0, base_load + switch_penalty)
        except Exception as e:
            logger.error(f"Error calculating cognitive load for {user_id}: {e}")
            return 0.5

    async def _get_session_duration(self, user_id: str) -> int:
        """Get current session duration in minutes."""
        try:
            # Check if we have a session start time in Redis
            session_start_str = await self.redis_client.get(f"adhd:session_start:{user_id}")
            if session_start_str:
                session_start = datetime.fromisoformat(session_start_str)
                delta = datetime.now(timezone.utc) - session_start
                return int(delta.total_seconds() / 60)

            # Fallback: if user is in profiles, they are technically active
            return 0
        except Exception as e:
            logger.error(f"Error getting session duration for {user_id}: {e}")
            return 0

    async def _get_tasks_completed(self, user_id: str) -> int:
        """Get number of tasks completed today."""
        try:
            if self.activity_tracker:
                stats = await self.activity_tracker.get_daily_stats(user_id)
                return stats.get("completed", 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting completed tasks for {user_id}: {e}")
            return 0

    async def _get_total_tasks(self, user_id: str) -> int:
        """Get total number of tasks assigned/tracked for today."""
        try:
            if self.activity_tracker:
                stats = await self.activity_tracker.get_daily_stats(user_id)
                return stats.get("total", 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting total tasks for {user_id}: {e}")
            return 0

    async def _broadcast_state_update(self, user_id: str, change_type: str = "state_update"):
        """
        Broadcast state update to WebSocket clients.
        
        Part of Dashboard Day 7 - WebSocket Streaming Implementation.
        """
        try:
            # Import here to avoid circular dependency
            from api.websocket import manager
            
            # Get current state
            energy_level = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
            energy_str = energy_level.value if hasattr(energy_level, 'value') else str(energy_level)
            
            attention_state = self.current_attention_states.get(user_id, AttentionState.FOCUSED)
            attention_str = attention_state.value if hasattr(attention_state, 'value') else str(attention_state)
            
            cognitive_load = await self._calculate_cognitive_load(user_id)
            session_duration = await self._get_session_duration(user_id)
            tasks_completed = await self._get_tasks_completed(user_id)
            
            # Broadcast to all connected clients for this user
            await manager.broadcast(
                message={
                    "type": "state_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "change_type": change_type,
                    "data": {
                        "energy_level": energy_str,
                        "attention_state": attention_str,
                        "cognitive_load": cognitive_load,
                        "session_duration_minutes": session_duration,
                        "tasks_completed_today": tasks_completed,
                        "timestamp": datetime.utcnow().isoformat(),
                        "recommendation": self.active_accommodations.get(user_id, [AccommodationRecommendation(message="Continue current workflow", urgency="low", accommodation_type="none", suggested_actions=[])])[0].message if self.active_accommodations.get(user_id) else "Continue current workflow"
                    }
                },
                user_id=user_id
            )
            
            logger.debug(f"📡 Broadcast {change_type} to WebSocket clients for {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error broadcasting state update: {e}")

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
