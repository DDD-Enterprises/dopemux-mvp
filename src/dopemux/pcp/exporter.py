"""
Generic PCP evidence exporter.

Inspects an arbitrary Git repository (read-only, no network, no mutations) and
returns a dict that validates against
schemas/project_control_plane/project_evidence_export.schema.json.

Works on any Git repo with no named systems (no Dopemux / dNh / Task-Orchestrator
required).  The produced export always sets ``generated_from_fixture=False`` and
captures a real ``head_sha`` from the target repo.

Usage::

    from dopemux.pcp.exporter import export_evidence
    result = export_evidence("/path/to/repo")
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
from typing import Any

from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Schema location — resolved relative to the repo root at import time so the
# validator is available even when the package is imported from any CWD.
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve()
_SCHEMA_REL = pathlib.Path("schemas") / "project_control_plane" / "project_evidence_export.schema.json"
_VALIDATOR: Draft202012Validator | None = None


def _schema_candidates() -> list[pathlib.Path]:
    return [
        _HERE.parents[3] / _SCHEMA_REL,
        _HERE.parent / "schemas" / "project_evidence_export.schema.json",
    ]


def _load_validator() -> Draft202012Validator:
    global _VALIDATOR
    if _VALIDATOR is not None:
        return _VALIDATOR
    for candidate in _schema_candidates():
        if candidate.is_file():
            with candidate.open() as fh:
                schema = json.load(fh)
            _VALIDATOR = Draft202012Validator(schema)
            return _VALIDATOR
    raise FileNotFoundError(
        "project_evidence_export schema not found; checked: "
        + ", ".join(str(p) for p in _schema_candidates())
    )

# Authority doc filenames probed in every repo (generic, order preserved).
_AUTHORITY_DOC_NAMES = ["AGENTS.md", "RULES.md", "CLAUDE.md"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: str) -> str:
    """Run a read-only git subcommand and return stripped stdout.

    Hardened for inspecting arbitrary / untrusted repositories: no shell, a
    sanitized environment (all GIT_* redirection vars stripped, pager and
    terminal prompts disabled), optional locks off, and ``core.fsmonitor=false``
    so a hostile repo config cannot make git spawn an external helper.

    Raises ``subprocess.CalledProcessError`` on non-zero exit.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_PAGER"] = "cat"
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        ["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", cwd, *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return result.stdout.strip()


def _derive_project_id(repo_root: str) -> str:
    """Derive a project identifier from the remote origin URL or directory name."""
    try:
        url = _git(["config", "--get", "remote.origin.url"], cwd=repo_root)
        if url:
            # Strip trailing .git, then grab the last two path components as
            # "owner/repo" when the URL has that shape.
            url = re.sub(r"\.git$", "", url)
            parts = re.split(r"[/:]+", url)
            parts = [p for p in parts if p]
            if len(parts) >= 2:
                return "/".join(parts[-2:])
            if parts:
                return parts[-1]
    except subprocess.CalledProcessError:
        pass
    # Fall back to the directory basename.
    return pathlib.Path(repo_root).name


def _probe_authority_docs(repo_root: str) -> list[dict]:
    """Return a list of {path, state} entries for well-known authority docs."""
    entries = []
    for name in _AUTHORITY_DOC_NAMES:
        full = pathlib.Path(repo_root) / name
        state = "PRESENT" if full.exists() else "ABSENT"
        entries.append({"path": name, "state": state})
    return entries


def _porcelain_paths(porcelain_output: str) -> list[str]:
    """Parse ``git status --porcelain -z`` (NUL-delimited) into affected paths.

    NUL framing avoids the quoting / space / newline pitfalls of line parsing.
    For rename/copy entries git emits the status record (``XY <new>``) followed by
    a bare ``<old>`` record; both are real paths and are returned.
    """
    paths = []
    for record in porcelain_output.split("\0"):
        if not record:
            continue
        # "XY <path>" status records have a space at index 2; bare records
        # (rename/copy origins) are a path on their own.
        if len(record) >= 3 and record[2] == " ":
            paths.append(record[3:])
        else:
            paths.append(record)
    return paths


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_evidence(repo_path: str | os.PathLike = ".") -> dict:
    """Inspect *repo_path* and return a PCP evidence export dict.

    The returned dict validates against
    ``schemas/project_control_plane/project_evidence_export.schema.json``.

    Parameters
    ----------
    repo_path:
        Path to the Git repository to inspect.  Defaults to the current
        working directory.  Must be a directory containing an initialised Git
        repository with at least one commit.

    Returns
    -------
    dict
        Evidence export with ``generated_from_fixture=False`` and a real
        ``repo_state.head_sha``.

    Raises
    ------
    ValueError
        If *repo_path* is not a Git repository or has no commits.
    jsonschema.ValidationError
        If the produced dict does not satisfy the schema (defensive; should not
        occur in normal operation).
    """
    cwd = str(pathlib.Path(repo_path).resolve())

    # ------------------------------------------------------------------
    # 1. Resolve repo root.
    # ------------------------------------------------------------------
    try:
        repo_root = _git(["rev-parse", "--show-toplevel"], cwd=cwd)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise ValueError(
            f"Not a Git repository (or git is unavailable): {cwd!r}"
        ) from exc

    # ------------------------------------------------------------------
    # 2. Capture HEAD sha (fails on repos with no commits).
    # ------------------------------------------------------------------
    try:
        head_sha = _git(["rev-parse", "HEAD"], cwd=repo_root)
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"Git repository at {repo_root!r} has no commits — "
            "a real head_sha cannot be captured."
        ) from exc

    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head_sha):
        raise ValueError(
            f"Unexpected head_sha format from git rev-parse HEAD: {head_sha!r}"
        )

    # ------------------------------------------------------------------
    # 3. Branch (detached HEAD → null).
    # ------------------------------------------------------------------
    try:
        branch_raw = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
        branch: str | None = None if branch_raw == "HEAD" else branch_raw
    except subprocess.CalledProcessError:
        branch = None

    # ------------------------------------------------------------------
    # 4. Worktree / dirty state.
    # ------------------------------------------------------------------
    try:
        porcelain = _git(["status", "--porcelain", "-z"], cwd=repo_root)
    except subprocess.CalledProcessError:
        porcelain = ""

    changed_paths = _porcelain_paths(porcelain)
    is_dirty = bool(changed_paths)
    worktree_state = "DIRTY" if is_dirty else "CLEAN"

    # ------------------------------------------------------------------
    # 5. Project identifier.
    # ------------------------------------------------------------------
    project_id = _derive_project_id(repo_root)

    # ------------------------------------------------------------------
    # 6. Assemble the evidence export.
    # ------------------------------------------------------------------
    evidence: dict[str, Any] = {
        "schema_version": "pcp.project_evidence_export.v0",
        "project_id": project_id,
        "generated_from_fixture": False,
        "profile_ref": f"reports/project-control-plane/{project_id}/project_profile.json",
        "repo_state": {
            "root_verified": True,
            "worktree_state": worktree_state,
            "head_sha": head_sha,
            "branch": branch,
        },
        "authority_docs": _probe_authority_docs(repo_root),
        "active_packet": {
            "state": "ABSENT",
            "packet_id": None,
            "path": None,
        },
        "status_ledger": {
            "state": "ABSENT",
            "path": None,
            "entries": [],
        },
        "proof_manifest": {
            "state": "ABSENT",
            "path": None,
            "freshness": "UNKNOWN",
        },
        "workflow_list": [],
        "pr_review_state": {
            "state": "ABSENT",
            "authority_allowed": False,
            "open_prs": [],
        },
        "red_lane_results": [],
        "unknowns": [
            {
                "field": "profile_ref",
                "reason": (
                    "Generic exporter cannot locate a project profile document "
                    "without named system integration."
                ),
                "result": "UNKNOWN",
            },
            {
                "field": "status_ledger",
                "reason": (
                    "No status ledger discovered; no named systems present "
                    "in this generic repo export."
                ),
                "result": "UNKNOWN",
            },
            {
                "field": "proof_manifest",
                "reason": (
                    "No proof manifest discovered; proof freshness cannot be "
                    "assessed without named system integration."
                ),
                "result": "UNKNOWN",
            },
            {
                "field": "pr_review_state",
                "reason": (
                    "PR review state requires network access or a named CI/CD "
                    "integration; read-only generic exporter omits it."
                ),
                "result": "UNKNOWN",
            },
        ],
        "dirty_state": {
            "state": worktree_state,
            "paths": changed_paths,
        },
        "forbidden_action_confirmation": {
            "external_runner_executed": False,
            "external_workflow_written": False,
            "github_mutated": False,
            "runtime_written": False,
        },
    }

    # ------------------------------------------------------------------
    # 7. Defensive schema validation before returning.
    # ------------------------------------------------------------------
    errors = list(_load_validator().iter_errors(evidence))
    if errors:
        messages = "; ".join(str(e.message) for e in errors[:5])
        raise ValueError(
            f"Produced evidence export does not satisfy the schema: {messages}"
        )

    return evidence
