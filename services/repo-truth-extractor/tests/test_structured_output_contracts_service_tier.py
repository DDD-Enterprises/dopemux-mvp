"""Tests for service_tier passthrough in route_entries_for_stage().

Covers TP-RTE-COSTPROFILE-E3-CONTRACTS-001 S3/S7: route_entries_for_stage()
copies service_tier from each raw route row into the returned normalized row
and defaults to None when absent. Adding the field must not affect any other
returned field, and every stage (primary/repair/sidefill) must honor it.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_service_root_on_path() -> None:
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))


_ensure_service_root_on_path()
from lib.structured_output_contracts import route_entries_for_stage  # noqa: E402


def _step_contract_with_routes(
    *,
    primary: list | None = None,
    repair: list | None = None,
    sidefill: list | None = None,
) -> dict:
    lane: dict = {}
    if primary is not None:
        lane["primary_routes"] = primary
    if repair is not None:
        lane["repair_routes"] = repair
    if sidefill is not None:
        lane["sidefill_routes"] = sidefill
    return {"phase": "A", "step_id": "A1", "lane": lane}


def test_service_tier_propagates_when_present() -> None:
    contract = _step_contract_with_routes(
        primary=[
            {
                "provider": "openai",
                "model_id": "gpt-5",
                "api_key_env": "OPENAI_API_KEY",
                "service_tier": "flex",
            }
        ]
    )
    rows = route_entries_for_stage(contract, "primary")
    assert len(rows) == 1
    assert rows[0]["service_tier"] == "flex"


def test_service_tier_defaults_to_none_when_absent() -> None:
    contract = _step_contract_with_routes(
        primary=[
            {
                "provider": "openai",
                "model_id": "gpt-5",
                "api_key_env": "OPENAI_API_KEY",
            }
        ]
    )
    rows = route_entries_for_stage(contract, "primary")
    assert len(rows) == 1
    assert rows[0]["service_tier"] is None


def test_service_tier_independent_per_route_in_same_stage() -> None:
    contract = _step_contract_with_routes(
        primary=[
            {
                "provider": "openai",
                "model_id": "gpt-5",
                "api_key_env": "OPENAI_API_KEY",
                "service_tier": "priority",
            },
            {
                "provider": "openrouter",
                "model_id": "openai/gpt-5",
                "api_key_env": "OPENROUTER_API_KEY",
                "service_tier": "default",
            },
            {
                "provider": "anthropic",
                "model_id": "claude-opus-4.6",
                "api_key_env": "ANTHROPIC_API_KEY",
            },
        ]
    )
    rows = route_entries_for_stage(contract, "primary")
    assert [row["service_tier"] for row in rows] == ["priority", "default", None]


def test_service_tier_propagates_across_all_three_stages() -> None:
    contract = _step_contract_with_routes(
        primary=[
            {
                "provider": "openai",
                "model_id": "gpt-5",
                "api_key_env": "OPENAI_API_KEY",
                "service_tier": "flex",
            }
        ],
        repair=[
            {
                "provider": "openai",
                "model_id": "gpt-5",
                "api_key_env": "OPENAI_API_KEY",
                "service_tier": "priority",
            }
        ],
        sidefill=[
            {
                "provider": "openrouter",
                "model_id": "openai/gpt-5",
                "api_key_env": "OPENROUTER_API_KEY",
                "service_tier": "default",
            }
        ],
    )
    assert route_entries_for_stage(contract, "primary")[0]["service_tier"] == "flex"
    assert route_entries_for_stage(contract, "repair")[0]["service_tier"] == "priority"
    assert route_entries_for_stage(contract, "sidefill")[0]["service_tier"] == "default"


def test_other_fields_unchanged_when_service_tier_added() -> None:
    """Regression: adding service_tier must not alter other normalized fields."""
    contract = _step_contract_with_routes(
        primary=[
            {
                "provider": "openai",
                "model_id": "gpt-5",
                "api_key_env": "OPENAI_API_KEY",
                "structured_output_mode": "json_schema",
                "strict_json_schema": True,
                "strict_passthrough_verified": False,
                "service_tier": "flex",
            }
        ]
    )
    row = route_entries_for_stage(contract, "primary")[0]
    assert row["provider"] == "openai"
    assert row["model_id"] == "gpt-5"
    assert row["api_key_env"] == "OPENAI_API_KEY"
    assert row["structured_output_mode"] == "json_schema"
    assert row["strict_json_schema"] is True
    assert row["strict_passthrough_verified"] is False
    assert row["service_tier"] == "flex"


def test_service_tier_string_normalization() -> None:
    """Whitespace stripped; non-string and empty-string both yield None."""
    contract = _step_contract_with_routes(
        primary=[
            {
                "provider": "openai",
                "model_id": "gpt-5",
                "api_key_env": "OPENAI_API_KEY",
                "service_tier": "  flex  ",
            },
            {
                "provider": "openai",
                "model_id": "gpt-5-mini",
                "api_key_env": "OPENAI_API_KEY",
                "service_tier": "",
            },
            {
                "provider": "openai",
                "model_id": "gpt-5-nano",
                "api_key_env": "OPENAI_API_KEY",
                "service_tier": 42,
            },
        ]
    )
    rows = route_entries_for_stage(contract, "primary")
    assert rows[0]["service_tier"] == "flex"
    assert rows[1]["service_tier"] is None
    assert rows[2]["service_tier"] is None
