"""In-process wiring, authenticated receipts and immutable kernel evidence."""

import base64
import hashlib
import importlib
import importlib.util
from pathlib import Path

import httpx
import pytest

from dopemux.pm.ownership import canonical_json
from tests.unit.pm.test_ownership_store import (
    create,
    create_body,
    command,
    principal,
    read,
    transition,
)
from tests.unit.pm import test_ownership_store as store_support

env = store_support.env
modules = store_support.modules


@pytest.fixture
def runtime_module():
    assert importlib.util.find_spec("dopemux.pm.runtime"), "canonical runtime unavailable"
    return importlib.import_module("dopemux.pm.runtime")


class FixtureVerifier:
    def __init__(self, p):
        self.p = p
        self.calls = 0

    def verify(self, *, project_id, operation, body, credential):
        self.calls += 1
        if credential != "Bearer fixture":
            raise PermissionError("bad credential")
        return principal(self.p, project_id, operation, body)


@pytest.mark.asyncio
async def test_asgi_lifespan_exact_store_and_replay(env, runtime_module):
    s, p, *_ = env
    verifier = FixtureVerifier(p)
    runtime = runtime_module.CanonicalTaskRuntime(s, principal_verifier=verifier)
    app = runtime_module.create_runtime_app(lambda: runtime)
    async with app.router.lifespan_context(app):
        assert app.state.task_runtime is runtime
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://fixture"
        ) as c:
            headers = {"Authorization": "Bearer fixture"}
            created = await c.post(
                "/api/v2/projects/prj_a/workflow/tasks", json=create_body(), headers=headers
            )
            assert created.status_code == 200, created.text
            tid = created.json()["task_id"]
            body = command(tid)
            result = await c.post(
                "/api/v2/projects/prj_a/workflow/transition", json=body, headers=headers
            )
            assert result.status_code == 200, result.text
            assert read(env, tid)["version"] == 2
            replay = await c.post(
                "/api/v2/projects/prj_a/workflow/transition", json=body, headers=headers
            )
            assert replay.content == result.content
            malformed = await c.post(
                "/api/v2/projects/prj_a/workflow/transition",
                content='{"task_id":"x","task_id":"y"}',
                headers=headers,
            )
            assert malformed.status_code == 422
            bad = await c.post("/api/v2/projects/prj_a/workflow/transition", json=body)
            assert bad.status_code == 401
            foreign = await c.get("/api/v2/projects/prj_b/workflow/tasks/" + tid, headers=headers)
            missing = await c.get("/api/v2/projects/prj_a/workflow/tasks/missing", headers=headers)
            assert foreign.status_code == missing.status_code == 404
            assert foreign.json() == missing.json() == {"detail": "not_found"}


@pytest.mark.asyncio
async def test_missing_composition_and_default_verifier_are_held(env, runtime_module):
    app = runtime_module.create_runtime_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://fixture"
        ) as c:
            assert (
                await c.post("/api/v2/projects/prj_a/workflow/transition", json=command("missing"))
            ).status_code == 503
    rt = runtime_module.CanonicalTaskRuntime(env[0])
    with pytest.raises(env[0].Error):
        rt.transition("prj_a", canonical_json(command("missing")), None)


def test_scoped_view_capabilities_and_restart_projection(env, runtime_module):
    s, p, *_ = env
    tid = create(env)["task_id"]
    blocked = create(env, source="dependent", key="dependent", dependencies=[tid])["task_id"]
    rt = runtime_module.CanonicalTaskRuntime(s, principal_verifier=FixtureVerifier(p))
    view = rt.view("prj_a", credential="Bearer fixture", offset=0, limit=100)
    assert view["total"] == 2
    assert view["state"]["TODO"] == 2
    ready = next(t for t in view["tasks"] if t["task_id"] == tid)
    waiting = next(t for t in view["tasks"] if t["task_id"] == blocked)
    assert ready["allowed_transitions"] == ["start", "block"]
    assert waiting["allowed_transitions"] == ["block"]
    assert waiting["blockers"] == ["dependency_unavailable"]
    with pytest.raises(s.Error) as error:
        rt.view("foreign", credential="Bearer fixture", offset=0, limit=100)
    assert error.value.status == 404


def kernel_snapshot(task, *, empty=False, wrong_task=False, escape=False):
    from dopemux.workflow.models import WorkflowState, WorkflowTask, WorkflowPhase

    state = WorkflowState.new(
        workflow_id="wf_a", workspace_root=Path("/unused"), instance_id="inst_a", mode="test"
    )
    state.tasks = [
        WorkflowTask(task_id=task["task_id"], title="Task", status="done", artifact_dir="artifacts")
    ]
    state.current_task_id = task["task_id"]
    state.phase = WorkflowPhase.REFACTOR
    for phase in ["research_review", "plan_review", "implement", "refactor"]:
        state.record_checkpoint(phase, True, task_id="foreign" if wrong_task else task["task_id"])
    # Kernel implementation gate requires COMPLETE, not APPROVED.
    state.checkpoints[2].status = importlib.import_module(
        "dopemux.workflow.models"
    ).WorkflowCheckpointStatus.COMPLETE
    artifacts = {
        "artifacts/" + name + ".md": base64.b64encode(b"" if empty else b"evidence").decode()
        for name in state.tasks[0].required_artifacts
    }
    if escape:
        artifacts["../outside.md"] = base64.b64encode(b"escape").decode()
    return {
        "schema_version": "dopemux.pm.kernel-snapshot.v1",
        "project_id": task["project_id"],
        "task_id": task["task_id"],
        "task_version": task["version"],
        "identity": task["identity"],
        "source_revision": "fixture-revision",
        "workflow": state.to_dict(),
        "artifacts": artifacts,
    }


@pytest.mark.parametrize("bad", ["empty", "wrong_task", "escape"])
def test_kernel_completion_rejects_unqualified_evidence(env, runtime_module, bad):
    from dopemux.pm.completion import KernelBinding, KernelCompletionVerifier

    tid = create(env)["task_id"]
    transition(env, command(tid))
    task = read(env, tid)
    raw = canonical_json(kernel_snapshot(task, **{bad: True}))
    sha = hashlib.sha256(raw).hexdigest()
    binding = KernelBinding("prj_a", tid, "wf_a", "fixture-revision", "kernel-v1", 1)
    env[0].completion_verifier = KernelCompletionVerifier({"evidence": (binding, raw)})
    body = dict(
        command(tid, "done", 2, "done"), completion_evidence_ref={"id": "evidence", "sha256": sha}
    )
    with pytest.raises(env[0].Error):
        transition(env, body)
    assert read(env, tid)["status"] == "IN_PROGRESS"


@pytest.mark.parametrize("artifact_dir", [None, 7, ["artifacts"]])
def test_kernel_completion_nonstring_directory_denies_without_consuming_key(
    env, artifact_dir
):
    from dopemux.pm.completion import KernelBinding, KernelCompletionVerifier

    s, p, root, bundle = env
    tid = create(env)["task_id"]
    transition(env, command(tid))
    task = read(env, tid)
    snapshot = kernel_snapshot(task)
    snapshot["workflow"]["tasks"][0]["artifact_dir"] = artifact_dir
    binding = KernelBinding("prj_a", tid, "wf_a", "fixture-revision", "kernel-v1", 1)
    raw = canonical_json(snapshot)
    s.completion_verifier = KernelCompletionVerifier({"evidence": (binding, raw)})
    body = dict(
        command(tid, "done", 2, "directory-done"),
        completion_evidence_ref={
            "id": "evidence",
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
    )
    before = s.statistics()
    history = s.replay()
    checkpoint = (root / "checkpoint.jsonl").read_bytes()
    with pytest.raises(s.Error) as denied:
        transition(env, body)
    assert (denied.value.status, denied.value.code) == (409, "completion_unavailable")
    assert read(env, tid) == task
    assert s.statistics() == before
    assert s.replay() == history
    assert (root / "checkpoint.jsonl").read_bytes() == checkpoint
    assert (
        s._db.execute(
            "SELECT count(*) FROM operations WHERE principal=? AND kind=? AND key=?",
            ("alice", "task.transition", "directory-done"),
        ).fetchone()[0]
        == 0
    )

    # Storage-level nonconsumption probe only: callers changing snapshot evidence
    # must use a new intent key rather than retrying changed evidence under this key.
    snapshot["workflow"]["tasks"][0]["artifact_dir"] = "artifacts"
    raw = canonical_json(snapshot)
    s.completion_verifier = KernelCompletionVerifier({"evidence": (binding, raw)})
    body["completion_evidence_ref"]["sha256"] = hashlib.sha256(raw).hexdigest()
    receipt = transition(env, body)
    assert receipt["to_status"] == "DONE" and receipt["version_after"] == 3
    assert transition(env, body) == receipt


def test_kernel_done_sealed_snapshot_unlocks_and_replays(env, runtime_module):
    from dopemux.pm.completion import KernelBinding, KernelCompletionVerifier

    tid = create(env)["task_id"]
    transition(env, command(tid))
    task = read(env, tid)
    snapshot = kernel_snapshot(task)
    raw = canonical_json(snapshot)
    sha = hashlib.sha256(raw).hexdigest()
    env[0].completion_verifier = KernelCompletionVerifier(
        {"evidence": (KernelBinding("prj_a", tid, "wf_a", "fixture-revision", "kernel-v1", 1), raw)}
    )
    snapshot["artifacts"].clear()  # editing producer state cannot change sealed bytes
    body = dict(
        command(tid, "done", 2, "done"), completion_evidence_ref={"id": "evidence", "sha256": sha}
    )
    receipt = transition(env, body)
    assert receipt["completion_verification"]["gate_scope"] == "workflow-kernel:task-evidence-shape"
    assert transition(env, body) == receipt
    dependent = create(env, source="dependent", key="dependent", dependencies=[tid])["task_id"]
    assert transition(env, command(dependent, key="start-dependent"))["to_status"] == "IN_PROGRESS"


def test_adapters_reject_bad_receipts_and_never_cache(env, runtime_module):
    from dopemux.pm.adapters.ownership import SyncOwnershipAdapter

    tid = create(env)["task_id"]
    body = command(tid)
    receipt = transition(env, body)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=receipt)

    adapter = SyncOwnershipAdapter(
        project_id="prj_a",
        writer_instance_id="inst_a",
        endpoint="https://fixture",
        principal_id="alice",
        client_id="client_a",
        credential_supplier=lambda: "Bearer fixture",
        transport=httpx.MockTransport(handler),
    )
    try:
        assert adapter.transition_command(body) == receipt
        assert adapter.transition_command(body) == receipt
        assert len(calls) == 2
        for patch in ({"project_id": "foreign"}, {"outcome": "illegal"}, {"version_after": 999}):
            original = dict(receipt)
            receipt.update(patch)
            with pytest.raises(ValueError):
                adapter.transition_command(body)
            receipt.clear()
            receipt.update(original)
    finally:
        adapter.close()


def test_outbox_order_failure_and_receiver_dedupe(env, runtime_module):
    s, p, *_ = env
    tid = create(env)["task_id"]
    transition(env, command(tid))
    seen = set()
    delivered = []

    class Destination:
        def deliver(self, envelope):
            key = (envelope["project_id"], envelope["event_id"], envelope["destination"])
            if key not in seen:
                seen.add(key)
                delivered.append(envelope["event_sequence"])
            return runtime_module.DeliveryAck(
                envelope["project_id"],
                envelope["event_id"],
                envelope["destination"],
                envelope["event_sha256"],
                True,
            )

    rt = runtime_module.CanonicalTaskRuntime(s, destinations={"mirror": Destination()})
    original = s.record_delivery

    def fail(*args, **kwargs):
        raise OSError("lost acknowledgment")

    s.record_delivery = fail
    result = rt.drain_once()
    assert result["failed"] == 1 and delivered == [2]
    s.record_delivery = original
    assert rt.drain_once()["delivered"] == 2 and delivered == [2, 3]
    assert not s.pending_outbox()


@pytest.mark.asyncio
async def test_legacy_local_writer_denied_before_effect(env, runtime_module):
    from dopemux.pm import write

    class Bomb:
        def transition(self, *args, **kwargs):
            pytest.fail("legacy store was mutated")

        def patch_metadata(self, *args, **kwargs):
            pytest.fail("legacy metadata was mutated")

    with pytest.raises(RuntimeError):
        await write.pm_transition_work_item(
            store=Bomb(),
            task_id="x",
            project_id="prj_a",
            workflow_id="x",
            new_status="DONE",
            expected_version=1,
            idempotency_key="key",
        )
    with pytest.raises(RuntimeError):
        await write.pm_update_work_item(
            store=Bomb(),
            task_id="x",
            patch={"status": "DONE"},
            expected_version=1,
            idempotency_key="key",
        )


@pytest.mark.asyncio
async def test_async_v2_wrapper_consumes_receipt_without_promoting_event(
    env, runtime_module, monkeypatch
):
    from dopemux.pm.adapters.ownership import AsyncOwnershipAdapter
    from dopemux.pm.api import PMWriteBoundary
    from dopemux.pm import write, api

    tid = create(env)["task_id"]
    monkeypatch.setattr(
        api,
        "emit_pm_promotable_source_event",
        lambda *a, **k: pytest.fail("client promoted canonical event"),
    )
    rt = runtime_module.CanonicalTaskRuntime(env[0], principal_verifier=FixtureVerifier(env[1]))
    app = runtime_module.create_runtime_app(lambda: rt)
    async with app.router.lifespan_context(app):
        adapter = AsyncOwnershipAdapter(
            project_id="prj_a",
            writer_instance_id="inst_a",
            endpoint="https://fixture",
            principal_id="alice",
            client_id="client_a",
            credential_supplier=lambda: "Bearer fixture",
            transport=httpx.ASGITransport(app=app),
        )
        try:
            body = command(tid)
            result = await PMWriteBoundary(
                orchestrator_client=adapter, project_id="prj_a"
            ).pm_transition_work_item(tid, "start", body)
            assert result["version_after"] == 2
            assert await write.pm_transition_command(adapter=adapter, command=body) == result
        finally:
            await adapter.close()


def test_outbox_rejects_spoofed_ack_and_serializes_pumps(env, runtime_module):
    create(env)
    calls = []
    nested = []

    class Adapter:
        def deliver(self, envelope):
            calls.append(envelope["event_id"])
            if len(calls) == 1:
                nested.append(rt.drain_once())
            return runtime_module.DeliveryAck(
                "foreign", envelope["event_id"], "mirror", envelope["event_sha256"], True
            )

    rt = runtime_module.CanonicalTaskRuntime(env[0], destinations={"mirror": Adapter()})
    assert rt.drain_once() == {"delivered": 0, "failed": 1}
    assert len(calls) == 1
    assert nested == [{"delivered": 0, "failed": 0, "busy": True}]
    assert len(env[0].pending_outbox()) == 1


def test_completed_workflow_snapshot_requires_workflow_artifacts(env, runtime_module):
    from dopemux.pm.completion import KernelBinding, KernelCompletionVerifier

    tid = create(env)["task_id"]
    transition(env, command(tid))
    task = read(env, tid)
    snapshot = kernel_snapshot(task)
    snapshot["workflow"].update(
        phase="complete", status="complete", required_artifacts=["summary.md"]
    )
    binding = KernelBinding(
        "prj_a",
        tid,
        "wf_a",
        "fixture-revision",
        "kernel-v1",
        1,
        required_workflow_artifacts=("summary.md",),
        workflow_scope=True,
    )
    for present in (False, True):
        if present:
            snapshot["artifacts"]["summary.md"] = base64.b64encode(b"summary evidence").decode()
        raw = canonical_json(snapshot)
        sha = hashlib.sha256(raw).hexdigest()
        env[0].completion_verifier = KernelCompletionVerifier({"workflow": (binding, raw)})
        body = dict(
            command(tid, "done", 2, "workflow-done"),
            completion_evidence_ref={"id": "workflow", "sha256": sha},
        )
        if present:
            assert (
                transition(env, body)["completion_verification"]["gate_scope"]
                == "workflow-kernel:workflow-evidence-shape"
            )
        else:
            with pytest.raises(env[0].Error):
                transition(env, body)


def test_runtime_shutdown_drains_existing_delivery_and_rejects_new_work(env, runtime_module):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    tid = create(env)["task_id"]
    delivering, release, closing, closed = (Event() for _ in range(4))

    class Destination:
        def deliver(self, envelope):
            delivering.set()
            assert release.wait(5), "fixture delivery not released"
            return runtime_module.DeliveryAck(
                envelope["project_id"],
                envelope["event_id"],
                envelope["destination"],
                envelope["event_sha256"],
                True,
            )

    runtime = runtime_module.CanonicalTaskRuntime(
        env[0],
        principal_verifier=FixtureVerifier(env[1]),
        destinations={"mirror": Destination()},
    )

    def close():
        closing.set()
        try:
            runtime.close()
        finally:
            closed.set()

    with ThreadPoolExecutor(2) as pool:
        delivery = pool.submit(runtime.drain_once)
        assert delivering.wait(5)
        shutdown = pool.submit(close)
        assert closing.wait(5)
        try:
            assert not closed.wait(0.1), "runtime closed before in-flight delivery finished"
            with pytest.raises(env[0].Error):
                runtime.transition("prj_a", canonical_json(command(tid)), "Bearer fixture")
            with pytest.raises(env[0].Error):
                runtime.drain_once()
        finally:
            release.set()
        assert delivery.result(timeout=5) == {"delivered": 1, "failed": 0}
        shutdown.result(timeout=5)
    with pytest.raises(env[0].Error):
        runtime.drain_once()


@pytest.mark.parametrize(
    "field,value",
    [
        ("artifacts", None),
        ("artifacts", []),
        ("artifacts", {"artifacts/research.md": 7}),
        ("artifacts", {"artifacts/research.md": "%%%"}),
        ("workflow", None),
        ("workflow", []),
        ("tasks", None),
        ("tasks", {}),
        ("tasks", [None]),
        ("tasks", [{}]),
        ("checkpoints", None),
        ("checkpoints", {}),
        ("checkpoints", [None]),
        ("checkpoints", [{}]),
        ("required_artifacts", None),
        ("required_artifacts", "research"),
        ("required_artifacts", [7]),
        ("task.required_artifacts", None),
        ("task.required_artifacts", []),
        ("task.required_artifacts", [7]),
        ("task.task_id", []),
        ("task.metadata", None),
        ("task.verification_commands", None),
        ("checkpoint.metadata", None),
        ("checkpoint.phase", []),
        ("checkpoint.task_id", []),
        ("iteration", None),
        ("current_task_id", []),
        ("history", None),
    ],
)
def test_kernel_nested_shapes_deny_without_consuming_key(env, field, value):
    """Malformed sealed input must not escape typed denial or become coerced proof."""
    from dopemux.pm.completion import KernelBinding, KernelCompletionVerifier

    s, p, root, bundle = env
    tid = create(env)["task_id"]
    transition(env, command(tid))
    task = read(env, tid)
    snapshot = kernel_snapshot(task)
    if field in {"artifacts", "workflow"}:
        snapshot[field] = value
    elif field.startswith("task."):
        snapshot["workflow"]["tasks"][0][field.split(".")[1]] = value
    elif field.startswith("checkpoint."):
        snapshot["workflow"]["checkpoints"][0][field.split(".")[1]] = value
    else:
        snapshot["workflow"][field] = value
    binding = KernelBinding("prj_a", tid, "wf_a", "fixture-revision", "kernel-v1", 1)
    raw = canonical_json(snapshot)
    verifier = KernelCompletionVerifier({"evidence": (binding, raw)})
    s.completion_verifier = verifier
    body = dict(
        command(tid, "done", 2, "shape-done"),
        completion_evidence_ref={
            "id": "evidence",
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
    )
    history, counts = s.replay(), s.statistics()
    checkpoint = (root / "checkpoint.jsonl").read_bytes()
    with pytest.raises(ValueError):
        verifier.verify(
            project_id="prj_a",
            task=task,
            reference=body["completion_evidence_ref"],
            policy=bundle["completion_policies"][0],
        )
    with pytest.raises(s.Error) as denied:
        transition(env, body)
    assert (denied.value.status, denied.value.code) == (409, "completion_unavailable")
    assert s.replay() == history and s.statistics() == counts
    assert (
        read(env, tid) == task
        and (root / "checkpoint.jsonl").read_bytes() == checkpoint
    )
    valid = canonical_json(kernel_snapshot(task))
    s.completion_verifier = KernelCompletionVerifier({"evidence": (binding, valid)})
    body["completion_evidence_ref"]["sha256"] = hashlib.sha256(valid).hexdigest()
    receipt = transition(env, body)
    assert receipt["to_status"] == "DONE"
    assert transition(env, body) == receipt


def test_unexpected_injected_verifier_bug_is_not_normalized(env):
    """Typed input denial must not hide arbitrary trusted-verifier defects."""
    s = env[0]
    tid = create(env)["task_id"]
    transition(env, command(tid))

    class BrokenVerifier:
        def verify(self, **kwargs):
            raise TypeError("injected verifier defect")

    s.completion_verifier = BrokenVerifier()
    before = s.statistics()
    body = dict(
        command(tid, "done", 2, "bug-done"),
        completion_evidence_ref={"id": "evidence", "sha256": "1" * 64},
    )
    with pytest.raises(TypeError, match="injected verifier defect"):
        transition(env, body)
    assert s.statistics() == before
