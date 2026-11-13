"""Project-level admission, routine dispatch and Master return integration."""

from __future__ import annotations

import asyncio
import fcntl
import hashlib
import json
import time
from contextlib import contextmanager
from pathlib import Path

from .kernel import Grant, Supervisor, Work
from .mandates import canonical, validate
from .process import LocalProcessRunner, snapshot
from .transport import (
    ReturnConflict,
    ReturnPublisher,
    directory,
    exclusive,
    immutable_bytes,
    read_json,
)


class Runtime:
    """Trusted local coordinator. No cloud/service or model activation occurs implicitly."""

    def __init__(self, state_root, return_root, receiver_ref):
        if not isinstance(receiver_ref, str) or not receiver_ref.strip():
            raise ValueError("Explicit Master/operator receiver required")
        self.root = directory(state_root)
        self.return_root = Path(return_root).absolute()
        self.receiver_ref = receiver_ref
        self.admission_fault_hook = None
        exclusive(
            self.root / "runtime.json",
            {"return_root": str(self.return_root), "receiver_ref": receiver_ref},
        )
        self.kernel = Supervisor(self.root / "journal.sqlite")
        self.kernel.db.execute(
            "CREATE TABLE IF NOT EXISTS mandates("
            "id TEXT PRIMARY KEY, data TEXT NOT NULL, baseline TEXT NOT NULL)"
        )
        self.publisher = ReturnPublisher(self.return_root, receiver_ref)

    def close(self):
        self.kernel.close()

    def _plans(self):
        return {
            key: json.loads(data)
            for key, data in self.kernel.db.execute("SELECT id,data FROM mandates ORDER BY rowid")
        }

    @contextmanager
    def coordinator(self):
        path = self.root / "coordinator.lock"
        if path.is_symlink():
            raise ValueError("Invalid coordinator lock")
        with path.open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("A coordinator already owns this journal") from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def admit(self, raw, *, authorization_ref):
        with self.coordinator():
            return self._admit(raw, authorization_ref=authorization_ref)

    def _admit(self, raw, *, authorization_ref):
        plan = validate(raw, authorization_ref)
        if min(plan["expires_at"], plan["route"]["valid_until"]) <= time.time():
            raise ValueError("Expired mandate or binding; no clock reset")
        data = canonical(plan).decode()
        old = self.kernel.db.execute(
            "SELECT data FROM mandates WHERE id=?", (plan["mandate_id"],)
        ).fetchone()
        if old and old[0] != data:
            raise ValueError("Immutable mandate changed; explicit successor required")
        root = Path(plan["project_root"])
        for private in (self.root.resolve(), self.return_root.resolve()):
            if root == private or root in private.parents or private in root.parents:
                raise ValueError("Project and private state/return roots must be disjoint")
        for existing in self._plans().values():
            other = Path(existing["project_root"])
            if existing["project_id"] != plan["project_id"] and (
                root == other or root in other.parents or other in root.parents
            ):
                raise ValueError("Cross-project physical roots overlap")
        baseline = canonical(snapshot(root)).decode() if old is None else None
        with self.kernel.admission_transaction():
            self.kernel.db.execute(
                "INSERT OR IGNORE INTO mandates VALUES(?,?,?)",
                (plan["mandate_id"], data, baseline or "{}"),
            )
            self._admission_stage("mandate")
            self.kernel.admit(
                Grant(
                    grant_id=plan["mandate_id"],
                    project_id=plan["project_id"],
                    issuer_ref=plan["issuer_ref"],
                    scopes=("development",),
                    effects=("read", "write", "test"),
                    expires_at=plan["expires_at"],
                    active_seconds=plan["active_seconds"],
                    spend_limit_micros=0,
                    max_parallel=plan["max_parallel"],
                    harness_repairs=0,
                    stop_conditions=tuple(plan["stop_conditions"]),
                    ordinary_repairs=plan["repair_limit"],
                    max_attempts=len(plan["steps"]),
                )
            )
            self._admission_stage("grant")
            route = plan["route"]
            route_ref = plan["mandate_id"] + ":" + hashlib.sha256(canonical(route)).hexdigest()
            # Existing work retains its original immutable binding on identical re-admission.
            previous = self.kernel._state()["works"].get(
                plan["mandate_id"] + ":" + plan["steps"][0]["step_id"]
            )
            if previous:
                route_ref = previous["spec"]["route_refs"][0]
            self.kernel.bind_route(
                route_ref,
                model_class=route["model_class"],
                valid_until=route["valid_until"],
            )
            self._admission_stage("route")
            for step in plan["steps"]:
                work_id = plan["mandate_id"] + ":" + step["step_id"]
                writers = ("project:" + plan["project_id"], "root:" + str(root).casefold())
                writers += tuple("resource:" + x.casefold() for x in step.get("resources", []))
                self.kernel.enqueue(
                    Work(
                        work_id=work_id,
                        project_id=plan["project_id"],
                        grant_id=plan["mandate_id"],
                        input_fingerprint=hashlib.sha256(
                            canonical({"mandate": plan, "step": step})
                        ).hexdigest(),
                        scope="development",
                        effects=tuple(step["effects"]),
                        writer_keys=writers,
                        depends_on=tuple(plan["mandate_id"] + ":" + x for x in step["depends_on"]),
                        context_refs=(str(self.root / "journal.sqlite"),),
                        route_refs=(route_ref,),
                        max_spend_micros=0,
                        timeout_seconds=step["timeout_seconds"],
                        gates=plan["gates"],
                        heavy=step["heavy"],
                        completion_dependencies=True,
                        failure_dependencies=(
                            (plan["mandate_id"] + ":" + step["when_failed"],)
                            if step.get("when_failed")
                            else ()
                        ),
                        ordinary_repair=step["kind"] == "repair",
                    )
                )

                self._admission_stage("work:" + step["step_id"])
            self._admission_stage("complete")

    def _admission_stage(self, name):
        if self.admission_fault_hook is not None:
            self.admission_fault_hook(name)

    def status(self):
        state = self.kernel._state()
        plans = self._plans()
        outcomes = {}
        for key, plan in plans.items():
            works = {
                s["step_id"]: state["works"].get(key + ":" + s["step_id"]) for s in plan["steps"]
            }
            unknown = any(w and w["status"] in {"EFFECT_UNKNOWN", "HELD"} for w in works.values())
            unknown = (
                unknown
                or plan["project_id"] in state["stops"]
                or state["grants"].get(key, {}).get("owner_held", False)
            )
            running = any(w and w["status"] == "RUNNING" for w in works.values())
            implemented = all(
                works[s["step_id"]] and works[s["step_id"]]["status"] == "SUCCEEDED"
                for s in plan["steps"]
                if s["kind"] == "implementation"
            )
            succeeded = implemented and any(
                works[x] and works[x]["status"] == "SUCCEEDED" for x in plan["success_steps"]
            )
            if unknown:
                result = "HELD"
            elif running:
                result = "RUNNING"
            elif succeeded:
                result = "COMPLETED_PENDING_NATIVE_ACCEPTANCE"
            else:
                result = "READY_OR_BLOCKED"
            outcomes[key] = dict(
                status=result,
                project_id=plan["project_id"],
                issuer_ref=plan["issuer_ref"],
                repairs_used=state["grants"].get(key, {}).get("ordinary_repairs", 0),
                attempts_used=state["grants"].get(key, {}).get("attempts", 0),
                max_attempts=len(plan["steps"]),
            )
        return dict(
            mandates=outcomes,
            works=state["works"],
            pending_returns=len(self.kernel.pending_returns()),
            authority="NONE",
            live_model_routes="NOT_INSTALLED",
        )

    def _aggregate(self):
        summary = self.status()
        for key, outcome in summary["mandates"].items():
            works = {
                name.split(":", 1)[1]: dict(
                    status=w["status"],
                    evidence_sequence=w["sequence"],
                    input_fingerprint=w["spec"]["input_fingerprint"],
                )
                for name, w in summary["works"].items()
                if w["spec"]["grant_id"] == key
            }
            payload = dict(
                kind="PROJECT_RETURN",
                mandate_id=key,
                **outcome,
                works=works,
                evidence_journal_ref=str(self.root / "journal.sqlite"),
                authority="NONE",
                native_acceptance="SEPARATE",
            )
            identity = hashlib.sha256(canonical(payload)).hexdigest()
            event_key = canonical(["project-return", key, identity]).decode()
            payload["key"] = event_key
            data = canonical(payload)
            if len(data) > 16384:
                raise ValueError("Aggregate return exceeds compact event ceiling")
            self.kernel.db.execute(
                "INSERT OR IGNORE INTO outbox VALUES(?,?,?,?,?,NULL)",
                (
                    event_key,
                    outcome["project_id"],
                    data.decode(),
                    hashlib.sha256(data).hexdigest(),
                    time.time(),
                ),
            )

    async def deliver_returns(self):
        self._aggregate()
        for event in self.kernel.pending_returns(limit=10000):
            try:
                digest = await self.publisher(event)
                if digest is not None:
                    self.kernel.ack(event["key"], digest)
            except ReturnConflict:
                self.kernel.stop_project(event["payload"]["project_id"], "RETURN_CONFLICT")
            except OSError:
                # Delivery is retryable and cannot invalidate execution in another project.
                continue

    def _checkpoint_step(self, dispatch, result):
        """Freeze successful child evidence before finish; never promote unknown effects."""
        current = self.kernel.work_state(dispatch.work.work_id)
        if (
            current["status"] != "RUNNING"
            or current["attempt_id"] != dispatch.attempt_id
            or current["route_ref"] != dispatch.route_ref
            or current["spec"]["input_fingerprint"] != dispatch.work.input_fingerprint
        ):
            raise ValueError("Checkpoint dispatch identity differs from running work")
        root = directory(self.root / "evidence" / dispatch.attempt_id)
        stdout, stderr, native_path = (
            root / "stdout.log",
            root / "stderr.log",
            root / "PROCESS_RESULT.json",
        )
        expected = tuple(str(path) for path in (stdout, stderr, native_path))
        if (
            result.status != "SUCCEEDED"
            or result.spent_micros != 0
            or result.evidence_refs != expected
        ):
            raise ValueError("Checkpoint requires the exact successful local result")
        ack_path = root / "START_ACK.json"
        native = read_json(native_path)
        ack = read_json(ack_path)
        if (
            native.get("attempt_id") != dispatch.attempt_id
            or native.get("work_id") != dispatch.work.work_id
            or type(native.get("native_exit")) is not int
            or native["native_exit"] != 0
            or native.get("owned_group_absent") is not True
            or native.get("capture_complete") is not True
            or native.get("stop_reason") is not None
            or ack.get("attempt_id") != dispatch.attempt_id
            or type(ack.get("pid")) is not int
            or ack["pid"] <= 0
            or ack.get("pgid") != ack["pid"]
        ):
            raise ValueError("Checkpoint native completion identity is unconfirmed")
        evidence = []
        captured = {}
        for path in (stdout, stderr, native_path, ack_path):
            raw = immutable_bytes(path, 1048576 if path in (stdout, stderr) else 32768)
            if path in (stdout, stderr):
                captured[path.stem] = len(raw)
            elif raw != canonical(native if path == native_path else ack):
                raise ValueError("Checkpoint native evidence changed while reading")
            evidence.append(
                dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            )
        if captured != native.get("capture_bytes") or sum(captured.values()) > 1048576:
            raise ValueError("Checkpoint capture identity differs from native result")
        checkpoint = root / "STEP_BOUNDARY_CHECKPOINT.json"
        exclusive(
            checkpoint,
            dict(
                kind="STEP_BOUNDARY_CHECKPOINT",
                version=1,
                work_id=dispatch.work.work_id,
                attempt_id=dispatch.attempt_id,
                input_fingerprint=dispatch.work.input_fingerprint,
                boundary="LOCAL_CHILD_EXIT_BEFORE_KERNEL_FINISH",
                mid_command=False,
                evidence=evidence,
                authority="NONE",
            ),
        )
        self.kernel.checkpoint(
            dispatch,
            fingerprint=dispatch.work.input_fingerprint,
            evidence_refs=(str(checkpoint), *result.evidence_refs),
        )

    async def run(self):
        with self.coordinator():
            self.kernel.recover_interrupted()
            plans = self._plans()

            def verify(key, current):
                saved = json.loads(
                    self.kernel.db.execute(
                        "SELECT baseline FROM mandates WHERE id=?", (key,)
                    ).fetchone()[0]
                )
                if saved != current:
                    self.kernel.stop_project(plans[key]["project_id"], "INPUT_OUTPUT_DRIFT")
                    raise ValueError("Input/output view changed; explicit reconciliation required")

            def save(key, current):
                self.kernel.db.execute(
                    "UPDATE mandates SET baseline=? WHERE id=?",
                    (canonical(current).decode(), key),
                )

            state = self.kernel._state()
            for key, plan in plans.items():
                expected = {key + ":" + step["step_id"] for step in plan["steps"]}
                if key not in state["grants"] or not expected <= state["works"].keys():
                    self.kernel.stop_project(plan["project_id"], "ADMISSION_INCOMPLETE")
                    continue
                try:
                    verify(key, snapshot(Path(plan["project_root"])))
                except ValueError:
                    self.kernel.stop_project(plan["project_id"], "INPUT_OUTPUT_DRIFT")
            runner = LocalProcessRunner(plans, self.root / "evidence", verify, save)

            async def checkpointed_runner(dispatch):
                result = await runner(dispatch)
                if result.status == "SUCCEEDED":
                    self._checkpoint_step(dispatch, result)
                return result

            finished = asyncio.Event()

            async def publish():
                while not finished.is_set():
                    await self.deliver_returns()
                    try:
                        await asyncio.wait_for(finished.wait(), 0.05)
                    except asyncio.TimeoutError:
                        pass

            publishing = asyncio.create_task(publish())
            try:
                await self.kernel.run_ready(checkpointed_runner)
            finally:
                finished.set()
                await publishing
                await self.deliver_returns()
        return self.status()
