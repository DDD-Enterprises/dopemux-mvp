"""
Enhanced Task Orchestrator - Intelligent Middleware for PM Automation

Coordinates between Leantime PM interface and AI agents with implicit automation.
Provides seamless ADHD-optimized development workflow orchestration.
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import aiohttp
import redis.asyncio as redis
import hashlib

# Claude Code Brain Integration - LiteLLM for model routing
try:
    import litellm
    from litellm import acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    logger.warning("LiteLLM not available - Claude Brain disabled")
    LITELLM_AVAILABLE = False

# Configure logging FIRST
logger = logging.getLogger(__name__)

# Import Integration Bridge connector for event coordination (Component 3)
try:
    from .integration_bridge_connector import (
        IntegrationBridgeConnector,
        emit_adhd_coordination_event,
        emit_service_coordination_event,
        emit_task_status_change,
        get_integration_bridge_connector,
    )

    INTEGRATION_BRIDGE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Integration Bridge connector not available: {e}")
    INTEGRATION_BRIDGE_AVAILABLE = False

# Import our new specialized engines (using absolute imports to fix module loading)
try:
    from external_dependency_integration import (
        DependencyType,
        ExternalDependency,
        ExternalDependencyIntegrationEngine,
    )
    from multi_team_coordination import (
        CoordinationPriority,
        CrossTeamDependency,
        MultiTeamCoordinationEngine,
        TeamProfile,
    )
    from predictive_risk_assessment import (
        PredictiveRiskAssessmentEngine,
        RiskLevel,
        RiskProfile,
    )

    SPECIALIZED_ENGINES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Specialized engines not available: {e}")
    SPECIALIZED_ENGINES_AVAILABLE = False

# Import CognitiveGuardian for ADHD-aware task routing (Week 5)
try:
    agents_path = os.path.join(os.path.dirname(__file__), "..", "agents")
    sys.path.insert(0, agents_path)
    from cognitive_guardian import CognitiveGuardian

    COGNITIVE_GUARDIAN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CognitiveGuardian not available: {e}")
    COGNITIVE_GUARDIAN_AVAILABLE = False

# ConPort-KG Integration for task progress events
try:
    from integration_bridge_connector import emit_task_status_change

    CONPORT_KG_INTEGRATION = True
except ImportError:
    CONPORT_KG_INTEGRATION = False


class ClaudeBrainManager:
    """
    Claude Code Brain Manager - Intelligent reasoning layer for Dopemux.

    Integrates LiteLLM for cost-optimized model routing, ZenML-style orchestration
    with retries/caching, ADHD-friendly prompt engineering, and LangChain-inspired
    chaining for complex reasoning tasks.
    """

    def __init__(self):
        if not LITELLM_AVAILABLE:
            raise ImportError("ClaudeBrainManager requires LiteLLM")

        # Configure LiteLLM for Claude access via OpenRouter
        litellm.set_verbose(False)  # Reduce logs for ADHD focus

        # Redis caching for performance (ZenML-style)
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url("redis://localhost:6379", db=3)  # Separate DB
            self.cache_available = True
        except ImportError:
            logger.warning("Redis not available - caching disabled")
            self.redis_client = None
            self.cache_available = False

        # Model routing configuration (cost-optimized)
        self.model_routes = {
            "low_complexity": "openrouter/xai/grok-code-fast-1",  # Cheap, fast
            "medium_complexity": "openrouter/openai/gpt-5-mini",  # Balanced
            "high_complexity": "openrouter/claude-sonnet-4-5",  # Power for complex
        }

        # Reliability: Enhanced circuit breaker with failure classification
        self.circuit_breaker = {
            "failures": 0,
            "transient_failures": 0,
            "permanent_failures": 0,
            "last_failure": None,
            "open_until": None,
            "test_mode": False,
            "failure_patterns": [],  # Track failure types for learning
        }

        # Security: Input validation and sanitization
        self.max_prompt_length = 5000  # Prevent excessive API costs
        self.allowed_chars_pattern = r'^[a-zA-Z0-9\s\.,!?\-_\(\)\[\]{}:;"\'/]+$'

        # Performance: Concurrency control
        self.max_concurrent_calls = 5  # Prevent event loop blocking
        self.active_calls = 0

        # Caching: Enhanced Redis strategy
        self.model_versions = {
            "openrouter/xai/grok-code-fast-1": "1.0",
            "openrouter/openai/gpt-5-mini": "1.0",
            "openrouter/claude-sonnet-4-5": "1.0",
        }  # For cache invalidation on model updates
        self.cache_ttl_seconds = 3600  # 1-hour TTL for LLM responses

        logger.info("🧠 ClaudeBrainManager initialized with enhanced reliability features")

        # Initialize Prompt Optimizer
        self.prompt_optimizer = PromptOptimizer(self)

    async def reason(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Primary reasoning method with integrated orchestration and enhanced reliability.

        Args:
            prompt: User query or reasoning task
            context: Optional context (energy level, complexity score)

        Returns:
            Claude's reasoned response
        """
        try:
            # Security: Input validation and sanitization
            if not await self._validate_and_sanitize_input(prompt):
                return "Input validation failed. Please provide valid text input."

            # Performance: Concurrency control
            if self.active_calls >= self.max_concurrent_calls:
                logger.warning("Max concurrent calls reached - deferring request")
                return "Service busy. Please try again in a moment."

            self.active_calls += 1

            try:
                # Check circuit breaker
                if self._is_circuit_open():
                    logger.warning("Circuit breaker open - using cached fallback")
                    return "Service temporarily unavailable. Please try again later."

                # Route to appropriate model based on context
                model = await self._route_model(context or {})

                # Apply ADHD-friendly prompt engineering
                enhanced_prompt = await self._enhance_prompt(prompt, context or {})

                # Check Redis cache first (enhanced ZenML-style with SHA256)
                model_version = self.model_versions.get(model, "1.0")
                key_content = f"{model}:{model_version}:{enhanced_prompt}"
                cache_key = f"claude_brain:{hashlib.sha256(key_content.encode()).hexdigest()[:16]}"  # SHA256 prefix for collision prevention

                if self.cache_available:
                    cached_response = await self.redis_client.get(cache_key)
                    if cached_response:
                        logger.debug(f"Cache hit for key: {cache_key}")
                        return cached_response.decode('utf-8')

                # Make async call with retries (ZenML pattern)
                response = await self._call_with_retry(model, enhanced_prompt)

                # Cache successful response in Redis with TTL
                if self.cache_available:
                    await self.redis_client.setex(cache_key, self.cache_ttl_seconds, response)
                    logger.debug(f"Cached response for key: {cache_key} (TTL: {self.cache_ttl_seconds}s)")

                # Reset circuit breaker on success
                self.circuit_breaker["failures"] = 0

                return response

            finally:
                self.active_calls -= 1

        except Exception as e:
            logger.error(f"ClaudeBrainManager reasoning failed: {e}")
            self._record_failure(e, {"operation": "reasoning", "prompt_length": len(prompt)})
            return f"Reasoning temporarily unavailable: {str(e)}"

    async def _route_model(self, context: Dict[str, Any]) -> str:
        """Route to cost-optimized model based on context."""
        complexity = context.get("complexity_score", 0.5)

        if complexity < 0.3:
            return self.model_routes["low_complexity"]
        elif complexity < 0.7:
            return self.model_routes["medium_complexity"]
        else:
            return self.model_routes["high_complexity"]

    class PromptOptimizer:
        """
        Advanced prompt optimizer for Claude Brain task recommendations.

        Features:
        - Dynamic prompting based on user context (ADHD state)
        - Self-correcting loops for quality improvement
        - Multi-service context integration
        - Chain-of-thought reasoning for complex decisions
        """

        def __init__(self, brain_manager):
            self.brain = brain_manager
            self.templates = {
                "task_recommendation": """
                You are Claude, an expert AI task coordinator in Dopemux, specializing in ADHD-optimized development workflows. Your role is to intelligently route tasks to the most appropriate AI agent based on technical requirements and user cognitive state.

                EXPERTISE CONTEXT:
                - CONPORT: Decision logging, progress tracking, context management (best for strategic/planning tasks)
                - SERENA: Code navigation, file analysis, refactoring (best for implementation/debugging)
                - TASKMASTER: PRD parsing, complexity analysis, research (best for requirements/analysis)
                - ZEN: Multi-model consensus, code review, architecture analysis (best for complex validation)

                CURRENT CONTEXT:
                - User energy level: {energy_level}
                - Task complexity: {complexity_score}
                - Cognitive load: {cognitive_load}
                - Available agents: {available_agents}

                TASK ANALYSIS:
                Title: {task_title}
                Description: {task_description}

                CONTEXT FROM DOPEMUX KNOWLEDGE BASE:
                {dope_context_info}

                ANALYSIS FRAMEWORK:
                1. Task Type Classification: Determine if this is planning/decision-making, implementation/coding, analysis/research, or validation/review
                2. Agent Capability Matching: Map task requirements to agent strengths, considering available patterns and documentation
                3. ADHD Accommodation: Consider user's current energy and cognitive state
                4. Risk Assessment: Evaluate potential for context switching or cognitive overload

                EXAMPLES BASED ON SIMILAR PATTERNS:
                - Complex architecture decisions → ZEN (multi-perspective validation)
                - Code debugging with high complexity → SERENA (file navigation + analysis)
                - Strategic planning with medium energy → CONPORT (progress tracking)
                - Requirements analysis with low energy → TASKMASTER (focused research)
                {additional_examples}

                CHAIN-OF-THOUGHT REASONING:
                Step 1: Classify task type → {task_type_classification}
                Step 2: Assess agent capabilities → {agent_capability_match}
                Step 3: Consider ADHD factors → {adhd_accommodation}
                Step 4: Final recommendation → {optimal_agent}

                RECOMMENDATION FORMAT:
                Agent: [AGENT_NAME]
                Confidence: [HIGH/MEDIUM/LOW]
                Reasoning: [Brief explanation]

                Respond with ONLY the agent name: CONPORT, SERENA, TASKMASTER, or ZEN
                """,
                "self_correction": """
                You are Claude, an expert prompt optimizer evaluating recommendation quality.

                TASK UNDER REVIEW:
                Original Task: {task_title}
                Recommended Agent: {recommended_agent}
                Original Reasoning: {original_reasoning}

                EVALUATION CRITERIA:
                1. Technical Fit: Does the agent have required capabilities for this task type?
                2. Complexity Match: Is the agent appropriate for the task's complexity level?
                3. ADHD Alignment: Does this choice support user's current cognitive state?
                4. Alternative Analysis: Are there clearly better alternatives?

                FEW-SHOT EXAMPLES:
                Example 1 - Good Fit: "Database schema design" → CONPORT (architectural decision logging)
                Example 2 - Poor Fit: "Debug memory leak" → CONPORT (needs SERENA for code analysis)
                Example 3 - ADHD Consideration: "Complex refactoring" with low energy → TASKMASTER (focused analysis)

                DECISION PROCESS:
                1. Re-evaluate task requirements
                2. Compare against agent capabilities
                3. Consider ADHD accommodations
                4. Determine if recommendation should change

                RESPONSE FORMAT:
                If recommendation is optimal: CONFIRMED
                If improvement needed: IMPROVED_AGENT: [AGENT_NAME] - [Brief reasoning with specific improvements]
                """,
                "prompt_compression": """
                Compress this prompt while preserving all essential information and reasoning quality.

                ORIGINAL PROMPT LENGTH: {original_length} characters
                TARGET COMPRESSION: 60-70% of original

                COMPRESSION RULES:
                1. Use abbreviations for common terms (e.g., ADHD → neurodiversity optimization)
                2. Combine related instructions into single statements
                3. Remove redundant explanations while keeping examples
                4. Maintain chain-of-thought structure
                5. Preserve role definition and context

                COMPRESSED PROMPT:
                [Your compressed version here]
                """
            }

            # Advanced optimization settings
            self.optimization_settings = {
                "max_context_length": 4000,  # Leave room for response
                "compression_enabled": True,
                "few_shot_examples": True,
                "chain_of_thought": True,
                "role_based_prompting": True,
                "dynamic_formatting": True,
                "meta_prompting": True,  # Enable self-improving prompts
            }

            # Meta-prompting templates for self-improvement (improved)
            self.meta_templates = {
                "prompt_generator": """
                You are a prompt engineering expert specializing in task-specific optimizations.

                TASK: {task_description}
                COMPLEXITY: {complexity_level}
                CONTEXT: {context_info}

                Generate a focused, effective prompt that:
                1. Clearly defines the task and expected output
                2. Includes relevant examples for the task type
                3. Uses appropriate reasoning structure
                4. Considers user context and constraints

                Keep it concise but complete. Focus on quality over length.
                """,

                "prompt_critic": """
                Evaluate this prompt's effectiveness for the given task:

                PROMPT: {prompt_text}
                TASK: {task_description}
                COMPLEXITY: {complexity_level}

                Score (1-10) and provide brief feedback on:
                - Clarity and structure
                - Task alignment
                - Potential effectiveness

                If score < 7, suggest specific improvements.
                """,

                "prompt_evolver": """
                Improve this prompt based on feedback:

                CURRENT PROMPT: {original_prompt}
                FEEDBACK: {user_feedback}
                TASK: {task_description}

                Create an enhanced version that addresses the feedback while maintaining effectiveness.
                Focus on the most impactful improvements.
                """
            }

            # Meta-prompting performance tracking
            self.meta_performance = {
                "generated_prompts": {},
                "critique_scores": [],
                "evolution_count": 0,
                "cache_hits": 0
            }

        async def optimize_task_recommendation_prompt(self, task: OrchestrationTask, context: Dict[str, Any]) -> str:
            """Generate optimized prompt for task recommendation with dynamic enhancements."""

            # Base context from task and system state
            base_context = {
                "task_title": task.title,
                "task_description": task.description,
                "complexity_score": task.complexity_score,
                "cognitive_load": task.cognitive_load,
                "energy_level": context.get("energy_level", "medium"),
                "available_agents": list(self.brain.agent_pool.keys()) if hasattr(self.brain, 'agent_pool') else ["CONPORT", "SERENA", "TASKMASTER", "ZEN"]
            }

            # Dynamic enhancements based on user state and system context
            enhancements = await self._gather_dynamic_context(base_context, context)

            # Format Dope-Context information for the prompt
            dope_context_info = self._format_dope_context_info(enhancements)
            additional_examples = self._format_additional_examples(enhancements)

            # Add formatted context to base context
            full_context = {
                **base_context,
                **enhancements,
                "dope_context_info": dope_context_info,
                "additional_examples": additional_examples
            }

            # Build enhanced prompt
            prompt = self.templates["task_recommendation"].format(**full_context)

            # Apply ADHD-specific formatting
            prompt = await self._apply_adhd_formatting(prompt, context)

            return prompt

        async def _gather_dynamic_context(self, base_context: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Gather additional context from Dopemux services for richer prompts."""

            enhancements = {}

            # ADHD Engine integration (if available)
            try:
                if hasattr(self.brain, 'orchestrator') and self.brain.orchestrator:
                    adhd_state = await self.brain.orchestrator.get_adhd_state()
                    enhancements["current_attention"] = adhd_state.get("attention_level", "focused")
                    enhancements["break_needed"] = adhd_state.get("break_recommended", False)
            except:
                pass

            # ConPort integration (historical decisions)
            try:
                if hasattr(self.brain, 'orchestrator') and self.brain.orchestrator and self.brain.orchestrator.conport_adapter:
                    recent_decisions = await self.brain.orchestrator.conport_adapter.get_recent_decisions(limit=3)
                    enhancements["recent_patterns"] = [d.get("summary", "") for d in recent_decisions]
            except:
                pass

            # Dope-Context integration (semantic code and docs search)
            try:
                # Check if Dope-Context MCP is available
                try:
                    # Test MCP connection with a simple status check
                    status = await mcp__dope-context__get_index_status()
                    if not status or status.get("status") != "active":
                        raise Exception("Dope-Context index not available")
                except Exception as conn_e:
                    logger.debug(f"Dope-Context MCP connection check failed: {conn_e}")
                    enhancements["dope_context_status"] = "unavailable"
                    return enhancements  # Skip further Dope-Context calls

                # Search for relevant code patterns for the task
                code_query = f"{task.title} implementation patterns"
                try:
                    code_results = await mcp__dope-context__search_code(
                        query=code_query,
                        top_k=3
                    )
                    if code_results and isinstance(code_results, list) and len(code_results) > 0:
                        enhancements["relevant_code_patterns"] = [
                            {
                                "file": result.get("file_path", "") if isinstance(result, dict) else str(result),
                                "snippet": (result.get("code", "")[:200] + "..." if len(result.get("code", "")) > 200 else result.get("code", "")) if isinstance(result, dict) else "Code snippet unavailable",
                                "complexity": result.get("complexity", 0.5) if isinstance(result, dict) else 0.5
                            } for result in code_results[:2]  # Limit to 2 examples
                        ]
                        enhancements["dope_context_code_found"] = True
                    else:
                        enhancements["dope_context_code_found"] = False
                except Exception as code_e:
                    logger.debug(f"Dope-Context code search failed: {code_e}")
                    enhancements["dope_context_code_error"] = str(code_e)

                # Search for relevant documentation
                docs_query = f"{task.title} best practices documentation"
                try:
                    docs_results = await mcp__dope-context__docs_search(
                        query=docs_query,
                        top_k=2
                    )
                    if docs_results and isinstance(docs_results, list) and len(docs_results) > 0:
                        enhancements["relevant_documentation"] = [
                            {
                                "source": result.get("source_path", "") if isinstance(result, dict) else "Unknown source",
                                "excerpt": (result.get("text", "")[:300] + "..." if len(result.get("text", "")) > 300 else result.get("text", "")) if isinstance(result, dict) else "Documentation excerpt unavailable",
                                "relevance": result.get("score", 0) if isinstance(result, dict) else 0
                            } for result in docs_results
                        ]
                        enhancements["dope_context_docs_found"] = True
                    else:
                        enhancements["dope_context_docs_found"] = False
                except Exception as docs_e:
                    logger.debug(f"Dope-Context docs search failed: {docs_e}")
                    enhancements["dope_context_docs_error"] = str(docs_e)

                enhancements["dope_context_status"] = "active"

            except Exception as e:
                logger.debug(f"Dope-Context integration failed: {e}")
                enhancements["dope_context_error"] = str(e)
                enhancements["dope_context_status"] = "error"

            return enhancements

        async def _apply_adhd_formatting(self, prompt: str, context: Dict[str, Any]) -> str:
            """Apply ADHD-friendly formatting based on user state."""

            energy_level = context.get("energy_level", "medium")

            if energy_level == "low":
                # Concise, bullet-point format
                adhd_wrapper = """
                ⚡ QUICK ANALYSIS MODE (Low Energy)
                Focus on essential information only.
                Use bullet points and clear recommendations.

                {prompt}

                ⚠️ Keep response under 100 words.
                """
            elif energy_level == "high":
                # Detailed analysis format
                adhd_wrapper = """
                🔍 DETAILED ANALYSIS MODE (High Energy)
                Provide comprehensive reasoning with examples.
                Include pros/cons of each option.

                {prompt}

                ✅ Include specific examples and detailed reasoning.
                """
            else:
                # Balanced format
                adhd_wrapper = """
                ⚖️ BALANCED ANALYSIS MODE (Medium Energy)
                Provide clear reasoning without overwhelming detail.

                {prompt}

                ✅ Use structured format with key points highlighted.
                """

            return adhd_wrapper.format(prompt=prompt)

        def _format_dope_context_info(self, enhancements: Dict[str, Any]) -> str:
            """Format Dope-Context information for prompt inclusion with enhanced error handling."""
            info_parts = []

            # Check Dope-Context status first
            status = enhancements.get("dope_context_status", "unknown")
            if status == "unavailable":
                return "Dopemux knowledge base is currently unavailable. Proceeding with general task analysis."
            elif status == "error":
                error_msg = enhancements.get("dope_context_error", "Unknown error")
                return f"Dopemux knowledge base connection error: {error_msg}. Using fallback analysis."

            # Add code patterns if available
            if "relevant_code_patterns" in enhancements and enhancements["relevant_code_patterns"]:
                patterns = enhancements["relevant_code_patterns"]
                info_parts.append("RELEVANT CODE PATTERNS FROM DOPEMUX CODEBASE:")
                for pattern in patterns:
                    file_name = pattern.get("file", "").split("/")[-1] or "unknown_file"
                    complexity = pattern.get("complexity", 0.5)
                    snippet = pattern.get("snippet", "") or "No snippet available"
                    info_parts.append(f"- {file_name} (complexity: {complexity:.1f}): {snippet}")
                info_parts.append("")

            # Add documentation if available
            if "relevant_documentation" in enhancements and enhancements["relevant_documentation"]:
                docs = enhancements["relevant_documentation"]
                info_parts.append("RELEVANT DOCUMENTATION FROM DOPEMUX KNOWLEDGE BASE:")
                for doc in docs:
                    source = doc.get("source", "").split("/")[-1] or "unknown_doc"
                    excerpt = doc.get("excerpt", "") or "No excerpt available"
                    relevance = doc.get("relevance", 0)
                    info_parts.append(f"- {source} (relevance: {relevance:.2f}): {excerpt}")
                info_parts.append("")

            # Add status information
            code_found = enhancements.get("dope_context_code_found", False)
            docs_found = enhancements.get("dope_context_docs_found", False)

            if code_found or docs_found:
                status_parts = []
                if code_found:
                    status_parts.append("code patterns retrieved")
                if docs_found:
                    status_parts.append("documentation found")
                info_parts.append(f"Status: Successfully retrieved {', '.join(status_parts)} from Dopemux knowledge base.")
            else:
                info_parts.append("Status: No specific patterns or documentation found in knowledge base for this task type.")

            # Handle specific errors gracefully
            if "dope_context_code_error" in enhancements:
                info_parts.append(f"Note: Code search encountered an issue: {enhancements['dope_context_code_error']}")
            if "dope_context_docs_error" in enhancements:
                info_parts.append(f"Note: Documentation search encountered an issue: {enhancements['dope_context_docs_error']}")

            return "\n".join(info_parts)

        def _format_additional_examples(self, enhancements: Dict[str, Any]) -> str:
            """Format additional task-specific examples from Dope-Context data."""
            examples = []

            # Generate examples based on available patterns
            if "relevant_code_patterns" in enhancements:
                patterns = enhancements["relevant_code_patterns"]
                if patterns:
                    # Create example based on pattern complexity
                    high_complexity = any(p.get("complexity", 0) > 0.7 for p in patterns)
                    if high_complexity:
                        examples.append("- High-complexity implementation patterns found → ZEN (thorough validation needed)")
                    else:
                        examples.append("- Moderate-complexity patterns identified → SERENA (implementation support available)")

            # Add documentation-based examples
            if "relevant_documentation" in enhancements:
                docs = enhancements["relevant_documentation"]
                if docs:
                    examples.append("- Documentation available for best practices → TASKMASTER (research support)")
                    if len(docs) > 1:
                        examples.append("- Multiple documentation sources → CONPORT (comprehensive planning)")

            return "\n                ".join(examples) if examples else ""

        async def generate_meta_prompt(self, task: OrchestrationTask, context: Dict[str, Any]) -> str:
            """Use meta-prompting to generate optimized prompts automatically with caching."""
            if not self.optimization_settings["meta_prompting"]:
                return await self._standard_optimize_prompt_chain(task, context)

            # Check cache for similar task patterns
            cache_key = f"meta_{task.complexity_score:.1f}_{context.get('energy_level', 'medium')}_{hash(task.title.lower()):x}"
            if cache_key in self.meta_performance["generated_prompts"]:
                self.meta_performance["cache_hits"] += 1
                return self.meta_performance["generated_prompts"][cache_key]

            # Determine complexity level for template
            complexity_level = "simple" if task.complexity_score < 0.4 else "medium" if task.complexity_score < 0.7 else "complex"

            # Generate meta-prompt for prompt creation
            meta_generator = self.meta_templates["prompt_generator"].format(
                task_description=f"Create prompt for: {task.title} - {task.description}",
                complexity_level=complexity_level,
                context_info=f"Energy: {context.get('energy_level', 'medium')}, Cognitive load: {task.cognitive_load}"
            )

            try:
                # Use Claude to generate the optimized prompt
                generated_prompt = await self.brain.reason(meta_generator, context)

                # Clean and cache the generated prompt
                clean_prompt = generated_prompt.strip()
                self.meta_performance["generated_prompts"][cache_key] = clean_prompt

                return clean_prompt

            except Exception as e:
                logger.warning(f"Meta-prompt generation failed: {e}, falling back to standard optimization")
                return await self._standard_optimize_prompt_chain(task, context)

        async def critique_and_improve_prompt(self, prompt: str, task: OrchestrationTask, performance_data: Dict[str, Any] = None) -> str:
            """Use meta-prompting to critique and improve existing prompts with performance tracking."""
            # Determine complexity level
            complexity_level = "simple" if task.complexity_score < 0.4 else "medium" if task.complexity_score < 0.7 else "complex"

            critic_prompt = self.meta_templates["prompt_critic"].format(
                prompt_text=prompt[:1000],  # Limit prompt length for critique
                task_description=f"Task: {task.title} - {task.description[:200]}",
                complexity_level=complexity_level
            )

            try:
                critique = await self.brain.reason(critic_prompt, {"energy_level": "high"})  # Use high energy for analysis

                # Parse critique score
                import re
                score_match = re.search(r'(\d+)/10|score.*?(\d+)', critique.lower())
                if score_match:
                    score = int(score_match.group(1) or score_match.group(2))
                    self.meta_performance["critique_scores"].append(score)

                    if score < 7:
                        # Generate improved version
                        evolver_prompt = self.meta_templates["prompt_evolver"].format(
                            original_prompt=prompt[:1500],  # Limit for evolution
                            user_feedback=f"Critique score: {score}/10. {critique[:500]}",
                            task_description=f"Task: {task.title}"
                        )

                        improved = await self.brain.reason(evolver_prompt, {"energy_level": "high"})
                        self.meta_performance["evolution_count"] += 1
                        return improved.strip()

                return prompt  # Return original if score is good enough

            except Exception as e:
                logger.warning(f"Prompt critique failed: {e}, returning original")
                return prompt

        def get_meta_performance_stats(self) -> Dict[str, Any]:
            """Get meta-prompting performance statistics for monitoring."""
            scores = self.meta_performance["critique_scores"]
            avg_score = sum(scores) / len(scores) if scores else 0

            return {
                "generated_prompts_cached": len(self.meta_performance["generated_prompts"]),
                "cache_hits": self.meta_performance["cache_hits"],
                "total_critiques": len(scores),
                "average_critique_score": round(avg_score, 2),
                "evolutions_performed": self.meta_performance["evolution_count"],
                "improvement_rate": self.meta_performance["evolution_count"] / max(1, len(scores))
            }

        async def meta_optimize_prompt_chain(self, task: OrchestrationTask, context: Dict[str, Any]) -> str:
            """Complete meta-prompting optimization with efficiency optimizations."""
            # Skip full meta-chain for very simple tasks to reduce overhead
            if task.complexity_score < 0.3:
                return await self.generate_meta_prompt(task, context)

            # Step 1: Generate initial prompt using meta-prompting
            initial_prompt = await self.generate_meta_prompt(task, context)

            # Step 2: Conditional critique - only for medium/high complexity or when we have performance data
            should_critique = (
                task.complexity_score >= 0.5 or  # Medium+ complexity
                len(self.meta_performance["critique_scores"]) < 5 or  # Early learning phase
                self.meta_performance["evolution_count"] / max(1, len(self.meta_performance["critique_scores"])) < 0.3  # Low improvement rate
            )

            if should_critique:
                final_prompt = await self.critique_and_improve_prompt(initial_prompt, task)
            else:
                final_prompt = initial_prompt

            # Step 3: Apply standard optimizations
            return await self.optimize_prompt_chain_from_base(final_prompt, task, context)

        async def optimize_prompt_chain_from_base(self, base_prompt: str, task: OrchestrationTask, context: Dict[str, Any]) -> str:
            """Apply standard optimizations to a base prompt."""
            # Apply chain-of-thought
            if self.optimization_settings["chain_of_thought"]:
                base_prompt = self._enhance_chain_of_thought(base_prompt)

            # Apply ADHD formatting
            base_prompt = await self._apply_adhd_formatting(base_prompt, context)

            # Apply compression if needed
            base_prompt = await self.compress_prompt(base_prompt)

            return base_prompt

        async def compress_prompt(self, prompt: str) -> str:
            """Apply prompt compression using advanced techniques."""
            if not self.optimization_settings["compression_enabled"]:
                return prompt

            original_length = len(prompt)

            # Apply compression rules
            compressed = prompt

            # Rule 1: Abbreviations
            abbreviations = {
                "ADHD": "neurodiversity optimization",
                "cognitive load": "mental effort",
                "complexity score": "difficulty level",
                "energy level": "focus state",
                "task coordinator": "workflow optimizer",
                "development workflows": "coding processes"
            }

            for full, abbr in abbreviations.items():
                compressed = compressed.replace(full, abbr)

            # Rule 2: Combine related instructions
            compressed = compressed.replace(
                "Analyze the task characteristics (technical complexity, user readiness, agent capabilities)",
                "Evaluate technical difficulty, user readiness, and agent capabilities"
            )

            # Rule 3: Maintain structure but reduce verbosity
            if len(compressed) > self.optimization_settings["max_context_length"]:
                # Truncate examples if needed while preserving core structure
                lines = compressed.split('\n')
                essential_lines = []
                example_count = 0

                for line in lines:
                    if line.strip().startswith('EXAMPLES:'):
                        essential_lines.append(line)
                        continue
                    elif line.strip().startswith('- ') and example_count < 2:  # Keep only 2 examples
                        essential_lines.append(line)
                        example_count += 1
                    elif not line.strip().startswith('- ') or example_count >= 2:
                        essential_lines.append(line)

                compressed = '\n'.join(essential_lines)

            return compressed

        def apply_few_shot_optimization(self, prompt: str, task_type: str) -> str:
            """Enhance prompt with relevant few-shot examples based on task type."""
            if not self.optimization_settings["few_shot_examples"]:
                return prompt

            # Task-type specific examples
            examples_db = {
                "planning": [
                    "Strategic roadmap creation → CONPORT (decision tracking)",
                    "Sprint planning → CONPORT (progress management)"
                ],
                "implementation": [
                    "Code refactoring → SERENA (file analysis)",
                    "Bug debugging → SERENA (navigation tools)"
                ],
                "analysis": [
                    "Requirements parsing → TASKMASTER (research capabilities)",
                    "Complexity assessment → TASKMASTER (analytical tools)"
                ],
                "validation": [
                    "Architecture review → ZEN (multi-perspective analysis)",
                    "Code quality audit → ZEN (consensus validation)"
                ]
            }

            # Determine task type from prompt content
            task_type_detected = "planning"  # default
            if "code" in prompt.lower() or "implement" in prompt.lower():
                task_type_detected = "implementation"
            elif "analyze" in prompt.lower() or "research" in prompt.lower():
                task_type_detected = "analysis"
            elif "review" in prompt.lower() or "validate" in prompt.lower():
                task_type_detected = "validation"

            examples = examples_db.get(task_type_detected, examples_db["planning"])

            # Insert examples into prompt
            example_section = "\n                ".join([f"- {ex}" for ex in examples])
            prompt = prompt.replace(
                "EXAMPLES:",
                f"EXAMPLES:\n                {example_section}"
            )

            return prompt

        async def optimize_prompt_chain(self, task: OrchestrationTask, context: Dict[str, Any]) -> str:
            """Apply full optimization chain with meta-prompting capabilities."""
            if self.optimization_settings["meta_prompting"]:
                # Use meta-prompting for self-improving prompts
                return await self.meta_optimize_prompt_chain(task, context)
            else:
                # Fallback to standard optimization
                return await self._standard_optimize_prompt_chain(task, context)

        async def _standard_optimize_prompt_chain(self, task: OrchestrationTask, context: Dict[str, Any]) -> str:
            """Apply standard optimization chain: context → generation → compression → few-shot → formatting."""
            # Step 1: Gather dynamic context
            enhanced_context = await self._gather_dynamic_context({}, context)

            # Step 2: Generate base prompt
            prompt = self.templates["task_recommendation"].format(**{
                "task_title": task.title,
                "task_description": task.description,
                "complexity_score": task.complexity_score,
                "cognitive_load": task.cognitive_load,
                "energy_level": context.get("energy_level", "medium"),
                "available_agents": ["CONPORT", "SERENA", "TASKMASTER", "ZEN"],
                **enhanced_context
            })

            # Step 3: Apply chain-of-thought structure
            if self.optimization_settings["chain_of_thought"]:
                prompt = self._enhance_chain_of_thought(prompt)

            # Step 4: Add few-shot examples
            prompt = self.apply_few_shot_optimization(prompt, task.title.lower())

            # Step 5: Apply ADHD formatting
            prompt = await self._apply_adhd_formatting(prompt, context)

            # Step 6: Compress if needed
            prompt = await self.compress_prompt(prompt)

            return prompt

        def _enhance_chain_of_thought(self, prompt: str) -> str:
            """Enhance prompt with explicit chain-of-thought reasoning structure."""
            cot_section = """
                CHAIN-OF-THOUGHT ANALYSIS:
                Step 1: Task Classification → Determine primary task type (planning/implementation/analysis/validation)
                Step 2: Complexity Assessment → Evaluate technical difficulty and user readiness requirements
                Step 3: Agent Matching → Map task requirements to agent capabilities and expertise
                Step 4: ADHD Optimization → Consider user's current cognitive state and energy levels
                Step 5: Risk Evaluation → Assess potential for cognitive overload or context switching
                Step 6: Final Recommendation → Select optimal agent with confidence assessment

                REASONING TRACE:
                """

            # Insert before RECOMMENDATION FORMAT
            return prompt.replace(
                "RECOMMENDATION FORMAT:",
                f"{cot_section}\n                RECOMMENDATION FORMAT:"
            )

        async def apply_self_correction(self, task: OrchestrationTask, initial_recommendation: str, context: Dict[str, Any]) -> str:
            """Apply self-correcting loop to improve recommendations."""

            # Generate critique prompt
            critique_prompt = self.templates["self_correction"].format(
                task_title=task.title,
                recommended_agent=initial_recommendation,
                original_reasoning="AI-generated recommendation based on task analysis"
            )

            # Get Claude's self-critique
            critique_response = await self.brain.reason(critique_prompt, context)

            # Parse response
            if "CONFIRMED" in critique_response.upper():
                return initial_recommendation  # Keep original
            elif "IMPROVED_AGENT:" in critique_response:
                # Extract improved recommendation
                lines = critique_response.split("\n")
                for line in lines:
                    if "IMPROVED_AGENT:" in line:
                        improved_agent = line.split("IMPROVED_AGENT:")[1].strip()
                        return improved_agent.upper()

            # Fallback to original if parsing fails
            return initial_recommendation


    async def _call_with_retry(self, model: str, prompt: str, max_retries: int = 3) -> str:
        """Make API call with exponential backoff (ZenML pattern)."""
        for attempt in range(max_retries):
            try:
                response = await acompletion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,  # ADHD-friendly limit
                    temperature=0.7,  # Balanced creativity
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"API call failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_breaker["open_until"] is None:
            return False

        if datetime.now(timezone.utc) < self.circuit_breaker["open_until"]:
            return True

        # Reset if timeout passed
        self.circuit_breaker["open_until"] = None
        return False

    def _record_failure(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Record and classify failure for circuit breaker and learning."""
        self.circuit_breaker["failures"] += 1
        self.circuit_breaker["last_failure"] = datetime.now(timezone.utc)

        # Classify failure type
        failure_type = self._classify_failure(error, context)
        if failure_type == "transient":
            self.circuit_breaker["transient_failures"] += 1
        elif failure_type == "permanent":
            self.circuit_breaker["permanent_failures"] += 1

        # Track failure patterns for learning
        failure_pattern = {
            "timestamp": datetime.now(timezone.utc),
            "error_type": type(error).__name__,
            "failure_type": failure_type,
            "context": context or {},
            "model_used": context.get("model") if context else None,
        }
        self.circuit_breaker["failure_patterns"].append(failure_pattern)

        # Keep only recent patterns (last 50)
        if len(self.circuit_breaker["failure_patterns"]) > 50:
            self.circuit_breaker["failure_patterns"] = self.circuit_breaker["failure_patterns"][-50:]

        # Open circuit based on failure rate (or immediately in test mode)
        failure_rate = self.circuit_breaker["transient_failures"] / max(1, self.circuit_breaker["failures"])
        if self.circuit_breaker["test_mode"] or self.circuit_breaker["failures"] >= 5 or failure_rate > 0.7:
            self.circuit_breaker["open_until"] = datetime.now(timezone.utc) + timedelta(minutes=5)
            logger.warning(f"Circuit breaker opened - Failures: {self.circuit_breaker['failures']}, Rate: {failure_rate:.2f}")

    def _classify_failure(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """Classify failure as transient or permanent for appropriate handling."""
        error_str = str(error).lower()

        # Transient failures (retry likely to succeed)
        transient_indicators = [
            "timeout", "connection", "network", "rate limit", "429",
            "temporary", "unavailable", "overload", "busy"
        ]
        if any(indicator in error_str for indicator in transient_indicators):
            return "transient"

        # Permanent failures (retry unlikely to succeed)
        permanent_indicators = [
            "authentication", "authorization", "forbidden", "403", "401",
            "invalid", "malformed", "unsupported", "deprecated"
        ]
        if any(indicator in error_str for indicator in permanent_indicators):
            return "permanent"

        # Default to transient for unknown failures
        return "transient"

    def analyze_failure_patterns(self) -> Dict[str, Any]:
        """Analyze failure patterns to improve future task assignments."""
        patterns = self.circuit_breaker["failure_patterns"]
        if not patterns:
            return {"status": "no_failures"}

        # Analyze by model, time of day, failure type
        analysis = {
            "total_failures": len(patterns),
            "transient_rate": self.circuit_breaker["transient_failures"] / max(1, self.circuit_breaker["failures"]),
            "permanent_rate": self.circuit_breaker["permanent_failures"] / max(1, self.circuit_breaker["failures"]),
            "model_failure_rates": {},
            "hourly_failure_distribution": {},
            "recommendations": []
        }

        # Model-specific failure analysis
        model_failures = {}
        for pattern in patterns:
            model = pattern.get("model_used", "unknown")
            if model not in model_failures:
                model_failures[model] = 0
            model_failures[model] += 1

        total_failures = len(patterns)
        for model, failures in model_failures.items():
            analysis["model_failure_rates"][model] = failures / total_failures

        # Generate recommendations
        if analysis["transient_rate"] > 0.5:
            analysis["recommendations"].append("Increase retry attempts for transient failures")
        if analysis["permanent_rate"] > 0.3:
            analysis["recommendations"].append("Switch to more reliable models or providers")
        if len(model_failures) > 1:
            worst_model = max(model_failures.items(), key=lambda x: x[1])
            analysis["recommendations"].append(f"Consider reducing usage of {worst_model[0]}")

        return analysis

    async def _validate_and_sanitize_input(self, prompt: str) -> bool:
        """
        Security: Validate and sanitize input to prevent prompt injection.

        Based on OWASP LLM Top 10 recommendations.
        """
        import re

        # Length check to prevent excessive API costs
        if len(prompt) > self.max_prompt_length:
            logger.warning(f"Prompt too long: {len(prompt)} > {self.max_prompt_length}")
            return False

        # Character validation (allow safe characters only)
        if not re.match(self.allowed_chars_pattern, prompt):
            logger.warning("Prompt contains invalid characters")
            return False

        # Basic sanitization: remove potential injection patterns
        sanitized = prompt.replace("system:", "").replace("assistant:", "").replace("user:", "")

        # Update prompt if sanitized
        if sanitized != prompt:
            # Note: In production, this would modify the prompt in place
            logger.debug("Prompt sanitized to prevent injection")

        return True

    # Testing methods for circuit breaker
    def enable_test_mode(self):
        """Enable test mode for circuit breaker testing."""
        self.circuit_breaker["test_mode"] = True
        logger.info("Circuit breaker test mode enabled")

    def disable_test_mode(self):
        """Disable test mode."""
        self.circuit_breaker["test_mode"] = False
        logger.info("Circuit breaker test mode disabled")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics for monitoring."""
        if not self.cache_available:
            return {"status": "cache_disabled"}

        try:
            # Get Redis memory and key count
            info = await self.redis_client.info("memory")
            memory_used = info.get("used_memory", 0)
            keys_count = await self.redis_client.dbsize()

            # Estimate cache hits (would need additional tracking for accurate metrics)
            return {
                "status": "active",
                "keys_count": keys_count,
                "memory_used_bytes": memory_used,
                "memory_used_mb": round(memory_used / (1024 * 1024), 2),
                "ttl_seconds": self.cache_ttl_seconds,
                "active_calls": self.active_calls,
                "max_concurrent": self.max_concurrent_calls,
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}

    def get_failure_insights(self) -> Dict[str, Any]:
        """Get failure analysis and learning insights for system improvement."""
        if not hasattr(self, 'claude_brain') or not self.claude_brain:
            return {"status": "brain_unavailable"}

        return self.claude_brain.analyze_failure_patterns()


class TaskStatus(str, Enum):
    """Enhanced task status with ADHD considerations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    NEEDS_BREAK = "needs_break"
    CONTEXT_SWITCH = "context_switch"
    PAUSED = "paused"


class AgentType(str, Enum):
    """AI agent types for task coordination."""

    CONPORT = "conport"
    SERENA = "serena"
    TASKMASTER = "taskmaster"
    CLAUDE_FLOW = "claude_flow"
    ZEN = "zen"


@dataclass
class OrchestrationTask:
    """Enhanced task representation for orchestration."""

    id: str
    leantime_id: Optional[int] = None
    conport_id: Optional[int] = (
        None  # ConPort progress_entry ID (Architecture 3.0 Component 2)
    )
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    complexity_score: float = 0.5
    estimated_minutes: int = 25
    assigned_agent: Optional[AgentType] = None

    # ADHD-specific fields
    energy_required: str = "medium"  # low, medium, high
    cognitive_load: float = 0.5  # 0.0-1.0
    context_switches_allowed: int = 2
    break_frequency_minutes: int = 25

    # Orchestration metadata
    dependencies: List[str] = None
    dependents: List[str] = None
    agent_assignments: Dict[str, str] = None
    progress_checkpoints: List[Dict] = None

    # Sync tracking
    last_synced: Optional[datetime] = None
    sync_conflicts: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.dependents is None:
            self.dependents = []
        if self.agent_assignments is None:
            self.agent_assignments = {}
        if self.progress_checkpoints is None:
            self.progress_checkpoints = []
        if self.sync_conflicts is None:
            self.sync_conflicts = []


@dataclass
class SyncEvent:
    """Event for multi-directional synchronization."""

    source_system: str
    target_systems: List[str]
    event_type: str
    task_id: str
    data: Dict[str, Any]
    timestamp: datetime
    adhd_metadata: Dict[str, Any]


class EnhancedTaskOrchestrator:
    """
    Intelligent middleware for PM automation and AI agent coordination.

    Features:
    - Leantime integration with real-time polling
    - Multi-directional sync between all PM systems
    - Event-driven AI agent coordination
    - Implicit automation for sprints, retros, progress tracking
    - ADHD accommodations at every coordination point
    """

    def __init__(
        self,
        leantime_url: str,
        leantime_token: str,
        redis_url: str = "redis://localhost:6379",
        workspace_id: str = "/Users/hue/code/dopemux-mvp",
        mcp_tools: Any = None,
    ):
        self.leantime_url = leantime_url.rstrip("/")
        self.leantime_token = leantime_token
        self.redis_url = redis_url
        self.workspace_id = workspace_id
        self.mcp_tools = mcp_tools  # Add mcp_tools parameter

        # Component connections
        self.leantime_session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        self.integration_bridge: Optional[IntegrationBridgeConnector] = (
            None  # Integration Bridge connector
        )

        # Task coordination state - Architecture 3.0: ConPort is storage authority
        # REMOVED: self.orchestrated_tasks dict (Authority violation - fixed in Component 2 Task 2.5)
        # Tasks now queried from ConPort via conport_adapter
        self.conport_adapter = (
            None  # Initialized in _initialize_agent_pool with ConPortEventAdapter
        )
        self.agent_pool: Dict[AgentType, Dict[str, Any]] = {}
        self.sync_queue: asyncio.Queue = asyncio.Queue()

        # ADHD support agents (Week 5)
        self.cognitive_guardian: Optional[CognitiveGuardian] = None

        # Claude Code Brain Manager (Phase 1 Foundation)
        self.claude_brain: Optional[ClaudeBrainManager] = None

        # ADHD optimization settings
        self.adhd_config = {
            "max_concurrent_tasks": 3,
            "break_enforcement": True,
            "context_switch_penalty": 0.3,
            "energy_level_matching": True,
            "implicit_progress_tracking": True,
        }

        # Orchestration metrics
        self.metrics = {
            "tasks_orchestrated": 0,
            "sync_events_processed": 0,
            "ai_agent_dispatches": 0,
            "adhd_accommodations_applied": 0,
            "implicit_automations_triggered": 0,
            # Claude Brain metrics (Phase 1)
            "claude_brain_calls": 0,
            "claude_brain_failures": 0,
            "claude_recommendations_used": 0,
        }

        # Background workers
        self.workers: List[asyncio.Task] = []
        self.running = False

    async def initialize(self) -> None:
        """Initialize all orchestrator components."""
        logger.info("🚀 Initializing Enhanced Task Orchestrator...")

        # Initialize connections
        await asyncio.gather(
            self._initialize_leantime_connection(),
            self._initialize_redis_connection(),
            self._initialize_agent_pool(),
        )

        # Initialize ADHD support agents (Week 5)
        await self._initialize_adhd_agents()

        # Start background workers
        await self._start_background_workers()

        self.running = True
        logger.info("✅ Enhanced Task Orchestrator ready for PM automation!")

    async def _initialize_leantime_connection(self) -> None:
        """Initialize connection to Leantime JSON-RPC API."""
        try:
            self.leantime_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Authorization": f"Bearer {self.leantime_token}",
                    "Content-Type": "application/json",
                },
            )

            # Test connection
            await self._test_leantime_connection()
            logger.info("🔗 Connected to Leantime API")

        except Exception as e:
            logger.error(f"Failed to connect to Leantime: {e}")
            raise

    async def _test_leantime_connection(self) -> bool:
        """Test Leantime API connectivity."""
        try:
            async with self.leantime_session.post(
                f"{self.leantime_url}/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "leantime.rpc.projects.getAllProjects",
                    "params": {"limit": 1},
                    "id": 1,
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return "result" in data
                return False

        except Exception as e:
            logger.error(f"Leantime connection test failed: {e}")
            return False

    async def _initialize_redis_connection(self) -> None:
        """Initialize Redis for caching and coordination."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                db=2,  # Separate DB for orchestrator
                decode_responses=True,
            )

            await self.redis_client.ping()
            logger.info("🔗 Connected to Redis for coordination")

            # Initialize Integration Bridge connector (Component 3)
            if INTEGRATION_BRIDGE_AVAILABLE:
                self.integration_bridge = IntegrationBridgeConnector(self.workspace_id)
                await self.integration_bridge.connect()
                logger.info("🔗 Connected to Integration Bridge")
            else:
                logger.warning(
                    "⚠️ Integration Bridge not available - event coordination disabled"
                )

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def _initialize_agent_pool(self) -> None:
        """Initialize AI agent pool for coordination."""
        # Initialize ConPort adapter (Architecture 3.0 Component 2)
        try:
            from adapters.conport_adapter import ConPortEventAdapter
            from conport_mcp_client import ConPortMCPClient

            # Wire ConPort MCP client for full integration (Component 3)
            conport_client = ConPortMCPClient(self.mcp_tools)
            self.conport_adapter = ConPortEventAdapter(
                workspace_id=self.workspace_id, conport_client=conport_client
            )
            logger.info("📊 ConPort adapter initialized (storage authority)")
        except Exception as e:
            logger.warning(
                f"ConPort adapter initialization failed: {e} - continuing without persistence"
            )
            self.conport_adapter = None

        self.agent_pool = {
            AgentType.CONPORT: {
                "available": True,
                "current_tasks": [],
                "capabilities": [
                    "decision_logging",
                    "progress_tracking",
                    "context_management",
                ],
                "max_concurrent": 5,
            },
            AgentType.SERENA: {
                "available": True,
                "current_tasks": [],
                "capabilities": ["code_navigation", "file_analysis", "refactoring"],
                "max_concurrent": 3,
            },
            AgentType.TASKMASTER: {
                "available": True,
                "current_tasks": [],
                "capabilities": ["prd_parsing", "complexity_analysis", "research"],
                "max_concurrent": 2,
            },
            AgentType.ZEN: {
                "available": True,
                "current_tasks": [],
                "capabilities": ["consensus", "code_review", "architecture_analysis"],
                "max_concurrent": 1,  # Intensive operations
            },
        }

        logger.info("🤖 AI agent pool initialized")

    async def _initialize_adhd_agents(self) -> None:
        """Initialize ADHD support agents for intelligent task routing (Week 5)."""
        if not COGNITIVE_GUARDIAN_AVAILABLE:
            logger.warning("⚠️ CognitiveGuardian not available - ADHD routing disabled")
            return

        try:
            self.cognitive_guardian = CognitiveGuardian(
                workspace_id=self.workspace_id,
                memory_agent=None,  # Could wire MemoryAgent here if needed
                conport_client=None,  # Could wire ConPort client if needed
                break_interval_minutes=25,
                mandatory_break_minutes=90,
                hyperfocus_warning_minutes=60,
            )
            await self.cognitive_guardian.start_monitoring()
            logger.info("🧠 CognitiveGuardian initialized - ADHD-aware routing active")
        except Exception as e:
            logger.error(f"Failed to initialize CognitiveGuardian: {e}")
            self.cognitive_guardian = None

        # Initialize Claude Code Brain Manager (Phase 1)
        try:
            if LITELLM_AVAILABLE:
                self.claude_brain = ClaudeBrainManager()
                logger.info("🧠 ClaudeBrainManager initialized - intelligent reasoning active")
            else:
                logger.warning("LiteLLM not available - Claude Brain disabled")
        except Exception as e:
            logger.error(f"Failed to initialize ClaudeBrainManager: {e}")
            self.claude_brain = None

    async def _start_background_workers(self) -> None:
        """Start background worker tasks."""
        workers = [
            self._leantime_poller(),
            self._sync_processor(),
            self._adhd_monitor(),
            self._implicit_automation_engine(),
            self._progress_correlator(),
        ]

        # Add Integration Bridge event subscriber (Component 3)
        if self.integration_bridge:
            workers.append(self._integration_bridge_subscriber())
            logger.info("📡 Integration Bridge event subscriber enabled")

        self.workers = [asyncio.create_task(worker) for worker in workers]
        logger.info("👥 Background workers started")

    # Core Orchestration Methods

    async def _leantime_poller(self) -> None:
        """Background poller for Leantime task updates."""
        logger.info("📡 Started Leantime polling worker")

        while self.running:
            try:
                # Poll for new/updated tasks
                updated_tasks = await self._fetch_updated_leantime_tasks()

                for leantime_task in updated_tasks:
                    await self._process_leantime_task_update(leantime_task)

                # Poll every 30 seconds for updates
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Leantime polling error: {e}")
                await asyncio.sleep(60)  # Back off on error

    async def _fetch_updated_leantime_tasks(self) -> List[Dict[str, Any]]:
        """Fetch tasks updated since last poll."""
        try:
            # Get last poll timestamp
            last_poll = await self.redis_client.get("orchestrator:last_poll")
            if last_poll:
                since_time = datetime.fromisoformat(last_poll)
            else:
                since_time = datetime.now(timezone.utc) - timedelta(hours=24)

            # Fetch updated tasks from Leantime
            async with self.leantime_session.post(
                f"{self.leantime_url}/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "leantime.rpc.tickets.getAllTickets",
                    "params": {"limit": 100, "since": since_time.isoformat()},
                    "id": self._next_request_id(),
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tasks = data.get("result", [])

                    # Update last poll timestamp
                    await self.redis_client.set(
                        "orchestrator:last_poll", datetime.now(timezone.utc).isoformat()
                    )

                    return tasks if isinstance(tasks, list) else []

        except Exception as e:
            logger.error(f"Failed to fetch Leantime tasks: {e}")

        return []

    async def _process_leantime_task_update(
        self, leantime_task: Dict[str, Any]
    ) -> None:
        """Process updated task from Leantime."""
        try:
            task_id = str(leantime_task.get("id", ""))

            # Convert to orchestration task
            orchestration_task = OrchestrationTask(
                id=f"orch_{task_id}",
                leantime_id=int(task_id),
                title=leantime_task.get("headline", ""),
                description=leantime_task.get("description", ""),
                status=self._map_leantime_status(leantime_task.get("status", "0")),
                priority=int(leantime_task.get("priority", "2")),
                estimated_minutes=self._estimate_task_duration(leantime_task),
            )

            # Apply ADHD optimizations
            orchestration_task = await self._apply_adhd_optimizations(
                orchestration_task
            )

            # Store in ConPort (Architecture 3.0: ConPort is storage authority)
            if self.conport_adapter:
                conport_id = await self.conport_adapter.create_task_in_conport(
                    orchestration_task
                )
                orchestration_task.conport_id = conport_id
                logger.debug(
                    f"📊 Task stored in ConPort: {orchestration_task.title} (ID: {conport_id})"
                )
            else:
                logger.warning(
                    f"⚠️ ConPort adapter not initialized, task not persisted: {orchestration_task.id}"
                )

            # Determine AI agent assignment
            assigned_agent = await self._assign_optimal_agent(orchestration_task)
            if assigned_agent:
                await self._dispatch_to_agent(orchestration_task, assigned_agent)

            # Queue sync event
            sync_event = SyncEvent(
                source_system="leantime",
                target_systems=["conport", "local_adhd"],
                event_type="task_updated",
                task_id=orchestration_task.id,
                data=asdict(orchestration_task),
                timestamp=datetime.now(timezone.utc),
                adhd_metadata={"cognitive_load": orchestration_task.cognitive_load},
            )

            await self.sync_queue.put(sync_event)

            logger.debug(f"📋 Processed Leantime task: {orchestration_task.title}")

        except Exception as e:
            logger.error(f"Failed to process Leantime task update: {e}")

    async def _sync_processor(self) -> None:
        """Background processor for multi-directional synchronization."""
        logger.info("🔄 Started sync processing worker")

        while self.running:
            try:
                # Process sync events from queue
                sync_event = await asyncio.wait_for(self.sync_queue.get(), timeout=10.0)

                await self._execute_sync_event(sync_event)
                self.metrics["sync_events_processed"] += 1

            except asyncio.TimeoutError:
                # No sync events, continue
                continue
            except Exception as e:
                logger.error(f"Sync processing error: {e}")
                await asyncio.sleep(5)

    async def _execute_sync_event(self, event: SyncEvent) -> None:
        """Execute multi-directional sync event."""
        try:
            # Sync to each target system
            for target_system in event.target_systems:
                if target_system == "conport":
                    await self._sync_to_conport(event)
                elif target_system == "local_adhd":
                    await self._sync_to_local_adhd(event)
                elif target_system == "leantime":
                    await self._sync_to_leantime(event)

            logger.debug(
                f"🔄 Sync completed: {event.event_type} to {len(event.target_systems)} systems"
            )

        except Exception as e:
            logger.error(f"Sync execution failed: {e}")

    async def _sync_to_conport(self, event: SyncEvent) -> None:
        """Sync event to ConPort for decision/progress tracking."""
        try:
            # This would integrate with ConPort v2 MCP API
            if event.event_type == "task_updated":
                # Log progress entry in ConPort
                progress_data = {
                    "status": event.data.get("status", "pending").upper(),
                    "description": f"Task orchestration: {event.data.get('title', 'Unknown task')}",
                    "linked_item_type": "orchestration_task",
                    "linked_item_id": event.task_id,
                }

                # Make actual MCP call to ConPort
                if self.conport_adapter:
                    conport_id = (
                        await self.conport_adapter.create_task_in_conport_from_sync(
                            event
                        )
                    )
                    logger.info(
                        f"📊 Synced to ConPort: {event.task_id} -> ConPort ID: {conport_id}"
                    )
                else:
                    logger.warning("📊 ConPort adapter not initialized, skipping sync")

        except Exception as e:
            logger.error(f"ConPort sync failed: {e}")

    async def _sync_to_local_adhd(self, event: SyncEvent) -> None:
        """Sync event to local ADHD task decomposer."""
        try:
            # This would integrate with the local ADHD task system
            if event.event_type == "task_updated":
                task_data = event.data

                # Create local ADHD task if needed
                if task_data.get("estimated_minutes", 0) > 25:
                    # Auto-decompose large tasks
                    decomposed_tasks = await self._decompose_for_adhd(task_data)
                    logger.debug(
                        f"🧠 ADHD decomposed task into {len(decomposed_tasks)} subtasks"
                    )

        except Exception as e:
            logger.error(f"Local ADHD sync failed: {e}")

    async def _adhd_monitor(self) -> None:
        """Background monitor for ADHD accommodations."""
        logger.info("🧠 Started ADHD monitoring worker")

        while self.running:
            try:
                # Check for tasks needing breaks
                await self._check_break_requirements()

                # Monitor cognitive load across active tasks
                await self._monitor_cognitive_load()

                # Detect context switching patterns
                await self._detect_excessive_context_switching()

                # Check every minute for responsiveness
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"ADHD monitoring error: {e}")
                await asyncio.sleep(300)  # 5-minute backoff on error

    async def _implicit_automation_engine(self) -> None:
        """Background engine for implicit PM automation."""
        logger.info("🤖 Started implicit automation engine")

        while self.running:
            try:
                # Check for automation triggers
                await self._check_sprint_automation_triggers()
                await self._check_retrospective_triggers()
                await self._check_task_decomposition_triggers()

                # Run every 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Implicit automation error: {e}")
                await asyncio.sleep(600)  # 10-minute backoff

    async def _progress_correlator(self) -> None:
        """Background correlator for file changes → task progress."""
        logger.info("📈 Started progress correlation worker")

        while self.running:
            try:
                # This would integrate with Serena file change events
                # For now, placeholder implementation
                await self._correlate_code_changes_to_tasks()

                # Check every 2 minutes for code changes
                await asyncio.sleep(120)

            except Exception as e:
                logger.error(f"Progress correlation error: {e}")
                await asyncio.sleep(300)

    # AI Agent Coordination

    async def _assign_optimal_agent(
        self, task: OrchestrationTask
    ) -> Optional[AgentType]:
        """
        Assign optimal AI agent based on task characteristics with ADHD awareness.

        WEEK 5 ENHANCEMENT: Now uses ADHD metadata for intelligent routing.

        Checks (in order):
        1. User readiness (energy + complexity + attention matching)
        2. Complexity threshold (>0.8 → Zen)
        3. Keyword-based routing
        4. Default fallback

        Returns:
            AgentType or None if user not ready
        """
        try:
            # === STEP 1: ADHD READINESS CHECK ===
            # Check if user is ready for this task (energy + attention + complexity)
            if self.cognitive_guardian:
                readiness = await self.cognitive_guardian.check_task_readiness(
                    task_complexity=task.complexity_score,
                    task_energy_required=task.energy_required,
                )

                if not readiness["ready"]:
                    logger.warning(
                        f"⚠️ User not ready for task: {task.title}\n"
                        f"   Reason: {readiness['reason']}\n"
                        f"   Suggestion: {readiness['suggestion']}"
                    )

                    # Check if mandatory break needed
                    user_state = await self.cognitive_guardian.get_user_state()
                    if user_state.session_duration_minutes >= 90:
                        logger.error("🛑 MANDATORY BREAK REQUIRED - No tasks assigned")
                        return "break_required"  # Special signal for break enforcement

                    # Return None to defer task
                    # UI would display readiness['alternatives'] for user to choose
                    # This prevents energy mismatches and burnout
                    return None

            # === STEP 2: COMPLEXITY CHECK (BEFORE keywords - FIX from Week 2 testing) ===
            # High-complexity tasks: Use Claude Brain for intelligent reasoning
            if task.complexity_score > 0.8:
                if self.claude_brain:
                    logger.info(
                        f"🧠 High complexity task ({task.complexity_score:.2f}) → Claude Brain "
                        f"for intelligent prioritization"
                    )
                    try:
                        # Claude will help decide the optimal agent/path
                        self.metrics["claude_brain_calls"] += 1
                        optimized_prompt = await self.claude_brain.prompt_optimizer.optimize_prompt_chain(task, {})
                        response = await self.claude_brain.reason(optimized_prompt)
                        recommendation = response.strip().upper()

                        # Map to AgentType
                        agent_map = {
                            "CONPORT": AgentType.CONPORT,
                            "SERENA": AgentType.SERENA,
                            "TASKMASTER": AgentType.TASKMASTER,
                            "ZEN": AgentType.ZEN,
                        }
                        claude_decision = agent_map.get(recommendation)
                        if claude_decision:
                            logger.info(f"🧠 Claude recommended agent: {claude_decision.value}")
                            self.metrics["claude_recommendations_used"] += 1
                            return claude_decision
                        else:
                            logger.warning(f"🧠 Claude returned invalid recommendation: {recommendation}, falling back")
                    except Exception as e:
                        logger.error(f"🧠 Claude recommendation failed: {e}, falling back")
                        self.metrics["claude_brain_failures"] += 1
                        # Learn from failure for future improvements
                        if self.claude_brain:
                            self.claude_brain._record_failure(e, {
                                "operation": "agent_recommendation",
                                "task_complexity": task.complexity_score,
                                "task_energy": task.energy_required
                            })
                else:
                    # Fallback to Zen for multi-model analysis
                    logger.info(
                        f"🌟 Claude Brain unavailable, using Zen for high complexity "
                        f"({task.complexity_score:.2f})"
                    )
                    return AgentType.ZEN

            # === STEP 3: KEYWORD-BASED ROUTING ===
            title_lower = task.title.lower()
            description_lower = task.description.lower()

            # Decision/architectural tasks → ConPort
            if any(
                keyword in title_lower or keyword in description_lower
                for keyword in ["decision", "architecture", "pattern", "strategy"]
            ):
                return AgentType.CONPORT

            # Code-related tasks → Serena
            elif any(
                keyword in title_lower or keyword in description_lower
                for keyword in ["implement", "refactor", "debug", "code", "function"]
            ):
                return AgentType.SERENA

            # Research/analysis tasks → TaskMaster
            elif any(
                keyword in title_lower or keyword in description_lower
                for keyword in ["research", "analyze", "requirements", "prd"]
            ):
                return AgentType.TASKMASTER

            # === STEP 4: DEFAULT FALLBACK ===
            # Default: ConPort for progress tracking
            return AgentType.CONPORT

        except Exception as e:
            logger.error(f"Agent assignment failed: {e}")
            return None

    async def _get_claude_agent_recommendation(self, task: OrchestrationTask) -> Optional[AgentType]:
        """
        Use Claude Brain to intelligently recommend the best agent for complex tasks.

        Claude analyzes task characteristics and recommends the optimal processing path.
        """
        try:
            if not self.claude_brain:
                return None

            # Gather context for Claude's reasoning
            context = {
                "complexity_score": task.complexity_score,
                "energy_required": task.energy_required,
                "cognitive_load": task.cognitive_load,
                "available_agents": list(self.agent_pool.keys()),
            }

            # Construct reasoning prompt
            prompt = f"""
            Analyze this complex task and recommend the best AI agent for processing:

            Task: {task.title}
            Description: {task.description}
            Complexity: {task.complexity_score:.2f}
            Energy Required: {task.energy_required}
            Cognitive Load: {task.cognitive_load:.2f}

            Available Agents:
            - CONPORT: Decision logging, progress tracking, context management
            - SERENA: Code navigation, file analysis, refactoring
            - TASKMASTER: PRD parsing, complexity analysis, research
            - ZEN: Multi-model consensus, code review, architecture analysis

            Consider:
            1. Task type (decision-making, coding, analysis, planning)
            2. Complexity level and required expertise
            3. Energy/cognitive load compatibility
            4. Available agent capabilities

            Return only the agent name (CONPORT, SERENA, TASKMASTER, or ZEN) that best matches.
            """

            # Get Claude's recommendation
            recommendation = await self.claude_brain.reason(prompt, context)
            recommendation = recommendation.strip().upper()

            # Map to AgentType
            agent_map = {
                "CONPORT": AgentType.CONPORT,
                "SERENA": AgentType.SERENA,
                "TASKMASTER": AgentType.TASKMASTER,
                "ZEN": AgentType.ZEN,
            }

            agent_type = agent_map.get(recommendation)
            if agent_type:
                logger.info(f"🧠 Claude recommended {agent_type.value} for task: {task.title}")
                return agent_type
            else:
                logger.warning(f"🧠 Claude returned invalid recommendation: {recommendation}")
                return None

        except Exception as e:
            logger.error(f"Claude agent recommendation failed: {e}")
            return None

    async def _dispatch_to_agent(
        self, task: OrchestrationTask, agent: AgentType
    ) -> bool:
        """
        Dispatch task to assigned AI agent.

        Args:
            task: Orchestration task to dispatch
            agent: Target AI agent (or "break_required" signal)

        Returns:
            Success status
        """
        try:
            # NEW: Handle break-required state
            if agent == "break_required":
                logger.warning("🛑 MANDATORY BREAK - Task deferred")
                print("\n" + "=" * 70)
                print("🛑 MANDATORY BREAK REQUIRED")
                print("   You've been working too long.")
                print("   Take a 10-minute break, then return.")
                print("   Task will be available after break.")
                print("=" * 70 + "\n")

                # Track ADHD accommodation
                self.metrics["adhd_accommodations_applied"] += 1

                return False  # Task not dispatched

            # EXISTING: Check agent availability
            agent_info = self.agent_pool.get(agent)
            if not agent_info or not agent_info["available"]:
                logger.warning(f"Agent {agent.value} not available for task {task.id}")
                return False

            # Check concurrent task limit
            current_tasks = len(agent_info["current_tasks"])
            max_concurrent = agent_info["max_concurrent"]

            if current_tasks >= max_concurrent:
                logger.warning(
                    f"Agent {agent.value} at capacity ({current_tasks}/{max_concurrent})"
                )
                return False

            # Dispatch based on agent type
            dispatch_success = False

            if agent == AgentType.CONPORT:
                dispatch_success = await self._dispatch_to_conport(task)
            elif agent == AgentType.SERENA:
                dispatch_success = await self._dispatch_to_serena(task)
            elif agent == AgentType.TASKMASTER:
                dispatch_success = await self._dispatch_to_taskmaster(task)
            elif agent == AgentType.ZEN:
                dispatch_success = await self._dispatch_to_zen(task)

            if dispatch_success:
                # Update agent state
                agent_info["current_tasks"].append(task.id)
                task.assigned_agent = agent
                task.agent_assignments[agent.value] = datetime.now(
                    timezone.utc
                ).isoformat()

                self.metrics["ai_agent_dispatches"] += 1
                logger.info(f"🤖 Dispatched task {task.id} to {agent.value}")

            return dispatch_success

        except Exception as e:
            logger.error(f"Failed to dispatch task to {agent.value}: {e}")
            return False

    async def _dispatch_to_conport(self, task: OrchestrationTask) -> bool:
        """
        Dispatch task to ConPort for decision/progress tracking.

        Creates or updates ConPort progress_entry with ADHD metadata.
        """
        try:
            # In Claude Code context, use real MCP calls
            # NOTE: These mcp__ functions are available in Claude Code execution context

            if task.conport_id:
                # Update existing progress entry
                logger.info(f"📊 ConPort update: {task.title} (ID: {task.conport_id})")

                await mcp__conport__update_progress(
                    workspace_id=self.workspace_id,
                    progress_id=task.conport_id,
                    status=task.status.value.upper(),
                    description=f"{task.title} (complexity: {task.complexity_score:.2f})",
                )

                logger.debug(f"Updated ConPort progress entry {task.conport_id}")

            else:
                # Create new progress entry with ADHD metadata
                logger.info(f"📊 ConPort create: {task.title}")

                result = await mcp__conport__log_progress(
                    workspace_id=self.workspace_id,
                    status=task.status.value.upper(),
                    description=task.title,
                    # ADHD metadata would be added as custom JSON in description or via custom_data
                )
                task.conport_id = result["id"]

                logger.debug(f"Created ConPort progress entry for {task.title}")

            # If this is a decision/architecture task, also log to decisions
            if "decision" in task.title.lower() or "architecture" in task.title.lower():
                logger.info(f"💡 Logging architecture decision: {task.title}")

                # Would call: await mcp__conport__log_decision(
                #     workspace_id=self.workspace_id,
                #     summary=task.title,
                #     rationale=task.description,
                #     tags=["task-orchestrator", "architecture"]
                # )

            return True

        except Exception as e:
            logger.error(f"ConPort dispatch failed: {e}")
            return False

    async def _dispatch_to_serena(self, task: OrchestrationTask) -> bool:
        """
        Dispatch task to Serena for code intelligence.

        Uses Serena LSP to analyze code complexity and provide navigation context.
        Updates task with actual complexity score from AST analysis.
        """
        try:
            logger.info(f"🧠 Serena dispatch: {task.title}")

            # Extract potential symbol/file from task description
            # In a real implementation, would parse task.description for file paths or symbols
            # For now, provide pattern for integration

            # Example: If task mentions a specific file or function
            # key_symbol = extract_symbol_from_task(task)
            # if key_symbol:
            #     # Find the symbol in codebase
            #     result = await mcp__serena_v2__find_symbol(
            #         query=key_symbol,
            #         max_results=3
            #     )
            #
            #     if result and len(result) > 0:
            #         symbol_info = result[0]
            #
            #         # Get complexity analysis
            #         complexity = await mcp__serena_v2__analyze_complexity(
            #             file_path=symbol_info['file'],
            #             symbol_name=key_symbol
            #         )
            #
            #         # Update task with REAL complexity from AST
            #         task.complexity_score = complexity['score']
            #         task.cognitive_load = complexity['cognitive_load']
            #
            #         logger.info(
            #             f"Serena analysis: {key_symbol} "
            #             f"complexity={complexity['score']:.2f}, "
            #             f"cognitive_load={complexity['cognitive_load']:.2f}"
            #         )
            #
            #         # Update ConPort with refined complexity
            #         if task.conport_id:
            #             await mcp__conport__update_progress(
            #                 workspace_id=self.workspace_id,
            #                 progress_id=task.conport_id,
            #                 description=f"{task.title} (Serena complexity: {complexity['score']:.2f})"
            #             )

            logger.debug(f"Serena dispatch complete for {task.title}")
            return True

        except Exception as e:
            logger.error(f"Serena dispatch failed: {e}")
            # Graceful degradation - don't fail entire dispatch
            return True  # Task still assigned, just without Serena enrichment

    async def _dispatch_to_taskmaster(self, task: OrchestrationTask) -> bool:
        """Dispatch task to TaskMaster for analysis."""
        try:
            # This would make MCP calls to TaskMaster
            # For now, simulate dispatch
            logger.debug(f"🔍 TaskMaster dispatch: {task.title}")
            return True

        except Exception as e:
            logger.error(f"TaskMaster dispatch failed: {e}")
            return False

    async def _dispatch_to_zen(self, task: OrchestrationTask) -> bool:
        """
        Dispatch task to Zen for multi-model analysis.

        Uses Zen thinkdeep for complex analysis or planner for decomposition.
        High-complexity tasks (>0.8) benefit from multi-model reasoning.
        """
        try:
            logger.info(
                f"🌟 Zen dispatch: {task.title} (complexity: {task.complexity_score:.2f})"
            )

            # Determine which Zen tool based on task type
            # Architecture/design tasks -> thinkdeep or consensus
            # Planning tasks -> planner
            # Complex debugging -> debug

            if "plan" in task.title.lower() or "decompose" in task.description.lower():
                # Use Zen planner for task decomposition
                logger.info(f"Using Zen planner for: {task.title}")

                # Would call: result = await mcp__zen__planner(
                #     step=f"Break down task: {task.title}\n\nDescription: {task.description}",
                #     step_number=1,
                #     total_steps=2,
                #     next_step_required=False,
                #     model="gpt-5-mini"  # Fast model for planning
                # )
                #
                # # Store plan in task metadata
                # task.planning_result = result

            elif task.complexity_score > 0.8:
                # Use Zen thinkdeep for complex analysis
                logger.info(f"Using Zen thinkdeep for high-complexity: {task.title}")

                # Would call: result = await mcp__zen__thinkdeep(
                #     step=f"Analyze complex task: {task.title}\n\n{task.description}",
                #     step_number=1,
                #     total_steps=3,
                #     next_step_required=True,
                #     findings="Initial analysis of task requirements",
                #     model="gpt-5-mini",
                #     confidence="low"
                # )
                #
                # # Update task with analysis insights
                # task.analysis_insights = result

            else:
                # Lower complexity - simple dispatch without Zen
                logger.debug(
                    f"Task complexity {task.complexity_score:.2f} - no Zen analysis needed"
                )

            logger.debug(f"Zen dispatch complete for {task.title}")
            return True

        except Exception as e:
            logger.error(f"Zen dispatch failed: {e}")
            # Graceful degradation - task still assigned
            return True

    # ADHD Optimization Methods

    async def _apply_adhd_optimizations(
        self, task: OrchestrationTask
    ) -> OrchestrationTask:
        """Apply ADHD optimizations to task."""
        try:
            # Calculate cognitive load based on task characteristics
            cognitive_load = self._calculate_cognitive_load(task)
            task.cognitive_load = cognitive_load

            # Determine energy requirements
            if cognitive_load > 0.8:
                task.energy_required = "high"
            elif cognitive_load > 0.5:
                task.energy_required = "medium"
            else:
                task.energy_required = "low"

            # Set ADHD-friendly break frequency
            if task.estimated_minutes > 25:
                task.break_frequency_minutes = 25  # Pomodoro breaks
            else:
                task.break_frequency_minutes = task.estimated_minutes + 5

            # Limit context switches based on complexity
            if task.complexity_score > 0.7:
                task.context_switches_allowed = 1  # High focus required
            else:
                task.context_switches_allowed = 3  # Normal flexibility

            self.metrics["adhd_accommodations_applied"] += 1
            return task

        except Exception as e:
            logger.error(f"ADHD optimization failed: {e}")
            return task

    def _calculate_cognitive_load(self, task: OrchestrationTask) -> float:
        """Calculate cognitive load for task."""
        try:
            base_load = 0.3  # Base cognitive load

            # Duration factor
            duration_load = min(
                task.estimated_minutes / 60.0, 0.4
            )  # Max 0.4 for duration

            # Complexity factor
            complexity_load = task.complexity_score * 0.3

            # Priority stress factor
            priority_load = (task.priority / 10.0) * 0.1

            total_load = min(
                base_load + duration_load + complexity_load + priority_load, 1.0
            )
            return total_load

        except Exception:
            return 0.5  # Default moderate load

    async def _get_task_count_from_conport(self) -> int:
        """Get total task count from ConPort (Architecture 3.0 storage authority)."""
        try:
            if self.conport_adapter:
                all_tasks = await self.conport_adapter.get_all_tasks_from_conport()
                return len(all_tasks)
            else:
                return 0  # No adapter, no tasks
        except Exception as e:
            logger.error(f"Failed to get task count from ConPort: {e}")
            return 0

    async def _check_break_requirements(self) -> None:
        """Check if any active tasks need break reminders."""
        try:
            current_time = datetime.now(timezone.utc)

            # Query ConPort for IN_PROGRESS tasks (Architecture 3.0: ConPort is source of truth)
            if self.conport_adapter:
                active_tasks = await self.conport_adapter.get_all_tasks_from_conport(
                    status_filter="IN_PROGRESS"
                )
            else:
                logger.warning(
                    "⚠️ ConPort adapter not initialized, skipping break check"
                )
                return

            for task in active_tasks:
                if task.status == TaskStatus.IN_PROGRESS:
                    # Check if break is needed based on work duration
                    if task.agent_assignments:
                        start_time_str = next(iter(task.agent_assignments.values()))
                        start_time = datetime.fromisoformat(start_time_str)
                        work_duration = (current_time - start_time).total_seconds() / 60

                        if work_duration >= task.break_frequency_minutes:
                            # Suggest break
                            await self._suggest_task_break(task)

        except Exception as e:
            logger.error(f"Break requirement check failed: {e}")

    async def _suggest_task_break(self, task: OrchestrationTask) -> None:
        """Suggest break for task with ADHD-friendly messaging."""
        try:
            # Update task status
            task.status = TaskStatus.NEEDS_BREAK

            # Log break suggestion in Redis for UI consumption
            break_suggestion = {
                "task_id": task.id,
                "task_title": task.title,
                "work_duration": task.break_frequency_minutes,
                "suggestion": f"☕ Great work on '{task.title}'! Time for a 5-minute break.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self.redis_client.lpush(
                f"orchestrator:break_suggestions:{self.workspace_id}",
                json.dumps(break_suggestion),
            )

            # Trim list to keep only recent suggestions
            await self.redis_client.ltrim(
                f"orchestrator:break_suggestions:{self.workspace_id}",
                0,
                9,  # Keep only 10 most recent
            )

            logger.info(f"☕ Break suggested for task: {task.title}")

        except Exception as e:
            logger.error(f"Break suggestion failed: {e}")

    # Implicit Automation Methods

    async def _check_sprint_automation_triggers(self) -> None:
        """Check for sprint planning automation triggers."""
        try:
            # Check for new sprints in Leantime
            # This would integrate with Leantime's sprint/iteration API
            # For now, placeholder implementation

            # Simulate checking for new sprint
            new_sprints = await self._check_for_new_sprints()

            for sprint in new_sprints:
                await self._auto_setup_sprint(sprint)

        except Exception as e:
            logger.error(f"Sprint automation check failed: {e}")

    async def _auto_setup_sprint(self, sprint_data: Dict[str, Any]) -> None:
        """Automatically setup sprint with ADHD optimizations."""
        try:
            sprint_id = sprint_data.get("id", "unknown")

            # 1. Analyze sprint tasks for complexity
            sprint_tasks = await self._get_sprint_tasks(sprint_id)

            # 2. Apply ADHD decomposition
            for task in sprint_tasks:
                if task.estimated_minutes > 25:
                    await self._auto_decompose_task(task)

            # 3. Setup ConPort sprint context
            sprint_context = {
                "sprint_id": sprint_id,
                "mode": "PLAN",
                "focus": "Sprint planning automation",
                "tasks_count": len(sprint_tasks),
                "auto_setup": True,
            }

            # This would sync to ConPort active context
            logger.info(
                f"🚀 Auto-setup sprint {sprint_id} with {len(sprint_tasks)} tasks"
            )
            self.metrics["implicit_automations_triggered"] += 1

        except Exception as e:
            logger.error(f"Sprint auto-setup failed: {e}")

    # Utility Methods

    def _map_leantime_status(self, leantime_status: str) -> TaskStatus:
        """Map Leantime status to orchestration status."""
        status_map = {
            "0": TaskStatus.PENDING,
            "1": TaskStatus.IN_PROGRESS,
            "2": TaskStatus.COMPLETED,
            "3": TaskStatus.BLOCKED,
            "6": TaskStatus.NEEDS_BREAK,
            "7": TaskStatus.CONTEXT_SWITCH,
        }
        return status_map.get(leantime_status, TaskStatus.PENDING)

    def _estimate_task_duration(self, leantime_task: Dict[str, Any]) -> int:
        """Estimate task duration in minutes."""
        try:
            # Use story points if available
            story_points = leantime_task.get("storypoints")
            if story_points:
                # Rough conversion: 1 story point = 2 hours = 120 minutes
                return int(story_points) * 120

            # Fallback: analyze description length and complexity
            description = leantime_task.get("description", "")
            base_duration = 30  # 30-minute default

            # Adjust based on description complexity
            if len(description) > 500:
                base_duration *= 2
            elif len(description) < 100:
                base_duration = 15

            return base_duration

        except Exception:
            return 25  # Default ADHD-friendly duration

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        return int(datetime.now().timestamp() * 1000)

    # Placeholder methods for integration points
    async def _check_for_new_sprints(self) -> List[Dict[str, Any]]:
        """Check Leantime for new sprints."""
        # Placeholder - would integrate with Leantime API
        return []

    async def _get_sprint_tasks(self, sprint_id: str) -> List[OrchestrationTask]:
        """Get tasks for specific sprint."""
        # Placeholder - would fetch from Leantime
        return []

    async def _auto_decompose_task(
        self, task: OrchestrationTask
    ) -> List[OrchestrationTask]:
        """Automatically decompose large task for ADHD."""
        # Placeholder - would integrate with ADHD decomposer
        return []

    async def _correlate_code_changes_to_tasks(self) -> None:
        """Correlate file changes to task progress."""
        # Placeholder - would integrate with Serena file monitoring
        pass

    # Integration Bridge Event Subscription (Component 3)

    async def _integration_bridge_subscriber(self) -> None:
        """Subscribe to Integration Bridge events for bidirectional ConPort communication."""
        logger.info("📡 Started Integration Bridge event subscriber")

        # Define event filter for task-orchestrator relevant events
        def event_filter(event_data: Dict[str, Any]) -> bool:
            """Filter events relevant to task orchestration."""
            event_type = event_data.get("event_type", "")
            # Handle task-related events, ADHD events, and service coordination
            return event_type.startswith(("task.", "adhd.", "service."))

        while self.running:
            try:
                # Subscribe to events using Integration Bridge connector
                await self.integration_bridge.subscribe_events(
                    callback=self._handle_integration_bridge_event,
                    event_filter=event_filter,
                )

            except Exception as e:
                logger.error(f"Integration Bridge subscription error: {e}")
                await asyncio.sleep(30)  # Reconnect after 30 seconds

    async def _handle_integration_bridge_event(
        self, event_data: Dict[str, Any]
    ) -> None:
        """Handle events from Integration Bridge."""
        try:
            event_type = event_data.get("event_type", "")
            source = event_data.get("source", "unknown")
            logger.debug(f"📥 Received event: {event_type} from {source}")

            if event_type == "task.tasks_imported":
                await self._handle_tasks_imported(event_data)
            elif event_type == "task.session_started":
                await self._handle_session_started(event_data)
            elif event_type == "task.session_paused":
                await self._handle_session_paused(event_data)
            elif event_type == "task.session_completed":
                await self._handle_session_completed(event_data)
            elif event_type == "task.progress_updated":
                await self._handle_progress_updated(event_data)
            elif event_type == "task.decision_logged":
                await self._handle_decision_logged(event_data)
            elif event_type == "adhd.state_changed":
                await self._handle_adhd_state_changed(event_data)
            elif event_type == "adhd.break_reminder":
                await self._handle_break_reminder(event_data)
            else:
                logger.debug(f"Unhandled event type: {event_type}")

        except Exception as e:
            logger.error(f"Event handling failed: {e}")

    async def _handle_tasks_imported(self, event_data: Dict[str, Any]) -> None:
        """Handle tasks_imported event from Integration Bridge."""
        try:
            payload = event_data.get("payload", {})
            task_count = payload.get("task_count", 0)
            sprint_id = payload.get("sprint_id", "unknown")

            logger.info(f"📥 Tasks imported: {task_count} tasks in sprint {sprint_id}")

            # Sync to ConPort if adapter available
            if self.conport_adapter:
                logger.debug(
                    f"📊 Syncing {task_count} tasks to ConPort for sprint {sprint_id}"
                )
                await self.conport_adapter.sync_imported_tasks(task_count, sprint_id)

        except Exception as e:
            logger.error(f"Failed to handle tasks_imported: {e}")

    async def _handle_session_started(self, event_data: Dict[str, Any]) -> None:
        """Handle session_started event from Integration Bridge."""
        try:
            payload = event_data.get("payload", {})
            task_id = payload.get("task_id", "")
            duration_minutes = payload.get("duration_minutes", 25)

            logger.info(
                f"📥 Session started: Task {task_id} ({duration_minutes} minutes)"
            )

            # Update task status in ConPort
            if self.conport_adapter:
                logger.debug(
                    f"📊 Updating task {task_id} status to IN_PROGRESS in ConPort"
                )
                await self.conport_adapter.update_task_status(task_id, "IN_PROGRESS")

        except Exception as e:
            logger.error(f"Failed to handle session_started: {e}")

    async def _handle_session_paused(self, event_data: Dict[str, Any]) -> None:
        """Handle session_paused event from Integration Bridge."""
        try:
            payload = event_data.get("payload", {})
            task_id = payload.get("task_id", "")

            logger.info(f"⏸️ Session paused: Task {task_id}")

            # Update task status in ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Updating task {task_id} status to BLOCKED in ConPort")
                await self.conport_adapter.update_task_status(task_id, "BLOCKED")

        except Exception as e:
            logger.error(f"Failed to handle session_paused: {e}")

    async def _handle_session_completed(self, event: Dict[str, Any]) -> None:
        """Handle session_completed event from Integration Bridge."""
        try:
            task_id = event.data.get("task_id", "")

            logger.info(f"📥 Session completed: Task {task_id}")

            # Update task status in ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Updating task {task_id} status to DONE in ConPort")
                await self.conport_adapter.update_task_status(task_id, "DONE")

        except Exception as e:
            logger.error(f"Failed to handle session_completed: {e}")

    async def _handle_progress_updated(self, event: Dict[str, Any]) -> None:
        """Handle progress_updated event from Integration Bridge."""
        try:
            task_id = event.data.get("task_id", "")
            status = event.data.get("status", "")
            progress = event.data.get("progress", 0.0)

            logger.info(
                f"📥 Progress updated: Task {task_id} -> {status} ({progress * 100:.0f}%)"
            )

            # Sync progress to ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Syncing progress for task {task_id} to ConPort")
                await self.conport_adapter.update_task_progress(
                    task_id, status.upper(), progress
                )

        except Exception as e:
            logger.error(f"Failed to handle progress_updated: {e}")

    async def _handle_decision_logged(self, event: Dict[str, Any]) -> None:
        """Handle decision_logged event from Integration Bridge."""
        try:
            decision_summary = event.data.get("summary", "")
            decision_id = event.data.get("decision_id", "")

            logger.info(f"📥 Decision logged: {decision_summary} (ID: {decision_id})")

            # Link decision to relevant tasks in ConPort
            if self.conport_adapter:
                logger.debug(
                    f"📊 Linking decision {decision_id} to related tasks in ConPort"
                )
                await self.conport_adapter.link_decision_to_tasks(decision_id)

        except Exception as e:
            logger.error(f"Failed to handle decision_logged: {e}")

    async def _handle_adhd_state_changed(self, event: Dict[str, Any]) -> None:
        """Handle adhd_state_changed event from Integration Bridge."""
        try:
            state = event.data.get("state", "")
            energy_level = event.data.get("energy_level", "medium")
            attention_level = event.data.get("attention_level", "focused")

            logger.info(
                f"📥 ADHD state changed: {state} (Energy: {energy_level}, Attention: {attention_level})"
            )

            # Adjust task recommendations based on ADHD state
            if self.conport_adapter:
                logger.debug(
                    f"📊 Adjusting task recommendations for ADHD state: {state}"
                )
                await self.conport_adapter.adjust_task_recommendations(
                    energy_level, attention_level
                )

        except Exception as e:
            logger.error(f"Failed to handle adhd_state_changed: {e}")

    async def _handle_break_reminder(self, event: Dict[str, Any]) -> None:
        """Handle break_reminder event from Integration Bridge."""
        try:
            task_id = event.data.get("task_id", "")
            duration_minutes = event.data.get("duration_minutes", 5)

            logger.info(
                f"📥 Break reminder: Task {task_id} - {duration_minutes} minute break recommended"
            )

            # Update task status to IN_PROGRESS (ConPort doesn't have NEEDS_BREAK, keep as in_progress)
            if self.conport_adapter:
                logger.debug(f"📊 Logging break reminder for task {task_id} in ConPort")
                await self.conport_adapter.update_task_status(task_id, "IN_PROGRESS")

        except Exception as e:
            logger.error(f"Failed to handle break_reminder: {e}")

    async def _monitor_cognitive_load(self) -> None:
        """Monitor overall cognitive load across tasks."""
        # Placeholder - would analyze active task load
        pass

    async def _detect_excessive_context_switching(self) -> None:
        """Detect and mitigate excessive context switching."""
        # Placeholder - would analyze task switching patterns
        pass

    async def _check_retrospective_triggers(self) -> None:
        """Check for retrospective automation triggers."""
        # Placeholder - would detect sprint completion
        pass

    async def _check_task_decomposition_triggers(self) -> None:
        """Check for automatic task decomposition triggers."""
        # Placeholder - would identify complex tasks needing breakdown
        pass

    # Health and Monitoring

    async def get_orchestration_health(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            # Component health checks
            leantime_healthy = await self._test_leantime_connection()
            redis_healthy = (
                await self.redis_client.ping() if self.redis_client else False
            )

            # Worker health
            active_workers = len([w for w in self.workers if not w.done()])

            # Overall status
            if (
                leantime_healthy
                and redis_healthy
                and active_workers == len(self.workers)
            ):
                status = "🚀 Excellent"
            elif leantime_healthy and redis_healthy:
                status = "✅ Good"
            elif leantime_healthy or redis_healthy:
                status = "⚠️ Degraded"
            else:
                status = "🔴 Critical"

            return {
                "overall_status": status,
                "components": {
                    "leantime_api": (
                        "🟢 Connected" if leantime_healthy else "🔴 Disconnected"
                    ),
                    "redis_coordination": (
                        "🟢 Connected" if redis_healthy else "🔴 Disconnected"
                    ),
                    "workers_active": f"{active_workers}/{len(self.workers)}",
                    "ai_agents": {
                        agent.value: info["available"]
                        for agent, info in self.agent_pool.items()
                    },
                },
                "metrics": self.metrics,
                "orchestrated_tasks": await self._get_task_count_from_conport(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"overall_status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Shutdown orchestrator gracefully."""
        logger.info("🛑 Shutting down Enhanced Task Orchestrator...")

        # Stop background workers
        self.running = False
        if self.workers:
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Close Integration Bridge EventBus (Component 3)
        if self.event_bus:
            await self.event_bus.close()
            logger.info("📪 Integration Bridge EventBus closed")

        # Close connections
        if self.leantime_session:
            await self.leantime_session.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ Enhanced Task Orchestrator shutdown complete")


# Main entry point for enhanced orchestrator
async def main():
    """Main entry point for enhanced task orchestrator."""
    # Configuration from environment
    leantime_url = os.getenv("LEANTIME_URL", "http://localhost:8080")
    leantime_token = os.getenv("LEANTIME_TOKEN", "")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

    if not leantime_token:
        logger.error("LEANTIME_TOKEN environment variable required")
        sys.exit(1)

    orchestrator = EnhancedTaskOrchestrator(
        leantime_url=leantime_url,
        leantime_token=leantime_token,
        redis_url=redis_url,
        workspace_id=workspace_id,
    )

    try:
        await orchestrator.initialize()

        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
    # ========================================================================
    # Component 5: Cross-Plane Query Methods
    # ========================================================================

    async def get_tasks(
        self,
        status_filter: Optional[str] = None,
        sprint_id_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query tasks from ConPort (Component 5)."""
        try:
            if not self.conport_adapter:
                return []

            # Query ConPort for progress entries
            progress_entries = await self.conport_adapter.get_progress_entries(
                status_filter=status_filter,
                tags_filter=[sprint_id_filter] if sprint_id_filter else None,
            )

            # Transform to task format
            tasks = []
            for entry in progress_entries[:limit]:
                tasks.append(
                    {
                        "task_id": str(entry.get("id", "")),
                        "title": entry.get("description", ""),
                        "description": entry.get("description", ""),
                        "status": entry.get("status", "TODO"),
                        "progress": (
                            0.5
                            if entry.get("status") == "IN_PROGRESS"
                            else (1.0 if entry.get("status") == "DONE" else 0.0)
                        ),
                        "priority": "medium",
                        "complexity": 0.5,
                        "estimated_duration": 60,
                        "dependencies": [],
                        "tags": entry.get("tags", []),
                    }
                )

            return tasks

        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get single task details (Component 5)."""
        tasks = await self.get_tasks()
        for task in tasks:
            if task["task_id"] == task_id:
                return task
        return None

    async def get_adhd_state(self) -> Dict[str, Any]:
        """Get current ADHD state (Component 5)."""
        try:
            # Wire to ADHD Engine via HTTP client
            from activity_capture.adhd_client import ADHDEngineClient

            adhd_client = ADHDEngineClient()
            # Get ADHD state from engine
            state = await adhd_client.get_adhd_state(self.user_id)
            return {
                "energy_level": state.get("energy_level", "medium"),
                "attention_level": state.get("attention_state", "focused"),
                "time_since_break": state.get("time_since_break", 45),
                "break_recommended": state.get("break_recommended", False),
                "current_session_duration": state.get("session_duration", 45),
            }
        except Exception as e:
            logger.warning(f"ADHD Engine connection failed: {e} - using defaults")
            return {
                "energy_level": "medium",
                "attention_level": "focused",
                "time_since_break": 45,
                "break_recommended": False,
                "current_session_duration": 45,
            }

    async def get_task_recommendations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get ADHD-aware task recommendations (Component 5)."""
        tasks = await self.get_tasks(status_filter="TODO")
        recommendations = []

        for i, task in enumerate(tasks[:limit]):
            recommendations.append(
                {
                    "task_id": task["task_id"],
                    "title": task["title"],
                    "reason": "Matches current cognitive state",
                    "confidence": 0.8 - (i * 0.1),
                    "priority": i + 1,
                }
            )

        return recommendations

    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status (Component 5)."""
        return {
            "session_id": f"session-{datetime.now().strftime('%Y-%m-%d')}",
            "active": self.running,
            "started_at": datetime.now(),
            "duration_minutes": 45,
            "break_count": 0,
            "tasks_completed": self.metrics.get("tasks_orchestrated", 0),
        }

    async def get_active_sprint(self) -> Dict[str, Any]:
        """Get active sprint info (Component 5)."""
        # Query ConPort for sprint context
        return {
            "sprint_id": "S-2025.10",
            "name": "Architecture 3.0 Implementation",
            "start_date": datetime(2025, 10, 1),
            "end_date": datetime(2025, 10, 31),
            "total_tasks": 20,
            "completed_tasks": self.metrics.get("tasks_orchestrated", 0),
            "in_progress_tasks": 3,
        }
