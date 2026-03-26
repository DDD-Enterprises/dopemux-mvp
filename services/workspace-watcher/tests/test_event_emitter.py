import pytest

import event_emitter as emitter_module
from event_emitter import WorkspaceSwitchEmitter


class FakeEventBus:
    def __init__(self, redis_url=None):
        self.redis_url = redis_url
        self.published = []

    async def initialize(self):
        return None

    async def publish(self, stream, event):
        self.published.append((stream, event))
        return "1-0"

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_workspace_event_includes_top_level_file_activity(monkeypatch):
    fake_bus = FakeEventBus()

    monkeypatch.setattr(emitter_module, "EventBus", lambda redis_url=None: fake_bus)

    emitter = WorkspaceSwitchEmitter(redis_url="redis://test")
    await emitter.initialize()

    result = await emitter.emit_workspace_switch(
        from_workspace="/tmp/one",
        to_workspace="/tmp/two",
        from_app="Terminal",
        to_app="Claude Code",
        file_activity={"files_modified": 2},
    )

    assert result is True
    assert fake_bus.published[0][0] == "dopemux:events"
    event = fake_bus.published[0][1]
    assert event.type == "workspace.switched"
    assert event.data["file_activity"] == {"files_modified": 2}
    assert event.data["adhd_context_capture"]["file_activity"] == {"files_modified": 2}
