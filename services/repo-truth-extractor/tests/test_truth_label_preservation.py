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
        "run_extraction_v5_truth_labels",
        module_path,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_truth_labels_module():
    root = Path(__file__).resolve().parents[3]
    module_path = (
        root / "services" / "repo-truth-extractor" / "lib" / "truth_labels.py"
    )
    spec = importlib.util.spec_from_file_location("truth_labels_test_module", module_path)
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


def _truth_fields(label: str) -> Dict[str, Any]:
    if label == "UNKNOWN":
        return {
            "truth_label": "UNKNOWN",
            "label_source": "primary_extraction",
            "label_reason": "not established by source excerpt",
            "unknown_reason_if_any": "source excerpt does not establish value",
            "evidence_refs": ["fixture:docs/example.md:1-2"],
        }
    if label == "CONFLICTING":
        return {
            "truth_label": "CONFLICTING",
            "label_source": "primary_extraction",
            "label_reason": "two source-backed candidates conflict",
            "conflicting_values_if_any": ["runtime:path_a", "runtime:path_b"],
            "evidence_refs": ["fixture:docs/example.md:1-2"],
        }
    return {
        "truth_label": label,
        "label_source": "runtime_source",
        "label_reason": "source excerpt establishes value",
        "evidence_refs": ["fixture:docs/example.md:1-2"],
    }


def _d1_artifact(
    runner,
    artifact_name: str,
    *,
    omit_fields: Optional[Iterable[str]] = None,
    truth_label: Optional[str] = None,
    truth_overrides: Optional[Dict[str, Any]] = None,
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
    if truth_label:
        item.update(_truth_fields(truth_label))
    if truth_overrides:
        item.update(truth_overrides)
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
    truth_by_artifact: Optional[Dict[str, str]] = None,
    truth_overrides_by_artifact: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    missing = set(missing_artifacts or set())
    omitted = omit_by_artifact or {}
    truth_labels = truth_by_artifact or {}
    truth_overrides = truth_overrides_by_artifact or {}
    contract = runner._step_contract_for("D", "D1")
    assert isinstance(contract, dict)
    return [
        _d1_artifact(
            runner,
            artifact_name,
            omit_fields=omitted.get(artifact_name),
            truth_label=truth_labels.get(artifact_name),
            truth_overrides=truth_overrides.get(artifact_name),
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
    prompt = tmp_path / "PROMPT_D1_TRUTH_LABELS.md"
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


def _doc_index_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    for artifact in payload["artifacts"]:
        if artifact["artifact_name"] == "DOC_INDEX.partX.json":
            return artifact["payload"]["items"][0]
    raise AssertionError("DOC_INDEX.partX.json not found")


def _truth_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    meta = payload["request_meta"]
    truth_payload = meta["truth_label_preservation"]
    assert meta["truth_label_preservation_validation_errors"] == []
    assert truth_payload["schema_version"] == "rte_truth_label_preservation_v1"
    return truth_payload


def test_unknown_survives_deterministic_parse_repair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    calls = {"count": 0}

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        return {
            "text": "prefix " + json.dumps(
                {
                    "artifacts": _d1_artifacts(
                        runner,
                        truth_by_artifact={"DOC_INDEX.partX.json": "UNKNOWN"},
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
    item = _doc_index_item(payload)
    truth_payload = _truth_payload(payload)

    assert calls["count"] == 1
    assert item["truth_label"] == "UNKNOWN"
    assert item["unknown_reason_if_any"] == "source excerpt does not establish value"
    assert any(
        record["truth_label"] == "UNKNOWN"
        and record["artifact_name"] == "DOC_INDEX.partX.json"
        and record["provenance_kind"] == "deterministic_parse_repair"
        for record in truth_payload["records"]
    )


def test_conflicting_survives_deterministic_schema_repair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        return {
            "text": json.dumps(
                {
                    "artifacts": _d1_artifacts(
                        runner,
                        omit_by_artifact={"DOC_INDEX.partX.json": {"path"}},
                        truth_by_artifact={"DOC_INDEX.partX.json": "CONFLICTING"},
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
    item = _doc_index_item(payload)
    truth_payload = _truth_payload(payload)

    assert payload["request_meta"]["repair_invocations"] == 1
    assert item["path"] == "docs/example.md"
    assert item["truth_label"] == "CONFLICTING"
    assert item["conflicting_values_if_any"] == ["runtime:path_a", "runtime:path_b"]
    assert any(
        record["truth_label"] == "CONFLICTING"
        and record["artifact_name"] == "DOC_INDEX.partX.json"
        for record in truth_payload["records"]
    )


def test_provider_repair_cannot_upgrade_unknown_without_source_backed_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    calls = {"count": 0}

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        if calls["count"] == 1:
            artifacts = _d1_artifacts(
                runner,
                omit_by_artifact={"DOC_INDEX.partX.json": {"line_range"}},
                truth_by_artifact={"DOC_INDEX.partX.json": "UNKNOWN"},
            )
        else:
            artifacts = [
                _d1_artifact(
                    runner,
                    "DOC_INDEX.partX.json",
                    truth_label="OBSERVED",
                    truth_overrides={
                        "label_source": "provider_repair_candidate",
                        "label_reason": "candidate repair proposed clean value",
                    },
                )
            ]
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
    item = _doc_index_item(payload)
    truth_payload = _truth_payload(payload)

    assert calls["count"] == 2
    assert payload["request_meta"]["repair_invocations"] >= 1
    assert item["truth_label"] == "UNKNOWN"
    blocked = [
        record
        for record in truth_payload["records"]
        if record["transition_action"] == "blocked_protected_label_upgrade"
    ]
    assert blocked
    assert blocked[0]["truth_label"] == "UNKNOWN"
    assert blocked[0]["attempted_truth_label_if_any"] == "OBSERVED"
    assert blocked[0]["provenance_kind"] == "provider_repair"


def test_sidefill_and_prescan_candidates_cannot_hide_conflicting_or_unknown() -> None:
    truth_labels = _load_truth_labels_module()
    original = [
        {
            "artifact_name": "MERGE_QA.json",
            "payload": {
                "items": [
                    {
                        "id": "row-1",
                        "truth_label": "CONFLICTING",
                        "conflicting_values_if_any": ["left", "right"],
                        "evidence_refs": ["fixture:source:1-2"],
                    }
                ]
            },
        }
    ]
    sidefill_candidate = [
        {
            "artifact_name": "MERGE_QA.json",
            "payload": {
                "items": [
                    {
                        "id": "row-1",
                        "truth_label": "OBSERVED",
                        "label_source": "sidefill_candidate",
                    }
                ]
            },
        }
    ]

    preserved, records = truth_labels.preserve_protected_truth_labels(
        original_artifacts=original,
        candidate_artifacts=sidefill_candidate,
        provenance_kind="sidefill",
        source_lane="sidefill",
        source_phase="T",
        source_step_id="T9",
        source_partition_id="T_P0001",
        reason_code="sidefill_candidate_conflict",
        generated_at="2026-05-15T00:00:00Z",
    )

    item = preserved[0]["payload"]["items"][0]
    assert item["truth_label"] == "CONFLICTING"
    assert item["conflicting_values_if_any"] == ["left", "right"]
    assert records[0]["transition_action"] == "blocked_protected_label_upgrade"
    assert records[0]["provenance_kind"] == "sidefill"

    drop_candidate = [
        {
            "artifact_name": "MERGE_QA.json",
            "payload": {"items": [{"id": "row-1", "label_source": "sidefill"}]},
        }
    ]
    preserved_drop, drop_records = truth_labels.preserve_protected_truth_labels(
        original_artifacts=original,
        candidate_artifacts=drop_candidate,
        provenance_kind="sidefill",
        source_lane="sidefill",
        source_phase="T",
        source_step_id="T9",
        source_partition_id="T_P0001",
        reason_code="sidefill_candidate_drop",
        generated_at="2026-05-15T00:00:00Z",
    )
    assert preserved_drop[0]["payload"]["items"][0]["truth_label"] == "CONFLICTING"
    assert drop_records[0]["transition_action"] == "blocked_protected_label_drop"

    prescan_candidate = json.loads(json.dumps(sidefill_candidate))
    prescan_candidate[0]["payload"]["items"][0]["truth_label"] = "OBSERVED"
    preserved_prescan, prescan_records = truth_labels.preserve_protected_truth_labels(
        original_artifacts=[
            {
                "artifact_name": "MERGE_QA.json",
                "payload": {
                    "items": [
                        {
                            "id": "row-1",
                            "truth_label": "UNKNOWN",
                            "unknown_reason_if_any": "prescan is advisory only",
                            "evidence_refs": ["fixture:prescan:advisory"],
                        }
                    ]
                },
            }
        ],
        candidate_artifacts=prescan_candidate,
        provenance_kind="prescan_derived",
        source_lane="prescan",
        source_phase="P",
        source_step_id="P4",
        source_partition_id="P_P0001",
        reason_code="prescan_advisory_candidate",
        generated_at="2026-05-15T00:00:00Z",
    )
    assert preserved_prescan[0]["payload"]["items"][0]["truth_label"] == "UNKNOWN"
    assert prescan_records[0]["provenance_kind"] == "prescan_derived"


def test_comparison_truth_labels_are_non_authoritative(tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_phase"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    results = [
        {
            "partition_id": "A_P0001",
            "artifacts": [
                {
                    "artifact_name": "COMPARE.json",
                    "payload": {
                        "items": [
                            {
                                "id": "row-1",
                                "truth_label": "UNKNOWN",
                                "unknown_reason_if_any": "comparison lane only",
                                "evidence_refs": ["fixture:comparison"],
                            }
                        ]
                    },
                }
            ],
            "request_meta": {"lane": "comparison", "authoritative": False},
        }
    ]

    updated = runner._attach_comparison_provenance_to_results(
        phase="A",
        step_id="A9",
        phase_dir=phase_dir,
        provider="xai",
        model="grok-4.20-beta",
        results=results,
    )
    meta = updated[0]["request_meta"]
    truth_payload = meta["truth_label_preservation"]
    record = truth_payload["records"][0]

    assert meta["authoritative"] is False
    assert record["truth_label"] == "UNKNOWN"
    assert record["provenance_kind"] == "comparison"
    assert record["authoritative"] is False


def test_primary_observed_truth_label_is_not_degraded_and_normalization_rolls_up(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        return {
            "text": json.dumps(
                {
                    "artifacts": _d1_artifacts(
                        runner,
                        truth_by_artifact={"DOC_INDEX.partX.json": "OBSERVED"},
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
    item = _doc_index_item(payload)
    truth_payload = _truth_payload(payload)

    assert item["truth_label"] == "OBSERVED"
    assert truth_payload["summary"]["protected_records_total"] == 0

    phase_dir = Path(payload["_phase_dir"])
    runner.normalize_step(
        "D",
        payload["_prompt_spec"],
        phase_dir,
        payload["_partitions"],
        payload["_stats"],
    )
    rollup = json.loads(
        (phase_dir / "qa" / "D1_TRUTH_LABEL_PRESERVATION.json").read_text(
            encoding="utf-8"
        )
    )
    qa = json.loads((phase_dir / "qa" / "D1_QA.json").read_text(encoding="utf-8"))
    assert rollup["summary"]["records_total"] >= 1
    assert rollup["summary"]["labels"]["OBSERVED"] >= 1
    assert qa["truth_label_preservation"]["records_total"] >= 1
