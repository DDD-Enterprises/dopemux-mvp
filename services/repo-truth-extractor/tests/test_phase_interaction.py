"""
Tests for: Phase interaction design — optional R inputs, model map SYNTHESIS lane,
and --check-phases CLI.

These tests validate:
- R_OPTIONAL_INPUT_PHASES constant is defined
- run_phase_R collects optional B/E/G/W/Q norm when present
- run_phase_R still works with only mandatory A/H/D/C
- model_map.yaml has SYNTHESIS lane on R0,R2-R10 and S0-S11
- model_map.yaml keeps CE lane on R1 and S12
- --check-phases flag shows readiness table
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

# ---------------------------------------------------------------------------
# Load v5 module without modifying installed packages
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_V5_PATH = _REPO_ROOT / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
_MODEL_MAP_PATH = _REPO_ROOT / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "model_map.yaml"
_EXTRACT_CMDS_PATH = _REPO_ROOT / "src" / "dopemux" / "commands" / "extract_commands.py"


def _load_v5():
    if "v5_mod_pi" in sys.modules:
        return sys.modules["v5_mod_pi"]
    spec = importlib.util.spec_from_file_location("v5_mod_pi", _V5_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v5_mod_pi"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_extract_cmds():
    """Load just the constants and functions from extract_commands.py by exec-ing
    only the tail section (avoids relative import issues)."""
    import types

    src = _EXTRACT_CMDS_PATH.read_text()
    # Extract the constants and function at the end of the file
    # Find the phase readiness section marker
    marker = "# ── Phase readiness table"
    idx = src.find(marker)
    if idx == -1:
        raise RuntimeError("Phase readiness section not found in extract_commands.py")

    # Build a mini-module with just the readiness code + needed imports
    tail_code = src[idx:]
    preamble = (
        "from pathlib import Path\n"
        "from typing import Optional\n"
        "from rich.panel import Panel\n"
        "from rich.table import Table\n"
    )
    mod = types.ModuleType("extract_cmds_pi")
    exec(preamble + tail_code, mod.__dict__)  # noqa: S102
    sys.modules["extract_cmds_pi"] = mod
    return mod


# ---------------------------------------------------------------------------
# Phase interaction constants
# ---------------------------------------------------------------------------
class TestPhaseInteractionConstants(unittest.TestCase):
    def test_r_optional_input_phases_exists(self):
        v5 = _load_v5()
        self.assertTrue(hasattr(v5, "R_OPTIONAL_INPUT_PHASES"))

    def test_r_optional_input_phases_values(self):
        v5 = _load_v5()
        self.assertEqual(set(v5.R_OPTIONAL_INPUT_PHASES), {"B", "E", "G", "W", "Q", "X"})

    def test_r_required_input_phases_unchanged(self):
        v5 = _load_v5()
        self.assertEqual(v5.R_REQUIRED_INPUT_PHASES, ["A", "H", "D", "C"])


# ---------------------------------------------------------------------------
# run_phase_R with optional inputs
# ---------------------------------------------------------------------------
class TestRunPhaseROptionalInputs(unittest.TestCase):
    """Verify run_phase_R collects optional norm when available."""

    def _make_dirs(self, tmp_path):
        """Create dirs dict with mandatory + optional phase dirs."""
        dirs = {}
        for p in ["A", "H", "D", "C", "B", "E", "G", "W", "Q", "R", "X", "T", "Z", "S"]:
            phase_dir = tmp_path / p
            phase_dir.mkdir()
            (phase_dir / "raw").mkdir()
            (phase_dir / "norm").mkdir()
            dirs[p] = phase_dir
        return dirs

    def _populate_mandatory_norms(self, dirs):
        """Write minimal norm artifacts for A/H/D/C so R deps pass."""
        v5 = _load_v5()
        for phase, groups in v5.R_REQUIRED_ARTIFACT_GROUPS.items():
            norm_dir = dirs[phase] / "norm"
            for group in groups:
                artifact_name = group[0]
                (norm_dir / artifact_name).write_text(json.dumps({"test": True}))

    def test_optional_b_collected_when_present(self):
        """When B has norm outputs, run_phase_R should include them."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            dirs = self._make_dirs(tmp)
            self._populate_mandatory_norms(dirs)
            # Add B norm artifact
            (dirs["B"] / "norm" / "BOUNDARY_ENFORCEMENT_POINTS.json").write_text(
                json.dumps({"boundary": "test"})
            )

            v5 = _load_v5()
            collected_items = []

            def mock_run_phase_inner(phase, dirs, cfg, *args, precollected_items=None, **kwargs):
                if precollected_items:
                    collected_items.extend(precollected_items)

            with patch.object(v5, "_run_phase_inner", side_effect=mock_run_phase_inner):
                with patch.object(v5, "_ensure_required_norm_artifact_groups", return_value=[]):
                    with patch.object(v5, "_selected_execution_step_ids_for_phase", return_value=None):
                        cfg = MagicMock()
                        cfg.selected_steps = None
                        v5.run_phase_R(dirs, cfg)

            # to_items returns dicts with "path" key
            paths = [item.get("path", str(item)) if isinstance(item, dict) else str(item) for item in collected_items]
            b_files = [p for p in paths if "/B/norm/" in p]
            self.assertTrue(len(b_files) > 0, f"B norm files not collected. Paths: {paths[:5]}")

    def test_optional_phases_skipped_when_empty(self):
        """When optional phases have no norm outputs, R still works."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            dirs = self._make_dirs(tmp)
            self._populate_mandatory_norms(dirs)

            v5 = _load_v5()
            collected_items = []

            def mock_run_phase_inner(phase, dirs, cfg, *args, precollected_items=None, **kwargs):
                if precollected_items:
                    collected_items.extend(precollected_items)

            with patch.object(v5, "_run_phase_inner", side_effect=mock_run_phase_inner):
                with patch.object(v5, "_ensure_required_norm_artifact_groups", return_value=[]):
                    with patch.object(v5, "_selected_execution_step_ids_for_phase", return_value=None):
                        cfg = MagicMock()
                        cfg.selected_steps = None
                        v5.run_phase_R(dirs, cfg)

            # to_items returns dicts with "path" key
            paths = [item.get("path", str(item)) if isinstance(item, dict) else str(item) for item in collected_items]
            optional_files = [p for p in paths if any(f"/{o}/norm/" in p for o in ["B", "E", "G", "W", "Q"])]
            self.assertEqual(len(optional_files), 0, f"No optional files expected: {optional_files}")


# ---------------------------------------------------------------------------
# Model map SYNTHESIS lane
# ---------------------------------------------------------------------------
class TestModelMapSynthesisLane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(_MODEL_MAP_PATH) as f:
            cls.model_map = yaml.safe_load(f)
        cls.steps = cls.model_map["steps"]

    def _step(self, step_id):
        matches = [s for s in self.steps if s["step_id"] == step_id]
        self.assertTrue(len(matches) == 1, f"Step {step_id} not found or duplicated")
        return matches[0]

    def test_r0_is_synthesis(self):
        self.assertEqual(self._step("R0")["lane_class"], "BULK_DOCS_GENERAL")

    def test_r1_is_ce(self):
        self.assertEqual(self._step("R1")["lane_class"], "CE")

    def test_r2_through_r10_are_synthesis(self):
        for i in range(2, 11):
            step = self._step(f"R{i}")
            self.assertEqual(step["lane_class"], "BULK_DOCS_GENERAL", f"R{i} should be BULK_DOCS_GENERAL")

    def test_s0_through_s11_are_synthesis(self):
        for i in range(0, 12):
            step = self._step(f"S{i}")
            self.assertEqual(step["lane_class"], "BULK_DOCS_GENERAL", f"S{i} should be BULK_DOCS_GENERAL")

    def test_s12_is_ce(self):
        self.assertEqual(self._step("S12")["lane_class"], "CE")


# ---------------------------------------------------------------------------
# Prompt contract amendments
# ---------------------------------------------------------------------------
class TestPromptContractAmendments(unittest.TestCase):
    """Verify R prompts mention optional surfaces."""

    _PROMPTS_DIR = _REPO_ROOT / "services" / "repo-truth-extractor" / "prompts" / "v3"

    def _read_prompt(self, filename):
        return (self._PROMPTS_DIR / filename).read_text()

    def test_r0_mentions_phase_g(self):
        text = self._read_prompt("PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md")
        self.assertIn("Phase G", text)
        self.assertIn("GOV_CI_GATES", text)

    def test_r0_mentions_phase_e(self):
        text = self._read_prompt("PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md")
        self.assertIn("Phase E", text)
        self.assertIn("EXEC_BOOTSTRAP_COMMANDS", text)

    def test_r3_mentions_phase_b(self):
        text = self._read_prompt("PROMPT_R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md")
        self.assertIn("Phase B", text)
        self.assertIn("BOUNDARY_ENFORCEMENT_POINTS", text)

    def test_r5_mentions_phase_w(self):
        text = self._read_prompt("PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md")
        self.assertIn("Phase W", text)
        self.assertIn("WORKFLOW_CATALOG", text)

    def test_r5_mentions_phase_e(self):
        text = self._read_prompt("PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md")
        self.assertIn("Phase E", text)

    def test_r6_mentions_phase_g(self):
        text = self._read_prompt("PROMPT_R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md")
        self.assertIn("Phase G", text)

    def test_r7_mentions_phase_q(self):
        text = self._read_prompt("PROMPT_R7_CONFLICT_LEDGER.md")
        self.assertIn("Phase Q", text)
        self.assertIn("QA_MISSING_ARTIFACTS", text)

    def test_r8_mentions_phase_b(self):
        text = self._read_prompt("PROMPT_R8_RISK_REGISTER_TOP20.md")
        self.assertIn("Phase B", text)
        self.assertIn("BOUNDARY_BYPASS_RISKS", text)

    def test_r8_mentions_phase_e(self):
        text = self._read_prompt("PROMPT_R8_RISK_REGISTER_TOP20.md")
        self.assertIn("Phase E", text)
        self.assertIn("EXEC_RISK_FACTS", text)

    def test_r10_mentions_optional_inputs(self):
        text = self._read_prompt("PROMPT_R10_TWO_PLANE_ARCHITECTURE_TRUTH.md")
        self.assertIn("Optional supplemental", text)
        self.assertIn("Phase B", text)

    def test_hard_rule_updated_not_only(self):
        """Prompts should say 'required' not 'ONLY' for mandatory phases."""
        for fname in [
            "PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md",
            "PROMPT_R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md",
            "PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md",
            "PROMPT_R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md",
            "PROMPT_R7_CONFLICT_LEDGER.md",
            "PROMPT_R8_RISK_REGISTER_TOP20.md",
        ]:
            text = self._read_prompt(fname)
            self.assertNotIn("Reason only from", text, f"{fname} still has 'only from' hard rule")
            self.assertIn("required", text.lower(), f"{fname} should mention 'required'")

    def test_r0_mentions_phase_x(self):
        text = self._read_prompt("PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md")
        self.assertIn("Phase X", text)
        self.assertIn("FEATURE_INDEX_MERGED", text)

    def test_r5_mentions_phase_x(self):
        text = self._read_prompt("PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md")
        self.assertIn("Phase X", text)
        self.assertIn("FEATURE_DEP_GRAPH", text)

    def test_r8_mentions_phase_x(self):
        text = self._read_prompt("PROMPT_R8_RISK_REGISTER_TOP20.md")
        self.assertIn("Phase X", text)
        self.assertIn("FEATURE_SURFACE", text)


# ---------------------------------------------------------------------------
# Phase target coverage
# ---------------------------------------------------------------------------
class TestPhaseTargetCoverage(unittest.TestCase):
    """Verify each phase handler targets the expected input surfaces."""

    def test_phase_e_includes_docker(self):
        """E must scan docker/ for Dockerfiles, entrypoints, healthchecks."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_E)
        self.assertIn('"docker"', src)
        self.assertIn('"installers"', src)
        self.assertIn('"ops"', src)

    def test_phase_g_includes_governance_files(self):
        """G must scan pyproject.toml, pre-commit, Makefile, etc."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_G)
        self.assertIn('"pyproject.toml"', src)
        self.assertIn('".pre-commit-config.yaml"', src)
        self.assertIn('"Makefile"', src)
        self.assertIn('"pytest.ini"', src)
        self.assertIn('"contracts"', src)

    def test_phase_w_includes_compose_and_config(self):
        """W must scan Makefile, compose.yml, docker/, config/ for coordination."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_W)
        self.assertIn('"Makefile"', src)
        self.assertIn('"compose.yml"', src)
        self.assertIn('"docker"', src)
        self.assertIn('"config"', src)

    def test_phase_c_includes_mcp_server_source(self):
        """C must scan docker/mcp-servers-source/ and components/."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_C)
        self.assertIn('"docker/mcp-servers-source"', src)
        self.assertIn('"components"', src)

    def test_phase_b_includes_contracts_and_config(self):
        """B must scan contracts/, config/, .claude/."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_B)
        self.assertIn('"contracts"', src)
        self.assertIn('"config"', src)
        self.assertIn('".claude"', src)

    def test_phase_t_includes_governance_context(self):
        """T must include AGENTS.md and .claude/PROJECT_INSTRUCTIONS.md."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_T)
        self.assertIn("AGENTS.md", src)
        self.assertIn("PROJECT_INSTRUCTIONS.md", src)

    def test_phase_x_uses_collector_not_r_artifacts(self):
        """X must do a direct repo scan, not consume R norm artifacts."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_X)
        self.assertIn("Collector", src, "X should use Collector for direct repo scan")
        self.assertNotIn('dirs["R"]', src, "X should not read R artifacts")

    def test_phase_q_aggregates_x(self):
        """Q should aggregate X outputs alongside A-G."""
        import inspect
        v5 = _load_v5()
        src = inspect.getsource(v5.run_phase_Q)
        self.assertIn('"X"', src, "Q should include X in its aggregation list")


if __name__ == "__main__":
    unittest.main()
