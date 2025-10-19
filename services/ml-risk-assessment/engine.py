"""
Predictive Risk Assessment ML Engine for Task Orchestrator
ADHD-Optimized Machine Learning-based Blocker Detection and Risk Mitigation

Uses pattern recognition and historical data to predict potential obstacles
before they impact neurodivergent developers.
"""

import asyncio
import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import math

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk severity levels for predictions."""
    MINIMAL = "minimal"        # 0.0-0.2: Very low risk
    LOW = "low"               # 0.2-0.4: Minor risk, monitor
    MODERATE = "moderate"     # 0.4-0.6: Moderate risk, plan mitigation
    HIGH = "high"             # 0.6-0.8: High risk, immediate attention
    CRITICAL = "critical"     # 0.8-1.0: Critical risk, stop and resolve


class RiskCategory(str, Enum):
    """Categories of risks that can be predicted."""
    COGNITIVE_OVERLOAD = "cognitive_overload"           # ADHD-specific
    CONTEXT_SWITCHING = "context_switching"            # ADHD-specific
    DEPENDENCY_BLOCKER = "dependency_blocker"          # Technical
    RESOURCE_CONFLICT = "resource_conflict"            # Resource
    TIMELINE_SLIPPAGE = "timeline_slippage"            # Schedule
    INTEGRATION_FAILURE = "integration_failure"        # Technical
    COMMUNICATION_BREAKDOWN = "communication_breakdown" # Team
    HYPERFOCUS_BURNOUT = "hyperfocus_burnout"         # ADHD-specific


@dataclass
class RiskFactor:
    """Individual risk factor identified by ML."""
    factor_id: str
    category: RiskCategory
    risk_level: RiskLevel
    confidence: float              # 0.0-1.0 model confidence
    description: str
    evidence: List[str]            # Supporting evidence
    predicted_impact: float        # 0.0-1.0 impact severity
    time_to_manifestation: float   # Hours until risk materializes
    mitigation_suggestions: List[str]
    adhd_considerations: List[str] # Specific ADHD mitigations


@dataclass
class RiskProfile:
    """Comprehensive risk assessment for a task/project."""
    profile_id: str
    target_entity: str             # task_id, project_id, team_id
    entity_type: str               # "task", "project", "team"
    overall_risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    risk_score: float              # 0.0-1.0 composite score
    confidence_interval: Tuple[float, float]  # (low, high)
    assessment_timestamp: datetime
    next_reassessment: datetime
    historical_accuracy: float     # How accurate past predictions were


class PredictiveRiskAssessmentEngine:
    """
    ML-powered risk assessment with ADHD-specific pattern recognition.

    Features:
    - Real-time risk prediction using historical patterns
    - ADHD-specific risk factor identification
    - Proactive mitigation strategy generation
    - Confidence-weighted recommendation system
    - Continuous learning from outcome feedback
    """

    def __init__(self, conport_client=None, context7_client=None):
        self.conport = conport_client
        self.context7 = context7_client

        # ML Model Components (simplified ML simulation)
        self.historical_patterns: Dict[str, List[Dict]] = {}
        self.risk_models: Dict[RiskCategory, Dict] = {}
        self.prediction_accuracy: Dict[str, float] = {}

        # ADHD Pattern Database
        self.adhd_patterns = {
            "cognitive_overload_signals": [
                "multiple_parallel_tasks",
                "complex_technical_depth",
                "tight_deadlines",
                "context_heavy_requirements"
            ],
            "hyperfocus_risk_signals": [
                "single_complex_task",
                "deep_technical_interest",
                "deadline_pressure",
                "isolation_indicators"
            ],
            "context_switch_triggers": [
                "interruptions_frequency",
                "task_variety",
                "meeting_density",
                "notification_volume"
            ]
        }

        # Risk Assessment Cache
        self.risk_cache: Dict[str, RiskProfile] = {}
        self.assessment_queue: asyncio.Queue = asyncio.Queue()

        # Learning System
        self.learning_enabled = True
        self.prediction_feedback: List[Dict] = []
        self.model_accuracy_target = 0.75

        # Statistics
        self.assessment_stats = {
            "predictions_made": 0,
            "accurate_predictions": 0,
            "risks_prevented": 0,
            "adhd_specific_interventions": 0,
            "model_improvements": 0
        }

    async def initialize(self) -> None:
        """Initialize the predictive risk assessment engine."""
        try:
            await self._load_historical_data()
            await self._initialize_ml_models()
            await self._start_continuous_assessment()
            logger.info("Predictive risk assessment engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize risk assessment engine: {e}")

    async def assess_risk(
        self,
        entity_id: str,
        entity_type: str,
        context_data: Dict[str, Any]
    ) -> Optional[RiskProfile]:
        """Perform comprehensive risk assessment for an entity."""
        try:
            # Generate unique assessment ID
            profile_id = f"risk_{uuid.uuid4().hex[:8]}"

            # Extract features for ML models
            features = await self._extract_features(entity_id, entity_type, context_data)

            # Run risk predictions across all categories
            risk_factors = await self._predict_risks(features, context_data)

            # Calculate overall risk score and level
            overall_score, overall_level = self._calculate_overall_risk(risk_factors)

            # Calculate confidence intervals
            confidence_interval = self._calculate_confidence_interval(risk_factors)

            # Create risk profile
            risk_profile = RiskProfile(
                profile_id=profile_id,
                target_entity=entity_id,
                entity_type=entity_type,
                overall_risk_level=overall_level,
                risk_factors=risk_factors,
                risk_score=overall_score,
                confidence_interval=confidence_interval,
                assessment_timestamp=datetime.now(),
                next_reassessment=datetime.now() + timedelta(hours=6),
                historical_accuracy=self.prediction_accuracy.get(entity_type, 0.7)
            )

            # Cache assessment
            self.risk_cache[entity_id] = risk_profile

            # Log assessment if ConPort available
            if self.conport:
                await self._log_risk_assessment(risk_profile)

            self.assessment_stats["predictions_made"] += 1
            logger.info(f"Risk assessment completed for {entity_id}: {overall_level.value}")

            return risk_profile

        except Exception as e:
            logger.error(f"Risk assessment failed for {entity_id}: {e}")
            return None

    async def predict_blockers(
        self,
        project_context: Dict[str, Any],
        time_horizon: int = 24
    ) -> List[RiskFactor]:
        """Predict potential blockers within specified time horizon (hours)."""
        try:
            blockers = []

            # Analyze dependency chains
            dependency_risks = await self._analyze_dependency_risks(project_context, time_horizon)
            blockers.extend(dependency_risks)

            # Analyze team capacity and ADHD factors
            team_risks = await self._analyze_team_capacity_risks(project_context, time_horizon)
            blockers.extend(team_risks)

            # Analyze technical integration risks
            technical_risks = await self._analyze_technical_risks(project_context, time_horizon)
            blockers.extend(technical_risks)

            # Sort by likelihood and impact
            blockers.sort(key=lambda x: x.predicted_impact * x.confidence, reverse=True)

            return blockers

        except Exception as e:
            logger.error(f"Blocker prediction failed: {e}")
            return []

    async def generate_mitigation_strategies(
        self,
        risk_profile: RiskProfile
    ) -> Dict[str, List[str]]:
        """Generate ADHD-optimized mitigation strategies."""
        try:
            strategies = {
                "immediate_actions": [],
                "preventive_measures": [],
                "adhd_accommodations": [],
                "monitoring_points": []
            }

            for risk_factor in risk_profile.risk_factors:
                # Generate category-specific strategies
                category_strategies = await self._generate_category_strategies(risk_factor)

                # Add to appropriate strategy lists
                strategies["immediate_actions"].extend(category_strategies.get("immediate", []))
                strategies["preventive_measures"].extend(category_strategies.get("preventive", []))
                strategies["adhd_accommodations"].extend(risk_factor.adhd_considerations)
                strategies["monitoring_points"].extend(category_strategies.get("monitoring", []))

            # Remove duplicates and prioritize
            for key in strategies:
                strategies[key] = list(set(strategies[key]))

            return strategies

        except Exception as e:
            logger.error(f"Mitigation strategy generation failed: {e}")
            return {}

    async def update_prediction_feedback(
        self,
        prediction_id: str,
        actual_outcome: Dict[str, Any],
        intervention_applied: bool = False
    ) -> None:
        """Update ML models with actual outcomes for continuous learning."""
        try:
            feedback = {
                "prediction_id": prediction_id,
                "actual_outcome": actual_outcome,
                "intervention_applied": intervention_applied,
                "timestamp": datetime.now(),
                "accuracy_score": self._calculate_accuracy_score(prediction_id, actual_outcome)
            }

            self.prediction_feedback.append(feedback)

            # Update model accuracy
            if len(self.prediction_feedback) > 10:
                await self._update_model_accuracy()

            # Trigger model retraining if accuracy drops
            current_accuracy = self._calculate_current_accuracy()
            if current_accuracy < self.model_accuracy_target:
                await self._retrain_models()

            logger.info(f"Prediction feedback updated for {prediction_id}")

        except Exception as e:
            logger.error(f"Failed to update prediction feedback: {e}")

    # Private implementation methods

    async def _load_historical_data(self) -> None:
        """Load historical patterns for ML training."""
        # Implementation would load historical risk data
        pass

    async def _initialize_ml_models(self) -> None:
        """Initialize ML models for each risk category."""
        # Simplified ML model initialization
        for category in RiskCategory:
            self.risk_models[category] = {
                "weights": [0.5, 0.3, 0.2],  # Simplified feature weights
                "bias": 0.1,
                "accuracy": 0.7
            }

    async def _start_continuous_assessment(self) -> None:
        """Start background continuous risk assessment."""
        # Implementation would start monitoring loops
        pass

    async def _extract_features(
        self, entity_id: str, entity_type: str, context_data: Dict[str, Any]
    ) -> List[float]:
        """Extract features for ML prediction."""
        # Simplified feature extraction
        features = [
            context_data.get("complexity", 0.5),
            context_data.get("team_load", 0.3),
            context_data.get("dependency_count", 0) / 10.0,
            context_data.get("adhd_team_members", 0) / 5.0,
            context_data.get("timeline_pressure", 0.4)
        ]
        return features

    async def _predict_risks(
        self, features: List[float], context_data: Dict[str, Any]
    ) -> List[RiskFactor]:
        """Use ML models to predict risks."""
        risk_factors = []

        for category in RiskCategory:
            # Simplified ML prediction
            model = self.risk_models[category]
            risk_score = sum(f * w for f, w in zip(features, model["weights"])) + model["bias"]
            risk_score = max(0.0, min(1.0, risk_score))  # Clamp to [0,1]

            if risk_score > 0.3:  # Only report significant risks
                risk_level = self._score_to_risk_level(risk_score)

                risk_factor = RiskFactor(
                    factor_id=f"{category.value}_{uuid.uuid4().hex[:6]}",
                    category=category,
                    risk_level=risk_level,
                    confidence=model["accuracy"],
                    description=f"Predicted {category.value} risk based on current patterns",
                    evidence=self._generate_evidence(category, features, context_data),
                    predicted_impact=risk_score,
                    time_to_manifestation=self._estimate_time_to_manifestation(category, risk_score),
                    mitigation_suggestions=self._get_standard_mitigations(category),
                    adhd_considerations=self._get_adhd_mitigations(category)
                )

                risk_factors.append(risk_factor)

        return risk_factors

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert numerical risk score to risk level."""
        if score < 0.2:
            return RiskLevel.MINIMAL
        elif score < 0.4:
            return RiskLevel.LOW
        elif score < 0.6:
            return RiskLevel.MODERATE
        elif score < 0.8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _calculate_overall_risk(self, risk_factors: List[RiskFactor]) -> Tuple[float, RiskLevel]:
        """Calculate overall risk score and level."""
        if not risk_factors:
            return 0.0, RiskLevel.MINIMAL

        # Weighted average of risk impacts
        total_impact = sum(rf.predicted_impact * rf.confidence for rf in risk_factors)
        total_confidence = sum(rf.confidence for rf in risk_factors)

        overall_score = total_impact / total_confidence if total_confidence > 0 else 0.0
        overall_level = self._score_to_risk_level(overall_score)

        return overall_score, overall_level

    def _calculate_confidence_interval(self, risk_factors: List[RiskFactor]) -> Tuple[float, float]:
        """Calculate confidence interval for risk assessment."""
        if not risk_factors:
            return (0.0, 0.0)

        confidences = [rf.confidence for rf in risk_factors]
        avg_confidence = statistics.mean(confidences)
        std_dev = statistics.stdev(confidences) if len(confidences) > 1 else 0.1

        return (max(0.0, avg_confidence - std_dev), min(1.0, avg_confidence + std_dev))

    def _generate_evidence(
        self, category: RiskCategory, features: List[float], context: Dict[str, Any]
    ) -> List[str]:
        """Generate evidence supporting risk prediction."""
        evidence = []

        if category == RiskCategory.COGNITIVE_OVERLOAD and features[0] > 0.7:
            evidence.append("High task complexity detected")

        if category == RiskCategory.CONTEXT_SWITCHING and context.get("adhd_team_members", 0) > 0:
            evidence.append("ADHD team members present with context switching risk")

        return evidence

    def _estimate_time_to_manifestation(self, category: RiskCategory, risk_score: float) -> float:
        """Estimate hours until risk materializes."""
        base_times = {
            RiskCategory.COGNITIVE_OVERLOAD: 4.0,
            RiskCategory.HYPERFOCUS_BURNOUT: 8.0,
            RiskCategory.DEPENDENCY_BLOCKER: 12.0,
            RiskCategory.TIMELINE_SLIPPAGE: 24.0
        }

        base_time = base_times.get(category, 12.0)
        # Higher risk scores manifest sooner
        return base_time * (1.0 - risk_score * 0.7)

    def _get_standard_mitigations(self, category: RiskCategory) -> List[str]:
        """Get standard mitigation strategies for risk category."""
        mitigations = {
            RiskCategory.COGNITIVE_OVERLOAD: [
                "Break task into smaller chunks",
                "Schedule focused work blocks",
                "Reduce parallel tasks"
            ],
            RiskCategory.CONTEXT_SWITCHING: [
                "Batch similar tasks together",
                "Use time-blocking techniques",
                "Minimize interruptions"
            ],
            RiskCategory.DEPENDENCY_BLOCKER: [
                "Identify alternative approaches",
                "Prepare contingency plans",
                "Escalate dependency resolution"
            ]
        }
        return mitigations.get(category, ["Monitor situation closely"])

    def _get_adhd_mitigations(self, category: RiskCategory) -> List[str]:
        """Get ADHD-specific mitigation strategies."""
        adhd_mitigations = {
            RiskCategory.COGNITIVE_OVERLOAD: [
                "Use visual task boards",
                "Set gentle reminder alarms",
                "Create distraction-free environment"
            ],
            RiskCategory.HYPERFOCUS_BURNOUT: [
                "Schedule mandatory breaks",
                "Use focus time limits",
                "Monitor energy levels"
            ],
            RiskCategory.CONTEXT_SWITCHING: [
                "Use transition rituals",
                "Maintain context notes",
                "Allow buffer time between tasks"
            ]
        }
        return adhd_mitigations.get(category, ["Apply general ADHD accommodations"])

    async def _analyze_dependency_risks(
        self, project_context: Dict[str, Any], time_horizon: int
    ) -> List[RiskFactor]:
        """Analyze dependency-related risks."""
        # Implementation would analyze dependency chains
        return []

    async def _analyze_team_capacity_risks(
        self, project_context: Dict[str, Any], time_horizon: int
    ) -> List[RiskFactor]:
        """Analyze team capacity and ADHD-related risks."""
        # Implementation would analyze team workload and ADHD factors
        return []

    async def _analyze_technical_risks(
        self, project_context: Dict[str, Any], time_horizon: int
    ) -> List[RiskFactor]:
        """Analyze technical integration risks."""
        # Implementation would analyze technical complexity
        return []

    async def _generate_category_strategies(self, risk_factor: RiskFactor) -> Dict[str, List[str]]:
        """Generate strategies for specific risk category."""
        # Implementation would generate detailed strategies
        return {
            "immediate": risk_factor.mitigation_suggestions[:2],
            "preventive": risk_factor.mitigation_suggestions[2:],
            "monitoring": [f"Monitor {risk_factor.category.value} indicators"]
        }

    def _calculate_accuracy_score(self, prediction_id: str, actual_outcome: Dict[str, Any]) -> float:
        """Calculate accuracy score for a prediction."""
        # Implementation would compare prediction vs actual outcome
        return 0.8  # Simplified

    async def _update_model_accuracy(self) -> None:
        """Update model accuracy based on recent feedback."""
        recent_feedback = self.prediction_feedback[-10:]
        accuracy_scores = [f["accuracy_score"] for f in recent_feedback]

        if accuracy_scores:
            for category in RiskCategory:
                self.risk_models[category]["accuracy"] = statistics.mean(accuracy_scores)

    def _calculate_current_accuracy(self) -> float:
        """Calculate current model accuracy."""
        if not self.prediction_feedback:
            return 0.7

        recent_scores = [f["accuracy_score"] for f in self.prediction_feedback[-20:]]
        return statistics.mean(recent_scores)

    async def _retrain_models(self) -> None:
        """Retrain ML models when accuracy drops."""
        logger.info("Retraining ML models due to accuracy drop")
        self.assessment_stats["model_improvements"] += 1

    async def _log_risk_assessment(self, risk_profile: RiskProfile) -> None:
        """Log risk assessment to ConPort."""
        # Implementation would log to ConPort if available
        pass