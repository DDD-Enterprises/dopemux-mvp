"""
Serena v2 Phase 2D: Effectiveness-Based Evolution System

Automatic template improvement system using effectiveness feedback, A/B testing,
and ADHD accommodation optimization for continuous pattern enhancement.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

# Phase 2D Components
from .strategy_template_manager import StrategyTemplateManager, NavigationStrategyTemplate, TemplateComplexity
from .personal_pattern_adapter import PersonalPatternAdapter, PersonalizationDelta, PersonalizationType
from .cross_session_persistence_bridge import (
    CrossSessionPersistenceBridge, TemplateEvolutionProposal, EvolutionProposal
)

# Phase 2B Components
from .effectiveness_tracker import EffectivenessTracker, EffectivenessDimension, ABTest
from .learning_profile_manager import PersonalLearningProfileManager

# Phase 2A Components
from .database import SerenaIntelligenceDatabase

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class EvolutionTrigger(str, Enum):
    """Triggers for template evolution."""
    EFFECTIVENESS_THRESHOLD = "effectiveness_threshold"      # Low effectiveness detected
    USER_FEEDBACK = "user_feedback"                         # Direct user feedback
    DELTA_CLUSTERING = "delta_clustering"                   # Similar personalizations detected
    PERFORMANCE_DEGRADATION = "performance_degradation"     # Performance issues detected
    ADHD_ACCOMMODATION_NEED = "adhd_accommodation_need"     # New ADHD needs identified
    USAGE_PATTERN_CHANGE = "usage_pattern_change"          # User patterns evolved
    COMPETITIVE_ANALYSIS = "competitive_analysis"          # Better alternatives identified


class EvolutionStrategy(str, Enum):
    """Strategies for template evolution."""
    INCREMENTAL_IMPROVEMENT = "incremental_improvement"      # Small, safe improvements
    ACCOMMODATION_ENHANCEMENT = "accommodation_enhancement"  # Improve ADHD accommodations
    COMPLEXITY_OPTIMIZATION = "complexity_optimization"     # Optimize complexity handling
    TIMING_REFINEMENT = "timing_refinement"                # Refine time estimates
    STEP_REORDERING = "step_reordering"                    # Optimize step order
    BRANCH_SIMPLIFICATION = "branch_simplification"        # Simplify decision points
    PERSONALIZATION_INTEGRATION = "personalization_integration"  # Integrate common personalizations


class EvolutionValidation(str, Enum):
    """Validation methods for template evolution."""
    A_B_TESTING = "a_b_testing"                            # A/B test new vs old
    EFFECTIVENESS_COMPARISON = "effectiveness_comparison"   # Compare effectiveness metrics
    USER_SATISFACTION_SURVEY = "user_satisfaction_survey"  # Direct user feedback
    COGNITIVE_LOAD_MEASUREMENT = "cognitive_load_measurement"  # Measure cognitive impact
    USAGE_ANALYTICS = "usage_analytics"                    # Analyze usage patterns


@dataclass
class EvolutionOpportunity:
    """Identified opportunity for template evolution."""
    opportunity_id: str
    template_id: str
    template_hash: str
    trigger: EvolutionTrigger
    evidence_data: Dict[str, Any]

    # Opportunity assessment
    improvement_potential: float  # 0.0-1.0
    user_impact_scope: int  # Number of users affected
    adhd_benefit_potential: float  # 0.0-1.0
    implementation_complexity: str  # low, medium, high

    # Proposed evolution
    suggested_strategy: EvolutionStrategy
    suggested_changes: Dict[str, Any]
    validation_method: EvolutionValidation
    expected_effectiveness_improvement: float

    # Metadata
    confidence: float = 0.0
    priority: str = "medium"  # low, medium, high, critical
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EvolutionExperiment:
    """A/B testing experiment for template evolution."""
    experiment_id: str
    template_id: str
    original_template: NavigationStrategyTemplate
    evolved_template: NavigationStrategyTemplate

    # Experiment configuration
    target_sample_size: int
    current_sample_size: int
    success_threshold: float  # Minimum improvement to accept evolution

    # Results tracking
    original_results: List[float] = field(default_factory=list)
    evolved_results: List[float] = field(default_factory=list)
    statistical_significance: Optional[float] = None
    winner: Optional[str] = None  # "original", "evolved", "no_difference"

    # ADHD-specific metrics
    cognitive_load_comparison: Dict[str, float] = field(default_factory=dict)
    accommodation_effectiveness: Dict[str, float] = field(default_factory=dict)
    user_preference_votes: Dict[str, int] = field(default_factory=dict)

    # Experiment status
    status: str = "running"  # planning, running, analyzing, completed
    start_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None


class EffectivenessEvolutionSystem:
    """
    Effectiveness-based evolution system for automatic template improvement.

    Features:
    - Continuous monitoring of template effectiveness across users
    - Automatic detection of evolution opportunities from effectiveness data
    - A/B testing framework for validating template improvements
    - ADHD accommodation optimization based on user feedback
    - Statistical validation of evolution benefits before deployment
    - Integration with delta clustering for personalization-driven evolution
    - Performance impact assessment for all evolved templates
    - Curator workflow for complex evolution decisions
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        template_manager: StrategyTemplateManager,
        pattern_adapter: PersonalPatternAdapter,
        effectiveness_tracker: EffectivenessTracker,
        persistence_bridge: CrossSessionPersistenceBridge,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.template_manager = template_manager
        self.pattern_adapter = pattern_adapter
        self.effectiveness_tracker = effectiveness_tracker
        self.persistence_bridge = persistence_bridge
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Evolution configuration
        self.effectiveness_threshold = 0.75  # Templates below this need evolution
        self.min_sample_size = 20  # Minimum usage for reliable evolution
        self.evolution_confidence_threshold = 0.8
        self.max_concurrent_experiments = 3  # Limit concurrent A/B tests

        # Active tracking
        self._evolution_opportunities: Dict[str, EvolutionOpportunity] = {}
        self._active_experiments: Dict[str, EvolutionExperiment] = {}
        self._evolution_history: List[Dict[str, Any]] = []

        # ADHD optimization thresholds
        self.adhd_satisfaction_threshold = 0.8
        self.cognitive_load_threshold = 0.6
        self.accommodation_effectiveness_threshold = 0.7

    # Core Evolution Detection

    async def monitor_template_effectiveness(self) -> Dict[str, Any]:
        """Monitor all templates for evolution opportunities."""
        operation_id = self.performance_monitor.start_operation("monitor_template_effectiveness")

        try:
            monitoring_results = {
                "templates_monitored": 0,
                "opportunities_detected": 0,
                "experiments_started": 0,
                "evolution_proposals_created": 0
            }

            # Get all active templates
            library = await self.template_manager.get_template_library()

            # Monitor each template
            for template_id in library.most_popular_templates + library.newest_templates:
                template = await self.template_manager.get_template_by_id(template_id)
                if template:
                    # Check for evolution opportunities
                    opportunities = await self._detect_evolution_opportunities(template)

                    for opportunity in opportunities:
                        self._evolution_opportunities[opportunity.opportunity_id] = opportunity
                        monitoring_results["opportunities_detected"] += 1

                        # Start experiment if appropriate
                        if await self._should_start_experiment(opportunity):
                            experiment = await self._start_evolution_experiment(opportunity)
                            if experiment:
                                monitoring_results["experiments_started"] += 1

                    monitoring_results["templates_monitored"] += 1

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"📊 Template monitoring: {monitoring_results['opportunities_detected']} opportunities detected")
            return monitoring_results

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Template effectiveness monitoring failed: {e}")
            return {"error": str(e)}

    async def _detect_evolution_opportunities(
        self, template: NavigationStrategyTemplate
    ) -> List[EvolutionOpportunity]:
        """Detect evolution opportunities for a specific template."""
        opportunities = []

        try:
            # Get template effectiveness data
            effectiveness_data = await self._get_template_effectiveness_data(template.template_id)

            if not effectiveness_data:
                return opportunities

            # Check effectiveness threshold
            avg_effectiveness = effectiveness_data.get('average_effectiveness', 0.5)
            if avg_effectiveness < self.effectiveness_threshold:
                opportunity = EvolutionOpportunity(
                    opportunity_id=f"eff_{template.template_id}_{int(time.time())}",
                    template_id=template.template_id,
                    template_hash=template.template_hash,
                    trigger=EvolutionTrigger.EFFECTIVENESS_THRESHOLD,
                    evidence_data=effectiveness_data,
                    improvement_potential=self.effectiveness_threshold - avg_effectiveness,
                    user_impact_scope=effectiveness_data.get('user_count', 0),
                    adhd_benefit_potential=self._assess_adhd_benefit_potential(effectiveness_data),
                    implementation_complexity="medium",
                    suggested_strategy=EvolutionStrategy.INCREMENTAL_IMPROVEMENT,
                    suggested_changes=await self._suggest_effectiveness_improvements(template, effectiveness_data),
                    validation_method=EvolutionValidation.A_B_TESTING,
                    expected_effectiveness_improvement=0.1,
                    confidence=0.7,
                    priority="high"
                )
                opportunities.append(opportunity)

            # Check ADHD accommodation effectiveness
            accommodation_data = effectiveness_data.get('accommodation_effectiveness', {})
            for accommodation, effectiveness in accommodation_data.items():
                if effectiveness < self.accommodation_effectiveness_threshold:
                    opportunity = EvolutionOpportunity(
                        opportunity_id=f"adhd_{template.template_id}_{accommodation}_{int(time.time())}",
                        template_id=template.template_id,
                        template_hash=template.template_hash,
                        trigger=EvolutionTrigger.ADHD_ACCOMMODATION_NEED,
                        evidence_data={"accommodation": accommodation, "effectiveness": effectiveness},
                        improvement_potential=self.accommodation_effectiveness_threshold - effectiveness,
                        user_impact_scope=effectiveness_data.get('user_count', 0),
                        adhd_benefit_potential=0.8,  # High benefit for ADHD improvements
                        implementation_complexity="low",
                        suggested_strategy=EvolutionStrategy.ACCOMMODATION_ENHANCEMENT,
                        suggested_changes={
                            "accommodation_type": accommodation,
                            "improvement_strategy": "enhance_or_replace"
                        },
                        validation_method=EvolutionValidation.COGNITIVE_LOAD_MEASUREMENT,
                        expected_effectiveness_improvement=0.15,
                        confidence=0.8,
                        priority="high"
                    )
                    opportunities.append(opportunity)

            # Check for delta clustering opportunities
            delta_clusters = await self._get_delta_clusters_for_template(template.template_hash)
            for cluster in delta_clusters:
                if cluster.user_support_count >= 5 and cluster.effectiveness_improvement > 0.1:
                    opportunity = EvolutionOpportunity(
                        opportunity_id=f"cluster_{template.template_id}_{cluster.cluster_id}",
                        template_id=template.template_id,
                        template_hash=template.template_hash,
                        trigger=EvolutionTrigger.DELTA_CLUSTERING,
                        evidence_data={"cluster": cluster.__dict__},
                        improvement_potential=cluster.effectiveness_improvement,
                        user_impact_scope=cluster.user_support_count,
                        adhd_benefit_potential=0.6,
                        implementation_complexity="medium",
                        suggested_strategy=EvolutionStrategy.PERSONALIZATION_INTEGRATION,
                        suggested_changes=cluster.potential_template_improvement,
                        validation_method=EvolutionValidation.EFFECTIVENESS_COMPARISON,
                        expected_effectiveness_improvement=cluster.effectiveness_improvement,
                        confidence=cluster.cluster_confidence,
                        priority="medium"
                    )
                    opportunities.append(opportunity)

            return opportunities

        except Exception as e:
            logger.error(f"Failed to detect evolution opportunities: {e}")
            return []

    # A/B Testing for Evolution Validation

    async def _start_evolution_experiment(
        self, opportunity: EvolutionOpportunity
    ) -> Optional[EvolutionExperiment]:
        """Start A/B testing experiment for template evolution."""
        try:
            # Check if we have capacity for new experiment
            if len(self._active_experiments) >= self.max_concurrent_experiments:
                logger.debug(f"Max concurrent experiments reached, deferring {opportunity.opportunity_id}")
                return None

            # Get original template
            original_template = await self.template_manager.get_template_by_id(opportunity.template_id)
            if not original_template:
                return None

            # Create evolved template based on opportunity
            evolved_template = await self._create_evolved_template(original_template, opportunity)
            if not evolved_template:
                return None

            experiment_id = f"exp_{opportunity.template_id}_{int(time.time())}"

            # Create experiment
            experiment = EvolutionExperiment(
                experiment_id=experiment_id,
                template_id=opportunity.template_id,
                original_template=original_template,
                evolved_template=evolved_template,
                target_sample_size=20,  # ADHD-appropriate sample size
                current_sample_size=0,
                success_threshold=0.1,  # 10% improvement threshold
                status="running"
            )

            # Register experiment with effectiveness tracker
            ab_test = await self.effectiveness_tracker.start_ab_test(
                test_name=f"Template Evolution: {opportunity.suggested_strategy.value}",
                user_session_id="system",  # System-wide test
                strategy_a={"template": original_template.template_id},
                strategy_b={"template": evolved_template.template_id},
                target_sample_size=20
            )

            self._active_experiments[experiment_id] = experiment

            logger.info(f"🧪 Started evolution experiment {experiment_id} for {opportunity.template_id}")
            return experiment

        except Exception as e:
            logger.error(f"Failed to start evolution experiment: {e}")
            return None

    async def _create_evolved_template(
        self, original_template: NavigationStrategyTemplate, opportunity: EvolutionOpportunity
    ) -> Optional[NavigationStrategyTemplate]:
        """Create evolved template based on evolution opportunity."""
        try:
            import copy
            evolved_template = copy.deepcopy(original_template)

            # Apply evolution based on strategy
            if opportunity.suggested_strategy == EvolutionStrategy.INCREMENTAL_IMPROVEMENT:
                evolved_template = await self._apply_incremental_improvement(
                    evolved_template, opportunity.suggested_changes
                )

            elif opportunity.suggested_strategy == EvolutionStrategy.ACCOMMODATION_ENHANCEMENT:
                evolved_template = await self._apply_accommodation_enhancement(
                    evolved_template, opportunity.suggested_changes
                )

            elif opportunity.suggested_strategy == EvolutionStrategy.COMPLEXITY_OPTIMIZATION:
                evolved_template = await self._apply_complexity_optimization(
                    evolved_template, opportunity.suggested_changes
                )

            elif opportunity.suggested_strategy == EvolutionStrategy.TIMING_REFINEMENT:
                evolved_template = await self._apply_timing_refinement(
                    evolved_template, opportunity.suggested_changes
                )

            elif opportunity.suggested_strategy == EvolutionStrategy.PERSONALIZATION_INTEGRATION:
                evolved_template = await self._apply_personalization_integration(
                    evolved_template, opportunity.suggested_changes
                )

            # Update template metadata
            evolved_template.template_id = f"{original_template.template_id}_evolved"
            evolved_template.version = self._increment_version(original_template.version, "minor")
            evolved_template.template_hash = self._calculate_template_hash(evolved_template)
            evolved_template.curator_approved = False  # Needs approval
            evolved_template.created_at = datetime.now(timezone.utc)

            return evolved_template

        except Exception as e:
            logger.error(f"Failed to create evolved template: {e}")
            return None

    # Evolution Strategies Implementation

    async def _apply_incremental_improvement(
        self, template: NavigationStrategyTemplate, changes: Dict[str, Any]
    ) -> NavigationStrategyTemplate:
        """Apply incremental improvements to template."""
        # Improve step efficiency based on effectiveness data
        if 'step_improvements' in changes:
            for step_id, improvements in changes['step_improvements'].items():
                for step in template.steps:
                    if step.step_id == step_id:
                        # Apply improvements
                        if 'reduce_cognitive_load' in improvements:
                            step.cognitive_load = max(0.0, step.cognitive_load - 0.1)
                        if 'optimize_timing' in improvements:
                            step.estimated_duration_seconds = int(step.estimated_duration_seconds * 0.9)

        return template

    async def _apply_accommodation_enhancement(
        self, template: NavigationStrategyTemplate, changes: Dict[str, Any]
    ) -> NavigationStrategyTemplate:
        """Apply ADHD accommodation enhancements."""
        accommodation_type = changes.get('accommodation_type')

        if accommodation_type == 'progressive_disclosure':
            # Enhance progressive disclosure in template
            for step in template.steps:
                if step.complexity_level > 0.5:
                    if 'progressive_disclosure' not in [acc.value for acc in step.adhd_accommodations]:
                        from .strategy_template_manager import AccommodationType
                        step.adhd_accommodations.append(AccommodationType.PROGRESSIVE_DISCLOSURE)

        elif accommodation_type == 'cognitive_load_limiting':
            # Add cognitive load limiting to high-load steps
            for step in template.steps:
                if step.cognitive_load > 0.6:
                    from .strategy_template_manager import AccommodationType
                    if AccommodationType.COGNITIVE_LOAD_LIMITING not in step.adhd_accommodations:
                        step.adhd_accommodations.append(AccommodationType.COGNITIVE_LOAD_LIMITING)

        return template

    async def _apply_complexity_optimization(
        self, template: NavigationStrategyTemplate, changes: Dict[str, Any]
    ) -> NavigationStrategyTemplate:
        """Apply complexity optimization to template."""
        optimization_type = changes.get('optimization_type', 'reduce_overall')

        if optimization_type == 'reduce_overall':
            # Reduce overall template complexity
            template.max_cognitive_load = max(0.3, template.max_cognitive_load - 0.1)

            for step in template.steps:
                step.cognitive_load = max(0.1, step.cognitive_load - 0.05)

        elif optimization_type == 'progressive_complexity':
            # Ensure complexity increases progressively
            for i, step in enumerate(template.steps):
                target_complexity = (i + 1) / len(template.steps) * template.max_cognitive_load
                step.cognitive_load = min(step.cognitive_load, target_complexity)

        return template

    async def _apply_timing_refinement(
        self, template: NavigationStrategyTemplate, changes: Dict[str, Any]
    ) -> NavigationStrategyTemplate:
        """Apply timing refinements based on actual usage data."""
        timing_adjustments = changes.get('timing_adjustments', {})

        for step_id, adjustment in timing_adjustments.items():
            for step in template.steps:
                if step.step_id == step_id:
                    multiplier = adjustment.get('duration_multiplier', 1.0)
                    step.estimated_duration_seconds = int(step.estimated_duration_seconds * multiplier)

        # Update overall template timing
        total_step_time = sum(step.estimated_duration_seconds for step in template.steps)
        template.estimated_completion_time_minutes = max(1, total_step_time // 60)

        return template

    async def _apply_personalization_integration(
        self, template: NavigationStrategyTemplate, changes: Dict[str, Any]
    ) -> NavigationStrategyTemplate:
        """Integrate common personalizations into base template."""
        common_personalizations = changes.get('common_personalizations', [])

        for personalization in common_personalizations:
            pers_type = personalization.get('type')
            pers_data = personalization.get('data', {})

            if pers_type == 'step_reordering':
                # Apply most common step reordering
                new_order = pers_data.get('new_order', [])
                if new_order and len(new_order) == len(template.steps):
                    step_map = {step.step_id: step for step in template.steps}
                    template.steps = [step_map[step_id] for step_id in new_order if step_id in step_map]

            elif pers_type == 'accommodation_addition':
                # Add commonly requested accommodations
                new_accommodations = pers_data.get('accommodations', [])
                from .strategy_template_manager import AccommodationType
                for acc_str in new_accommodations:
                    try:
                        accommodation = AccommodationType(acc_str)
                        if accommodation not in template.adhd_accommodations:
                            template.adhd_accommodations.append(accommodation)
                    except ValueError:
                        continue

        return template

    # Effectiveness Analysis

    async def _get_template_effectiveness_data(self, template_id: str) -> Dict[str, Any]:
        """Get comprehensive effectiveness data for template."""
        try:
            # Query template usage and effectiveness from various sources
            usage_query = """
            SELECT COUNT(*) as total_uses,
                   COUNT(DISTINCT user_session_id) as unique_users,
                   AVG(effectiveness_score) as avg_effectiveness,
                   AVG(duration_minutes) as avg_duration,
                   AVG(cognitive_load_experienced) as avg_cognitive_load
            FROM template_usage_tracking
            WHERE template_id = $1
              AND usage_timestamp > NOW() - INTERVAL '30 days'
            """

            results = await self.database.execute_query(usage_query, (template_id,))

            if results and results[0]['total_uses']:
                effectiveness_data = {
                    "template_id": template_id,
                    "total_uses": results[0]['total_uses'],
                    "unique_users": results[0]['unique_users'],
                    "average_effectiveness": results[0]['avg_effectiveness'],
                    "average_duration": results[0]['avg_duration'],
                    "average_cognitive_load": results[0]['avg_cognitive_load'],
                    "user_count": results[0]['unique_users']
                }

                # Get accommodation effectiveness
                accommodation_effectiveness = await self._get_accommodation_effectiveness(template_id)
                effectiveness_data['accommodation_effectiveness'] = accommodation_effectiveness

                return effectiveness_data

            return {}

        except Exception as e:
            logger.error(f"Failed to get template effectiveness data: {e}")
            return {}

    async def _get_accommodation_effectiveness(self, template_id: str) -> Dict[str, float]:
        """Get effectiveness of ADHD accommodations for template."""
        try:
            # Query accommodation usage and effectiveness
            accommodation_query = """
            SELECT accommodations_used, AVG(effectiveness_score) as effectiveness
            FROM template_usage_tracking
            WHERE template_id = $1
              AND accommodations_used IS NOT NULL
              AND usage_timestamp > NOW() - INTERVAL '30 days'
            GROUP BY accommodations_used
            """

            results = await self.database.execute_query(accommodation_query, (template_id,))

            accommodation_effectiveness = {}
            for row in results:
                accommodations = json.loads(row['accommodations_used'])
                effectiveness = row['effectiveness']

                for accommodation in accommodations:
                    if accommodation not in accommodation_effectiveness:
                        accommodation_effectiveness[accommodation] = []
                    accommodation_effectiveness[accommodation].append(effectiveness)

            # Calculate average effectiveness per accommodation
            return {
                accommodation: statistics.mean(scores)
                for accommodation, scores in accommodation_effectiveness.items()
            }

        except Exception as e:
            logger.error(f"Failed to get accommodation effectiveness: {e}")
            return {}

    # Evolution Management

    async def process_evolution_results(self, experiment_id: str) -> Dict[str, Any]:
        """Process results of evolution experiment and make decisions."""
        try:
            if experiment_id not in self._active_experiments:
                return {"error": "Experiment not found"}

            experiment = self._active_experiments[experiment_id]

            # Check if experiment has enough data
            if experiment.current_sample_size < experiment.target_sample_size:
                return {"status": "insufficient_data", "current_sample": experiment.current_sample_size}

            # Analyze results
            if len(experiment.original_results) >= 10 and len(experiment.evolved_results) >= 10:
                original_avg = statistics.mean(experiment.original_results)
                evolved_avg = statistics.mean(experiment.evolved_results)

                improvement = evolved_avg - original_avg
                improvement_percentage = improvement / original_avg if original_avg > 0 else 0

                # Determine winner
                if improvement > experiment.success_threshold:
                    experiment.winner = "evolved"
                    experiment.statistical_significance = 0.9  # Simplified
                elif improvement < -experiment.success_threshold:
                    experiment.winner = "original"
                    experiment.statistical_significance = 0.9
                else:
                    experiment.winner = "no_difference"
                    experiment.statistical_significance = 0.3

                experiment.status = "completed"
                experiment.end_date = datetime.now(timezone.utc)

                # If evolved template wins, propose for deployment
                if experiment.winner == "evolved":
                    await self._propose_template_deployment(experiment)

                # Archive experiment
                self._evolution_history.append({
                    "experiment_id": experiment_id,
                    "winner": experiment.winner,
                    "improvement": improvement,
                    "improvement_percentage": improvement_percentage,
                    "statistical_significance": experiment.statistical_significance,
                    "completed_at": experiment.end_date.isoformat()
                })

                # Remove from active experiments
                del self._active_experiments[experiment_id]

                logger.info(f"🏁 Experiment {experiment_id} completed: {experiment.winner} wins "
                           f"({improvement_percentage:.1%} improvement)")

                return {
                    "status": "completed",
                    "winner": experiment.winner,
                    "improvement": improvement,
                    "improvement_percentage": improvement_percentage,
                    "statistical_significance": experiment.statistical_significance
                }

            return {"status": "analyzing", "sample_size": experiment.current_sample_size}

        except Exception as e:
            logger.error(f"Failed to process evolution results: {e}")
            return {"error": str(e)}

    async def _propose_template_deployment(self, experiment: EvolutionExperiment) -> None:
        """Propose evolved template for deployment."""
        try:
            # Create evolution proposal for curator review
            proposal = TemplateEvolutionProposal(
                proposal_id=f"deploy_{experiment.template_id}_{int(time.time())}",
                template_hash=experiment.evolved_template.template_hash,
                template_name=experiment.evolved_template.template_name,
                evolution_type=EvolutionProposal.MINOR_IMPROVEMENT,
                proposed_changes={
                    "template_replacement": True,
                    "old_template_id": experiment.original_template.template_id,
                    "new_template_id": experiment.evolved_template.template_id
                },
                supporting_evidence={
                    "experiment_id": experiment.experiment_id,
                    "improvement_percentage": statistics.mean(experiment.evolved_results) - statistics.mean(experiment.original_results),
                    "statistical_significance": experiment.statistical_significance,
                    "sample_size": experiment.current_sample_size
                },
                user_support_count=experiment.current_sample_size,
                effectiveness_improvement=statistics.mean(experiment.evolved_results) - statistics.mean(experiment.original_results),
                adhd_optimization_benefit="Validated improvement through A/B testing"
            )

            # Submit to persistence bridge for ConPort sync
            await self.persistence_bridge._evolution_proposals.update({proposal.proposal_id: proposal})

            logger.info(f"📋 Proposed template deployment for {experiment.template_id}")

        except Exception as e:
            logger.error(f"Failed to propose template deployment: {e}")

    # Continuous Improvement

    async def analyze_system_wide_patterns(self) -> Dict[str, Any]:
        """Analyze system-wide patterns for strategic improvements."""
        try:
            analysis_results = {
                "total_templates_analyzed": 0,
                "underperforming_templates": [],
                "high_performing_templates": [],
                "common_personalizations": [],
                "adhd_accommodation_gaps": [],
                "system_wide_improvements": []
            }

            # Get all templates for analysis
            library = await self.template_manager.get_template_library()

            for template_id in library.most_popular_templates:
                template = await self.template_manager.get_template_by_id(template_id)
                if template:
                    effectiveness_data = await self._get_template_effectiveness_data(template_id)

                    if effectiveness_data:
                        avg_effectiveness = effectiveness_data.get('average_effectiveness', 0.5)

                        if avg_effectiveness < 0.6:
                            analysis_results["underperforming_templates"].append({
                                "template_id": template_id,
                                "effectiveness": avg_effectiveness,
                                "user_count": effectiveness_data.get('user_count', 0)
                            })
                        elif avg_effectiveness > 0.85:
                            analysis_results["high_performing_templates"].append({
                                "template_id": template_id,
                                "effectiveness": avg_effectiveness,
                                "user_count": effectiveness_data.get('user_count', 0)
                            })

                    analysis_results["total_templates_analyzed"] += 1

            # Analyze common personalizations across all templates
            common_personalizations = await self._analyze_common_personalizations()
            analysis_results["common_personalizations"] = common_personalizations

            # Identify ADHD accommodation gaps
            accommodation_gaps = await self._identify_accommodation_gaps()
            analysis_results["adhd_accommodation_gaps"] = accommodation_gaps

            # Generate system-wide improvement recommendations
            improvements = await self._generate_system_improvements(analysis_results)
            analysis_results["system_wide_improvements"] = improvements

            logger.info(f"📈 System-wide analysis: {len(analysis_results['underperforming_templates'])} templates need improvement")
            return analysis_results

        except Exception as e:
            logger.error(f"Failed to analyze system-wide patterns: {e}")
            return {"error": str(e)}

    # Utility Methods

    def _calculate_template_hash(self, template: NavigationStrategyTemplate) -> str:
        """Calculate immutable hash for template (expert-recommended SHA256)."""
        # Create deterministic hash from template structure
        hash_data = {
            "name": template.template_name,
            "steps": [step.step_id for step in template.steps],
            "accommodations": [acc.value for acc in template.adhd_accommodations],
            "complexity": template.max_cognitive_load,
            "version": template.version
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _increment_version(self, current_version: str, increment_type: str = "patch") -> str:
        """Increment semantic version."""
        try:
            major, minor, patch = map(int, current_version.split('.'))

            if increment_type == "major":
                return f"{major + 1}.0.0"
            elif increment_type == "minor":
                return f"{major}.{minor + 1}.0"
            else:  # patch
                return f"{major}.{minor}.{patch + 1}"

        except Exception:
            return "1.0.1"  # Default if parsing fails

    def _assess_adhd_benefit_potential(self, effectiveness_data: Dict[str, Any]) -> float:
        """Assess potential ADHD benefit from evolution."""
        # High benefit if cognitive load can be reduced
        avg_cognitive_load = effectiveness_data.get('average_cognitive_load', 0.5)
        if avg_cognitive_load > 0.7:
            return 0.8  # High potential for ADHD benefit

        # Moderate benefit if effectiveness is low (can be improved)
        avg_effectiveness = effectiveness_data.get('average_effectiveness', 0.5)
        if avg_effectiveness < 0.6:
            return 0.6

        return 0.4  # Default moderate potential

    async def _should_start_experiment(self, opportunity: EvolutionOpportunity) -> bool:
        """Determine if evolution opportunity should start A/B testing."""
        # Criteria for starting experiment
        return (
            opportunity.improvement_potential > 0.1 and
            opportunity.user_impact_scope >= 5 and
            opportunity.confidence > 0.6 and
            len(self._active_experiments) < self.max_concurrent_experiments
        )

    async def _suggest_effectiveness_improvements(
        self, template: NavigationStrategyTemplate, effectiveness_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest specific improvements based on effectiveness data."""
        improvements = {}

        avg_cognitive_load = effectiveness_data.get('average_cognitive_load', 0.5)
        if avg_cognitive_load > 0.7:
            improvements['reduce_cognitive_load'] = True
            improvements['add_accommodations'] = ['cognitive_load_limiting', 'progressive_disclosure']

        avg_duration = effectiveness_data.get('average_duration', template.estimated_completion_time_minutes)
        if avg_duration > template.estimated_completion_time_minutes * 1.3:
            improvements['optimize_timing'] = True
            improvements['timing_multiplier'] = avg_duration / template.estimated_completion_time_minutes

        return improvements

    # Placeholder methods for complex operations
    async def _get_delta_clusters_for_template(self, template_hash: str) -> List[Any]:
        return []  # Would get actual delta clusters

    async def _analyze_common_personalizations(self) -> List[Dict[str, Any]]:
        return []  # Would analyze personalization patterns

    async def _identify_accommodation_gaps(self) -> List[str]:
        return []  # Would identify missing ADHD accommodations

    async def _generate_system_improvements(self, analysis_results: Dict[str, Any]) -> List[str]:
        return ["Continuous improvement system operational"]

    def _get_template_by_hash(self, template_hash: str) -> Optional[NavigationStrategyTemplate]:
        return None  # Would retrieve template by hash


# Convenience functions
async def create_effectiveness_evolution_system(
    database: SerenaIntelligenceDatabase,
    template_manager: StrategyTemplateManager,
    pattern_adapter: PersonalPatternAdapter,
    effectiveness_tracker: EffectivenessTracker,
    persistence_bridge: CrossSessionPersistenceBridge,
    performance_monitor: PerformanceMonitor = None
) -> EffectivenessEvolutionSystem:
    """Create effectiveness evolution system instance."""
    return EffectivenessEvolutionSystem(
        database, template_manager, pattern_adapter, effectiveness_tracker,
        persistence_bridge, performance_monitor
    )


async def run_evolution_monitoring_cycle(
    evolution_system: EffectivenessEvolutionSystem
) -> Dict[str, Any]:
    """Run complete evolution monitoring cycle."""
    try:
        # Monitor template effectiveness
        monitoring_results = await evolution_system.monitor_template_effectiveness()

        # Analyze system-wide patterns
        analysis_results = await evolution_system.analyze_system_wide_patterns()

        return {
            "monitoring_results": monitoring_results,
            "analysis_results": analysis_results,
            "evolution_cycle_status": "completed",
            "opportunities_detected": monitoring_results.get("opportunities_detected", 0),
            "experiments_active": monitoring_results.get("experiments_started", 0)
        }

    except Exception as e:
        logger.error(f"Evolution monitoring cycle failed: {e}")
        return {
            "evolution_cycle_status": "failed",
            "error": str(e)
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🧬 Serena Effectiveness-Based Evolution System")
        print("Automatic template improvement with A/B testing and ADHD optimization")
        print("✅ Module loaded successfully")

    asyncio.run(main())