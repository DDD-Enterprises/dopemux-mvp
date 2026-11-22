"""External-ledger archaeology dispatch. No provider adapters or automatic retries.

Events are authority; checkpoints are replaceable projections. POSIX local disk only.
Run as ``python -m dopemux.archaeology_supervisor --help``.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterator

VERSION = 1
PRIVACY = {"public": 0, "internal": 1, "restricted": 2}
TERMINAL = {"SUCCEEDED", "FAILED", "CAPACITY_FAILED", "LAUNCH_FAILED"}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class SupervisorError(ValueError):
    """Fail-closed contract or custody error; messages never contain input values."""


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise SupervisorError("duplicate JSON key")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_bytes(),
            object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(
                SupervisorError("non-finite JSON")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SupervisorError("unreadable JSON document") from exc


def fields(value: Any, required: set[str], optional: set[str] | None = None) -> None:
    if (
        not isinstance(value, dict)
        or not required <= value.keys()
        or value.keys() - required - (optional or set())
    ):
        raise SupervisorError("missing or undeclared contract fields")


def identifier(value: Any) -> None:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise SupervisorError("invalid identifier")


def strings(value: Any, *, ids: bool = False, nonempty: bool = False) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        raise SupervisorError("expected string list")
    if any(not isinstance(x, str) or not x or "\x00" in x for x in value) or len(
        value
    ) != len(set(value)):
        raise SupervisorError("invalid string list")
    if ids:
        for x in value:
            identifier(x)


def integer(value: Any, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise SupervisorError("invalid integer")


def number(value: Any, minimum: float = 0) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
        raise SupervisorError("invalid finite number")


def validate_campaign(campaign: Any) -> None:
    fields(campaign, {"version", "id", "max_parallel", "tasks"})
    if type(campaign["version"]) is not int or campaign["version"] != VERSION:
        raise SupervisorError("unsupported campaign version")
    identifier(campaign["id"])
    integer(campaign["max_parallel"], 1)
    if not isinstance(campaign["tasks"], list) or not campaign["tasks"]:
        raise SupervisorError("campaign tasks required")
    tasks = {}
    for task in campaign["tasks"]:
        fields(
            task,
            {
                "id",
                "release_id",
                "depends_on",
                "capabilities",
                "privacy",
                "allowed_routes",
                "preferred_routes",
                "independent_of",
                "premium_allowed",
            },
        )
        identifier(task["id"])
        if task["id"] in tasks:
            raise SupervisorError("duplicate task")
        tasks[task["id"]] = task
        if task["release_id"] is not None:
            identifier(task["release_id"])
        for key in (
            "depends_on",
            "allowed_routes",
            "preferred_routes",
            "independent_of",
        ):
            strings(task[key], ids=True, nonempty=key == "allowed_routes")
        strings(task["capabilities"])
        if (
            not isinstance(task["privacy"], str)
            or task["privacy"] not in PRIVACY
            or type(task["premium_allowed"]) is not bool
        ):
            raise SupervisorError("invalid task policy")
        if not set(task["preferred_routes"]) <= set(task["allowed_routes"]):
            raise SupervisorError("preferred route outside release")
        if not set(task["independent_of"]) <= set(task["depends_on"]):
            raise SupervisorError("independence must name dependencies")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise SupervisorError("dependency cycle")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in tasks[task_id]["depends_on"]:
            if dep not in tasks:
                raise SupervisorError("missing dependency")
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in sorted(tasks):
        visit(task_id)


def capacity_band(used_percent: float | None) -> str:
    if used_percent is None:
        return "UNKNOWN"
    number(used_percent)
    if used_percent > 100:
        raise SupervisorError("capacity percentage outside range")
    if used_percent < 70:
        return "GREEN"
    if used_percent < 85:
        return "YELLOW"
    if used_percent < 95:
        return "RED"
    return "CRITICAL"


def validate_routes(ledger: Any, campaign: dict) -> None:
    fields(ledger, {"version", "campaign_id", "routes"})
    if (
        type(ledger["version"]) is not int
        or ledger["version"] != VERSION
        or ledger["campaign_id"] != campaign["id"]
    ):
        raise SupervisorError("route ledger binding mismatch")
    if not isinstance(ledger["routes"], list):
        raise SupervisorError("routes must be list")
    seen = set()
    pools: dict[str, dict] = {}
    for route in ledger["routes"]:
        fields(
            route,
            {
                "id",
                "argv",
                "model",
                "family",
                "runtime",
                "capabilities",
                "privacy",
                "qualification",
                "capacity",
                "pool",
                "premium",
                "reserve_slots",
                "capacity_exit_codes",
            },
        )
        for key in ("id", "family", "runtime", "pool"):
            identifier(route[key])
        if route["id"] in seen:
            raise SupervisorError("duplicate route")
        seen.add(route["id"])
        if (
            not isinstance(route["model"], str)
            or not route["model"]
            or "\x00" in route["model"]
        ):
            raise SupervisorError("model identity required")
        # argv preserves repeats: repeated flags/values can be legitimate.
        argv = route["argv"]
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(x, str) or "\x00" in x for x in argv)
        ):
            raise SupervisorError("invalid runner argv")
        if not Path(argv[0]).is_absolute():
            raise SupervisorError("runner executable must be absolute")
        strings(route["capabilities"])
        if (
            not isinstance(route["privacy"], str)
            or route["privacy"] not in PRIVACY
            or type(route["premium"]) is not bool
        ):
            raise SupervisorError("invalid route policy")
        qual = route["qualification"]
        fields(qual, {"status", "evidence_id", "command_sha256"})
        if not isinstance(qual["status"], str) or qual["status"] not in {
            "VERIFIED",
            "UNKNOWN",
        }:
            raise SupervisorError("invalid qualification status")
        if qual["status"] == "VERIFIED":
            identifier(qual["evidence_id"])
            if qual["command_sha256"] != digest(argv):
                raise SupervisorError("qualified command binding mismatch")
        elif qual["evidence_id"] is not None or qual["command_sha256"] is not None:
            raise SupervisorError("UNKNOWN qualification carries no proof")
        cap = route["capacity"]
        fields(cap, {"used_percent", "slots", "observed_at", "ttl_seconds"})
        capacity_band(cap["used_percent"])
        if cap["slots"] is not None:
            integer(cap["slots"])
        number(cap["observed_at"])
        number(cap["ttl_seconds"], 0.001)
        integer(route["reserve_slots"])
        if cap["slots"] is not None and route["reserve_slots"] > cap["slots"]:
            raise SupervisorError("reserve exceeds slots")
        # Routes sharing quota must have a single consistent capacity snapshot.
        pool_policy = {"capacity": cap, "reserve_slots": route["reserve_slots"]}
        if route["pool"] in pools and pools[route["pool"]] != pool_policy:
            raise SupervisorError("conflicting pool capacity")
        pools[route["pool"]] = pool_policy
        codes = route["capacity_exit_codes"]
        if (
            not isinstance(codes, list)
            or any(type(c) is not int for c in codes)
            or len(codes) != len(set(codes))
        ):
            raise SupervisorError("invalid capacity exit codes")
        for code in codes:
            integer(code, 1)
            if code > 255:
                raise SupervisorError("capacity exit code outside range")
    required = {r for task in campaign["tasks"] for r in task["allowed_routes"]}
    if not required <= seen:
        raise SupervisorError("released route missing from ledger")


def route_binding(ledger: dict) -> str:
    """Capacity refresh cannot redefine qualified routes or quota pools."""
    return digest(
        sorted(
            ({k: v for k, v in r.items() if k != "capacity"} for r in ledger["routes"]),
            key=lambda r: r["id"],
        )
    )


def task_attempts(attempts: dict, task_id: str) -> list[dict]:
    return [a for a in attempts.values() if a["task_id"] == task_id]


def ready_tasks(campaign: dict, attempts: dict) -> list[dict]:
    succeeded = {a["task_id"] for a in attempts.values() if a["status"] == "SUCCEEDED"}
    return sorted(
        (
            t
            for t in campaign["tasks"]
            if t["release_id"] is not None
            and not task_attempts(attempts, t["id"])
            and set(t["depends_on"]) <= succeeded
        ),
        key=lambda t: t["id"],
    )


def choose_route(
    task: dict, routes: list[dict], attempts: dict, now: float
) -> dict | None:
    candidates = []
    prior = [a for a in attempts.values() if a["task_id"] in task["independent_of"]]
    active = [a for a in attempts.values() if a["status"] not in TERMINAL]
    for route in routes:
        if (
            route["id"] not in task["allowed_routes"]
            or route["qualification"]["status"] != "VERIFIED"
        ):
            continue
        if (
            not set(task["capabilities"]) <= set(route["capabilities"])
            or PRIVACY[route["privacy"]] < PRIVACY[task["privacy"]]
        ):
            continue
        if any(
            a["family"] == route["family"] or a["runtime"] == route["runtime"]
            for a in prior
        ):
            continue
        if route["premium"] and not task["premium_allowed"]:
            continue
        cap = route["capacity"]
        band = capacity_band(cap["used_percent"])
        if band in {"UNKNOWN", "CRITICAL"} or cap["slots"] is None:
            continue
        if not 0 <= now - cap["observed_at"] <= cap["ttl_seconds"]:
            continue
        occupied = sum(a["pool"] == route["pool"] for a in active)
        usable = cap["slots"] - (
            0 if task["premium_allowed"] else route["reserve_slots"]
        )
        if occupied >= usable:
            continue
        # Least scarce band first; preserve premium quota; plan preference only
        # within those tiers. Stable percentage/id ties preserve replay order.
        score = (
            {"GREEN": 0, "YELLOW": 1, "RED": 2}[band],
            route["premium"],
            route["id"] not in task["preferred_routes"],
            cap["used_percent"],
            route["id"],
        )
        candidates.append((score, route))
    return min(candidates, key=lambda x: x[0])[1] if candidates else None


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise SupervisorError("symlink state path forbidden")
    fd, tmp = tempfile.mkstemp(prefix=".atomic-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(tmp, path)  # Never overwrite a terminal receipt or dispatch spec.
            os.unlink(tmp)
        else:
            os.replace(tmp, path)
        _sync_directory(path.parent)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def external_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if root.is_symlink() or resolved == Path(resolved.anchor):
        raise SupervisorError("unsafe state root")
    for parent in (resolved, *resolved.parents):
        if (parent / ".git").exists():
            raise SupervisorError("state root must be outside repositories")
    return resolved


class State:
    """Supervisor owns events/checkpoint; each wrapper owns one terminal receipt."""

    def __init__(self, root: Path):
        self.root = external_root(root)

    def path(self, *parts: str) -> Path:
        path = self.root.joinpath(*parts)
        # Refuse redirected state, including intermediate directory symlinks.
        for p in (self.root, *path.relative_to(self.root).parents):
            check = p if p.is_absolute() else self.root / p
            if check.is_symlink():
                raise SupervisorError("symlink state path forbidden")
        if path.is_symlink():
            raise SupervisorError("symlink state path forbidden")
        return path

    @contextmanager
    def lock(self, *, create: bool = False) -> Iterator[None]:
        if create:
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise SupervisorError("state not initialized")
        path = self.path("writer.lock")
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SupervisorError("another supervisor owns state") from exc
            yield
        finally:
            os.close(fd)

    def campaign(self) -> dict:
        campaign = load_json(self.path("campaign.json"))
        validate_campaign(campaign)
        return campaign

    def replay(self, campaign: dict) -> tuple[list[dict], dict]:
        path = self.path("events.jsonl")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise SupervisorError("event log missing") from exc
        if not raw or not raw.endswith(b"\n"):
            raise SupervisorError("event log incomplete; operator recovery required")
        events = []
        attempts: dict = {}
        previous = "0" * 64
        for line in raw.splitlines():
            try:
                event = json.loads(line, object_pairs_hook=_pairs)
            except (ValueError, UnicodeError) as exc:
                raise SupervisorError("corrupt event log") from exc
            fields(event, {"seq", "previous", "kind", "data", "hash"})
            unhashed = {k: v for k, v in event.items() if k != "hash"}
            if (
                type(event["seq"]) is not int
                or event["seq"] != len(events) + 1
                or event["previous"] != previous
                or event["hash"] != digest(unhashed)
            ):
                raise SupervisorError("event chain mismatch")
            kind, data = event["kind"], event["data"]
            if not events:
                if kind != "INIT" or data != {
                    "campaign_sha256": digest(campaign),
                    "routes_sha256": load_json(self.path("binding.json"))[
                        "routes_sha256"
                    ],
                }:
                    raise SupervisorError("campaign/event binding mismatch")
            elif kind == "INTENT":
                fields(
                    data,
                    {
                        "id",
                        "task_id",
                        "route_id",
                        "family",
                        "runtime",
                        "pool",
                        "release_id",
                        "successor_of",
                        "spec_sha256",
                    },
                )
                for key in (
                    "id",
                    "task_id",
                    "route_id",
                    "family",
                    "runtime",
                    "pool",
                    "release_id",
                ):
                    identifier(data[key])
                if data["id"] in attempts or data["task_id"] not in {
                    t["id"] for t in campaign["tasks"]
                }:
                    raise SupervisorError("invalid dispatch intent")
                prior = task_attempts(attempts, data["task_id"])
                if data["successor_of"] is None:
                    if prior:
                        raise SupervisorError("duplicate initial dispatch")
                else:
                    parent = attempts.get(data["successor_of"])
                    if (
                        not parent
                        or parent["task_id"] != data["task_id"]
                        or parent["status"] != "CAPACITY_FAILED"
                        or prior[-1]["id"] != parent["id"]
                    ):
                        raise SupervisorError("invalid successor intent")
                attempts[data["id"]] = {**data, "status": "OUTCOME_UNKNOWN"}
            elif kind == "TERMINAL":
                fields(data, {"attempt_id", "spec_sha256", "status", "exit_code"})
                attempt = attempts.get(data["attempt_id"])
                if (
                    not attempt
                    or attempt["status"] in TERMINAL
                    or not isinstance(data["status"], str)
                    or data["status"] not in TERMINAL
                    or data["spec_sha256"] != attempt["spec_sha256"]
                ):
                    raise SupervisorError("invalid terminal transition")
                self.validate_receipt(data, attempt)
                attempt.update(status=data["status"], exit_code=data["exit_code"])
            else:
                raise SupervisorError("unknown event kind")
            events.append(event)
            previous = event["hash"]
        return events, attempts

    def append(self, events: list[dict], kind: str, data: dict) -> None:
        event = {
            "seq": len(events) + 1,
            "previous": events[-1]["hash"] if events else "0" * 64,
            "kind": kind,
            "data": data,
        }
        event["hash"] = digest(event)
        path = self.path("events.jsonl")
        fd = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(fd, "ab") as stream:
            stream.write(canonical(event))
            stream.flush()
            os.fsync(stream.fileno())
        _sync_directory(self.root)
        events.append(event)

    def checkpoint(self, campaign: dict, events: list[dict], attempts: dict) -> dict:
        value = {
            "version": VERSION,
            "campaign_id": campaign["id"],
            "seq": len(events),
            "event_hash": events[-1]["hash"],
            "attempts": attempts,
        }
        atomic_json(self.path("checkpoint.json"), value)
        return value

    def initialize(self, campaign: dict, ledger: dict) -> None:
        validate_campaign(campaign)
        validate_routes(ledger, campaign)
        with self.lock(create=True):
            # Failed init is intentionally not silently resumed or overwritten.
            if any(
                self.path(p).exists()
                for p in ("campaign.json", "binding.json", "events.jsonl", "attempts")
            ):
                raise SupervisorError("state already initialized or partial init")
            self.path("attempts").mkdir(mode=0o700)
            atomic_json(self.path("campaign.json"), campaign, exclusive=True)
            atomic_json(
                self.path("binding.json"),
                {"routes_sha256": route_binding(ledger)},
                exclusive=True,
            )
            events: list[dict] = []
            self.append(
                events,
                "INIT",
                {
                    "campaign_sha256": digest(campaign),
                    "routes_sha256": route_binding(ledger),
                },
            )
            self.checkpoint(campaign, events, {})

    def validate_receipt(self, receipt: dict, attempt: dict) -> None:
        fields(receipt, {"attempt_id", "spec_sha256", "status", "exit_code"})
        if (
            receipt["attempt_id"] != attempt["id"]
            or receipt["spec_sha256"] != attempt["spec_sha256"]
        ):
            raise SupervisorError("receipt binding mismatch")
        spec = load_json(self.path("attempts", attempt["id"], "spec.json"))
        if digest(spec) != attempt["spec_sha256"]:
            raise SupervisorError("dispatch specification changed")
        code = receipt["exit_code"]
        if code is None:
            expected = "LAUNCH_FAILED"
        elif type(code) is not int or not -255 <= code <= 255:
            raise SupervisorError("invalid receipt exit code")
        else:
            expected = (
                "SUCCEEDED"
                if code == 0
                else (
                    "CAPACITY_FAILED"
                    if code in spec["capacity_exit_codes"]
                    else "FAILED"
                )
            )
        if receipt["status"] != expected:
            raise SupervisorError("receipt status/exit mismatch")

    def reconcile(
        self, campaign: dict, events: list[dict], attempts: dict, *, persist: bool
    ) -> None:
        for attempt_id in sorted(attempts):
            attempt = attempts[attempt_id]
            receipt_path = self.path("attempts", attempt_id, "receipt.json")
            if receipt_path.exists():
                receipt = load_json(receipt_path)
                self.validate_receipt(receipt, attempt)
                if attempt["status"] in TERMINAL:
                    if (attempt["status"], attempt["exit_code"]) != (
                        receipt["status"],
                        receipt["exit_code"],
                    ):
                        raise SupervisorError("terminal receipt changed")
                    continue
                if persist:
                    self.append(events, "TERMINAL", receipt)
                attempt.update(status=receipt["status"], exit_code=receipt["exit_code"])
        if persist:
            self.checkpoint(campaign, events, attempts)

    def status(self) -> dict:
        with self.lock():
            campaign = self.campaign()
            events, attempts = self.replay(campaign)
            self.reconcile(campaign, events, attempts, persist=False)
            return {
                "campaign_id": campaign["id"],
                "event_seq": len(events),
                "attempts": attempts,
                "ready": [t["id"] for t in ready_tasks(campaign, attempts)],
            }

    def run(
        self,
        ledger: dict,
        *,
        max_dispatch: int = 1,
        successor_of: str | None = None,
        successor_release: str | None = None,
    ) -> list[str]:
        integer(max_dispatch, 1)
        if (successor_of is None) != (successor_release is None):
            raise SupervisorError("successor requires explicit attempt and release")
        if successor_of is not None:
            identifier(successor_of)
            identifier(successor_release)
            if max_dispatch != 1:
                raise SupervisorError("successor invocation dispatches exactly once")
        launched = []
        with self.lock():
            campaign = self.campaign()
            validate_routes(ledger, campaign)
            if load_json(self.path("binding.json")) != {
                "routes_sha256": route_binding(ledger)
            }:
                raise SupervisorError(
                    "route declarations changed; capacity-only refresh allowed"
                )
            events, attempts = self.replay(campaign)
            self.reconcile(campaign, events, attempts, persist=True)
            for _ in range(max_dispatch):
                self.reconcile(campaign, events, attempts, persist=True)
                if (
                    sum(a["status"] not in TERMINAL for a in attempts.values())
                    >= campaign["max_parallel"]
                ):
                    break
                if successor_of is not None:
                    parent = attempts.get(successor_of)
                    if not parent or parent["status"] != "CAPACITY_FAILED":
                        raise SupervisorError(
                            "successor needs terminal capacity failure"
                        )
                    history = task_attempts(attempts, parent["task_id"])
                    if history[-1]["id"] != successor_of:
                        raise SupervisorError("successor already exists")
                    if successor_release == parent["release_id"] or any(
                        a["release_id"] == successor_release for a in attempts.values()
                    ):
                        raise SupervisorError("successor release must be distinct")
                    tasks = [
                        t for t in campaign["tasks"] if t["id"] == parent["task_id"]
                    ]
                else:
                    tasks = ready_tasks(campaign, attempts)
                selected = None
                for task in tasks:
                    route = choose_route(task, ledger["routes"], attempts, time.time())
                    if route is not None:
                        selected = (task, route)
                        break
                if selected is None:
                    break
                task, route = selected
                attempt_id = f"attempt-{len(attempts) + 1:06d}"
                directory = self.path("attempts", attempt_id)
                directory.mkdir(mode=0o700)  # Orphan spec => stop, never reuse its ID.
                _sync_directory(directory.parent)
                spec = {
                    "attempt_id": attempt_id,
                    "task_id": task["id"],
                    "argv": route["argv"],
                    "capacity_exit_codes": route["capacity_exit_codes"],
                    "route_sha256": digest(route),
                    "campaign_sha256": digest(campaign),
                }
                atomic_json(directory / "spec.json", spec, exclusive=True)
                intent = {
                    "id": attempt_id,
                    "task_id": task["id"],
                    "route_id": route["id"],
                    "family": route["family"],
                    "runtime": route["runtime"],
                    "pool": route["pool"],
                    "release_id": successor_release or task["release_id"],
                    "successor_of": successor_of,
                    "spec_sha256": digest(spec),
                }
                self.append(events, "INTENT", intent)
                attempts[attempt_id] = {**intent, "status": "OUTCOME_UNKNOWN"}
                self.checkpoint(campaign, events, attempts)
                # Intent is durable before any process launch. No resumption of
                # intent without receipt, even when Popen may never have run.
                try:
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "_worker",
                            str(self.root),
                            attempt_id,
                        ],
                        shell=False,
                        start_new_session=True,
                        close_fds=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        cwd=directory,
                    )
                except OSError:
                    atomic_json(
                        directory / "receipt.json",
                        {
                            "attempt_id": attempt_id,
                            "spec_sha256": digest(spec),
                            "status": "LAUNCH_FAILED",
                            "exit_code": None,
                        },
                        exclusive=True,
                    )
                    self.reconcile(campaign, events, attempts, persist=True)
                launched.append(attempt_id)
        return launched


def worker(root: Path, attempt_id: str) -> int:
    """Detached receipt writer. Never holds supervisor lock while runner executes."""
    identifier(attempt_id)
    state = State(root)
    directory = state.path("attempts", attempt_id)
    fd = os.open(
        state.path("attempts", attempt_id, "wrapper.lock"),
        os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
        0o600,
    )
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 2
        # Lifetime-independent dedupe: completed or previously started wrapper
        # can never start again, even after death before terminal receipt.
        started = state.path("attempts", attempt_id, "started.json")
        receipt_path = state.path("attempts", attempt_id, "receipt.json")
        if receipt_path.exists() or started.exists():
            return 2
        spec = load_json(state.path("attempts", attempt_id, "spec.json"))
        fields(
            spec,
            {
                "attempt_id",
                "task_id",
                "argv",
                "capacity_exit_codes",
                "route_sha256",
                "campaign_sha256",
            },
        )
        if spec["attempt_id"] != attempt_id:
            raise SupervisorError("wrapper specification binding mismatch")
        # Read durable intent under one-writer lock before independent launch.
        # Parent may still hold lock: do not race it or give up and lose dispatch.
        lock_fd = os.open(state.path("writer.lock"), os.O_RDONLY | os.O_NOFOLLOW)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_SH)
            campaign = state.campaign()
            _, attempts = state.replay(campaign)
            attempt = attempts.get(attempt_id)
            if (
                not attempt
                or attempt["status"] in TERMINAL
                or attempt["task_id"] != spec["task_id"]
                or attempt["spec_sha256"] != digest(spec)
                or spec["campaign_sha256"] != digest(campaign)
            ):
                raise SupervisorError("wrapper has no matching intent")
        finally:
            os.close(lock_fd)
        atomic_json(started, {"spec_sha256": digest(spec)}, exclusive=True)
        code = None
        try:
            env = dict(os.environ)
            env.update(
                DMX_ARCHAEOLOGY_TASK_ID=spec["task_id"],
                DMX_ARCHAEOLOGY_ATTEMPT_ID=attempt_id,
            )
            code = subprocess.run(
                spec["argv"],
                shell=False,
                check=False,
                close_fds=True,
                cwd=directory,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
        except OSError:
            pass
        status = (
            "LAUNCH_FAILED"
            if code is None
            else (
                "SUCCEEDED"
                if code == 0
                else (
                    "CAPACITY_FAILED"
                    if code in spec["capacity_exit_codes"]
                    else "FAILED"
                )
            )
        )
        atomic_json(
            receipt_path,
            {
                "attempt_id": attempt_id,
                "spec_sha256": digest(spec),
                "status": status,
                "exit_code": code,
            },
            exclusive=True,
        )
        return 0
    finally:
        os.close(fd)


def probe(executable: str, *, catalog: bool = False) -> dict:
    """Fixed metadata commands only. Never print tool output or environment."""
    if executable not in {"codex", "claude", "gemini", "opencode"} or (
        catalog and executable != "opencode"
    ):
        raise SupervisorError("unsupported metadata probe")
    path = shutil.which(executable)
    if path is None:
        return {"tool": executable, "status": "NOT_INSTALLED", "inference": "NOT_RUN"}
    argv = [path, "models"] if catalog else [path, "--version"]
    try:
        result = subprocess.run(
            argv,
            shell=False,
            check=False,
            timeout=15,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=tempfile.gettempdir(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"tool": executable, "status": "UNKNOWN", "inference": "NOT_RUN"}
    result_data = {
        "tool": executable,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "exit_code": result.returncode,
        "probe": "catalog" if catalog else "version",
        "inference": "NOT_RUN",
    }
    if not catalog:
        match = re.search(
            rb"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+)(?![0-9])", result.stdout[:4096]
        )
        result_data["version"] = match.group(1).decode() if match else "UNKNOWN"
    else:
        result_data["catalog_lines"] = (
            len(result.stdout.splitlines()) if result.returncode == 0 else None
        )
    return result_data


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    validate = commands.add_parser(
        "validate", help="read-only campaign and route contract check"
    )
    validate.add_argument("--campaign", type=Path, required=True)
    validate.add_argument("--routes", type=Path, required=True)
    init = commands.add_parser("init", help="bind immutable campaign to external state")
    init.add_argument("--campaign", type=Path, required=True)
    init.add_argument("--routes", type=Path, required=True)
    init.add_argument("--state-root", type=Path, required=True)
    status = commands.add_parser(
        "status", help="replay events and inspect receipts; no dispatch"
    )
    status.add_argument("--state-root", type=Path, required=True)
    run = commands.add_parser(
        "run", help="dispatch released tasks; never retry implicitly"
    )
    run.add_argument("--state-root", type=Path, required=True)
    run.add_argument("--routes", type=Path, required=True)
    run.add_argument("--once", action="store_true")
    run.add_argument("--max-dispatch", type=int, default=1)
    run.add_argument("--successor-of")
    run.add_argument("--successor-release")
    meta = commands.add_parser(
        "probe", help="metadata only; never inference or quota calls"
    )
    meta.add_argument("tool", choices=["codex", "claude", "gemini", "opencode"])
    meta.add_argument(
        "--catalog", action="store_true", help="OpenCode model catalog only"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command in {"validate", "init"}:
            campaign, ledger = load_json(args.campaign), load_json(args.routes)
            validate_campaign(campaign)
            validate_routes(ledger, campaign)
            if args.command == "init":
                State(args.state_root).initialize(campaign, ledger)
            result = {"status": "PASS", "campaign_id": campaign["id"]}
        elif args.command == "status":
            result = State(args.state_root).status()
        elif args.command == "run":
            if args.once and args.max_dispatch != 1:
                raise SupervisorError("--once conflicts with --max-dispatch")
            result = {
                "dispatched": State(args.state_root).run(
                    load_json(args.routes),
                    max_dispatch=args.max_dispatch,
                    successor_of=args.successor_of,
                    successor_release=args.successor_release,
                )
            }
        else:
            result = probe(args.tool, catalog=args.catalog)
        print(canonical(result).decode(), end="")
        return 0
    except SupervisorError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print("BLOCKED: state/process filesystem operation failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "_worker":
        try:
            sys.exit(worker(Path(sys.argv[2]), sys.argv[3]))
        except (SupervisorError, OSError):
            sys.exit(2)
    sys.exit(main())
