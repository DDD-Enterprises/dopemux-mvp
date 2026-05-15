from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _load_batch_clients_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "lib" / "batch_clients.py"
    spec = importlib.util.spec_from_file_location("rte_pkt_08_batch_clients", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("rte_pkt_08_runner", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _output_row(custom_id: str, *, model: str = "gpt-5-nano") -> dict[str, Any]:
    return {
        "id": f"batch_req_{custom_id}",
        "custom_id": custom_id,
        "response": {
            "status_code": 200,
            "request_id": f"req_{custom_id}",
            "body": {
                "id": f"chatcmpl_{custom_id}",
                "model": model,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "{\"ok\": true}"},
                    }
                ],
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                },
            },
        },
        "error": None,
    }


def _error_row(custom_id: str, secret: str) -> dict[str, Any]:
    return {
        "custom_id": custom_id,
        "response": {"status_code": 400},
        "error": {
            "type": "invalid_request_error",
            "code": "bad_request",
            "message": f"provider rejected Authorization: Bearer {secret}",
        },
    }


def test_batch_static_output_jsonl_preserves_custom_id_and_response_metadata() -> None:
    module = _load_batch_clients_module()
    raw_text = "\n".join(
        json.dumps(row, sort_keys=True)
        for row in [_output_row("A_P0001"), _output_row("A_P0002", model="gpt-5-mini")]
    )

    report = module.parse_openai_compatible_batch_output_jsonl(raw_text)

    assert report["artifact_class"] == "provider_output_jsonl_fixture"
    assert report["parse_status"] == "parsed"
    assert report["custom_ids"] == ["A_P0001", "A_P0002"]
    row = report["rows"][0]
    assert row["custom_id"] == "A_P0001"
    assert row["response_status_code"] == 200
    assert row["response_body_present"] is True
    assert row["response_id_if_present"] == "chatcmpl_A_P0001"
    assert row["returned_model_id_if_present"] == "gpt-5-nano"
    assert row["finish_reason_if_present"] == "stop"
    assert row["usage_if_present"]["total_tokens"] == 18
    assert row["parse_status"] == "parsed"
    assert "NOT_LIVE_VALIDATED" in report["markers"]


def test_batch_static_error_jsonl_preserves_custom_id_and_redacts_error_metadata() -> None:
    module = _load_batch_clients_module()
    secret = "sk-proj-" + ("A" * 32)
    raw_text = json.dumps(_error_row("A_P0002", secret), sort_keys=True)

    report = module.parse_openai_compatible_batch_error_jsonl(raw_text)

    assert report["artifact_class"] == "provider_error_jsonl_fixture"
    assert report["custom_ids"] == ["A_P0002"]
    row = report["rows"][0]
    assert row["custom_id"] == "A_P0002"
    assert row["error_type"] == "invalid_request_error"
    assert row["error_code"] == "bad_request"
    assert row["status_code_if_present"] == 400
    assert row["failure_type"] == "provider_error"
    assert row["redaction_status"] == "redacted"
    assert secret not in json.dumps(report, sort_keys=True)
    assert "[REDACTED]" in row["error_message_redacted"]


def test_batch_static_missing_rows_are_hard_failures_and_partial_is_distinct() -> None:
    module = _load_batch_clients_module()
    output_report = module.parse_openai_compatible_batch_output_jsonl(
        json.dumps(_output_row("A_P0001"), sort_keys=True)
    )
    error_report = module.parse_openai_compatible_batch_error_jsonl(
        json.dumps(_error_row("A_P0002", "sk-proj-" + ("B" * 32)), sort_keys=True)
    )

    partial = module.build_openai_compatible_batch_static_proof(
        request_custom_ids=["A_P0001", "A_P0002", "A_P0003"],
        output_rows=output_report["rows"],
        error_rows=error_report["rows"],
        batch_info={
            "id": "batch_fixture",
            "status": "completed",
            "output_file_id": "file-output-1",
            "error_file_id": "file-error-1",
        },
        provider="xai",
        requested_provider="xai",
        requested_model_id="grok-code-fast-1",
    )
    full = module.build_openai_compatible_batch_static_proof(
        request_custom_ids=["A_P0001"],
        output_rows=output_report["rows"],
        error_rows=[],
        batch_info={"id": "batch_fixture", "status": "completed"},
        provider="openai",
        requested_provider="openai",
        requested_model_id="gpt-5-nano",
    )

    assert partial["request_count"] == 3
    assert partial["result_count"] == 1
    assert partial["error_count"] == 1
    assert partial["missing_row_count"] == 1
    assert partial["missing_custom_ids"] == ["A_P0003"]
    assert partial["missing_rows_are_hard_failure"] is True
    assert partial["partial_failure"] is True
    assert partial["full_success"] is False
    assert partial["output_file_id"] == "file-output-1"
    assert partial["error_file_id"] == "file-error-1"
    assert partial["not_live_validated"] is True
    assert full["partial_failure"] is False
    assert full["full_success"] is True


def test_batch_static_terminal_statuses_are_distinct_and_runner_treats_expired_terminal() -> None:
    module = _load_batch_clients_module()
    runner = _load_runner_module()

    assert module.classify_batch_terminal_status("completed")["status_class"] == "success"
    assert module.classify_batch_terminal_status("failed")["status_class"] == "failed"
    assert module.classify_batch_terminal_status("expired")["status_class"] == "expired"
    assert module.classify_batch_terminal_status("cancelled")["status_class"] == "cancelled"
    assert module.classify_batch_terminal_status("timeout")["status_class"] == "timeout"
    assert module.classify_batch_terminal_status("submitted")["terminal"] is False
    assert runner._batch_terminal_state("expired") is True


def test_batch_static_corrupt_jsonl_lines_are_counted_and_threshold_is_explicit() -> None:
    module = _load_batch_clients_module()
    valid_rows = [json.dumps(_output_row(f"A_P{i:04d}"), sort_keys=True) for i in range(20)]
    under_threshold = module.parse_openai_compatible_batch_output_jsonl(
        "\n".join([*valid_rows, "{not-json"])
    )

    assert under_threshold["parse_status"] == "parsed_with_discards"
    assert under_threshold["valid_row_count"] == 20
    assert under_threshold["discarded_line_count"] == 1
    assert under_threshold["corruption_threshold_exceeded"] is False
    assert under_threshold["discarded_lines"][0]["reason"] == "invalid_json"

    try:
        module.parse_openai_compatible_batch_output_jsonl(
            "\n".join([json.dumps(_output_row("A_P0001"), sort_keys=True), "{not-json"]),
            raise_on_corruption=True,
        )
    except RuntimeError as exc:
        assert "BatchCorruptionError" in str(exc)
        assert "1/2" in str(exc)
    else:
        raise AssertionError("Expected corrupt JSONL threshold to fail closed")


def test_batch_static_request_metadata_excludes_raw_payload_text() -> None:
    module = _load_batch_clients_module()
    request = module.BatchRequest(
        custom_id="A_P0001",
        model_id="gpt-5-nano",
        system_prompt="Return JSON. Authorization: Bearer sk-proj-" + ("C" * 32),
        user_content="fixture body",
        force_json_output=False,
        metadata={
            "phase": "A",
            "step_id": "A1",
            "partition_id": "A_P0001",
            "structured_output_mode": "json_schema",
        },
        response_format={
            "type": "json_schema",
            "json_schema": {"strict": True, "schema": {"type": "object"}},
        },
    )
    wire_row = {
        "custom_id": "A_P0001",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-5-nano",
            "messages": [{"role": "system", "content": "[omitted]"}],
            "response_format": request.response_format,
        },
    }

    metadata = module.build_batch_request_static_metadata(
        request,
        module.BatchRoute("openai", "gpt-5-nano", "OPENAI_API_KEY"),
        wire_row=wire_row,
    )

    assert metadata["custom_id"] == "A_P0001"
    assert metadata["body.model"] == "gpt-5-nano"
    assert metadata["body.messages_present_boolean"] is True
    assert metadata["body.response_format_type_if_present"] == "json_schema"
    assert metadata["provider"] == "openai"
    assert metadata["requested_model_id"] == "gpt-5-nano"
    assert metadata["structured_output_mode_if_present"] == "json_schema"
    assert metadata["phase_if_encoded"] == "A"
    assert metadata["step_id_if_encoded"] == "A1"
    assert metadata["partition_id_if_encoded"] == "A_P0001"
    assert metadata["payload_text_included"] is False
    assert "sk-proj-" not in json.dumps(metadata, sort_keys=True)


def test_batch_static_helpers_do_not_instantiate_provider_clients(monkeypatch) -> None:
    module = _load_batch_clients_module()

    def fail_provider_init(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("provider client construction must not be reached")

    monkeypatch.setattr(module.OpenAIBatchClient, "__init__", fail_provider_init)
    monkeypatch.setattr(module.XAIBatchClient, "__init__", fail_provider_init)

    report = module.parse_openai_compatible_batch_output_jsonl(
        json.dumps(_output_row("A_P0001"), sort_keys=True)
    )
    proof = module.build_openai_compatible_batch_static_proof(
        request_custom_ids=["A_P0001"],
        output_rows=report["rows"],
        error_rows=[],
        batch_info={"status": "completed"},
        provider="xai",
    )

    assert proof["markers"] == list(module.BATCH_STATIC_PROOF_MARKERS)
    assert proof["not_live_validated"] is True
    assert proof["request_count"] == 1
