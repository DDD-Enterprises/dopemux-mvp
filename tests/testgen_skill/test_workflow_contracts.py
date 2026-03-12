from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "templates" / "skills" / "testgen" / "scripts" / "testgen_workflow.py"
    spec = importlib.util.spec_from_file_location("testgen_workflow", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load testgen_workflow module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


workflow = _load_module()


def test_parse_feature_list_payload():
    payload = """
    - Login succeeds with valid credentials
    - Login fails with invalid password
    """
    requirements = workflow.parse_feature_list_payload(payload)
    assert len(requirements) == 2
    assert requirements[0].req_id == "F001"
    assert "valid credentials" in requirements[0].text


def test_parse_task_packet_payload_extracts_sections():
    packet = """
    ## Objective

    Deliver deterministic authentication behavior.

    ## Scope

    IN:

    - Add lockout policy
    - Add audit logging

    OUT:

    - UI redesign

    ## Invariants (Must Remain True)

    - Existing API route names remain stable

    ## Acceptance Criteria

    - Lockout triggers after five failures
    - Audit events are emitted for each attempt
    """

    requirements = workflow.parse_task_packet_payload(packet)
    sources = {item.source for item in requirements}
    assert "objective" in sources
    assert "scope-in" in sources
    assert "acceptance" in sources
    assert any("five failures" in item.text for item in requirements)


def test_layer_applicability_for_service_and_ui_paths():
    requirements = [
        workflow.Requirement("F001", "Validate browser user flow and service health", "feature-list")
    ]
    touched_files = ["services/auth/api.py", "ui-dashboard/src/Login.tsx"]

    decisions = workflow.determine_test_layers(requirements, touched_files, "post-impl-generator")
    by_layer = {decision.layer: decision for decision in decisions}

    assert by_layer["unit"].applicable is True
    assert by_layer["smoke"].applicable is True
    assert by_layer["integration"].applicable is True
    assert by_layer["e2e"].applicable is True
    assert by_layer["regression"].applicable is True


def test_coverage_gate_fails_closed_when_touched_file_missing(tmp_path: Path):
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        """
        <coverage>
          <packages>
            <package name="x">
              <classes>
                <class name="auth" filename="src/auth.py">
                  <lines>
                    <line number="1" hits="1"/>
                    <line number="2" hits="1"/>
                  </lines>
                </class>
              </classes>
            </package>
          </packages>
        </coverage>
        """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(workflow.CoverageResolutionError):
        workflow.evaluate_touched_coverage(
            coverage_xml=coverage_xml,
            touched_files=["src/auth.py", "src/missing.py"],
            coverage_target=90,
        )
