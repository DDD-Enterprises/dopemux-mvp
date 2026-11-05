"""Dispatcher (`.claude/hooks/run_native_hooks.sh`) and `native_hooks.main()` payload handling.

The dispatcher tests drive the real shell script through real subprocesses against
real git repos and linked worktrees built under ``tmp_path``.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

import pytest

from dopemux.claude import native_hooks

REPO_ROOT = Path(__file__).resolve().parents[2]
DISPATCHER_SRC = REPO_ROOT / ".claude" / "hooks" / "run_native_hooks.sh"
HOOK_REL = Path("src") / "dopemux" / "claude" / "native_hooks.py"

# A stub hook: reports which file ran, the inherited project dir, and exits 2.
STUB_HOOK = (
    "#!/bin/sh\n"
    'echo "ran:$0"\n'
    'echo "project_dir:${CLAUDE_PROJECT_DIR:-}"\n'
    "exit 2\n"
)
# A fake interpreter that runs the hook file it is handed as a shell script.
FAKE_PYTHON = '#!/bin/sh\nexec sh "$@"\n'
# A fake `dopemux` that logs argv and stdin, then exits with FAKE_DOPEMUX_EXIT.
FAKE_DOPEMUX = (
    "#!/bin/sh\n"
    'echo "argv:$*" >> "$FAKE_LOG"\n'
    'echo "stdin:$(cat)" >> "$FAKE_LOG"\n'
    'exit "${FAKE_DOPEMUX_EXIT:-0}"\n'
)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _write_exe(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


class Env:
    def __init__(self, tmp_path: Path, *, with_hook_file: bool) -> None:
        self.main = tmp_path / "main"
        self.main.mkdir()
        _git(self.main, "init", "-q", "-b", "main")
        if with_hook_file:
            _write_exe(self.main / HOOK_REL, STUB_HOOK)
        else:
            (self.main / "README.md").write_text("x\n", encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-q", "-m", "init")
        self.worktree = tmp_path / "wt"
        _git(self.main, "worktree", "add", "-q", "-b", "wt-branch", str(self.worktree))
        self.worktree = self.worktree.resolve()
        self.main = self.main.resolve()

        self.dispatcher = self.main / ".claude" / "hooks" / "run_native_hooks.sh"
        self.dispatcher.parent.mkdir(parents=True)
        shutil.copy2(DISPATCHER_SRC, self.dispatcher)

        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        self.log = tmp_path / "fake.log"
        self.home = tmp_path / "home"
        self.home.mkdir()

    def env(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        # PATH: fake bin first, then only the dirs holding the tools the script
        # itself needs (git, dirname), so a host-installed `dopemux` cannot leak in.
        system = {str(Path(shutil.which(tool)).parent) for tool in ("git", "dirname", "sh")}
        env = {
            "PATH": os.pathsep.join([str(self.bin), *sorted(system)]),
            "HOME": str(self.home),
            "FAKE_LOG": str(self.log),
        }
        env.update(extra or {})
        return env

    def run(
        self,
        payload: str = '{"hook_event_name":"SessionStart"}',
        *,
        cwd: Optional[Path] = None,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sh", str(self.dispatcher)],
            cwd=cwd or self.worktree,
            input=payload,
            env=self.env(extra_env),
            capture_output=True,
            text=True,
            timeout=30,
        )


@pytest.fixture
def env_with_hook(tmp_path: Path) -> Env:
    return Env(tmp_path, with_hook_file=True)


@pytest.fixture
def env_without_hook(tmp_path: Path) -> Env:
    return Env(tmp_path, with_hook_file=False)


def test_dispatcher_prefers_checkout_hook_file_with_main_venv(env_with_hook: Env) -> None:
    env = env_with_hook
    assert not (env.worktree / ".venv").exists()
    _write_exe(env.main / ".venv" / "bin" / "python", FAKE_PYTHON)

    result = env.run()

    assert result.returncode == 2, result.stderr
    assert f"ran:{env.worktree / HOOK_REL}" in result.stdout
    assert f"ran:{env.main / HOOK_REL}" not in result.stdout


def test_dispatcher_prefers_checkout_venv_over_main_venv(env_with_hook: Env) -> None:
    env = env_with_hook
    _write_exe(env.main / ".venv" / "bin" / "python", '#!/bin/sh\necho "main-venv"\nexit 7\n')
    _write_exe(env.worktree / ".venv" / "bin" / "python", FAKE_PYTHON)

    result = env.run()

    assert result.returncode == 2, result.stderr
    assert "main-venv" not in result.stdout


def test_dispatcher_resolves_main_venv_from_a_subdirectory(env_with_hook: Env) -> None:
    env = env_with_hook
    _write_exe(env.main / ".venv" / "bin" / "python", FAKE_PYTHON)
    subdir = env.worktree / "src" / "dopemux"

    result = env.run(cwd=subdir)

    assert result.returncode == 2, result.stderr
    assert f"ran:{env.worktree / HOOK_REL}" in result.stdout


def test_dispatcher_uses_installed_dopemux_when_no_hook_file(env_without_hook: Env) -> None:
    env = env_without_hook
    _write_exe(env.bin / "dopemux", FAKE_DOPEMUX)
    payload = '{"hook_event_name":"SessionStart","cwd":"/somewhere"}'

    result = env.run(payload)

    assert result.returncode == 0, result.stderr
    log = env.log.read_text(encoding="utf-8")
    assert "argv:native-hooks run" in log
    assert f"stdin:{payload}" in log


def test_dispatcher_passes_exit_code_through(env_without_hook: Env) -> None:
    env = env_without_hook
    _write_exe(env.bin / "dopemux", FAKE_DOPEMUX)

    result = env.run(extra_env={"FAKE_DOPEMUX_EXIT": "2"})

    assert result.returncode == 2, result.stderr


def test_dispatcher_fails_open_when_nothing_found(env_without_hook: Env) -> None:
    result = env_without_hook.run()

    assert result.returncode == 0
    assert result.stdout == ""
    assert "no interpreter" in result.stderr


def test_dispatcher_keeps_inherited_claude_project_dir(env_with_hook: Env) -> None:
    env = env_with_hook
    _write_exe(env.main / ".venv" / "bin" / "python", FAKE_PYTHON)

    result = env.run(extra_env={"CLAUDE_PROJECT_DIR": "/elsewhere"})

    assert result.returncode == 2, result.stderr
    assert "project_dir:/elsewhere" in result.stdout


def test_dispatcher_defaults_claude_project_dir_to_checkout_top(env_with_hook: Env) -> None:
    env = env_with_hook
    _write_exe(env.main / ".venv" / "bin" / "python", FAKE_PYTHON)

    result = env.run()

    assert f"project_dir:{env.worktree}" in result.stdout


class _Recorder:
    calls: list = []

    def __init__(self, project_root: Optional[Path] = None) -> None:
        type(self).calls.append(project_root)

    def handle_event(self, payload):  # noqa: ANN001
        return 0, {}


def _run_main(monkeypatch: pytest.MonkeyPatch, stdin_text: str) -> None:
    _Recorder.calls = []
    monkeypatch.setattr(native_hooks, "NativeHookAdapter", _Recorder)
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    with pytest.raises(SystemExit) as exc:
        native_hooks.main()
    assert exc.value.code == 0


def test_main_passes_payload_cwd_to_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _run_main(monkeypatch, json.dumps({"hook_event_name": "SessionStart", "cwd": str(tmp_path)}))

    assert _Recorder.calls == [tmp_path]


def test_main_without_cwd_uses_process_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_main(monkeypatch, json.dumps({"hook_event_name": "SessionStart"}))

    assert _Recorder.calls == [None]


def test_main_non_json_stdin_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _run_main(monkeypatch, "this is not json\x00\xff")

    assert _Recorder.calls == []
    assert '"decision"' not in capsys.readouterr().out


def test_native_hooks_run_reads_stdin_and_exits_with_adapter_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from click.testing import CliRunner

    from dopemux.cli import cli

    seen: list = []

    class _Blocker:
        def __init__(self, project_root: Optional[Path] = None) -> None:
            seen.append(project_root)

        def handle_event(self, payload):  # noqa: ANN001
            seen.append(payload["hook_event_name"])
            return 2, {"decision": "block"}

    monkeypatch.setattr(native_hooks, "NativeHookAdapter", _Blocker)
    payload = {"hook_event_name": "PreToolUse", "cwd": str(tmp_path)}

    result = CliRunner().invoke(cli, ["native-hooks", "run"], input=json.dumps(payload))

    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout) == {"decision": "block"}
    assert seen == [tmp_path, "PreToolUse"]
