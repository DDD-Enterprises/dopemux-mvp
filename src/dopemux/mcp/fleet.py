"""Fleet/worktree MCP config helpers (Packet 003).

``fleet init`` plans/applies local config across worktrees.
``fleet doctor`` aggregates Packet 001 doctor reports.
Neither mutates globals nor starts/stops containers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .config_repair import RepairPlan, apply_repair, plan_repair
from .project_identity import ProjectIdentityError, resolve_project_identity

SCHEMA_VERSION = "1.0"


def _status_rank(status: str) -> int:
    order = {
        "PASS": 0,
        "PASS_WITH_WARNINGS": 1,
        "NOOP": 0,
        "PLANNED": 1,
        "APPLIED": 0,
        "FAIL": 2,
        "BLOCKED": 2,
        "UNKNOWN": 3,
    }
    return order.get(status, 3)


def _worst_status(statuses: Sequence[str]) -> str:
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=_status_rank)


def _paths_same_project(project_root: Path, worktree: Path) -> tuple[bool, str]:
    """Return (ok, reason) whether worktree belongs to project_root."""
    try:
        project_root = project_root.expanduser().resolve()
        worktree = worktree.expanduser().resolve()
    except OSError as exc:
        return False, f"path resolve failed: {exc}"

    if not worktree.is_dir():
        return False, "worktree path is not a directory"
    if not project_root.is_dir():
        return False, "project root is not a directory"

    try:
        identity = resolve_project_identity(
            cwd=worktree,
            env={"DOPEMUX_WORKSPACE_ROOT": str(worktree)},
        )
    except ProjectIdentityError as exc:
        return False, f"identity resolution failed: {exc}"

    try:
        id_project = identity.project_root.resolve()
        expected = project_root.resolve()
    except OSError as exc:
        return False, f"project root resolve failed: {exc}"

    if id_project != expected:
        # Also accept when worktree IS the project root itself
        if worktree.resolve() == expected:
            return True, "worktree is project root"
        return (
            False,
            f"worktree project_root={id_project} does not match --repo {expected}",
        )
    return True, "FLEET_WORKTREE_VALID"


@dataclass
class FleetWorktreeResult:
    path: str
    status: str
    code: str
    message: str
    repair: Optional[Dict[str, Any]] = None
    top_findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "path": self.path,
            "status": self.status,
            "code": self.code,
            "message": self.message,
            "top_findings": list(self.top_findings),
        }
        if self.repair is not None:
            out["repair"] = self.repair
        return out


@dataclass
class FleetInitReport:
    schema_version: str = SCHEMA_VERSION
    operation: str = "fleet-init"
    dry_run: bool = True
    status: str = "UNKNOWN"
    project_root: str = ""
    worktrees: List[FleetWorktreeResult] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    next_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "dry_run": self.dry_run,
            "status": self.status,
            "project_root": self.project_root,
            "worktrees": [w.to_dict() for w in self.worktrees],
            "counts": dict(self.counts),
            "next_actions": list(self.next_actions),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2) + "\n"


@dataclass
class FleetDoctorReport:
    schema_version: str = SCHEMA_VERSION
    operation: str = "fleet-doctor"
    status: str = "UNKNOWN"
    project_root: str = ""
    worktrees: List[Dict[str, Any]] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    next_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "status": self.status,
            "project_root": self.project_root,
            "worktrees": list(self.worktrees),
            "counts": dict(self.counts),
            "next_actions": list(self.next_actions),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2) + "\n"


def fleet_init(
    project_root: Path | str,
    worktrees: Sequence[Path | str],
    catalog: Mapping[str, Any],
    *,
    dry_run: bool = True,
    apply: bool = False,
    catalog_paths: Optional[Sequence[str]] = None,
    **plan_kwargs: Any,
) -> FleetInitReport:
    """Plan or apply config repair across worktrees. Never starts containers."""
    if dry_run and apply:
        # Prefer dry-run semantics when both set; callers should prevent this.
        apply = False
    if not dry_run and not apply:
        dry_run = True

    root = Path(project_root).expanduser().resolve()
    report = FleetInitReport(
        dry_run=dry_run and not apply,
        project_root=str(root),
        counts={
            "initialized": 0,
            "already_valid": 0,
            "repaired": 0,
            "skipped": 0,
            "failed": 0,
            "unknown": 0,
        },
        next_actions=[
            "dopemux mcp fleet doctor --repo <project> --worktrees <paths> --json",
            "dopemux mcp start --repo <worktree>",
        ],
    )

    statuses: List[str] = []
    for raw in worktrees:
        wt_path = Path(raw).expanduser()
        try:
            wt_path = wt_path.resolve()
        except OSError:
            result = FleetWorktreeResult(
                path=str(raw),
                status="FAIL",
                code="FLEET_WORKTREE_INVALID",
                message="path does not resolve",
            )
            report.worktrees.append(result)
            report.counts["failed"] += 1
            statuses.append("FAIL")
            continue

        ok, reason = _paths_same_project(root, wt_path)
        if not ok:
            result = FleetWorktreeResult(
                path=str(wt_path),
                status="FAIL",
                code="FLEET_WORKTREE_INVALID",
                message=reason,
            )
            report.worktrees.append(result)
            report.counts["failed"] += 1
            statuses.append("FAIL")
            continue

        try:
            plan: RepairPlan = plan_repair(
                wt_path,
                catalog,
                dry_run=not apply,
                catalog_paths=catalog_paths,
                **plan_kwargs,
            )
            if apply and plan.status != "BLOCKED":
                plan.dry_run = False
                plan = apply_repair(plan)
        except Exception as exc:  # noqa: BLE001 — surface as failed worktree
            result = FleetWorktreeResult(
                path=str(wt_path),
                status="UNKNOWN",
                code="FLEET_WORKTREE_UNKNOWN",
                message=str(exc),
            )
            report.worktrees.append(result)
            report.counts["unknown"] += 1
            statuses.append("UNKNOWN")
            continue

        if plan.status == "BLOCKED":
            code = "FLEET_WORKTREE_SKIPPED"
            bucket = "skipped"
            st = "FAIL"
        elif plan.status == "NOOP":
            code = "FLEET_WORKTREE_VALID"
            bucket = "already_valid"
            st = "PASS"
        elif plan.status == "APPLIED":
            code = "FLEET_WORKTREE_REPAIRED"
            bucket = "repaired"
            st = "PASS"
        elif plan.status == "PLANNED":
            # dry-run planned repair counts as initialized (would init/repair)
            code = "FLEET_WORKTREE_REPAIRED"
            bucket = "initialized" if any(
                c.get("reason") in {"MISSING_MCP_JSON", "ENVRC_REGENERATED"}
                for c in plan.planned_changes
            ) else "repaired"
            st = "PASS_WITH_WARNINGS"
        else:
            code = "FLEET_WORKTREE_UNKNOWN"
            bucket = "unknown"
            st = "UNKNOWN"

        report.counts[bucket] = report.counts.get(bucket, 0) + 1
        statuses.append(st)
        report.worktrees.append(
            FleetWorktreeResult(
                path=str(wt_path),
                status=st,
                code=code,
                message=reason,
                repair=plan.to_dict(),
                top_findings=[c.get("reason") or "" for c in plan.planned_changes[:3]],
            )
        )

    report.status = _worst_status(statuses)
    return report


def fleet_doctor(
    project_root: Path | str,
    worktrees: Sequence[Path | str],
    catalog: Mapping[str, Any],
    *,
    catalog_paths: Optional[Sequence[str]] = None,
    skip_docker: bool = True,
    process_env: Optional[Mapping[str, str]] = None,
    run_doctor_fn: Any = None,
) -> FleetDoctorReport:
    """Run repo-aware doctor for each worktree and aggregate."""
    root = Path(project_root).expanduser().resolve()
    report = FleetDoctorReport(
        project_root=str(root),
        counts={"pass": 0, "warn": 0, "fail": 0, "unknown": 0},
        next_actions=[],
    )

    if run_doctor_fn is None:
        from .doctor import run_mcp_doctor

        run_doctor_fn = run_mcp_doctor

    statuses: List[str] = []
    for raw in worktrees:
        wt_path = Path(raw).expanduser()
        try:
            wt_path = wt_path.resolve()
        except OSError:
            report.worktrees.append(
                {
                    "path": str(raw),
                    "status": "UNKNOWN",
                    "top_findings": ["PATH_UNRESOLVABLE"],
                }
            )
            report.counts["unknown"] += 1
            statuses.append("UNKNOWN")
            continue

        ok, reason = _paths_same_project(root, wt_path)
        if not ok:
            report.worktrees.append(
                {
                    "path": str(wt_path),
                    "status": "FAIL",
                    "top_findings": ["FLEET_WORKTREE_INVALID", reason],
                }
            )
            report.counts["fail"] += 1
            statuses.append("FAIL")
            continue

        try:
            dr = run_doctor_fn(
                str(wt_path),
                catalog=catalog,
                catalog_paths_checked=list(catalog_paths or []),
                compose_path=None,
                skip_docker=skip_docker,
                process_env=dict(process_env or {}),
            )
            status = getattr(dr, "status", None) or (
                dr.get("status") if isinstance(dr, dict) else "UNKNOWN"
            )
            findings = []
            raw_findings = getattr(dr, "findings", None)
            if raw_findings is None and isinstance(dr, dict):
                raw_findings = dr.get("findings") or []
            for f in list(raw_findings or [])[:3]:
                if hasattr(f, "code"):
                    findings.append(str(f.code))
                elif isinstance(f, dict):
                    findings.append(str(f.get("code") or f.get("id") or "FINDING"))
                else:
                    findings.append(str(f))
        except Exception as exc:  # noqa: BLE001
            status = "UNKNOWN"
            findings = [f"DOCTOR_ERROR:{exc}"]

        status_s = str(status)
        if status_s == "PASS":
            report.counts["pass"] += 1
        elif status_s == "PASS_WITH_WARNINGS":
            report.counts["warn"] += 1
        elif status_s == "FAIL":
            report.counts["fail"] += 1
        else:
            report.counts["unknown"] += 1
        statuses.append(status_s)
        report.worktrees.append(
            {
                "path": str(wt_path),
                "status": status_s,
                "top_findings": findings,
            }
        )

    report.status = _worst_status(statuses)
    if report.counts.get("fail") or report.counts.get("unknown"):
        report.next_actions = [
            "dopemux mcp repair-config --repo <failing-worktree> --dry-run --json",
            "dopemux mcp repair-config --repo <failing-worktree> --apply",
            "dopemux mcp start --repo <failing-worktree>",
        ]
    return report


def format_fleet_init_human(report: FleetInitReport) -> str:
    lines = [
        f"fleet init {report.status}  dry_run={report.dry_run}",
        f"project: {report.project_root}",
        f"counts: {report.counts}",
    ]
    for wt in report.worktrees[:20]:
        lines.append(f"  • {wt.path}: {wt.status} [{wt.code}] {wt.message}")
    return "\n".join(lines) + "\n"


def format_fleet_doctor_human(report: FleetDoctorReport, *, max_findings: int = 3) -> str:
    lines = [
        f"fleet doctor {report.status}",
        f"project: {report.project_root}",
        f"counts: pass={report.counts.get('pass', 0)} warn={report.counts.get('warn', 0)} "
        f"fail={report.counts.get('fail', 0)} unknown={report.counts.get('unknown', 0)}",
    ]
    for wt in report.worktrees:
        tops = ", ".join((wt.get("top_findings") or [])[:max_findings]) or "(none)"
        lines.append(f"  • {wt.get('path')}: {wt.get('status')} — {tops}")
    return "\n".join(lines) + "\n"
