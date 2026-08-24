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


def test_v4_promptset_lint_flags_non_monotonic_extraction_numbering(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()
    promptset_path = root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "promptset.yaml"
    artifacts_path = root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "artifacts.yaml"
    promptset = yaml.safe_load(promptset_path.read_text(encoding="utf-8"))
    step = next(
        row
        for row in promptset["phases"]["R"]["steps"]
        if row["step_id"] == "R0"
    )

    bad_prompt_rel = "services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R0_BROKEN.md"
    bad_prompt_abs = tmp_path / bad_prompt_rel
    bad_prompt_abs.parent.mkdir(parents=True, exist_ok=True)
    bad_prompt_abs.write_text(
        (
            "# PROMPT_R0\n\n"
            "## Goal\n"
            "A sufficiently long goal section for lint coverage.\n\n"
            "## Inputs\n"
            "- input one\n\n"
            "## Outputs\n"
            "- `CONTROL_PLANE_TRUTH_MAP.md`\n\n"
            "## Schema\n"
            "- `CONTROL_PLANE_TRUTH_MAP.md`\n\n"
            "## Extraction Procedure\n"
            "1. First.\n"
            "2. Second.\n"
            "2. Duplicate.\n\n"
            "## Shared Rules\n"
            "Refer to `PROMPTSET_RULES.md` for all shared enforcement rules.\n"
        ),
        encoding="utf-8",
    )
    step["prompt_file"] = bad_prompt_rel

    mutated_promptset = tmp_path / "promptset.yaml"
    mutated_promptset.write_text(
        yaml.safe_dump(promptset, sort_keys=False),
        encoding="utf-8",
    )
    payload = module.run_audit(tmp_path, mutated_promptset, artifacts_path)
    r0_row = next(row for row in payload["rows"] if row["step_id"] == "R0")
    assert any(
        note.startswith("scan:extraction_procedure_non_monotonic_numbering")
        for note in r0_row["notes"]
    )


# Phase 3 Tests - Extended Audit Script


def test_phase_s_audit_passes() -> None:
    """Verify phase_s audit passes with current state."""
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()
    result = module._audit_phase_s(root)

    assert result["status"] == "pass", f"Errors: {result.get('errors', [])}"
    assert result["prompt_count"] == 13
    assert result["schema_count"] == 8  # SP4, SP5, SP7-SP12 (8 total)
    assert len(result.get("errors", [])) == 0


def test_phase_s_int_audit_passes() -> None:
    """Verify phase_s_int audit passes with current state."""
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()
    result = module._audit_phase_s_int(root)

    assert result["status"] == "pass", f"Errors: {result.get('errors', [])}"
    assert result["prompt_count"] == 5
    assert result["schema_count"] == 5
    assert len(result.get("errors", [])) == 0


def test_phase_fl_int_audit_passes() -> None:
    """Verify phase_fl_int audit passes with current state."""
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()
    result = module._audit_phase_fl_int(root)

    assert result["status"] == "pass", f"Errors: {result.get('errors', [])}"
    assert result["prompt_count"] == 8
    assert len(result.get("errors", [])) == 0


def test_prescan_audit_passes() -> None:
    """Verify prescan audit passes with current state."""
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()
    result = module._audit_prescan(root)

    assert result["status"] == "pass", f"Errors: {result.get('errors', [])}"
    assert result["prompt_count"] == 4
    assert len(result.get("errors", [])) == 0


def test_all_populations_audit_passes() -> None:
    """Verify --population all mode runs all 5 audits and aggregates results."""
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()

    results = {}
    for pop in ["v4", "phase_s", "phase_s_int", "phase_fl_int", "prescan"]:
        results[pop] = module._audit_population(pop, root)

    # All populations should pass
    for pop, result in results.items():
        assert result["status"] == "pass", f"{pop} failed: {result.get('errors', [])}"

    # Verify each has expected counts
    assert results["v4"]["prompt_count"] > 0
    assert results["phase_s"]["prompt_count"] == 13
    assert results["phase_s_int"]["prompt_count"] == 5
    assert results["phase_fl_int"]["prompt_count"] == 8
    assert results["prescan"]["prompt_count"] == 4


# --- F-29 (TP-RTE-TRUTH-R3-006): synthesis-tier evidence citation shape -----------------
#
# R7/R8/S4/S5/S6 synthesize claims by aggregating many upstream normalized artifacts, with
# no requirement to name the exact upstream artifact + item id a given claim derives from.
# PROMPTSET_RULES.md now declares a synthesis-tier evidence object
# ({upstream_artifact,item_id,excerpt}, modeled on PROMPT_R11's `<- ARTIFACT:item_id`
# pattern) and these tests pin that the lint fails closed if either half of the contract
# (the shared rules file, or the mandated step's own prompt text) drops the reference.


def _write_stub_synthesis_prompt(path: Path, *, cite_synthesis_evidence: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    shared_rules_body = "Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols."
    if cite_synthesis_evidence:
        shared_rules_body += (
            " This step synthesizes claims from multiple upstream normalized artifacts "
            "(F-29): every claim additionally requires `PROMPTSET_RULES.md`'s Synthesis "
            "Evidence Rules citation shape (`{upstream_artifact,item_id,excerpt}`)."
        )
    path.write_text(
        "# PROMPT_STUB\n\n"
        "## Goal\nStub synthesis step used only to exercise the F-29 lint check.\n\n"
        "## Inputs\nConsumes upstream normalized artifacts UPSTREAM_ONE.json and UPSTREAM_TWO.json.\n\n"
        "## Outputs\n- `STUB_SYNTHESIS_OUTPUT.md`\n\n"
        "## Schema\nOutput is markdown with a deterministic section structure.\n\n"
        "## Extraction Procedure\n1. Load upstream artifacts.\n2. Synthesize claims across them.\n\n"
        f"## Shared Rules\n{shared_rules_body}\n",
        encoding="utf-8",
    )


def _stub_synthesis_promptset(step_id: str, prompt_rel_path: str) -> dict:
    phase = step_id[0]
    return {
        "version": "4.0",
        "phases": {
            phase: {
                "required_steps": [step_id],
                "steps": [
                    {
                        "step_id": step_id,
                        "prompt_file": prompt_rel_path,
                        "outputs": ["STUB_SYNTHESIS_OUTPUT.md"],
                    }
                ],
            }
        },
    }


def _write_promptset_rules(path: Path, *, declare_synthesis_evidence: bool) -> None:
    body = "# STUB PROMPTSET RULES\n\n## Evidence Rules\n- stub\n"
    if declare_synthesis_evidence:
        body += (
            "\n## Synthesis Evidence Rules\n"
            "- Every synthesized claim carries `{upstream_artifact,item_id,excerpt}`.\n"
        )
    path.write_text(body, encoding="utf-8")


def test_synthesis_evidence_lint_fails_when_rules_file_missing_heading(tmp_path: Path) -> None:
    """PROMPTSET_RULES.md dropping the Synthesis Evidence Rules heading must fail closed."""
    module = _load_linter_module()
    prompt_rel = "prompts/PROMPT_R7_STUB.md"
    _write_stub_synthesis_prompt(tmp_path / prompt_rel, cite_synthesis_evidence=True)
    _write_promptset_rules(tmp_path / "PROMPTSET_RULES.md", declare_synthesis_evidence=False)

    promptset_path = tmp_path / "promptset.yaml"
    promptset_path.write_text(
        yaml.safe_dump(_stub_synthesis_promptset("R7", prompt_rel), sort_keys=False), encoding="utf-8"
    )

    issues = module._synthesis_evidence_issues(
        tmp_path, promptset_path, yaml.safe_load(promptset_path.read_text(encoding="utf-8"))
    )
    assert any(
        "PROMPTSET_RULES.md missing '## Synthesis Evidence Rules' section" in issue for issue in issues
    ), issues


def test_synthesis_evidence_lint_fails_when_mandated_step_omits_reference(tmp_path: Path) -> None:
    """R7 (a mandated F-29 step) must reference the Synthesis Evidence Rules by name."""
    module = _load_linter_module()
    prompt_rel = "prompts/PROMPT_R7_STUB.md"
    _write_stub_synthesis_prompt(tmp_path / prompt_rel, cite_synthesis_evidence=False)
    _write_promptset_rules(tmp_path / "PROMPTSET_RULES.md", declare_synthesis_evidence=True)

    promptset_path = tmp_path / "promptset.yaml"
    promptset_payload = _stub_synthesis_promptset("R7", prompt_rel)
    promptset_path.write_text(yaml.safe_dump(promptset_payload, sort_keys=False), encoding="utf-8")

    issues = module._synthesis_evidence_issues(tmp_path, promptset_path, promptset_payload)
    assert any(
        "R7 (PROMPT_R7_STUB.md) does not reference 'Synthesis Evidence Rules'" in issue for issue in issues
    ), issues

    # Also verify it surfaces through the full run_audit() global-issues path, not just the
    # standalone helper.
    artifacts_path = tmp_path / "artifacts.yaml"
    artifacts_path.write_text(
        yaml.safe_dump(
            {
                "version": "4.0",
                "artifacts": [
                    {
                        "phase": "R",
                        "artifact_name": "STUB_SYNTHESIS_OUTPUT.md",
                        "canonical_writer_step_id": "R7",
                        "kind": "markdown",
                        "norm_artifact": False,
                        "merge_strategy": "markdown_concat",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    payload = module.run_audit(tmp_path, promptset_path, artifacts_path)
    assert payload["summary"]["status"] == "FAIL"
    assert any("synthesis_evidence" in issue for issue in payload["summary"]["global_issues"])


def test_synthesis_evidence_lint_passes_when_mandated_step_cites_it(tmp_path: Path) -> None:
    """Positive case: rules file + step both carry the citation shape reference -> no issue."""
    module = _load_linter_module()
    prompt_rel = "prompts/PROMPT_R8_STUB.md"
    _write_stub_synthesis_prompt(tmp_path / prompt_rel, cite_synthesis_evidence=True)
    _write_promptset_rules(tmp_path / "PROMPTSET_RULES.md", declare_synthesis_evidence=True)

    promptset_path = tmp_path / "promptset.yaml"
    promptset_payload = _stub_synthesis_promptset("R8", prompt_rel)
    promptset_path.write_text(yaml.safe_dump(promptset_payload, sort_keys=False), encoding="utf-8")

    issues = module._synthesis_evidence_issues(tmp_path, promptset_path, promptset_payload)
    assert issues == []


def test_synthesis_evidence_lint_ignores_non_mandated_steps(tmp_path: Path) -> None:
    """A step outside {R7,R8,S4,S5,S6} (e.g. A9) is not required to cite the shape."""
    module = _load_linter_module()
    prompt_rel = "prompts/PROMPT_A9_STUB.md"
    _write_stub_synthesis_prompt(tmp_path / prompt_rel, cite_synthesis_evidence=False)
    _write_promptset_rules(tmp_path / "PROMPTSET_RULES.md", declare_synthesis_evidence=True)

    promptset_path = tmp_path / "promptset.yaml"
    promptset_payload = _stub_synthesis_promptset("A9", prompt_rel)
    promptset_path.write_text(yaml.safe_dump(promptset_payload, sort_keys=False), encoding="utf-8")

    issues = module._synthesis_evidence_issues(tmp_path, promptset_path, promptset_payload)
    assert issues == []


def test_real_v4_promptset_mandates_synthesis_evidence_on_all_five_f29_steps() -> None:
    """Pin the real fix: R7/R8/S4/S5/S6 in the shipped promptset all cite the shape, and
    PROMPTSET_RULES.md actually declares the object with all three required keys."""
    root = Path(__file__).resolve().parents[3]
    module = _load_linter_module()
    promptset_path = (
        root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "promptset.yaml"
    )
    promptset_payload = yaml.safe_load(promptset_path.read_text(encoding="utf-8"))

    issues = module._synthesis_evidence_issues(root, promptset_path, promptset_payload)
    assert issues == [], issues

    rules_text = (
        root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "PROMPTSET_RULES.md"
    ).read_text(encoding="utf-8")
    assert "## Synthesis Evidence Rules" in rules_text
    for key in ("upstream_artifact", "item_id", "excerpt"):
        assert key in rules_text
