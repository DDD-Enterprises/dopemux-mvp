"""Temporary-only durable writer falsification suite."""

import hashlib
import importlib
import importlib.util
import json
import sqlite3
import time
import uuid
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

import pytest

from dopemux.pm.ownership import canonical_json


def seal(path, value):
    raw = canonical_json(value)
    path.write_bytes(raw)
    path.chmod(0o600)
    return hashlib.sha256(raw).hexdigest()


def admission_fixture(root, project="prj_a"):
    root.mkdir(exist_ok=True, mode=0o700)
    root.chmod(0o700)
    registry = {
        "schema_version": "dopemux.mcp.identity-registry.v1",
        "generation": 3,
        "updated_at": "2026-11-04T00:00:00Z",
        "projects": {
            project: {
                "project_id": project,
                "aliases": [],
                "workspaces": {
                    "ws_a": {
                        "workspace_id": "ws_a",
                        "aliases": [],
                        "instances": {"inst_a": {"instance_id": "inst_a", "aliases": []}},
                    }
                },
            }
        },
    }
    digest = seal(root / "registry.json", registry)
    source = {
        "source_system": "dopemux",
        "source_instance_id": "producer_a",
        "external_project_id": project,
        "producer_principal_ids": ["alice"],
    }
    bundle = {
        "schema_version": "dopemux.pm.admission-bundle.v1",
        "idempotency_key": "bootstrap",
        "project_id": project,
        "workspace_id": "ws_a",
        "instance_id": "inst_a",
        "admission_id": "admission_a",
        "expected_epoch": 0,
        "store_uuid": "store_a",
        "status": "ACTIVE",
        "registry_path": str(root / "registry.json"),
        "registry_sha256": digest,
        "registry_generation": 3,
        "operator_decision_ref": "fixture-approval",
        "created_at_utc": "2026-11-04T00:00:00Z",
        "sources": [source],
        "grants": [
            {
                "principal_id": "alice",
                "client_ids": ["client_a", "client_b"],
                "verifier_ids": ["fixture"],
                "credential_generations": ["generation_1", "generation_2"],
                "actions": [
                    "task.read",
                    "task.create",
                    "task.transition.start",
                    "task.transition.block",
                    "task.transition.resume",
                    "task.transition.done",
                ],
            }
        ],
        "completion_policies": [{"id": "kernel-v1", "version": 1, "kind": "workflow-kernel-v1"}],
        "destinations": ["mirror"],
        "inventory": {
            "schema_version": "dopemux.pm.allocation-inventory.v1",
            "revision": 1,
            "complete": True,
            "composite_consumers_qualified": True,
            "admissions": [project],
            "sources": [
                {
                    "project_id": project,
                    **{k: v for k, v in source.items() if k != "producer_principal_ids"},
                }
            ],
            "legacy_allocations": [],
        },
    }
    seal(root / "bundle.json", bundle)
    return bundle


@pytest.fixture
def modules():
    assert importlib.util.find_spec("dopemux.pm.sqlite_store"), "durable writer unavailable"
    return importlib.import_module("dopemux.pm.sqlite_store"), importlib.import_module(
        "dopemux.pm.principal"
    )


@pytest.fixture
def env(tmp_path, modules):
    m, p = modules
    root = tmp_path / "store"
    bundle = admission_fixture(root)
    digest = seal(root / "bundle.json", bundle)
    m.SQLiteTaskStore.bootstrap(
        root / "tasks.db", root / "checkpoint.jsonl", root / "bundle.json", digest
    )
    store = m.SQLiteTaskStore(root / "tasks.db", root / "checkpoint.jsonl")
    yield store, p, root, bundle
    store.close()


def principal(p, project, kind, body, **overrides):
    values = dict(
        principal_id="alice",
        client_id="client_a",
        verifier_id="fixture",
        credential_generation="generation_1",
        audience="dopemux.pm:inst_a:" + project,
        expires_at=time.time() + 300,
        request_binding=p.request_binding(project, kind, body),
    )
    values.update(overrides)
    return p.VerifiedPrincipal(**values)


def create_body(project="prj_a", source="stable-create-uuid", key="create", dependencies=None):
    return dict(
        schema_version="dopemux.pm.create-command.v1",
        idempotency_key=key,
        admission_epoch=1,
        identity=dict(
            project_id=project,
            source_system="dopemux",
            source_instance_id="producer_a",
            source_task_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, source)),
        ),
        title="Task",
        description=None,
        dependencies=dependencies or [],
        linked_ids={"ticket": "42"},
        completion_policy_id="kernel-v1",
    )


def create(env, **kwargs):
    s, p, *_ = env
    body = create_body(**kwargs)
    return s.create("prj_a", body, principal(p, "prj_a", "task.create", body))


def command(task_id, transition="start", version=1, key="start", epoch=1):
    return dict(
        schema_version="dopemux.pm.transition-command.v1",
        task_id=task_id,
        transition=transition,
        expected_version=version,
        expected_binding_version=1,
        admission_epoch=epoch,
        idempotency_key=key,
        reason="fixture intent",
        completion_evidence_ref=None,
    )


def transition(env, body, **overrides):
    s, p, *_ = env
    return s.transition("prj_a", body, principal(p, "prj_a", "task.transition", body, **overrides))


def read(env, task_id):
    s, p, *_ = env
    body = {"task_id": task_id}
    return s.get_task("prj_a", task_id, principal(p, "prj_a", "task.read", body))


def test_create_replay_and_identity_conflict(env):
    first = create(env)
    assert create(env) == first
    assert read(env, first["task_id"])["version"] == 1
    s = env[0]
    with pytest.raises(s.Error, match="identity_exists"):
        create(env, key="different")
    changed = create_body()
    changed["title"] = "Changed"
    with pytest.raises(s.Error, match="fingerprint"):
        s.create("prj_a", changed, principal(env[1], "prj_a", "task.create", changed))


def test_exact_historical_replay_and_detached_state(env):
    tid = create(env)["task_id"]
    start = command(tid)
    receipt = transition(env, start)
    assert receipt["version_after"] == 2
    transition(env, command(tid, "block", 2, "block"))
    assert canonical_json(transition(env, start)) == canonical_json(receipt)
    assert transition(env, start, credential_generation="generation_2") == receipt
    view = read(env, tid)
    view["status"] = "DONE"
    assert read(env, tid)["status"] == "BLOCKED"
    assert env[0].statistics()["journal"] == 4


@pytest.mark.parametrize(
    "patch",
    [
        {"task_id": "another"},
        {"reason": "changed"},
        {"expected_version": 2},
        {"admission_epoch": 2},
        {"transition": "block"},
    ],
)
def test_key_fingerprint_covers_intent(env, patch):
    tid = create(env)["task_id"]
    body = command(tid)
    transition(env, body)
    with pytest.raises(env[0].Error, match="fingerprint"):
        transition(env, dict(body, **patch))


def test_client_change_conflicts_but_receipt_read_is_scoped(env):
    tid = create(env)["task_id"]
    body = command(tid)
    result = transition(env, body)
    with pytest.raises(env[0].Error, match="fingerprint"):
        transition(env, body, client_id="client_b")
    lookup = {"operation_kind": "task.transition", "idempotency_key": "start"}
    assert (
        env[0].receipt(
            "prj_a", lookup, principal(env[1], "prj_a", "task.read", lookup, client_id="client_b")
        )
        == result
    )


def test_named_legality_dependencies_and_default_deny_done(env):
    tid = create(env)["task_id"]
    block = command(tid, "block", 1, "block")
    blocked_receipt = transition(env, block)
    with pytest.raises(env[0].Error, match="illegal"):
        transition(env, command(tid, "block", 2, "again"))
    with pytest.raises(env[0].Error, match="illegal"):
        transition(env, command(tid, "start", 2, "start"))
    transition(env, command(tid, "resume", 2, "resume"))
    assert transition(env, block) == blocked_receipt
    done = dict(
        command(tid, "done", 3, "done"), completion_evidence_ref={"id": "fake", "sha256": "0" * 64}
    )
    with pytest.raises(env[0].Error):
        transition(env, done)
    dependent = create(env, source="dependent", key="dependent", dependencies=[tid])["task_id"]
    with pytest.raises(env[0].Error, match="dependency_unavailable"):
        transition(env, command(dependent, key="start-dependent"))
    with pytest.raises(env[0].Error, match="dependency_unavailable"):
        create(env, source="foreign-edge", key="foreign-edge", dependencies=["foreign"])


@pytest.mark.parametrize(
    "patch",
    [
        {"expires_at": 0},
        {"audience": "wrong"},
        {"request_binding": "0" * 64},
        {"credential_generation": "revoked"},
        {"verifier_id": "forged"},
    ],
)
def test_auth_denied_before_lookup(env, patch):
    with pytest.raises(env[0].Error):
        transition(env, command("missing"), **patch)
    assert env[0].statistics()["journal"] == 1


def test_cas_and_second_writer(env):
    tid = create(env)["task_id"]

    def work(key):
        try:
            return transition(env, command(tid, key=key))["outcome"]
        except env[0].Error:
            return "CONFLICT"

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(work, ["one", "two"])) == ["APPLIED", "CONFLICT"]
    with pytest.raises(env[0].Error, match="writer"):
        type(env[0])(env[2] / "tasks.db", env[2] / "checkpoint.jsonl")


def test_crash_before_commit_and_after_checkpoint(env):
    s = env[0]
    tid = create(env)["task_id"]
    body = command(tid)

    def crash(point):
        if point == "before_commit":
            raise OSError("injected storage failure")

    s.fault_hook = crash
    with pytest.raises(OSError):
        transition(env, body)
    s.fault_hook = None
    assert read(env, tid)["version"] == 1
    result = transition(env, body)
    s.close()
    reopened = type(s)(env[2] / "tasks.db", env[2] / "checkpoint.jsonl")
    try:
        assert transition((reopened, *env[1:]), body) == result
    finally:
        reopened.close()


def test_commit_without_checkpoint_holds_and_never_exposes_receipt(env):
    s = env[0]
    tid = create(env)["task_id"]

    def crash(point):
        if point == "after_commit":
            raise OSError("checkpoint unavailable")

    s.fault_hook = crash
    with pytest.raises(s.Error, match="UNKNOWN"):
        transition(env, command(tid))
    with pytest.raises(s.Error):
        read(env, tid)
    s.close()
    with pytest.raises(s.Error, match="checkpoint"):
        type(s)(env[2] / "tasks.db", env[2] / "checkpoint.jsonl")


def test_old_database_new_checkpoint_and_torn_anchor_hold(env):
    s, p, root, _ = env
    old = (root / "tasks.db").read_bytes()
    create(env)
    s.close()
    (root / "tasks.db").write_bytes(old)
    with pytest.raises(s.Error, match="checkpoint"):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    with (root / "checkpoint.jsonl").open("ab") as f:
        f.write(b'{"torn":')
    with pytest.raises(s.Error):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")


def test_replay_integrity_and_policy_revocation(env):
    s, p, root, bundle = env
    tid = create(env)["task_id"]
    body = command(tid)
    receipt = transition(env, body)
    replay = s.replay()
    assert replay["tasks"][tid]["status"] == "IN_PROGRESS"
    assert receipt in list(replay["operations"].values())
    s.close()
    bundle.update(expected_epoch=1, idempotency_key="revoke")
    bundle["grants"][0]["credential_generations"] = ["generation_2"]
    digest = seal(root / "replace.json", bundle)
    type(s).replace_admission(
        root / "tasks.db", root / "checkpoint.jsonl", root / "replace.json", digest
    )
    updated = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        with pytest.raises(s.Error):
            transition((updated, p, root, bundle), body)
        assert (
            transition((updated, p, root, bundle), body, credential_generation="generation_2")
            == receipt
        )
    finally:
        updated.close()


def test_bootstrap_permissions_registry_and_inventory(tmp_path, modules):
    m, _ = modules
    root = tmp_path / "safe"
    bundle = admission_fixture(root)
    for patch in (
        {"inventory": dict(bundle["inventory"], complete=False)},
        {"registry_sha256": "0" * 64},
    ):
        sha = seal(root / "bad.json", dict(bundle, **patch))
        with pytest.raises((ValueError, m.SQLiteTaskStore.Error)):
            m.SQLiteTaskStore.bootstrap(
                root / "tasks.db", root / "checkpoint.jsonl", root / "bad.json", sha
            )
        assert not (root / "tasks.db").exists()
    sha = seal(root / "bundle.json", bundle)
    (root / "bundle.json").chmod(0o666)
    with pytest.raises((ValueError, m.SQLiteTaskStore.Error)):
        m.SQLiteTaskStore.bootstrap(
            root / "tasks.db", root / "checkpoint.jsonl", root / "bundle.json", sha
        )


def test_corrupt_journal_holds(env):
    s, _, root, _ = env
    s.close()
    db = sqlite3.connect(root / "tasks.db")
    db.execute("UPDATE journal SET digest=?", ("0" * 64,))
    db.commit()
    db.close()
    with pytest.raises(s.Error):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")


def test_operation_index_corruption_does_not_change_replay_truth(env):
    s, p, root, bundle = env
    create(env)
    s.close()
    db = sqlite3.connect(root / "tasks.db")
    db.execute("UPDATE operations SET digest=? WHERE kind='task.create'", ("0" * 64,))
    db.commit()
    db.close()
    with pytest.raises(s.Error, match="projection"):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")


def test_native_identity_requires_stable_uuid(env):
    s, p, *_ = env
    body = create_body()
    body["identity"]["source_task_id"] = "regenerated-or-title"
    with pytest.raises(ValueError):
        s.create("prj_a", body, principal(p, "prj_a", "task.create", body))


@pytest.mark.parametrize("value", [1, "true", False])
def test_inventory_proof_flags_are_strict_boolean(tmp_path, modules, value):
    m, _ = modules
    root = tmp_path / "strict"
    bundle = admission_fixture(root)
    bundle["inventory"]["complete"] = value
    sha = seal(root / "bundle.json", bundle)
    with pytest.raises(ValueError):
        m.SQLiteTaskStore.bootstrap(
            root / "tasks.db", root / "checkpoint.jsonl", root / "bundle.json", sha
        )


def test_named_done_grant_and_suspension_apply_before_replay(env):
    s, p, root, bundle = env
    tid = create(env)["task_id"]
    body = command(tid)
    receipt = transition(env, body)
    s.close()
    bundle.update(status="SUSPENDED", expected_epoch=1, idempotency_key="suspend")
    type(s).replace_admission(
        root / "tasks.db",
        root / "checkpoint.jsonl",
        root / "bundle.json",
        seal(root / "bundle.json", bundle),
    )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        with pytest.raises(s.Error):
            transition((reopened, p, root, bundle), body)
        lookup = {"operation_kind": "task.transition", "idempotency_key": "start"}
        assert (
            reopened.receipt("prj_a", lookup, principal(p, "prj_a", "task.read", lookup)) == receipt
        )
    finally:
        reopened.close()


def test_sqlite_full_rollback_and_closed_writer_hold(env):
    s, p, *_ = env
    pages = s._db.execute("PRAGMA page_count").fetchone()[0]
    s._db.execute("PRAGMA max_page_count=" + str(pages))
    body = create_body()
    body["description"] = "x" * 1_000_000
    with pytest.raises(sqlite3.OperationalError, match="full"):
        s.create("prj_a", body, principal(p, "prj_a", "task.create", body))
    assert s.statistics() == {"journal": 1, "tasks": 0, "operations": 1, "outbox": 0}
    s._db.execute("PRAGMA max_page_count=10000")
    result = create(env)
    before = s.replay()
    s.close()
    with pytest.raises(s.Error):
        transition(env, command(result["task_id"]))
    reopened = type(s)(env[2] / "tasks.db", env[2] / "checkpoint.jsonl")
    try:
        assert reopened.replay() == before
    finally:
        reopened.close()


@pytest.mark.parametrize("damage", ["sequence", "schema"])
def test_gap_and_unsupported_schema_hold(env, damage):
    s, _, root, _ = env
    create(env)
    s.close()
    db = sqlite3.connect(root / "tasks.db")
    if damage == "sequence":
        db.execute("DELETE FROM journal WHERE sequence=1")
    else:
        db.execute("UPDATE metadata SET value='unknown' WHERE key='schema'")
    db.commit()
    db.close()
    with pytest.raises(s.Error):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")


def test_registry_drift_aborts_handoff(tmp_path, modules, monkeypatch):
    from dopemux.pm.admission import OperatorLocalContext

    m, _ = modules
    root = tmp_path / "drift"
    bundle = admission_fixture(root)
    original = OperatorLocalContext.recheck

    def drift(context):
        (root / "registry.json").write_bytes(b"{}")
        original(context)

    monkeypatch.setattr(OperatorLocalContext, "recheck", drift)
    with pytest.raises(ValueError, match="drift"):
        m.SQLiteTaskStore.bootstrap(
            root / "tasks.db",
            root / "checkpoint.jsonl",
            root / "bundle.json",
            seal(root / "bundle.json", bundle),
        )
    db = sqlite3.connect(root / "tasks.db")
    try:
        assert db.execute("SELECT count(*) FROM journal").fetchone()[0] == 0
    finally:
        db.close()


def test_second_process_cannot_acquire_writer(env):
    s, _, root, _ = env
    context = multiprocessing.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)

    def attempt():
        try:
            other = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
            other.close()
            sender.send("UNEXPECTED_WRITER")
        except s.Error as exc:
            sender.send(exc.code)
        finally:
            sender.close()

    child = context.Process(target=attempt)
    child.start()
    sender.close()
    try:
        assert receiver.poll(5), "owned fixture process did not return"
        assert receiver.recv() == "writer_unavailable"
        child.join(5)
        assert child.exitcode == 0
    finally:
        if child.is_alive():
            child.terminate()
            child.join(5)
        receiver.close()


def test_lost_response_after_acknowledged_commit_replays_once(env):
    s, p, root, bundle = env
    tid = create(env)["task_id"]
    body = command(tid)

    def crash(point):
        if point == "after_checkpoint":
            raise OSError("lost response")

    s.fault_hook = crash
    with pytest.raises(OSError, match="lost response"):
        transition(env, body)
    s.close()
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        assert transition((reopened, p, root, bundle), body)["version_after"] == 2
        assert reopened.statistics()["journal"] == 3
    finally:
        reopened.close()


def test_shutdown_waits_for_inflight_commit_before_releasing_writer(env):
    from threading import Event

    s, p, root, bundle = env
    tid = create(env)["task_id"]
    body = command(tid)
    at_commit, release, closing, closed = (Event() for _ in range(4))

    def pause(point):
        if point == "before_commit":
            at_commit.set()
            assert release.wait(5), "fixture commit not released"

    def close():
        closing.set()
        try:
            s.close()
        finally:
            closed.set()

    s.fault_hook = pause
    with ThreadPoolExecutor(2) as pool:
        write = pool.submit(transition, env, body)
        assert at_commit.wait(5)
        shutdown = pool.submit(close)
        assert closing.wait(5)
        try:
            assert not closed.wait(0.1), "writer released during an in-flight transaction"
            with pytest.raises(s.Error, match="writer"):
                type(s)(root / "tasks.db", root / "checkpoint.jsonl")
        finally:
            release.set()
        receipt = write.result(timeout=5)
        shutdown.result(timeout=5)
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        assert transition((reopened, p, root, bundle), body) == receipt
    finally:
        reopened.close()


@pytest.mark.parametrize("operation", ["resume", "done"])
def test_specific_transition_grant_required_before_evidence_or_replay(env, operation):
    s, p, root, bundle = env
    tid = create(env)["task_id"]
    if operation == "resume":
        transition(env, command(tid, "block", 1, "block"))
    else:
        transition(env, command(tid))
    s.close()
    bundle.update(expected_epoch=1, idempotency_key="remove-grant")
    bundle["grants"][0]["actions"].remove("task.transition." + operation)
    type(s).replace_admission(
        root / "tasks.db",
        root / "checkpoint.jsonl",
        root / "replace.json",
        seal(root / "replace.json", bundle),
    )

    class UnexpectedVerifier:
        def verify(self, **kwargs):
            pytest.fail("evidence consulted before authorization")

    reopened = type(s)(
        root / "tasks.db",
        root / "checkpoint.jsonl",
        completion_verifier=UnexpectedVerifier(),
    )
    try:
        body = dict(command(tid, operation, 2, "unauthorized"), admission_epoch=2)
        if operation == "done":
            body["completion_evidence_ref"] = {"id": "untrusted", "sha256": "0" * 64}
        before = reopened.statistics()
        with pytest.raises(s.Error) as error:
            transition((reopened, p, root, bundle), body)
        assert error.value.status == 404
        assert reopened.statistics() == before
    finally:
        reopened.close()


@pytest.mark.parametrize("damage", ["ahead", "behind", "missing"])
def test_task_projection_drift_is_held_without_rewriting_truth(env, damage):
    s, _, root, _ = env
    tid = create(env)["task_id"]
    transition(env, command(tid))
    s.close()
    db = sqlite3.connect(root / "tasks.db")
    journal = db.execute("SELECT sequence,payload,digest FROM journal ORDER BY sequence").fetchall()
    if damage == "missing":
        db.execute("DELETE FROM tasks WHERE task_id=?", (tid,))
    else:
        task = json.loads(
            db.execute("SELECT snapshot FROM tasks WHERE task_id=?", (tid,)).fetchone()[0]
        )
        task["version"] = 3 if damage == "ahead" else 1
        db.execute("UPDATE tasks SET snapshot=? WHERE task_id=?", (canonical_json(task), tid))
    db.commit()
    db.close()
    with pytest.raises(s.Error, match="projection"):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    db = sqlite3.connect(root / "tasks.db")
    try:
        assert (
            db.execute("SELECT sequence,payload,digest FROM journal ORDER BY sequence").fetchall()
            == journal
        )
    finally:
        db.close()


def test_missing_checkpoint_never_reopens_acknowledged_store(env):
    s, _, root, _ = env
    create(env)
    s.close()
    (root / "checkpoint.jsonl").rename(root / "preserved-checkpoint.jsonl")
    before = (root / "tasks.db").read_bytes()
    with pytest.raises(ValueError, match="absent"):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    assert (root / "tasks.db").read_bytes() == before


@pytest.mark.parametrize(
    "change",
    [
        "revision",
        "equal-change",
        "admission-drop",
        "source-drop",
        "source-reassign",
        "legacy-drop",
        "legacy-reassign",
        "task-source",
        "task-source-remap",
        "task-policy",
        "task-policy-drop",
    ],
)
def test_replacement_preserves_inventory_and_task_contracts(env, change):
    """Missing preservation checks would admit each destructive replacement."""
    s, p, root, bundle = env
    create(env)
    s.close()
    baseline = json.loads(canonical_json(bundle))
    baseline.update(expected_epoch=1, idempotency_key="expand")
    baseline["inventory"]["revision"] = 2
    baseline["inventory"]["admissions"].append("prj_b")
    baseline["inventory"]["sources"].append(
        dict(
            project_id="prj_b",
            source_system="other",
            source_instance_id="other",
            external_project_id="other",
        )
    )
    baseline["inventory"]["legacy_allocations"].append(
        dict(
            project_id="prj_b",
            task_id="old",
            source_system="other",
            source_instance_id="other",
            source_task_id="old",
        )
    )
    path = root / "replace.json"
    type(s).replace_admission(
        root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, baseline)
    )
    current = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    history, counts = current.replay(), current.statistics()
    current.close()
    checkpoint = (root / "checkpoint.jsonl").read_bytes()
    replacement = json.loads(canonical_json(baseline))
    replacement.update(expected_epoch=2, idempotency_key="denied-replacement")
    replacement["inventory"]["revision"] = 3
    if change == "revision":
        replacement["inventory"]["revision"] = 1
    elif change == "equal-change":
        replacement["inventory"]["revision"] = 2
        replacement["inventory"]["admissions"].append("prj_c")
    elif change == "admission-drop":
        replacement["inventory"]["admissions"].append("prj_c")
        replacement["inventory"]["admissions"].remove("prj_b")
        replacement["inventory"]["sources"].pop()
        replacement["inventory"]["legacy_allocations"].clear()
    elif change == "source-drop":
        replacement["inventory"]["sources"].pop()
    elif change == "source-reassign":
        replacement["inventory"]["sources"][-1]["project_id"] = "prj_a"
    elif change == "legacy-drop":
        replacement["inventory"]["legacy_allocations"].clear()
    elif change == "legacy-reassign":
        replacement["inventory"]["legacy_allocations"][0]["task_id"] = "changed"
    elif change == "task-source":
        replacement["sources"] = []
    elif change == "task-source-remap":
        replacement["sources"][0]["external_project_id"] = "new-external"
        replacement["inventory"]["sources"].append(
            dict(project_id="prj_a", source_system="dopemux", source_instance_id="producer_a", external_project_id="new-external")
        )
    elif change == "task-policy":
        replacement["completion_policies"][0]["version"] = 2
    elif change == "task-policy-drop":
        replacement["completion_policies"] = []
    with pytest.raises((ValueError, s.Error)):
        type(s).replace_admission(
            root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, replacement)
        )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    assert reopened.replay() == history and reopened.statistics() == counts
    reopened.close()
    assert (root / "checkpoint.jsonl").read_bytes() == checkpoint
    # The denied key was never consumed; valid status/access replacement can use it.
    valid = json.loads(canonical_json(baseline))
    valid.update(
        expected_epoch=2, idempotency_key="denied-replacement", status="SUSPENDED"
    )
    valid["grants"] = []
    valid["sources"][0]["producer_principal_ids"] = []
    receipt = type(s).replace_admission(
        root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, valid)
    )
    assert (
        type(s).replace_admission(
            root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, valid)
        )
        == receipt
    )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    assert reopened.replay()["policy"]["status"] == "SUSPENDED"
    reopened.close()


@pytest.mark.parametrize("change", ["revision", "task-source", "task-policy"])
def test_replay_holds_invalid_replacement_history(env, change):
    """A valid hash/checkpoint cannot legitimize destructive policy history."""
    s, p, root, bundle = env
    create(env)
    replacement = json.loads(canonical_json(bundle))
    replacement["admission_epoch"] = 2
    if change == "revision":
        replacement["inventory"]["admissions"].append("prj_b")
    elif change == "task-source":
        replacement["sources"] = []
    else:
        replacement["completion_policies"] = []
    with s._transaction():
        s._append(
            "admission.replace",
            {"idempotency_key": "invalid-history"},
            "operator",
            "maintenance-cli",
            "operator-local",
            "os-uid",
            policy=replacement,
        )
    s.close()
    with pytest.raises(s.Error, match="journal_integrity_hold"):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")


def test_inventory_preservation_allows_producer_revocation(env):
    """Durable source identity must not freeze current producer permissions."""
    s, p, root, bundle = env
    created = create(env)
    s.close()
    replacement = json.loads(canonical_json(bundle))
    replacement.update(expected_epoch=1, idempotency_key="revoke-producer")
    replacement["sources"][0]["producer_principal_ids"] = []
    path = root / "replace.json"
    type(s).replace_admission(root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, replacement))
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        changed_env = (reopened, p, root, replacement)
        assert read(changed_env, created["task_id"])["status"] == "TODO"
        before = reopened.statistics()
        body = create_body(source="new-after-revocation", key="new-after-revocation")
        body["admission_epoch"] = 2
        with pytest.raises(s.Error) as denied:
            reopened.create("prj_a", body, principal(p, "prj_a", "task.create", body))
        assert (denied.value.status, denied.value.code) == (404, "not_found")
        assert reopened.statistics() == before
    finally:
        reopened.close()
