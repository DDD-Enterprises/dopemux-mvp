"""Tests for the PM source-event promotion-capable fan-out fix.

Covers TP-DMX-MCP-FLEET-ROADMAP-004-MEMORY-SPINE Step 2 follow-up:

- emit_pm_promotable_source_event now passes emit_event_bus=None (not the
  previously-hardcoded False) so the env/config resolution in
  emit_capture_event can decide, rather than being permanently blocked.
- Default dev environments (env var unset) still resolve to no Redis
  fan-out — this is a promotion-CAPABLE, not promotion-ON-BY-DEFAULT, change.
- rte_adapter.write_decision_to_conport emits a decision.logged capture
  event on success and fails open (never surfaces a capture error) if
  emission raises.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from dopemux.pm import writes as pm_writes
from dopemux.pm.models import PMTaskStatus
from dopemux.pm.writes import PMWriteConfig, pm_transition_work_item


@pytest.fixture(autouse=True)
def _hermetic_capture_ledger(tmp_path, monkeypatch):
    """Redirect the capture ledger to a temp path so tests that exercise the
    real emit path never create/modify ``.dopemux/chronicle.sqlite`` under the
    working tree."""
    monkeypatch.setenv(
        "DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "chronicle.sqlite")
    )


class _RecordingOrchestrator:
    def transition(self, **kwargs):
        return {"status": "success"}


class _RecordingConport:
    def record_progress(self, task_id, progress_notes, is_decision, idempotency_key):
        return None


def test_emit_pm_promotable_source_event_passes_emit_event_bus_none(monkeypatch):
    """The core fix: the hardcoded False must become None (env-deferred)."""

    captured_kwargs: Dict[str, Any] = {}

    def _fake_try_emit(event_type, payload, **kwargs):
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(pm_writes, "try_emit_promotable_capture_event", _fake_try_emit)

    pm_writes.emit_pm_promotable_source_event(
        "decision.logged",
        project_id="proj-1",
        work_item_id="task-1",
        canonical_system="conport",
        operation_type="decision_log",
        payload={"decision_id": "task-1", "title": "t", "rationale": "r"},
    )

    assert "emit_event_bus" in captured_kwargs
    assert captured_kwargs["emit_event_bus"] is None


def test_pm_transition_work_item_uses_emit_event_bus_none_end_to_end(monkeypatch):
    """pm_transition_work_item's downstream emits also carry emit_event_bus=None."""

    captured_calls = []

    def _fake_try_emit(event_type, payload, **kwargs):
        captured_calls.append((event_type, kwargs.get("emit_event_bus")))
        return None

    monkeypatch.setattr(pm_writes, "try_emit_promotable_capture_event", _fake_try_emit)

    config = PMWriteConfig(
        leantime_client=None,
        orchestrator_client=_RecordingOrchestrator(),
        conport_client=None,
        memory_client=None,
        project_id="proj-1",
    )

    pm_transition_work_item(
        config=config,
        task_id="task-1",
        new_status=PMTaskStatus.DONE,
        reason="merged",
        idempotency_key="idem-1",
        expected_version=1,
    )

    assert captured_calls, "expected at least one promotable capture event emit"
    assert all(emit_event_bus is None for _event_type, emit_event_bus in captured_calls)
    event_types = {event_type for event_type, _ in captured_calls}
    assert "workflow.phase_changed" in event_types
    assert "task.completed" in event_types


def test_default_env_resolves_to_no_event_bus_fan_out(monkeypatch):
    """Prove: with DOPEMUX_CAPTURE_EMIT_EVENTBUS unset, no Redis call happens.

    Mocks capture_client's _emit_to_event_stream (the Redis fan-out) to
    detect whether it would have been invoked, while letting
    emit_capture_event run its real env-resolution logic.
    """

    monkeypatch.delenv("DOPEMUX_CAPTURE_EMIT_EVENTBUS", raising=False)

    from dopemux.memory import capture_client as capture_client_module

    redis_calls = []
    monkeypatch.setattr(
        capture_client_module,
        "_emit_to_event_stream",
        lambda event: redis_calls.append(event),
    )

    # Exercise the real emit_capture_event resolution path (emit_event_bus=None)
    # without touching the filesystem ledger by mocking the ledger-writing
    # internals is unnecessary here: emit_pm_promotable_source_event's
    # try_emit_promotable_capture_event already swallows failures, and we
    # only care whether the event-bus branch is taken. We call the resolver
    # logic directly via emit_capture_event with a repo_root pointed at a
    # tmp-like real repo root (resolve_repo_root_strict) is avoided by using
    # the public try_emit wrapper, which is exception-safe end to end.
    monkeypatch.setattr(pm_writes, "try_emit_promotable_capture_event", pm_writes.try_emit_promotable_capture_event)

    pm_writes.emit_pm_promotable_source_event(
        "decision.logged",
        project_id="proj-1",
        work_item_id="task-default-env",
        canonical_system="conport",
        operation_type="decision_log",
        payload={"decision_id": "task-default-env", "title": "t", "rationale": "r"},
    )

    assert redis_calls == []


def test_task_status_capture_events_has_no_failed_mapping():
    """task.failed enum add is deferred (contract risk) — document via test.

    PMTaskStatus has an enforced 5-value invariant (see
    tests/unit/pm/test_pm_models.py) and no FAILED member exists, so
    TASK_STATUS_CAPTURE_EVENTS cannot yet map to "task.failed". This test
    pins that state so a future contract-reviewed enum change is a
    deliberate, visible diff here.
    """

    assert "task.failed" not in pm_writes.TASK_STATUS_CAPTURE_EVENTS.values()
    assert not hasattr(PMTaskStatus, "FAILED")


@pytest.mark.asyncio
async def test_rte_adapter_emits_decision_logged_on_success(monkeypatch):
    from dopemux.adhd import rte_adapter as rte_adapter_module

    captured = []

    def _fake_try_emit(event_type, payload, **kwargs):
        captured.append((event_type, payload, kwargs))
        return None

    monkeypatch.setattr(rte_adapter_module, "try_emit_promotable_capture_event", _fake_try_emit)

    adapter = rte_adapter_module.RTEAdapter(workspace_root=Path("/tmp/does-not-matter"))

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"decision_id": "dec-123"}

    class _FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def post(self, url, json, timeout):
            return _FakeResponse()

    monkeypatch.setattr(rte_adapter_module.httpx, "AsyncClient", lambda: _FakeAsyncClient())

    result = await adapter.write_decision_to_conport(
        {"title": "RTE Truth Decomposed", "rationale": "Automated breakdown"}
    )

    assert result == {"decision_id": "dec-123"}
    assert len(captured) == 1
    event_type, payload, kwargs = captured[0]
    assert event_type == "decision.logged"
    assert payload["decision_id"] == "dec-123"
    assert payload["title"] == "RTE Truth Decomposed"
    assert payload["rationale"] == "Automated breakdown"
    assert kwargs["emit_event_bus"] is None
    # capture must resolve against the adapter's workspace, not the process cwd
    assert kwargs["repo_root"] == Path("/tmp/does-not-matter")


@pytest.mark.asyncio
async def test_rte_adapter_swallows_capture_errors_fail_open(monkeypatch):
    """A capture-emit failure must never surface as a ConPort write failure."""

    from dopemux.adhd import rte_adapter as rte_adapter_module

    def _raising_try_emit(*args, **kwargs):
        raise RuntimeError("capture backend exploded")

    monkeypatch.setattr(rte_adapter_module, "try_emit_promotable_capture_event", _raising_try_emit)

    adapter = rte_adapter_module.RTEAdapter(workspace_root=Path("/tmp/does-not-matter"))

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"decision_id": "dec-456"}

    class _FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def post(self, url, json, timeout):
            return _FakeResponse()

    monkeypatch.setattr(rte_adapter_module.httpx, "AsyncClient", lambda: _FakeAsyncClient())

    # Must not raise even though try_emit_promotable_capture_event raises.
    result = await adapter.write_decision_to_conport({"title": "x", "rationale": "y"})
    assert result == {"decision_id": "dec-456"}
