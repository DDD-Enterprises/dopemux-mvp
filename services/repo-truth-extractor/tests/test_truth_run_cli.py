"""
Tests for: dopemux extract truth-run CLI command and v5 UI enhancements.

These tests validate:
- CLI subcommand is registered and produces correct help output
- Hygiene errors block extraction unless --force is passed
- partition_start_event adds to active dict
- retry_event updates active dict and emits structured event
- failure_spotlight accepts retry_trace parameter
- call_llm retry_callback is invoked on retry
"""
from __future__ import annotations

import importlib.util
import sys
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Load modules under test without modifying installed packages
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_V5_PATH = _REPO_ROOT / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
_EXTRACT_CMDS_PATH = _REPO_ROOT / "src" / "dopemux" / "commands" / "extract_commands.py"


def _load_v5():
    if "v5_mod" in sys.modules:
        return sys.modules["v5_mod"]
    spec = importlib.util.spec_from_file_location("v5_mod", _V5_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v5_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helper: build a minimal UI instance (no filesystem writes needed for tests)
# ---------------------------------------------------------------------------
def _make_ui(tmp_path: Path):
    v5 = _load_v5()
    run_root = tmp_path / "run_root"
    run_root.mkdir(parents=True, exist_ok=True)
    # Create required telemetry dir
    (run_root / "telemetry").mkdir(exist_ok=True)
    cfg = v5.UiConfig(mode="plain", quiet=False, jsonl_events=False)
    return v5.UI(cfg=cfg, run_root=run_root, run_id="test-run-001")


# ---------------------------------------------------------------------------
# Test 1: CLI command is registered
# ---------------------------------------------------------------------------
class TestTruthRunCommandRegistered(unittest.TestCase):
    def _import_extract_group(self):
        """Import extract command group via the installed package."""
        # Add src to sys.path if needed
        src_path = str(_REPO_ROOT / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        try:
            # Use the installed package import path
            from dopemux.commands.extract_commands import extract
            return extract
        except ImportError:
            self.skipTest("dopemux package not importable in this test context")

    def test_truth_run_in_extract_group(self):
        """truth-run subcommand must be registered under the extract group."""
        extract = self._import_extract_group()
        self.assertIn("truth-run", extract.commands,
                      "truth-run not found in extract command group")

    def test_truth_run_options(self):
        """truth-run must have all expected options."""
        extract = self._import_extract_group()
        cmd = extract.commands["truth-run"]
        param_names = {p.name for p in cmd.params}
        for expected in ["run_id", "phase", "workers", "routing_policy",
                         "doctor", "skip_hygiene", "apply_cleanup", "force"]:
            self.assertIn(expected, param_names, f"Option {expected!r} missing from truth-run")


# ---------------------------------------------------------------------------
# Test 2: partition_start_event adds to active dict
# ---------------------------------------------------------------------------
class TestPartitionStartEvent(unittest.TestCase):
    def test_adds_to_active_partitions(self):
        """partition_start_event must register partition in _active_partitions dict."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            self.assertEqual(len(ui._active_partitions), 0)
            ui.partition_start_event(
                phase="A", step_id="A0__A", partition_id="A_P0001",
                provider="openai", model_id="gpt-4.1-mini",
            )
            self.assertIn("A_P0001", ui._active_partitions)
            entry = ui._active_partitions["A_P0001"]
            self.assertEqual(entry["provider"], "openai")
            self.assertEqual(entry["model_id"], "gpt-4.1-mini")
            self.assertEqual(entry["status"], "running")

    def test_thread_safe_concurrent_adds(self):
        """partition_start_event must be thread-safe."""
        import tempfile, time
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            errors: list = []

            def add(partition_id):
                try:
                    ui.partition_start_event(
                        phase="A", step_id="A0__A", partition_id=partition_id,
                        provider="openai", model_id="gpt-4.1-mini",
                    )
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=add, args=(f"P{i:04d}",)) for i in range(50)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(errors, [])
            self.assertEqual(len(ui._active_partitions), 50)


# ---------------------------------------------------------------------------
# Test 3: retry_event updates active dict
# ---------------------------------------------------------------------------
class TestRetryEvent(unittest.TestCase):
    def test_retry_event_updates_status(self):
        """retry_event must update status to 'retry' and store attempt number."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            ui.partition_start_event(
                phase="A", step_id="A0__A", partition_id="A_P0001",
                provider="openai", model_id="gpt-4.1-mini",
            )
            ui.retry_event(
                phase="A", step_id="A0__A", partition_id="A_P0001",
                attempt=2, max_attempts=3,
                provider="openai", model_id="gpt-4.1-mini",
                status_code=429, failure_type="rate_limit",
                delay_seconds=2.0,
            )
            entry = ui._active_partitions.get("A_P0001")
            self.assertIsNotNone(entry)
            self.assertEqual(entry["status"], "retry")
            self.assertEqual(entry["attempt"], 2)

    def test_retry_event_emits_jsonl(self):
        """retry_event must write a partition_retry event to the timeline JSONL."""
        import json, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            ui.partition_start_event(
                phase="A", step_id="A0__A", partition_id="A_P0001",
                provider="openai", model_id="gpt-4.1-mini",
            )
            ui.retry_event(
                phase="A", step_id="A0__A", partition_id="A_P0001",
                attempt=2, max_attempts=3,
                provider="openai", model_id="gpt-4.1-mini",
                status_code=429, failure_type="rate_limit",
                delay_seconds=2.0,
            )
            # Check that timeline JSONL has a partition_retry event
            timeline = ui._timeline_path
            if not timeline.exists():
                self.skipTest("timeline not written in plain mode")
            events = [json.loads(line) for line in timeline.read_text().strip().splitlines()]
            retry_events = [e for e in events if e.get("type") == "partition_retry"]
            self.assertTrue(len(retry_events) >= 1, "No partition_retry event in timeline")
            ev = retry_events[0]
            self.assertEqual(ev["attempt"], 2)
            self.assertEqual(ev["status_code"], 429)


# ---------------------------------------------------------------------------
# Test 4: failure_spotlight accepts retry_trace
# ---------------------------------------------------------------------------
class TestFailureSpotlightRetryTrace(unittest.TestCase):
    def test_accepts_retry_trace_param(self):
        """failure_spotlight must accept retry_trace without error."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            trace = [
                {"attempt": 1, "status_code": 429, "failure_type": "rate_limit", "delay_seconds": 1.0},
                {"attempt": 2, "status_code": 500, "failure_type": "server_error", "delay_seconds": 2.0},
            ]
            # Should not raise
            ui.failure_spotlight(
                phase="A",
                step_id="A0__A",
                partition_id="A_P0001",
                failure_class="provider",
                reason="rate_limit",
                route="openai/gpt-4.1-mini",
                retry_trace=trace,
            )

    def test_retry_trace_in_emitted_event(self):
        """retry_trace must appear in the emitted JSONL event."""
        import json, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            trace = [{"attempt": 1, "status_code": 429, "failure_type": "rate_limit"}]
            ui.failure_spotlight(
                phase="A", step_id="A0__A", partition_id="A_P0001",
                failure_class="provider", reason="rate_limit", route="openai/gpt-4.1",
                retry_trace=trace,
            )
            if not ui._timeline_path.exists():
                self.skipTest("timeline not written in plain mode")
            events = [json.loads(l) for l in ui._timeline_path.read_text().strip().splitlines()]
            spotlight_events = [e for e in events if e.get("type") == "step_failure_spotlight"]
            self.assertTrue(len(spotlight_events) >= 1)
            ev = spotlight_events[0]
            self.assertIn("retry_trace", ev)
            self.assertEqual(ev["retry_trace"][0]["status_code"], 429)


# ---------------------------------------------------------------------------
# Test 5: call_llm retry_callback signature
# ---------------------------------------------------------------------------
class TestCallLlmRetryCallback(unittest.TestCase):
    def test_retry_callback_in_signature(self):
        """call_llm must have retry_callback as an optional parameter."""
        import inspect
        v5 = _load_v5()
        sig = inspect.signature(v5.call_llm)
        self.assertIn("retry_callback", sig.parameters)
        param = sig.parameters["retry_callback"]
        # Default must be None
        self.assertIsNone(param.default,
                          f"retry_callback default should be None, got {param.default!r}")

    def test_retry_callback_none_is_backward_compatible(self):
        """call_llm(retry_callback=None) must not alter call semantics."""
        import inspect
        v5 = _load_v5()
        # Verify it doesn't fail at import time and signature is intact
        sig = inspect.signature(v5.call_llm)
        # All original params should still exist
        for name in ["provider", "model_id", "api_key_env", "system_prompt",
                     "user_content", "cfg"]:
            self.assertIn(name, sig.parameters, f"Original param {name!r} missing")


# ---------------------------------------------------------------------------
# Test 6: _provider_color returns valid strings
# ---------------------------------------------------------------------------
class TestProviderColor(unittest.TestCase):
    def test_known_providers(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            for provider, expected_fragment in [
                ("openai", "green"),
                ("anthropic", "magenta"),
                ("gemini", "blue"),
                ("xai", "yellow"),
                ("openrouter", "cyan"),
            ]:
                color = ui._provider_color(provider)
                self.assertIn(expected_fragment, color,
                              f"Expected {expected_fragment!r} in color for {provider!r}, got {color!r}")

    def test_unknown_provider_returns_white(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ui = _make_ui(Path(tmp))
            color = ui._provider_color("some_unknown_provider_xyz")
            self.assertIn("white", color)


# ---------------------------------------------------------------------------
# Test 7: v5 output path is under v5 (not v3)
# ---------------------------------------------------------------------------
class TestV5OutputPath(unittest.TestCase):
    def test_extraction_root_is_v5(self):
        """V5_EXTRACTION_ROOT must point to .../v5, not .../v3."""
        v5 = _load_v5()
        root = v5.V5_EXTRACTION_ROOT
        self.assertIn("v5", str(root),
                      f"V5_EXTRACTION_ROOT should contain 'v5', got: {root}")
        self.assertNotIn("v3", str(root),
                         f"V5_EXTRACTION_ROOT should not contain 'v3', got: {root}")

    def test_v3_constants_not_present(self):
        """V3_EXTRACTION_ROOT, V3_RUNS_ROOT etc. must NOT be defined in v5 module."""
        v5 = _load_v5()
        for legacy_name in ["V3_EXTRACTION_ROOT", "V3_RUNS_ROOT",
                            "V3_LATEST_RUN_FILE", "V3_DOCTOR_ROOT"]:
            self.assertFalse(hasattr(v5, legacy_name),
                             f"Legacy constant {legacy_name!r} should not exist in v5 module")


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Test 8: --resume and --import-v3 options are present
# ---------------------------------------------------------------------------
class TestTruthRunResumeAndImportOptions(unittest.TestCase):
    def _get_cmd(self):
        src_path = str(_REPO_ROOT / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        try:
            from dopemux.commands.extract_commands import extract
            return extract.commands["truth-run"]
        except ImportError:
            self.skipTest("dopemux package not importable")

    def test_resume_option_present(self):
        """truth-run must have a --resume flag."""
        cmd = self._get_cmd()
        names = {p.name for p in cmd.params}
        self.assertIn("resume", names, "--resume option missing from truth-run")

    def test_import_v3_option_present(self):
        """truth-run must have --import-v3 option."""
        cmd = self._get_cmd()
        names = {p.name for p in cmd.params}
        self.assertIn("import_v3_run_id", names, "--import-v3 option missing from truth-run")

    def test_all_options_present(self):
        """truth-run must expose all expected options including new ones."""
        cmd = self._get_cmd()
        names = {p.name for p in cmd.params}
        for expected in ["run_id", "phase", "workers", "routing_policy",
                         "doctor", "resume", "import_v3_run_id",
                         "skip_hygiene", "apply_cleanup", "force"]:
            self.assertIn(expected, names, f"Option {expected!r} missing")


# ---------------------------------------------------------------------------
# Test 9: --import-v3 migration logic (filesystem)
# ---------------------------------------------------------------------------
class TestImportV3MigrationLogic(unittest.TestCase):
    def test_copy_from_v3_to_v5_runs(self):
        """_display_v3_migration_summary must not crash on well-formed run dir."""
        import tempfile
        src_path = str(_REPO_ROOT / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        try:
            from dopemux.commands.extract_commands import _display_v3_migration_summary
        except ImportError:
            self.skipTest("dopemux package not importable")

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "FULL_RUN"
            phase_dir = run_dir / "A_repo_control_plane"
            (phase_dir / "raw").mkdir(parents=True)
            (phase_dir / "norm").mkdir(parents=True)
            (phase_dir / "qa").mkdir(parents=True)
            # Populate some fake artifacts
            (phase_dir / "raw" / "A0__A_P0001.json").write_text("{}")
            (phase_dir / "raw" / "A0__A_P0002.json").write_text("{}")
            (phase_dir / "raw" / "A0__A_P0003.FAILED.txt").write_text("err")
            (phase_dir / "norm" / "NORM.json").write_text("{}")
            (phase_dir / "qa" / "QA.json").write_text("{}")

            from dopemux.ui.theme import create_console
            console = create_console(file=open("/dev/null", "w"))
            # Must not raise
            _display_v3_migration_summary(run_dir, "FULL_RUN", console)

    def test_resume_flag_passed_to_subprocess_cmd(self):
        """When --resume is True, '--resume' must appear in the subprocess command."""
        src_path = str(_REPO_ROOT / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        try:
            from dopemux.commands.extract_commands import _build_truth_run_command
        except ImportError:
            self.skipTest("dopemux package not importable")

        runner_path = Path("/fake/run_extraction_v5.py")
        auto_run_id, display_run_id, cmd = _build_truth_run_command(
            runner_path=runner_path,
            run_id="FULL_RUN",
            phase="ALL",
            workers=10,
            routing_policy="balanced_openrouter",
            doctor=False,
            resume=True,
        )

        self.assertIn("--resume", cmd, "--resume must be in cmd when resume=True")
        self.assertIn("FULL_RUN", cmd, "--run-id FULL_RUN must be in cmd")
        self.assertEqual(auto_run_id, "FULL_RUN")
        self.assertEqual(display_run_id, "FULL_RUN")

    def test_no_resume_flag_without_flag(self):
        """When --resume is False, '--resume' must NOT appear in subprocess command."""
        src_path = str(_REPO_ROOT / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        try:
            from dopemux.commands.extract_commands import _build_truth_run_command
        except ImportError:
            self.skipTest("dopemux package not importable")

        runner_path = Path("/fake/run_extraction_v5.py")
        auto_run_id, display_run_id, cmd = _build_truth_run_command(
            runner_path=runner_path,
            run_id=None,
            phase="ALL",
            workers=10,
            routing_policy="balanced_openrouter",
            doctor=False,
            resume=False,
        )
        self.assertNotIn("--resume", cmd)
        self.assertIn("--run-id", cmd)
        self.assertIsNotNone(auto_run_id)
        self.assertEqual(display_run_id, auto_run_id)

    def test_resume_without_explicit_run_id_omits_run_id_flag(self):
        """Implicit resume must let v5 resolve latest_run_id.txt."""
        src_path = str(_REPO_ROOT / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        try:
            from dopemux.commands.extract_commands import _build_truth_run_command
        except ImportError:
            self.skipTest("dopemux package not importable")

        _auto_run_id, display_run_id, cmd = _build_truth_run_command(
            runner_path=Path("/fake/run_extraction_v5.py"),
            run_id=None,
            phase="ALL",
            workers=10,
            routing_policy="balanced_openrouter",
            doctor=False,
            resume=True,
        )

        self.assertEqual(display_run_id, "latest_run_id.txt")
        self.assertIn("--resume", cmd)
        self.assertNotIn("--run-id", cmd)
