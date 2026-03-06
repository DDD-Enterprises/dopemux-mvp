#!/usr/bin/env python3
"""
Deterministic RepoScan runner.

This wrapper keeps `run_extraction_v3.py` unchanged and layers:
1) Stage 0/1 scanning and archetype classification
2) Deterministic profile selection
3) PromptPack v1/v2 generation
4) Delegation to the existing v3 extraction runner via env prompt-root override
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from lib.promptgen import (
    ARCHETYPES_FILENAME,
    BUILD_SURFACE_FILENAME,
    DEPENDENCY_GRAPH_HINTS_FILENAME,
    PROFILE_SELECTION_FILENAME,
    PROMPTPACK_DIFF_FILENAME,
    PROMPTPACK_V1_FILENAME,
    PROMPTPACK_V2_FILENAME,
    PROMPTPACK_V2_HASH_FILENAME,
    PROMPT_ADJUSTMENTS_FILENAME,
    REPO_FINGERPRINT_FILENAME,
    adjust_promptpack_v2,
    build_stage0_artifacts,
    classify_archetypes,
    compile_promptpack_v1,
    load_promptpack,
    load_selected_profile,
    select_profile,
)
from lib.promptgen.fingerprint import DEFAULT_EXCLUDE_GLOBS, DEFAULT_INCLUDE_GLOBS, ScanConfig
from lib.promptgen.hashing import sha256_file, sha256_text
from lib.promptgen.io import write_json
from lib.phase_contract_map import CONTRACT_MAP_FILENAME as PHASE_CONTRACT_MAP_FILENAME, write_phase_contract_map

PHASES = ["A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]
PHASE_DIR_NAMES: Dict[str, str] = {
    "A": "A_repo_control_plane",
    "H": "H_home_control_plane",
    "D": "D_docs_pipeline",
    "C": "C_code_surfaces",
    "E": "E_execution_plane",
    "W": "W_workflow_plane",
    "B": "B_boundary_plane",
    "G": "G_governance_plane",
    "Q": "Q_quality_assurance",
    "R": "R_arbitration",
    "X": "X_feature_index",
    "T": "T_task_packets",
    "Z": "Z_handoff_freeze",
}
PROMPTGEN_MODE_CHOICES = ("off", "v1", "v2", "auto")
RUN_PROMPTPACK_FINGERPRINT_FILENAME = "RUN_PROMPTPACK_FINGERPRINT.json"
PROMPTPACK_DIRNAME = "promptpacks"
DEFAULT_PROMPT_ROOT = SERVICE_DIR / "prompts" / "v3"
DEFAULT_PROFILES_DIR = SERVICE_DIR / "lib" / "promptgen" / "profiles"
DEFAULT_LEGACY_RUNNER = SERVICE_DIR / "run_extraction_v3.py"

V3_EXTRACTION_ROOT = Path("extraction/repo-truth-extractor/v3")
V3_RUNS_ROOT = V3_EXTRACTION_ROOT / "runs"
V3_LATEST_RUN_FILE = V3_EXTRACTION_ROOT / "latest_run_id.txt"

NO_PHASE_OPTS = {
    "--verify-phase-output",
    "--print-config",
    "--doctor-auth",
    "--preflight-providers",
    "--doctor",
    "--coverage-report",
    "--status",
    "--status-json",
    "--print-promptpack",
    "--gemini-list-models",
}


def _repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "services" / "repo-truth-extractor").is_dir():
            return candidate
    return start


def _has_opt(args: Iterable[str], option: str) -> bool:
    for token in args:
        if token == option or token.startswith(f"{option}="):
            return True
    return False


def _timestamp_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _resolve_run_id(repo_root: Path, explicit: Optional[str], mode: str, promptgen_only: bool) -> str:
    if explicit:
        return explicit.strip()
    if mode == "v2" or promptgen_only:
        latest_path = repo_root / V3_LATEST_RUN_FILE
        if latest_path.exists():
            latest = latest_path.read_text(encoding="utf-8").strip()
            if latest:
                return latest
    return _timestamp_run_id()


def _run_root(repo_root: Path, run_id: str) -> Path:
    return repo_root / V3_RUNS_ROOT / run_id


def _phase_list(phase_value: Optional[str]) -> List[str]:
    if not phase_value or phase_value == "ALL":
        return list(PHASES)
    return [phase_value]


def _write_stage_artifacts(out_dir: Path, artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    digests: Dict[str, str] = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename in sorted(artifacts):
        artifact_path = out_dir / filename
        write_json(artifact_path, artifacts[filename])
        digests[filename] = sha256_text(artifact_path.read_text(encoding="utf-8"))
    return digests


def _resolve_promptpack_json(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_dir():
        v2 = path / PROMPTPACK_V2_FILENAME
        if v2.exists():
            return v2
        v1 = path / PROMPTPACK_V1_FILENAME
        if v1.exists():
            return v1
        raise RuntimeError(
            f"Promptpack directory missing {PROMPTPACK_V1_FILENAME}/{PROMPTPACK_V2_FILENAME}: {path}"
        )
    return path


def _prompt_root_from_promptpack(promptpack_json: Path, payload: Dict[str, Any]) -> Path:
    rendered_root = str(payload.get("rendered_prompt_root") or "").strip()
    if rendered_root:
        return Path(rendered_root)
    if promptpack_json.name == PROMPTPACK_V2_FILENAME:
        return promptpack_json.parent / "PROMPTPACK.v2"
    return promptpack_json.parent / "PROMPTPACK.v1"


def _coverage_inputs_present(run_root: Path) -> bool:
    coverage = run_root / "COVERAGE_REPORT.json"
    if not coverage.exists():
        return False
    for phase in PHASES:
        qa_dir = run_root / PHASE_DIR_NAMES[phase] / "qa"
        if not qa_dir.exists():
            continue
        if any(True for _ in qa_dir.glob("*_QA.json")):
            return True
    return False


def _resolve_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _write_run_promptpack_fingerprint(
    *,
    run_root: Path,
    run_id: str,
    mode: str,
    promptpack_path: Optional[Path],
    promptpack_payload: Optional[Dict[str, Any]],
    prompt_root: Optional[Path],
    profile_selection: Optional[Dict[str, Any]],
    stage_artifact_digests: Optional[Dict[str, str]],
) -> Dict[str, Any]:
    promptpack_sha = sha256_file(promptpack_path) if promptpack_path and promptpack_path.exists() else None
    payload = {
        "version": "RUN_PROMPTPACK_FINGERPRINT_V1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "run_id": run_id,
        "promptgen_mode": mode,
        "promptpack_path": str(promptpack_path.resolve()) if promptpack_path else None,
        "promptpack_sha256": promptpack_sha,
        "promptpack_version": (promptpack_payload or {}).get("version") if promptpack_payload else None,
        "prompt_root": str(prompt_root.resolve()) if prompt_root else None,
        "profile_selection_path": str((run_root / PROFILE_SELECTION_FILENAME).resolve())
        if (run_root / PROFILE_SELECTION_FILENAME).exists()
        else None,
        "profile_id": (profile_selection or {}).get("selected_profile_id") if profile_selection else None,
        "profile_version": (profile_selection or {}).get("selected_profile_version") if profile_selection else None,
        "stage_artifact_sha256": stage_artifact_digests or {},
        "phase_contract_map": str((run_root / PHASE_CONTRACT_MAP_FILENAME).resolve())
        if (run_root / PHASE_CONTRACT_MAP_FILENAME).exists()
        else None,
    }
    write_json(run_root / RUN_PROMPTPACK_FINGERPRINT_FILENAME, payload)
    return payload


def _legacy_args(base_args: List[str], run_id: str, phase: str) -> List[str]:
    out = list(base_args)
    if not _has_opt(out, "--run-id"):
        out.extend(["--run-id", run_id])
    has_no_phase_op = any(_has_opt(out, opt) for opt in NO_PHASE_OPTS)
    if not has_no_phase_op and not _has_opt(out, "--phase"):
        out.extend(["--phase", phase])
    return out


def _run_legacy_runner(
    *,
    legacy_runner: Path,
    repo_root: Path,
    args: List[str],
    prompt_root: Optional[Path] = None,
) -> int:
    env = os.environ.copy()
    if prompt_root is not None:
        env["REPO_TRUTH_EXTRACTOR_PROMPT_ROOT"] = str(prompt_root.resolve())
    cmd = [sys.executable, str(legacy_runner), *args]
    proc = subprocess.run(cmd, cwd=str(repo_root), env=env)
    return int(proc.returncode)


def _ensure_coverage_report(legacy_runner: Path, repo_root: Path, run_id: str) -> int:
    args = ["--coverage-report", "--run-id", run_id]
    return _run_legacy_runner(legacy_runner=legacy_runner, repo_root=repo_root, args=args, prompt_root=None)


def _scan_and_classify(
    *,
    repo_root: Path,
    run_id: str,
    max_files: int,
    include_globs: Tuple[str, ...],
    exclude_globs: Tuple[str, ...],
) -> Dict[str, Dict[str, Any]]:
    scan_cfg = ScanConfig(
        max_files=max_files,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
    )
    stage0 = build_stage0_artifacts(repo_root, run_id, scan_cfg)
    archetypes = classify_archetypes(
        root=repo_root,
        run_id=run_id,
        repo_fingerprint=stage0[REPO_FINGERPRINT_FILENAME],
        build_surface=stage0[BUILD_SURFACE_FILENAME],
        dependency_hints=stage0[DEPENDENCY_GRAPH_HINTS_FILENAME],
    )
    artifacts = dict(stage0)
    artifacts[ARCHETYPES_FILENAME] = archetypes
    return artifacts


def _summary(
    *,
    run_id: str,
    mode: str,
    promptpack_path: Optional[Path],
    prompt_root: Optional[Path],
    run_root: Path,
    auto_v2_path: Optional[Path],
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "promptgen_mode": mode,
        "promptpack_path": str(promptpack_path.resolve()) if promptpack_path else None,
        "prompt_root": str(prompt_root.resolve()) if prompt_root else None,
        "profile_selection_path": str((run_root / PROFILE_SELECTION_FILENAME).resolve())
        if (run_root / PROFILE_SELECTION_FILENAME).exists()
        else None,
        "run_promptpack_fingerprint": str((run_root / RUN_PROMPTPACK_FINGERPRINT_FILENAME).resolve()),
        "auto_v2_suggestion_path": str(auto_v2_path.resolve()) if auto_v2_path else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser("RepoScan promptgen wrapper for run_extraction_v3.py")
    parser.add_argument("--phase", choices=PHASES + ["ALL"], default="ALL")
    parser.add_argument("--run-id", type=str)
    parser.add_argument("--promptgen", choices=list(PROMPTGEN_MODE_CHOICES), default="off")
    parser.add_argument("--promptpack", type=str)
    parser.add_argument("--promptgen-only", action="store_true")
    parser.add_argument("--prompt-root", type=str, default=str(DEFAULT_PROMPT_ROOT))
    parser.add_argument("--profiles-dir", type=str, default=str(DEFAULT_PROFILES_DIR))
    parser.add_argument("--legacy-runner", type=str, default=str(DEFAULT_LEGACY_RUNNER))
    parser.add_argument("--promptgen-max-files", type=int, default=600)
    parser.add_argument("--promptgen-include-globs", action="append")
    parser.add_argument("--promptgen-exclude-globs", action="append")
    parser.add_argument("--promptgen-output-dir", type=str, default="00_inputs")
    args, passthrough = parser.parse_known_args()

    if args.promptgen_only and args.promptgen == "off" and not args.promptpack:
        parser.error("--promptgen-only requires --promptgen v1|v2|auto or --promptpack.")
    if args.promptpack and args.promptgen != "off":
        print("warning: --promptpack takes precedence over --promptgen mode.", file=sys.stderr)

    repo_root = _repo_root(Path.cwd())
    run_id = _resolve_run_id(repo_root, args.run_id, args.promptgen, args.promptgen_only)
    run_root = _run_root(repo_root, run_id)
    inputs_root = run_root / args.promptgen_output_dir
    promptpack_root = run_root / PROMPTPACK_DIRNAME
    run_root.mkdir(parents=True, exist_ok=True)
    inputs_root.mkdir(parents=True, exist_ok=True)
    promptpack_root.mkdir(parents=True, exist_ok=True)
    try:
        write_phase_contract_map(run_root, run_id)
    except Exception as exc:
        print(f"warning: failed to write {PHASE_CONTRACT_MAP_FILENAME}: {exc}", file=sys.stderr)

    phases = _phase_list(args.phase)
    phase_value = args.phase or "ALL"
    legacy_runner = _resolve_path(args.legacy_runner, repo_root)
    source_prompt_root = _resolve_path(args.prompt_root, repo_root)
    profiles_dir = _resolve_path(args.profiles_dir, repo_root)

    promptpack_path: Optional[Path] = None
    promptpack_payload: Optional[Dict[str, Any]] = None
    selected_prompt_root: Optional[Path] = None
    profile_selection: Optional[Dict[str, Any]] = None
    profile_payload: Optional[Dict[str, Any]] = None
    stage_artifact_digests: Optional[Dict[str, str]] = None
    v1_payload: Optional[Dict[str, Any]] = None

    if args.promptpack:
        promptpack_path = _resolve_promptpack_json(args.promptpack)
        promptpack_payload = load_promptpack(promptpack_path)
        selected_prompt_root = _prompt_root_from_promptpack(promptpack_path, promptpack_payload)
        _write_run_promptpack_fingerprint(
            run_root=run_root,
            run_id=run_id,
            mode="promptpack",
            promptpack_path=promptpack_path,
            promptpack_payload=promptpack_payload,
            prompt_root=selected_prompt_root,
            profile_selection=None,
            stage_artifact_digests=None,
        )
    elif args.promptgen != "off":
        include_globs = tuple(args.promptgen_include_globs or list(DEFAULT_INCLUDE_GLOBS))
        exclude_globs = tuple(args.promptgen_exclude_globs or list(DEFAULT_EXCLUDE_GLOBS))
        stage_artifacts = _scan_and_classify(
            repo_root=repo_root,
            run_id=run_id,
            max_files=int(args.promptgen_max_files),
            include_globs=include_globs,
            exclude_globs=exclude_globs,
        )
        stage_artifact_digests = _write_stage_artifacts(inputs_root, stage_artifacts)

        profile_selection = select_profile(
            run_id=run_id,
            root=repo_root,
            repo_fingerprint=stage_artifacts[REPO_FINGERPRINT_FILENAME],
            archetypes_payload=stage_artifacts[ARCHETYPES_FILENAME],
            profiles_dir=profiles_dir,
        )
        write_json(run_root / PROFILE_SELECTION_FILENAME, profile_selection)
        profile_payload = load_selected_profile(profile_selection, profiles_dir)

        v1_result = compile_promptpack_v1(
            run_id=run_id,
            root=repo_root,
            prompt_root=source_prompt_root,
            promptpack_root=promptpack_root,
            phases=phases,
            profile_selection=profile_selection,
            profile_payload=profile_payload,
            archetypes_payload=stage_artifacts[ARCHETYPES_FILENAME],
        )
        promptpack_path = Path(v1_result["promptpack_json"])
        promptpack_payload = v1_result["payload"]
        selected_prompt_root = Path(v1_result["prompt_root"])
        v1_payload = v1_result["payload"]

        if args.promptgen == "v2":
            if not _coverage_inputs_present(run_root):
                raise RuntimeError(
                    "Promptgen v2 requires existing COVERAGE_REPORT.json and *_QA.json files. "
                    "Run extraction first or use --promptgen v1/auto."
                )
            v2_result = adjust_promptpack_v2(
                run_id=run_id,
                run_root=run_root,
                promptpack_root=promptpack_root,
                promptpack_v1_payload=v1_payload,
                profile_payload=profile_payload,
            )
            promptpack_path = Path(v2_result["promptpack_json"])
            promptpack_payload = v2_result["payload"]
            selected_prompt_root = Path(v2_result["prompt_root"])

        _write_run_promptpack_fingerprint(
            run_root=run_root,
            run_id=run_id,
            mode=args.promptgen,
            promptpack_path=promptpack_path,
            promptpack_payload=promptpack_payload,
            prompt_root=selected_prompt_root,
            profile_selection=profile_selection,
            stage_artifact_digests=stage_artifact_digests,
        )
    else:
        _write_run_promptpack_fingerprint(
            run_root=run_root,
            run_id=run_id,
            mode="off",
            promptpack_path=None,
            promptpack_payload=None,
            prompt_root=source_prompt_root,
            profile_selection=None,
            stage_artifact_digests=None,
        )

    auto_v2_path: Optional[Path] = None
    if args.promptgen_only:
        if args.promptgen == "auto" and v1_payload is not None and profile_payload is not None and _coverage_inputs_present(run_root):
            v2_result = adjust_promptpack_v2(
                run_id=run_id,
                run_root=run_root,
                promptpack_root=promptpack_root,
                promptpack_v1_payload=v1_payload,
                profile_payload=profile_payload,
            )
            auto_v2_path = Path(v2_result["promptpack_json"])
        print(
            json.dumps(
                _summary(
                    run_id=run_id,
                    mode=args.promptgen if not args.promptpack else "promptpack",
                    promptpack_path=promptpack_path,
                    prompt_root=selected_prompt_root,
                    run_root=run_root,
                    auto_v2_path=auto_v2_path,
                ),
                indent=2,
            )
        )
        return 0

    delegated_args = _legacy_args(list(passthrough), run_id=run_id, phase=phase_value)
    rc = _run_legacy_runner(
        legacy_runner=legacy_runner,
        repo_root=repo_root,
        args=delegated_args,
        prompt_root=selected_prompt_root,
    )
    if rc != 0:
        return rc

    if args.promptgen == "auto" and v1_payload is not None and profile_payload is not None:
        coverage_rc = _ensure_coverage_report(legacy_runner, repo_root, run_id)
        if coverage_rc == 0 and _coverage_inputs_present(run_root):
            v2_result = adjust_promptpack_v2(
                run_id=run_id,
                run_root=run_root,
                promptpack_root=promptpack_root,
                promptpack_v1_payload=v1_payload,
                profile_payload=profile_payload,
            )
            auto_v2_path = Path(v2_result["promptpack_json"])
            print(
                json.dumps(
                    {
                        "run_id": run_id,
                        "auto_v2_suggestion_path": str(auto_v2_path.resolve()),
                        "prompt_adjustments_path": str((promptpack_root / PROMPT_ADJUSTMENTS_FILENAME).resolve()),
                        "promptpack_diff_path": str((promptpack_root / PROMPTPACK_DIFF_FILENAME).resolve()),
                        "promptpack_v2_sha_path": str((promptpack_root / PROMPTPACK_V2_HASH_FILENAME).resolve()),
                    },
                    indent=2,
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
