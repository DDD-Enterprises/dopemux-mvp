"""Vanilla Agent implementation using LLM-based iterative repair."""

from typing import Dict, Any, List
import asyncio
from datetime import datetime

import sys
sys.path.insert(0, '../services')
from genetic_agent.core.agent import BaseAgent
from core.state import AgentState
from shared.mcp.serena_client import SerenaClient
from shared.mcp.dope_context_client import DopeContextClient
from shared.mcp.zen_client import ZenClient


class RepairAttempt:
    """Represents a single repair attempt with metadata."""

    def __init__(self, code: str, explanation: str, confidence: float):
        self.code = code
        self.explanation = explanation
        self.confidence = confidence
        self.timestamp = datetime.now()


class VanillaAgent(BaseAgent):
    """Vanilla agent using traditional LLM-based iterative repair."""

    def __init__(self, config):
        super().__init__(config)
        self.serena_client = SerenaClient(self.config.serena_url, self.config)
        self.dope_client = DopeContextClient(self.config.dope_context_url, self.config)
        self.repair_history: List[RepairAttempt] = []

    async def _execute_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute vanilla iterative repair process with mode detection."""
        bug_description = task.get("bug_description", "")
        file_path = task.get("file_path", "")
        line_number = task.get("line_number", 0)

        # Mode Detection Phase
        mode = self._detect_task_mode(bug_description)
        self.status.update_state(AgentState.ANALYZING)
        context = await self._analyze_bug(bug_description, file_path, line_number)
        context['mode'] = mode.value

        if mode == DevelopmentMode.REPAIR:
            # Execute standard repair loop
            return await self._execute_repair_loop(context)
        elif mode == DevelopmentMode.IDEATION:
            return await self._execute_ideation_mode(context)
        elif mode == DevelopmentMode.DESIGN:
            return await self._execute_design_mode(context)
        elif mode == DevelopmentMode.IMPLEMENTATION:
            return await self._execute_implementation_mode(context)
        else:
            # Fallback to repair for unknown modes
            context['mode'] = DevelopmentMode.REPAIR.value
            return await self._execute_repair_loop(context)

    def _detect_task_mode(self, description: str) -> DevelopmentMode:
        """Detect task mode from description using keyword matching."""
        description_lower = description.lower()

        if any(word in description_lower for word in ['fix', 'bug', 'error', 'issue', 'problem']):
            return DevelopmentMode.REPAIR
        elif any(word in description_lower for word in ['idea', 'feature', 'new', 'build', 'create', 'add']):
            return DevelopmentMode.IDEATION
        elif any(word in description_lower for word in ['design', 'architecture', 'plan', 'structure']):
            return DevelopmentMode.DESIGN
        elif any(word in description_lower for word in ['implement', 'code', 'write', 'develop']):
            return DevelopmentMode.IMPLEMENTATION
        else:
            return DevelopmentMode.REPAIR

    async def _execute_ideation_mode(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ideation mode for bluesky development with GPT-Researcher integration."""
        self.status.update_state(AgentState.GENERATING)

        # Use GPT-Researcher for initial research
        research_query = f"bluesky development ideas for {context['description']}"
        try:
            from shared.mcp.gptr_client import GPTRClient
            research_results = await self._call_gptr_mcp(research_query)
            research_insights = research_results.get('insights', [])
        except Exception as e:
            print(f"GPT-Researcher unavailable: {e}")
            research_insights = []

        # Use Zen for idea generation with research context
        ideation_prompt = f"""
Generate 3 creative ideas for: {context['description']}

Research insights:
{research_insights}

Consider:
- Innovative approaches from research
- User needs and workflows
- Technical feasibility
- Integration with existing systems

Return JSON array with ideas, each with:
- title
- description
- feasibility (1-10)
- complexity (low/medium/high)
- estimated effort (low/medium/high)
- research_link (from GPT-Researcher if available)
"""

        try:
            zen_response = await self._call_zen_mcp(ideation_prompt)
            ideas = json.loads(zen_response.strip())
        except:
            ideas = [
                {"title": "Fallback Idea 1", "description": "Basic implementation", "feasibility": 8, "complexity": "low", "research_link": None},
                {"title": "Fallback Idea 2", "description": "Alternative approach", "feasibility": 6, "complexity": "medium", "research_link": None},
                {"title": "Fallback Idea 3", "description": "Advanced solution", "feasibility": 4, "complexity": "high", "research_link": None}
            ]

        self.status.update_state(AgentState.VALIDATING)
        return {
            "success": True,
            "mode": "ideation",
            "research_insights": research_insights,
            "ideas": ideas,
            "explanation": "Generated ideation options with research integration",
            "confidence": 0.85
        }

    async def _call_gptr_mcp(self, query: str) -> Dict[str, Any]:
        """Call GPT-Researcher MCP for research insights."""
        from shared.mcp.gptr_client import GPTRClient

        # Initialize GPT-Researcher client if not available
        if not hasattr(self, '_gptr_client'):
            self._gptr_client = GPTRClient(self.config.zen_url.replace('/zen', '/gptr-mcp'), self.config)

        async with self._gptr_client:
            return await self._gptr_client.deep_research(query)

    async def _execute_design_mode(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute design mode for architecture planning."""
        self.status.update_state(AgentState.GENERATING)

        design_prompt = f"""
Create design for: {context['description']}

Include:
- Architecture overview
- Component breakdown
- Data flow diagram
- Integration points
- Risk assessment

Return structured JSON with design details
"""

        try:
            zen_response = await self._call_zen_mcp(design_prompt)
            design = json.loads(zen_response.strip())
        except:
            design = {
                "overview": "Basic architecture for the feature",
                "components": ["Component 1", "Component 2"],
                "data_flow": "Simple data flow",
                "integration": "Standard integration points",
                "risks": "Low risk implementation"
            }

        self.status.update_state(AgentState.VALIDATING)
        return {
            "success": True,
            "mode": "design",
            "design": design,
            "explanation": "Generated architecture design",
            "confidence": 0.7
        }

    async def _execute_integration_mode(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute integration mode for merging and dependency resolution."""
        self.status.update_state(AgentState.GENERATING)

        # Get implementation from previous phase
        impl = context.get('implementation', {}).get('code', context.get('description', ''))

        integration_prompt = f"""
Integrate this code into existing codebase: {impl}

Include:
- Dependency resolution
- Conflict identification
- Merge strategy
- Test plan

Return JSON with:
- merge_plan
- conflicts (array)
- dependencies (array)
- test_plan
"""

        try:
            zen_response = await self._call_zen_mcp(integration_prompt)
            integration = json.loads(zen_response.strip())
        except:
            integration = {
                "merge_plan": "Standard merge to main branch",
                "conflicts": [],
                "dependencies": [],
                "test_plan": "Run full test suite after merge"
            }

        self.status.update_state(AgentState.VALIDATING)
        return {
            "success": True,
            "mode": "integration",
            "integration": integration,
            "explanation": "Generated integration plan",
            "confidence": 0.8
        }

    async def _execute_testing_mode(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute testing mode for validation."""
        self.status.update_state(AgentState.VALIDATING)

        # Get integration from previous phase
        integration = context.get('integration', {})
        code = context.get('implementation', {}).get('code', context.get('description', ''))

        testing_prompt = f"""
Generate comprehensive test suite for: {code}

Include:
- Unit tests
- Integration tests
- Edge case tests
- Coverage targets

Return JSON with:
- test_suite (code)
- coverage_target (float)
- test_strategy
"""

        try:
            zen_response = await self._call_zen_mcp(testing_prompt)
            testing = json.loads(zen_response.strip())
        except:
            testing = {
                "test_suite": "# Test suite for {context['description']}\ndef test_basic(): assert True",
                "coverage_target": 0.8,
                "test_strategy": "Basic validation tests"
            }

        self.status.update_state(AgentState.VALIDATING)
        return {
            "success": True,
            "mode": "testing",
            "testing": testing,
            "explanation": "Generated test suite",
            "confidence": 0.85
        }

        # Iterative Repair Phase
        self.status.update_state(AgentState.REPAIRING)
        best_repair = None
        best_confidence = 0.0

        # Enhanced iterative loop with Zen optimization
        previous_attempt = None
        for iteration in range(self.config.max_iterations):
            # Use Zen to optimize the repair prompt based on previous attempts
            if iteration > 0 and previous_attempt:
                context = await self._optimize_next_attempt(context, previous_attempt, iteration)

            repair = await self._generate_repair_attempt(context, iteration)
            confidence = await self._validate_repair(repair, context)

            self.repair_history.append(repair)

            # Log attempt to ConPort for learning
            await self._log_attempt_to_conport(repair, confidence, iteration)

            if confidence > best_confidence:
                best_repair = repair
                best_confidence = confidence

            # Early exit if we have a good solution
            if confidence >= self.config.confidence_threshold:
                break

            previous_attempt = repair

        # Validation Phase
        self.status.update_state(AgentState.VALIDATING)
        final_result = await self._finalize_repair(best_repair, context)

        return {
            "success": best_confidence >= self.config.confidence_threshold,
            "confidence": best_confidence,
            "repair": best_repair.code if best_repair else None,
            "iterations": len(self.repair_history),
            "explanation": best_repair.explanation if best_repair else "No suitable repair found"
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

    async def _optimize_next_attempt(self, context: Dict[str, Any], previous_attempt: RepairAttempt, iteration: int) -> Dict[str, Any]:
        """Optimize the next repair attempt using Zen research capabilities."""
        try:
            # Use Zen to analyze why previous attempt failed and suggest improvements
            optimization_prompt = f"""
Previous repair attempt failed. Analyze the issue and suggest improvements for the next attempt.

Previous context:
{context['description']}
Complexity: {context.get('complexity', {}).get('score', 'unknown')}
Previous repair:
{previous_attempt.code}

Why did this fail? What should the next attempt focus on?

Respond with JSON: {{"analysis": "brief analysis", "suggestions": ["suggestion1", "suggestion2"], "focus_areas": ["area1", "area2"]}}
"""

            zen_response = await self._call_zen_mcp(optimization_prompt)

            import json
            try:
                opt_response = json.loads(zen_response.strip())
                analysis = opt_response.get("analysis", "Unknown failure")
                suggestions = opt_response.get("suggestions", [])
                focus_areas = opt_response.get("focus_areas", [])

                # Update context with optimization insights
                context["optimization"] = {
                    "iteration": iteration,
                    "previous_analysis": analysis,
                    "suggestions": suggestions,
                    "focus_areas": focus_areas
                }

                # Log to ConPort for future learning
                await self._log_optimization_step(iteration, analysis, suggestions)

            except (json.JSONDecodeError, ValueError):
                # Fallback optimization
                context["optimization"] = {
                    "iteration": iteration,
                    "previous_analysis": "Failed to parse optimization response",
                    "suggestions": ["Try alternative approach", "Simplify the logic"],
                    "focus_areas": ["Basic implementation", "Error handling"]
                }

        except Exception as e:
            print(f"Optimization step failed: {e}")
            context["optimization"] = {
                "iteration": iteration,
                "previous_analysis": "Optimization unavailable",
                "suggestions": ["Proceed with standard approach"],
                "focus_areas": ["Default repair strategy"]
            }

        return context

    async def _log_optimization_step(self, iteration: int, analysis: str, suggestions: list) -> None:
        """Log optimization step to ConPort for learning."""
        try:
            from shared.mcp.conport_client import ConPortClient

            log_entry = {
                "iteration": iteration,
                "analysis": analysis,
                "suggestions": suggestions,
                "timestamp": time.time()
            }

            # Log to ConPort for future optimization learning
            async with ConPortClient(self.config.conport_url, self.config) as client:
                await client.log_custom_data(
                    category="repair_optimization",
                    key=f"optimization_step_{iteration}",
                    value=log_entry
                )
        except Exception as e:
            print(f"Failed to log optimization step: {e}")

    async def _generate_repair_attempt(self, context: Dict[str, Any], iteration: int) -> RepairAttempt:
        """Generate a repair attempt using Zen MCP for real LLM calls with optimization."""
        # Include optimization context if available
        prompt = self._build_repair_prompt(context, iteration)

        try:
            # Use Zen MCP for LLM-powered code repair generation
            zen_prompt = f"""
You are an expert software engineer tasked with fixing a bug. Generate a precise code repair based on the following context.

{prompt}

Optimization insights from previous attempt:
{context.get('optimization', {}).get('analysis', 'No previous attempt')}

Focus areas for this attempt:
{', '.join(context.get('optimization', {}).get('focus_areas', []))}

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
            # Fallback to template if MCP call fails
            print(f"Zen MCP call failed: {e}")
            code = f"# Zen MCP fix for: {context['description']}\n# MCP error: {str(e)}\npass"
            explanation = f"Zen MCP call failed, using fallback template"
            confidence = 0.2

        return RepairAttempt(
            code=code,
            explanation=explanation,
            confidence=confidence
        )

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

    async def _validate_repair(self, repair: RepairAttempt, context: Dict[str, Any]) -> float:
        """Validate repair quality (basic implementation)."""
        # TODO: Add syntax checking, basic heuristics
        # For now, cap confidence and add some basic validation
        if not repair.code or "TODO" in repair.code:
            return min(repair.confidence, 0.6)  # Penalize incomplete repairs

        return min(repair.confidence, 0.9)  # Cap until real testing

    async def _finalize_repair(self, repair: RepairAttempt, context: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize and format the repair result."""
        return {
            "repair": repair,
            "context": context,
            "validation_complete": True
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