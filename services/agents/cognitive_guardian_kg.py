#!/usr/bin/env python3
"""
CognitiveGuardianKG - ADHD-Optimized Knowledge Graph Integration
Week 4 Day 1: KG Query Layer Foundation

Architecture validated via deep analysis (see WEEK4_DAY1_DEEP_ANALYSIS.md)

Design Decisions:
- Dependency injection (testable, flexible)
- Graceful degradation (ADHD-friendly)
- Parameterized queries (secure)
- Per-instance AGE client (isolated, scalable)

Provides:
- Task relationship mapping (dependencies, blockers, related)
- Semantic task search (natural language)
- Decision context retrieval (track "why")
- ADHD pattern mining (successful patterns)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

# ConPort-KG imports (sys.path approach validated in deep analysis)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'conport_kg'))

try:
    from age_client import AGEClient
    from adhd_query_adapter import AttentionStateMonitor
    CONPORT_KG_AVAILABLE = True
except ImportError as e:
    CONPORT_KG_AVAILABLE = False
    logger.info(f"⚠️  ConPort-KG not available: {e}")
    # Define stub classes for graceful degradation
    class AGEClient:
        pass
    class AttentionStateMonitor:
        pass

logger = logging.getLogger(__name__)


class CognitiveGuardianKG:
    """
    ADHD-optimized Knowledge Graph integration for CognitiveGuardian.
    
    Features:
    - Task relationship queries (dependencies, blockers, related)
    - Semantic task search (natural language queries)
    - Decision context retrieval (why decisions made)
    - ADHD pattern mining (learn successful patterns)
    
    Architecture:
    - Dependency injection (testable)
    - Graceful degradation (ADHD-friendly)
    - Parameterized queries (secure against injection)
    - Connection pooling (per-instance, shareable via DI)
    """
    
    def __init__(
        self,
        workspace_id: str,
        age_client: Optional[AGEClient] = None,
        attention_monitor: Optional[AttentionStateMonitor] = None,
        enable_kg: bool = True
    ):
        """
        Initialize Knowledge Graph integration.
        
        Args:
            workspace_id: Workspace identifier (e.g., "/user/project")
            age_client: Optional AGE client (for sharing or mocking)
            attention_monitor: Optional attention monitor (for ADHD state tracking)
            enable_kg: Enable KG features (False = graceful degradation mode)
        """
        self.workspace_id = workspace_id
        self.enable_kg = enable_kg and CONPORT_KG_AVAILABLE
        
        # Dependency injection with defaults
        if self.enable_kg:
            try:
                self.age_client = age_client or self._create_age_client()
                self.attention_monitor = attention_monitor or AttentionStateMonitor()
                logger.info(f"✅ CognitiveGuardianKG initialized: {workspace_id}")
            except Exception as e:
                logger.warning(f"KG initialization failed, falling back to basic mode: {e}")
                self.enable_kg = False
                self.age_client = None
                self.attention_monitor = None
        else:
            self.age_client = None
            self.attention_monitor = None
            logger.info(f"⚠️  CognitiveGuardianKG in basic mode (KG disabled): {workspace_id}")
    
    def _create_age_client(self) -> AGEClient:
        """
        Create default AGE client with connection pooling.
        
        Returns:
            Configured AGE client
            
        Raises:
            Exception: If client creation fails
        """
        return AGEClient(
            host=os.getenv('AGE_HOST', 'localhost'),
            port=int(os.getenv('AGE_PORT', 5455)),
            database=os.getenv('AGE_DATABASE', 'dopemux_knowledge_graph'),
            user=os.getenv('AGE_USER', 'dopemux_age'),
            password=os.getenv('AGE_PASSWORD'),
            graph_name=os.getenv('AGE_GRAPH', 'conport_knowledge'),
            min_connections=1,
            max_connections=5
        )
    
    async def get_task_relationships(
        self,
        task_id: str
    ) -> Dict[str, List[str]]:
        """
        Get task relationships from knowledge graph.
        
        SECURE: Uses parameterized queries (prevents injection).
        ADHD-FRIENDLY: Graceful degradation (returns empty on failure).
        
        Args:
            task_id: Task identifier to query
            
        Returns:
            Dictionary with relationships:
            {
                "dependencies": ["task-123", ...],  # Tasks this depends on
                "blockers": ["task-456", ...],      # Tasks this blocks
                "related": ["task-789", ...]        # Related tasks
            }
            
        Example:
            >>> kg = CognitiveGuardianKG("/workspace")
            >>> rels = await kg.get_task_relationships("task-123")
            >>> logger.info(rels['dependencies'])
            ['task-setup-api', 'task-design-schema']
        """
        # Graceful degradation if KG disabled
        if not self.enable_kg or not self.age_client:
            return {"dependencies": [], "blockers": [], "related": []}
        
        # Parameterized query (AGE syntax: $1, $2, etc. in cypher, %s in PostgreSQL)
        query = """
        SELECT * FROM cypher('conport_knowledge', $$
            MATCH (t:Task)
            WHERE t.id = $1
            OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)
            OPTIONAL MATCH (t)-[:BLOCKS]->(block:Task)
            OPTIONAL MATCH (t)-[:RELATED_TO]->(rel:Task)
            RETURN 
                collect(DISTINCT dep.id) as dependencies,
                collect(DISTINCT block.id) as blockers,
                collect(DISTINCT rel.id) as related
        $$, %s) AS (
            dependencies agtype,
            blockers agtype,
            related agtype
        );
        """
        
        try:
            result = self.age_client.execute_cypher(query, (task_id,))
            
            if not result:
                return {"dependencies": [], "blockers": [], "related": []}
            
            row = result[0]
            return {
                "dependencies": self._parse_id_list(row.get('dependencies', [])),
                "blockers": self._parse_id_list(row.get('blockers', [])),
                "related": self._parse_id_list(row.get('related', []))
            }
            
        except Exception as e:
            # LOUD error logging (ERROR level for monitoring)
            logger.error(
                f"Task relationship query failed for {task_id}: {e}",
                exc_info=True,
                extra={
                    "task_id": task_id,
                    "query_type": "relationships",
                    "workspace_id": self.workspace_id
                }
            )
            
            # Graceful degradation (ADHD-friendly: no disruption)
            return {"dependencies": [], "blockers": [], "related": []}
    
    async def search_tasks_semantic(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for tasks (natural language queries).
        
        Day 1: Basic keyword matching
        Day 3: Will enhance with embeddings (sentence-transformers)
        
        ADHD-FRIENDLY: 
        - No need to remember exact task titles
        - Fuzzy matching via keywords
        - Limited results (default 5 to prevent overwhelm)
        
        Args:
            query: Natural language query (e.g., "tasks about API integration")
            limit: Maximum results (default 5 for ADHD)
            
        Returns:
            List of matching tasks with relevance scores:
            [
                {
                    "task_id": "task-123",
                    "title": "Implement REST API",
                    "relevance": 0.85,
                    "complexity": 0.7,
                    "energy_required": "high"
                },
                ...
            ]
            
        Example:
            >>> kg = CognitiveGuardianKG("/workspace")
            >>> results = await kg.search_tasks_semantic("API integration")
            >>> for task in results:
            ...     logger.info(f"{task['title']} (relevance: {task['relevance']:.2f})")
        """
        # Graceful degradation
        if not self.enable_kg or not self.age_client:
            return []
        
        if not query or not query.strip():
            return []
        
        # Day 1: Simple keyword matching
        # Day 3: Will add embedding-based semantic search
        keywords = query.lower().split()
        
        # Build parameterized query for keyword matching
        # Use ILIKE for case-insensitive matching
        query_conditions = []
        params = []
        for i, keyword in enumerate(keywords, start=1):
            query_conditions.append(f"toLower(t.title) CONTAINS ${i}")
            params.append(keyword)
        
        conditions_str = " OR ".join(query_conditions)
        
        cypher_query = f"""
        SELECT * FROM cypher('conport_knowledge', $$
            MATCH (t:Task)
            WHERE {conditions_str}
            RETURN t.id, t.title, t.complexity, t.energy_required
            LIMIT {limit}
        $$, {', '.join(['%s'] * len(params))}) AS (
            task_id agtype,
            title agtype,
            complexity agtype,
            energy_required agtype
        );
        """
        
        try:
            results = self.age_client.execute_cypher(cypher_query, tuple(params))
            
            # Calculate basic relevance (keyword match count)
            tasks = []
            for row in results:
                title = str(row.get('title', ''))
                
                # Count keyword matches
                matches = sum(1 for kw in keywords if kw in title.lower())
                relevance = matches / len(keywords) if keywords else 0.0
                
                tasks.append({
                    "task_id": str(row.get('task_id', '')),
                    "title": title,
                    "relevance": relevance,
                    "complexity": float(row.get('complexity', 0.5)),
                    "energy_required": str(row.get('energy_required', 'medium'))
                })
            
            # Sort by relevance (descending)
            tasks.sort(key=lambda t: t['relevance'], reverse=True)
            
            return tasks
            
        except Exception as e:
            logger.error(
                f"Semantic search failed for query '{query}': {e}",
                exc_info=True,
                extra={
                    "query": query,
                    "limit": limit,
                    "workspace_id": self.workspace_id
                }
            )
            
            # Graceful degradation
            return []
    
    def _parse_id_list(self, agtype_list: Any) -> List[str]:
        """
        Parse AGE agtype list to Python list of IDs.
        
        AGE returns lists as JSON strings or Python lists.
        
        Args:
            agtype_list: AGE agtype value (list)
            
        Returns:
            Python list of string IDs
        """
        if not agtype_list:
            return []
        
        # AGE can return lists as Python lists or JSON strings
        if isinstance(agtype_list, list):
            return [str(item) for item in agtype_list if item]
        
        # Try parsing as JSON if string
        if isinstance(agtype_list, str):
            try:
                import json
                parsed = json.loads(agtype_list)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed if item]
            except (json.JSONDecodeError, ValueError):
                pass
        
        return []
    
    def close(self):
        """Close AGE client connection pool."""
        if self.age_client:
            try:
                self.age_client.close()
                logger.info(f"✅ CognitiveGuardianKG closed: {self.workspace_id}")
            except Exception as e:
                logger.warning(f"Error closing AGE client: {e}")


# Module-level validation
if __name__ == "__main__":
    # Quick validation (synchronous wrapper for testing)
    async def test_basic():
        """Basic validation test."""
        logger.info("Testing CognitiveGuardianKG initialization...")
        
        # Test 1: Basic initialization
        kg = CognitiveGuardianKG(workspace_id="/test", enable_kg=False)
        logger.info(f"✅ Initialized in basic mode: {kg.workspace_id}")
        
        # Test 2: Graceful degradation
        rels = await kg.get_task_relationships("task-123")
        assert rels == {"dependencies": [], "blockers": [], "related": []}
        logger.info("✅ Graceful degradation works")
        
        # Test 3: Semantic search fallback
        results = await kg.search_tasks_semantic("test query")
        assert results == []
        logger.info("✅ Semantic search fallback works")
        
        logger.info("\n✅ All basic tests passed!")
    
    # Run test
    asyncio.run(test_basic())
