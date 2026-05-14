from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any


def _load_batch_clients_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "lib" / "batch_clients.py"
    spec = importlib.util.spec_from_file_location("batch_clients_under_test", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeFiles:
    def __init__(self, result_text: str = "") -> None:
        self.result_text = result_text
        self.uploads: list[str] = []

    def create(self, *, file, purpose: str):  # type: ignore[no-untyped-def]
        assert purpose == "batch"
        payload = file.read()
        self.uploads.append(
            payload.decode("utf-8")
            if isinstance(payload, (bytes, bytearray))
            else str(payload)
        )
        return SimpleNamespace(id="uploaded-file-1")

    def content(self, file_id: str):  # type: ignore[no-untyped-def]
        assert file_id == "result-file-1"
        return SimpleNamespace(text=self.result_text)


class _FakeBatches:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.created.append(dict(kwargs))
        return SimpleNamespace(id="batch-job-1")

    def retrieve(self, job_id: str):  # type: ignore[no-untyped-def]
        assert job_id == "batch-job-1"
        return SimpleNamespace(
            id=job_id,
            status="completed",
            output_file_id="result-file-1",
            error_file_id="",
        )

    def cancel(self, job_id: str) -> None:
        assert job_id == "batch-job-1"


class _FakeOpenAICompatClient:
    def __init__(self, result_text: str = "") -> None:
        self.files = _FakeFiles(result_text)
        self.batches = _FakeBatches()


def _client(module: Any, cls: type, result_text: str = ""):
    client = object.__new__(cls)
    fake = _FakeOpenAICompatClient(result_text)
    client._client = fake
    return client, fake


def _route(module: Any, provider: str = "openai"):
    return module.BatchRoute(
        provider=provider,
        model_id="gpt-5-nano",
        api_key_env="OPENAI_API_KEY",
    )


def _batch_request(module: Any, **overrides: Any):
    payload = {
        "custom_id": "A_P0001",
        "model_id": "gpt-5-nano",
        "system_prompt": "Return JSON.",
        "user_content": "Summarize this fixture.",
        "force_json_output": True,
        "metadata": {"phase": "A", "step_id": "A1", "partition_id": "A_P0001"},
    }
    payload.update(overrides)
    return module.BatchRequest(**payload)


def _result_line(custom_id: str, content: str) -> str:
    return json.dumps(
        {
            "id": f"batch_req_{custom_id}",
            "custom_id": custom_id,
            "response": {
                "status_code": 200,
                "request_id": f"req_{custom_id}",
                "body": {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": content,
                            }
                        }
                    ]
                },
            },
            "error": None,
        }
    )


def _strict_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "batch_fixture_schema",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
                "additionalProperties": False,
            },
        },
    }


def test_openai_fetch_results_parses_valid_provider_jsonl() -> None:
    module = _load_batch_clients_module()
    raw_text = "\n".join(
        [
            _result_line("A_P0001", "{\"ok\": true}"),
            _result_line("A_P0002", "{\"ok\": false}"),
        ]
    )
    client, _ = _client(module, module.OpenAIBatchClient, raw_text)

    results = client.fetch_results("batch-job-1")

    assert [result.custom_id for result in results] == ["A_P0001", "A_P0002"]
    assert [result.output_text for result in results] == [
        "{\"ok\": true}",
        "{\"ok\": false}",
    ]
    assert results[0].error is None
    assert results[0].meta["response"]["status_code"] == 200


def test_openai_fetch_results_keeps_valid_rows_when_corrupt_lines_under_threshold() -> None:
    module = _load_batch_clients_module()
    valid_rows = [_result_line(f"A_P{i:04d}", "{\"ok\": true}") for i in range(20)]
    raw_text = "\n".join([*valid_rows, "{not-json"])
    client, _ = _client(module, module.OpenAIBatchClient, raw_text)

    results = client.fetch_results("batch-job-1")

    assert len(results) == 20
    assert results[0].custom_id == "A_P0000"
    assert results[-1].custom_id == "A_P0019"


def test_openai_fetch_results_raises_when_corrupt_threshold_exceeded() -> None:
    module = _load_batch_clients_module()
    raw_text = "\n".join([_result_line("A_P0001", "{\"ok\": true}"), "{not-json"])
    client, _ = _client(module, module.OpenAIBatchClient, raw_text)

    try:
        client.fetch_results("batch-job-1")
    except RuntimeError as exc:
        assert "BatchCorruptionError" in str(exc)
        assert "1/2" in str(exc)
    else:
        raise AssertionError("Expected BatchCorruptionError-style RuntimeError")


def test_openai_submit_serializes_strict_json_schema_response_format() -> None:
    module = _load_batch_clients_module()
    client, fake = _client(module, module.OpenAIBatchClient)
    request = _batch_request(
        module,
        metadata={"strict": "true", "phase": "A", "step_id": "A1"},
        response_format=_strict_response_format(),
    )

    job_id = client.submit([request], _route(module), {"phase": "A", "step_id": "A1"})

    assert job_id == "batch-job-1"
    rows = [json.loads(line) for line in fake.files.uploads[0].splitlines()]
    assert len(rows) == 1
    response_format = rows[0]["body"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["additionalProperties"] is False


def test_openai_submit_fails_closed_for_strict_without_schema() -> None:
    module = _load_batch_clients_module()
    client, fake = _client(module, module.OpenAIBatchClient)
    request = _batch_request(module, metadata={"strict": "true"})

    try:
        client.submit([request], _route(module), {"phase": "A", "step_id": "A1"})
    except ValueError as exc:
        assert "Strict batch request requires response_format.type=json_schema" in str(exc)
    else:
        raise AssertionError("Expected strict batch request without json_schema to fail closed")

    assert fake.files.uploads == []
    assert fake.batches.created == []


def test_openai_submit_preserves_non_strict_json_object_payload() -> None:
    module = _load_batch_clients_module()
    client, fake = _client(module, module.OpenAIBatchClient)
    request = _batch_request(module, metadata={"phase": "A", "step_id": "A1"})

    job_id = client.submit([request], _route(module), {"phase": "A", "step_id": "A1"})

    assert job_id == "batch-job-1"
    rows = [json.loads(line) for line in fake.files.uploads[0].splitlines()]
    assert rows[0]["body"]["response_format"] == {"type": "json_object"}


def test_xai_fetch_results_uses_inherited_openai_compatible_parser() -> None:
    module = _load_batch_clients_module()
    raw_text = _result_line("X_P0001", "{\"provider\": \"xai\"}")
    client, _ = _client(module, module.XAIBatchClient, raw_text)

    results = client.fetch_results("batch-job-1")

    assert len(results) == 1
    assert results[0].custom_id == "X_P0001"
    assert results[0].output_text == "{\"provider\": \"xai\"}"
