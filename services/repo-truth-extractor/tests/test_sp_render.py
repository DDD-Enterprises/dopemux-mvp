from __future__ import annotations

import re
from pathlib import Path
import sys

import pytest


def test_render_sp0_with_phase_input() -> None:
    sp_render, sp_models = _load_sp_modules()
    step = sp_models.SP_STEPS_BY_ID["S0"]
    rendered = sp_render.render_sp_prompt(step, {"SP_PHASE_INPUT_JSON": {"ok": True}})
    assert "PROMPT_S0" in rendered
    assert "{{" not in rendered


def test_render_sp7_with_all_vars() -> None:
    sp_render, sp_models = _load_sp_modules()
    step = sp_models.SP_STEPS_BY_ID["S7"]
    rendered = sp_render.render_sp_prompt(
        step,
        {
            "SCHEMA_JSON": {"type": "object"},
            "RULES_JSON": {"dedupe_keys": ["id"]},
            "CANONICAL_JSON": {"items": [{"id": "a"}]},
        },
    )
    assert '"dedupe_keys": [' in rendered
    assert '"items": [' in rendered
    assert "{{" not in rendered


def test_render_sp8_drift_check() -> None:
    sp_render, sp_models = _load_sp_modules()
    step = sp_models.SP_STEPS_BY_ID["S8"]
    rendered = sp_render.render_sp_prompt(
        step,
        {
            "BASE_JSON": {"baseline": True},
            "NEW_JSON": {"baseline": False},
        },
    )
    assert '"baseline": true' in rendered
    assert '"baseline": false' in rendered


def test_render_fails_on_missing_required_var() -> None:
    sp_render, sp_models = _load_sp_modules()
    step = sp_models.SP_STEPS_BY_ID["S7"]
    with pytest.raises(RuntimeError):
        sp_render.render_sp_prompt(
            step,
            {
                "SCHEMA_JSON": {"type": "object"},
                "CANONICAL_JSON": {"items": []},
            },
        )


def test_render_fails_on_unreplaced_placeholder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sp_render, sp_models = _load_sp_modules()
    monkeypatch.setattr(sp_render, "_PROMPT_ROOT", tmp_path)
    prompt_path = tmp_path / "PROMPT_SPX.md"
    prompt_path.write_text("Needs {{UNKNOWN_VAR}}\n", encoding="utf-8")
    step = sp_models.SPStep("SPX", "PROMPT_SPX.md", tuple())
    with pytest.raises(RuntimeError):
        sp_render.render_sp_prompt(step, {})


def test_render_tolerates_missing_placeholder_in_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sp_render, sp_models = _load_sp_modules()
    monkeypatch.setattr(sp_render, "_PROMPT_ROOT", tmp_path)
    prompt_path = tmp_path / "PROMPT_SPO.md"
    prompt_path.write_text("No placeholders here.\n", encoding="utf-8")
    step = sp_models.SPStep("SPO", "PROMPT_SPO.md", ("MISSING_VAR",))
    rendered = sp_render.render_sp_prompt(step, {"MISSING_VAR": {"ok": True}})
    assert rendered.strip() == "No placeholders here."


def test_all_sp_steps_have_valid_prompt_files() -> None:
    _load_sp_modules()
    root = Path(__file__).resolve().parents[3]
    prompt_root = root / "services" / "repo-truth-extractor" / "prompts" / "phase_s"
    _, sp_models = _load_sp_modules()
    for step in sp_models.SP_STEPS:
        assert (prompt_root / step.prompt_file).exists()


def test_sp_steps_template_vars_match_prompts() -> None:
    _load_sp_modules()
    root = Path(__file__).resolve().parents[3]
    prompt_root = root / "services" / "repo-truth-extractor" / "prompts" / "phase_s"
    allow_missing = {f"S{i}" for i in range(7)}
    _, sp_models = _load_sp_modules()
    for step in sp_models.SP_STEPS:
        prompt_path = prompt_root / step.prompt_file
        text = prompt_path.read_text(encoding="utf-8")
        actual_vars = set(re.findall(r"\{\{([A-Z_]+)\}\}", text))
        expected_vars = set(step.template_vars)
        if not actual_vars and step.step_id in allow_missing and expected_vars == {"SP_PHASE_INPUT_JSON"}:
            continue
        assert actual_vars == expected_vars


def _load_sp_modules():
    root = Path(__file__).resolve().parents[3]
    module_root = root / "services" / "repo-truth-extractor"
    sys.path.insert(0, str(module_root))
    import sp.render as sp_render  # type: ignore
    import sp.models as sp_models  # type: ignore
    return sp_render, sp_models
