from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RUNNER_PATH = Path(__file__).resolve().parents[2] / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_all_routing_policies_have_required_tiers():
    required_tiers = {"bulk", "extract", "synthesis", "qa"}
    for policy, tiers in runner.ROUTING_LADDERS.items():
        assert required_tiers.issubset(tiers.keys()), f"Policy {policy} missing required tiers"


def test_no_unsupported_providers_exist():
    allowed_providers = {"openai", "gemini", "xai"}
    for policy, tiers in runner.ROUTING_LADDERS.items():
        for tier, routes in tiers.items():
            for provider, model, env in routes:
                assert provider in allowed_providers, f"Unsupported provider '{provider}' in {policy}/{tier}"


def test_resolve_step_ladder_returns_valid_list():
    # Test for phase D, step D1 using the default policy
    ladder = runner.resolve_step_ladder(runner.DEFAULT_ROUTING_POLICY, "D", "D1")
    assert isinstance(ladder, list)
    assert len(ladder) > 0
    for route in ladder:
        assert len(route) == 3
        provider, model, env = route
        assert provider in {"openai", "gemini", "xai"}


def test_apply_model_overrides_preserves_validity():
    # Active routing ladders have already been initialized on load
    allowed_providers = {"openai", "gemini", "xai"}
    
    # Check default initialization
    for policy, tiers in runner.ACTIVE_ROUTING_LADDERS.items():
        for tier, routes in tiers.items():
            for provider, model, env in routes:
                assert provider in allowed_providers, f"Unsupported provider '{provider}' injected by default init in {policy}/{tier}"

    # Verify a new override doesn't inject invalid providers
    runner.apply_model_overrides("gemini-1.5-pro", "cost")
    for policy, tiers in runner.ACTIVE_ROUTING_LADDERS.items():
        for tier, routes in tiers.items():
            for provider, model, env in routes:
                assert provider in allowed_providers, f"Unsupported provider '{provider}' injected by override in {policy}/{tier}"

    # Restore default
    runner.apply_model_overrides(runner.DEFAULT_GEMINI_MODEL_ID, runner.DEFAULT_ROUTING_POLICY)
