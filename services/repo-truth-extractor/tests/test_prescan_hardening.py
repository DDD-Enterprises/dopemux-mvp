import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import os
import json

from lib.prescan.models import PrescanConfig
from lib.prescan.grok_passes import (
    GrokPassRunner, 
    SecurityViolation, 
    RoutingExhausted, 
    ExecutionEvidence,
    ExecutionAttempt
)
from lib.throttle import ProviderLimiter, ProviderRateConfig

@pytest.fixture
def mock_config(tmp_path):
    return PrescanConfig(
        repo_root=tmp_path / "repo",
        output_dir=tmp_path / "out",
        allow_online_llm=False
    )

@pytest.fixture
def mock_limiter():
    return ProviderLimiter(config=ProviderRateConfig(rpm=10, tpm=1000))

def test_prescan_spend_gate_blocks_online_without_flag(mock_config, mock_limiter):
    runner = GrokPassRunner(mock_config, limiter=mock_limiter)
    candidate = {"provider": "xai", "model_id": "grok-4", "api_key_env": "XAI_API_KEY"}
    evidence = ExecutionEvidence(pass_id="dedup", batch_id=None, planned_candidates=[candidate])
    
    with patch.dict(os.environ, {"XAI_API_KEY": "fake-key"}):
        with pytest.raises(SecurityViolation):
            runner._call_grok("dedup", "payload", candidate, MagicMock())

def test_prescan_spend_gate_allows_mock_without_flag(mock_config):
    limiter = MagicMock(spec=ProviderLimiter)
    limiter.acquire.return_value = 0.0
    runner = GrokPassRunner(mock_config, limiter=limiter)
    candidate = {"provider": "mock", "model_id": "mock-model", "api_key_env": "MOCK_KEY"}
    
    attempt = MagicMock()
    response = runner._call_grok("dedup", "payload", candidate, attempt, est_tokens=25)
    assert isinstance(response, dict)
    assert response.get("status") == "ok"
    assert response.get("pass_id") == "dedup"
    limiter.acquire.assert_called_once_with(25)

def test_prescan_route_divergence_recorded(mock_config, mock_limiter):
    mock_config.allow_online_llm = True
    runner = GrokPassRunner(mock_config, limiter=mock_limiter)
    
    routing_plan = {
        "candidate_routes": {
            "dedup": [
                {"provider": "xai", "model_id": "grok-fail", "api_key_env": "XAI_API_KEY"},
                {"provider": "openai", "model_id": "gpt-success", "api_key_env": "OPENAI_API_KEY"}
            ]
        }
    }
    evidence = ExecutionEvidence(pass_id="dedup", batch_id=None, planned_candidates=routing_plan["candidate_routes"]["dedup"])
    
    with patch.dict(os.environ, {"XAI_API_KEY": "k1", "OPENAI_API_KEY": "k2"}):
        with patch.object(GrokPassRunner, "_call_grok") as mock_call:
            def side_effect(pass_id, payload, candidate, attempt_record, est_tokens=0):
                if candidate["model_id"] == "grok-fail":
                    raise Exception("429")
                attempt_record.status = "success"
                return {"status": "ok"}
            mock_call.side_effect = side_effect
            
            runner._call_grok_validated("dedup", "payload", routing_plan, evidence)
            
            # Verify divergence recording
            assert evidence.planned_candidates[0]["model_id"] == "grok-fail"
            # In our evidence, the 'actual' is the successful attempt in the ladder
            assert evidence.attempts[-1].model == "gpt-success"
            assert evidence.attempts[-1].status == "success"
            assert evidence.final_status == "success"

def test_prescan_no_eligible_route_fails_closed(mock_config, mock_limiter):
    mock_config.allow_online_llm = True
    runner = GrokPassRunner(mock_config, limiter=mock_limiter)
    # Empty ladder
    routing_plan = {"candidate_routes": {"dedup": []}}
    evidence = ExecutionEvidence(pass_id="dedup", batch_id=None, planned_candidates=[])
    
    # Refactor note: if ladder is empty, it falls back to legacy if not careful.
    # But _call_grok_validated should exhaust.
    with patch.dict(os.environ, {}, clear=True): # No keys at all
         result = runner._call_grok_validated("dedup", "payload", routing_plan, evidence)
         assert result is None
         assert evidence.final_status == "exhausted"

def test_prescan_missing_credential_skips_route(mock_config, mock_limiter):
    mock_config.allow_online_llm = True
    runner = GrokPassRunner(mock_config, limiter=mock_limiter)
    routing_plan = {
        "candidate_routes": {
            "dedup": [
                {"provider": "xai", "model_id": "grok-no-key", "api_key_env": "MISSING_KEY"},
                {"provider": "openai", "model_id": "gpt-ok", "api_key_env": "OPENAI_API_KEY"}
            ]
        }
    }
    evidence = ExecutionEvidence(pass_id="dedup", batch_id=None, planned_candidates=routing_plan["candidate_routes"]["dedup"])
    
    # Mock _call_grok to behave like the real one: raise ValueError if key missing
    def side_effect(pass_id, payload, candidate, attempt_record, est_tokens=0):
        if candidate["api_key_env"] == "MISSING_KEY":
            raise ValueError("API key not found")
        attempt_record.status = "success"
        return {"status": "ok"}

    with patch.dict(os.environ, {"OPENAI_API_KEY": "valid-key"}):
        with patch.object(GrokPassRunner, "_call_grok", side_effect=side_effect):
            result = runner._call_grok_validated("dedup", "payload", routing_plan, evidence)
            assert result == {"status": "ok"}
            # grok-no-key: 2 attempts (exhausted)
            # gpt-ok: 1 attempt (success)
            assert len(evidence.attempts) == 3
            assert evidence.attempts[0].model == "grok-no-key"
            assert evidence.attempts[0].status == "failed"
            assert evidence.attempts[2].model == "gpt-ok"
            assert evidence.attempts[2].status == "success"
            assert evidence.final_status == "success"

def test_prescan_tpm_exceeded_blocks_call(mock_config):
    import time as _time_module
    # Set a limiter that will block immediately
    limiter = ProviderLimiter(config=ProviderRateConfig(rpm=1, tpm=10))
    # Initialize window start to prevent reset in acquire()
    limiter.token_window_start = _time_module.time()
    
    runner = GrokPassRunner(mock_config, limiter=limiter)
    candidate = {"provider": "mock", "model_id": "m1", "api_key_env": "K1"}
    attempt = ExecutionAttempt(provider="mock", model="m1", api_key_env="K1", status="pending")
    
    with patch.dict(os.environ, {"K1": "v1"}):
        # Current window already at 8 tokens
        limiter.tokens_used_window = 8
        # Next call asks for 5 tokens -> Total 13 > 10. Should wait.
        with patch("time.sleep") as mock_sleep:
            with patch("openai.OpenAI"):
                try:
                    runner._call_grok("dedup", "payload", candidate, attempt, est_tokens=5)
                except: pass
                assert mock_sleep.called
                assert attempt.limiter_wait_ms > 0

def test_prescan_attempt_artifact_schema(tmp_path):
    config = PrescanConfig(repo_root=tmp_path, output_dir=tmp_path, allow_online_llm=True)
    runner = GrokPassRunner(config)
    evidence = ExecutionEvidence(pass_id="test", batch_id="b1", planned_candidates=[])
    evidence.attempts.append(ExecutionAttempt(provider="p1", model="m1", api_key_env="k1", status="success"))
    runner.evidence_log.append(evidence)
    
    path = runner.save_attempts()
    data = json.loads(path.read_text())
    
    assert "evidence" in data
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["pass_id"] == "test"
    assert data["evidence"][0]["attempts"][0]["provider"] == "p1"

def test_prescan_limiter_acquire_called_before_request(mock_config):
    limiter = MagicMock(spec=ProviderLimiter)
    limiter.acquire.return_value = 0.0
    runner = GrokPassRunner(mock_config, limiter=limiter)
    
    candidate = {"provider": "mock", "model_id": "m1", "api_key_env": "K1"}
    attempt = MagicMock()
    
    with patch.dict(os.environ, {"K1": "v1"}):
        with patch("openai.OpenAI"):
            try:
                runner._call_grok("dedup", "payload", candidate, attempt, est_tokens=500)
            except:
                pass
            
            limiter.acquire.assert_called_once_with(500)
