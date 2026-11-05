"""Falsification tests. All runner execution uses local Python, never providers."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import Mock

import pytest

from dopemux import archaeology_supervisor as sup


def task(task_id="survey", **updates):
    value = {
        "id": task_id,
        "release_id": "release-001",
        "depends_on": [],
        "capabilities": ["read"],
        "privacy": "internal",
        "allowed_routes": ["ordinary", "alternate"],
        "preferred_routes": ["ordinary"],
        "independent_of": [],
        "premium_allowed": False,
    }
    value.update(updates)
    return value


def route(route_id="ordinary", **updates):
    argv = [sys.executable, "-c", "pass"]
    value = {
        "id": route_id,
        "argv": argv,
        "model": "synthetic-local",
        "family": "family-one",
        "runtime": "runtime-one",
        "capabilities": ["read"],
        "privacy": "internal",
        "pool": route_id,
        "premium": False,
        "reserve_slots": 0,
        "qualification": {
            "status": "VERIFIED",
            "evidence_id": "synthetic-fixture",
            "command_sha256": sup.digest(argv),
        },
        "capacity": {
            "used_percent": 20,
            "slots": 2,
            "observed_at": time.time(),
            "ttl_seconds": 120,
        },
        "capacity_exit_codes": [75],
    }
    value.update(updates)
    if "argv" in updates:
        value["qualification"]["command_sha256"] = sup.digest(value["argv"])
    return value


def campaign(*tasks, **updates):
    value = {
        "version": 1,
        "id": "synthetic-campaign",
        "max_parallel": 2,
        "tasks": list(tasks) or [task()],
    }
    value.update(updates)
    return value


def ledger(*routes):
    return {
        "version": 1,
        "campaign_id": "synthetic-campaign",
        "routes": list(routes) or [route(), route("alternate")],
    }


def initialized(tmp_path, c=None, routes=None):
    c, routes = c or campaign(), routes or ledger()
    state = sup.State(tmp_path / "state")
    state.initialize(c, routes)
    return state, routes


def wait_receipt(state, attempt_id, timeout=10):
    deadline = time.monotonic() + timeout
    path = state.path("attempts", attempt_id, "receipt.json")
    while time.monotonic() < deadline:
        if path.exists():
            return sup.load_json(path)
        time.sleep(0.02)
    pytest.fail("synthetic wrapper failed to produce receipt")


def receipt(state, attempt_id, code=0):
    spec = sup.load_json(state.path("attempts", attempt_id, "spec.json"))
    status = (
        "SUCCEEDED"
        if code == 0
        else "CAPACITY_FAILED" if code in spec["capacity_exit_codes"] else "FAILED"
    )
    value = {
        "attempt_id": attempt_id,
        "spec_sha256": sup.digest(spec),
        "status": status,
        "exit_code": code,
    }
    sup.atomic_json(
        state.path("attempts", attempt_id, "receipt.json"), value, exclusive=True
    )
    return value


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, "UNKNOWN"),
        (0, "GREEN"),
        (69.99, "GREEN"),
        (70, "YELLOW"),
        (84.99, "YELLOW"),
        (85, "RED"),
        (94.99, "RED"),
        (95, "CRITICAL"),
        (100, "CRITICAL"),
    ],
)
def test_capacity_bands(value, expected):
    assert sup.capacity_band(value) == expected


@pytest.mark.parametrize("value", [-1, 101, True, float("nan"), float("inf"), "70"])
def test_capacity_invalid(value):
    with pytest.raises(sup.SupervisorError):
        sup.capacity_band(value)


def test_task_dag_and_release():
    c = campaign(
        task("author"),
        task("audit", depends_on=["author"]),
        task("held", release_id=None),
    )
    assert [t["id"] for t in sup.ready_tasks(c, {})] == ["author"]
    attempts = {"1": {"task_id": "author", "status": "OUTCOME_UNKNOWN"}}
    assert sup.ready_tasks(c, attempts) == []
    attempts["1"]["status"] = "SUCCEEDED"
    assert [t["id"] for t in sup.ready_tasks(c, attempts)] == ["audit"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda c: c.update(extra=True),
        lambda c: c.update(version=True),
        lambda c: c["tasks"].append(deepcopy(c["tasks"][0])),
        lambda c: c["tasks"][0].update(depends_on=["survey"]),
        lambda c: c["tasks"][0].update(depends_on=["absent"]),
        lambda c: c["tasks"][0].update(independent_of=["absent"]),
        lambda c: c["tasks"][0].update(privacy=[]),
        lambda c: c["tasks"][0].update(premium_allowed=1),
        lambda c: c["tasks"][0].update(allowed_routes=["../escape"]),
    ],
)
def test_invalid_campaign(mutate):
    c = campaign()
    mutate(c)
    with pytest.raises(sup.SupervisorError):
        sup.validate_campaign(c)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(argv=["python", "-c", "pass"]),
        lambda r: r.update(privacy=[]),
        lambda r: r["qualification"].update(status="PASS"),
        lambda r: r["qualification"].update(command_sha256="wrong"),
        lambda r: r.update(capacity_exit_codes=[0]),
        lambda r: r.update(capacity_exit_codes=[75, 75]),
        lambda r: r.update(capacity_exit_codes=[[75]]),
        lambda r: r["capacity"].update(slots=True),
        lambda r: r["capacity"].update(ttl_seconds=0),
    ],
)
def test_invalid_route(mutate):
    r = route()
    mutate(r)
    with pytest.raises(sup.SupervisorError):
        sup.validate_routes(ledger(r, route("alternate")), campaign())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(capabilities=[]),
        lambda r: r.update(privacy="public"),
        lambda r: r["qualification"].update(
            status="UNKNOWN", evidence_id=None, command_sha256=None
        ),
        lambda r: r["capacity"].update(used_percent=None),
        lambda r: r["capacity"].update(slots=None),
        lambda r: r["capacity"].update(used_percent=95),
        lambda r: r["capacity"].update(observed_at=time.time() - 1000),
        lambda r: r["capacity"].update(observed_at=time.time() + 1000),
        lambda r: r.update(premium=True),
        lambda r: r.update(id="not-released"),
    ],
)
def test_hard_filters_before_plan_preference(mutate):
    first, second = route(), route("alternate")
    mutate(first)
    assert (
        sup.choose_route(task(), [first, second], {}, time.time())["id"] == "alternate"
    )


def test_scarcity_before_preference_and_stable_ties():
    first, second = route(), route("alternate")
    first["capacity"]["used_percent"] = 90
    assert (
        sup.choose_route(task(), [first, second], {}, time.time())["id"] == "alternate"
    )
    first["capacity"]["used_percent"] = 10
    assert (
        sup.choose_route(task(), [second, first], {}, time.time())["id"] == "ordinary"
    )
    t = task(preferred_routes=[])
    first["capacity"]["used_percent"] = second["capacity"]["used_percent"]
    assert sup.choose_route(t, [first, second], {}, time.time())["id"] == "alternate"


def test_independence_rejects_same_family_or_runtime():
    author = {
        "task_id": "author",
        "family": "family-one",
        "runtime": "runtime-one",
        "pool": "ordinary",
        "status": "SUCCEEDED",
    }
    audit = task("audit", depends_on=["author"], independent_of=["author"])
    candidate = route()
    assert sup.choose_route(audit, [candidate], {"a": author}, time.time()) is None
    candidate["family"] = "family-two"
    assert sup.choose_route(audit, [candidate], {"a": author}, time.time()) is None
    candidate["runtime"] = "runtime-two"
    assert sup.choose_route(audit, [candidate], {"a": author}, time.time()) == candidate


def test_reserve_and_unknown_inflight_count_across_pool():
    r = route(reserve_slots=1)
    active = {
        "a": {
            "task_id": "other",
            "family": "other",
            "runtime": "other",
            "pool": "ordinary",
            "status": "OUTCOME_UNKNOWN",
        }
    }
    assert sup.choose_route(task(), [r], active, time.time()) is None
    assert sup.choose_route(task(premium_allowed=True), [r], active, time.time()) == r
    r["capacity"]["slots"] = 1
    r["reserve_slots"] = 0
    assert (
        sup.choose_route(task(premium_allowed=True), [r], active, time.time()) is None
    )


def test_pool_conflicting_snapshots_rejected():
    r1 = route(pool="shared")
    r2 = route("alternate", pool="shared")
    r2["capacity"] = deepcopy(r1["capacity"])
    sup.validate_routes(ledger(r1, r2), campaign())
    r2["capacity"]["slots"] += 1
    with pytest.raises(sup.SupervisorError, match="conflicting pool"):
        sup.validate_routes(ledger(r1, r2), campaign())


def test_shared_pool_limits_dispatch(tmp_path, monkeypatch):
    c = campaign(task("one"), task("two"), task("three"), max_parallel=3)
    r1, r2 = route(pool="shared"), route("alternate", pool="shared")
    r1["capacity"]["slots"] = 1
    r2["capacity"] = deepcopy(r1["capacity"])
    state, routes = initialized(tmp_path, c, ledger(r1, r2))
    launch = Mock()
    monkeypatch.setattr(sup.subprocess, "Popen", launch)
    assert state.run(routes, max_dispatch=3) == ["attempt-000001"]
    assert launch.call_count == 1
    assert state.run(routes, max_dispatch=3) == []


def test_outcome_unknown_no_duplicate_and_checkpoint_rebuild(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)
    launch = Mock()
    monkeypatch.setattr(sup.subprocess, "Popen", launch)
    assert state.run(routes) == ["attempt-000001"]
    state.path("checkpoint.json").write_text("corrupt cached projection")
    assert state.status()["attempts"]["attempt-000001"]["status"] == "OUTCOME_UNKNOWN"
    assert state.run(routes) == []
    assert launch.call_count == 1
    assert (
        sup.load_json(state.path("checkpoint.json"))["attempts"]["attempt-000001"][
            "status"
        ]
        == "OUTCOME_UNKNOWN"
    )
    receipt(state, "attempt-000001")
    assert state.status()["attempts"]["attempt-000001"]["status"] == "SUCCEEDED"
    assert state.run(routes) == []
    assert launch.call_count == 1
    with state.lock():
        events, attempts = state.replay(state.campaign())
    assert len(events) == 3
    assert attempts["attempt-000001"]["status"] == "SUCCEEDED"


def test_crash_after_intent_before_launch_blocks_duplicate(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)
    checkpoint = state.checkpoint
    launch = Mock()
    monkeypatch.setattr(sup.subprocess, "Popen", launch)

    def crash(c, events, attempts):
        if attempts:
            raise OSError("synthetic crash")
        return checkpoint(c, events, attempts)

    monkeypatch.setattr(state, "checkpoint", crash)
    with pytest.raises(OSError):
        state.run(routes)
    assert launch.call_count == 0
    recovered = sup.State(state.root)
    assert (
        recovered.status()["attempts"]["attempt-000001"]["status"] == "OUTCOME_UNKNOWN"
    )
    assert recovered.run(routes) == []
    assert launch.call_count == 0


def test_terminal_capacity_failure_explicit_successor_only(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)
    monkeypatch.setattr(sup.subprocess, "Popen", Mock())
    state.run(routes)
    receipt(state, "attempt-000001", 75)
    assert state.run(routes) == []
    with pytest.raises(sup.SupervisorError):
        state.run(routes, successor_of="attempt-000001")
    with pytest.raises(sup.SupervisorError):
        state.run(
            routes, successor_of="attempt-000001", successor_release="release-001"
        )
    assert state.run(
        routes, successor_of="attempt-000001", successor_release="release-002"
    ) == ["attempt-000002"]
    assert state.status()["attempts"]["attempt-000001"]["status"] == "CAPACITY_FAILED"
    with pytest.raises(sup.SupervisorError):
        state.run(
            routes, successor_of="attempt-000001", successor_release="release-003"
        )
    receipt(state, "attempt-000002")
    state.run(routes)
    statuses = state.status()["attempts"]
    assert statuses["attempt-000001"]["status"] == "CAPACITY_FAILED"
    assert statuses["attempt-000002"]["status"] == "SUCCEEDED"


@pytest.mark.parametrize("code", [None, 0, 1])
def test_successor_rejects_noncapacity_outcomes(tmp_path, monkeypatch, code):
    state, routes = initialized(tmp_path)
    monkeypatch.setattr(sup.subprocess, "Popen", Mock())
    state.run(routes)
    if code is not None:
        receipt(state, "attempt-000001", code)
    with pytest.raises(sup.SupervisorError, match="terminal capacity failure"):
        state.run(
            routes, successor_of="attempt-000001", successor_release="release-002"
        )


def test_wrapper_launch_failure_terminal_no_retry(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)
    monkeypatch.setattr(
        sup.subprocess, "Popen", Mock(side_effect=OSError("synthetic failure"))
    )
    assert state.run(routes) == ["attempt-000001"]
    assert state.status()["attempts"]["attempt-000001"]["status"] == "LAUNCH_FAILED"
    assert state.run(routes) == []


def test_route_drift_rejected_capacity_refresh_accepted(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)
    monkeypatch.setattr(sup.subprocess, "Popen", Mock())
    drift = deepcopy(routes)
    drift["routes"][0]["family"] = "changed-family"
    with pytest.raises(sup.SupervisorError, match="declarations changed"):
        state.run(drift)
    refresh = deepcopy(routes)
    refresh["routes"][0]["capacity"]["used_percent"] = 95
    assert state.run(refresh) == ["attempt-000001"]
    assert state.status()["attempts"]["attempt-000001"]["route_id"] == "alternate"


def test_campaign_drift_and_event_chain_corruption_rejected(tmp_path):
    state, _ = initialized(tmp_path)
    c = state.campaign()
    c["max_parallel"] += 1
    sup.atomic_json(state.path("campaign.json"), c)
    with pytest.raises(sup.SupervisorError, match="binding mismatch"):
        state.status()


@pytest.mark.parametrize(
    "mutation", [lambda raw: raw[:-1], lambda raw: raw.replace(b'"seq":1', b'"seq":2')]
)
def test_truncated_or_tampered_event_log(tmp_path, mutation):
    state, _ = initialized(tmp_path)
    log = state.path("events.jsonl")
    log.write_bytes(mutation(log.read_bytes()))
    with pytest.raises(sup.SupervisorError):
        state.status()


def test_receipt_status_mismatch_and_later_tamper_rejected(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)
    monkeypatch.setattr(sup.subprocess, "Popen", Mock())
    state.run(routes)
    value = receipt(state, "attempt-000001", 75)
    value["status"] = "SUCCEEDED"
    sup.atomic_json(state.path("attempts", "attempt-000001", "receipt.json"), value)
    with pytest.raises(sup.SupervisorError, match="status/exit mismatch"):
        state.run(routes)
    value["status"] = "CAPACITY_FAILED"
    sup.atomic_json(state.path("attempts", "attempt-000001", "receipt.json"), value)
    state.run(routes)
    value.update(status="FAILED", exit_code=1)
    sup.atomic_json(state.path("attempts", "attempt-000001", "receipt.json"), value)
    with pytest.raises(sup.SupervisorError, match="terminal receipt changed"):
        state.status()


def test_lock_atomic_replace_and_receipt_exclusivity(tmp_path):
    state, _ = initialized(tmp_path)
    with state.lock():
        with pytest.raises(sup.SupervisorError, match="another supervisor"):
            with sup.State(state.root).lock():
                pytest.fail("second writer acquired lock")
    path = state.path("test.json")
    sup.atomic_json(path, {"value": 1}, exclusive=True)
    with pytest.raises(FileExistsError):
        sup.atomic_json(path, {"value": 2}, exclusive=True)
    assert sup.load_json(path) == {"value": 1}
    sup.atomic_json(path, {"value": 3})
    assert sup.load_json(path) == {"value": 3}
    assert not list(state.root.glob(".atomic-*"))


def test_atomic_replace_failure_preserves_old_projection(tmp_path, monkeypatch):
    path = tmp_path / "checkpoint.json"
    sup.atomic_json(path, {"old": True})
    monkeypatch.setattr(
        sup.os, "replace", Mock(side_effect=OSError("synthetic rename failure"))
    )
    with pytest.raises(OSError):
        sup.atomic_json(path, {"old": False})
    assert sup.load_json(path) == {"old": True}
    assert not list(tmp_path.glob(".atomic-*"))


def test_state_root_and_symlink_guard(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").touch()
    with pytest.raises(sup.SupervisorError, match="outside repositories"):
        sup.State(repo / "state")
    state, _ = initialized(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    state.path("attempts").rmdir()
    (state.root / "attempts").symlink_to(elsewhere)
    with pytest.raises(sup.SupervisorError, match="symlink"):
        state.path("attempts", "a", "receipt.json")


def test_reinit_and_duplicate_json_keys_fail_closed(tmp_path):
    state, routes = initialized(tmp_path)
    with pytest.raises(sup.SupervisorError, match="already initialized"):
        state.initialize(state.campaign(), routes)
    path = tmp_path / "bad.json"
    path.write_text('{"version":1,"version":2}')
    with pytest.raises(sup.SupervisorError, match="duplicate JSON"):
        sup.load_json(path)


def test_shell_false_and_intent_durable_before_popen(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)

    def launch(argv, **kwargs):
        assert kwargs["shell"] is False
        assert kwargs["start_new_session"] is True
        assert kwargs["close_fds"] is True
        assert argv[0] == sys.executable
        assert argv[2] == "_worker"
        # Do not call status (it correctly refuses concurrent writer).
        _, attempts = state.replay(state.campaign())
        assert attempts["attempt-000001"]["status"] == "OUTCOME_UNKNOWN"
        assert state.path("attempts", "attempt-000001", "spec.json").exists()
        assert sup.load_json(state.path("checkpoint.json"))["attempts"] == attempts

    monkeypatch.setattr(sup.subprocess, "Popen", launch)
    state.run(routes)


def test_wrapper_survives_supervisor_exit_and_arguments_are_literal(tmp_path):
    sentinel = tmp_path / "runner-result.json"
    literal = "$(touch SHOULD_NOT_EXIST); `echo injected`"
    argv = [
        sys.executable,
        "-c",
        "import json,os,pathlib,sys,time; time.sleep(0.25); "
        "pathlib.Path(sys.argv[1]).write_text(json.dumps([sys.argv[2],os.environ['DMX_ARCHAEOLOGY_TASK_ID']])); "
        "print('SYNTHETIC_DO_NOT_LOG')",
        str(sentinel),
        literal,
    ]
    routes = ledger(route(argv=argv), route("alternate"))
    c_path, r_path = tmp_path / "campaign.json", tmp_path / "routes.json"
    c_path.write_bytes(sup.canonical(campaign()))
    r_path.write_bytes(sup.canonical(routes))
    state = sup.State(tmp_path / "state")
    source = Path(sup.__file__).resolve()
    init = subprocess.run(
        [
            sys.executable,
            str(source),
            "init",
            "--campaign",
            str(c_path),
            "--routes",
            str(r_path),
            "--state-root",
            str(state.root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert init.returncode == 0, init.stderr
    parent = subprocess.run(
        [
            sys.executable,
            str(source),
            "run",
            "--state-root",
            str(state.root),
            "--routes",
            str(r_path),
            "--once",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert parent.returncode == 0, parent.stderr
    assert "SYNTHETIC_DO_NOT_LOG" not in parent.stdout + parent.stderr
    assert json.loads(parent.stdout)["dispatched"] == ["attempt-000001"]
    assert wait_receipt(state, "attempt-000001")["status"] == "SUCCEEDED"
    assert json.loads(sentinel.read_text()) == [literal, "survey"]
    assert not state.path("attempts", "attempt-000001", "SHOULD_NOT_EXIST").exists()
    events_before = state.path("events.jsonl").read_bytes()
    assert state.status()["attempts"]["attempt-000001"]["status"] == "SUCCEEDED"
    assert state.path("events.jsonl").read_bytes() == events_before  # status read-only
    assert sup.worker(state.root, "attempt-000001") == 2
    assert state.run(routes) == []
    assert b"SYNTHETIC_DO_NOT_LOG" not in state.path("events.jsonl").read_bytes()


def test_worker_exit_classification(tmp_path):
    routes = ledger(
        route(argv=[sys.executable, "-c", "import sys;sys.exit(75)"]),
        route("alternate"),
    )
    state, _ = initialized(tmp_path, routes=routes)
    state.run(routes)
    assert wait_receipt(state, "attempt-000001")["status"] == "CAPACITY_FAILED"
    assert state.run(routes) == []


def test_worker_started_without_receipt_never_resumes(tmp_path, monkeypatch):
    state, routes = initialized(tmp_path)
    monkeypatch.setattr(sup.subprocess, "Popen", Mock())
    state.run(routes)
    sup.atomic_json(
        state.path("attempts", "attempt-000001", "started.json"),
        {"started": True},
        exclusive=True,
    )
    run = Mock()
    monkeypatch.setattr(sup.subprocess, "run", run)
    assert sup.worker(state.root, "attempt-000001") == 2
    assert run.call_count == 0
    assert state.status()["attempts"]["attempt-000001"]["status"] == "OUTCOME_UNKNOWN"


def test_probe_metadata_only_redacted(monkeypatch):
    monkeypatch.setattr(sup.shutil, "which", lambda name: "/trusted/" + name)
    fake = Mock(
        return_value=subprocess.CompletedProcess(
            [], 0, stdout=b"tool 1.2.3 SECRET_SAMPLE"
        )
    )
    monkeypatch.setattr(sup.subprocess, "run", fake)
    assert sup.probe("claude")["version"] == "1.2.3"
    assert "SECRET_SAMPLE" not in json.dumps(sup.probe("opencode", catalog=True))
    assert fake.call_args.args[0] == ["/trusted/opencode", "models"]
    assert fake.call_args.kwargs["shell"] is False
    with pytest.raises(sup.SupervisorError):
        sup.probe("claude", catalog=True)
    with pytest.raises(sup.SupervisorError):
        sup.probe("unknown-tool")
    monkeypatch.setattr(sup.shutil, "which", lambda _: None)
    assert sup.probe("claude")["status"] == "NOT_INSTALLED"


def test_cli_finite_dispatch_and_no_validation_writes(tmp_path, capsys):
    c_path, r_path = tmp_path / "campaign.json", tmp_path / "routes.json"
    c_path.write_bytes(sup.canonical(campaign()))
    r_path.write_bytes(sup.canonical(ledger()))
    before = sorted(tmp_path.iterdir())
    assert (
        sup.main(["validate", "--campaign", str(c_path), "--routes", str(r_path)]) == 0
    )
    assert sorted(tmp_path.iterdir()) == before
    capsys.readouterr()
    assert (
        sup.main(
            [
                "run",
                "--state-root",
                str(tmp_path / "absent"),
                "--routes",
                str(r_path),
                "--max-dispatch",
                "0",
            ]
        )
        == 2
    )
    assert "BLOCKED:" in capsys.readouterr().err
    assert not (tmp_path / "absent").exists()


def test_wrapper_survives_abrupt_supervisor_death(tmp_path):
    state, routes = initialized(tmp_path)
    route_path = tmp_path / "routes.json"
    route_path.write_bytes(sup.canonical(routes))
    # Kill only this owned supervisor through os._exit after its actual Popen.
    # Wrapper must progress after the parent's lock disappears, without retry.
    source = Path(sup.__file__).resolve()
    program = (
        "import importlib.util,os,pathlib,sys; "
        "spec=importlib.util.spec_from_file_location('subject',sys.argv[1]); "
        "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
        "original=m.subprocess.Popen; "
        "m.subprocess.Popen=lambda *a,**k: (original(*a,**k),os._exit(91)); "
        "m.State(pathlib.Path(sys.argv[2])).run(m.load_json(pathlib.Path(sys.argv[3])))"
    )
    parent = subprocess.run(
        [sys.executable, "-c", program, str(source), str(state.root), str(route_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert parent.returncode == 91
    assert wait_receipt(state, "attempt-000001")["status"] == "SUCCEEDED"
    assert state.run(routes) == []


def test_real_dependency_schedule_and_independence(tmp_path):
    c = campaign(
        task("author"), task("audit", depends_on=["author"], independent_of=["author"])
    )
    routes = ledger(
        route(), route("alternate", family="family-two", runtime="runtime-two")
    )
    state, _ = initialized(tmp_path, c, routes)
    assert state.run(routes, max_dispatch=2) == ["attempt-000001"]
    wait_receipt(state, "attempt-000001")
    assert state.run(routes) == ["attempt-000002"]
    wait_receipt(state, "attempt-000002")
    attempts = state.status()["attempts"]
    assert attempts["attempt-000001"]["route_id"] == "ordinary"
    assert attempts["attempt-000002"]["route_id"] == "alternate"
    assert all(a["status"] == "SUCCEEDED" for a in attempts.values())
    assert state.run(routes) == []
