# src/dopemux/orchestrator/perpacket.py
"""Per-packet test isolation and validation logic for Task Orchestrator."""

from __future__ import annotations
import json
import subprocess
import yaml
from pathlib import Path
from typing import Any, Dict, List

from dopemux.orchestrator.validation.packets import validate_packet_file
from dopemux.orchestrator.validation.proof import validate_proof_file

DEFAULT_MAP_PATH = Path("config/orchestrator/perpacket_test_map.yaml")


def load_test_map(map_path: Path = DEFAULT_MAP_PATH) -> Dict[str, Any]:
    """Load and parse the declarative per-packet test mapping."""
    if not map_path.exists():
        raise FileNotFoundError(f"Per-packet test map missing: {map_path}")
    with open(map_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_perpacket_validation(
    packet_id: str,
    *,
    map_path: Path = DEFAULT_MAP_PATH,
) -> Dict[str, Any]:
    """Execute isolated validation steps for the specified packet."""
    test_map = load_test_map(map_path)
    if packet_id not in test_map:
        raise ValueError(f"Packet ID {packet_id} not found in the test map ({map_path})")

    entry = test_map[packet_id]
    validations = []
    all_pass = True

    # 1. Run pytest paths
    tests = entry.get("tests") or []
    for test_path in tests:
        # Resolve from repository root to be safe
        cmd = ["pytest", "-q", test_path]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            exit_code = res.returncode
        except Exception:
            exit_code = 1
        
        status = "PASS" if exit_code == 0 else "FAIL"
        if exit_code != 0:
            all_pass = False
        
        validations.append({
            "name": f"pytest: {test_path}",
            "exit_code": exit_code,
            "status": status,
        })

    # 2. Validate Packet JSON schema
    packet_spec_path = entry.get("packet")
    if packet_spec_path:
        report = validate_packet_file(packet_spec_path)
        status = "PASS" if report.valid else "FAIL"
        if not report.valid:
            all_pass = False
        
        validations.append({
            "name": f"packet-validation: {packet_spec_path}",
            "exit_code": report.exit_code,
            "status": status,
        })

    # 3. Validate Proof JSON schema (if it exists)
    proof_path = entry.get("proof")
    if proof_path:
        proof_file = Path(proof_path)
        if proof_file.exists():
            report = validate_proof_file(proof_file)
            status = "PASS" if report.valid else "FAIL"
            if not report.valid:
                all_pass = False
            
            validations.append({
                "name": f"proof-validation: {proof_path}",
                "exit_code": report.exit_code,
                "status": status,
            })
        else:
            # Not yet created/valid in current checkout phase
            validations.append({
                "name": f"proof-validation: {proof_path}",
                "exit_code": 1,
                "status": "NOT_RUN",
            })

    # 4. Extra verify commands
    verify_cmds = entry.get("verify_commands") or []
    for verify_cmd in verify_cmds:
        try:
            res = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True, check=False)
            exit_code = res.returncode
        except Exception:
            exit_code = 1
        
        status = "PASS" if exit_code == 0 else "FAIL"
        if exit_code != 0:
            all_pass = False
        
        validations.append({
            "name": f"verify: {verify_cmd}",
            "exit_code": exit_code,
            "status": status,
        })

    return {
        "packet_id": packet_id,
        "valid": all_pass,
        "validations": validations,
    }
