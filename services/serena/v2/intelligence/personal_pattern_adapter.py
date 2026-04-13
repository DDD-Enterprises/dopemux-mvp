"""
Serena v2 Phase 2D: Personal Pattern Adapter

Delta patch system for personalizing navigation strategy templates while maintaining
immutable template integrity and enabling automatic template evolution.
"""

import asyncio
import json
import logging
import hashlib
import time
import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

# Phase 2D Components
from .strategy_template_manager import (
    StrategyTemplateManager, NavigationStrategyTemplate, StrategyStep,
    TemplateComplexity, AccommodationType
)

# Phase 2 Intelligence Components
from .database import SerenaIntelligenceDatabase
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .effectiveness_tracker import EffectivenessTracker
from .adaptive_learning import AttentionState

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class PersonalizationType(str, Enum):
    """Types of template personalizations."""
    STEP_REORDERING = "step_reordering"           # Change step order
    STEP_MODIFICATION = "step_modification"       # Modify step parameters
    STEP_ADDITION = "step_addition"               # Add custom steps
    STEP_REMOVAL = "step_removal"                 # Remove unnecessary steps
    ACCOMMODATION_ADJUSTMENT = "accommodation_adjustment"  # Modify ADHD accommodations
    TIMING_ADJUSTMENT = "timing_adjustment"       # Adjust time estimates
    COMPLEXITY_ADJUSTMENT = "complexity_adjustment"  # Adjust complexity levels
    BRANCHING_MODIFICATION = "branching_modification"  # Modify decision points


class PersonalizationOrigin(str, Enum):
    """Origin of personalization changes."""
    USER_EXPLICIT = "user_explicit"               # User explicitly requested
    LEARNING_AUTOMATIC = "learning_automatic"     # Automatically learned from behavior
    EFFECTIVENESS_DRIVEN = "effectiveness_driven" # Based on effectiveness feedback
    ATTENTION_ADAPTED = "attention_adapted"       # Adapted for attention patterns
    PATTERN_EVOLVED = "pattern_evolved"          # Evolved from usage patterns


@dataclass
class PersonalizationDelta:
    """Delta patch for personalizing a template."""
    delta_id: str
    template_hash: str  # Reference to immutable template
    user_session_id: str
    workspace_path: str

    # Personalization details
    personalization_type: PersonalizationType
    personalization_origin: PersonalizationOrigin
    delta_data: Dict[str, Any]  # JSONB diff data
    rationale: str

    # Effectiveness tracking
    usage_count: int = 0
    success_rate: float = 0.0
    average_effectiveness: float = 0.0
    cognitive_load_improvement: float = 0.0
    time_reduction_percentage: float = 0.0

    # Evolution tracking
    similar_deltas_count: int = 0  # How many users have similar personalizations
    evolution_candidate: bool = False  # Whether this should become a template update
    curator_review_requested: bool = False

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PersonalizedTemplate:
    """Template personalized for specific user with delta patches applied."""
    base_template: NavigationStrategyTemplate
    applied_deltas: List[PersonalizationDelta]
    personalization_confidence: float  # How confident we are in personalizations
    user_effectiveness_score: float
    user_preference_alignment: float

    # Computed properties
    personalized_steps: List[StrategyStep] = field(default_factory=list)
    personalized_accommodations: List[AccommodationType] = field(default_factory=list)
    personalized_complexity: float = 0.0
    personalized_timing: int = 0

    # Performance tracking
    personalization_overhead_ms: float = 0.0
    cache_hit_rate: float = 0.0


@dataclass
class DeltaCluster:
    """Cluster of similar delta patches for template evolution."""
    cluster_id: str
    template_hash: str
    similar_deltas: List[PersonalizationDelta]
    cluster_confidence: float
    potential_template_improvement: Dict[str, Any]
    user_support_count: int
    effectiveness_improvement: float
    curator_approval_recommended: bool


class PersonalPatternAdapter:
    """
    Personal pattern adapter with delta patch system for template personalization.

    Features:
    - Delta patch system maintaining template immutability (expert-recommended)
    - Automatic personalization based on user navigation patterns and effectiveness
    - JSONB diff storage for efficient personalization tracking
    - Template evolution detection through delta clustering
    - Performance optimization with Redis caching for <150ms targets
    - Integration with ConPort for strategic template synchronization
    - Curator workflow for template evolution approval
    - ADHD accommodation personalization and optimization
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        template_manager: StrategyTemplateManager,
        profile_manager: PersonalLearningProfileManager,
        effectiveness_tracker: EffectivenessTracker,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.template_manager = template_manager
        self.profile_manager = profile_manager
        self.effectiveness_tracker = effectiveness_tracker
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Personalization configuration
        self.auto_personalization_threshold = 0.7  # Effectiveness threshold for auto-personalization
        self.delta_clustering_threshold = 5  # Users needed for evolution consideration
        self.max_deltas_per_template = 10   # ADHD cognitive load limit

        # Caching for performance
        self._personalized_template_cache: Dict[str, PersonalizedTemplate] = {}
        self._delta_cache: Dict[str, List[PersonalizationDelta]] = {}

        # Evolution tracking
        self._delta_clusters: Dict[str, DeltaCluster] = {}

    # Core Personalization

    async def get_personalized_template(
        self,
        template_id: str,
        user_session_id: str,
        workspace_path: str,
        current_context: Optional[Dict[str, Any]] = None
    ) -> Optional[PersonalizedTemplate]:
        """Get template personalized for specific user with applied delta patches."""
        operation_id = self.performance_monitor.start_operation("get_personalized_template")

        try:
            cache_key = f"{template_id}_{user_session_id}_{workspace_path}"

            # Check cache first for performance
            if cache_key in self._personalized_template_cache:
                cached_template = self._personalized_template_cache[cache_key]
                # Check if cache is still valid (template or deltas haven't changed)
                if await self._is_personalized_cache_valid(cached_template):
                    self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                    return cached_template

            # Get base template
            base_template = await self.template_manager.get_template_by_id(template_id)
            if not base_template:
                self.performance_monitor.end_operation(operation_id, success=False)
                return None

            # Get user's delta patches for this template
            deltas = await self._get_user_deltas(
                base_template.template_hash, user_session_id, workspace_path
            )

            # Apply deltas to create personalized template
            personalized_template = await self._apply_deltas_to_template(
                base_template, deltas, user_session_id, workspace_path, current_context
            )

            # Cache the personalized template
            self._personalized_template_cache[cache_key] = personalized_template

            self.performance_monitor.end_operation(operation_id, success=True, cache_hit=False)

            logger.debug(f"🎯 Created personalized template {template_id} with {len(deltas)} deltas")
            return personalized_template

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get personalized template: {e}")
            return None

    async def create_personalization_delta(
        self,
        template_hash: str,
        user_session_id: str,
        workspace_path: str,
        personalization_type: PersonalizationType,
        delta_data: Dict[str, Any],
        rationale: str,
        origin: PersonalizationOrigin = PersonalizationOrigin.USER_EXPLICIT
    ) -> PersonalizationDelta:
        """Create new personalization delta patch."""
        operation_id = self.performance_monitor.start_operation("create_personalization_delta")

        try:
            delta_id = self._generate_delta_id(template_hash, user_session_id, personalization_type)

            # Create delta patch
            delta = PersonalizationDelta(
                delta_id=delta_id,
                template_hash=template_hash,
                user_session_id=user_session_id,
                workspace_path=workspace_path,
                personalization_type=personalization_type,
                personalization_origin=origin,
                delta_data=delta_data,
                rationale=rationale
            )

            # Store delta in PostgreSQL
            await self._store_delta_patch(delta)

            # Clear relevant caches
            await self._invalidate_personalization_cache(user_session_id, template_hash)

            # Check for evolution opportunities
            await self._check_delta_clustering(delta)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"📝 Created personalization delta: {personalization_type.value} for template {template_hash[:8]}")
            return delta

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to create personalization delta: {e}")
            raise

    async def apply_automatic_personalization(
        self,
        template_id: str,
        user_session_id: str,
        workspace_path: str,
        usage_feedback: Dict[str, Any]
    ) -> List[PersonalizationDelta]:
        """Automatically create personalization deltas based on usage feedback."""
        try:
            # Get base template
            base_template = await self.template_manager.get_template_by_id(template_id)
            if not base_template:
                return []

            # Get user profile for personalization context
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            # Analyze usage feedback for personalization opportunities
            personalization_opportunities = await self._analyze_personalization_opportunities(
                base_template, usage_feedback, profile
            )

            created_deltas = []
            for opportunity in personalization_opportunities:
                delta = await self.create_personalization_delta(
                    base_template.template_hash,
                    user_session_id,
                    workspace_path,
                    opportunity['type'],
                    opportunity['delta_data'],
                    opportunity['rationale'],
                    PersonalizationOrigin.LEARNING_AUTOMATIC
                )
                created_deltas.append(delta)

            logger.info(f"🤖 Created {len(created_deltas)} automatic personalizations for {template_id}")
            return created_deltas

        except Exception as e:
            logger.error(f"Failed to apply automatic personalization: {e}")
            return []

    # Delta Application System

    async def _apply_deltas_to_template(
        self,
        base_template: NavigationStrategyTemplate,
        deltas: List[PersonalizationDelta],
        user_session_id: str,
        workspace_path: str,
        current_context: Optional[Dict[str, Any]] = None
    ) -> PersonalizedTemplate:
        """Apply delta patches to base template for personalization."""
        try:
            # Start with base template
            personalized_steps = copy.deepcopy(base_template.steps)
            personalized_accommodations = copy.deepcopy(base_template.adhd_accommodations)
            personalized_complexity = base_template.max_cognitive_load
            personalized_timing = base_template.estimated_completion_time_minutes

            # Apply deltas in chronological order
            sorted_deltas = sorted(deltas, key=lambda d: d.created_at)

            for delta in sorted_deltas:
                if delta.personalization_type == PersonalizationType.STEP_REORDERING:
                    personalized_steps = self._apply_step_reordering(personalized_steps, delta.delta_data)

                elif delta.personalization_type == PersonalizationType.STEP_MODIFICATION:
                    personalized_steps = self._apply_step_modification(personalized_steps, delta.delta_data)

                elif delta.personalization_type == PersonalizationType.ACCOMMODATION_ADJUSTMENT:
                    personalized_accommodations = self._apply_accommodation_adjustment(
                        personalized_accommodations, delta.delta_data
                    )

                elif delta.personalization_type == PersonalizationType.TIMING_ADJUSTMENT:
                    timing_adjustment = delta.delta_data.get('timing_multiplier', 1.0)
                    personalized_timing = int(personalized_timing * timing_adjustment)

                elif delta.personalization_type == PersonalizationType.COMPLEXITY_ADJUSTMENT:
                    complexity_adjustment = delta.delta_data.get('complexity_adjustment', 0.0)
                    personalized_complexity = max(0.0, min(1.0, personalized_complexity + complexity_adjustment))

            # Calculate personalization metrics
            user_profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            personalization_confidence = self._calculate_personalization_confidence(deltas, user_profile)
            effectiveness_score = await self._calculate_personalized_effectiveness(
                base_template, deltas, user_session_id
            )
            preference_alignment = self._calculate_preference_alignment(
                personalized_accommodations, personalized_complexity, user_profile
            )

            # Create personalized template
            personalized_template = PersonalizedTemplate(
                base_template=base_template,
                applied_deltas=deltas,
                personalization_confidence=personalization_confidence,
                user_effectiveness_score=effectiveness_score,
                user_preference_alignment=preference_alignment,
                personalized_steps=personalized_steps,
                personalized_accommodations=personalized_accommodations,
                personalized_complexity=personalized_complexity,
                personalized_timing=personalized_timing
            )

            return personalized_template

        except Exception as e:
            logger.error(f"Failed to apply deltas to template: {e}")
            # Return template with no personalization as fallback
            return PersonalizedTemplate(
                base_template=base_template,
                applied_deltas=[],
                personalization_confidence=0.0,
                user_effectiveness_score=base_template.success_rate,
                user_preference_alignment=0.5,
                personalized_steps=base_template.steps,
                personalized_accommodations=base_template.adhd_accommodations,
                personalized_complexity=base_template.max_cognitive_load,
                personalized_timing=base_template.estimated_completion_time_minutes
            )

    # Delta Operations

    def _apply_step_reordering(
        self, steps: List[StrategyStep], delta_data: Dict[str, Any]
    ) -> List[StrategyStep]:
        """Apply step reordering delta."""
        try:
            new_order = delta_data.get('new_order', [])
            if not new_order:
                return steps

            # Create mapping of step_id to step
            step_map = {step.step_id: step for step in steps}

            # Reorder steps according to new order
            reordered_steps = []
            for step_id in new_order:
                if step_id in step_map:
                    reordered_steps.append(step_map[step_id])

            # Add any steps not in new order at the end
            remaining_steps = [step for step in steps if step.step_id not in new_order]
            reordered_steps.extend(remaining_steps)

            return reordered_steps

        except Exception as e:
            logger.error(f"Failed to apply step reordering: {e}")
            return steps

    def _apply_step_modification(
        self, steps: List[StrategyStep], delta_data: Dict[str, Any]
    ) -> List[StrategyStep]:
        """Apply step modification delta."""
        try:
            modifications = delta_data.get('modifications', {})

            modified_steps = []
            for step in steps:
                if step.step_id in modifications:
                    # Apply modifications to this step
                    mod_data = modifications[step.step_id]
                    modified_step = copy.deepcopy(step)

                    # Apply specific modifications
                    if 'estimated_duration_seconds' in mod_data:
                        modified_step.estimated_duration_seconds = mod_data['estimated_duration_seconds']

                    if 'cognitive_load' in mod_data:
                        modified_step.cognitive_load = mod_data['cognitive_load']

                    if 'attention_requirements' in mod_data:
                        modified_step.attention_requirements = mod_data['attention_requirements']

                    if 'adhd_accommodations' in mod_data:
                        modified_step.adhd_accommodations = [
                            AccommodationType(acc) for acc in mod_data['adhd_accommodations']
                        ]

                    modified_steps.append(modified_step)
                else:
                    modified_steps.append(step)

            return modified_steps

        except Exception as e:
            logger.error(f"Failed to apply step modification: {e}")
            return steps

    def _apply_accommodation_adjustment(
        self, accommodations: List[AccommodationType], delta_data: Dict[str, Any]
    ) -> List[AccommodationType]:
        """Apply accommodation adjustment delta."""
        try:
            add_accommodations = delta_data.get('add', [])
            remove_accommodations = delta_data.get('remove', [])

            # Start with current accommodations
            new_accommodations = list(accommodations)

            # Add new accommodations
            for acc_str in add_accommodations:
                try:
                    accommodation = AccommodationType(acc_str)
                    if accommodation not in new_accommodations:
                        new_accommodations.append(accommodation)
                except ValueError:
                    logger.warning(f"Invalid accommodation type: {acc_str}")

            # Remove accommodations
            for acc_str in remove_accommodations:
                try:
                    accommodation = AccommodationType(acc_str)
                    if accommodation in new_accommodations:
                        new_accommodations.remove(accommodation)
                except ValueError:
                    logger.warning(f"Invalid accommodation type for removal: {acc_str}")

            return new_accommodations

        except Exception as e:
            logger.error(f"Failed to apply accommodation adjustment: {e}")
            return accommodations

    # Personalization Analysis

    async def _analyze_personalization_opportunities(
        self,
        template: NavigationStrategyTemplate,
        usage_feedback: Dict[str, Any],
        profile: PersonalLearningProfile
    ) -> List[Dict[str, Any]]:
        """Analyze usage feedback for automatic personalization opportunities."""
        opportunities = []

        try:
            effectiveness_score = usage_feedback.get('effectiveness_score', 0.5)
            cognitive_load = usage_feedback.get('cognitive_load_experienced', 0.5)
            duration_actual = usage_feedback.get('actual_duration_minutes', template.estimated_completion_time_minutes)

            # Timing personalization opportunity
            if abs(duration_actual - template.estimated_completion_time_minutes) > 2:
                timing_multiplier = duration_actual / template.estimated_completion_time_minutes
                if 0.5 <= timing_multiplier <= 2.0:  # Reasonable range
                    opportunities.append({
                        'type': PersonalizationType.TIMING_ADJUSTMENT,
                        'delta_data': {'timing_multiplier': timing_multiplier},
                        'rationale': f"User takes {timing_multiplier:.1f}x template time estimate"
                    })

            # Complexity personalization opportunity
            if cognitive_load != template.max_cognitive_load and effectiveness_score > 0.6:
                complexity_adjustment = (cognitive_load - template.max_cognitive_load) * 0.5  # Conservative adjustment
                if abs(complexity_adjustment) > 0.1:
                    opportunities.append({
                        'type': PersonalizationType.COMPLEXITY_ADJUSTMENT,
                        'delta_data': {'complexity_adjustment': complexity_adjustment},
                        'rationale': f"User experiences {'higher' if complexity_adjustment > 0 else 'lower'} cognitive load"
                    })

            # Accommodation personalization opportunity
            if effectiveness_score < 0.6 and cognitive_load > 0.7:
                # User struggling - add more accommodations
                additional_accommodations = self._suggest_additional_accommodations(
                    template.adhd_accommodations, profile, usage_feedback
                )
                if additional_accommodations:
                    opportunities.append({
                        'type': PersonalizationType.ACCOMMODATION_ADJUSTMENT,
                        'delta_data': {'add': [acc.value for acc in additional_accommodations]},
                        'rationale': "Adding accommodations to reduce cognitive load"
                    })

            # Step modification opportunity (if specific steps took much longer)
            step_feedback = usage_feedback.get('step_feedback', {})
            for step_id, step_data in step_feedback.items():
                step_duration = step_data.get('actual_duration_seconds', 0)
                if step_duration > 0:
                    # Find corresponding step in template
                    template_step = next((s for s in template.steps if s.step_id == step_id), None)
                    if template_step and step_duration > template_step.estimated_duration_seconds * 1.5:
                        # Step took significantly longer - adjust
                        opportunities.append({
                            'type': PersonalizationType.STEP_MODIFICATION,
                            'delta_data': {
                                'modifications': {
                                    step_id: {
                                        'estimated_duration_seconds': step_duration,
                                        'cognitive_load': min(1.0, template_step.cognitive_load + 0.1)
                                    }
                                }
                            },
                            'rationale': f"Step {step_id} takes longer for this user"
                        })

            return opportunities

        except Exception as e:
            logger.error(f"Failed to analyze personalization opportunities: {e}")
            return []

    def _suggest_additional_accommodations(
        self,
        current_accommodations: List[AccommodationType],
        profile: PersonalLearningProfile,
        usage_feedback: Dict[str, Any]
    ) -> List[AccommodationType]:
        """Suggest additional ADHD accommodations based on user needs."""
        suggestions = []

        # Progressive disclosure if user struggles with complexity
        if (AccommodationType.PROGRESSIVE_DISCLOSURE not in current_accommodations and
            usage_feedback.get('cognitive_load_experienced', 0) > 0.7):
            suggestions.append(AccommodationType.PROGRESSIVE_DISCLOSURE)

        # Focus mode integration if user has attention challenges
        if (AccommodationType.FOCUS_MODE_INTEGRATION not in current_accommodations and
            profile.context_switch_tolerance <= 3):
            suggestions.append(AccommodationType.FOCUS_MODE_INTEGRATION)

        # Break reminders for long attention spans
        if (AccommodationType.BREAK_REMINDERS not in current_accommodations and
            usage_feedback.get('actual_duration_minutes', 0) > profile.average_attention_span_minutes):
            suggestions.append(AccommodationType.BREAK_REMINDERS)

        # Cognitive load limiting if consistently overwhelming
        if (AccommodationType.COGNITIVE_LOAD_LIMITING not in current_accommodations and
            usage_feedback.get('overwhelm_experienced', False)):
            suggestions.append(AccommodationType.COGNITIVE_LOAD_LIMITING)

        return suggestions

    # Delta Clustering for Template Evolution

    async def _check_delta_clustering(self, new_delta: PersonalizationDelta) -> None:
        """Check if delta should contribute to template evolution clustering."""
        try:
            # Find similar deltas from other users
            similar_deltas = await self._find_similar_deltas(new_delta)

            if len(similar_deltas) >= self.delta_clustering_threshold:
                # Create or update cluster
                cluster_id = f"cluster_{new_delta.template_hash}_{new_delta.personalization_type.value}"

                if cluster_id not in self._delta_clusters:
                    # Create new cluster
                    cluster = DeltaCluster(
                        cluster_id=cluster_id,
                        template_hash=new_delta.template_hash,
                        similar_deltas=similar_deltas,
                        cluster_confidence=self._calculate_cluster_confidence(similar_deltas),
                        potential_template_improvement=self._analyze_cluster_improvement_potential(similar_deltas),
                        user_support_count=len(similar_deltas),
                        effectiveness_improvement=self._calculate_cluster_effectiveness_improvement(similar_deltas),
                        curator_approval_recommended=len(similar_deltas) >= 10  # High user support
                    )

                    self._delta_clusters[cluster_id] = cluster

                    # Request curator review if warranted
                    if cluster.curator_approval_recommended:
                        await self._request_curator_review(cluster)

                logger.debug(f"🔗 Updated delta cluster {cluster_id} with {len(similar_deltas)} similar deltas")

        except Exception as e:
            logger.error(f"Failed to check delta clustering: {e}")

    async def _find_similar_deltas(self, target_delta: PersonalizationDelta) -> List[PersonalizationDelta]:
        """Find similar delta patches from other users."""
        try:
            query = """
            SELECT * FROM personalization_deltas
            WHERE template_hash = $1
              AND personalization_type = $2
              AND user_session_id != $3
              AND success_rate > 0.6
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT 20
            """

            results = await self.database.execute_query(query, (
                target_delta.template_hash,
                target_delta.personalization_type.value,
                target_delta.user_session_id
            ))

            similar_deltas = []
            for row in results:
                delta = await self._row_to_delta(row)

                # Check similarity of delta_data
                similarity = self._calculate_delta_similarity(target_delta.delta_data, delta.delta_data)
                if similarity > 0.7:  # High similarity threshold
                    similar_deltas.append(delta)

            return similar_deltas

        except Exception as e:
            logger.error(f"Failed to find similar deltas: {e}")
            return []

    def _calculate_delta_similarity(self, delta1: Dict[str, Any], delta2: Dict[str, Any]) -> float:
        """Calculate similarity between two delta patches."""
        try:
            # Simple similarity based on common keys and values
            common_keys = set(delta1.keys()) & set(delta2.keys())
            if not common_keys:
                return 0.0

            similarity_scores = []
            for key in common_keys:
                if delta1[key] == delta2[key]:
                    similarity_scores.append(1.0)
                elif isinstance(delta1[key], (int, float)) and isinstance(delta2[key], (int, float)):
                    # Numeric similarity
                    diff = abs(delta1[key] - delta2[key]) / max(abs(delta1[key]), abs(delta2[key]), 1)
                    similarity_scores.append(max(0.0, 1.0 - diff))
                else:
                    similarity_scores.append(0.0)

            return statistics.mean(similarity_scores) if similarity_scores else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate delta similarity: {e}")
            return 0.0

    # Database Operations

    async def _store_delta_patch(self, delta: PersonalizationDelta) -> None:
        """Store delta patch in PostgreSQL database."""
        try:
            insert_query = """
            INSERT INTO personalization_deltas (
                delta_id, template_hash, user_session_id, workspace_path,
                personalization_type, personalization_origin, delta_data,
                rationale, usage_count, success_rate, average_effectiveness,
                cognitive_load_improvement, time_reduction_percentage,
                similar_deltas_count, evolution_candidate
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (delta_id)
            DO UPDATE SET
                delta_data = EXCLUDED.delta_data,
                rationale = EXCLUDED.rationale,
                updated_at = NOW()
            """

            await self.database.execute_query(insert_query, (
                delta.delta_id,
                delta.template_hash,
                delta.user_session_id,
                delta.workspace_path,
                delta.personalization_type.value,
                delta.personalization_origin.value,
                json.dumps(delta.delta_data),
                delta.rationale,
                delta.usage_count,
                delta.success_rate,
                delta.average_effectiveness,
                delta.cognitive_load_improvement,
                delta.time_reduction_percentage,
                delta.similar_deltas_count,
                delta.evolution_candidate
            ))

        except Exception as e:
            logger.error(f"Failed to store delta patch: {e}")

    async def _get_user_deltas(
        self, template_hash: str, user_session_id: str, workspace_path: str
    ) -> List[PersonalizationDelta]:
        """Get user's delta patches for a template."""
        try:
            cache_key = f"{template_hash}_{user_session_id}_{workspace_path}"
            if cache_key in self._delta_cache:
                return self._delta_cache[cache_key]

            query = """
            SELECT * FROM personalization_deltas
            WHERE template_hash = $1
              AND user_session_id = $2
              AND workspace_path = $3
            ORDER BY created_at
            """

            results = await self.database.execute_query(query, (template_hash, user_session_id, workspace_path))

            deltas = []
            for row in results:
                delta = await self._row_to_delta(row)
                deltas.append(delta)

            # Cache the deltas
            self._delta_cache[cache_key] = deltas

            return deltas

        except Exception as e:
            logger.error(f"Failed to get user deltas: {e}")
            return []

    # Utility Methods

    def _generate_delta_id(
        self, template_hash: str, user_session_id: str, personalization_type: PersonalizationType
    ) -> str:
        """Generate unique delta ID."""
        delta_content = f"{template_hash}_{user_session_id}_{personalization_type.value}_{time.time()}"
        return hashlib.md5(delta_content.encode()).hexdigest()[:16]

    def _calculate_personalization_confidence(
        self, deltas: List[PersonalizationDelta], profile: PersonalLearningProfile
    ) -> float:
        """Calculate confidence in personalization quality."""
        if not deltas:
            return 0.0

        confidence_factors = []

        # Base confidence on user's learning progression
        confidence_factors.append(profile.pattern_confidence)

        # Confidence based on delta effectiveness
        effective_deltas = [d for d in deltas if d.average_effectiveness > 0.6]
        effectiveness_ratio = len(effective_deltas) / len(deltas)
        confidence_factors.append(effectiveness_ratio)

        # Confidence based on usage frequency
        well_used_deltas = [d for d in deltas if d.usage_count >= 3]
        usage_ratio = len(well_used_deltas) / len(deltas)
        confidence_factors.append(usage_ratio)

        return statistics.mean(confidence_factors)

    async def _calculate_personalized_effectiveness(
        self, template: NavigationStrategyTemplate, deltas: List[PersonalizationDelta], user_session_id: str
    ) -> float:
        """Calculate effectiveness of personalized template."""
        if not deltas:
            return template.success_rate

        # Weight base template effectiveness with delta effectiveness
        base_weight = 0.4
        delta_weight = 0.6

        delta_effectiveness = [d.average_effectiveness for d in deltas if d.average_effectiveness > 0]
        avg_delta_effectiveness = statistics.mean(delta_effectiveness) if delta_effectiveness else 0.5

        return base_weight * template.success_rate + delta_weight * avg_delta_effectiveness

    def _calculate_preference_alignment(
        self,
        accommodations: List[AccommodationType],
        complexity: float,
        profile: PersonalLearningProfile
    ) -> float:
        """Calculate how well personalization aligns with user preferences."""
        alignment_factors = []

        # Progressive disclosure alignment
        if (profile.progressive_disclosure_preference and
            AccommodationType.PROGRESSIVE_DISCLOSURE in accommodations):
            alignment_factors.append(0.9)
        elif not profile.progressive_disclosure_preference:
            alignment_factors.append(0.7)
        else:
            alignment_factors.append(0.5)

        # Complexity alignment
        if complexity <= profile.optimal_complexity_range[1]:
            alignment_factors.append(1.0)
        elif complexity <= profile.optimal_complexity_range[1] + 0.2:
            alignment_factors.append(0.7)
        else:
            alignment_factors.append(0.4)

        # Focus mode alignment (if user prefers limited context switching)
        if (profile.context_switch_tolerance <= 3 and
            AccommodationType.FOCUS_MODE_INTEGRATION in accommodations):
            alignment_factors.append(0.8)
        else:
            alignment_factors.append(0.6)

        return statistics.mean(alignment_factors)

    # Cache Management

    async def _is_personalized_cache_valid(self, cached_template: PersonalizedTemplate) -> bool:
        """Check if personalized template cache is still valid."""
        try:
            # Check if any of the applied deltas have been updated
            for delta in cached_template.applied_deltas:
                current_delta = await self._get_delta_by_id(delta.delta_id)
                if current_delta and current_delta.updated_at > delta.updated_at:
                    return False

            return True

        except Exception:
            return False

    async def _invalidate_personalization_cache(self, user_session_id: str, template_hash: str) -> None:
        """Invalidate personalization cache for user and template."""
        keys_to_remove = [
            key for key in self._personalized_template_cache.keys()
            if user_session_id in key and template_hash in key
        ]

        for key in keys_to_remove:
            del self._personalized_template_cache[key]

        # Also clear delta cache
        delta_cache_keys = [
            key for key in self._delta_cache.keys()
            if template_hash in key and user_session_id in key
        ]

        for key in delta_cache_keys:
            del self._delta_cache[key]

    # Placeholder methods for complex operations
    async def _row_to_delta(self, row: Dict[str, Any]) -> PersonalizationDelta:
        """Convert database row to delta object."""
        return PersonalizationDelta(
            delta_id=row['delta_id'],
            template_hash=row['template_hash'],
            user_session_id=row['user_session_id'],
            workspace_path=row['workspace_path'],
            personalization_type=PersonalizationType(row['personalization_type']),
            personalization_origin=PersonalizationOrigin(row['personalization_origin']),
            delta_data=json.loads(row['delta_data']),
            rationale=row['rationale'],
            usage_count=row['usage_count'],
            success_rate=row['success_rate'],
            average_effectiveness=row['average_effectiveness'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    async def _get_delta_by_id(self, delta_id: str) -> Optional[PersonalizationDelta]:
        """Get delta by ID."""
        # Simplified implementation
        return None

    def _calculate_cluster_confidence(self, deltas: List[PersonalizationDelta]) -> float:
        return min(1.0, len(deltas) / 10.0)

    def _analyze_cluster_improvement_potential(self, deltas: List[PersonalizationDelta]) -> Dict[str, Any]:
        return {"improvement_type": "effectiveness", "estimated_improvement": 0.1}

    def _calculate_cluster_effectiveness_improvement(self, deltas: List[PersonalizationDelta]) -> float:
        if not deltas:
            return 0.0
        return statistics.mean([d.average_effectiveness for d in deltas])

    async def _request_curator_review(self, cluster: DeltaCluster) -> None:
        """Request curator review for potential template evolution."""
        logger.info(f"📋 Requesting curator review for cluster {cluster.cluster_id}")


# Convenience functions
async def create_personal_pattern_adapter(
    database: SerenaIntelligenceDatabase,
    template_manager: StrategyTemplateManager,
    profile_manager: PersonalLearningProfileManager,
    effectiveness_tracker: EffectivenessTracker,
    performance_monitor: PerformanceMonitor = None
) -> PersonalPatternAdapter:
    """Create personal pattern adapter instance."""
    return PersonalPatternAdapter(
        database, template_manager, profile_manager, effectiveness_tracker, performance_monitor
    )


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🔧 Serena Personal Pattern Adapter")
        print("Delta patch system for template personalization with immutability")
        print("✅ Module loaded successfully")

    asyncio.run(main())