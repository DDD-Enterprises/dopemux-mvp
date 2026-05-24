"""
FA-8-HIGH-1 — Provider preflight probe returns AMBIGUOUS_PROVIDER_BLOCK
even when API keys are valid and direct API calls to the provider succeed.

Reproduction (manual):
  curl -X POST https://openrouter.ai/api/v1/chat/completions \\
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \\
    -d '{"model":"openai/gpt-5.2","messages":[...],"max_tokens":32}'
  # returns valid completion

  python services/repo-truth-extractor/run_extraction_v5.py \\
    --preflight-providers --phase A \\
    --routing-policy balanced_grok_openrouter \\
    --run-id any --output-root /tmp/out
  # returns failure_type=unknown, blocker_code=AMBIGUOUS_PROVIDER_BLOCK

Documented in: rte_audit_findings_FA8_liverun.md / FA-8-HIGH-1

This is a characterization test: it requires real API keys (skipped in CI
unless CI has them). The test marks the probe as broken when keys ARE set
but probe returns failure. xfail until the call_llm/payload-construction
bug is root-caused and fixed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_SERVICE_ROOT = Path(__file__).resolve().parents[3]
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="Requires real OPENROUTER_API_KEY in env (audit-only test)",
)
@pytest.mark.xfail(
    reason="FA-8-HIGH-1: run_provider_doctor_probe returns failure_type=unknown / AMBIGUOUS_PROVIDER_BLOCK even with valid keys + live providers (direct curl succeeds). Root cause likely in call_llm payload construction (max_tokens? response_format?)."
)
def test_preflight_probe_succeeds_with_valid_keys() -> None:
    """xfail until the preflight probe bug is fixed."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_extraction_v5", _SERVICE_ROOT / "run_extraction_v5.py"
    )
    assert spec is not None
    runner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = runner
    spec.loader.exec_module(runner)

    cfg = runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=True,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced_grok_openrouter",
    )
    probe = runner.run_provider_doctor_probe(
        provider="openrouter",
        model_id="openai/gpt-5.2",
        api_key_env="OPENROUTER_API_KEY",
        cfg=cfg,
    )
    assert probe.get("ready") is True, (
        f"Probe should report ready=True with valid OPENROUTER_API_KEY; got: "
        f"failure_type={probe.get('failure_type')}, blocker={probe.get('readiness_blocker', {}).get('blocker_code')}"
    )
