"""Behavioural tests for the Claude Code hook dispatcher shell script.

These run the REAL ``.claude/hooks/run_native_hooks.sh`` under ``sh`` against
throwaway git fixtures. ``native_hooks.py`` is replaced by a stdlib-only stub
and the "venv" interpreters are fake wrapper scripts, so nothing here touches
the repository's real ``.venv``, the real HOME, a real Claude, or the network.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "run_native_hooks.sh"
HOOK_REL = Path("src") / "dopemux" / "claude" / "native_hooks.py"

STUB = '''\
import json
import os
import sys

if os.environ.get("STUB_CRASH"):
    raise ModuleNotFoundError("No module named 'pydantic'")

stdin = sys.stdin.read()
if os.environ.get("STUB_STDERR"):
    sys.stderr.write(os.environ["STUB_STDERR"])
if os.environ.get("STUB_STDOUT"):
    sys.stdout.write(os.environ["STUB_STDOUT"])
else:
    sys.stdout.write(
        json.dumps(
            {
                "venv": os.environ.get("FAKE_VENV"),
                "script": os.path.realpath(sys.argv[0]),
                "claude_project_dir": os.environ.get("CLAUDE_PROJECT_DIR"),
                "pythonpath": os.environ.get("PYTHONPATH"),
                "stdin": stdin,
            }
        )
    )
sys.exit(int(os.environ.get("STUB_RC", "0")))
'''


@dataclass
class Fixture:
    root: Path
    main: Path
    wt: Path
    outside: Path
    bin_dir: Path

    def env(self, **extra: str) -> Dict[str, str]:
        env = {
            "PATH": f"{self.bin_dir}:/usr/bin:/bin",
            "HOME": str(self.root / "home"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self.root.parent),
        }
        env.update(extra)
        return env


def _git_env(tmp: Path) -> Dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "HOME": str(tmp / "home"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid",
        }
    )
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def _git(cwd: Path, env: Dict[str, str], *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)


def _fake_venv(venv: Path, label: str) -> None:
    """Create ``<venv>/bin/python``: tag the env with ``label`` and exec the real python."""
    py = venv / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text(f'#!/bin/sh\nFAKE_VENV={label}\nexport FAKE_VENV\nexec "{sys.executable}" "$@"\n')
    py.chmod(0o755)
    (venv / "lib" / "python3.12" / "site-packages").mkdir(parents=True)


def _build(tmp_path: Path, main_venv: bool = True) -> Fixture:
    root = (tmp_path / "fx").resolve()
    main = root / "main"
    wt = root / "wt"
    outside = root / "outside"
    bin_dir = root / "bin"
    for d in (main, outside, bin_dir, root / "home"):
        d.mkdir(parents=True)
    env = _git_env(root)
    _git(main, env, "init", "-q")
    hook = main / HOOK_REL
    hook.parent.mkdir(parents=True)
    hook.write_text(STUB)
    _git(main, env, "add", "-A")
    _git(main, env, "commit", "-q", "-m", "stub")
    _git(main, env, "worktree", "add", "-q", str(wt))
    if main_venv:
        _fake_venv(main / ".venv", "main")
    return Fixture(root=root, main=main, wt=wt, outside=outside, bin_dir=bin_dir)


@pytest.fixture
def fx(tmp_path: Path) -> Fixture:
    return _build(tmp_path)


def payload(event: str, **extra: object) -> str:
    return json.dumps({"hook_event_name": event, "session_id": "s1", **extra})


def run(
    cwd: Path, env: Dict[str, str], stdin: str
) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        ["sh", str(SCRIPT)],
        input=stdin,
        cwd=cwd,
        env=env,
        timeout=30,
        capture_output=True,
        text=True,
    )


def report(proc: "subprocess.CompletedProcess[str]") -> dict:
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


# (a) linked worktree without its own .venv -> main checkout venv
def test_worktree_without_venv_uses_main_venv_and_worktree_hook(fx: Fixture) -> None:
    proc = run(
        fx.wt,
        fx.env(CLAUDE_PROJECT_DIR=str(fx.main)),
        payload("PostToolUse"),
    )
    got = report(proc)
    assert got["venv"] == "main"
    assert got["script"] == str((fx.wt / HOOK_REL).resolve())
    assert got["claude_project_dir"] == str(fx.wt)
    assert got["pythonpath"].split(os.pathsep)[0] == str(
        fx.main / ".venv" / "lib" / "python3.12" / "site-packages"
    )


# (b) worktree with its own .venv -> its own wins
def test_worktree_own_venv_wins(fx: Fixture) -> None:
    _fake_venv(fx.wt / ".venv", "wt")
    got = report(run(fx.wt, fx.env(), payload("PostToolUse")))
    assert got["venv"] == "wt"
    assert got["pythonpath"].split(os.pathsep)[0] == str(
        fx.wt / ".venv" / "lib" / "python3.12" / "site-packages"
    )


# (c) PreToolUse crash -> fail closed
def test_pretooluse_crash_fails_closed(fx: Fixture) -> None:
    proc = run(fx.main, fx.env(STUB_CRASH="1"), payload("PreToolUse"))
    assert proc.returncode == 2
    assert "DOPEMUX_HOOKS_FAIL_OPEN=1" in proc.stderr
    assert "fail-closed" in proc.stderr


# (d) non-PreToolUse events stay non-blocking on dispatcher failure
@pytest.mark.parametrize(
    "event", ["PostToolUse", "Stop", "SubagentStop", "UserPromptSubmit", "SessionStart"]
)
def test_other_events_crash_stays_nonblocking(fx: Fixture, event: str) -> None:
    proc = run(fx.main, fx.env(STUB_CRASH="1"), payload(event))
    assert proc.returncode == 1
    assert "fail-closed" not in proc.stderr


# (e) operator override
def test_pretooluse_crash_with_override_stays_nonblocking(fx: Fixture) -> None:
    proc = run(
        fx.main,
        fx.env(STUB_CRASH="1", DOPEMUX_HOOKS_FAIL_OPEN="1"),
        payload("PreToolUse"),
    )
    assert proc.returncode == 1


# (f) no interpreter at all
def _no_python_env(fx: Fixture) -> Dict[str, str]:
    tools = fx.root / "tools"
    tools.mkdir()
    for name in ("git", "dirname", "cat", "sh"):
        found = shutil.which(name)
        assert found, name
        (tools / name).symlink_to(found)
    env = fx.env()
    env["PATH"] = f"{fx.bin_dir}:{tools}"
    return env


@pytest.mark.parametrize("separators", [None, (",", ":")])
def test_no_interpreter_pretooluse_fails_closed(tmp_path: Path, separators) -> None:
    fx = _build(tmp_path, main_venv=False)
    body = json.dumps({"hook_event_name": "PreToolUse"}, separators=separators)
    proc = run(fx.main, _no_python_env(fx), body)
    assert proc.returncode == 2
    assert "DOPEMUX_HOOKS_FAIL_OPEN=1" in proc.stderr


def test_no_interpreter_other_event_nonblocking(tmp_path: Path) -> None:
    fx = _build(tmp_path, main_venv=False)
    proc = run(fx.main, _no_python_env(fx), payload("Stop"))
    assert proc.returncode not in (0, 2)


def test_no_interpreter_pretooluse_with_override_nonblocking(tmp_path: Path) -> None:
    fx = _build(tmp_path, main_venv=False)
    env = _no_python_env(fx)
    env["DOPEMUX_HOOKS_FAIL_OPEN"] = "1"
    proc = run(fx.main, env, payload("PreToolUse"))
    assert proc.returncode not in (0, 2)


# (g) passthrough of the native hook's own results
def test_exit_zero_passthrough_stdout_identical(fx: Fixture) -> None:
    out = '{"decision": "allow",  "n": 1}\n'
    proc = run(fx.main, fx.env(STUB_STDOUT=out), payload("PreToolUse"))
    assert proc.returncode == 0
    assert proc.stdout == out


def test_exit_two_passthrough(fx: Fixture) -> None:
    proc = run(
        fx.main,
        fx.env(STUB_RC="2", STUB_STDERR="denied by stub\n"),
        payload("PreToolUse"),
    )
    assert proc.returncode == 2
    assert "denied by stub" in proc.stderr
    assert "fail-closed" not in proc.stderr


# (h) cwd outside any project; incoming CLAUDE_PROJECT_DIR points at the checkout
def test_cwd_outside_project_uses_incoming_project_dir(fx: Fixture) -> None:
    got = report(
        run(fx.outside, fx.env(CLAUDE_PROJECT_DIR=str(fx.main)), payload("PostToolUse"))
    )
    assert got["script"] == str((fx.main / HOOK_REL).resolve())
    assert got["claude_project_dir"] == str(fx.main)
    assert got["venv"] == "main"


# (i) payload delivered unchanged
def test_payload_delivered_unchanged(fx: Fixture) -> None:
    body = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "echo '$HOME' \"q\" \\ ☃ -n %s"},
    }
    got = report(run(fx.main, fx.env(), json.dumps(body)))
    assert json.loads(got["stdin"]) == body
