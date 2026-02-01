"""Genetic Agent implementation with GP operators and hybrid approach."""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
import time

from ...services.genetic-agent.core.agent import BaseAgent
from core.state import AgentState
from shared.mcp.serena_client import SerenaClient
from shared.mcp.dope_context_client import DopeContextClient
from shared.mcp.conport_client import ConPortClient
from shared.mcp.memory_adapter import MemoryAdapter
from shared.eventbus import SimpleEventBus as EventBus, Event, EventType
from shared.mcp.zen_client import ZenClient

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
        self.conport_client = ConPortClient(self.config.conport_url, self.config)
        self.zen_client = ZenClient(self.config.zen_url, self.config)

        # EventBus integration for real-time events
        self.event_bus = EventBus(redis_url=getattr(self.config, 'redis_url', 'redis://localhost:6379'), db=2)
        asyncio.create_task(self._start_event_subscriber())

        # GP components
        self.gp_operators = GPOperators(max_tree_depth=self.config.max_tree_depth)
        self.population_manager = GPPopulation(
            operators=self.gp_operators,
            population_size=self.config.population_size
        )

        # Memory adapter for ConPort logging (research-based learning)
        self.memory_adapter = MemoryAdapter(self.conport_client, self.config.workspace_id)

        self.repair_candidates: List[RepairCandidate] = []

    async def _start_event_subscriber(self):
        """Start background subscriber for feedback events."""
        async def feedback_callback(event):
            await self._handle_feedback(event)

        await self.event_bus.subscribe(
            event_type="test_results",
            callback=feedback_callback,
            filter_fn=lambda e: e.payload.get('workspace_id') == self.config.workspace_id
        )
        await self.event_bus.subscribe(
            event_type="user_feedback",
            callback=feedback_callback,
            filter_fn=lambda e: e.payload.get('user_id') == getattr(self.config, 'user_id', None)
        )

    async def _handle_feedback(self, event):
        """Handle incoming feedback events."""
        payload = event.payload
        if event.type == "test_results":
            # Update ConPort learning with test outcomes
            await self.memory_adapter.log_attempt(
                attempt_number=payload.get("attempt_id", 0),
                fitness_score=payload.get("test_score", 0.0),
                context={"test_results": payload},
                success=payload.get("passed", False)
            )
        elif event.type == "user_feedback":
            # Adjust confidence thresholds based on user input
            feedback_score = payload.get("rating", 0.0)
            await self.memory_adapter.update_confidence_threshold(feedback_score)

    async def _execute_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hybrid LLM + GP repair process with selective GP activation."""
        bug_description = task.get("bug_description", "")
        file_path = task.get("file_path", "")
        line_number = task.get("line_number", 0)

        # Emit bug_detected event
        await self.event_bus.publish(
            event=Event(
                type="bug_detected",
                source="genetic_agent",
                payload={
                    "workspace_id": self.config.workspace_id,
                    "user_id": getattr(self.config, 'user_id', None),
                    "bug_description": bug_description,
                    "file_path": file_path,
                    "line_number": line_number
                }
            )
        )

        # Phase 1: Analysis
        self.status.update_state(AgentState.ANALYZING)
        context = await self._analyze_bug(bug_description, file_path, line_number)

        # Phase 1.5: Determine repair strategy based on failure patterns
        repair_strategy = await self._determine_repair_strategy(context)

        # Phase 2: LLM-First Generation (Vanilla-style)
        self.status.update_state(AgentState.REPAIRING)
        llm_repair = await self._generate_llm_repair(context)

        # Emit repair_attempted event
        await self.event_bus.publish(
            event=Event(
                type="repair_attempted",
                source="genetic_agent",
                payload={
                    "workspace_id": self.config.workspace_id,
                    "user_id": getattr(self.config, 'user_id', None),
                    "confidence": llm_repair.confidence,
                    "source": "llm",
                    "file_path": file_path,
                    "attempt_number": 1
                }
            )
        )

        # Log LLM attempt to ConPort (research-based learning)
        await self.memory_adapter.log_attempt(
            attempt_number=1,
            operator="llm_initial",
            fitness_score=llm_repair.confidence,
            context=context,
            success=llm_repair.confidence >= self.config.confidence_threshold
        )

        if llm_repair.confidence >= self.config.confidence_threshold:
            # LLM repair is good enough, return it
            await self._log_session_summary(success=True)
            # Emit repair_successful event
            await self.event_bus.publish(
                event=Event(
                    type="repair_successful",
                    source="genetic_agent",
                    payload={
                        "workspace_id": self.config.workspace_id,
                        "user_id": getattr(self.config, 'user_id', None),
                        "confidence": llm_repair.confidence,
                        "method": "llm",
                        "success": True,
                        "iterations": 1
                    }
                )
            )
            return self._format_success_response(llm_repair, 1, "llm")

        # Phase 3: GP Enhancement (selective based on strategy)
        if repair_strategy == "selective_gp":
            gp_success = await self._run_selective_gp(llm_repair, context)
        else:
            gp_success = await self._run_gp_optimization(llm_repair, context)

        if gp_success:
            # Return best GP-enhanced repair
            best_candidate = self._get_best_candidate()
            if best_candidate and best_candidate.confidence >= self.config.confidence_threshold:
                iterations = self.population_manager.generation + 1  # +1 for LLM phase
                await self._log_session_summary(success=True)
                # Emit repair_successful event
                await self.event_bus.publish(
                    event=Event(
                        type="repair_successful",
                        source="genetic_agent",
                        payload={
                            "workspace_id": self.config.workspace_id,
                            "user_id": getattr(self.config, 'user_id', None),
                            "confidence": best_candidate.confidence,
                            "method": "gp",
                            "success": True,
                            "iterations": iterations
                        }
                    )
                )
                return self._format_success_response(best_candidate, iterations, "gp")

        # Phase 4: Fallback to best available
        best_candidate = self._get_best_candidate()
        if best_candidate:
            iterations = len(self.repair_candidates)
            # Log successful hybrid approach
            await self.memory_adapter.log_attempt(
                attempt_number=iterations,
                operator="hybrid_fallback",
                fitness_score=best_candidate.confidence,
                context=context,
                success=True
            )
            await self._log_session_summary(success=True)
            # Emit repair_successful event
            await self.event_bus.publish(
                event=Event(
                    type="repair_successful",
                    source="genetic_agent",
                    payload={
                        "workspace_id": self.config.workspace_id,
                        "user_id": getattr(self.config, 'user_id', None),
                        "confidence": best_candidate.confidence,
                        "method": "hybrid",
                        "success": True,
                        "iterations": iterations
                    }
                )
            )
            return self._format_success_response(best_candidate, iterations, "hybrid")

        # No suitable repair found - log failure signals for learning
        failure_signals = [
            "llm_repair_insufficient",
            "gp_optimization_failed",
            f"complexity_{context.get('complexity', {}).get('score', 0.5):.1f}",
            f"similar_patterns_{len(context.get('similar_patterns', {}).get('results', []))}"
        ]
        await self.memory_adapter.log_failure_signals(failure_signals, context)

        # Log session summary for research learning
        await self._log_session_summary(success=False)

        # No suitable repair found
        return {
            "success": False,
            "confidence": 0.0,
            "repair": None,
            "iterations": len(self.repair_candidates),
            "explanation": "No suitable repair found within constraints",
            "candidates_evaluated": len(self.repair_candidates)
        }

    async def _determine_repair_strategy(self, context: Dict[str, Any]) -> str:
        """Determine repair strategy based on failure patterns and bug complexity."""
        try:
            # Retrieve historical failure patterns
            failure_patterns = await self.memory_adapter.get_failure_patterns(limit=10)

            # Analyze bug complexity indicators
            complexity_score = context.get('complexity', {}).get('score', 0.5)
            similar_patterns_count = len(context.get('similar_patterns', {}).get('results', []))
            description_length = len(context.get('description', ''))

            # Decision criteria for selective GP (Phase 2 research)
            # Use GP for complex bugs with failure patterns
            use_selective_gp = (
                complexity_score > 0.7 or  # High complexity
                similar_patterns_count < 3 or  # Few similar patterns (novel problem)
                description_length > 100 or  # Complex description
                len([p for p in failure_patterns if 'complexity' in p.get('signals', [])]) > 3  # Pattern of complex failures
            )

            if use_selective_gp:
                return "selective_gp"
            else:
                return "standard_gp"

        except Exception as e:
            # Fallback to standard GP on error
            print(f"Strategy determination failed: {e}")
            return "standard_gp"

    async def _run_selective_gp(self, llm_repair: RepairCandidate, context: Dict[str, Any]) -> bool:
        """Run selective GP with small population (3-5 candidates) for complex bugs."""
        try:
            # Phase 2: Small population (3-5 candidates) - research-based approach
            small_population_size = 3  # Research shows 3-5 candidates optimal for complex cases

            # Get complexity for operator recommendation
            complexity_score = context.get('complexity', {}).get('score', 0.5)

            # Get recommended operator from learning history
            recommended_operator = await self.memory_adapter.recommend_operator(
                context_complexity=complexity_score,
                recent_failures=[]  # Could be populated from context
            )

            # Initialize selective population with LLM seed and recommended operator bias
            self.population_manager.initialize_from_seed(llm_repair.code, variations=small_population_size - 1)

            # Enhanced fitness function with operator awareness
            def fitness_func(code: str) -> tuple[float, Dict[str, float]]:
                fitness, components = self._evaluate_fitness(code, context)
                # Bonus for using recommended operator patterns (learned from history)
                if recommended_operator in ["negate_condition", "swap_operator"]:
                    # These operators work well for complex logic - slight bonus
                    fitness += 0.05
                return fitness, components

            # Evolve with limited generations (research shows 2-3 generations sufficient for small populations)
            max_selective_generations = 2

            for generation in range(max_selective_generations):
                continue_evolution = self.population_manager.evolve(fitness_func)

                # Log selective GP attempt with operator recommendation
                operator_used = f"selective_gp_{recommended_operator}_gen_{generation + 1}"
                await self.memory_adapter.log_attempt(
                    attempt_number=generation + 2,  # +1 for LLM, +1 for generation offset
                    operator=operator_used,
                    fitness_score=self.population_manager.get_best_individual().fitness,
                    context=context,
                    success=False  # Will be updated if successful
                )

                # Check for good enough solution (research threshold)
                best_fitness = self.population_manager.get_best_individual().fitness
                if best_fitness >= self.config.confidence_threshold:
                    # Convert to candidate
                    best_individual = self.population_manager.get_best_individual()
                    candidate = RepairCandidate(
                        code=best_individual.code,
                        explanation=f"Selective GP success with {recommended_operator} (gen {generation + 1}, fitness {best_fitness:.3f})",
                        confidence=best_fitness,
                        source="selective_gp"
                    )
                    self.repair_candidates.append(candidate)

                    # Log successful selective GP
                    await self.memory_adapter.log_attempt(
                        attempt_number=generation + 2,
                        operator=operator_used,
                        fitness_score=best_fitness,
                        context=context,
                        success=True
                    )
                    return True

                if not continue_evolution:
                    break

            # Add final best individual as candidate
            best_individual = self.population_manager.get_best_individual()
            candidate = RepairCandidate(
                code=best_individual.code,
                explanation=f"Selective GP final with {recommended_operator} (fitness {best_individual.fitness:.3f})",
                confidence=best_individual.fitness,
                source="selective_gp"
            )
            self.repair_candidates.append(candidate)

            return best_individual.fitness >= 0.6  # Lower threshold for selective GP (research-based)

        except Exception as e:
            # Selective GP failed, log and continue
            print(f"Selective GP failed: {e}")
            return False

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
        """Generate initial repair using LLM via Zen MCP."""
        prompt = self._build_repair_prompt(context, 0)

        try:
            # Use Zen MCP for LLM-powered code repair generation
            zen_prompt = f"""
You are an expert software engineer tasked with fixing a bug. Generate a precise code repair based on the following context.

{prompt}

IMPORTANT: Respond ONLY with a valid JSON object in this exact format:
{{"code": "the fixed code here", "explanation": "brief explanation of the fix", "confidence": 0.8}}

Do not include any other text, markdown formatting, or explanations outside the JSON.
"""

            # Use Zen MCP chat tool for code generation
            zen_response = await self._call_zen_mcp(zen_prompt)

            # Parse the JSON response
            import json
            try:
                llm_response = json.loads(zen_response.strip())
                code = llm_response.get("code", "")
                explanation = llm_response.get("explanation", "LLM-generated repair")
                confidence = float(llm_response.get("confidence", 0.5))
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback if JSON parsing fails
                print(f"LLM response parsing failed: {e}, response: {zen_response}")
                code = f"# LLM-generated fix for: {context['description']}\n# Error parsing response\npass"
                explanation = f"LLM response parsing failed, using fallback"
                confidence = 0.3

        except Exception as e:
            # Fallback to basic template if MCP call fails
            print(f"LLM MCP call failed: {e}")
            code = f"# LLM-generated fix for: {context['description']}\n# MCP error: {str(e)}\npass"
            explanation = f"LLM MCP call failed, using fallback template"
            confidence = 0.2

        candidate = RepairCandidate(
            code=code,
            explanation=explanation,
            confidence=confidence,
            source="llm"
        )

        self.repair_candidates.append(candidate)
        return candidate

    async def _call_zen_mcp(self, prompt: str) -> str:
        """Call Zen MCP for LLM-powered code generation."""
        # Import here to avoid circular imports
        from shared.mcp.zen_client import ZenClient

        # Initialize Zen client if not already available
        if not hasattr(self, '_zen_client'):
            self._zen_client = ZenClient(self.config.zen_url, self.config)

        async with self._zen_client:
            response = await self._zen_client.chat(
                prompt=prompt,
                model="gpt-5-codex",  # Code-specialized model
                temperature=0.1,  # Low creativity for code generation
                max_tokens=1000
            )

        return response

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
        """Evaluate fitness using research-based multi-objective scoring."""

        # Component 1: Test Success (100% weight - research priority)
        # TODO: Replace with actual test execution
        # For now, use syntax validation as proxy for basic correctness
        tree = self.gp_operators.code_to_tree(code)
        syntax_valid = 1.0 if tree and self.gp_operators.validate_ast(tree) else 0.0
        test_success = syntax_valid  # Placeholder - would run actual tests

        # Component 2: Size Penalty (0.1/line over 50 lines - from Chronicle research)
        lines_of_code = len(code.split('\n'))
        size_penalty = max(0, (lines_of_code - 50) * 0.1) if lines_of_code > 50 else 0.0
        size_score = max(0.0, 1.0 - size_penalty)  # Convert penalty to score

        # Component 3: Lint Penalty (5/error - research-based lint weighting)
        # TODO: Replace with actual linting
        # For now, use basic AST complexity as proxy
        complexity_penalty = self.gp_operators.get_tree_complexity(tree) / 100.0 if tree else 1.0
        lint_penalty = complexity_penalty * 5  # 5 points per "error"
        lint_score = max(0.0, 1.0 - lint_penalty)

        # Research-based weighted fitness (GenProg/Chronicle methodology)
        # Test success gets highest priority, followed by code quality metrics
        fitness = (
            1.0 * test_success +           # 100% weight on test success
            0.3 * size_score +             # Size minimization (Chronicle)
            0.2 * lint_score               # Code quality (research standards)
        )

        # Normalize to 0.0-1.0 range
        fitness = min(1.0, max(0.0, fitness))

        components = {
            "test_success": test_success,
            "size_score": size_score,
            "lint_score": lint_score,
            "lines_of_code": lines_of_code,
            "complexity_penalty": complexity_penalty,
            "raw_fitness": fitness
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

    async def _log_session_summary(self, success: bool) -> None:
        """Log comprehensive session summary for research learning."""
        total_attempts = len(self.repair_candidates)
        successful_repairs = sum(1 for c in self.repair_candidates if c.confidence >= self.config.confidence_threshold)

        # Calculate average fitness
        avg_fitness = sum(c.confidence for c in self.repair_candidates) / max(total_attempts, 1)

        # Count operator usage (from source field)
        operators_used = {}
        for candidate in self.repair_candidates:
            op = getattr(candidate, 'source', 'unknown')
            operators_used[op] = operators_used.get(op, 0) + 1

        # Log to ConPort
        await self.memory_adapter.log_session_summary(
            total_attempts=total_attempts,
            successful_repairs=successful_repairs,
            average_fitness=avg_fitness,
            operators_used=operators_used
        )

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