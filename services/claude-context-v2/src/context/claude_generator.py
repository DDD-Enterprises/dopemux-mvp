"""
Claude Context Generator - Task 3
Generates contextual snippets for code chunks using Anthropic's Claude API.

Based on Anthropic's contextual retrieval research:
https://www.anthropic.com/news/contextual-retrieval
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from ..preprocessing.code_chunker import CodeChunk


logger = logging.getLogger(__name__)


@dataclass
class ContextRequest:
    """Request for context generation."""

    chunk: CodeChunk
    file_path: str
    module_name: Optional[str] = None

    def cache_key(self) -> str:
        """Generate cache key."""
        content = f"{self.file_path}:{self.chunk.start_line}:{self.chunk.end_line}:{self.chunk.content}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ContextResponse:
    """Generated context response."""

    context: str
    tokens_used: int
    cached: bool = False
    cost_usd: float = 0.0


@dataclass
class CostTracker:
    """Track Claude API costs."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    total_cost_usd: float = 0.0
    cache_hits: int = 0

    # Claude pricing (Haiku - fast and cheap for context generation)
    # Input: $0.25/M tokens, Output: $1.25/M tokens
    INPUT_PRICE_PER_M = 0.25
    OUTPUT_PRICE_PER_M = 1.25

    def add_request(
        self,
        input_tokens: int,
        output_tokens: int,
        cached: bool = False
    ) -> float:
        """Add request and return cost."""
        self.total_requests += 1

        if cached:
            self.cache_hits += 1
            return 0.0

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        cost = (
            (input_tokens / 1_000_000) * self.INPUT_PRICE_PER_M +
            (output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_M
        )
        self.total_cost_usd += cost
        return cost

    def summary(self) -> Dict:
        """Get cost summary."""
        cache_rate = self.cache_hits / max(self.total_requests, 1)
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cache_hits": self.cache_hits,
            "cache_rate": round(cache_rate, 3),
        }


class ClaudeContextGenerator:
    """
    Generates context snippets for code chunks using Claude API.

    Features:
    - Batch processing (up to 10 chunks per API call)
    - In-memory caching with TTL
    - Cost tracking
    - Anthropic's contextual retrieval approach
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-20241022",
        cache_ttl_hours: int = 720,  # 30 days (contexts rarely change)
        max_batch_size: int = 10,
    ):
        """
        Initialize Claude context generator.

        Args:
            api_key: Anthropic API key
            model: Claude model (default: Haiku for speed/cost)
            cache_ttl_hours: Cache TTL (default: 30 days)
            max_batch_size: Max chunks per batch (default: 10)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.cache: Dict[str, Tuple[ContextResponse, datetime]] = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.max_batch_size = max_batch_size
        self.cost_tracker = CostTracker()

    def _get_cached(self, cache_key: str) -> Optional[ContextResponse]:
        """Get cached context if valid."""
        if cache_key not in self.cache:
            return None

        response, cached_at = self.cache[cache_key]

        # Check TTL
        if datetime.now() - cached_at > self.cache_ttl:
            del self.cache[cache_key]
            return None

        # Return cached response
        cached_response = ContextResponse(
            context=response.context,
            tokens_used=response.tokens_used,
            cached=True,
            cost_usd=0.0,
        )
        return cached_response

    def _cache_response(self, cache_key: str, response: ContextResponse):
        """Cache context response."""
        self.cache[cache_key] = (response, datetime.now())

    def _build_context_prompt(
        self,
        chunk: CodeChunk,
        file_path: str,
        module_name: Optional[str] = None,
    ) -> str:
        """
        Build prompt for context generation.

        Format: "This {type} from {file} {does what}. {Dependencies}."
        Target: 50-100 tokens (concise but informative)
        """
        # Determine what to call this chunk
        chunk_desc = {
            "function": "function",
            "method": "method",
            "class": "class",
            "block": "code block",
        }.get(chunk.chunk_type, "code")

        # Module context
        if module_name:
            location = f"{module_name}.{chunk.symbol_name}" if chunk.symbol_name else module_name
        else:
            location = f"{file_path}"

        prompt = f"""Generate a concise 2-3 sentence context description for this {chunk_desc}.

Location: {location}
Language: {chunk.language}
Lines: {chunk.start_line}-{chunk.end_line}

Code:
```{chunk.language}
{chunk.content}
```

Write a context snippet in this format:
"This [function/class/method] from [module] in [file_path] [purpose]. [Key dependencies or relationships]. [What it does or returns]."

Keep it under 100 tokens. Focus on PURPOSE and RELATIONSHIPS, not implementation details.

Context:"""

        return prompt

    async def generate_context(
        self,
        chunk: CodeChunk,
        file_path: str,
        module_name: Optional[str] = None,
    ) -> ContextResponse:
        """
        Generate context for a single code chunk.

        Args:
            chunk: Code chunk to generate context for
            file_path: Full file path
            module_name: Module name (optional)

        Returns:
            ContextResponse with generated context
        """
        request = ContextRequest(
            chunk=chunk,
            file_path=file_path,
            module_name=module_name,
        )

        # Check cache
        cache_key = request.cache_key()
        cached = self._get_cached(cache_key)
        if cached:
            self.cost_tracker.add_request(0, 0, cached=True)
            logger.debug(f"Cache hit for {file_path}:{chunk.start_line}")
            return cached

        # Build prompt
        prompt = self._build_context_prompt(chunk, file_path, module_name)

        try:
            # Call Claude API
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=150,  # ~100 token context + buffer
                temperature=0.0,  # Deterministic
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract context
            context = message.content[0].text.strip()

            # Track cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            cost = self.cost_tracker.add_request(
                input_tokens, output_tokens, cached=False
            )

            response = ContextResponse(
                context=context,
                tokens_used=input_tokens + output_tokens,
                cached=False,
                cost_usd=cost,
            )

            # Cache
            self._cache_response(cache_key, response)

            logger.debug(
                f"Generated context for {file_path}:{chunk.start_line} "
                f"({output_tokens} tokens, ${cost:.6f})"
            )

            return response

        except Exception as e:
            logger.error(f"Context generation failed: {e}")
            # Fallback: simple context
            fallback_context = (
                f"This {chunk.chunk_type} from {file_path} "
                f"(lines {chunk.start_line}-{chunk.end_line})."
            )
            return ContextResponse(
                context=fallback_context,
                tokens_used=0,
                cached=False,
                cost_usd=0.0,
            )

    async def generate_contexts_batch(
        self,
        chunks: List[CodeChunk],
        file_paths: List[str],
        module_names: Optional[List[str]] = None,
    ) -> List[ContextResponse]:
        """
        Generate contexts for multiple chunks in batch.

        Uses batching of prompts (up to max_batch_size) for efficiency.

        Args:
            chunks: List of code chunks
            file_paths: List of file paths (same length as chunks)
            module_names: Optional list of module names

        Returns:
            List of ContextResponse in same order as input
        """
        if not chunks:
            return []

        if len(chunks) != len(file_paths):
            raise ValueError("chunks and file_paths must have same length")

        if module_names is None:
            module_names = [None] * len(chunks)

        # Check cache for all chunks
        responses: List[Optional[ContextResponse]] = []
        uncached_indices: List[int] = []
        uncached_requests: List[ContextRequest] = []

        for i, (chunk, file_path, module_name) in enumerate(
            zip(chunks, file_paths, module_names)
        ):
            request = ContextRequest(
                chunk=chunk,
                file_path=file_path,
                module_name=module_name,
            )
            cache_key = request.cache_key()
            cached = self._get_cached(cache_key)

            if cached:
                self.cost_tracker.add_request(0, 0, cached=True)
                responses.append(cached)
            else:
                responses.append(None)
                uncached_indices.append(i)
                uncached_requests.append(request)

        # If all cached, return
        if not uncached_requests:
            logger.debug(f"All {len(chunks)} contexts cached")
            return responses  # type: ignore

        logger.debug(
            f"Batch: {len(chunks)} total, {len(uncached_requests)} uncached"
        )

        # Process uncached in batches
        all_contexts: List[ContextResponse] = []

        for i in range(0, len(uncached_requests), self.max_batch_size):
            batch = uncached_requests[i:i + self.max_batch_size]

            # Generate contexts concurrently
            tasks = [
                self.generate_context(
                    req.chunk, req.file_path, req.module_name
                )
                for req in batch
            ]

            batch_results = await asyncio.gather(*tasks)
            all_contexts.extend(batch_results)

        # Merge cached and new contexts
        for idx, response in zip(uncached_indices, all_contexts):
            responses[idx] = response

        return responses  # type: ignore

    def clear_cache(self):
        """Clear context cache."""
        self.cache.clear()
        logger.info("Context cache cleared")

    def get_cost_summary(self) -> Dict:
        """Get cost tracking summary."""
        return self.cost_tracker.summary()


# Example usage
async def main():
    """Example usage of ClaudeContextGenerator."""
    import os
    from ..preprocessing.code_chunker import CodeChunker, CodeChunk

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY environment variable")
        return

    generator = ClaudeContextGenerator(api_key=api_key)
    chunker = CodeChunker()

    # Example code
    code = '''
def calculate_user_score(user_id: int, activity_data: dict) -> float:
    """Calculate engagement score based on user activity."""
    if not activity_data:
        return 0.0

    weights = {"posts": 2.0, "comments": 1.0, "likes": 0.5}
    score = sum(activity_data.get(k, 0) * v for k, v in weights.items())
    return min(score / 100.0, 1.0)
'''

    # Chunk code
    chunks = chunker.chunk_code_string(code, language="python")

    # Generate context
    if chunks:
        response = await generator.generate_context(
            chunk=chunks[0],
            file_path="src/scoring/user_metrics.py",
            module_name="scoring.user_metrics",
        )

        print(f"Generated context ({response.tokens_used} tokens, ${response.cost_usd:.6f}):")
        print(response.context)
        print()

        # Show contextualized content
        print("Contextualized content:")
        print(f"{response.context}\n\n{chunks[0].content}")

    # Cost summary
    summary = generator.get_cost_summary()
    print(f"\nCost summary: {summary}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
