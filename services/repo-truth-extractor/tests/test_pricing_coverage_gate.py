"""TP-RTE-TRUTH-R2-001 — coverage gate tying COST_PROFILES + ladder fallbacks
to priced rows in config/pricing.yaml (packet REQUIRED OUTCOME #4).

A2 (claudedocs/rte-truth-program-2026-07/A2-cost-truthfulness.md) §2.2 found
"no CI gate tying COST_PROFILES cell_aliases + ladder fallbacks to
pricing.yaml keys; coverage is only checked at runtime, and only in E3, and
only when a cap is set. A new profile alias can silently route an unpriced
model with no cap -> E2 max-fallback pricing distorts the ledger; with a cap
-> hard startup failure (good, but late)."

This test makes that check a CI-time gate instead of a runtime surprise: for
every declared cost profile, it resolves every route reachable through
run_extraction_v5.collect_provider_routes (which already walks the FULL
ladder — lead + hardcoded fallbacks — for every phase/step, the same
resolution `initialize_spend_tracker`'s own missing-route check uses at
startup) and asserts each one has a numeric row in config/pricing.yaml.

Before TP-RTE-TRUTH-R2-001, this failed for real: 5 hardcoded ladder
fallback models (openrouter/openai/gpt-5.2-chat, gpt-5.2-pro, gpt-5-pro,
gpt-4.1-nano, gpt-4o-mini — reachable via the openrouter-resilient,
value-default, gemini-value, and balanced-mix profiles) had NO row in
config/pricing.yaml at all. Fixed by adding priced (LOW/MEDIUM-confidence,
clearly-captioned) rows for those 5 routes.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _service_root() -> Path:
    return _repo_root() / "services" / "repo-truth-extractor"


def _load_runner_module():
    module_path = _service_root() / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_pricing_gate", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    if str(_service_root()) not in sys.path:
        sys.path.insert(0, str(_service_root()))
    spec.loader.exec_module(module)
    return module


def _priced_keys(pricing_path: Path) -> set[str]:
    payload = yaml.safe_load(pricing_path.read_text(encoding="utf-8"))
    models = payload.get("models") or {}
    priced = set()
    for key, row in models.items():
        if not isinstance(row, dict):
            continue
        if row.get("input_cost_per_m") is not None and row.get("output_cost_per_m") is not None:
            priced.add(str(key).strip().lower())
    return priced


@pytest.fixture(scope="module")
def runner():
    return _load_runner_module()


@pytest.fixture(scope="module")
def priced_keys(runner) -> set[str]:
    return _priced_keys(Path(runner.PRICING_CONFIG_PATH))


def _profile_route_gaps(runner, priced: set[str], profile_key: str, profile: dict) -> set[str]:
    routes = runner.collect_provider_routes(
        phases=runner.PHASES,
        routing_policy=profile["routing_policy"],
        cost_profile=profile_key,
    )
    missing = set()
    for route in routes.values():
        provider = str(route.get("provider") or "").strip().lower()
        model_id = str(route.get("model_id") or "").strip()
        if not provider or not model_id:
            continue
        key = f"{provider}/{model_id}"
        if key not in priced:
            missing.add(key)
    return missing


def test_every_cost_profile_resolves_only_to_priced_routes(runner, priced_keys) -> None:
    """The core coverage gate: every route reachable from every declared
    COST_PROFILES entry (cell_aliases + hardcoded ladder fallbacks, walked by
    collect_provider_routes across every phase) must have a numeric priced
    row in config/pricing.yaml. A gap here means a run on that profile would
    either hard-fail at E3 startup (cap set) or silently mis-price via E2's
    fallback (no cap) — exactly F-10/F-11's mechanism."""
    gaps: dict[str, set[str]] = {}
    for profile_key, profile in runner.COST_PROFILES.items():
        missing = _profile_route_gaps(runner, priced_keys, profile_key, profile)
        if missing:
            gaps[profile_key] = missing

    assert not gaps, (
        "COST_PROFILES routes with no priced row in config/pricing.yaml "
        f"(add a row or fix the alias): {gaps}"
    )


def test_coverage_gate_detects_a_genuinely_unpriced_route(runner) -> None:
    """Mutation-style self-check: prove the gate actually catches a gap
    rather than trivially passing regardless of pricing.yaml's contents."""
    fabricated_priced_keys = {"openai/gpt-5.4"}  # deliberately sparse
    profile = runner.COST_PROFILES["value-default"]
    missing = _profile_route_gaps(runner, fabricated_priced_keys, "value-default", profile)
    assert missing, "expected the coverage gate to flag routes against a near-empty registry"
