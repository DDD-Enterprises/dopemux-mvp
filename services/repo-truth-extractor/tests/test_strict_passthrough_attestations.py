from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pytest


OPENAI_ROUTE = ("openai", "gpt-5-nano", "OPENAI_API_KEY")
ARTIFACT_NAME = "STRICT_ATTESTATION.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module():
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_strict_attestation", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: Any):
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    defaults = {
        "dry_run": True,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": False,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "default",
        "retry_max_attempts": 4,
        "retry_base_seconds": 2.0,
        "retry_max_seconds": 30.0,
        "phase_auth_fail_threshold": 5,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "executor": "thread",
        "routing_policy": "cost",
        "disable_escalation": False,
        "escalation_max_hops": 2,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 30,
        "batch_wait_timeout_seconds": 1800,
        "batch_max_requests_per_job": 2000,
        "batch_submit_only": False,
        "webhook_url": "",
        "webhook_secret": "",
        "webhook_timeout_seconds": 5,
        "webhook_required": False,
        "webhook_auto_continue": False,
        "live_ok": False,
        "selected_s_steps": None,
        "selected_execution_step": None,
        "d0_max_files": None,
        "d1_max_files": None,
        "provider_denylist": (),
        "compare_mode": None,
        "compare_model": None,
        "compare_provider": None,
        "compare_steps": None,
        "prescan_dir": None,
        "router": None,
        "prescan_skip": False,
        "prescan_online": False,
        "prescan_import_dir": None,
        "prescan_allow_scope_reduction": False,
        "allow_online_llm": False,
        "max_cost_usd": None,
        "ledger": None,
        "fl_int_provider_timeout_seconds": 180,
        "fl_int_f0_batch_timeout_seconds": 210,
    }
    for key, value in defaults.items():
        object.__setattr__(cfg, key, value)
    return cfg


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
    def create(self, **kwargs):  # type: ignore[no-untyped-def]
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
    provider: str = OPENAI_ROUTE[0],
    model_id: str = OPENAI_ROUTE[1],
    api_key_env: str = OPENAI_ROUTE[2],
    strict_passthrough_verified: bool = True,
) -> dict[str, Any]:
    return {
        "phase": "A",
        "step_id": "A1",
        "scope": {"json_managed": True},
        "expected_artifacts": [ARTIFACT_NAME],
        "artifact_order": [ARTIFACT_NAME],
        "lane": {
            "lane_class": "BULK_DOCS_STRICT",
            "strict_schema_required": True,
            "strict_schema_required_primary": True,
            "primary_routes": [
                {
                    "provider": provider,
                    "model_id": model_id,
                    "api_key_env": api_key_env,
                    "structured_output_mode": "json_schema",
                    "strict_json_schema": True,
                    "strict_passthrough_verified": strict_passthrough_verified,
                }
            ],
        },
        "artifacts": {
            ARTIFACT_NAME: {
                "canonical_schema_id": "STRICT_ATTESTATION@v1",
                "required_fields": ["id", "path", "line_range"],
                "prompt_required_item_fields": [],
                "allow_empty_array_fields": [],
            }
        },
    }


def _batch_request(runner: Any, **overrides: Any):
    payload = {
        "custom_id": "A_P0001",
        "model_id": OPENAI_ROUTE[1],
        "system_prompt": "Return JSON.",
        "user_content": "Extract the fixture.",
        "provider": OPENAI_ROUTE[0],
        "selected_route": OPENAI_ROUTE,
        "transport": "openai_sdk",
        "strict_contract_required": True,
        "step_contract": _strict_step_contract(),
        "artifact_names": (ARTIFACT_NAME,),
        "force_json_output": False,
        "metadata": {"phase": "A", "step_id": "A1", "partition_id": "A_P0001"},
    }
    payload.update(overrides)
    return runner.build_v5_batch_request(**payload)


def _dirs(runner: Any, tmp_path: Path) -> dict[str, Path]:
    root = tmp_path / "run"
    phase_dir = root / runner.PHASE_DIR_NAMES["A"]
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    return {"root": root, "A": phase_dir}


def _write_raw(
    dirs: dict[str, Path],
    *,
    request_meta: dict[str, Any],
    phase: str = "A",
    step_id: str = "A1",
    partition_id: str = "A_P0001",
) -> None:
    raw_path = dirs[phase] / "raw" / f"{step_id}__{partition_id}.json"
    raw_path.write_text(
        json.dumps(
            {
                "phase": phase,
                "step_id": step_id,
                "partition_id": partition_id,
                "artifacts": [],
                "request_meta": request_meta,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _strict_attestation(**overrides: Any) -> dict[str, Any]:
    row = {
        "stage": "primary",
        "selected": True,
        "provider": OPENAI_ROUTE[0],
        "model_id": OPENAI_ROUTE[1],
        "api_key_env": OPENAI_ROUTE[2],
        "transport": "openai_sdk",
        "strict_required": True,
        "strict_json_schema": True,
        "strict_passthrough_verified": True,
        "strict_capable": True,
        "attempts": [],
    }
    row.update(overrides)
    return row


def test_strict_attestation_verifies_only_observed_wire_payload(
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    request = _batch_request(runner)
    client, fake = _client(runner)

    client.submit(
        [request],
        runner.BatchRoute(*OPENAI_ROUTE),
        {"phase": "A", "step_id": "A1", "partition_id": "A_P0001"},
    )

    wire_row = json.loads(fake.files.uploads[0].splitlines()[0])
    evidence = runner.build_strict_passthrough_evidence_from_wire_payload(
        wire_row,
        provider=OPENAI_ROUTE[0],
        model_id=OPENAI_ROUTE[1],
        transport="openai_sdk",
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
    )
    dirs = _dirs(runner, tmp_path)
    _write_raw(
        dirs,
        request_meta={
            runner.STRICT_PASSTHROUGH_RUNTIME_EVIDENCE_KEY: [evidence],
            "strict_route_attestations": [_strict_attestation()],
        },
    )

    payload = runner.write_strict_passthrough_attestations(dirs, "run-test", ["A"])

    assert payload["version"] == "STRICT_PASSTHROUGH_ATTESTATIONS_V2"
    row = payload["rows"][0]
    assert row["attestation_status"] == "VERIFIED"
    assert row["attestation_reason"] == "observed_strict_json_schema"
    assert row["strict_passthrough_verified"] is True
    assert row["route_strict_passthrough_claim"] is True
    assert row["evidence_source"] == "wire_payload"
    assert row["response_format_type"] == "json_schema"
    assert row["json_schema_present"] is True
    assert row["json_schema_strict"] is True
    assert row["schema_sha256"]


def test_strict_intent_alone_is_not_verified(tmp_path: Path) -> None:
    runner = _load_runner_module()
    dirs = _dirs(runner, tmp_path)
    _write_raw(
        dirs,
        request_meta={"strict_route_attestations": [_strict_attestation()]},
    )

    payload = runner.write_strict_passthrough_attestations(dirs, "run-test", ["A"])

    row = payload["rows"][0]
    assert row["attestation_status"] == "UNVERIFIED"
    assert row["attestation_reason"] == "runtime_or_wire_evidence_missing"
    assert row["strict_passthrough_verified"] is False
    assert row["route_strict_passthrough_claim"] is True


def test_explicit_openrouter_route_outside_primary_contract_is_not_synthesized_verified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    contract = runner._step_contract_for("A", "A0")
    monkeypatch.setenv(
        "DPMX_EXPLICIT_STEP_ROUTES",
        json.dumps(
            {
                "enabled": True,
                "steps": {"A:A0": "openrouter/anthropic/claude-opus-4-6"},
                "phases": {},
            }
        ),
    )

    with pytest.raises(RuntimeError, match="openrouter_strict_passthrough_unverified"):
        runner.resolve_effective_step_route("A", "A0", cfg, step_contract=contract)

    selected_route = ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY")
    with pytest.raises(ValueError, match="openrouter_strict_passthrough_unverified"):
        _batch_request(
            runner,
            provider=selected_route[0],
            model_id=selected_route[1],
            selected_route=selected_route,
            selected_route_entry={
                "provider": selected_route[0],
                "model_id": selected_route[1],
                "api_key_env": selected_route[2],
                "structured_output_mode": "json_schema",
                "strict_json_schema": True,
                "strict_passthrough_verified": False,
            },
            transport="openai_sdk",
        )


def test_gemini_strict_route_cannot_be_verified(tmp_path: Path) -> None:
    runner = _load_runner_module()
    evidence = runner._strict_passthrough_evidence_from_response_format(
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "gemini_strict_fixture",
                "strict": True,
                "schema": {"type": "object", "additionalProperties": False},
            },
        },
        evidence_source="constructed_request",
        provider="gemini",
        model_id="gemini-3.1-pro-preview",
        transport="sdk",
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
    )
    dirs = _dirs(runner, tmp_path)
    _write_raw(
        dirs,
        request_meta={
            runner.STRICT_PASSTHROUGH_RUNTIME_EVIDENCE_KEY: [evidence],
            "strict_route_attestations": [
                _strict_attestation(
                    provider="gemini",
                    model_id="gemini-3.1-pro-preview",
                    api_key_env="GEMINI_API_KEY",
                    transport="sdk",
                )
            ],
        },
    )

    payload = runner.write_strict_passthrough_attestations(dirs, "run-test", ["A"])

    row = payload["rows"][0]
    assert row["attestation_status"] == "FAILED"
    assert row["attestation_reason"] == "provider_not_strict_capable:gemini"
    assert row["strict_passthrough_verified"] is False

    selected_route = ("gemini", "gemini-3.1-pro-preview", "GEMINI_API_KEY")
    with pytest.raises(ValueError, match="provider_not_strict_capable:gemini"):
        _batch_request(
            runner,
            provider=selected_route[0],
            model_id=selected_route[1],
            selected_route=selected_route,
            selected_route_entry={
                "provider": selected_route[0],
                "model_id": selected_route[1],
                "api_key_env": selected_route[2],
                "structured_output_mode": "json_schema",
                "strict_json_schema": True,
                "strict_passthrough_verified": True,
            },
            transport="sdk",
        )
