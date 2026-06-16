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
        "workload_class",
        "governance_posture",
        "provider_surface",
        "allowed_payload_sensitivity",
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
    # value-default and quality carry their own caps but are excluded from this
    # enforcement gate (the operator explicitly owns cost for the default and
    # production go/no-go lanes). Every other profile — including all Plan B
    # additions — MUST carry a numeric cap so we don't repeat the audit's
    # uncapped-profile finding.
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


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("rte-cost-prescan-cheap", "economy"),
        ("rte-cost-balanced", "value-default"),
        ("rte-cost-structured", "openai-heavy"),
        ("rte-cost-batch-backfill", "economy"),
        ("rte-cost-high-reliability", "quality"),
        ("rte-cost-governance-safe-direct", "openai-heavy"),
        ("rte-cost-aggregator-benchmark", "openrouter-resilient"),
    ],
)
def test_logical_cost_profile_aliases_resolve_to_canonical(alias: str, expected: str) -> None:
    name, profile = runner.resolve_cost_profile(alias)
    assert name == expected
    assert profile is runner.COST_PROFILES[expected]


def test_logical_alias_metadata_is_present_for_each_alias() -> None:
    required = {
        "workload_class",
        "governance_posture",
        "allowed_payload_sensitivity",
        "provider_surface",
        "fail_closed_if",
        "profile_notes",
    }
    for alias in runner.COST_PROFILE_ALIASES:
        metadata = runner.COST_PROFILE_ALIAS_METADATA[alias]
        assert required <= set(metadata.keys())
        assert metadata["profile_notes"] == runner._OBSERVED_PROFILE_NOTES


def test_unknown_rte_cost_alias_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown logical cost profile alias"):
        runner.resolve_cost_profile("rte-cost-not-real")


def test_sandbox_free_alias_is_blocked() -> None:
    with pytest.raises(ValueError, match="BLOCKED"):
        runner.resolve_cost_profile("rte-cost-sandbox-free")


def test_resolve_cell_alias_resolves_from_profile_defaults() -> None:
    assert (
        runner.resolve_cell_alias("${SYNTH_MODEL}", "quality") == "openai/gpt-5.5"
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
        cost_profile="value-default",
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


def test_strict_cells_use_openai_namespace_everywhere() -> None:
    """Strict cells (CE/SYNTH) can only use OpenAI strict-JSON-passthrough
    models: openai/* direct, or openrouter/openai/*. Verified for every
    profile via the dispatch guard."""
    for name, profile in runner.COST_PROFILES.items():
        for cell in runner.COST_PROFILE_STRICT_CELL_KEYS:
            value = profile["cell_aliases"][cell]
            provider, model = runner._parse_alias_provider_model(value)
            # Must not raise — this is exactly the dispatch-time guard.
            runner.assert_strict_route_provider_allowed(
                phase="X", step_id="X0", provider=provider, model_id=model
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
    # Logical rte-cost-* aliases must also appear in --help choices.
    for alias in runner.COST_PROFILE_ALIASES:
        assert alias in help_text, f"--cost-profile alias {alias} missing from --help"


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


def _model_map_steps_by_lane(*lane_classes):
    import yaml as _yaml

    mm = Path(__file__).resolve().parents[1] / "promptsets" / "v4" / "model_map.yaml"
    data = _yaml.safe_load(mm.read_text(encoding="utf-8"))
    out = []
    for step in data.get("steps", []):
        if step.get("lane_class") in lane_classes:
            out.append((str(step["phase"]), str(step["step_id"]), step["lane_class"]))
    return out


def test_strict_repair_sidefill_leads_resolve_to_openai_across_profiles() -> None:
    """Increment 3: every CE/AGG repair_routes/sidefill_routes lead must resolve,
    under every cost profile, to an OpenAI strict-capable model with no ${} leak,
    so the profile drives the repair/sidefill model and the strict guard passes."""
    steps = _model_map_steps_by_lane("CE", "AGG")
    assert steps, "expected CE/AGG steps in model_map"
    for profile in runner.COST_PROFILES:
        cfg = _make_cfg(cost_profile=profile)
        for phase, step_id, _lane in steps:
            resolved = runner.resolve_contract_routes(
                runner._step_contract_for(phase, step_id), cfg
            )
            for stage in ("repair_routes", "sidefill_routes"):
                rows = resolved["lane"].get(stage) or []
                assert rows, f"{phase}:{step_id} {stage} empty"
                lead = rows[0]
                assert not str(lead["model_id"]).startswith("${"), (
                    f"{profile} {phase}:{step_id} {stage} leaked {lead['model_id']}"
                )
                # Must pass the strict-provider guard (raises otherwise).
                runner.assert_strict_route_provider_allowed(
                    phase=phase,
                    step_id=step_id,
                    provider=str(lead["provider"]),
                    model_id=str(lead["model_id"]),
                )
                assert lead.get("strict_json_schema") is True


def test_ce_repair_sidefill_lead_tracks_cost_profile() -> None:
    """The CE repair/sidefill lead model changes with the profile (value-default
    -> codex, economy -> codex-mini, quality -> gpt-5.5)."""
    expected = {
        "value-default": "gpt-5.3-codex",
        "economy": "gpt-5.1-codex-mini",
        "quality": "gpt-5.5",
    }
    for profile, model in expected.items():
        cfg = _make_cfg(cost_profile=profile)
        resolved = runner.resolve_contract_routes(
            runner._step_contract_for("D", "D0"), cfg
        )
        for stage in ("repair_routes", "sidefill_routes"):
            lead = resolved["lane"][stage][0]
            assert lead["provider"] == "openai"
            assert lead["model_id"] == model


def test_bulk_repair_activates_and_tracks_cost_profile() -> None:
    """Increment 3 commit 2: bulk repair/sidefill were dead under the old
    unconditional strict_required=True (non-strict bulk routes filtered to None).
    With lane-aware strictness, a non-strict bulk lane now selects its profile
    route — so bulk recovery dispatches and tracks the cost profile."""
    expected = {
        "value-default": ("openai", "gpt-5.4-mini"),
        "gemini-value": ("gemini", "gemini-3-flash-preview"),
        "grok-fast": ("xai", "grok-4-fast"),
    }
    contract = runner._step_contract_for("A", "A2")  # BULK_DOCS_GENERAL
    assert runner.is_strict_contract_step(contract) is False
    for profile, (prov, model) in expected.items():
        cfg = _make_cfg(cost_profile=profile)
        resolved = runner.resolve_contract_routes(contract, cfg)

        def _transport(provider: str) -> str:
            return runner.transport_for_provider(provider, cfg)

        # Old behavior: strict_required=True filters the non-strict bulk route to None.
        none_route, _ = runner.resolve_stage_route(
            step_contract=resolved,
            stage="repair",
            transport_for_provider=_transport,
            strict_required=True,
        )
        assert none_route is None
        # New behavior: lane-aware (non-strict) selects the profile's bulk route.
        route, _ = runner.resolve_stage_route(
            step_contract=resolved,
            stage="repair",
            transport_for_provider=_transport,
            strict_required=False,
        )
        assert route is not None
        assert (route["provider"], route["model_id"]) == (prov, model)


def test_bulk_strict_openai_repair_stays_pinned() -> None:
    """M-phase bulk steps deliberately repair with a strict OpenAI model; those
    routes are left hardcoded (not templatized), so they do NOT track the
    profile and never downgrade to a non-strict bulk model."""
    contract = runner._step_contract_for("M", "M0")
    for profile in ("value-default", "gemini-value", "grok-fast"):
        cfg = _make_cfg(cost_profile=profile)
        resolved = runner.resolve_contract_routes(contract, cfg)
        lead = resolved["lane"]["repair_routes"][0]
        assert lead["provider"] == "openai"
        assert lead["model_id"] == "gpt-5.4-mini"
        assert not str(lead["model_id"]).startswith("${")


def test_routing_fingerprint_resolves_placeholders(tmp_path) -> None:
    """RUN_ROUTING_FINGERPRINT.json must record the route that actually runs
    under the active profile, not the static ${CELL} placeholder — else the
    proof/replay artifact misdescribes the run (Codex P2)."""
    import json

    cfg = _make_cfg(cost_profile="gemini-value")
    runner.write_run_routing_fingerprint(tmp_path, "run-fp", cfg, ["A"])
    payload = json.loads(
        (tmp_path / "RUN_ROUTING_FINGERPRINT.json").read_text(encoding="utf-8")
    )
    blob = json.dumps(payload)
    assert "${" not in blob, "routing fingerprint leaked a ${CELL} placeholder"
    # A2 is BULK_DOCS_GENERAL → gemini-value resolves it to the Gemini bulk model.
    a2 = [
        entry
        for phase_entries in payload.get("phases", {}).values()
        if isinstance(phase_entries, list)
        for entry in phase_entries
        if entry.get("step_id") == "A2"
    ]
    assert a2, "A2 missing from fingerprint"
    assert a2[0]["provider"] == "gemini"
    assert a2[0]["model_id"] == "gemini-3-flash-preview"


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
    # openrouter/anthropic is NOT strict-JSON capable → must raise.
    with pytest.raises(RuntimeError):
        runner.assert_strict_route_provider_allowed(
            phase="A",
            step_id="A0",
            provider="openrouter",
            model_id="anthropic/claude-opus-4.6",
        )
    # Allowed: openai/* direct, and openrouter/openai/*.
    runner.assert_strict_route_provider_allowed(
        phase="A", step_id="A0", provider="openai", model_id="gpt-5.5"
    )
    runner.assert_strict_route_provider_allowed(
        phase="A",
        step_id="A0",
        provider="openrouter",
        model_id="openai/gpt-5.4",
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


def test_strict_primary_leads_resolve_to_openai_across_profiles() -> None:
    """Regression (Codex 3361748519): every CE/AGG *primary_routes* lead must
    resolve, under every cost profile, to an OpenAI strict-capable model with no
    ${} leak — mirroring the repair/sidefill guard above.

    Before the fix, 18 templatized primary leads kept strict_json_schema:false
    (they were originally gemini routes that Plan B incr2 rewrote by swapping only
    model_id). resolve_stage_route(strict_required=True) therefore skipped the
    profile-resolved lead and fell through to the hardcoded gpt-5.3-codex
    fallback, so the selected profile model was silently ignored."""
    steps = _model_map_steps_by_lane("CE", "AGG")
    assert steps, "expected CE/AGG steps in model_map"
    for profile in runner.COST_PROFILES:
        cfg = _make_cfg(cost_profile=profile)
        for phase, step_id, _lane in steps:
            resolved = runner.resolve_contract_routes(
                runner._step_contract_for(phase, step_id), cfg
            )
            rows = resolved["lane"].get("primary_routes") or []
            assert rows, f"{phase}:{step_id} primary_routes empty"
            lead = rows[0]
            assert not str(lead["model_id"]).startswith("${"), (
                f"{profile} {phase}:{step_id} primary leaked {lead['model_id']}"
            )
            # Must pass the strict-provider guard (raises otherwise).
            runner.assert_strict_route_provider_allowed(
                phase=phase,
                step_id=step_id,
                provider=str(lead["provider"]),
                model_id=str(lead["model_id"]),
            )
            assert lead.get("strict_json_schema") is True, (
                f"{profile} {phase}:{step_id} primary lead not strict-capable"
            )


def test_strict_contract_primary_lead_is_selected_per_cost_profile() -> None:
    """Regression (Codex 3361748519): the contract-lane strict selector must pick
    the profile's CE/SYNTH model from the *primary* lead, not fall through to the
    hardcoded gpt-5.3-codex fallback.

    value-default hid the bug because CE_MODEL == gpt-5.3-codex == the fallback;
    economy/quality expose it. D1 exercises ${CE_MODEL}, D4 exercises
    ${SYNTH_MODEL}."""
    cases = [
        # (phase, step_id, profile, expected_selected_model)
        ("D", "D1", "economy", "gpt-5.1-codex-mini"),  # CE lead
        ("D", "D1", "quality", "gpt-5.5"),  # CE lead
        ("D", "D4", "economy", "gpt-5.4"),  # AGG (SYNTH) lead
        ("D", "D4", "quality", "gpt-5.5"),  # AGG (SYNTH) lead
    ]
    for phase, step_id, profile, expected in cases:
        cfg = _make_cfg(cost_profile=profile)
        contract = runner._step_contract_for(phase, step_id)
        route = runner.resolve_effective_step_route(
            phase, step_id, cfg, step_contract=contract
        )
        assert route["provider"] == "openai", (
            f"{profile} {phase}:{step_id} provider={route['provider']}"
        )
        assert route["model_id"] == expected, (
            f"{profile} {phase}:{step_id} selected {route['model_id']} != {expected}"
        )
        assert route["reason"] == "contract_lane_primary_strict"
        attempts = route.get("strict_route_attempts") or []
        assert attempts and attempts[0]["strict_capable"] is True, (
            f"{profile} {phase}:{step_id} primary lead was skipped as non-strict"
        )


def test_provider_lock_detects_single_provider_profiles() -> None:
    """Single-provider profiles lock to their provider; value-default opts out;
    multi-provider profiles do not lock (Codex P2 #3364972852)."""
    expected = {
        "openrouter-resilient": "openrouter",
        "economy": "openai",
        "quality": "openai",
        "openai-heavy": "openai",
        "quality-mix": "openai",
        "value-default": None,  # allow_cross_provider_fallback opt-out
        "gemini-value": None,  # multi-provider
        "grok-fast": None,
        "balanced-mix": None,
        "budget-mix": None,
        "experimental": None,
    }
    for profile, lock in expected.items():
        cfg = _make_cfg(cost_profile=profile)
        assert runner._profile_provider_lock(cfg) == lock, f"{profile}"


def _ladder(profile: str, phase: str, step_id: str):
    cfg = _make_cfg(cost_profile=profile)
    info = runner.resolve_effective_step_route(
        phase, step_id, cfg, step_contract=runner._step_contract_for(phase, step_id)
    )
    return [(p, mdl) for (p, mdl, *_rest) in info["ladder"]]


def test_provider_lock_drops_cross_provider_fallbacks() -> None:
    # openrouter-resilient: bulk + CE ladders reference only openrouter (the
    # single-key fix); the direct xai/openai fallbacks are dropped.
    for prov, _m in _ladder("openrouter-resilient", "A", "A2"):
        assert prov == "openrouter"
    for prov, _m in _ladder("openrouter-resilient", "A", "A0"):
        assert prov == "openrouter"
    # economy (openai-locked): the bulk xai fallback is dropped.
    assert {p for p, _ in _ladder("economy", "A", "A2")} == {"openai"}


def test_value_default_keeps_cross_provider_fallback() -> None:
    # The default profile opted out, so its bulk lane keeps the xai failover.
    providers = {p for p, _ in _ladder("value-default", "A", "A2")}
    assert "xai" in providers


def test_provider_lock_preflight_probes_only_locked_provider() -> None:
    """Launch preflight for a single-key profile references only its provider's
    key — an OPENROUTER_API_KEY-only operator no longer fails on missing
    XAI/OpenAI/Gemini keys."""
    routes = runner.collect_provider_routes(
        phases=["A"], routing_policy="balanced_openrouter", cost_profile="openrouter-resilient"
    )
    assert {r["api_key_env"] for r in routes.values()} == {"OPENROUTER_API_KEY"}
    # economy probes only OpenAI.
    routes_eco = runner.collect_provider_routes(
        phases=["A"], routing_policy="balanced_openrouter", cost_profile="economy"
    )
    assert {r["api_key_env"] for r in routes_eco.values()} == {"OPENAI_API_KEY"}


def test_provider_lock_filters_repair_sidefill_stages() -> None:
    """The lock applies to every dispatch stage, so single-key repair/sidefill
    recovery never falls to a cross-provider key (Codex P2 #3364972852)."""
    cfg = _make_cfg(cost_profile="openrouter-resilient")
    resolved = runner.resolve_contract_routes(runner._step_contract_for("A", "A2"), cfg)
    for stage in ("primary_routes", "repair_routes", "sidefill_routes"):
        provs = {r["provider"] for r in resolved["lane"][stage]}
        assert provs == {"openrouter"}, f"{stage} not locked: {provs}"
    # value-default opted out → repair/sidefill keep the xai failover.
    rc_default = runner.resolve_contract_routes(
        runner._step_contract_for("A", "A2"), _make_cfg(cost_profile="value-default")
    )
    assert "xai" in {r["provider"] for r in rc_default["lane"]["repair_routes"]}


def test_provider_lock_fails_closed_on_foreign_override() -> None:
    """Overriding a locked profile's cell to a foreign provider fails closed
    before spend (the lock is the profile's declared intent, not silently
    dissolved by --model-alias)."""
    import pytest

    foreign = _make_cfg(
        cost_profile="openrouter-resilient",
        model_alias_overrides=(("BULK_DOCS_MODEL", "xai/grok-4.3"),),
    )
    with pytest.raises(RuntimeError, match="provider-locked"):
        runner.resolve_effective_step_route(
            "A", "A2", foreign, step_contract=runner._step_contract_for("A", "A2")
        )
    # A same-provider override (openrouter/...) is fine — no raise.
    same = _make_cfg(
        cost_profile="openrouter-resilient",
        model_alias_overrides=(("BULK_DOCS_MODEL", "openrouter/openai/gpt-5.4"),),
    )
    route = runner.resolve_effective_step_route(
        "A", "A2", same, step_contract=runner._step_contract_for("A", "A2")
    )
    assert route["provider"] == "openrouter"
    # An opt-out (value-default) and a multi-provider profile never fail closed.
    for profile in ("value-default", "gemini-value"):
        cfg = _make_cfg(
            cost_profile=profile,
            model_alias_overrides=(("BULK_DOCS_MODEL", "xai/grok-4.3"),),
        )
        runner.resolve_effective_step_route(
            "A", "A2", cfg, step_contract=runner._step_contract_for("A", "A2")
        )
