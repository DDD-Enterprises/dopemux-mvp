"""Launch preflight must probe the routes the ACTIVE cost profile will run.

Regression for the Codex P1: rte_ops_surfaces.run_provider_preflight called the
collect_provider_routes callback without cost_profile, so a launch on a
non-default profile (grok-fast/gemini-value/openrouter-resilient) preflighted
value-default/OpenAI routes instead of the routes that actually execute — a
missing provider key could slip through.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import rte_ops_surfaces


def _run_preflight_capturing(cfg, tmp_path: Path):
    recorded: dict = {}

    def fake_collect_provider_routes(**kwargs):
        recorded.update(kwargs)
        return {}  # no routes -> no probes -> PASS, keeps the test focused

    ok, _payload = rte_ops_surfaces.run_provider_preflight(
        root=tmp_path,
        run_id="r-test",
        cfg=cfg,
        phases=["A"],
        selected_execution_step_ids_for_phase=lambda _cfg, _phase: None,
        collect_provider_routes=fake_collect_provider_routes,
        run_provider_doctor_probe=lambda **_kw: {"ready": True},
        resolve_api_key=lambda _p, _e: ("", ""),
        current_doctor_root=lambda root: root,
        now_iso=lambda: "2026-06-05T00:00:00Z",
        write_json=lambda _path, _data: None,
        routing_policy_version="v-test",
    )
    return ok, recorded


def test_launch_preflight_forwards_active_cost_profile(tmp_path: Path) -> None:
    cfg = SimpleNamespace(
        routing_policy="balanced_openrouter",
        cost_profile="grok-fast",
        model_alias_overrides=(),
        batch_mode=False,
        batch_provider="auto",
    )
    ok, recorded = _run_preflight_capturing(cfg, tmp_path)
    assert recorded.get("cost_profile") == "grok-fast"
    assert ok is True


def test_launch_preflight_forwards_model_alias_overrides(tmp_path: Path) -> None:
    # An operator --model-alias to a different provider must be probed, not the
    # profile default — else the launch passes without checking the real key.
    overrides = (("BULK_DOCS_MODEL", "xai/grok-4.3"),)
    cfg = SimpleNamespace(
        routing_policy="balanced_openrouter",
        cost_profile="value-default",
        model_alias_overrides=overrides,
        batch_mode=False,
        batch_provider="auto",
    )
    ok, recorded = _run_preflight_capturing(cfg, tmp_path)
    assert recorded.get("model_alias_overrides") == overrides
    assert ok is True
