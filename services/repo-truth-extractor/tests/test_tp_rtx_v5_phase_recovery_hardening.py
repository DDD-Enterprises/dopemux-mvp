"""Tests for TP-RTX-V5-PHASE-RECOVERY-HARDENING-0001.

T1 – H9 regression: issues field shape variants for HOMECTRL_QA items.
T2 – Resume validation: failure_type in request_meta should not auto-RERUN valid artifacts.
T3 – Phase A regression: subcommands: [] in CLI_COMMAND_SURFACE items.
T4 – Cross-phase: normalization works for REPOCTRL_QA (Phase A QA artifact).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_contracts():
    return _load_module(
        _repo_root() / "services" / "repo-truth-extractor" / "lib" / "structured_output_contracts.py",
        "structured_output_contracts_hardening",
    )


def _load_contract_map():
    return _load_module(
        _repo_root() / "services" / "repo-truth-extractor" / "lib" / "phase_contract_map.py",
        "phase_contract_map_hardening",
    )


def _load_runner():
    from _v5_smoke_helpers import load_runner_module
    return load_runner_module()


def _make_homectrl_qa_artifact(issues_value, include_issues: bool = True) -> Dict[str, Any]:
    """Build a synthetic HOMECTRL_QA artifact entry for contract testing."""
    item: Dict[str, Any] = {
        "id": "H9:item1",
        "path": "some/file.py",
        "line_range": [1, 10],
        "status": "PASS",
        "checks": ["check1"],
        "evidence": ["evidence1"],
    }
    if include_issues:
        item["issues"] = issues_value
    return item


def _make_artifact_meta(allow_empty: List[str], extra_required: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "required_fields": ["id", "path", "line_range"],
        "prompt_required_item_fields": ["status", "checks", "issues", "evidence"] + (extra_required or []),
        "allow_empty_array_fields": allow_empty,
    }


def _make_step_contract(artifact_name: str, artifact_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Build a minimal step contract for use in describe_contract_failure."""
    return {
        "artifact_order": [artifact_name],
        "expected_artifacts": [artifact_name],
        "artifacts": {artifact_name: artifact_meta},
        "lane": {"strict_schema_required_primary": True},
        "scope": {"json_managed": True},
    }


def _make_artifact_payload(artifact_name: str, items: List[Dict[str, Any]], schema_id: str = "") -> List[Dict[str, Any]]:
    return [{"artifact_name": artifact_name, "payload": {"schema": schema_id or f"{artifact_name[:-5]}@v1", "items": items}}]


# ---------------------------------------------------------------------------
# T1 – H9 regression: issues field shape variants
# ---------------------------------------------------------------------------

class TestT1H9IssuesShapeVariants:
    """Issues field with various shapes should be accepted after allow_empty_array_fields."""

    def _artifact_meta(self) -> Dict[str, Any]:
        return _make_artifact_meta(allow_empty=["issues", "status"])

    @pytest.mark.parametrize("issues_value,include_issues,expect_pass", [
        ([], True, True),              # issues: [] — semantically valid, no issues found
        (None, True, True),            # issues: null — normalize to []
        ("", True, True),              # issues: "" — normalize to []
        (["actual issue"], True, True), # issues: ["actual issue"] — passes as-is
        (None, False, True),           # missing key — normalize to []
    ])
    def test_issues_variants_with_allow_empty(self, issues_value, include_issues, expect_pass):
        contracts = _load_contracts()
        artifact_meta = self._artifact_meta()

        item = _make_homectrl_qa_artifact(issues_value, include_issues=include_issues)

        # First normalize items
        items = [item]
        norm_items, coercions = contracts.normalize_required_array_fields(items, artifact_meta)

        assert isinstance(norm_items, list)
        assert len(norm_items) == 1
        assert isinstance(norm_items[0].get("issues"), list), (
            f"After normalization, issues should be a list, got {type(norm_items[0].get('issues'))}"
        )

        # Then check contract gate (with allow_empty_array_fields so [] passes)
        artifact_name = "HOMECTRL_QA.json"
        step_contract = _make_step_contract(artifact_name, artifact_meta)
        artifact_name_no_ext = "HOMECTRL_QA"
        step_contract["artifacts"][artifact_name]["canonical_schema_id"] = f"{artifact_name_no_ext}@v1"
        artifacts = _make_artifact_payload(artifact_name, norm_items, schema_id=f"{artifact_name_no_ext}@v1")
        failure = contracts.describe_contract_failure(artifacts, step_contract)
        if expect_pass:
            assert failure is None, f"Expected no failure but got: {failure}"
        else:
            assert failure is not None

    def test_issues_empty_list_passes_describe_contract_failure_directly(self):
        """Directly confirm describe_contract_failure returns None for issues: []."""
        contracts = _load_contracts()
        artifact_meta = self._artifact_meta()
        artifact_meta["canonical_schema_id"] = "HOMECTRL_QA@v1"

        item = _make_homectrl_qa_artifact([])  # issues: []
        artifact_name = "HOMECTRL_QA.json"
        step_contract = _make_step_contract(artifact_name, artifact_meta)
        step_contract["artifacts"][artifact_name]["canonical_schema_id"] = "HOMECTRL_QA@v1"
        artifacts = _make_artifact_payload(artifact_name, [item], schema_id="HOMECTRL_QA@v1")
        failure = contracts.describe_contract_failure(artifacts, step_contract)
        assert failure is None, f"issues: [] should not trigger contract failure, got: {failure}"

    def test_normalize_coercions_recorded(self):
        """Coercions are recorded for None and missing fields."""
        contracts = _load_contracts()
        artifact_meta = self._artifact_meta()

        item_null = _make_homectrl_qa_artifact(None, include_issues=True)
        item_missing = _make_homectrl_qa_artifact(None, include_issues=False)
        items = [item_null, item_missing]
        norm_items, coercions = contracts.normalize_required_array_fields(items, artifact_meta)

        assert len(coercions) >= 2
        coerced_fields = [c["field"] for c in coercions]
        assert "issues" in coerced_fields


# ---------------------------------------------------------------------------
# T2 – Resume validation: failure_type in request_meta
# ---------------------------------------------------------------------------

class TestT2ResumeValidation:
    """validate_success_partition_output should not RERUN when request_meta has failure_type
    but artifacts are valid."""

    def _valid_success_payload(self, runner, include_request_meta_failure: bool = False) -> Dict[str, Any]:
        from _v5_smoke_helpers import make_valid_d1_success_payload
        payload = make_valid_d1_success_payload(runner)
        if include_request_meta_failure:
            payload["request_meta"] = {"failure_type": "schema", "model": "test"}
        return payload

    def test_valid_artifacts_with_failure_type_in_request_meta_is_skip(self, tmp_path: Path):
        """(a) file with failure_type in request_meta but valid artifacts → SKIP not RERUN."""
        runner = _load_runner()
        payload = self._valid_success_payload(runner, include_request_meta_failure=True)
        success_json = tmp_path / "D1__D_P0001.json"
        success_json.write_text(json.dumps(payload) + "\n", encoding="utf-8")

        is_valid, reason = runner.validate_success_partition_output(
            success_json_path=success_json,
            phase="D",
            step_id="D1",
            partition_id="D_P0001",
            expected_artifact_names=tuple(
                art["artifact_name"] for art in payload["artifacts"]
            ),
        )
        assert is_valid is True, f"Expected SKIP (valid) but got reason={reason}"
        assert reason == "valid_success"

    def test_failure_type_and_empty_artifacts_is_rerun(self, tmp_path: Path):
        """(b) file with failure_type AND no expected artifacts → RERUN."""
        runner = _load_runner()
        payload = {
            "phase": "D",
            "step_id": "D1",
            "partition_id": "D_P0001",
            "request_meta": {"failure_type": "schema"},
            "artifacts": [],
        }
        success_json = tmp_path / "D1__D_P0001.json"
        success_json.write_text(json.dumps(payload) + "\n", encoding="utf-8")

        is_valid, reason = runner.validate_success_partition_output(
            success_json_path=success_json,
            phase="D",
            step_id="D1",
            partition_id="D_P0001",
            expected_artifact_names=("DOC_INDEX.json",),
        )
        assert is_valid is False, "Expected RERUN but got valid"

    def test_no_failure_type_valid_artifacts_is_skip(self, tmp_path: Path):
        """(c) file with no failure_type, valid artifacts → SKIP."""
        runner = _load_runner()
        payload = self._valid_success_payload(runner, include_request_meta_failure=False)
        success_json = tmp_path / "D1__D_P0001.json"
        success_json.write_text(json.dumps(payload) + "\n", encoding="utf-8")

        is_valid, reason = runner.validate_success_partition_output(
            success_json_path=success_json,
            phase="D",
            step_id="D1",
            partition_id="D_P0001",
            expected_artifact_names=tuple(
                art["artifact_name"] for art in payload["artifacts"]
            ),
        )
        assert is_valid is True
        assert reason == "valid_success"

    def test_corrupted_file_is_rerun(self, tmp_path: Path):
        """(d) corrupted file → RERUN."""
        runner = _load_runner()
        success_json = tmp_path / "D1__D_P0001.json"
        success_json.write_text("NOT VALID JSON{{{{", encoding="utf-8")

        is_valid, reason = runner.validate_success_partition_output(
            success_json_path=success_json,
            phase="D",
            step_id="D1",
            partition_id="D_P0001",
            expected_artifact_names=("DOC_INDEX.json",),
        )
        assert is_valid is False


# ---------------------------------------------------------------------------
# T3 – Phase A regression: subcommands: [] in CLI_COMMAND_SURFACE items
# ---------------------------------------------------------------------------

class TestT3PhaseASubcommandsRegression:
    """subcommands: [] should pass contract for CLI_COMMAND_SURFACE after allow_empty_array_fields."""

    def _artifact_meta_with_subcommands(self) -> Dict[str, Any]:
        # CLI_COMMAND_SURFACE items have subcommands but not QA-specific fields like checks/issues
        return {
            "required_fields": ["id", "path", "line_range"],
            "prompt_required_item_fields": ["subcommands", "evidence"],
            "allow_empty_array_fields": ["subcommands"],
            "canonical_schema_id": "CLI_COMMAND_SURFACE@v1",
        }

    @pytest.mark.parametrize("subcommands_value,include_key,expect_pass", [
        ([], True, True),                      # subcommands: [] — valid: no subcommands
        (["sub1"], True, True),               # subcommands: ["sub1"] — valid: has subcommands
        (None, True, True),                   # subcommands: null — normalize to []
        ("", True, True),                     # subcommands: "" — normalize to []
        (None, False, True),                  # missing key — normalize to []
    ])
    def test_subcommands_variants(self, subcommands_value, include_key, expect_pass):
        contracts = _load_contracts()
        artifact_meta = self._artifact_meta_with_subcommands()
        artifact_meta["canonical_schema_id"] = "CLI_COMMAND_SURFACE@v1"

        item: Dict[str, Any] = {
            "id": "cmd:git",
            "path": "src/cli.py",
            "line_range": [1, 20],
            "evidence": ["git is a CLI tool"],
        }
        if include_key:
            item["subcommands"] = subcommands_value

        items = [item]
        norm_items, coercions = contracts.normalize_required_array_fields(items, artifact_meta)
        assert isinstance(norm_items[0].get("subcommands"), list)

        artifact_name = "CLI_COMMAND_SURFACE.json"
        step_contract = _make_step_contract(artifact_name, artifact_meta)
        artifacts = _make_artifact_payload(artifact_name, norm_items, schema_id="CLI_COMMAND_SURFACE@v1")
        failure = contracts.describe_contract_failure(artifacts, step_contract)

        if expect_pass:
            assert failure is None, f"Expected pass but got: {failure}"
        else:
            assert failure is not None

    def test_phase_contract_map_includes_allow_empty_array_fields_for_cli(self):
        """CLI_COMMAND_SURFACE.json entry in phase_contract_map has allow_empty_array_fields."""
        contract_map = _load_contract_map()
        contract_map.compile_phase_contract_map.cache_clear()
        compiled = contract_map.compile_phase_contract_map()
        steps = compiled.get("steps", {})
        # find any step with CLI_COMMAND_SURFACE.json in artifacts
        for step_key, step_val in steps.items():
            artifacts = step_val.get("artifacts", {})
            if "CLI_COMMAND_SURFACE.json" in artifacts:
                allow_empty = artifacts["CLI_COMMAND_SURFACE.json"].get("allow_empty_array_fields", [])
                assert "subcommands" in allow_empty, (
                    f"CLI_COMMAND_SURFACE.json missing subcommands in allow_empty_array_fields: {allow_empty}"
                )
                return
        pytest.skip("CLI_COMMAND_SURFACE.json not found in compiled contract map")


# ---------------------------------------------------------------------------
# T4 – Cross-phase: normalization works for REPOCTRL_QA (Phase A QA artifact)
# ---------------------------------------------------------------------------

class TestT4CrossPhaseRepoctrlQa:
    """normalize_required_array_fields works for REPOCTRL_QA.json (Phase A QA artifact)."""

    def _artifact_meta(self) -> Dict[str, Any]:
        return _make_artifact_meta(allow_empty=["issues", "status"])

    @pytest.mark.parametrize("issues_value,include_issues", [
        ([], True),
        (None, True),
        ("", True),
        (None, False),
    ])
    def test_repoctrl_qa_issues_normalization(self, issues_value, include_issues):
        contracts = _load_contracts()
        artifact_meta = self._artifact_meta()

        item: Dict[str, Any] = {
            "id": "A99:item1",
            "path": "some/repo_file.py",
            "line_range": [1, 5],
            "checks": ["check1"],
            "evidence": ["evidence1"],
        }
        if include_issues:
            item["issues"] = issues_value

        items = [item]
        norm_items, coercions = contracts.normalize_required_array_fields(items, artifact_meta)

        assert isinstance(norm_items[0].get("issues"), list), (
            f"REPOCTRL_QA issues should normalize to list, got {type(norm_items[0].get('issues'))}"
        )

    def test_phase_contract_map_includes_allow_empty_array_fields_for_repoctrl_qa(self):
        """REPOCTRL_QA.json entry in phase_contract_map has allow_empty_array_fields."""
        contract_map = _load_contract_map()
        contract_map.compile_phase_contract_map.cache_clear()
        compiled = contract_map.compile_phase_contract_map()
        steps = compiled.get("steps", {})
        for step_key, step_val in steps.items():
            artifacts = step_val.get("artifacts", {})
            if "REPOCTRL_QA.json" in artifacts:
                allow_empty = artifacts["REPOCTRL_QA.json"].get("allow_empty_array_fields", [])
                assert "issues" in allow_empty, (
                    f"REPOCTRL_QA.json missing issues in allow_empty_array_fields: {allow_empty}"
                )
                return
        pytest.skip("REPOCTRL_QA.json not found in compiled contract map")

    def test_phase_contract_map_includes_allow_empty_array_fields_for_homectrl_qa(self):
        """HOMECTRL_QA.json entry in phase_contract_map has allow_empty_array_fields."""
        contract_map = _load_contract_map()
        contract_map.compile_phase_contract_map.cache_clear()
        compiled = contract_map.compile_phase_contract_map()
        steps = compiled.get("steps", {})
        for step_key, step_val in steps.items():
            artifacts = step_val.get("artifacts", {})
            if "HOMECTRL_QA.json" in artifacts:
                allow_empty = artifacts["HOMECTRL_QA.json"].get("allow_empty_array_fields", [])
                assert "issues" in allow_empty, (
                    f"HOMECTRL_QA.json missing issues in allow_empty_array_fields: {allow_empty}"
                )
                return
        pytest.skip("HOMECTRL_QA.json not found in compiled contract map")
