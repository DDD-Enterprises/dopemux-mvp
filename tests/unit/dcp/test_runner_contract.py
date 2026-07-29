"""Tests for DMX-DCP-MODEL-ROUTING-MVP-0008 inert runner contract."""

from __future__ import annotations

import pytest

from dopemux.dcp.runner_contract import (
    RunnerContractError,
    RunnerInvocationPlan,
    RunnerPlanStatus,
    build_blocked_plan,
    document_plan,
    execute_runner_plan,
)


def test_plan_rejects_authorized_true():
    with pytest.raises(RunnerContractError):
        RunnerInvocationPlan(
            runner_id="claude",
            argv=("claude", "--version"),
            invocation_authorized=True,
        )


def test_execute_never_runs():
    plan = build_blocked_plan("claude", ["claude", "--version"])
    assert plan.invocation_authorized is False
    result = execute_runner_plan(plan)
    assert result.status is RunnerPlanStatus.NOT_RUN
    assert result.exit_code is None
    assert "not authorized" in result.error


def test_document_plan_serializes_false_auth():
    plan = build_blocked_plan("codex", ["codex", "--version"])
    doc = document_plan(plan)
    d = doc.to_dict()
    assert d["invocation_authorized"] is False
    assert d["plan"]["invocation_authorized"] is False
    assert d["result"]["status"] == "NOT_RUN"
    assert "no_subprocess_executed" in d["proof_envelope"]["non_claims"]


def test_no_subprocess_import_side_effects():
    import dopemux.dcp.runner_contract as mod
    assert not hasattr(mod, "subprocess")
    import ast
    from pathlib import Path
    tree = ast.parse(Path(mod.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = {"subprocess", "socket", "httpx", "requests", "asyncio"}
    assert forbidden.isdisjoint(set(imports))
