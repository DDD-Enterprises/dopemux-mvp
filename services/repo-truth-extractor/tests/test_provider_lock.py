"""Provider-lock for single-key cost profiles (Codex 3364972852, P2).

Cost profiles only rewrite the ${CELL} *lead* route per profile; the ladder's
*fallback* routes are hardcoded direct providers (e.g. xai/grok-4.3,
openai/gpt-5.5). For a genuinely single-key profile (openrouter-resilient: every
cell is openrouter/*, intended for an env with only OPENROUTER_API_KEY;
openai-heavy: every cell openai/*, single OPENAI_API_KEY) those direct fallbacks
break two ways:

1. Launch preflight enumerates the full ladder including direct fallbacks, so it
   probes XAI/OpenAI/Gemini keys the operator does not have and fails preflight.
2. Dispatch: if the locked lead fails, the ladder falls through to a
   direct-provider fallback that needs a key the operator lacks (primary AND
   repair/sidefill).

The fix adds provider-lock logic in _profile_provider_lock / _apply_provider_lock:
profiles whose declared cell_aliases all resolve to one provider are auto-locked
(unless they set allow_cross_provider_fallback=True). Locked profiles drop
cross-provider fallback routes at both preflight and dispatch. Multi-provider
profiles (value-default via allow_cross_provider_fallback, balanced-mix,
grok-fast, etc.) keep their direct fallbacks for real multi-key resilience.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402


def _make_cfg(**overrides):
    payload = {
        "dry_run": False,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": True,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "default",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 1,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "routing_policy": "balanced_openrouter",
    }
    payload.update(overrides)
    return runner.RunnerConfig(**payload)


# Profiles auto-locked (all cells single-provider, no allow_cross_provider_fallback).
# economy/quality/quality-mix are all-OpenAI by coincidence and are also
# auto-locked — their direct xai fallbacks are dropped at dispatch.
# value-default opts out via allow_cross_provider_fallback=True.
AUTO_LOCKED_PROFILES = {
    "openrouter-resilient": "openrouter",
    "openai-heavy": "openai",
    "economy": "openai",
    "quality": "openai",
    "quality-mix": "openai",
}
UNLOCKED_PROFILES = {
    "value-default",    # allow_cross_provider_fallback=True
    "experimental",     # mixed providers
    "gemini-value",     # mixed providers
    "grok-fast",        # mixed providers
    "balanced-mix",     # mixed providers
    "budget-mix",       # mixed providers
}


# ---------------------------------------------------------------------------
# Registry / invariants
# ---------------------------------------------------------------------------


def test_value_default_has_allow_cross_provider_fallback() -> None:
    # value-default must opt out of auto-lock so its direct xai fallbacks survive.
    assert runner.COST_PROFILES["value-default"].get("allow_cross_provider_fallback") is True


def test_unlocked_profiles_have_no_allow_cross_provider_fallback_block() -> None:
    # Profiles that are naturally multi-provider (mixed-cell) should NOT need the
    # opt-out flag — they're not auto-locked in the first place.
    for name in ("balanced-mix", "grok-fast", "gemini-value", "budget-mix"):
        profile = runner.COST_PROFILES[name]
        # Multi-provider: cells map to different providers, so auto-derive returns
        # None without needing the flag.
        aliases = profile.get("cell_aliases", {})
        providers = {
            runner._parse_alias_provider_model(str(v))[0]
            for v in aliases.values()
            if v and not runner._is_alias_placeholder(str(v))
        }
        assert len(providers) > 1, (
            f"{name} expected mixed providers, got {providers}"
        )


def test_auto_locked_profiles_have_single_provider_cells() -> None:
    for name, expected_lock in AUTO_LOCKED_PROFILES.items():
        profile = runner.COST_PROFILES[name]
        aliases = profile.get("cell_aliases", {})
        providers = {
            runner._parse_alias_provider_model(str(v))[0]
            for v in aliases.values()
            if v and not runner._is_alias_placeholder(str(v))
        }
        assert providers == {expected_lock}, (
            f"{name} expected single provider {expected_lock!r}, got {providers}"
        )


def test_profile_provider_lock_returns_correct_lock() -> None:
    assert (
        runner._profile_provider_lock(
            _make_cfg(cost_profile="openrouter-resilient")
        )
        == "openrouter"
    )
    assert (
        runner._profile_provider_lock(_make_cfg(cost_profile="openai-heavy"))
        == "openai"
    )
    assert (
        runner._profile_provider_lock(_make_cfg(cost_profile="value-default"))
        is None
    ), "value-default opts out via allow_cross_provider_fallback"
    assert (
        runner._profile_provider_lock(_make_cfg(cost_profile="balanced-mix"))
        is None
    ), "balanced-mix has mixed providers, not auto-locked"


# ---------------------------------------------------------------------------
# _apply_provider_lock filter unit
# ---------------------------------------------------------------------------


def test_apply_provider_lock_drops_foreign_fallback_routes() -> None:
    # openrouter-resilient: lead is openrouter, fallbacks xai + openai → dropped.
    cfg = _make_cfg(cost_profile="openrouter-resilient", routing_policy="openrouter")
    routes = [
        {"provider": "openrouter", "model_id": "openai/gpt-5.4-mini"},
        {"provider": "xai", "model_id": "grok-4.3"},
        {"provider": "openai", "model_id": "gpt-5.5"},
    ]
    kept = runner._apply_provider_lock(routes, cfg)
    assert [r["provider"] for r in kept] == ["openrouter"]


def test_apply_provider_lock_noop_for_unlocked_profile() -> None:
    cfg = _make_cfg(cost_profile="value-default", routing_policy="balanced_openrouter")
    routes = [
        {"provider": "openrouter", "model_id": "openai/gpt-5.4-mini"},
        {"provider": "xai", "model_id": "grok-4.3"},
    ]
    result = runner._apply_provider_lock(routes, cfg)
    assert result == routes


def test_apply_provider_lock_keeps_multiple_same_provider_routes() -> None:
    # openai-heavy: both openai routes kept, xai dropped.
    cfg = _make_cfg(cost_profile="openai-heavy", routing_policy="quality")
    routes = [
        {"provider": "openai", "model_id": "gpt-5.3-codex"},
        {"provider": "openai", "model_id": "gpt-5.5"},
        {"provider": "xai", "model_id": "grok-4.3"},
    ]
    kept = runner._apply_provider_lock(routes, cfg)
    assert [r["model_id"] for r in kept] == ["gpt-5.3-codex", "gpt-5.5"]


def test_apply_provider_lock_raises_on_foreign_lead() -> None:
    # Fail-closed: if the lead is foreign-provider under a locked profile, raise.
    cfg = _make_cfg(cost_profile="openrouter-resilient", routing_policy="openrouter")
    routes = [
        {"provider": "xai", "model_id": "grok-4.3"},      # lead is foreign
        {"provider": "openrouter", "model_id": "openai/gpt-5.4-mini"},
    ]
    with pytest.raises(RuntimeError, match="provider-locked"):
        runner._apply_provider_lock(routes, cfg)


# ---------------------------------------------------------------------------
# Dispatch: primary ladder (resolve_effective_step_route)
# ---------------------------------------------------------------------------


def _ladder_providers(route_info) -> list:
    return [str(row[0]).strip().lower() for row in route_info.get("ladder", [])]


def test_openrouter_resilient_bulk_ladder_drops_direct_xai_fallback() -> None:
    # A2 is BULK_DOCS_GENERAL: lead xai/${BULK_DOCS_MODEL}, fallback xai/grok-4.3.
    cfg = _make_cfg(cost_profile="openrouter-resilient", routing_policy="openrouter")
    route = runner.resolve_effective_step_route("A", "A2", cfg)
    assert _ladder_providers(route) == ["openrouter"]
    assert route["api_key_env"] == "OPENROUTER_API_KEY"


def test_openrouter_resilient_strict_ladder_drops_direct_openai_fallback() -> None:
    # A0 is CE (strict): lead openai/${CE_MODEL}, fallback openai/gpt-5.5 (direct).
    cfg = _make_cfg(cost_profile="openrouter-resilient", routing_policy="openrouter")
    route = runner.resolve_effective_step_route("A", "A0", cfg)
    assert _ladder_providers(route) == ["openrouter"]
    assert route["provider"] == "openrouter"
    assert route["model_id"].startswith("openai/")


def test_openai_heavy_bulk_ladder_drops_direct_xai_fallback() -> None:
    cfg = _make_cfg(cost_profile="openai-heavy", routing_policy="quality")
    route = runner.resolve_effective_step_route("A", "A2", cfg)
    assert _ladder_providers(route) == ["openai"]
    assert route["api_key_env"] == "OPENAI_API_KEY"


def test_unlocked_profile_keeps_direct_xai_fallback() -> None:
    # Control: value-default opts out of lock; its direct xai fallback on the bulk
    # lane is intentional resilience and must remain in the ladder.
    cfg = _make_cfg(cost_profile="value-default", routing_policy="balanced_openrouter")
    route = runner.resolve_effective_step_route("A", "A2", cfg)
    providers = _ladder_providers(route)
    assert "xai" in providers, f"expected direct xai fallback retained, got {providers}"


def test_locked_profile_override_to_foreign_provider_fails_closed() -> None:
    # An operator --model-alias that routes a locked profile's lead off-lock raises
    # rather than silently dispatching a cross-provider route.
    cfg = _make_cfg(
        cost_profile="openrouter-resilient",
        routing_policy="openrouter",
        model_alias_overrides=(("BULK_DOCS_MODEL", "xai/grok-4.3"),),
    )
    with pytest.raises(RuntimeError):
        runner.resolve_effective_step_route("A", "A2", cfg)


# ---------------------------------------------------------------------------
# Dispatch: repair/sidefill ladders (resolve_contract_routes)
# ---------------------------------------------------------------------------


def test_locked_profile_filters_repair_sidefill_fallbacks() -> None:
    cfg = _make_cfg(cost_profile="openrouter-resilient", routing_policy="openrouter")
    contract = runner._step_contract_for("A", "A0")  # CE strict, has openai fallback
    resolved = runner.resolve_contract_routes(contract, cfg)
    for stage in ("primary_routes", "repair_routes", "sidefill_routes"):
        rows = resolved["lane"].get(stage) or []
        providers = [str(r.get("provider")).strip().lower() for r in rows]
        assert providers, f"{stage} unexpectedly empty for a templated CE lane"
        assert set(providers) == {"openrouter"}, (
            f"{stage} kept non-openrouter route under lock: {providers}"
        )


def test_unlocked_profile_keeps_repair_sidefill_fallbacks() -> None:
    cfg = _make_cfg(cost_profile="value-default", routing_policy="balanced_openrouter")
    contract = runner._step_contract_for("A", "A2")  # bulk, xai fallback
    resolved = runner.resolve_contract_routes(contract, cfg)
    sidefill = resolved["lane"].get("sidefill_routes") or []
    providers = {str(r.get("provider")).strip().lower() for r in sidefill}
    assert "xai" in providers, f"expected xai fallback retained, got {providers}"


# ---------------------------------------------------------------------------
# Preflight: readiness summary requires only the locked provider's key
# ---------------------------------------------------------------------------


def _readiness_envs(summary) -> set:
    cats = summary["api_key_env_categories"]
    return set(cats["required_active_route"]) | set(cats["optional_fallback"])


def test_openrouter_resilient_preflight_requires_only_openrouter_key() -> None:
    # Phase A exercises both a strict CE lane (direct openai fallback) and a bulk
    # lane (direct xai fallback). Under the lock, both fallbacks are dropped, so
    # the only key an operator needs is OPENROUTER_API_KEY.
    summary = runner.derive_route_readiness_summary(
        ["A"], "openrouter", cost_profile="openrouter-resilient"
    )
    envs = _readiness_envs(summary)
    assert envs == {"OPENROUTER_API_KEY"}, envs


def test_openai_heavy_preflight_requires_only_openai_key() -> None:
    summary = runner.derive_route_readiness_summary(
        ["A"], "quality", cost_profile="openai-heavy"
    )
    envs = _readiness_envs(summary)
    assert envs == {"OPENAI_API_KEY"}, envs


def test_unlocked_preflight_still_enumerates_direct_fallback_keys() -> None:
    # Control: value-default phase A probes the direct xai fallback key too.
    summary = runner.derive_route_readiness_summary(
        ["A"], "balanced_openrouter", cost_profile="value-default"
    )
    envs = _readiness_envs(summary)
    assert "XAI_API_KEY" in envs, envs


# ---------------------------------------------------------------------------
# Comprehensive sweep: no foreign-provider route survives in any live stage
# ---------------------------------------------------------------------------


def _live_model_map_steps():
    import yaml as _yaml

    mm = SERVICE_ROOT / "promptsets" / "v4" / "model_map.yaml"
    data = _yaml.safe_load(mm.read_text(encoding="utf-8"))
    live = set(runner.PHASES)
    return [
        (str(s["phase"]), str(s["step_id"]))
        for s in data.get("steps", [])
        if str(s["phase"]) in live
    ]


@pytest.mark.parametrize(
    "profile,lock", sorted(AUTO_LOCKED_PROFILES.items())
)
def test_locked_profile_has_no_foreign_route_in_any_live_stage(profile, lock) -> None:
    # Sweep every live phase/step (orphan phase M excluded — not in PHASES, no
    # dispatch path). Every resolved primary/repair/sidefill route must be the
    # locked provider; the direct-provider fallbacks are gone everywhere.
    steps = _live_model_map_steps()
    assert steps, "expected live model_map steps"
    routing_policy = runner.COST_PROFILES[profile]["routing_policy"]
    cfg = _make_cfg(cost_profile=profile, routing_policy=routing_policy)
    checked = 0
    for phase, step_id in steps:
        contract = runner._step_contract_for(phase, step_id)
        if not isinstance(contract, dict):
            continue  # not a JSON-managed/laned step
        lane = (runner.resolve_contract_routes(contract, cfg) or {}).get("lane") or {}
        primary = lane.get("primary_routes") or []
        if not primary:
            continue  # no contract lane (legacy/policy-ladder step)
        checked += 1
        for stage in ("primary_routes", "repair_routes", "sidefill_routes"):
            for route in lane.get(stage) or []:
                provider = str(route.get("provider")).strip().lower()
                assert provider == lock, (
                    f"{profile} {phase}:{step_id} {stage} kept foreign route "
                    f"{provider}/{route.get('model_id')} under lock {lock!r}"
                )
    assert checked >= 20, f"expected many laned live steps checked, got {checked}"
