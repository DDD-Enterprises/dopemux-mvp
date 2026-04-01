from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, Optional

import pytest

from _fl_int_helpers import build_fl_int_run_root, ensure_service_root_on_path, fake_fl_int_payload, load_run_module


def test_run_fl_int_writes_outputs_and_preserves_pm_plane(tmp_path: Path) -> None:
    module = load_run_module()
    run_root = build_fl_int_run_root(tmp_path)
    out_root = tmp_path / "postprocess"
    seen_steps = []

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        assert "{{FL_INT_INPUT_JSON}}" not in rendered_prompt
        assert "{{PRIOR_OUTPUTS_JSON}}" not in rendered_prompt
        seen_steps.append(step.step_id)
        return {"payload": fake_fl_int_payload(step.step_id)}

    summary = module.run_fl_int(run_root, dry_run=False, out_root=out_root, prompt_executor=fake_executor)
    assert summary["status"] == "OK"
    assert seen_steps[0] == "F0"
    assert seen_steps.count("F0") == summary["batch_counts"]["F0"]
    assert seen_steps.count("L0") == summary["batch_counts"]["L0"]
    filtered_steps = [step for index, step in enumerate(seen_steps) if index == 0 or step != seen_steps[index - 1]]
    assert filtered_steps == ["F0", "F1", "F2", "F4", "L0", "L1", "L3", "L4"]

    result_root = out_root
    assert (result_root / "FL_INT_MACHINE_SUMMARY.json").exists()
    assert (result_root / "FL_INT_SUMMARY.md").exists()
    assert (result_root / "FL_INT_CHECKLIST.md").exists()
    assert (result_root / "FL_INT_FAIL_CLOSED.md").exists()
    assert (result_root / "DESIGN_CLAIMS_RAW.json").exists()
    assert (result_root / "DESIGN_CLAIMS_CLASSIFIED.json").exists()
    assert (result_root / "DESIGN_CONTRADICTIONS.json").exists()
    assert (result_root / "CANONICAL_DESIGN.md").exists()
    assert (result_root / "CANONICAL_DESIGN_META.json").exists()
    assert (result_root / "FEATURE_CANDIDATES_RAW.json").exists()
    assert (result_root / "FEATURE_CANDIDATES_NORMALIZED.json").exists()
    assert (result_root / "FEATURE_MERGE_LOG.json").exists()
    assert (result_root / "FEATURE_LEDGER_ROUTING.json").exists()
    assert (result_root / "MASTER_FEATURE_LEDGER.json").exists()
    assert not (result_root / "FEATURE_LEDGER_STATUS.json").exists()
    assert (result_root / "F0_INPUT_REDUCTION.json").exists()
    assert (result_root / "L0_INPUT_REDUCTION.json").exists()
    assert (result_root / "raw" / "F0_BATCH_PLAN.json").exists()
    assert (result_root / "raw" / "L0_BATCH_PLAN.json").exists()

    routing = json.loads((result_root / "FEATURE_LEDGER_ROUTING.json").read_text(encoding="utf-8"))
    buckets = {row["routing_bucket"] for row in routing["items"]}
    assert buckets == {
        "canonical",
        "historical_appendix",
        "uncertain_appendix",
        "excluded_non_feature",
    }

    meta = json.loads((result_root / "CANONICAL_DESIGN_META.json").read_text(encoding="utf-8"))
    ledger = json.loads((result_root / "MASTER_FEATURE_LEDGER.json").read_text(encoding="utf-8"))
    assert meta["contradictions"] == [{"contradiction_id": "FL-1", "status": "unresolved"}]
    assert ledger["contradictions"] == [{"contradiction_id": "FL-1", "status": "unresolved"}]
    assert ledger["statistics"]["by_plane"]["pm"] > 0


def test_run_fl_int_fails_closed_on_invalid_step_payload(tmp_path: Path) -> None:
    module = load_run_module()
    run_root = build_fl_int_run_root(tmp_path)

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        del rendered_prompt, schema, prior_outputs
        if step.step_id == "F0":
            return {"payload": {"status": "OK", "missing_evidence": []}}
        return {"payload": fake_fl_int_payload(step.step_id)}

    with pytest.raises(ValueError):
        module.run_fl_int(run_root, dry_run=False, prompt_executor=fake_executor)


def test_run_fl_int_dry_run_via_cli(tmp_path: Path) -> None:
    root = ensure_service_root_on_path()
    script = root / "services" / "repo-truth-extractor" / "run_fl_int.py"
    run_root = build_fl_int_run_root(tmp_path)
    result = subprocess.run(
        [sys.executable, str(script), "--run-root", str(run_root), "--dry-run"],
        cwd=str(root),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "DRY_RUN"
    assert (run_root / "postprocess" / "fl_int_v1" / "FL_INT_MACHINE_SUMMARY.json").exists()


def test_run_fl_int_writes_f0_trace_artifact(tmp_path: Path) -> None:
    module = load_run_module()
    run_root = build_fl_int_run_root(tmp_path)
    out_root = tmp_path / "postprocess"

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        del rendered_prompt, schema
        observer = prior_outputs.get("__fl_int_diag_observer__")
        if step.step_id == "F0" and callable(observer):
            route = ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY")
            request_meta = {
                "provider": route[0],
                "model_id": route[1],
                "api_key_env_requested": route[2],
                "status_code": 200,
                "response_received": True,
                "timeout_seconds": 180,
            }
            observer("provider_call_start", {"route": route, "request_meta": request_meta})
            observer(
                "provider_call_return",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 128,
                },
            )
            observer(
                "normalize_start",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 128,
                },
            )
            observer(
                "normalize_return",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 128,
                },
            )
        return {"payload": fake_fl_int_payload(step.step_id)}

    summary = module.run_fl_int(run_root, dry_run=False, out_root=out_root, prompt_executor=fake_executor)
    assert summary["status"] == "OK"
    trace = json.loads((out_root / "raw" / "F0_BATCH_000_TRACE.json").read_text(encoding="utf-8"))
    stages = [row["stage"] for row in trace["stage_history"]]
    assert trace["stage"] == "artifact_write_success"
    assert stages[:5] == [
        "batch_start",
        "provider_call_start",
        "provider_call_return",
        "normalize_start",
        "normalize_return",
    ]
    assert "schema_validate_start" in stages
    assert "schema_validate_return" in stages
    assert stages[-2:] == ["artifact_write_start", "artifact_write_success"]


def test_run_fl_int_writes_failure_artifacts_on_invalid_f0_payload(tmp_path: Path) -> None:
    module = load_run_module()
    run_root = build_fl_int_run_root(tmp_path)
    out_root = tmp_path / "postprocess"

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        del rendered_prompt, schema
        if step.step_id != "F0":
            return {"payload": fake_fl_int_payload(step.step_id)}
        observer = prior_outputs.get("__fl_int_diag_observer__")
        route = ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY")
        request_meta = {
            "provider": route[0],
            "model_id": route[1],
            "api_key_env_requested": route[2],
            "status_code": 200,
            "failure_type": "invalid_json",
            "response_received": True,
            "provider_error_reason": None,
        }
        if callable(observer):
            observer("provider_call_start", {"route": route, "request_meta": request_meta})
            observer(
                "provider_call_return",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 9,
                },
            )
            observer(
                "normalize_start",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 9,
                },
            )
        return {
            "payload": None,
            "request_meta": request_meta,
            "response_text": "{not json",
            "route": route,
        }

    with pytest.raises(RuntimeError, match="failure_type=invalid_json"):
        module.run_fl_int(run_root, dry_run=False, out_root=out_root, prompt_executor=fake_executor)

    failure = json.loads((out_root / "raw" / "F0_BATCH_000_FAILURE.json").read_text(encoding="utf-8"))
    machine = json.loads((out_root / "FL_INT_MACHINE_SUMMARY.json").read_text(encoding="utf-8"))
    response_text = (out_root / "raw" / "F0_BATCH_000_RESPONSE.txt").read_text(encoding="utf-8")
    assert failure["terminal_stage"] == "normalize_start"
    assert failure["failure_type"] == "invalid_json"
    assert response_text == "{not json"
    assert machine["status"] == "FAILED"
    assert machine["failed_step"] == "F0"
    assert machine["failed_batch"] == "F0_BATCH_000"


def test_run_fl_int_f0_timeout_writes_failure_and_aborts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_run_module()
    run_root = build_fl_int_run_root(tmp_path)
    out_root = tmp_path / "postprocess"
    ticks = iter([0.0, 0.1, 0.2, 0.3, 2.6, 2.7, 2.8, 2.9, 3.0])
    last_tick = 3.0

    def fake_monotonic() -> float:
        nonlocal last_tick
        try:
            last_tick = next(ticks)
        except StopIteration:
            pass
        return last_tick

    monkeypatch.setattr(module.time, "monotonic", fake_monotonic)

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        del rendered_prompt, schema
        if step.step_id != "F0":
            return {"payload": fake_fl_int_payload(step.step_id)}
        observer = prior_outputs.get("__fl_int_diag_observer__")
        route = ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY")
        request_meta = {
            "provider": route[0],
            "model_id": route[1],
            "api_key_env_requested": route[2],
            "status_code": 200,
            "response_received": True,
            "timeout_seconds": 180,
        }
        if callable(observer):
            observer("provider_call_start", {"route": route, "request_meta": request_meta})
            observer(
                "provider_call_return",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 128,
                },
            )
            observer(
                "normalize_start",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 128,
                },
            )
            observer(
                "normalize_return",
                {
                    "route": route,
                    "request_meta": request_meta,
                    "response_received": True,
                    "response_text_chars": 128,
                },
            )
        return {"payload": fake_fl_int_payload("F0"), "request_meta": request_meta, "response_text": "{\"ok\":true}", "route": route}

    with pytest.raises(RuntimeError, match="exceeded timeout"):
        module.run_fl_int(
            run_root,
            dry_run=False,
            out_root=out_root,
            prompt_executor=fake_executor,
            f0_batch_timeout_seconds=1,
        )

    failure = json.loads((out_root / "raw" / "F0_BATCH_000_FAILURE.json").read_text(encoding="utf-8"))
    machine = json.loads((out_root / "FL_INT_MACHINE_SUMMARY.json").read_text(encoding="utf-8"))
    assert failure["terminal_stage"] == "provider_call_timeout"
    assert failure["failure_type"] == "timeout"
    assert machine["status"] == "FAILED"
    assert machine["failed_batch"] == "F0_BATCH_000"


def test_normalize_step_payload_coerces_f0_row_aliases_and_evidence() -> None:
    module = load_run_module()
    payload = module.normalize_step_payload(
        "F0",
        {
            "status": "OK",
            "missing_evidence": [],
            "DESIGN_CLAIMS_RAW.json": [
                {
                    "id": "claim-1",
                    "path": "docs/architecture.md",
                    "line_range": [10, 12],
                    "claim": "Architecture claim",
                    "source": "DOC_CONTRACT_CLAIMS.part0001.json",
                    "evidence": ["excerpt one", "excerpt two"],
                },
                {
                    "id": "claim-2",
                    "path": "docs/runtime.md",
                    "line_range": [20, 21],
                    "name": "Runtime claim",
                    "evidence": "single excerpt",
                },
            ],
        },
    )

    wrapped = payload["design_claims_raw"]
    assert wrapped["schema"] == "DESIGN_CLAIMS_RAW@v1"
    first, second = wrapped["items"]
    assert first["claim_text"] == "Architecture claim"
    assert first["source_artifact"] == "DOC_CONTRACT_CLAIMS.part0001.json"
    assert first["evidence"] == [
        {
            "path": "docs/architecture.md",
            "line_range": [10, 12],
            "excerpt": "excerpt one",
        },
        {
            "path": "docs/architecture.md",
            "line_range": [10, 12],
            "excerpt": "excerpt two",
        },
    ]
    assert second["claim_text"] == "Runtime claim"
    assert second["source_artifact"] == "unspecified"
    assert second["plane"] == "unspecified"
    assert second["evidence"] == [
        {
            "path": "docs/runtime.md",
            "line_range": [20, 21],
            "excerpt": "single excerpt",
        }
    ]
