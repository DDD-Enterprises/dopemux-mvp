#!/usr/bin/env python3
"""
Pre-restart hygiene scanner and quarantine tool for the repo-truth extractor.
TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001

Usage:
    python extraction_hygiene.py scan [--repo-root PATH] [--json]
    python extraction_hygiene.py apply [--repo-root PATH] [--dry-run | --apply]

Scan mode (default, read-only):
    Reports noisy paths, stale run-state artifacts, version/path mismatches,
    and authority tier summary. Safe to run at any time.

Apply mode:
    Archives stale artifacts to extraction/repo-truth-extractor/quarantine/{ts}/.
    Default is --dry-run (no mutations). Pass --apply to execute.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Policy paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT_DEFAULT = _SCRIPT_DIR.parents[1]
_POLICY_PATH = _REPO_ROOT_DEFAULT / "config" / "extraction_hygiene" / "hygiene_policy.yaml"
_TIERS_PATH = _REPO_ROOT_DEFAULT / "config" / "extraction_hygiene" / "authority_tiers.yaml"

# ---------------------------------------------------------------------------
# Logging (grep-friendly tags)
# ---------------------------------------------------------------------------
logging.basicConfig(format="%(message)s", level=logging.INFO)
log = logging.getLogger("extraction_hygiene")


def _log(tag: str, msg: str) -> None:
    log.info(f"{tag}: {msg}")


# ---------------------------------------------------------------------------
# Exclude patterns (mirrors PROMPTGEN_DEFAULT_EXCLUDE_GLOBS in v5 runner,
# plus extraction-specific additions from hygiene_policy.yaml)
# ---------------------------------------------------------------------------
_EXCLUDE_PATTERNS: list[tuple[str, str]] = [
    # (glob_pattern, category)
    ("**/.git/**", "vcs"),
    ("**/__pycache__/**", "build_cache"),
    ("**/__pycache__", "build_cache"),
    ("**/.venv/**", "virtualenv"),
    ("**/.taskx_venv/**", "virtualenv"),
    ("**/.dopetask_venv/**", "virtualenv"),
    ("**/dist/**", "build_artifact"),
    ("**/build/**", "build_artifact"),
    ("htmlcov/**", "test_artifact"),
    ("htmlcov", "test_artifact"),
    ("**/.pytest_cache/**", "test_artifact"),
    ("**/.mypy_cache/**", "test_artifact"),
    ("**/node_modules/**", "vendored_deps"),
    ("**/node_modules", "vendored_deps"),
    ("vendor/**", "vendored_deps"),
    ("**/dist/**", "build_artifact"),
    ("ui-dashboard/dist/**", "build_artifact"),
    ("**/*.png", "binary"),
    ("**/*.jpg", "binary"),
    ("**/*.jpeg", "binary"),
    ("**/*.webp", "binary"),
    ("**/*.gif", "binary"),
    ("**/*.pdf", "binary"),
    ("**/*.zip", "archive"),
    ("**/.DS_Store", "os_artifact"),
    ("extraction/repo-truth-extractor/v3/runs/**", "run_output"),
    ("extraction/repo-truth-extractor/v4/runs/**", "run_output"),
    ("extraction/repo-truth-extractor/v3/doctor/**", "run_output"),
    ("extraction/repo-truth-extractor/v4/doctor/**", "run_output"),
    ("extraction/repo-truth-extractor/quarantine/**", "quarantine"),
    ("extraction/repo-truth-extractor/v5/proofs/**", "proof_bundle"),
    ("proof/**", "proof_bundle"),
    ("reports/**", "generated_report"),
    ("tmp/**", "temp"),
    ("out/**", "temp"),
    ("SYSTEM_ARCHIVE/**", "archive"),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ClassifyResult:
    path: str
    is_excluded: bool
    category: str  # "ok" if not excluded
    pattern: str = ""  # which pattern matched


@dataclass
class VersionPathFinding:
    has_mismatch: bool
    runner_version: str
    output_path: str
    severity: str  # "warn" | "error" | "ok"
    message: str


@dataclass
class ResumeIssue:
    issue_type: str  # "stale_failed" | "orphan_failed" | "blocked_promptset"
    path: Path
    severity: str  # "warn" | "error"
    message: str


@dataclass
class HygieneWarning:
    path: Path
    message: str
    category: str


@dataclass
class ScanResult:
    warnings: List[HygieneWarning] = field(default_factory=list)
    errors: List[HygieneWarning] = field(default_factory=list)
    noise_paths: List[ClassifyResult] = field(default_factory=list)
    version_path_issues: List[VersionPathFinding] = field(default_factory=list)
    resume_state_issues: List[ResumeIssue] = field(default_factory=list)
    authority_summary: dict = field(default_factory=dict)


@dataclass
class PlannedAction:
    action: str  # "move_to_quarantine" | "skip"
    source: Path
    dest: Optional[Path]
    reason: str


@dataclass
class ApplyPlan:
    dry_run: bool
    planned_actions: List[PlannedAction] = field(default_factory=list)
    applied_actions: List[PlannedAction] = field(default_factory=list)
    canonical_sources_mutated: bool = False
    manifest_path: Optional[Path] = None


# ---------------------------------------------------------------------------
# Core classification
# ---------------------------------------------------------------------------

def classify_path(rel_path: str) -> ClassifyResult:
    """Classify a repo-relative path as excluded (with category) or ok."""
    for pattern, category in _EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(rel_path, pattern):
            return ClassifyResult(path=rel_path, is_excluded=True, category=category, pattern=pattern)
        # Also check each path component for non-glob patterns like node_modules
        parts = rel_path.replace("\\", "/").split("/")
        plain = pattern.strip("**/")
        if plain in parts and not any(c in plain for c in ("*", "?")):
            return ClassifyResult(path=rel_path, is_excluded=True, category=category, pattern=pattern)
    return ClassifyResult(path=rel_path, is_excluded=False, category="ok")


# ---------------------------------------------------------------------------
# Authority classification
# ---------------------------------------------------------------------------

# Rules applied top-to-bottom; first match wins.
_AUTHORITY_RULES: list[tuple[str, str]] = [
    # generated — highest-specificity patterns first
    ("extraction/repo-truth-extractor/v3/runs/", "generated"),
    ("extraction/repo-truth-extractor/v4/runs/", "generated"),
    ("extraction/repo-truth-extractor/v5/proofs/", "generated"),
    ("extraction/repo-truth-extractor/quarantine/", "generated"),
    ("proof/", "generated"),
    ("tmp/", "generated"),
    ("out/", "generated"),
    ("SYSTEM_ARCHIVE/", "generated"),
    ("htmlcov/", "generated"),
    # status_audit (before generic reports/ which is also status_audit)
    ("repo-truth-pack/", "status_audit"),
    ("review_artifacts/", "status_audit"),
    ("docs/05-audit-reports/", "status_audit"),
    ("reports/", "status_audit"),
    # roadmap_speculative
    ("UPGRADES/", "roadmap_speculative"),
    ("docs/archive/", "roadmap_speculative"),
    ("task-packets/", "roadmap_speculative"),
    ("contracts/", "roadmap_speculative"),
    ("docs/91-rfc/", "roadmap_speculative"),
    # reference
    ("docs/03-reference/", "reference"),
    ("docs/02-how-to/", "reference"),
    ("docs/04-explanation/", "reference"),
    ("docs/01-tutorials/", "reference"),
    ("docs/", "reference"),  # catch-all for other docs/ paths
]

_AUTHORITY_FILENAME_RULES: list[tuple[str, str]] = [
    ("AUDIT_*.md", "status_audit"),
    ("AUDIT_*.json", "status_audit"),
    ("CHANGELOG.md", "reference"),
    # README.md is reference only when inside a subdirectory;
    # root-level README.md falls through to canonical (handled at end of classify_authority)
]

_AUTHORITY_CONTAINS: list[tuple[str, str]] = [
    ("__pycache__", "generated"),
    ("node_modules", "generated"),
    (".venv", "generated"),
    ("/.git/", "generated"),
    ("/dist/", "generated"),
    ("vendor/", "generated"),  # vendor prefix or /vendor/ anywhere
]


def classify_authority(rel_path: str) -> str:
    """Return the authority tier for a repo-relative path."""
    norm = rel_path.replace("\\", "/")

    # Contains checks (highest priority — generated paths contain noise markers)
    for substring, tier in _AUTHORITY_CONTAINS:
        if substring in norm:
            return tier

    # Path prefix checks (order matters — more specific first)
    for prefix, tier in _AUTHORITY_RULES:
        if norm.startswith(prefix):
            return tier

    # Filename pattern checks (always applied)
    filename = norm.split("/")[-1]
    has_parent = "/" in norm
    for pattern, tier in _AUTHORITY_FILENAME_RULES:
        if fnmatch.fnmatch(filename, pattern):
            return tier

    # README.md and CHANGELOG.md are reference in subdirectories, canonical at root
    if has_parent and filename in ("README.md", "CHANGELOG.md"):
        return "reference"

    return "canonical"


# ---------------------------------------------------------------------------
# Version/path check
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r"run_extraction_v(\d+)\.py$")
_V5_CONST_RE = re.compile(r'V5_EXTRACTION_ROOT\s*=\s*(?:Path\()?["\']([^"\']+)["\']')
_V3_CONST_RE = re.compile(r'V3_EXTRACTION_ROOT\s*=\s*(?:Path\()?["\']([^"\']+)["\']')


def check_version_path(
    runner_path: Path,
    repo_root: Path,
    override_output_path: Optional[str] = None,
) -> VersionPathFinding:
    """Detect version/path mismatch in the runner."""
    m = _VERSION_RE.search(str(runner_path))
    runner_version = f"v{m.group(1)}" if m else "unknown"

    # Determine the output path the runner writes to
    output_path = override_output_path
    if output_path is None:
        # Try multiple candidate root locations
        candidates = [
            repo_root / runner_path,
            Path.cwd() / runner_path,
            runner_path if runner_path.is_absolute() else None,
            _REPO_ROOT_DEFAULT / runner_path,
        ]
        content: Optional[str] = None
        for candidate in candidates:
            if candidate is not None and candidate.exists():
                try:
                    content = candidate.read_text(errors="replace")
                    break
                except OSError:
                    pass

        if content is not None:
            # Try V5 first (new convention), then V3 (legacy)
            cm = _V5_CONST_RE.search(content)
            if cm is None:
                cm = _V3_CONST_RE.search(content)
            output_path = cm.group(1) if cm else "unknown"
        else:
            # Cannot find runner — infer as matching (no mismatch to report)
            output_path = f"extraction/repo-truth-extractor/{runner_version}"

    # Check mismatch: runner claims vN but output_path contains a different vM
    path_version_m = re.search(r"/v(\d+)", output_path or "")
    path_version = f"v{path_version_m.group(1)}" if path_version_m else "unknown"

    has_mismatch = runner_version != path_version and runner_version != "unknown" and path_version != "unknown"
    severity = "warn" if has_mismatch else "ok"
    if has_mismatch:
        msg = (
            f"VERSION_PATH_MISMATCH: runner is {runner_version} but output root is "
            f"'{output_path}' ({path_version}). "
            "This is intentional for resume compatibility. "
            f"To migrate to a {runner_version} output path, create a separate task packet."
        )
    else:
        msg = f"Version and path are aligned: runner={runner_version}, output={output_path}"

    return VersionPathFinding(
        has_mismatch=has_mismatch,
        runner_version=runner_version,
        output_path=output_path or "",
        severity=severity,
        message=msg,
    )


# ---------------------------------------------------------------------------
# Resume-state scan
# ---------------------------------------------------------------------------

def scan_resume_state(run_dirs: List[Path]) -> List[ResumeIssue]:
    """Scan run directories for resume-state hazards."""
    issues: List[ResumeIssue] = []

    for run_dir in run_dirs:
        if not run_dir.is_dir():
            continue

        # Scan RESUME_PROOF.json
        proof_path = run_dir / "RESUME_PROOF.json"
        if proof_path.exists():
            try:
                data = json.loads(proof_path.read_text())
                if data.get("blocked_promptset"):
                    issues.append(ResumeIssue(
                        issue_type="blocked_promptset",
                        path=proof_path,
                        severity="warn",
                        message=f"HYGIENE_WARN: {proof_path} has blocked_promptset=true — do not resume from this run",
                    ))
            except (json.JSONDecodeError, OSError):
                pass

        # Scan for FAILED sidecars vs success files
        for failed_file in run_dir.rglob("*.FAILED.*"):
            # Derive the corresponding success file path
            name = failed_file.name
            # Pattern: STEP__PART.FAILED.json → STEP__PART.json
            success_name = re.sub(r"\.FAILED\.[^.]+$", ".json", name)
            if not success_name or success_name == name:
                continue
            success_path = failed_file.parent / success_name

            if not success_path.exists():
                issues.append(ResumeIssue(
                    issue_type="orphan_failed",
                    path=failed_file,
                    severity="warn",
                    message=f"HYGIENE_WARN: orphan FAILED sidecar with no corresponding success: {failed_file}",
                ))
            else:
                # Stale: failed file is older than success
                if failed_file.stat().st_mtime < success_path.stat().st_mtime:
                    issues.append(ResumeIssue(
                        issue_type="stale_failed",
                        path=failed_file,
                        severity="warn",
                        message=f"HYGIENE_WARN: stale FAILED sidecar (older than success): {failed_file}",
                    ))

    return issues


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

_DEFAULT_RUNNER = Path("services/repo-truth-extractor/run_extraction_v5.py")


def run_scan(
    repo_root: Path = _REPO_ROOT_DEFAULT,
    run_dirs: Optional[List[Path]] = None,
) -> ScanResult:
    """Read-only scan. Returns a ScanResult with all findings."""
    result = ScanResult()
    _log("HYGIENE_SCAN_START", f"repo_root={repo_root}")

    # --- noise-path detection: walk the tree and flag excluded paths ---
    noise_found: list[ClassifyResult] = []
    try:
        for p in repo_root.rglob("*"):
            rel = str(p.relative_to(repo_root))
            cr = classify_path(rel)
            if cr.is_excluded and cr.category in ("vendored_deps", "os_artifact"):
                noise_found.append(cr)
                result.warnings.append(HygieneWarning(
                    path=p,
                    message=f"HYGIENE_WARN: excluded path found: {rel} (category={cr.category})",
                    category=cr.category,
                ))
    except PermissionError:
        pass
    result.noise_paths = noise_found

    # --- version/path check ---
    runner = repo_root / _DEFAULT_RUNNER
    if runner.exists():
        finding = check_version_path(runner_path=_DEFAULT_RUNNER, repo_root=repo_root)
        if finding.has_mismatch:
            result.version_path_issues.append(finding)
            result.warnings.append(HygieneWarning(
                path=runner,
                message=finding.message,
                category="version_path",
            ))
            _log("VERSION_PATH_MISMATCH", finding.message)

    # --- resume-state scan ---
    if run_dirs is None:
        v3_runs = repo_root / "extraction/repo-truth-extractor/v3/runs"
        run_dirs = list(v3_runs.iterdir()) if v3_runs.is_dir() else []
    resume_issues = scan_resume_state(run_dirs)
    result.resume_state_issues = resume_issues
    for issue in resume_issues:
        if issue.severity == "error":
            result.errors.append(HygieneWarning(
                path=issue.path, message=issue.message, category=issue.issue_type
            ))
        else:
            result.warnings.append(HygieneWarning(
                path=issue.path, message=issue.message, category=issue.issue_type
            ))

    # --- authority classification summary ---
    tier_counts: dict[str, int] = {
        "canonical": 0,
        "reference": 0,
        "status_audit": 0,
        "roadmap_speculative": 0,
        "generated": 0,
    }
    try:
        for p in repo_root.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(repo_root))
                tier = classify_authority(rel)
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
    except PermissionError:
        pass
    result.authority_summary = tier_counts
    _log("AUTHORITY_CLASSIFICATION_SUMMARY", str(tier_counts))

    _log(
        "HYGIENE_SCAN_RESULT",
        f"warnings={len(result.warnings)} errors={len(result.errors)} "
        f"noise_paths={len(result.noise_paths)} "
        f"version_path_issues={len(result.version_path_issues)} "
        f"resume_state_issues={len(result.resume_state_issues)}",
    )
    return result


# ---------------------------------------------------------------------------
# Apply / quarantine
# ---------------------------------------------------------------------------

_CANONICAL_PROTECTED_PATTERNS = [
    "compose.yml",
    "pyproject.toml",
    "dopemux.toml",
    "README.md",
    "INSTALL.md",
    "QUICK_START.md",
    "AGENTS.md",
    "CHANGELOG.md",
]
_CANONICAL_PROTECTED_PREFIXES = [
    "src/",
    ".claude/",
    ".github/",
    "config/",
    "services/",
    "docker/",
    "compose/",
    "scripts/",
    "tools/",
]


def _is_canonical_protected(rel_path: str) -> bool:
    """Return True if this path must never be touched by cleanup."""
    norm = rel_path.replace("\\", "/")
    filename = norm.split("/")[-1]
    if filename in _CANONICAL_PROTECTED_PATTERNS:
        return True
    for prefix in _CANONICAL_PROTECTED_PREFIXES:
        if norm.startswith(prefix):
            return True
    return False


def run_apply(
    repo_root: Path = _REPO_ROOT_DEFAULT,
    dry_run: bool = True,
) -> ApplyPlan:
    """
    Apply hygiene cleanup. dry_run=True (default) reports but makes no changes.
    dry_run=False moves stale artifacts to quarantine and writes a manifest.
    """
    plan = ApplyPlan(dry_run=dry_run)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    quarantine_root = repo_root / "extraction/repo-truth-extractor/quarantine" / timestamp

    candidates: list[tuple[Path, str]] = []  # (path, reason)

    # 1. Stale FAILED sidecars in extraction tree
    for version in ("v3", "v4"):
        runs_root = repo_root / f"extraction/repo-truth-extractor/{version}/runs"
        if not runs_root.is_dir():
            continue
        for failed_file in runs_root.rglob("*.FAILED.*"):
            name = failed_file.name
            success_name = re.sub(r"\.FAILED\.[^.]+$", ".json", name)
            if not success_name or success_name == name:
                continue
            success_path = failed_file.parent / success_name
            if success_path.exists() and failed_file.stat().st_mtime < success_path.stat().st_mtime:
                candidates.append((failed_file, "stale_failed_sidecar"))

    # 2. .DS_Store files in the extraction tree
    for ds in (repo_root / "extraction").rglob(".DS_Store"):
        candidates.append((ds, "ds_store_in_extraction_tree"))

    # 3. .zip files in extraction run directories (not source zips)
    for version in ("v3", "v4"):
        runs_root = repo_root / f"extraction/repo-truth-extractor/{version}/runs"
        if runs_root.is_dir():
            for zf in runs_root.rglob("*.zip"):
                candidates.append((zf, "zip_in_run_dir"))

    # Build planned actions
    for src, reason in candidates:
        rel = str(src.relative_to(repo_root))
        if _is_canonical_protected(rel):
            continue  # safety guard — should never happen, but explicit
        dest = quarantine_root / src.relative_to(repo_root)
        plan.planned_actions.append(PlannedAction(
            action="move_to_quarantine",
            source=src,
            dest=dest,
            reason=reason,
        ))

    if dry_run:
        return plan

    # Execute
    moved_items = []
    for action in plan.planned_actions:
        if action.action == "move_to_quarantine" and action.source.exists():
            action.dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(action.source), str(action.dest))
            plan.applied_actions.append(action)
            moved_items.append({
                "source": str(action.source),
                "dest": str(action.dest),
                "reason": action.reason,
            })
            _log("HYGIENE_QUARANTINE", f"moved {action.source} → {action.dest}")

    if moved_items:
        quarantine_root.mkdir(parents=True, exist_ok=True)
        manifest_path = quarantine_root / "ARCHIVE_MANIFEST.json"
        manifest = {
            "timestamp": timestamp,
            "dry_run": False,
            "moved_items": moved_items,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))
        plan.manifest_path = manifest_path
        _log("HYGIENE_ARCHIVE_MANIFEST_WRITTEN", str(manifest_path))

    return plan


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pre-restart hygiene scanner for the repo-truth extractor."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT_DEFAULT,
        help="Path to the repository root (default: auto-detected)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Read-only preflight scan")
    scan_p.add_argument("--json", action="store_true", help="Output results as JSON")

    apply_p = sub.add_parser("apply", help="Quarantine stale artifacts")
    apply_p.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Report what would be done (default)",
    )
    apply_p.add_argument(
        "--apply",
        dest="dry_run",
        action="store_false",
        help="Execute quarantine actions",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        result = run_scan(repo_root=args.repo_root)
        if getattr(args, "json", False):
            print(json.dumps({
                "warnings": len(result.warnings),
                "errors": len(result.errors),
                "noise_paths": len(result.noise_paths),
                "version_path_issues": len(result.version_path_issues),
                "resume_state_issues": len(result.resume_state_issues),
                "authority_summary": result.authority_summary,
            }, indent=2))
        else:
            _print_scan_report(result)
        return 1 if result.errors else 0

    elif args.command == "apply":
        plan = run_apply(repo_root=args.repo_root, dry_run=args.dry_run)
        mode = "DRY-RUN" if plan.dry_run else "APPLY"
        print(f"\n[{mode}] Planned actions: {len(plan.planned_actions)}")
        for action in plan.planned_actions[:20]:
            print(f"  {action.action}: {action.source} ({action.reason})")
        if not plan.dry_run:
            print(f"[APPLY] Applied: {len(plan.applied_actions)} actions")
            if plan.manifest_path:
                print(f"[APPLY] Manifest: {plan.manifest_path}")
        return 0

    return 0


def _print_scan_report(result: ScanResult) -> None:
    print("\n" + "=" * 60)
    print("HYGIENE SCAN REPORT")
    print("=" * 60)
    if result.version_path_issues:
        print("\n[VERSION/PATH]")
        for f in result.version_path_issues:
            print(f"  {f.severity.upper()}: {f.message}")
    if result.noise_paths:
        print(f"\n[NOISE PATHS] {len(result.noise_paths)} found")
        for cr in result.noise_paths[:10]:
            print(f"  {cr.category}: {cr.path}")
    if result.resume_state_issues:
        print(f"\n[RESUME STATE] {len(result.resume_state_issues)} issues")
        for issue in result.resume_state_issues[:10]:
            print(f"  {issue.severity}: {issue.issue_type} — {issue.path}")
    print(f"\n[AUTHORITY SUMMARY]")
    for tier, count in sorted(result.authority_summary.items()):
        print(f"  {tier}: {count}")
    print(f"\nTotal warnings: {len(result.warnings)}, errors: {len(result.errors)}")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
