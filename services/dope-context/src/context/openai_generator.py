"""
OpenAI Context Generator
Drop-in replacement for ClaudeContextGenerator using OpenAI API.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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


class OpenAIContextGenerator:
    """
    OpenAI-based context generator.
    Compatible interface with ClaudeContextGenerator.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",  # Fast and cheap
        cache_ttl_hours: int = 168,  # 1 week
    ):
        """
        Initialize OpenAI context generator.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-5-mini)
            cache_ttl_hours: Cache TTL in hours
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: Dict[str, tuple[ContextResponse, datetime]] = {}

        # Stats
        self.total_requests = 0
        self.cache_hits = 0
        self.total_tokens = 0

        logger.info(f"OpenAI context generator initialized with model {model}")

    async def generate_context(
        self,
        chunk: CodeChunk,
        file_path: str,
        module_name: Optional[str] = None,
    ) -> ContextResponse:
        """
        Generate context for a code chunk.

        Args:
            chunk: Code chunk to contextualize
            file_path: Path to source file
            module_name: Optional module name

        Returns:
            ContextResponse with generated context
        """
        request = ContextRequest(
            chunk=chunk,
            file_path=file_path,
            module_name=module_name
        )

        # Check cache
        cache_key = request.cache_key()
        if cache_key in self._cache:
            response, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                self.cache_hits += 1
                return ContextResponse(
                    context=response.context,
                    tokens_used=0,
                    cached=True,
                    cost_usd=0.0
                )

        # Generate context
        self.total_requests += 1

        prompt = self._build_prompt(chunk, file_path, module_name)

        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code documentation assistant. Generate concise, informative context descriptions for code chunks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # gpt-5-mini only supports default temperature=1, max_completion_tokens instead of max_tokens
                max_completion_tokens=200
            )

            context = completion.choices[0].message.content.strip()
            tokens_used = completion.usage.total_tokens
            input_tokens = completion.usage.prompt_tokens
            output_tokens = completion.usage.completion_tokens

            # Calculate cost (gpt-5-mini pricing)
            cost_usd = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)

            self.total_tokens += tokens_used

            response = ContextResponse(
                context=context,
                tokens_used=tokens_used,
                cached=False,
                cost_usd=cost_usd
            )

            # Cache result
            self._cache[cache_key] = (response, datetime.now())

            return response

        except Exception as e:
            logger.error(f"Context generation failed: {e}")
            # Return fallback context
            return ContextResponse(
                context=f"Code from {file_path}",
                tokens_used=0,
                cached=False,
                cost_usd=0.0
            )

    async def generate_contexts_batch(
        self,
        chunks: List[CodeChunk],
        file_paths: List[str],
        module_names: Optional[List[str]] = None,
    ) -> List[ContextResponse]:
        """
        Generate contexts for multiple chunks in batch.

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

        # Generate contexts in parallel
        tasks = [
            self.generate_context(chunk, file_path, module_name)
            for chunk, file_path, module_name in zip(chunks, file_paths, module_names)
        ]

        return await asyncio.gather(*tasks)

    def _build_prompt(
        self,
        chunk: CodeChunk,
        file_path: str,
        module_name: Optional[str] = None
    ) -> str:
        """Build prompt for context generation."""

        file_context = f"File: {file_path}"
        if module_name:
            file_context += f"\nModule: {module_name}"

        return f"""Generate a concise contextual description (2-3 sentences) for this code chunk.

{file_context}
Lines: {chunk.start_line}-{chunk.end_line}

Code:
```
{chunk.content}
```

Provide a brief description that would help someone understand what this code does and where it fits in the codebase. Focus on purpose and functionality, not implementation details."""

    def get_stats(self) -> Dict:
        """Get usage statistics."""
        cache_rate = self.cache_hits / self.total_requests if self.total_requests > 0 else 0
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_rate": round(cache_rate, 3),
            "total_tokens": self.total_tokens,
            "avg_tokens_per_request": round(self.total_tokens / max(1, self.total_requests - self.cache_hits), 1)
        }
