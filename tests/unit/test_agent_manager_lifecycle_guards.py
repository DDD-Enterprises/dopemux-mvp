"""Bounded Fable-generated regression tests; no service launches."""
import threading
import time
from pathlib import Path
from unittest import mock

import pytest

from dopemux import agent_orchestrator


def _make_manager(monkeypatch, litellm):
    """Build an AgentManager wired to a mock LiteLLM manager (no real services)."""
    monkeypatch.setattr(agent_orchestrator, "get_litellm_manager", lambda *a, **k: litellm)
    return agent_orchestrator.AgentManager(project_root=Path("/nonexistent-dopemux-test-root"))


def test_start_fails_closed_and_is_restartable_when_monitoring_start_raises(monkeypatch):
    litellm = mock.Mock()
    litellm.start.side_effect = [RuntimeError("monitor boom"), None]
    mgr = _make_manager(monkeypatch, litellm)

    try:
        with pytest.raises(RuntimeError, match="monitor boom"):
            mgr.start()

        # Fail closed: nothing left running after a failed start.
        assert mgr._running is False
        leaked = mgr._worker_thread
        assert leaked is None or not leaked.is_alive()

        # Restartable: a second start with healthy monitoring succeeds.
        mgr.start()
        assert mgr._running is True
        worker = mgr._worker_thread
        assert worker is not None and worker.is_alive()
        assert litellm.start.call_count == 2

        # Idempotent start.
        mgr.start()
        assert litellm.start.call_count == 2

        mgr.stop()
        worker.join(timeout=1.0)
        assert mgr._running is False
        assert not worker.is_alive()

        # Idempotent stop.
        mgr.stop()
        litellm.stop.assert_called_once()
    finally:
        # Never leak a spinning daemon worker into other tests, even on failure.
        mgr._running = False


def test_stop_does_not_hold_manager_lock_while_joining_worker(monkeypatch):
    litellm = mock.Mock()
    mgr = _make_manager(monkeypatch, litellm)

    release = threading.Event()
    finished = threading.Event()
    # Signal the fake worker once stop() has begun tearing down.
    litellm.stop.side_effect = lambda: release.set()

    def worker_body():
        release.wait(timeout=10.0)
        # The worker needs the manager lock to finish its final iteration.
        with mgr._lock:
            finished.set()

    worker = threading.Thread(target=worker_body, daemon=True, name="FakeAgentWorker")
    mgr._running = True
    mgr._worker_thread = worker
    worker.start()

    t0 = time.monotonic()
    mgr.stop()
    elapsed = time.monotonic() - t0
    worker.join(timeout=1.0)

    assert finished.is_set()
    assert not worker.is_alive()
    # Pinned code holds the lock across join(timeout=5.0), so stop() stalls ~5s.
    assert elapsed < 2.0, f"stop() blocked for {elapsed:.2f}s while worker waited on the lock"
    assert mgr._running is False
    litellm.stop.assert_called_once()

    # Idempotent stop.
    mgr.stop()
    litellm.stop.assert_called_once()


# --- MP021 audit repairs (F1/F2/F3) ----------------------------------------


def _make_logged_litellm(call_log):
    """Mock LiteLLM manager whose start/stop append to ``call_log``."""
    litellm = mock.Mock()
    litellm.start.side_effect = lambda: call_log.append("start")
    litellm.stop.side_effect = lambda: call_log.append("stop")
    return litellm


def test_f1_start_during_teardown_waits_and_old_generation_exits(monkeypatch):
    """F1: start() overlapping stop()'s teardown waits for teardown to end.

    Afterwards the manager runs with monitoring ACTIVE (last LiteLLM call is
    ``start``) and the old worker generation has exited.
    """
    call_log = []
    litellm = _make_logged_litellm(call_log)
    teardown_entered = threading.Event()
    release_teardown = threading.Event()

    def slow_stop():
        call_log.append("stop")
        teardown_entered.set()
        assert release_teardown.wait(timeout=10.0), "teardown never released"

    litellm.stop.side_effect = slow_stop
    mgr = _make_manager(monkeypatch, litellm)

    start_done = threading.Event()
    start_error = []

    def concurrent_start():
        try:
            mgr.start()
        except Exception as exc:  # pragma: no cover - surfaced via assertion
            start_error.append(exc)
        finally:
            start_done.set()

    stopper = threading.Thread(target=mgr.stop, daemon=True, name="Stopper")
    starter = threading.Thread(
        target=concurrent_start, daemon=True, name="Starter"
    )
    try:
        mgr.start()
        gen1 = mgr._worker_thread
        assert gen1 is not None and gen1.is_alive()

        stopper.start()
        assert teardown_entered.wait(timeout=5.0), "stop() never hit teardown"

        starter.start()
        # start() must block while teardown is still in progress.
        assert not start_done.wait(timeout=0.3), (
            "start() proceeded during stop() teardown"
        )
        assert call_log == ["start", "stop"]

        release_teardown.set()
        stopper.join(timeout=10.0)
        assert start_done.wait(timeout=10.0), "start() never completed"
        assert not start_error, start_error

        # Monitoring active under the new generation: the restart's start()
        # happened strictly AFTER the original stop()'s teardown.
        assert call_log == ["start", "stop", "start"]
        assert mgr._running is True
        gen2 = mgr._worker_thread
        assert gen2 is not None and gen2 is not gen1 and gen2.is_alive()

        # The old generation exits and does not keep processing.
        gen1.join(timeout=5.0)
        assert not gen1.is_alive(), "old worker generation survived restart"
    finally:
        release_teardown.set()
        mgr._running = False
        stale = mgr._worker_thread
        if stale is not None:
            stale.join(timeout=5.0)


def test_f2_worker_construction_failure_rolls_back_monitoring(monkeypatch):
    """F2: a Thread-constructor failure propagates, stops monitoring once, and
    leaves the manager stopped and restartable."""
    call_log = []
    litellm = _make_logged_litellm(call_log)
    mgr = _make_manager(monkeypatch, litellm)

    real_thread = threading.Thread
    boom = {"armed": True}

    def fault_thread(*args, **kwargs):
        if boom["armed"] and kwargs.get("name") == "AgentOrchestratorWorker":
            raise RuntimeError("thread boom")
        return real_thread(*args, **kwargs)

    monkeypatch.setattr(agent_orchestrator.threading, "Thread", fault_thread)
    try:
        with pytest.raises(RuntimeError, match="thread boom"):
            mgr.start()

        assert call_log == ["start", "stop"], "monitoring not stopped once"
        assert mgr._running is False
        leaked = mgr._worker_thread
        assert leaked is None or not leaked.is_alive()

        # Restartable once the fault clears.
        boom["armed"] = False
        mgr.start()
        assert mgr._running is True
        assert call_log == ["start", "stop", "start"]
        worker = mgr._worker_thread
        assert worker is not None and worker.is_alive()

        mgr.stop()
        worker.join(timeout=5.0)
        assert not worker.is_alive()
        assert call_log == ["start", "stop", "start", "stop"]
    finally:
        mgr._running = False


def test_f2_cleanup_failure_does_not_mask_original_exception(monkeypatch):
    """F2: if rollback cleanup also fails, the ORIGINAL exception wins."""
    litellm = mock.Mock()
    litellm.stop.side_effect = RuntimeError("cleanup boom")
    mgr = _make_manager(monkeypatch, litellm)

    real_thread = threading.Thread

    def fault_thread(*args, **kwargs):
        if kwargs.get("name") == "AgentOrchestratorWorker":
            raise ValueError("thread boom")
        return real_thread(*args, **kwargs)

    monkeypatch.setattr(agent_orchestrator.threading, "Thread", fault_thread)
    with pytest.raises(ValueError, match="thread boom"):
        mgr.start()

    litellm.start.assert_called_once()
    litellm.stop.assert_called_once()
    assert mgr._running is False


def test_f3_worker_reference_retained_after_stop(monkeypatch):
    """F3: the worker reference survives stop() (existing contract)."""
    litellm = mock.Mock()
    mgr = _make_manager(monkeypatch, litellm)
    try:
        mgr.start()
        worker = mgr._worker_thread
        assert worker is not None
        mgr.stop()
        worker.join(timeout=5.0)
        assert not worker.is_alive()
        assert mgr._worker_thread is worker
        assert mgr._running is False
    finally:
        mgr._running = False


def test_f3_start_rejects_while_timed_out_worker_still_alive(monkeypatch):
    """F3: after a timed-out join leaves the old worker alive, start() fails
    closed (raises AgentError, a RuntimeError) instead of launching a second
    concurrently-processing generation; once the old worker exits, start works.
    """
    litellm = mock.Mock()
    mgr = _make_manager(monkeypatch, litellm)

    release = threading.Event()
    stuck = threading.Thread(
        target=lambda: release.wait(timeout=30.0),
        daemon=True,
        name="StuckAgentWorker",
    )
    stuck.start()

    # Model a running generation whose worker will not honour the bounded join.
    mgr._running = True
    mgr._worker_thread = stuck
    mgr._worker_join_timeout = 0.05
    try:
        mgr.stop()
        assert mgr._running is False
        litellm.stop.assert_called_once()
        # Reference retained so the escaped worker remains tracked.
        assert mgr._worker_thread is stuck
        assert stuck.is_alive()

        with pytest.raises(agent_orchestrator.AgentError):
            mgr.start()
        assert isinstance(agent_orchestrator.AgentError("x"), RuntimeError)
        litellm.start.assert_not_called()
        assert mgr._running is False
        assert mgr._worker_thread is stuck

        # Once the old worker is gone, a fresh generation may start.
        release.set()
        stuck.join(timeout=5.0)
        assert not stuck.is_alive()
        mgr.start()
        assert mgr._running is True
        litellm.start.assert_called_once()
        new_worker = mgr._worker_thread
        assert new_worker is not stuck and new_worker.is_alive()
        mgr.stop()
        new_worker.join(timeout=5.0)
        assert not new_worker.is_alive()
    finally:
        release.set()
        mgr._running = False
