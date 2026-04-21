import pytest
import os
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from lib.prescan.models import PrescanConfig
from lib.prescan.grok_passes import GrokPassRunner, SecurityViolation

@pytest.fixture
def mock_config(tmp_path):
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    return PrescanConfig(
        repo_root=tmp_path,
        output_dir=out,
        allow_online_llm=False,
        api_key_env="XAI_API_KEY"
    )

def test_prescan_online_gate_enforced(mock_config):
    """VERIFY: If allow_online_llm is False, SecurityViolation is raised at the call boundary."""
    runner = GrokPassRunner(mock_config)
    candidate = {"provider": "openai", "model_id": "gpt-5", "api_key_env": "OPENAI_API_KEY"}
    attempt = MagicMock()
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        with pytest.raises(SecurityViolation) as excinfo:
            runner._call_grok("dedup", "payload", candidate, attempt)
        assert "Spend gate blocked call" in str(excinfo.value)

def test_prescan_route_divergence_recorded(mock_config):
    """VERIFY: Primary fails, fallback succeeds, artifact records both attempts."""
    mock_config.allow_online_llm = True
    runner = GrokPassRunner(mock_config)
    
    routing_plan = {
        "candidate_routes": {
            "dedup": [
                {"provider": "openai", "model_id": "primary-fail", "api_key_env": "KEY1"},
                {"provider": "openai", "model_id": "fallback-win", "api_key_env": "KEY2"}
            ]
        }
    }
    
    with patch.dict(os.environ, {"KEY1": "sk1", "KEY2": "sk2"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Simulate failure (primary), failure (retry primary), then success (fallback)
            mock_client.chat.completions.create.side_effect = [
                Exception("Primary Overloaded"),
                Exception("Primary Still Overloaded"),
                MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                content='{"duplicate_assessments": [], "version_chain_summaries": [], "divergent_pairs": []}'
                            )
                        )
                    ],
                    usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                )
            ]
            
            results = runner.run_passes(["dedup"], {}, [], routing_plan=routing_plan)
            
            assert "dedup" in results
            
            # Check Evidence
            attempts_path = runner.save_attempts()
            data = json.loads(attempts_path.read_text())
            
            evidence = data["evidence"][0]
            assert evidence["pass_id"] == "dedup"
            assert evidence["final_status"] == "success"
            # 2 attempts for first candidate + 1 for second = 3
            assert len(evidence["attempts"]) == 3
            
            # Verify attempt order and status
            assert evidence["attempts"][0]["model"] == "primary-fail"
            assert evidence["attempts"][0]["status"] == "failed"
            
            assert evidence["attempts"][1]["model"] == "primary-fail"
            assert evidence["attempts"][1]["status"] == "failed"
            
            assert evidence["attempts"][2]["model"] == "fallback-win"
            assert evidence["attempts"][2]["status"] == "success"

def test_prescan_no_eligible_route_fails_closed(mock_config):
    """VERIFY: All candidates fail -> returns None, records exhausted."""
    mock_config.allow_online_llm = True
    runner = GrokPassRunner(mock_config)
    
    routing_plan = {
        "candidate_routes": {
            "dedup": [
                {"provider": "openai", "model_id": "fail1", "api_key_env": "KEY1"},
                {"provider": "openai", "model_id": "fail2", "api_key_env": "KEY1"}
            ]
        }
    }
    
    with patch.dict(os.environ, {"KEY1": "sk1"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("Hard Fail")
            
            results = runner.run_passes(["dedup"], {}, [], routing_plan=routing_plan)
            
            assert results == {}
            
            data = json.loads(runner.save_attempts().read_text())
            evidence = data["evidence"][0]
            assert evidence["final_status"] == "exhausted"
            # 2 candidates * (1 primary + 1 retry) = 4 attempts total
            assert len(evidence["attempts"]) == 4 

def test_prescan_missing_credential_skips_route(mock_config):
    """VERIFY: Missing credential mid-ladder skips attempt."""
    mock_config.allow_online_llm = True
    runner = GrokPassRunner(mock_config)
    
    routing_plan = {
        "candidate_routes": {
            "dedup": [
                {"provider": "openai", "model_id": "no-key", "api_key_env": "MISSING_KEY"},
                {"provider": "openai", "model_id": "ok-key", "api_key_env": "EXISTING_KEY"}
            ]
        }
    }
    
    with patch.dict(os.environ, {"EXISTING_KEY": "sk-ok"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content='{"duplicate_assessments": [], "version_chain_summaries": [], "divergent_pairs": []}'
                        )
                    )
                ],
                usage=MagicMock(prompt_tokens=1, completion_tokens=1, total_tokens=2)
            )
            
            results = runner.run_passes(["dedup"], {}, [], routing_plan=routing_plan)
            
            data = json.loads(runner.save_attempts().read_text())
            evidence = data["evidence"][0]
            
            assert evidence["attempts"][0]["model"] == "no-key"
            assert evidence["attempts"][0]["status"] == "failed"
            assert "API key not found" in evidence["attempts"][0]["error"]

def test_prescan_limiter_tpm_exceeded_blocks_call(mock_config):
    """VERIFY: If limiter acquire() is called, it respects the wait."""
    mock_config.allow_online_llm = True
    mock_limiter = MagicMock()
    mock_limiter.acquire.return_value = 0.5 # Wait 0.5s
    
    runner = GrokPassRunner(mock_config, limiter=mock_limiter)
    candidate = {"provider": "openai", "model_id": "m1", "api_key_env": "K"}
    attempt = MagicMock()
    
    with patch.dict(os.environ, {"K": "sk"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content='{"duplicate_assessments": [], "version_chain_summaries": [], "divergent_pairs": []}'
                        )
                    )
                ],
                usage=None
            )
            
            runner._call_grok("dedup", "p", candidate, attempt, est_tokens=100)
            
            mock_limiter.acquire.assert_called_once_with(100)
            assert attempt.limiter_wait_ms == 500.0

def test_prescan_attempt_artifact_schema(mock_config):
    """VERIFY: Artifact schema matches expected structure for audit."""
    mock_config.allow_online_llm = True
    runner = GrokPassRunner(mock_config)
    
    routing_plan = {"candidate_routes": {"dedup": [{"provider": "mock", "model_id": "m1", "api_key_env": "K"}]}}
    
    with patch.dict(os.environ, {"K": "sk"}):
        runner.run_passes(["dedup"], {}, [], routing_plan=routing_plan)
        path = runner.save_attempts()
        data = json.loads(path.read_text())
        
        assert "generated_at" in data
        assert "evidence" in data
        ev = data["evidence"][0]
        assert "pass_id" in ev
        assert "attempts" in ev
        assert "final_status" in ev
        assert "planned_candidates" in ev
        
        att = ev["attempts"][0]
        assert "provider" in att
        assert "model" in att
        assert "status" in att
        assert "latency_ms" in att
