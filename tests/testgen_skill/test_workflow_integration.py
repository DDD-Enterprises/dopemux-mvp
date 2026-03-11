from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "templates" / "skills" / "testgen" / "scripts" / "testgen_workflow.py"
    spec = importlib.util.spec_from_file_location("testgen_workflow", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load testgen_workflow module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


workflow = _load_module()


def _request() -> object:
    return workflow.TestgenRequest(
        mode="tdd-driver",
        source="feature-list",
        payload="- Add audit logging for login attempts",
        coverage_target=90,
        preferred_cli="gemini",
        use_pal_testgen="auto",
    )


def test_strategy_prefers_clink_when_available(tmp_path: Path):
    availability = workflow.ToolAvailability(
        thinkdeep=True,
        planner=True,
        consensus=True,
        clink=True,
        pal_testgen=True,
    )

    plan = workflow.generate_testgen_plan(
        request=_request(),
        repo_root=tmp_path,
        tool_availability=availability,
        explicit_touched=["src/auth.py"],
    )

    assert plan["tool_strategy"]["specialist"]["primary"].startswith("clink:gemini")
    assert plan["tool_strategy"]["pal_testgen"] == "enabled"


def test_strategy_falls_back_without_clink(tmp_path: Path):
    availability = workflow.ToolAvailability(
        thinkdeep=True,
        planner=True,
        consensus=True,
        clink=False,
        pal_testgen=False,
    )

    plan = workflow.generate_testgen_plan(
        request=_request(),
        repo_root=tmp_path,
        tool_availability=availability,
        explicit_touched=["src/auth.py"],
    )

    assert plan["tool_strategy"]["specialist"]["primary"] == "builtin-test-specialist"
    assert plan["tool_strategy"]["pal_testgen"] == "disabled"


def test_forced_pal_testgen_requires_availability(tmp_path: Path):
    availability = workflow.ToolAvailability(
        thinkdeep=True,
        planner=True,
        consensus=True,
        clink=True,
        pal_testgen=False,
    )

    request = workflow.TestgenRequest(
        mode="post-impl-generator",
        source="feature-list",
        payload="- Keep bugfix from regressing",
        coverage_target=90,
        preferred_cli="claude",
        use_pal_testgen="on",
    )

    with pytest.raises(workflow.ToolingResolutionError):
        workflow.generate_testgen_plan(
            request=request,
            repo_root=tmp_path,
            tool_availability=availability,
            explicit_touched=["src/bugfix.py"],
        )


def test_copilot_prefers_codex_subagent_when_clink_available(tmp_path: Path):
    availability = workflow.ToolAvailability(
        thinkdeep=True,
        planner=True,
        consensus=True,
        clink=True,
        pal_testgen=False,
    )

    request = workflow.TestgenRequest(
        mode="post-impl-generator",
        source="feature-list",
        payload="- Verify checkout bugfix remains stable",
        coverage_target=90,
        preferred_cli="copilot",
        use_pal_testgen="auto",
    )

    plan = workflow.generate_testgen_plan(
        request=request,
        repo_root=tmp_path,
        tool_availability=availability,
        explicit_touched=["src/checkout.ts"],
    )

    assert plan["tool_strategy"]["specialist"]["primary"] == "clink:codex:test-specialist"
    assert plan["tool_strategy"]["specialist"]["fallback"] == "builtin-test-specialist"


def test_strict_reasoning_mode_fails_when_tools_missing(tmp_path: Path):
    availability = workflow.ToolAvailability(
        thinkdeep=False,
        planner=False,
        consensus=False,
        clink=False,
        pal_testgen=False,
    )

    with pytest.raises(workflow.ToolingResolutionError):
        workflow.generate_testgen_plan(
            request=_request(),
            repo_root=tmp_path,
            tool_availability=availability,
            explicit_touched=["src/auth.py"],
            allow_local_reasoning_fallback=False,
        )
