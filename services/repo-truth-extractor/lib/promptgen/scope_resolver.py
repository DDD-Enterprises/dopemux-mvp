"""Scope resolver for universal repo-truth-extractor.

Takes detected features + profile targets and produces per-step
input scope lists (file globs and directory roots to scan).

This replaces the hardcoded targets_by_phase in profiles with
dynamically resolved scopes based on actual repo structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from .fingerprint import deterministic_generated_at

SCOPE_RESOLUTION_FILENAME = "SCOPE_RESOLUTION.json"


# Default scan scopes per step when no feature provides a specific scope.
# These are generic patterns that work for most repos.
DEFAULT_STEP_SCOPES: Dict[str, List[str]] = {
    # Phase A: Repo Control Plane
    "A0": [".", "config/", "compose.yml", "docker-compose*.yml", ".github/"],
    "A1": ["."],
    "A6": ["scripts/", "tools/", "Makefile"],
    "A99": ["."],
    # Phase D: Documentation
    "D0": ["docs/", "README.md", "*.md"],
    "D1": ["docs/"],
    "D2": ["docs/"],
    "D3": ["docs/"],
    "D4": ["docs/"],
    "D5": ["docs/"],
    # Phase C: Code Surfaces
    "C0": ["src/", "lib/", "pkg/", "app/", "services/"],
    "C1": ["src/", "services/", "apps/"],
    "C6": ["src/", "services/"],
    "C7": ["src/", "services/"],
    "C8": ["src/", "bin/"],
    "C9": ["src/", "bin/"],
    "C14": ["src/", "lib/"],
    "C16": ["src/", "services/", "lib/", "pkg/"],
    # Phase E: Environment
    "E0": [".env*", "config/", "*.toml", "*.yaml"],
    "E1": ["."],
    "E2": ["."],
    "E6": ["tests/", "test/"],
    "E9": ["."],
    # Phase G: Governance
    "G0": ["."],
    "G1": [".github/", ".gitlab-ci.yml", "Jenkinsfile"],
    "G2": ["."],
    "G3": ["."],
    "G4": ["."],
    "G9": ["."],
    # Phase Q: QA (reads upstream artifacts, not repo)
    "Q0": [],
    "Q1": [],
    "Q2": [],
    "Q3": [],
    "Q9": [],
    # Phase R: Arbitration (reads upstream artifacts)
    "R0": [],
    "R2": [],
    "R3": [],
    "R5": [],
    "R6": [],
    "R7": [],
    "R8": [],
    # Phase X: Feature Index (reads upstream artifacts)
    "X0": [],
    "X1": [],
    "X2": [],
    "X3": [],
    "X4": [],
    "X9": [],
    # Phase Z: Summary (reads upstream artifacts)
    "Z0": [],
    "Z1": [],
    "Z2": [],
    "Z9": [],
    # Phase S: Synthesis (reads upstream artifacts, NOT repo)
    "S0": [],
    "S1": [],
    "S2": [],
    "S3": [],
    "S4": [],
    "S5": [],
    "S8": [],
    "S9": [],
    "S10": [],
    "S11": [],
}

# Feature → step scope overrides.
# When a feature is detected, these scopes replace the defaults for specific steps.
FEATURE_SCOPE_OVERRIDES: Dict[str, Dict[str, List[str]]] = {
    "http_api_python": {
        "C1": ["src/", "services/", "app/"],
        "C14": ["src/", "lib/"],
        "C15": ["src/", "services/", "app/"],
    },
    "http_api_node": {
        "C1": ["src/", "services/", "apps/", "packages/"],
        "C15": ["src/", "services/", "apps/"],
    },
    "http_api_go": {
        "C1": ["cmd/", "internal/", "pkg/", "api/"],
        "C15": ["cmd/", "internal/", "api/"],
    },
    "grpc_api": {
        "C15": ["proto/", "api/", "services/"],
    },
    "event_bus": {
        "C2": ["src/", "services/", "pkg/", "internal/"],
        "A13": ["src/", "services/"],
    },
    "mcp_tools": {
        "A4": [".claude.json", "mcp-proxy-config*", "config/mcp/"],
        "A5": [".claude.json", "config/mcp/"],
        "C10": ["services/", "src/", "docker/mcp-servers/"],
    },
    "docker_compose": {
        "A2": ["compose.yml", "docker-compose*.yml", "compose/"],
        "A3": ["compose.yml", "docker-compose*.yml"],
    },
    "ci_github_actions": {
        "G1": [".github/workflows/"],
        "E0": [".github/", ".env*"],
    },
    "ci_gitlab": {
        "G1": [".gitlab-ci.yml"],
    },
    "docs_structured": {
        "D0": ["docs/"],
        "D1": ["docs/"],
    },
    "python_packaging": {
        "C14": ["src/", "lib/"],
        "C16": ["src/", "lib/", "services/"],
    },
    "plugin_system": {
        "B0": ["plugins/", "extensions/"],
        "B1": ["plugins/", "extensions/"],
    },
    "kubernetes": {
        "E3": ["k8s/", "helm/", "charts/", "deploy/"],
        "E4": ["k8s/", "helm/", "deploy/"],
    },
    "terraform": {
        "E3": ["terraform/", "infra/", "infrastructure/"],
        "E4": ["terraform/", "infra/"],
    },
    "agent_orchestration": {
        "C12": ["src/", "services/", "agents/"],
    },
}


def resolve_scopes(
    *,
    run_id: str,
    auto_features: Dict[str, Any],
    phase_plan: Dict[str, Any],
    scope_overrides: Optional[Dict[str, List[str]]] = None,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Resolve per-step input scopes based on features and phase plan.

    Args:
        run_id: Unique run identifier.
        auto_features: Output of feature_detector.detect_features().
        phase_plan: Output of phase_applicability.determine_phase_plan().
        scope_overrides: Manual overrides from interactive discovery (step_id → paths).
        profile: Selected profile with phase_policy.targets_by_phase.

    Returns:
        SCOPE_RESOLUTION.json payload with per-step scope lists.
    """
    scope_overrides = scope_overrides or {}
    detected_ids = set(auto_features.get("feature_ids", []))

    # Build feature → scan_roots index from auto_features
    feature_roots: Dict[str, List[str]] = {}
    for feat in auto_features.get("detected_features", []):
        fid = feat.get("feature_id", "")
        feature_roots[fid] = feat.get("scan_roots", [])

    # Determine included phases
    included_phases: Set[str] = set()
    skipped_steps: Set[str] = set()
    for phase_entry in phase_plan.get("phases", []):
        phase_code = phase_entry.get("phase", "")
        if phase_entry.get("status") == "skip":
            continue
        included_phases.add(phase_code)
        # Check step-level gates
        step_gates = phase_entry.get("step_gates") or {}
        for step_id, gate_info in step_gates.items():
            if gate_info.get("status") == "skip":
                skipped_steps.add(step_id)

    # Resolve scopes
    step_scopes: Dict[str, Dict[str, Any]] = {}

    for step_id, default_scopes in DEFAULT_STEP_SCOPES.items():
        phase_code = step_id[0]

        # Skip if phase is excluded
        if phase_code not in included_phases:
            continue

        # Skip if step is gated out
        if step_id in skipped_steps:
            continue

        # Start with defaults
        resolved = list(default_scopes)
        resolution_source = "default"

        # Apply feature-based overrides
        for feat_id in detected_ids:
            overrides = FEATURE_SCOPE_OVERRIDES.get(feat_id, {})
            if step_id in overrides:
                resolved = list(overrides[step_id])
                resolution_source = f"feature:{feat_id}"
                break

        # Enrich with feature scan roots where applicable
        for feat in auto_features.get("detected_features", []):
            if step_id in feat.get("maps_to_steps", []):
                feat_roots = feat.get("scan_roots", [])
                for fr in feat_roots:
                    if fr not in resolved:
                        resolved.append(fr)
                if feat_roots:
                    resolution_source = f"feature_roots:{feat['feature_id']}"

        # Apply manual overrides (highest priority)
        if step_id in scope_overrides:
            resolved = list(scope_overrides[step_id])
            resolution_source = "manual_override"

        step_scopes[step_id] = {
            "scopes": resolved,
            "source": resolution_source,
            "phase": phase_code,
        }

    # Add profile budget hints if available
    budgets: Dict[str, Dict[str, Any]] = {}
    if profile:
        phase_policy = profile.get("phase_policy", {})
        budgets_by_phase = phase_policy.get("budgets_by_phase", {})
        for phase_code, budget in budgets_by_phase.items():
            if phase_code in included_phases:
                budgets[phase_code] = budget

    payload = {
        "version": "SCOPE_RESOLUTION_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "included_phases": sorted(included_phases),
        "total_steps_resolved": len(step_scopes),
        "skipped_steps": sorted(skipped_steps),
        "step_scopes": dict(sorted(step_scopes.items())),
        "phase_budgets": budgets if budgets else None,
    }

    return payload
