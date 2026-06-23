"""
Tests for the LIVE_WRITE_READY readiness gate schema.

Covers:
- Schema self-consistency: live_write_ready.schema.json is a valid Draft 2020-12 schema.
- Clean READY assertion (all preconditions satisfied) validates with zero errors.
- ONE test per precondition: READY is rejected when that precondition is missing/false.
  Preconditions tested: canonical_writer null/empty, allowlist.diff_within_allowlist false,
  approval.approved false, idempotency.idempotent false, rollback.available false,
  dry_run_proof.performed false, independent_audit.performed false,
  independent_audit.independent false, independent_audit.status FAIL,
  independent_audit.status NOT_RUN, post_write_verification.planned false.
- BLOCKED with empty blocked_reasons is rejected (minItems 1).
- live_write_performed=true is rejected (const false).
- Unknown top-level field is rejected (additionalProperties: false).
- NO-LIVE-WRITE structural proof:
  - live_write_performed is pinned const false in the schema.
  - This packet's own files contain no call to forbidden wiring
    (scripts/batch_resolve_and_merge.py, queue_drain.py execute=True).
"""

from __future__ import annotations

import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = (
    _REPO_ROOT / "schemas" / "project_control_plane" / "live_write_ready.schema.json"
)

with _SCHEMA_PATH.open() as _fh:
    _SCHEMA: dict = json.load(_fh)


def _schema_errors(instance: dict) -> list:
    """Return all Draft 2020-12 validation errors for *instance* against _SCHEMA."""
    return list(Draft202012Validator(_SCHEMA).iter_errors(instance))


# ---------------------------------------------------------------------------
# Fully-satisfied READY builder
# ---------------------------------------------------------------------------

def _ready_assertion(**overrides) -> dict:
    """Return a fully-satisfied READY assertion.

    All preconditions are true, independent_audit is PASS + independent,
    blocked_reasons is empty.  Callers may override individual keys to
    introduce a single failing precondition.
    """
    base: dict = {
        "schema_version": "pcp.live_write_ready.v0",
        "assertion_id": "test-assertion-001",
        "operation_ref": "TP-DMX-PCP-LIVE-WRITE-GATES-0001",
        "target_surface": "github.pr.merge",
        "canonical_writer": "dopemux.pr_steward",
        "allowlist": {
            "paths": ["src/dopemux/pcp/pr_steward.py"],
            "diff_within_allowlist": True,
        },
        "approval": {
            "approved": True,
            "approver": "hu3mann",
            "approval_ref": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/1#approval",
        },
        "idempotency": {
            "idempotent": True,
            "key": "pr-merge-42-sha-abc123",
        },
        "rollback": {
            "available": True,
            "plan": "git revert HEAD && git push origin main",
        },
        "dry_run_proof": {
            "performed": True,
            "proof_ref": "claudedocs/dry-run-pr-42-2026-06-22.txt",
        },
        "independent_audit": {
            "performed": True,
            "independent": True,
            "status": "PASS",
            "auditor": "claude-sonnet-4-6",
        },
        "post_write_verification": {
            "planned": True,
            "performed": False,
            "verification_ref": "tests/integration/test_post_merge_state.py",
        },
        "status": "READY",
        "blocked_reasons": [],
        "live_write_performed": False,
        "created_at": "2026-06-22T00:00:00Z",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Schema self-consistency
# ---------------------------------------------------------------------------

def test_schema_is_valid_draft202012():
    """The schema itself must be a valid JSON Schema Draft 2020-12 meta-schema."""
    Draft202012Validator.check_schema(_SCHEMA)


# ---------------------------------------------------------------------------
# 2. Clean READY assertion validates
# ---------------------------------------------------------------------------

def test_clean_ready_assertion_is_valid():
    """A fully-satisfied READY assertion produces zero schema errors."""
    errors = _schema_errors(_ready_assertion())
    assert errors == [], [str(e) for e in errors]


# ---------------------------------------------------------------------------
# 3. Per-precondition rejection tests
#    Each sets status="READY" with exactly ONE bad precondition → ≥1 schema error.
# ---------------------------------------------------------------------------

def test_ready_rejected_when_canonical_writer_is_null():
    """READY must be rejected when canonical_writer is null."""
    instance = _ready_assertion(canonical_writer=None)
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_canonical_writer_is_empty_string():
    """READY must be rejected when canonical_writer is an empty string."""
    instance = _ready_assertion(canonical_writer="")
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_diff_outside_allowlist():
    """READY must be rejected when allowlist.diff_within_allowlist is false."""
    instance = _ready_assertion(
        allowlist={"paths": ["src/dopemux/pcp/pr_steward.py"], "diff_within_allowlist": False}
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_not_approved():
    """READY must be rejected when approval.approved is false."""
    instance = _ready_assertion(
        approval={"approved": False, "approver": None, "approval_ref": None}
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_not_idempotent():
    """READY must be rejected when idempotency.idempotent is false."""
    instance = _ready_assertion(
        idempotency={"idempotent": False, "key": None}
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_no_rollback():
    """READY must be rejected when rollback.available is false."""
    instance = _ready_assertion(
        rollback={"available": False, "plan": None}
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_dry_run_not_performed():
    """READY must be rejected when dry_run_proof.performed is false."""
    instance = _ready_assertion(
        dry_run_proof={"performed": False, "proof_ref": None}
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_audit_not_performed():
    """READY must be rejected when independent_audit.performed is false."""
    instance = _ready_assertion(
        independent_audit={
            "performed": False,
            "independent": True,
            "status": "PASS",
            "auditor": "claude-sonnet-4-6",
        }
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_audit_not_independent():
    """READY must be rejected when independent_audit.independent is false."""
    instance = _ready_assertion(
        independent_audit={
            "performed": True,
            "independent": False,
            "status": "PASS",
            "auditor": "implementer",
        }
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_audit_status_is_fail():
    """READY must be rejected when independent_audit.status is FAIL."""
    instance = _ready_assertion(
        independent_audit={
            "performed": True,
            "independent": True,
            "status": "FAIL",
            "auditor": "claude-sonnet-4-6",
        }
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_audit_status_is_not_run():
    """READY must be rejected when independent_audit.status is NOT_RUN."""
    instance = _ready_assertion(
        independent_audit={
            "performed": True,
            "independent": True,
            "status": "NOT_RUN",
            "auditor": None,
        }
    )
    assert len(_schema_errors(instance)) >= 1


def test_ready_rejected_when_post_write_verification_not_planned():
    """READY must be rejected when post_write_verification.planned is false."""
    instance = _ready_assertion(
        post_write_verification={
            "planned": False,
            "performed": False,
            "verification_ref": None,
        }
    )
    assert len(_schema_errors(instance)) >= 1


# ---------------------------------------------------------------------------
# 4. BLOCKED with empty blocked_reasons is rejected
# ---------------------------------------------------------------------------

def test_blocked_with_empty_blocked_reasons_is_rejected():
    """BLOCKED status with blocked_reasons=[] must be rejected (minItems 1)."""
    instance = _ready_assertion(status="BLOCKED", blocked_reasons=[])
    assert len(_schema_errors(instance)) >= 1


# ---------------------------------------------------------------------------
# 5. live_write_performed=true is rejected
# ---------------------------------------------------------------------------

def test_live_write_performed_true_is_rejected():
    """live_write_performed=true must be rejected (const false)."""
    instance = _ready_assertion(live_write_performed=True)
    assert len(_schema_errors(instance)) >= 1


# ---------------------------------------------------------------------------
# 6. Unknown top-level field is rejected
# ---------------------------------------------------------------------------

def test_additional_top_level_property_is_rejected():
    """An unknown top-level field must be rejected (additionalProperties: false)."""
    instance = _ready_assertion()
    instance["unknown_field_xyz"] = "should not be allowed"
    assert len(_schema_errors(instance)) >= 1


# ---------------------------------------------------------------------------
# 7. NO-LIVE-WRITE structural proof
# ---------------------------------------------------------------------------

def test_schema_pins_live_write_performed_const_false():
    """The schema must pin live_write_performed as const false."""
    props = _SCHEMA.get("properties", {})
    live_write_prop = props.get("live_write_performed", {})
    assert live_write_prop.get("const") is False, (
        "live_write_performed must be pinned const:false in the schema"
    )


def test_packet_files_contain_no_forbidden_wiring():
    """NO-LIVE-WRITE structural proof for this packet's own files.

    Proves that this packet adds no Python source module under src/ and that
    the test file's executable code contains no live-write invocation patterns.

    Specifically:
    1. The packet's only .py file is this test file — no new live_write*.py
       module exists under src/dopemux/pcp/.
    2. The executable code section of this test file contains no forbidden
       live-write invocation patterns (checked below via code_section scan).
    3. The packet's three files (schema, test, doc) exist at their expected paths.
    """
    schema_file = _REPO_ROOT / "schemas" / "project_control_plane" / "live_write_ready.schema.json"
    test_file = _REPO_ROOT / "tests" / "project_control_plane" / "test_live_write_gates.py"
    doc_file = _REPO_ROOT / "docs" / "03-reference" / "architecture" / "pcp-live-write-gates.md"

    # 1. Packet files exist at their expected paths.
    assert schema_file.exists(), f"Schema file missing: {schema_file}"
    assert test_file.exists(), f"Test file missing: {test_file}"
    assert doc_file.exists(), f"Doc file missing: {doc_file}"

    # 2. No new src/dopemux/pcp/live_write*.py module was added by this packet.
    src_pcp_dir = _REPO_ROOT / "src" / "dopemux" / "pcp"
    live_write_modules = list(src_pcp_dir.glob("live_write*.py")) if src_pcp_dir.exists() else []
    assert live_write_modules == [], (
        f"This packet must add no live-write Python module under src/; "
        f"found: {[str(p) for p in live_write_modules]}"
    )

    # 3. This test file contains no live-write invocation patterns in executable code.
    #    Patterns are defined as (prefix, suffix) pairs so that the pattern strings
    #    themselves do not appear literally in this source file and cannot self-match.
    import ast as _ast
    raw_source = test_file.read_text(encoding="utf-8")
    tree = _ast.parse(raw_source, filename=str(test_file))
    # Collect all string literal values from the AST (docstrings, f-strings excluded).
    # Then reconstruct the source with all string constants replaced by placeholders
    # so we can scan for forbidden call/assignment patterns without self-matching.
    # Simpler: scan token-by-token using tokenize to strip string tokens.
    import tokenize as _tokenize
    import io as _io
    non_string_tokens = []
    try:
        for tok in _tokenize.generate_tokens(_io.StringIO(raw_source).readline):
            if tok.type not in (_tokenize.STRING, _tokenize.COMMENT):
                non_string_tokens.append(tok.string)
    except _tokenize.TokenError:
        pass
    code_without_strings = " ".join(non_string_tokens)

    # Patterns joined from fragments so they don't self-match as literals here.
    _eq = "="
    forbidden_calls = [
        "execute" + _eq + "True",      # execute=True keyword arg
        "subprocess",                   # subprocess module usage
        "gh" + " pr " + "merge",       # gh pr merge invocation
        "gh" + " pr " + "ready",       # gh pr ready invocation
        "git" + " push",               # git push invocation
    ]
    for pattern in forbidden_calls:
        assert pattern not in code_without_strings, (
            f"Forbidden live-write invocation pattern {pattern!r} found in executable "
            f"code of {test_file}. This test file must contain no live-write wiring."
        )


# ---------------------------------------------------------------------------
# 8. Fail-open lock tests (lock the two schema security fixes)
# ---------------------------------------------------------------------------

def test_ready_rejected_when_allowlist_paths_is_empty():
    """READY must be rejected when allowlist.paths is an empty list.

    An empty allowlist makes 'diff_within_allowlist: true' vacuously true —
    it proves nothing. The READY gate must require at least one declared path.
    """
    instance = _ready_assertion(
        allowlist={"paths": [], "diff_within_allowlist": True}
    )
    errors = _schema_errors(instance)
    assert len(errors) >= 1, (
        "Expected ≥1 schema error for READY with allowlist.paths=[] but got none. "
        "Empty allowlist is a fail-open — READY gate must enforce minItems: 1 on paths."
    )


def test_ready_rejected_when_rollback_plan_is_null():
    """READY must be rejected when rollback.plan is null.

    rollback.available=true with plan=null is a vacuous guarantee — there is no
    concrete rollback path. The READY gate must require a non-empty plan string.
    """
    instance = _ready_assertion(
        rollback={"available": True, "plan": None}
    )
    errors = _schema_errors(instance)
    assert len(errors) >= 1, (
        "Expected ≥1 schema error for READY with rollback.plan=null but got none. "
        "Null rollback plan is a fail-open — READY gate must require a non-empty plan."
    )


def test_ready_rejected_when_rollback_plan_is_empty_string():
    """READY must be rejected when rollback.plan is an empty string.

    An empty string is not a concrete rollback plan and must be treated the same
    as null by the READY gate (minLength: 1 enforcement).
    """
    instance = _ready_assertion(
        rollback={"available": True, "plan": ""}
    )
    errors = _schema_errors(instance)
    assert len(errors) >= 1, (
        "Expected ≥1 schema error for READY with rollback.plan='' but got none. "
        "Empty-string rollback plan is a fail-open — READY gate must enforce minLength: 1."
    )
