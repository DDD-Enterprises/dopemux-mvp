"""Sync engine for the universal repo-truth-extractor.

Orchestrates the full pipeline:
  fingerprint → classify → auto-detect features → interactive discovery
  → resolve scopes → render templates → generate contracts → validate integrity

This is the canonical entrypoint for generating a working promptset
for any arbitrary codebase.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .contract_generator import generate_all_contracts
from .feature_detector import detect_features
from .fingerprint import build_stage0_artifacts, deterministic_generated_at
from .integrity_validator import validate_promptset_integrity
from .interactive_discovery import run_interactive_discovery
from .phase_applicability import determine_phase_plan
from .scope_resolver import resolve_scopes
from .template_renderer import (
    build_template_context,
    render_promptset,
    validate_rendered_prompt,
)

logger = logging.getLogger(__name__)


class SyncResult:
    """Result of a sync pipeline run."""

    def __init__(self):
        self.success: bool = False
        self.run_id: str = ""
        self.output_dir: str = ""
        self.stages_completed: List[str] = []
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
        self.artifacts: Dict[str, str] = {}
        self.summary: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "run_id": self.run_id,
            "output_dir": self.output_dir,
            "stages_completed": self.stages_completed,
            "errors": self.errors,
            "warnings": self.warnings,
            "artifacts": self.artifacts,
            "summary": self.summary,
        }


def _compute_repo_hash(repo_root: Path) -> str:
    """Compute a short hash to identify the target repo."""
    repo_name = repo_root.resolve().name
    repo_path = str(repo_root.resolve())
    h = hashlib.sha256(repo_path.encode()).hexdigest()[:12]
    return f"{repo_name}-{h}"


def run_sync(
    *,
    repo_root: Path,
    output_root: Optional[Path] = None,
    template_dir: Optional[Path] = None,
    feature_map_path: Optional[Path] = None,
    interactive: bool = False,
    enrich: bool = False,
    force_include: Optional[List[str]] = None,
    force_skip: Optional[List[str]] = None,
    run_id: Optional[str] = None,
) -> SyncResult:
    """Run the full sync pipeline.

    Args:
        repo_root: Path to the target repository.
        output_root: Root directory for generated promptsets.
            Defaults to <extractor_root>/promptsets/generated/.
        template_dir: Directory containing base prompt templates.
            Defaults to <extractor_root>/base_prompts/.
        feature_map_path: Path to a pre-authored FEATURE_MAP.json
            (skips interactive discovery).
        interactive: If True, run interactive feature discovery.
        enrich: If True, run optional LLM enrichment pass.
        force_include: Phases to force-include regardless of detection.
        force_skip: Phases to force-skip regardless of detection.
        run_id: Unique run identifier. Auto-generated if not provided.

    Returns:
        SyncResult with pipeline output details.
    """
    result = SyncResult()

    # --- Setup ---
    repo_root = Path(repo_root).resolve()
    if not repo_root.exists():
        result.errors.append({"stage": "setup", "message": f"Repo not found: {repo_root}"})
        return result

    extractor_root = Path(__file__).parent.parent.parent
    repo_hash = _compute_repo_hash(repo_root)

    if run_id is None:
        run_id = f"sync-{repo_hash}-{deterministic_generated_at('sync')}"
    result.run_id = run_id

    if output_root is None:
        output_root = extractor_root / "promptsets" / "generated" / repo_hash
    else:
        output_root = Path(output_root)

    result.output_dir = str(output_root)

    if template_dir is None:
        template_dir = extractor_root / "base_prompts"

    prompt_output_dir = output_root / "prompts"

    logger.info("Sync started: repo=%s run_id=%s output=%s", repo_root, run_id, output_root)

    try:
        # --- Stage 0h: Feature detection ---
        logger.info("Stage 0h: Feature detection")
        auto_features = detect_features(root=repo_root, run_id=run_id)
        _write_artifact(output_root, "AUTO_FEATURES.json", auto_features)
        result.stages_completed.append("feature_detection")
        result.artifacts["auto_features"] = str(output_root / "AUTO_FEATURES.json")
        logger.info(
            "Detected %d features (dopemux=%s)",
            auto_features["feature_count"],
            auto_features["is_dopemux_repo"],
        )

        # --- Stage 0g: Phase applicability ---
        logger.info("Stage 0g: Phase applicability")
        phase_plan = determine_phase_plan(
            run_id=run_id,
            auto_features=auto_features,
            force_include=force_include or [],
            force_skip=force_skip or [],
        )
        _write_artifact(output_root, "PHASE_PLAN.json", phase_plan)
        result.stages_completed.append("phase_plan")
        result.artifacts["phase_plan"] = str(output_root / "PHASE_PLAN.json")

        # --- Stage 1: Feature discovery ---
        logger.info("Stage 1: Feature discovery")
        if feature_map_path and Path(feature_map_path).exists():
            # Use pre-authored feature map
            with open(feature_map_path) as f:
                feature_map = json.load(f)
            scope_overrides_payload = {
                "version": "SCOPE_OVERRIDES_V1",
                "run_id": run_id,
                "overrides": {},
            }
        else:
            feature_map, scope_overrides_payload = run_interactive_discovery(
                auto_features=auto_features,
                phase_plan=phase_plan,
                repo_root=repo_root,
                run_id=run_id,
                non_interactive=not interactive,
            )

        _write_artifact(output_root, "FEATURE_MAP.json", feature_map)
        _write_artifact(output_root, "SCOPE_OVERRIDES.json", scope_overrides_payload)
        result.stages_completed.append("feature_discovery")
        result.artifacts["feature_map"] = str(output_root / "FEATURE_MAP.json")

        # --- Scope resolution ---
        logger.info("Resolving scopes")
        scope_resolution = resolve_scopes(
            run_id=run_id,
            auto_features=auto_features,
            phase_plan=phase_plan,
            scope_overrides=scope_overrides_payload.get("overrides", {}),
        )
        _write_artifact(output_root, "SCOPE_RESOLUTION.json", scope_resolution)
        result.stages_completed.append("scope_resolution")

        # --- Stage 2: Template rendering ---
        if template_dir.exists():
            logger.info("Stage 2: Template rendering from %s", template_dir)
            context = build_template_context(
                feature_map=feature_map,
                scope_resolution=scope_resolution,
                phase_plan=phase_plan,
                repo_root=repo_root,
            )

            render_result = render_promptset(
                template_dir=template_dir,
                output_dir=prompt_output_dir,
                context=context,
            )
            result.stages_completed.append("template_rendering")
            result.summary["templates_rendered"] = render_result["rendered"]
            result.summary["templates_skipped"] = render_result["skipped"]

            if render_result["errors"]:
                for err in render_result["errors"]:
                    result.warnings.append({
                        "stage": "template_rendering",
                        "message": f"{err['template']}: {err['error']}",
                    })
        else:
            logger.info("No template_dir at %s — skipping template rendering", template_dir)
            prompt_output_dir.mkdir(parents=True, exist_ok=True)

        # --- Stage 2f: Contract generation ---
        logger.info("Stage 2f: Contract generation")
        contract_result = generate_all_contracts(
            phase_plan=phase_plan,
            scope_resolution=scope_resolution,
            prompt_dir=prompt_output_dir,
            output_dir=output_root,
            run_id=run_id,
            repo_name=repo_root.name,
        )
        result.stages_completed.append("contract_generation")
        result.artifacts["promptset"] = contract_result["promptset_path"]
        result.artifacts["artifacts"] = contract_result["artifacts_path"]
        result.artifacts["model_map"] = contract_result["model_map_path"]
        result.summary["phases"] = contract_result["phase_count"]
        result.summary["steps"] = contract_result["step_count"]
        result.summary["artifacts"] = contract_result["artifact_count"]

        # --- Stage 2h: Integrity validation ---
        logger.info("Stage 2h: Integrity validation")
        import yaml
        with open(contract_result["promptset_path"]) as f:
            promptset_data = yaml.safe_load(f)
        with open(contract_result["artifacts_path"]) as f:
            artifacts_data = yaml.safe_load(f)
        with open(contract_result["model_map_path"]) as f:
            model_map_data = yaml.safe_load(f)

        integrity = validate_promptset_integrity(
            promptset=promptset_data,
            artifacts=artifacts_data,
            model_map=model_map_data,
        )
        _write_artifact(output_root, "INTEGRITY_REPORT.json", integrity)
        result.stages_completed.append("integrity_validation")

        if not integrity["passed"]:
            for err in integrity["errors"]:
                result.errors.append({
                    "stage": "integrity_validation",
                    "message": f"[{err['check']}] {err['message']}",
                })
            logger.error(
                "Integrity validation FAILED: %d errors",
                integrity["error_count"],
            )
        else:
            logger.info("Integrity validation PASSED")

        for warn in integrity.get("warnings", []):
            result.warnings.append({
                "stage": "integrity_validation",
                "message": f"[{warn['check']}] {warn['message']}",
            })

        # --- Enrichment (optional, behind flag) ---
        if enrich:
            logger.info("LLM enrichment requested but not yet implemented — skipping")
            result.warnings.append({
                "stage": "enrichment",
                "message": "LLM enrichment not yet implemented",
            })

        # --- Write sync manifest ---
        result.success = integrity["passed"]
        manifest = result.to_dict()
        _write_artifact(output_root, "SYNC_MANIFEST.json", manifest)

        logger.info(
            "Sync complete: success=%s stages=%d errors=%d warnings=%d",
            result.success,
            len(result.stages_completed),
            len(result.errors),
            len(result.warnings),
        )

    except Exception as e:
        logger.exception("Sync pipeline failed: %s", e)
        result.errors.append({"stage": "pipeline", "message": str(e)})

    return result


def _write_artifact(output_dir: Path, filename: str, data: Dict[str, Any]) -> None:
    """Write a JSON artifact to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
