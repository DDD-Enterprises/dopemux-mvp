"""Contracts proving embedded-audit CI cannot run a model or Clink audit."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "embedded-audit.yml"


def test_embedded_audit_workflow_has_no_provider_or_clink_execution_path() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").lower()
    forbidden = (
        "anthropic_api_key",
        "claude_api_key",
        "openai_api_key",
        "pal_clink_runner",
        "run pal clink audit",
        "@anthropic-ai/claude-code",
        "allow_api_spend",
        "gemini-cli",
        "clink",
    )
    for marker in forbidden:
        assert marker not in text


def test_provider_credentials_do_not_create_model_steps() -> None:
    workflow = yaml.load(
        WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    serialized_steps = "\n".join(
        str(step)
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
    ).lower()
    for provider in ("anthropic", "claude", "openai", "gemini", "xai", "openrouter"):
        assert provider not in serialized_steps


def test_workflow_uses_only_deterministic_audit_programs() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "scripts/governance/validate_change_contract.py" in text
    assert "scripts.audit.local_audit_acceptance" in text
    assert "scripts/audit/run_embedded_audit.py" in text
    assert "scripts.audit.pr_audit_router" not in text
    assert "tools.auditor_router" not in text
