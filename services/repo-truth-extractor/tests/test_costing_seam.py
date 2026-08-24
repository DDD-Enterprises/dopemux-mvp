from __future__ import annotations

from decimal import Decimal
from importlib import reload
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from extractor import costing  # noqa: E402
from extractor._spend_tracker_registry import get_registry  # noqa: E402


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


def test_spend_tracker_refuses_breach_before_recording_spend() -> None:
    """TP-RTE-TRUTH-R2-003 (F-13/A2-7): default cost_cap_mode="preventive"
    checks a call's cost against max_cost_usd BEFORE committing it, so a
    single over-cap call is refused rather than recorded-then-flagged. This
    replaces the pre-fix "records_post_response_breach_and_snapshot" test,
    which asserted the OLD commit-then-compare overshoot (entries_total==1
    with the breaching call's cost already added to the total)."""
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
        state = costing.get_active_spend_tracker()
        assert state is not None
        assert state.cost_cap_mode == "preventive"
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

        assert updated["failure_type"] == "cost_aborted"
        assert updated["cost_cap"]["cost_abort_triggered"] is True
        assert updated["spend_ledger_recorded"] is False
        assert state.cost_abort_triggered is True
        # The breaching call's cost was never committed: refused before
        # spend, not recorded-then-noticed (the exact F-13 overshoot).
        assert state.total_cost_usd == Decimal("0")
        assert state.entries == []
        assert writes[-1][1]["entries_total"] == 0
        assert writes[-1][1]["total_cost_usd"] == 0.0
    finally:
        costing.reset_spend_tracker()


def test_spend_tracker_post_hoc_mode_commits_then_flags_breach() -> None:
    """TP-RTE-TRUTH-R2-003: cost_cap_mode="post_hoc" is the explicit opt-in
    legacy path proving the field is wired to real behavior (not
    decorative) -- it reproduces the pre-fix commit-then-compare overshoot
    that "preventive" (the default, proven above) no longer exhibits."""
    writes: list[tuple[Path, dict]] = []
    deps = _deps(writes)
    cfg = SimpleNamespace(
        max_cost_usd=Decimal("0.10"),
        partition_workers=1,
        routing_policy="balanced_openrouter",
        cost_profile="value-default",
        cost_cap_mode="post_hoc",
    )

    costing.reset_spend_tracker()
    try:
        costing.initialize_spend_tracker(
            deps=deps,
            run_root=Path("/tmp/rte-costing"),
            run_id="costing-breach-post-hoc",
            cfg=cfg,
            phases=["A"],
        )
        state = costing.get_active_spend_tracker()
        assert state is not None
        assert state.cost_cap_mode == "post_hoc"
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

        assert updated["failure_type"] == "cost_aborted"
        assert updated["cost_cap"]["cost_abort_triggered"] is True
        assert state.cost_abort_triggered is True
        assert writes[-1][1]["entries_total"] == 1
        assert writes[-1][1]["total_cost_usd"] > 0.1
    finally:
        costing.reset_spend_tracker()


def test_spend_tracker_registry_identity_survives_dual_imports() -> None:
    """Test that tracker registry identity is stable across module reloads.

    This verifies the fix for R1-004 dual-import desync. When tests load
    the costing module (directly or via v5) multiple times, the registry
    must maintain a single identity so tracker state doesn't diverge.

    Mechanism:
    - The registry is a dedicated module pinned in sys.modules
    - Even if costing.py is reloaded, the registry module stays cached
    - All accesses to the registry get the same object with the same state
    """
    writes: list[tuple[Path, dict]] = []
    deps = _deps(writes)
    cfg = SimpleNamespace(
        max_cost_usd=1.0,
        partition_workers=1,
        routing_policy="balanced_openrouter",
        cost_profile="value-default",
    )

    # Store the initial registry identity
    initial_registry = get_registry()
    initial_registry_id = id(initial_registry)

    costing.reset_spend_tracker()
    try:
        # Initialize tracker
        snapshot = costing.initialize_spend_tracker(
            deps=deps,
            run_root=Path("/tmp/rte-dual-load"),
            run_id="dual-load-test",
            cfg=cfg,
            phases=["A"],
        )
        assert snapshot is not None

        # Get tracker before reload
        tracker_before = costing.get_active_spend_tracker()
        assert tracker_before is not None
        assert tracker_before.run_id == "dual-load-test"

        # Reload the costing module (simulating what happens in dual imports)
        reload(costing)

        # After reload, registry identity must be the same
        reloaded_registry = get_registry()
        assert id(reloaded_registry) == initial_registry_id, (
            "Registry identity changed after reload; "
            "tracker state may desync between module instances"
        )

        # Tracker state must still be accessible and unchanged
        tracker_after = costing.get_active_spend_tracker()
        assert tracker_after is not None, "Tracker lost after reload"
        assert tracker_after.run_id == "dual-load-test", (
            "Tracker state diverged after reload; "
            "different module objects may have different state"
        )
        assert tracker_after is tracker_before, (
            "Tracker object identity changed; "
            "imports are now accessing different state"
        )
    finally:
        costing.reset_spend_tracker()
