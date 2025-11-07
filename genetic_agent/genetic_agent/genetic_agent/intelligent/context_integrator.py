"""Context Integration Framework for intelligent repair assistance."""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ..shared.mcp.serena_client import SerenaClient
from ..shared.mcp.dope_context_client import DopeContextClient
from ..core.config import AgentConfig


@dataclass
class ContextSource:
    """Represents a single context source with metadata."""
    name: str
    content: Dict[str, Any]
    relevance_score: float = 0.0
    token_estimate: int = 0
    source_type: str = "unknown"  # "static", "dynamic", "semantic"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnhancedContext:
    """Enhanced context with prioritization and progressive disclosure."""
    essential_context: Dict[str, Any]
    full_context: Dict[str, Any]
    total_sources: int = 0
    prioritized_sources: List[str] = field(default_factory=list)
    token_budget_used: int = 0
    max_token_budget: int = 2000
    quality_score: float = 0.0


class ContextIntegrator:
    """Integrates context from multiple sources for intelligent repair assistance."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.serena_client = SerenaClient(config.serena_url, config)
        self.dope_client = DopeContextClient(config.dope_context_url, config)

        # Context relevance weights
        self.relevance_weights = {
            "static": 0.4,    # Code structure, complexity
            "dynamic": 0.35,  # Runtime behavior, test traces
            "semantic": 0.25  # Similar patterns, natural language
        }

    async def gather_context(self, issue_context: Dict[str, Any]) -> EnhancedContext:
        """Gather and integrate context from all available sources."""
        context_sources = await self._collect_all_sources(issue_context)

        # Score and prioritize sources
        scored_sources = self._score_sources(context_sources, issue_context)

        # Apply progressive disclosure
        enhanced_context = self._apply_progressive_disclosure(scored_sources, issue_context)

        return enhanced_context

    async def _collect_all_sources(self, issue_context: Dict[str, Any]) -> List[ContextSource]:
        """Collect context from all available sources concurrently."""
        sources = []

        # Static context (code structure, complexity)
        static_task = self._gather_static_context(issue_context)
        # Dynamic context (runtime traces, test patterns)
        dynamic_task = self._gather_dynamic_context(issue_context)
        # Semantic context (similar patterns, documentation)
        semantic_task = self._gather_semantic_context(issue_context)

        # Execute all concurrently
        results = await asyncio.gather(static_task, dynamic_task, semantic_task, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            source_type = ["static", "dynamic", "semantic"][i]

            if isinstance(result, Exception):
                # Handle collection failures gracefully
                error_source = ContextSource(
                    name=f"{source_type}_error",
                    content={"error": str(result), "available": False},
                    source_type=source_type
                )
                sources.append(error_source)
            else:
                sources.extend(result)

        return sources

    async def _gather_static_context(self, issue_context: Dict[str, Any]) -> List[ContextSource]:
        """Gather static context from code structure and analysis."""
        sources = []

        try:
            async with self.serena_client:
                # Code complexity analysis
                complexity = await self.serena_client.analyze_complexity(
                    issue_context.get("file_path", ""),
                    issue_context.get("function_name", "")
                )

                if complexity and not complexity.get("error"):
                    sources.append(ContextSource(
                        name="code_complexity",
                        content=complexity,
                        source_type="static"
                    ))

                # AST-level code structure (placeholder for future enhancement)
                # This could include function signatures, class hierarchies, etc.

        except Exception as e:
            sources.append(ContextSource(
                name="static_context_error",
                content={"error": str(e), "available": False},
                source_type="static"
            ))

        return sources

    async def _gather_dynamic_context(self, issue_context: Dict[str, Any]) -> List[ContextSource]:
        """Gather dynamic context from runtime behavior and test traces."""
        sources = []

        # Test execution patterns (placeholder - would integrate with test runner)
        test_patterns = {
            "test_coverage": issue_context.get("test_coverage", 0),
            "failing_tests": issue_context.get("failing_tests", []),
            "execution_path": issue_context.get("execution_path", [])
        }

        if test_patterns.get("failing_tests"):
            sources.append(ContextSource(
                name="test_failure_patterns",
                content=test_patterns,
                source_type="dynamic"
            ))

        # Runtime traces (placeholder - would integrate with instrumentation)
        runtime_traces = issue_context.get("runtime_traces", [])
        if runtime_traces:
            sources.append(ContextSource(
                name="runtime_execution_trace",
                content={"traces": runtime_traces},
                source_type="dynamic"
            ))

        return sources

    async def _gather_semantic_context(self, issue_context: Dict[str, Any]) -> List[ContextSource]:
        """Gather semantic context from similar patterns and documentation."""
        sources = []

        try:
            async with self.dope_client:
                # Similar code patterns
                similar_patterns = await self.dope_client.search_code(
                    f"fix {issue_context.get('description', '')}",
                    top_k=5
                )

                if similar_patterns and similar_patterns.get("results"):
                    sources.append(ContextSource(
                        name="similar_repair_patterns",
                        content=similar_patterns,
                        source_type="semantic"
                    ))

                # Related documentation or comments
                # This could include docstring analysis, comments, etc.

        except Exception as e:
            sources.append(ContextSource(
                name="semantic_context_error",
                content={"error": str(e), "available": False},
                source_type="semantic"
            ))

        return sources

    def _score_sources(self, sources: List[ContextSource], issue_context: Dict[str, Any]) -> List[ContextSource]:
        """Score sources by relevance to the issue."""
        for source in sources:
            # Base relevance from source type
            base_relevance = self.relevance_weights.get(source.source_type, 0.1)

            # Content-specific relevance adjustments
            content_relevance = self._assess_content_relevance(source, issue_context)

            # Token efficiency factor (prefer high-value, low-token sources)
            token_efficiency = 1.0 / max(source.token_estimate, 1)

            # Combine factors
            source.relevance_score = base_relevance * content_relevance * token_efficiency

            # Estimate token usage for this source
            source.token_estimate = self._estimate_token_usage(source)

        # Sort by relevance score (highest first)
        sources.sort(key=lambda s: s.relevance_score, reverse=True)

        return sources

    def _assess_content_relevance(self, source: ContextSource, issue_context: Dict[str, Any]) -> float:
        """Assess how relevant the source content is to the issue."""
        issue_description = issue_context.get("description", "").lower()
        issue_type = issue_context.get("error_type", "").lower()

        relevance_score = 1.0

        # Boost relevance for error-specific content
        if source.name == "code_complexity" and "complexity" in issue_description:
            relevance_score *= 1.5

        if source.name == "test_failure_patterns" and ("test" in issue_description or "assert" in issue_description):
            relevance_score *= 1.8

        if source.name == "similar_repair_patterns":
            # Check if similar patterns match issue type
            patterns = source.content.get("results", [])
            matching_patterns = [p for p in patterns if issue_type in str(p).lower()]
            if matching_patterns:
                relevance_score *= 1.3

        # Penalize error sources
        if "error" in source.name:
            relevance_score *= 0.3

        return min(relevance_score, 2.0)  # Cap at 2x boost

    def _estimate_token_usage(self, source: ContextSource) -> int:
        """Estimate token usage for including this source."""
        # Rough estimation based on content size
        content_str = str(source.content)
        # Estimate ~4 characters per token
        estimated_tokens = len(content_str) // 4

        # Adjust based on source type
        if source.source_type == "static":
            estimated_tokens = int(estimated_tokens * 0.8)  # More structured
        elif source.source_type == "semantic":
            estimated_tokens = int(estimated_tokens * 1.2)  # More verbose

        return max(estimated_tokens, 10)  # Minimum estimate

    def _apply_progressive_disclosure(self, sources: List[ContextSource],
                                    issue_context: Dict[str, Any]) -> EnhancedContext:
        """Apply progressive disclosure to create essential vs full context."""
        essential_context = {}
        full_context = {}
        prioritized_sources = []
        total_tokens = 0
        max_budget = self.config.get("context_token_budget", 2000)

        for source in sources:
            source_name = source.name
            source_content = source.content

            # Add to full context always
            full_context[source_name] = {
                "content": source_content,
                "relevance": source.relevance_score,
                "tokens": source.token_estimate,
                "type": source.source_type
            }

            # Add to essential context if within budget and high relevance
            if (total_tokens + source.token_estimate <= max_budget and
                source.relevance_score >= 0.3):  # Minimum relevance threshold

                essential_context[source_name] = source_content
                prioritized_sources.append(source_name)
                total_tokens += source.token_estimate

        # Calculate overall quality score
        quality_score = self._calculate_context_quality(essential_context, sources)

        return EnhancedContext(
            essential_context=essential_context,
            full_context=full_context,
            total_sources=len(sources),
            prioritized_sources=prioritized_sources,
            token_budget_used=total_tokens,
            max_token_budget=max_budget,
            quality_score=quality_score
        )

    def _calculate_context_quality(self, essential_context: Dict[str, Any],
                                 all_sources: List[ContextSource]) -> float:
        """Calculate overall quality score of the gathered context."""
        if not essential_context:
            return 0.0

        # Quality factors
        coverage_score = len(essential_context) / max(len(all_sources), 1)
        relevance_score = sum(s.relevance_score for s in all_sources if s.name in essential_context) / max(len(essential_context), 1)
        diversity_score = len(set(s.source_type for s in all_sources if s.name in essential_context)) / 3.0  # Max 3 types

        # Weighted combination
        quality = (
            coverage_score * 0.3 +
            relevance_score * 0.5 +
            diversity_score * 0.2
        )

        return min(quality, 1.0)

    def get_context_statistics(self, context: EnhancedContext) -> Dict[str, Any]:
        """Generate statistics about the context gathering process."""
        source_types = {}
        for source_name, source_data in context.full_context.items():
            source_type = source_data.get("type", "unknown")
            source_types[source_type] = source_types.get(source_type, 0) + 1

        return {
            "total_sources": context.total_sources,
            "prioritized_sources": len(context.prioritized_sources),
            "token_budget_used": context.token_budget_used,
            "token_budget_remaining": context.max_token_budget - context.token_budget_used,
            "quality_score": context.quality_score,
            "source_type_breakdown": source_types,
            "context_coverage": len(context.essential_context) / max(context.total_sources, 1)
        }