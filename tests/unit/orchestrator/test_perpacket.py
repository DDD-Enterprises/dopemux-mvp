# tests/unit/orchestrator/test_perpacket.py
"""Unit tests for per-packet test isolation and validation logic."""

from __future__ import annotations
import json
from pathlib import Path
import pytest
from dopemux.orchestrator.perpacket import (
    load_test_map,
    run_perpacket_validation,
)

TEMP_MAP_CONTENT = """
TEST-PACKET-VALID:
  tests: []
  packet: "task-packets/generated/TP-DMX-ORCH-PROOF-PERPACKET-001.json"
  proof: "proof/dmx-orch-integration/TP-DMX-ORCH-PROOF-PERPACKET-001/PROOF.json"
  verify_commands: []

TEST-PACKET-INVALID:
  tests: []
  packet: "non-existent-packet-file.json"
  proof: ""
  verify_commands: []
"""


def test_load_test_map(tmp_path: Path):
    map_file = tmp_path / "perpacket_test_map.yaml"
    map_file.write_text(TEMP_MAP_CONTENT, encoding="utf-8")

    test_map = load_test_map(map_file)
    assert "TEST-PACKET-VALID" in test_map
    assert "TEST-PACKET-INVALID" in test_map
    assert test_map["TEST-PACKET-VALID"]["tests"] == []


def test_run_perpacket_validation_missing_packet():
    with pytest.raises(ValueError, match="not found in the test map"):
        run_perpacket_validation("NON-EXISTENT-PACKET-ID")


def test_run_perpacket_validation_invalid_file(tmp_path: Path):
    map_file = tmp_path / "perpacket_test_map.yaml"
    map_file.write_text(TEMP_MAP_CONTENT, encoding="utf-8")

    result = run_perpacket_validation("TEST-PACKET-INVALID", map_path=map_file)
    assert result["packet_id"] == "TEST-PACKET-INVALID"
    assert result["valid"] is False
    
    # Verify that the invalid packet file triggered a failed validation entry
    packet_val = next(v for v in result["validations"] if "packet-validation" in v["name"])
    assert packet_val["status"] == "FAIL"
    assert packet_val["exit_code"] != 0


def test_run_perpacket_validation_valid(tmp_path: Path):
    # Ensure test mapping is valid
    map_file = tmp_path / "perpacket_test_map.yaml"
    map_file.write_text(TEMP_MAP_CONTENT, encoding="utf-8")

    result = run_perpacket_validation("TEST-PACKET-VALID", map_path=map_file)
    assert result["packet_id"] == "TEST-PACKET-VALID"
    # Valid is True because packet is present and proof validation defaults to NOT_RUN
    assert result["valid"] is True
