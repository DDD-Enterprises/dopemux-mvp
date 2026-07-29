"""Tests for DMX-DCP-MODEL-ROUTING-MVP-0009 runner capability registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.dcp.runner_capability_registry import (
    CapabilityRegistryError,
    assert_no_invocation_authorized,
    load_runner_capabilities,
)
from dopemux.dcp.runner_contract import build_blocked_plan, execute_runner_plan, RunnerPlanStatus


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


def test_contract_still_blocks_execution():
    plan = build_blocked_plan("claude", ["claude", "--version"])
    result = execute_runner_plan(plan)
    assert result.status is RunnerPlanStatus.NOT_RUN
