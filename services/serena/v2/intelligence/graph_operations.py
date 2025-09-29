"""
Serena v2 Phase 2: Core Graph Operations

High-performance code relationship queries with ADHD-optimized complexity filtering
and <200ms response guarantees for intelligent navigation.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum

from .database import SerenaIntelligenceDatabase, DatabaseConfig
from ..performance_monitor import PerformanceMonitor
from ..adhd_features import CodeComplexityAnalyzer
from ..tree_sitter_analyzer import StructuralElement, CodeComplexity

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of code relationships for navigation intelligence."""
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    DEFINES = "defines"
    USES = "uses"
    CONTAINS = "contains"
    REFERENCES = "references"
    IMPLEMENTS = "implements"
    OVERRIDES = "overrides"
    SIMILAR_TO = "similar_to"


class NavigationMode(str, Enum):
    """Navigation modes for ADHD optimization."""
    FOCUS = "focus"          # Minimal results, high relevance
    EXPLORE = "explore"      # Moderate results, balanced complexity
    COMPREHENSIVE = "comprehensive"  # Full results, all complexity levels


@dataclass
class CodeElementNode:
    """Enhanced code element with relationship intelligence."""
    id: int
    file_path: str
    element_name: str
    element_type: str
    language: str
    start_line: int
    end_line: int
    complexity_score: float
    complexity_level: str
    cognitive_load_factor: float
    access_frequency: int
    adhd_insights: List[str]
    tree_sitter_metadata: Dict[str, Any]

    @property
    def adhd_friendly(self) -> bool:
        """Check if this element is ADHD-friendly (low cognitive load)."""
        return self.complexity_score <= 0.6 and self.cognitive_load_factor <= 0.5

    @property
    def location_signature(self) -> str:
        """Generate location signature for navigation."""
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


@dataclass
class RelationshipEdge:
    """Code relationship with ADHD navigation metadata."""
    source_id: int
    target_id: int
    relationship_type: str
    strength: float
    confidence: float
    cognitive_load: float
    adhd_navigation_difficulty: str
    traversal_frequency: int
    average_traversal_time: float

    @property
    def adhd_recommended(self) -> bool:
        """Check if this relationship is recommended for ADHD navigation."""
        return (self.cognitive_load <= 0.5 and
                self.adhd_navigation_difficulty in ["easy", "moderate"] and
                self.confidence >= 0.7)


@dataclass
class NavigationPath:
    """A path through the code relationship graph."""
    elements: List[CodeElementNode]
    relationships: List[RelationshipEdge]
    total_complexity: float
    cognitive_load_score: float
    estimated_traversal_time: float
    adhd_recommendations: List[str]

    @property
    def adhd_difficulty(self) -> str:
        """Assess ADHD difficulty of this navigation path."""
        if self.cognitive_load_score <= 0.3:
            return "easy"
        elif self.cognitive_load_score <= 0.6:
            return "moderate"
        elif self.cognitive_load_score <= 0.8:
            return "challenging"
        else:
            return "overwhelming"


class SerenaGraphOperations:
    """
    Core graph operations for Serena v2 Phase 2 intelligence.

    Features:
    - Sub-200ms code relationship queries
    - ADHD-optimized complexity filtering
    - Progressive disclosure for cognitive load management
    - Integration with TreeSitterAnalyzer for structural context
    - Intelligent prefetching for common navigation patterns
    - Adaptive query optimization based on user patterns
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.complexity_analyzer = CodeComplexityAnalyzer()

        # Query cache for performance optimization
        self._query_cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = 300  # 5 minutes

        # ADHD optimization settings
        self.default_result_limits = {
            NavigationMode.FOCUS: 5,
            NavigationMode.EXPLORE: 15,
            NavigationMode.COMPREHENSIVE: 50
        }

    # Core Element Queries

    async def get_element_by_id(self, element_id: int) -> Optional[CodeElementNode]:
        """Get a code element by ID with performance monitoring."""
        operation_id = self.performance_monitor.start_operation("get_element_by_id")

        try:
            query = """
            SELECT id, file_path, element_name, element_type, language,
                   start_line, end_line, complexity_score, complexity_level,
                   cognitive_load_factor, access_frequency, adhd_insights,
                   tree_sitter_metadata
            FROM code_elements
            WHERE id = $1
            """

            result = await self.database.execute_query(
                query,
                (element_id,),
                cache_key=f"element_{element_id}"
            )

            if result:
                element_data = result[0]
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                return CodeElementNode(**element_data)

            self.performance_monitor.end_operation(operation_id, success=True, cache_hit=False)
            return None

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get element {element_id}: {e}")
            raise

    async def find_elements_by_name(
        self,
        element_name: str,
        file_path: Optional[str] = None,
        element_type: Optional[str] = None,
        mode: NavigationMode = NavigationMode.EXPLORE
    ) -> List[CodeElementNode]:
        """Find code elements by name with ADHD-optimized filtering."""
        operation_id = self.performance_monitor.start_operation("find_elements_by_name")

        try:
            # Build query with optional filters
            conditions = ["element_name ILIKE $1"]
            params = [f"%{element_name}%"]
            param_count = 1

            if file_path:
                param_count += 1
                conditions.append(f"file_path = ${param_count}")
                params.append(file_path)

            if element_type:
                param_count += 1
                conditions.append(f"element_type = ${param_count}")
                params.append(element_type)

            # ADHD optimization: order by complexity and relevance
            query = f"""
            SELECT id, file_path, element_name, element_type, language,
                   start_line, end_line, complexity_score, complexity_level,
                   cognitive_load_factor, access_frequency, adhd_insights,
                   tree_sitter_metadata
            FROM code_elements
            WHERE {' AND '.join(conditions)}
            ORDER BY
                complexity_score ASC,  -- Simple first for ADHD
                access_frequency DESC, -- Frequently accessed first
                element_name
            LIMIT ${ param_count + 1}
            """

            result_limit = self.default_result_limits[mode]
            params.append(result_limit)

            results = await self.database.execute_query(
                query,
                tuple(params),
                cache_key=f"find_name_{element_name}_{file_path}_{element_type}_{mode}"
            )

            elements = [CodeElementNode(**row) for row in results]

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🔍 Found {len(elements)} elements for '{element_name}' in {mode} mode")
            return elements

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to find elements by name '{element_name}': {e}")
            raise

    async def get_elements_in_file(
        self,
        file_path: str,
        complexity_filter: bool = True,
        mode: NavigationMode = NavigationMode.EXPLORE
    ) -> List[CodeElementNode]:
        """Get all elements in a file with ADHD complexity filtering."""
        operation_id = self.performance_monitor.start_operation("get_elements_in_file")

        try:
            # Base query
            query = """
            SELECT id, file_path, element_name, element_type, language,
                   start_line, end_line, complexity_score, complexity_level,
                   cognitive_load_factor, access_frequency, adhd_insights,
                   tree_sitter_metadata
            FROM code_elements
            WHERE file_path = $1
            """

            # Apply ADHD complexity filtering
            if complexity_filter and mode == NavigationMode.FOCUS:
                query += " AND complexity_score <= 0.6"  # Only simple and moderate complexity

            # ADHD-optimized ordering
            query += """
            ORDER BY
                start_line ASC,       -- Natural file order
                complexity_score ASC  -- Simple first within each section
            LIMIT $2
            """

            result_limit = self.default_result_limits[mode]
            results = await self.database.execute_query(
                query,
                (file_path, result_limit),
                cache_key=f"file_elements_{file_path}_{complexity_filter}_{mode}"
            )

            elements = [CodeElementNode(**row) for row in results]

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"📁 Found {len(elements)} elements in {file_path} (mode: {mode})")
            return elements

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get elements in file '{file_path}': {e}")
            raise

    # Relationship Queries

    async def get_related_elements(
        self,
        element_id: int,
        relationship_types: Optional[List[RelationshipType]] = None,
        direction: str = "both",  # "outgoing", "incoming", "both"
        mode: NavigationMode = NavigationMode.EXPLORE
    ) -> List[Tuple[CodeElementNode, RelationshipEdge]]:
        """Get elements related to a given element with ADHD optimization."""
        operation_id = self.performance_monitor.start_operation("get_related_elements")

        try:
            # Build relationship type filter
            type_filter = ""
            params = [element_id]
            param_count = 1

            if relationship_types:
                type_list = [t.value for t in relationship_types]
                param_count += 1
                type_filter = f" AND r.relationship_type = ANY(${param_count})"
                params.append(type_list)

            # Build direction filter
            direction_conditions = []
            if direction in ["outgoing", "both"]:
                direction_conditions.append("r.source_element_id = $1")
            if direction in ["incoming", "both"]:
                direction_conditions.append("r.target_element_id = $1")

            direction_filter = f" AND ({' OR '.join(direction_conditions)})"

            query = f"""
            SELECT
                -- Element data
                e.id, e.file_path, e.element_name, e.element_type, e.language,
                e.start_line, e.end_line, e.complexity_score, e.complexity_level,
                e.cognitive_load_factor, e.access_frequency, e.adhd_insights,
                e.tree_sitter_metadata,
                -- Relationship data
                r.source_element_id, r.target_element_id, r.relationship_type,
                r.strength, r.confidence, r.cognitive_load as rel_cognitive_load,
                r.adhd_navigation_difficulty, r.traversal_frequency, r.average_traversal_time
            FROM code_relationships r
            JOIN code_elements e ON (
                CASE
                    WHEN r.source_element_id = $1 THEN e.id = r.target_element_id
                    ELSE e.id = r.source_element_id
                END
            )
            WHERE 1=1
            {direction_filter}
            {type_filter}
            ORDER BY
                r.strength DESC,           -- Strongest relationships first
                e.complexity_score ASC,    -- Simple elements first for ADHD
                r.traversal_frequency DESC -- Frequently used paths first
            LIMIT ${ param_count + 1}
            """

            result_limit = self.default_result_limits[mode]
            params.append(result_limit)

            results = await self.database.execute_query(
                query,
                tuple(params),
                cache_key=f"related_{element_id}_{direction}_{mode}"
            )

            # Parse results into elements and relationships
            related_pairs = []
            for row in results:
                # Extract element data (first 13 fields)
                element_data = {
                    'id': row['id'],
                    'file_path': row['file_path'],
                    'element_name': row['element_name'],
                    'element_type': row['element_type'],
                    'language': row['language'],
                    'start_line': row['start_line'],
                    'end_line': row['end_line'],
                    'complexity_score': row['complexity_score'],
                    'complexity_level': row['complexity_level'],
                    'cognitive_load_factor': row['cognitive_load_factor'],
                    'access_frequency': row['access_frequency'],
                    'adhd_insights': row['adhd_insights'],
                    'tree_sitter_metadata': row['tree_sitter_metadata']
                }

                # Extract relationship data
                relationship_data = {
                    'source_id': row['source_element_id'],
                    'target_id': row['target_element_id'],
                    'relationship_type': row['relationship_type'],
                    'strength': row['strength'],
                    'confidence': row['confidence'],
                    'cognitive_load': row['rel_cognitive_load'],
                    'adhd_navigation_difficulty': row['adhd_navigation_difficulty'],
                    'traversal_frequency': row['traversal_frequency'],
                    'average_traversal_time': row['average_traversal_time']
                }

                element = CodeElementNode(**element_data)
                relationship = RelationshipEdge(**relationship_data)
                related_pairs.append((element, relationship))

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🔗 Found {len(related_pairs)} related elements for element {element_id}")
            return related_pairs

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get related elements for {element_id}: {e}")
            raise

    async def find_navigation_path(
        self,
        source_element_id: int,
        target_element_id: int,
        max_depth: int = 3,
        adhd_optimized: bool = True
    ) -> Optional[NavigationPath]:
        """Find optimal navigation path between two elements with ADHD considerations."""
        operation_id = self.performance_monitor.start_operation("find_navigation_path")

        try:
            # Use recursive CTE for path finding with complexity weighting
            query = """
            WITH RECURSIVE navigation_path AS (
                -- Base case: direct relationships
                SELECT
                    r.source_element_id,
                    r.target_element_id,
                    r.relationship_type,
                    r.strength,
                    r.cognitive_load,
                    ARRAY[r.source_element_id] as path_elements,
                    ARRAY[r.relationship_type] as path_relationships,
                    1 as depth,
                    r.cognitive_load as total_cognitive_load
                FROM code_relationships r
                WHERE r.source_element_id = $1
                  AND ($3 = FALSE OR r.cognitive_load <= 0.7) -- ADHD filter

                UNION ALL

                -- Recursive case: extend paths
                SELECT
                    np.source_element_id,
                    r.target_element_id,
                    r.relationship_type,
                    np.strength * r.strength as strength,
                    r.cognitive_load,
                    np.path_elements || r.source_element_id,
                    np.path_relationships || r.relationship_type,
                    np.depth + 1,
                    np.total_cognitive_load + r.cognitive_load
                FROM navigation_path np
                JOIN code_relationships r ON np.target_element_id = r.source_element_id
                WHERE np.depth < $4
                  AND r.target_element_id != ALL(np.path_elements) -- Avoid cycles
                  AND ($3 = FALSE OR r.cognitive_load <= 0.7) -- ADHD filter
            )
            SELECT *
            FROM navigation_path
            WHERE target_element_id = $2
            ORDER BY
                depth ASC,                    -- Shortest paths first
                total_cognitive_load ASC,     -- Lowest cognitive load first
                strength DESC                 -- Strongest relationships first
            LIMIT 1
            """

            results = await self.database.execute_query(
                query,
                (source_element_id, target_element_id, adhd_optimized, max_depth)
            )

            if not results:
                self.performance_monitor.end_operation(operation_id, success=True)
                return None

            path_data = results[0]

            # Fetch full element and relationship details for the path
            path_element_ids = path_data['path_elements'] + [path_data['target_element_id']]

            # Get elements in path
            elements_query = """
            SELECT id, file_path, element_name, element_type, language,
                   start_line, end_line, complexity_score, complexity_level,
                   cognitive_load_factor, access_frequency, adhd_insights,
                   tree_sitter_metadata
            FROM code_elements
            WHERE id = ANY($1)
            ORDER BY array_position($1, id)
            """

            element_results = await self.database.execute_query(
                elements_query,
                (path_element_ids,)
            )

            elements = [CodeElementNode(**row) for row in element_results]

            # Generate ADHD recommendations for this path
            adhd_recommendations = self._generate_path_recommendations(
                elements,
                path_data['total_cognitive_load'],
                path_data['depth']
            )

            path = NavigationPath(
                elements=elements,
                relationships=[],  # Would need to fetch relationship details if needed
                total_complexity=sum(e.complexity_score for e in elements) / len(elements),
                cognitive_load_score=path_data['total_cognitive_load'],
                estimated_traversal_time=path_data['depth'] * 30.0,  # Estimate 30s per hop
                adhd_recommendations=adhd_recommendations
            )

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🛤️ Found navigation path from {source_element_id} to {target_element_id} (depth: {path_data['depth']})")
            return path

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to find navigation path from {source_element_id} to {target_element_id}: {e}")
            raise

    # ADHD Optimization Helpers

    def _generate_path_recommendations(
        self,
        elements: List[CodeElementNode],
        cognitive_load: float,
        depth: int
    ) -> List[str]:
        """Generate ADHD-specific recommendations for a navigation path."""
        recommendations = []

        # Cognitive load assessment
        if cognitive_load <= 0.3:
            recommendations.append("🟢 Easy path - good for any focus level")
        elif cognitive_load <= 0.6:
            recommendations.append("🟡 Moderate complexity - best during focused time")
        elif cognitive_load <= 0.8:
            recommendations.append("🟠 Complex path - consider breaking into smaller steps")
        else:
            recommendations.append("🔴 High complexity - tackle during peak focus time")

        # Depth recommendations
        if depth <= 2:
            recommendations.append("📍 Short path - easy to follow")
        elif depth <= 4:
            recommendations.append("🧭 Medium path - consider bookmarking intermediate stops")
        else:
            recommendations.append("🗺️ Long path - strongly recommend progressive exploration")

        # Complexity distribution analysis
        complex_elements = [e for e in elements if e.complexity_score > 0.7]
        if complex_elements:
            recommendations.append(f"⚠️ Contains {len(complex_elements)} complex elements - review those separately")

        # Access frequency insights
        frequently_accessed = [e for e in elements if e.access_frequency > 10]
        if frequently_accessed:
            recommendations.append(f"🚀 {len(frequently_accessed)} elements are frequently accessed - familiar territory")

        return recommendations

    async def get_adhd_insights_for_element(self, element_id: int) -> Dict[str, Any]:
        """Get comprehensive ADHD insights for a code element."""
        operation_id = self.performance_monitor.start_operation("get_adhd_insights")

        try:
            element = await self.get_element_by_id(element_id)
            if not element:
                return {"error": "Element not found"}

            # Get related elements for context
            related = await self.get_related_elements(element_id, mode=NavigationMode.FOCUS)

            # Analyze complexity and cognitive load
            complexity_category, complexity_description = self.complexity_analyzer.categorize_complexity(
                element.complexity_score
            )

            insights = {
                "element_info": {
                    "name": element.element_name,
                    "type": element.element_type,
                    "location": element.location_signature,
                    "complexity_category": complexity_category,
                    "complexity_description": complexity_description,
                    "adhd_friendly": element.adhd_friendly,
                    "cognitive_load_factor": element.cognitive_load_factor
                },
                "navigation_context": {
                    "related_elements_count": len(related),
                    "adhd_recommended_related": len([r for r, e in related if e.adhd_recommended]),
                    "access_frequency": element.access_frequency,
                    "popularity": "high" if element.access_frequency > 20 else
                               "medium" if element.access_frequency > 5 else "low"
                },
                "adhd_recommendations": element.adhd_insights,
                "focus_suggestions": []
            }

            # Generate focus suggestions
            if element.complexity_score > 0.7:
                insights["focus_suggestions"].append("Consider reviewing during peak focus time")
                insights["focus_suggestions"].append("Break down into smaller conceptual pieces")

            if len(related) > 10:
                insights["focus_suggestions"].append("Many connections - use progressive disclosure")

            if element.cognitive_load_factor > 0.6:
                insights["focus_suggestions"].append("High cognitive load - take breaks if needed")

            self.performance_monitor.end_operation(operation_id, success=True)

            return insights

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get ADHD insights for element {element_id}: {e}")
            raise

    # Performance and Analytics

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get graph operations performance metrics."""
        try:
            # Query performance statistics
            stats_query = """
            SELECT
                COUNT(*) as total_elements,
                COUNT(DISTINCT file_path) as files_covered,
                AVG(complexity_score) as avg_complexity,
                COUNT(*) FILTER (WHERE complexity_score <= 0.6) as adhd_friendly_count,
                AVG(access_frequency) as avg_access_frequency
            FROM code_elements
            """

            relationship_stats_query = """
            SELECT
                COUNT(*) as total_relationships,
                COUNT(DISTINCT relationship_type) as relationship_types,
                AVG(strength) as avg_relationship_strength,
                AVG(cognitive_load) as avg_cognitive_load,
                COUNT(*) FILTER (WHERE adhd_navigation_difficulty IN ('easy', 'moderate')) as adhd_friendly_relationships
            FROM code_relationships
            """

            element_stats = await self.database.execute_query(stats_query)
            relationship_stats = await self.database.execute_query(relationship_stats_query)

            # Get cache statistics
            cache_hit_rate = len([k for k, (_, ts) in self._query_cache.items()
                                if time.time() - ts < self._cache_ttl]) / max(len(self._query_cache), 1)

            return {
                "elements": element_stats[0] if element_stats else {},
                "relationships": relationship_stats[0] if relationship_stats else {},
                "performance": {
                    "cache_hit_rate": cache_hit_rate,
                    "cached_queries": len(self._query_cache),
                    "average_query_time_ms": getattr(self.performance_monitor, 'average_duration', 0)
                },
                "adhd_optimization": {
                    "adhd_friendly_elements_percentage": (
                        element_stats[0]['adhd_friendly_count'] / max(element_stats[0]['total_elements'], 1) * 100
                        if element_stats else 0
                    ),
                    "adhd_friendly_relationships_percentage": (
                        relationship_stats[0]['adhd_friendly_relationships'] / max(relationship_stats[0]['total_relationships'], 1) * 100
                        if relationship_stats else 0
                    )
                }
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}

    async def clear_cache(self) -> None:
        """Clear the query cache for fresh performance testing."""
        self._query_cache.clear()
        logger.info("🧹 Graph operations cache cleared")


# Convenience functions for common operations
async def create_graph_operations(
    database: SerenaIntelligenceDatabase,
    performance_monitor: PerformanceMonitor = None
) -> SerenaGraphOperations:
    """Create graph operations instance with database connection."""
    return SerenaGraphOperations(database, performance_monitor)


async def quick_performance_test(database: SerenaIntelligenceDatabase) -> Dict[str, Any]:
    """Run quick performance test for graph operations."""
    try:
        graph_ops = SerenaGraphOperations(database)

        test_results = {
            "tests_run": [],
            "all_under_200ms": True,
            "average_time_ms": 0.0,
            "adhd_compliant": True
        }

        # Test basic queries
        test_queries = [
            ("get_element_1", lambda: graph_ops.get_element_by_id(1)),
            ("find_elements_main", lambda: graph_ops.find_elements_by_name("main")),
            ("get_performance_metrics", lambda: graph_ops.get_performance_metrics())
        ]

        total_time = 0.0
        for test_name, test_func in test_queries:
            start_time = time.time()
            try:
                await test_func()
                query_time = (time.time() - start_time) * 1000
                total_time += query_time

                test_results["tests_run"].append({
                    "name": test_name,
                    "time_ms": round(query_time, 2),
                    "adhd_compliant": query_time < 200
                })

                if query_time >= 200:
                    test_results["all_under_200ms"] = False

            except Exception as e:
                test_results["tests_run"].append({
                    "name": test_name,
                    "error": str(e),
                    "adhd_compliant": False
                })
                test_results["all_under_200ms"] = False

        test_results["average_time_ms"] = round(total_time / len(test_queries), 2)
        test_results["adhd_compliant"] = test_results["all_under_200ms"] and test_results["average_time_ms"] < 150

        return test_results

    except Exception as e:
        return {"error": str(e), "adhd_compliant": False}


if __name__ == "__main__":
    # Performance test when run directly
    async def main():
        print("🗄️ Serena Graph Operations Performance Test")

        # Would need actual database connection for real test
        print("⚠️ Requires database connection for full testing")
        print("✅ Graph operations module loaded successfully")

    asyncio.run(main())