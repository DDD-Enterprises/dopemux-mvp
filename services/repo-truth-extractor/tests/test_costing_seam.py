from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from extractor import costing  # noqa: E402


def _deps(writes: list[tuple[Path, dict]]) -> costing.CostingDeps:
    return costing.CostingDeps(
        selected_execution_step_ids_for_phase=lambda _cfg, _phase: None,
        collect_provider_routes=lambda **_kwargs: {
            "openrouter:openai/gpt-5-mini:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5-mini",
            }
        },
        load_pricing_registry=lambda: (
            {
                "openrouter/openai/gpt-5-mini": {
                    "input_cost_per_m": Decimal("1.00"),
                    "output_cost_per_m": Decimal("1.00"),
                }
            },
            "sha-test",
        ),
        pricing_config_path=Path("/tmp/pricing.yaml"),
        write_json=lambda path, payload: writes.append((path, payload)),
        telemetry_path=lambda root, filename: root / "telemetry" / filename,
        now_iso=lambda: "2026-07-12T00:00:00+00:00",
        pricing_surface_metadata=lambda **_kwargs: {"pricing_surface": "test"},
        spend_ledger_filename="spend_ledger.json",
    )


def test_spend_tracker_initializes_and_exposes_active_state() -> None:
    writes: list[tuple[Path, dict]] = []
    deps = _deps(writes)
    cfg = SimpleNamespace(
        max_cost_usd=0.10,
        partition_workers=1,
        routing_policy="balanced_openrouter",
        cost_profile="value-default",
    )

    costing.reset_spend_tracker()
    try:
        snapshot = costing.initialize_spend_tracker(
            deps=deps,
            run_root=Path("/tmp/rte-costing"),
            run_id="costing-init",
            cfg=cfg,
            phases=["A"],
        )

        state = costing.get_active_spend_tracker()
        assert snapshot is not None
        assert state is not None
        assert state.run_id == "costing-init"
        assert snapshot["pricing_sha256"] == "sha-test"
        assert writes[0][0] == Path("/tmp/rte-costing/telemetry/spend_ledger.json")
    finally:
        costing.reset_spend_tracker()


def test_spend_tracker_records_post_response_breach_and_snapshot() -> None:
    writes: list[tuple[Path, dict]] = []
    deps = _deps(writes)
    cfg = SimpleNamespace(
        max_cost_usd=Decimal("0.10"),
        partition_workers=1,
        routing_policy="balanced_openrouter",
        cost_profile="value-default",
    )

    costing.reset_spend_tracker()
    try:
        costing.initialize_spend_tracker(
            deps=deps,
            run_root=Path("/tmp/rte-costing"),
            run_id="costing-breach",
            cfg=cfg,
            phases=["A"],
        )
        updated = costing.record_request_cost(
            deps=deps,
            meta={
                "response_summary": {
                    "usage": {
                        "prompt_tokens": 100_000,
                        "completion_tokens": 100_000,
                        "total_tokens": 200_000,
                    }
                }
            },
            phase="A",
            step_id="A1",
            partition_id="A_P0001",
            provider="openrouter",
            model_id="openai/gpt-5-mini",
        )

        state = costing.get_active_spend_tracker()
        assert state is not None
        assert updated["failure_type"] == "cost_aborted"
        assert updated["cost_cap"]["cost_abort_triggered"] is True
        assert state.cost_abort_triggered is True
        assert writes[-1][1]["entries_total"] == 1
    finally:
        costing.reset_spend_tracker()
