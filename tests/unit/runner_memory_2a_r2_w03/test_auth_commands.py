"""CLI tests for ``dopemux auth`` (issue, rotate, revoke, list)."""

from __future__ import annotations

import json
import logging
import re

from click.testing import CliRunner

from dopemux.auth import hash_token
from dopemux.commands.auth_commands import auth

HEX64 = re.compile(r"[0-9a-f]{64}")


def run(*args: str):
    return CliRunner().invoke(auth, list(args))


def assert_clean(env, result, *tokens: str) -> None:
    blob = (result.output or "") + env.home_files_text()
    for token in tokens:
        assert token not in blob
        for argv in env.argv_calls():
            assert all(token not in part for part in argv)


def test_should_register_auth_group_on_main_cli():
    from dopemux.cli import cli

    assert "auth" in cli.commands
    assert set(cli.commands["auth"].commands) == {"issue", "rotate", "revoke", "list"}


def test_should_print_dry_run_plan_and_change_nothing_by_default(env):
    result = run("issue", "runner:codex")
    assert result.exit_code == 0, result.output
    assert "dry run" in result.output.lower()
    assert "--apply" in result.output
    assert not env.auth_dir.exists()
    assert env.argv_calls() == []
    assert env.keychain() == {}


def test_should_note_unknown_principal_in_dry_run(env):
    result = run("issue", "runner:grok")
    assert result.exit_code == 0
    assert "not in the known 2A principal list" in result.output
    known = run("issue", "runner:codex")
    assert "not in the known" not in known.output


def test_should_reject_invalid_principal(env):
    result = run("issue", "codex", "--apply")
    assert result.exit_code != 0
    assert env.argv_calls() == []


def test_should_issue_token_store_hash_and_hide_token(env):
    result = run("issue", "runner:codex", "--apply")
    assert result.exit_code == 0, result.output
    token = env.keychain_token("runner:codex")
    assert json.loads(env.hash_file.read_text()) == {hash_token(token): "runner:codex"}
    assert_clean(env, result, token)
    assert hash_token(token) not in result.output


def test_should_not_log_token_when_issuing(env, caplog):
    caplog.set_level(logging.DEBUG)
    result = run("issue", "runner:codex", "--apply")
    token = env.keychain_token("runner:codex")
    assert token not in caplog.text and token not in result.output


def test_should_refuse_second_issue_for_same_principal(env):
    assert run("issue", "runner:codex", "--apply").exit_code == 0
    first = env.keychain_token("runner:codex")
    again = run("issue", "runner:codex", "--apply")
    assert again.exit_code != 0
    assert "rotate" in again.output
    assert env.keychain_token("runner:codex") == first


def test_should_keep_other_principals_when_issuing(env):
    run("issue", "runner:codex", "--apply")
    run("issue", "runner:claude", "--apply")
    hashes = json.loads(env.hash_file.read_text())
    assert sorted(hashes.values()) == ["runner:claude", "runner:codex"]


def test_should_not_clobber_unreadable_hash_file_on_issue(env):
    env.auth_dir.mkdir(parents=True)
    env.hash_file.write_text("{oops", encoding="utf-8")
    result = run("issue", "runner:codex", "--apply")
    assert result.exit_code != 0
    assert env.hash_file.read_text() == "{oops"
    assert env.keychain() == {}


def test_should_leave_no_hash_when_keychain_write_fails(env):
    env.set_mode("write_fail")
    result = run("issue", "runner:codex", "--apply")
    assert result.exit_code != 0
    assert not env.hash_file.exists()


def test_should_rotate_replacing_old_hash(env):
    run("issue", "runner:codex", "--apply")
    run("issue", "runner:claude", "--apply")
    old = env.keychain_token("runner:codex")
    result = run("rotate", "runner:codex", "--apply")
    assert result.exit_code == 0, result.output
    new = env.keychain_token("runner:codex")
    assert new != old
    hashes = json.loads(env.hash_file.read_text())
    assert hash_token(old) not in hashes
    assert hashes[hash_token(new)] == "runner:codex"
    assert sorted(hashes.values()) == ["runner:claude", "runner:codex"]
    assert_clean(env, result, old, new)


def test_should_rotate_dry_run_change_nothing(env):
    run("issue", "runner:codex", "--apply")
    before_token = env.keychain_token("runner:codex")
    before_file = env.hash_file.read_text()
    result = run("rotate", "runner:codex")
    assert result.exit_code == 0 and "dry run" in result.output.lower()
    assert env.keychain_token("runner:codex") == before_token
    assert env.hash_file.read_text() == before_file


def test_should_refuse_rotate_for_unissued_principal(env):
    result = run("rotate", "runner:codex", "--apply")
    assert result.exit_code != 0
    assert "issue" in result.output
    assert env.keychain() == {}


def test_should_revoke_hash_metadata_and_keychain_item(env):
    run("issue", "runner:codex", "--apply")
    run("issue", "runner:claude", "--apply")
    result = run("revoke", "runner:codex", "--apply")
    assert result.exit_code == 0, result.output
    assert list(json.loads(env.hash_file.read_text()).values()) == ["runner:claude"]
    assert "dopemux-mcp|runner:codex" not in env.keychain()
    assert "runner:codex" not in run("list").output


def test_should_revoke_dry_run_change_nothing(env):
    run("issue", "runner:codex", "--apply")
    result = run("revoke", "runner:codex")
    assert result.exit_code == 0 and "dry run" in result.output.lower()
    assert "dopemux-mcp|runner:codex" in env.keychain()
    assert len(json.loads(env.hash_file.read_text())) == 1


def test_should_revoke_hash_even_when_keychain_item_already_gone(env):
    run("issue", "runner:codex", "--apply")
    env.store.write_text("{}", encoding="utf-8")
    result = run("revoke", "runner:codex", "--apply")
    assert result.exit_code == 0, result.output
    assert json.loads(env.hash_file.read_text()) == {}
    assert "already" in result.output.lower()


def test_should_list_principals_and_creation_dates_only(env):
    run("issue", "runner:codex", "--apply")
    token = env.keychain_token("runner:codex")
    result = run("list")
    assert result.exit_code == 0
    assert "runner:codex" in result.output
    assert re.search(r"\d{4}-\d{2}-\d{2}", result.output)
    assert not HEX64.search(result.output)
    assert_clean(env, result, token)


def test_should_list_nothing_gracefully(env):
    result = run("list")
    assert result.exit_code == 0
    assert "no principals" in result.output.lower()


def test_should_keep_creation_date_across_rotation(env):
    run("issue", "runner:codex", "--apply")
    meta = env.auth_dir / "memory-token-meta.json"
    data = json.loads(meta.read_text())
    created = data["runner:codex"]["created"]
    run("rotate", "runner:codex", "--apply")
    data = json.loads(meta.read_text())
    assert data["runner:codex"]["created"] == created
    assert data["runner:codex"]["rotated"]
    assert not HEX64.search(meta.read_text()), "metadata sidecar must carry no hashes"
