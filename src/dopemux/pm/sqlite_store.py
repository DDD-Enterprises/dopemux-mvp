"""One-project durable PM writer. No default paths, discovery or network effects."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
import uuid

from .admission import (
    approved_admission,
    safe_path,
    merge_known_inventory,
    validate_admission_replacement,
)
from .completion import DenyCompletionVerifier, VerifiedCompletion
from .ownership import (
    ContractError,
    CreateTaskCommand,
    TransitionCommand,
    canonical_json,
    command_digest,
    new_task_id,
    parse_json_object,
    validate_receipt,
)
from .principal import VerifiedPrincipal, request_binding


class StoreError(RuntimeError):
    def __init__(self, status: int, code: str):
        self.status, self.code = status, code
        super().__init__(code)


ZERO = "0" * 64
SCHEMA = "dopemux.pm.store.v1"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _fsync_directory(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class SQLiteTaskStore:
    """Lifetime lock and serialized transactions; maintenance never overlaps runtime.

    Host code and injected verifiers are trusted composition, not network input.
    `fault_hook` exists for deterministic isolated crash tests only.
    """

    Error = StoreError

    def __init__(
        self,
        database: Path,
        checkpoint: Path,
        *,
        completion_verifier=None,
        _bootstrap=None,
        _reconcile=False,
    ):
        self.path = safe_path(database, exists=_bootstrap is None)
        self.checkpoint = safe_path(checkpoint, exists=_bootstrap is None and not _reconcile)
        if self.path == self.checkpoint:
            raise StoreError(503, "store_paths_conflict")
        self._mutex = threading.RLock()
        self._db = None
        self._lock_fd = None
        self._closed = False
        self._held = False
        self._ack_sequence = 0
        self.fault_hook = None
        self.completion_verifier = completion_verifier or DenyCompletionVerifier()
        try:
            lock = safe_path(Path(str(self.path) + ".lock"), exists=False)
            self._lock_fd = os.open(str(lock), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise StoreError(503, "writer_unavailable") from exc
            if _bootstrap is not None:
                if self.path.exists() or self.checkpoint.exists():
                    raise StoreError(409, "bootstrap_target_exists")
                fd = os.open(
                    str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600
                )
                os.close(fd)
            self._db = sqlite3.connect(
                str(self.path), isolation_level=None, timeout=0, check_same_thread=False
            )
            self._db.execute("PRAGMA foreign_keys=ON")
            self._db.execute("PRAGMA synchronous=FULL")
            self._db.execute("PRAGMA journal_mode=DELETE")
            if _bootstrap is not None:
                self._create_schema(*_bootstrap)
            else:
                metadata = dict(self._db.execute("SELECT key,value FROM metadata"))
                if metadata.get("schema") != SCHEMA:
                    raise StoreError(503, "unsupported_store_schema")
                self.project_id, self.store_uuid = metadata["project_id"], metadata["store_uuid"]
                replay = self.replay()
                if not _reconcile:
                    self._check_anchor(replay)
                self._check_projections(replay)
        except Exception:
            self.close()
            raise

    def _create_schema(self, bundle, operator):
        self.project_id, self.store_uuid = bundle.project_id, bundle.store_uuid
        self._db.executescript("""
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE journal(sequence INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL,
                payload BLOB NOT NULL, digest TEXT NOT NULL);
            CREATE TABLE tasks(task_id TEXT PRIMARY KEY, snapshot BLOB NOT NULL);
            CREATE TABLE policy(singleton INTEGER PRIMARY KEY CHECK(singleton=1), snapshot BLOB NOT NULL);
            CREATE TABLE operations(principal TEXT, kind TEXT, key TEXT, digest TEXT NOT NULL,
                receipt BLOB NOT NULL, sequence INTEGER NOT NULL REFERENCES journal(sequence),
                PRIMARY KEY(principal,kind,key));
            CREATE TABLE outbox(sequence INTEGER NOT NULL REFERENCES journal(sequence), task_id TEXT NOT NULL,
                destination TEXT NOT NULL, envelope BLOB NOT NULL, delivered INTEGER NOT NULL DEFAULT 0,
                error TEXT, PRIMARY KEY(sequence,destination));
        """)
        with self._transaction():
            self._db.executemany(
                "INSERT INTO metadata VALUES (?,?)",
                [
                    ("schema", SCHEMA),
                    ("project_id", self.project_id),
                    ("store_uuid", self.store_uuid),
                ],
            )
            policy = bundle.model_dump()
            policy["admission_epoch"] = 1
            operator.recheck()
            self._admin_append("admission.bootstrap", bundle, operator, policy=policy)

    @classmethod
    def bootstrap(cls, database, checkpoint, bundle_path, approved_sha256):
        bundle, operator = approved_admission(bundle_path, approved_sha256)
        if bundle.expected_epoch != 0:
            raise StoreError(409, "bootstrap_expected_absent")
        store = cls(database, checkpoint, _bootstrap=(bundle, operator))
        try:
            return store._last_receipt()
        finally:
            store.close()

    @classmethod
    def replace_admission(cls, database, checkpoint, bundle_path, approved_sha256):
        bundle, operator = approved_admission(bundle_path, approved_sha256)
        store = cls(database, checkpoint)
        try:
            with store._transaction():
                if bundle.project_id != store.project_id or bundle.store_uuid != store.store_uuid:
                    raise StoreError(409, "store_identity_mismatch")
                body = store._admin_body(bundle, operator)
                old = store._replay_operation(
                    operator.principal_id, "maintenance-cli", "admission.replace", body
                )
                if old is not None:
                    return old
                policy = store._policy()
                if bundle.expected_epoch != policy["admission_epoch"]:
                    raise StoreError(409, "stale_admission_epoch")
                if (bundle.workspace_id, bundle.instance_id) != (
                    policy["workspace_id"],
                    policy["instance_id"],
                ):
                    raise StoreError(409, "writer_identity_immutable")
                replacement = bundle.model_dump()
                replacement["admission_epoch"] = policy["admission_epoch"] + 1
                history = store.replay()
                try:
                    validate_admission_replacement(
                        policy,
                        replacement,
                        history["tasks"].values(),
                        history["known_inventory"],
                    )
                except ValueError as exc:
                    raise StoreError(409, "invalid_admission_replacement") from exc
                operator.recheck()
                return store._admin_append(
                    "admission.replace", bundle, operator, policy=replacement
                )
        finally:
            store.close()

    def close(self):
        # Keep the writer lock until in-flight commits and their checkpoint finish.
        with self._mutex:
            self._closed = True
            if self._db is not None:
                self._db.close()
                self._db = None
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None

    def _available(self):
        if self._held or self._closed:
            raise StoreError(503, "writer_held")

    def _fault(self, point):
        if self.fault_hook is not None:
            self.fault_hook(point)

    @contextmanager
    def _transaction(self):
        with self._mutex:
            self._available()
            self._db.execute("BEGIN IMMEDIATE")
            before = self._head()[0]
            try:
                yield
                self._fault("before_commit")
                self._db.execute("COMMIT")
            except BaseException:
                if self._db.in_transaction:
                    self._db.execute("ROLLBACK")
                raise
            if self._head()[0] != before:
                try:
                    self._fault("after_commit")
                    self._advance_anchor()
                except BaseException as exc:
                    self._held = True
                    raise StoreError(503, "UNKNOWN_checkpoint_unacknowledged") from exc
                self._fault("after_checkpoint")

    def _head(self):
        row = self._db.execute(
            "SELECT sequence,digest FROM journal ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        return row if row else (0, ZERO)

    def _advance_anchor(self):
        sequence, head = self._head()
        raw = (
            canonical_json(
                dict(
                    project_id=self.project_id,
                    store_uuid=self.store_uuid,
                    event_sequence=sequence,
                    chain_head=head,
                )
            )
            + b"\n"
        )
        safe_path(self.checkpoint, exists=False)
        fd = os.open(
            str(self.checkpoint), os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600
        )
        try:
            with os.fdopen(fd, "ab", closefd=False) as f:
                f.write(raw)
                f.flush()
                os.fsync(fd)
        finally:
            os.close(fd)
        _fsync_directory(self.checkpoint.parent)
        _fsync_directory(self.path.parent)
        self._ack_sequence = sequence

    def _check_anchor(self, replay):
        try:
            raw = self.checkpoint.read_bytes()
            if not raw.endswith(b"\n"):
                raise ValueError("torn")
            entries = [parse_json_object(line) for line in raw.splitlines()]
            previous = 0
            for entry in entries:
                seq = entry["event_sequence"]
                if (
                    type(seq) is not int
                    or seq <= previous
                    or set(entry) != {"project_id", "store_uuid", "event_sequence", "chain_head"}
                ):
                    raise ValueError("sequence")
                if entry["project_id"] != self.project_id or entry["store_uuid"] != self.store_uuid:
                    raise ValueError("identity")
                if replay["heads"].get(seq) != entry["chain_head"]:
                    raise ValueError("head")
                previous = seq
            if not entries or previous != replay["sequence"]:
                raise ValueError("head mismatch")
            self._ack_sequence = previous
        except (KeyError, ValueError, OSError) as exc:
            raise StoreError(503, "checkpoint_integrity_hold") from exc

    def _policy(self):
        row = self._db.execute("SELECT snapshot FROM policy WHERE singleton=1").fetchone()
        if not row:
            raise StoreError(503, "admission_unavailable")
        return parse_json_object(row[0])

    def _auth(self, project, principal, operation, body, action):
        self._available()
        if (
            type(principal) is not VerifiedPrincipal
            or not isinstance(principal.expires_at, (int, float))
            or not principal.expires_at > time.time()
        ):
            raise StoreError(401, "invalid_authentication")
        if principal.request_binding != request_binding(project, operation, body):
            raise StoreError(401, "invalid_authentication")
        policy = self._policy()
        if principal.audience != f"dopemux.pm:{policy['instance_id']}:{project}":
            raise StoreError(401, "invalid_authentication")
        if project != self.project_id:
            raise StoreError(404, "not_found")
        grant = next(
            (g for g in policy["grants"] if g["principal_id"] == principal.principal_id), None
        )
        if (
            not grant
            or principal.client_id not in grant["client_ids"]
            or principal.verifier_id not in grant["verifier_ids"]
            or principal.credential_generation not in grant["credential_generations"]
            or action not in grant["actions"]
        ):
            raise StoreError(404, "not_found")
        if action != "task.read" and policy["status"] != "ACTIVE":
            raise StoreError(503, "admission_unavailable")
        return policy

    def _task(self, task_id):
        row = self._db.execute("SELECT snapshot FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            raise StoreError(404, "not_found")
        task = parse_json_object(row[0])
        if task["project_id"] != self.project_id or task["ownership_state"] != "BOUND":
            raise StoreError(503, "ownership_integrity_hold")
        return task

    def _digest(self, principal, client, kind, body):
        return command_digest(
            body,
            project_id=self.project_id,
            principal_id=principal,
            client_id=client,
            operation_kind=kind,
        )

    def _replay_operation(self, principal, client, kind, body):
        row = self._db.execute(
            "SELECT digest,receipt,sequence FROM operations WHERE principal=? AND kind=? AND key=?",
            (principal, kind, body["idempotency_key"]),
        ).fetchone()
        if row:
            if row[0] != self._digest(principal, client, kind, body):
                raise StoreError(409, "fingerprint_mismatch")
            if row[2] > self._ack_sequence:
                raise StoreError(503, "checkpoint_integrity_hold")
            return parse_json_object(row[1])
        return None

    def _source(self, policy, identity, principal=None):
        if identity["project_id"] != self.project_id:
            raise StoreError(404, "not_found")
        source = next(
            (
                s
                for s in policy["sources"]
                if s["source_system"] == identity["source_system"]
                and s["source_instance_id"] == identity["source_instance_id"]
            ),
            None,
        )
        if not source or (
            principal is not None and principal not in source["producer_principal_ids"]
        ):
            raise StoreError(404, "not_found")
        return source

    def _dependencies(self, dependencies, *, completed=False):
        for dep in dependencies:
            try:
                task = self._task(dep)
            except StoreError:
                raise StoreError(409, "dependency_unavailable") from None
            if completed and (task["status"] != "DONE" or not task["completion_verification"]):
                raise StoreError(409, "dependency_unavailable")

    def create(self, project, body, principal):
        body = CreateTaskCommand.model_validate(body).model_dump()
        with self._transaction():
            policy = self._auth(project, principal, "task.create", body, "task.create")
            old = self._replay_operation(
                principal.principal_id, principal.client_id, "task.create", body
            )
            if old is not None:
                return old
            if body["admission_epoch"] != policy["admission_epoch"]:
                raise StoreError(409, "stale_admission_epoch")
            self._source(policy, body["identity"], principal.principal_id)
            tid = new_task_id(body["identity"])
            self._identity_absent(tid, body["identity"])
            self._dependencies(body["dependencies"])
            completion_policy = next(
                (
                    p
                    for p in policy["completion_policies"]
                    if p["id"] == body["completion_policy_id"]
                ),
                None,
            )
            if not completion_policy:
                raise StoreError(409, "completion_policy_unavailable")
            task = dict(
                project_id=project,
                task_id=tid,
                task_id_scheme="pm-v2",
                identity=body["identity"],
                ownership_state="BOUND",
                binding_version=1,
                version=1,
                status="TODO",
                title=body["title"],
                description=body["description"],
                dependencies=body["dependencies"],
                linked_ids=body["linked_ids"],
                completion_policy_id=completion_policy["id"],
                completion_policy_version=completion_policy["version"],
                completion_verification=None,
                source_binding_ref=None,
            )
            return self._append(
                "task.create",
                body,
                principal.principal_id,
                principal.client_id,
                principal.verifier_id,
                principal.credential_generation,
                task=task,
            )

    def _identity_absent(self, tid, identity):
        for (raw,) in self._db.execute("SELECT snapshot FROM tasks"):
            task = parse_json_object(raw)
            if task["task_id"] == tid or task["identity"] == identity:
                raise StoreError(409, "identity_exists")

    def _transition_state(self, project, body, principal):
        policy = self._auth(
            project, principal, "task.transition", body, "task.transition." + body["transition"]
        )
        old = self._replay_operation(
            principal.principal_id, principal.client_id, "task.transition", body
        )
        if old is not None:
            return policy, None, old
        if body["admission_epoch"] != policy["admission_epoch"]:
            raise StoreError(409, "stale_admission_epoch")
        task = self._task(body["task_id"])
        if (
            task["version"] != body["expected_version"]
            or task["binding_version"] != body["expected_binding_version"]
        ):
            raise StoreError(409, "stale_task_version")
        pairs = {
            "start": ({"TODO"}, "IN_PROGRESS"),
            "resume": ({"BLOCKED"}, "IN_PROGRESS"),
            "block": ({"TODO", "IN_PROGRESS"}, "BLOCKED"),
            "done": ({"IN_PROGRESS"}, "DONE"),
        }
        if task["status"] not in pairs[body["transition"]][0]:
            raise StoreError(409, "illegal_transition")
        if body["transition"] in {"start", "resume"}:
            self._dependencies(task["dependencies"], completed=True)
        return policy, task, None

    def transition(self, project, body, principal):
        body = TransitionCommand.model_validate(body).model_dump()
        with self._mutex:
            # Resolve/seal evidence outside the SQL transaction. Recheck all gates inside it.
            policy, task, old = self._transition_state(project, body, principal)
            if old is not None:
                return old
            completion = None
            if body["transition"] == "done":
                configured = next(
                    (
                        p
                        for p in policy["completion_policies"]
                        if p["id"] == task["completion_policy_id"]
                    ),
                    None,
                )
                if not configured or configured["version"] != task["completion_policy_version"]:
                    raise StoreError(409, "completion_policy_unavailable")
                try:
                    completion = self.completion_verifier.verify(
                        project_id=project,
                        task=json.loads(canonical_json(task)),
                        reference=body["completion_evidence_ref"],
                        policy=dict(configured),
                    )
                except (PermissionError, ValueError, OSError) as exc:
                    raise StoreError(409, "completion_unavailable") from exc
                if type(completion) is not VerifiedCompletion or (
                    completion.project_id,
                    completion.task_id,
                    completion.task_version,
                    completion.policy_id,
                    completion.policy_version,
                ) != (
                    project,
                    task["task_id"],
                    task["version"],
                    configured["id"],
                    configured["version"],
                ):
                    raise StoreError(409, "completion_binding_mismatch")
                if (
                    _sha(completion.snapshot) != completion.snapshot_sha256
                    or completion.snapshot_sha256 != body["completion_evidence_ref"]["sha256"]
                ):
                    raise StoreError(409, "completion_digest_mismatch")
            with self._transaction():
                policy, task, old = self._transition_state(project, body, principal)
                if old is not None:
                    return old
                before = task["status"]
                task["status"] = {
                    "start": "IN_PROGRESS",
                    "resume": "IN_PROGRESS",
                    "block": "BLOCKED",
                    "done": "DONE",
                }[body["transition"]]
                task["version"] += 1
                task["completion_verification"] = completion.receipt_value() if completion else None
                return self._append(
                    "task.transition",
                    body,
                    principal.principal_id,
                    principal.client_id,
                    principal.verifier_id,
                    principal.credential_generation,
                    task=task,
                    from_status=before,
                    completion=completion,
                )

    @staticmethod
    def _admin_body(bundle, operator):
        return dict(
            schema_version="dopemux.pm.admission-command.v1",
            idempotency_key=bundle.idempotency_key,
            approved_bundle_sha256=operator.approval_sha256,
            expected_epoch=bundle.expected_epoch,
            bundle=bundle.model_dump(),
        )

    def _admin_append(self, kind, bundle, operator, *, policy):
        return self._append(
            kind,
            self._admin_body(bundle, operator),
            operator.principal_id,
            "maintenance-cli",
            "operator-local",
            "os-uid",
            policy=policy,
        )

    def _append(
        self,
        kind,
        body,
        principal,
        client,
        verifier,
        generation,
        *,
        task=None,
        policy=None,
        from_status=None,
        completion=None,
    ):
        sequence, previous = self._head()
        sequence += 1
        event_id = "pme_" + uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        last = self._db.execute(
            "SELECT payload FROM journal ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        if last:
            now = max(now, parse_json_object(last[0])["committed_at_utc"])
        current = policy if policy is not None else self._policy()
        digest = self._digest(principal, client, kind, body)
        receipt = dict(
            schema_version="dopemux.pm.operation-receipt.v1",
            outcome="APPLIED",
            receipt_id="pmr_" + uuid.uuid4().hex,
            event_id=event_id,
            event_sequence=sequence,
            project_id=self.project_id,
            principal_id=principal,
            client_id=client,
            verifier_id=verifier,
            credential_generation=generation,
            operation_kind=kind,
            idempotency_key=body["idempotency_key"],
            request_sha256=digest,
            committed_at_utc=now,
            admission_epoch_at_commit=current["admission_epoch"],
        )
        if task:
            if task["source_binding_ref"] is None:
                task["source_binding_ref"] = event_id
            task["updated_at_utc"] = now
            receipt.update(
                task_id=task["task_id"],
                binding_version=task["binding_version"],
                source_binding_ref=task["source_binding_ref"],
                version_before=task["version"] - 1,
                version_after=task["version"],
                from_status=from_status,
                to_status=task["status"],
                completion_verification=task["completion_verification"],
            )
        if kind == "task.transition":
            receipt["schema_version"] = "dopemux.pm.transition-receipt.v1"
            validate_receipt(
                receipt, body, project_id=self.project_id, principal_id=principal, client_id=client
            )
        event = dict(
            schema_version="dopemux.pm.event.v1",
            sequence=sequence,
            event_id=event_id,
            project_id=self.project_id,
            store_uuid=self.store_uuid,
            previous_sha256=previous,
            operation_kind=kind,
            command=body,
            receipt=receipt,
            task=task,
            policy=policy,
            completion_snapshot=completion.snapshot.decode("utf-8") if completion else None,
            destinations=current["destinations"] if task else [],
            committed_at_utc=now,
        )
        payload = canonical_json(event)
        event_hash = _sha(b"dopemux.pm.event.v1\0" + payload)
        self._db.execute(
            "INSERT INTO journal VALUES (?,?,?,?)", (sequence, event_id, payload, event_hash)
        )
        if task:
            self._db.execute(
                "INSERT OR REPLACE INTO tasks VALUES (?,?)", (task["task_id"], canonical_json(task))
            )
        if policy:
            self._db.execute(
                "INSERT OR REPLACE INTO policy VALUES (1,?)", (canonical_json(policy),)
            )
        self._db.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?)",
            (principal, kind, body["idempotency_key"], digest, canonical_json(receipt), sequence),
        )
        for destination in event["destinations"]:
            envelope = self._envelope(event, event_hash, destination)
            self._db.execute(
                "INSERT INTO outbox(sequence,task_id,destination,envelope) VALUES (?,?,?,?)",
                (sequence, task["task_id"], destination, canonical_json(envelope)),
            )
        return json.loads(canonical_json(receipt))

    @staticmethod
    def _envelope(event, digest, destination):
        return dict(
            project_id=event["project_id"],
            task_id=event["task"]["task_id"],
            event_id=event["event_id"],
            event_sequence=event["sequence"],
            event_sha256=digest,
            destination=destination,
            receipt_sha256=_sha(canonical_json(event["receipt"])),
            receipt=event["receipt"],
        )

    def _last_receipt(self):
        return parse_json_object(
            self._db.execute(
                "SELECT receipt FROM operations ORDER BY sequence DESC LIMIT 1"
            ).fetchone()[0]
        )

    def get_task(self, project, task_id, principal):
        with self._mutex:
            self._auth(project, principal, "task.read", {"task_id": task_id}, "task.read")
            return self._public_task(self._task(task_id))

    @staticmethod
    def _public_task(task):
        # Raw imported metadata remains operator provenance, not a scoped read view.
        return {
            key: value
            for key, value in task.items()
            if key not in {"legacy_snapshot_json", "ownership_evidence_sha256"}
        }

    def list_tasks(self, project, principal, *, offset=0, limit=100):
        if (
            type(offset) is not int
            or type(limit) is not int
            or offset < 0
            or not 1 <= limit <= 1000
        ):
            raise ContractError("Invalid pagination")
        with self._mutex:
            self._auth(
                project, principal, "task.read", {"offset": offset, "limit": limit}, "task.read"
            )
            total = self._db.execute("SELECT count(*) FROM tasks").fetchone()[0]
            tasks = [
                self._public_task(parse_json_object(r[0]))
                for r in self._db.execute(
                    "SELECT snapshot FROM tasks ORDER BY task_id LIMIT ? OFFSET ?", (limit, offset)
                )
            ]
            return {"project_id": project, "total": total, "tasks": tasks}

    def receipt(self, project, lookup, principal):
        if set(lookup) != {"operation_kind", "idempotency_key"}:
            raise ContractError("Invalid receipt lookup")
        with self._mutex:
            self._auth(project, principal, "task.read", lookup, "task.read")
            row = self._db.execute(
                "SELECT receipt,sequence FROM operations WHERE principal=? AND kind=? AND key=?",
                (principal.principal_id, lookup["operation_kind"], lookup["idempotency_key"]),
            ).fetchone()
            if not row:
                raise StoreError(404, "not_found")
            if row[1] > self._ack_sequence:
                raise StoreError(503, "checkpoint_integrity_hold")
            return parse_json_object(row[0])

    def statistics(self):
        with self._mutex:
            self._available()
            return {
                name: self._db.execute("SELECT count(*) FROM " + name).fetchone()[0]
                for name in ("journal", "tasks", "operations", "outbox")
            }

    def replay(self):
        """Pure projection reconstruction, never dispatches an effect."""
        with self._mutex:
            tasks, operations, heads, outbox = {}, {}, {}, {}
            previous = ZERO
            sequence = 0
            policy = None
            known_inventory = None
            try:
                for seq, eid, raw, digest in self._db.execute(
                    "SELECT sequence,event_id,payload,digest FROM journal ORDER BY sequence"
                ):
                    event = parse_json_object(raw)
                    if (
                        seq != sequence + 1
                        or event["sequence"] != seq
                        or event["event_id"] != eid
                        or event["previous_sha256"] != previous
                        or event["schema_version"] != "dopemux.pm.event.v1"
                        or event["project_id"] != self.project_id
                        or event["store_uuid"] != self.store_uuid
                    ):
                        raise ValueError("journal chain")
                    if (
                        canonical_json(event) != raw
                        or _sha(b"dopemux.pm.event.v1\0" + raw) != digest
                    ):
                        raise ValueError("journal digest")
                    receipt = event["receipt"]
                    body = event["command"]
                    kind = event["operation_kind"]
                    if receipt["request_sha256"] != self._digest(
                        receipt["principal_id"], receipt["client_id"], kind, body
                    ):
                        raise ValueError("operation digest")
                    key = (receipt["principal_id"], kind, receipt["idempotency_key"])
                    if (
                        key in operations
                        or receipt["event_sequence"] != seq
                        or receipt["event_id"] != eid
                    ):
                        raise ValueError("operation uniqueness")
                    if kind == "task.transition":
                        validate_receipt(
                            receipt,
                            body,
                            project_id=self.project_id,
                            principal_id=receipt["principal_id"],
                            client_id=receipt["client_id"],
                        )
                        if (
                            tasks[receipt["task_id"]]["version"] != receipt["version_before"]
                            or tasks[receipt["task_id"]]["status"] != receipt["from_status"]
                        ):
                            raise ValueError("task continuity")
                    elif kind not in {
                        "admission.bootstrap",
                        "admission.replace",
                        "task.create",
                        "task.import_bound",
                        "checkpoint.reconcile",
                    }:
                        raise ValueError("unsupported event kind")
                    if event["task"]:
                        task = event["task"]
                        if (
                            task["ownership_state"] != "BOUND"
                            or task["project_id"] != self.project_id
                        ):
                            raise ValueError("ownership")
                        if task["status"] == "DONE" and not task["completion_verification"]:
                            raise ValueError("unverified done")
                        tasks[task["task_id"]] = task
                    if event["policy"]:
                        new_policy = event["policy"]
                        if new_policy["admission_epoch"] != (
                            1 if policy is None else policy["admission_epoch"] + 1
                        ):
                            raise ValueError("policy epoch")
                        if policy is not None:
                            validate_admission_replacement(
                                policy, new_policy, tasks.values(), known_inventory
                            )
                        known_inventory = merge_known_inventory(
                            known_inventory, new_policy["inventory"]
                        )
                        policy = new_policy
                    if kind == "task.import_bound":
                        known_inventory = merge_known_inventory(
                            known_inventory, body["manifest"]["inventory"]
                        )
                    for destination in event["destinations"]:
                        outbox[(seq, destination)] = self._envelope(event, digest, destination)
                    operations[key] = receipt
                    heads[seq] = digest
                    sequence = seq
                    previous = digest
                if policy is None:
                    raise ValueError("absent admission")
                return dict(
                    tasks=tasks,
                    known_inventory=known_inventory,
                    operations=operations,
                    policy=policy,
                    heads=heads,
                    sequence=sequence,
                    outbox=outbox,
                )
            except (KeyError, TypeError, ValueError, sqlite3.DatabaseError) as exc:
                raise StoreError(503, "journal_integrity_hold") from exc

    def _check_projections(self, replay):
        tasks = {
            tid: parse_json_object(raw)
            for tid, raw in self._db.execute("SELECT task_id,snapshot FROM tasks")
        }
        operations = {
            (p, k, key): parse_json_object(raw)
            for p, k, key, raw in self._db.execute(
                "SELECT principal,kind,key,receipt FROM operations"
            )
        }
        outbox = {
            (seq, dest): parse_json_object(raw)
            for seq, dest, raw in self._db.execute(
                "SELECT sequence,destination,envelope FROM outbox"
            )
        }
        if (
            tasks != replay["tasks"]
            or operations != replay["operations"]
            or self._policy() != replay["policy"]
            or outbox != replay["outbox"]
        ):
            raise StoreError(503, "projection_integrity_hold")
        for principal, kind, key, digest, sequence in self._db.execute(
            "SELECT principal,kind,key,digest,sequence FROM operations"
        ):
            receipt = replay["operations"][(principal, kind, key)]
            if (digest, sequence) != (receipt["request_sha256"], receipt["event_sequence"]):
                raise StoreError(503, "projection_integrity_hold")

    def pending_outbox(self):
        with self._mutex:
            self._available()
            return [
                parse_json_object(row[0])
                for row in self._db.execute(
                    "SELECT envelope FROM outbox WHERE delivered=0 AND sequence<=? ORDER BY sequence,destination",
                    (self._ack_sequence,),
                )
            ]

    def record_delivery(self, sequence, destination, *, delivered, error=None):
        with self._transaction():
            if sequence > self._ack_sequence:
                raise StoreError(503, "checkpoint_integrity_hold")
            self._db.execute(
                "UPDATE outbox SET delivered=?,error=? WHERE sequence=? AND destination=?",
                (int(delivered), error, sequence, destination),
            )
