from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "pr_steward"
    / "merge_readiness.schema.json"
)


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_is_valid_draft7():
    Draft7Validator.check_schema(_schema())


def test_security_release_is_required_top_level_key():
    schema = _schema()
    assert "security_release" in schema["required"]


def test_security_release_object_shape():
    schema = _schema()
    props = schema["properties"]["security_release"]["properties"]
    for key in ("required", "approved", "categories", "approval"):
        assert key in props


def test_ready_requires_security_release_satisfied():
    """A hand-crafted READY payload with required=True, approved=False must fail schema."""
    schema = _schema()
    base = _minimal_valid_document()
    base["readiness"] = "READY"
    base["security_release"] = {
        "required": True,
        "approved": False,
        "categories": ["ci_workflow"],
        "approval": None,
    }
    base["blockers"] = []
    base["unknowns"] = []
    errors = list(Draft7Validator(schema).iter_errors(base))
    assert errors, "READY with required=True, approved=False must be schema-invalid"


def _minimal_valid_document() -> dict:
    return {
        "schema_version": "1.1.0",
        "generated_at": "2026-07-20T10:00:00Z",
        "pr": {
            "number": 1,
            "url": "https://example.invalid/pr/1",
            "base_ref": "main",
            "head_ref": "feature",
            "head_sha": "a" * 40,
            "changed_files": [],
            "commits": [],
        },
        "readiness": "NOT_READY",
        "risk_tier": "LOW",
        "review_item_ledger_path": "REVIEW_ITEM_LEDGER.json",
        "thread_dispositions_path": "THREAD_DISPOSITIONS.json",
        "ci_triage_path": "CI_TRIAGE.json",
        "embedded_audit": {"status": "SKIPPED", "report_path": ""},
        "proof": {
            "proof_path": "",
            "proof_head_sha": None,
            "matches_pr_head": False,
            "proof_freshness": {
                "status": "MISSING",
                "matches_pr_head": False,
                "reason": "",
                "proof_recorded_sha": None,
                "pr_head_sha": None,
                "self_reference_exception": None,
            },
        },
        "blockers": [],
        "unknowns": [],
        "mutation_performed": False,
        "security_release": {
            "required": False,
            "approved": False,
            "categories": [],
            "approval": None,
        },
    }
