"""Tests for TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001: comparison lane isolation.

These tests verify:
- Comparison disabled → no comparison execution
- Comparison enabled on eligible step → separate artifacts created
- Canonical outputs unchanged when comparison runs
- Comparison route metadata stored correctly
- Comparison uses same normalization/validation pipeline
- Comparison failure is non-blocking (canonical still succeeds)
- Invalid step → clear error with eligible step list
- Comparison resume isolation (independent of canonical)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Module loader helpers
# ---------------------------------------------------------------------------

def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner, *, compare_mode=None, compare_model=None,
              compare_provider=None, compare_steps=None):
    """Build a minimal RunnerConfig with optional comparison fields."""
    kwargs = dict(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10_000,
        max_request_bytes=200_000,
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
        routing_policy="cost",
        disable_escalation=True,
        escalation_max_hops=1,
    )
    # Inject comparison fields only if the dataclass has them
    if hasattr(runner.RunnerConfig, "__dataclass_fields__"):
        fields = runner.RunnerConfig.__dataclass_fields__
        if "compare_mode" in fields:
            kwargs["compare_mode"] = compare_mode
        if "compare_model" in fields:
            kwargs["compare_model"] = compare_model
        if "compare_provider" in fields:
            kwargs["compare_provider"] = compare_provider
        if "compare_steps" in fields:
            kwargs["compare_steps"] = (
                tuple(compare_steps.split(",")) if isinstance(compare_steps, str)
                else compare_steps
            )
    return runner.RunnerConfig(**kwargs)


def _make_prompt_spec(runner, step_id: str, tmp_path: Path, output_artifacts=("OUT.json",)):
    prompt = tmp_path / f"PROMPT_{step_id}_TEST.md"
    prompt.write_text(f"Goal: {output_artifacts[0]}\n", encoding="utf-8")
    return runner.PromptSpec(
        step_id=step_id,
        prompt_path=prompt,
        output_artifacts=output_artifacts,
    )


def _make_partitions():
    return [{"id": "A_P0001", "paths": ["/tmp/p1"]}]


def _fake_context(**kwargs):  # type: ignore[no-untyped-def]
    return (
        "PARTITION_PATH=/tmp/p1",
        {"files_included": 1, "files_skipped": 0, "context_bytes": 20, "redaction_hits": 0},
    )


def _first_nonstricteligible(runner) -> str:
    """Return a known non-strict eligible step (BULK_DOCS_GENERAL, not AGG).

    A9, R9, S9 are non-strict. A9 is chosen as the stable test default.
    Using a non-strict step avoids contract-gate failures with fake payloads.
    """
    non_strict = {"A9", "R9", "S9"}
    available = non_strict & runner.COMPARISON_ELIGIBLE_STEPS
    # Prefer A9 for test stability; fall back to first sorted available
    if "A9" in available:
        return "A9"
    return sorted(available)[0] if available else sorted(runner.COMPARISON_ELIGIBLE_STEPS)[0]


def _success_payload(step_id: str, partition_id: str) -> Dict[str, Any]:
    return {
        "phase": step_id[0],
        "step_id": step_id,
        "partition_id": partition_id,
        "artifacts": [
            {
                "artifact_name": "OUT.json",
                "payload": {"items": [{"id": "row1", "path": "/tmp/p1", "evidence": ["x"]}]},
            }
        ],
        "request_meta": {
            "provider": "openai",
            "model_id": "model-canonical",
            "lane": "canonical",
            "authoritative": True,
        },
    }


def _fake_call_llm_success(step_id: str, partition_id: str):
    """Returns a factory for call_llm that always succeeds with canonical payload."""
    def _call(**kwargs):
        return {
            "text": json.dumps(_success_payload(step_id, partition_id)),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_summary": {"finish_reason": "STOP"},
            },
        }
    return _call


# ---------------------------------------------------------------------------
# T1: Comparison disabled → no comparison execution
# ---------------------------------------------------------------------------

def test_comparison_disabled_produces_no_comparison_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When compare_mode is None (default), no comparison/ directory is created."""
    runner = _load_runner_module()

    # Guard: module must expose is_comparison_enabled or similar
    assert hasattr(runner, "is_comparison_enabled"), (
        "run_extraction_v5 must expose is_comparison_enabled(cfg)"
    )

    phase = "A"
    step_id = "A9"
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    cfg = _make_cfg(runner, compare_mode=None)
    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", _fake_call_llm_success(step_id, "A_P0001"))
    monkeypatch.setattr(
        runner, "resolve_step_ladder",
        lambda routing_policy, phase, step_id: [("openai", "model-canonical", "OPENAI_API_KEY")],
    )

    runner.execute_step_for_partitions(
        phase=phase,
        prompt_spec=_make_prompt_spec(runner, step_id, tmp_path),
        partitions=_make_partitions(),
        phase_dir=phase_dir,
        cfg=cfg,
    )

    comparison_dir = phase_dir / "raw" / "comparison"
    assert not comparison_dir.exists(), (
        "comparison/ directory must NOT be created when compare_mode is disabled"
    )


# ---------------------------------------------------------------------------
# T2: Comparison enabled on eligible step → separate artifacts created
# ---------------------------------------------------------------------------

def test_comparison_enabled_on_eligible_step_creates_separate_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When compare_mode=additional and step is eligible, comparison artifacts are created."""
    runner = _load_runner_module()

    assert hasattr(runner, "COMPARISON_ELIGIBLE_STEPS"), (
        "run_extraction_v5 must expose COMPARISON_ELIGIBLE_STEPS constant"
    )
    assert len(runner.COMPARISON_ELIGIBLE_STEPS) > 0, "COMPARISON_ELIGIBLE_STEPS must not be empty"

    step_id = _first_nonstricteligible(runner)
    phase = step_id[0]
    phase_dir = tmp_path / f"{phase}_phase_dir"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    cfg = _make_cfg(
        runner,
        compare_mode="additional",
        compare_model="grok-4.20-beta",
        compare_provider="xai",
        compare_steps=step_id,
    )

    call_count: Dict[str, int] = {"canonical": 0, "comparison": 0}

    def _fake_llm(**kwargs):
        model = kwargs.get("model_id", "")
        if model == "grok-4.20-beta":
            call_count["comparison"] += 1
        else:
            call_count["canonical"] += 1
        part_id = kwargs.get("partition_id", "A_P0001")
        return {
            "text": json.dumps(_success_payload(step_id, part_id)),
            "meta": {"failure_type": None, "status_code": 200,
                     "response_summary": {"finish_reason": "STOP"}},
        }

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", _fake_llm)
    monkeypatch.setattr(
        runner, "resolve_step_ladder",
        lambda routing_policy, p, s: [("openai", "model-canonical", "OPENAI_API_KEY")],
    )

    runner.execute_step_for_partitions(
        phase=phase,
        prompt_spec=_make_prompt_spec(runner, step_id, tmp_path),
        partitions=_make_partitions(),
        phase_dir=phase_dir,
        cfg=cfg,
    )

    comparison_dir = phase_dir / "raw" / "comparison"
    assert comparison_dir.exists(), "comparison/ directory must be created when enabled"

    # Find any comparison artifact
    comparison_files = list(comparison_dir.rglob("*.json"))
    assert len(comparison_files) > 0, "At least one comparison artifact must be written"


# ---------------------------------------------------------------------------
# T3: Canonical outputs unchanged when comparison runs
# ---------------------------------------------------------------------------

def test_canonical_outputs_unchanged_when_comparison_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Canonical raw artifact must be byte-identical with or without comparison."""
    runner = _load_runner_module()

    assert hasattr(runner, "COMPARISON_ELIGIBLE_STEPS"), (
        "run_extraction_v5 must expose COMPARISON_ELIGIBLE_STEPS"
    )
    step_id = _first_nonstricteligible(runner)
    phase = step_id[0]

    def _run_with_compare(compare_enabled: bool, run_dir: Path) -> Path:
        phase_dir = run_dir / f"{phase}_phase_dir"
        (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
        cfg = _make_cfg(
            runner,
            compare_mode="additional" if compare_enabled else None,
            compare_model="grok-4.20-beta" if compare_enabled else None,
            compare_provider="xai" if compare_enabled else None,
            compare_steps=step_id if compare_enabled else None,
        )
        monkeypatch.setattr(runner, "build_partition_context", _fake_context)
        monkeypatch.setattr(runner, "call_llm", _fake_call_llm_success(step_id, "A_P0001"))
        monkeypatch.setattr(
            runner, "resolve_step_ladder",
            lambda routing_policy, p, s: [("openai", "model-canonical", "OPENAI_API_KEY")],
        )
        runner.execute_step_for_partitions(
            phase=phase,
            prompt_spec=_make_prompt_spec(runner, step_id, run_dir),
            partitions=_make_partitions(),
            phase_dir=phase_dir,
            cfg=cfg,
        )
        return phase_dir / "raw" / f"{step_id}__A_P0001.json"

    canonical_no_compare = _run_with_compare(False, tmp_path / "run_a")
    canonical_with_compare = _run_with_compare(True, tmp_path / "run_b")

    assert canonical_no_compare.exists(), "canonical artifact must exist (no compare)"
    assert canonical_with_compare.exists(), "canonical artifact must exist (with compare)"

    content_no_compare = json.loads(canonical_no_compare.read_text(encoding="utf-8"))
    content_with_compare = json.loads(canonical_with_compare.read_text(encoding="utf-8"))

    # Artifacts must be identical (ignoring request_meta timing fields and generated_at).
    # We compare only the structural/content fields: phase, step_id, partition_id, artifacts.
    def extract_stable(d: dict) -> dict:
        """Extract only the stable, non-timing fields from the canonical artifact."""
        return {
            k: v for k, v in d.items()
            if k not in {"request_meta", "generated_at", "elapsed_ms",
                         "started_at", "finished_at", "route_elapsed_ms", "wall_time_ms"}
        }

    stable_no_compare = extract_stable(content_no_compare)
    stable_with_compare = extract_stable(content_with_compare)

    assert stable_no_compare == stable_with_compare, (
        "Canonical output (excluding timing fields) must be identical "
        "whether comparison is enabled or not"
    )


# ---------------------------------------------------------------------------
# T4: Comparison route metadata stored correctly
# ---------------------------------------------------------------------------

def test_comparison_route_metadata_distinct_from_canonical(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Comparison artifact must have lane=comparison, authoritative=false."""
    runner = _load_runner_module()

    assert hasattr(runner, "COMPARISON_ELIGIBLE_STEPS"), (
        "run_extraction_v5 must expose COMPARISON_ELIGIBLE_STEPS"
    )
    step_id = _first_nonstricteligible(runner)
    phase = step_id[0]
    phase_dir = tmp_path / f"{phase}_phase_dir"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    cfg = _make_cfg(
        runner,
        compare_mode="additional",
        compare_model="grok-4.20-beta",
        compare_provider="xai",
        compare_steps=step_id,
    )

    def _fake_llm(**kwargs):
        part_id = kwargs.get("partition_id", "A_P0001")
        model = kwargs.get("model_id", "model-canonical")
        payload = _success_payload(step_id, part_id)
        payload["request_meta"]["model_id"] = model
        return {
            "text": json.dumps(payload),
            "meta": {"failure_type": None, "status_code": 200,
                     "response_summary": {"finish_reason": "STOP"}},
        }

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", _fake_llm)
    monkeypatch.setattr(
        runner, "resolve_step_ladder",
        lambda routing_policy, p, s: [("openai", "model-canonical", "OPENAI_API_KEY")],
    )

    runner.execute_step_for_partitions(
        phase=phase,
        prompt_spec=_make_prompt_spec(runner, step_id, tmp_path),
        partitions=_make_partitions(),
        phase_dir=phase_dir,
        cfg=cfg,
    )

    # Find comparison artifact
    comparison_files = list((phase_dir / "raw" / "comparison").rglob("*.json"))
    assert len(comparison_files) > 0, "comparison artifact must exist"

    comp_payload = json.loads(comparison_files[0].read_text(encoding="utf-8"))
    meta = comp_payload.get("request_meta", {})

    assert meta.get("lane") == "comparison", (
        f"comparison artifact must have lane=comparison, got: {meta.get('lane')!r}"
    )
    assert meta.get("authoritative") is False, (
        "comparison artifact must have authoritative=false"
    )
    assert meta.get("provider") == "xai" or meta.get("model_id") == "grok-4.20-beta", (
        "comparison artifact must record comparison provider/model"
    )

    # Canonical artifact must have lane=canonical
    canonical_path = phase_dir / "raw" / f"{step_id}__A_P0001.json"
    if canonical_path.exists():
        can_payload = json.loads(canonical_path.read_text(encoding="utf-8"))
        can_meta = can_payload.get("request_meta", {})
        assert can_meta.get("lane", "canonical") == "canonical", (
            "canonical artifact must have lane=canonical"
        )
        assert can_meta.get("authoritative", True) is True, (
            "canonical artifact must have authoritative=true"
        )


# ---------------------------------------------------------------------------
# T5: Comparison uses same normalization/validation pipeline
# ---------------------------------------------------------------------------

def test_comparison_uses_same_validation_pipeline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """run_comparison_lane must call the same parse/normalize functions as canonical."""
    runner = _load_runner_module()

    assert hasattr(runner, "run_comparison_lane"), (
        "run_extraction_v5 must expose run_comparison_lane()"
    )
    assert hasattr(runner, "parse_json_from_response"), (
        "run_extraction_v5 must expose parse_json_from_response()"
    )

    parse_calls: List[str] = []
    original_parse = runner.parse_json_from_response

    def _tracked_parse(text, *args, **kwargs):
        parse_calls.append("called")
        return original_parse(text, *args, **kwargs)

    monkeypatch.setattr(runner, "parse_json_from_response", _tracked_parse)

    step_id = _first_nonstricteligible(runner)
    phase = step_id[0]
    phase_dir = tmp_path / f"{phase}_phase_dir"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    cfg = _make_cfg(
        runner,
        compare_mode="additional",
        compare_model="grok-4.20-beta",
        compare_provider="xai",
        compare_steps=step_id,
    )
    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", _fake_call_llm_success(step_id, "A_P0001"))
    monkeypatch.setattr(
        runner, "resolve_step_ladder",
        lambda routing_policy, p, s: [("openai", "model-canonical", "OPENAI_API_KEY")],
    )

    runner.execute_step_for_partitions(
        phase=phase,
        prompt_spec=_make_prompt_spec(runner, step_id, tmp_path),
        partitions=_make_partitions(),
        phase_dir=phase_dir,
        cfg=cfg,
    )

    # parse_json_from_response must have been called at least twice:
    # once for canonical, once for comparison
    assert len(parse_calls) >= 2, (
        f"parse_json_from_response must be called for both lanes; calls={len(parse_calls)}"
    )


# ---------------------------------------------------------------------------
# T6: Comparison failure is non-blocking
# ---------------------------------------------------------------------------

def test_comparison_failure_does_not_affect_canonical_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Comparison lane must be non-blocking: run_comparison_lane doesn't raise on LLM failure,
    and the execute_step_for_partitions wrapper catches any exception from the comparison block.
    """
    runner = _load_runner_module()

    assert hasattr(runner, "COMPARISON_ELIGIBLE_STEPS"), (
        "run_extraction_v5 must expose COMPARISON_ELIGIBLE_STEPS"
    )
    assert hasattr(runner, "run_comparison_lane"), (
        "run_extraction_v5 must expose run_comparison_lane()"
    )
    step_id = _first_nonstricteligible(runner)
    phase = step_id[0]
    phase_dir = tmp_path / f"{phase}_phase_dir"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    cfg = _make_cfg(
        runner,
        compare_mode="additional",
        compare_model="grok-4.20-beta",
        compare_provider="xai",
        compare_steps=step_id,
    )

    # --- Part A: Verify execute_step_for_partitions has a try/except for comparison ---
    import inspect as _inspect
    src = _inspect.getsource(runner.execute_step_for_partitions)
    assert "run_comparison_lane" in src, (
        "execute_step_for_partitions must call run_comparison_lane"
    )
    assert "COMPARE_LANE_ERROR" in src, (
        "execute_step_for_partitions must log COMPARE_LANE_ERROR on comparison failure"
    )
    # The comparison block must be inside a try/except
    assert "except" in src, (
        "execute_step_for_partitions must have try/except guarding the comparison block"
    )

    # --- Part B: run_comparison_lane is non-blocking when call_llm raises ---
    def _always_raise(**kwargs):
        raise RuntimeError("injected-comparison-failure")

    results = runner.run_comparison_lane(
        phase=phase,
        step_id=step_id,
        partitions=_make_partitions(),
        phase_dir=phase_dir,
        cfg=cfg,
        prompt_text="test prompt for comparison",
        output_artifacts=(f"{step_id.lower()}_output",),
        build_partition_context_fn=_fake_context,
        call_llm_fn=_always_raise,
        parse_json_from_response_fn=runner.parse_json_from_response,
        coerce_artifacts_from_response_fn=runner.coerce_artifacts_from_response,
    )

    # run_comparison_lane must return a list (not raise)
    assert isinstance(results, list), (
        "run_comparison_lane must return a list even when call_llm raises"
    )
    assert len(results) == len(_make_partitions()), (
        "run_comparison_lane must return one result per partition"
    )
    for r in results:
        assert r["success"] is False, (
            "failed comparison partition must have success=False"
        )
        assert r.get("failure_reason"), (
            "failed comparison partition must record failure_reason"
        )

    # FAILED sidecar must be written for the failed comparison partition
    comparison_dir = phase_dir / "raw" / "comparison"
    assert comparison_dir.exists(), "comparison artifact dir must be created"
    failed_files = list(comparison_dir.rglob("*.FAILED.*"))
    assert len(failed_files) > 0, (
        "FAILED sidecar must be written when comparison lane call_llm raises"
    )


# ---------------------------------------------------------------------------
# T7: Invalid step → clear error
# ---------------------------------------------------------------------------

def test_invalid_comparison_step_raises_clear_error(tmp_path: Path) -> None:
    """Requesting comparison on a disallowed step must raise with list of eligible steps."""
    runner = _load_runner_module()

    assert hasattr(runner, "is_comparison_enabled"), (
        "run_extraction_v5 must expose is_comparison_enabled(cfg)"
    )
    assert hasattr(runner, "validate_comparison_steps"), (
        "run_extraction_v5 must expose validate_comparison_steps(cfg)"
    )

    cfg = _make_cfg(
        runner,
        compare_mode="additional",
        compare_model="grok-4.20-beta",
        compare_provider="xai",
        compare_steps="Z9",  # Z9 is mechanical/checksum step — not doc-heavy
    )

    try:
        runner.validate_comparison_steps(cfg)
    except (ValueError, SystemExit) as exc:
        error_msg = str(exc)
        # Error must mention the ineligible step
        assert "Z9" in error_msg, f"Error must mention the ineligible step Z9; got: {error_msg!r}"
        # Error must mention eligible steps
        eligible = list(runner.COMPARISON_ELIGIBLE_STEPS)
        assert any(s in error_msg for s in eligible), (
            f"Error must list at least one eligible step; got: {error_msg!r}"
        )
    else:
        raise AssertionError(
            "validate_comparison_steps must raise for ineligible step Z9"
        )


# ---------------------------------------------------------------------------
# T8: Comparison resume isolation
# ---------------------------------------------------------------------------

def test_comparison_resume_does_not_invalidate_canonical(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Existing comparison artifact must not cause canonical step to be marked done/skipped."""
    runner = _load_runner_module()

    assert hasattr(runner, "COMPARISON_ELIGIBLE_STEPS"), (
        "run_extraction_v5 must expose COMPARISON_ELIGIBLE_STEPS"
    )
    assert hasattr(runner, "compute_comparison_resume_decision"), (
        "run_extraction_v5 must expose compute_comparison_resume_decision()"
    )

    eligible = list(runner.COMPARISON_ELIGIBLE_STEPS)
    step_id = sorted(eligible)[0]  # sort for deterministic ordering; use A9 first
    phase_dir = tmp_path / "A_phase_dir"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Pre-populate a valid comparison artifact
    comp_dir = raw_dir / "comparison" / "xai__grok-4.20-beta"
    comp_dir.mkdir(parents=True, exist_ok=True)
    comp_artifact = comp_dir / f"{step_id}__A_P0001.json"
    comp_artifact.write_text(
        json.dumps(_success_payload(step_id, "A_P0001")),
        encoding="utf-8",
    )

    # canonical artifact does NOT exist
    canonical_path = raw_dir / f"{step_id}__A_P0001.json"
    assert not canonical_path.exists()

    # compute_resume_decision must still say RERUN for canonical
    decision = runner.compute_resume_decision(
        success_json_path=canonical_path,
        raw_dir=raw_dir,
        phase=phase_dir.name.split("_")[0] if "_" in phase_dir.name else "A",
        step_id=step_id,
        partition_id="A_P0001",
        expected_artifact_names=("OUT.json",),
    )
    assert decision["action"] == "RERUN", (
        f"canonical must require RERUN even if comparison artifact exists; got {decision['action']!r}"
    )

    # compute_comparison_resume_decision must say SKIP for comparison
    comp_decision = runner.compute_comparison_resume_decision(
        comparison_artifact_path=comp_artifact,
        step_id=step_id,
        partition_id="A_P0001",
        provider="xai",
        model="grok-4.20-beta",
    )
    assert comp_decision["action"] == "SKIP", (
        f"comparison must SKIP when valid artifact exists; got {comp_decision['action']!r}"
    )
