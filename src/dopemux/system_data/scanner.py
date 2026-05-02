"""Storage scanner built on required external tools."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .classifier import classify_path
from .models import EvidenceRecord, Finding, RISK_PRIORITY, ScanResult
from .platform_macos import build_environment
from .tools import (
    ToolError,
    ToolRunner,
    run_dua,
    run_dust,
    run_gdu,
    run_ncdu,
    run_procs,
)


def candidate_paths(home: Path) -> tuple[Path, ...]:
    library = home / "Library"
    return (
        library / "Containers" / "com.apple.MobileSMS" / "Data" / "tmp",
        library / "Messages" / "Caches" / "Previews",
        library / "Caches" / "CloudKit",
        library / "Caches",
        library / "Messages" / "Attachments",
        library / "Containers" / "com.docker.docker",
        home / ".docker",
        library / "Developer" / "Xcode" / "DerivedData",
        library / "Developer" / "Xcode" / "Archives",
        library / "Application Support" / "MobileSync" / "Backup",
        library / "Developer" / "CoreSimulator",
        library / "Developer" / "CoreSimulator" / "Profiles" / "Runtimes",
        home / "Downloads",
        home / ".npm",
        library / "Caches" / "Yarn",
        library / "Caches" / "pip",
        library / "Caches" / "pypoetry",
        home / ".cache" / "uv",
        home / ".cargo",
        home / ".gradle",
        home / ".m2",
        library / "Caches" / "Homebrew",
    )


def _stable_id(path: str, category: str) -> str:
    digest = hashlib.sha256(f"{category}:{path}".encode("utf-8")).hexdigest()[:12]
    return f"{category}-{digest}"


def _evidence_size(evidence: EvidenceRecord) -> int:
    try:
        return int(evidence.data.get("size_bytes", 0))
    except Exception:
        return 0


def _is_under(path: str, root: Path) -> bool:
    root_text = str(root).rstrip("/")
    path_text = str(Path(path)).rstrip("/")
    return path_text == root_text or path_text.startswith(root_text + "/")


def _records_for_root(
    root: Path, evidence_by_path: dict[str, list[EvidenceRecord]]
) -> tuple[EvidenceRecord, ...]:
    records: list[EvidenceRecord] = []
    for path, path_records in evidence_by_path.items():
        if _is_under(path, root):
            records.extend(path_records)
    return tuple(records)


def _root_size(root: Path, records: tuple[EvidenceRecord, ...]) -> int:
    root_text = str(root).rstrip("/")
    exact = [
        _evidence_size(record)
        for record in records
        if record.path and str(Path(record.path)).rstrip("/") == root_text
    ]
    if exact:
        return max(exact)
    return max((_evidence_size(record) for record in records), default=0)


def _warning(source: str, text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    denied = [
        line
        for line in lines
        if (
            "Operation not permitted" in line
            or "PermissionDenied" in line
            or "Permission denied" in line
        )
    ]
    if denied:
        return (
            f"{source}: {len(denied)} permission-limited paths hidden; "
            "grant Full Disk Access for deeper visibility"
        )
    if len(lines) > 3:
        return f"{source}: {' | '.join(lines[:3])} | ... ({len(lines)} lines)"
    return f"{source}: {' | '.join(lines)}"


def _finding_from_evidence(
    path: str, size_bytes: int, evidence: tuple[EvidenceRecord, ...]
) -> Finding:
    risk, mode, action, rationale, apps = classify_path(Path(path))
    estimate = size_bytes if mode in {"delete", "tool"} and risk != "review_first" else 0
    category = action.replace("_", "-")
    return Finding(
        finding_id=_stable_id(path, category),
        category=category,
        path=path,
        size_bytes=size_bytes,
        kind="directory",
        risk_level=risk,
        reclaim_mode=mode,
        reclaim_estimate_bytes=estimate,
        same_volume_quarantine_effective=False,
        recommended_action=action,
        requires_app_quit=apps,
        rationale=rationale,
        evidence=evidence,
    )


def scan(home: Path, runner: ToolRunner | None = None) -> ScanResult:
    runner = runner or ToolRunner()
    tool_report = runner.require_tools()
    environment = build_environment(home, runner)
    if environment.platform != "Darwin":
        raise ToolError("unsupported platform: system-data is macOS-only")
    paths = tuple(path for path in candidate_paths(home) if path.exists())
    warnings = list(environment.warnings)

    evidence_by_path: dict[str, list[EvidenceRecord]] = {}
    for record in run_dust(runner, paths):
        if record.warning:
            warnings.append(_warning("dust", record.warning))
            continue
        if record.path:
            evidence_by_path.setdefault(record.path, []).append(record)

    # Deepen evidence for large or important roots.
    for root in paths:
        if any(
            token in str(root)
            for token in (
                "Developer",
                "Messages",
                "Caches",
                ".npm",
                ".cargo",
                ".gradle",
                ".m2",
            )
        ):
            for record in run_gdu(runner, root):
                if record.warning:
                    warnings.append(_warning("gdu", record.warning))
                elif record.path:
                    evidence_by_path.setdefault(record.path, []).append(record)
            for record in run_dua(runner, root):
                if record.warning:
                    warnings.append(_warning("dua", record.warning))
                elif record.path:
                    evidence_by_path.setdefault(record.path, []).append(record)

    # ncdu is intentionally reserved for review-first broad roots.
    for root in (home / "Library" / "Messages" / "Attachments", home / "Downloads"):
        for record in run_ncdu(runner, root):
            if record.warning:
                warnings.append(_warning("ncdu", record.warning))
            elif record.path:
                evidence_by_path.setdefault(record.path, []).append(record)

    process_evidence = run_procs(
        runner,
        (
            "Messages",
            "Xcode",
            "Simulator",
            "Docker",
            "backupd",
            "npm",
            "yarn",
            "pip",
            "cargo",
            "gradle",
            "mvn",
        ),
    )
    if process_evidence:
        warnings.append(
            f"process preconditions observed: {len(process_evidence)} matching rows from procs"
        )

    findings: list[Finding] = []
    for root in paths:
        records = _records_for_root(root, evidence_by_path)
        size_bytes = _root_size(root, records)
        if size_bytes <= 0:
            continue
        findings.append(_finding_from_evidence(str(root), size_bytes, records))

    findings.sort(
        key=lambda item: (
            RISK_PRIORITY.get(item.risk_level, 99),
            -item.reclaim_estimate_bytes,
            item.path,
        )
    )
    return ScanResult(
        tool_report=tool_report,
        environment=environment,
        findings=tuple(findings),
        warnings=tuple(sorted(set(warnings))),
        processes=process_evidence,
    )
