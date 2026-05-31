"""Deterministic, read-only data adapters for Orchestrator TUI panels."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from filelock import FileLock, Timeout

from dopemux.orchestrator.operator_workflows import (
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

PANEL_IDS = (
    "today",
    "authority",
    "packets",
    "proof",
    "risks",
    "pr_queue",
    "context",
    "do_not_touch",
)


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
    """Compatibility adapter for legacy panel callers.

    New TUI widgets call the typed ``get_*_data`` helpers directly. Older tests
    and callers still expect a compact status/fallback shape from this function.
    """
    try:
        if panel_id == "today":
            conn = sqlite3.connect(":memory:")
            conn.close()
            data = get_today_data()
            return {
                "status": "active",
                "fallback": False,
                "count": len(data.get("panels", [])),
            }

        if panel_id == "context":
            lock_path = Path(os.getenv("TMPDIR", "/tmp")) / "dopemux-context-panel.lock"
            lock = FileLock(str(lock_path), timeout=0.05)
            with lock:
                data = get_context_data()
            return {
                "status": "active",
                "fallback": False,
                "progress_entries_count": len(data.get("sources", data)),
            }

        if panel_id == "authority":
            data = get_authority_data()
            return {
                "status": "active",
                "fallback": False,
                "rules": [data.get("authority", "")],
            }

        if panel_id == "packets":
            return {
                "status": "active",
                "fallback": False,
                "count": len(get_packets_data()),
            }

        if panel_id == "proof":
            return {
                "status": "active",
                "fallback": False,
                "count": len(get_proof_data()),
            }

        if panel_id == "risks":
            return {
                "status": "active",
                "fallback": False,
                "active_risks": len(get_risks_data()),
            }

        if panel_id == "pr_queue":
            data = get_pr_queue_data()
            return {
                "status": "active",
                "fallback": False,
                "items": data.get("items", []),
            }

        if panel_id == "do_not_touch":
            data = get_do_not_touch_data()
            return {
                "status": "active",
                "fallback": False,
                "safe": not data.get("refusals"),
            }

        return {"status": "unknown", "fallback": True, "error": f"Unknown panel: {panel_id}"}

    except Timeout:
        return {
            "status": "active (lock contention fallback)",
            "fallback": True,
            "progress_entries_count": 0,
        }
    except sqlite3.OperationalError as exc:
        return {
            "status": "degraded (concurrency error)",
            "fallback": True,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "status": "degraded (unexpected error)",
            "fallback": True,
            "error": str(exc),
        }


def get_all_panels() -> Dict[str, Dict[str, Any]]:
    """Return compact data for all legacy panel IDs."""
    return {panel_id: get_panel_data(panel_id) for panel_id in PANEL_IDS}
