"""JSON Schema contract tests for the canonical reconciliation schemas.

These prove the committed JSON schemas actually validate the objects they define
(the Codex P2 regression) and that the reconciliation-decision schema matches the
decision/classification strings the resolver code can emit.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "task-orchestrator"
CANONICAL_DATASTORE_SCHEMA = SCHEMA_DIR / "canonical-datastore.schema.json"
RECONCILIATION_DECISION_SCHEMA = SCHEMA_DIR / "reconciliation-decision.schema.json"
COMMITTED_COLDSTART = (
    ROOT
    / "audit_inputs"
    / "task-orchestrator-canon"
    / "to-all-dbs-20260622T192814Z"
    / "COLDSTART_RECONCILIATION.json"
)

# Decision / classification strings reachable in
# tools/task_orchestrator_reconcile/resolve.py::coldstart_report.
CODE_DECISIONS = [
    "accepted_do_not_rerun",
    "remain_active_in_progress",
    "keep_blocked_until_repo_packet_allowlist_exists",
    "operator_only_do_not_automate",
    "do_not_infer_readiness_from_to_role",
]
CODE_CLASSIFICATIONS = [
    "repo_pr_proof_observed",
    "active_root_in_progress",
    "explicit_blocked",
    "operator_gate",
    "queue_only",
    "queue_only_supervisor_required",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _provenance(**overrides) -> dict:
    base = {
        "source_db_slug": "dopemux-mvp-2e346e2084bca021",
        "source_database_path": "/tmp/dopemux/current-tasks.db",
        "source_schema_hash": "abc123",
        "source_table": "DATABASE_INDEX.csv",
        "source_row_id": "dopemux-mvp-2e346e2084bca021",
        "source_mtime_utc": "2026-06-22T00:00:00Z",
        "import_run_id": "to-canon-20260622T192814Z",
        "archive_sha256": "deadbeef",
    }
    base.update(overrides)
    return base


def _datastore_validator() -> Draft202012Validator:
    return Draft202012Validator(_load(CANONICAL_DATASTORE_SCHEMA))


def _subschema_validator(ref: str) -> Draft202012Validator:
    """Validate against a single $defs subschema, with $defs available for $ref
    resolution but WITHOUT the root manifest constraints applying."""
    schema = _load(CANONICAL_DATASTORE_SCHEMA)
    return Draft202012Validator({"$defs": schema["$defs"], "$ref": ref})


def test_schema_files_are_valid_draft_2020_12() -> None:
    for path in (CANONICAL_DATASTORE_SCHEMA, RECONCILIATION_DECISION_SCHEMA):
        schema = _load(path)
        # Raises SchemaError if the schema itself is malformed.
        Draft202012Validator.check_schema(schema)


def test_canonical_datastore_schema_accepts_source_database_extension_fields() -> None:
    source_database = {
        **_provenance(),
        "schema_class": "modern",
        "adjudication_class": "active_current_dopemux",
        "canonical_treatment": "current dopemux workflow-memory source",
    }
    # Validate the composed $defs.source_database directly: it must accept the
    # provenance fields PLUS the allOf extension fields (the Codex P2 failure).
    _subschema_validator("#/$defs/source_database").validate(source_database)


def test_canonical_datastore_schema_accepts_imported_entity_extension_fields() -> None:
    imported_entity = {**_provenance(), "entity_type": "canonical_current_work_item"}
    _subschema_validator("#/$defs/imported_entity").validate(imported_entity)


def test_canonical_datastore_schema_rejects_unexpected_composed_property() -> None:
    bad = {
        **_provenance(),
        "schema_class": "modern",
        "adjudication_class": "active_current_dopemux",
        "canonical_treatment": "current",
        "unexpected_field": "nope",
    }
    with pytest.raises(ValidationError):
        _subschema_validator("#/$defs/source_database").validate(bad)


def test_canonical_datastore_schema_accepts_full_manifest() -> None:
    manifest = {
        "schema_version": "task-orchestrator.canonical-datastore.v0",
        "source_pack": {
            "archive_sha256": "deadbeef",
            "generated_at_utc": "2026-06-22T00:00:00Z",
            "redacted_only": True,
        },
        "source_databases": [
            {
                **_provenance(),
                "schema_class": "modern",
                "adjudication_class": "active_current_dopemux",
                "canonical_treatment": "current",
            }
        ],
        "imported_entities": [
            {**_provenance(), "entity_type": "canonical_current_work_item"}
        ],
        "redaction_policy": {
            "raw_note_bodies": "excluded",
            "fts_rows": "excluded",
            "freeform_descriptions": "redacted_hash_handle",
        },
    }
    _datastore_validator().validate(manifest)


def test_reconciliation_decision_schema_accepts_emitted_coldstart_decisions() -> None:
    schema = _load(RECONCILIATION_DECISION_SCHEMA)
    validator = Draft202012Validator(schema)
    items = [
        {
            "source_row_id": f"row-{i}",
            "title": f"TP-EXAMPLE-{i}",
            "role": "queue",
            "status_label": None,
            "classification": classification,
            "decision": decision,
            "evidence": {"role": "queue"},
        }
        for i, (decision, classification) in enumerate(
            zip(CODE_DECISIONS, CODE_CLASSIFICATIONS)
        )
    ]
    fixture = {
        "schema_version": "task-orchestrator.reconciliation-decision.v0",
        "active_db_slug": "dopemux-mvp-2e346e2084bca021",
        "classification_counts": {c: 1 for c in CODE_CLASSIFICATIONS},
        "items": items,
        "root_decision": "remain_active_in_progress",
        "point_in_time": {
            "valid_as_of_utc": "2026-06-22T19:28:14Z",
            "basis": "test fixture",
        },
    }
    # Every code-reachable decision/classification string must be in the enum.
    validator.validate(fixture)


def test_reconciliation_decision_schema_validates_committed_artifact() -> None:
    if not COMMITTED_COLDSTART.is_file():
        pytest.skip("committed COLDSTART_RECONCILIATION.json not present")
    schema = _load(RECONCILIATION_DECISION_SCHEMA)
    Draft202012Validator(schema).validate(_load(COMMITTED_COLDSTART))
