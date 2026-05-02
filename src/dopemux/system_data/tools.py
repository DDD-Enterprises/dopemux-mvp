"""Required external tool integration for system-data workflows."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

from .models import CommandResult, DiskVolume, EvidenceRecord, ToolReport, ToolStatus


REQUIRED_TOOLS: tuple[str, ...] = ("dust", "duf", "btop", "procs", "gdu", "dua", "ncdu")
INSTALL_COMMAND = "brew install dust duf btop procs gdu dua-cli ncdu"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class ToolError(RuntimeError):
    """Raised when a required tool preflight fails."""


def _version_args(tool: str) -> list[str]:
    if tool == "duf":
        return [tool, "-version"]
    if tool == "btop":
        return [tool, "--version"]
    return [tool, "--version"]


class ToolRunner:
    """Thin wrapper around external tools with deterministic result capture."""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.commands_run: list[CommandResult] = []

    def run(self, args: list[str], *, timeout: int | None = None) -> CommandResult:
        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout or self.timeout,
            )
            result = CommandResult(
                command=args,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            result = CommandResult(
                command=args,
                returncode=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                timed_out=True,
            )
        self.commands_run.append(result)
        return result

    def check_required_tools(self) -> ToolReport:
        statuses: list[ToolStatus] = []
        for tool in REQUIRED_TOOLS:
            path = shutil.which(tool)
            if not path:
                statuses.append(
                    ToolStatus(
                        name=tool,
                        path=None,
                        version=None,
                        available=False,
                        error=f"{tool} not found on PATH",
                    )
                )
                continue
            version_result = self.run(_version_args(tool), timeout=5)
            version = (version_result.stdout or version_result.stderr).strip().splitlines()
            statuses.append(
                ToolStatus(
                    name=tool,
                    path=path,
                    version=version[0] if version else None,
                    available=version_result.returncode == 0,
                    error=None if version_result.returncode == 0 else version_result.stderr.strip(),
                )
            )
        return ToolReport(required=REQUIRED_TOOLS, statuses=tuple(statuses), install_command=INSTALL_COMMAND)

    def require_tools(self) -> ToolReport:
        report = self.check_required_tools()
        if not report.ok:
            missing = ", ".join(report.missing)
            raise ToolError(f"missing required system-data tools: {missing}. Install with: {INSTALL_COMMAND}")
        return report


def parse_human_size(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    match = re.match(r"(?i)^\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGTPE]?i?B?|B)?\s*$", text)
    if not match:
        return 0
    amount = float(match.group(1))
    unit = (match.group(2) or "B").upper().replace("IB", "I")
    powers = {
        "B": 0,
        "K": 1,
        "KI": 1,
        "KB": 1,
        "M": 2,
        "MI": 2,
        "MB": 2,
        "G": 3,
        "GI": 3,
        "GB": 3,
        "T": 4,
        "TI": 4,
        "TB": 4,
        "P": 5,
        "PI": 5,
        "PB": 5,
    }
    return int(amount * (1024 ** powers.get(unit, 0)))


def parse_duf_json(text: str) -> tuple[DiskVolume, ...]:
    raw = json.loads(text or "[]")
    items = raw.get("filesystems", raw) if isinstance(raw, dict) else raw
    volumes: list[DiskVolume] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        volumes.append(
            DiskVolume(
                mount_point=str(item.get("mount_point") or item.get("mountpoint") or ""),
                device=str(item.get("device") or item.get("filesystem") or ""),
                fs_type=str(item.get("fs_type") or item.get("type") or ""),
                device_type=str(item.get("device_type") or ""),
                total_bytes=int(item.get("total") or item.get("size") or 0),
                used_bytes=int(item.get("used") or 0),
                free_bytes=int(item.get("free") or item.get("avail") or 0),
            )
        )
    return tuple(volumes)


def _walk_size_nodes(raw: Any, *, source: str) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            name = node.get("name") or node.get("path") or node.get("label")
            size = node.get("size") or node.get("asize") or node.get("dsize")
            if name is not None and size is not None:
                records.append(
                    EvidenceRecord(
                        source=source,
                        path=str(name),
                        data={"size_bytes": parse_human_size(size), "raw_size": size},
                    )
                )
            for child_key in ("children", "items", "entries"):
                for child in node.get(child_key) or []:
                    visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(raw)
    return records


def parse_dust_json(text: str) -> tuple[EvidenceRecord, ...]:
    cleaned = text.strip()
    # dust may emit progress control chars before JSON.
    start = cleaned.find("{")
    if start > 0:
        cleaned = cleaned[start:]
    return tuple(_walk_size_nodes(json.loads(cleaned or "{}"), source="dust"))


def parse_gdu_text(text: str) -> tuple[EvidenceRecord, ...]:
    records: list[EvidenceRecord] = []
    for line in text.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        records.append(EvidenceRecord(source="gdu", path=parts[1], data={"size_bytes": parse_human_size(parts[0])}))
    return tuple(records)


def parse_dua_text(text: str) -> tuple[EvidenceRecord, ...]:
    records: list[EvidenceRecord] = []
    for line in text.splitlines():
        cleaned = ANSI_RE.sub("", line).strip()
        match = re.match(r"^([0-9]+(?:\.[0-9]+)?\s*[A-Za-z]*)\s+(.+)$", cleaned)
        if not match:
            continue
        records.append(
            EvidenceRecord(
                source="dua",
                path=match.group(2),
                data={"size_bytes": parse_human_size(match.group(1))},
            )
        )
    return tuple(records)


def parse_json_export(text: str, *, source: str) -> tuple[EvidenceRecord, ...]:
    cleaned = text.strip()
    if not cleaned:
        return ()
    return tuple(_walk_size_nodes(json.loads(cleaned), source=source))


def parse_procs_json(text: str) -> tuple[dict[str, Any], ...]:
    cleaned = text.strip()
    if not cleaned:
        return ()
    raw = json.loads(cleaned)
    if isinstance(raw, dict):
        raw = raw.get("processes", [raw])
    return tuple(item for item in raw if isinstance(item, dict))


def run_duf(runner: ToolRunner) -> tuple[DiskVolume, ...]:
    result = runner.run(["duf", "--json"], timeout=15)
    if result.returncode != 0:
        return ()
    return parse_duf_json(result.stdout)


def run_dust(runner: ToolRunner, paths: Iterable[Path], *, depth: int = 3) -> tuple[EvidenceRecord, ...]:
    existing = [str(path) for path in paths if path.exists()]
    if not existing:
        return ()
    result = runner.run(["dust", "-j", "-p", "-n", "80", "-d", str(depth), *existing], timeout=60)
    if result.returncode != 0:
        return (EvidenceRecord(source="dust", warning=result.stderr.strip()),)
    records = list(parse_dust_json(result.stdout))
    return tuple(
        EvidenceRecord(source=record.source, command=result.command, path=record.path, data=record.data, warning=record.warning)
        for record in records
    )


def run_gdu(runner: ToolRunner, path: Path, *, depth: int = 2) -> tuple[EvidenceRecord, ...]:
    if not path.exists():
        return ()
    # On macOS this may be dundee/gdu or GNU du from coreutils; support both.
    help_result = runner.run(["gdu", "--help"], timeout=5)
    if "-o, --output-file" in help_result.stdout:
        result = runner.run(["gdu", "-o-", "--depth", str(depth), str(path)], timeout=60)
        if result.returncode == 0:
            try:
                return parse_json_export(result.stdout, source="gdu")
            except Exception:
                return (EvidenceRecord(source="gdu", command=result.command, warning="gdu JSON parse failed"),)
    result = runner.run(["gdu", "-B1", f"-d{depth}", str(path)], timeout=60)
    if result.returncode != 0:
        return (EvidenceRecord(source="gdu", command=result.command, warning=result.stderr.strip()),)
    return tuple(
        EvidenceRecord(source=record.source, command=result.command, path=record.path, data=record.data)
        for record in parse_gdu_text(result.stdout)
    )


def run_ncdu(runner: ToolRunner, path: Path) -> tuple[EvidenceRecord, ...]:
    if not path.exists():
        return ()
    result = runner.run(["ncdu", "-o", "-", str(path)], timeout=60)
    if result.returncode != 0:
        return (EvidenceRecord(source="ncdu", command=result.command, warning=result.stderr.strip()),)
    try:
        return parse_json_export(result.stdout, source="ncdu")
    except Exception:
        return (EvidenceRecord(source="ncdu", command=result.command, warning="ncdu JSON parse failed"),)


def run_dua(runner: ToolRunner, path: Path) -> tuple[EvidenceRecord, ...]:
    if not path.exists():
        return ()
    result = runner.run(
        ["dua", "aggregate", "--format", "bytes", "--no-total", str(path)],
        timeout=60,
    )
    if result.returncode != 0:
        return (EvidenceRecord(source="dua", command=result.command, warning=result.stderr.strip()),)
    return tuple(
        EvidenceRecord(
            source=record.source,
            command=result.command,
            path=record.path,
            data=record.data,
        )
        for record in parse_dua_text(result.stdout)
    )


def run_procs(runner: ToolRunner, keywords: Iterable[str]) -> tuple[dict[str, Any], ...]:
    args = ["procs", "--json", "--or", *[kw for kw in keywords if kw]]
    result = runner.run(args, timeout=10)
    if result.returncode != 0:
        return ()
    try:
        return parse_procs_json(result.stdout)
    except Exception:
        return ()
