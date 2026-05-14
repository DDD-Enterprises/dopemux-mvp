from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pytest


SELECTED_ROUTE = ("openai", "gpt-5-nano", "OPENAI_API_KEY")
ARTIFACT_NAME = "STRICT_BATCH_RESPONSE.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module():
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_batch_response_format", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeFiles:
    def __init__(self) -> None:
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


class _FakeBatches:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.created.append(dict(kwargs))
        return SimpleNamespace(id="batch-job-1")


class _FakeOpenAICompatClient:
    def __init__(self) -> None:
        self.files = _FakeFiles()
        self.batches = _FakeBatches()


def _client(runner: Any):
    client = object.__new__(runner.OpenAIBatchClient)
    fake = _FakeOpenAICompatClient()
    client._client = fake
    return client, fake


def _strict_step_contract(
    *,
    expected_artifacts: tuple[str, ...] = (ARTIFACT_NAME,),
    route_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route = {
        "provider": SELECTED_ROUTE[0],
        "model_id": SELECTED_ROUTE[1],
        "api_key_env": SELECTED_ROUTE[2],
        "structured_output_mode": "json_schema",
        "strict_json_schema": True,
        "strict_passthrough_verified": True,
    }
    route.update(route_overrides or {})
    return {
        "phase": "A",
        "step_id": "A1",
        "scope": {"json_managed": True},
        "expected_artifacts": list(expected_artifacts),
        "artifact_order": list(expected_artifacts),
        "lane": {
            "lane_class": "BULK_DOCS_STRICT",
            "strict_schema_required": True,
            "strict_schema_required_primary": True,
            "primary_routes": [route],
        },
        "artifacts": {
            name: {
                "canonical_schema_id": f"{name.removesuffix('.json')}@v1",
                "required_fields": ["id", "path", "line_range"],
                "prompt_required_item_fields": [],
                "allow_empty_array_fields": [],
            }
            for name in expected_artifacts
        },
    }


def _batch_request(runner: Any, **overrides: Any):
    payload = {
        "custom_id": "A_P0001",
        "model_id": SELECTED_ROUTE[1],
        "system_prompt": "Return JSON.",
        "user_content": "Extract the fixture.",
        "provider": SELECTED_ROUTE[0],
        "selected_route": SELECTED_ROUTE,
        "transport": "openai_sdk",
        "strict_contract_required": True,
        "step_contract": _strict_step_contract(),
        "artifact_names": (ARTIFACT_NAME,),
        "force_json_output": False,
        "metadata": {"phase": "A", "step_id": "A1", "partition_id": "A_P0001"},
    }
    payload.update(overrides)
    return runner.build_v5_batch_request(**payload)


def test_v5_batch_request_construction_propagates_strict_response_format_to_wire_payload() -> None:
    runner = _load_runner_module()
    request = _batch_request(runner)

    assert request.metadata["strict"] == "true"
    assert request.response_format is not None
    assert request.response_format["type"] == "json_schema"
    assert request.response_format["json_schema"]["strict"] is True
    assert request.response_format["json_schema"]["schema"]["type"] == "object"

    client, fake = _client(runner)
    job_id = client.submit(
        [request],
        runner.BatchRoute(*SELECTED_ROUTE),
        {"phase": "A", "step_id": "A1", "partition_id": "A_P0001"},
    )

    assert job_id == "batch-job-1"
    assert len(fake.files.uploads) == 1
    rows = [json.loads(line) for line in fake.files.uploads[0].splitlines()]
    assert len(rows) == 1
    response_format = rows[0]["body"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["additionalProperties"] is False


def test_v5_strict_batch_request_missing_schema_fails_before_upload_or_submit() -> None:
    runner = _load_runner_module()
    _unused_client, fake = _client(runner)

    with pytest.raises(ValueError, match="requires at least one artifact schema"):
        _batch_request(
            runner,
            step_contract=_strict_step_contract(expected_artifacts=()),
            artifact_names=(ARTIFACT_NAME,),
        )

    assert fake.files.uploads == []
    assert fake.batches.created == []


def test_v5_strict_batch_request_cannot_downgrade_to_json_object() -> None:
    runner = _load_runner_module()

    with pytest.raises(ValueError, match="response_format.type=json_schema"):
        _batch_request(
            runner,
            step_contract=_strict_step_contract(
                route_overrides={
                    "structured_output_mode": "json_object",
                    "strict_json_schema": False,
                }
            ),
        )


def test_v5_non_strict_batch_request_preserves_omitted_openai_response_format() -> None:
    runner = _load_runner_module()
    request = _batch_request(
        runner,
        strict_contract_required=False,
        step_contract=None,
        artifact_names=(),
        force_json_output=False,
    )

    assert "strict" not in request.metadata
    assert request.response_format is None

    client, fake = _client(runner)
    job_id = client.submit(
        [request],
        runner.BatchRoute(*SELECTED_ROUTE),
        {"phase": "A", "step_id": "A1", "partition_id": "A_P0001"},
    )

    assert job_id == "batch-job-1"
    rows = [json.loads(line) for line in fake.files.uploads[0].splitlines()]
    assert "response_format" not in rows[0]["body"]
