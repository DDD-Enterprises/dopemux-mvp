"""Local-only maintenance. All paths and approval digests must be explicit.

No HTTP/MCP registration, automatic admission or live discovery is provided.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from .admission import AllocationInventory, merge_known_inventory, safe_path
from .completion import DenyCompletionVerifier, VerifiedCompletion
from .models import PMTask
from .ownership import (
    StrictModel,
    ID,
    Key,
    Digest,
    Positive,
    Identity,
    EvidenceRef,
    canonical_json,
    parse_json_object,
    identifier,
)
from .sqlite_store import SQLiteTaskStore, StoreError, ZERO, _fsync_directory


class Candidate(StrictModel):
    idempotency_key: Key
    snapshot_json: str
    snapshot_sha256: Digest
    identity: Identity | None
    dependencies: list[ID]
    completion_policy_id: ID
    completion_policy_version: Positive
    ownership_evidence_sha256: Digest | None
    completion_evidence_ref: EvidenceRef | None


class MigrationInput(StrictModel):
    schema_version: Literal["dopemux.pm.migration-input.v1"]
    project_id: ID
    expected_admission_epoch: Positive
    inventory: AllocationInventory
    rows: list[Candidate]


class ManifestRow(Candidate):
    classification: Literal["UNBOUND", "BOUND_CANDIDATE", "QUARANTINED"]
    reasons: list[ID]


class ImportManifest(StrictModel):
    schema_version: Literal["dopemux.pm.import-manifest.v1"]
    project_id: ID
    expected_admission_epoch: Positive
    inventory: AllocationInventory
    source_input_sha256: Digest
    import_order: list[Annotated[int, Field(strict=True, ge=0)]]
    rows: list[ManifestRow]


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _legacy(row):
    raw = row["snapshot_json"].encode("utf-8")
    if _digest(raw) != row["snapshot_sha256"]:
        raise ValueError("legacy_digest_mismatch")
    snapshot = parse_json_object(raw)
    if set(snapshot) - set(PMTask.model_fields):
        raise ValueError("unknown_legacy_fields")
    if type(snapshot.get("version")) is not int or snapshot["version"] < 1:
        raise ValueError("legacy_version_invalid")
    identifier(snapshot["task_id"])
    PMTask.model_validate(snapshot)  # Preserve the legacy serializer's supported shape.
    if snapshot["status"] not in {"TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELED"}:
        raise ValueError("legacy_status_invalid")
    if row["dependencies"] != sorted(set(row["dependencies"])):
        raise ValueError("invalid_dependencies")
    return snapshot


def _task_from_row(project, row):
    old = _legacy(row)
    return dict(
        project_id=project,
        task_id=old["task_id"],
        task_id_scheme="legacy-v1",
        identity=row["identity"],
        ownership_state="BOUND",
        binding_version=1,
        version=old["version"],
        status=old["status"],
        title=old["title"],
        description=old.get("description"),
        dependencies=row["dependencies"],
        linked_ids=old.get("linked_ids", {}),
        completion_policy_id=row["completion_policy_id"],
        completion_policy_version=row["completion_policy_version"],
        completion_verification=None,
        source_binding_ref=None,
        legacy_snapshot_sha256=row["snapshot_sha256"],
        legacy_snapshot_json=row["snapshot_json"],
        ownership_evidence_sha256=row["ownership_evidence_sha256"],
    )


def _verify_completion(verifier, project, row):
    task = _task_from_row(project, row)
    if row["completion_evidence_ref"] is None:
        raise ValueError("completion_unqualified")
    verified = verifier.verify(
        project_id=project,
        task=task,
        reference=row["completion_evidence_ref"],
        policy={
            "id": row["completion_policy_id"],
            "version": row["completion_policy_version"],
            "kind": "workflow-kernel-v1",
        },
    )
    if type(verified) is not VerifiedCompletion or (
        verified.project_id,
        verified.task_id,
        verified.task_version,
        verified.policy_id,
        verified.policy_version,
    ) != (
        project,
        task["task_id"],
        task["version"],
        row["completion_policy_id"],
        row["completion_policy_version"],
    ):
        raise ValueError("completion_binding_mismatch")
    if (
        _digest(verified.snapshot) != verified.snapshot_sha256
        or verified.snapshot_sha256 != row["completion_evidence_ref"]["sha256"]
    ):
        raise ValueError("completion_digest_mismatch")
    return verified


def dry_run(data: dict, *, completion_verifier=None) -> dict:
    source = MigrationInput.model_validate(data).model_dump()
    verifier = completion_verifier or DenyCompletionVerifier()
    rows = []
    ids = []
    for row in source["rows"]:
        result = dict(row, classification="BOUND_CANDIDATE", reasons=[])
        tid = None
        try:
            old = _legacy(row)
            tid = old["task_id"]
            identity = row["identity"]
            if identity is None or row["ownership_evidence_sha256"] is None:
                result.update(classification="UNBOUND", reasons=["ownership_unapproved"])
            elif (
                identity["project_id"] != source["project_id"]
                or old["source"] != identity["source_system"]
                or (
                    old.get("source_task_id") is not None
                    and old["source_task_id"] != identity["source_task_id"]
                )
            ):
                result.update(classification="QUARANTINED", reasons=["source_identity_conflict"])
            elif not any(
                a == dict(task_id=tid, **identity)
                for a in source["inventory"]["legacy_allocations"]
            ):
                result.update(classification="UNBOUND", reasons=["allocation_unapproved"])
            elif old["status"] == "DONE":
                try:
                    _verify_completion(verifier, source["project_id"], row)
                except (ValueError, PermissionError, OSError):
                    result.update(classification="UNBOUND", reasons=["completion_unqualified"])
            elif row["completion_evidence_ref"] is not None:
                result.update(
                    classification="QUARANTINED", reasons=["unexpected_completion_evidence"]
                )
        except (ValueError, KeyError, TypeError):
            result.update(classification="QUARANTINED", reasons=["invalid_legacy_snapshot"])
        rows.append(result)
        ids.append(tid)
    counts = Counter(tid for tid in ids if tid is not None)
    keys = Counter(r["idempotency_key"] for r in rows)
    for row, tid in zip(rows, ids):
        if (tid and counts[tid] > 1) or keys[row["idempotency_key"]] > 1:
            row.update(classification="QUARANTINED", reasons=["duplicate_migration_identity"])
    # Only candidates whose predecessors have already been ordered are importable.
    ready = set()
    order = []
    remaining = {i for i, r in enumerate(rows) if r["classification"] == "BOUND_CANDIDATE"}
    while remaining:
        progress = [i for i in sorted(remaining) if set(rows[i]["dependencies"]) <= ready]
        if not progress:
            break
        for i in progress:
            ready.add(ids[i])
            remaining.remove(i)
            order.append(i)
    for i in remaining:
        rows[i].update(classification="UNBOUND", reasons=["dependency_unbound_or_cycle"])
    return dict(
        schema_version="dopemux.pm.import-manifest.v1",
        project_id=source["project_id"],
        expected_admission_epoch=source["expected_admission_epoch"],
        inventory=source["inventory"],
        source_input_sha256=_digest(canonical_json(source)),
        import_order=order,
        rows=rows,
    )


def _approved(path, sha):
    raw = safe_path(path).read_bytes()
    if _digest(raw) != sha:
        raise ValueError("Approval digest mismatch")
    return parse_json_object(raw)


def import_bound(
    database, checkpoint, manifest_path, approved_sha256, row_index, *, completion_verifier=None
):
    manifest = ImportManifest.model_validate(_approved(manifest_path, approved_sha256)).model_dump()
    verifier = completion_verifier or DenyCompletionVerifier()
    source = dict(
        schema_version="dopemux.pm.migration-input.v1",
        project_id=manifest["project_id"],
        expected_admission_epoch=manifest["expected_admission_epoch"],
        inventory=manifest["inventory"],
        rows=[
            {k: v for k, v in r.items() if k not in {"classification", "reasons"}}
            for r in manifest["rows"]
        ],
    )
    if type(row_index) is not int or not 0 <= row_index < len(manifest["rows"]):
        raise ValueError("Invalid manifest row")
    row = manifest["rows"][row_index]
    if row["classification"] != "BOUND_CANDIDATE":
        raise ValueError("Staging row is not admitted")
    store = SQLiteTaskStore(database, checkpoint, completion_verifier=verifier)
    try:
        actor = "operator-local:" + str(os.getuid())
        body = dict(
            schema_version="dopemux.pm.import-command.v1",
            idempotency_key=row["idempotency_key"],
            approved_manifest_sha256=approved_sha256,
            row_index=row_index,
            manifest=manifest,
        )
        # Historical authorized replay must not reopen mutable evidence.
        old = store._replay_operation(actor, "maintenance-cli", "task.import_bound", body)
        if old is not None:
            return old
        if dry_run(source, completion_verifier=verifier) != manifest:
            raise ValueError("Manifest classification mismatch")
        policy = store._policy()
        inventory = manifest["inventory"]
        if manifest["project_id"] != store.project_id:
            raise StoreError(404, "not_found")
        if manifest["expected_admission_epoch"] != policy["admission_epoch"]:
            raise StoreError(409, "stale_admission_epoch")
        if policy["status"] != "ACTIVE":
            raise StoreError(503, "admission_unavailable")
        if inventory["revision"] < policy["inventory"]["revision"]:
            raise ValueError("Stale allocation inventory")
        for field in ("admissions", "sources", "legacy_allocations"):
            if any(value not in inventory[field] for value in policy["inventory"][field]):
                raise ValueError("Incomplete allocation inventory")
        for existing in store.replay()["tasks"].values():
            if (
                existing["task_id_scheme"] == "legacy-v1"
                and dict(task_id=existing["task_id"], **existing["identity"])
                not in inventory["legacy_allocations"]
            ):
                raise ValueError("Missing existing legacy allocation")
        task = _task_from_row(store.project_id, row)
        store._source(policy, task["identity"])
        configured = next(
            (p for p in policy["completion_policies"] if p["id"] == task["completion_policy_id"]),
            None,
        )
        if configured is None or configured["version"] != task["completion_policy_version"]:
            raise ValueError("Completion policy mismatch")
        completion = (
            _verify_completion(verifier, store.project_id, row)
            if task["status"] == "DONE"
            else None
        )
        with store._transaction():
            try:
                merge_known_inventory(store.replay()["known_inventory"], inventory)
            except ValueError as exc:
                raise StoreError(409, "invalid_import_inventory") from exc
            if (
                _digest(safe_path(Path(policy["registry_path"])).read_bytes())
                != policy["registry_sha256"]
            ):
                raise ValueError("Registry handoff drift")
            store._identity_absent(task["task_id"], task["identity"])
            store._dependencies(task["dependencies"])
            old_status = task["status"]
            task["version"] += 1
            if completion:
                task["completion_verification"] = completion.receipt_value()
            return store._append(
                "task.import_bound",
                body,
                actor,
                "maintenance-cli",
                "operator-local",
                "os-uid",
                task=task,
                from_status=old_status,
                completion=completion,
            )
    finally:
        store.close()


class IndependentReceipt(StrictModel):
    event_sequence: Positive
    receipt_sha256: Digest


class ReconciliationBundle(StrictModel):
    schema_version: Literal["dopemux.pm.reconciliation-bundle.v1"]
    idempotency_key: Key
    project_id: ID
    store_uuid: ID
    db_sequence: Positive
    db_head: Digest
    anchor_sequence: Annotated[int, Field(strict=True, ge=0)]
    anchor_head: Digest
    anchor_sha256: Digest
    acknowledged_history_preserved: bool
    operator_decision_ref: ID
    independent_receipts: list[IndependentReceipt]


def reconcile(database, checkpoint, bundle_path, approved_sha256):
    bundle = ReconciliationBundle.model_validate(
        _approved(bundle_path, approved_sha256)
    ).model_dump()
    if bundle["acknowledged_history_preserved"] is not True:
        raise ValueError("Acknowledged history unknown; HOLD")
    store = SQLiteTaskStore(database, checkpoint, _reconcile=True)
    try:
        body = dict(
            schema_version="dopemux.pm.reconcile-command.v1",
            idempotency_key=bundle["idempotency_key"],
            approved_bundle_sha256=approved_sha256,
            bundle=bundle,
        )
        actor = "operator-local:" + str(os.getuid())
        replay = store.replay()
        # A completed reconciliation can be read only after the current anchor verifies.
        if store._db.execute(
            "SELECT 1 FROM operations WHERE principal=? AND kind=? AND key=?",
            (actor, "checkpoint.reconcile", body["idempotency_key"]),
        ).fetchone():
            store._check_anchor(replay)
            return store._replay_operation(actor, "maintenance-cli", "checkpoint.reconcile", body)
        raw = Path(checkpoint).read_bytes() if Path(checkpoint).exists() else b""
        if not raw or bundle["anchor_sequence"] == 0:
            raise ValueError("Acknowledged history missing; HOLD")
        if _digest(raw) != bundle["anchor_sha256"]:
            raise ValueError("Anchor bytes changed")
        if (
            bundle["project_id"],
            bundle["store_uuid"],
            bundle["db_sequence"],
            bundle["db_head"],
        ) != (
            store.project_id,
            store.store_uuid,
            replay["sequence"],
            replay["heads"][replay["sequence"]],
        ):
            raise ValueError("Exact database head mismatch")
        if raw and not raw.endswith(b"\n"):
            raise ValueError("Torn anchor; preserve and investigate")
        previous = 0
        head = ZERO
        for line in raw.splitlines():
            entry = parse_json_object(line)
            seq = entry["event_sequence"]
            if (
                type(seq) is not int
                or seq <= previous
                or replay["heads"].get(seq) != entry["chain_head"]
                or entry["project_id"] != store.project_id
                or entry["store_uuid"] != store.store_uuid
            ):
                raise ValueError("Acknowledged history missing")
            previous = seq
            head = entry["chain_head"]
        if (previous, head) != (
            bundle["anchor_sequence"],
            bundle["anchor_head"],
        ) or previous >= replay["sequence"]:
            raise ValueError("Not a proved DB-ahead reconciliation")
        receipts = {
            r["event_sequence"]: _digest(canonical_json(r)) for r in replay["operations"].values()
        }
        if any(
            receipts.get(r["event_sequence"]) != r["receipt_sha256"]
            for r in bundle["independent_receipts"]
        ):
            raise ValueError("Independent receipt missing or mismatched")
        with store._transaction():
            return store._append(
                "checkpoint.reconcile", body, actor, "maintenance-cli", "operator-local", "os-uid"
            )
    finally:
        store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Explicit local PM maintenance; stop runtime first"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    dry = commands.add_parser("dry-run")
    dry.add_argument("--input", type=Path, required=True)
    dry.add_argument("--approved-sha256", required=True)
    dry.add_argument("--output", type=Path, required=True)
    for name in ("bootstrap", "replace-admission", "import-bound", "reconcile"):
        p = commands.add_parser(name)
        p.add_argument("--database", type=Path, required=True)
        p.add_argument("--checkpoint", type=Path, required=True)
        p.add_argument("--bundle", type=Path, required=True)
        p.add_argument("--approved-sha256", required=True)
        if name == "import-bound":
            p.add_argument("--row", type=int, required=True)
    args = parser.parse_args(argv)
    if args.command == "dry-run":
        result = dry_run(_approved(args.input, args.approved_sha256))
        safe_path(args.output, exists=False)
        fd = os.open(str(args.output), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as out:
            out.write(canonical_json(result))
            out.flush()
            os.fsync(out.fileno())
        _fsync_directory(args.output.parent)
        print(_digest(canonical_json(result)))
        return 0
    fn = {
        "bootstrap": SQLiteTaskStore.bootstrap,
        "replace-admission": SQLiteTaskStore.replace_admission,
        "import-bound": import_bound,
        "reconcile": reconcile,
    }[args.command]
    extra = [args.row] if args.command == "import-bound" else []
    receipt = fn(args.database, args.checkpoint, args.bundle, args.approved_sha256, *extra)
    print(canonical_json(receipt).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
