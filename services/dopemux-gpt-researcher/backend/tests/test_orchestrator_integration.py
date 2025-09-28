"""
Integration tests for ResearchTaskOrchestrator with SearchOrchestrator

Tests the complete integration between query classification, search orchestration,
and ADHD-optimized research workflows.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from ..models.research_task import (
    ResearchType,
    ADHDConfiguration,
    ProjectContext
)
from ..services.orchestrator import ResearchTaskOrchestrator
from ..engines.search.base_adapter import SearchResult, SearchResultType, SourceQuality, SearchMetadata


class TestOrchestatorIntegration:
    """Test suite for integrated orchestrator functionality"""

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator with mock adapters for testing"""

        # Mock project context
        project_context = ProjectContext(
            tech_stack=["Python", "FastAPI", "React"],
            architecture_patterns=["microservices", "event-driven"],
            current_focus="research-integration"
        )

        # Create orchestrator without real API keys (will use mock adapter)
        orchestrator = ResearchTaskOrchestrator(
            project_context=project_context,
            search_api_keys={}  # No keys = mock adapter
        )

        return orchestrator

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results for testing"""
        return [
            SearchResult(
                title="Advanced Search Integration Patterns",
                url="https://example.com/search-patterns",
                content="Comprehensive guide to integrating multiple search engines with intelligent orchestration...",
                summary="Guide covers multi-engine search patterns and orchestration strategies",
                relevance_score=0.92,
                result_type=SearchResultType.DOCUMENTATION,
                source_quality=SourceQuality.EXCELLENT,
                reading_time_minutes=5,
                complexity_level="medium",
                key_points=[
                    "Use strategy pattern for engine selection",
                    "Implement result deduplication",
                    "Apply ADHD-friendly result formatting"
                ]
            ),
            SearchResult(
                title="ADHD-Optimized Research Workflows",
                url="https://example.com/adhd-research",
                content="Research methodology specifically designed for ADHD developers focusing on cognitive load management...",
                summary="Methodology for managing cognitive load during research tasks",
                relevance_score=0.88,
                result_type=SearchResultType.BLOG_POST,
                source_quality=SourceQuality.GOOD,
                reading_time_minutes=3,
                complexity_level="low",
                key_points=[
                    "Progressive disclosure reduces overwhelm",
                    "Pomodoro timing maintains focus",
                    "Visual progress indicators improve motivation"
                ]
            )
        ]

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes with all components"""

        # Verify core components are present
        assert orchestrator.query_classifier is not None
        assert orchestrator.search_orchestrator is not None
        assert orchestrator.active_tasks == {}
        assert orchestrator.auto_save_tasks == {}

        # Verify search orchestrator has at least one engine (mock in this case)
        assert len(orchestrator.search_orchestrator.engines) >= 1

    @pytest.mark.asyncio
    async def test_research_task_creation_and_classification(self, orchestrator):
        """Test complete task creation with query classification"""

        # Test various query types to verify classification
        test_queries = [
            ("How to implement microservices architecture", "documentation_research"),
            ("Debug React rendering performance issues", "bug_investigation"),
            ("Compare FastAPI vs Django for our API", "technology_evaluation"),
            ("Design event-driven system architecture", "architecture_design")
        ]

        for query, expected_intent_type in test_queries:
            task = await orchestrator.create_research_task(
                user_id="test_user",
                prompt=query
            )

            # Verify task creation
            assert task.id in orchestrator.active_tasks
            assert task.initial_prompt == query
            assert task.metadata is not None

            # Verify classification occurred
            classification = task.metadata.get('classification', {})
            assert 'intent' in classification
            assert 'search_strategy' in task.metadata
            assert 'estimated_duration_minutes' in task.metadata

    @pytest.mark.asyncio
    async def test_research_plan_generation(self, orchestrator):
        """Test research plan generation with enhanced prompts"""

        # Create test task
        task = await orchestrator.create_research_task(
            user_id="test_user",
            prompt="How to integrate multiple search engines with ADHD optimizations"
        )

        # Generate research plan
        questions = await orchestrator.generate_research_plan(task.id)

        # Verify plan structure
        assert len(questions) > 0
        assert all(q.question for q in questions)
        assert all(q.priority > 0 for q in questions)
        assert all(q.estimated_duration_minutes > 0 for q in questions)

        # Verify task state updated
        retrieved_task = orchestrator.active_tasks[task.id]
        assert len(retrieved_task.research_plan) == len(questions)
        assert retrieved_task.enhanced_prompt is not None

    @pytest.mark.asyncio
    async def test_search_orchestrator_integration(self, orchestrator, mock_search_results):
        """Test integration with SearchOrchestrator"""

        # Mock the search orchestrator's search method
        mock_metadata = SearchMetadata(
            engine_name="orchestrator",
            query_time_ms=150,
            total_results=2,
            results_returned=2,
            search_strategy="comprehensive"
        )

        with patch.object(orchestrator.search_orchestrator, 'search',
                         return_value=(mock_search_results, mock_metadata)) as mock_search:

            # Create and execute research task
            task = await orchestrator.create_research_task(
                user_id="test_user",
                prompt="How to implement search engine integration"
            )

            questions = await orchestrator.generate_research_plan(task.id)
            result = await orchestrator.execute_research_step(task.id, 0)

            # Verify search was called with correct parameters
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert 'query' in call_args.kwargs
            assert 'strategy' in call_args.kwargs
            assert 'adhd_mode' in call_args.kwargs

            # Verify result structure
            assert result is not None
            assert len(result.sources) > 0
            assert result.confidence > 0
            assert len(result.search_engines_used) > 0

            # Verify ADHD optimizations applied
            for source in result.sources:
                assert 'complexity_level' in source
                assert 'reading_time_minutes' in source
                assert len(source.get('key_points', [])) <= 3  # ADHD limit
                if source.get('content'):
                    assert len(source['content']) <= 500  # Content truncation

    @pytest.mark.asyncio
    async def test_strategy_mapping(self, orchestrator, mock_search_results):
        """Test that query classification strategies map correctly to search strategies"""

        strategy_test_cases = [
            ("How to use FastAPI documentation", "documentation_first"),
            ("Latest React 2024 updates", "recent_developments"),
            ("Debug complex microservices architecture", "technical_deep_dive"),
            ("General information about Python", "balanced_approach")
        ]

        mock_metadata = SearchMetadata(
            engine_name="test",
            query_time_ms=100,
            total_results=1,
            results_returned=1
        )

        for query, expected_strategy in strategy_test_cases:
            with patch.object(orchestrator.search_orchestrator, 'search',
                             return_value=(mock_search_results[:1], mock_metadata)) as mock_search:

                # Create task and execute research
                task = await orchestrator.create_research_task(
                    user_id="test_user",
                    prompt=query
                )

                questions = await orchestrator.generate_research_plan(task.id)
                await orchestrator.execute_research_step(task.id, 0)

                # Verify correct strategy was used
                call_args = mock_search.call_args
                strategy_used = call_args.kwargs.get('strategy')

                # Strategy mapping verification
                expected_search_strategy = {
                    'documentation_first': 'documentation_first',
                    'recent_developments': 'recent_developments',
                    'technical_deep_dive': 'technical_deep_dive',
                    'balanced_approach': 'comprehensive'
                }.get(expected_strategy, 'comprehensive')

                assert strategy_used.value == expected_search_strategy

    @pytest.mark.asyncio
    async def test_adhd_configuration_application(self, orchestrator):
        """Test that ADHD configurations are properly applied throughout the workflow"""

        # Create task with specific ADHD configuration
        custom_adhd_config = ADHDConfiguration(
            work_duration_minutes=15,
            max_concurrent_sources=3,
            progressive_disclosure=True,
            gentle_notifications=True,
            auto_save_interval_seconds=60
        )

        task = await orchestrator.create_research_task(
            user_id="test_user",
            prompt="Research task with custom ADHD settings",
            adhd_config=custom_adhd_config
        )

        # Verify ADHD config applied
        assert task.adhd_config.max_concurrent_sources == 3
        assert task.adhd_config.progressive_disclosure == True
        assert task.adhd_config.work_duration_minutes == 15

        # Generate plan and verify ADHD considerations
        questions = await orchestrator.generate_research_plan(task.id)

        # Verify work segmentation (questions should fit work duration)
        total_estimated_time = sum(q.estimated_duration_minutes for q in questions)
        assert total_estimated_time <= task.adhd_config.work_duration_minutes * 2  # Allow some flexibility

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self, orchestrator):
        """Test comprehensive error handling with fallbacks"""

        # Mock search orchestrator to raise exception
        with patch.object(orchestrator.search_orchestrator, 'search',
                         side_effect=Exception("Search service unavailable")) as mock_search:

            # Create task and attempt execution
            task = await orchestrator.create_research_task(
                user_id="test_user",
                prompt="Test error handling"
            )

            questions = await orchestrator.generate_research_plan(task.id)
            result = await orchestrator.execute_research_step(task.id, 0)

            # Verify graceful error handling
            assert result is not None
            assert "temporarily unavailable" in result.answer.lower()
            assert result.confidence < 0.2  # Low confidence for error case
            assert "error_fallback" in result.search_engines_used

    @pytest.mark.asyncio
    async def test_complete_research_workflow(self, orchestrator, mock_search_results):
        """Test complete end-to-end research workflow"""

        mock_metadata = SearchMetadata(
            engine_name="integrated_test",
            query_time_ms=200,
            total_results=2,
            results_returned=2,
            search_strategy="comprehensive"
        )

        with patch.object(orchestrator.search_orchestrator, 'search',
                         return_value=(mock_search_results, mock_metadata)):

            # Complete workflow test
            task = await orchestrator.create_research_task(
                user_id="test_user",
                prompt="Complete workflow test for search integration"
            )

            # Generate plan
            questions = await orchestrator.generate_research_plan(task.id)
            assert len(questions) > 0

            # Execute all research steps
            for i in range(len(questions)):
                result = await orchestrator.execute_research_step(task.id, i)
                assert result is not None
                assert result.confidence > 0

            # Complete research
            completed_task = await orchestrator.complete_research(task.id)

            # Verify completion
            assert completed_task.status.value == "completed"
            assert len(completed_task.results) == len(questions)
            assert completed_task.confidence_score > 0
            assert completed_task.sources_discovered > 0


# Run basic validation if executed directly
if __name__ == "__main__":
    async def run_basic_test():
        """Run a basic integration test"""
        orchestrator = ResearchTaskOrchestrator(search_api_keys={})

        print("Testing orchestrator initialization...")
        assert orchestrator.search_orchestrator is not None
        print("✅ Orchestrator initialized successfully")

        print("Testing task creation...")
        task = await orchestrator.create_research_task(
            user_id="test",
            prompt="Test integration between SearchOrchestrator and ResearchTaskOrchestrator"
        )
        assert task.id in orchestrator.active_tasks
        print("✅ Task creation successful")

        print("Testing plan generation...")
        questions = await orchestrator.generate_research_plan(task.id)
        assert len(questions) > 0
        print(f"✅ Generated {len(questions)} research questions")

        print("🎉 Basic integration test passed!")

    # Run the test
    asyncio.run(run_basic_test())