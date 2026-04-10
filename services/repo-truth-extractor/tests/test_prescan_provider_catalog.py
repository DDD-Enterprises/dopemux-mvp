from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.models import PrescanConfig
from lib.prescan.provider_catalog import (
    PRESCAN_PASS_REQUIREMENTS,
    PRESCAN_TIER_RANK,
    SANCTIONED_PROVIDERS,
    _pricing,
    _select_route_for_tier,
    build_prescan_routing_plan,
    build_provider_model_catalog,
    classify_prescan_route,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_FAKE_LADDERS: dict[str, dict[str, list[tuple[str, str, str]]]] = {
    "cost": {
        "tier_1": [
            ("openai", "gpt-5-nano", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
        ],
        "tier_2": [
            ("openai", "gpt-5.3-codex", "OPENAI_API_KEY"),
        ],
    },
    "quality": {
        "tier_1": [
            ("openai", "gpt-5.4", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"),
        ],
    },
}

_FAKE_PROVIDER_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def _make_config(tmp_path: Path, **overrides: Any) -> PrescanConfig:
    defaults: dict[str, Any] = dict(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=False,
    )
    defaults.update(overrides)
    return PrescanConfig(**defaults)


def _available_route(
    provider: str,
    model_id: str,
    api_key_env: str,
    tier: str,
    input_1m: float = 1.0,
    output_1m: float = 4.0,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "model_id": model_id,
        "api_key_env": api_key_env,
        "available": True,
        "prescan_tier": tier,
        "pricing": {"input_1m_usd": input_1m, "output_1m_usd": output_1m},
    }


# ---------------------------------------------------------------------------
# classify_prescan_route
# ---------------------------------------------------------------------------


class TestClassifyPrescanRoute:
    def test_premium_model_returns_premium_planning(self) -> None:
        assert classify_prescan_route("openai", "gpt-5.4") == "premium_planning"
        assert classify_prescan_route("openai", "gpt-5.3-codex") == "premium_planning"
        assert classify_prescan_route("openai", "gpt-5.2") == "premium_planning"
        assert classify_prescan_route("openai", "claude-opus-4-6") == "premium_planning"
        assert classify_prescan_route("gemini", "gemini-2.5-pro") == "premium_planning"

    def test_cheap_model_returns_cheap_structured(self) -> None:
        assert classify_prescan_route("openai", "gpt-5-nano") == "cheap_structured"
        assert classify_prescan_route("openai", "gpt-4.1-nano") == "cheap_structured"
        assert classify_prescan_route("openai", "gpt-4o-mini") == "cheap_structured"
        assert classify_prescan_route("gemini", "gemini-2.5-flash") == "cheap_structured"
        assert classify_prescan_route("xai", "grok-code-fast") == "cheap_structured"

    def test_gemini_flash_variant_returns_cheap_structured(self) -> None:
        assert classify_prescan_route("gemini", "gemini-3-flash-preview") == "cheap_structured"

    def test_unknown_model_returns_balanced_analysis(self) -> None:
        assert classify_prescan_route("openai", "unknown-model-xyz") == "balanced_analysis"
        assert classify_prescan_route("xai", "grok-4.20-beta") == "balanced_analysis"

    def test_empty_model_id_returns_balanced_analysis(self) -> None:
        assert classify_prescan_route("openai", "") == "balanced_analysis"

    def test_case_insensitive_matching(self) -> None:
        assert classify_prescan_route("openai", "GPT-5.4") == "premium_planning"
        assert classify_prescan_route("openai", "GPT-5-NANO") == "cheap_structured"


# ---------------------------------------------------------------------------
# _pricing
# ---------------------------------------------------------------------------


class TestPricing:
    def test_pricing_returns_fallback_when_spend_ledger_unavailable(self) -> None:
        with patch("lib.prescan.provider_catalog.get_model_cost_rate", None):
            result = _pricing("openai", "some-model")
        assert result["input_1m_usd"] == 10.0
        assert result["output_1m_usd"] == 40.0
        assert result["pricing_authority"] == "fallback_default"

    def test_pricing_maps_spend_ledger_dict_fields(self) -> None:
        fake_rate = {
            "input_cost_per_1m_usd": 2.5,
            "output_cost_per_1m_usd": 8.0,
            "pricing_source": "route_registry_baseline",
        }
        mock_get_rate = MagicMock(return_value=fake_rate)
        with patch("lib.prescan.provider_catalog.get_model_cost_rate", mock_get_rate):
            result = _pricing("openai", "gpt-5.4")
        mock_get_rate.assert_called_once_with(provider="openai", model_id="gpt-5.4")
        assert result["input_1m_usd"] == 2.5
        assert result["output_1m_usd"] == 8.0
        assert result["pricing_authority"] == "shared_spend_ledger_registry"

    def test_pricing_falls_back_to_defaults_when_rate_keys_missing(self) -> None:
        mock_get_rate = MagicMock(return_value={})
        with patch("lib.prescan.provider_catalog.get_model_cost_rate", mock_get_rate):
            result = _pricing("xai", "grok-4.20-beta")
        assert result["input_1m_usd"] == 10.0
        assert result["output_1m_usd"] == 40.0
        assert result["pricing_authority"] == "shared_spend_ledger_registry"

    def test_pricing_returns_float_values(self) -> None:
        mock_get_rate = MagicMock(
            return_value={"input_cost_per_1m_usd": 1, "output_cost_per_1m_usd": 4}
        )
        with patch("lib.prescan.provider_catalog.get_model_cost_rate", mock_get_rate):
            result = _pricing("openai", "gpt-5-nano")
        assert isinstance(result["input_1m_usd"], float)
        assert isinstance(result["output_1m_usd"], float)


# ---------------------------------------------------------------------------
# build_provider_model_catalog
# ---------------------------------------------------------------------------


class TestBuildProviderModelCatalog:
    def test_catalog_includes_routes_from_active_routing_ladders(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        with patch(
            "lib.prescan.provider_catalog._load_runner_authority",
            return_value=(_FAKE_LADDERS, _FAKE_PROVIDER_ENV),
        ), patch(
            "lib.prescan.provider_catalog.get_model_cost_rate",
            return_value={"input_cost_per_1m_usd": 1.0, "output_cost_per_1m_usd": 4.0},
        ):
            catalog = build_provider_model_catalog(cfg)

        model_ids = [r["model_id"] for r in catalog["routes"]]
        assert "gpt-5-nano" in model_ids
        assert "gemini-2.5-flash" in model_ids
        assert "gpt-5.3-codex" in model_ids
        assert "gpt-5.4" in model_ids
        assert "gemini-2.5-pro" in model_ids

    def test_catalog_deduplicates_same_provider_model_pair(self, tmp_path: Path) -> None:
        ladders = {
            "cost": {
                "tier_1": [("openai", "gpt-5-nano", "OPENAI_API_KEY")],
            },
            "quality": {
                "tier_1": [("openai", "gpt-5-nano", "OPENAI_API_KEY")],
            },
        }
        cfg = _make_config(tmp_path)
        with patch(
            "lib.prescan.provider_catalog._load_runner_authority",
            return_value=(ladders, {}),
        ), patch(
            "lib.prescan.provider_catalog.get_model_cost_rate",
            return_value={"input_cost_per_1m_usd": 1.0, "output_cost_per_1m_usd": 4.0},
        ):
            catalog = build_provider_model_catalog(cfg)

        nano_routes = [r for r in catalog["routes"] if r["model_id"] == "gpt-5-nano"]
        assert len(nano_routes) == 1
        # The two source policies should be recorded in the single entry
        policies = [s["policy"] for s in nano_routes[0]["sources"]]
        assert "cost" in policies
        assert "quality" in policies

    def test_catalog_marks_availability_by_env_var(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        with patch(
            "lib.prescan.provider_catalog._load_runner_authority",
            return_value=(_FAKE_LADDERS, _FAKE_PROVIDER_ENV),
        ), patch(
            "lib.prescan.provider_catalog.get_model_cost_rate",
            return_value={"input_cost_per_1m_usd": 1.0, "output_cost_per_1m_usd": 4.0},
        ), patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key", "GEMINI_API_KEY": ""}, clear=False):
            catalog = build_provider_model_catalog(cfg)

        openai_routes = [r for r in catalog["routes"] if r["provider"] == "openai"]
        gemini_routes = [r for r in catalog["routes"] if r["provider"] == "gemini"]
        assert all(r["available"] is True for r in openai_routes)
        assert all(r["available"] is False for r in gemini_routes)

    def test_catalog_assigns_prescan_tier_to_each_route(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        with patch(
            "lib.prescan.provider_catalog._load_runner_authority",
            return_value=(_FAKE_LADDERS, _FAKE_PROVIDER_ENV),
        ), patch(
            "lib.prescan.provider_catalog.get_model_cost_rate",
            return_value={"input_cost_per_1m_usd": 1.0, "output_cost_per_1m_usd": 4.0},
        ):
            catalog = build_provider_model_catalog(cfg)

        tier_map = {r["model_id"]: r["prescan_tier"] for r in catalog["routes"]}
        assert tier_map["gpt-5-nano"] == "cheap_structured"
        assert tier_map["gemini-2.5-flash"] == "cheap_structured"
        assert tier_map["gpt-5.3-codex"] == "premium_planning"
        assert tier_map["gpt-5.4"] == "premium_planning"
        assert tier_map["gemini-2.5-pro"] == "premium_planning"

    def test_catalog_includes_legacy_prescan_config_entry(self, tmp_path: Path) -> None:
        cfg = _make_config(
            tmp_path,
            provider="xai",
            model="grok-4.20-beta-0309-non-reasoning",
            api_key_env="XAI_API_KEY",
        )
        with patch(
            "lib.prescan.provider_catalog._load_runner_authority",
            return_value=({}, {}),
        ), patch(
            "lib.prescan.provider_catalog.get_model_cost_rate",
            return_value={"input_cost_per_1m_usd": 1.0, "output_cost_per_1m_usd": 4.0},
        ):
            catalog = build_provider_model_catalog(cfg)

        xai_routes = [r for r in catalog["routes"] if r["provider"] == "xai"]
        assert len(xai_routes) == 1
        assert any(
            s["policy"] == "legacy_prescan_config" for s in xai_routes[0]["sources"]
        )

    def test_catalog_excludes_unsanctioned_providers(self, tmp_path: Path) -> None:
        ladders = {
            "cost": {
                "tier_1": [
                    ("openai", "gpt-5-nano", "OPENAI_API_KEY"),
                    ("fakeprovider", "some-model", "FAKE_KEY"),
                ]
            }
        }
        cfg = _make_config(tmp_path)
        with patch(
            "lib.prescan.provider_catalog._load_runner_authority",
            return_value=(ladders, {}),
        ), patch(
            "lib.prescan.provider_catalog.get_model_cost_rate",
            return_value={"input_cost_per_1m_usd": 1.0, "output_cost_per_1m_usd": 4.0},
        ):
            catalog = build_provider_model_catalog(cfg)

        providers = {r["provider"] for r in catalog["routes"]}
        assert "fakeprovider" not in providers
        assert providers.issubset(set(SANCTIONED_PROVIDERS))

    def test_catalog_structure_has_required_top_level_keys(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        with patch(
            "lib.prescan.provider_catalog._load_runner_authority",
            return_value=(_FAKE_LADDERS, _FAKE_PROVIDER_ENV),
        ), patch(
            "lib.prescan.provider_catalog.get_model_cost_rate",
            return_value={"input_cost_per_1m_usd": 1.0, "output_cost_per_1m_usd": 4.0},
        ):
            catalog = build_provider_model_catalog(cfg)

        assert "generated_from" in catalog
        assert "sanctioned_providers" in catalog
        assert "routes" in catalog
        assert isinstance(catalog["routes"], list)


# ---------------------------------------------------------------------------
# _select_route_for_tier
# ---------------------------------------------------------------------------


class TestSelectRouteForTier:
    def test_selects_exact_tier_when_available(self) -> None:
        routes = [
            _available_route("openai", "gpt-5-nano", "OPENAI_API_KEY", "cheap_structured", 1.0, 4.0),
            _available_route("openai", "gpt-5.4", "OPENAI_API_KEY", "premium_planning", 10.0, 40.0),
        ]
        selected, adjustment = _select_route_for_tier(routes, "cheap_structured")
        assert selected is not None
        assert selected["model_id"] == "gpt-5-nano"
        assert adjustment == "exact"

    def test_upgrades_to_higher_tier_when_required_not_available(self) -> None:
        routes = [
            _available_route("openai", "gpt-5.3-codex", "OPENAI_API_KEY", "premium_planning", 5.0, 20.0),
        ]
        selected, adjustment = _select_route_for_tier(routes, "balanced_analysis")
        assert selected is not None
        assert selected["prescan_tier"] == "premium_planning"
        assert adjustment == "upgrade"

    def test_returns_none_when_no_eligible_routes(self) -> None:
        routes = [
            _available_route("openai", "gpt-5-nano", "OPENAI_API_KEY", "cheap_structured"),
        ]
        selected, adjustment = _select_route_for_tier(routes, "premium_planning")
        assert selected is None
        assert adjustment is None

    def test_selects_lowest_cost_within_eligible_tier_band(self) -> None:
        routes = [
            _available_route("openai", "gpt-5.4", "OPENAI_API_KEY", "premium_planning", 20.0, 80.0),
            _available_route("openai", "gpt-5.3-codex", "OPENAI_API_KEY", "premium_planning", 5.0, 20.0),
            _available_route("gemini", "gemini-2.5-pro", "GEMINI_API_KEY", "premium_planning", 8.0, 32.0),
        ]
        selected, _ = _select_route_for_tier(routes, "premium_planning")
        assert selected is not None
        assert selected["model_id"] == "gpt-5.3-codex"

    def test_empty_routes_returns_none(self) -> None:
        selected, adjustment = _select_route_for_tier([], "cheap_structured")
        assert selected is None
        assert adjustment is None


# ---------------------------------------------------------------------------
# build_prescan_routing_plan  (tier-based selection per prescan pass)
# ---------------------------------------------------------------------------


class TestBuildPrescanRoutingPlan:
    def _make_catalog_with_all_tiers(self) -> dict[str, Any]:
        return {
            "routes": [
                _available_route("openai", "gpt-5-nano", "OPENAI_API_KEY", "cheap_structured", 0.5, 2.0),
                _available_route("openai", "gpt-5.2", "OPENAI_API_KEY", "balanced_analysis", 3.0, 12.0),
                _available_route("openai", "gpt-5.4", "OPENAI_API_KEY", "premium_planning", 10.0, 40.0),
            ]
        }

    def test_dedup_pass_selects_cheap_structured_tier(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=["dedup"])
        route = plan["selected_routes"]["dedup"]
        assert route["required_tier"] == "cheap_structured"
        assert route["selected_tier"] in PRESCAN_TIER_RANK
        assert PRESCAN_TIER_RANK[route["selected_tier"]] >= PRESCAN_TIER_RANK["cheap_structured"]

    def test_discover_pass_selects_cheap_structured_tier(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=["discover"])
        route = plan["selected_routes"]["discover"]
        assert route["required_tier"] == "cheap_structured"
        assert PRESCAN_TIER_RANK[route["selected_tier"]] >= PRESCAN_TIER_RANK["cheap_structured"]

    def test_feasibility_pass_selects_balanced_or_higher_tier(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=["feasibility"])
        route = plan["selected_routes"]["feasibility"]
        assert route["required_tier"] == "balanced_analysis"
        assert PRESCAN_TIER_RANK[route["selected_tier"]] >= PRESCAN_TIER_RANK["balanced_analysis"]

    def test_optimize_pass_selects_premium_tier(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=["optimize"])
        route = plan["selected_routes"]["optimize"]
        assert route["required_tier"] == "premium_planning"
        assert PRESCAN_TIER_RANK[route["selected_tier"]] >= PRESCAN_TIER_RANK["premium_planning"]

    def test_plan_status_is_pass_when_all_routes_resolved(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=list(PRESCAN_PASS_REQUIREMENTS))
        assert plan["status"] == "PASS"
        assert plan["failures"] == []
        assert set(plan["selected_routes"].keys()) == set(PRESCAN_PASS_REQUIREMENTS.keys())

    def test_plan_status_is_fail_when_required_tier_unavailable(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        # Only cheap_structured available — premium_planning not satisfiable
        catalog = {
            "routes": [
                _available_route("openai", "gpt-5-nano", "OPENAI_API_KEY", "cheap_structured"),
            ]
        }
        plan = build_prescan_routing_plan(cfg, catalog, passes=["optimize"])
        assert plan["status"] == "FAIL"
        assert len(plan["failures"]) == 1
        assert plan["failures"][0]["pass_id"] == "optimize"
        assert plan["failures"][0]["required_tier"] == "premium_planning"

    def test_plan_excludes_unavailable_routes(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = {
            "routes": [
                {
                    **_available_route("openai", "gpt-5-nano", "OPENAI_API_KEY", "cheap_structured"),
                    "available": False,
                }
            ]
        }
        plan = build_prescan_routing_plan(cfg, catalog, passes=["dedup"])
        assert plan["status"] == "FAIL"
        assert "dedup" not in plan["selected_routes"]

    def test_plan_ignores_unknown_pass_ids(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=["none", "dedup", "unknown_pass"])
        assert "none" not in plan["selected_routes"]
        assert "unknown_pass" not in plan["selected_routes"]
        assert "dedup" in plan["selected_routes"]

    def test_plan_with_none_passes_returns_empty_plan(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=None)
        assert plan["requested_passes"] == []
        assert plan["selected_routes"] == {}
        assert plan["status"] == "PASS"

    def test_plan_route_records_legacy_change_flag(self, tmp_path: Path) -> None:
        cfg = _make_config(
            tmp_path,
            provider="xai",
            model="grok-4.20-beta",
            api_key_env="XAI_API_KEY",
        )
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=["dedup"])
        route = plan["selected_routes"]["dedup"]
        # Selected route (openai/gpt-5-nano) differs from config (xai/grok-4.20-beta)
        assert route["legacy_route_changed"] is True

    def test_plan_route_includes_pricing_info(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        catalog = self._make_catalog_with_all_tiers()
        plan = build_prescan_routing_plan(cfg, catalog, passes=["dedup"])
        route = plan["selected_routes"]["dedup"]
        assert "pricing" in route
        assert "input_1m_usd" in route["pricing"]
        assert "output_1m_usd" in route["pricing"]
