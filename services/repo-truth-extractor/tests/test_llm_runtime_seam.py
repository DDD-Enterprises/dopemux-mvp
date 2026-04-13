from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import load_runner_module


def test_call_llm_delegates_to_llm_runtime_impl(monkeypatch):
    runner = load_runner_module()
    sentinel = {"ok": True, "text": "{}", "meta": {}}
    calls = {}

    monkeypatch.setattr(runner, "_llm_runtime_deps", lambda: "llm-deps")

    def fake_impl(
        deps,
        provider,
        model_id,
        api_key_env,
        system_prompt,
        user_content,
        cfg,
        **kwargs,
    ):
        calls["args"] = (
            deps,
            provider,
            model_id,
            api_key_env,
            system_prompt,
            user_content,
            cfg,
            kwargs,
        )
        return sentinel

    monkeypatch.setattr(runner, "llm_runtime_call_llm", fake_impl)

    cfg = object()
    result = runner.call_llm(
        provider="openrouter",
        model_id="openai/gpt-5.3-codex",
        api_key_env="OPENROUTER_API_KEY",
        system_prompt="system",
        user_content="user",
        cfg=cfg,
        force_json_output=True,
    )

    assert result is sentinel
    assert calls["args"][0:7] == (
        "llm-deps",
        "openrouter",
        "openai/gpt-5.3-codex",
        "OPENROUTER_API_KEY",
        "system",
        "user",
        cfg,
    )
    assert calls["args"][7]["force_json_output"] is True


def test_run_comparison_lane_delegates_to_llm_runtime_impl(monkeypatch, tmp_path: Path):
    runner = load_runner_module()
    sentinel = [{"partition_id": "A_P0001", "success": True}]
    calls = {}

    monkeypatch.setattr(runner, "_llm_runtime_deps", lambda: "llm-deps")

    def fake_impl(deps, **kwargs):
        calls["deps"] = deps
        calls["kwargs"] = kwargs
        return sentinel

    monkeypatch.setattr(runner, "llm_runtime_run_comparison_lane", fake_impl)

    result = runner.run_comparison_lane(
        phase="A",
        step_id="A9",
        partitions=[{"id": "A_P0001", "paths": ["/tmp/p1"]}],
        phase_dir=tmp_path,
        cfg=object(),
        prompt_text="prompt",
        output_artifacts=("OUT.json",),
        build_partition_context_fn=lambda **_: ("ctx", {}),
        call_llm_fn=lambda **_: {"text": "{}", "meta": {}},
        parse_json_from_response_fn=runner.parse_json_from_response,
        coerce_artifacts_from_response_fn=runner.coerce_artifacts_from_response,
    )

    assert result is sentinel
    assert calls["deps"] == "llm-deps"
    assert calls["kwargs"]["phase"] == "A"
    assert calls["kwargs"]["step_id"] == "A9"
    assert calls["kwargs"]["output_artifacts"] == ("OUT.json",)
