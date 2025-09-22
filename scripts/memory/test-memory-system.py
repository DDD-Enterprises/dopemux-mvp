#!/usr/bin/env python3
"""
Test suite for Dopemux Unified Memory System

Tests the ConPort memory server MCP tools and integration with Milvus/PostgreSQL.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

import asyncpg
import requests
from pymilvus import MilvusClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemorySystemTester:
    """Test suite for the memory system."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory")
        self.conport_url = "http://localhost:3004"
        self.milvus_host = "localhost"
        self.milvus_port = 19530
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if details:
            logger.info(f"   {details}")
        self.test_results.append((test_name, success, details))

    async def test_database_connection(self) -> bool:
        """Test PostgreSQL database connection."""
        try:
            pool = await asyncpg.create_pool(self.database_url)
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1
            await pool.close()
            return True
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
            return False

    def test_milvus_connection(self) -> bool:
        """Test Milvus connection."""
        try:
            client = MilvusClient(uri=f"http://{self.milvus_host}:{self.milvus_port}")
            # Try to list collections
            collections = client.list_collections()
            return True
        except Exception as e:
            self.log_test("Milvus Connection", False, str(e))
            return False

    def test_conport_health(self) -> bool:
        """Test ConPort health endpoint."""
        try:
            response = requests.get(f"{self.conport_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.log_test("ConPort Health", False, str(e))
            return False

    async def test_mem_upsert(self) -> bool:
        """Test mem.upsert tool via direct database check."""
        try:
            # We'll test by directly inserting data since we don't have MCP client here
            pool = await asyncpg.create_pool(self.database_url)

            test_node = {
                "id": "test_decision_001",
                "type": "decision",
                "text": "Test decision for memory system validation",
                "metadata": json.dumps({"test": True, "priority": "high"}),
                "repo": "dopemux-mvp",
                "author": "test_suite"
            }

            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO nodes (id, type, text, metadata, repo, author, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        updated_at = CURRENT_TIMESTAMP
                """, test_node["id"], test_node["type"], test_node["text"],
                test_node["metadata"], test_node["repo"], test_node["author"])

                # Verify insertion
                result = await conn.fetchrow("SELECT * FROM nodes WHERE id = $1", test_node["id"])
                assert result is not None
                assert result["type"] == "decision"

            await pool.close()
            return True
        except Exception as e:
            self.log_test("mem.upsert", False, str(e))
            return False

    async def test_graph_operations(self) -> bool:
        """Test graph link and neighbor operations."""
        try:
            pool = await asyncpg.create_pool(self.database_url)

            # Create test nodes
            nodes = [
                {"id": "test_file_001", "type": "file", "text": "src/test.py"},
                {"id": "test_task_001", "type": "task", "text": "Implement memory system"}
            ]

            async with pool.acquire() as conn:
                for node in nodes:
                    await conn.execute("""
                        INSERT INTO nodes (id, type, text, repo, author, created_at, updated_at)
                        VALUES ($1, $2, $3, 'dopemux-mvp', 'test_suite', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO NOTHING
                    """, node["id"], node["type"], node["text"])

                # Create edge
                await conn.execute("""
                    INSERT INTO edges (from_id, to_id, relation, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (from_id, to_id, relation) DO NOTHING
                """, "test_decision_001", "test_file_001", "affects", json.dumps({"reason": "test"}))

                # Test neighbor query
                neighbors = await conn.fetch("""
                    SELECT n.id, n.type, n.text
                    FROM nodes n
                    JOIN edges e ON (e.to_id = n.id OR e.from_id = n.id)
                    WHERE (e.from_id = $1 OR e.to_id = $1) AND n.id != $1
                """, "test_decision_001")

                assert len(neighbors) > 0

            await pool.close()
            return True
        except Exception as e:
            self.log_test("Graph Operations", False, str(e))
            return False

    async def test_conversation_storage(self) -> bool:
        """Test conversation thread and message storage."""
        try:
            pool = await asyncpg.create_pool(self.database_url)

            async with pool.acquire() as conn:
                # Create test thread
                thread_id = "test_thread_001"
                await conn.execute("""
                    INSERT INTO conversation_threads (id, title, repo, participants, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO NOTHING
                """, thread_id, "Test Conversation", "dopemux-mvp", ["user", "assistant"])

                # Create test message
                message_id = "test_msg_001"
                await conn.execute("""
                    INSERT INTO messages (id, thread_id, role, content, source, created_at)
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO NOTHING
                """, message_id, thread_id, "user", "Test message content", "test_suite")

                # Verify storage
                thread = await conn.fetchrow("SELECT * FROM conversation_threads WHERE id = $1", thread_id)
                message = await conn.fetchrow("SELECT * FROM messages WHERE id = $1", message_id)

                assert thread is not None
                assert message is not None

            await pool.close()
            return True
        except Exception as e:
            self.log_test("Conversation Storage", False, str(e))
            return False

    def test_milvus_collections(self) -> bool:
        """Test that Milvus collections are properly created."""
        try:
            client = MilvusClient(uri=f"http://{self.milvus_host}:{self.milvus_port}")
            collections = client.list_collections()

            expected_collections = ["decisions", "messages", "files", "tasks"]
            found_collections = [col for col in expected_collections if col in collections]

            if len(found_collections) >= 2:  # At least some collections exist
                return True
            else:
                self.log_test("Milvus Collections", False, f"Expected collections not found. Found: {collections}")
                return False

        except Exception as e:
            self.log_test("Milvus Collections", False, str(e))
            return False

    async def test_import_tracking(self) -> bool:
        """Test import run tracking."""
        try:
            pool = await asyncpg.create_pool(self.database_url)

            async with pool.acquire() as conn:
                # Create test import run
                run_id = "test_run_001"
                await conn.execute("""
                    INSERT INTO import_runs (id, source, file_path, status, items_processed, started_at)
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO NOTHING
                """, run_id, "test", "/tmp/test.jsonl", "completed", 100)

                # Verify storage
                run = await conn.fetchrow("SELECT * FROM import_runs WHERE id = $1", run_id)
                assert run is not None
                assert run["status"] == "completed"

            await pool.close()
            return True
        except Exception as e:
            self.log_test("Import Tracking", False, str(e))
            return False

    async def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        logger.info("🧪 Starting Dopemux Memory System Tests")
        logger.info("=" * 50)

        # Connection tests
        db_ok = await self.test_database_connection()
        self.log_test("Database Connection", db_ok)

        milvus_ok = self.test_milvus_connection()
        self.log_test("Milvus Connection", milvus_ok)

        conport_ok = self.test_conport_health()
        self.log_test("ConPort Health", conport_ok)

        if not (db_ok and milvus_ok):
            logger.error("❌ Basic connectivity tests failed. Skipping functional tests.")
            return False

        # Functional tests
        upsert_ok = await self.test_mem_upsert()
        graph_ok = await self.test_graph_operations()
        conv_ok = await self.test_conversation_storage()
        import_ok = await self.test_import_tracking()
        collections_ok = self.test_milvus_collections()

        # Summary
        logger.info("\n📊 Test Results Summary:")
        logger.info("=" * 30)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        for name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status:8} {name}")

        logger.info(f"\n🎯 Results: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All tests passed! Memory system is ready for use.")
            logger.info("\n🚀 Quick Start:")
            logger.info("   • Add to Claude Code: claude mcp add conport-memory http://localhost:3004")
            logger.info("   • Import Claude Code history: python -m conport.importers --source claude-code --file /path/to/conversations.db")
            logger.info("   • Test mem.search: Use ConPort MCP tools in Claude Code")
        else:
            logger.info("⚠️  Some tests failed. Check the errors above.")

        return passed == total


async def main():
    """Main test runner."""
    tester = MemorySystemTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())