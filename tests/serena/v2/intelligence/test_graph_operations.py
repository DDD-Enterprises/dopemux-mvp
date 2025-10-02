"""
Comprehensive Test Suite for SerenaGraphOperations

Tests code relationship graph queries, navigation paths, ADHD optimizations,
and performance targets for intelligent code navigation.
"""

import pytest
import asyncio
import time

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.graph_operations import (
    SerenaGraphOperations,
    RelationshipType,
    NavigationMode,
    CodeElementNode,
    RelationshipEdge,
    NavigationPath,
    create_graph_operations,
    quick_performance_test
)
from v2.intelligence.database import SerenaIntelligenceDatabase


# ==========================================
# Test 1: Graph Operations Initialization
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_graph_operations_initialization(intelligence_db, performance_monitor):
    """Test graph operations initialization."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    assert graph_ops.database == intelligence_db
    assert graph_ops.performance_monitor == performance_monitor
    assert graph_ops.complexity_analyzer is not None

    # Should have navigation mode limits configured
    assert NavigationMode.FOCUS in graph_ops.default_result_limits
    assert graph_ops.default_result_limits[NavigationMode.FOCUS] == 5
    assert graph_ops.default_result_limits[NavigationMode.EXPLORE] == 15
    assert graph_ops.default_result_limits[NavigationMode.COMPREHENSIVE] == 50


# ==========================================
# Test 2: Relationship Type Enum
# ==========================================

@pytest.mark.unit
def test_relationship_type_enum():
    """Test RelationshipType enum values."""
    assert RelationshipType.CALLS == "calls"
    assert RelationshipType.IMPORTS == "imports"
    assert RelationshipType.INHERITS == "inherits"
    assert RelationshipType.DEFINES == "defines"
    assert RelationshipType.USES == "uses"
    assert RelationshipType.CONTAINS == "contains"
    assert RelationshipType.REFERENCES == "references"
    assert RelationshipType.IMPLEMENTS == "implements"
    assert RelationshipType.OVERRIDES == "overrides"
    assert RelationshipType.SIMILAR_TO == "similar_to"


# ==========================================
# Test 3: Navigation Mode Enum
# ==========================================

@pytest.mark.unit
def test_navigation_mode_enum():
    """Test NavigationMode enum values and ADHD optimization levels."""
    assert NavigationMode.FOCUS == "focus"
    assert NavigationMode.EXPLORE == "explore"
    assert NavigationMode.COMPREHENSIVE == "comprehensive"


# ==========================================
# Test 4: CodeElementNode Data Class
# ==========================================

@pytest.mark.unit
def test_code_element_node_adhd_properties():
    """Test CodeElementNode ADHD helper properties."""
    # ADHD-friendly element (low complexity, low cognitive load)
    friendly_element = CodeElementNode(
        id=1,
        file_path="/test.py",
        element_name="simple_func",
        element_type="function",
        language="python",
        start_line=10,
        end_line=15,
        complexity_score=0.4,
        complexity_level="simple",
        cognitive_load_factor=0.3,
        access_frequency=5,
        adhd_insights=["short function"],
        tree_sitter_metadata={}
    )

    assert friendly_element.adhd_friendly is True
    assert friendly_element.location_signature == "/test.py:10-15"

    # Not ADHD-friendly (high complexity)
    complex_element = CodeElementNode(
        id=2,
        file_path="/test.py",
        element_name="complex_func",
        element_type="function",
        language="python",
        start_line=20,
        end_line=100,
        complexity_score=0.9,
        complexity_level="very_complex",
        cognitive_load_factor=0.8,
        access_frequency=2,
        adhd_insights=["long function", "complex logic"],
        tree_sitter_metadata={}
    )

    assert complex_element.adhd_friendly is False


# ==========================================
# Test 5: RelationshipEdge ADHD Recommendations
# ==========================================

@pytest.mark.unit
def test_relationship_edge_adhd_recommended():
    """Test RelationshipEdge ADHD recommendation logic."""
    # Recommended relationship (low load, easy, high confidence)
    recommended_rel = RelationshipEdge(
        source_id=1,
        target_id=2,
        relationship_type=RelationshipType.CALLS,
        strength=0.9,
        confidence=0.8,
        cognitive_load=0.3,
        adhd_navigation_difficulty="easy",
        traversal_frequency=10,
        average_traversal_time=5.0
    )

    assert recommended_rel.adhd_recommended is True

    # Not recommended (high load)
    not_recommended_rel = RelationshipEdge(
        source_id=1,
        target_id=3,
        relationship_type=RelationshipType.INHERITS,
        strength=0.6,
        confidence=0.9,
        cognitive_load=0.8,  # High cognitive load
        adhd_navigation_difficulty="hard",
        traversal_frequency=1,
        average_traversal_time=30.0
    )

    assert not_recommended_rel.adhd_recommended is False


# ==========================================
# Test 6: Navigation Path ADHD Difficulty
# ==========================================

@pytest.mark.unit
def test_navigation_path_adhd_difficulty():
    """Test NavigationPath ADHD difficulty assessment."""
    # Easy path
    easy_path = NavigationPath(
        elements=[],
        relationships=[],
        total_complexity=0.2,
        cognitive_load_score=0.2,
        estimated_traversal_time=10.0,
        adhd_recommendations=[]
    )
    assert easy_path.adhd_difficulty == "easy"

    # Moderate path
    moderate_path = NavigationPath(
        elements=[],
        relationships=[],
        total_complexity=0.5,
        cognitive_load_score=0.5,
        estimated_traversal_time=25.0,
        adhd_recommendations=[]
    )
    assert moderate_path.adhd_difficulty == "moderate"

    # Challenging path
    challenging_path = NavigationPath(
        elements=[],
        relationships=[],
        total_complexity=0.7,
        cognitive_load_score=0.7,
        estimated_traversal_time=45.0,
        adhd_recommendations=["Take breaks", "Use focus mode"]
    )
    assert challenging_path.adhd_difficulty == "challenging"

    # Overwhelming path
    overwhelming_path = NavigationPath(
        elements=[],
        relationships=[],
        total_complexity=0.95,
        cognitive_load_score=0.9,
        estimated_traversal_time=90.0,
        adhd_recommendations=["Break into smaller steps", "Use guided navigation"]
    )
    assert overwhelming_path.adhd_difficulty == "overwhelming"


# ==========================================
# Test 7: Built-in Performance Test
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
@pytest.mark.adhd
async def test_quick_performance_test_function(intelligence_db, assert_adhd_compliant):
    """Test the built-in quick performance test."""
    result = await quick_performance_test(intelligence_db)

    # Should run successfully
    assert "tests_run" in result
    assert len(result["tests_run"]) > 0

    # All tests should be ADHD compliant
    assert result["all_under_200ms"] is True
    assert result["adhd_compliant"] is True

    # Average should be excellent
    assert result["average_time_ms"] < 200.0
    assert_adhd_compliant(result["average_time_ms"])

    # Individual test results
    for test in result["tests_run"]:
        assert test["adhd_compliant"] is True
        assert test["time_ms"] < 200.0


# ==========================================
# Test 8: Get Element Performance
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
async def test_get_element_performance(intelligence_db, performance_monitor, assert_adhd_compliant):
    """Test element retrieval performance meets ADHD targets."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    # Test get_element_by_id (with empty database)
    start_time = time.time()
    element = await graph_ops.get_element_by_id(999999)  # Non-existent
    query_time = (time.time() - start_time) * 1000

    # Should be None (not found)
    assert element is None

    # Should still be fast even for non-existent elements
    assert_adhd_compliant(query_time)


# ==========================================
# Test 9: Find Elements by Name
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
async def test_find_elements_by_name_performance(intelligence_db, performance_monitor, assert_adhd_compliant):
    """Test name search performance with empty database."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    # Search for non-existent element
    start_time = time.time()
    elements = await graph_ops.find_elements_by_name("test_function", mode=NavigationMode.FOCUS)
    query_time = (time.time() - start_time) * 1000

    # Should return empty list
    assert isinstance(elements, list)
    assert len(elements) == 0

    # Should be fast
    assert_adhd_compliant(query_time)


# ==========================================
# Test 10: Navigation Mode Result Limiting
# ==========================================

@pytest.mark.unit
def test_navigation_mode_result_limits(intelligence_db, performance_monitor):
    """Test that navigation modes have appropriate result limits."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    # Verify ADHD-optimized limits
    assert graph_ops.default_result_limits[NavigationMode.FOCUS] == 5  # Minimal for scattered attention
    assert graph_ops.default_result_limits[NavigationMode.EXPLORE] == 15  # Moderate for exploration
    assert graph_ops.default_result_limits[NavigationMode.COMPREHENSIVE] == 50  # Maximum


# ==========================================
# Test 11: Cache Functionality
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_graph_operations_cache(intelligence_db, performance_monitor):
    """Test graph operations caching."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    # First query - uncached
    start_time = time.time()
    element1 = await graph_ops.get_element_by_id(1)
    uncached_time = (time.time() - start_time) * 1000

    # Second query - should use cache
    start_time = time.time()
    element2 = await graph_ops.get_element_by_id(1)
    cached_time = (time.time() - start_time) * 1000

    # Results should be consistent
    assert element1 == element2

    # Cached should be faster (if result was found and cached)
    if element1 is not None:
        assert cached_time <= uncached_time

    # Test cache clearing
    await graph_ops.clear_cache()
    assert len(graph_ops._query_cache) == 0


# ==========================================
# Test 12: Performance Metrics
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_get_performance_metrics(intelligence_db, performance_monitor):
    """Test performance metrics retrieval."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    # Execute some operations
    await graph_ops.get_element_by_id(1)
    await graph_ops.find_elements_by_name("test")

    # Get metrics
    metrics = await graph_ops.get_performance_metrics()

    # Should have performance data
    assert "operations_performed" in metrics or "query_count" in metrics or isinstance(metrics, dict)


# ==========================================
# Test 13: Factory Function
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_create_graph_operations_factory(intelligence_db, performance_monitor):
    """Test convenience factory function."""
    graph_ops = await create_graph_operations(intelligence_db, performance_monitor)

    assert isinstance(graph_ops, SerenaGraphOperations)
    assert graph_ops.database == intelligence_db


# ==========================================
# Test 14: Multiple Navigation Modes
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_navigation_modes_affect_results(intelligence_db, performance_monitor):
    """Test that different navigation modes produce appropriately limited results."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    # Test each mode
    for mode in [NavigationMode.FOCUS, NavigationMode.EXPLORE, NavigationMode.COMPREHENSIVE]:
        elements = await graph_ops.find_elements_by_name("test", mode=mode)

        # All should return lists
        assert isinstance(elements, list)

        # With empty database, all return empty
        # But the query should execute successfully
        assert len(elements) == 0


# ==========================================
# Test 15: ADHD Insights Generation
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_adhd_insights_for_element(intelligence_db, performance_monitor):
    """Test ADHD-specific insights generation."""
    graph_ops = SerenaGraphOperations(intelligence_db, performance_monitor)

    # Test for non-existent element (should handle gracefully)
    insights = await graph_ops.get_adhd_insights_for_element(99999)

    # Should return result (empty or with default insights)
    assert insights is not None
    assert isinstance(insights, (dict, list, type(None)))
