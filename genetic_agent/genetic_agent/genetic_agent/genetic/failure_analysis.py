"""
Failure Pattern Analysis for Enhanced Iterative Agent

Implements statistical analysis of failure patterns, Zen-enhanced insights,
and ConPort integration for historical learning.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics
import json

from shared.mcp.zen_client import ZenClient
from shared.mcp.conport_client import ConPortClient

@dataclass
class FailurePattern:
    """Represents a failure pattern with statistical data."""
    pattern_type: str  # "complexity_high", "patterns_missing", "llm_insufficient", etc.
    frequency: int
    average_confidence: float
    associated_complexity: float
    common_signals: List[str]
    recovery_success_rate: float
    zen_analysis_summary: Optional[str] = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class FailureAnalysisResult:
    """Result of failure pattern analysis."""
    primary_failure_mode: str
    confidence_score: float
    recommended_strategy: str
    statistical_insights: Dict[str, Any]
    zen_recommendations: Optional[str] = None
    learning_opportunities: List[str] = None

    def __post_init__(self):
        if self.learning_opportunities is None:
            self.learning_opportunities = []

class FailureAnalysisEngine:
    """
    Analyzes failure patterns using statistical methods and Zen reasoning.

    Key Features:
    - Statistical pattern recognition across failure signals
    - Zen-enhanced complex failure analysis
    - ConPort integration for historical learning
    - Confidence-based pattern validation
    - Learning opportunity identification
    """

    def __init__(self, zen_client: ZenClient, conport_client: ConPortClient, workspace_id: str):
        self.zen_client = zen_client
        self.conport_client = conport_client
        self.workspace_id = workspace_id

        # Initialize failure pattern database
        self.failure_patterns: Dict[str, FailurePattern] = {}
        self.min_pattern_confidence = 0.7
        self.max_pattern_history = 1000

    async def analyze_failure(
        self,
        failure_signals: List[str],
        context: Dict[str, Any],
        repair_candidates: List[Any]
    ) -> FailureAnalysisResult:
        """
        Analyze failure patterns and provide insights.

        Args:
            failure_signals: List of failure indicators
            context: Bug context (complexity, patterns, etc.)
            repair_candidates: Failed repair attempts

        Returns:
            Comprehensive failure analysis with recommendations
        """
        # Phase 1: Statistical pattern analysis
        statistical_analysis = self._analyze_failure_statistics(failure_signals, context, repair_candidates)

        # Phase 2: Pattern correlation and learning
        pattern_correlations = self._identify_pattern_correlations(failure_signals, context)

        # Phase 3: Zen-enhanced complex analysis
        zen_insights = await self._get_zen_failure_analysis(
            failure_signals, context, repair_candidates, statistical_analysis
        )

        # Phase 4: Strategy recommendation
        recommended_strategy = self._recommend_recovery_strategy(
            statistical_analysis, pattern_correlations, zen_insights
        )

        # Phase 5: Learning opportunity identification
        learning_opportunities = self._identify_learning_opportunities(
            failure_signals, context, repair_candidates
        )

        # Update historical patterns
        await self._update_failure_patterns(failure_signals, context)

        return FailureAnalysisResult(
            primary_failure_mode=statistical_analysis['primary_mode'],
            confidence_score=statistical_analysis['confidence'],
            recommended_strategy=recommended_strategy,
            statistical_insights=statistical_analysis,
            zen_recommendations=zen_insights.get('recommendations'),
            learning_opportunities=learning_opportunities
        )

    def _analyze_failure_statistics(
        self,
        failure_signals: List[str],
        context: Dict[str, Any],
        repair_candidates: List[Any]
    ) -> Dict[str, Any]:
        """Perform statistical analysis of failure signals."""

        # Count signal frequencies
        signal_counts = {}
        for signal in failure_signals:
            signal_counts[signal] = signal_counts.get(signal, 0) + 1

        # Calculate pattern strength
        total_signals = len(failure_signals)
        dominant_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)

        # Determine primary failure mode
        primary_mode = self._classify_failure_mode(dominant_signals, context, repair_candidates)

        # Calculate confidence in analysis
        confidence = min(1.0, len(dominant_signals) / 5.0)  # More signals = higher confidence

        # Generate statistical insights
        insights = {
            'signal_frequencies': signal_counts,
            'dominant_signals': dominant_signals[:3],
            'total_signals': total_signals,
            'pattern_strength': len(dominant_signals) / max(1, total_signals),
            'complexity_correlation': context.get('complexity', {}).get('score', 0.5),
            'candidate_count': len(repair_candidates),
            'average_candidate_confidence': self._calculate_average_confidence(repair_candidates)
        }

        return {
            'primary_mode': primary_mode,
            'confidence': confidence,
            'insights': insights
        }

    def _classify_failure_mode(
        self,
        dominant_signals: List[Tuple[str, int]],
        context: Dict[str, Any],
        repair_candidates: List[Any]
    ) -> str:
        """Classify the primary failure mode based on signals and context."""

        # Check for complexity-related failures
        if any('complexity' in signal for signal, _ in dominant_signals):
            return "complexity_overload"

        # Check for pattern-related failures
        if any('patterns' in signal for signal, _ in dominant_signals):
            pattern_count = len(context.get('patterns', {}).get('results', []))
            if pattern_count < 2:
                return "insufficient_patterns"

        # Check for LLM capability issues
        if len(repair_candidates) > 0:
            avg_confidence = self._calculate_average_confidence(repair_candidates)
            if avg_confidence < 0.4:
                return "llm_capability_limit"

        # Check for GP optimization issues
        if any('gp' in signal.lower() for signal, _ in dominant_signals):
            return "gp_optimization_failure"

        # Default to general complexity issue
        return "general_complexity_issue"

    def _calculate_average_confidence(self, repair_candidates: List[Any]) -> float:
        """Calculate average confidence from repair candidates."""
        if not repair_candidates:
            return 0.0

        confidences = []
        for candidate in repair_candidates:
            if hasattr(candidate, 'confidence'):
                confidences.append(candidate.confidence)

        return statistics.mean(confidences) if confidences else 0.0

    def _identify_pattern_correlations(
        self,
        failure_signals: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify correlations between failure signals and context."""

        correlations = {
            'complexity_vs_signals': [],
            'patterns_vs_success': [],
            'signal_clusters': []
        }

        # Analyze complexity correlations
        complexity_score = context.get('complexity', {}).get('score', 0.5)

        # Group related signals
        complexity_signals = [s for s in failure_signals if 'complexity' in s]
        pattern_signals = [s for s in failure_signals if 'patterns' in s]
        llm_signals = [s for s in failure_signals if 'llm' in s.lower()]

        correlations['signal_clusters'] = {
            'complexity_related': len(complexity_signals),
            'pattern_related': len(pattern_signals),
            'llm_related': len(llm_signals)
        }

        return correlations

    async def _get_zen_failure_analysis(
        self,
        failure_signals: List[str],
        context: Dict[str, Any],
        repair_candidates: List[Any],
        statistical_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use Zen reasoning for complex failure analysis."""

        analysis_prompt = f"""Analyze complex code repair failure patterns:

Failure Signals: {', '.join(failure_signals)}
Bug Context: {context['description']}
Complexity Score: {context.get('complexity', {}).get('score', 0.5)}
Statistical Analysis: {statistical_analysis['primary_mode']} (confidence: {statistical_analysis['confidence']:.2f})

Repair Attempts: {len(repair_candidates)} candidates, avg confidence: {statistical_analysis['insights']['average_candidate_confidence']:.2f}

Provide sophisticated analysis:
1. Root cause hypothesis beyond surface signals
2. Strategic recommendations for recovery
3. Learning insights for future improvements
4. Specific implementation guidance

Format: {{"root_cause": "hypothesis", "strategic_recommendations": ["list"], "learning_insights": ["list"], "implementation_guidance": "detailed guidance"}}
"""

        try:
            async with self.zen_client:
                response = await self.zen_client.thinkdeep(
                    step=analysis_prompt,
                    step_number=1,
                    total_steps=1,
                    next_step_required=False,
                    findings=f"Complex failure analysis for {len(repair_candidates)} failed repairs",
                    model="gpt-5-codex"
                )

                # Extract Zen analysis
                zen_analysis = response.get('reasoning', {})

                return {
                    'root_cause': zen_analysis.get('root_cause', 'Complex multi-factor failure'),
                    'strategic_recommendations': zen_analysis.get('strategic_recommendations', []),
                    'learning_insights': zen_analysis.get('learning_insights', []),
                    'implementation_guidance': zen_analysis.get('implementation_guidance', 'Needs detailed analysis'),
                    'recommendations': zen_analysis.get('strategic_recommendations', [])
                }

        except Exception as e:
            return {
                'error': f'Zen analysis failed: {e}',
                'fallback': 'Proceed with statistical analysis only'
            }

    def _recommend_recovery_strategy(
        self,
        statistical: Dict[str, Any],
        correlations: Dict[str, Any],
        zen_insights: Dict[str, Any]
    ) -> str:
        """Recommend recovery strategy based on all analyses."""

        primary_mode = statistical['primary_mode']

        # Strategy mapping based on failure mode
        strategy_map = {
            'complexity_overload': 'selective_gp_small_population',
            'insufficient_patterns': 'llm_only_extended_patterns',
            'llm_capability_limit': 'gp_enhancement_full_population',
            'gp_optimization_failure': 'hybrid_adaptive_approach',
            'general_complexity_issue': 'balanced_hybrid_approach'
        }

        base_strategy = strategy_map.get(primary_mode, 'balanced_hybrid_approach')

        # Adjust based on Zen insights if available
        if 'strategic_recommendations' in zen_insights:
            zen_strategies = zen_insights['strategic_recommendations']
            if any('reduce population' in str(rec) for rec in zen_strategies):
                base_strategy = 'selective_gp_small_population'

        return base_strategy

    def _identify_learning_opportunities(
        self,
        failure_signals: List[str],
        context: Dict[str, Any],
        repair_candidates: List[Any]
    ) -> List[str]:
        """Identify learning opportunities from failure analysis."""

        opportunities = []

        # Check for pattern learning opportunities
        if len(context.get('patterns', {}).get('results', [])) < 3:
            opportunities.append("Expand pattern database for similar bug types")

        # Check for operator effectiveness learning
        if any('gp' in signal.lower() for signal in failure_signals):
            opportunities.append("Analyze GP operator effectiveness on high-complexity bugs")

        # Check for LLM capability boundaries
        if len(repair_candidates) > 0:
            avg_confidence = self._calculate_average_confidence(repair_candidates)
            if avg_confidence < 0.5:
                opportunities.append("Identify LLM capability boundaries for complex code")

        # Check for complexity assessment improvement
        complexity_score = context.get('complexity', {}).get('score', 0.5)
        if complexity_score > 0.8 and 'complexity_overload' in failure_signals:
            opportunities.append("Improve complexity assessment accuracy for extreme cases")

        return opportunities

    async def _update_failure_patterns(
        self,
        failure_signals: List[str],
        context: Dict[str, Any]
    ) -> None:
        """Update historical failure patterns in ConPort."""

        try:
            # Prepare failure pattern data
            pattern_data = {
                'failure_signals': failure_signals,
                'context_complexity': context.get('complexity', {}).get('score', 0.5),
                'pattern_count': len(context.get('patterns', {}).get('results', [])),
                'timestamp': datetime.now().isoformat(),
                'workspace_id': self.workspace_id
            }

            # Store in ConPort
            await self.conport_client.log_custom_data(
                category="failure_patterns",
                key=f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                value=pattern_data
            )

        except Exception as e:
            # Log but don't fail the analysis
            print(f"Failed to update failure patterns: {e}")

    async def get_historical_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve historical failure pattern insights from ConPort."""

        try:
            data = await self.conport_client.get_custom_data(
                category="failure_patterns"
            )

            # Process and return insights
            insights = []
            for key, value in data.items():
                if isinstance(value, dict):
                    insights.append({
                        'pattern_id': key,
                        'signals': value.get('failure_signals', []),
                        'complexity': value.get('context_complexity', 0.5),
                        'patterns_available': value.get('pattern_count', 0),
                        'timestamp': value.get('timestamp')
                    })

            # Sort by timestamp and limit
            insights.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return insights[:limit]

        except Exception as e:
            print(f"Failed to retrieve historical insights: {e}")
            return []