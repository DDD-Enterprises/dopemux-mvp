import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

def test_gemini_structured_output_mode_mapping() -> None:
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    
    from lib.structured_output_contracts import build_provider_step_contract_output
    
    # Mock route for Gemini with json_schema mode
    route = {
        "provider": "gemini",
        "model_id": "gemini-3.5-pro",
        "structured_output_mode": "json_schema",
        "strict_json_schema": True
    }
    
    step_contract = {
        "phase": "A",
        "step_id": "A1",
        "schema_id": "test_schema",
        "artifact_names": ["test_artifact"]
    }
    
    response_format, response_meta = build_provider_step_contract_output(
        route=route,
        transport="gemini_native",
        step_contract=step_contract,
        artifact_names=("test_artifact",)
    )
    
    assert response_meta["enabled"] is True
    assert response_meta["transport_mode"] == "response_json_schema"
    # For gemini_native, it should return the inner schema directly
    assert "type" in response_format
    assert response_format["type"] == "object"
    assert "properties" in response_format

def test_openai_structured_output_mode_mapping() -> None:
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    
    from lib.structured_output_contracts import build_provider_step_contract_output
    
    # Mock route for OpenAI with json_schema mode
    route = {
        "provider": "openai",
        "model_id": "gpt-5-pro",
        "structured_output_mode": "json_schema",
        "strict_json_schema": True
    }
    
    step_contract = {
        "phase": "A",
        "step_id": "A1",
        "schema_id": "test_schema",
        "artifact_names": ["test_artifact"]
    }
    
    response_format, response_meta = build_provider_step_contract_output(
        route=route,
        transport="openai_compat_http",
        step_contract=step_contract,
        artifact_names=("test_artifact",)
    )
    
    assert response_meta["enabled"] is True
    assert response_meta["transport_mode"] == "response_format_json_schema"
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True

def test_prescan_routing_plan_records_json_schema_mode() -> None:
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    from lib.prescan.provider_catalog import build_prescan_routing_plan
    from lib.prescan.models import PrescanConfig

    config = PrescanConfig(
        repo_root=root,
        output_dir=root / "tmp",
    )

    route = {
        "provider": "openai",
        "model_id": "gpt-5-nano",
        "api_key_env": "OPENAI_API_KEY",
        "available": True,
        "route_admissible": True,
        "prescan_tier": "cheap_structured",
        "pricing": {"input_1m_usd": 0.5, "output_1m_usd": 2.0},
        "structured_output_mode": "json_schema",
    }

    plan = build_prescan_routing_plan(
        config=config,
        catalog={
            "routes": [route]
        },
        readiness={
            "routes": [
                {
                    "provider": "openai",
                    "model_id": "gpt-5-nano",
                    "api_key_env": "OPENAI_API_KEY",
                    "status": "ready",
                    "ready": True
                }
            ]
        },
        passes=["dedup"],
    )
    assert "dedup" in plan["selected_routes"], f"Plan failures: {plan.get('failures')}"
    assert plan["selected_routes"]["dedup"]["structured_output_mode"] == "json_schema"
    assert plan["candidate_routes"]["dedup"][0]["structured_output_mode"] == "json_schema"
