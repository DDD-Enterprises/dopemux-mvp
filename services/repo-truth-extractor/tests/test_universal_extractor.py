"""Tests for universal extractor modules.

Covers: feature_detector, phase_applicability, scope_resolver,
interactive_discovery, template_renderer.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from lib.promptgen.feature_detector import (
    AUTO_FEATURES_FILENAME,
    BUILTIN_RULES,
    FeatureRule,
    detect_features,
)
from lib.promptgen.phase_applicability import (
    PHASE_PLAN_FILENAME,
    PHASE_REGISTRY,
    STEP_FEATURE_GATES,
    determine_phase_plan,
)
from lib.promptgen.scope_resolver import (
    SCOPE_RESOLUTION_FILENAME,
    resolve_scopes,
)


RUN_ID = "test-run-001"


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    """Create a minimal empty repo structure."""
    (tmp_path / "README.md").write_text("# My Project\n")
    return tmp_path


@pytest.fixture
def python_api_repo(tmp_path: Path) -> Path:
    """Create a repo with Python API patterns."""
    # Python source
    src = tmp_path / "src" / "myapp"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/health')\n"
        "def health():\n    return {'status': 'ok'}\n"
    )
    (src / "routes.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/api/v1/users')\n"
        "def list_users():\n    pass\n"
    )

    # Services
    svc = tmp_path / "services" / "api-gateway"
    svc.mkdir(parents=True)
    (svc / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    svc2 = tmp_path / "services" / "worker"
    svc2.mkdir(parents=True)
    (svc2 / "main.py").write_text("import celery\n")

    svc3 = tmp_path / "services" / "auth"
    svc3.mkdir(parents=True)
    (svc3 / "main.py").write_text("pass\n")

    # Compose
    (tmp_path / "compose.yml").write_text("services:\n  api:\n    build: .\n")

    # CI
    gh = tmp_path / ".github" / "workflows"
    gh.mkdir(parents=True)
    (gh / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n")

    # Python packaging
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'myapp'\n")
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")

    # Tests
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_main.py").write_text("import pytest\ndef test_health(): pass\n")

    # Docs
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide\n")
    (docs / "api.md").write_text("# API\n")
    (docs / "setup.md").write_text("# Setup\n")

    # Event bus
    events = tmp_path / "src" / "myapp" / "event_bus.py"
    events.write_text("class EventBus:\n    def publish(self, event): pass\n")

    # README
    (tmp_path / "README.md").write_text("# My API Project\n")

    return tmp_path


@pytest.fixture
def dopemux_repo(tmp_path: Path) -> Path:
    """Create a repo with dopemux-specific patterns."""
    # Dopemux source
    src = tmp_path / "src" / "dopemux"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "cli.py").write_text("import click\n")
    (src / "event_bus.py").write_text("class EventBus: pass\n")

    # Dopemux services
    for svc_name in ["adhd_engine", "task-orchestrator", "conport", "dopecon-bridge"]:
        svc = tmp_path / "services" / svc_name
        svc.mkdir(parents=True)
        (svc / "main.py").write_text("pass\n")

    # Dopemux-specific files
    (tmp_path / ".dopemux").mkdir()
    (tmp_path / "task-packets").mkdir()
    (tmp_path / "task-packets" / "TASK_PACKET_001.md").write_text("# Task Packet\n")

    # Ensure dopemux is detectable via content and filenames
    (src / "dopemux_config.py").write_text("# dopemux configuration\nclass DopemuxConfig: pass\n")

    # MCP config
    (tmp_path / ".claude.json").write_text('{"mcpServers": {}}\n')
    (tmp_path / "mcp-proxy-config.yaml").write_text("servers:\n")

    # Compose
    (tmp_path / "compose.yml").write_text("services:\n  api:\n    build: .\n")

    return tmp_path


# ---- Feature Detector Tests ----


class TestFeatureDetector:
    def test_builtin_rules_not_empty(self):
        assert len(BUILTIN_RULES) > 20, "Should have 20+ built-in rules"

    def test_empty_repo_minimal_features(self, empty_repo: Path):
        result = detect_features(root=empty_repo, run_id=RUN_ID)
        assert result["version"] == "AUTO_FEATURES_V1"
        assert result["run_id"] == RUN_ID
        assert isinstance(result["detected_features"], list)
        assert result["is_dopemux_repo"] is False

    def test_python_api_repo_detects_features(self, python_api_repo: Path):
        result = detect_features(root=python_api_repo, run_id=RUN_ID)
        feature_ids = set(result["feature_ids"])

        assert "http_api_python" in feature_ids, "Should detect Python HTTP API"
        assert "ci_github_actions" in feature_ids, "Should detect GitHub Actions"
        assert "docker_compose" in feature_ids, "Should detect Docker Compose"
        assert "python_packaging" in feature_ids, "Should detect Python packaging"
        assert "testing_python" in feature_ids, "Should detect Python tests"
        assert "docs_structured" in feature_ids, "Should detect structured docs"
        assert "event_bus" in feature_ids, "Should detect event bus"

    def test_python_api_repo_not_dopemux(self, python_api_repo: Path):
        result = detect_features(root=python_api_repo, run_id=RUN_ID)
        assert result["is_dopemux_repo"] is False

    def test_dopemux_repo_detected(self, dopemux_repo: Path):
        result = detect_features(root=dopemux_repo, run_id=RUN_ID)
        assert result["is_dopemux_repo"] is True
        assert "dopemux_core" in result["feature_ids"]

    def test_feature_has_evidence(self, python_api_repo: Path):
        result = detect_features(root=python_api_repo, run_id=RUN_ID)
        for feat in result["detected_features"]:
            assert "evidence" in feat
            assert isinstance(feat["evidence"], list)
            assert len(feat["evidence"]) > 0, f"Feature {feat['feature_id']} should have evidence"

    def test_feature_has_scan_roots(self, python_api_repo: Path):
        result = detect_features(root=python_api_repo, run_id=RUN_ID)
        for feat in result["detected_features"]:
            assert "scan_roots" in feat
            assert isinstance(feat["scan_roots"], list)

    def test_feature_confidence_levels(self, python_api_repo: Path):
        result = detect_features(root=python_api_repo, run_id=RUN_ID)
        confidences = {f["feature_id"]: f["confidence"] for f in result["detected_features"]}
        # Python API with content matches should be high confidence
        assert confidences.get("http_api_python") in ("high", "medium")

    def test_suggested_phase_plan(self, python_api_repo: Path):
        result = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = result["suggested_phase_plan"]
        assert "include" in plan
        assert "skip" in plan
        # Universal phases should always be included
        for phase in ["A", "D", "Q", "R", "X", "Z", "S"]:
            assert phase in plan["include"], f"Universal phase {phase} should be included"
        # H and T should be skipped for non-dopemux
        assert "H" in plan["skip"]
        assert "T" in plan["skip"]

    def test_custom_rules(self, python_api_repo: Path):
        custom = FeatureRule(
            feature_id="custom_feature",
            label="Custom",
            description="Test custom rule",
            file_globs=("**/*.md",),
            maps_to_steps=("C99",),
            maps_to_phases=("C",),
        )
        result = detect_features(root=python_api_repo, run_id=RUN_ID, extra_rules=[custom])
        assert "custom_feature" in result["feature_ids"]


# ---- Phase Applicability Tests ----


class TestPhaseApplicability:
    def test_phase_registry_complete(self):
        expected = {"A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z", "S", "M"}
        assert set(PHASE_REGISTRY.keys()) == expected

    def test_universal_phases_included(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        included = {p["phase"] for p in plan["phases"] if p["status"] == "include"}
        for phase in ["A", "D", "C", "E", "G", "Q", "R", "X", "Z", "S"]:
            assert phase in included, f"Universal phase {phase} should be included"

    def test_dopemux_phases_skipped_for_generic(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        skipped = {p["phase"] for p in plan["phases"] if p["status"] == "skip"}
        assert "H" in skipped, "Phase H should be skipped for non-dopemux"
        assert "T" in skipped, "Phase T should be skipped for non-dopemux"

    def test_dopemux_phases_included_for_dopemux(self, dopemux_repo: Path):
        features = detect_features(root=dopemux_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        included = {p["phase"] for p in plan["phases"] if p["status"] == "include"}
        assert "H" in included or "T" in included, "Dopemux phases should be included for dopemux repo"

    def test_force_include(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(
            run_id=RUN_ID, auto_features=features, force_include=["H"]
        )
        h_phase = next(p for p in plan["phases"] if p["phase"] == "H")
        assert h_phase["status"] == "include"
        assert h_phase["reason"] == "force_include"

    def test_force_skip(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(
            run_id=RUN_ID, auto_features=features, force_skip=["C"]
        )
        c_phase = next(p for p in plan["phases"] if p["phase"] == "C")
        assert c_phase["status"] == "skip"
        assert c_phase["reason"] == "force_skip"

    def test_step_gates_present(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        c_phase = next(p for p in plan["phases"] if p["phase"] == "C")
        step_gates = c_phase.get("step_gates")
        assert step_gates is not None, "Phase C should have step gates"
        # C3 (Dope-Memory) should be gated out for non-dopemux
        if "C3" in step_gates:
            assert step_gates["C3"]["status"] == "skip"

    def test_summary_counts(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        summary = plan["summary"]
        assert summary["total_phases"] == len(PHASE_REGISTRY)
        assert summary["include"] + summary["skip"] + summary["conditional"] == summary["total_phases"]


# ---- Scope Resolver Tests ----


class TestScopeResolver:
    def test_basic_resolution(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        assert scopes["version"] == "SCOPE_RESOLUTION_V1"
        assert scopes["total_steps_resolved"] > 0
        assert isinstance(scopes["step_scopes"], dict)

    def test_skipped_phases_excluded(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        # Phase H should be skipped, so no H steps in scopes
        for step_id in scopes["step_scopes"]:
            assert not step_id.startswith("H"), f"Step {step_id} from skipped phase H shouldn't be in scopes"

    def test_feature_overrides_applied(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        # C1 should have feature-specific scopes since http_api_python is detected
        if "C1" in scopes["step_scopes"]:
            c1 = scopes["step_scopes"]["C1"]
            assert c1["source"] != "default", "C1 should have feature-overridden source"

    def test_manual_overrides(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(
            run_id=RUN_ID,
            auto_features=features,
            phase_plan=plan,
            scope_overrides={"A0": ["custom/path/", "other/"]},
        )

        a0 = scopes["step_scopes"]["A0"]
        assert a0["scopes"] == ["custom/path/", "other/"]
        assert a0["source"] == "manual_override"

    def test_included_phases_listed(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        assert "included_phases" in scopes
        assert "A" in scopes["included_phases"]
        assert "H" not in scopes["included_phases"]

    def test_skipped_steps_tracked(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        assert "skipped_steps" in scopes
        assert isinstance(scopes["skipped_steps"], list)


# ---- Integration: Full Pipeline Test ----


class TestPipelineIntegration:
    def test_full_pipeline_python_api(self, python_api_repo: Path):
        """Test the full feature detection → phase plan → scope resolution pipeline."""
        # Stage 0e: Feature detection
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        assert features["feature_count"] > 0

        # Stage 0f: Phase plan
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        assert plan["summary"]["include"] > plan["summary"]["skip"]

        # Scope resolution
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)
        assert scopes["total_steps_resolved"] > 10

        # Verify the pipeline is coherent
        included_phases = set(scopes["included_phases"])
        for step_id, step_info in scopes["step_scopes"].items():
            assert step_id[0] in included_phases, f"Step {step_id} phase not in included phases"

    def test_full_pipeline_empty_repo(self, empty_repo: Path):
        """Even an empty repo should produce a valid pipeline."""
        features = detect_features(root=empty_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        # Universal phases should still be included
        assert "A" in scopes["included_phases"]
        assert "D" in scopes["included_phases"]
        assert scopes["total_steps_resolved"] > 0

    def test_all_outputs_are_json_serializable(self, python_api_repo: Path):
        """All outputs must be JSON-serializable."""
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        json.dumps(features)  # Should not raise
        json.dumps(plan)      # Should not raise
        json.dumps(scopes)    # Should not raise


# ---- Interactive Discovery Tests ----

from lib.promptgen.interactive_discovery import (
    FEATURE_MAP_FILENAME,
    SCOPE_OVERRIDES_FILENAME,
    run_interactive_discovery,
)


class TestInteractiveDiscovery:
    def test_non_interactive_mode(self, python_api_repo: Path):
        """Non-interactive mode should accept all auto-detected features."""
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        feature_map, scope_overrides = run_interactive_discovery(
            auto_features=features,
            phase_plan=plan,
            repo_root=python_api_repo,
            run_id=RUN_ID,
            non_interactive=True,
        )

        assert feature_map["version"] == "FEATURE_MAP_V1"
        assert feature_map["discovery_mode"] == "auto_only"
        assert feature_map["run_id"] == RUN_ID
        assert len(feature_map["confirmed_features"]) == len(features["detected_features"])
        assert feature_map["rejected_features"] == []
        assert feature_map["added_features"] == []

    def test_non_interactive_scope_overrides_empty(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        _, scope_overrides = run_interactive_discovery(
            auto_features=features,
            phase_plan=plan,
            repo_root=python_api_repo,
            run_id=RUN_ID,
            non_interactive=True,
        )

        assert scope_overrides["version"] == "SCOPE_OVERRIDES_V1"
        assert scope_overrides["overrides"] == {}

    def test_non_interactive_preserves_dopemux_flag(self, dopemux_repo: Path):
        features = detect_features(root=dopemux_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        feature_map, _ = run_interactive_discovery(
            auto_features=features,
            phase_plan=plan,
            repo_root=dopemux_repo,
            run_id=RUN_ID,
            non_interactive=True,
        )

        assert feature_map["is_dopemux_repo"] is True

    def test_non_interactive_outputs_json_serializable(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        feature_map, scope_overrides = run_interactive_discovery(
            auto_features=features,
            phase_plan=plan,
            repo_root=python_api_repo,
            run_id=RUN_ID,
            non_interactive=True,
        )

        json.dumps(feature_map)
        json.dumps(scope_overrides)

    def test_feature_ids_preserved(self, python_api_repo: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        feature_map, _ = run_interactive_discovery(
            auto_features=features,
            phase_plan=plan,
            repo_root=python_api_repo,
            run_id=RUN_ID,
            non_interactive=True,
        )

        assert set(feature_map["feature_ids"]) == set(features["feature_ids"])


# ---- Template Renderer Tests ----

from lib.promptgen.template_renderer import (
    build_template_context,
    render_prompt_template,
    render_promptset,
    validate_rendered_prompt,
)


class TestTemplateRenderer:
    def _make_pipeline_artifacts(self, repo_path: Path):
        """Helper to run the full pipeline up to template context."""
        features = detect_features(root=repo_path, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)
        feature_map, _ = run_interactive_discovery(
            auto_features=features,
            phase_plan=plan,
            repo_root=repo_path,
            run_id=RUN_ID,
            non_interactive=True,
        )
        return features, plan, scopes, feature_map

    def test_build_context_structure(self, python_api_repo: Path):
        _, plan, scopes, feature_map = self._make_pipeline_artifacts(python_api_repo)

        ctx = build_template_context(
            feature_map=feature_map,
            scope_resolution=scopes,
            phase_plan=plan,
            repo_root=python_api_repo,
        )

        assert "repo" in ctx
        assert "scopes" in ctx
        assert "features" in ctx
        assert "domain" in ctx
        assert "profile" in ctx
        assert "phases" in ctx
        assert ctx["repo"]["name"] == python_api_repo.name

    def test_render_simple_template(self, python_api_repo: Path):
        _, plan, scopes, feature_map = self._make_pipeline_artifacts(python_api_repo)
        ctx = build_template_context(
            feature_map=feature_map,
            scope_resolution=scopes,
            phase_plan=plan,
            repo_root=python_api_repo,
        )

        template = "# Extraction for {{ repo.name }}\nProfile: {{ profile.id }}"
        result = render_prompt_template(template, ctx)
        assert python_api_repo.name in result
        assert "P00_GENERIC" in result

    def test_render_with_feature_conditionals(self, python_api_repo: Path):
        _, plan, scopes, feature_map = self._make_pipeline_artifacts(python_api_repo)
        ctx = build_template_context(
            feature_map=feature_map,
            scope_resolution=scopes,
            phase_plan=plan,
            repo_root=python_api_repo,
        )

        template = (
            "{% if features.http_api_python.present %}"
            "Has Python API"
            "{% else %}"
            "No Python API"
            "{% endif %}"
        )
        result = render_prompt_template(template, ctx)
        assert "Has Python API" in result

    def test_validate_good_prompt(self):
        prompt = """# PROMPT_A0

## Goal
Scan the repository control plane and produce an inventory of all control files.

## Inputs
Scan the following directories and files for control-plane artifacts:
- `compose.yml` / `docker-compose*.yml`
- `Makefile`, `Taskfile.yml`
- `pyproject.toml`, `package.json`, `Cargo.toml`
- `.github/workflows/*.yml`
- `scripts/**/*.sh`
- All configuration files in `config/`
Include hidden directories: `.github`, `.pre-commit-config.yaml`

## Outputs
- `REPO_CONTROL_INVENTORY.json`

## Schema
```json
{
  "control_files": [
    {
      "path": "string (repo-relative)",
      "category": "string (compose|makefile|ci|package|config|script)",
      "description": "string",
      "evidence": [
        { "path": "string", "line_range": [1, 10], "excerpt": "string ≤200 chars" }
      ]
    }
  ],
  "partitions": [
    {
      "partition_id": "string",
      "description": "string",
      "file_count": "integer"
    }
  ]
}
```

## Extraction Procedure
1. Walk the repo tree top-down
2. Match files against known control-plane patterns
3. Categorize each match
4. Group into logical partitions
5. Emit structured JSON

## Evidence Rules
- Every item must carry at least one evidence object
- `path` must be repo-relative
- `excerpt` must be exact, ≤ 200 chars

## Determinism Rules
- Sort all arrays by primary key
- Use stable IDs derived from file paths
- No timestamps in output

## Anti-Fabrication Rules
- If a file does not exist, do not invent it
- If content is ambiguous, mark as UNKNOWN
- Never infer behavior from naming conventions alone

## Failure Modes
- If repo has no control files, emit empty arrays
- If a file cannot be read, skip with error note
"""
        result = validate_rendered_prompt(prompt)
        assert result["valid"] is True
        assert len(result["sections_missing"]) == 0

    def test_validate_missing_sections(self):
        prompt = "# Bad Prompt\n## Goal\nDo stuff.\n"
        result = validate_rendered_prompt(prompt)
        assert result["valid"] is False
        assert "Inputs" in result["sections_missing"]

    def test_validate_detects_unresolved_variables(self):
        prompt = """## Goal
Scan {{ repo.name }} repository.

## Inputs
Scan {{ scopes.A0 }} directories.

## Outputs
- OUTPUT.json

## Schema
```json
{ "items": [] }
```
This schema defines the full output structure for extraction.
More schema details here to meet minimum length requirements.
Additional fields may be added as needed for extensibility.

## Extraction Procedure
Walk the tree and extract.

## Evidence Rules
Evidence required.

## Determinism Rules
Sort output.

## Anti-Fabrication Rules
No fabrication.

## Failure Modes
Emit empty on failure.
"""
        result = validate_rendered_prompt(prompt)
        assert result["valid"] is False
        assert any("Unresolved" in i for i in result["issues"])

    def test_render_promptset_directory(self, python_api_repo: Path, tmp_path: Path):
        _, plan, scopes, feature_map = self._make_pipeline_artifacts(python_api_repo)
        ctx = build_template_context(
            feature_map=feature_map,
            scope_resolution=scopes,
            phase_plan=plan,
            repo_root=python_api_repo,
        )

        # Create a template directory with one template
        tmpl_dir = tmp_path / "templates"
        tmpl_dir.mkdir()
        (tmpl_dir / "PROMPT_A0_CONTROL_INVENTORY.md").write_text(
            "# Prompt A0\n## Goal\nScan {{ repo.name }}.\n"
        )

        out_dir = tmp_path / "output"
        result = render_promptset(
            template_dir=tmpl_dir,
            output_dir=out_dir,
            context=ctx,
        )

        assert result["rendered"] == 1
        assert result["errors"] == []
        assert (out_dir / "PROMPT_A0_CONTROL_INVENTORY.md").exists()


# ---- End-to-End Pipeline Test ----


class TestEndToEndPipeline:
    def test_full_sync_pipeline_non_interactive(self, python_api_repo: Path, tmp_path: Path):
        """Test the complete pipeline: detect → plan → scope → discovery → context → render."""
        # Stage 0: Auto-detection
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        assert features["feature_count"] > 0

        # Stage 0g: Phase plan
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)

        # Stage 0h: Scope resolution
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        # Stage 1: Interactive discovery (non-interactive)
        feature_map, scope_overrides = run_interactive_discovery(
            auto_features=features,
            phase_plan=plan,
            repo_root=python_api_repo,
            run_id=RUN_ID,
            non_interactive=True,
        )

        # Stage 2a: Build template context
        ctx = build_template_context(
            feature_map=feature_map,
            scope_resolution=scopes,
            phase_plan=plan,
            repo_root=python_api_repo,
        )

        # Stage 2b: Render a template
        template = (
            "# Extraction for {{ repo.name }}\n\n"
            "{% if features.http_api_python.present %}"
            "HTTP API detected — scanning {{ features.http_api_python.roots | as_list }}\n"
            "{% endif %}"
            "{% if features.docker_compose.present %}"
            "Docker Compose detected\n"
            "{% endif %}"
        )
        rendered = render_prompt_template(template, ctx)

        assert python_api_repo.name in rendered
        assert "HTTP API detected" in rendered
        assert "Docker Compose detected" in rendered

        # All outputs must be JSON-serializable
        json.dumps(features)
        json.dumps(plan)
        json.dumps(scopes)
        json.dumps(feature_map)
        json.dumps(scope_overrides)


# ---- Contract Generator Tests ----

from lib.promptgen.contract_generator import (
    generate_all_contracts,
    generate_artifacts_yaml,
    generate_model_map,
    generate_promptset_yaml,
)
from lib.promptgen.integrity_validator import validate_promptset_integrity


class TestContractGenerator:
    def _pipeline_to_contracts(self, repo_path: Path, tmp_path: Path):
        """Helper: run full pipeline → generate contracts."""
        features = detect_features(root=repo_path, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir(exist_ok=True)

        promptset = generate_promptset_yaml(
            phase_plan=plan,
            scope_resolution=scopes,
            prompt_dir=prompt_dir,
            run_id=RUN_ID,
            repo_name="test",
        )
        return features, plan, scopes, promptset

    def test_promptset_structure(self, python_api_repo: Path, tmp_path: Path):
        _, _, _, promptset = self._pipeline_to_contracts(python_api_repo, tmp_path)

        assert promptset["version"] == "4.0"
        assert "phases" in promptset
        assert "all_phase_order" in promptset
        assert len(promptset["phases"]) > 0

    def test_only_included_phases(self, python_api_repo: Path, tmp_path: Path):
        _, _, _, promptset = self._pipeline_to_contracts(python_api_repo, tmp_path)

        # H and T should not be in phases (non-dopemux)
        assert "H" not in promptset["phases"]
        assert "T" not in promptset["phases"]

    def test_artifacts_generated(self, python_api_repo: Path, tmp_path: Path):
        _, _, _, promptset = self._pipeline_to_contracts(python_api_repo, tmp_path)
        artifacts = generate_artifacts_yaml(promptset=promptset, run_id=RUN_ID)

        assert artifacts["version"] == "4.0"
        assert len(artifacts["artifacts"]) > 0
        # Every artifact should have a canonical writer
        for art in artifacts["artifacts"]:
            assert "canonical_writer_step_id" in art
            assert art["canonical_writer_step_id"] != ""

    def test_model_map_generated(self, python_api_repo: Path, tmp_path: Path):
        _, _, _, promptset = self._pipeline_to_contracts(python_api_repo, tmp_path)
        model_map = generate_model_map(promptset=promptset, run_id=RUN_ID)

        assert model_map["version"] == "2.0"
        assert "lanes" in model_map
        assert len(model_map["steps"]) > 0

    def test_generate_all_contracts_writes_files(self, python_api_repo: Path, tmp_path: Path):
        features = detect_features(root=python_api_repo, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        output_dir = tmp_path / "output"

        result = generate_all_contracts(
            phase_plan=plan,
            scope_resolution=scopes,
            prompt_dir=prompt_dir,
            output_dir=output_dir,
            run_id=RUN_ID,
        )

        assert (output_dir / "promptset.yaml").exists()
        assert (output_dir / "artifacts.yaml").exists()
        assert (output_dir / "model_map.yaml").exists()
        assert result["step_count"] > 0
        assert result["artifact_count"] > 0


class TestIntegrityValidator:
    def _make_valid_contracts(self, repo_path: Path, tmp_path: Path):
        """Generate a consistent set of contracts for testing."""
        features = detect_features(root=repo_path, run_id=RUN_ID)
        plan = determine_phase_plan(run_id=RUN_ID, auto_features=features)
        scopes = resolve_scopes(run_id=RUN_ID, auto_features=features, phase_plan=plan)

        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()

        promptset = generate_promptset_yaml(
            phase_plan=plan,
            scope_resolution=scopes,
            prompt_dir=prompt_dir,
            run_id=RUN_ID,
        )
        artifacts = generate_artifacts_yaml(promptset=promptset, run_id=RUN_ID)
        model_map = generate_model_map(promptset=promptset, run_id=RUN_ID)
        return promptset, artifacts, model_map

    def test_valid_contracts_pass(self, python_api_repo: Path, tmp_path: Path):
        promptset, artifacts, model_map = self._make_valid_contracts(
            python_api_repo, tmp_path,
        )
        result = validate_promptset_integrity(
            promptset=promptset, artifacts=artifacts, model_map=model_map,
        )
        assert result["passed"] is True
        assert result["error_count"] == 0

    def test_detects_orphaned_model_map_step(self, python_api_repo: Path, tmp_path: Path):
        promptset, artifacts, model_map = self._make_valid_contracts(
            python_api_repo, tmp_path,
        )
        # Add a step to model_map that doesn't exist in promptset
        model_map["steps"].append({
            "phase": "Z",
            "step_id": "Z99",
            "lane": "contract_emitter",
        })
        result = validate_promptset_integrity(
            promptset=promptset, artifacts=artifacts, model_map=model_map,
        )
        has_error = any(
            "Z99" in e["message"] and "model_map" in e["check"]
            for e in result["errors"]
        )
        assert has_error

    def test_detects_undefined_lane(self, python_api_repo: Path, tmp_path: Path):
        promptset, artifacts, model_map = self._make_valid_contracts(
            python_api_repo, tmp_path,
        )
        # Change a step to reference a non-existent lane
        if model_map["steps"]:
            model_map["steps"][0]["lane"] = "nonexistent_lane"

        result = validate_promptset_integrity(
            promptset=promptset, artifacts=artifacts, model_map=model_map,
        )
        assert result["passed"] is False
        has_lane_error = any("nonexistent_lane" in e["message"] for e in result["errors"])
        assert has_lane_error

    def test_detects_missing_artifact_contract(self, python_api_repo: Path, tmp_path: Path):
        promptset, artifacts, model_map = self._make_valid_contracts(
            python_api_repo, tmp_path,
        )
        # Add an output to a step that has no artifact contract
        for phase_def in promptset["phases"].values():
            for step in phase_def["steps"]:
                step["outputs"].append("NONEXISTENT_ARTIFACT.json")
                break
            break

        result = validate_promptset_integrity(
            promptset=promptset, artifacts=artifacts, model_map=model_map,
        )
        has_error = any("NONEXISTENT_ARTIFACT" in e["message"] for e in result["errors"])
        assert has_error

    def test_summary_counts(self, python_api_repo: Path, tmp_path: Path):
        promptset, artifacts, model_map = self._make_valid_contracts(
            python_api_repo, tmp_path,
        )
        result = validate_promptset_integrity(
            promptset=promptset, artifacts=artifacts, model_map=model_map,
        )
        assert result["summary"]["promptset_steps"] > 0
        assert result["summary"]["model_map_steps"] > 0
        assert result["summary"]["artifacts"] > 0


# ---- Sync Engine Tests ----

from lib.promptgen.sync_engine import SyncResult, run_sync


class TestSyncEngine:
    def test_sync_non_interactive(self, python_api_repo: Path, tmp_path: Path):
        """Full non-interactive sync against a Python API repo."""
        output_dir = tmp_path / "generated"
        result = run_sync(
            repo_root=python_api_repo,
            output_root=output_dir,
            run_id="test-sync-001",
        )

        assert result.success is True
        assert "feature_detection" in result.stages_completed
        assert "phase_plan" in result.stages_completed
        assert "feature_discovery" in result.stages_completed
        assert "scope_resolution" in result.stages_completed
        assert "contract_generation" in result.stages_completed
        assert "integrity_validation" in result.stages_completed

    def test_sync_writes_all_artifacts(self, python_api_repo: Path, tmp_path: Path):
        output_dir = tmp_path / "generated"
        result = run_sync(
            repo_root=python_api_repo,
            output_root=output_dir,
            run_id="test-sync-002",
        )

        assert (output_dir / "AUTO_FEATURES.json").exists()
        assert (output_dir / "PHASE_PLAN.json").exists()
        assert (output_dir / "FEATURE_MAP.json").exists()
        assert (output_dir / "SCOPE_RESOLUTION.json").exists()
        assert (output_dir / "promptset.yaml").exists()
        assert (output_dir / "artifacts.yaml").exists()
        assert (output_dir / "model_map.yaml").exists()
        assert (output_dir / "INTEGRITY_REPORT.json").exists()
        assert (output_dir / "SYNC_MANIFEST.json").exists()

    def test_sync_manifest_matches_result(self, python_api_repo: Path, tmp_path: Path):
        output_dir = tmp_path / "generated"
        result = run_sync(
            repo_root=python_api_repo,
            output_root=output_dir,
            run_id="test-sync-003",
        )

        with open(output_dir / "SYNC_MANIFEST.json") as f:
            manifest = json.load(f)

        assert manifest["success"] == result.success
        assert manifest["run_id"] == "test-sync-003"

    def test_sync_with_force_skip(self, python_api_repo: Path, tmp_path: Path):
        output_dir = tmp_path / "generated"
        result = run_sync(
            repo_root=python_api_repo,
            output_root=output_dir,
            run_id="test-sync-004",
            force_skip=["C", "E"],
        )

        assert result.success is True
        # Check that C and E phases are not in generated contracts
        with open(output_dir / "promptset.yaml") as f:
            import yaml
            promptset = yaml.safe_load(f)
        assert "C" not in promptset.get("phases", {})
        assert "E" not in promptset.get("phases", {})

    def test_sync_nonexistent_repo_fails(self, tmp_path: Path):
        result = run_sync(
            repo_root=tmp_path / "nonexistent",
            output_root=tmp_path / "output",
            run_id="test-sync-fail",
        )
        assert result.success is False
        assert len(result.errors) > 0

    def test_sync_empty_repo(self, empty_repo: Path, tmp_path: Path):
        output_dir = tmp_path / "generated"
        result = run_sync(
            repo_root=empty_repo,
            output_root=output_dir,
            run_id="test-sync-empty",
        )
        assert result.success is True
        assert result.summary.get("phases", 0) > 0

    def test_sync_result_serializable(self, python_api_repo: Path, tmp_path: Path):
        output_dir = tmp_path / "generated"
        result = run_sync(
            repo_root=python_api_repo,
            output_root=output_dir,
            run_id="test-sync-serial",
        )
        json.dumps(result.to_dict())  # Should not raise
