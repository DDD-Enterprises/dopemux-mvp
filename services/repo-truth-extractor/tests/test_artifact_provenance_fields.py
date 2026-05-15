from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Optional, Set

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location(
        "run_extraction_v5_artifact_provenance",
        module_path,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner):
    return runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced_grok_openrouter",
    )


def _fake_context(**_kwargs):  # type: ignore[no-untyped-def]
    return (
        "--- FILE: docs/example.md ---\n0001: line one\n0002: line two\n",
        {
            "files_included": 1,
            "files_skipped": 0,
            "context_bytes": 60,
            "redaction_hits": 0,
        },
    )


def _evidence(path: str = "docs/example.md") -> List[Dict[str, Any]]:
    return [{"path": path, "line_range": [1, 2], "excerpt": "0001: line one"}]


def _d1_artifact(
    runner,
    artifact_name: str,
    *,
    omit_fields: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    omit = set(omit_fields or [])
    contract = runner._step_contract_for("D", "D1")
    assert isinstance(contract, dict)
    artifact_meta = contract["artifacts"][artifact_name]
    item: Dict[str, Any] = {
        "id": f"{artifact_name}:item",
        "path": "docs/example.md",
        "line_range": [1, 2],
        "evidence": _evidence(),
    }
    required = set(artifact_meta.get("required_fields") or []) | set(
        artifact_meta.get("prompt_required_item_fields") or []
    )
    for field in sorted(required):
        if field in item or field in omit:
            continue
        item[field] = f"{artifact_name}:{field}"
    for field in omit:
        item.pop(field, None)
    return {
        "artifact_name": artifact_name,
        "payload": {
            "schema": artifact_meta["canonical_schema_id"],
            "items": [item],
        },
    }


def _d1_artifacts(
    runner,
    *,
    missing_artifacts: Optional[Set[str]] = None,
    omit_by_artifact: Optional[Dict[str, Iterable[str]]] = None,
) -> List[Dict[str, Any]]:
    missing = set(missing_artifacts or set())
    omitted = omit_by_artifact or {}
    contract = runner._step_contract_for("D", "D1")
    assert isinstance(contract, dict)
    return [
        _d1_artifact(
            runner,
            artifact_name,
            omit_fields=omitted.get(artifact_name),
        )
        for artifact_name in contract["artifact_order"]
        if artifact_name not in missing
    ]


def _run_d1(
    runner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake_call_llm,
) -> Dict[str, Any]:
    phase_dir = tmp_path / "D_docs_pipeline"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_D1_PROVENANCE.md"
    prompt.write_text("Goal: D1 strict output\n", encoding="utf-8")
    contract = runner._step_contract_for("D", "D1")
    assert contract is not None
    prompt_spec = runner.PromptSpec(
        step_id="D1",
        prompt_path=prompt,
        output_artifacts=tuple(contract["artifact_order"]),
        contract=contract,
    )
    partitions = [{"id": "D_P0001", "paths": ["docs/example.md"]}]
    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)
    stats = runner.execute_step_for_partitions(
        phase="D",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )
    payload = json.loads(
        (phase_dir / "raw" / "D1__D_P0001.json").read_text(encoding="utf-8")
    )
    payload["_stats"] = stats
    payload["_phase_dir"] = str(phase_dir)
    payload["_prompt_spec"] = prompt_spec
    payload["_partitions"] = partitions
    return payload


def _provenance(payload: Dict[str, Any]) -> Dict[str, Any]:
    meta = payload["request_meta"]
    provenance = meta["artifact_provenance"]
    assert meta["artifact_provenance_validation_errors"] == []
    assert provenance["schema_version"] == "rte_artifact_provenance_v1"
    return provenance


def test_primary_observed_artifacts_are_explicitly_primary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        return {
            "text": json.dumps({"artifacts": _d1_artifacts(runner)}),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    payload = _run_d1(runner, monkeypatch, tmp_path, fake_call_llm)
    provenance = _provenance(payload)

    assert provenance["field_records"] == []
    assert {
        record["provenance_kind"] for record in provenance["artifact_records"]
    } == {"primary_observed"}
    assert all(
        record["primary_observed_field_count"] > 0
        and record["derived_field_count"] == 0
        for record in provenance["artifact_records"]
    )


def test_deterministic_parse_repair_fields_are_marked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        return {
            "text": "prefix " + json.dumps({"artifacts": _d1_artifacts(runner)}),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    payload = _run_d1(runner, monkeypatch, tmp_path, fake_call_llm)
    provenance = _provenance(payload)

    kinds = {record["provenance_kind"] for record in provenance["field_records"]}
    assert "deterministic_parse_repair" in kinds
    assert all(
        record["request_meta_ref_if_any"] == "request_meta.response_parse_provenance"
        for record in provenance["field_records"]
        if record["provenance_kind"] == "deterministic_parse_repair"
    )


def test_deterministic_schema_repair_path_field_is_marked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    calls = {"count": 0}

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        return {
            "text": json.dumps(
                {
                    "artifacts": _d1_artifacts(
                        runner,
                        omit_by_artifact={"DOC_INDEX.partX.json": {"path"}},
                    )
                }
            ),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    payload = _run_d1(runner, monkeypatch, tmp_path, fake_call_llm)
    provenance = _provenance(payload)

    assert calls["count"] == 1
    assert payload["request_meta"]["repair_invocations"] == 1
    assert payload["request_meta"]["repair_successes"] == 1
    assert any(
        record["artifact_name"] == "DOC_INDEX.partX.json"
        and record["field_path"] == "payload.items[0].path"
        and record["provenance_kind"] == "deterministic_schema_repair"
        and record["original_value_present"] is False
        and record["replacement_value_present"] is True
        for record in provenance["field_records"]
    )


def test_sidefilled_fields_are_distinguishable_from_primary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    calls = {"count": 0}

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        artifacts = (
            _d1_artifacts(runner, missing_artifacts={"CAP_NOTICES.partX.json"})
            if calls["count"] == 1
            else [_d1_artifact(runner, "CAP_NOTICES.partX.json")]
        )
        return {
            "text": json.dumps({"artifacts": artifacts}),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    payload = _run_d1(runner, monkeypatch, tmp_path, fake_call_llm)
    provenance = _provenance(payload)

    assert calls["count"] == 2
    assert payload["request_meta"]["sidefill_invocations"] == 1
    sidefill_records = [
        record
        for record in provenance["field_records"]
        if record["provenance_kind"] == "sidefill"
    ]
    assert sidefill_records
    assert {record["artifact_name"] for record in sidefill_records} == {
        "CAP_NOTICES.partX.json"
    }
    assert any(
        record["artifact_name"] == "DOC_INDEX.partX.json"
        and record["provenance_kind"] == "primary_observed"
        for record in provenance["artifact_records"]
    )
    assert any(
        record["artifact_name"] == "CAP_NOTICES.partX.json"
        and record["provenance_kind"] == "sidefill"
        and record["derived_field_count"] > 0
        for record in provenance["artifact_records"]
    )

    phase_dir = Path(payload["_phase_dir"])
    runner.normalize_step(
        "D",
        payload["_prompt_spec"],
        phase_dir,
        payload["_partitions"],
        payload["_stats"],
    )
    rollup = json.loads(
        (phase_dir / "qa" / "D1_ARTIFACT_PROVENANCE.json").read_text(
            encoding="utf-8"
        )
    )
    assert rollup["summary"]["field_records_total"] >= len(sidefill_records)
    assert "sidefill" in rollup["summary"]["provenance_kinds"]


def test_provider_repair_fields_are_marked_with_provider_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    calls = {"count": 0}

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        artifacts = (
            _d1_artifacts(
                runner,
                omit_by_artifact={"DOC_INDEX.partX.json": {"line_range"}},
            )
            if calls["count"] == 1
            else [_d1_artifact(runner, "DOC_INDEX.partX.json")]
        )
        return {
            "text": json.dumps({"artifacts": artifacts}),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    payload = _run_d1(runner, monkeypatch, tmp_path, fake_call_llm)
    provenance = _provenance(payload)

    assert calls["count"] == 2
    assert payload["request_meta"]["repair_invocations"] >= 1
    provider_records = [
        record
        for record in provenance["field_records"]
        if record["provenance_kind"] == "provider_repair"
    ]
    assert provider_records
    assert {record["artifact_name"] for record in provider_records} == {
        "DOC_INDEX.partX.json"
    }
    assert all(
        record["repair_or_sidefill_provider_if_any"]
        and record["repair_or_sidefill_model_id_if_any"]
        for record in provider_records
    )
