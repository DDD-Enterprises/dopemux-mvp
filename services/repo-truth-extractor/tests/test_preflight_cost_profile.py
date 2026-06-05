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


def test_launch_preflight_forwards_active_cost_profile(tmp_path: Path) -> None:
    recorded: dict = {}

    def fake_collect_provider_routes(**kwargs):
        recorded.update(kwargs)
        return {}  # no routes -> no probes -> PASS, keeps the test focused

    cfg = SimpleNamespace(
        routing_policy="balanced_openrouter",
        cost_profile="grok-fast",
        batch_mode=False,
        batch_provider="auto",
    )

    ok, payload = rte_ops_surfaces.run_provider_preflight(
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

    assert recorded.get("cost_profile") == "grok-fast"
    assert ok is True
