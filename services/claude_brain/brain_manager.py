"""
Claude Brain Manager - Core orchestration for prompt optimization and AI services

This module provides the central coordination for Claude Brain operations,
including LiteLLM routing, multi-service integration, and cost optimization.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

import aiohttp
import redis.asyncio as redis
from litellm import completion, completion_cost
from litellm.exceptions import APIConnectionError, RateLimitError

from .config import settings
from .cache_manager import CacheManager
from .failure_handler import FailureHandler

logger = logging.getLogger(__name__)


@dataclass
class ProviderProfile:
    """AI provider profile with capabilities and costs."""
    name: str
    cost_tier: str  # FREE, LOW, MEDIUM, HIGH
    cost_per_1k_tokens: float
    avg_quality_score: float  # 0.0-1.0
    avg_response_time: float  # seconds
    rate_limit_per_hour: int
    max_context_length: int
    team_model_id: str
    agent_model_id: str


@dataclass
class ServiceIntegration:
    """Integration point for external services."""
    service_name: str
    base_url: str
    health_endpoint: str = "/health"
    api_key: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class ClaudeBrainRequest:
    """Request object for brain operations."""
    operation: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    cognitive_load: float = 0.5  # 0.0-1.0 ADHD cognitive load
    attention_state: str = "focused"  # focused, scattered, hyperfocused, fatigued
    max_tokens: int = 1000
    temperature: float = 0.3
    model_preference: Optional[str] = None


@dataclass
class ClaudeBrainResponse:
    """Response object for brain operations."""
    success: bool
    result: Any
    provider_used: str
    model_used: str
    tokens_used: int
    cost: float
    processing_time: float
    cached: bool = False
    error_message: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


class ClaudeBrainManager:
    """
    Central manager for Claude Brain operations.

    Coordinates prompt optimization, multi-service integration, and intelligent
    provider routing with ADHD accommodations and cost optimization.
    """

    def __init__(self):
        self.cache_manager = CacheManager()
        self.failure_handler = FailureHandler()

        # Provider configurations
        self.providers = self._initialize_providers()

        # Service integrations
        self.services = self._initialize_services()

        # Performance tracking
        self.request_count = 0
        self.total_cost = 0.0
        self.avg_response_time = 0.0

        # ADHD optimization state
        self.current_cognitive_load = 0.5
        self.attention_state = "focused"

    def _initialize_providers(self) -> Dict[str, ProviderProfile]:
        """Initialize AI provider profiles with capabilities and costs."""
        return {
            "openrouter": ProviderProfile(
                name="openrouter",
                cost_tier="MEDIUM",
                cost_per_1k_tokens=0.001,
                avg_quality_score=0.90,
                avg_response_time=3.0,
                rate_limit_per_hour=1000,
                max_context_length=200000,
                team_model_id="anthropic/claude-3.5-sonnet",
                agent_model_id="anthropic/claude-3.5-haiku"
            ),
            "anthropic": ProviderProfile(
                name="anthropic",
                cost_tier="HIGH",
                cost_per_1k_tokens=0.015,
                avg_quality_score=0.95,
                avg_response_time=2.0,
                rate_limit_per_hour=1000,
                max_context_length=200000,
                team_model_id="claude-3-5-sonnet-20241022",
                agent_model_id="claude-3-5-haiku-20241022"
            ),
            "openai": ProviderProfile(
                name="openai",
                cost_tier="HIGH",
                cost_per_1k_tokens=0.010,
                avg_quality_score=0.92,
                avg_response_time=1.5,
                rate_limit_per_hour=10000,
                max_context_length=128000,
                team_model_id="gpt-4o",
                agent_model_id="gpt-4o-mini"
            ),
            "groq": ProviderProfile(
                name="groq",
                cost_tier="FREE",
                cost_per_1k_tokens=0.0,
                avg_quality_score=0.75,
                avg_response_time=0.8,
                rate_limit_per_hour=14400,
                max_context_length=32768,
                team_model_id="llama3-groq-70b-8192-tool-use-preview",
                agent_model_id="llama3-groq-8b-8192-tool-use-preview"
            )
        }

    def _initialize_services(self) -> Dict[str, ServiceIntegration]:
        """Initialize external service integrations."""
        return {
            "adhd_engine": ServiceIntegration(
                service_name="adhd_engine",
                base_url=settings.ADHD_ENGINE_URL or "http://localhost:8095",
                api_key=settings.ADHD_ENGINE_API_KEY
            ),
            "conport": ServiceIntegration(
                service_name="conport",
                base_url=settings.CONPORT_URL or "http://localhost:5455",
                api_key=settings.CONPORT_API_KEY
            ),
            "serena": ServiceIntegration(
                service_name="serena",
                base_url=settings.SERENA_URL or "http://localhost:8003",
                api_key=settings.SERENA_API_KEY
            )
        }

    async def initialize(self) -> bool:
        """Initialize the brain manager and all components."""
        try:
            logger.info("🧠 Initializing Claude Brain Manager...")

            # Initialize cache manager
            await self.cache_manager.initialize()

            # Test service connections
            await self._test_service_connections()

            logger.info("✅ Claude Brain Manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude Brain Manager: {e}")
            return False

    async def _test_service_connections(self) -> None:
        """Test connections to integrated services."""
        for service_name, service in self.services.items():
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {}
                    if service.api_key:
                        headers["Authorization"] = f"Bearer {service.api_key}"

                    async with session.get(
                        f"{service.base_url}{service.health_endpoint}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"✅ {service_name} connection healthy")
                        else:
                            logger.warning(f"⚠️ {service_name} returned status {response.status}")

            except Exception as e:
                logger.warning(f"⚠️ {service_name} connection failed: {e}")

    def _select_optimal_provider(self, request: ClaudeBrainRequest) -> Tuple[str, str]:
        """
        Select the optimal AI provider based on request characteristics.

        Considers cost, quality, speed, and ADHD optimization needs.
        """
        # ADHD-aware provider selection
        if request.cognitive_load > 0.7:  # High cognitive load
            # Use faster, more reliable providers
            if request.attention_state in ["scattered", "fatigued"]:
                return "groq", self.providers["groq"].agent_model_id  # Fast and free
            else:
                return "anthropic", self.providers["anthropic"].agent_model_id

        # Cost optimization for normal cognitive load
        if settings.COST_OPTIMIZATION_ENABLED:
            # Use free tier when possible
            return "groq", self.providers["groq"].agent_model_id

        # Quality optimization for complex requests
        if len(request.prompt) > 1000 or request.max_tokens > 2000:
            return "anthropic", self.providers["anthropic"].team_model_id

        # Default to OpenRouter for balance
        return "openrouter", self.providers["openrouter"].agent_model_id

    async def _query_adhd_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Query ADHD Engine for user context and cognitive state."""
        try:
            service = self.services["adhd_engine"]
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {service.api_key}"} if service.api_key else {}

                async with session.get(
                    f"{service.base_url}/api/v1/user-profile/{user_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.current_cognitive_load = data.get("cognitive_load", 0.5)
                        self.attention_state = data.get("attention_state", "focused")
                        return data

        except Exception as e:
            logger.debug(f"ADHD context query failed: {e}")

        return {
            "cognitive_load": self.current_cognitive_load,
            "attention_state": self.attention_state,
            "energy_level": "medium",
            "focus_duration": 1500  # 25 minutes
        }

    async def _log_decision(self, operation: str, provider: str, cost: float, success: bool) -> None:
        """Log decision to ConPort for pattern analysis."""
        try:
            service = self.services["conport"]
            decision_data = {
                "summary": f"AI Provider Selection: {operation} → {provider}",
                "rationale": f"Selected {provider} based on cost (${cost:.4f}), cognitive load ({self.current_cognitive_load:.1f}), and attention state ({self.attention_state})",
                "implementation_details": f"Operation: {operation}, Cost: ${cost:.4f}, Success: {success}",
                "tags": ["ai_provider_selection", "cost_optimization", "adhd_optimization", operation]
            }

            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {service.api_key}"} if service.api_key else {}
                headers["Content-Type"] = "application/json"

                async with session.post(
                    f"{service.base_url}/api/decisions",
                    json=decision_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status not in [200, 201]:
                        logger.debug(f"Decision logging failed: {response.status}")

        except Exception as e:
            logger.debug(f"Decision logging error: {e}")

    async def process_request(self, request: ClaudeBrainRequest) -> ClaudeBrainResponse:
        """
        Process a Claude Brain request with intelligent routing and optimization.

        This is the main entry point for all brain operations.
        """
        start_time = time.time()
        self.request_count += 1

        try:
            # Check cache first
            cache_key = f"{request.operation}:{hash(request.prompt)}:{request.user_id}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                return ClaudeBrainResponse(
                    success=True,
                    result=cached_result,
                    provider_used="cache",
                    model_used="cached",
                    tokens_used=0,
                    cost=0.0,
                    processing_time=time.time() - start_time,
                    cached=True
                )

            # Query ADHD context if user provided
            if request.user_id and request.session_id:
                await self._query_adhd_context(request.user_id, request.session_id)

            # Select optimal provider
            provider, model = self._select_optimal_provider(request)

            # Check circuit breaker
            if not self.failure_handler.can_proceed(provider):
                # Fallback to secondary provider
                if provider == "anthropic":
                    provider, model = "openrouter", self.providers["openrouter"].agent_model_id
                else:
                    provider, model = "groq", self.providers["groq"].agent_model_id

            # Make the AI request
            response = await self._make_ai_request(request, provider, model)

            # Update performance metrics
            processing_time = time.time() - start_time
            self.avg_response_time = (self.avg_response_time + processing_time) / 2
            self.total_cost += response.cost

            # Cache successful results
            if response.success and len(str(response.result)) > 100:
                await self.cache_manager.set(cache_key, response.result, ttl=3600)

            # Log decision for pattern analysis
            await self._log_decision(request.operation, provider, response.cost, response.success)

            # Update circuit breaker
            self.failure_handler.record_result(provider, response.success)

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Brain request failed: {e}")

            return ClaudeBrainResponse(
                success=False,
                result=None,
                provider_used="error",
                model_used="error",
                tokens_used=0,
                cost=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )

    async def _make_ai_request(self, request: ClaudeBrainRequest, provider: str, model: str) -> ClaudeBrainResponse:
        """Make the actual AI API request with error handling."""
        try:
            # Prepare messages based on operation type
            messages = self._prepare_messages(request)

            # ADHD-optimized parameters
            temperature = self._optimize_temperature(request)
            max_tokens = self._optimize_max_tokens(request)

            # Make the completion call
            response = await completion(
                model=f"{provider}/{model}",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=60
            )

            # Calculate cost
            cost = completion_cost(response)

            return ClaudeBrainResponse(
                success=True,
                result=response.choices[0].message.content,
                provider_used=provider,
                model_used=model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                cost=cost,
                processing_time=0.0  # Will be set by caller
            )

        except RateLimitError:
            self.failure_handler.record_result(provider, False)
            return ClaudeBrainResponse(
                success=False,
                result=None,
                provider_used=provider,
                model_used=model,
                tokens_used=0,
                cost=0.0,
                processing_time=0.0,
                error_message="Rate limit exceeded"
            )

        except APIConnectionError as e:
            self.failure_handler.record_result(provider, False)
            return ClaudeBrainResponse(
                success=False,
                result=None,
                provider_used=provider,
                model_used=model,
                tokens_used=0,
                cost=0.0,
                processing_time=0.0,
                error_message=f"API connection failed: {str(e)}"
            )

        except Exception as e:
            self.failure_handler.record_result(provider, False)
            return ClaudeBrainResponse(
                success=False,
                result=None,
                provider_used=provider,
                model_used=model,
                tokens_used=0,
                cost=0.0,
                processing_time=0.0,
                error_message=f"Unexpected error: {str(e)}"
            )

            logger.error(f"Error: {e}")
    def _prepare_messages(self, request: ClaudeBrainRequest) -> List[Dict[str, str]]:
        """Prepare messages for the AI request based on operation type."""
        system_prompt = self._get_system_prompt(request)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.prompt}
        ]

        # Add context if provided
        if request.context:
            context_str = f"\n\nContext: {json.dumps(request.context, indent=2)}"
            messages[1]["content"] += context_str

        return messages

    def _get_system_prompt(self, request: ClaudeBrainRequest) -> str:
        """Get optimized system prompt based on operation and ADHD context."""
        base_prompt = "You are Claude Brain, an advanced AI assistant optimized for ADHD-friendly interactions."

        # ADHD accommodations
        adhd_accommodations = """
ADHD Optimization Guidelines:
- Provide clear, structured responses with bullet points when helpful
- Lead with the most important information
- Use progressive disclosure (essential info first, details on request)
- Keep explanations concise but comprehensive
- Include specific, actionable next steps
- Avoid overwhelming amounts of information at once"""

        # Cognitive load adjustments
        if request.cognitive_load > 0.7:
            adhd_accommodations += "\n- Use very short paragraphs and simple language"
            adhd_accommodations += "\n- Break complex ideas into smaller, digestible pieces"
        elif request.attention_state in ["scattered", "fatigued"]:
            adhd_accommodations += "\n- Use visual indicators (✅ ❌ ⚠️ 💡 🎯)"
            adhd_accommodations += "\n- Provide gentle, encouraging tone"

        # Operation-specific instructions
        operation_instructions = self._get_operation_instructions(request.operation)

        return f"{base_prompt}\n\n{adhd_accommodations}\n\n{operation_instructions}"

    def _get_operation_instructions(self, operation: str) -> str:
        """Get operation-specific instructions."""
        instructions = {
            "optimize_prompt": "Focus on improving prompt clarity, specificity, and effectiveness. Provide concrete improvements with examples.",
            "generate_meta_prompt": "Create meta-prompts that guide prompt evolution and improvement cycles.",
            "analyze_critique": "Provide detailed analysis of prompt quality with specific improvement recommendations.",
            "brain_reasoning": "Apply advanced reasoning techniques including chain-of-thought and systematic analysis."
        }

        return instructions.get(operation, "Provide helpful, accurate, and well-structured responses.")

    def _optimize_temperature(self, request: ClaudeBrainRequest) -> float:
        """Optimize temperature based on cognitive load and operation type."""
        base_temp = request.temperature

        # Adjust for cognitive load
        if request.cognitive_load > 0.7:
            base_temp = min(base_temp, 0.3)  # More deterministic for high load
        elif request.attention_state == "hyperfocused":
            base_temp = min(base_temp + 0.2, 0.9)  # Allow more creativity when hyperfocused

        # Adjust for operation type
        if request.operation in ["optimize_prompt", "analyze_critique"]:
            base_temp = min(base_temp, 0.2)  # More deterministic for analysis

        return base_temp

    def _optimize_max_tokens(self, request: ClaudeBrainRequest) -> int:
        """Optimize max tokens based on cognitive load and operation."""
        base_tokens = request.max_tokens

        # Reduce for high cognitive load
        if request.cognitive_load > 0.7:
            base_tokens = min(base_tokens, 500)  # Shorter responses

        # Increase for complex operations
        if request.operation in ["brain_reasoning", "analyze_critique"]:
            base_tokens = max(base_tokens, 2000)  # Allow more detailed analysis

        return base_tokens

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the brain manager."""
        return {
            "status": "operational",
            "version": "1.0.0",
            "requests_processed": self.request_count,
            "total_cost": round(self.total_cost, 4),
            "avg_response_time": round(self.avg_response_time, 2),
            "cache_stats": await self.cache_manager.get_stats(),
            "circuit_breaker_status": self.failure_handler.get_status(),
            "cognitive_state": {
                "current_load": self.current_cognitive_load,
                "attention_state": self.attention_state
            },
            "service_health": await self._check_service_health()
        }

    async def _check_service_health(self) -> Dict[str, bool]:
        """Check health of integrated services."""
        health = {}
        for service_name, service in self.services.items():
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {service.api_key}"} if service.api_key else {}
                    async with session.get(
                        f"{service.base_url}{service.health_endpoint}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        health[service_name] = response.status == 200
            except Exception as e:
                health[service_name] = False

                logger.error(f"Error: {e}")
        return health