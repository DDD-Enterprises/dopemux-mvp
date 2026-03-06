from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
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
        {"files_included": 1, "files_skipped": 0, "context_bytes": 60, "redaction_hits": 0},
    )


def _evidence(path: str, line_range: list[int]) -> list[dict]:
    return [{"path": path, "line_range": line_range, "excerpt": "0001: line one"}]


def test_d1_missing_artifact_sidefill_repairs_and_normalizes_schema_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "D_docs_pipeline"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_D1_TEST.md"
    prompt.write_text("Goal: D1 strict output\n", encoding="utf-8")
    contract = runner._step_contract_for("D", "D1")
    assert contract is not None
    outputs = tuple(contract["artifact_order"])
    prompt_spec = runner.PromptSpec(
        step_id="D1",
        prompt_path=prompt,
        output_artifacts=outputs,
        contract=contract,
    )
    partitions = [{"id": "D_P0001", "paths": ["docs/example.md"]}]

    calls = {"count": 0, "response_format_used": 0}

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        if kwargs.get("response_format_override"):
            calls["response_format_used"] += 1
        common_meta = {
            "failure_type": None,
            "status_code": 200,
            "response_received": True,
            "response_summary": {"finish_reason": "STOP"},
        }
        if calls["count"] == 1:
            payload = {
                "artifacts": [
                    {
                        "artifact_name": "DOC_INDEX.partX.json",
                        "payload": {
                            "schema": "doc_index@v1",
                            "items": [
                                {
                                    "id": "DOC_INDEX:item",
                                    "path": "docs/example.md",
                                    "line_range": [1, 2],
                                    "name": "Example",
                                    "kind": "guide",
                                    "evidence": _evidence("docs/example.md", [1, 2]),
                                }
                            ],
                        },
                    },
                    {
                        "artifact_name": "DOC_CONTRACT_CLAIMS.partX.json",
                        "payload": {
                            "schema": "DOC_CONTRACT_CLAIMS@v1",
                            "items": [
                                {
                                    "id": "DOC_CONTRACT_CLAIMS:item",
                                    "path": "docs/example.md",
                                    "line_range": [1, 2],
                                    "evidence": _evidence("docs/example.md", [1, 2]),
                                }
                            ],
                        },
                    },
                    {
                        "artifact_name": "DOC_BOUNDARIES.partX.json",
                        "payload": {
                            "schema": "DOC_BOUNDARIES@v1",
                            "items": [
                                {
                                    "id": "DOC_BOUNDARIES:item",
                                    "path": "docs/example.md",
                                    "line_range": [1, 2],
                                    "evidence": _evidence("docs/example.md", [1, 2]),
                                }
                            ],
                        },
                    },
                    {
                        "artifact_name": "DOC_SUPERSESSION.partX.json",
                        "payload": {
                            "schema": "DOC_SUPERSESSION@v1",
                            "items": [
                                {
                                    "id": "DOC_SUPERSESSION:item",
                                    "path": "docs/example.md",
                                    "line_range": [1, 2],
                                    "evidence": _evidence("docs/example.md", [1, 2]),
                                }
                            ],
                        },
                    },
                ]
            }
            return {"text": json.dumps(payload), "meta": dict(common_meta)}

        payload = {
            "artifacts": [
                {
                    "artifact_name": "CAP_NOTICES.partX.json",
                    "payload": {
                        "schema": "cap_notices@v1",
                        "items": [
                            {
                                "id": "CAP_NOTICES:item",
                                "path": "docs/example.md",
                                "line_range": [1, 2],
                                "evidence": _evidence("docs/example.md", [1, 2]),
                            }
                        ],
                    },
                }
            ]
        }
        return {"text": json.dumps(payload), "meta": dict(common_meta)}

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="D",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["ok"] == 1
    assert stats["failed"] == 0
    assert stats["sidefill_invocations"] == 1
    assert "CAP_NOTICES.partX.json" in stats["sidefill_filled_artifacts"]
    assert calls["response_format_used"] >= 2

    payload = json.loads((phase_dir / "raw" / "D1__D_P0001.json").read_text(encoding="utf-8"))
    request_meta = payload["request_meta"]
    artifacts = payload["artifacts"]
    assert [row["artifact_name"] for row in artifacts] == list(outputs)
    assert request_meta["schema_gate_passed"] is True
    assert request_meta["final_contract_status"] == "pass"
    assert request_meta["sidefill_invocations"] == 1
    assert "CAP_NOTICES.partX.json" in request_meta["sidefill_filled_artifacts"]
    assert any(
        row.get("artifact_name") == "DOC_INDEX.partX.json" and row.get("to") == "DOC_INDEX@v1"
        for row in request_meta.get("schema_id_normalizations", [])
    )


def test_d1_targeted_repair_fixes_missing_line_range_without_sidefill(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "D_docs_pipeline"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_D1_TARGETED.md"
    prompt.write_text("Goal: D1 strict output\n", encoding="utf-8")
    contract = runner._step_contract_for("D", "D1")
    assert contract is not None
    outputs = tuple(contract["artifact_order"])
    prompt_spec = runner.PromptSpec(
        step_id="D1",
        prompt_path=prompt,
        output_artifacts=outputs,
        contract=contract,
    )
    partitions = [{"id": "D_P0001", "paths": ["docs/example.md"]}]

    calls = {"count": 0}

    def _item(item_id: str, *, include_line_range: bool = True) -> dict:
        row = {
            "id": item_id,
            "path": "docs/example.md",
            "evidence": _evidence("docs/example.md", [1, 2]),
        }
        if include_line_range:
            row["line_range"] = [1, 2]
        return row

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        meta = {
            "failure_type": None,
            "status_code": 200,
            "response_received": True,
            "response_summary": {"finish_reason": "STOP"},
        }
        if calls["count"] == 1:
            payload = {
                "artifacts": [
                    {
                        "artifact_name": "DOC_INDEX.partX.json",
                        "payload": {
                            "schema": "DOC_INDEX@v1",
                            "items": [
                                {
                                    **_item("DOC_INDEX:item", include_line_range=False),
                                    "name": "Example",
                                    "kind": "guide",
                                }
                            ],
                        },
                    },
                    {
                        "artifact_name": "DOC_CONTRACT_CLAIMS.partX.json",
                        "payload": {"schema": "DOC_CONTRACT_CLAIMS@v1", "items": [_item("DOC_CONTRACT_CLAIMS:item")]},
                    },
                    {
                        "artifact_name": "DOC_BOUNDARIES.partX.json",
                        "payload": {"schema": "DOC_BOUNDARIES@v1", "items": [_item("DOC_BOUNDARIES:item")]},
                    },
                    {
                        "artifact_name": "DOC_SUPERSESSION.partX.json",
                        "payload": {"schema": "DOC_SUPERSESSION@v1", "items": [_item("DOC_SUPERSESSION:item")]},
                    },
                    {
                        "artifact_name": "CAP_NOTICES.partX.json",
                        "payload": {"schema": "CAP_NOTICES@v1", "items": [_item("CAP_NOTICES:item")]},
                    },
                ]
            }
            return {"text": json.dumps(payload), "meta": dict(meta)}

        payload = {
            "artifacts": [
                {
                    "artifact_name": "DOC_INDEX.partX.json",
                    "payload": {
                        "schema": "DOC_INDEX@v1",
                        "items": [
                            {
                                **_item("DOC_INDEX:item"),
                                "name": "Example",
                                "kind": "guide",
                            }
                        ],
                    },
                }
            ]
        }
        return {"text": json.dumps(payload), "meta": dict(meta)}

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="D",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["ok"] == 1
    assert stats["failed"] == 0
    assert stats["repair_invocations"] >= 1
    assert stats["repair_successes"] >= 1
    assert stats["sidefill_invocations"] == 0
    assert calls["count"] == 2

    payload = json.loads((phase_dir / "raw" / "D1__D_P0001.json").read_text(encoding="utf-8"))
    request_meta = payload["request_meta"]
    assert request_meta["schema_gate_passed"] is True
    assert request_meta["final_contract_status"] == "pass"
    assert request_meta["repair_invocations"] >= 1
    assert request_meta["sidefill_invocations"] == 0
