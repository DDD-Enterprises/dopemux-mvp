import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from run_extraction_v5 import (
    RunnerConfig,
    execute_step_for_partitions,
    PromptSpec,
)
from lib.intelligence_router import IntelligenceRouter

@pytest.fixture
def mock_router():
    router = MagicMock(spec=IntelligenceRouter)
    router.code_report = {"hotspots": [], "pagerank_scores": {}, "signature_index": {}}
    router.reorder_partition.side_effect = lambda x: x
    # Default is standard
    router.get_model_tier.return_value = "standard"
    return router

def test_intelligence_driven_routing_upgrade(tmp_path: Path, mock_router):
    # Setup: a partition with one 'premium' hotspot file
    phase = "C"
    step_id = "C1"
    partition_id = "p1"
    hotspot_file = "src/critical_logic.py"
    
    partitions = [
        {
            "id": partition_id,
            "paths": [hotspot_file],
            "context_brief": "Some context."
        }
    ]
    
    # Configure router to recommend premium for this file
    mock_router.get_model_tier.side_effect = lambda p: "premium" if p == hotspot_file else "standard"
    
    cfg = RunnerConfig(
        dry_run=True, # Dry run is enough to see the routing decision
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=5000,
        file_truncate_chars=1000,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=True,
        gemini_auth_mode="api_key",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="constant",
        retry_max_attempts=1,
        retry_base_seconds=1.0,
        retry_max_seconds=1.0,
        phase_auth_fail_threshold=1,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced",
        router=mock_router
    )
    
    prompt_spec = PromptSpec(
        step_id=step_id,
        prompt_path=tmp_path / "prompt.md",
        output_artifacts=("result.json",),
        tier_override=None
    )
    (tmp_path / "prompt.md").write_text("Extract truth.")
    
    phase_dir = tmp_path / "phase_c"
    (phase_dir / "raw").mkdir(parents=True)
    
    mock_resolve = MagicMock()
    runner_globals = execute_step_for_partitions.__globals__
    with patch.dict(
        runner_globals,
        {
            "_ACTIVE_INTELLIGENCE_ROUTER": mock_router,
            "resolve_effective_step_route": mock_resolve,
        },
    ):
        
        # Initial call for the whole step (standard tier)
        mock_resolve.return_value = {
            "step_tier": "extract",
            "step_type": "code",
            "ladder": [("openai", "gpt-4o-mini", "OPENAI_API_KEY")],
            "provider": "openai",
            "model_id": "gpt-4o-mini",
            "reason": "default"
        }
        
        # Second call for the partition upgrade (premium tier)
        def side_effect(*args, **kwargs):
            if kwargs.get("tier_override") == "synthesis":
                return {
                    "step_tier": "synthesis",
                    "step_type": "code",
                    "ladder": [("openai", "gpt-4o", "OPENAI_API_KEY")],
                    "provider": "openai",
                    "model_id": "gpt-4o",
                    "reason": "intelligence_upgrade"
                }
            return mock_resolve.return_value
            
        mock_resolve.side_effect = side_effect

        results = execute_step_for_partitions(
            phase=phase,
            prompt_spec=prompt_spec,
            partitions=partitions,
            phase_dir=phase_dir,
            cfg=cfg
        )
        
        # Verify
        assert results["ok"] == 0 # Dry run doesn't count as 'ok' in results summary usually, wait let's check
        
        # Check if the upgrade was logged
        # We need to capture logs or check the partition result metadata
        # Since execute_step_for_partitions returns a summary, we check the emitted JSON
        
        output_json = phase_dir / "raw" / f"{step_id}__{partition_id}.json"
        assert output_json.exists()
        with open(output_json) as f:
            data = json.load(f)
            req_meta = data.get("request_meta", {})
            assert req_meta.get("model_id") == "gpt-4o"
            assert req_meta.get("routing_tier") == "synthesis"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
