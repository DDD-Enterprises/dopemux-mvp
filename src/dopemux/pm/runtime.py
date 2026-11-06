"""Explicit source-qualified runtime composition; imports never start a service."""

from contextlib import asynccontextmanager
from dataclasses import dataclass
import sqlite3
import threading

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import Response

from .ownership import CreateTaskCommand, TransitionCommand, canonical_json, parse_json_object
from .principal import DenyPrincipalVerifier
from .sqlite_store import SQLiteTaskStore, StoreError


@dataclass(frozen=True)
class DeliveryAck:
    """Output of a trusted destination adapter's channel verification, not JSON claims."""

    project_id: str
    event_id: str
    destination: str
    event_sha256: str
    authenticated: bool


class CanonicalTaskRuntime:
    def __init__(self, store: SQLiteTaskStore, *, principal_verifier=None, destinations=None):
        if type(store) is not SQLiteTaskStore:
            raise ValueError("Canonical durable store required")
        self.store = store
        self.principal_verifier = principal_verifier or DenyPrincipalVerifier()
        self.destinations = dict(destinations or {})
        self.closed = False
        self._drain_lock = threading.Lock()

    def _principal(self, project, kind, body, credential):
        if self.closed:
            raise StoreError(503, "runtime_unavailable")
        try:
            return self.principal_verifier.verify(
                project_id=project, operation=kind, body=body, credential=credential
            )
        except PermissionError as exc:
            raise StoreError(401, "invalid_authentication") from exc

    def transition(self, project, raw, credential):
        body = TransitionCommand.model_validate(parse_json_object(raw)).model_dump()
        p = self._principal(project, "task.transition", body, credential)
        return self.store.transition(project, body, p)

    def create(self, project, raw, credential):
        body = CreateTaskCommand.model_validate(parse_json_object(raw)).model_dump()
        p = self._principal(project, "task.create", body, credential)
        return self.store.create(project, body, p)

    def task(self, project, task_id, credential):
        body = {"task_id": task_id}
        return self.store.get_task(
            project, task_id, self._principal(project, "task.read", body, credential)
        )

    def receipt(self, project, lookup, credential):
        return self.store.receipt(
            project, lookup, self._principal(project, "task.read", lookup, credential)
        )

    def view(self, project, *, credential, offset, limit):
        body = {"offset": offset, "limit": limit}
        p = self._principal(project, "task.read", body, credential)
        # One writer mutex covers authorization, counts, traversal and advisory capabilities.
        with self.store._mutex:
            result = self.store.list_tasks(project, p, offset=offset, limit=limit)
            policy = self.store._policy()
            grant = next(g for g in policy["grants"] if g["principal_id"] == p.principal_id)
            counts = {
                status: 0 for status in ("TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELED")
            }
            for (raw,) in self.store._db.execute("SELECT snapshot FROM tasks"):
                counts[parse_json_object(raw)["status"]] += 1
            for task in result["tasks"]:
                task["blockers"] = []
                try:
                    self.store._dependencies(task["dependencies"], completed=True)
                except StoreError:
                    task["blockers"] = ["dependency_unavailable"]
                task["allowed_transitions"] = []
                if policy["status"] != "ACTIVE":
                    continue
                options = {
                    "TODO": ["start", "block"],
                    "IN_PROGRESS": ["block"],
                    "BLOCKED": ["resume"],
                    "DONE": [],
                    "CANCELED": [],
                }[task["status"]]
                task["allowed_transitions"] = [
                    name
                    for name in options
                    if "task.transition." + name in grant["actions"]
                    and (name == "block" or not task["blockers"])
                ]
                # DONE needs an exact evidence reference; a read does not claim one exists.
            result["state"] = counts
            result["queue"] = [
                t["task_id"] for t in result["tasks"] if "start" in t["allowed_transitions"]
            ]
            result["next_action"] = result["queue"][0] if result["queue"] else None
            return result

    def drain_once(self):
        """At-least-once delivery; no background scheduling and no canonical retry."""
        if self.closed:
            raise StoreError(503, "runtime_unavailable")
        if not self._drain_lock.acquire(blocking=False):
            return {"delivered": 0, "failed": 0, "busy": True}
        try:
            if self.closed:
                raise StoreError(503, "runtime_unavailable")
            return self._drain_ordered()
        finally:
            self._drain_lock.release()

    def _drain_ordered(self):
        delivered = failed = 0
        blocked = set()
        for envelope in self.store.pending_outbox():
            group = (envelope["project_id"], envelope["task_id"], envelope["destination"])
            if group in blocked:
                continue
            try:
                adapter = self.destinations.get(envelope["destination"])
                if adapter is None:
                    raise PermissionError("Destination channel unavailable")
                ack = adapter.deliver(envelope)
                if (
                    type(ack) is not DeliveryAck
                    or ack.authenticated is not True
                    or (ack.project_id, ack.event_id, ack.destination, ack.event_sha256)
                    != (
                        envelope["project_id"],
                        envelope["event_id"],
                        envelope["destination"],
                        envelope["event_sha256"],
                    )
                ):
                    raise PermissionError("Unverified delivery acknowledgment")
                self.store.record_delivery(
                    envelope["event_sequence"], envelope["destination"], delivered=True
                )
                delivered += 1
            except Exception:
                failed += 1
                blocked.add(group)
                try:
                    self.store.record_delivery(
                        envelope["event_sequence"],
                        envelope["destination"],
                        delivered=False,
                        error="delivery_unconfirmed",
                    )
                except Exception:
                    pass  # pending durable row already retains retry work
        return {"delivered": delivered, "failed": failed}

    def close(self):
        self.closed = True
        # The host stops new requests before waiting for an existing delivery pump.
        with self._drain_lock:
            self.store.close()


ownership_router = APIRouter(
    prefix="/api/v2/projects/{project_id}/workflow", tags=["canonical-project-workflow"]
)


def _runtime(request):
    value = getattr(request.app.state, "task_runtime", None)
    if type(value) is not CanonicalTaskRuntime:
        raise HTTPException(503, "runtime_unavailable")
    return value


def _call(operation):
    try:
        return Response(canonical_json(operation()), media_type="application/json")
    except StoreError as exc:
        raise HTTPException(exc.status, exc.code) from exc
    except (ValueError, TypeError):
        raise HTTPException(422, "invalid_command") from None
    except (sqlite3.Error, OSError):
        raise HTTPException(503, "writer_unavailable") from None


async def _body(request):
    result = b""
    async for chunk in request.stream():
        result += chunk
        if len(result) > 65536:
            raise HTTPException(422, "command_too_large")
    return result


@ownership_router.post("/transition")
async def transition_route(project_id: str, request: Request):
    runtime = _runtime(request)
    raw = await _body(request)
    return _call(lambda: runtime.transition(project_id, raw, request.headers.get("authorization")))


@ownership_router.post("/tasks")
async def create_route(project_id: str, request: Request):
    runtime = _runtime(request)
    raw = await _body(request)
    return _call(lambda: runtime.create(project_id, raw, request.headers.get("authorization")))


@ownership_router.get("/tasks/{task_id}")
async def task_route(project_id: str, task_id: str, request: Request):
    runtime = _runtime(request)
    return _call(lambda: runtime.task(project_id, task_id, request.headers.get("authorization")))


@ownership_router.get("/receipts")
async def receipt_route(
    project_id: str, operation_kind: str, idempotency_key: str, request: Request
):
    runtime = _runtime(request)
    lookup = {"operation_kind": operation_kind, "idempotency_key": idempotency_key}
    return _call(lambda: runtime.receipt(project_id, lookup, request.headers.get("authorization")))


@ownership_router.get("/state")
async def state_route(project_id: str, request: Request, offset: int = 0, limit: int = 100):
    runtime = _runtime(request)
    return _call(
        lambda: runtime.view(
            project_id, credential=request.headers.get("authorization"), offset=offset, limit=limit
        )
    )


def create_runtime_app(runtime_factory=None):
    """In-process qualification app; no coordinator, servers or default store opened."""

    @asynccontextmanager
    async def lifespan(app):
        runtime = runtime_factory() if runtime_factory else None
        if runtime is not None and type(runtime) is not CanonicalTaskRuntime:
            raise ValueError("Invalid runtime factory")
        app.state.task_runtime = runtime
        try:
            yield
        finally:
            if runtime is not None:
                runtime.close()
            app.state.task_runtime = None

    app = FastAPI(lifespan=lifespan)
    app.include_router(ownership_router)
    return app
