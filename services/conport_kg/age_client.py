#!/usr/bin/env python3
"""
AGE Client - Direct psycopg2 Connection with Pooling
Part of CONPORT-KG-2025 Phase 2 (Decision #117)

Eliminates 50-100ms docker exec overhead, enabling performance targets:
- Tier 1: <50ms
- Tier 2: <150ms
- Tier 3: <500ms
"""

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import List, Dict, Any, Optional
import json


class AGEClient:
    """
    PostgreSQL AGE Client with Connection Pooling

    Features:
    - Connection pooling (1-5 concurrent connections)
    - AGE extension loading and graph initialization
    - agtype result parsing to Python types
    - Error handling with graceful fallback
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5455,
        database: str = "dopemux_knowledge_graph",
        user: str = "dopemux_age",
        password: Optional[str] = None,
        graph_name: str = "conport_knowledge",
        min_connections: int = 1,
        max_connections: int = 5
    ):
        """Initialize AGE client with connection pool"""

        self.graph_name = graph_name
        self.host = host
        self.port = port
        self.database = database
        self.user = user

        # Get password from environment or use provided
        self.password = password or os.getenv('AGE_PASSWORD', 'dopemux_age_dev_password')

        try:
            # Create connection pool
            self.pool = psycopg2.pool.SimpleConnectionPool(
                min_connections,
                max_connections,
                host=host,
                port=port,
                database=database,
                user=user,
                password=self.password
            )

            # Test connection and ensure AGE is loaded
            conn = self.pool.getconn()
            try:
                cursor = conn.cursor()

                # Load AGE extension
                cursor.execute("LOAD 'age';")

                # Set search path
                cursor.execute(f"SET search_path = ag_catalog, {graph_name}, public;")

                cursor.close()
                conn.commit()
            finally:
                self.pool.putconn(conn)

            print(f"✅ AGE Client initialized: {host}:{port}/{database} (graph: {graph_name})")
            print(f"   Connection pool: {min_connections}-{max_connections} connections")

        except Exception as e:
            print(f"❌ AGE Client initialization failed: {e}")
            print(f"   Falling back to docker exec method")
            self.pool = None
            raise

    def execute_cypher(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute Cypher query via AGE and return parsed results

        Args:
            cypher_query: Cypher query string (embedded in SELECT FROM cypher())
            params: Optional query parameters (for parameterized queries)

        Returns:
            List of dictionaries with parsed results
        """

        if self.pool is None:
            raise Exception("Connection pool not initialized - use docker exec fallback")

        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            # Ensure AGE is loaded and search path is set
            cursor.execute("LOAD 'age';")
            cursor.execute(f"SET search_path = ag_catalog, {self.graph_name}, public;")

            # Execute query
            cursor.execute(cypher_query, params or {})

            # Fetch all results
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []

            # Parse results
            results = []
            for row in rows:
                result_dict = {}
                for i, value in enumerate(row):
                    col_name = column_names[i] if i < len(column_names) else f"col_{i}"
                    result_dict[col_name] = self._parse_agtype(value)
                results.append(result_dict)

            cursor.close()
            return results

        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            print(f"   Query: {cypher_query[:100]}...")
            raise

        finally:
            self.pool.putconn(conn)

    def _parse_agtype(self, value: Any) -> Any:
        """
        Parse AGE agtype values to Python types

        AGE returns values in agtype format which needs parsing:
        - Vertex: {"id": X, "label": "Label", "properties": {...}}
        - Edge: {"id": X, "label": "TYPE", "start_id": Y, "end_id": Z, "properties": {...}}
        - Scalar: Direct value or JSON string
        """

        if value is None:
            return None

        # If already a Python type, return as-is
        if isinstance(value, (int, float, bool)):
            return value

        # Try to parse as JSON (agtype is JSON-like)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)

                # Check if it's a vertex or edge
                if isinstance(parsed, dict):
                    if 'label' in parsed and 'properties' in parsed:
                        # It's a vertex or edge
                        return parsed

                return parsed

            except (json.JSONDecodeError, TypeError):
                # Not JSON, return as string
                return value

        # For other types, return as-is
        return value

    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            print("✅ AGE Client connection pool closed")


if __name__ == "__main__":
    # Test AGE Client
    print("=" * 60)
    print("Testing AGE Client with Connection Pooling")
    print("=" * 60)

    try:
        # Initialize client
        client = AGEClient()

        # Test query: Count decisions
        print("\n[Test 1] Count all decisions:")
        cypher = """
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                RETURN COUNT(d) as total
            $$) as (total agtype);
        """
        results = client.execute_cypher(cypher)
        print(f"   Total decisions: {results[0]['total']}")

        # Test query: Get recent decisions
        print("\n[Test 2] Get 3 recent decisions:")
        cypher = """
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                RETURN d.id, d.summary
                ORDER BY d.id DESC
                LIMIT 3
            $$) as (id agtype, summary agtype);
        """
        results = client.execute_cypher(cypher)
        for i, decision in enumerate(results, 1):
            print(f"   {i}. #{decision['id']}: {decision['summary'][:60]}...")

        # Test query: Get relationships
        print("\n[Test 3] Sample relationships:")
        cypher = """
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d1:Decision)-[r]->(d2:Decision)
                RETURN d1.id as source, type(r) as rel_type, d2.id as target
                LIMIT 5
            $$) as (source agtype, rel_type agtype, target agtype);
        """
        results = client.execute_cypher(cypher)
        for rel in results:
            print(f"   Decision #{rel['source']} --{rel['rel_type']}--> Decision #{rel['target']}")

        # Close client
        client.close()

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
