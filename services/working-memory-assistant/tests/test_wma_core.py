"""
Comprehensive test suite for Working Memory Assistant core functionality.

Tests cover:
- Snapshot capture and storage
- Context recovery operations
- Memory management and cleanup
- Error handling and edge cases
- Performance benchmarks
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from wma_core import (
    WorkingMemoryAssistant,
    DevelopmentSnapshot,
    SnapshotEngine,
    RecoveryEngine,
    MemoryManager,
    WMAError,
    SnapshotError,
    RecoveryError,
    StorageError,
    ValidationError,
    ConnectionError
)


class TestMemoryManager:
    """Test MemoryManager functionality"""

    @pytest.fixture
    def memory_manager(self):
        """Create MemoryManager instance"""
        return MemoryManager()

    @pytest.mark.asyncio
    async def test_store_and_retrieve_snapshot_memory(self, memory_manager):
        """Test storing and retrieving snapshots in memory"""
        # Create test snapshot
        snapshot = DevelopmentSnapshot(
            id="test-snapshot-1",
            session_id="test-session",
            timestamp=datetime.now(),
            interruption_type="manual",
            current_task="Testing WMA",
            thought_process="Running comprehensive tests",
            energy_level=0.8,
            attention_state="focused"
        )

        # Store snapshot
        store_result = await memory_manager.store_snapshot(snapshot)
        assert store_result["success"] is True
        assert store_result["snapshot_id"] == "test-snapshot-1"
        assert store_result["compression_ratio"] > 0

        # Retrieve snapshot
        retrieved = await memory_manager.retrieve_snapshot("test-snapshot-1")
        assert retrieved is not None
        assert retrieved.id == "test-snapshot-1"
        assert retrieved.current_task == "Testing WMA"

    @pytest.mark.asyncio
    async def test_cleanup_expired_snapshots_memory(self, memory_manager):
        """Test cleanup of expired snapshots in memory"""
        # Create old snapshot (31 days ago)
        old_timestamp = datetime.now() - timedelta(days=31)
        old_snapshot = DevelopmentSnapshot(
            id="old-snapshot",
            session_id="test-session",
            timestamp=old_timestamp,
            interruption_type="manual",
            current_task="Old task"
        )

        # Create recent snapshot
        recent_snapshot = DevelopmentSnapshot(
            id="recent-snapshot",
            session_id="test-session",
            timestamp=datetime.now(),
            interruption_type="manual",
            current_task="Recent task"
        )

        # Store both
        await memory_manager.store_snapshot(old_snapshot)
        await memory_manager.store_snapshot(recent_snapshot)

        # Cleanup expired (30 days max)
        cleanup_result = await memory_manager.cleanup_expired_snapshots(max_age_days=30)
        assert cleanup_result["cleaned_snapshots"] == 1
        assert cleanup_result["remaining_snapshots"] == 1
        assert cleanup_result["storage_type"] == "memory"

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_snapshot(self, memory_manager):
        """Test retrieving non-existent snapshot raises error"""
        with pytest.raises(StorageError) as exc_info:
            await memory_manager.retrieve_snapshot("nonexistent-snapshot")

        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.storage_type == "memory"

    @pytest.mark.asyncio
    async def test_invalid_snapshot_id_validation(self, memory_manager):
        """Test validation of empty snapshot ID"""
        with pytest.raises(ValidationError) as exc_info:
            await memory_manager.retrieve_snapshot("")

        assert exc_info.value.field == "snapshot_id"


class TestSnapshotEngine:
    """Test SnapshotEngine functionality"""

    @pytest.fixture
    def snapshot_engine(self):
        """Create SnapshotEngine instance"""
        return SnapshotEngine()

    @pytest.mark.asyncio
    async def test_capture_snapshot(self, snapshot_engine):
        """Test basic snapshot capture"""
        result = await snapshot_engine.capture_snapshot("manual")
        assert result.success is True
        assert result.snapshot_id.startswith("snapshot_")
        assert result.capture_time_ms > 0
        assert result.data_size_bytes > 0
        assert result.compression_ratio > 0

    @pytest.mark.asyncio
    async def test_get_latest_snapshot_empty(self, snapshot_engine):
        """Test getting latest snapshot when none exist"""
        with pytest.raises(StorageError) as exc_info:
            await snapshot_engine.getLatestSnapshot("nonexistent-session")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_session_id_validation(self, snapshot_engine):
        """Test validation of empty session ID"""
        with pytest.raises(ValidationError) as exc_info:
            await snapshot_engine.getLatestSnapshot("")

        assert exc_info.value.field == "session_id"


class TestRecoveryEngine:
    """Test RecoveryEngine functionality"""

    @pytest.fixture
    def recovery_engine(self):
        """Create RecoveryEngine instance"""
        snapshot_engine = SnapshotEngine()
        return RecoveryEngine(snapshot_engine)

    @pytest.mark.asyncio
    async def test_recovery_with_invalid_snapshot(self, recovery_engine):
        """Test recovery with non-existent snapshot"""
        result = await recovery_engine.initiate_recovery("invalid-snapshot")
        assert result.success is False
        assert result.context_restored_percentage == 0.0
        assert result.recovery_time_ms > 0


class TestWorkingMemoryAssistant:
    """Test WorkingMemoryAssistant integration"""

    @pytest.fixture
    def wma(self):
        """Create WMA instance"""
        return WorkingMemoryAssistant()

    @pytest.mark.asyncio
    async def test_initialization(self, wma):
        """Test WMA initialization"""
        await wma.initialize()
        status = wma.get_system_status()
        assert "snapshot_engine" in status
        assert "recovery_engine" in status
        assert "memory_manager" in status

    @pytest.mark.asyncio
    async def test_snapshot_and_recovery_workflow(self, wma):
        """Test complete snapshot and recovery workflow"""
        # Initialize
        await wma.initialize()

        # Trigger snapshot
        snapshot_result = await wma.trigger_snapshot("manual")
        assert snapshot_result.success is True
        snapshot_id = snapshot_result.snapshot_id

        # Attempt recovery
        recovery_result = await wma.instant_recovery(snapshot_id)
        assert recovery_result.success is True
        assert recovery_result.context_restored_percentage >= 0.0
        assert recovery_result.recovery_time_ms > 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, wma):
        """Test session cleanup functionality"""
        await wma.initialize()

        # Create some snapshots first
        await wma.trigger_snapshot("manual")
        await asyncio.sleep(0.1)  # Small delay
        await wma.trigger_snapshot("manual")

        # Test cleanup (should not clean recent sessions)
        cleanup_result = await wma.cleanup_expired_sessions(max_session_age_days=7)
        assert "expired_sessions" in cleanup_result
        assert "cleaned_snapshots" in cleanup_result
        assert "active_sessions" in cleanup_result


class TestErrorHandling:
    """Test error handling and exception hierarchy"""

    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from WMAError"""
        exceptions = [
            WMAError("test", "TEST_ERROR"),
            SnapshotError("snapshot error", "test-snapshot"),
            RecoveryError("recovery error", "detailed"),
            StorageError("storage error", "redis"),
            ValidationError("validation error", "field", "value"),
            ConnectionError("connection error", "redis")
        ]

        for exc in exceptions:
            assert isinstance(exc, WMAError)
            assert hasattr(exc, 'error_code')
            assert hasattr(exc, 'message')
            assert hasattr(exc, 'details')

    def test_error_codes(self):
        """Test that error codes are set correctly"""
        assert WMAError("test").error_code == "WMA_ERROR"
        assert SnapshotError("test").error_code == "SNAPSHOT_ERROR"
        assert RecoveryError("test").error_code == "RECOVERY_ERROR"
        assert StorageError("test").error_code == "STORAGE_ERROR"
        assert ValidationError("test").error_code == "VALIDATION_ERROR"
        assert ConnectionError("test").error_code == "CONNECTION_ERROR"


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    @pytest.fixture
    def wma(self):
        """Create WMA instance for performance testing"""
        return WorkingMemoryAssistant()

    @pytest.mark.asyncio
    async def test_snapshot_performance(self, wma):
        """Benchmark snapshot capture performance"""
        await wma.initialize()

        start_time = time.perf_counter()
        result = await wma.trigger_snapshot("manual")
        capture_time = time.perf_counter() - start_time

        # Should complete within 200ms target
        assert capture_time < 0.2, f"Snapshot took {capture_time:.3f}s, exceeds 200ms target"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_recovery_performance(self, wma):
        """Benchmark recovery performance"""
        await wma.initialize()

        # Create snapshot first
        snapshot_result = await wma.trigger_snapshot("manual")
        assert snapshot_result.success is True

        # Benchmark recovery
        start_time = time.perf_counter()
        recovery_result = await wma.instant_recovery(snapshot_result.snapshot_id)
        recovery_time = time.perf_counter() - start_time

        # Should complete within 2s target
        assert recovery_time < 2.0, f"Recovery took {recovery_time:.3f}s, exceeds 2s target"
        assert recovery_result.success is True

    @pytest.mark.asyncio
    async def test_memory_usage_bounds(self, wma):
        """Test that memory usage stays within bounds"""
        await wma.initialize()

        # Create multiple snapshots
        for i in range(10):
            result = await wma.trigger_snapshot("manual")
            assert result.success is True

        # Check memory usage
        status = wma.get_system_status()
        memory_mb = status["memory_manager"]["memory_usage_mb"]

        # Should stay under 50MB target
        assert memory_mb < 50, f"Memory usage {memory_mb}MB exceeds 50MB target"


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""

    @pytest.fixture
    def wma(self):
        """Create WMA instance for integration testing"""
        return WorkingMemoryAssistant()

    @pytest.mark.asyncio
    async def test_multiple_sessions_workflow(self, wma):
        """Test workflow with multiple sessions"""
        await wma.initialize()

        # Simulate multiple sessions
        session_ids = ["session-1", "session-2", "session-3"]

        snapshots_by_session = {}
        for session_id in session_ids:
            # Manually set session ID (normally would come from context)
            wma.active_session = session_id

            # Create snapshots for this session
            snapshots = []
            for i in range(3):
                result = await wma.trigger_snapshot("manual")
                assert result.success is True
                snapshots.append(result.snapshot_id)

            snapshots_by_session[session_id] = snapshots

        # Verify each session has its snapshots
        total_snapshots = sum(len(snapshots) for snapshots in snapshots_by_session.values())
        status = wma.get_system_status()
        assert status["snapshot_engine"]["total_snapshots_captured"] >= total_snapshots

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, wma):
        """Test error handling and recovery workflow"""
        await wma.initialize()

        # Test with invalid snapshot ID
        recovery_result = await wma.instant_recovery("invalid-snapshot-id")
        assert recovery_result.success is False
        assert recovery_result.context_restored_percentage == 0.0

        # Test with valid snapshot
        snapshot_result = await wma.trigger_snapshot("manual")
        assert snapshot_result.success is True

        recovery_result = await wma.instant_recovery(snapshot_result.snapshot_id)
        assert recovery_result.success is True
        assert recovery_result.context_restored_percentage >= 0.0


if __name__ == "__main__":
    # Run basic smoke test
    print("Running WMA Core smoke tests...")

    async def smoke_test():
        wma = WorkingMemoryAssistant()
        await wma.initialize()

        # Basic snapshot test
        result = await wma.trigger_snapshot("manual")
        if result.success:
            print(f"✅ Snapshot captured: {result.snapshot_id}")

            # Basic recovery test
            recovery = await wma.instant_recovery(result.snapshot_id)
            if recovery.success:
                print(f"✅ Recovery successful: {recovery.recovery_time_ms:.1f}ms")
            else:
                print("❌ Recovery failed")
        else:
            print(f"❌ Snapshot failed: {result.error}")

        print("Smoke test completed!")

    asyncio.run(smoke_test())