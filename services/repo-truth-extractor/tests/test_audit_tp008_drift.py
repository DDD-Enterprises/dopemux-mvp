from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


def _load_audit_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "audit_tp008.py"
    spec = importlib.util.spec_from_file_location("audit_tp008", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_tp008_map(path: Path) -> None:
    path.write_text(
        """
tp008:
  policy:
    no_auto_transport_flips: true
    scope: "JSON-producing steps only"
  lanes:
    CE:
      primary: ["openrouter/openai/gpt-5.3-codex (strict)", "openrouter/openai/gpt-5.2 (strict)"]
      repair: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill_enabled: true
      repair_mode: targeted_then_envelope
    BULK_docs_general:
      primary: ["xai/grok-4-1-fast-reasoning", "xai/grok-4-1-fast-non-reasoning"]
      repair: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill_enabled_default: false
      repair_mode: targeted_only
    BULK_code_heavy:
      primary: ["xai/grok-code-fast-1", "xai/grok-4-1-fast-reasoning"]
      repair: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill_enabled_default: false
      repair_mode: targeted_only
    AGG:
      primary: ["openrouter/openai/gpt-5-mini (strict)"]
      repair: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill: ["openrouter/openai/gpt-5.2 (strict)"]
      sidefill_enabled_default: false
      repair_mode: envelope
  phases:
    A:
      CE: [A0]
      BULK: [A11]
    C:
      BULK_code_heavy: [C1]
    D:
      CE: [D0, D1]
      BULK_docs_general: [D2, D3, D4, D5]
    T:
      BULK_docs_general: [T2]
    Z:
      mixed_json_managed_CE: [Z0]
      markdown_only_excluded: [Z1]
  bulk_sidefill_opt_in_recommended:
    - D2
    - E4
    - T2
    - T4
    - T5
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_tp008_map_normalization_and_phase_d_corrections(tmp_path: Path) -> None:
    module = _load_audit_module()
    tp008_path = tmp_path / "tp008.yaml"
    _write_tp008_map(tp008_path)

    scope = module._load_repo_truth_scope(module.REPO_TRUTH_MAP_PATH)
    parsed = module._load_tp008_map(tp008_path, scope)

    # Decision-locked D corrections are applied regardless of input map bucket.
    assert parsed["steps"]["D:D2"]["lane_class"] == "CE"
    assert parsed["steps"]["D:D3"]["lane_class"] == "BULK_DOCS_GENERAL"
    assert parsed["steps"]["D:D4"]["lane_class"] == "AGG"
    assert parsed["steps"]["D:D5"]["lane_class"] == "AGG"

    # C1 is single-artifact BULK code-heavy => sidefill remains OFF.
    assert parsed["steps"]["C:C1"]["lane_class"] == "BULK_CODE_HEAVY"
    assert parsed["steps"]["C:C1"]["sidefill_enabled"] is False

    # T2 is explicit bulk opt-in and plural JSON in repo_truth_map => sidefill ON.
    assert parsed["steps"]["T:T2"]["sidefill_enabled"] is True


def test_static_drift_includes_scope_info_and_detects_d2_lane_drift(tmp_path: Path) -> None:
    module = _load_audit_module()
    tp008_path = tmp_path / "tp008.yaml"
    _write_tp008_map(tp008_path)

    scope = module._load_repo_truth_scope(module.REPO_TRUTH_MAP_PATH)
    model_map = module._load_model_map(module.MODEL_MAP_PATH)
    parsed = module._load_tp008_map(tp008_path, scope)

    drift = module._run_static_drift_audit(
        tp008_path=tp008_path,
        tp008_map=parsed,
        model_map_path=module.MODEL_MAP_PATH,
        model_map=model_map,
        repo_truth_path=module.REPO_TRUTH_MAP_PATH,
        repo_scope=scope,
        scope_excluded_as_info=True,
    )

    findings = drift["findings"]

    # A11 is outside repo_truth_map JSON-managed scope -> informational.
    assert any(
        row["finding_code"] == module.FINDING_INFO_NONEXISTENT and row["step_key"] == "A:A11"
        for row in findings
    )

    # D2 correction expects CE, current model_map lane is BULK_DOCS_GENERAL -> lane drift failure.
    assert any(
        row["finding_code"] == module.FINDING_FAIL_LANE
        and row["step_key"] == "D:D2"
        and row["severity"] == "fail"
        for row in findings
    )


def test_model_usage_classification_and_rollups(tmp_path: Path) -> None:
    module = _load_audit_module()
    tp008_path = tmp_path / "tp008.yaml"
    _write_tp008_map(tp008_path)

    scope = module._load_repo_truth_scope(module.REPO_TRUTH_MAP_PATH)
    parsed = module._load_tp008_map(tp008_path, scope)

    run_dir = tmp_path / "runs" / "sample_run"
    raw_dir = run_dir / "A_repo_control_plane" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    def _row(provider: str, model_id: str, part: str) -> None:
        payload = {
            "phase": "A",
            "step_id": "A0",
            "partition_id": part,
            "artifacts": [],
            "request_meta": {
                "provider": provider,
                "model_id": model_id,
                "routing_policy": "balanced_grok_openrouter",
                "no_auto_transport_flips": True,
            },
        }
        (raw_dir / f"A0__{part}.json").write_text(json.dumps(payload), encoding="utf-8")

    _row("openrouter", "openai/gpt-5.3-codex", "A_P0001")
    _row("openrouter", "openai/gpt-5.2", "A_P0002")
    _row("xai", "grok-4-1-fast-non-reasoning", "A_P0003")

    usage = module._run_model_usage_audit(
        run_dir=run_dir,
        tp008_map=parsed,
        repo_scope=scope,
        scope_excluded_as_info=True,
    )

    by_step = usage["summary"]["by_step"]["A:A0"]
    assert by_step["total"] == 3
    assert by_step["match"] == 1
    assert by_step["ladder_fallback_match"] == 1
    assert by_step["drift"] == 1

    by_lane = usage["summary"]["by_lane"]["CE"]
    assert by_lane["total"] == 3
    assert by_lane["drift"] == 1
