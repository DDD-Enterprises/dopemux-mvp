from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_direct_model_smoke import (
    _resolve_prompted_credentials,
    run_direct_model_smoke,
)
from benchmarking.direct_model import runner as direct_runner


def test_direct_model_smoke_persists_fixed_matrix_without_route_claims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        direct_runner.DirectModelRunner,
        "preflight",
        lambda self, candidates: [
            {
                "model_key": candidate.model_key,
                "provider_name": candidate.provider_name,
                "provider_model_id": candidate.provider_model_id,
                "api_key_env": candidate.api_key_env,
                "status_code": 200,
                "failure_type": None,
                "provider_signature": f"{candidate.provider_name}:{candidate.provider_model_id}",
                "api_key_present": True,
                "provider_error_reason": None,
            }
            for candidate in candidates
        ],
    )

    def fake_invoke(self, *, model_id, system_prompt, user_prompt, response_format, max_tokens, retry_max_attempts):
        if "conflicting" in user_prompt:
            text = json.dumps(
                {
                    "service_name": "mercury",
                    "primary_language": "Rust",
                    "owner_team": "unknown",
                    "default_branch": "unknown",
                    "conflicts": ["default_branch", "owner_team"],
                    "unknowns": ["default_branch", "owner_team"],
                }
            )
        elif "packaging" in user_prompt:
            text = json.dumps(
                {
                    "document_id": "api_contract_packet",
                    "claims": [
                        {"claim_id": "public_endpoint", "value": "/v1/tasks", "evidence_ref": "docs/api.md#L10"},
                        {"claim_id": "auth_mode", "value": "bearer-token", "evidence_ref": "docs/api.md#L30"},
                    ],
                    "warnings": [],
                }
            )
        elif "adjudication" in user_prompt:
            text = json.dumps(
                {
                    "selected_claim_id": "claim_alpha",
                    "confidence": "medium",
                    "blocked_claim_ids": ["claim_beta"],
                    "reason": "source_a and source_b are newer and consistent",
                }
            )
        else:
            text = json.dumps(
                {
                    "repo_name": "atlas-api",
                    "primary_language": "Python",
                    "ci_system": "GitHub Actions",
                    "owner_team": "platform-eng",
                    "default_branch": "main",
                    "unknowns": [],
                }
            )
        return {
            "ok": True,
            "request_payload": {"model": model_id, "response_format": response_format},
            "response_text": text,
            "meta": {"provider": "mock", "model_id": model_id, "retry_trace": [{"attempt": 1}], "response_summary": {}},
            "latency_ms": 12.5,
            "request_payload_bytes_estimate": 100,
        }

    monkeypatch.setattr(direct_runner.OpenRouterDirectAdapter, "invoke", fake_invoke)
    monkeypatch.setattr(direct_runner.XaiDirectAdapter, "invoke", fake_invoke)

    proof_dir = tmp_path / "proof"
    payload = run_direct_model_smoke(
        root=tmp_path / "benchmarks",
        proof_dir=proof_dir,
        openrouter_api_key="or-test",
        xai_api_key="xai-test",
        prompt_for_keys=False,
    )
    assert len(payload["attempts"]) == 11
    assert payload["no_route_profile_truth_claimed"] is True
    assert (proof_dir / "DIRECT_MODEL_CAMPAIGN_MANIFEST.json").exists()
    comparison = json.loads((proof_dir / "DIRECT_MODEL_COMPARISON.json").read_text(encoding="utf-8"))
    assert "lane_boundary_note" in comparison
    failures = json.loads((proof_dir / "DIRECT_MODEL_FAILURES.json").read_text(encoding="utf-8"))
    assert isinstance(failures, list)


def test_prompted_credentials_fail_closed_when_missing_in_noninteractive_mode(monkeypatch) -> None:
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with pytest.raises(RuntimeError, match="Cannot prompt for missing credentials"):
        _resolve_prompted_credentials(
            openrouter_api_key=None,
            xai_api_key=None,
            prompt_for_keys=True,
        )
