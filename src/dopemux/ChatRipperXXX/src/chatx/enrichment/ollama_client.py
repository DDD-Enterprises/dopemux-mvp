"""Production Ollama client with async patterns and monitoring."""

import asyncio
import hashlib
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional
from dataclasses import dataclass, asdict

try:
    import httpx
except ImportError:
    httpx = None

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    # Fallback decorator for environments without tenacity
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = wait_exponential = retry_if_exception_type = lambda *args, **kwargs: None

from chatx.enrichment.models import (
    MessageEnrichment, 
    EnrichmentRequest,
    EnrichmentResponse, 
    BatchEnrichmentRequest,
    BatchEnrichmentResponse
)

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama-related errors."""
    pass


class RetryableOllamaError(OllamaError):
    """Errors that should be retried."""
    pass


@dataclass
class OllamaModelConfig:
    """Configuration for Ollama model settings."""
    name: str = "gemma2:9b-instruct-q4_K_M"
    temperature: float = 0.0  # Deterministic for consistency
    seed: int = 42  # Fixed seed for reproducibility
    num_predict: int = 800  # Token limit for structured output
    context_window: int = 8192  # Context size for throughput
    top_k: int = 1  # Most deterministic sampling
    top_p: float = 0.1  # Very focused sampling
    repeat_penalty: float = 1.1  # Slight penalty for repetition


@dataclass 
class PerformanceMetrics:
    """Performance tracking for Ollama operations."""
    requests_processed: int = 0
    total_time_seconds: float = 0.0
    average_latency_ms: float = 0.0
    throughput_requests_per_second: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0
    confidence_low_count: int = 0  # confidence < 0.4
    confidence_medium_count: int = 0  # 0.4 <= confidence < 0.7
    confidence_high_count: int = 0  # confidence >= 0.7


class OllamaHealthMonitor:
    """Monitor Ollama server health and availability."""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check using Ollama API."""
        try:
            # Check server availability
            response = await self.client.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                
                # Check if our target model is available
                target_model = "gemma2:9b-instruct-q4_K_M"
                model_available = any(target_model in model for model in models)
                
                return {
                    "status": "healthy",
                    "server_available": True,
                    "target_model_available": model_available,
                    "available_models": models,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "status": "unhealthy",
                    "server_available": False,
                    "status_code": response.status_code
                }
                
        except httpx.TimeoutException:
            return {"status": "timeout", "server_available": False}
        except Exception as e:
            return {"status": "error", "server_available": False, "error": str(e)}
    
    async def wait_for_ready(self, max_wait_seconds: int = 60) -> bool:
        """Wait for Ollama to be ready with exponential backoff."""
        wait_time = 1
        total_waited = 0
        
        while total_waited < max_wait_seconds:
            health = await self.health_check()
            if health.get("status") == "healthy" and health.get("target_model_available"):
                logger.info(f"Ollama ready after {total_waited}s")
                return True
            
            logger.info(f"Ollama not ready, waiting {wait_time}s... ({total_waited}s elapsed)")
            await asyncio.sleep(wait_time)
            total_waited += wait_time
            wait_time = min(wait_time * 2, 10)  # Cap at 10s
        
        logger.error(f"Ollama not ready after {max_wait_seconds}s")
        return False


class OllamaMemoryOptimizer:
    """Configure Ollama for optimal memory usage and performance."""
    
    @staticmethod
    def configure_environment() -> dict[str, str]:
        """Set environment variables for optimal performance."""
        config = {
            # Memory optimization (2025 features)
            "OLLAMA_NEW_ESTIMATES": "1",  # Improved memory estimation
            "OLLAMA_KV_CACHE_TYPE": "q8_0",  # Quantized KV cache (50-75% memory reduction)
            "OLLAMA_FLASH_ATTENTION": "1",  # Improved throughput
            
            # Parallel processing
            "OLLAMA_NUM_PARALLEL": "4",  # Number of parallel requests
            "OLLAMA_MAX_LOADED_MODELS": "2",  # Keep models in memory
            
            # GPU optimization
            "OLLAMA_GPU_LAYERS": "-1",  # Use all available GPU layers
            "OLLAMA_GPU_MEMORY_FRACTION": "0.8",  # Reserve 20% GPU memory
        }

        for key, value in config.items():
            os.environ[key] = value
            logger.debug(f"Set {key}={value}")
        
        return config


class ProductionOllamaClient:
    """Production-ready Ollama client with async patterns and monitoring."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        max_concurrent: int = 4,
        timeout: int = 30,
        model_config: Optional[OllamaModelConfig] = None
    ):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.model_config = model_config or OllamaModelConfig()
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # HTTP client
        self.client: Optional[httpx.AsyncClient] = None
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.latencies: list[float] = []
        
        # Configure memory optimization
        OllamaMemoryOptimizer.configure_environment()
        
        logger.info(
            f"Initialized Ollama client: {base_url}, "
            f"max_concurrent={max_concurrent}, model={self.model_config.name}"
        )
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=self.max_concurrent * 2)
        )
        
        # Wait for Ollama to be ready
        async with OllamaHealthMonitor(self.base_url) as monitor:
            if not await monitor.wait_for_ready():
                raise OllamaError("Ollama server not ready")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    @asynccontextmanager
    async def rate_limited_request(self):
        """Context manager for rate-limited requests."""
        async with self.semaphore:
            yield
    
    def _compute_prompt_hash(self, prompt: str, model_config: OllamaModelConfig) -> str:
        """Compute deterministic hash of prompt and model config."""
        content = f"{prompt}:{model_config.name}:{model_config.temperature}:{model_config.seed}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _build_enrichment_prompt(self, request: EnrichmentRequest) -> str:
        """Build structured prompt for message enrichment."""
        context_str = ""
        if request.context:
            context_msgs = []
            for ctx_msg in request.context[-2:]:  # Last 2 messages for context
                sender = "ME" if ctx_msg.get("is_me") else request.contact
                context_msgs.append(f"{sender}: {ctx_msg.get('text', '')}")
            context_str = "Context:\n" + "\n".join(context_msgs) + "\n\n"
        
        prompt = f"""{context_str}Analyze this message and provide detailed enrichment following the exact JSON schema:

Message: "{request.text}"
Sender: {"ME" if request.text else request.contact}
Platform: {request.platform}

Provide a comprehensive analysis including:
1. Speech act classification (ask, inform, promise, refuse, apologize, propose, meta)
2. Primary emotion (joy, anger, fear, sadness, disgust, surprise, neutral)
3. Communication stance (supportive, neutral, challenging)
4. Intent and inferred meaning (concise)
5. Boundary signals if any (none, set, test, violate, reinforce)
6. Certainty and directness levels (0.0 to 1.0)
7. Your confidence in this analysis (0.0 to 1.0)

Respond with valid JSON matching the MessageEnrichment schema exactly."""
        
        return prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(RetryableOllamaError),
        reraise=True
    )
    async def _robust_chat_request(
        self, 
        prompt: str, 
        schema: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Make robust chat request with automatic retry."""
        async with self.rate_limited_request():
            try:
                payload = {
                    "model": self.model_config.name,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {
                        "temperature": self.model_config.temperature,
                        "seed": self.model_config.seed,
                        "num_predict": self.model_config.num_predict,
                        "top_k": self.model_config.top_k,
                        "top_p": self.model_config.top_p,
                        "repeat_penalty": self.model_config.repeat_penalty,
                    },
                    "stream": False  # Disable streaming for determinism
                }
                
                # Add JSON schema if provided (Ollama structured output)
                if schema:
                    payload["format"] = schema
                
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [502, 503, 429]:
                    # Retryable errors
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(f"Retryable error: {error_msg}")
                    raise RetryableOllamaError(error_msg)
                else:
                    # Non-retryable errors
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Non-retryable error: {error_msg}")
                    raise OllamaError(error_msg)
                    
            except httpx.TimeoutException as e:
                logger.warning(f"Request timeout: {e}")
                raise RetryableOllamaError(f"Timeout: {e}") from e
            
            except httpx.ConnectError as e:
                logger.warning(f"Connection error: {e}")
                raise RetryableOllamaError(f"Connection error: {e}") from e
            
            except Exception as e:
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in [
                    "rate limit", "too many requests", "overloaded", "busy"
                ]):
                    logger.warning(f"Rate limit or overload: {e}")
                    raise RetryableOllamaError(f"Retryable error: {e}") from e
                else:
                    logger.error(f"Non-retryable error: {e}")
                    raise OllamaError(f"Non-retryable error: {e}") from e
    
    async def enrich_message(self, request: EnrichmentRequest) -> EnrichmentResponse:
        """Enrich a single message with structured analysis."""
        start_time = time.time()
        
        try:
            # Build prompt
            prompt = self._build_enrichment_prompt(request)
            prompt_hash = self._compute_prompt_hash(prompt, self.model_config)
            
            # Get JSON schema for structured output
            schema = MessageEnrichment.model_json_schema()
            
            # Make request to Ollama
            response_data = await self._robust_chat_request(prompt, schema)
            
            # Parse response
            message_content = response_data.get("message", {}).get("content", "")
            if not message_content:
                raise OllamaError("Empty response from Ollama")
            
            # Parse and validate with Pydantic
            try:
                enrichment_dict = json.loads(message_content)
                enrichment_dict["msg_id"] = request.msg_id
                enrichment_dict["source"] = "local"
                
                enrichment = MessageEnrichment(**enrichment_dict)
                
                # Set provenance
                enrichment.set_provenance(
                    run_id="local_enrichment",
                    model_id=self.model_config.name,
                    prompt_hash=prompt_hash
                )
                
                # Track confidence distribution
                if enrichment.confidence_llm < 0.4:
                    self.metrics.confidence_low_count += 1
                elif enrichment.confidence_llm < 0.7:
                    self.metrics.confidence_medium_count += 1
                else:
                    self.metrics.confidence_high_count += 1
                
                processing_time_ms = (time.time() - start_time) * 1000
                self.latencies.append(time.time() - start_time)
                
                return EnrichmentResponse(
                    msg_id=request.msg_id,
                    enrichment=enrichment,
                    processing_time_ms=processing_time_ms
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {request.msg_id}: {e}")
                logger.debug(f"Raw response: {message_content}")
                raise OllamaError(f"Invalid JSON response: {e}") from e
            
            except Exception as e:
                logger.error(f"Pydantic validation error for {request.msg_id}: {e}")
                raise OllamaError(f"Schema validation error: {e}") from e
        
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            self.metrics.error_count += 1
            
            return EnrichmentResponse(
                msg_id=request.msg_id,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
    
    async def enrich_batch(self, batch_request: BatchEnrichmentRequest) -> BatchEnrichmentResponse:
        """Process a batch of enrichment requests with concurrency control."""
        start_time = time.time()
        
        logger.info(f"Processing batch {batch_request.batch_id} with {len(batch_request.requests)} messages")
        
        # Process all requests concurrently
        tasks = [self.enrich_message(req) for req in batch_request.requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch item {i} failed with exception: {response}")
                processed_responses.append(EnrichmentResponse(
                    msg_id=batch_request.requests[i].msg_id,
                    error=str(response),
                    processing_time_ms=0
                ))
            else:
                processed_responses.append(response)
        
        total_time_ms = (time.time() - start_time) * 1000
        
        # Update metrics
        self.metrics.requests_processed += len(batch_request.requests)
        self.metrics.total_time_seconds += (total_time_ms / 1000)
        
        # Calculate response statistics
        success_count = sum(1 for r in processed_responses if r.enrichment is not None)
        error_count = sum(1 for r in processed_responses if r.error is not None)
        
        # Update throughput metrics
        if self.metrics.total_time_seconds > 0:
            self.metrics.throughput_requests_per_second = (
                self.metrics.requests_processed / self.metrics.total_time_seconds
            )
        
        if self.latencies:
            self.metrics.average_latency_ms = sum(self.latencies) / len(self.latencies) * 1000
        
        if self.metrics.requests_processed > 0:
            self.metrics.error_rate = self.metrics.error_count / self.metrics.requests_processed
        
        logger.info(
            f"Batch {batch_request.batch_id} complete: "
            f"{success_count} success, {error_count} errors, "
            f"{total_time_ms:.1f}ms total, "
            f"{self.metrics.throughput_requests_per_second:.1f} msg/s"
        )
        
        return BatchEnrichmentResponse(
            batch_id=batch_request.batch_id,
            responses=processed_responses,
            total_processing_time_ms=total_time_ms,
            success_count=success_count,
            error_count=error_count
        )
    
    async def process_message_stream(
        self, 
        messages: AsyncIterator[EnrichmentRequest]
    ) -> AsyncIterator[EnrichmentResponse]:
        """Process messages as a stream with backpressure control."""
        batch = []
        batch_size = min(50, self.max_concurrent * 10)  # Optimal batch size
        
        async for message in messages:
            batch.append(message)
            
            if len(batch) >= batch_size:
                batch_request = BatchEnrichmentRequest(requests=batch)
                batch_response = await self.enrich_batch(batch_request)
                
                for response in batch_response.responses:
                    yield response
                
                batch = []
                
                # Apply backpressure if throughput too high
                if self.metrics.throughput_requests_per_second > 30:  # Above target
                    await asyncio.sleep(0.1)
        
        # Process remaining messages
        if batch:
            batch_request = BatchEnrichmentRequest(requests=batch)
            batch_response = await self.enrich_batch(batch_request)
            
            for response in batch_response.responses:
                yield response
    
    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        p95_latency_ms = 0.0
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            p95_index = int(0.95 * len(sorted_latencies))
            p95_latency_ms = sorted_latencies[p95_index] * 1000
        
        return {
            **asdict(self.metrics),
            "p95_latency_ms": p95_latency_ms,
            "meets_throughput_target": self.metrics.throughput_requests_per_second >= 25.0,
            "meets_latency_target": p95_latency_ms <= 250.0,  # From NFR requirements
        }
