"""
Test Suite for Query Classification Engine

Validates intelligent query analysis and adaptive research strategy selection
for ADHD-optimized research workflows.
"""

import pytest
import asyncio
from ..engines.query_classifier import (
    QueryClassificationEngine,
    QueryIntent,
    ResearchScope,
    OutputFormat,
    SearchEngineStrategy
)
from ..models.research_task import ResearchType

@pytest.fixture
def classifier():
    """Create query classification engine for testing"""
    return QueryClassificationEngine()

class TestQueryClassification:
    """Test suite for query classification functionality"""

    @pytest.mark.asyncio
    async def test_feature_planning_classification(self, classifier):
        """Test classification of feature planning queries"""
        query = "How do I implement user authentication with OAuth in my React application?"

        result = await classifier.classify_query(query)

        assert result.intent == QueryIntent.FEATURE_PLANNING
        assert result.research_type == ResearchType.FEATURE_RESEARCH
        assert result.output_format == OutputFormat.PRD
        assert result.confidence > 0.7
        assert "implement" in result.keywords_detected
        assert "authentication" in result.keywords_detected

    @pytest.mark.asyncio
    async def test_bug_investigation_classification(self, classifier):
        """Test classification of bug investigation queries"""
        query = "My React app is crashing when users log in. What could be causing this error?"

        result = await classifier.classify_query(query)

        assert result.intent == QueryIntent.BUG_INVESTIGATION
        assert result.research_type == ResearchType.BUG_INVESTIGATION
        assert result.output_format == OutputFormat.RCA
        assert result.confidence > 0.7
        assert "crashing" in result.keywords_detected or "error" in result.keywords_detected

    @pytest.mark.asyncio
    async def test_technology_evaluation_classification(self, classifier):
        """Test classification of technology evaluation queries"""
        query = "Should I use Redux or Context API for state management? What are the pros and cons?"

        result = await classifier.classify_query(query)

        assert result.intent == QueryIntent.TECHNOLOGY_EVALUATION
        assert result.research_type == ResearchType.TECHNOLOGY_EVALUATION
        assert result.output_format == OutputFormat.COMPARISON_MATRIX
        assert result.confidence > 0.7

    @pytest.mark.asyncio
    async def test_architecture_design_classification(self, classifier):
        """Test classification of architecture design queries"""
        query = "Design a microservices architecture for a large-scale e-commerce platform"

        result = await classifier.classify_query(query)

        assert result.intent == QueryIntent.ARCHITECTURE_DESIGN
        assert result.research_type == ResearchType.SYSTEM_ARCHITECTURE
        assert result.output_format == OutputFormat.ADR
        assert result.search_strategy == SearchEngineStrategy.TECHNICAL_DEEP_DIVE

    @pytest.mark.asyncio
    async def test_scope_assessment(self, classifier):
        """Test research scope assessment"""
        # Quick overview
        quick_query = "Quick overview of React hooks"
        quick_result = await classifier.classify_query(quick_query)
        assert quick_result.scope == ResearchScope.QUICK_OVERVIEW
        assert quick_result.estimated_duration_minutes < 15

        # Deep dive
        deep_query = "Comprehensive analysis of microservices patterns for enterprise applications"
        deep_result = await classifier.classify_query(deep_query)
        assert deep_result.scope in [ResearchScope.DEEP_DIVE, ResearchScope.COMPREHENSIVE]
        assert deep_result.estimated_duration_minutes > 20

    @pytest.mark.asyncio
    async def test_adhd_optimization_configuration(self, classifier):
        """Test ADHD-specific configuration generation"""
        # High complexity query
        complex_query = "Enterprise-grade distributed system architecture with multiple microservices"
        result = await classifier.classify_query(complex_query)

        # High complexity should trigger ADHD accommodations
        assert result.adhd_config.max_concurrent_sources <= 5
        assert result.adhd_config.progressive_disclosure == True
        assert result.adhd_config.gentle_notifications == True
        assert result.complexity_score > 0.6

        # Simple query
        simple_query = "Basic React component"
        simple_result = await classifier.classify_query(simple_query)

        # Low complexity allows more sources
        assert simple_result.adhd_config.max_concurrent_sources >= 5
        assert simple_result.complexity_score < 0.6

    @pytest.mark.asyncio
    async def test_search_strategy_selection(self, classifier):
        """Test search engine strategy selection"""
        # Documentation query should prioritize documentation
        doc_query = "How to configure Next.js API routes"
        doc_result = await classifier.classify_query(doc_query)
        assert doc_result.search_strategy == SearchEngineStrategy.DOCUMENTATION_FIRST

        # Technology evaluation should focus on recent developments
        eval_query = "Compare React vs Vue vs Angular in 2024"
        eval_result = await classifier.classify_query(eval_query)
        assert eval_result.search_strategy == SearchEngineStrategy.RECENT_DEVELOPMENTS

    @pytest.mark.asyncio
    async def test_tool_orchestration_planning(self, classifier):
        """Test tool selection for different query types"""
        query = "Implement GraphQL API with authentication and caching"
        result = await classifier.classify_query(query)

        # Should include core tools
        assert "context7" in result.required_tools
        assert len(result.required_tools) >= 2
        assert len(result.optional_tools) >= 1

    @pytest.mark.asyncio
    async def test_user_context_integration(self, classifier):
        """Test user context influence on classification"""
        query = "How to optimize database performance"

        # Without user context
        result1 = await classifier.classify_query(query)

        # With user context indicating expertise level
        user_context = {
            "expertise_level": "beginner",
            "previous_queries": ["basic SQL", "database setup"],
            "preferred_complexity": "low"
        }
        result2 = await classifier.classify_query(query, user_context=user_context)

        # Results should be the same intent but potentially different optimization
        assert result1.intent == result2.intent
        # User context may affect ADHD configuration or scope

    @pytest.mark.asyncio
    async def test_project_context_integration(self, classifier):
        """Test project context influence on classification"""
        query = "Add user authentication"

        project_context = {
            "tech_stack": ["React", "Node.js", "MongoDB"],
            "architecture_patterns": ["microservices", "REST API"],
            "existing_auth": False
        }

        result = await classifier.classify_query(
            query,
            project_context=project_context
        )

        assert result.intent == QueryIntent.FEATURE_PLANNING
        assert result.research_type == ResearchType.FEATURE_RESEARCH

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, classifier):
        """Test confidence scoring for different query types"""
        # Clear, specific query should have high confidence
        clear_query = "Implement JWT authentication in Express.js"
        clear_result = await classifier.classify_query(clear_query)
        assert clear_result.confidence > 0.8

        # Vague query should have lower confidence
        vague_query = "Make it better"
        vague_result = await classifier.classify_query(vague_query)
        assert vague_result.confidence < 0.7

    @pytest.mark.asyncio
    async def test_reasoning_generation(self, classifier):
        """Test reasoning explanation generation"""
        query = "Debug memory leak in React application"
        result = await classifier.classify_query(query)

        assert result.reasoning is not None
        assert len(result.reasoning) > 20
        assert "bug" in result.reasoning.lower() or "debug" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_duration_estimation(self, classifier):
        """Test research duration estimation"""
        # Quick task
        quick_query = "React useState hook example"
        quick_result = await classifier.classify_query(quick_query)
        assert quick_result.estimated_duration_minutes < 20

        # Complex task
        complex_query = "Complete microservices security audit with OWASP compliance"
        complex_result = await classifier.classify_query(complex_query)
        assert complex_result.estimated_duration_minutes > 30

    @pytest.mark.asyncio
    async def test_keyword_extraction(self, classifier):
        """Test keyword extraction functionality"""
        query = "Implement secure user authentication with JWT tokens and refresh functionality"
        result = await classifier.classify_query(query)

        expected_keywords = ["implement", "secure", "user", "authentication", "jwt", "tokens", "refresh", "functionality"]
        detected_keywords = [kw.lower() for kw in result.keywords_detected]

        # Should detect at least some important keywords
        keyword_overlap = set(expected_keywords) & set(detected_keywords)
        assert len(keyword_overlap) >= 3

class TestAdHDOptimizations:
    """Test ADHD-specific optimization features"""

    @pytest.mark.asyncio
    async def test_progressive_disclosure_configuration(self, classifier):
        """Test progressive disclosure settings"""
        # Complex query should enable progressive disclosure
        complex_query = "Enterprise microservices architecture with service mesh"
        result = await classifier.classify_query(complex_query)
        assert result.adhd_config.progressive_disclosure == True

    @pytest.mark.asyncio
    async def test_source_limiting(self, classifier):
        """Test source limiting for cognitive load management"""
        query = "Comprehensive analysis of cloud platforms"
        result = await classifier.classify_query(query)

        # Should limit sources to manageable number
        assert result.adhd_config.max_concurrent_sources <= 7
        assert result.adhd_config.max_concurrent_sources >= 3

    @pytest.mark.asyncio
    async def test_work_duration_adaptation(self, classifier):
        """Test work duration adaptation based on scope"""
        # Quick task should have shorter work periods
        quick_query = "Simple React component example"
        quick_result = await classifier.classify_query(quick_query)
        assert quick_result.adhd_config.work_duration_minutes <= 25

        # Complex task should have longer work periods
        complex_query = "Complete system architecture for distributed application"
        complex_result = await classifier.classify_query(complex_query)
        assert complex_result.adhd_config.work_duration_minutes >= 25

if __name__ == "__main__":
    # Run basic functionality test
    async def test_basic_functionality():
        """Basic test to validate system works"""
        classifier = QueryClassificationEngine()
        result = await classifier.classify_query("How to implement user authentication?")

        print(f"Intent: {result.intent}")
        print(f"Research Type: {result.research_type}")
        print(f"Scope: {result.scope}")
        print(f"Complexity: {result.complexity_score:.2f}")
        print(f"Duration: {result.estimated_duration_minutes} minutes")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
        print(f"ADHD Config: max_sources={result.adhd_config.max_concurrent_sources}, work_duration={result.adhd_config.work_duration_minutes}")

        assert result.intent is not None
        assert result.confidence > 0.5
        print("\n✅ Query classification system working correctly!")

    asyncio.run(test_basic_functionality())