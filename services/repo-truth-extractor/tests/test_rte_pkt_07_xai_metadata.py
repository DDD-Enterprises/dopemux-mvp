from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module() -> types.ModuleType:
    module_path = (
        _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_extraction_v5_rte_pkt_07", module_path
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Obj:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


def _choice(content: str, finish_reason: str = "stop", **message_fields: Any) -> Obj:
    return Obj(
        finish_reason=finish_reason,
        message=Obj(content=content, **message_fields),
    )


def test_openai_compatible_response_summary_captures_returned_model_and_usage() -> None:
    runner = _load_runner_module()
    response = Obj(
        id="chatcmpl-local-001",
        model="gpt-returned-fixture",
        created=1770000000,
        system_fingerprint="fp_fixture",
        choices=[_choice('{"ok": true}', "stop")],
        usage=Obj(prompt_tokens=17, completion_tokens=5, total_tokens=22),
    )

    summary = runner.summarize_llm_response(
        provider="openai",
        transport="openai_sdk",
        response_obj=response,
        response_json=None,
        response_text='{"ok": true}',
    )

    assert summary["response_id"] == "chatcmpl-local-001"
    assert summary["returned_model_id"] == "gpt-returned-fixture"
    assert summary["effective_model_id"] == "gpt-returned-fixture"
    assert summary["finish_reason"] == "stop"
    assert summary["finish_reasons"] == ["stop"]
    assert summary["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "total_tokens": 22,
    }
    assert summary["response_text_length"] == len('{"ok": true}')
    assert summary["choice_count"] == 1
    assert summary["created"] == 1770000000
    assert summary["system_fingerprint_if_present"] == "fp_fixture"


def test_direct_xai_request_meta_keeps_requested_and_returned_model_separate() -> None:
    runner = _load_runner_module()
    summary = runner.summarize_llm_response(
        provider="xai",
        transport="openai_sdk",
        response_obj=Obj(
            id="xai-local-001",
            model="grok-effective-fixture",
            choices=[_choice("{}", "stop")],
            usage=Obj(prompt_tokens=10, completion_tokens=4, total_tokens=14),
        ),
        response_json=None,
        response_text="{}",
    )

    meta = runner.enrich_request_meta(
        {
            "provider": "xai",
            "model_id": "grok-requested-fixture",
            "api_key_env_requested": "XAI_API_KEY",
            "transport": "openai_sdk",
            "endpoint_effective": "https://api.x.ai/v1/chat/completions",
            "response_summary": summary,
        },
        run_id="run-local",
        phase="D",
        step_id="D0",
        partition_id="D_P0001",
        provider="xai",
        model_id="grok-requested-fixture",
    )

    assert meta["requested_provider"] == "xai"
    assert meta["requested_model_id"] == "grok-requested-fixture"
    assert meta["provider_route_kind"] == "direct_provider"
    assert meta["returned_model_id"] == "grok-effective-fixture"
    assert meta["effective_model_id"] == "grok-effective-fixture"
    assert meta["response_id"] == "xai-local-001"
    assert meta["api_key_env"] == "XAI_API_KEY"


def test_openrouter_xai_proxy_request_meta_is_not_direct_xai() -> None:
    runner = _load_runner_module()
    summary = runner.summarize_llm_response(
        provider="openrouter",
        transport="openai_sdk",
        response_obj=Obj(
            id="or-local-001",
            model="x-ai/grok-proxy-fixture",
            choices=[_choice("{}", "stop")],
            usage={"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        ),
        response_json=None,
        response_text="{}",
    )

    meta = runner.enrich_request_meta(
        {
            "provider": "openrouter",
            "model_id": "x-ai/grok-proxy-fixture",
            "api_key_env_requested": "OPENROUTER_API_KEY",
            "transport": "openai_sdk",
            "endpoint_effective": "https://openrouter.ai/api/v1/chat/completions",
            "response_summary": summary,
        },
        run_id="run-local",
        phase="D",
        step_id="D0",
        partition_id="D_P0002",
        provider="openrouter",
        model_id="x-ai/grok-proxy-fixture",
    )

    assert meta["requested_provider"] == "openrouter"
    assert meta["requested_model_id"] == "x-ai/grok-proxy-fixture"
    assert meta["provider_route_kind"] == "openrouter_proxy_xai"
    assert meta["returned_model_id"] == "x-ai/grok-proxy-fixture"


def test_provider_refusal_state_is_captured_without_parse_failure() -> None:
    runner = _load_runner_module()
    response = Obj(
        id="chatcmpl-refusal",
        model="gpt-refusal-fixture",
        choices=[
            _choice(
                "",
                "stop",
                refusal="Cannot comply with token=Abcd1234Abcd1234Abcd1234Abcd1234Abcd1234.",
            )
        ],
        usage=Obj(prompt_tokens=3, completion_tokens=1, total_tokens=4),
    )

    summary = runner.summarize_llm_response(
        provider="openai",
        transport="openai_sdk",
        response_obj=response,
        response_json=None,
        response_text="",
    )

    assert summary["refusal"] is True
    assert "[REDACTED]" in summary["refusal_reason"]
    assert "Abcd1234" not in summary["refusal_reason"]
    assert "failure_type" not in summary


def test_provider_incomplete_state_is_separate_from_local_parse_repair() -> None:
    runner = _load_runner_module()
    response_json = {
        "id": "chatcmpl-incomplete",
        "model": "gpt-incomplete-fixture",
        "status": "incomplete",
        "incomplete_details": {"reason": "max_output_tokens"},
        "choices": [
            {
                "finish_reason": "length",
                "message": {"content": "{\"partial\": true"},
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 2, "total_tokens": 11},
    }

    summary = runner.summarize_llm_response(
        provider="openai",
        transport="openai_compat_http",
        response_obj=response_json,
        response_json=response_json,
        response_text='{"partial": true',
    )

    assert summary["response_status"] == "incomplete"
    assert summary["finish_reason"] == "length"
    assert summary["incomplete"] is True
    assert summary["incomplete_reason"] == "max_output_tokens"


def test_gemini_style_response_summary_preserves_finish_safety_and_usage() -> None:
    runner = _load_runner_module()
    response = Obj(
        candidates=[Obj(finish_reason="SAFETY", safety_reason="policy_block")],
        usage_metadata=Obj(
            prompt_token_count=13,
            candidates_token_count=6,
            total_token_count=19,
        ),
    )

    summary = runner.summarize_llm_response(
        provider="gemini",
        transport="sdk",
        response_obj=response,
        response_json=None,
        response_text="{}",
    )

    assert summary["finish_reason"] == "SAFETY"
    assert summary["finish_reasons"] == ["SAFETY"]
    assert summary["safety_reason"] == "policy_block"
    assert summary["usage"] == {
        "input_tokens": 13,
        "output_tokens": 6,
        "total_tokens": 19,
    }


def test_structured_output_metadata_is_flattened_into_request_meta() -> None:
    runner = _load_runner_module()
    meta = runner.enrich_request_meta(
        {
            "provider": "openai",
            "model_id": "gpt-structured-fixture",
            "structured_output": {
                "enabled": True,
                "structured_output_mode_effective": "json_schema",
                "response_format_type": "json_schema",
                "schema_name": "RTEFixtureSchema",
                "strict": True,
                "schema_variant": "openai_strict_json_schema",
                "transport_mode": "response_format_json_schema",
            },
        },
        run_id="run-local",
        phase="D",
        step_id="D0",
        partition_id="D_P0003",
        provider="openai",
        model_id="gpt-structured-fixture",
    )

    assert meta["structured_output_mode"] == "json_schema"
    assert meta["response_format_type"] == "json_schema"
    assert meta["json_schema_name_if_present"] == "RTEFixtureSchema"
    assert meta["strict_schema_required"] is True
    assert meta["provider_schema_variant"] == "openai_strict_json_schema"


def test_metadata_extraction_tests_do_not_invoke_provider_clients(monkeypatch) -> None:
    runner = _load_runner_module()

    def fail_provider_call(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("provider client must not be invoked by metadata tests")

    monkeypatch.setattr(runner, "get_xai_client", fail_provider_call)
    monkeypatch.setattr(runner, "get_openrouter_client", fail_provider_call)
    monkeypatch.setattr(runner, "get_openai_client", fail_provider_call)
    monkeypatch.setattr(runner, "get_gemini_client", fail_provider_call)

    summary = runner.summarize_llm_response(
        provider="openrouter",
        transport="openai_sdk",
        response_obj=Obj(
            id="local-only",
            model="x-ai/local-only",
            choices=[_choice("{}", "stop")],
            usage=Obj(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        ),
        response_json=None,
        response_text="{}",
    )

    assert summary["response_id"] == "local-only"
