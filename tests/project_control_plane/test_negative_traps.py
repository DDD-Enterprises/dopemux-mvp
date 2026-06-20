"""
Tests for PCP Packet 4.5 — Executed Negative Traps.

Validates:
- negative_case_result.schema.json is itself a valid JSON Schema (meta-validate).
- run_negative_traps() output validates against the schema (zero errors).
- Every case has executed==True and result=="PASS".
- total == passed and failed == 0.
- The committed NEGATIVE_TRAPS_RESULT.json loads + validates against the schema.

All tests are skipped gracefully when the ``git`` executable is unavailable.
"""

from __future__ import annotations

import json
import pathlib
import shutil

import pytest
from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for

# ---------------------------------------------------------------------------
# Paths — repo-root-relative, resolved from this file's location.
# tests/project_control_plane/test_*.py → 3 levels up = repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = (
    _REPO_ROOT
    / "schemas"
    / "project_control_plane"
    / "negative_case_result.schema.json"
)
_ARTIFACT_PATH = (
    _REPO_ROOT
    / "reports"
    / "project-control-plane"
    / "validation"
    / "NEGATIVE_TRAPS_RESULT.json"
)

with _SCHEMA_PATH.open() as _fh:
    _SCHEMA: dict = json.load(_fh)

# ---------------------------------------------------------------------------
# Skip guard — silently skip the whole module if git is unavailable.
# ---------------------------------------------------------------------------
_GIT_AVAILABLE = shutil.which("git") is not None
pytestmark = pytest.mark.skipif(
    not _GIT_AVAILABLE,
    reason="git executable not found; skipping negative-traps tests",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _schema_errors(instance: dict, schema: dict | None = None) -> list:
    """Return a list of Draft202012Validator errors for *instance*."""
    if schema is None:
        schema = _SCHEMA
    return list(Draft202012Validator(schema).iter_errors(instance))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNegativeCaseResultSchemaMeta:
    """The schema file itself must be a valid JSON Schema (draft 2020-12)."""

    def test_schema_is_valid_json_schema(self) -> None:
        """Meta-validate negative_case_result.schema.json."""
        validator_cls = validator_for(_SCHEMA)
        validator_cls.check_schema(_SCHEMA)  # raises SchemaError on invalid schema


class TestRunNegativeTrapsOutput:
    """run_negative_traps() must return a fully valid, all-PASS result."""

    def test_validates_against_schema(self) -> None:
        from dopemux.pcp.negative_cases import run_negative_traps

        result = run_negative_traps()
        errors = _schema_errors(result)
        assert errors == [], (
            f"run_negative_traps() output has {len(errors)} schema error(s): "
            + "; ".join(str(e.message) for e in errors)
        )

    def test_every_case_executed_true(self) -> None:
        from dopemux.pcp.negative_cases import run_negative_traps

        result = run_negative_traps()
        not_executed = [c["name"] for c in result["cases"] if c.get("executed") is not True]
        assert not_executed == [], f"Cases with executed != True: {not_executed}"

    def test_every_case_result_pass(self) -> None:
        from dopemux.pcp.negative_cases import run_negative_traps

        result = run_negative_traps()
        failing = [c["name"] for c in result["cases"] if c["result"] != "PASS"]
        assert failing == [], (
            f"Cases that did not PASS: {failing}\n"
            + "\n".join(
                f"  {c['name']}: {c['outcome']}"
                for c in result["cases"]
                if c["result"] != "PASS"
            )
        )

    def test_total_equals_passed_and_failed_zero(self) -> None:
        from dopemux.pcp.negative_cases import run_negative_traps

        result = run_negative_traps()
        assert result["failed"] == 0, f"failed={result['failed']}"
        assert result["total"] == result["passed"], (
            f"total={result['total']} != passed={result['passed']}"
        )


class TestCommittedArtifact:
    """The committed NEGATIVE_TRAPS_RESULT.json must exist and validate."""

    def test_artifact_file_exists(self) -> None:
        assert _ARTIFACT_PATH.exists(), (
            f"NEGATIVE_TRAPS_RESULT.json not found at {_ARTIFACT_PATH}"
        )

    def test_artifact_is_valid_json(self) -> None:
        with _ARTIFACT_PATH.open() as fh:
            data = json.load(fh)
        assert isinstance(data, dict)

    def test_artifact_validates_against_schema(self) -> None:
        with _ARTIFACT_PATH.open() as fh:
            data = json.load(fh)
        errors = _schema_errors(data)
        assert errors == [], (
            f"Committed artifact has {len(errors)} schema error(s): "
            + "; ".join(str(e.message) for e in errors)
        )

    def test_artifact_all_cases_pass(self) -> None:
        with _ARTIFACT_PATH.open() as fh:
            data = json.load(fh)
        failing = [c["name"] for c in data.get("cases", []) if c.get("result") != "PASS"]
        assert failing == [], f"Failing cases in committed artifact: {failing}"

    def test_artifact_failed_count_zero(self) -> None:
        with _ARTIFACT_PATH.open() as fh:
            data = json.load(fh)
        assert data["failed"] == 0
        assert data["total"] == data["passed"]
