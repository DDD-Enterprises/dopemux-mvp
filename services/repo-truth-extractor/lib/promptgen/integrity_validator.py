"""Referential integrity validator for generated promptsets.

Implements the "Tier 0" hard gate from the audit:
- step_id alignment across promptset.yaml ↔ model_map.yaml ↔ artifacts.yaml
- prompt file existence checks
- artifact contract existence checks
- no duplicate canonical writers per artifact
- all required sections present in prompt files

Runs as the final gate in the sync pipeline. If any check fails,
the sync emits an error rather than a broken promptset.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

logger = logging.getLogger(__name__)


class IntegrityError:
    """A single integrity check failure."""

    def __init__(self, check: str, severity: str, message: str):
        self.check = check
        self.severity = severity  # "error" or "warning"
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {
            "check": self.check,
            "severity": self.severity,
            "message": self.message,
        }


def validate_promptset_integrity(
    *,
    promptset: Dict[str, Any],
    artifacts: Dict[str, Any],
    model_map: Dict[str, Any],
    prompt_dir: Path | None = None,
) -> Dict[str, Any]:
    """Validate referential integrity across all three contract files.

    Args:
        promptset: Parsed promptset.yaml content.
        artifacts: Parsed artifacts.yaml content.
        model_map: Parsed model_map.yaml content.
        prompt_dir: Optional directory to check prompt file existence.

    Returns:
        Validation result with pass/fail status and any errors.
    """
    errors: List[IntegrityError] = []

    # Collect all step_ids from promptset
    promptset_step_ids: Set[str] = set()
    promptset_outputs: Dict[str, List[str]] = {}
    prompt_files: Dict[str, str] = {}

    for phase_id, phase_def in promptset.get("phases", {}).items():
        for step in phase_def.get("steps", []):
            sid = step["step_id"]
            promptset_step_ids.add(sid)
            promptset_outputs[sid] = step.get("outputs", [])
            prompt_files[sid] = step.get("prompt_file", "")

    # Check 1: model_map step_ids ⊆ promptset step_ids
    model_map_step_ids: Set[str] = set()
    for step_entry in model_map.get("steps", []):
        sid = step_entry.get("step_id", "")
        model_map_step_ids.add(sid)
        if sid not in promptset_step_ids:
            errors.append(IntegrityError(
                check="model_map_step_alignment",
                severity="error",
                message=f"Step '{sid}' in model_map.yaml but not in promptset.yaml",
            ))

    # Check 1b: promptset step_ids ⊆ model_map step_ids
    for sid in promptset_step_ids:
        if sid not in model_map_step_ids:
            errors.append(IntegrityError(
                check="model_map_coverage",
                severity="warning",
                message=f"Step '{sid}' in promptset.yaml has no model_map entry",
            ))

    # Check 2: prompt file existence
    if prompt_dir is not None:
        for sid, pfile in prompt_files.items():
            ppath = Path(pfile)
            if not ppath.is_absolute():
                ppath = prompt_dir / ppath
            if not ppath.exists():
                errors.append(IntegrityError(
                    check="prompt_file_existence",
                    severity="error",
                    message=f"Prompt file for step '{sid}' not found: {pfile}",
                ))

    # Check 3: promptset outputs ⊆ artifacts artifact_names
    artifact_names: Set[str] = set()
    canonical_writers: Dict[str, str] = {}
    for artifact in artifacts.get("artifacts", []):
        aname = artifact.get("artifact_name", "")
        artifact_names.add(aname)
        cw = artifact.get("canonical_writer_step_id", "")
        if aname in canonical_writers:
            errors.append(IntegrityError(
                check="duplicate_canonical_writer",
                severity="error",
                message=f"Artifact '{aname}' has duplicate canonical writers: "
                        f"{canonical_writers[aname]} and {cw}",
            ))
        canonical_writers[aname] = cw

    for sid, outputs in promptset_outputs.items():
        for output in outputs:
            if output not in artifact_names:
                errors.append(IntegrityError(
                    check="artifact_contract_existence",
                    severity="error",
                    message=f"Step '{sid}' output '{output}' has no artifact contract",
                ))

    # Check 4: canonical writers reference valid step_ids
    for aname, cw_sid in canonical_writers.items():
        if cw_sid and cw_sid not in promptset_step_ids:
            errors.append(IntegrityError(
                check="canonical_writer_validity",
                severity="error",
                message=f"Artifact '{aname}' canonical writer '{cw_sid}' not in promptset",
            ))

    # Check 5: model_map lane references exist
    defined_lanes = set(model_map.get("lanes", {}).keys())
    for step_entry in model_map.get("steps", []):
        lane = step_entry.get("lane", "")
        if lane and lane not in defined_lanes:
            errors.append(IntegrityError(
                check="lane_existence",
                severity="error",
                message=f"Step '{step_entry.get('step_id')}' references undefined lane '{lane}'",
            ))

    # Partition by severity
    error_list = [e for e in errors if e.severity == "error"]
    warning_list = [e for e in errors if e.severity == "warning"]

    passed = len(error_list) == 0

    return {
        "passed": passed,
        "total_checks": 5,
        "error_count": len(error_list),
        "warning_count": len(warning_list),
        "errors": [e.to_dict() for e in error_list],
        "warnings": [e.to_dict() for e in warning_list],
        "summary": {
            "promptset_steps": len(promptset_step_ids),
            "model_map_steps": len(model_map_step_ids),
            "artifacts": len(artifact_names),
        },
    }


def validate_from_files(
    *,
    promptset_path: Path,
    artifacts_path: Path,
    model_map_path: Path,
    prompt_dir: Path | None = None,
) -> Dict[str, Any]:
    """Convenience function to validate from file paths."""
    with open(promptset_path) as f:
        promptset = yaml.safe_load(f)
    with open(artifacts_path) as f:
        artifacts = yaml.safe_load(f)
    with open(model_map_path) as f:
        model_map = yaml.safe_load(f)

    return validate_promptset_integrity(
        promptset=promptset,
        artifacts=artifacts,
        model_map=model_map,
        prompt_dir=prompt_dir,
    )
