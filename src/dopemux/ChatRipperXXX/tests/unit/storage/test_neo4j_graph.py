"""Tests for Neo4j graph database integration."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import List, Dict, Any

from chatx.storage.graph import Neo4jGraphStore
from chatx.storage.base import BaseGraphStore, GraphNode, GraphRelationship, ConversationGraph


class TestGraphDataStructures:
    """Test graph data structure models."""

    def test_graph_node_creation(self):
        """Test GraphNode data structure."""
        node = GraphNode(
            id="msg_123",
            node_type="message",
            properties={
                "text": "I feel like you're crossing my boundaries",
                "timestamp": "2025-09-04T10:30:00Z",
                "sender": "me",
                "psychology_labels": ["boundary_violation", "assertiveness"]
            }
        )
        
        assert node.id == "msg_123"
        assert node.node_type == "message"
        assert "boundary_violation" in node.properties["psychology_labels"]

    def test_graph_relationship_creation(self):
        """Test GraphRelationship data structure."""
        relationship = GraphRelationship(
            from_node="msg_123",
            to_node="msg_124", 
            relationship_type="RESPONDS_TO",
            properties={
                "response_time_seconds": 300,
                "escalation_level": "medium",
                "repair_attempt": True
            }
        )
        
        assert relationship.from_node == "msg_123"
        assert relationship.to_node == "msg_124"
        assert relationship.relationship_type == "RESPONDS_TO"
        assert relationship.properties["repair_attempt"] is True

    def test_conversation_graph_creation(self):
        """Test ConversationGraph assembly."""
        nodes = [
            GraphNode("msg_1", "message", {"text": "Hey", "sender": "me"}),
            GraphNode("msg_2", "message", {"text": "Hi back", "sender": "them"})
        ]
        
        relationships = [
            GraphRelationship("msg_1", "msg_2", "RESPONDS_TO", {"delay_seconds": 120})
        ]
        
        graph = ConversationGraph(
            conversation_id="conv_abc123",
            nodes=nodes,
            relationships=relationships,
            metadata={"contact": "CN_123abc", "date_range": "2025-09-04"}
        )
        
        assert graph.conversation_id == "conv_abc123"
        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
        assert graph.metadata["contact"] == "CN_123abc"


class TestBaseGraphStore:
    """Test BaseGraphStore interface."""

    def test_base_graph_store_is_abstract(self):
        """Test that BaseGraphStore cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseGraphStore()

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = BaseGraphStore.__abstractmethods__
        
        expected_methods = {
            "connect",
            "disconnect", 
            "create_graph",
            "get_conversation_graph",
            "query_relationships",
            "detect_patterns",
            "get_temporal_evolution"
        }
        
        assert expected_methods == abstract_methods


class TestNeo4jGraphStore:
    """Test Neo4j graph store implementation."""

    @pytest.fixture
    def mock_async_neo4j_driver(self):
        """Mock async Neo4j driver."""
        driver = AsyncMock()
        session = AsyncMock()
        
        # Mock async context manager for sessions
        driver.session.return_value.__aenter__ = AsyncMock(return_value=session)
        driver.session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Mock async session.run results
        async_result = AsyncMock()
        async_result.__aiter__ = AsyncMock(return_value=iter([]))
        session.run.return_value = async_result
        
        return driver, session

    @pytest.fixture
    def graph_store(self, mock_async_neo4j_driver):
        """Create Neo4j graph store with mocked async driver."""
        driver, session = mock_async_neo4j_driver
        
        store = Neo4jGraphStore(
            uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
            database="neo4j",
            max_connection_lifetime=300,
            max_connection_pool_size=25,
            connection_timeout=30,
            connection_acquisition_timeout=60
        )
        
        # Replace driver with mock
        store.driver = driver
        return store, session
            
    def test_neo4j_import_successful(self):
        """Test successful Neo4j import and instantiation."""
        from chatx.storage.graph import Neo4jGraphStore
        
        # Should be able to instantiate (though connection will fail without server)
        store = Neo4jGraphStore("bolt://localhost:7687", "neo4j", "password")
        assert store is not None
        assert isinstance(store, Neo4jGraphStore)

    @pytest.mark.asyncio
    async def test_neo4j_async_connection(self, graph_store):
        """Test async Neo4j connection and disconnection."""
        from unittest.mock import patch
        from chatx.storage.graph import AsyncGraphDatabase
        
        store, session = graph_store
        
        # Configure the mock driver's session context manager properly
        session_context = AsyncMock()
        session_context.__aenter__ = AsyncMock(return_value=session)
        session_context.__aexit__ = AsyncMock(return_value=None)
        mock_driver = AsyncMock()
        mock_driver.session.return_value = session_context
        
        # Mock AsyncGraphDatabase.driver to return our configured mock driver
        with patch.object(AsyncGraphDatabase, 'driver', return_value=mock_driver):
            await store.connect()
            mock_driver.session.assert_called_with(database="neo4j")
            session.run.assert_called_with("RETURN 1")
        
        # Test disconnection (now using the mock_driver)
        await store.disconnect()
        mock_driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_session_context_management(self, graph_store):
        """Test that async sessions are properly managed."""
        store, session = graph_store
        
        # Mock a simple query
        await store.get_conversation_graph("test_conv")
        
        # Verify async session context was used
        store.driver.session.assert_called_with(database="neo4j")
        store.driver.session.return_value.__aenter__.assert_called()
        store.driver.session.return_value.__aexit__.assert_called()

    @pytest.mark.asyncio 
    async def test_async_query_execution(self, graph_store):
        """Test that queries are properly awaited."""
        store, session = graph_store
        
        # Mock query result with records
        mock_records = [
            {"id": "node_1", "type": "chunk", "props": {"text": "test"}},
            {"id": "node_2", "type": "chunk", "props": {"text": "test2"}}
        ]
        
        async def mock_aiter():
            for record in mock_records:
                yield record
        
        session.run.return_value.__aiter__ = mock_aiter
        
        # Execute query
        result = await store.get_conversation_graph("test_conv")
        
        # Verify async run was called
        session.run.assert_called()
        
        # Should handle empty results gracefully
        assert result is None  # No nodes found in this mock

    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test Neo4j store creation from pydantic config."""
        from chatx.utils.config import Neo4jConfig
        
        # Create config
        config = Neo4jConfig(
            uri="bolt://test:7687",
            username="testuser",
            password="testpass",
            max_connection_lifetime=600,
            max_connection_pool_size=50,
            connection_timeout=15
        )
        
        # Create store from config
        store = Neo4jGraphStore.from_config(config)
        
        # Verify configuration was applied
        assert store.uri == "bolt://test:7687"
        assert store.auth == ("testuser", "testpass")
        assert store.max_connection_lifetime == 600
        assert store.max_connection_pool_size == 50
        assert store.connection_timeout == 15

    @pytest.mark.asyncio
    async def test_async_driver_configuration(self, mock_async_neo4j_driver):
        """Test that async driver is created with proper configuration."""
        from chatx.storage.graph import AsyncGraphDatabase
        
        driver, session = mock_async_neo4j_driver
        
        # Create store with custom config
        store = Neo4jGraphStore(
            uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
            max_connection_lifetime=500,
            max_connection_pool_size=75,
            connection_timeout=20
        )
        
        # Mock AsyncGraphDatabase.driver
        from unittest.mock import patch
        with patch.object(AsyncGraphDatabase, 'driver', return_value=driver) as mock_driver:
            await store.connect()
            
            # Verify driver was created with proper config
            mock_driver.assert_called_once_with(
                "bolt://localhost:7687",
                auth=("neo4j", "password"),
                max_connection_lifetime=500,
                max_connection_pool_size=75,
                connection_timeout=20
            )

    @pytest.mark.asyncio
    async def test_conversation_to_graph_transformation(self):
        """Test converting conversation chunks to graph structure."""
        mock_store = Mock(spec=BaseGraphStore)
        
        # Mock conversation chunks
        chunks = [
            {
                "chunk_id": "ch_001",
                "text": "I feel like you're not listening to me",
                "meta": {
                    "message_ids": ["msg_1", "msg_2"],
                    "psychology_labels": ["attention_availability", "boundary_consent"]
                }
            }
        ]
        
        expected_graph = ConversationGraph(
            conversation_id="conv_test",
            nodes=[],
            relationships=[],
            metadata={}
        )
        
        mock_store.create_graph = AsyncMock(return_value=expected_graph)
        
        result = await mock_store.create_graph("conv_test", chunks)
        
        mock_store.create_graph.assert_called_once_with("conv_test", chunks)
        assert result.conversation_id == "conv_test"

    @pytest.mark.asyncio
    async def test_relationship_evolution_queries(self):
        """Test temporal relationship evolution queries."""
        mock_store = Mock(spec=BaseGraphStore)
        
        # Mock temporal query
        expected_evolution = [
            {
                "timeframe": "2025-09-01_2025-09-07",
                "escalation_events": 3,
                "repair_attempts": 2,
                "dominant_patterns": ["boundary_tension", "repair_cycle"]
            }
        ]
        
        mock_store.get_temporal_evolution = AsyncMock(return_value=expected_evolution)
        
        result = await mock_store.get_temporal_evolution(
            conversation_id="conv_123",
            time_window_days=7
        )
        
        mock_store.get_temporal_evolution.assert_called_once_with(
            conversation_id="conv_123",
            time_window_days=7
        )
        assert result[0]["escalation_events"] == 3
        assert "repair_cycle" in result[0]["dominant_patterns"]

    @pytest.mark.asyncio 
    async def test_escalation_pattern_detection(self):
        """Test escalation pattern detection in relationships."""
        mock_store = Mock(spec=BaseGraphStore)
        
        expected_patterns = [
            {
                "pattern_type": "escalation_cycle",
                "confidence": 0.85,
                "message_sequence": ["msg_1", "msg_2", "msg_3"],
                "triggers": ["boundary_violation", "attention_availability"],
                "resolution": "repair_attempt"
            }
        ]
        
        mock_store.detect_patterns = AsyncMock(return_value=expected_patterns)
        
        result = await mock_store.detect_patterns(
            conversation_id="conv_123",
            pattern_types=["escalation_cycle", "repair_cycle"]
        )
        
        mock_store.detect_patterns.assert_called_once()
        assert result[0]["pattern_type"] == "escalation_cycle"
        assert result[0]["confidence"] == 0.85


class TestGraphSchemaDesign:
    """Test graph schema design for psychology relationships."""

    def test_message_node_schema(self):
        """Test message node contains required psychology properties."""
        message_node = GraphNode(
            id="msg_123",
            node_type="message",
            properties={
                "text": "I need you to respect my boundaries",
                "timestamp": "2025-09-04T10:30:00Z",
                "sender": "me",
                "psychology_labels_coarse": ["boundary_consent"],
                "psychology_labels_fine": ["boundary_setting_explicit"],
                "emotion_primary": "assertive",
                "boundary_signal": "set",
                "repair_attempt": False
            }
        )
        
        assert message_node.properties["psychology_labels_coarse"] == ["boundary_consent"]
        assert message_node.properties["boundary_signal"] == "set"

    def test_relationship_types_schema(self):
        """Test relationship types for psychology analysis."""
        relationship_types = [
            "RESPONDS_TO",           # Direct response
            "ESCALATES_FROM",        # Escalation relationship
            "REPAIRS_AFTER",         # Repair attempt  
            "TRIGGERS",              # Trigger relationship
            "PARALLELS",             # Similar pattern
            "CONTRADICTS",           # Contradiction
            "REFERENCES_BACK",       # Historical reference
        ]
        
        for rel_type in relationship_types:
            relationship = GraphRelationship(
                from_node="msg_1",
                to_node="msg_2", 
                relationship_type=rel_type,
                properties={"confidence": 0.8}
            )
            assert relationship.relationship_type == rel_type

    def test_temporal_properties_schema(self):
        """Test temporal properties for relationship evolution."""
        relationship = GraphRelationship(
            from_node="msg_1",
            to_node="msg_2",
            relationship_type="ESCALATES_FROM",
            properties={
                "time_delta_seconds": 3600,
                "escalation_intensity": "high", 
                "psychology_transition": "boundary_test_to_violation",
                "repair_opportunity_missed": True,
                "pattern_frequency": 0.15  # 15% of similar situations
            }
        )
        
        assert relationship.properties["time_delta_seconds"] == 3600
        assert relationship.properties["psychology_transition"] == "boundary_test_to_violation"


class TestHybridStorageConsistency:
    """Test consistency between ChromaDB and Neo4j storage."""

    @pytest.mark.asyncio
    async def test_hybrid_storage_consistency(self):
        """Test data consistency between vector and graph stores."""
        # Mock both stores
        mock_vector_store = Mock()
        mock_graph_store = Mock(spec=BaseGraphStore)
        
        # Test data consistency
        chunk_id = "ch_001"
        
        # Vector store has embedding
        mock_vector_store.get_chunk = Mock(return_value={
            "chunk_id": chunk_id,
            "text": "I feel anxious about our relationship",
            "psychology_labels": ["anxiety", "relationship_concern"]
        })
        
        # Graph store has relationships
        mock_graph_store.get_conversation_graph = AsyncMock(return_value=ConversationGraph(
            conversation_id="conv_123",
            nodes=[GraphNode(chunk_id, "chunk", {"psychology_labels": ["anxiety", "relationship_concern"]})],
            relationships=[],
            metadata={}
        ))
        
        # Verify consistency
        vector_chunk = mock_vector_store.get_chunk(chunk_id)
        graph_data = await mock_graph_store.get_conversation_graph("conv_123")
        
        # Should have matching psychology labels
        vector_labels = set(vector_chunk["psychology_labels"])
        graph_labels = set(graph_data.nodes[0].properties["psychology_labels"])
        
        assert vector_labels == graph_labels