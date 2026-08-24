"""TP-RTE-TRUTH-R2-001 — single pricing authority, fail-closed catalog.

This is the MANDATORY-VERIFICATION core proof for the packet: without it,
per the dispatch instructions, "the packet is not done." It builds the
fixture table described in A2 §5.5 (claudedocs/rte-truth-program-2026-07/
A2-cost-truthfulness.md) and asserts:

  1. For identical usage (same provider/model/tokens/optimizer context),
     preview (E2 SpendLedger.price_usage), the preventive-check pricing path
     (run_extraction_v5._pricing_preview, the function backing
     _check_projected_cost_limit), and E2 accounting (SpendLedger.accumulate)
     all produce the SAME dollar figure — trivially true once they share one
     code path, but asserted explicitly as a regression guard.
  2. For identical usage, E2's accounting (SpendLedger, catalog-authority
     rates + optimizer multipliers) and E3's accounting
     (extractor.costing.estimate_usage_cost_usd / record_request_cost,
     pricing.yaml-authority Decimal math) produce the SAME dollar figure —
     the actual cross-authority proof that F-11's "two authorities disagree"
     defect (preview/preventive E2 multiplier-adjusted vs. abort-authority E3
     flat, ~2x divergence on flex profiles) is closed. Both a flat/default
     scenario AND a flex-tier scenario (the specific case the audit named)
     are covered, plus batch and cached-input scenarios.
  3. A catalog LOAD failure (missing config/pricing.yaml, or one missing its
     `models` map) blocks every costed code path with a RuntimeError instead
     of silently repricing at a $0.15/$0.60 baseline (F-10).
  4. An unknown model with a spend cap set raises in BOTH E2 and E3,
     consistently (F-10/F-11 requirement #3: raise-with-cap, never a
     fabricated number).

Both E2 and E3 load their registry from the SAME real config/pricing.yaml
file via extractor.costing.load_pricing_registry — not two independently
hand-authored mock registries — so this genuinely exercises the unified
authority rather than two coincidentally-matching test fixtures.
"""

from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _service_root() -> Path:
    return _repo_root() / "services" / "repo-truth-extractor"


def _load_module(name: str, relative_path: str):
    module_path = _service_root() / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    if str(_service_root()) not in sys.path:
        sys.path.insert(0, str(_service_root()))
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def costing():
    return _load_module("costing_fixture_table", "extractor/costing.py")


@pytest.fixture(scope="module")
def spend_ledger():
    return _load_module("spend_ledger_fixture_table", "lib/spend_ledger.py")


@pytest.fixture(scope="module")
def runner():
    return _load_module("run_extraction_v5_fixture_table", "run_extraction_v5.py")


@pytest.fixture(scope="module")
def real_pricing_registry(costing):
    """The REAL config/pricing.yaml, loaded through the single authority — the
    exact same function extractor.costing.initialize_spend_tracker uses at
    startup. Both E2 and E3 price against THIS registry in the tests below,
    so a passing test proves the two authorities agree on real data, not on
    two independently-crafted mocks."""
    registry, _sha = costing.load_pricing_registry(_repo_root() / "config" / "pricing.yaml")
    return registry


def _make_runner_cfg(runner, **overrides) -> Any:
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


# ---------------------------------------------------------------------------
# Fixture table (A2 §5.5): identical usage, multiple optimizer contexts.
# ---------------------------------------------------------------------------

FIXTURE_TABLE = [
    pytest.param(
        "openai", "gpt-5.4", 1_000_000, 100_000,
        {}, {},
        id="default_no_optimizers",
    ),
    pytest.param(
        "openai", "gpt-5.4", 1_000_000, 100_000,
        {"service_tier": "flex"}, {"service_tier": "flex"},
        id="flex_tier_the_audit_named_case",
    ),
    pytest.param(
        "openai", "gpt-5.4", 1_000_000, 100_000,
        {"is_batch": True}, {"is_batch": True},
        id="batch_discount",
    ),
    pytest.param(
        "openai", "gpt-5.4", 1_000_000, 0,
        {"cached_input_tokens": 500_000}, {"cached_input_tokens": 500_000},
        id="cached_input",
    ),
    pytest.param(
        "openai", "gpt-5.4", 1_000_000, 100_000,
        {"service_tier": "flex", "cached_input_tokens": 500_000},
        {"service_tier": "flex", "cached_input_tokens": 500_000},
        id="combined_flex_and_cache",
    ),
]


@pytest.mark.parametrize("provider,model_id,input_tokens,output_tokens,e2_kwargs,e3_kwargs", FIXTURE_TABLE)
def test_preview_preventive_and_e2_accounting_agree_for_identical_usage(
    runner,
    provider: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    e2_kwargs: dict,
    e3_kwargs: dict,
    tmp_path: Path,
) -> None:
    """Preview, preventive check, and E2 accounting are one code path
    (SpendLedger.price_usage) — assert that stays true across every fixture
    row, not just the default case.

    _pricing_preview (the function backing the preview print AND
    _check_projected_cost_limit's preventive check) derives its optimizer
    context from `cfg` + `execution_mode`, not from arbitrary kwargs, so this
    test configures cfg/execution_mode/cached_input_tokens to match each
    fixture row's e2_kwargs exactly, then asserts the same dollar figure
    comes out of the direct price_usage/accumulate calls that use e2_kwargs
    directly.
    """
    service_tier = e2_kwargs.get("service_tier")
    is_batch = bool(e2_kwargs.get("is_batch"))
    cached_input_tokens = int(e2_kwargs.get("cached_input_tokens", 0) or 0)

    cfg = _make_runner_cfg(
        runner,
        default_service_tier=service_tier or "default",
        enable_batch_when_supported=True,
        enable_cached_input=True,
    )
    ledger = runner.SpendLedger(tmp_path, f"fixture_{provider}_{model_id}".replace("/", "_").replace(".", "_"))
    object.__setattr__(cfg, "ledger", ledger)

    preview = runner._pricing_preview(
        cfg,
        provider=provider,
        model_id=model_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        execution_mode="batch_submit" if is_batch else "sync",
        cached_input_tokens=cached_input_tokens,
    )
    assert preview is not None
    preview_cost = preview["estimated_cost_usd"]

    direct = ledger.price_usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        provider=provider,
        model_id=model_id,
        **e2_kwargs,
    )
    assert direct["estimated_cost_usd"] == pytest.approx(preview_cost, abs=1e-9)

    accumulated = ledger.accumulate(
        "FIXTURE",
        input_tokens,
        output_tokens,
        provider=provider,
        model_id=model_id,
        **e2_kwargs,
    )
    assert accumulated["estimated_cost_usd"] == pytest.approx(preview_cost, abs=1e-9)


@pytest.mark.parametrize("provider,model_id,input_tokens,output_tokens,e2_kwargs,e3_kwargs", FIXTURE_TABLE)
def test_e2_and_e3_authorities_agree_for_identical_usage(
    costing,
    real_pricing_registry,
    provider: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    e2_kwargs: dict,
    e3_kwargs: dict,
    tmp_path: Path,
) -> None:
    """THE core proof (F-11 fix): E2 (SpendLedger, optimizer-aware) and E3
    (SpendTrackerState/estimate_usage_cost_usd, Decimal money-math) price the
    SAME usage identically, including the flex-tier case the audit named as
    a ~2x divergence. Both load rates from the SAME real config/pricing.yaml
    via extractor.costing.load_pricing_registry — one authority, verified on
    real data, not on two independently-authored mocks."""
    resolved_rate = costing.resolve_model_rate(real_pricing_registry, provider, model_id)
    assert resolved_rate["unknown_model"] is False, "fixture model must be priced"

    e2_breakdown = costing.compute_optimized_cost(
        resolved_rate,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        prompt_token_count=input_tokens,
        **e2_kwargs,
    )
    e2_cost = e2_breakdown["final_cost_usd"]

    e3_cost = costing.estimate_usage_cost_usd(
        provider=provider,
        model_id=model_id,
        usage={"prompt_tokens": input_tokens, "completion_tokens": output_tokens},
        pricing_registry=real_pricing_registry,
        **e3_kwargs,
    )

    assert float(e3_cost) == pytest.approx(e2_cost, abs=1e-6), (
        f"E2/E3 pricing diverged for {provider}/{model_id} "
        f"in={input_tokens} out={output_tokens} ctx={e2_kwargs}: "
        f"E2={e2_cost} E3={e3_cost}"
    )


def test_e2_and_e3_agree_via_the_actual_record_request_cost_seam(
    costing,
    real_pricing_registry,
    tmp_path: Path,
) -> None:
    """Same as above but through the real production seam
    (extractor.costing.record_request_cost / initialize_spend_tracker),
    proving the wired accounting path — not just the underlying math
    function — produces the number E2 would produce for the same usage and
    optimizer context."""
    writes: list[tuple[Path, dict]] = []
    deps = costing.CostingDeps(
        selected_execution_step_ids_for_phase=lambda _cfg, _phase: None,
        collect_provider_routes=lambda **_kwargs: {
            "openai:gpt-5.4:OPENAI_API_KEY": {"provider": "openai", "model_id": "gpt-5.4"}
        },
        load_pricing_registry=lambda: costing.load_pricing_registry(_repo_root() / "config" / "pricing.yaml"),
        pricing_config_path=_repo_root() / "config" / "pricing.yaml",
        write_json=lambda path, payload: writes.append((path, payload)),
        telemetry_path=lambda root, filename: root / "telemetry" / filename,
        now_iso=lambda: "2026-07-27T00:00:00+00:00",
        pricing_surface_metadata=lambda **_kwargs: {"pricing_surface": "test"},
        spend_ledger_filename="spend_ledger.json",
    )
    cfg = SimpleNamespace(
        max_cost_usd=1000.0,
        partition_workers=1,
        routing_policy="balanced_openrouter",
        cost_profile="value-default",
    )
    costing.reset_spend_tracker()
    try:
        costing.initialize_spend_tracker(
            deps=deps, run_root=tmp_path, run_id="seam-parity", cfg=cfg, phases=["A"]
        )
        updated = costing.record_request_cost(
            deps=deps,
            meta={
                "response_summary": {
                    "usage": {"prompt_tokens": 1_000_000, "completion_tokens": 100_000}
                }
            },
            phase="A",
            step_id="A1",
            partition_id="A_P0001",
            provider="openai",
            model_id="gpt-5.4",
            service_tier="flex",
        )
        e3_cost = updated["cost_event"]["cost_usd"]

        resolved_rate = costing.resolve_model_rate(real_pricing_registry, "openai", "gpt-5.4")
        e2_breakdown = costing.compute_optimized_cost(
            resolved_rate,
            input_tokens=1_000_000,
            output_tokens=100_000,
            service_tier="flex",
            prompt_token_count=1_000_000,
        )
        assert e3_cost == pytest.approx(e2_breakdown["final_cost_usd"], abs=1e-6)
    finally:
        costing.reset_spend_tracker()


# ---------------------------------------------------------------------------
# Catalog-failure fixture: must BLOCK, never silently reprice (F-10).
# ---------------------------------------------------------------------------


def test_catalog_load_failure_blocks_rather_than_repricing_missing_file(costing, tmp_path: Path) -> None:
    costing.reset_pricing_registry_cache()
    missing_path = tmp_path / "does_not_exist_pricing.yaml"
    with pytest.raises(RuntimeError, match="Pricing config missing"):
        costing.load_pricing_registry(missing_path)
    with pytest.raises(RuntimeError, match="Pricing config missing"):
        costing.load_pricing_registry_cached(missing_path)


def test_catalog_load_failure_blocks_rather_than_repricing_no_models_map(costing, tmp_path: Path) -> None:
    costing.reset_pricing_registry_cache()
    broken_path = tmp_path / "broken_pricing.yaml"
    broken_path.write_text("version: RTE_PRICING_V2\n", encoding="utf-8")  # no `models:` key
    with pytest.raises(RuntimeError, match="missing models map"):
        costing.load_pricing_registry(broken_path)


def test_catalog_load_failure_blocks_spend_tracker_init(costing, tmp_path: Path) -> None:
    """E3 startup: a broken catalog must fail closed at initialize_spend_tracker
    (the codepath run_extraction_v5.py wraps with sys.exit(1) on any startup
    RuntimeError), never construct a tracker with degraded pricing."""
    broken_path = tmp_path / "broken_pricing.yaml"
    broken_path.write_text("version: RTE_PRICING_V2\n", encoding="utf-8")
    deps = costing.CostingDeps(
        selected_execution_step_ids_for_phase=lambda _cfg, _phase: None,
        collect_provider_routes=lambda **_kwargs: {
            "openai:gpt-5.4:OPENAI_API_KEY": {"provider": "openai", "model_id": "gpt-5.4"}
        },
        load_pricing_registry=lambda: costing.load_pricing_registry(broken_path),
        pricing_config_path=broken_path,
        write_json=lambda path, payload: None,
        telemetry_path=lambda root, filename: root / "telemetry" / filename,
        now_iso=lambda: "2026-07-27T00:00:00+00:00",
        pricing_surface_metadata=lambda **_kwargs: {},
        spend_ledger_filename="spend_ledger.json",
    )
    cfg = SimpleNamespace(
        max_cost_usd=1.0, partition_workers=1, routing_policy="balanced_openrouter", cost_profile="value-default"
    )
    costing.reset_spend_tracker()
    try:
        with pytest.raises(RuntimeError, match="missing models map"):
            costing.initialize_spend_tracker(deps=deps, run_root=tmp_path, run_id="broken-catalog", cfg=cfg, phases=["A"])
        assert costing.get_active_spend_tracker() is None, "a broken catalog must never leave a tracker active"
    finally:
        costing.reset_spend_tracker()


def test_catalog_load_failure_blocks_spend_ledger_get_model_cost_rate(spend_ledger, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """E2 side: lib.spend_ledger.get_model_cost_rate must propagate a broken
    catalog as RuntimeError too — this is the exact defect F-10 named
    (spend_ledger.py used to catch this and silently degrade to
    $0.15/$0.60). It must not be catchable-and-ignorable by accident."""
    broken_path = tmp_path / "broken_pricing.yaml"
    broken_path.write_text("version: RTE_PRICING_V2\n", encoding="utf-8")
    monkeypatch.setattr(spend_ledger, "PRICING_CONFIG_PATH", broken_path)
    with pytest.raises(RuntimeError, match="missing models map"):
        spend_ledger.get_model_cost_rate(provider="openai", model_id="gpt-5.4")


# ---------------------------------------------------------------------------
# Unknown model + cap set: raise consistently in both authorities.
# ---------------------------------------------------------------------------


def test_unknown_model_raises_in_both_authorities_when_cap_is_set(
    spend_ledger, costing, real_pricing_registry, tmp_path: Path
) -> None:
    # E2
    capped_ledger = spend_ledger.SpendLedger(tmp_path, "unknown_cap_e2", max_cost_usd=5.0)
    with pytest.raises(RuntimeError, match="Unknown model pricing with a spend cap set"):
        capped_ledger.accumulate("A", 100, 50, provider="mystery", model_id="unknown-model-x")

    # E3 (E3 only ever exists once a cap is set, by construction — see
    # initialize_spend_tracker's early return when cfg.max_cost_usd is None —
    # so "unknown model reaches estimate_usage_cost_usd" IS the cap-set case).
    with pytest.raises(RuntimeError, match="Missing pricing for route"):
        costing.estimate_usage_cost_usd(
            provider="mystery",
            model_id="unknown-model-x",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            pricing_registry=real_pricing_registry,
        )


def test_unknown_model_marks_unpriced_without_a_cap_in_e2(spend_ledger, tmp_path: Path) -> None:
    """No cap set -> UNPRICED with a $0.00 rate, never a fabricated number."""
    uncapped_ledger = spend_ledger.SpendLedger(tmp_path, "unknown_no_cap")
    priced = uncapped_ledger.accumulate("A", 100, 50, provider="mystery", model_id="unknown-model-x")
    assert priced["unknown_model"] is True
    assert priced["pricing_status"] == "UNPRICED_UNKNOWN"
    assert priced["estimated_cost_usd"] == 0.0
