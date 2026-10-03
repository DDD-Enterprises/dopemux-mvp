"""Tests for DMX-DCP-MODEL-ROUTING-MVP-0009 / R6 runner capability registry."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from dopemux.dcp.runner_capability_registry import (
    CapabilityRegistryError,
    assert_no_invocation_authorized,
    load_runner_capabilities,
)
from dopemux.dcp.runner_contract import (
    RunnerPlanStatus,
    build_blocked_plan,
    execute_runner_plan,
)


def test_default_registry_disables_all_invocation():
    reg = load_runner_capabilities()
    assert reg.global_invocation_authorized is False
    assert reg.authorized_runners() == []
    assert_no_invocation_authorized(reg)
    assert len(reg.runners) >= 1
    for r in reg.runners:
        assert r.invocation_authorized is False
        assert r.mutation_authorized is False
        assert r.paid_inference_authorized is False


def test_default_registry_conforms_to_schema():
    schema_path = (
        Path(__file__).resolve().parents[3]
        / "schemas"
        / "dcp"
        / "runner_capability_registry.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    reg_path = (
        Path(__file__).resolve().parents[3]
        / "config"
        / "dcp"
        / "runner_capabilities.json"
    )
    raw = json.loads(reg_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(raw))
    assert not errors, f"Registry schema validation failed: {[e.message for e in errors]}"


def test_rejects_authorized_runner(tmp_path: Path):
    bad = {
        "schema_version": "1.0.0",
        "global_invocation_authorized": False,
        "global_mutation_authorized": False,
        "global_paid_inference_authorized": False,
        "runners": [
            {
                "runner_id": "evil",
                "installed": True,
                "resolved_path": "/bin/evil",
                "version_text": "1",
                "invocation_authorized": True,
                "mutation_authorized": False,
                "paid_inference_authorized": False,
                "notes": "nope",
            }
        ],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(CapabilityRegistryError):
        load_runner_capabilities(p)


def test_rejects_global_flags(tmp_path: Path):
    for key in (
        "global_invocation_authorized",
        "global_mutation_authorized",
        "global_paid_inference_authorized",
    ):
        bad = {
            "schema_version": "1.0.0",
            "global_invocation_authorized": False,
            "global_mutation_authorized": False,
            "global_paid_inference_authorized": False,
            "runners": [],
        }
        bad[key] = True
        p = tmp_path / f"bad_{key}.json"
        p.write_text(json.dumps(bad))
        with pytest.raises(CapabilityRegistryError, match=f"{key} must be false"):
            load_runner_capabilities(p)


def test_authorized_runners_raises_on_mutated_state():
    from dopemux.dcp.runner_capability_registry import RunnerCapability, RunnerCapabilityRegistry

    reg = RunnerCapabilityRegistry(
        schema_version="1.0.0",
        global_invocation_authorized=True,
        global_mutation_authorized=False,
        global_paid_inference_authorized=False,
        runners=(),
        source_path="",
    )
    with pytest.raises(CapabilityRegistryError, match="global_invocation_authorized must be false"):
        reg.authorized_runners()

    bad_runner = RunnerCapability(
        runner_id="rogue",
        installed=True,
        resolved_path=None,
        version_text=None,
        invocation_authorized=True,
        mutation_authorized=False,
        paid_inference_authorized=False,
        notes="",
    )
    reg2 = RunnerCapabilityRegistry(
        schema_version="1.0.0",
        global_invocation_authorized=False,
        global_mutation_authorized=False,
        global_paid_inference_authorized=False,
        runners=(bad_runner,),
        source_path="",
    )
    with pytest.raises(CapabilityRegistryError, match="runners with invocation_authorized true forbidden"):
        reg2.authorized_runners()


def test_contract_still_blocks_execution():
    plan = build_blocked_plan("claude", ["claude", "--version"])
    result = execute_runner_plan(plan)
    assert result.status is RunnerPlanStatus.NOT_RUN
