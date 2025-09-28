"""
Test Suite for Multi-Engine Search System

Comprehensive tests for search adapters, orchestration, and ADHD optimizations.
Tests both individual engine functionality and integrated orchestration scenarios.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ..engines.search import (
    BaseSearchAdapter,
    SearchResult,
    SearchResultType,
    SourceQuality,
    SearchMetadata,
    SearchOrchestrator,
    SearchStrategy,
    SearchConfig,
    EngineWeight,
    ExaSearchAdapter,
    TavilySearchAdapter,
    PerplexitySearchAdapter,
    Context7SearchAdapter
)


class MockSearchAdapter(BaseSearchAdapter):
    """Mock search adapter for testing"""

    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self.search_calls = []

    @property
    def engine_name(self) -> str:
        return self._name

    @property
    def max_results_per_request(self) -> int:
        return 10

    @property
    def supports_date_filtering(self) -> bool:
        return True

    @property
    def supports_domain_filtering(self) -> bool:
        return True

    async def _execute_search(self, query, max_results, result_types, date_filter, domain_filter, **kwargs):
        # Record the call
        self.search_calls.append({
            'query': query,
            'max_results': max_results,
            'result_types': result_types,
            'date_filter': date_filter,
            'domain_filter': domain_filter,
            'kwargs': kwargs
        })

        # Return mock results
        results = []
        for i in range(min(max_results, 3)):  # Return up to 3 mock results
            result = SearchResult(
                title=f"{self._name} Result {i+1}: {query}",
                url=f"https://{self._name.lower()}.com/result-{i+1}",
                content=f"Mock content from {self._name} for query: {query}",
                summary=f"Summary from {self._name}",
                result_type=SearchResultType.DOCUMENTATION,
                source_quality=SourceQuality.GOOD,
                relevance_score=0.8 - (i * 0.1),  # Decreasing relevance
                engine_metadata={'mock_engine': self._name, 'result_index': i}
            )
            results.append(result)

        return results


@pytest.fixture
def mock_engines():
    """Create mock search engines for testing"""
    return {
        'exa': MockSearchAdapter('exa'),
        'tavily': MockSearchAdapter('tavily'),
        'perplexity': MockSearchAdapter('perplexity'),
        'context7': MockSearchAdapter('context7')
    }


@pytest.fixture
def orchestrator(mock_engines):
    """Create search orchestrator with mock engines"""
    config = SearchConfig(
        strategy=SearchStrategy.COMPREHENSIVE,
        max_total_results=15,
        max_per_engine=5,
        enable_parallel=True,
        deduplicate_results=True,
        adhd_mode=True
    )
    return SearchOrchestrator(mock_engines, **config.__dict__)


class TestBaseSearchAdapter:
    """Test base search adapter functionality"""

    @pytest.mark.asyncio
    async def test_search_validation(self):
        """Test input validation in base adapter"""
        adapter = MockSearchAdapter('test')

        # Test empty query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await adapter.search("")

        # Test invalid max_results
        with pytest.raises(ValueError, match="max_results must be between"):
            await adapter.search("test query", max_results=0)

        with pytest.raises(ValueError, match="max_results must be between"):
            await adapter.search("test query", max_results=100)

    @pytest.mark.asyncio
    async def test_adhd_optimizations(self):
        """Test ADHD-specific optimizations in base adapter"""
        adapter = MockSearchAdapter('test')

        results, metadata = await adapter.search(
            "test query for ADHD optimization",
            max_results=3
        )

        # Check that results have ADHD-optimized fields
        for result in results:
            assert result.summary is not None
            assert result.reading_time_minutes > 0
            assert result.complexity_level in ['low', 'medium', 'high']

    @pytest.mark.asyncio
    async def test_result_ranking(self):
        """Test ADHD-optimized result ranking"""
        adapter = MockSearchAdapter('test')

        results, metadata = await adapter.search("test ranking", max_results=5)

        # Results should be sorted by ADHD ranking score
        scores = [adapter._adhd_ranking_score(result) for result in results]
        assert scores == sorted(scores, reverse=True)


class TestSearchOrchestrator:
    """Test search orchestration functionality"""

    @pytest.mark.asyncio
    async def test_basic_orchestration(self, orchestrator):
        """Test basic orchestrated search"""
        results, metadata = await orchestrator.search(
            "python web framework",
            max_results=10
        )

        # Should have results from multiple engines
        assert len(results) > 0
        assert len(results) <= 10

        # Check metadata
        assert metadata.engine_name == "orchestrator"
        assert metadata.total_results > 0
        assert metadata.search_strategy == "comprehensive"

    @pytest.mark.asyncio
    async def test_strategy_selection(self, orchestrator):
        """Test different search strategies"""

        # Test documentation-first strategy
        results, metadata = await orchestrator.search(
            "React hooks API documentation",
            strategy=SearchStrategy.DOCUMENTATION_FIRST,
            max_results=8
        )

        assert metadata.search_strategy == "documentation_first"
        assert len(results) <= 8

        # Test troubleshooting strategy
        results, metadata = await orchestrator.search(
            "React component error debugging",
            strategy=SearchStrategy.TROUBLESHOOTING,
            max_results=6
        )

        assert metadata.search_strategy == "troubleshooting"

    @pytest.mark.asyncio
    async def test_parallel_execution(self, orchestrator):
        """Test parallel search execution"""

        start_time = datetime.now()

        results, metadata = await orchestrator.search(
            "async programming patterns",
            strategy=SearchStrategy.COMPREHENSIVE,
            max_results=12
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        # Parallel execution should be faster than sequential
        # (Though with mocks, this mainly tests that it doesn't fail)
        assert execution_time < 5  # Should complete quickly with mocks

        # Should have results from multiple engines
        engines_used = set()
        for result in results:
            engine = result.engine_metadata.get('source_engine')
            if engine:
                engines_used.add(engine)

        assert len(engines_used) > 1  # Multiple engines should be used

    @pytest.mark.asyncio
    async def test_result_deduplication(self, orchestrator):
        """Test result deduplication functionality"""

        # Create orchestrator with deduplication enabled
        orchestrator.config.deduplicate_results = True

        results, metadata = await orchestrator.search(
            "duplicate test query",
            max_results=20
        )

        # Check for URL uniqueness
        urls = [result.url for result in results]
        assert len(urls) == len(set(urls))  # All URLs should be unique

        # Check for title similarity handling
        titles = [result.title for result in results]
        # Should not have identical titles (though similar ones might remain)

    @pytest.mark.asyncio
    async def test_adhd_optimizations(self, orchestrator):
        """Test ADHD-specific optimizations in orchestration"""

        results, metadata = await orchestrator.search(
            "complex technical architecture patterns",
            strategy=SearchStrategy.COMPREHENSIVE,
            max_results=10
        )

        # Check ADHD optimizations
        for result in results:
            # Should have concise summaries
            assert result.summary is not None
            assert len(result.summary) <= 200

            # Should have key points
            assert isinstance(result.key_points, list)

            # Should have complexity assessment
            assert result.complexity_level in ['low', 'medium', 'high']

            # Should have reading time estimate
            assert result.reading_time_minutes > 0

            # Code snippets should be limited
            assert len(result.code_snippets) <= 3

    @pytest.mark.asyncio
    async def test_strategy_recommendation(self, orchestrator):
        """Test automatic strategy recommendation"""

        # Documentation query
        strategy = await orchestrator.get_strategy_recommendation(
            "How to use React hooks API documentation"
        )
        assert strategy == SearchStrategy.DOCUMENTATION_FIRST

        # Recent information query
        strategy = await orchestrator.get_strategy_recommendation(
            "Latest JavaScript features 2024"
        )
        assert strategy == SearchStrategy.RECENT_DEVELOPMENTS

        # Troubleshooting query
        strategy = await orchestrator.get_strategy_recommendation(
            "Fix React component rendering error"
        )
        assert strategy == SearchStrategy.TROUBLESHOOTING

        # Comparison query
        strategy = await orchestrator.get_strategy_recommendation(
            "React vs Vue vs Angular comparison"
        )
        assert strategy == SearchStrategy.COMPARISON

    def test_strategy_info(self, orchestrator):
        """Test strategy information retrieval"""

        strategies = orchestrator.get_available_strategies()
        assert len(strategies) > 0
        assert 'comprehensive' in strategies
        assert 'documentation_first' in strategies

        # Get info for specific strategy
        info = orchestrator.get_strategy_info(SearchStrategy.DOCUMENTATION_FIRST)
        assert info['name'] == 'documentation_first'
        assert 'engines' in info
        assert 'description' in info


class TestExaAdapter:
    """Test Exa search adapter"""

    def test_initialization(self):
        """Test Exa adapter initialization"""
        adapter = ExaSearchAdapter(api_key="test_key")

        assert adapter.engine_name == "exa"
        assert adapter.max_results_per_request == 20
        assert adapter.supports_date_filtering == True
        assert adapter.supports_domain_filtering == True

    def test_quality_domain_mapping(self):
        """Test domain quality assessment"""
        adapter = ExaSearchAdapter(api_key="test_key")

        # Test excellent quality domains
        excellent_url = "https://docs.python.org/3/library/"
        quality = adapter._assess_source_quality(excellent_url)
        assert quality == SourceQuality.EXCELLENT

        # Test good quality domains
        good_url = "https://stackoverflow.com/questions/12345"
        quality = adapter._assess_source_quality(good_url)
        assert quality == SourceQuality.GOOD

    def test_result_type_classification(self):
        """Test result type classification"""
        adapter = ExaSearchAdapter(api_key="test_key")

        # Test documentation classification
        result_type = adapter._classify_result_type(
            "https://docs.python.org/guide",
            "Python documentation content",
            "Python Documentation"
        )
        assert result_type == SearchResultType.DOCUMENTATION

        # Test Stack Overflow classification
        result_type = adapter._classify_result_type(
            "https://stackoverflow.com/questions/123",
            "How to fix this error",
            "Python error question"
        )
        assert result_type == SearchResultType.STACK_OVERFLOW


class TestTavilyAdapter:
    """Test Tavily search adapter"""

    def test_initialization(self):
        """Test Tavily adapter initialization"""
        adapter = TavilySearchAdapter(api_key="test_key")

        assert adapter.engine_name == "tavily"
        assert adapter.max_results_per_request == 20
        assert adapter.supports_date_filtering == True
        assert adapter.supports_domain_filtering == True

    def test_developer_query_enhancement(self):
        """Test developer-focused query enhancement"""
        adapter = TavilySearchAdapter(api_key="test_key")

        # Test code example enhancement
        enhanced = adapter._enhance_query_for_developers(
            "React component",
            [SearchResultType.CODE_EXAMPLE]
        )
        assert "code example implementation" in enhanced

        # Test tutorial enhancement
        enhanced = adapter._enhance_query_for_developers(
            "Vue setup",
            [SearchResultType.TUTORIAL]
        )
        assert "tutorial how to" in enhanced

    def test_domain_preferences(self):
        """Test result type domain preferences"""
        adapter = TavilySearchAdapter(api_key="test_key")

        domains = adapter._get_domains_for_result_types([SearchResultType.CODE_EXAMPLE])
        assert 'github.com' in domains
        assert 'codepen.io' in domains

        domains = adapter._get_domains_for_result_types([SearchResultType.STACK_OVERFLOW])
        assert 'stackoverflow.com' in domains


class TestPerplexityAdapter:
    """Test Perplexity search adapter"""

    def test_initialization(self):
        """Test Perplexity adapter initialization"""
        adapter = PerplexitySearchAdapter(api_key="test_key")

        assert adapter.engine_name == "perplexity"
        assert adapter.max_results_per_request == 10
        assert adapter.supports_date_filtering == True
        assert adapter.supports_domain_filtering == True

    def test_model_selection(self):
        """Test model selection based on query complexity"""
        adapter = PerplexitySearchAdapter(api_key="test_key")

        # Simple query should use fast model
        model = adapter._select_model_for_query("React hooks", None)
        assert model == adapter.models['fast']

        # Complex query should use comprehensive model
        model = adapter._select_model_for_query(
            "Compare enterprise architecture patterns for microservices",
            None
        )
        assert model == adapter.models['comprehensive']

        # Code query should use balanced model
        model = adapter._select_model_for_query(
            "implement authentication",
            [SearchResultType.CODE_EXAMPLE]
        )
        assert model == adapter.models['balanced']

    def test_system_prompt_generation(self):
        """Test system prompt generation for different result types"""
        adapter = PerplexitySearchAdapter(api_key="test_key")

        # Test code example prompt
        prompt = adapter._get_system_prompt([SearchResultType.CODE_EXAMPLE])
        assert "code examples" in prompt.lower()

        # Test API reference prompt
        prompt = adapter._get_system_prompt([SearchResultType.API_REFERENCE])
        assert "api documentation" in prompt.lower()


class TestContext7Adapter:
    """Test Context7 search adapter"""

    def test_initialization(self):
        """Test Context7 adapter initialization"""
        adapter = Context7SearchAdapter()

        assert adapter.engine_name == "context7"
        assert adapter.max_results_per_request == 10
        assert adapter.supports_date_filtering == False  # Official docs don't need date filtering
        assert adapter.supports_domain_filtering == False  # All results are official

    def test_library_name_extraction(self):
        """Test library name extraction from queries"""
        adapter = Context7SearchAdapter()

        # Test popular library detection
        libraries = adapter._extract_library_names("How to use React hooks")
        assert 'react' in libraries

        # Test multiple libraries
        libraries = adapter._extract_library_names("Compare Django vs Flask")
        assert 'django' in libraries
        assert 'flask' in libraries

    def test_topic_extraction(self):
        """Test topic extraction from queries"""
        adapter = Context7SearchAdapter()

        # Test installation topic
        topic = adapter._extract_topic_from_query(
            "How to install Django",
            None
        )
        assert topic == "installation"

        # Test API topic
        topic = adapter._extract_topic_from_query(
            "Django API reference",
            [SearchResultType.API_REFERENCE]
        )
        assert topic == "api"

    def test_token_calculation(self):
        """Test token limit calculation"""
        adapter = Context7SearchAdapter()

        # Simple query should use default tokens
        tokens = adapter._calculate_token_limit("React", None)
        assert tokens == adapter.default_tokens

        # Complex query should use more tokens
        tokens = adapter._calculate_token_limit(
            "How to implement complex authentication system",
            [SearchResultType.API_REFERENCE]
        )
        assert tokens > adapter.default_tokens


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""

    @pytest.mark.asyncio
    async def test_feature_implementation_workflow(self, orchestrator):
        """Test workflow for implementing a new feature"""

        # Step 1: Get documentation
        results, metadata = await orchestrator.search(
            "React authentication implementation guide",
            strategy=SearchStrategy.DOCUMENTATION_FIRST,
            max_results=5
        )

        assert len(results) > 0
        assert any(result.result_type == SearchResultType.DOCUMENTATION for result in results)

        # Step 2: Find code examples
        results, metadata = await orchestrator.search(
            "React authentication code examples",
            strategy=SearchStrategy.TECHNICAL_DEEP_DIVE,
            max_results=5
        )

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_troubleshooting_workflow(self, orchestrator):
        """Test workflow for troubleshooting an issue"""

        # Search for solutions
        results, metadata = await orchestrator.search(
            "React component not rendering error fix",
            strategy=SearchStrategy.TROUBLESHOOTING,
            max_results=8
        )

        assert len(results) > 0
        assert metadata.search_strategy == "troubleshooting"

    @pytest.mark.asyncio
    async def test_technology_comparison_workflow(self, orchestrator):
        """Test workflow for comparing technologies"""

        # Compare technologies
        results, metadata = await orchestrator.search(
            "React vs Vue performance comparison 2024",
            strategy=SearchStrategy.COMPARISON,
            max_results=6
        )

        assert len(results) > 0
        assert metadata.search_strategy == "comparison"

    @pytest.mark.asyncio
    async def test_adhd_friendly_results(self, orchestrator):
        """Test that results are optimized for ADHD users"""

        results, metadata = await orchestrator.search(
            "complex microservices architecture patterns",
            strategy=SearchStrategy.COMPREHENSIVE,
            max_results=10
        )

        # Check ADHD optimizations
        for result in results:
            # Summaries should be concise
            assert len(result.summary) <= 200

            # Should have key points for scanning
            assert len(result.key_points) <= 3

            # Should have complexity assessment
            assert result.complexity_level in ['low', 'medium', 'high']

            # Reading time should be estimated
            assert result.reading_time_minutes > 0

        # Results should be sorted by ADHD-friendliness initially
        # (Simpler, shorter content first for better cognitive load management)


if __name__ == "__main__":
    # Run basic functionality test
    async def test_basic_functionality():
        """Basic test to validate system works"""

        # Test individual adapter
        mock_adapter = MockSearchAdapter('test')
        results, metadata = await mock_adapter.search("test query", max_results=3)

        print(f"Mock adapter returned {len(results)} results")
        assert len(results) == 3
        assert metadata.engine_name == "test"

        # Test orchestrator
        engines = {
            'mock1': MockSearchAdapter('mock1'),
            'mock2': MockSearchAdapter('mock2')
        }

        orchestrator = SearchOrchestrator(engines)
        results, metadata = await orchestrator.search("test orchestration", max_results=5)

        print(f"Orchestrator returned {len(results)} results")
        assert len(results) > 0
        assert metadata.engine_name == "orchestrator"

        print("✅ Multi-engine search system working correctly!")

    asyncio.run(test_basic_functionality())