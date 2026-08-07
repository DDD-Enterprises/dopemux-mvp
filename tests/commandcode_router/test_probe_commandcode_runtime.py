import os
import json
import pytest
from pathlib import Path
from scripts.commandcode_router.probe_commandcode_runtime import (
    sanitize_text,
    sanitize_json,
    ProbeHarness,
    validate_results,
    PROBE_STATES
)

def test_redaction_sanitization():
    home_dir = "/Users/testuser"
    raw_text = f"API Key: sk-1234567890abcdef1234, GitHub: ghp_1234567890abcdef1234567890, Path: {home_dir}/projects/foo"
    sanitized = sanitize_text(raw_text, home_dir=home_dir)
    assert "sk-" not in sanitized or "[REDACTED_API_KEY]" in sanitized
    assert "ghp_" not in sanitized or "[REDACTED_GITHUB_TOKEN]" in sanitized
    assert home_dir not in sanitized
    assert "/HOME_DIR" in sanitized

def test_synthetic_workspace_creation(tmp_path):
    output_dir = tmp_path / "output"
    harness = ProbeHarness(output_dir=output_dir, dry_run=True)
    ws_dir = harness.create_synthetic_workspace()
    try:
        assert ws_dir.exists()
        assert (ws_dir / "PROBE_SENTINEL.txt").exists()
        assert (ws_dir / "WRITE_TARGET.txt").exists()
        assert (ws_dir / ".commandcode" / "agents" / "ccar001-reader.md").exists()
        assert (ws_dir / ".commandcode" / "skills" / "ccar001-skill" / "SKILL.md").exists()
        assert (ws_dir / ".mcp.json").exists()
        assert (ws_dir / "fixture_mcp_server.py").exists()
    finally:
        import shutil
        shutil.rmtree(ws_dir, ignore_errors=True)

def test_dry_run_execution(tmp_path):
    output_dir = tmp_path / "dry_run_output"
    harness = ProbeHarness(output_dir=output_dir, dry_run=True)
    harness.setup_dirs()
    ws_dir = harness.create_synthetic_workspace()
    try:
        harness.run_probes(ws_dir)
        harness.generate_manifest()
        harness.generate_reports()

        assert (output_dir / "PROBE_RESULTS.json").exists()
        assert (output_dir / "MANIFEST.json").exists()
        assert (output_dir / "COMMAND_LOG.md").exists()
        assert (output_dir / "IMPLEMENTATION_IMPACT.md").exists()

        results = json.loads((output_dir / "PROBE_RESULTS.json").read_text())
        assert "P00_ENVIRONMENT" in results
        assert results["P00_ENVIRONMENT"]["state"] in PROBE_STATES
    finally:
        import shutil
        shutil.rmtree(ws_dir, ignore_errors=True)

def test_results_validation(tmp_path):
    results_file = tmp_path / "PROBE_RESULTS.json"
    sample_data = {
        "P00_ENVIRONMENT": {
            "probe_id": "P00_ENVIRONMENT",
            "claim": "CLI environment is observable",
            "state": "PASS",
            "evidence": {"version": "1.6.0"}
        }
    }
    results_file.write_text(json.dumps(sample_data))
    validate_results(results_file)
