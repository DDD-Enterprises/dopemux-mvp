"""Phase applicability determination for universal repo-truth-extractor.

Uses detected features + archetype classification to determine which
extraction phases should be included, skipped, or conditionally run.

Output: PHASE_PLAN.json
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .fingerprint import deterministic_generated_at

PHASE_PLAN_FILENAME = "PHASE_PLAN.json"


# Phase metadata: description, universality, skip conditions
PHASE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "A": {
        "label": "Repo Control Plane",
        "description": "Repository-level control surfaces (compose, configs, CI, MCP)",
        "universality": "universal",
        "required_features": [],  # always included
    },
    "H": {
        "label": "Home Control Plane",
        "description": "User-home control surfaces (~/.dopemux, ~/.config)",
        "universality": "dopemux_only",
        "required_features": ["dopemux_home_control"],
    },
    "D": {
        "label": "Docs Pipeline",
        "description": "Documentation inventory and partitioning",
        "universality": "universal",
        "required_features": [],
    },
    "C": {
        "label": "Code Surfaces",
        "description": "Runtime code surfaces, service graph, APIs, dependencies",
        "universality": "universal",
        "required_features": [],
    },
    "E": {
        "label": "Environment & Deployment",
        "description": "Environment config, CI/CD, deployment, infrastructure",
        "universality": "universal",
        "required_features": [],
    },
    "W": {
        "label": "Workflows & Automation",
        "description": "Workflow definitions, automation scripts, hooks",
        "universality": "conditional",
        "required_features": [],
        "suggested_features": ["ci_github_actions", "ci_gitlab", "ci_jenkins"],
    },
    "B": {
        "label": "Boundaries & Plugins",
        "description": "Plugin systems, extension points, boundaries",
        "universality": "conditional",
        "required_features": [],
        "suggested_features": ["plugin_system"],
    },
    "G": {
        "label": "Governance & Quality",
        "description": "Code quality, linting, testing strategy, coverage",
        "universality": "universal",
        "required_features": [],
    },
    "Q": {
        "label": "QA & Validation",
        "description": "Quality assurance, cross-phase validation, coverage gaps",
        "universality": "universal",
        "required_features": [],
    },
    "R": {
        "label": "Arbitration & Truth",
        "description": "Evidence-linked truth maps, conflict resolution",
        "universality": "universal",
        "required_features": [],
    },
    "X": {
        "label": "Feature Index",
        "description": "Developer-queryable feature catalog",
        "universality": "universal",
        "required_features": [],
    },
    "T": {
        "label": "Task Packets",
        "description": "Implementation-ready task packet generation",
        "universality": "dopemux_only",
        "required_features": ["dopemux_task_packets"],
    },
    "Z": {
        "label": "Final Summary",
        "description": "Run summary, cost report, final audit",
        "universality": "universal",
        "required_features": [],
    },
    "S": {
        "label": "Synthesis & Documentation",
        "description": "Architecture diagrams, dependency analysis, API reference, docs generation",
        "universality": "universal",
        "required_features": [],
    },
    "M": {
        "label": "ML Risk Assessment",
        "description": "Machine learning risk assessment and sprint planning",
        "universality": "conditional",
        "required_features": [],
        "suggested_features": ["dopemux_core"],
    },
}


# Step-level applicability rules for conditional steps within universal phases.
# Format: step_id → list of feature_ids (include step if ANY feature is detected)
STEP_FEATURE_GATES: Dict[str, List[str]] = {
    # Phase A conditional steps
    "A2": ["docker_compose"],
    "A3": ["docker_compose"],
    "A4": ["mcp_tools"],
    "A5": ["mcp_tools"],
    "A7": ["llm_integration"],
    "A8": ["llm_integration"],
    "A9": ["llm_integration"],
    "A10": ["ci_github_actions", "ci_gitlab", "ci_jenkins"],
    "A11": ["ci_github_actions", "ci_gitlab", "ci_jenkins"],
    "A12": ["ci_github_actions", "ci_gitlab", "ci_jenkins"],
    "A13": ["event_bus"],
    # Phase C conditional steps
    "C2": ["event_bus"],
    "C3": ["dopemux_core"],   # Dope-Memory → generalized as "State/Memory Store"
    "C4": ["dopemux_core"],   # Trinity boundaries
    "C5": ["dopemux_core", "task_management"],  # TaskX → generalized
    "C10": ["mcp_tools"],
    "C11": ["task_management", "dopemux_core"],  # Leantime → generalized
    "C12": ["agent_orchestration"],
    "C13": ["dopemux_core"],  # ADHD Engine
    "C15": ["http_api_python", "http_api_node", "http_api_go", "grpc_api", "graphql_api"],
    "C17": ["dopemux_core"],  # Cognitive features
    # Phase B conditional steps
    "B0": ["plugin_system"],
    "B1": ["plugin_system"],
    "B2": ["plugin_system"],
    "B3": ["plugin_system"],
    # Phase W conditional steps
    "W0": ["monitoring"],
    # Phase E conditional steps
    "E3": ["dockerfile", "kubernetes"],
    "E4": ["terraform", "kubernetes"],
}


def determine_phase_plan(
    *,
    run_id: str,
    auto_features: Dict[str, Any],
    archetypes_payload: Optional[Dict[str, Any]] = None,
    force_include: Optional[List[str]] = None,
    force_skip: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Determine which phases and steps to include/skip for this repo.

    Args:
        run_id: Unique run identifier.
        auto_features: Output of feature_detector.detect_features().
        archetypes_payload: Output of archetype_classify.classify_archetypes().
        force_include: Phases to force-include regardless of detection.
        force_skip: Phases to force-skip regardless of detection.

    Returns:
        PHASE_PLAN.json payload.
    """
    force_include_set = set(force_include or [])
    force_skip_set = set(force_skip or [])

    detected_ids = set(auto_features.get("feature_ids", []))
    is_dopemux = auto_features.get("is_dopemux_repo", False)

    phases: List[Dict[str, Any]] = []

    for phase_code, meta in PHASE_REGISTRY.items():
        universality = meta["universality"]
        required = meta.get("required_features", [])
        suggested = meta.get("suggested_features", [])

        # Determine inclusion
        if phase_code in force_skip_set:
            status = "skip"
            reason = "force_skip"
        elif phase_code in force_include_set:
            status = "include"
            reason = "force_include"
        elif universality == "universal":
            status = "include"
            reason = "universal_phase"
        elif universality == "dopemux_only":
            if is_dopemux or any(f in detected_ids for f in required):
                status = "include"
                reason = f"dopemux_feature_detected: {', '.join(f for f in required if f in detected_ids)}"
            else:
                status = "skip"
                reason = "dopemux_only_phase_not_detected"
        elif universality == "conditional":
            matching = [f for f in (required + suggested) if f in detected_ids]
            if matching:
                status = "include"
                reason = f"feature_detected: {', '.join(matching)}"
            else:
                status = "conditional"
                reason = "no_features_detected_but_may_apply"
        else:
            status = "include"
            reason = "default"

        # Determine step-level gates within this phase
        step_gates: Dict[str, Dict[str, Any]] = {}
        for step_id, gate_features in STEP_FEATURE_GATES.items():
            if not step_id.startswith(phase_code):
                continue
            matching_gates = [f for f in gate_features if f in detected_ids]
            if matching_gates:
                step_gates[step_id] = {
                    "status": "include",
                    "reason": f"feature_detected: {', '.join(matching_gates)}",
                }
            else:
                step_gates[step_id] = {
                    "status": "skip",
                    "reason": f"no_matching_features (needs: {', '.join(gate_features)})",
                }

        phases.append({
            "phase": phase_code,
            "label": meta["label"],
            "status": status,
            "reason": reason,
            "universality": universality,
            "step_gates": step_gates if step_gates else None,
        })

    # Summary counts
    include_count = sum(1 for p in phases if p["status"] == "include")
    skip_count = sum(1 for p in phases if p["status"] == "skip")
    conditional_count = sum(1 for p in phases if p["status"] == "conditional")

    payload = {
        "version": "PHASE_PLAN_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "is_dopemux_repo": is_dopemux,
        "summary": {
            "total_phases": len(phases),
            "include": include_count,
            "skip": skip_count,
            "conditional": conditional_count,
        },
        "phases": phases,
    }

    return payload
