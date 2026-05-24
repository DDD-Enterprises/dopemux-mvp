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


def test_cost_profiles_dict_has_four_canonical_profiles() -> None:
    assert set(runner.COST_PROFILES.keys()) == {
        "economy",
        "value-default",
        "quality",
        "experimental",
    }


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
        runner.resolve_cell_alias("${QUALITY_SYNTH_CRITICAL_MODEL}", "quality")
        == "anthropic/claude-opus-4.6"
    )
    assert (
        runner.resolve_cell_alias(
            "${VALUE_DEFAULT_CE_MEDIUM_MODEL}", "value-default"
        )
        == "openai/gpt-5.3-codex"
    )


def test_resolve_cell_alias_cli_override_wins() -> None:
    result = runner.resolve_cell_alias(
        "${QUALITY_SYNTH_CRITICAL_MODEL}",
        "quality",
        cli_overrides={"QUALITY_SYNTH_CRITICAL_MODEL": "anthropic/claude-opus-4.7"},
    )
    assert result == "anthropic/claude-opus-4.7"


def test_resolve_cell_alias_env_override_takes_precedence_over_profile() -> None:
    result = runner.resolve_cell_alias(
        "${QUALITY_SYNTH_CRITICAL_MODEL}",
        "quality",
        env={"QUALITY_SYNTH_CRITICAL_MODEL": "anthropic/claude-opus-4.7"},
    )
    assert result == "anthropic/claude-opus-4.7"


def test_resolve_cell_alias_passes_through_bare_model_id() -> None:
    assert (
        runner.resolve_cell_alias("openai/gpt-5.4", "quality") == "openai/gpt-5.4"
    )


def test_resolve_cell_alias_returns_placeholder_when_unresolved() -> None:
    # Operator typo'd an alias key — return the placeholder verbatim so it's
    # visible in logs rather than silently dropping to None.
    result = runner.resolve_cell_alias("${UNKNOWN_ALIAS_KEY}", "quality")
    assert result == "${UNKNOWN_ALIAS_KEY}"


def test_quality_profile_uses_opus_4_6_not_4_7() -> None:
    """Per Phase D consensus (claude-opus-4.5 against-stance review):
    Default to opus 4.6 to avoid the ~1.35x tokenization tax of opus 4.7.
    Operators can swap centrally via env var or --model-alias."""
    profile = runner.COST_PROFILES["quality"]
    assert (
        profile["cell_aliases"]["QUALITY_SYNTH_CRITICAL_MODEL"]
        == "anthropic/claude-opus-4.6"
    )
    # And experimental profile DOES use 4.7 (opt-in for canary testing).
    exp = runner.COST_PROFILES["experimental"]
    assert (
        exp["cell_aliases"]["EXPERIMENTAL_SYNTH_CRITICAL_MODEL"]
        == "anthropic/claude-opus-4.7"
    )


def test_economy_profile_uses_flex_tier_by_default() -> None:
    assert runner.COST_PROFILES["economy"]["default_service_tier"] == "flex"
    assert runner.COST_PROFILES["economy"]["max_cost_usd_default"] == 5.00


def test_quality_profile_uses_priority_tier() -> None:
    assert runner.COST_PROFILES["quality"]["default_service_tier"] == "priority"
    assert runner.COST_PROFILES["quality"]["escalation_max_hops"] == 3


def test_value_default_profile_balanced_tradeoffs() -> None:
    p = runner.COST_PROFILES["value-default"]
    assert p["default_service_tier"] == "default"
    assert p["enable_cached_input"] is True
    assert p["enable_batch_when_supported"] is True
    assert p["max_cost_usd_default"] is None  # operator explicitly sets


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
    # Cost profile choices
    for name in ("economy", "value-default", "quality", "experimental"):
        assert name in help_text, f"--cost-profile choice {name} missing from --help"
