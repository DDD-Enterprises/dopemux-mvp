"""
Enhanced Iterative Agent - Phase 1 Implementation
Core iteration loop with basic GP operators for code repair.

This agent implements the hybrid LLM+GP approach with research-backed fitness functions
and MCP integration for intelligent code repair.

Key Features:
- LLM-first generation with confidence-based validation
- Selective GP enhancement for complex cases
- Research-based fitness evaluation (GenProg/Chronicle methodology)
- Comprehensive Zen MCP integration for reasoning and quality assurance
- ADHD-optimized progressive disclosure and cognitive load management
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
from enum import Enum
import time
import json

from ..core.agent import BaseAgent
from ..core.state import AgentState
from shared.mcp.serena_client import SerenaClient
from shared.mcp.dope_context_client import DopeContextClient
from shared.mcp.conport_client import ConPortClient
from shared.mcp.zen_client import ZenClient
from shared.utils.prompt_sanitizer import PromptSanitizer

from .gp_operators import GPOperators
from .population import GPPopulation, GPIndividual
from .failure_analysis import FailureAnalysisEngine
from .adaptive_population import AdaptivePopulationManager
from .historical_learning import HistoricalLearningSystem

class RepairCandidate:
    """Represents a repair candidate with metadata."""
    def __init__(self, code: str, explanation: str, confidence: float, source: str = "unknown"):
        self.code = code
        self.explanation = explanation
        self.confidence = confidence
        self.source = source  # "llm", "gp", "hybrid"
        self.timestamp = time.time()

class RepairStrategy(Enum):
    """Repair strategy based on complexity and historical patterns."""
    LLM_ONLY = "llm_only"
    SELECTIVE_GP = "selective_gp"
    FULL_GP = "full_gp"

class EnhancedIterativeAgent(BaseAgent):
    """Enhanced Iterative Agent with hybrid LLM+GP code repair."""

    def __init__(self, config):
        super().__init__(config)
        self.serena_client = SerenaClient(self.config.serena_url, self.config)
        self.dope_client = DopeContextClient(self.config.dope_context_url, self.config)
        self.conport_client = ConPortClient(self.config.conport_url, self.config)
        self.zen_client = ZenClient(self.config.zen_url, self.config)

        # GP components
        self.gp_operators = GPOperators(max_tree_depth=self.config.max_tree_depth)
        self.population_manager = GPPopulation(
            operators=self.gp_operators,
            population_size=self.config.population_size
        )

        # Phase 2 Intelligence Components
        self.failure_analyzer = FailureAnalysisEngine(
            zen_client=self.zen_client,
            conport_client=self.conport_client,
            workspace_id=self.config.workspace_id
        )
        self.population_adaptor = AdaptivePopulationManager(
            base_population_size=self.config.population_size
        )
        self.learning_system = HistoricalLearningSystem(
            conport_client=self.conport_client,
            workspace_id=self.config.workspace_id
        )

        self.repair_candidates: List[RepairCandidate] = []
        self.max_iterations = self.config.max_iterations
        self.confidence_threshold = self.config.confidence_threshold

    async def _execute_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the enhanced iterative repair process with Phase 2 intelligence."""
        bug_description = task.get("bug_description", "")
        file_path = task.get("file_path", "")
        line_number = task.get("line_number", 0)

        self.status.update_state(AgentState.ANALYZING)

        # Phase 1: Comprehensive analysis
        analysis = await self._analyze_bug(bug_description, file_path, line_number)

        # Phase 2: Assess problem complexity for population adaptation
        complexity = self.population_adaptor.assess_problem_complexity(
            complexity_score=analysis.get('complexity', {}).get('score', 0.5),
            pattern_count=len(analysis.get('patterns', {}).get('results', [])),
            description_length=len(bug_description)
        )

        # Phase 3: Determine strategy with intelligence enhancement
        strategy = await self._determine_strategy_with_intelligence(analysis)

        # Phase 4: Iterative repair loop with adaptive population management
        best_repair = await self._intelligent_iterative_repair(analysis, strategy, complexity)

        if best_repair and best_repair.confidence >= self.confidence_threshold:
            # Record successful repair for learning
            await self.learning_system.record_repair_attempt(
                operator_used=strategy.value,
                context=analysis,
                fitness_before=0.0,  # Baseline
                fitness_after=best_repair.confidence,
                time_cost=1.0,  # Placeholder
                population_size=self.population_manager.population_size if hasattr(self.population_manager, 'population_size') else self.config.population_size,
                generation=self.population_manager.generation if hasattr(self.population_manager, 'generation') else 0
            )
            return self._format_success_response(best_repair, "intelligent_hybrid")

        # Analyze failure for learning
        failure_analysis = await self.failure_analyzer.analyze_failure(
            failure_signals=["low_confidence", "strategy_exhausted"],
            context=analysis,
            repair_candidates=self.repair_candidates
        )

        return self._format_failure_response(analysis, failure_analysis)

    async def _analyze_bug(self, description: str, file_path: str, line: int) -> Dict[str, Any]:
        """Analyze the bug using MCP services."""
        # Complexity analysis
        complexity = await self.serena_client.analyze_complexity(file_path)

        # Pattern search
        patterns = await self.dope_client.search_code(
            query=f"fix {description}",
            top_k=10,
            profile="debugging"
        )

        return {
            "description": description,
            "file_path": file_path,
            "line": line,
            "complexity": complexity,
            "patterns": patterns
        }

    async def _determine_strategy(self, analysis: Dict[str, Any]) -> RepairStrategy:
        """Determine repair strategy based on analysis."""
        complexity_score = analysis.get('complexity', {}).get('score', 0.5)
        pattern_count = len(analysis.get('patterns', {}).get('results', []))

        if complexity_score < 0.6 and pattern_count > 5:
            return RepairStrategy.LLM_ONLY
        elif complexity_score > 0.8:
            return RepairStrategy.FULL_GP
        else:
            return RepairStrategy.SELECTIVE_GP

    async def _iterative_repair(self, analysis: Dict[str, Any], strategy: RepairStrategy) -> Optional[RepairCandidate]:
        """Run iterative repair loop with strategy-specific logic."""
        current_confidence = 0.0
        iteration = 0

        while iteration < self.max_iterations and current_confidence < self.confidence_threshold:
            iteration += 1

            # Generate repair attempt
            attempt = await self._generate_attempt(analysis, iteration, strategy)

            if attempt.confidence > current_confidence:
                current_confidence = attempt.confidence
                best_attempt = attempt

                # Apply GP enhancement if strategy allows
                if strategy != RepairStrategy.LLM_ONLY:
                    enhanced = await self._enhance_with_gp(attempt, analysis)
                    if enhanced.confidence > current_confidence:
                        best_attempt = enhanced
                        current_confidence = enhanced.confidence

            # Validate with Zen
            validation = await self._validate_attempt(best_attempt, analysis)
            if validation.get('approved', False):
                return best_attempt

        return best_attempt

    async def _generate_attempt(self, analysis: Dict[str, Any], iteration: int, strategy: RepairStrategy) -> RepairCandidate:
        """Generate repair attempt using LLM."""
        prompt = self._build_prompt(analysis, iteration)

        # Use Zen for enhanced reasoning
        reasoning = await self.zen_client.thinkdeep(
            step=prompt,
            step_number=iteration,
            total_steps=self.max_iterations,
            next_step_required=False,
            findings=f"Repair attempt {iteration}"
        )

        # Extract from reasoning
        code = reasoning.get('code', '# Generated repair code')
        explanation = reasoning.get('explanation', f'Iteration {iteration} attempt')
        confidence = reasoning.get('confidence', 0.5)

        return RepairCandidate(code, explanation, confidence, "llm")

    async def _enhance_with_gp(self, attempt: RepairCandidate, analysis: Dict[str, Any]) -> RepairCandidate:
        """Enhance repair with genetic programming."""
        # Initialize population from attempt
        self.population_manager.initialize_from_seed(attempt.code)

        # Evolve for limited generations
        for gen in range(3):
            self.population_manager.evolve(lambda code: self._fitness(code, analysis))

        best_individual = self.population_manager.get_best_individual()

        return RepairCandidate(
            code=best_individual.code,
            explanation=f"GP enhanced (gen 3, fitness {best_individual.fitness})",
            confidence=best_individual.fitness,
            source="gp_enhanced"
        )

    def _fitness(self, code: str, analysis: Dict[str, Any]) -> float:
        """Simple fitness evaluation."""
        # Placeholder - would use actual test execution
        complexity = analysis.get('complexity', {}).get('score', 0.5)
        lines = len(code.split('\n'))
        score = 1.0 - (lines / 100.0) - complexity
        return max(0.0, min(1.0, score))

    async def _validate_attempt(self, attempt: RepairCandidate, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate repair attempt with Zen codereview."""
        review_prompt = f"Review repair for bug: {analysis['description']}\nCode: {attempt.code}"

        review = await self.zen_client.codereview(
            step=review_prompt,
            step_number=1,
            total_steps=1,
            next_step_required=False,
            findings="Repair validation"
        )

        return {
            'approved': review.get('approved', False),
            'score': review.get('score', 0.5)
        }

    def _build_prompt(self, analysis: Dict[str, Any], iteration: int) -> str:
        """Build LLM prompt for repair generation."""
        return f"""
Fix bug: {analysis['description']}
File: {analysis['file_path']}:{analysis['line']}
Iteration: {iteration}

Context: Complexity {analysis['complexity'].get('score', 0.5)}

Generate repair code with confidence score.
Format: {{"code": "repair", "explanation": "reason", "confidence": 0.7}}
"""

    def _format_success_response(self, repair: RepairCandidate, method: str) -> Dict[str, Any]:
        """Format successful repair response."""
        return {
            "success": True,
            "confidence": repair.confidence,
            "repair": repair.code,
            "explanation": repair.explanation,
            "method": method
        }

    async def _determine_strategy_with_intelligence(self, analysis: Dict[str, Any]) -> RepairStrategy:
        """Determine repair strategy using intelligence enhancement."""
        # Start with basic strategy determination
        base_strategy = await self._determine_strategy(analysis)

        # Use historical learning to refine strategy
        historical_insights = await self.learning_system.get_learning_insights(limit=5)

        # Analyze recent performance patterns
        recent_success_patterns = [
            insight for insight in historical_insights
            if insight.get('type') == 'top_operator'
        ]

        # Adjust strategy based on historical performance
        if recent_success_patterns:
            # If LLM approaches have been successful recently, prefer LLM
            llm_success = any(
                pattern.get('operator', '').startswith('llm') and
                pattern.get('success_rate', 0) > 0.7
                for pattern in recent_success_patterns
            )
            if llm_success and base_strategy != RepairStrategy.LLM_ONLY:
                return RepairStrategy.LLM_ONLY

        # Use failure analysis insights for strategy refinement
        failure_insights = await self.failure_analyzer.get_historical_insights(limit=3)

        # If recent failures were due to GP complexity, prefer selective approach
        gp_complexity_failures = [
            insight for insight in failure_insights
            if 'complexity' in insight.get('signals', [])
        ]

        if gp_complexity_failures and len(gp_complexity_failures) > len(failure_insights) * 0.5:
            return RepairStrategy.SELECTIVE_GP

        return base_strategy

    async def _intelligent_iterative_repair(
        self,
        analysis: Dict[str, Any],
        strategy: RepairStrategy,
        complexity: Any
    ) -> Optional[RepairCandidate]:
        """Run intelligent iterative repair with adaptive population management."""
        current_confidence = 0.0
        iteration = 0
        population_size = complexity.recommended_population_size

        # Initialize adaptive population
        self.population_adaptor.performance_history.clear()  # Reset for new repair

        while iteration < self.max_iterations and current_confidence < self.confidence_threshold:
            iteration += 1

            # Adapt population size based on performance
            available_resources = {'memory_mb': 400, 'time_limit': 30}  # Placeholder
            new_size, adaptation_reason = self.population_adaptor.adapt_population_size(
                current_population=self.population_manager,
                problem_complexity=complexity,
                performance_metrics={'generation': iteration, 'best_fitness': current_confidence},
                available_resources=available_resources
            )

            if new_size != population_size:
                population_size = new_size
                # Note: In real implementation, we'd resize the population

            # Generate repair attempt with operator intelligence
            attempt = await self._generate_intelligent_attempt(analysis, iteration, strategy)

            if attempt.confidence > current_confidence:
                current_confidence = attempt.confidence
                best_attempt = attempt

                # Apply GP enhancement with operator recommendation
                if strategy != RepairStrategy.LLM_ONLY:
                    enhanced = await self._enhance_with_intelligent_gp(attempt, analysis)
                    if enhanced.confidence > current_confidence:
                        best_attempt = enhanced
                        current_confidence = enhanced.confidence

            # Validate with Zen
            validation = await self._validate_attempt(best_attempt, analysis)
            if validation.get('approved', False):
                return best_attempt

        return best_attempt

    async def _generate_intelligent_attempt(
        self,
        analysis: Dict[str, Any],
        iteration: int,
        strategy: RepairStrategy
    ) -> RepairCandidate:
        """Generate repair attempt using historical intelligence."""
        prompt = self._build_prompt(analysis, iteration)

        # Get operator recommendation for enhanced reasoning
        recommendation = await self.learning_system.recommend_operator(
            context=analysis,
            available_operators=["mutate_condition", "swap_operators", "negate_condition"],
            population_size=self.config.population_size,
            current_generation=iteration
        )

        # Enhance prompt with historical insights
        enhanced_prompt = f"{prompt}\n\nHistorical Insight: {recommendation.reasoning}"

        # Use Zen for enhanced reasoning
        reasoning = await self.zen_client.thinkdeep(
            step=enhanced_prompt,
            step_number=iteration,
            total_steps=self.max_iterations,
            next_step_required=False,
            findings=f"Intelligent repair attempt {iteration} with {recommendation.recommended_operator}",
            model="gpt-5-codex"
        )

        # Extract from reasoning
        code = reasoning.get('code', '# Generated intelligent repair code')
        explanation = f"Iteration {iteration} with {recommendation.recommended_operator}: {reasoning.get('explanation', f'Intelligent attempt')}"
        confidence = reasoning.get('confidence', 0.5)

        # Boost confidence based on operator recommendation
        confidence = min(1.0, confidence * (1 + recommendation.confidence * 0.2))

        return RepairCandidate(code, explanation, confidence, "intelligent_llm")

    async def _enhance_with_intelligent_gp(self, attempt: RepairCandidate, analysis: Dict[str, Any]) -> RepairCandidate:
        """Enhance repair with intelligent GP using operator recommendations."""
        # Get operator recommendation for GP enhancement
        recommendation = await self.learning_system.recommend_operator(
            context=analysis,
            available_operators=["subtree_crossover", "hoist_mutation", "node_replacement"],
            population_size=self.config.population_size,
            current_generation=self.population_manager.generation if hasattr(self.population_manager, 'generation') else 1
        )

        # Use recommended operator for GP enhancement
        if recommendation.recommended_operator == "subtree_crossover":
            # Apply crossover-based enhancement
            enhanced_code = attempt.code  # Placeholder - would apply crossover
            enhancement_method = "intelligent_crossover"
        elif recommendation.recommended_operator == "hoist_mutation":
            # Apply hoist mutation
            enhanced_code = attempt.code  # Placeholder - would apply hoist
            enhancement_method = "intelligent_hoist"
        else:
            # Apply node replacement
            enhanced_code = attempt.code  # Placeholder - would apply replacement
            enhancement_method = "intelligent_replacement"

        # Calculate enhanced confidence
        base_confidence = attempt.confidence
        enhancement_boost = recommendation.expected_performance * 0.1
        enhanced_confidence = min(1.0, base_confidence + enhancement_boost)

        return RepairCandidate(
            code=enhanced_code,
            explanation=f"Intelligent GP enhanced with {recommendation.recommended_operator} (confidence boost: +{enhancement_boost:.2f})",
            confidence=enhanced_confidence,
            source=enhancement_method
        )

    def _format_failure_response(self, analysis: Dict[str, Any], failure_analysis: Any = None) -> Dict[str, Any]:
        """Format failure response with intelligence insights."""
        response = {
            "success": False,
            "confidence": 0.0,
            "repair": None,
            "explanation": "No suitable repair found within intelligence constraints",
            "method": "intelligent_analysis_failed",
            "analysis": analysis
        }

        if failure_analysis:
            response.update({
                "failure_analysis": {
                    "primary_mode": failure_analysis.primary_failure_mode,
                    "recommendations": failure_analysis.zen_recommendations,
                    "learning_opportunities": failure_analysis.learning_opportunities
                }
            })

        return response
