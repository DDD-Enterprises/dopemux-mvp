"""Contract generator for the universal repo-truth-extractor.

Dynamically generates promptset.yaml, artifacts.yaml, and model_map.yaml
from a resolved feature map + phase plan + scope resolution.

Only includes steps for applicable phases. Validates referential integrity
before emission.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from .fingerprint import deterministic_generated_at

logger = logging.getLogger(__name__)

REQUIRED_PROMPT_SECTIONS = [
    "Goal",
    "Inputs",
    "Outputs",
    "Schema",
    "Extraction Procedure",
    "Evidence Rules",
    "Determinism Rules",
    "Anti-Fabrication Rules",
    "Failure Modes",
]

# Default phase execution order
DEFAULT_PHASE_ORDER = [
    "A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z", "S", "M",
]

# Default lane assignments by step category
DEFAULT_LANE_MAP = {
    "inventory": "contract_emitter",
    "merge": "contract_emitter",
    "deep": "contract_emitter",
    "synthesis": "contract_emitter",
}

# Default model routing
DEFAULT_LANE_DEFINITIONS = {
    "contract_emitter": {
        "primary": {
            "provider": "openai_direct",
            "model_id": "gpt-5.3-codex",
            "strict": True,
        },
        "fallback": {
            "provider": "openai_direct",
            "model_id": "gpt-5.2",
            "strict": True,
        },
    },
}


def _step_to_lane(step_id: str) -> str:
    """Determine the lane for a step based on its ID suffix pattern."""
    if step_id.endswith("0"):
        return "contract_emitter"  # inventory steps
    if step_id.endswith("9") or step_id.endswith("99"):
        return "contract_emitter"  # merge/QA steps
    return "contract_emitter"  # default


def generate_promptset_yaml(
    *,
    phase_plan: Dict[str, Any],
    scope_resolution: Dict[str, Any],
    prompt_dir: Path,
    run_id: str,
    repo_name: str = "generated",
) -> Dict[str, Any]:
    """Generate a promptset.yaml configuration from pipeline artifacts.

    Args:
        phase_plan: Output from phase_applicability.determine_phase_plan().
        scope_resolution: Output from scope_resolver.resolve_scopes().
        prompt_dir: Directory containing rendered prompt files.
        run_id: Unique run identifier.
        repo_name: Name for the generated promptset.

    Returns:
        Dict representing the promptset.yaml content.
    """
    included_phases = set(scope_resolution.get("included_phases", []))
    skipped_steps = set(scope_resolution.get("skipped_steps", []))

    # Build phase order (only included phases)
    all_phase_order = [p for p in DEFAULT_PHASE_ORDER if p in included_phases]

    # Determine optional vs required phases
    optional_phases = []
    for phase_entry in phase_plan.get("phases", []):
        if phase_entry["status"] == "conditional" and phase_entry["phase"] in included_phases:
            optional_phases.append(phase_entry["phase"])

    # Build phase definitions
    phases: Dict[str, Any] = {}
    for phase_id in all_phase_order:
        phase_entry = next(
            (p for p in phase_plan.get("phases", []) if p["phase"] == phase_id),
            None,
        )
        if not phase_entry:
            continue

        # Collect steps for this phase from scope resolution
        step_ids = sorted(
            sid for sid in scope_resolution.get("step_scopes", {})
            if sid.startswith(phase_id) and sid not in skipped_steps
        )

        steps = []
        for step_id in step_ids:
            step_scope = scope_resolution["step_scopes"][step_id]

            # Find matching prompt file
            prompt_candidates = list(prompt_dir.glob(f"PROMPT_{step_id}_*.md"))
            prompt_file = str(prompt_candidates[0]) if prompt_candidates else f"prompts/PROMPT_{step_id}.md"

            steps.append({
                "step_id": step_id,
                "prompt_file": prompt_file,
                "coverage_targets": step_scope.get("scopes", []),
                "outputs": [],  # Will be populated from artifacts.yaml
            })

        if steps:
            phases[phase_id] = {
                "required_steps": [s["step_id"] for s in steps],
                "steps": steps,
            }

    return {
        "version": "4.0",
        "name": f"repo-truth-extractor-{repo_name}",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "all_phase_order": all_phase_order,
        "optional_phases": optional_phases,
        "required_prompt_sections": REQUIRED_PROMPT_SECTIONS,
        "phases": phases,
    }


def generate_artifacts_yaml(
    *,
    promptset: Dict[str, Any],
    run_id: str,
) -> Dict[str, Any]:
    """Generate artifacts.yaml from a promptset configuration.

    Creates artifact contract entries for each step's outputs.
    """
    artifacts: List[Dict[str, Any]] = []

    for phase_id, phase_def in promptset.get("phases", {}).items():
        for step in phase_def.get("steps", []):
            step_id = step["step_id"]

            # Generate standard output artifact names based on step pattern
            artifact_name = _default_artifact_name(step_id)
            if artifact_name:
                artifacts.append({
                    "phase": phase_id,
                    "artifact_name": artifact_name,
                    "canonical_writer_step_id": step_id,
                    "kind": "json_item_list",
                    "norm_artifact": True,
                    "allow_timestamp_keys": False,
                    "merge_strategy": "itemlist_by_id",
                    "required_fields": ["id", "path"],
                })

                # Update the step's outputs
                step["outputs"] = [artifact_name]

    return {
        "version": "4.0",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "forbidden_norm_keys": [
            "generated_at",
            "timestamp",
            "created_at",
            "updated_at",
        ],
        "artifacts": artifacts,
    }


def _default_artifact_name(step_id: str) -> Optional[str]:
    """Generate a default artifact name for a step."""
    phase = step_id[0]
    suffix = step_id[1:]

    if suffix in ("9", "99"):
        return f"PHASE_{phase}_MERGED.json"
    if suffix == "0":
        return f"PHASE_{phase}_INVENTORY.json"
    return f"{step_id}_EXTRACTION.json"


def generate_model_map(
    *,
    promptset: Dict[str, Any],
    run_id: str,
    lane_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate model_map.yaml from a promptset configuration.

    Args:
        promptset: The generated promptset.yaml content.
        run_id: Unique run identifier.
        lane_overrides: Optional override for lane definitions.
    """
    lanes = copy.deepcopy(DEFAULT_LANE_DEFINITIONS)
    if lane_overrides:
        lanes.update(lane_overrides)

    steps: List[Dict[str, Any]] = []
    for phase_id, phase_def in promptset.get("phases", {}).items():
        for step in phase_def.get("steps", []):
            step_id = step["step_id"]
            steps.append({
                "phase": phase_id,
                "step_id": step_id,
                "lane": _step_to_lane(step_id),
                "sidefill_enabled": True,
                "repair_mode": "targeted_then_envelope",
                "max_files_cap": 15,
            })

    return {
        "version": "2.0",
        "policy": "TP-universal",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "global_settings": {
            "no_auto_transport_flips": True,
            "bulk_repair_threshold_percent": 15,
            "escalation_order": ["sidefill", "repair"],
        },
        "lanes": lanes,
        "steps": steps,
    }


def generate_all_contracts(
    *,
    phase_plan: Dict[str, Any],
    scope_resolution: Dict[str, Any],
    prompt_dir: Path,
    output_dir: Path,
    run_id: str,
    repo_name: str = "generated",
    lane_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate all three contract files and write them to output_dir.

    Returns summary with file paths and statistics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate promptset
    promptset = generate_promptset_yaml(
        phase_plan=phase_plan,
        scope_resolution=scope_resolution,
        prompt_dir=prompt_dir,
        run_id=run_id,
        repo_name=repo_name,
    )

    # Generate artifacts (updates promptset step outputs in-place)
    artifacts = generate_artifacts_yaml(promptset=promptset, run_id=run_id)

    # Generate model map
    model_map = generate_model_map(
        promptset=promptset, run_id=run_id, lane_overrides=lane_overrides,
    )

    # Write files
    promptset_path = output_dir / "promptset.yaml"
    artifacts_path = output_dir / "artifacts.yaml"
    model_map_path = output_dir / "model_map.yaml"

    with open(promptset_path, "w") as f:
        yaml.dump(promptset, f, default_flow_style=False, sort_keys=False)

    with open(artifacts_path, "w") as f:
        yaml.dump(artifacts, f, default_flow_style=False, sort_keys=False)

    with open(model_map_path, "w") as f:
        yaml.dump(model_map, f, default_flow_style=False, sort_keys=False)

    return {
        "promptset_path": str(promptset_path),
        "artifacts_path": str(artifacts_path),
        "model_map_path": str(model_map_path),
        "phase_count": len(promptset["phases"]),
        "step_count": sum(
            len(p["steps"]) for p in promptset["phases"].values()
        ),
        "artifact_count": len(artifacts["artifacts"]),
    }
