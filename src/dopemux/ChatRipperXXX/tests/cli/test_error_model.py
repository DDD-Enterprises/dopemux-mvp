from __future__ import annotations

from pathlib import Path

from chatx.cli_errors import build_problem, redact_path


def test_build_problem_minimal() -> None:
    p = build_problem(code="INVALID_INPUT", title="Invalid input", status=400, detail="bad", instance="/extract")
    assert p["type"].endswith("/problems/INVALID_INPUT")
    assert p["title"] == "Invalid input"
    assert p["status"] == 400
    assert p["detail"] == "bad"
    assert p["instance"] == "/extract"
    assert p["code"] == "INVALID_INPUT"


def test_redact_path_home(tmp_path: Path, monkeypatch) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    p = fake_home / "Library" / "Messages" / "chat.db"
    red = redact_path(p)
    assert red.startswith("~")
    assert "chat.db" in red

