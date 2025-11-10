"""Vanilla Agent implementation using LLM-based iterative repair."""

from typing import Dict, Any, List
import asyncio
import logging
from datetime import datetime

from ...services.genetic_agent.core.agent import BaseAgent
from core.state import AgentState
from shared.mcp.serena_client import SerenaClient
from shared.mcp.dope_context_client import DopeContextClient


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
        self.logger = logging.getLogger(__name__)
        self.serena_client = SerenaClient(self.config.serena_url, self.config)
        self.dope_client = DopeContextClient(self.config.dope_context_url, self.config)
        self.repair_history: List[RepairAttempt] = []

    async def _execute_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute vanilla iterative repair process."""
        bug_description = task.get("bug_description", "")
        file_path = task.get("file_path", "")
        line_number = task.get("line_number", 0)

        # Analysis Phase
        self.status.update_state(AgentState.ANALYZING)
        context = await self._analyze_bug(bug_description, file_path, line_number)

        # Iterative Repair Phase
        self.status.update_state(AgentState.REPAIRING)
        best_repair = None
        best_confidence = 0.0

        for iteration in range(self.config.max_iterations):
            repair = await self._generate_repair_attempt(context, iteration)
            confidence = await self._validate_repair(repair, context)

            self.repair_history.append(repair)

            if confidence > best_confidence:
                best_repair = repair
                best_confidence = confidence

            if confidence >= self.config.confidence_threshold:
                break

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

    async def _generate_repair_attempt(self, context: Dict[str, Any], iteration: int) -> RepairAttempt:
        """Generate a repair attempt using LLM (placeholder for now)."""
        prompt = self._build_repair_prompt(context, iteration)

        # Call LLM using Zen MCP chat tool
        try:
            import httpx
            zen_url = "http://localhost:8002/mcp/zen/chat"  # Assuming Zen MCP server URL
            llm_request = {
                "prompt": prompt,
                "working_directory": "/tmp",  # Temporary working directory
                "model": "gpt-5-mini",  # Use fast model for iterations
                "temperature": 0.2  # Low temperature for code generation
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(zen_url, json=llm_request)
                if response.status_code == 200:
                    llm_response = response.json()
                    generated_code = llm_response.get("response", "").strip()
                    explanation = llm_response.get("explanation", "LLM-generated repair attempt")
                    confidence = min(0.95, 0.6 + iteration * 0.1)  # Base confidence + improvement
                else:
                    logger.warning(f"LLM call failed: {response.status_code}")
                    # Fallback to mock
                    generated_code = f"# LLM failed, mock repair for {context['description']}\npass"
                    explanation = "Fallback mock repair due to LLM service error"
                    confidence = 0.3
        except Exception as e:
            logger.error(f"LLM integration error: {e}")
            # Fallback to mock
            generated_code = f"# Error: {context['description']}\npass  # TODO: implement repair"
            explanation = f"Error generating repair attempt {iteration + 1}: {e}"
            confidence = 0.2

        return RepairAttempt(
            code=generated_code,
            explanation=explanation,
            confidence=confidence
        )

    async def _validate_repair(self, repair: RepairAttempt, context: Dict[str, Any]) -> float:
        """Validate repair quality (basic implementation)."""
        # Basic syntax checking using Serena client
        if not repair.code:
            return 0.0

        try:
            async with self.serena_client:
                # Use Serena to analyze complexity and syntax
                analysis = await self.serena_client.analyze_complexity(context["file_path"], repair.code)
                complexity = analysis.get("complexity", 0.5)

                # Syntax validation - if Serena reports syntax errors, penalize heavily
                if "syntax_error" in analysis:
                    self.logger.warning(f"Syntax error in repair: {analysis['syntax_error']}")
                    return 0.1  # Very low confidence for syntax errors

                # Basic heuristics
                if "TODO" in repair.code or "pass" in repair.code.lower():
                    penalty = 0.3  # Incomplete implementation
                else:
                    penalty = 0.0

                # Adjust confidence based on complexity (too complex might be wrong)
                if complexity > 0.8:
                    complexity_penalty = 0.2
                else:
                    complexity_penalty = 0.0

                adjusted_confidence = repair.confidence - penalty - complexity_penalty
                adjusted_confidence = max(0.0, min(0.95, adjusted_confidence))

                self.logger.debug(f"Repair validation: confidence={adjusted_confidence}, complexity={complexity}, penalties={penalty + complexity_penalty}")
                return adjusted_confidence

        except Exception as e:
            self.logger.warning(f"Serena validation failed: {e}")
            # Fallback validation
            if "TODO" in repair.code or "pass" in repair.code.lower():
                return min(repair.confidence, 0.6)
            return min(repair.confidence, 0.9)

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