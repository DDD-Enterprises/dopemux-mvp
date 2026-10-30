"""Parity between the ADHD engine MCP tools and the engines that serve them.

``services/adhd_engine/main.py`` exposes MCP tools that call ``engine.<method>()``.
Both the real ``ADHDAccommodationEngine`` and the test-mode ``_FallbackADHDEngine``
must implement every method those tools call.
"""

import ast
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services.adhd_engine.core.engine import ADHDAccommodationEngine
from services.adhd_engine.core.models import AttentionState, EnergyLevel

REPO_ROOT = Path(__file__).parent.parent.parent
MAIN_PATH = REPO_ROOT / "services" / "adhd_engine" / "main.py"
ENGINE_PATH = REPO_ROOT / "services" / "adhd_engine" / "core" / "engine.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _class_methods(tree: ast.Module, class_name: str) -> set[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    raise AssertionError(f"class {class_name} not found")


def _is_mcp_tool(func: ast.AsyncFunctionDef) -> bool:
    for dec in func.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if (
            isinstance(target, ast.Attribute)
            and target.attr == "tool"
            and isinstance(target.value, ast.Name)
            and target.value.id == "mcp"
        ):
            return True
    return False


def _engine_calls_in_mcp_tools(tree: ast.Module) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and _is_mcp_tool(node):
            for sub in ast.walk(node):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Attribute)
                    and isinstance(sub.func.value, ast.Name)
                    and sub.func.value.id == "engine"
                ):
                    called.add(sub.func.attr)
    return called


def test_mcp_tool_engine_calls_exist_on_both_engines():
    main_tree = _parse(MAIN_PATH)
    called = _engine_calls_in_mcp_tools(main_tree)
    real_methods = _class_methods(_parse(ENGINE_PATH), "ADHDAccommodationEngine")
    fallback_methods = _class_methods(main_tree, "_FallbackADHDEngine")

    assert called, "no engine calls found in MCP tools; the parser is broken"
    assert called >= {
        "get_energy_level",
        "get_attention_state",
        "get_cognitive_load",
        "assess_task",
    }
    assert not (called - real_methods), f"missing on ADHDAccommodationEngine: {sorted(called - real_methods)}"
    assert not (called - fallback_methods), f"missing on _FallbackADHDEngine: {sorted(called - fallback_methods)}"


@pytest.fixture
def engine():
    eng = ADHDAccommodationEngine()
    eng.current_energy_levels["u1"] = EnergyLevel.HIGH
    eng.current_attention_states["u1"] = AttentionState.SCATTERED
    return eng


async def test_energy_level_reads_engine_state(engine):
    snapshot = await engine.get_energy_level("u1")

    assert snapshot.level == "high"
    assert snapshot.score == 0.7


async def test_unknown_user_gets_route_defaults(engine):
    assert (await engine.get_energy_level("nobody")).level == "medium"
    assert (await engine.get_attention_state("nobody")).state == "focused"


async def test_attention_state_reads_engine_state(engine):
    assert (await engine.get_attention_state("u1")).state == "scattered"


async def test_cognitive_load_is_float_in_unit_range(engine, monkeypatch):
    mock = AsyncMock(return_value=0.42)
    monkeypatch.setattr(engine, "_calculate_cognitive_load", mock)

    load = await engine.get_cognitive_load("u1")

    assert load == 0.42
    assert isinstance(load, float)
    mock.assert_awaited_once_with("u1")


async def test_assess_task_uses_operator_and_marks_defaults(engine, monkeypatch):
    mock = AsyncMock(return_value={"suitable": True})
    monkeypatch.setattr(engine, "assess_task_suitability", mock)

    assessment = await engine.assess_task("Write docs", "x")

    assert assessment.dict() == {
        "suitable": True,
        "defaults_used": ["complexity_score", "estimated_minutes"],
    }
    args, kwargs = mock.await_args
    assert args[0] == engine.operator_user_id
    task_data = args[1] if len(args) > 1 else kwargs["task_data"]
    assert task_data["title"] == "Write docs"
    assert task_data["description"] == "x"
    assert task_data["complexity_score"] == 0.5
    assert task_data["estimated_minutes"] == 30
