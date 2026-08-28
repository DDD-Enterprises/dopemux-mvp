"""Tests for DMX-DCP-MODEL-ROUTING-MVP-0007A trusted adapter registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.dcp.input_adapters import active_trusted_adapters, is_execution_eligible
from dopemux.dcp.trusted_adapter_registry import (
    RegistryError,
    assert_no_mutation_adapters,
    listed_adapter_ids,
    load_registry,
)
from dopemux.dcp.routing_classifier import RoutingClassificationInput


def test_default_registry_loads_and_disables_mutation():
    reg = load_registry()
    assert reg.mutation_adapters_enabled is False
    assert reg.active_mutation_adapter_ids() == []
    assert listed_adapter_ids(reg)
    assert_no_mutation_adapters(reg)
    assert active_trusted_adapters() == []
    assert is_execution_eligible(RoutingClassificationInput()) is False


def test_registry_rejects_enabled_mutation(tmp_path: Path):
    bad = {
        "schema_version": "1.0.0",
        "mutation_adapters_enabled": False,
        "adapters": [
            {
                "adapter_id": "evil",
                "enabled_for_mutation": True,
                "derives_only": True,
                "notes": "should fail",
            }
        ],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(RegistryError):
        load_registry(p)


def test_registry_rejects_global_mutation_flag(tmp_path: Path):
    bad = {
        "schema_version": "1.0.0",
        "mutation_adapters_enabled": True,
        "adapters": [],
    }
    p = tmp_path / "bad2.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(RegistryError):
        load_registry(p)
