"""Genetic Agent implementation with GP operators and hybrid approach."""

import asyncio
from typing import Dict, Any, List, Optional
import time

from ..core.agent import BaseAgent
from ..core.state import AgentState
from ..shared.mcp.serena_client import SerenaClient
from ..shared.mcp.dope_context_client import DopeContextClient

from .gp_operators import GPOperators
from .population import GPPopulation, GPIndividual


class RepairCandidate:
    """Represents a repair candidate with metadata."""

    def __init__(self, code: str, explanation: str, confidence: float, source: str = "unknown"):
        self.code = code
        self.explanation = explanation
        self.confidence = confidence
        self.source = source  # "llm", "gp", "hybrid"
        self.timestamp = time.time()


class GeneticAgent(BaseAgent):
    """Genetic agent using hybrid LLM + GP approach for code repair."""

    def __init__(self, config):
        super().__init__(config)
        self.serena_client = SerenaClient(self.config.serena_url, self.config)
        self.dope_client = DopeContextClient(self.config.dope_context_url, self.config)

        # GP components
        self.gp_operators = GPOperators(max_tree_depth=self.config.max_tree_depth)
        self.population_manager = GPPopulation(
            operators=self.gp_operators,
            population_size=self.config.population_size
        )

        self.repair_candidates: List[RepairCandidate] = []

    async def _execute_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hybrid LLM + GP repair process."""
        bug_description = task.get("bug_description", "")
        file_path = task.get("file_path", "")
        line_number = task.get("line_number", 0)

        # Phase 1: Analysis
        self.status.update_state(AgentState.ANALYZING)
        context = await self._analyze_bug(bug_description, file_path, line_number)

        # Phase 2: LLM-First Generation (Vanilla-style)
        self.status.update_state(AgentState.REPAIRING)
        llm_repair = await self._generate_llm_repair(context)

        if llm_repair.confidence >= self.config.confidence_threshold:
            # LLM repair is good enough, return it
            return self._format_success_response(llm_repair, 1, "llm")

        # Phase 3: GP Enhancement
        gp_success = await self._run_gp_optimization(llm_repair, context)

        if gp_success:
            # Return best GP-enhanced repair
            best_candidate = self._get_best_candidate()
            if best_candidate and best_candidate.confidence >= self.config.confidence_threshold:
                iterations = self.population_manager.generation + 1  # +1 for LLM phase
                return self._format_success_response(best_candidate, iterations, "gp")

        # Phase 4: Fallback to best available
        best_candidate = self._get_best_candidate()
        if best_candidate:
            iterations = len(self.repair_candidates)
            return self._format_success_response(best_candidate, iterations, "hybrid")

        # No suitable repair found
        return {
            "success": False,
            "confidence": 0.0,
            "repair": None,
            "iterations": len(self.repair_candidates),
            "explanation": "No suitable repair found within constraints",
            "candidates_evaluated": len(self.repair_candidates)
        }

    async def _analyze_bug(self, description: str, file_path: str, line: int) -> Dict[str, Any]:
        """Analyze the bug using MCP services."""
        try:
            async with self.serena_client:
                complexity = await self.serena_client.analyze_complexity(file_path, "")
        except Exception:
            complexity = {"score": 0.5, "error": "Serena unavailable"}

        try:
            async with self.dope_client:
                similar_repairs = await self.dope_client.search_code(f"fix {description}")
        except Exception:
            similar_repairs = {"results": [], "error": "Dope-Context unavailable"}

        return {
            "description": description,
            "file_path": file_path,
            "line": line,
            "complexity": complexity,
            "similar_patterns": similar_repairs
        }

    async def _generate_llm_repair(self, context: Dict[str, Any]) -> RepairCandidate:
        """Generate initial repair using LLM (vanilla approach)."""
        prompt = self._build_repair_prompt(context, 0)

        # TODO: Replace with actual LLM call via MCP
        # For now, create a mock LLM response
        mock_response = {
            "code": f"# LLM-generated fix for: {context['description']}\npass  # TODO: implement repair",
            "explanation": f"LLM-generated repair attempt for: {context['description']}",
            "confidence": 0.6  # Lower confidence to trigger GP optimization
        }

        candidate = RepairCandidate(
            code=mock_response["code"],
            explanation=mock_response["explanation"],
            confidence=mock_response["confidence"],
            source="llm"
        )

        self.repair_candidates.append(candidate)
        return candidate

    async def _run_gp_optimization(self, llm_repair: RepairCandidate, context: Dict[str, Any]) -> bool:
        """Run GP optimization on the LLM-generated repair."""
        try:
            # Initialize population with LLM repair as seed
            self.population_manager.initialize_from_seed(llm_repair.code)

            # Define fitness function
            def fitness_func(code: str) -> tuple[float, Dict[str, float]]:
                return self._evaluate_fitness(code, context)

            # Evolve population
            max_generations = self.config.max_generations
            for generation in range(max_generations):
                continue_evolution = self.population_manager.evolve(fitness_func)

                # Check for good enough solution
                best_individual = self.population_manager.get_best_individual()
                if best_individual.fitness >= self.config.confidence_threshold:
                    # Convert to candidate
                    candidate = RepairCandidate(
                        code=best_individual.code,
                        explanation=f"GP-optimized repair (gen {generation + 1})",
                        confidence=best_individual.fitness,
                        source="gp"
                    )
                    self.repair_candidates.append(candidate)
                    return True

                if not continue_evolution:
                    break

            # Add final best individual as candidate
            best_individual = self.population_manager.get_best_individual()
            candidate = RepairCandidate(
                code=best_individual.code,
                explanation=f"GP-optimized repair (final)",
                confidence=best_individual.fitness,
                source="gp"
            )
            self.repair_candidates.append(candidate)

            return best_individual.fitness >= 0.5  # At least somewhat successful

        except Exception as e:
            # GP failed, log and continue
            print(f"GP optimization failed: {e}")
            return False

    def _evaluate_fitness(self, code: str, context: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Evaluate fitness of a code repair."""
        # Component 1: Correctness (syntax validity)
        tree = self.gp_operators.code_to_tree(code)
        correctness = 1.0 if tree and self.gp_operators.validate_ast(tree) else 0.0

        # Component 2: Simplicity (code length minimization)
        # Prefer shorter, simpler repairs
        simplicity = max(0.0, 1.0 - (len(code) / 1000.0))  # Penalize very long code

        # Component 3: Execution (placeholder - would run tests)
        execution = 0.5  # Placeholder - real implementation would run tests

        # Weighted fitness
        fitness = (
            self.config.correctness_weight * correctness +
            self.config.simplicity_weight * simplicity +
            self.config.execution_weight * execution
        )

        components = {
            "correctness": correctness,
            "simplicity": simplicity,
            "execution": execution
        }

        return fitness, components

    def _get_best_candidate(self) -> Optional[RepairCandidate]:
        """Get the candidate with highest confidence."""
        if not self.repair_candidates:
            return None
        return max(self.repair_candidates, key=lambda x: x.confidence)

    def _format_success_response(self, candidate: RepairCandidate, iterations: int, method: str) -> Dict[str, Any]:
        """Format successful repair response."""
        return {
            "success": True,
            "confidence": candidate.confidence,
            "repair": candidate.code,
            "iterations": iterations,
            "explanation": candidate.explanation,
            "method": method,
            "candidates_evaluated": len(self.repair_candidates)
        }

    def _build_repair_prompt(self, context: Dict[str, Any], iteration: int) -> str:
        """Build the repair prompt for LLM."""
        return f"""
Fix this bug: {context['description']}

File: {context['file_path']}
Line: {context['line']}

Context:
- Complexity score: {context.get('complexity', {}).get('score', 'unknown')}
- Similar patterns found: {len(context.get('similar_patterns', {}).get('results', []))}

Previous attempts: {iteration}

Generate a code repair with explanation and confidence score (0.0-1.0).
Format: {{"code": "...", "explanation": "...", "confidence": 0.8}}
"""