"""Typed models and deterministic serialization for system-data workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "system-data-proof.v1"
TOOL_VERSION = "TP-OPS-MAC-SCRUBBER-001.v1"

INSTALL_COMMAND = "brew install dust duf btop procs gdu dua-cli ncdu"

RISK_PRIORITY = {
    "safe_clear": 0,
    "rebuildable_cache": 1,
    "tool_mediated": 2,
    "review_first": 3,
    "blocked": 4,
    "unknown": 5,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def bytes_to_human(size: int) -> str:
    value = float(max(size, 0))
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return {k: to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [to_plain(v) for v in value]
    return value


def stable_json(value: Any) -> str:
    return json.dumps(to_plain(value), indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


@dataclass(frozen=True)
class ToolStatus:
    name: str
    path: str | None
    version: str | None
    available: bool
    required: bool = True
    error: str | None = None


@dataclass(frozen=True)
class ToolReport:
    required: tuple[str, ...]
    statuses: tuple[ToolStatus, ...]
    install_command: str = INSTALL_COMMAND

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(status.name for status in self.statuses if status.required and not status.available)

    @property
    def ok(self) -> bool:
        return not self.missing


@dataclass(frozen=True)
class DiskVolume:
    mount_point: str
    device: str
    fs_type: str
    device_type: str
    total_bytes: int
    used_bytes: int
    free_bytes: int


@dataclass(frozen=True)
class EnvironmentSnapshot:
    hostname: str
    platform: str
    macos_version: str
    home: str
    disk_pressure: str
    free_bytes: int
    total_bytes: int
    full_disk_access: str
    docker_cli_installed: bool
    docker_daemon_reachable: bool
    external_volumes: tuple[str, ...] = ()
    volumes: tuple[DiskVolume, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceRecord:
    source: str
    command: list[str] = field(default_factory=list)
    path: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    warning: str | None = None


@dataclass(frozen=True)
class Finding:
    finding_id: str
    category: str
    path: str
    size_bytes: int
    kind: str
    risk_level: str
    reclaim_mode: str
    reclaim_estimate_bytes: int
    same_volume_quarantine_effective: bool
    recommended_action: str
    requires_app_quit: tuple[str, ...]
    rationale: str
    evidence: tuple[EvidenceRecord, ...] = ()


@dataclass(frozen=True)
class PlanItem:
    action_id: str
    target_finding_id: str
    path: str
    action_type: str
    dry_run_supported: bool
    requires_confirmation: bool
    destructive_level: str
    expected_reclaim_bytes: int
    preconditions: tuple[str, ...]
    rollback_mode: str
    blocked_reason: str | None
    execution_order: int
    rationale: str


@dataclass(frozen=True)
class ExecutionRecord:
    action_id: str
    action_type: str
    path: str
    dry_run: bool
    status: str
    bytes_reclaimed: int = 0
    manifest_path: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ScanResult:
    tool_report: ToolReport
    environment: EnvironmentSnapshot
    findings: tuple[Finding, ...]
    warnings: tuple[str, ...] = ()
    processes: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class PlanResult:
    environment: EnvironmentSnapshot
    findings: tuple[Finding, ...]
    actions: tuple[PlanItem, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProofBundle:
    tp_id: str
    repo: str
    schema_version: str
    timestamp_utc: str
    git: dict[str, Any]
    tool_report: ToolReport
    implementation: dict[str, Any]
    tests: dict[str, Any]
    runtime_validation: dict[str, Any]
    docs: dict[str, Any]
    acceptance: dict[str, Any]
    unresolved: list[str] = field(default_factory=list)
