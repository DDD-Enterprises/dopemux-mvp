"""Stage 0–1: Welcome screen and repository health checks."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from dopemux.console import console

from .display import render_educational_panel, render_health_check, render_welcome_panel
from .stages import StageResult, StageStatus, WizardState


def run_welcome(state: WizardState) -> StageResult:
    """Stage 0 — Welcome banner and basic system checks."""
    checks: list[tuple[str, bool, str]] = []

    # Python version
    py_ver = platform.python_version()
    py_ok = sys.version_info >= (3, 11)
    checks.append(("Python ≥ 3.11", py_ok, f"v{py_ver}"))

    # Git available
    try:
        git_result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=5
        )
        git_ver = git_result.stdout.strip().replace("git version ", "")
        checks.append(("Git available", True, git_ver))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        checks.append(("Git available", False, "not found"))

    # Key Python packages
    for pkg in ("click", "rich", "questionary"):
        try:
            __import__(pkg)
            checks.append((f"{pkg} installed", True, ""))
        except ImportError:
            checks.append((f"{pkg} installed", False, "missing"))

    render_health_check(checks)

    all_ok = all(passed for _, passed, _ in checks)
    return StageResult(
        status=StageStatus.COMPLETED if all_ok else StageStatus.COMPLETED,
        message="System checks passed" if all_ok else "Some checks had warnings",
        data={"checks": [(l, p, d) for l, p, d in checks]},
    )


def run_repo_health(state: WizardState) -> StageResult:
    """Stage 1 — Repository health: branch, clean state, root detection."""
    checks: list[tuple[str, bool, str]] = []

    # Repo root
    try:
        root_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, cwd=str(state.repo_root),
        )
        if root_result.returncode == 0:
            detected_root = Path(root_result.stdout.strip())
            state.repo_root = detected_root
            checks.append(("Repository root", True, str(detected_root)))
        else:
            checks.append(("Repository root", False, "not a git repo"))
            return StageResult(status=StageStatus.FAILED, message="Not inside a git repository")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        checks.append(("Repository root", False, "git not available"))
        return StageResult(status=StageStatus.FAILED, message="Git not available")

    # Current branch
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(state.repo_root),
        )
        branch = branch_result.stdout.strip()
        state.git_branch = branch
        is_main = branch in ("main", "master")
        checks.append((
            "Branch",
            is_main,
            f"{branch}" + ("" if is_main else " (recommend main)"),
        ))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        checks.append(("Branch", False, "unknown"))

    # Working tree clean
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10, cwd=str(state.repo_root),
        )
        changed_lines = [l for l in status_result.stdout.strip().splitlines() if l.strip()]
        state.git_clean = len(changed_lines) == 0
        if state.git_clean:
            checks.append(("Working tree", True, "clean"))
        else:
            checks.append(("Working tree", False, f"{len(changed_lines)} changed file(s)"))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        checks.append(("Working tree", False, "unknown"))

    # Prescan script exists
    prescan_script = state.repo_root / "scripts" / "doc_audit_prescan.py"
    checks.append(("Prescan script", prescan_script.exists(), str(prescan_script.relative_to(state.repo_root))))

    render_health_check(checks)

    # Show welcome panel now that we have branch info
    render_welcome_panel(state)

    if state.educate_mode:
        render_educational_panel(
            "Why check repo health?",
            "Extraction results are most reliable when run against a clean main branch.\n"
            "Uncommitted changes may cause inconsistencies between the prescan corpus\n"
            "and the actual extraction. The wizard will continue with warnings if needed.",
        )

    failures = [l for l, p, _ in checks if not p and l == "Repository root"]
    return StageResult(
        status=StageStatus.FAILED if failures else StageStatus.COMPLETED,
        message="Repository health verified",
        data={"branch": state.git_branch, "clean": state.git_clean},
    )
