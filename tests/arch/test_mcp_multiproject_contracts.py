from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
R2_TOPOLOGY_SHA256 = "df8636983e23c273eeb8eb517ea4019653b4c6bcb50cae344cde2e847214d4c2"
R2_FALSIFICATION_SHA256 = "84b6e68f929e5b3f3ad37e9c2843755cc38a3a119fc87b5af057505d8ed83bcb"

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def test_ratified_r2_references_are_byte_exact():
    topology = REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json"
    falsification = REPO_ROOT / "docs/03-reference/mcp/multiproject-falsification-contract.md"
    assert _sha256(topology) == R2_TOPOLOGY_SHA256
    assert _sha256(falsification) == R2_FALSIFICATION_SHA256

def test_service_topology_has_exact_contract_shape():
    topology = json.loads(
        (REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json").read_text()
    )
    assert len(topology["services"]) == 26
    assert set(topology["sharing_classes"]) == {
        "HOST_SINGLETON",
        "PROJECT_SCOPED",
        "WORKTREE_SCOPED",
        "RETIRED",
    }
