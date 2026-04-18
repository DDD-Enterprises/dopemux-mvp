from __future__ import annotations

import contextlib
import subprocess
from pathlib import Path

from dopemux_pr_merge_specialist import queue_drain
from dopemux_pr_merge_specialist.schema import ReviewThread, ThreadComment


def _thread(
    *,
    body: str = "Please fix this.",
    comment_path: str = "",
    comment_line: int | None = None,
    thread_path: str = "src/example.py",
    thread_line: int | None = 11,
) -> ReviewThread:
    return ReviewThread(
        id="T-1",
        is_resolved=False,
        is_outdated=False,
        viewer_can_resolve=True,
        path=thread_path,
        line=thread_line,
        comments=[
            ThreadComment(
                id="C-1",
                author="human-dev",
                body=body,
                created_at="2026-03-12T00:00:00Z",
                path=comment_path,
                line=comment_line,
            )
        ],
    )


@contextlib.contextmanager
def _fake_env():
    yield {"HOME": "/tmp/fake-home"}


def test_remediate_review_thread_uses_thread_path_fallback(monkeypatch, tmp_path: Path):
    captured_prompt = {}
    logs: list[str] = []

    def fake_command(prompt: str):
        captured_prompt["value"] = prompt
        return ["gemini", "--prompt", prompt]

    class FakeProcess:
        def __init__(self):
            self.stdout = object()
            self.returncode = 0

        def communicate(self, timeout=None):
            return ("done", "")

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(queue_drain, "_gemini_ci_remediation_command", fake_command)
    monkeypatch.setattr(queue_drain, "_isolated_gemini_home_env", _fake_env)
    monkeypatch.setattr(queue_drain.subprocess, "Popen", lambda *a, **k: FakeProcess())

    ok = queue_drain.remediate_review_thread(
        worktree_path=tmp_path,
        thread=_thread(comment_path="", comment_line=None, thread_path="src/fallback.py", thread_line=24),
        log=lambda msg, *_: logs.append(msg),
    )

    assert ok is True
    assert "src/fallback.py" in logs[0]
    assert "`src/fallback.py` at line 24" in captured_prompt["value"]


def test_remediate_review_thread_returns_false_on_non_zero_exit(monkeypatch, tmp_path: Path):
    logs: list[str] = []

    class FakeProcess:
        def __init__(self):
            self.stdout = object()
            self.returncode = 2

        def communicate(self, timeout=None):
            return ("failed", "")

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(queue_drain, "_gemini_ci_remediation_command", lambda prompt: ["gemini"])
    monkeypatch.setattr(queue_drain, "_isolated_gemini_home_env", _fake_env)
    monkeypatch.setattr(queue_drain.subprocess, "Popen", lambda *a, **k: FakeProcess())

    ok = queue_drain.remediate_review_thread(
        worktree_path=tmp_path,
        thread=_thread(),
        log=lambda msg, *_: logs.append(msg),
    )

    assert ok is False
    assert any("non-zero exit code" in msg for msg in logs)


def test_remediate_review_thread_logs_quota_signals(monkeypatch, tmp_path: Path):
    logs: list[tuple[str, str]] = []

    class FakeProcess:
        def __init__(self):
            self.stdout = object()
            self.returncode = 0

        def communicate(self, timeout=None):
            return ("request failed with 429 rate limit", "")

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(queue_drain, "_gemini_ci_remediation_command", lambda prompt: ["gemini"])
    monkeypatch.setattr(queue_drain, "_isolated_gemini_home_env", _fake_env)
    monkeypatch.setattr(queue_drain.subprocess, "Popen", lambda *a, **k: FakeProcess())

    ok = queue_drain.remediate_review_thread(
        worktree_path=tmp_path,
        thread=_thread(),
        log=lambda msg, level="INFO": logs.append((msg, level)),
    )

    assert ok is True
    assert any("API QUOTA EXHAUSTED" in msg and level == "ERROR" for msg, level in logs)


def test_remediate_review_thread_returns_false_on_timeout(monkeypatch, tmp_path: Path):
    class FakeProcess:
        def __init__(self):
            self.stdout = object()
            self.returncode = 0
            self.killed = False
            self.communicate_calls = 0

        def communicate(self, timeout=None):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(cmd="gemini", timeout=timeout or 1)
            return ("", "")

        def wait(self, timeout=None):
            return 0

        def kill(self):
            self.killed = True

    process = FakeProcess()
    logs: list[tuple[str, str]] = []
    monkeypatch.setattr(queue_drain, "_gemini_ci_remediation_command", lambda prompt: ["gemini"])
    monkeypatch.setattr(queue_drain, "_isolated_gemini_home_env", _fake_env)
    monkeypatch.setattr(queue_drain.subprocess, "Popen", lambda *a, **k: process)

    ok = queue_drain.remediate_review_thread(
        worktree_path=tmp_path,
        thread=_thread(),
        log=lambda msg, level="INFO": logs.append((msg, level)),
        timeout_seconds=1,
    )

    assert ok is False
    assert process.killed is True
    assert any("timed out" in msg and level == "ERROR" for msg, level in logs)
