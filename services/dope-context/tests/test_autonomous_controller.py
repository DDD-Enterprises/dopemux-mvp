import asyncio
import functools

import pytest
from pathlib import Path

from src.autonomous.autonomous_controller import (
    AutonomousConfig,
    AutonomousController,
)


class DummyWorker:
    def __init__(self, *args, **kwargs):
        self.started = False

    async def start(self):
        self.started = True

    async def stop(self):
        self.started = False

    async def enqueue_changes(self, changed_files):
        return None

    def get_stats(self):
        return {"running": self.started}


class DummyWatchdog:
    def __init__(self, *args, **kwargs):
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def get_status(self):
        return {"running": self.started}


class DummyPeriodic:
    def __init__(self, *args, **kwargs):
        self.started = False

    async def start(self):
        self.started = True

    async def stop(self):
        self.started = False

    async def trigger(self):
        return {}

    def get_stats(self):
        return {"running": self.started}


if not hasattr(pytest.mark, "asyncio"):
    def _asyncio_marker(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))

        return _wrapper

    pytest.mark.asyncio = _asyncio_marker


def test_autonomous_controller_registry_keys(tmp_path, monkeypatch):
    """Ensure controllers register under custom keys for docs/code isolation."""
    async def _run():
        workspace = tmp_path / "repo"
        workspace.mkdir()

        monkeypatch.setattr(
            "src.autonomous.autonomous_controller.IndexingWorker",
            DummyWorker,
        )
        monkeypatch.setattr(
            "src.autonomous.autonomous_controller.WatchdogMonitor",
            DummyWatchdog,
        )
        monkeypatch.setattr(
            "src.autonomous.autonomous_controller.PeriodicSync",
            DummyPeriodic,
        )

        async def noop_index(*args, **kwargs):
            return None

        async def noop_sync(*args, **kwargs):
            return {}

        controller = AutonomousController(
            workspace_path=workspace,
            index_callback=noop_index,
            sync_callback=noop_sync,
            config=AutonomousConfig(),
            registry_key="custom-docs",
        )

        await controller.start()

        active = AutonomousController.get_active_controllers()
        assert "custom-docs" in active
        assert active["custom-docs"] is controller

        await controller.stop()
        active_after = AutonomousController.get_active_controllers()
        assert "custom-docs" not in active_after

    asyncio.run(_run())
