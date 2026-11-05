"""Approved local dry-run/import/reconciliation, all artifacts are temporary."""

import hashlib
import importlib
import importlib.util
import json

import pytest

from dopemux.pm.ownership import canonical_json
from tests.unit.pm.test_ownership_store import (
    seal,
    create,
    command,
    transition,
    read,
    admission_fixture,
    principal,
)
from tests.unit.pm import test_ownership_store as store_support

env = store_support.env
modules = store_support.modules


@pytest.fixture
def maintenance():
    assert importlib.util.find_spec("dopemux.pm.maintenance"), "local maintenance unavailable"
    return importlib.import_module("dopemux.pm.maintenance")


def migration_fixture(bundle, *, status="TODO"):
    snapshot = {
        "task_id": "legacy-stable-bytes",
        "title": "Old task",
        "description": "Preserved description",
        "source": "dopemux",
        "source_task_id": "legacy-source",
        "status": status,
        "version": 7,
        "created_at_utc": "2026-01-01T00:00:00Z",
        "updated_at_utc": "2026-02-01T00:00:00Z",
        "linked_ids": {"ticket": "007"},
        "meta": {"historical": "retain in provenance"},
        "refs": {},
        "labels": [],
    }
    raw = canonical_json(snapshot).decode()
    identity = dict(
        project_id="prj_a",
        source_system="dopemux",
        source_instance_id="producer_a",
        source_task_id="legacy-source",
    )
    inventory = json.loads(canonical_json(bundle["inventory"]))
    inventory["legacy_allocations"] = [dict(task_id=snapshot["task_id"], **identity)]
    row = dict(
        idempotency_key="import-legacy",
        snapshot_json=raw,
        snapshot_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        identity=identity,
        dependencies=[],
        completion_policy_id="kernel-v1",
        completion_policy_version=1,
        ownership_evidence_sha256="1" * 64,
        completion_evidence_ref=None,
    )
    return dict(
        schema_version="dopemux.pm.migration-input.v1",
        project_id="prj_a",
        expected_admission_epoch=1,
        inventory=inventory,
        rows=[row],
    )


def test_dry_run_is_deterministic_and_missing_ownership_stays_staged(env, maintenance):
    s, p, root, bundle = env
    data = migration_fixture(bundle)
    before = s.statistics()
    result = maintenance.dry_run(data)
    assert canonical_json(result) == canonical_json(maintenance.dry_run(data))
    assert result["rows"][0]["classification"] == "BOUND_CANDIDATE"
    assert s.statistics() == before
    data["rows"][0]["identity"] = None
    assert maintenance.dry_run(data)["rows"][0]["classification"] == "UNBOUND"
    data = migration_fixture(bundle, status="DONE")
    assert maintenance.dry_run(data)["rows"][0]["classification"] == "UNBOUND"


def test_duplicate_or_unbound_dependencies_stay_quarantined(env, maintenance):
    data = migration_fixture(env[3])
    data["rows"] *= 2
    assert all(r["classification"] == "QUARANTINED" for r in maintenance.dry_run(data)["rows"])
    data = migration_fixture(env[3])
    data["rows"][0]["dependencies"] = ["missing"]
    assert maintenance.dry_run(data)["rows"][0]["classification"] == "UNBOUND"


def test_atomic_bound_import_exact_replay_and_new_key_conflict(env, maintenance):
    s, p, root, bundle = env
    manifest = maintenance.dry_run(migration_fixture(bundle))
    sha = seal(root / "manifest.json", manifest)
    s.close()
    result = maintenance.import_bound(
        root / "tasks.db", root / "checkpoint.jsonl", root / "manifest.json", sha, 0
    )
    assert (
        result["task_id"] == "legacy-stable-bytes"
        and result["version_before"] == 7
        and result["version_after"] == 8
    )
    assert (
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", root / "manifest.json", sha, 0
        )
        == result
    )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        task = read((reopened, p, root, bundle), "legacy-stable-bytes")
        assert task["linked_ids"] == {"ticket": "007"} and task["status"] == "TODO"
        assert task["task_id_scheme"] == "legacy-v1" and task["binding_version"] == 1
        assert task["legacy_snapshot_sha256"] == manifest["rows"][0]["snapshot_sha256"]
        assert "legacy_snapshot_json" not in task
    finally:
        reopened.close()
    changed = migration_fixture(bundle)
    changed["rows"][0]["idempotency_key"] = "new-import-key"
    manifest = maintenance.dry_run(changed)
    sha = seal(root / "changed.json", manifest)
    with pytest.raises(s.Error, match="identity_exists"):
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", root / "changed.json", sha, 0
        )


def test_import_cannot_overlap_runtime_or_forge_classification(env, maintenance):
    s, p, root, bundle = env
    data = migration_fixture(bundle)
    data["rows"][0]["identity"] = None
    manifest = maintenance.dry_run(data)
    manifest["rows"][0]["classification"] = "BOUND_CANDIDATE"
    sha = seal(root / "forged.json", manifest)
    with pytest.raises((ValueError, s.Error)):
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", root / "forged.json", sha, 0
        )
    assert s.statistics()["tasks"] == 0


def test_checkpoint_reconciliation_is_exact_approved_and_nonreexecuting(env, maintenance):
    s, p, root, bundle = env
    tid = create(env)["task_id"]
    body = command(tid)
    anchor = (root / "checkpoint.jsonl").read_bytes()
    last = json.loads(anchor.splitlines()[-1])

    def crash(point):
        if point == "after_commit":
            raise OSError("power loss")

    s.fault_hook = crash
    with pytest.raises(s.Error, match="UNKNOWN"):
        transition(env, body)
    replay = s.replay()
    s.close()
    approval = dict(
        schema_version="dopemux.pm.reconciliation-bundle.v1",
        idempotency_key="reconcile-1",
        project_id="prj_a",
        store_uuid="store_a",
        db_sequence=replay["sequence"],
        db_head=replay["heads"][replay["sequence"]],
        anchor_sequence=last["event_sequence"],
        anchor_head=last["chain_head"],
        anchor_sha256=hashlib.sha256(anchor).hexdigest(),
        acknowledged_history_preserved=True,
        operator_decision_ref="fixture-investigation",
        independent_receipts=[],
    )
    sha = seal(root / "reconcile.json", approval)
    result = maintenance.reconcile(
        root / "tasks.db", root / "checkpoint.jsonl", root / "reconcile.json", sha
    )
    assert result["operation_kind"] == "checkpoint.reconcile"
    assert (
        maintenance.reconcile(
            root / "tasks.db", root / "checkpoint.jsonl", root / "reconcile.json", sha
        )
        == result
    )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        assert transition((reopened, p, root, bundle), body)["version_after"] == 2
        assert reopened.statistics()["journal"] == 4  # bootstrap, create, start, reconcile
    finally:
        reopened.close()


@pytest.mark.parametrize("anchor_state", ["missing", "empty"])
@pytest.mark.parametrize("with_receipt", [False, True])
def test_reconciliation_holds_missing_acknowledged_history(
    env, maintenance, anchor_state, with_receipt
):
    s, p, root, bundle = env
    receipt = create(env)
    checkpoint = root / "checkpoint.jsonl"
    preserved = checkpoint.read_bytes()
    history = s.replay()
    statistics = s.statistics()
    s.close()
    checkpoint.rename(root / "preserved-checkpoint.jsonl")
    if anchor_state == "empty":
        checkpoint.write_bytes(b"")
        checkpoint.chmod(0o600)
    database_before = (root / "tasks.db").read_bytes()
    approval = dict(
        schema_version="dopemux.pm.reconciliation-bundle.v1",
        idempotency_key="lost-history",
        project_id="prj_a",
        store_uuid="store_a",
        db_sequence=history["sequence"],
        db_head=history["heads"][history["sequence"]],
        anchor_sequence=0,
        anchor_head="0" * 64,
        anchor_sha256=hashlib.sha256(b"").hexdigest(),
        acknowledged_history_preserved=True,
        operator_decision_ref="fixture-investigation",
        independent_receipts=(
            [
                dict(
                    event_sequence=receipt["event_sequence"],
                    receipt_sha256=hashlib.sha256(canonical_json(receipt)).hexdigest(),
                )
            ]
            if with_receipt
            else []
        ),
    )
    sha = seal(root / "lost-history.json", approval)
    with pytest.raises(ValueError, match="HOLD"):
        maintenance.reconcile(
            root / "tasks.db", checkpoint, root / "lost-history.json", sha
        )
    assert checkpoint.exists() == (anchor_state == "empty")
    if checkpoint.exists():
        assert checkpoint.read_bytes() == b""
    assert (root / "preserved-checkpoint.jsonl").read_bytes() == preserved
    assert (root / "tasks.db").read_bytes() == database_before
    inspection = type(s)(root / "tasks.db", checkpoint, _reconcile=True)
    try:
        assert inspection.replay() == history
        assert inspection.statistics() == statistics
        assert (
            inspection._db.execute(
                "SELECT count(*) FROM operations WHERE kind=? AND key=?",
                ("checkpoint.reconcile", "lost-history"),
            ).fetchone()[0]
            == 0
        )
    finally:
        inspection.close()


def test_reconciliation_denies_mismatched_independent_receipt_without_consuming_key(
    env, maintenance
):
    s, p, root, bundle = env
    created = create(env)
    checkpoint = root / "checkpoint.jsonl"
    anchor = checkpoint.read_bytes()
    last = json.loads(anchor.splitlines()[-1])

    def crash(point):
        if point == "after_commit":
            raise OSError("power loss")

    s.fault_hook = crash
    with pytest.raises(s.Error, match="UNKNOWN"):
        transition(env, command(created["task_id"]))
    history = s.replay()
    s.close()
    database_before = (root / "tasks.db").read_bytes()
    approval = dict(
        schema_version="dopemux.pm.reconciliation-bundle.v1",
        idempotency_key="receipt-check",
        project_id="prj_a",
        store_uuid="store_a",
        db_sequence=history["sequence"],
        db_head=history["heads"][history["sequence"]],
        anchor_sequence=last["event_sequence"],
        anchor_head=last["chain_head"],
        anchor_sha256=hashlib.sha256(anchor).hexdigest(),
        acknowledged_history_preserved=True,
        operator_decision_ref="fixture-investigation",
        independent_receipts=[
            dict(event_sequence=created["event_sequence"], receipt_sha256="f" * 64)
        ],
    )
    path = root / "receipt-check.json"
    sha = seal(path, approval)
    with pytest.raises(ValueError, match="Independent receipt"):
        maintenance.reconcile(root / "tasks.db", checkpoint, path, sha)
    assert checkpoint.read_bytes() == anchor
    assert (root / "tasks.db").read_bytes() == database_before
    inspection = type(s)(root / "tasks.db", checkpoint, _reconcile=True)
    try:
        assert inspection.replay() == history
    finally:
        inspection.close()
    approval["independent_receipts"][0]["receipt_sha256"] = hashlib.sha256(
        canonical_json(created)
    ).hexdigest()
    sha = seal(path, approval)
    receipt = maintenance.reconcile(root / "tasks.db", checkpoint, path, sha)
    assert receipt["operation_kind"] == "checkpoint.reconcile"
    assert maintenance.reconcile(root / "tasks.db", checkpoint, path, sha) == receipt


def test_runtime_cannot_open_staging_as_store(env, maintenance):
    s, p, root, bundle = env
    seal(root / "staging.json", maintenance.dry_run(migration_fixture(bundle)))
    with pytest.raises(Exception):
        type(s)(root / "staging.json", root / "checkpoint.jsonl")


def test_maintenance_lock_and_manifest_recomputation(env, maintenance):
    s, p, root, bundle = env
    good = maintenance.dry_run(migration_fixture(bundle))
    sha = seal(root / "good.json", good)
    with pytest.raises(s.Error, match="writer"):
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", root / "good.json", sha, 0
        )
    s.close()
    bad = migration_fixture(bundle)
    bad["rows"][0]["identity"] = None
    manifest = maintenance.dry_run(bad)
    manifest["rows"][0]["classification"] = "BOUND_CANDIDATE"
    sha = seal(root / "bad.json", manifest)
    with pytest.raises(ValueError, match="classification"):
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", root / "bad.json", sha, 0
        )


def test_done_import_requires_actual_qualified_kernel_snapshot(env, maintenance):
    from dopemux.pm.completion import KernelBinding, KernelCompletionVerifier
    from tests.unit.pm.test_ownership_runtime import kernel_snapshot

    s, p, root, bundle = env
    data = migration_fixture(bundle, status="DONE")
    row = data["rows"][0]
    task = {
        "project_id": "prj_a",
        "task_id": "legacy-stable-bytes",
        "version": 7,
        "identity": row["identity"],
    }
    raw = canonical_json(kernel_snapshot(task))
    sha = hashlib.sha256(raw).hexdigest()
    verifier = KernelCompletionVerifier(
        {
            "legacy-done": (
                KernelBinding(
                    "prj_a", "legacy-stable-bytes", "wf_a", "fixture-revision", "kernel-v1", 1
                ),
                raw,
            )
        }
    )
    row["completion_evidence_ref"] = {"id": "legacy-done", "sha256": sha}
    manifest = maintenance.dry_run(data, completion_verifier=verifier)
    assert manifest["rows"][0]["classification"] == "BOUND_CANDIDATE"
    approved = seal(root / "done.json", manifest)
    s.close()
    receipt = maintenance.import_bound(
        root / "tasks.db",
        root / "checkpoint.jsonl",
        root / "done.json",
        approved,
        0,
        completion_verifier=verifier,
    )
    assert receipt["to_status"] == "DONE" and receipt["version_after"] == 8
    # Replay uses the sealed original result even with the default deny verifier.
    assert (
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", root / "done.json", approved, 0
        )
        == receipt
    )


def test_same_legacy_id_in_two_approved_source_partitions(env, maintenance, tmp_path):
    s, p, root_a, bundle_a = env
    data_a = migration_fixture(bundle_a)
    root_b = tmp_path / "store_b"
    bundle_b = admission_fixture(root_b, project="prj_b")
    registry_b = json.loads((root_b / "registry.json").read_text())
    project_b = registry_b["projects"]["prj_b"]
    workspace = project_b["workspaces"].pop("ws_a")
    workspace["workspace_id"] = "ws_b"
    instance = workspace["instances"].pop("inst_a")
    instance["instance_id"] = "inst_b"
    workspace["instances"]["inst_b"] = instance
    project_b["workspaces"]["ws_b"] = workspace
    registry_b["projects"].update(json.loads((root_a / "registry.json").read_text())["projects"])
    registry_b["generation"] = 6
    bundle_b.update(
        workspace_id="ws_b",
        instance_id="inst_b",
        store_uuid="store_b",
        registry_generation=6,
        registry_sha256=seal(root_b / "registry.json", registry_b),
    )
    bundle_b["sources"][0]["source_instance_id"] = "producer_b"
    data_b = migration_fixture(bundle_b)
    data_b["project_id"] = "prj_b"
    data_b["rows"][0]["identity"].update(project_id="prj_b", source_instance_id="producer_b")
    inventory = {
        "schema_version": "dopemux.pm.allocation-inventory.v1",
        "revision": 2,
        "complete": True,
        "composite_consumers_qualified": True,
        "admissions": ["prj_a", "prj_b"],
        "sources": [
            bundle_a["inventory"]["sources"][0],
            dict(
                project_id="prj_b",
                source_system="dopemux",
                source_instance_id="producer_b",
                external_project_id="prj_b",
            ),
        ],
        "legacy_allocations": [
            dict(task_id="legacy-stable-bytes", **data_a["rows"][0]["identity"]),
            dict(task_id="legacy-stable-bytes", **data_b["rows"][0]["identity"]),
        ],
    }
    bundle_b["inventory"] = inventory
    data_a["inventory"] = inventory
    data_b["inventory"] = inventory
    s.close()
    type(s).bootstrap(
        root_b / "tasks.db",
        root_b / "checkpoint.jsonl",
        root_b / "bundle.json",
        seal(root_b / "bundle.json", bundle_b),
    )
    for root, data in [(root_a, data_a), (root_b, data_b)]:
        manifest = maintenance.dry_run(data)
        sha = seal(root / "manifest.json", manifest)
        assert manifest["rows"][0]["classification"] == "BOUND_CANDIDATE"
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", root / "manifest.json", sha, 0
        )
    for root, project, instance_id in [(root_a, "prj_a", "inst_a"), (root_b, "prj_b", "inst_b")]:
        store = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
        try:
            body = {"task_id": "legacy-stable-bytes"}
            actor = principal(
                p, project, "task.read", body, audience=f"dopemux.pm:{instance_id}:{project}"
            )
            assert store.get_task(project, body["task_id"], actor)["project_id"] == project
            assert store.statistics()["tasks"] == 1
        finally:
            store.close()


@pytest.mark.parametrize("revision", [1, 4])
def test_replacement_preserves_imported_inventory_not_just_policy(
    env, maintenance, revision
):
    """Import manifests carry durable allocations absent from the policy projection."""
    s, p, root, bundle = env
    data = migration_fixture(bundle)
    data["inventory"]["revision"] = revision
    data["inventory"]["admissions"].append("prj_b")
    data["inventory"]["legacy_allocations"].append(
        dict(
            project_id="prj_b",
            task_id="known-unimported",
            source_system="other",
            source_instance_id="other",
            source_task_id="known",
        )
    )
    manifest = maintenance.dry_run(data)
    path = root / "manifest.json"
    s.close()
    imported = maintenance.import_bound(
        root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, manifest), 0
    )
    replacement = json.loads(canonical_json(bundle))
    replacement.update(expected_epoch=1, idempotency_key="replace-after-import")
    replacement["inventory"]["revision"] = revision + 1
    path = root / "replace.json"
    with pytest.raises((ValueError, s.Error)):
        type(s).replace_admission(
            root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, replacement)
        )
    # Exact known inventory permits equal revision, even for historical equal-revision import.
    replacement["inventory"] = manifest["inventory"]
    receipt = type(s).replace_admission(
        root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, replacement)
    )
    assert (
        type(s).replace_admission(
            root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, replacement)
        )
        == receipt
    )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    assert reopened.replay()["tasks"]["legacy-stable-bytes"]["status"] == "TODO"
    reopened.close()
    assert (
        maintenance.import_bound(
            root / "tasks.db",
            root / "checkpoint.jsonl",
            root / "manifest.json",
            seal(root / "manifest.json", manifest),
            0,
        )
        == imported
    )


@pytest.mark.parametrize("first_revision, second_revision", [(5, 2), (1, 1)])
def test_multiple_imports_preserve_union_and_highest_known_revision(
    env, maintenance, first_revision, second_revision
):
    """A later import cannot erase earlier allocations by leaving policy stale."""
    s, p, root, bundle = env
    first = migration_fixture(bundle)
    first["inventory"]["revision"] = first_revision
    first["inventory"]["admissions"].append("prj_b")
    reserved = dict(
        project_id="prj_b",
        task_id="reserved",
        source_system="other",
        source_instance_id="other",
        source_task_id="reserved",
    )
    first["inventory"]["legacy_allocations"].append(reserved)
    manifest = maintenance.dry_run(first)
    path = root / "first.json"
    s.close()
    maintenance.import_bound(
        root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, manifest), 0
    )
    second = migration_fixture(bundle)
    row = second["rows"][0]
    snapshot = json.loads(row["snapshot_json"])
    snapshot.update(task_id="second-legacy", source_task_id="second-source")
    row.update(
        idempotency_key="import-second", snapshot_json=canonical_json(snapshot).decode()
    )
    row["snapshot_sha256"] = hashlib.sha256(row["snapshot_json"].encode()).hexdigest()
    row["identity"]["source_task_id"] = "second-source"
    second_allocation = dict(task_id="second-legacy", **row["identity"])
    second["inventory"]["legacy_allocations"].append(second_allocation)
    second["inventory"]["revision"] = second_revision
    path = root / "second.json"
    maintenance.import_bound(
        root / "tasks.db",
        root / "checkpoint.jsonl",
        path,
        seal(path, maintenance.dry_run(second)),
        0,
    )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    known = reopened.replay()["known_inventory"]
    assert known["revision"] == first_revision
    assert {a["task_id"] for a in known["legacy_allocations"]} == {
        "legacy-stable-bytes",
        "second-legacy",
        "reserved",
    }
    history = reopened.replay()
    reopened.close()
    replacement = json.loads(canonical_json(bundle))
    replacement.update(expected_epoch=1, idempotency_key="replace-union")
    replacement["inventory"] = json.loads(canonical_json(known))
    replacement["inventory"]["revision"] = max(1, first_revision - 1)
    if first_revision == 1:
        replacement["inventory"]["legacy_allocations"].remove(reserved)
    path = root / "replace.json"
    with pytest.raises(s.Error, match="invalid_admission_replacement"):
        type(s).replace_admission(
            root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, replacement)
        )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    assert reopened.replay() == history
    reopened.close()
    replacement["inventory"] = json.loads(canonical_json(known))
    type(s).replace_admission(
        root / "tasks.db", root / "checkpoint.jsonl", path, seal(path, replacement)
    )
    reopened = type(s)(root / "tasks.db", root / "checkpoint.jsonl")
    assert reopened.replay()["known_inventory"] == known
    reopened.close()


@pytest.mark.parametrize("conflict", ["source", "legacy-key", "legacy-id"])
def test_replay_holds_conflicting_import_inventory(env, conflict):
    """Replay must reject conflicting immutable keys, never choose a union winner."""
    s, p, root, bundle = env
    first = migration_fixture(bundle)["inventory"]
    with s._transaction():
        s._append(
            "task.import_bound",
            {"idempotency_key": "first", "manifest": {"inventory": first}},
            "operator",
            "maintenance-cli",
            "operator-local",
            "os-uid",
        )
    second = json.loads(canonical_json(first))
    if conflict == "source":
        second["admissions"].append("prj_b")
        second["sources"][0]["project_id"] = "prj_b"
    elif conflict == "legacy-key":
        second["legacy_allocations"][0]["task_id"] = "reassigned"
    else:
        second["legacy_allocations"][0]["source_task_id"] = "different-source"
    with s._transaction():
        s._append(
            "task.import_bound",
            {"idempotency_key": "second", "manifest": {"inventory": second}},
            "operator",
            "maintenance-cli",
            "operator-local",
            "os-uid",
        )
    s.close()
    with pytest.raises(s.Error, match="journal_integrity_hold"):
        type(s)(root / "tasks.db", root / "checkpoint.jsonl")


def _import_state(store_type, root):
    """Read acknowledged state without substituting private writes for public imports."""
    store = store_type(root / "tasks.db", root / "checkpoint.jsonl")
    try:
        return dict(
            replay=store.replay(),
            statistics=store.statistics(),
            tables={
                table: store._db.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
                for table, order in (
                    ("journal", "sequence"),
                    ("tasks", "task_id"),
                    ("operations", "principal,kind,key"),
                    ("outbox", "sequence,destination"),
                )
            },
            checkpoint=(root / "checkpoint.jsonl").read_bytes(),
        )
    finally:
        store.close()


@pytest.mark.parametrize("conflict", ["source", "legacy-key", "legacy-id"])
def test_import_denies_conflicts_with_unimported_reservations(env, maintenance, conflict):
    """Missing admission guard must fail before a conflicting manifest consumes its key."""
    s, p, root, bundle = env
    first = migration_fixture(bundle)
    first["inventory"]["revision"] = 5
    first["inventory"]["admissions"].extend(["prj_b", "prj_c"])
    source = dict(
        project_id="prj_b",
        source_system="other",
        source_instance_id="other",
        external_project_id="external-reserved",
    )
    reserved = dict(
        project_id="prj_b",
        task_id="reserved-unimported",
        source_system="other",
        source_instance_id="other",
        source_task_id="reserved-source",
    )
    first["inventory"]["sources"].append(source)
    first["inventory"]["legacy_allocations"].append(reserved)
    first_manifest = maintenance.dry_run(first)
    first_path = root / "first.json"
    first_sha = seal(first_path, first_manifest)
    s.close()
    first_receipt = maintenance.import_bound(
        root / "tasks.db", root / "checkpoint.jsonl", first_path, first_sha, 0
    )
    before = _import_state(type(s), root)
    assert set(before["replay"]["tasks"]) == {"legacy-stable-bytes"}
    assert before["replay"]["policy"]["inventory"] == bundle["inventory"]
    assert source in before["replay"]["known_inventory"]["sources"]
    assert reserved in before["replay"]["known_inventory"]["legacy_allocations"]

    second = migration_fixture(bundle)
    second["inventory"]["revision"] = 6
    second["inventory"]["admissions"].extend(["prj_b", "prj_c"])
    row = second["rows"][0]
    snapshot = json.loads(row["snapshot_json"])
    snapshot.update(task_id="second-legacy", source_task_id="second-source")
    row.update(
        idempotency_key="import-second", snapshot_json=canonical_json(snapshot).decode()
    )
    row["snapshot_sha256"] = hashlib.sha256(row["snapshot_json"].encode()).hexdigest()
    row["identity"]["source_task_id"] = "second-source"
    second["inventory"]["legacy_allocations"].append(
        dict(task_id="second-legacy", **row["identity"])
    )
    conflicting = json.loads(canonical_json(second))
    if conflict == "source":
        conflicting["inventory"]["sources"].append(dict(source, project_id="prj_c"))
    elif conflict == "legacy-key":
        conflicting["inventory"]["legacy_allocations"].append(
            dict(reserved, task_id="reassigned")
        )
    else:
        conflicting["inventory"]["legacy_allocations"].append(
            dict(reserved, source_task_id="reassigned-source")
        )
    denied_manifest = maintenance.dry_run(conflicting)
    assert denied_manifest["rows"][0]["classification"] == "BOUND_CANDIDATE"
    second_path = root / "second.json"
    with pytest.raises(s.Error, match="invalid_import_inventory") as denied:
        maintenance.import_bound(
            root / "tasks.db",
            root / "checkpoint.jsonl",
            second_path,
            seal(second_path, denied_manifest),
            0,
        )
    assert denied.value.status == 409
    assert _import_state(type(s), root) == before

    # Corrected intent reuses the denied key; omitted reservations remain in the union.
    corrected_manifest = maintenance.dry_run(second)
    corrected_sha = seal(second_path, corrected_manifest)
    receipt = maintenance.import_bound(
        root / "tasks.db", root / "checkpoint.jsonl", second_path, corrected_sha, 0
    )
    assert receipt["idempotency_key"] == "import-second"
    assert receipt["task_id"] == "second-legacy"
    assert receipt["event_sequence"] == first_receipt["event_sequence"] + 1
    after = _import_state(type(s), root)
    assert after["statistics"] == dict(journal=3, tasks=2, operations=3, outbox=2)
    assert after["replay"]["known_inventory"]["revision"] == 6
    assert source in after["replay"]["known_inventory"]["sources"]
    assert reserved in after["replay"]["known_inventory"]["legacy_allocations"]
    assert (
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", first_path, first_sha, 0
        )
        == first_receipt
    )
    assert (
        maintenance.import_bound(
            root / "tasks.db", root / "checkpoint.jsonl", second_path, corrected_sha, 0
        )
        == receipt
    )
    assert _import_state(type(s), root) == after
