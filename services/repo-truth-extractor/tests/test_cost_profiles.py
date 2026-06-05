"""Cost profile registry + CLI integration (Phase E6).

Covers:
- COST_PROFILES has the 4 expected profiles with required fields.
- LEGACY_ROUTING_POLICY_TO_COST_PROFILE covers all 8 legacy values.
- resolve_cost_profile() handles new names, legacy names, None, and garbage.
- resolve_cell_alias() resolves ${KEY} from the profile's cell_aliases dict,
  honors CLI overrides, falls back to env, and passes through bare model IDs.
- --cost-profile + --disable-provider + --model-alias CLI flags appear in --help.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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


EXPECTED_PROFILES = {
    "economy",
    "value-default",
    "quality",
    "experimental",
    "gemini-value",
    "grok-fast",
    "openrouter-resilient",
    "openai-heavy",
    "balanced-mix",
    "quality-mix",
    "budget-mix",
}


def test_cost_profiles_registry_has_expected_profiles() -> None:
    assert set(runner.COST_PROFILES.keys()) == EXPECTED_PROFILES


def test_default_cost_profile_is_value_default() -> None:
    assert runner.DEFAULT_COST_PROFILE == "value-default"


def test_each_profile_has_required_fields() -> None:
    required = {
        "routing_policy",
        "default_service_tier",
        "enable_cached_input",
        "enable_batch_when_supported",
        "escalation_max_hops",
        "max_cost_usd_default",
        "cost_cap_mode",
        "notes",
        "cell_aliases",
    }
    for name, profile in runner.COST_PROFILES.items():
        missing = required - set(profile.keys())
        assert not missing, f"profile {name} missing fields: {missing}"
        # Every profile must define all four canonical, profile-agnostic cell
        # keys so a shared model_map.yaml resolves under any --cost-profile.
        cells = set(profile["cell_aliases"].keys())
        missing_cells = set(runner.COST_PROFILE_CELL_KEYS) - cells
        assert not missing_cells, f"profile {name} missing cells: {missing_cells}"
        # And no leftover profile-prefixed legacy keys.
        extra = cells - set(runner.COST_PROFILE_CELL_KEYS)
        assert not extra, f"profile {name} has non-canonical cell keys: {extra}"


def test_new_profiles_set_a_cost_cap() -> None:
    # value-default and quality are intentionally uncapped (operator explicitly
    # accepts cost for the default + production go/no-go lanes). Every other
    # profile — including all Plan B additions — MUST carry a numeric cap so we
    # don't repeat the audit's uncapped-profile finding.
    uncapped_by_design = {"value-default", "quality"}
    for name, profile in runner.COST_PROFILES.items():
        if name in uncapped_by_design:
            continue
        cap = profile["max_cost_usd_default"]
        assert isinstance(cap, (int, float)), f"profile {name} has no cost cap"


def test_all_strict_cells_resolve_to_allowed_providers() -> None:
    # Fail-closed contract: every profile's strict cells (CE/SYNTH) must resolve
    # to a strict-capable provider {openai, openrouter}.
    for name, profile in runner.COST_PROFILES.items():
        for cell in runner.COST_PROFILE_STRICT_CELL_KEYS:
            value = profile["cell_aliases"][cell]
            provider, _model = runner._parse_alias_provider_model(value)
            assert provider in runner.STRICT_ALLOWED_PROVIDERS, (
                f"profile {name} strict cell {cell}={value!r} resolves to "
                f"disallowed provider {provider!r}"
            )


def test_legacy_routing_policy_map_covers_all_eight_legacy_names() -> None:
    legacy_names = {
        "cost",
        "balanced",
        "balanced_openrouter",
        "balanced_grok_openrouter",
        "openrouter",
        "gemini_primary",
        "quality",
        "optimal",
    }
    mapped = set(runner.LEGACY_ROUTING_POLICY_TO_COST_PROFILE.keys())
    assert legacy_names == mapped


def test_legacy_balanced_openrouter_maps_to_value_default() -> None:
    name, profile = runner.resolve_cost_profile("balanced_openrouter")
    assert name == "value-default"
    assert profile["routing_policy"] == "balanced_openrouter"


def test_resolve_cost_profile_handles_all_inputs() -> None:
    # None and "" → default
    assert runner.resolve_cost_profile(None)[0] == "value-default"
    assert runner.resolve_cost_profile("")[0] == "value-default"
    # Canonical name passes through
    assert runner.resolve_cost_profile("quality")[0] == "quality"
    # Legacy name maps
    assert runner.resolve_cost_profile("optimal")[0] == "quality"
    # Garbage → default (not error)
    assert runner.resolve_cost_profile("does_not_exist")[0] == "value-default"
    # Case insensitivity
    assert runner.resolve_cost_profile("Quality")[0] == "quality"


def test_resolve_cell_alias_resolves_from_profile_defaults() -> None:
    assert (
        runner.resolve_cell_alias("${SYNTH_MODEL}", "quality")
        == "openrouter/anthropic/claude-opus-4.6"
    )
    assert (
        runner.resolve_cell_alias("${CE_MODEL}", "value-default")
        == "openai/gpt-5.3-codex"
    )


def test_resolve_cell_alias_cli_override_wins() -> None:
    result = runner.resolve_cell_alias(
        "${SYNTH_MODEL}",
        "quality",
        cli_overrides={"SYNTH_MODEL": "openrouter/anthropic/claude-opus-4.7"},
    )
    assert result == "openrouter/anthropic/claude-opus-4.7"


def test_resolve_cell_alias_env_override_takes_precedence_over_profile() -> None:
    result = runner.resolve_cell_alias(
        "${SYNTH_MODEL}",
        "quality",
        env={"SYNTH_MODEL": "openrouter/anthropic/claude-opus-4.7"},
    )
    assert result == "openrouter/anthropic/claude-opus-4.7"


def test_resolve_cell_alias_passes_through_bare_model_id() -> None:
    assert (
        runner.resolve_cell_alias("openai/gpt-5.4", "quality") == "openai/gpt-5.4"
    )


def test_resolve_cell_alias_returns_placeholder_when_unresolved() -> None:
    # Operator typo'd an alias key — return the placeholder verbatim so it's
    # visible in logs rather than silently dropping to None.
    result = runner.resolve_cell_alias("${UNKNOWN_ALIAS_KEY}", "quality")
    assert result == "${UNKNOWN_ALIAS_KEY}"


def test_resolve_effective_step_route_applies_model_alias_before_dispatch() -> None:
    cfg = _make_cfg(
        cost_profile="quality",
        model_alias_overrides=(
            ("SYNTH_MODEL", "openrouter/anthropic/claude-opus-4.7"),
        ),
    )
    step_contract = {
        "scope": {"json_managed": True},
        "expected_artifacts": ["SYNTH_REPORT.json"],
        "lane": {
            "primary_routes": [
                {
                    # Hardcoded provider/api_key_env are intentionally "wrong"
                    # (openai) to prove the full resolver derives them from the
                    # alias value, not the route's static fields.
                    "provider": "openai",
                    "model_id": "${SYNTH_MODEL}",
                    "api_key_env": "OPENAI_API_KEY",
                    "strict_json_schema": False,
                    "strict_passthrough_verified": False,
                    "service_tier": "priority",
                }
            ]
        },
    }

    route = runner.resolve_effective_step_route(
        "R", "R7", cfg, step_contract=step_contract
    )

    assert route["provider"] == "openrouter"
    assert route["model_id"] == "anthropic/claude-opus-4.7"
    assert route["api_key_env"] == "OPENROUTER_API_KEY"
    assert route["ladder"] == [
        ("openrouter", "anthropic/claude-opus-4.7", "OPENROUTER_API_KEY")
    ]
    assert route["ladder_route_entries"][0]["model_id"] == "anthropic/claude-opus-4.7"
    assert route["ladder_route_entries"][0]["service_tier"] == "priority"


def test_call_llm_forwards_cost_profile_runtime_controls(monkeypatch) -> None:
    captured = {}

    def fake_call_llm(_deps, provider, model_id, api_key_env, *_args, **kwargs):
        captured.update(
            {
                "provider": provider,
                "model_id": model_id,
                "api_key_env": api_key_env,
                "service_tier": kwargs.get("service_tier"),
                "disabled_providers": kwargs.get("disabled_providers"),
            }
        )
        return {"ok": True, "text": "{}", "meta": {}}

    monkeypatch.setattr(runner, "llm_runtime_call_llm", fake_call_llm)
    cfg = _make_cfg(
        default_service_tier="priority",
        disabled_providers=("openai",),
    )

    runner.call_llm(
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
        api_key_env="OPENROUTER_API_KEY",
        system_prompt="Return JSON.",
        user_content="{}",
        cfg=cfg,
    )

    assert captured["provider"] == "openrouter"
    assert captured["model_id"] == "anthropic/claude-opus-4.6"
    assert captured["service_tier"] == "priority"
    assert captured["disabled_providers"] == {"openai"}


def test_ladder_runtime_filters_disabled_providers_before_attempt() -> None:
    cfg = _make_cfg(disabled_providers=("openai",), escalation_max_hops=2)
    attempts = []

    def execute_attempt(route, hop_index):
        attempts.append((route, hop_index))
        return {
            "response_text": "{}",
            "request_meta": {},
            "artifacts": [{}],
            "route": route,
            "artifacts_ok": True,
        }

    result = runner.call_llm_with_ladder(
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy=cfg.routing_policy,
        routing_tier="bulk",
        ladder=[
            ("openai", "gpt-5.4", "OPENAI_API_KEY"),
            ("xai", "grok-4.3", "XAI_API_KEY"),
        ],
        cfg=cfg,
        execute_attempt=execute_attempt,
    )

    assert attempts == [(("xai", "grok-4.3", "XAI_API_KEY"), 0)]
    assert result["request_meta"]["provider"] == "xai"


def test_quality_profile_uses_opus_4_6_not_4_7() -> None:
    """Per Phase D consensus (claude-opus-4.5 against-stance review):
    Default to opus 4.6 to avoid the ~1.35x tokenization tax of opus 4.7.
    Operators can swap centrally via env var or --model-alias."""
    profile = runner.COST_PROFILES["quality"]
    assert (
        profile["cell_aliases"]["SYNTH_MODEL"]
        == "openrouter/anthropic/claude-opus-4.6"
    )
    # And experimental profile DOES use 4.7 (opt-in for canary testing).
    exp = runner.COST_PROFILES["experimental"]
    assert (
        exp["cell_aliases"]["SYNTH_MODEL"]
        == "openrouter/anthropic/claude-opus-4.7"
    )


def test_economy_profile_uses_flex_tier_by_default() -> None:
    assert runner.COST_PROFILES["economy"]["default_service_tier"] == "flex"
    assert runner.COST_PROFILES["economy"]["max_cost_usd_default"] == 5.00


def test_quality_profile_uses_priority_tier() -> None:
    assert runner.COST_PROFILES["quality"]["default_service_tier"] == "priority"
    assert runner.COST_PROFILES["quality"]["escalation_max_hops"] == 3
    assert runner.COST_PROFILES["quality"]["max_cost_usd_default"] == 25.00


def test_value_default_profile_balanced_tradeoffs() -> None:
    p = runner.COST_PROFILES["value-default"]
    assert p["default_service_tier"] == "default"
    assert p["enable_cached_input"] is True
    assert p["enable_batch_when_supported"] is True
    assert p["max_cost_usd_default"] == 5.00


def test_cli_help_lists_new_flags() -> None:
    """--cost-profile, --disable-provider, --model-alias must all appear in
    --help so operators discover them. --routing-policy retained for one
    release as deprecated alias."""
    result = subprocess.run(
        [
            sys.executable,
            str(SERVICE_ROOT / "run_extraction_v5.py"),
            "--help",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    help_text = result.stdout + result.stderr
    assert "--cost-profile" in help_text
    assert "--disable-provider" in help_text
    assert "--model-alias" in help_text
    assert "--routing-policy" in help_text  # legacy retained
    # Cost profile choices (dynamic from COST_PROFILES.keys()).
    for name in EXPECTED_PROFILES:
        assert name in help_text, f"--cost-profile choice {name} missing from --help"


# ---------------------------------------------------------------------------
# Direct-provider alias mechanism (Plan B)
# ---------------------------------------------------------------------------


def test_parse_alias_provider_model_direct_and_openrouter() -> None:
    assert runner._parse_alias_provider_model("xai/grok-4.3") == ("xai", "grok-4.3")
    assert runner._parse_alias_provider_model("openai/gpt-5.3-codex") == (
        "openai",
        "gpt-5.3-codex",
    )
    # OpenRouter keeps its full namespace remainder.
    assert runner._parse_alias_provider_model(
        "openrouter/anthropic/claude-opus-4.6"
    ) == ("openrouter", "anthropic/claude-opus-4.6")


def test_parse_alias_provider_model_rejects_invalid() -> None:
    import pytest

    with pytest.raises(ValueError):
        runner._parse_alias_provider_model("just-a-model")  # no slash
    with pytest.raises(ValueError):
        runner._parse_alias_provider_model("bogus/model")  # unknown provider
    with pytest.raises(ValueError):
        runner._parse_alias_provider_model("openrouter/")  # empty model
    with pytest.raises(ValueError):
        # Direct anthropic is unsupported; must go via openrouter.
        runner._parse_alias_provider_model("anthropic/claude-opus-4.6")


def test_resolve_route_entry_alias_full_derives_provider_env_model() -> None:
    cfg = _make_cfg(cost_profile="grok-fast")
    # BULK_DOCS_MODEL = xai/grok-4-fast under grok-fast.
    route = {
        "provider": "openai",  # deliberately wrong static fields
        "model_id": "${BULK_DOCS_MODEL}",
        "api_key_env": "OPENAI_API_KEY",
        "strict_json_schema": False,
    }
    resolved = runner._resolve_route_entry_alias_full(route, cfg)
    assert resolved["provider"] == "xai"
    assert resolved["model_id"] == "grok-4-fast"
    assert resolved["api_key_env"] == "XAI_API_KEY"


def test_resolve_route_entry_alias_full_is_idempotent_on_literals() -> None:
    cfg = _make_cfg(cost_profile="value-default")
    route = {
        "provider": "openai",
        "model_id": "gpt-5.3-codex",
        "api_key_env": "OPENAI_API_KEY",
    }
    resolved = runner._resolve_route_entry_alias_full(route, cfg)
    assert resolved == route
    # Resolving twice yields the same result.
    assert runner._resolve_route_entry_alias_full(resolved, cfg) == route


def test_resolve_contract_routes_resolves_all_stages() -> None:
    cfg = _make_cfg(cost_profile="gemini-value")
    contract = {
        "lane": {
            "primary_routes": [
                {
                    "provider": "openai",
                    "model_id": "${BULK_DOCS_MODEL}",
                    "api_key_env": "OPENAI_API_KEY",
                }
            ],
            "repair_routes": [
                {
                    "provider": "openai",
                    "model_id": "gpt-5.4-mini",  # literal — unchanged
                    "api_key_env": "OPENAI_API_KEY",
                }
            ],
        }
    }
    resolved = runner.resolve_contract_routes(contract, cfg)
    assert resolved["lane"]["primary_routes"][0]["provider"] == "gemini"
    assert resolved["lane"]["primary_routes"][0]["model_id"] == "gemini-3-flash-preview"
    assert resolved["lane"]["primary_routes"][0]["api_key_env"] == "GEMINI_API_KEY"
    assert resolved["lane"]["repair_routes"][0]["model_id"] == "gpt-5.4-mini"
    # Raw contract is not mutated.
    assert contract["lane"]["primary_routes"][0]["model_id"] == "${BULK_DOCS_MODEL}"


def test_strict_guard_rejects_disallowed_provider() -> None:
    import pytest

    with pytest.raises(RuntimeError):
        runner.assert_strict_route_provider_allowed(
            phase="A", step_id="A0", provider="xai", model_id="grok-4.3"
        )
    with pytest.raises(RuntimeError):
        runner.assert_strict_route_provider_allowed(
            phase="A", step_id="A0", provider="gemini", model_id="gemini-3-flash-preview"
        )
    # Allowed providers do not raise.
    runner.assert_strict_route_provider_allowed(
        phase="A", step_id="A0", provider="openai", model_id="gpt-5.5"
    )
    runner.assert_strict_route_provider_allowed(
        phase="A",
        step_id="A0",
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
    )


def test_strict_step_with_xai_profile_fails_closed_before_spend() -> None:
    import pytest

    # A profile (via override) routing a STRICT cell to xai must raise at
    # dispatch, before any token spend.
    cfg = _make_cfg(
        cost_profile="grok-fast",
        model_alias_overrides=(("CE_MODEL", "xai/grok-4.3"),),
    )
    step_contract = {
        "scope": {"json_managed": True},
        "expected_artifacts": ["CODE_ENTITIES.json"],
        "lane": {
            "strict_schema_required_primary": True,
            "primary_routes": [
                {
                    "provider": "openai",
                    "model_id": "${CE_MODEL}",
                    "api_key_env": "OPENAI_API_KEY",
                    "strict_json_schema": True,
                    "strict_passthrough_verified": True,
                }
            ]
        },
    }
    with pytest.raises(RuntimeError):
        runner.resolve_effective_step_route(
            "A", "A0", cfg, step_contract=step_contract
        )
