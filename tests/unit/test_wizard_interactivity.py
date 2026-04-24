from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from dopemux.ux.questionary_support import (
    MissingInteractiveDependencyError,
    QUESTIONARY_INSTALL_MESSAGE,
    require_questionary,
)
from dopemux.ux.wizard.corpus import run_corpus_audit
from dopemux.ux.wizard.cost_profiles import run_cost_selection
from dopemux.ux.wizard.extraction import run_extraction
from dopemux.ux.wizard.provider_overrides import run_provider_overrides
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


def test_run_extraction_uses_v5_upgrades_wrapper_with_resume_and_rich_ui(
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
    monkeypatch.setenv("PYTHONPATH", "")
    monkeypatch.setattr(
        "dopemux.ux.wizard.extraction.subprocess.Popen",
        lambda cmd, **kwargs: recorded.update({"env": dict(kwargs.get("env") or {})}) or _Proc(cmd),
    )

    result = run_extraction(
        WizardState(
            repo_root=tmp_path,
            execute_mode=True,
            educate_mode=False,
            selected_policy="cost",
            workers=1,
            run_id="RUN-20260415T120000",
            prescan_dir=str(tmp_path / "prescan"),
        )
    )

    assert result.status is StageStatus.COMPLETED
    assert recorded["cmd"] == [
        sys.executable,
        str(tmp_path / "services" / "repo-truth-extractor" / "run_extraction_v5.py"),
        "--phase",
        "A",
        "--run-id",
        "RUN-20260415T120000",
        "--partition-workers",
        "1",
        "--routing-policy",
        "cost",
        "--promptset-root",
        str(tmp_path / "extraction" / "promptset"),
        "--ui",
        "rich",
        "--resume",
        "--max-cost-usd",
        "5.0",
        "--prescan-dir",
        str(tmp_path / "prescan"),
        "--skip-prescan",
        "--execute",
    ]
    assert recorded["env"]["PYTHONPATH"] == str(tmp_path / "src")


def test_run_corpus_audit_uses_integrated_v5_prescan_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prescan_dir = tmp_path / "extraction" / "repo-truth-extractor" / "v5" / "runs" / "RUN-20260415T120000" / "prescan"
    prescan_dir.mkdir(parents=True)
    manifest = [
        {
            "rel_path": "src/app.py",
            "include": True,
            "authority_class": "canonical",
            "size_bytes": 120,
            "extension": ".py",
        },
        {
            "rel_path": ".pytest_cache/v/cache",
            "include": False,
            "authority_class": "generated",
            "size_bytes": 20,
            "extension": "",
        },
    ]
    intelligence = {
        "corpus_summary": {
            "included_files": 1,
            "total_files": 2,
            "total_size_bytes": 120,
        },
        "code_intelligence": {"analyzed_files": 1},
    }
    (prescan_dir / "corpus_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (prescan_dir / "prescan_intelligence.json").write_text(
        json.dumps(intelligence), encoding="utf-8"
    )

    router = object()
    monkeypatch.setattr(
        "dopemux.ux.wizard.corpus._run_integrated_v5_prescan",
        lambda state: (prescan_dir, router),
    )

    state = WizardState(
        repo_root=tmp_path,
        run_id="RUN-20260415T120000",
        educate_mode=False,
    )
    result = run_corpus_audit(state)

    assert result.status is StageStatus.COMPLETED
    assert state.prescan_dir == str(prescan_dir)
    assert state.intelligence_router is router
    assert state.corpus_included_count == 1
    assert state.corpus_total_size == 120
    assert state.corpus_stats["excluded_count"] == 1


def test_run_cost_selection_supports_profile_browsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answers = iter(["Next profile", "Select this profile"])

    class _Prompt:
        def ask(self) -> str:
            return next(answers)

    fake_questionary = SimpleNamespace(
        Style=lambda styles: styles,
        select=lambda *args, **kwargs: _Prompt(),
    )

    monkeypatch.setattr(
        "dopemux.ux.wizard.cost_profiles.require_questionary",
        lambda: fake_questionary,
    )

    state = WizardState(
        corpus_total_size=10 * 1024 * 1024,
        selected_policy="cost",
        educate_mode=False,
    )
    result = run_cost_selection(state)

    assert result.status is StageStatus.COMPLETED
    assert state.selected_policy == "balanced"
    assert "balanced" in result.message


def test_cost_profiles_read_balanced_openrouter_from_runner_source() -> None:
    rows = run_cost_selection.__globals__["_build_policy_rows"](10 * 1024 * 1024)
    by_name = {row["name"]: row for row in rows}

    assert by_name["balanced_openrouter"]["tier_routes"]["extract"][0] == (
        "openrouter",
        "openai/gpt-5-mini",
        "OPENROUTER_API_KEY",
    )
    assert by_name["balanced_openrouter"]["authority"].endswith(
        "services/repo-truth-extractor/run_extraction_v5.py"
    )


def test_run_provider_overrides_sets_session_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    select_answers = iter(["OpenAI (OPENAI_API_KEY) [missing]", "Continue"])
    password_answers = iter(["sk-test-override"])

    class _Prompt:
        def __init__(self, answer_iter):
            self._answer_iter = answer_iter

        def ask(self) -> str:
            return next(self._answer_iter)

    fake_questionary = SimpleNamespace(
        Style=lambda styles: styles,
        select=lambda *args, **kwargs: _Prompt(select_answers),
        password=lambda *args, **kwargs: _Prompt(password_answers),
    )

    monkeypatch.setattr(
        "dopemux.ux.wizard.provider_overrides.require_questionary",
        lambda: fake_questionary,
    )

    state = WizardState(educate_mode=False)
    result = run_provider_overrides(state)

    assert result.status is StageStatus.COMPLETED
    assert state.provider_key_overrides == {"OPENAI_API_KEY": "sk-test-override"}
