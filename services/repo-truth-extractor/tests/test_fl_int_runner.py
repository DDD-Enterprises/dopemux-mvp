from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

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


def test_normalize_step_payload_accepts_artifact_named_f0_envelope() -> None:
    module = load_run_module()
    payload = module.normalize_step_payload(
        "F0",
        {
            "DESIGN_CLAIMS_RAW": [],
        },
    )
    assert payload["status"] == "OK"
    assert payload["missing_evidence"] == []
    assert payload["design_claims_raw"] == {
        "schema": "DESIGN_CLAIMS_RAW@v1",
        "items": [],
    }


def test_normalize_step_payload_derives_f4_meta_from_prior_outputs() -> None:
    module = load_run_module()
    payload = module.normalize_step_payload(
        "F4",
        {
            "canonical_design": {
                "canonical_design_md": "# Canonical Design\n\n## Current State\n",
                "schema": "CANONICAL_DESIGN@v1",
            },
            "status": "OK",
        },
        {
            "F1": {
                "design_claims_classified": {
                    "schema": "DESIGN_CLAIMS_CLASSIFIED@v1",
                    "items": [
                        {"id": "c1", "evidence_class": "REPO_PROVEN_CURRENT"},
                        {"id": "c2", "evidence_class": "HISTORICAL"},
                        {"id": "c3", "evidence_class": "TARGET"},
                        {"id": "c4", "evidence_class": "UNKNOWN"},
                    ],
                }
            },
            "F2": {
                "design_contradictions": {
                    "schema": "DESIGN_CONTRADICTIONS@v1",
                    "items": [
                        {"id": "k1", "status": "unresolved"},
                    ],
                }
            },
        },
    )
    assert payload["canonical_design_markdown"].startswith("# Canonical Design")
    assert payload["meta"]["contradictions"] == [{"contradiction_id": "k1", "status": "unresolved"}]
    assert payload["meta"]["statistics"] == {
        "repo_proven_current_count": 1,
        "historical_count": 1,
        "target_count": 1,
        "unknown_count": 1,
    }
