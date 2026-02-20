#!/usr/bin/env python3
"""Reprocess failed partitions using deterministic failure-policy plans."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_SCRIPT = Path("services/repo-truth-extractor/run_extraction_v3.py")
REPROCESS_POLICY_MODULE = Path("services/repo-truth-extractor/lib/reprocess_policy.py")


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, (REPO_ROOT / path).resolve())
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner_mod = _load_module(RUNNER_SCRIPT, "repo_truth_extractor_v3")
reprocess_mod = _load_module(REPROCESS_POLICY_MODULE, "repo_truth_extractor_reprocess_policy")
DOCTOR_REPROCESS_PLAN_FILENAME = reprocess_mod.DOCTOR_REPROCESS_PLAN_FILENAME
build_run_reprocess_plan = reprocess_mod.build_run_reprocess_plan


def _collect_phase_dirs(run_root: Path, run_id: str) -> dict[str, Path]:
    run_dir = run_root / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    phase_dirs: dict[str, Path] = {}
    for entry in sorted(run_dir.iterdir()):
        if not entry.is_dir():
            continue
        phase_code = entry.name.split("_", 1)[0]
        if phase_code in runner_mod.PHASES and phase_code not in phase_dirs:
            phase_dirs[phase_code] = entry
    return phase_dirs


def _phase_subset(phases: Iterable[str], requested: Sequence[str]) -> Sequence[str]:
    if not requested:
        return sorted(phases)
    requested_upper = [phase.upper() for phase in requested]
    return [phase for phase in requested_upper if phase in phases]


def _write_partition_file(partitions: Sequence[str]) -> Path:
    tmp = tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8")
    tmp.write("\n".join(partitions))
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def _doctor_plan_path(run_root: Path) -> Path:
    return run_root.parent / "doctor" / DOCTOR_REPROCESS_PLAN_FILENAME


def _load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _filter_plan_to_phases(plan: Dict[str, object], phases: Sequence[str]) -> Dict[str, object]:
    payload_phases = plan.get("phases")
    if not isinstance(payload_phases, dict):
        return {"run_id": plan.get("run_id"), "phases": {}}
    if not phases:
        return plan
    filtered = {phase: payload_phases.get(phase) for phase in phases if phase in payload_phases}
    out = dict(plan)
    out["phases"] = filtered
    return out


def _plan_rows(plan: Dict[str, object]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    phases = plan.get("phases")
    if not isinstance(phases, dict):
        return rows
    for phase, phase_payload in sorted(phases.items()):
        if not isinstance(phase_payload, dict):
            continue
        phase_rows = phase_payload.get("plan_rows")
        if not isinstance(phase_rows, list):
            continue
        for row in phase_rows:
            if not isinstance(row, dict):
                continue
            merged = dict(row)
            merged.setdefault("phase", phase)
            rows.append(merged)
    return rows


def _print_plan_summary(plan: Dict[str, object]) -> None:
    summary = plan.get("summary")
    phases = plan.get("phases")
    print("Reprocess plan summary:")
    if isinstance(summary, dict):
        print(
            "  phases_planned={phases_planned} total_failures={total_failures} total_rerun_partitions={total_rerun_partitions}".format(
                phases_planned=summary.get("phases_planned", 0),
                total_failures=summary.get("total_failures", 0),
                total_rerun_partitions=summary.get("total_rerun_partitions", 0),
            )
        )
    if not isinstance(phases, dict):
        return
    for phase, payload in sorted(phases.items()):
        if not isinstance(payload, dict):
            continue
        rerun = payload.get("rerun_partitions")
        rerun_count = len(rerun) if isinstance(rerun, list) else 0
        total_failures = int(payload.get("total_failures", 0))
        print(f"  {phase}: failures={total_failures} rerun_partitions={rerun_count}")


def _build_plan(args: argparse.Namespace, phase_dirs: Dict[str, Path]) -> Dict[str, object]:
    selected_phases = _phase_subset(phase_dirs.keys(), args.phases or [])
    if args.from_doctor:
        plan_path = _doctor_plan_path(args.run_root)
        plan_payload = _load_json(plan_path)
        if not plan_payload:
            raise FileNotFoundError(f"Doctor reprocess plan not found or invalid: {plan_path}")
        return _filter_plan_to_phases(plan_payload, selected_phases)
    run_dir = args.run_root / args.run_id
    return build_run_reprocess_plan(run_dir=run_dir, run_id=args.run_id, phases=selected_phases)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reprocess only failed partitions.")
    parser.add_argument("--run-id", required=True, help="Run ID to reprocess.")
    parser.add_argument(
        "--run-root",
        type=Path,
        default=Path("extraction") / "repo-truth-extractor" / "v3" / "runs",
        help="Base path where extraction runs are stored.",
    )
    parser.add_argument(
        "--phases",
        nargs="+",
        help="Specific phases to reprocess (default=all phases with failures).",
    )
    parser.add_argument(
        "--failure-policy",
        choices=["matrix"],
        default="matrix",
        help="Failure policy selector (default: matrix).",
    )
    parser.add_argument(
        "--from-doctor",
        action="store_true",
        help="Load plan from extraction/repo-truth-extractor/v3/doctor/DOCTOR_REPROCESS_PLAN.json.",
    )
    parser.add_argument(
        "--emit-plan-only",
        action="store_true",
        help="Print plan and exit without running reruns.",
    )
    parser.add_argument(
        "--partition-workers",
        type=int,
        default=1,
        help="Worker count to pass to the runner.",
    )
    parser.add_argument(
        "--runner-extra",
        type=str,
        default="",
        help="Additional runner args (shell-split).",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not add --resume when rerunning the runner.",
    )
    parser.add_argument(
        "--gemini-transport",
        type=str,
        choices=["sdk", "openai_compat_http"],
        help="Gemini transport to pass to the runner.",
    )
    parser.add_argument(
        "--openai-transport",
        type=str,
        choices=["openai_sdk"],
        help="OpenAI transport to pass to the runner.",
    )
    parser.add_argument(
        "--open-transport",
        dest="openai_transport",
        type=str,
        choices=["openai_sdk"],
        help="Alias for --openai-transport.",
    )
    parser.add_argument(
        "--xai-transport",
        type=str,
        choices=["openai_sdk"],
        help="xAI transport to pass to the runner.",
    )
    args = parser.parse_args()

    phase_dirs = _collect_phase_dirs(args.run_root, args.run_id)
    if not phase_dirs:
        print("No target phases found; nothing to reprocess.")
        return 0
    plan = _build_plan(args, phase_dirs)
    _print_plan_summary(plan)
    if args.emit_plan_only:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    extra_args = shlex.split(args.runner_extra) if args.runner_extra else []
    runner_base = [
        sys.executable,
        str((REPO_ROOT / RUNNER_SCRIPT).resolve()),
    ]
    plan_phases = plan.get("phases")
    if not isinstance(plan_phases, dict):
        print("Plan has no phases to execute.")
        return 0
    status = 0
    for phase, phase_payload in sorted(plan_phases.items()):
        phase_dir = phase_dirs.get(phase)
        if not phase_dir:
            print(f"Skipping unknown phase {phase}")
            continue
        if not isinstance(phase_payload, dict):
            continue
        failed_ids = sorted(
            {
                str(partition_id).strip()
                for partition_id in phase_payload.get("rerun_partitions", [])
                if str(partition_id).strip()
            }
        )
        if not failed_ids:
            print(f"Phase {phase}: no failed partitions to reprocess.")
            continue
        print(f"Phase {phase}: reprocessing {len(failed_ids)} policy-selected partitions.")
        partition_file = _write_partition_file(failed_ids)
        plan_rows = phase_payload.get("plan_rows")
        conservative = False
        if isinstance(plan_rows, list):
            conservative = any(
                isinstance(row, dict) and str(row.get("action")) == "rerun_conservative"
                for row in plan_rows
            )
        workers = 1 if conservative else max(1, int(args.partition_workers))
        cmd = [
            *runner_base,
            "--phase",
            phase,
            "--run-id",
            args.run_id,
            "--no-write-latest",
            "--partition-workers",
            str(workers),
            "--partition-id-file",
            str(partition_file),
        ]
        if not args.no_resume:
            cmd.append("--resume")
        if args.gemini_transport:
            cmd.extend(["--gemini-transport", args.gemini_transport])
        if args.openai_transport:
            cmd.extend(["--openai-transport", args.openai_transport])
        if args.xai_transport:
            cmd.extend(["--xai-transport", args.xai_transport])
        cmd.extend(extra_args)
        try:
            subprocess.run(cmd, check=True, cwd=REPO_ROOT)
        except subprocess.CalledProcessError as exc:
            print(f"Runner failed for phase {phase}: {exc}")
            status = exc.returncode or 1
        finally:
            partition_file.unlink(missing_ok=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
