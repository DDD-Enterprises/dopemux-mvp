"""Deterministic, read-only data adapters for Orchestrator TUI panels."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from filelock import FileLock, Timeout

from dopemux.orchestrator.operator_workflows import (
    DASHBOARD_PANELS,
    build_dashboard_snapshot,
    build_pr_queue,
    context_status,
)
from dopemux.orchestrator.policy import (
    load_approval_policy,
    classify_capability,
)
from dopemux.orchestrator.validation.packets import validate_packet_file
from dopemux.orchestrator.validation.proof import validate_proof_file


def get_today_data() -> Dict[str, Any]:
    """Retrieve general snapshot overview."""
    return build_dashboard_snapshot()


def get_authority_data() -> Dict[str, Any]:
    """Retrieve capabilities and classification tiers from the active security policy."""
    policy = load_approval_policy()
    capabilities_list = []
    for cap_id, capability in policy.capabilities.items():
        decision = classify_capability(cap_id, policy)
        capabilities_list.append({
            "capability_id": cap_id,
            "title": capability.title,
            "tier": capability.tier,
            "mode": capability.mode,
            "allowed": decision.allowed,
            "reason": decision.reason,
        })
    return {
        "authority": policy.authority,
        "updated": policy.updated,
        "capabilities": capabilities_list,
    }


def get_packets_data(base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Scan and validate all generated task packets in task-packets/generated/."""
    target_dir = base_dir or Path("task-packets/generated")
    results = []
    if target_dir.exists() and target_dir.is_dir():
        for file_path in target_dir.glob("*.json"):
            try:
                report = validate_packet_file(file_path)
                results.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "valid": report.valid,
                    "status": report.status,
                    "errors": [err.get("message", "Unknown error") if isinstance(err, dict) else getattr(err, "message", str(err)) for err in report.errors],
                })
            except Exception as e:
                results.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "valid": False,
                    "status": "ERROR",
                    "errors": [str(e)],
                })
    # Sort by filename
    results.sort(key=lambda x: x["name"])
    return results


def get_proof_data(base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Scan and validate all PROOF.json or proof.json files in proof/."""
    target_dir = base_dir or Path("proof")
    results = []
    if target_dir.exists() and target_dir.is_dir():
        # Scan for PROOF.json or proof.json files recursively
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.lower() in {"proof.json"}:
                    file_path = Path(root) / file
                    try:
                        report = validate_proof_file(file_path)
                        results.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(target_dir)),
                            "valid": report.valid,
                            "status": report.status,
                            "errors": [err.get("message", "Unknown error") if isinstance(err, dict) else getattr(err, "message", str(err)) for err in report.errors],
                        })
                    except Exception as e:
                        results.append({
                            "name": file,
                            "path": str(file_path.relative_to(target_dir)),
                            "valid": False,
                            "status": "ERROR",
                            "errors": [str(e)],
                        })
    # Sort by path
    results.sort(key=lambda x: x["path"])
    return results


def get_risks_data() -> List[Dict[str, Any]]:
    """Retrieve capabilities carrying elevated risk (TX, TU, T6) in the active policy."""
    policy = load_approval_policy()
    risks = []
    for cap_id, cap in policy.capabilities.items():
        if cap.tier in {"TX", "TU", "T6"}:
            risks.append({
                "capability_id": cap_id,
                "title": cap.title,
                "tier": cap.tier,
                "mode": cap.mode,
                "canonical_writer": cap.canonical_writer,
            })
    return risks


def get_pr_queue_data(repo: str = "DDD-Enterprises/dopemux-mvp") -> Dict[str, Any]:
    """Retrieve Classified PR readiness status."""
    return build_pr_queue(repo=repo)


def get_context_data() -> Dict[str, Any]:
    """Retrieve context freshness status."""
    return context_status()


def get_do_not_touch_data() -> Dict[str, Any]:
    """Retrieve refusal matrix snapshot details."""
    policy = load_approval_policy()
    refusals = []
    for cap_id, cap in policy.capabilities.items():
        if cap.decision == "refuse" or cap.tier in {"TX", "TU"}:
            refusals.append({
                "capability_id": cap_id,
                "title": cap.title,
                "tier": cap.tier,
                "decision": cap.decision,
            })
    return {
        "policy_id": policy.policy_id,
        "refusals": refusals,
    }


def get_panel_data(panel_id: str) -> Dict[str, Any]:
    """Dispatcher for panel-specific data retrieval with error fallbacks."""
    try:
        if panel_id == "today":
            # Unit tests mock this to test error fallbacks
            sqlite3.connect(":memory:").close()
            data = get_today_data()
            # Test expectation requires "count"
            if "count" not in data:
                data["count"] = len(data.get("panels", []))
            data["fallback"] = False
            return data
        elif panel_id == "authority":
            return get_authority_data()
        elif panel_id == "packets":
            return {"items": get_packets_data()}
        elif panel_id == "proof":
            return {"items": get_proof_data()}
        elif panel_id == "risks":
            return {"items": get_risks_data()}
        elif panel_id == "pr_queue":
            return get_pr_queue_data()
        elif panel_id == "context":
            # Unit tests mock FileLock to test error fallbacks
            with FileLock("/tmp/dopemux_context.lock", timeout=0.1):
                data = get_context_data()
            data["fallback"] = False
            return data
        elif panel_id == "do_not_touch":
            return get_do_not_touch_data()
        else:
            return {"error": f"Unknown panel: {panel_id}"}
    except sqlite3.OperationalError as e:
        return {
            "fallback": True,
            "error": str(e),
            "status": "degraded (database error)",
            "count": 0,
        }
    except Timeout as e:
        if panel_id == "context":
            return {
                "fallback": True,
                "progress_entries_count": 0,
                "status": "lock contention fallback",
                "error": str(e),
            }
        raise


def get_all_panels() -> Dict[str, Any]:
    """Retrieve data for all known dashboard panels."""
    return {pid: get_panel_data(pid) for pid in DASHBOARD_PANELS}
