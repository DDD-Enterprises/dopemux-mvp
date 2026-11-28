"""Authenticated bridge runtime gates; synthetic Docker/HTTP, real Git/PID leases."""

from __future__ import annotations

import io
import json
import os
import signal
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest

from dopemux.auth import AuthError
from dopemux.mcp import docker_inspect as di
from dopemux.mcp import docker_runtime as dr
from dopemux.mcp import http_stdio_bridge as bridge
from dopemux.mcp import reap
from dopemux.mcp.lifecycle import runtime_dir_for
from dopemux.mcp.runtime_registry import RuntimeRegistry, build_instance_record
from dopemux.mcp.runtime_state import resolve_identity_view


@pytest.fixture
def runtime_case(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    # URL entries are valid: bridge protection must not require launcher entries.
    (root / ".mcp.json").write_text(
        '{"mcpServers":{"dope-memory":{"type":"http","url":"http://localhost:3120/mcp"}}}'
    )
    monkeypatch.chdir(root)
    monkeypatch.setenv(
        "DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "runtime" / "instances.json")
    )
    monkeypatch.delenv("DOPEMUX_MCP_BRIDGE_REQUIRE_API_ONLY", raising=False)
    identity = resolve_identity_view(root)
    envrc = root / ".envrc.dopemux-mcp"
    envrc.write_text(
        f"DOPE_MEMORY_PORT=3120\nDOPE_MEMORY_WORKSPACE_ID={root.name}\n"
        f"DOPE_MEMORY_INSTANCE_ID={identity.instance_id}\nCONPORT_MCP_PORT=3105\nCONPORT_HTTP_PORT=3104\n"
        f"DOPEMUX_WORKSPACE_ID={root}\nDOPEMUX_INSTANCE_ID={identity.instance_id}\n"
        "DOPE_MEMORY_EVENTBUS_ENABLED=false\n"
    )
    container = di.DockerContainerInfo(
        id="owned",
        name="memory",
        published_ports=[3120],
        labels={
            dr.LABEL_MANAGED: "true",
            "dopemux.project_id": identity.project_id,
            "dopemux.worktree_hash": identity.worktree_hash,
            "dopemux.service": "dope-memory",
            "dopemux.scope": "worktree",
        },
    )
    state = {
        "containers": [container],
        "available": True,
        "mode": False,
        "health": {
            "auth_mode": "log",
            "identity_required_writes": True,
            "auth_hash_file": "ok",
            "auth_principal_column": "ok",
        },
        "token": [],
        "http": [],
        "health_calls": [],
        "inspect": [],
    }
    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(
            available=state["available"], containers=state["containers"]
        ),
    )

    def inspect(container_id, **kwargs):
        state["inspect"].append(container_id)
        return state["mode"]

    monkeypatch.setattr(dr, "inspect_dope_memory_eventbus_mode", inspect)

    def token(principal):
        state["token"].append(principal)
        return "synthetic-bearer"

    monkeypatch.setattr(bridge, "get_token", token)

    class Response:
        status = 200
        headers = {"Content-Type": "application/json", "Mcp-Session-Id": "test-session"}

        def __init__(self, body):
            self.body = body

        def read(self, limit=-1):
            raw = json.dumps(self.body).encode()
            return raw if limit < 0 else raw[:limit]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def open_request(opener, request, **kwargs):
        if request.full_url.endswith("/health"):
            state["health_calls"].append(request)
            assert request.get_header("Authorization") is None
            return Response(state["health"])
        state["http"].append(request)
        msg = json.loads(request.data)
        return Response({"jsonrpc": "2.0", "id": msg.get("id"), "result": {"ok": True}})

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", open_request)
    return SimpleNamespace(
        root=root,
        identity=identity,
        envrc=envrc,
        container=container,
        state=state,
        runtime=runtime_dir_for(identity),
        response=Response,
    )


def _run(monkeypatch, server="dope-memory", lines=None):
    if lines is None:
        lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize"}]
    monkeypatch.setattr(
        bridge.sys, "stdin", io.StringIO("".join(json.dumps(x) + "\n" for x in lines))
    )
    return bridge.main(["--server", server, "--principal", "runner:codex"])


@pytest.mark.parametrize(
    "kind", ["foreign", "unknown", "missing", "ambiguous", "empty_id"]
)
def test_bridge_refuses_unproved_owner_before_token_or_http(
    runtime_case, monkeypatch, kind
):
    c = runtime_case
    if kind == "foreign":
        c.container.labels["dopemux.project_id"] = "foreign"
    elif kind == "unknown":
        c.state["available"] = False
    elif kind == "missing":
        c.state["containers"] = []
    elif kind == "ambiguous":
        c.state["containers"].append(c.container)
    else:
        c.container.id = ""
    assert _run(monkeypatch) != 0
    assert c.state["token"] == [] and c.state["http"] == []
    assert c.state["inspect"] == []


@pytest.mark.parametrize("mode", [True, None])
def test_bridge_refuses_mismatch_unknown_mode_before_token(
    runtime_case, monkeypatch, mode
):
    c = runtime_case
    c.state["mode"] = mode
    assert _run(monkeypatch) != 0
    assert c.state["token"] == [] and c.state["http"] == []


@pytest.mark.parametrize(
    "bad_health",
    [
        {},
        {"auth_mode": "off"},
        {"auth_mode": []},
        {"auth_mode": "log", "identity_required_writes": False, "auth_hash_file": "ok"},
        {
            "auth_mode": "log",
            "identity_required_writes": True,
            "auth_hash_file": "missing",
        },
    ],
)
def test_bridge_refuses_old_or_unqualified_health_before_token(
    runtime_case, monkeypatch, bad_health
):
    c = runtime_case
    c.state["health"] = bad_health
    assert _run(monkeypatch) != 0
    assert c.state["token"] == [] and c.state["http"] == []


def test_bridge_api_only_policy_survives_missing_envrc_flag(runtime_case, monkeypatch):
    c = runtime_case
    c.envrc.write_text(
        c.envrc.read_text().replace("DOPE_MEMORY_EVENTBUS_ENABLED=false\n", "")
    )
    c.state["mode"] = True
    monkeypatch.setenv("DOPEMUX_MCP_BRIDGE_REQUIRE_API_ONLY", "true")
    assert _run(monkeypatch) != 0
    assert c.state["token"] == [] and c.state["http"] == []


@pytest.mark.parametrize("policy", ["TRUE", "yes", "1", ""])
def test_bridge_policy_is_literal_fail_closed(runtime_case, monkeypatch, policy):
    monkeypatch.setenv("DOPEMUX_MCP_BRIDGE_REQUIRE_API_ONLY", policy)
    assert _run(monkeypatch) != 0
    assert runtime_case.state["token"] == [] and runtime_case.state["http"] == []


def test_bridge_conport_health_port_must_have_same_owner(runtime_case, monkeypatch):
    c = runtime_case
    c.container.labels["dopemux.service"] = "conport"
    c.container.published_ports = [3105]  # REST port is not owned by this container
    assert _run(monkeypatch, "conport") != 0
    assert (
        c.state["token"] == []
        and c.state["http"] == []
        and c.state["health_calls"] == []
    )


def _registry(c):
    path = Path(os.environ["DOPEMUX_MCP_RUNTIME_REGISTRY"])
    registry = RuntimeRegistry.load(path, create_missing=True)
    registry.upsert_instance(
        build_instance_record(
            instance_id="memory",
            project_id=c.identity.project_id,
            workspace_id=str(c.root),
            project_root=str(c.root),
            worktree_root=str(c.root),
            worktree_hash=c.identity.worktree_hash,
            project_hash=c.identity.project_hash,
            service="dope-memory",
            scope="worktree",
            status="running",
            ports={"DOPE_MEMORY_PORT": 3120},
            urls={},
            container_names=["memory"],
            compose_project_name="test",
            labels={},
        )
    )
    registry.save()
    return RuntimeRegistry.load(path)


def test_bridge_live_pid_lease_blocks_reaper_while_waiting_for_stdin(
    runtime_case, monkeypatch
):
    c = runtime_case
    registry = _registry(c)
    c.runtime.mkdir(parents=True, exist_ok=True)
    (c.runtime / "last_detach").write_text("old")
    old = time.time() - 3600
    os.utime(c.runtime / "last_detach", (old, old))
    assert reap.plan_reap(registry=registry, containers=[c.container], now=time.time())
    entered, finish = threading.Event(), threading.Event()
    outcome = []

    class Stdin:
        def readline(self):
            entered.set()
            assert finish.wait(5)
            return ""

    monkeypatch.setattr(bridge.sys, "stdin", Stdin())
    worker = threading.Thread(
        target=lambda: outcome.append(
            bridge.main(["--server", "dope-memory", "--principal", "runner:codex"])
        )
    )
    worker.start()
    try:
        assert entered.wait(5)
        record = c.runtime / "attached" / str(os.getpid())
        assert record.is_file()
        assert reap.live_attachments(c.runtime, prune=False) == 1
        assert (
            reap.plan_reap(registry=registry, containers=[c.container], now=time.time())
            == []
        )
    finally:
        finish.set()
        worker.join(5)
    assert not worker.is_alive() and outcome == [0]
    assert reap.live_attachments(c.runtime) == 0


@pytest.mark.parametrize("failure", ["token", "http_auth", "sigterm", "stdin_error"])
def test_bridge_detaches_on_errors_and_signals(runtime_case, monkeypatch, failure):
    c = runtime_case
    if failure == "token":

        def token(principal):
            assert reap.live_attachments(c.runtime) == 1
            raise AuthError("synthetic unavailable token")

        monkeypatch.setattr(bridge, "get_token", token)
        assert _run(monkeypatch) != 0
    elif failure == "http_auth":
        original = urllib.request.OpenerDirector.open

        def reject(opener, request, **kwargs):
            if request.full_url.endswith("/health"):
                return original(opener, request, **kwargs)
            assert reap.live_attachments(c.runtime) == 1
            raise urllib.error.HTTPError(
                request.full_url, 401, "denied", {}, io.BytesIO()
            )

        monkeypatch.setattr(urllib.request.OpenerDirector, "open", reject)
        assert _run(monkeypatch) == bridge.EXIT_AUTH
    else:

        class Stdin:
            def readline(self):
                assert reap.live_attachments(c.runtime) == 1
                if failure == "sigterm":
                    signal.raise_signal(signal.SIGTERM)
                raise RuntimeError("synthetic stdin error")

        monkeypatch.setattr(bridge.sys, "stdin", Stdin())
        with pytest.raises(
            SystemExit if failure == "sigterm" else RuntimeError
        ) as error:
            bridge.main(["--server", "dope-memory", "--principal", "runner:codex"])
        if failure == "sigterm":
            assert error.value.code == 143
    assert reap.live_attachments(c.runtime) == 0


def test_bridge_attach_itself_is_inside_cleanup_boundary(runtime_case, monkeypatch):
    from dopemux.mcp import bridge_runtime

    c = runtime_case
    real_attach = bridge_runtime.attach

    def interrupted(path):
        real_attach(path)
        signal.raise_signal(signal.SIGTERM)

    monkeypatch.setattr(bridge_runtime, "attach", interrupted)
    with pytest.raises(SystemExit) as error:
        _run(monkeypatch)
    assert error.value.code == 143
    assert reap.live_attachments(c.runtime) == 0
    assert c.state["token"] == [] and c.state["http"] == []


def test_bridge_http_and_stdin_never_hold_instance_lock(runtime_case, monkeypatch):
    from contextlib import contextmanager
    from dopemux.mcp import bridge_runtime

    held = []
    lock = bridge_runtime.instance_lock

    @contextmanager
    def observed(path):
        with lock(path):
            held.append(True)
            try:
                yield
            finally:
                held.pop()

    original = urllib.request.OpenerDirector.open

    def open_request(opener, request, **kwargs):
        assert not held
        return original(opener, request, **kwargs)

    monkeypatch.setattr(bridge_runtime, "instance_lock", observed)
    monkeypatch.setattr(urllib.request.OpenerDirector, "open", open_request)

    class Stdin:
        def readline(self):
            assert not held
            return ""

    monkeypatch.setattr(bridge.sys, "stdin", Stdin())
    assert bridge.main(["--server", "dope-memory", "--principal", "runner:codex"]) == 0


@pytest.mark.parametrize("change", ["foreign", "mode", "old_health"])
def test_bridge_session_expiry_revalidates_before_any_retry(
    runtime_case, monkeypatch, change
):
    c = runtime_case
    original = urllib.request.OpenerDirector.open

    def expired(opener, request, **kwargs):
        if (
            request.full_url.endswith("/mcp")
            and json.loads(request.data)["method"] == "tools/list"
        ):
            c.state["http"].append(request)
            if change == "foreign":
                c.container.labels["dopemux.project_id"] = "foreign"
            elif change == "mode":
                c.state["mode"] = None
            else:
                c.state["health"] = {}
            raise urllib.error.HTTPError(
                request.full_url, 404, "gone", {}, io.BytesIO()
            )
        return original(opener, request, **kwargs)

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", expired)
    assert (
        _run(
            monkeypatch,
            lines=[
                {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            ],
        )
        != 0
    )
    assert len(c.state["http"]) == 2  # no credential-bearing re-initialize/retry
    assert len(c.state["token"]) == 1
    assert reap.live_attachments(c.runtime) == 0


@pytest.mark.parametrize("change", ["port", "ids", "intent"])
def test_bridge_config_drift_refuses_next_exchange(runtime_case, monkeypatch, change):
    c = runtime_case
    original = urllib.request.OpenerDirector.open

    def changed(opener, request, **kwargs):
        response = original(opener, request, **kwargs)
        if request.full_url.endswith("/mcp"):
            text = c.envrc.read_text()
            if change == "port":
                text = text.replace("DOPE_MEMORY_PORT=3120", "DOPE_MEMORY_PORT=3121")
            elif change == "ids":
                text = text.replace(
                    f"DOPE_MEMORY_WORKSPACE_ID={c.root.name}",
                    "DOPE_MEMORY_WORKSPACE_ID=elsewhere",
                )
            else:
                text = text.replace("DOPE_MEMORY_EVENTBUS_ENABLED=false\n", "")
            c.envrc.write_text(text)
        return response

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", changed)
    assert (
        _run(
            monkeypatch,
            lines=[
                {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
            ],
        )
        != 0
    )
    assert len(c.state["http"]) == 1


def test_bridge_policy_accepts_proved_false_without_envrc_mode(
    runtime_case, monkeypatch
):
    c = runtime_case
    c.envrc.write_text(
        c.envrc.read_text().replace("DOPE_MEMORY_EVENTBUS_ENABLED=false\n", "")
    )
    monkeypatch.setenv("DOPEMUX_MCP_BRIDGE_REQUIRE_API_ONLY", "true")
    assert _run(monkeypatch) == 0
    assert len(c.state["http"]) == 1
    assert reap.live_attachments(c.runtime) == 0


def test_bridge_git_identity_ignores_ambient_target(runtime_case, monkeypatch):
    monkeypatch.setenv("DOPEMUX_PROJECT_ROOT", "/foreign/project")
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "foreign")
    assert _run(monkeypatch) == 0
    assert runtime_case.state["inspect"] == ["owned", "owned"]


@pytest.mark.parametrize("principal_column", ["missing", "invalid"])
def test_bridge_conport_requires_identity_principal_columns(
    runtime_case, monkeypatch, principal_column
):
    c = runtime_case
    c.container.labels["dopemux.service"] = "conport"
    c.container.published_ports = [3104, 3105]
    c.state["health"]["auth_principal_column"] = principal_column
    assert _run(monkeypatch, "conport") != 0
    assert c.state["token"] == [] and c.state["http"] == []


def test_bridge_conport_qualified_url_target_is_allowed(runtime_case, monkeypatch):
    c = runtime_case
    c.container.labels["dopemux.service"] = "conport"
    c.container.published_ports = [3104, 3105]
    assert _run(monkeypatch, "conport") == 0
    assert len(c.state["http"]) == 1
    assert c.state["health_calls"][0].full_url == "http://127.0.0.1:3104/health"


def test_bridge_health_payload_size_and_timeout_are_bounded(runtime_case, monkeypatch):
    c = runtime_case

    def oversized(opener, request, **kwargs):
        assert request.full_url.endswith("/health")
        assert request.get_method() == "GET" and kwargs["timeout"] == 3.0

        class Response(c.response):
            def read(self, limit=-1):
                assert limit == (1 << 16) + 1
                return b" " * limit

        return Response({})

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", oversized)
    assert _run(monkeypatch) != 0
    assert c.state["token"] == [] and c.state["http"] == []


def test_bridge_rejects_nested_envrc_shadow(runtime_case, monkeypatch):
    c = runtime_case
    nested = c.root / "nested"
    nested.mkdir()
    (nested / c.envrc.name).write_text(c.envrc.read_text())
    monkeypatch.chdir(nested)
    assert _run(monkeypatch) != 0
    assert c.state["token"] == [] and c.state["http"] == []


def test_bridge_runtime_binding_works_for_module_main_discovery(runtime_case):
    """`python -m` builds __main__.Discovery, a distinct class from imported Discovery."""
    from dopemux.mcp.bridge_runtime import runtime_session

    discovered = bridge.discover_profile("dope-memory", runtime_case.root)
    equivalent = SimpleNamespace(
        server=discovered.server,
        envrc_path=discovered.envrc_path,
        port=discovered.port,
        ids=dict(discovered.ids),
        base_url=discovered.base_url,
    )
    with runtime_session(equivalent) as qualify:
        qualify()


def test_bridge_policy_false_never_disables_owner_protection(runtime_case, monkeypatch):
    monkeypatch.setenv("DOPEMUX_MCP_BRIDGE_REQUIRE_API_ONLY", "false")
    runtime_case.container.labels["dopemux.project_id"] = "foreign"
    assert _run(monkeypatch) != 0
    assert runtime_case.state["token"] == [] and runtime_case.state["http"] == []
