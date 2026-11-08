"""auth_identity: modes, bearer verification, principal, counters, id checks."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

import pytest

from .helpers import (
    HASH_FILE_NAME,
    fake_token,
    load_dope_memory_auth_identity,
    write_hash_file,
)

auth_identity = load_dope_memory_auth_identity()


def _gate(mode, tmp_path, tokens=None):
    auth_dir = tmp_path / "auth"
    if tokens is not None:
        write_hash_file(auth_dir, tokens)
    return auth_identity.AuthGate(mode=mode, auth_dir=auth_dir)


# --- mode ------------------------------------------------------------------


def test_should_default_to_log_mode_when_env_unset():
    assert auth_identity.load_auth_mode({}) == "log"


@pytest.mark.parametrize("raw,expected", [("off", "off"), ("LOG", "log"), (" Enforce ", "enforce")])
def test_should_parse_mode_case_insensitively(raw, expected):
    assert auth_identity.load_auth_mode({"DOPE_MEMORY_AUTH_MODE": raw}) == expected


def test_should_reject_unknown_mode_instead_of_failing_open():
    with pytest.raises(ValueError, match="DOPE_MEMORY_AUTH_MODE"):
        auth_identity.load_auth_mode({"DOPE_MEMORY_AUTH_MODE": "permissive"})


def test_should_reject_unknown_mode_on_gate_construction(tmp_path):
    with pytest.raises(ValueError):
        auth_identity.AuthGate(mode="nope", auth_dir=tmp_path)


# --- bearer verification ---------------------------------------------------


def test_should_return_principal_for_valid_bearer_token(tmp_path):
    token = fake_token()
    gate = _gate("log", tmp_path, {token: "runner:codex"})
    identity = gate.authenticate(f"Bearer {token}")
    assert identity.verified is True
    assert identity.principal == "runner:codex"


def test_should_accept_lowercase_bearer_scheme(tmp_path):
    token = fake_token()
    gate = _gate("log", tmp_path, {token: "runner:claude"})
    assert gate.authenticate(f"bearer {token}").principal == "runner:claude"


@pytest.mark.parametrize(
    "header",
    [None, "", "Bearer", "Bearer ", "Basic abc", "Token abc", "Bearer " + "x" * 5000],
)
def test_should_treat_missing_or_malformed_header_as_unverified(tmp_path, header):
    gate = _gate("log", tmp_path, {fake_token(): "runner:codex"})
    identity = gate.authenticate(header)
    assert identity.verified is False
    assert identity.principal == "unverified"


def test_should_treat_wrong_token_as_unverified(tmp_path):
    gate = _gate("log", tmp_path, {fake_token(): "runner:codex"})
    identity = gate.authenticate(f"Bearer {fake_token('other')}")
    assert identity.verified is False
    assert identity.principal == "unverified"


def test_should_compare_hashes_with_hmac_compare_digest(tmp_path, monkeypatch):
    token = fake_token()
    gate = _gate("log", tmp_path, {token: "runner:codex"})
    calls = []
    real = hmac.compare_digest

    def spy(a, b):
        calls.append((a, b))
        return real(a, b)

    monkeypatch.setattr(hmac, "compare_digest", spy)
    assert gate.authenticate(f"Bearer {token}").verified is True
    assert calls, "hmac.compare_digest was never used"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert any(digest in pair for pair in calls)
    # The raw token is never one of the compared values.
    assert all(token not in pair for pair in calls)


def test_should_never_store_plaintext_tokens_in_hash_file(tmp_path):
    token = fake_token()
    write_hash_file(tmp_path / "auth", {token: "runner:codex"})
    text = (tmp_path / "auth" / HASH_FILE_NAME).read_text()
    assert token not in text


# --- hash file handling ----------------------------------------------------


def test_should_report_missing_hash_file_and_fail_closed(tmp_path):
    gate = auth_identity.AuthGate(mode="enforce", auth_dir=tmp_path / "absent")
    assert gate.authenticate(f"Bearer {fake_token()}").verified is False
    assert gate.health_fields()["auth_hash_file"] == "missing"


def test_should_report_unconfigured_when_no_directory_given():
    gate = auth_identity.AuthGate(mode="log", auth_dir=None)
    assert gate.authenticate("Bearer abc").verified is False
    assert gate.health_fields()["auth_hash_file"] == "unconfigured"


def test_should_fail_closed_on_malformed_hash_file(tmp_path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    (auth_dir / HASH_FILE_NAME).write_text("{not json", encoding="utf-8")
    gate = auth_identity.AuthGate(mode="enforce", auth_dir=auth_dir)
    assert gate.authenticate(f"Bearer {fake_token()}").verified is False
    assert gate.health_fields()["auth_hash_file"] == "invalid"


def test_should_skip_entries_with_bad_hash_or_principal(tmp_path):
    token = fake_token()
    good = hashlib.sha256(token.encode()).hexdigest()
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    (auth_dir / HASH_FILE_NAME).write_text(
        json.dumps(
            {
                good: "runner:codex",
                "not-a-hash": "runner:evil",
                hashlib.sha256(b"x").hexdigest(): "root",
                hashlib.sha256(b"y").hexdigest(): 7,
            }
        ),
        encoding="utf-8",
    )
    gate = auth_identity.AuthGate(mode="log", auth_dir=auth_dir)
    assert gate.authenticate(f"Bearer {token}").principal == "runner:codex"
    assert gate.authenticate("Bearer x").verified is False
    assert gate.authenticate("Bearer y").verified is False


def test_should_pick_up_rotated_hash_file_without_restart(tmp_path):
    old, new = fake_token("old"), fake_token("new")
    gate = _gate("log", tmp_path, {old: "runner:codex"})
    assert gate.authenticate(f"Bearer {old}").verified is True
    write_hash_file(tmp_path / "auth", {new: "runner:codex", fake_token("pad"): "internal:cli"})
    assert gate.authenticate(f"Bearer {old}").verified is False
    assert gate.authenticate(f"Bearer {new}").verified is True


def test_should_read_hash_file_from_env_directory(tmp_path):
    token = fake_token()
    write_hash_file(tmp_path / "auth", {token: "runner:codex"})
    gate = auth_identity.AuthGate.from_env(
        {"DOPE_MEMORY_AUTH_MODE": "enforce", "DOPE_MEMORY_AUTH_DIR": str(tmp_path / "auth")}
    )
    assert gate.mode == "enforce"
    assert gate.authenticate(f"Bearer {token}").principal == "runner:codex"


# --- authorize_write -------------------------------------------------------


@pytest.mark.parametrize("mode", ["off", "log", "enforce"])
@pytest.mark.parametrize("kind", ["valid", "invalid", "missing"])
def test_should_apply_each_mode_to_valid_invalid_and_missing_tokens(tmp_path, mode, kind):
    token = fake_token()
    gate = _gate(mode, tmp_path, {token: "runner:codex"})
    header = {
        "valid": f"Bearer {token}",
        "invalid": f"Bearer {fake_token('bad')}",
        "missing": None,
    }[kind]

    if mode == "enforce" and kind != "valid":
        with pytest.raises(auth_identity.Unauthorized):
            gate.authorize_write(header, "curl/8")
        return

    identity = gate.authorize_write(header, "curl/8")
    if mode == "off":
        assert identity.principal == "unverified"  # off never verifies
    elif kind == "valid":
        assert identity.principal == "runner:codex" and identity.verified
    else:
        assert identity.principal == "unverified" and not identity.verified


def test_should_count_unverified_calls_per_caller_in_log_and_enforce(tmp_path):
    log_gate = _gate("log", tmp_path, {fake_token(): "runner:codex"})
    log_gate.authorize_write(None, "curl/8")
    log_gate.authorize_write("Bearer nope", "curl/8")
    log_gate.authorize_write(None, "python-httpx")
    assert log_gate.health_fields()["auth_unverified_calls"] == {"curl/8": 2, "python-httpx": 1}

    enf_gate = _gate("enforce", tmp_path / "e", {fake_token(): "runner:codex"})
    with pytest.raises(auth_identity.Unauthorized):
        enf_gate.authorize_write(None, "curl/8")
    assert enf_gate.health_fields()["auth_unverified_calls"] == {"curl/8": 1}


def test_should_not_count_verified_or_off_mode_calls(tmp_path):
    token = fake_token()
    gate = _gate("log", tmp_path, {token: "runner:codex"})
    gate.authorize_write(f"Bearer {token}", "curl/8")
    assert gate.health_fields()["auth_unverified_calls"] == {}
    off = _gate("off", tmp_path / "o", {token: "runner:codex"})
    off.authorize_write(None, "curl/8")
    assert off.health_fields()["auth_unverified_calls"] == {}


def test_should_bound_the_number_of_tracked_callers(tmp_path):
    gate = _gate("log", tmp_path)
    for i in range(auth_identity.MAX_TRACKED_CALLERS + 20):
        gate.record_unverified(f"caller-{i}")
    counts = gate.health_fields()["auth_unverified_calls"]
    assert len(counts) <= auth_identity.MAX_TRACKED_CALLERS + 1
    assert counts["other"] == 20


def test_should_not_log_the_authorization_header_or_token(tmp_path, caplog):
    token = fake_token("leak")
    gate = _gate("enforce", tmp_path, {fake_token(): "runner:codex"})
    with caplog.at_level(logging.DEBUG):
        gate.authenticate(f"Bearer {token}")
        with pytest.raises(auth_identity.Unauthorized) as excinfo:
            gate.authorize_write(f"Bearer {token}", "curl/8")
    assert token not in caplog.text
    assert "Bearer" not in caplog.text
    assert token not in str(excinfo.value)


def test_should_describe_health_fields(tmp_path):
    fields = _gate("enforce", tmp_path, {fake_token(): "runner:codex"}).health_fields()
    assert fields["auth_mode"] == "enforce"
    assert fields["identity_required_writes"] is True
    assert fields["auth_hash_file"] == "ok"
    assert fields["auth_unverified_calls"] == {}


def test_should_sanitize_caller_labels():
    label = auth_identity.caller_label("evil\r\nagent/1.0\x00" + "A" * 200, "10.0.0.1")
    assert "\n" not in label and "\r" not in label and "\x00" not in label
    assert len(label) <= 64
    assert auth_identity.caller_label(None, "10.0.0.1") == "10.0.0.1"
    assert auth_identity.caller_label(None, None) == "unknown"


# --- write ids -------------------------------------------------------------


def test_should_accept_matching_ids():
    auth_identity.validate_write_ids("ws-a", "inst-1", "ws-a")


@pytest.mark.parametrize("ws,inst,expected", [(None, "i", ("w", "i")), ("w", None, ("w", "A")),
                                               ("", "i", ("w", "i")), ("w", "  ", ("w", "A")),
                                               (None, None, ("w", "A"))])
def test_should_fill_missing_or_blank_ids_from_the_binding(ws, inst, expected):
    # Amendment 04 (W12): omitted ids default to the binding / the server's instance.
    assert auth_identity.validate_write_ids(ws, inst, "w") == expected


def test_should_reject_workspace_that_differs_from_binding():
    with pytest.raises(auth_identity.WriteIdentityError, match="bound"):
        auth_identity.validate_write_ids("other", "i", "ws-a")


def test_should_reject_every_write_when_server_has_no_binding():
    with pytest.raises(auth_identity.WriteIdentityError, match="DOPE_MEMORY_WORKSPACE_ID"):
        auth_identity.validate_write_ids("ws-a", "i", None)


def test_should_list_exactly_the_mutating_tools():
    assert auth_identity.WRITE_TOOLS == frozenset(
        {
            "memory_store",
            "memory_correct",
            "memory_link_resolution",
            "memory_generate_reflection",
            "memory_mark_issue",
        }
    )


def test_should_not_verify_a_principal_with_a_trailing_newline(tmp_path):
    token = fake_token()
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    digest = hashlib.sha256(token.encode()).hexdigest()
    (auth_dir / HASH_FILE_NAME).write_text(
        json.dumps({digest: "runner:codex\n"}), encoding="utf-8"
    )
    gate = auth_identity.AuthGate(mode="log", auth_dir=auth_dir)
    assert gate.authenticate(f"Bearer {token}").verified is False


def test_should_skip_a_digest_with_a_trailing_newline(tmp_path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    digest = hashlib.sha256(b"x").hexdigest()
    (auth_dir / HASH_FILE_NAME).write_text(
        json.dumps({digest + "\n": "runner:codex"}), encoding="utf-8"
    )
    gate = auth_identity.AuthGate(mode="log", auth_dir=auth_dir)
    assert gate._read_hash_file() == ({}, "ok")
