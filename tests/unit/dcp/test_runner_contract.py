"""Tests for DMX-DCP-MODEL-ROUTING-MVP-0008 / R6 inert runner contract."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import jsonschema
import pytest

from dopemux.dcp.runner_contract import (
    InertRunnerAdapter,
    RunnerAdapter,
    RunnerContractDocument,
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


def test_document_plan_serializes_false_auth_and_validates_schema():
    schema_path = (
        Path(__file__).resolve().parents[3]
        / "schemas"
        / "dcp"
        / "runner_contract.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)

    # Test 1: without optional timeout_seconds
    plan_no_timeout = build_blocked_plan("codex", ["codex", "--version"])
    doc1 = document_plan(plan_no_timeout)
    d1 = doc1.to_dict()
    assert d1["invocation_authorized"] is False
    assert "invocation_authorized" not in d1["plan"]
    assert "timeout_seconds" not in d1["plan"]
    assert d1["result"]["status"] == "NOT_RUN"
    assert "no_process_spawned" in d1["proof_envelope"]["non_claims"]
    errors1 = list(validator.iter_errors(d1))
    assert not errors1, f"Schema validation failed: {[e.message for e in errors1]}"

    # Test 2: with optional timeout_seconds as float
    plan_with_timeout = build_blocked_plan(
        "claude", ["claude", "--version"], timeout_seconds=30.0
    )
    doc2 = document_plan(plan_with_timeout)
    d2 = doc2.to_dict()
    assert d2["plan"]["timeout_seconds"] == 30.0
    errors2 = list(validator.iter_errors(d2))
    assert not errors2, f"Schema validation failed: {[e.message for e in errors2]}"


def test_runner_adapter_protocol_conformance():
    adapter = InertRunnerAdapter("claude")
    assert isinstance(adapter, RunnerAdapter)

    plan = adapter.plan_invocation(["claude", "--version"], timeout_seconds=15.0)
    assert plan.runner_id == "claude"
    assert plan.invocation_authorized is False
    assert plan.timeout_seconds == 15.0

    result = adapter.execute(plan)
    assert result.status is RunnerPlanStatus.NOT_RUN


def test_no_subprocess_or_bridge_import_side_effects():
    import dopemux.dcp.runner_contract as mod

    assert not hasattr(mod, "subprocess")
    tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = {
        "subprocess",
        "socket",
        "httpx",
        "requests",
        "asyncio",
        "dopecon_bridge",
        "dope_memory",
        "dope_context",
        "task_orchestrator",
    }
    assert forbidden.isdisjoint(set(imports))
