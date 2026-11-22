"""Local bounded execution kernel; no live adapters or upstream authority writer.

Only a trusted project adapter may admit authenticated grants, gates, bindings
and native acceptance. Strings/hashes here are references, not authentication.
SQLite is technical local state, never PM/workflow/decision authority.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import math
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Awaitable, Callable


class Conflict(ValueError):
    """An immutable identity or idempotency key was reused with different bytes."""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _number(value, *, positive=False, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a finite numeric limit")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError("Expected a finite nonnegative limit")
    if integer and not isinstance(value, int):
        raise ValueError("Money and count limits require integers")


def _refs(values):
    if not isinstance(values, (tuple, list)) or any(
        not isinstance(v, str) or not v.strip() for v in values
    ):
        raise ValueError("Expected nonempty reference strings")


@dataclass(frozen=True)
class Grant:
    grant_id: str
    project_id: str
    issuer_ref: str
    scopes: tuple[str, ...]
    effects: tuple[str, ...]
    expires_at: float
    active_seconds: float
    spend_limit_micros: int
    max_parallel: int = 1
    harness_repairs: int = 0
    stop_conditions: tuple[str, ...] = ()
    ordinary_repairs: int = 0
    max_attempts: int = 32


@dataclass(frozen=True)
class Work:
    work_id: str
    project_id: str
    grant_id: str
    input_fingerprint: str
    scope: str
    effects: tuple[str, ...]
    writer_keys: tuple[str, ...]
    depends_on: tuple[str, ...]
    context_refs: tuple[str, ...]
    route_refs: tuple[str, ...]
    max_spend_micros: int
    timeout_seconds: float
    gates: dict[str, str]
    heavy: bool = False
    completion_dependencies: bool = False
    failure_dependencies: tuple[str, ...] = ()
    ordinary_repair: bool = False


@dataclass(frozen=True)
class Dispatch:
    work: Work
    attempt_id: str
    route_ref: str
    timeout_seconds: float


@dataclass(frozen=True)
class Result:
    status: str
    evidence_refs: tuple[str, ...] = ()
    spent_micros: int | None = None


class Supervisor:
    """Single-host journal and routine scheduler under previously admitted scope.

    Numeric limits are checked/reserved atomically. Async timeout is cooperative;
    an adapter must provide process containment, cash enforcement and authenticated
    upstream evidence. Cancellation/timeout never proves host termination.
    One local coordinator owns run_ready/recover_interrupted for a journal.
    Separate connections still serialize claims and budget/writer reservations.
    """

    def __init__(self, path: Path, *, clock=time.time, slots=2):
        _number(slots, positive=True, integer=True)
        self.clock, self.slots = clock, slots
        self._transaction_state = None
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS projection(id INTEGER PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS outbox(
                key TEXT PRIMARY KEY, project TEXT NOT NULL, payload TEXT NOT NULL,
                digest TEXT NOT NULL, created REAL NOT NULL, acked REAL);
        """)
        initial = dict(grants={}, routes={}, works={}, stops={})
        self.db.execute("INSERT OR IGNORE INTO projection VALUES(1,?)", (_json(initial),))

    def close(self):
        self.db.close()

    @contextmanager
    def _transaction(self):
        if self._transaction_state is not None:
            yield self._transaction_state
            return
        self.db.execute("BEGIN IMMEDIATE")
        try:
            state = json.loads(
                self.db.execute("SELECT data FROM projection WHERE id=1").fetchone()[0]
            )
            self._transaction_state = state
            yield state
            self.db.execute("UPDATE projection SET data=? WHERE id=1", (_json(state),))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        finally:
            self._transaction_state = None

    def admission_transaction(self):
        """One outer transaction for mandate, projection and outbox admission."""
        return self._transaction()

    def _state(self):
        return json.loads(self.db.execute("SELECT data FROM projection WHERE id=1").fetchone()[0])

    def _event(self, w, kind, evidence=()):
        w["sequence"] += 1
        key = _json([w["spec"]["work_id"], w["sequence"]])
        payload = _json(
            dict(
                key=key,
                kind=kind,
                work_id=w["spec"]["work_id"],
                project_id=w["spec"]["project_id"],
                grant_id=w["spec"]["grant_id"],
                attempt_id=w["attempt_id"],
                route_ref=w["route_ref"],
                status=w["status"],
                input_fingerprint=w["spec"]["input_fingerprint"],
                evidence_refs=evidence,
                authority="NONE",
            )
        )
        if len(payload.encode()) > 16384:
            raise ValueError("Return exceeds the compact event ceiling")
        digest = hashlib.sha256(payload.encode()).hexdigest()
        self.db.execute(
            "INSERT INTO outbox VALUES(?,?,?,?,?,NULL)",
            (key, w["spec"]["project_id"], payload, digest, self.clock()),
        )

    def admit(self, grant: Grant):
        _refs((grant.grant_id, grant.project_id, grant.issuer_ref))
        _refs(grant.scopes)
        _refs(grant.effects)
        _refs(grant.stop_conditions)
        _number(grant.expires_at)
        _number(grant.active_seconds, positive=True)
        _number(grant.spend_limit_micros, integer=True)
        _number(grant.max_parallel, positive=True, integer=True)
        _number(grant.harness_repairs, integer=True)
        _number(grant.ordinary_repairs, integer=True)
        _number(grant.max_attempts, positive=True, integer=True)
        spec = json.loads(_json(asdict(grant)))
        with self._transaction() as s:
            old = s["grants"].get(grant.grant_id)
            if old:
                if old["spec"] != spec:
                    raise Conflict("Grant identity changed; no allowance reset")
                return
            s["grants"][grant.grant_id] = dict(
                spec=spec,
                active=0,
                spent=0,
                repairs=0,
                ordinary_repairs=0,
                attempts=0,
                revoked=False,
            )

    def revoke(self, grant_id):
        with self._transaction() as s:
            s["grants"][grant_id]["revoked"] = True

    def bind_route(self, ref, *, model_class, valid_until):
        _refs((ref, model_class))
        _number(valid_until)
        value = dict(model_class=model_class, valid_until=valid_until, valid=True)
        with self._transaction() as s:
            old = s["routes"].get(ref)
            if old is not None and old != value:
                raise Conflict("Bindings are immutable; use a new identity")
            s["routes"][ref] = value

    def invalidate_route(self, ref):
        with self._transaction() as s:
            s["routes"][ref]["valid"] = False

    def stop_project(self, project_id, condition):
        _refs((project_id, condition))
        with self._transaction() as s:
            declared = {
                c
                for g in s["grants"].values()
                if g["spec"]["project_id"] == project_id
                for c in g["spec"]["stop_conditions"]
            }
            if condition not in declared | {
                "RETURN_CONFLICT",
                "INPUT_OUTPUT_DRIFT",
                "ADMISSION_INCOMPLETE",
            }:
                raise ValueError("Stop condition was not declared by this project's grants")
            s["stops"][project_id] = condition

    def control_mandate(
        self, grant_id, *, sequence, receipt_ref, action, gate=None, condition=None
    ):
        """Narrow a mandate as the current local UID, without the coordinator lock.

        The protected local journal is the trust boundary. This is not a native
        or Master identity assertion, and cannot release a stop or grant effects.
        """
        _refs((grant_id, receipt_ref))
        if type(sequence) is not int or sequence < 1:
            raise ValueError("Positive ordered control sequence required")
        if action not in {"deny", "revoke", "stop"}:
            raise ValueError("Only narrowing local owner controls are supported")
        if action == "deny":
            if (
                gate not in {"security", "spending", "workflow", "public_release", "human"}
                or condition is not None
            ):
                raise ValueError("Explicit supported gate required for denial")
        elif gate is not None or (action == "revoke" and condition is not None):
            raise ValueError("Unexpected control fields")
        if action == "stop":
            _refs((condition,))
        record = dict(
            sequence=sequence,
            receipt_ref=receipt_ref,
            action=action,
            gate=gate,
            condition=condition,
            principal_uid=os.getuid(),
        )
        with self._transaction() as state:
            grant = state["grants"][grant_id]
            history = grant.setdefault("owner_control_history", {})
            previous = grant.get("owner_control")
            if receipt_ref in history:
                if history[receipt_ref] != record:
                    raise Conflict("Owner control receipt changed")
                return
            if previous and sequence <= previous["sequence"]:
                raise Conflict("Stale or conflicting owner control sequence")
            if action == "stop" and condition not in grant["spec"]["stop_conditions"]:
                raise ValueError("Stop condition was not granted")
            history[receipt_ref] = record
            grant["owner_control"] = record
            # All supported controls are monotonic holds. Later observations
            # cannot erase an earlier denial and there is no implicit regrant.
            grant["owner_held"] = True
            if action == "revoke":
                grant["revoked"] = True
            if action == "stop":
                state["stops"][grant["spec"]["project_id"]] = condition
            for work in state["works"].values():
                if work["spec"]["grant_id"] == grant_id:
                    self._event(work, "LOCAL_OWNER_CONTROL", (receipt_ref,))

    def update_gates(self, work_id, *, gates, receipt_ref):
        """Trusted adapter records a current observation; this does not replay work."""
        _refs((receipt_ref,))
        if (
            not isinstance(gates, dict)
            or not gates
            or any(
                not isinstance(k, str) or v not in {"PASS", "DENIED", "UNKNOWN"}
                for k, v in gates.items()
            )
        ):
            raise ValueError("Invalid gate observation")
        with self._transaction() as s:
            w = s["works"][work_id]
            history = w.setdefault("gate_receipts", {})
            if receipt_ref in history:
                if history[receipt_ref] != gates:
                    raise Conflict("Gate receipt changed")
                return
            history[receipt_ref] = dict(gates)
            w["current_gates"] = dict(gates)
            self._event(w, "GATE_OBSERVED", (receipt_ref,))

    def enqueue(self, work: Work):
        for name in (
            "effects",
            "writer_keys",
            "depends_on",
            "context_refs",
            "route_refs",
            "failure_dependencies",
        ):
            _refs(getattr(work, name))
        _refs(
            (
                work.work_id,
                work.project_id,
                work.grant_id,
                work.input_fingerprint,
                work.scope,
            )
        )
        _number(work.max_spend_micros, integer=True)
        _number(work.timeout_seconds, positive=True)
        if len(_json(asdict(work)).encode()) > 16384:
            raise ValueError("Work context must be compact references, not history")
        if not isinstance(work.gates, dict):
            raise ValueError("Expected typed gate observations")
        if not isinstance(work.heavy, bool):
            raise ValueError("Heavy-resource declaration must be boolean")
        if not isinstance(work.completion_dependencies, bool) or not isinstance(
            work.ordinary_repair, bool
        ):
            raise ValueError("Dependency and repair declarations must be boolean")
        if work.ordinary_repair and not work.failure_dependencies:
            raise ValueError("An ordinary repair requires a known failed predecessor")
        spec = json.loads(_json(asdict(work)))
        with self._transaction() as s:
            g = s["grants"][work.grant_id]
            if g["spec"]["project_id"] != work.project_id:
                raise ValueError("Grant belongs to a different project")
            old = s["works"].get(work.work_id)
            if old:
                if old["spec"] != spec:
                    raise Conflict("Work identity changed; explicit successor required")
                return
            s["works"][work.work_id] = dict(
                spec=spec,
                status="READY",
                sequence=0,
                created=self.clock(),
                started=None,
                ended=None,
                attempt_id=None,
                route_ref=None,
                reserved_spend_micros=0,
                reserved_active_seconds=0,
                spend_unknown=False,
                checkpoints=[],
                evidence_refs=[],
                harness_repairs=0,
                failures=[],
                native_acceptance=None,
                terminal_payload=None,
                current_gates=dict(work.gates),
                gate_receipts={},
                harness_held=False,
                charged_active_seconds=0,
                resolution=None,
                reuse_source=None,
            )
            w = s["works"][work.work_id]
            match = self._reuse_source(s, w)
            if match:
                w.update(status="HELD", reuse_source=match)
            self._event(s["works"][work.work_id], "ENQUEUED")

    @staticmethod
    def _reuse_source(s, w):
        # Equal fingerprints are an adapter claim. Hold for actual output identity
        # verification rather than silently executing or accepting that claim.
        keys = ("project_id", "scope", "effects", "input_fingerprint", "writer_keys")
        return next(
            (
                key
                for key, old in s["works"].items()
                if old is not w
                and old["status"] == "SUCCEEDED"
                and not old["spend_unknown"]
                and all(old["spec"][k] == w["spec"][k] for k in keys)
            ),
            None,
        )

    def reuse_success(self, work_id, *, receipt_ref):
        """Trusted adapter attests unchanged inputs AND outputs under current scope."""
        _refs((receipt_ref,))
        with self._transaction() as s:
            w = s["works"][work_id]
            old_receipt = w.get("reuse_receipt")
            if old_receipt:
                if old_receipt != receipt_ref:
                    raise Conflict("Reuse receipt changed")
                return
            source = w.get("reuse_source")
            if not source or self._reuse_source(s, w) != source or not self._gate(s, w):
                raise Conflict("No currently permitted equivalent successful result")
            old = s["works"][source]
            w.update(
                status="SUCCEEDED",
                ended=self.clock(),
                reuse_receipt=receipt_ref,
                evidence_refs=list(old["evidence_refs"]),
            )
            self._event(w, "EVIDENCE_REUSED", (*old["evidence_refs"], receipt_ref))

    def _gate(self, s, w, route_ref=None):
        p = w["spec"]
        g = s["grants"][p["grant_id"]]
        spec = g["spec"]
        now = self.clock()
        if (
            g["revoked"]
            or g.get("owner_held", False)
            or p["project_id"] in s["stops"]
            or now >= spec["expires_at"]
        ):
            return None
        if p["scope"] not in spec["scopes"] or not set(p["effects"]) <= set(spec["effects"]):
            return None
        if set(p["effects"]) & {"vm", "credentials", "security_settings"}:
            return None
        if set(p["effects"]) & {"write", "publish", "release", "deploy"} and not p["writer_keys"]:
            return None
        if any(
            v["spec"]["grant_id"] == p["grant_id"] and v["spend_unknown"]
            for v in s["works"].values()
        ):
            return None
        gates = w.get("current_gates", p["gates"])
        required = {"security", "spending", "workflow"}
        if set(p["effects"]) & {"publish", "release", "deploy"}:
            required.add("public_release")
        if any(gates.get(k) != "PASS" for k in required):
            return None
        if any(v != "PASS" for v in gates.values()):
            return None
        for dependency in p["depends_on"]:
            dep = s["works"].get(dependency)
            if p.get("completion_dependencies", False):
                if (
                    not dep
                    or dep["status"] != "SUCCEEDED"
                    or dep["spec"]["project_id"] != p["project_id"]
                    or dep["spec"]["grant_id"] != p["grant_id"]
                ):
                    return None
            elif not dep or dep["native_acceptance"] is None:
                return None
        for dependency in p.get("failure_dependencies", ()):
            dep = s["works"].get(dependency)
            if (
                not dep
                or dep["status"] != "FAILED"
                or dep["spec"]["project_id"] != p["project_id"]
                or dep["spec"]["grant_id"] != p["grant_id"]
            ):
                return None
        routes = [(r, s["routes"].get(r)) for r in p["route_refs"]]
        routes = [(r, v) for r, v in routes if v and v["valid"] and v["valid_until"] > now]
        if route_ref is not None:
            return route_ref if any(r == route_ref for r, _ in routes) else None
        if not routes:
            return None
        # Route refs are prequalified by the trusted adapter; preference is not attestation.
        return min(routes, key=lambda rv: rv[1]["model_class"] != "sol")[0]

    def claim_ready(self):
        claims = []
        with self._transaction() as s:
            live = [w for w in s["works"].values() if w["status"] in {"RUNNING", "EFFECT_UNKNOWN"}]
            held_writers = {key for w in live for key in self._resources(w["spec"])}
            for w in s["works"].values():
                if w["status"] != "READY":
                    continue
                route = self._gate(s, w)
                p, g = w["spec"], s["grants"][w["spec"]["grant_id"]]
                spec = g["spec"]
                if (
                    not route
                    or sum(v["status"] == "RUNNING" for v in live) >= self.slots
                    or self._resources(p) & held_writers
                    or g.get("attempts", 0) >= spec.get("max_attempts", 32)
                    or w.get("harness_held", False)
                ):
                    continue
                match = self._reuse_source(s, w)
                if match:
                    w.update(status="HELD", reuse_source=match)
                    self._event(w, "REUSE_VERIFICATION_REQUIRED")
                    continue
                siblings = [v for v in live if v["spec"]["grant_id"] == p["grant_id"]]
                if len(siblings) >= spec["max_parallel"]:
                    continue
                reserved_money = sum(
                    v["reserved_spend_micros"]
                    for v in s["works"].values()
                    if v["spec"]["grant_id"] == p["grant_id"]
                )
                reserved_time = sum(
                    v["reserved_active_seconds"]
                    for v in s["works"].values()
                    if v["spec"]["grant_id"] == p["grant_id"]
                )
                remaining = spec["active_seconds"] - g["active"] - reserved_time
                if (
                    g["spent"] + reserved_money + p["max_spend_micros"] > spec["spend_limit_micros"]
                    or remaining <= 0
                ):
                    continue
                timeout = min(p["timeout_seconds"], remaining, spec["expires_at"] - self.clock())
                if timeout <= 0:
                    continue
                if p.get("ordinary_repair", False):
                    if g.get("ordinary_repairs", 0) >= spec.get("ordinary_repairs", 0):
                        continue
                    g["ordinary_repairs"] = g.get("ordinary_repairs", 0) + 1
                w.update(
                    status="RUNNING",
                    started=self.clock(),
                    attempt_id=uuid.uuid4().hex,
                    route_ref=route,
                    reserved_spend_micros=p["max_spend_micros"],
                    reserved_active_seconds=timeout,
                )
                g["attempts"] = g.get("attempts", 0) + 1
                self._event(w, "DISPATCH_INTENT")
                live.append(w)
                held_writers.update(self._resources(p))
                typed = dict(p)
                for field in (
                    "effects",
                    "writer_keys",
                    "depends_on",
                    "context_refs",
                    "route_refs",
                    "failure_dependencies",
                ):
                    typed[field] = tuple(typed[field])
                claims.append(Dispatch(Work(**typed), w["attempt_id"], route, timeout))
        return claims

    @staticmethod
    def _resources(spec):
        keys = set(spec["writer_keys"])
        if spec["heavy"]:
            keys.add("supervisor:host-heavy")
        return keys

    @staticmethod
    def _running(s, dispatch):
        w = s["works"][dispatch.work.work_id]
        if w["status"] != "RUNNING" or w["attempt_id"] != dispatch.attempt_id:
            raise Conflict("Stale or terminal execution result")
        return w

    def checkpoint(self, dispatch, *, fingerprint, evidence_refs):
        _refs(evidence_refs)
        with self._transaction() as s:
            w = self._running(s, dispatch)
            if fingerprint != w["spec"]["input_fingerprint"]:
                raise Conflict("Checkpoint inputs changed")
            refs = list(evidence_refs)
            if refs not in w["checkpoints"]:
                w["checkpoints"].append(refs)
                self._event(w, "CHECKPOINT", refs)

    def finish(self, dispatch, result: Result, *, elapsed_seconds):
        _number(elapsed_seconds)
        _refs(result.evidence_refs)
        if result.status not in {"SUCCEEDED", "FAILED", "EFFECT_UNKNOWN"}:
            raise ValueError("Unknown result status")
        if result.spent_micros is not None:
            _number(result.spent_micros, integer=True)
        terminal_payload = _json(dict(result=asdict(result), elapsed_seconds=elapsed_seconds))
        with self._transaction() as s:
            existing = s["works"][dispatch.work.work_id]
            if existing["terminal_payload"] is not None:
                if (
                    existing["attempt_id"] == dispatch.attempt_id
                    and existing["terminal_payload"] == terminal_payload
                ):
                    return
                raise Conflict("Terminal result identity or payload changed")
            w = self._running(s, dispatch)
            g = s["grants"][w["spec"]["grant_id"]]
            if result.spent_micros is not None:
                g["spent"] += result.spent_micros
                if result.spent_micros > w["reserved_spend_micros"]:
                    s["stops"][w["spec"]["project_id"]] = "SPEND_OVERRUN"
                w["reserved_spend_micros"] = 0
            else:
                w["spend_unknown"] = True
            g["active"] += elapsed_seconds
            w["charged_active_seconds"] = elapsed_seconds
            if elapsed_seconds > w["reserved_active_seconds"]:
                s["stops"][w["spec"]["project_id"]] = "ACTIVE_TIME_OVERRUN"
            if result.status != "EFFECT_UNKNOWN":
                w["reserved_active_seconds"] = 0
            else:
                w["reserved_active_seconds"] = max(
                    0, w["reserved_active_seconds"] - elapsed_seconds
                )
            w.update(
                status=result.status,
                ended=self.clock(),
                evidence_refs=list(result.evidence_refs),
                terminal_payload=terminal_payload,
            )
            self._event(w, "RESULT", result.evidence_refs)

    def resolve_unknown(
        self,
        work_id,
        *,
        outcome,
        spent_micros,
        elapsed_seconds,
        evidence_refs,
        receipt_ref,
        process_closed,
    ):
        """Trusted adapter reconciles actual custody/spend; never requeues an effect.

        Caller authentication and evidence verification are outside this local
        library. A bare receipt string cannot establish those facts.
        """
        _refs((*evidence_refs, receipt_ref))
        _number(spent_micros, integer=True)
        _number(elapsed_seconds)
        if (
            outcome not in {"SUCCEEDED", "FAILED"}
            or process_closed is not True
            or not evidence_refs
        ):
            raise ValueError("Reconciliation requires terminal evidence and closed process custody")
        payload = dict(
            outcome=outcome,
            spent_micros=spent_micros,
            elapsed_seconds=elapsed_seconds,
            evidence_refs=list(evidence_refs),
            receipt_ref=receipt_ref,
            process_closed=True,
        )
        with self._transaction() as s:
            w = s["works"][work_id]
            if w.get("resolution"):
                if w["resolution"] != payload:
                    raise Conflict("Reconciliation identity changed")
                return
            if w["status"] != "EFFECT_UNKNOWN" and not w["spend_unknown"]:
                raise Conflict("No unresolved outcome or spend")
            if w["status"] != "EFFECT_UNKNOWN" and outcome != w["status"]:
                raise Conflict("Spend settlement cannot change an observed outcome")
            charged = w.get("charged_active_seconds", 0)
            if elapsed_seconds < charged:
                raise Conflict("Reconciliation cannot erase charged active time")
            g = s["grants"][w["spec"]["grant_id"]]
            if w["spend_unknown"]:
                g["spent"] += spent_micros
            elif spent_micros != json.loads(w["terminal_payload"])["result"]["spent_micros"]:
                raise Conflict("Observed spend cannot be rewritten")
            g["active"] += elapsed_seconds - charged
            if g["active"] > g["spec"]["active_seconds"]:
                s["stops"][w["spec"]["project_id"]] = "ACTIVE_TIME_OVERRUN"
            if g["spent"] > g["spec"]["spend_limit_micros"]:
                s["stops"][w["spec"]["project_id"]] = "SPEND_OVERRUN"
            w.update(
                status=outcome,
                resolution=payload,
                reserved_spend_micros=0,
                reserved_active_seconds=0,
                charged_active_seconds=elapsed_seconds,
                spend_unknown=False,
                ended=self.clock(),
                evidence_refs=list(dict.fromkeys(w["evidence_refs"] + list(evidence_refs))),
            )
            self._event(w, "UNKNOWN_RECONCILED", (*evidence_refs, receipt_ref))

    def accept(self, work_id, *, receipt_ref, capability):
        _refs((receipt_ref, capability))
        with self._transaction() as s:
            w = s["works"][work_id]
            value = dict(receipt_ref=receipt_ref, capability=capability)
            if w["status"] != "SUCCEEDED":
                raise Conflict("Only an observed successful result may be accepted")
            if w["native_acceptance"] is not None:
                if w["native_acceptance"] != value:
                    raise Conflict("Acceptance identity changed")
                return
            w["native_acceptance"] = value
            self._event(w, "NATIVE_ACCEPTANCE", (receipt_ref,))

    def record_harness_failure(self, work_id, signature):
        _refs((signature,))
        with self._transaction() as s:
            w = s["works"][work_id]
            g = s["grants"][w["spec"]["grant_id"]]
            if w["status"] not in {"READY", "SUCCEEDED", "FAILED"} or not self._gate(s, w):
                return False
            if (
                g["repairs"] >= g["spec"]["harness_repairs"]
                or g["active"] >= g["spec"]["active_seconds"]
            ):
                w["harness_held"] = True
                if w["status"] == "READY":
                    w["status"] = "HELD"
                self._event(w, "HARNESS_ALLOWANCE_EXHAUSTED")
                return False
            w["failures"].append(signature)
            if w["failures"].count(signature) >= 2:
                w["harness_held"] = True
                if w["status"] == "READY":
                    w["status"] = "HELD"
                self._event(w, "REPEATED_HARNESS_FAILURE")
                return False
            g["repairs"] += 1
            w["harness_repairs"] += 1
            self._event(w, "HARNESS_REPAIR_ALLOWED")
            # Permission only for same-input parsing/harness repair; never requeues work.
            return True

    def recover_interrupted(self):
        """Caller first establishes sole coordinator custody; never launches anything."""
        with self._transaction() as s:
            for w in s["works"].values():
                if w["status"] == "RUNNING":
                    w["status"] = "EFFECT_UNKNOWN"
                    w["spend_unknown"] = True
                    self._event(w, "RECOVERY_HOLD")

    def work_state(self, work_id):
        return self._state()["works"][work_id]

    def pending_returns(self, limit=100):
        _number(limit, positive=True, integer=True)
        return [
            dict(key=k, digest=d, payload=json.loads(p))
            for k, d, p in self.db.execute(
                "SELECT key,digest,payload FROM outbox WHERE acked IS NULL ORDER BY rowid LIMIT ?",
                (limit,),
            )
        ]

    def ack(self, key, digest):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT digest,acked FROM outbox WHERE key=?", (key,)).fetchone()
            if row is None or row[0] != digest:
                raise Conflict("Return key or payload differs")
            if row[1] is None:
                self.db.execute("UPDATE outbox SET acked=? WHERE key=?", (self.clock(), key))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    async def flush_returns(self, sink):
        """Deliver stable envelopes to an already-authorized sink; never rerun work.

        The receiver must deduplicate by key and digest and return that digest.
        Missing/failed ACK leaves the original outbox entry pending.
        """
        for event in self.pending_returns(limit=10000):
            digest = await sink(event)
            if digest is not None:
                self.ack(event["key"], digest)

    def metrics(self, project_id):
        s = self._state()
        works = [w for w in s["works"].values() if w["spec"]["project_id"] == project_id]
        grants = [g for g in s["grants"].values() if g["spec"]["project_id"] == project_id]
        waits = [
            max(0, ack - made)
            for made, ack in self.db.execute(
                "SELECT created,acked FROM outbox WHERE project=? AND acked IS NOT NULL",
                (project_id,),
            )
        ]
        unknown_spend = any(
            w["spend_unknown"] or w["status"] in {"RUNNING", "EFFECT_UNKNOWN"} for w in works
        )
        return dict(
            accepted_capabilities=len(
                {w["native_acceptance"]["capability"] for w in works if w["native_acceptance"]}
            ),
            active_seconds=sum(g["active"] for g in grants),
            elapsed_seconds=max(
                0,
                self.clock() - min((w["created"] for w in works), default=self.clock()),
            ),
            spent_micros=None if unknown_spend else sum(g["spent"] for g in grants),
            reserved_spend_micros=sum(w["reserved_spend_micros"] for w in works),
            coordination_wait_seconds=sum(waits) if waits else None,
            coordination_wait_definition="sum of acknowledged return creation-to-ACK intervals",
        )

    async def run_ready(self, executor: Callable[[Dispatch], Awaitable[Result]]):
        """Backfill each free slot on completion; held siblings create no barrier."""
        running = set()
        try:
            while True:
                for dispatch in self.claim_ready():
                    running.add(asyncio.create_task(self._execute(executor, dispatch)))
                if not running:
                    return
                done, running = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    task.result()
        finally:
            for task in running:
                task.cancel()
            if running:
                await asyncio.gather(*running, return_exceptions=True)

    async def _execute(self, executor, dispatch):
        started = time.monotonic()
        task, cause, forced = None, None, False
        result = Result("EFFECT_UNKNOWN")
        try:
            task = asyncio.create_task(executor(dispatch))
            while True:
                remaining = dispatch.timeout_seconds - (time.monotonic() - started)
                state = self._state()
                current = state["works"][dispatch.work.work_id]
                if remaining <= 0:
                    cause, forced = "kernel:timeout", True
                    break
                if not self._gate(state, current, dispatch.route_ref):
                    cause, forced = "kernel:gate-changed", True
                    break
                done, _ = await asyncio.wait({task}, timeout=min(0.05, remaining))
                if done:
                    result = task.result()
                    if not isinstance(result, Result):
                        cause, forced = "kernel:malformed-result", True
                        result = Result("EFFECT_UNKNOWN")
                    state = self._state()
                    if not self._gate(
                        state, state["works"][dispatch.work.work_id], dispatch.route_ref
                    ):
                        cause, forced = "kernel:gate-changed", True
                    break
        except asyncio.CancelledError:
            cause, forced = "kernel:cancelled", True
        except Exception as exc:
            cause, forced = "kernel:exception:" + type(exc).__name__, True
        finally:
            if task is not None and not task.done():
                task.cancel()
                # Explicit cooperative cleanup ceiling, not proof of host fencing.
                done, _ = await asyncio.wait({task}, timeout=0.25)
                if not done:
                    cause = "kernel:cleanup-unconfirmed"
                elif (
                    not task.cancelled()
                    and task.exception() is None
                    and isinstance(task.result(), Result)
                ):
                    result = task.result()
        if forced:
            result = Result("EFFECT_UNKNOWN", (*result.evidence_refs, cause), result.spent_micros)
        elapsed = time.monotonic() - started
        # Enforcement jitter and bounded cancellation are not a runner overrun.
        # Unconfirmed cleanup is a material stop and retains unknown custody.
        if forced and cause != "kernel:cleanup-unconfirmed":
            elapsed = min(elapsed, dispatch.timeout_seconds)
        try:
            self.finish(dispatch, result, elapsed_seconds=elapsed)
        except Conflict:
            raise
        except ValueError:
            # A malformed return is not proof that submission had no effect.
            self.finish(
                dispatch,
                Result("EFFECT_UNKNOWN", ("kernel:invalid-return",)),
                elapsed_seconds=elapsed,
            )
