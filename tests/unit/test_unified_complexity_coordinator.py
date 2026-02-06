from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "complexity_coordinator"
    / "unified_complexity.py"
)


@pytest.fixture(scope="module")
def complexity_module():
    spec = importlib.util.spec_from_file_location("unified_complexity", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complexity_breakdown_to_dict_interpretation(complexity_module):
    low = complexity_module.ComplexityBreakdown(
        ast_score=0.2,
        lsp_score=0.2,
        usage_score=0.2,
        adhd_multiplier=1.0,
        unified_score=0.25,
        confidence=0.8,
    )
    medium = complexity_module.ComplexityBreakdown(
        ast_score=0.5,
        lsp_score=0.5,
        usage_score=0.5,
        adhd_multiplier=1.0,
        unified_score=0.5,
        confidence=0.8,
    )
    high = complexity_module.ComplexityBreakdown(
        ast_score=0.9,
        lsp_score=0.9,
        usage_score=0.9,
        adhd_multiplier=1.0,
        unified_score=0.9,
        confidence=0.8,
    )

    assert low.to_dict()["interpretation"].startswith("Low complexity")
    assert medium.to_dict()["interpretation"].startswith("Medium complexity")
    assert high.to_dict()["interpretation"].startswith("High complexity")


@pytest.mark.asyncio
async def test_unified_complexity_weighting_and_clamp(complexity_module, monkeypatch):
    coordinator = complexity_module.ComplexityCoordinator()

    async def _noop():
        return None

    async def _ast(*args, **kwargs):
        return (0.9, 0.9)

    async def _lsp(*args, **kwargs):
        return (0.8, 0.7)

    async def _usage(*args, **kwargs):
        return (0.7, 0.6)

    async def _adhd(*args, **kwargs):
        return 1.5

    monkeypatch.setattr(coordinator, "_ensure_clients", _noop)
    monkeypatch.setattr(coordinator, "get_ast_complexity", _ast)
    monkeypatch.setattr(coordinator, "get_lsp_complexity", _lsp)
    monkeypatch.setattr(coordinator, "get_usage_complexity", _usage)
    monkeypatch.setattr(coordinator, "get_adhd_multiplier", _adhd)

    breakdown = await coordinator.get_unified_complexity("src/example.py", "func", "hue")

    # Base score = 0.9*0.4 + 0.8*0.3 + 0.7*0.3 = 0.81; with multiplier 1.5 => 1.215, clamped to 1.0
    assert breakdown.unified_score == 1.0
    assert breakdown.confidence == pytest.approx((0.9 + 0.7 + 0.6) / 3.0)


@pytest.mark.asyncio
async def test_adhd_multiplier_clamps_in_bounds(complexity_module, monkeypatch):
    coordinator = complexity_module.ComplexityCoordinator()

    async def _noop():
        return None

    class _Config:
        async def get_state(self, user_id: str):
            return {"energy_level": "low", "attention_state": "scattered"}

    monkeypatch.setattr(coordinator, "_ensure_clients", _noop)
    coordinator._adhd_config = _Config()
    multiplier = await coordinator.get_adhd_multiplier("hue")
    assert multiplier == 1.5

    class _ConfigLow:
        async def get_state(self, user_id: str):
            return {"energy_level": "high", "attention_state": "hyperfocused"}

    coordinator._adhd_config = _ConfigLow()
    multiplier_low = await coordinator.get_adhd_multiplier("hue")
    assert multiplier_low == pytest.approx(0.56)
