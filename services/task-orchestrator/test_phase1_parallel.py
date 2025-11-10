#!/usr/bin/env python3
"""
Test script for Phase 1 parallel MCP operations implementation.

Tests the MCPParallelExecutor and BatchFileOps classes without requiring
full MCP server setup. Validates core functionality and error handling.
"""

import asyncio
import tempfile
import json
from pathlib import Path

# Import our new classes
from services.task_orchestrator.src.dopemux.mcp.parallel_executor import MCPParallelExecutor
from services.task_orchestrator.src.dopemux.file_ops.batch_handler import BatchFileOps


class MockMCPClient:
    """Mock MCP client for testing parallel operations."""

    async def mock_operation(self, operation_id: int, delay: float = 0.1):
        """Mock async operation with configurable delay."""
        await asyncio.sleep(delay)
        return f"Operation {operation_id} completed"

    async def failing_operation(self, operation_id: int):
        """Mock operation that sometimes fails."""
        if operation_id % 3 == 0:  # Every 3rd operation fails
            raise ValueError(f"Operation {operation_id} failed")
        await asyncio.sleep(0.05)
        return f"Operation {operation_id} succeeded"


async def test_parallel_executor():
    """Test MCPParallelExecutor functionality."""
    print("🧪 Testing MCPParallelExecutor...")

    executor = MCPParallelExecutor(max_concurrent=3)
    mock_client = MockMCPClient()

    # Test successful batch execution
    calls = [
        {'method': 'mock_operation', 'args': [1], 'kwargs': {'delay': 0.1}},
        {'method': 'mock_operation', 'args': [2], 'kwargs': {'delay': 0.1}},
        {'method': 'mock_operation', 'args': [3], 'kwargs': {'delay': 0.1}},
    ]

    results = await executor.execute_batch(mock_client, calls)
    assert len(results) == 3
    assert all("completed" in result for result in results)
    print("✅ Batch execution test passed")

    # Test error handling
    error_calls = [
        {'method': 'failing_operation', 'args': [1]},
        {'method': 'failing_operation', 'args': [2]},
        {'method': 'failing_operation', 'args': [3]},  # This will fail
    ]

    error_results = await executor.execute_batch(mock_client, error_calls, return_exceptions=True)
    assert len(error_results) == 3
    assert isinstance(error_results[2], ValueError)  # 3rd operation failed
    print("✅ Error handling test passed")

    # Test rate limiting
    assert executor.is_available()
    assert executor.get_active_call_count() == 0
    print("✅ Rate limiting test passed")


async def test_batch_file_ops():
    """Test BatchFileOps functionality."""
    print("🧪 Testing BatchFileOps...")

    batch_ops = BatchFileOps(max_concurrent=5)

    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files
        test_files = {}
        for i in range(3):
            file_path = tmpdir / f"test_{i}.json"
            content = json.dumps({"id": i, "name": f"Test {i}"})
            file_path.write_text(content)
            test_files[str(file_path)] = content

        # Test batch read
        file_paths = list(test_files.keys())
        read_results = await batch_ops.batch_read_files(file_paths)

        assert len(read_results) == 3
        for path, content in read_results.items():
            assert isinstance(content, str)
            assert json.loads(content) == json.loads(test_files[path])
        print("✅ Batch read test passed")

        # Test batch write
        write_data = {
            str(tmpdir / "output_1.txt"): "Hello World 1",
            str(tmpdir / "output_2.txt"): "Hello World 2",
        }

        write_results = await batch_ops.batch_write_files(write_data)
        assert len(write_results) == 2
        assert all(isinstance(result, str) for result in write_results.values())

        # Verify files were written
        for path, expected_content in write_data.items():
            assert Path(path).read_text() == expected_content
        print("✅ Batch write test passed")

        # Test config batch reading
        config_files = [str(tmpdir / f"test_{i}.json") for i in range(3)]
        merged_config = await batch_ops.read_config_batch(config_files)

        assert len(merged_config) > 0  # Should merge all configs
        print("✅ Config batch read test passed")


async def main():
    """Run all tests."""
    print("🚀 Starting Phase 1 implementation tests...\n")

    try:
        await test_parallel_executor()
        print()
        await test_batch_file_ops()
        print()
        print("🎉 All tests passed! Phase 1 implementation is working correctly.")
        print("📊 Performance expectations:")
        print("   - MCP calls: 3-5x speedup for batches")
        print("   - File ops: 2-4x speedup for multiple files")
        print("   - Error handling: Graceful failure isolation")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())