"""
PCP Negative Trap Runner (Packet 4.5).

Executes a set of fail-closed "negative traps" against the PCP exporter and
emits a failure-index artifact that validates against
schemas/project_control_plane/negative_case_result.schema.json.

The key invariant is ``executed: true`` in every case — these traps are RUN,
not merely asserted.  The schema enforces this with ``"executed": {"const": true}``.

Usage (standalone)::

    python -m dopemux.pcp.negative_cases

Or from Python::

    from dopemux.pcp.negative_cases import run_negative_traps, write_result
    result = run_negative_traps()
    write_result("reports/project-control-plane/validation/NEGATIVE_TRAPS_RESULT.json")
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile

from jsonschema import Draft202012Validator

from ._schemas import load_schema

# ---------------------------------------------------------------------------
# Schemas — loaded from bundled package data (dopemux.pcp._schemas) so the
# validators are available both from the source tree and from an installed
# wheel. No repo-root-relative path is assumed.
# ---------------------------------------------------------------------------
_SCHEMA: dict = load_schema("negative_case_result.schema.json")
_EVIDENCE_SCHEMA: dict = load_schema("project_evidence_export.schema.json")

_VALIDATOR = Draft202012Validator(_SCHEMA)
_EVIDENCE_VALIDATOR = Draft202012Validator(_EVIDENCE_SCHEMA)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git_init_with_commit(path: pathlib.Path) -> str:
    """Init a throwaway git repo with one commit.  Returns HEAD sha."""

    def _g(*args: str) -> None:
        subprocess.check_call(
            ["git", "-C", str(path), *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    _g("init")
    _g("config", "user.email", "trap@example.com")
    _g("config", "user.name", "Trap User")
    (path / "README.md").write_text("# trap repo\n")
    _g("add", "README.md")
    _g("commit", "-m", "Initial commit")
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


# ---------------------------------------------------------------------------
# Individual traps
# ---------------------------------------------------------------------------

def _trap_non_git_dir() -> dict:
    """Trap (a): call export_evidence on a plain directory — expect ValueError."""
    from dopemux.pcp.exporter import export_evidence  # local import avoids circular

    with tempfile.TemporaryDirectory() as tmp:
        try:
            export_evidence(tmp)
            outcome = "No exception raised — ValueError expected"
            result = "FAIL"
        except ValueError as exc:
            outcome = f"ValueError: {exc}"
            result = "PASS"
        except Exception as exc:  # noqa: BLE001
            outcome = f"Unexpected {type(exc).__name__}: {exc}"
            result = "FAIL"

    return {
        "name": "non_git_dir",
        "category": "discovery",
        "scenario": "Call export_evidence on a plain directory with no .git",
        "expectation": "ValueError raised (not a Git repository)",
        "executed": True,
        "outcome": outcome,
        "result": result,
    }


def _trap_no_commit_repo() -> dict:
    """Trap (b): git init a dir with no commit — export_evidence must raise ValueError."""
    from dopemux.pcp.exporter import export_evidence

    with tempfile.TemporaryDirectory() as tmp:
        try:
            subprocess.check_call(
                ["git", "-C", tmp, "init"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.check_call(
                ["git", "-C", tmp, "config", "user.email", "trap@example.com"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.check_call(
                ["git", "-C", tmp, "config", "user.name", "Trap"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            export_evidence(tmp)
            outcome = "No exception raised — ValueError expected (no commits)"
            result = "FAIL"
        except ValueError as exc:
            outcome = f"ValueError: {exc}"
            result = "PASS"
        except Exception as exc:  # noqa: BLE001
            outcome = f"Unexpected {type(exc).__name__}: {exc}"
            result = "FAIL"

    return {
        "name": "no_commit_repo",
        "category": "discovery",
        "scenario": "git init a directory but make no commits, then call export_evidence",
        "expectation": "ValueError raised (no commits — head_sha unavailable)",
        "executed": True,
        "outcome": outcome,
        "result": result,
    }


def _trap_runtime_missing_head_sha() -> dict:
    """Trap (c): validate an instance where generated_from_fixture=false and head_sha=null.

    The project_evidence_export schema's allOf gate must reject this.
    """
    bad_instance = {
        "schema_version": "pcp.project_evidence_export.v0",
        "project_id": "trap/test",
        "generated_from_fixture": False,
        "profile_ref": "reports/x/y.json",
        "repo_state": {
            "root_verified": True,
            "worktree_state": "CLEAN",
            "head_sha": None,   # ← null: violates runtime gate
            "branch": None,
        },
        "authority_docs": [],
        "active_packet": {"state": "ABSENT", "packet_id": None, "path": None},
        "status_ledger": {"state": "ABSENT", "path": None, "entries": []},
        "proof_manifest": {"state": "ABSENT", "path": None, "freshness": "UNKNOWN"},
        "workflow_list": [],
        "pr_review_state": {
            "state": "ABSENT",
            "authority_allowed": False,
            "open_prs": [],
        },
        "red_lane_results": [],
        "unknowns": [],
        "dirty_state": {"state": "CLEAN", "paths": []},
        "forbidden_action_confirmation": {
            "external_workflow_written": False,
            "external_runner_executed": False,
            "github_mutated": False,
            "runtime_written": False,
        },
    }
    errors = list(_EVIDENCE_VALIDATOR.iter_errors(bad_instance))
    if errors:
        outcome = f"{len(errors)} validation error(s): {errors[0].message[:120]}"
        result = "PASS"
    else:
        outcome = "Instance validated without errors — runtime head_sha gate did NOT fire"
        result = "FAIL"

    return {
        "name": "runtime_missing_head_sha",
        "category": "schema-gate",
        "scenario": "Validate project_evidence_export instance with generated_from_fixture=false and repo_state.head_sha=null",
        "expectation": "Schema rejects: allOf runtime head_sha gate fires (null is not valid string)",
        "executed": True,
        "outcome": outcome,
        "result": result,
    }


def _trap_old_dopemux_field() -> dict:
    """Trap (d): validate an instance using the old key ``dopetask_executed``.

    The schema only permits the de-Dopemuxed keys; old keys must be rejected.
    """
    bad_instance = {
        "schema_version": "pcp.project_evidence_export.v0",
        "project_id": "trap/test",
        "generated_from_fixture": True,   # fixture=true so head_sha gate doesn't fire
        "profile_ref": "reports/x/y.json",
        "repo_state": {
            "root_verified": True,
            "worktree_state": "CLEAN",
            "head_sha": None,
            "branch": None,
        },
        "authority_docs": [],
        "active_packet": {"state": "ABSENT", "packet_id": None, "path": None},
        "status_ledger": {"state": "ABSENT", "path": None, "entries": []},
        "proof_manifest": {"state": "ABSENT", "path": None, "freshness": "UNKNOWN"},
        "workflow_list": [],
        "pr_review_state": {
            "state": "ABSENT",
            "authority_allowed": False,
            "open_prs": [],
        },
        "red_lane_results": [],
        "unknowns": [],
        "dirty_state": {"state": "CLEAN", "paths": []},
        "forbidden_action_confirmation": {
            # OLD forbidden keys — should be rejected by additionalProperties:false
            "dopetask_executed": False,
            "live_task_orchestrator_written": False,
        },
    }
    errors = list(_EVIDENCE_VALIDATOR.iter_errors(bad_instance))
    if errors:
        # Look for additionalProperties error on forbidden_action_confirmation
        relevant = [
            e for e in errors
            if "dopetask_executed" in str(e.message)
            or "additional" in e.message.lower()
        ]
        if relevant:
            outcome = f"Rejected (additionalProperties): {relevant[0].message[:120]}"
        else:
            outcome = f"Rejected ({len(errors)} errors): {errors[0].message[:120]}"
        result = "PASS"
    else:
        outcome = "Instance validated without errors — old dopetask_executed field NOT rejected"
        result = "FAIL"

    return {
        "name": "old_dopemux_field",
        "category": "de-dopemux",
        "scenario": "Validate project_evidence_export instance whose forbidden_action_confirmation uses old key dopetask_executed",
        "expectation": "Schema rejects due to additionalProperties:false on forbidden_action_confirmation",
        "executed": True,
        "outcome": outcome,
        "result": result,
    }


def _trap_secret_content_no_leak() -> dict:
    """Trap (e): the exporter must NOT include file CONTENT in its JSON output.

    Build a repo whose committed file contains a known marker string, run
    export_evidence, serialise to JSON, and confirm the marker is absent.
    """
    from dopemux.pcp.exporter import export_evidence

    SECRET_MARKER = "TRAP_SECRET_A7B3C9D2E5F1"  # fixed, unique literal

    with tempfile.TemporaryDirectory() as tmp:
        # Create a repo with a file containing the secret marker
        _git_init_with_commit(
            pathlib.Path(tmp)  # creates README.md first
        )
        secret_file = pathlib.Path(tmp) / "secrets.txt"
        secret_file.write_text(f"top secret\n{SECRET_MARKER}\nend\n")

        # Stage and commit the secret file
        subprocess.check_call(
            ["git", "-C", tmp, "add", "secrets.txt"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        subprocess.check_call(
            ["git", "-C", tmp, "commit", "-m", "Add secret file"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        try:
            export = export_evidence(tmp)
            serialized = json.dumps(export)
            if SECRET_MARKER in serialized:
                outcome = f"SECRET LEAKED — marker '{SECRET_MARKER}' found in export JSON"
                result = "FAIL"
            else:
                outcome = (
                    f"Marker '{SECRET_MARKER}' absent from export JSON "
                    f"({len(serialized)} chars); exporter records paths only"
                )
                result = "PASS"
        except Exception as exc:  # noqa: BLE001
            outcome = f"Unexpected {type(exc).__name__} during export: {exc}"
            result = "FAIL"

    return {
        "name": "secret_content_no_leak",
        "category": "secret-safety",
        "scenario": "Commit a file containing a unique marker to a tmp repo; run export_evidence; check the JSON",
        "expectation": "Secret marker absent from export JSON (exporter records paths, not content)",
        "executed": True,
        "outcome": outcome,
        "result": result,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_negative_traps() -> dict:
    """Execute all negative traps and return a validated result dict.

    Each trap is actually RUN (not asserted from static data).  The returned
    dict validates against ``negative_case_result.schema.json`` — the schema
    is validated before returning; a ``ValueError`` is raised on failure.

    Returns
    -------
    dict
        Validated negative-case result with ``executed: true`` on every case.

    Raises
    ------
    ValueError
        If the produced result does not satisfy the schema.
    """
    trap_runners = [
        _trap_non_git_dir,
        _trap_no_commit_repo,
        _trap_runtime_missing_head_sha,
        _trap_old_dopemux_field,
        _trap_secret_content_no_leak,
    ]

    cases = [runner() for runner in trap_runners]

    total = len(cases)
    passed = sum(1 for c in cases if c["result"] == "PASS")
    failed = sum(1 for c in cases if c["result"] == "FAIL")

    result: dict = {
        "schema_version": "pcp.negative_case_result.v0",
        "generated_from_fixture": False,
        "total": total,
        "passed": passed,
        "failed": failed,
        "cases": cases,
    }

    # Defensive schema validation before returning.
    errors = list(_VALIDATOR.iter_errors(result))
    if errors:
        messages = "; ".join(str(e.message) for e in errors[:5])
        raise ValueError(
            f"Produced negative-case result does not satisfy the schema: {messages}"
        )

    return result


def write_result(path: str | pathlib.Path) -> dict:
    """Run all negative traps and write the JSON artifact to *path*.

    Parameters
    ----------
    path:
        Destination file path.  Parent directories must exist.

    Returns
    -------
    dict
        The validated result dict (same value written to *path*).
    """
    result = run_negative_traps()
    dest = pathlib.Path(path)
    dest.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(run_negative_traps(), indent=2))
