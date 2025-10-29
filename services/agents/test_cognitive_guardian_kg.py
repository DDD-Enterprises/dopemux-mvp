#!/usr/bin/env python3
"""
Unit tests for CognitiveGuardianKG
Week 4 Day 1: KG Query Layer Foundation

Tests:
- Initialization (with/without KG)
- Task relationship queries
- Semantic search
- Graceful degradation
- Error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from cognitive_guardian_kg import CognitiveGuardianKG


class TestCognitiveGuardianKGInitialization:
    """Test initialization and configuration."""
    
    def test_initialization_basic_mode(self):
        """Test initialization in basic mode (KG disabled)."""
        kg = CognitiveGuardianKG(workspace_id="/test", enable_kg=False)
        
        assert kg.workspace_id == "/test"
        assert kg.enable_kg == False
        assert kg.age_client is None
        assert kg.attention_monitor is None
    
    def test_initialization_with_workspace(self):
        """Test workspace ID is stored correctly."""
        kg = CognitiveGuardianKG(workspace_id="/user/project", enable_kg=False)
        
        assert kg.workspace_id == "/user/project"
    
    def test_initialization_with_mocked_client(self):
        """Test dependency injection with mocked AGE client."""
        mock_client = Mock()
        kg = CognitiveGuardianKG(
            workspace_id="/test",
            age_client=mock_client,
            enable_kg=True
        )
        
        assert kg.age_client == mock_client
        assert kg.enable_kg == True


class TestTaskRelationshipQueries:
    """Test task relationship queries."""
    
    @pytest.mark.asyncio
    async def test_get_task_relationships_empty_in_basic_mode(self):
        """Test graceful degradation returns empty relationships."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        rels = await kg.get_task_relationships("task-123")
        
        assert rels == {"dependencies": [], "blockers": [], "related": []}
    
    @pytest.mark.asyncio
    async def test_get_task_relationships_with_mocked_data(self):
        """Test parsing of relationship data from AGE."""
        # Mock AGE client
        mock_client = Mock()
        mock_client.execute_cypher = Mock(return_value=[
            {
                "dependencies": ["task-dep-1", "task-dep-2"],
                "blockers": ["task-block-1"],
                "related": ["task-rel-1", "task-rel-2", "task-rel-3"]
            }
        ])
        
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        rels = await kg.get_task_relationships("task-123")
        
        assert len(rels["dependencies"]) == 2
        assert "task-dep-1" in rels["dependencies"]
        assert len(rels["blockers"]) == 1
        assert len(rels["related"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_task_relationships_error_handling(self):
        """Test graceful degradation on query error."""
        # Mock AGE client that raises error
        mock_client = Mock()
        mock_client.execute_cypher = Mock(side_effect=Exception("DB connection failed"))
        
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        rels = await kg.get_task_relationships("task-123")
        
        # Should return empty relationships (graceful degradation)
        assert rels == {"dependencies": [], "blockers": [], "related": []}
    
    @pytest.mark.asyncio
    async def test_get_task_relationships_empty_result(self):
        """Test handling of empty result from AGE."""
        # Mock AGE client returning empty result
        mock_client = Mock()
        mock_client.execute_cypher = Mock(return_value=[])
        
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        rels = await kg.get_task_relationships("nonexistent-task")
        
        assert rels == {"dependencies": [], "blockers": [], "related": []}


class TestSemanticSearch:
    """Test semantic search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_tasks_empty_in_basic_mode(self):
        """Test search returns empty in basic mode."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        results = await kg.search_tasks_semantic("API integration")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_tasks_empty_query(self):
        """Test search with empty query returns empty."""
        mock_client = Mock()
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        
        results = await kg.search_tasks_semantic("")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_tasks_with_results(self):
        """Test search returns and ranks results."""
        # Mock AGE client with search results
        mock_client = Mock()
        mock_client.execute_cypher = Mock(return_value=[
            {
                "task_id": "task-1",
                "title": "Implement REST API endpoint",
                "complexity": 0.7,
                "energy_required": "high"
            },
            {
                "task_id": "task-2",
                "title": "Add API tests",
                "complexity": 0.5,
                "energy_required": "medium"
            }
        ])
        
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        results = await kg.search_tasks_semantic("API integration")
        
        assert len(results) == 2
        assert all("task_id" in r for r in results)
        assert all("title" in r for r in results)
        assert all("relevance" in r for r in results)
        assert all("complexity" in r for r in results)
        
        # Results should be sorted by relevance
        assert results[0]["relevance"] >= results[1]["relevance"]
    
    @pytest.mark.asyncio
    async def test_search_tasks_relevance_calculation(self):
        """Test relevance score calculation."""
        # Mock AGE client
        mock_client = Mock()
        mock_client.execute_cypher = Mock(return_value=[
            {
                "task_id": "task-1",
                "title": "API integration testing",
                "complexity": 0.6,
                "energy_required": "medium"
            }
        ])
        
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        
        # Query: "API integration"
        # Title: "API integration testing"
        # Both keywords match = 2/2 = 1.0 relevance
        results = await kg.search_tasks_semantic("API integration")
        
        assert len(results) == 1
        assert results[0]["relevance"] == 1.0
    
    @pytest.mark.asyncio
    async def test_search_tasks_error_handling(self):
        """Test graceful degradation on search error."""
        # Mock AGE client that raises error
        mock_client = Mock()
        mock_client.execute_cypher = Mock(side_effect=Exception("Search failed"))
        
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        results = await kg.search_tasks_semantic("test query")
        
        # Should return empty list (graceful degradation)
        assert results == []


class TestHelperMethods:
    """Test internal helper methods."""
    
    def test_parse_id_list_with_python_list(self):
        """Test parsing Python list from AGE."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        result = kg._parse_id_list(["task-1", "task-2", "task-3"])
        
        assert result == ["task-1", "task-2", "task-3"]
    
    def test_parse_id_list_with_json_string(self):
        """Test parsing JSON string from AGE."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        result = kg._parse_id_list('["task-1", "task-2"]')
        
        assert result == ["task-1", "task-2"]
    
    def test_parse_id_list_with_empty(self):
        """Test parsing empty/null values."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        assert kg._parse_id_list(None) == []
        assert kg._parse_id_list([]) == []
        assert kg._parse_id_list("") == []
    
    def test_parse_id_list_filters_nones(self):
        """Test that None values are filtered out."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        result = kg._parse_id_list(["task-1", None, "task-2", None])
        
        assert result == ["task-1", "task-2"]


class TestGracefulDegradation:
    """Test graceful degradation behavior."""
    
    @pytest.mark.asyncio
    async def test_all_methods_work_in_basic_mode(self):
        """Test all methods return safe values when KG disabled."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        # Task relationships
        rels = await kg.get_task_relationships("task-123")
        assert rels == {"dependencies": [], "blockers": [], "related": []}
        
        # Semantic search
        results = await kg.search_tasks_semantic("test query")
        assert results == []
    
    def test_close_in_basic_mode(self):
        """Test close() works without AGE client."""
        kg = CognitiveGuardianKG("/test", enable_kg=False)
        
        # Should not raise exception
        kg.close()


class TestSecurityParameterizedQueries:
    """Test that queries use parameterization (injection prevention)."""
    
    @pytest.mark.asyncio
    async def test_task_relationships_uses_parameters(self):
        """Test get_task_relationships uses parameterized query."""
        mock_client = Mock()
        mock_client.execute_cypher = Mock(return_value=[])
        
        kg = CognitiveGuardianKG("/test", age_client=mock_client, enable_kg=True)
        
        # Try injection attempt
        malicious_id = "'; DROP GRAPH; --"
        await kg.get_task_relationships(malicious_id)
        
        # Verify execute_cypher was called with parameters (not string interpolation)
        assert mock_client.execute_cypher.called
        call_args = mock_client.execute_cypher.call_args
        
        # First arg is query (should not contain the malicious string directly)
        query = call_args[0][0]
        assert malicious_id not in query
        
        # Second arg should be parameters tuple
        params = call_args[0][1]
        assert isinstance(params, tuple)
        assert params[0] == malicious_id  # Safely passed as parameter


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
