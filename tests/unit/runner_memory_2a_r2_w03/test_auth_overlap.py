"""Overlapping ``dopemux auth --apply`` commands serialize on one lock.

PR 1498's review found the window: a command read the hash file, waited on the
keychain, then wrote back what it had read, so a revoke that finished in between
was undone and the revoked token verified again.

``run_overlapping`` holds the first command in that window, between its keychain
write and its hash write, and runs the second command there. The click callbacks
are called directly because ``CliRunner`` swaps ``sys.stdout`` process-wide and
cannot run in two threads at once.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import threading
from collections.abc import Callable

import click
import pytest

from dopemux.auth import hash_token, hashfile
from dopemux.commands import auth_commands
from dopemux.commands.auth_commands import issue, list_principals, revoke, rotate

# How long the first command stays in the window. Without the lock the second
# command finishes well inside this; with it the second command waits it out.
# A slow machine can only hide the bug, never fail a correct build.
WINDOW_SECONDS = 0.5
JOIN_SECONDS = 30.0


def run_overlapping(
    env, first: Callable[[], None], second: Callable[[], None]
) -> dict[str, click.ClickException]:
    """Run ``second`` inside ``first``'s window; return each one's refusal, if any."""
    real_store = auth_commands.store_token
    in_window = threading.Event()
    second_finished = threading.Event()
    refusals: dict[str, click.ClickException] = {}

    def store_then_hold(principal: str, token: str) -> None:
        real_store(principal, token)
        if threading.current_thread().name == "first":
            in_window.set()
            second_finished.wait(WINDOW_SECONDS)

    env.monkeypatch.setattr(auth_commands, "store_token", store_then_hold)

    def body(command: Callable[[], None]) -> None:
        name = threading.current_thread().name
        try:
            command()
        except click.ClickException as exc:
            refusals[name] = exc
        finally:
            if name == "second":
                second_finished.set()

    first_thread = threading.Thread(
        target=body, args=(first,), name="first", daemon=True
    )
    second_thread = threading.Thread(
        target=body, args=(second,), name="second", daemon=True
    )
    first_thread.start()
    assert in_window.wait(
        JOIN_SECONDS
    ), "the first command never reached its keychain write"
    second_thread.start()
    first_thread.join(JOIN_SECONDS)
    second_thread.join(JOIN_SECONDS)
    assert not first_thread.is_alive() and not second_thread.is_alive()
    return refusals


def hashes_on_disk(env) -> dict[str, str]:
    return json.loads(env.hash_file.read_text(encoding="utf-8"))


def meta_on_disk(env) -> dict:
    return json.loads(hashfile.meta_file_path().read_text(encoding="utf-8"))


def test_should_not_restore_a_revoked_hash_when_issue_overlaps_revoke(env):
    issue.callback("runner:a", True)
    revoked_hash = hash_token(env.keychain_token("runner:a"))

    refusals = run_overlapping(
        env,
        lambda: issue.callback("runner:b", True),
        lambda: revoke.callback("runner:a", True),
    )

    assert refusals == {}
    assert revoked_hash not in hashes_on_disk(env)
    assert hashes_on_disk(env) == {
        hash_token(env.keychain_token("runner:b")): "runner:b"
    }


def test_should_not_restore_a_revoked_principal_when_rotate_overlaps_revoke(env):
    issue.callback("runner:a", True)

    refusals = run_overlapping(
        env,
        lambda: rotate.callback("runner:a", True),
        lambda: revoke.callback("runner:a", True),
    )

    assert refusals == {}
    assert hashes_on_disk(env) == {}
    assert "runner:a" not in meta_on_disk(env)
    assert "dopemux-mcp|runner:a" not in env.keychain()


def test_should_refuse_the_second_issue_when_two_issues_overlap(env):
    refusals = run_overlapping(
        env,
        lambda: issue.callback("runner:a", True),
        lambda: issue.callback("runner:a", True),
    )

    assert set(refusals) == {"second"}
    assert "already has a token" in refusals["second"].message
    assert hashes_on_disk(env) == {
        hash_token(env.keychain_token("runner:a")): "runner:a"
    }


def test_should_keep_keychain_and_hash_in_step_when_two_rotates_overlap(env):
    issue.callback("runner:a", True)

    refusals = run_overlapping(
        env,
        lambda: rotate.callback("runner:a", True),
        lambda: rotate.callback("runner:a", True),
    )

    assert refusals == {}
    assert hashes_on_disk(env) == {
        hash_token(env.keychain_token("runner:a")): "runner:a"
    }


def test_should_refuse_a_rotate_whose_principal_was_revoked_while_it_waited(env):
    issue.callback("runner:a", True)
    token_before = env.keychain_token("runner:a")
    refusals: list[click.ClickException] = []

    def body() -> None:
        try:
            rotate.callback("runner:a", True)
        except click.ClickException as exc:
            refusals.append(exc)

    with hashfile.exclusive_lock():
        waiter = threading.Thread(target=body, daemon=True)
        waiter.start()
        waiter.join(0.2)
        env.hash_file.write_text("{}\n", encoding="utf-8")
    waiter.join(JOIN_SECONDS)

    assert not waiter.is_alive()
    assert [exc.message for exc in refusals] == [
        "runner:a has no token; use `dopemux auth issue runner:a`"
    ]
    assert hashes_on_disk(env) == {}
    assert env.keychain_token("runner:a") == token_before


def test_should_fail_closed_and_change_nothing_when_the_lock_stays_busy(env):
    issue.callback("runner:a", True)
    token_before = env.keychain_token("runner:a")
    hash_bytes_before = env.hash_file.read_bytes()
    env.monkeypatch.setattr(hashfile, "LOCK_TIMEOUT_SECONDS", 0.1)

    with hashfile.exclusive_lock():
        with pytest.raises(
            click.ClickException, match="another `dopemux auth` command"
        ):
            rotate.callback("runner:a", True)

    assert env.hash_file.read_bytes() == hash_bytes_before
    assert env.keychain_token("runner:a") == token_before


def test_should_print_a_dry_run_plan_while_the_lock_is_held(env, capsys):
    issue.callback("runner:a", True)
    env.monkeypatch.setattr(hashfile, "LOCK_TIMEOUT_SECONDS", 0.1)

    with hashfile.exclusive_lock():
        rotate.callback("runner:a", False)

    assert "DRY RUN: rotate runner:a" in capsys.readouterr().out


def test_should_list_principals_while_the_lock_is_held(env, capsys):
    issue.callback("runner:a", True)
    env.monkeypatch.setattr(hashfile, "LOCK_TIMEOUT_SECONDS", 0.1)

    with hashfile.exclusive_lock():
        list_principals.callback()

    assert "runner:a" in capsys.readouterr().out


def test_should_block_another_process_while_the_lock_is_held(env):
    code = (
        "from dopemux.auth import hashfile\n"
        "hashfile.LOCK_TIMEOUT_SECONDS = 0.2\n"
        "with hashfile.exclusive_lock():\n"
        "    pass\n"
    )

    with hashfile.exclusive_lock():
        held = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
    free = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    assert held.returncode != 0 and "HashFileError" in held.stderr
    assert free.returncode == 0, free.stderr


def test_should_lose_no_update_when_processes_contend_for_the_lock(env, tmp_path):
    """Pins the mutual exclusion itself, so a filelock upgrade has to keep it."""
    counter = tmp_path / "counter"
    counter.write_text("0", encoding="utf-8")
    code = (
        "import pathlib, sys\n"
        "from dopemux.auth import hashfile\n"
        "path = pathlib.Path(sys.argv[1])\n"
        "for _ in range(25):\n"
        "    with hashfile.exclusive_lock():\n"
        "        value = int(path.read_text())\n"
        "        path.write_text(str(value + 1))\n"
    )

    workers = [
        subprocess.Popen(
            [sys.executable, "-c", code, str(counter)], env=os.environ.copy()
        )
        for _ in range(4)
    ]

    assert [worker.wait(JOIN_SECONDS * 2) for worker in workers] == [0, 0, 0, 0]
    assert counter.read_text(encoding="utf-8") == "100"


def test_should_keep_the_lock_file_and_its_directory_private(env):
    with hashfile.exclusive_lock():
        lock_file = env.auth_dir / hashfile.LOCK_FILE_NAME
        assert stat.S_IMODE(lock_file.stat().st_mode) == 0o600
        assert stat.S_IMODE(env.auth_dir.stat().st_mode) == 0o700
