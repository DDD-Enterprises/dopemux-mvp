from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import yaml


def _load_linter_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "scripts" / "repo_truth_extractor_promptset_audit_v4.py"
    spec = importlib.util.spec_from_file_location("repo_truth_extractor_promptset_audit_v4", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v4_promptset_lint_passes() -> None:
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()
    payload = module.run_audit(
        root,
        root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "promptset.yaml",
        root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "artifacts.yaml",
    )
    summary = payload["summary"]
    assert summary["status"] == "PASS"
    assert summary["rating_counts"]["stub"] == 0
    assert summary["lint_failures"] == 0


def test_v4_promptset_contains_c10_service_catalog() -> None:
    root = Path(__file__).resolve().parents[3]
    promptset = yaml.safe_load((root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "promptset.yaml").read_text(encoding="utf-8"))
    phase_c_steps = promptset["phases"]["C"]["steps"]
    step_ids = [row["step_id"] for row in phase_c_steps]
    assert "C10" in step_ids
    c10 = next(row for row in phase_c_steps if row["step_id"] == "C10")
    assert c10["outputs"] == ["SERVICE_CATALOG.partX.json"]


def test_v4_step_order_validation_rejects_lexical_order(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    promptset_path = root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "promptset.yaml"
    artifacts_path = root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "artifacts.yaml"
    promptset = yaml.safe_load(promptset_path.read_text(encoding="utf-8"))
    phase_c_steps = promptset["phases"]["C"]["steps"]
    # Force lexical-style ordering bug by moving C10 before C9.
    c10_idx = next(i for i, row in enumerate(phase_c_steps) if row["step_id"] == "C10")
    c9_idx = next(i for i, row in enumerate(phase_c_steps) if row["step_id"] == "C9")
    phase_c_steps[c9_idx], phase_c_steps[c10_idx] = phase_c_steps[c10_idx], phase_c_steps[c9_idx]

    bad_promptset = tmp_path / "promptset_bad.yaml"
    bad_promptset.write_text(yaml.safe_dump(promptset, sort_keys=False), encoding="utf-8")
    module = _load_linter_module()
    payload = module.run_audit(root, bad_promptset, artifacts_path)
    assert payload["summary"]["status"] == "FAIL"
    assert any("not numeric deterministic" in issue for issue in payload["summary"]["global_issues"])


def test_v4_promptset_lint_fails_on_missing_required_sections(tmp_path: Path) -> None:
    module = _load_linter_module()
    prompts_dir = tmp_path / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    prompt_rel_path = "services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A0_STUB.md"
    (tmp_path / prompt_rel_path).write_text(
        "# PROMPT_A0\n\n## Goal\nTiny.\n\n## Outputs\n- `A0_OUTPUT.json`\n",
        encoding="utf-8",
    )

    promptset = {
        "version": "4.0",
        "required_prompt_sections": [
            "Goal",
            "Inputs",
            "Outputs",
            "Schema",
            "Extraction Procedure",
            "Evidence Rules",
            "Determinism Rules",
            "Anti-Fabrication Rules",
            "Failure Modes",
        ],
        "phases": {
            "A": {
                "required_steps": ["A0"],
                "steps": [
                    {
                        "step_id": "A0",
                        "prompt_file": prompt_rel_path,
                        "outputs": ["A0_OUTPUT.json"],
                    }
                ],
            }
        },
    }
    artifacts = {
        "version": "4.0",
        "forbidden_norm_keys": ["generated_at"],
        "artifacts": [
            {
                "phase": "A",
                "artifact_name": "A0_OUTPUT.json",
                "canonical_writer_step_id": "A0",
                "kind": "json_item_list",
                "norm_artifact": True,
                "allow_timestamp_keys": False,
                "merge_strategy": "itemlist_by_id",
                "required_fields": ["id", "path", "line_range"],
            }
        ],
    }
    promptset_path = tmp_path / "promptset.yaml"
    artifacts_path = tmp_path / "artifacts.yaml"
    promptset_path.write_text(yaml.safe_dump(promptset, sort_keys=False), encoding="utf-8")
    artifacts_path.write_text(yaml.safe_dump(artifacts, sort_keys=False), encoding="utf-8")

    payload = module.run_audit(tmp_path, promptset_path, artifacts_path)
    assert payload["summary"]["status"] == "FAIL"
    assert payload["summary"]["lint_failures"] > 0
