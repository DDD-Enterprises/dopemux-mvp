"""
Integration tests for Sync Manager persistence and loop behavior.

Covers:
- Task mappings save/load cycle
- Conflict storage file creation with content
- Sync loop start/stop invoking sync_all repeatedly
- Initialization health checks across clients
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from core.config import Config
from integrations.sync_manager import (
    LeantimeTaskMasterSyncManager,
    TaskMapping,
    SyncDirection,
)
from integrations.leantime_bridge import LeantimeTask, TaskStatus, TaskPriority
from integrations.taskmaster_bridge import TaskMasterTask


@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_mappings_save_and_load(tmp_path):
    mappings_file = tmp_path / "task_mappings.json"

    config = Config({
        "sync": {
            "mappings_file": str(mappings_file),
        }
    })

    mgr = LeantimeTaskMasterSyncManager(config)

    # Seed a mapping and save
    mapping_key = "lt_123"
    mgr.task_mappings[mapping_key] = TaskMapping(
        leantime_id=123,
        taskmaster_id="tm_abc",
        sync_hash="deadbeef",
        last_sync=datetime.now(),
        conflict_count=2,
        sync_direction=SyncDirection.BIDIRECTIONAL,
    )

    await mgr._save_task_mappings()
    assert mappings_file.exists()
    data = json.loads(mappings_file.read_text())
    assert mapping_key in data
    assert data[mapping_key]["leantime_id"] == 123

    # Load into a fresh manager
    mgr2 = LeantimeTaskMasterSyncManager(config)
    await mgr2._load_task_mappings()
    assert mapping_key in mgr2.task_mappings
    loaded = mgr2.task_mappings[mapping_key]
    assert loaded.leantime_id == 123
    assert loaded.taskmaster_id == "tm_abc"
    assert loaded.conflict_count == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_store_conflict_for_review_creates_file(tmp_path):
    conflicts_file = tmp_path / "conflicts.json"
    config = Config({
        "sync": {
            "conflicts_file": str(conflicts_file)
        }
    })

    mgr = LeantimeTaskMasterSyncManager(config)

    lt_task = LeantimeTask(
        id=1,
        headline="Test LT",
        description="LT Desc",
        project_id=10,
        status=TaskStatus.PENDING,
        priority=TaskPriority.FOCUSED,
    )
    tm_task = TaskMasterTask(
        id="tm_1",
        title="Test TM",
        description="TM Desc",
        status="pending",
    )
    mapping = TaskMapping(
        leantime_id=1,
        taskmaster_id="tm_1",
        sync_hash="hash",
        last_sync=datetime.now(),
    )

    await mgr._store_conflict_for_review(lt_task, tm_task, mapping)
    assert conflicts_file.exists()
    conflicts = json.loads(conflicts_file.read_text())
    assert isinstance(conflicts, list) and len(conflicts) == 1
    assert conflicts[0]["mapping"]["leantime_id"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_start_and_stop_sync_loop_invokes_sync_all(monkeypatch):
    config = Config({"sync": {"interval": 0}})  # tick as fast as possible
    mgr = LeantimeTaskMasterSyncManager(config)

    # Inject minimal clients and health
    class Dummy:
        async def health_check(self):
            return {"connected": True}

    mgr.leantime_client = Dummy()
    mgr.taskmaster_client = Dummy()

    calls = {"count": 0}

    async def fake_sync_all():
        calls["count"] += 1
        await asyncio.sleep(0)
        return AsyncMock()

    monkeypatch.setattr(mgr, "sync_all", fake_sync_all)

    task = asyncio.create_task(mgr.start_sync_loop())
    # Allow a couple of iterations
    await asyncio.sleep(0.05)
    await mgr.stop_sync_loop()
    await asyncio.sleep(0)

    # Ensure the loop invoked sync_all
    assert calls["count"] >= 1
    # Cleanup
    task.cancel()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialize_checks_client_health():
    config = Config({})
    mgr = LeantimeTaskMasterSyncManager(config)

    class Ok:
        async def health_check(self):
            return {"connected": True}

    class NotOk:
        async def health_check(self):
            return {"connected": False}

    assert await mgr.initialize(Ok(), Ok()) is True
    assert await mgr.initialize(Ok(), NotOk()) is False
    assert await mgr.initialize(NotOk(), Ok()) is False

