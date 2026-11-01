"""ConPort ``auth_identity``: modes, hash-file contract, ids, ASGI gate, headers."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys

import pytest

from .helpers import (
    BOUND_WORKSPACE,
    HASH_FILE_NAME,
    OTHER_WORKSPACE,
    WMA_DIR,
    fake_token,
    sha256_hex,
    write_hash_file,
)


def _gate(ai, mode, auth_dir):
    return ai.AuthGate(mode, auth_dir)


# -- mode and env names ------------------------------------------------------


def test_should_use_conport_specific_env_names_and_default_to_log(auth_identity):
    assert auth_identity.ENV_AUTH_MODE == "CONPORT_AUTH_MODE"
    assert auth_identity.ENV_AUTH_DIR == "CONPORT_AUTH_DIR"
    assert auth_identity.load_auth_mode({}) == "log"
    assert auth_identity.load_auth_mode({"CONPORT_AUTH_MODE": " Enforce "}) == "enforce"
    # the dope-memory switch does not move ConPort
    assert auth_identity.load_auth_mode({"DOPE_MEMORY_AUTH_MODE": "enforce"}) == "log"


def test_should_reject_an_unknown_mode(auth_identity):
    with pytest.raises(ValueError, match="CONPORT_AUTH_MODE"):
        auth_identity.load_auth_mode({"CONPORT_AUTH_MODE": "permissive"})
    with pytest.raises(ValueError, match="auth mode"):
        auth_identity.AuthGate("permissive")


# -- the shared hash-file contract (byte-compatible with dope-memory's) ---------


def test_should_share_the_dope_memory_hash_file_contract(auth_identity):
    spec = importlib.util.spec_from_file_location("wma_auth_identity_parity", WMA_DIR / "auth_identity.py")
    wma = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = wma
    try:
        spec.loader.exec_module(wma)
    finally:
        sys.modules.pop(spec.name, None)
    assert auth_identity.HASH_FILE_NAME == wma.HASH_FILE_NAME == HASH_FILE_NAME
    assert auth_identity._PRINCIPAL_RE.pattern == wma._PRINCIPAL_RE.pattern
    assert auth_identity._SHA256_HEX_RE.pattern == wma._SHA256_HEX_RE.pattern
    assert auth_identity.UNVERIFIED_PRINCIPAL == wma.UNVERIFIED_PRINCIPAL
    assert auth_identity.MAX_TOKEN_CHARS == wma.MAX_TOKEN_CHARS


def test_should_verify_what_the_dope_memory_gate_verifies(auth_identity, tmp_path):
    spec = importlib.util.spec_from_file_location("wma_auth_identity_parity2", WMA_DIR / "auth_identity.py")
    wma = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = wma
    try:
        spec.loader.exec_module(wma)
    finally:
        sys.modules.pop(spec.name, None)
    codex, hooks = fake_token("codex"), fake_token("hooks")
    write_hash_file(tmp_path, {codex: "runner:codex", hooks: "internal:hooks"})
    cp = auth_identity.AuthGate("log", tmp_path)
    dm = wma.AuthGate("log", tmp_path)
    for token in (codex, hooks, fake_token("nobody")):
        header = f"Bearer {token}"
        assert cp.authenticate(header).principal == dm.authenticate(header).principal


def test_should_verify_a_token_against_the_hash_file(auth_identity, tmp_path):
    token = fake_token()
    write_hash_file(tmp_path, {token: "runner:codex"})
    gate = _gate(auth_identity, "log", tmp_path)
    identity = gate.authenticate(f"Bearer {token}")
    assert identity.verified and identity.principal == "runner:codex"
    assert gate.authenticate(f"bearer {token}").principal == "runner:codex"


@pytest.mark.parametrize(
    "header",
    [None, "", "Bearer", "Bearer ", "Basic abc", "Token abc", "Bearer " + "x" * 600],
)
def test_should_treat_missing_or_malformed_headers_as_unverified(auth_identity, tmp_path, header):
    write_hash_file(tmp_path, {fake_token(): "runner:codex"})
    gate = _gate(auth_identity, "log", tmp_path)
    assert gate.authenticate(header).principal == "unverified"
    assert not gate.authenticate(header).verified


def test_should_skip_malformed_entries_and_keep_good_ones(auth_identity, tmp_path):
    good = fake_token()
    payload = {
        sha256_hex(good): "runner:codex",
        "not-a-digest": "runner:x",
        sha256_hex("a"): "root",
        sha256_hex("b"): "Runner:Upper",
        sha256_hex("c"): 7,
    }
    (tmp_path / HASH_FILE_NAME).write_text(json.dumps(payload), encoding="utf-8")
    gate = _gate(auth_identity, "log", tmp_path)
    assert gate.authenticate(f"Bearer {good}").principal == "runner:codex"
    assert gate.authenticate("Bearer a").principal == "unverified"
    assert gate.health_fields()["auth_hash_file"] == "ok"


@pytest.mark.parametrize("content", ["{not json", "[]", '"text"', ""])
def test_should_verify_nothing_when_the_file_is_unreadable_or_not_an_object(
    auth_identity, tmp_path, content
):
    (tmp_path / HASH_FILE_NAME).write_text(content, encoding="utf-8")
    gate = _gate(auth_identity, "enforce", tmp_path)
    assert gate.authenticate("Bearer anything").principal == "unverified"
    assert gate.health_fields()["auth_hash_file"] == "invalid"
    with pytest.raises(auth_identity.Unauthorized):
        gate.authorize_write("Bearer anything", "c")


def test_should_report_missing_and_unconfigured_hash_files(auth_identity, tmp_path):
    assert _gate(auth_identity, "log", tmp_path / "nope").health_fields()["auth_hash_file"] == "missing"
    assert _gate(auth_identity, "log", None).health_fields()["auth_hash_file"] == "unconfigured"
    with pytest.raises(auth_identity.Unauthorized):
        _gate(auth_identity, "enforce", None).authorize_write("Bearer x", "c")


def test_should_reread_the_file_when_it_changes(auth_identity, tmp_path):
    old, new = fake_token("old"), fake_token("new")
    path = write_hash_file(tmp_path, {old: "runner:codex"})
    gate = _gate(auth_identity, "log", tmp_path)
    assert gate.authenticate(f"Bearer {old}").verified
    write_hash_file(tmp_path, {new: "runner:claude", fake_token("pad"): "internal:hooks"})
    os.utime(path, ns=(1, 1))  # force a different mtime even on coarse clocks
    assert gate.authenticate(f"Bearer {old}").principal == "unverified"
    assert gate.authenticate(f"Bearer {new}").principal == "runner:claude"


# -- modes ---------------------------------------------------------------------


def test_should_never_verify_in_off_mode(auth_identity, tmp_path):
    token = fake_token()
    write_hash_file(tmp_path, {token: "runner:codex"})
    gate = _gate(auth_identity, "off", tmp_path)
    identity = gate.authorize_write(f"Bearer {token}", "c")
    assert identity.principal == "unverified" and not identity.verified
    assert gate.health_fields()["auth_unverified_calls"] == {}


def test_should_accept_and_count_unverified_callers_in_log_mode(auth_identity, tmp_path):
    write_hash_file(tmp_path, {fake_token(): "runner:codex"})
    gate = _gate(auth_identity, "log", tmp_path)
    assert gate.authorize_write(None, "curl/8").principal == "unverified"
    assert gate.authorize_write("Bearer nope", "curl/8").principal == "unverified"
    assert gate.health_fields()["auth_unverified_calls"] == {"curl/8": 2}


def test_should_reject_unverified_writes_in_enforce_mode(auth_identity, tmp_path):
    token = fake_token()
    write_hash_file(tmp_path, {token: "runner:codex"})
    gate = _gate(auth_identity, "enforce", tmp_path)
    assert gate.authorize_write(f"Bearer {token}", "c").principal == "runner:codex"
    with pytest.raises(auth_identity.Unauthorized, match="401"):
        gate.authorize_write(None, "curl/8")
    assert gate.health_fields()["auth_unverified_calls"] == {"curl/8": 1}


def test_should_report_the_gate_fields_for_the_generator_and_doctor(auth_identity, tmp_path):
    write_hash_file(tmp_path, {})
    fields = _gate(auth_identity, "enforce", tmp_path).health_fields()
    assert fields["auth_mode"] == "enforce"
    assert fields["identity_required_writes"] is True
    assert set(fields) >= {"auth_hash_file", "auth_unverified_calls"}


def test_should_bound_the_number_of_tracked_callers(auth_identity, tmp_path):
    gate = _gate(auth_identity, "log", tmp_path)
    for i in range(auth_identity.MAX_TRACKED_CALLERS + 20):
        gate.record_unverified(f"c{i}")
    counts = gate.health_fields()["auth_unverified_calls"]
    assert len(counts) == auth_identity.MAX_TRACKED_CALLERS + 1
    assert counts["other"] == 20


def test_should_never_log_a_token_a_hash_or_the_header(auth_identity, tmp_path, caplog):
    token = fake_token()
    write_hash_file(tmp_path, {token: "runner:codex"})
    (tmp_path / "junk").write_text("x")
    gate = _gate(auth_identity, "enforce", tmp_path)
    with caplog.at_level(logging.DEBUG):
        gate.authorize_write(f"Bearer {token}", "ok-caller")
        with pytest.raises(auth_identity.Unauthorized):
            gate.authorize_write("Bearer " + token + "-wrong", "bad-caller")
    text = caplog.text
    assert token not in text and sha256_hex(token) not in text and "Bearer" not in text
    assert "bad-caller" in text


def test_should_make_a_log_safe_caller_label(auth_identity):
    assert auth_identity.caller_label("curl/8.1\x00\x1b[31m", "1.2.3.4") == "curl/8.1[31m"
    assert auth_identity.caller_label(None, "1.2.3.4") == "1.2.3.4"
    assert auth_identity.caller_label("", None) == "unknown"
    assert len(auth_identity.caller_label("x" * 500, None)) == auth_identity.MAX_CALLER_LABEL_CHARS


# -- ids ---------------------------------------------------------------------


def test_should_require_workspace_id_on_every_write(auth_identity):
    for ws in (None, "", "   "):
        with pytest.raises(auth_identity.WriteIdentityError, match="workspace_id is required"):
            auth_identity.validate_write_ids(ws, "i", BOUND_WORKSPACE)
        with pytest.raises(auth_identity.WriteIdentityError, match="workspace_id is required"):
            auth_identity.validate_write_ids(ws, "i", BOUND_WORKSPACE, require_instance=False)


def test_should_require_instance_id_only_where_the_row_carries_one(auth_identity):
    for inst in (None, "", "  "):
        with pytest.raises(auth_identity.WriteIdentityError, match="instance_id is required"):
            auth_identity.validate_write_ids(BOUND_WORKSPACE, inst, BOUND_WORKSPACE)
        auth_identity.validate_write_ids(BOUND_WORKSPACE, inst, BOUND_WORKSPACE, require_instance=False)
    auth_identity.validate_write_ids(BOUND_WORKSPACE, "shared", BOUND_WORKSPACE)


def test_should_reject_a_workspace_that_is_not_the_bound_one(auth_identity):
    with pytest.raises(auth_identity.WriteIdentityError, match="does not match"):
        auth_identity.validate_write_ids(OTHER_WORKSPACE, "i", BOUND_WORKSPACE)


def test_should_fail_closed_without_a_workspace_binding(auth_identity):
    for bound in (None, ""):
        with pytest.raises(auth_identity.WriteIdentityError, match="no workspace binding"):
            auth_identity.validate_write_ids(BOUND_WORKSPACE, "i", bound)


def test_should_map_rejections_to_http_statuses(auth_identity):
    assert auth_identity.WriteIdentityError("x").status == 400
    assert auth_identity.PrincipalStorageUnavailable("x").status == 503
    assert issubclass(auth_identity.WriteIdentityError, auth_identity.WriteRejected)
    assert issubclass(auth_identity.PrincipalStorageUnavailable, auth_identity.WriteRejected)


# -- forwarding headers for the in-image proxies ----------------------------------


def test_should_forward_the_callers_bearer_token(auth_identity, tmp_path):
    token = fake_token()
    write_hash_file(tmp_path, {token: "runner:codex"})
    gate = _gate(auth_identity, "enforce", tmp_path)
    headers = auth_identity.build_rest_write_headers(gate, f"Bearer {token}", "c")
    assert headers == {"Authorization": f"Bearer {token}"}


def test_should_use_the_proxy_principal_only_in_log_mode_without_a_caller_token(auth_identity, tmp_path):
    write_hash_file(tmp_path, {})
    proxy = fake_token("proxy")
    log_gate = _gate(auth_identity, "log", tmp_path)
    headers = auth_identity.build_rest_write_headers(log_gate, None, "curl/8", fallback_token=proxy)
    assert headers["Authorization"] == f"Bearer {proxy}"
    assert headers[auth_identity.UNVERIFIED_CALLER_HEADER] == "curl/8"
    # a caller who sent a (bad) token is forwarded as-is, never replaced
    bad = auth_identity.build_rest_write_headers(log_gate, "Bearer nope", "curl/8", fallback_token=proxy)
    assert bad["Authorization"] == "Bearer nope"
    # no fallback token available (W03 helper not landed): nothing is invented
    none = auth_identity.build_rest_write_headers(log_gate, None, "curl/8")
    assert "Authorization" not in none and none[auth_identity.UNVERIFIED_CALLER_HEADER] == "curl/8"


def test_should_refuse_to_forward_for_an_unverified_caller_in_enforce_mode(auth_identity, tmp_path):
    write_hash_file(tmp_path, {})
    gate = _gate(auth_identity, "enforce", tmp_path)
    with pytest.raises(auth_identity.Unauthorized):
        auth_identity.build_rest_write_headers(gate, None, "c", fallback_token=fake_token())


def test_should_forward_nothing_special_in_off_mode(auth_identity, tmp_path):
    gate = _gate(auth_identity, "off", tmp_path)
    assert auth_identity.build_rest_write_headers(gate, None, "c", fallback_token=fake_token()) == {}


# -- the ASGI gate for the SSE and streamable surfaces ------------------------------


class _Recorder:
    def __init__(self):
        self.calls = 0

    async def __call__(self, scope, receive, send):
        self.calls += 1
        if scope["type"] != "http":
            return
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"seen:" + body})


def _asgi(auth_identity, gate, downstream):
    return auth_identity.WriteAuthMiddleware(
        downstream,
        lambda: gate,
        write_paths=frozenset({"/mcp", "/messages/"}),
        write_tools=frozenset({"log_progress", "update_context"}),
    )


async def _post(app, path, payload, headers=None):
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost:3005") as client:
        return await client.post(path, content=json.dumps(payload), headers=headers or {})


CALL_WRITE = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "log_progress", "arguments": {}}}
CALL_READ = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_context", "arguments": {}}}


@pytest.mark.parametrize("path", ["/mcp", "/messages/"])
async def test_should_answer_401_for_an_unverified_write_in_enforce_mode(auth_identity, tmp_path, path):
    pytest.importorskip("httpx")
    write_hash_file(tmp_path, {fake_token(): "runner:codex"})
    gate = _gate(auth_identity, "enforce", tmp_path)
    down = _Recorder()
    response = await _post(_asgi(auth_identity, gate, down), path, CALL_WRITE)
    assert response.status_code == 401 and down.calls == 0
    assert response.headers["www-authenticate"] == "Bearer"
    assert gate.health_fields()["auth_unverified_calls"]


@pytest.mark.parametrize("path", ["/mcp", "/messages/"])
async def test_should_pass_verified_writes_reads_and_other_paths(auth_identity, tmp_path, path):
    pytest.importorskip("httpx")
    token = fake_token()
    write_hash_file(tmp_path, {token: "runner:codex"})
    gate = _gate(auth_identity, "enforce", tmp_path)
    app = _asgi(auth_identity, gate, _Recorder())
    ok = await _post(app, path, CALL_WRITE, {"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200 and ok.content.startswith(b"seen:")
    read = await _post(app, path, CALL_READ)
    assert read.status_code == 200
    batch = await _post(app, path, [CALL_READ, CALL_WRITE])
    assert batch.status_code == 401
    other = await _post(app, "/elsewhere", CALL_WRITE)
    assert other.status_code == 200
    junk = await _post(app, path, {"not": "json-rpc"})
    assert junk.status_code == 200


@pytest.mark.parametrize("mode", ["off", "log"])
async def test_should_not_block_in_off_or_log_mode(auth_identity, tmp_path, mode):
    pytest.importorskip("httpx")
    gate = _gate(auth_identity, mode, tmp_path)
    response = await _post(_asgi(auth_identity, gate, _Recorder()), "/mcp", CALL_WRITE)
    assert response.status_code == 200


async def test_should_reject_oversized_bodies(auth_identity, tmp_path):
    pytest.importorskip("httpx")
    gate = _gate(auth_identity, "log", tmp_path)
    app = auth_identity.WriteAuthMiddleware(
        _Recorder(), lambda: gate, write_paths=frozenset({"/mcp"}), write_tools=frozenset({"log_progress"}),
        max_body_bytes=64,
    )
    response = await _post(app, "/mcp", {"pad": "x" * 200})
    assert response.status_code == 413
