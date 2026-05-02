"""Cleanup executor. External tools discover; Dopemux owns mutation and proof."""

from __future__ import annotations

import shutil
from pathlib import Path

from .models import ExecutionRecord, PlanItem, stable_json, utc_now
from .tools import ToolRunner


def _manifest_path(root: Path, name: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{name}.json"


def execute_plan(
    actions: tuple[PlanItem, ...],
    *,
    dry_run: bool = True,
    yes: bool = False,
    proof_dir: Path,
    quarantine_dir: Path | None = None,
    runner: ToolRunner | None = None,
) -> tuple[ExecutionRecord, ...]:
    runner = runner or ToolRunner()
    records: list[ExecutionRecord] = []
    for action in sorted(actions, key=lambda item: item.execution_order):
        path = Path(action.path).expanduser()
        manifest = proof_dir / f"{action.action_id}-manifest.json"
        if dry_run:
            blocked = action.action_type in {"blocked", "review_required"}
            records.append(
                ExecutionRecord(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    path=action.path,
                    dry_run=True,
                    status="skipped" if blocked else "planned",
                    error=(action.blocked_reason or "operator review required") if blocked else None,
                )
            )
            continue
        manifest = _manifest_path(proof_dir, f"{action.action_id}-manifest")
        if action.action_type in {"blocked", "review_required"}:
            record = ExecutionRecord(
                action_id=action.action_id,
                action_type=action.action_type,
                path=action.path,
                dry_run=dry_run,
                status="skipped",
                manifest_path=str(manifest),
                error=action.blocked_reason or "operator review required",
            )
            manifest.write_text(stable_json({"timestamp_utc": utc_now(), "record": record}), encoding="utf-8")
            records.append(record)
            continue
        if action.requires_confirmation and not yes:
            record = ExecutionRecord(
                action_id=action.action_id,
                action_type=action.action_type,
                path=action.path,
                dry_run=False,
                status="blocked",
                manifest_path=str(manifest),
                error="confirmation required",
            )
            manifest.write_text(stable_json({"timestamp_utc": utc_now(), "record": record}), encoding="utf-8")
            records.append(record)
            continue
        try:
            if action.action_type == "docker_prune":
                result = runner.run(["docker", "system", "prune", "--force"], timeout=120)
                status = "executed" if result.returncode == 0 else "failed"
                error = None if result.returncode == 0 else result.stderr.strip()
            elif action.action_type == "homebrew_cleanup":
                result = runner.run(["brew", "cleanup", "--prune=all"], timeout=120)
                status = "executed" if result.returncode == 0 else "failed"
                error = None if result.returncode == 0 else result.stderr.strip()
            elif action.action_type == "simctl_delete_unavailable":
                result = runner.run(["xcrun", "simctl", "delete", "unavailable"], timeout=120)
                status = "executed" if result.returncode == 0 else "failed"
                error = None if result.returncode == 0 else result.stderr.strip()
            elif action.action_type == "quarantine":
                if quarantine_dir is None:
                    raise RuntimeError("quarantine_dir required for quarantine action")
                quarantine_dir.mkdir(parents=True, exist_ok=True)
                dest = quarantine_dir / f"{action.action_id}-{path.name}"
                shutil.move(str(path), str(dest))
                status = "executed"
                error = None
            elif action.action_type == "clear_safe_path":
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.exists():
                    path.unlink()
                status = "executed"
                error = None
            else:
                record = ExecutionRecord(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    path=action.path,
                    dry_run=False,
                    status="blocked",
                    manifest_path=str(manifest),
                    error=f"unsupported action type: {action.action_type}",
                )
                manifest.write_text(
                    stable_json({"timestamp_utc": utc_now(), "record": record}),
                    encoding="utf-8",
                )
                records.append(record)
                continue
            record = ExecutionRecord(
                action_id=action.action_id,
                action_type=action.action_type,
                path=action.path,
                dry_run=False,
                status=status,
                bytes_reclaimed=action.expected_reclaim_bytes if status == "executed" else 0,
                manifest_path=str(manifest),
                error=error,
            )
        except Exception as exc:
            record = ExecutionRecord(
                action_id=action.action_id,
                action_type=action.action_type,
                path=action.path,
                dry_run=False,
                status="failed",
                manifest_path=str(manifest),
                error=str(exc),
            )
        manifest.write_text(stable_json({"timestamp_utc": utc_now(), "record": record}), encoding="utf-8")
        records.append(record)
    return tuple(records)


def restore_manifest(manifest_path: Path, *, dry_run: bool = True) -> ExecutionRecord:
    # V1 stores manifests for audit and exposes restore listing. Actual restore
    # for moved paths is deliberately conservative until external volume policy
    # is exercised in a real run.
    return ExecutionRecord(
        action_id=manifest_path.stem,
        action_type="restore",
        path=str(manifest_path),
        dry_run=dry_run,
        status="planned" if dry_run else "blocked",
        error=None if dry_run else "manual restore review required",
    )
