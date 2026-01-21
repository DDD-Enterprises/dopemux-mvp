"""
Grok Context Generator - Fast, FREE context generation via OpenRouter

Uses xAI's grok-code-fast-1 via OpenRouter for generating contextual code descriptions.
- FREE on OpenRouter
- Code-specialized (better than grok-4 for code understanding)
- Intelligence 18 (top-tier model)
- 2M context window
- Fast inference
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import List
import aiohttp


logger = logging.getLogger(__name__)


@dataclass
class ContextResponse:
    """Response from context generation."""

    context: str
    tokens: int = 0
    cached: bool = False
    cost_usd: float = 0.0  # Grok-4-Fast is FREE!


class GrokContextGenerator:
    """
    Generate code context descriptions using Grok-4-Fast via Zen MCP.

    Features:
    - FREE context generation (no API costs!)
    - Fast inference with grok-4-fast
    - 2M context window (handles large files)
    - Graceful fallback on errors
    """

    def __init__(
        self,
        model: str = "xai/grok-code-fast-1",
        fail_on_error: bool = False,
        api_key: str = None,
    ):
        """
        Initialize Grok context generator.

        Args:
            model: OpenRouter model to use (default: xai/grok-code-fast-1 - FREE)
            fail_on_error: If True, raise on generation errors; if False, return simple fallback
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
        """
        self.model = model
        self.fail_on_error = fail_on_error
        self.total_requests = 0
        self.failed_requests = 0

        # Get API key
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.openrouter_available = bool(self.api_key)

        if not self.openrouter_available:
            logger.warning(
                "⚠️  OPENROUTER_API_KEY not set - will use fallback context generation"
            )
        else:
            logger.info(f"✅ OpenRouter API available - using {self.model}")

    async def generate_context(
        self,
        chunk_content: str,
        file_path: str,
        function_name: str = None,
    ) -> ContextResponse:
        """
        Generate contextual description for a code chunk using Grok via Zen MCP.

        Args:
            chunk_content: Code content
            file_path: File path for context
            function_name: Optional function/class name

        Returns:
            ContextResponse with generated context
        """
        self.total_requests += 1

        # Build prompt
        symbol = f" ({function_name})" if function_name else ""
        prompt = f"""Generate a concise 2-3 sentence description of this code from {file_path}{symbol}:

```
{chunk_content[:2000]}  # Limit to 2000 chars
```

Focus on: What does this code do? What's its purpose in the larger system?"""

        # Try OpenRouter API if available
        if self.openrouter_available:
            try:
                # Call OpenRouter API
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 200,  # 2-3 sentences = ~150 tokens
                        },
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            context = data["choices"][0]["message"]["content"].strip()

                            if context:
                                logger.debug(f"Generated context with {self.model} for {file_path}")
                                return ContextResponse(
                                    context=context,
                                    tokens=data.get("usage", {}).get("total_tokens", 0),
                                    cost_usd=0.0,  # FREE!
                                )
                        else:
                            error_text = await response.text()
                            logger.warning(f"OpenRouter API error {response.status}: {error_text}")

                # If we got here, API call failed - use fallback
                self.failed_requests += 1
                context = self._generate_fallback_context(
                    file_path, function_name, chunk_content
                )

                return ContextResponse(
                    context=context,
                    tokens=0,
                    cost_usd=0.0,
                )

            except Exception as e:
                logger.warning(f"Grok context generation failed: {e}")
                self.failed_requests += 1

                if self.fail_on_error:
                    raise

                # Fallback to simple context
                context = self._generate_fallback_context(
                    file_path, function_name, chunk_content
                )

                return ContextResponse(
                    context=context,
                    tokens=0,
                    cost_usd=0.0,
                )

        # No OpenRouter API available - use fallback
        context = self._generate_fallback_context(
            file_path, function_name, chunk_content
        )

        return ContextResponse(
            context=context,
            tokens=0,
            cost_usd=0.0,
        )

    async def generate_contexts_batch(
        self,
        chunks: List,
        file_paths: List[str],
    ) -> List[ContextResponse]:
        """
        Generate contexts for multiple chunks.

        Args:
            chunks: List of CodeChunk objects
            file_paths: List of file paths

        Returns:
            List of ContextResponse objects
        """
        responses = []

        for chunk, file_path in zip(chunks, file_paths):
            response = await self.generate_context(
                chunk_content=chunk.content,
                file_path=file_path,
                function_name=chunk.symbol_name,
            )
            responses.append(response)

        return responses

    def _generate_fallback_context(
        self,
        file_path: str,
        function_name: str,
        chunk_content: str,
    ) -> str:
        """Generate simple fallback context."""

        # Try to infer purpose from code
        lines = chunk_content.split('\n')

        # Look for docstring
        for line in lines[:5]:
            line = line.strip()
            if line.startswith('"""') or line.startswith("'''"):
                # Extract first line of docstring
                docstring = line.strip('"""').strip("'''").strip()
                if docstring and function_name:
                    return f"Function {function_name} from {file_path}: {docstring}"
                elif docstring:
                    return f"Code from {file_path}: {docstring}"

        # Generic fallback
        if function_name:
            return f"Function {function_name} defined in {file_path}"
        else:
            return f"Code from {file_path}"

    def get_cost_summary(self) -> dict:
        """Get cost summary (always $0 for Grok!)."""
        failure_rate = self.failed_requests / max(self.total_requests, 1)

        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "failure_rate": round(failure_rate, 3),
            "total_cost_usd": 0.0,  # FREE!
            "model": self.model,
        }


# Example usage
async def main():
    """Example usage of GrokContextGenerator."""

    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.info("❌ OPENROUTER_API_KEY not set")
        logger.info("Set with: export OPENROUTER_API_KEY=your_key_here")
        return

    generator = GrokContextGenerator(
        model="xai/grok-code-fast-1",
        fail_on_error=False,
    )

    # Test context generation
    code = """
def calculate_complexity(node: Node) -> float:
    '''Calculate ADHD-friendly complexity score (0.0-1.0).'''

    def count_depth(n: Node, depth: int = 0) -> int:
        if not n.children:
            return depth
        return max(count_depth(c, depth + 1) for c in n.children)

    def count_branches(n: Node) -> int:
        count = 0
        if n.type in ('if_statement', 'for_statement', 'while_statement'):
            count += 1
        for child in n.children:
            count += count_branches(child)
        return count

    depth = count_depth(node)
    branches = count_branches(node)
    lines = node.end_point[0] - node.start_point[0] + 1

    complexity = depth_score * 0.3 + branch_score * 0.4 + lines_score * 0.3
    return round(complexity, 2)
"""

    logger.info("=" * 80)
    logger.info("TESTING GROK-CODE-FAST-1 CONTEXT GENERATION")
    logger.info("=" * 80)

    response = await generator.generate_context(
        chunk_content=code,
        file_path="src/preprocessing/code_chunker.py",
        function_name="calculate_complexity",
    )

    logger.info(f"\nContext: {response.context}")
    logger.info(f"Tokens: {response.tokens}")
    logger.info(f"Cost: ${response.cost_usd:.6f} (FREE!)")

    # Cost summary
    summary = generator.get_cost_summary()
    logger.info(f"\nSummary: {summary}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
