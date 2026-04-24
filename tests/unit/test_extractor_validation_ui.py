from __future__ import annotations

from io import StringIO

from rich.console import Console

from dopemux.commands.extractor_validation_ui import BatchValidationUI


def _payload() -> dict:
    return {
        "run_id": "run-123",
        "stage": "provider_probe",
        "status": "blocked",
        "promptset_root": "/tmp/promptset",
        "routing_policy": "balanced_openrouter",
        "max_cost": 5.0,
        "launch_profile_fingerprint": "abc123def456",
        "launch_profile": {
            "validator_target_policy": "balanced_openrouter",
            "promptset_model_map_sha256": "deadbeef",
        },
        "spend_ledger": {"total_estimated_upper_bound_usd": 1.25},
        "blockers": [
            "provider auth missing",
            "prompt hash mismatch",
        ],
        "baseline": {
            "live_ok": False,
            "provider_env": {
                "OPENAI_API_KEY": {"present": False},
                "GEMINI_API_KEY": {"present": True},
            },
        },
        "stage_decisions": [
            {"stage": "preflight", "status": "pass"},
            {"stage": "provider_probe", "status": "blocked"},
        ],
        "breaker_state": {
            "circuits": {
                "provider_probe": {"state": "open"},
            }
        },
    }


def test_plain_render_preserves_full_blocker_list() -> None:
    ui = BatchValidationUI(mode="plain")

    rendered = ui._render_plain(_payload())

    assert "launch_profile_fingerprint=abc123def456" in rendered
    assert "model_map_sha256=deadbeef" in rendered
    assert "safe_to_spend=no" in rendered
    assert "why_stopped_spending=provider auth missing" in rendered
    assert "blockers:" in rendered
    assert "- provider auth missing" in rendered
    assert "- prompt hash mismatch" in rendered


def test_rich_render_exposes_safe_to_spend_and_blocker_actions() -> None:
    ui = BatchValidationUI(mode="rich")
    buffer = StringIO()
    ui._console = Console(file=buffer, force_terminal=False, color_system=None, width=160)
    ui._rich = True

    ui._emit_rich(_payload())

    rendered = buffer.getvalue()
    assert "Safe to spend" in rendered
    assert "no" in rendered
    assert "Launch fingerprint" in rendered
    assert "abc123def456" in rendered
    assert "provider auth missing" in rendered
    assert "Verify provider credentials and rerun provider preflight before spending." in rendered
    assert "prompt hash mismatch" in rendered
    assert "Fix the promptset root or required prompt files, then rerun preflight." in rendered
