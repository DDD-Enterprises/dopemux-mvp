from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from dopemux.ux.questionary_support import (
    MissingInteractiveDependencyError,
    QUESTIONARY_INSTALL_MESSAGE,
    require_questionary,
)
from dopemux.ux.wizard.extraction import run_extraction
from dopemux.ux.wizard.stages import StageStatus, WizardState


def test_interactive_modules_import_without_questionary() -> None:
    modules = [
        "dopemux.ux.interactive_prompts",
        "dopemux.ux.wizard.extraction",
        "dopemux.ux.wizard.prompts",
        "dopemux.ux.wizard.cost_profiles",
        "dopemux.ux.wizard.runner",
    ]

    for name in modules:
        module = importlib.import_module(name)
        assert module is not None


def test_require_questionary_raises_deterministic_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import_module = importlib.import_module

    def _fake_import_module(name: str, package: str | None = None):
        if name == "questionary":
            raise ImportError("missing")
        return real_import_module(name, package)

    monkeypatch.setattr(
        "dopemux.ux.questionary_support.importlib.import_module",
        _fake_import_module,
    )

    with pytest.raises(MissingInteractiveDependencyError, match="Interactive Dopemux UX requires `questionary`"):
        require_questionary()

    assert "uv sync --frozen --extra test --extra services" in QUESTIONARY_INSTALL_MESSAGE


def test_run_extraction_uses_truth_run_without_forced_skip_hygiene(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    recorded: dict[str, object] = {}

    class _Prompt:
        def __init__(self, value: str):
            self._value = value

        def ask(self) -> str:
            return self._value

    fake_questionary = SimpleNamespace(
        Style=lambda styles: styles,
        select=lambda *args, **kwargs: _Prompt("Run"),
        confirm=lambda *args, **kwargs: _Prompt(True),
    )

    class _Proc:
        def __init__(self, cmd):
            self.stdout = []
            self.returncode = 0
            recorded["cmd"] = list(cmd)

        def wait(self) -> None:
            return None

    monkeypatch.setattr(
        "dopemux.ux.wizard.extraction.require_questionary",
        lambda: fake_questionary,
    )
    monkeypatch.setattr("dopemux.ux.wizard.extraction.PHASES", ["A"])
    monkeypatch.setattr(
        "dopemux.ux.wizard.extraction.subprocess.Popen",
        lambda cmd, **kwargs: _Proc(cmd),
    )

    result = run_extraction(
        WizardState(
            repo_root=tmp_path,
            execute_mode=True,
            educate_mode=False,
            selected_policy="balanced_openrouter",
            workers=4,
            run_id="RUN-20260415T120000",
        )
    )

    assert result.status is StageStatus.COMPLETED
    assert recorded["cmd"] == [
        sys.executable,
        "-m",
        "dopemux",
        "extract",
        "truth-run",
        "--phase",
        "A",
        "--routing-policy",
        "balanced_openrouter",
        "--workers",
        "4",
        "--run-id",
        "RUN-20260415T120000",
    ]
    assert "--skip-hygiene" not in recorded["cmd"]
