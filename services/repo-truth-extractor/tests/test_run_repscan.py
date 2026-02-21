from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = ROOT / "services" / "repo-truth-extractor" / "run_repscan.py"
PROFILES_DIR = ROOT / "services" / "repo-truth-extractor" / "lib" / "promptgen" / "profiles"
PROMPT_ROOT = ROOT / "services" / "repo-truth-extractor" / "tests" / "fixtures" / "promptgen" / "v1" / "prompts"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_repscan", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_main(module, argv: List[str], monkeypatch) -> int:
    monkeypatch.setattr(sys, "argv", argv)
    return int(module.main())


def test_promptgen_only_v1_emits_required_artifacts(tmp_path: Path, monkeypatch) -> None:
    runner = _load_module()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    (tmp_path / "services").mkdir(parents=True, exist_ok=True)
    (tmp_path / "services" / "svc.py").write_text("print('ok')\n", encoding="utf-8")

    run_id = "repscan_v1_fixture"
    rc = _run_main(
        runner,
        [
            str(RUNNER_PATH),
            "--promptgen",
            "v1",
            "--promptgen-only",
            "--run-id",
            run_id,
            "--phase",
            "C",
            "--prompt-root",
            str(PROMPT_ROOT),
            "--profiles-dir",
            str(PROFILES_DIR),
        ],
        monkeypatch,
    )
    assert rc == 0

    run_root = tmp_path / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id
    assert (run_root / "00_inputs" / "REPO_FINGERPRINT.json").exists()
    assert (run_root / "00_inputs" / "BUILD_SURFACE.json").exists()
    assert (run_root / "00_inputs" / "ENTRYPOINT_CANDIDATES.json").exists()
    assert (run_root / "00_inputs" / "DEPENDENCY_GRAPH_HINTS.json").exists()
    assert (run_root / "00_inputs" / "ARCHETYPES.json").exists()
    assert (run_root / "PROFILE_SELECTION.json").exists()
    assert (run_root / "promptpacks" / "PROMPTPACK.v1.json").exists()
    assert (run_root / "promptpacks" / "PROMPTPACK.v1.sha256.json").exists()
    assert (run_root / "RUN_PROMPTPACK_FINGERPRINT.json").exists()


def test_auto_mode_runs_once_then_emits_v2_suggestion(tmp_path: Path, monkeypatch) -> None:
    runner = _load_module()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    (tmp_path / "services").mkdir(parents=True, exist_ok=True)
    (tmp_path / "services" / "svc.py").write_text("print('ok')\n", encoding="utf-8")

    run_id = "repscan_auto_fixture"
    run_root = tmp_path / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id
    calls: List[List[str]] = []

    def fake_legacy_runner(*, legacy_runner: Path, repo_root: Path, args: List[str], prompt_root: Path | None = None) -> int:
        del legacy_runner, repo_root, prompt_root
        calls.append(list(args))
        if "--coverage-report" in args:
            coverage = {
                "phases": {
                    "C": {
                        "failure_type_histogram": {"parse_or_empty": 2, "payload_unshrinkable": 1},
                        "partitions_attempted": 8,
                        "partitions_ok": 3,
                    }
                }
            }
            qa_dir = run_root / "C_code_surfaces" / "qa"
            qa_dir.mkdir(parents=True, exist_ok=True)
            (qa_dir / "C0_QA.json").write_text(
                json.dumps({"step_id": "C0", "missing_expected_artifacts": ["EVENTBUS_SURFACE.json"]}),
                encoding="utf-8",
            )
            (run_root / "RUN_ROUTING_FINGERPRINT.json").write_text(
                json.dumps({"phases": {"C": [{"step_id": "C0", "provider": "xai", "model_id": "grok-code-fast-1"}]}}),
                encoding="utf-8",
            )
            (run_root / "COVERAGE_REPORT.json").write_text(json.dumps(coverage), encoding="utf-8")
        return 0

    monkeypatch.setattr(runner, "_run_legacy_runner", fake_legacy_runner)

    rc = _run_main(
        runner,
        [
            str(RUNNER_PATH),
            "--promptgen",
            "auto",
            "--run-id",
            run_id,
            "--phase",
            "C",
            "--prompt-root",
            str(PROMPT_ROOT),
            "--profiles-dir",
            str(PROFILES_DIR),
            "--dry-run",
        ],
        monkeypatch,
    )
    assert rc == 0
    assert len(calls) == 2
    assert "--coverage-report" not in calls[0]
    assert "--coverage-report" in calls[1]
    assert (run_root / "promptpacks" / "PROMPTPACK.v2.json").exists()
    assert (run_root / "promptpacks" / "PROMPT_ADJUSTMENTS.json").exists()

