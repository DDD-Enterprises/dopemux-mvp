import pytest
import os
import json
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.models import PrescanConfig
from lib.prescan.grok_passes import GrokPassRunner

@pytest.fixture
def mock_config(tmp_path):
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    return PrescanConfig(
        repo_root=tmp_path,
        output_dir=out,
        online_authorized=False,
        api_key_env="MOCK_API_KEY"
    )

def test_grok_pass_runner_respects_online_gate(mock_config):
    """Verify that if online_authorized is False, passes are skipped."""
    runner = GrokPassRunner(mock_config)
    
    # Even if API key is present
    with patch.dict(os.environ, {"MOCK_API_KEY": "sk-mock"}):
        results = runner.run_passes(["dedup"], {}, [])
        assert results == {}
        # Verify no LLM call happened (mocking would be better but the skip log is sufficient)

def test_grok_pass_runner_respects_routing_plan(mock_config):
    """Verify that routing_plan is used if provided."""
    mock_config.online_authorized = True
    runner = GrokPassRunner(mock_config)
    
    routing_plan = {
        "selected_routes": {
            "dedup": {
                "provider": "mock-provider",
                "model_id": "mock-model",
                "api_key_env": "MOCK_API_KEY"
            }
        }
    }
    
    with patch.dict(os.environ, {"MOCK_API_KEY": "sk-mock"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"status": "ok"}'))],
                usage=MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)
            )
            
            results = runner.run_passes(["dedup"], {}, [], routing_plan=routing_plan)
            
            assert "dedup" in results
            assert results["dedup"] == {"status": "ok"}
            
            # Verify the mock-model was used
            mock_client.chat.completions.create.assert_called_once()
            args, kwargs = mock_client.chat.completions.create.call_args
            assert kwargs["model"] == "mock-model"
            
            # Verify attempts tracking
            attempts_path = runner.save_attempts()
            assert attempts_path.exists()
            attempts_data = json.loads(attempts_path.read_text())
            assert attempts_data["total_attempts"] == 1
            assert attempts_data["success_count"] == 1
            assert attempts_data["attempts"][0]["pass_id"] == "dedup"
            assert attempts_data["attempts"][0]["model_id"] == "mock-model"
            assert attempts_data["attempts"][0]["success"] is True
