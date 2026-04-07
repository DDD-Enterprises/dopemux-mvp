from __future__ import annotations

import argparse
import importlib
import json

from _fl_int_helpers import ensure_service_root_on_path, fake_fl_int_payload


def test_standalone_prompt_executor_passes_timeout_and_observer(monkeypatch) -> None:
    root = ensure_service_root_on_path()
    module = importlib.import_module("run_fl_int")
    models = importlib.import_module("fl_int.models")
    schema_module = importlib.import_module("s_int.schema_validate")
    step = next(row for row in models.FL_INT_STEPS if row.step_id == "F0")
    schema = schema_module.load_schema(
        root
        / "services"
        / "repo-truth-extractor"
        / "prompts"
        / "phase_fl_int"
        / "schemas"
        / "F0.json"
    )
    observed = []
    captured = {}

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        captured["timeout_seconds"] = kwargs.get("timeout_seconds")
        return {
            "ok": True,
            "text": json.dumps(fake_fl_int_payload("F0")),
            "meta": {
                "provider": kwargs["provider"],
                "model_id": kwargs["model_id"],
                "api_key_env_requested": kwargs["api_key_env"],
                "status_code": 200,
                "response_received": True,
                "timeout_seconds": kwargs.get("timeout_seconds"),
            },
        }

    def fake_call_llm_with_ladder(**kwargs):  # type: ignore[no-untyped-def]
        return kwargs["execute_attempt"](tuple(kwargs["ladder"][0]), 0)

    monkeypatch.setattr(module.runner, "call_llm", fake_call_llm)
    monkeypatch.setattr(module.runner, "call_llm_with_ladder", fake_call_llm_with_ladder)

    args = argparse.Namespace(
        dry_run=False,
        routing_policy="cost",
        fl_int_provider_timeout_seconds=123,
        fl_int_f0_batch_timeout_seconds=210,
    )
    cfg = module._build_cfg(args)
    executor = module._prompt_executor(cfg)
    expected_route = tuple(models.ladder_for_step(step)[0])
    payload = executor(
        step,
        "{}",
        schema,
        {
            "__fl_int_diag_observer__": lambda stage, info=None: observed.append(
                {
                    "stage": stage,
                    "info": info or {},
                }
            )
        },
    )

    assert captured["timeout_seconds"] == 123
    assert payload["route"] == expected_route
    assert [row["stage"] for row in observed] == [
        "provider_call_start",
        "provider_call_return",
        "normalize_start",
        "normalize_return",
    ]
    assert observed[1]["info"]["request_meta"]["timeout_seconds"] == 123
