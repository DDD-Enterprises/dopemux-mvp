"""Helper-module tests (keychain + hash file) for ``dopemux.auth``."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import stat

import pytest

from dopemux.auth import (
    InvalidPrincipalError,
    KeychainError,
    TokenNotFoundError,
    generate_token,
    get_token,
    hash_token,
    is_known_principal,
    validate_principal,
)
from dopemux.auth import hashfile, keychain


def test_should_accept_only_runner_and_internal_principals():
    for good in ("runner:codex", "internal:bridge-proxy", "runner:a", "internal:x_1.y-2"):
        assert validate_principal(good) == good
    for bad in ("", "codex", "Runner:codex", "runner:", "runner:-x", "other:x", "runner:a b", "runner:" + "a" * 65):
        with pytest.raises(InvalidPrincipalError):
            validate_principal(bad)


def test_should_flag_principals_outside_the_known_2a_list():
    assert is_known_principal("runner:claude")
    assert is_known_principal("internal:brain")
    assert not is_known_principal("runner:grok")


def test_should_generate_32_random_bytes_as_base64url():
    a, b = generate_token(), generate_token()
    assert a != b
    assert not any(generate_token().startswith("-") for _ in range(300))
    assert re.fullmatch(r"[A-Za-z0-9_-]+", a)
    assert len(base64.urlsafe_b64decode(a + "=" * (-len(a) % 4))) == 32


def test_should_hash_token_as_lowercase_hex_sha256_of_utf8():
    assert hash_token("abc") == hashlib.sha256(b"abc").hexdigest()


def test_should_store_token_without_putting_it_in_argv_and_read_it_back(env):
    token = generate_token()
    keychain.store_token("runner:codex", token)
    assert env.keychain_token("runner:codex") == token
    for argv in env.argv_calls():
        assert all(token not in part for part in argv)
    assert env.argv_calls()[0] == ["-i"]
    assert get_token("runner:codex") == token
    # one read-back inside store_token, one explicit get_token: both with stdin closed
    assert env.stdin_lens() == [0, 0], "reads must run with stdin closed"
    read_argv = env.argv_calls()[-1]
    assert read_argv[:1] == ["find-generic-password"]
    assert "dopemux-mcp" in read_argv and "runner:codex" in read_argv and "-w" in read_argv


def test_should_raise_typed_error_when_item_absent(env):
    with pytest.raises(TokenNotFoundError) as exc:
        get_token("runner:codex")
    assert "runner:codex" in str(exc.value)
    assert "dopemux auth issue" in str(exc.value)


def test_should_fail_hard_and_name_cause_when_keychain_locked(env):
    env.set_mode("locked")
    with pytest.raises(KeychainError) as exc:
        get_token("runner:codex")
    msg = str(exc.value).lower()
    assert "locked" in msg and "login session" in msg
    assert len(env.argv_calls()) == 1, "never retry into a prompt"


def test_should_fail_hard_on_empty_output(env):
    env.set_mode("empty")
    with pytest.raises(KeychainError):
        get_token("runner:codex")


def test_should_fail_hard_on_timeout(env):
    env.set_mode("hang")
    env.monkeypatch.setattr(keychain, "TIMEOUT_SECONDS", 0.5)
    with pytest.raises(KeychainError) as exc:
        get_token("runner:codex")
    assert "timed out" in str(exc.value)


def test_should_fail_when_security_binary_missing(env):
    env.monkeypatch.setattr(keychain, "SECURITY_BIN", "/nonexistent/security")
    with pytest.raises(KeychainError):
        get_token("runner:codex")


def test_should_fail_when_write_fails_and_not_leak_token(env):
    env.set_mode("write_fail")
    token = generate_token()
    with pytest.raises(KeychainError) as exc:
        keychain.store_token("runner:codex", token)
    assert token not in str(exc.value)


def test_should_fail_when_readback_differs_after_write(env):
    # security -i may exit 0 even if the add failed; the helper verifies.
    env.set_mode("empty")
    with pytest.raises(KeychainError):
        keychain.store_token("runner:codex", generate_token())


def test_should_refuse_invalid_principal_before_calling_security(env):
    with pytest.raises(InvalidPrincipalError):
        get_token("nope")
    assert env.argv_calls() == []


def test_should_not_log_token_or_hash(env, caplog):
    caplog.set_level(logging.DEBUG)
    token = generate_token()
    keychain.store_token("runner:codex", token)
    get_token("runner:codex")
    assert token not in caplog.text
    assert hash_token(token) not in caplog.text


def test_should_write_hash_file_atomically_with_private_modes(env):
    h = hash_token("t1")
    hashfile.write_hashes({h: "runner:codex"})
    path = hashfile.hash_file_path()
    assert path == env.hash_file
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert json.loads(path.read_text()) == {h: "runner:codex"}
    assert sorted(p.name for p in path.parent.iterdir()) == ["memory-token-hashes.json"]


def test_should_tighten_existing_directory_mode(env):
    env.auth_dir.mkdir(parents=True, mode=0o755)
    os.chmod(env.auth_dir, 0o755)
    hashfile.write_hashes({})
    assert stat.S_IMODE(env.auth_dir.stat().st_mode) == 0o700


def test_should_leave_no_temp_file_when_write_fails(env, monkeypatch):
    hashfile.write_hashes({hash_token("a"): "runner:codex"})
    before = env.hash_file.read_text()

    def boom(*_a, **_k):
        raise OSError("disk full")

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "replace", boom)
        with pytest.raises(OSError):
            hashfile.write_hashes({hash_token("b"): "runner:claude"})
    assert env.hash_file.read_text() == before
    assert [p.name for p in env.auth_dir.iterdir()] == ["memory-token-hashes.json"]


def test_should_refuse_to_overwrite_unreadable_hash_file(env):
    env.auth_dir.mkdir(parents=True)
    env.hash_file.write_text("{not json", encoding="utf-8")
    with pytest.raises(hashfile.HashFileError):
        hashfile.load_hashes()
    assert env.hash_file.read_text() == "{not json"


def test_should_load_missing_hash_file_as_empty(env):
    assert hashfile.load_hashes() == {}


@pytest.mark.parametrize("bad", ["runner:codex\n", "internal:cli\n", "runner:codex\r\n", "runner:codex\n\n"])
def test_should_reject_a_principal_with_a_trailing_line_ending(bad):
    with pytest.raises(InvalidPrincipalError):
        validate_principal(bad)


def test_should_refuse_to_write_a_token_with_a_trailing_newline(env):
    with pytest.raises(ValueError):
        keychain.store_token("runner:codex", "a" * 43 + "\n")
    assert env.argv_calls() == []


def test_should_refuse_a_hash_file_principal_with_a_trailing_newline(env):
    env.auth_dir.mkdir(parents=True)
    env.hash_file.write_text('{"' + "a" * 64 + '": "runner:codex\\n"}', encoding="utf-8")
    with pytest.raises(hashfile.HashFileError):
        hashfile.load_hashes()
