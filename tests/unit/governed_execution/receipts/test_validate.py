"""Tests for dopemux.governed_execution.receipts.validate.

Reuses the read-only fixtures under
tests/governance/governed_execution/fixtures/{valid,invalid}/ (owned by W01;
never modified here) as the ground truth for what each receipt kind accepts
and rejects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dopemux.governed_execution.receipts.validate import (
    Provenance,
    ReceiptInvalid,
    UnknownReceiptKind,
    validate_receipt,
)

# tests/unit/governed_execution/receipts/test_validate.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[4]
_FIXTURES_DIR = _REPO_ROOT / "tests" / "governance" / "governed_execution" / "fixtures"
_VALID_DIR = _FIXTURES_DIR / "valid"
_INVALID_DIR = _FIXTURES_DIR / "invalid"

_PROVENANCE = Provenance(
    verified_by="tests/unit/governed_execution/receipts/test_validate.py",
    verified_at="2026-09-11T00:00:00Z",
    schema_set_digest="0" * 64,
)


def _kind_for(path: Path) -> str:
    # valid fixtures: <schema-shortname>.json or <schema-shortname>__<variant>.json
    # invalid fixtures: <schema-shortname>__<reason>.json
    return path.stem.split("__", 1)[0]


def _valid_fixtures() -> list[Path]:
    return sorted(_VALID_DIR.glob("*.json"))


def _invalid_fixtures() -> list[Path]:
    return sorted(_INVALID_DIR.glob("*.json"))


@pytest.mark.parametrize("path", _valid_fixtures(), ids=lambda p: p.name)
def test_valid_fixture_round_trips(path: Path) -> None:
    kind = _kind_for(path)
    raw = path.read_bytes()
    validated = validate_receipt(kind, raw, _PROVENANCE)
    assert validated.kind == kind
    assert validated.payload["schema_version"].endswith(kind)
    assert len(validated.sha256) == 64
    assert validated.provenance == _PROVENANCE


# finality_receipt.v1__audited_head_ne_finality_head.json is schema-valid: a
# JSON Schema cannot compare two sibling string fields for equality
# (docs/03-reference/governance/governed-execution-contract-v2.md, "Exact-head
# rule"). It is an intentionally invalid fixture only at the semantic layer,
# which is W04's own SubjectMismatch check in freeze/finality.py
# (test_finality_subject_binding.py), not the schema-validation boundary
# tested here.
_SCHEMA_VALID_BUT_SEMANTICALLY_INVALID = {
    "finality_receipt.v1__audited_head_ne_finality_head.json",
}


@pytest.mark.parametrize(
    "path",
    [p for p in _invalid_fixtures() if p.name not in _SCHEMA_VALID_BUT_SEMANTICALLY_INVALID],
    ids=lambda p: p.name,
)
def test_invalid_fixture_raises_receipt_invalid(path: Path) -> None:
    kind = _kind_for(path)
    raw = path.read_bytes()
    with pytest.raises(ReceiptInvalid) as excinfo:
        validate_receipt(kind, raw, _PROVENANCE)
    assert excinfo.value.kind == kind
    assert excinfo.value.errors


def test_exact_head_equality_fixture_is_schema_valid_not_receipt_invalid() -> None:
    """The one invalid fixture whose defect the schema cannot express.

    validate_receipt only enforces schema shape, so this fixture round-trips
    here; the semantic exact-head rule is enforced by
    freeze/finality.py::author_finality_receipt (SubjectMismatch).
    """
    path = _INVALID_DIR / "finality_receipt.v1__audited_head_ne_finality_head.json"
    validated = validate_receipt("finality_receipt.v1", path.read_bytes(), _PROVENANCE)
    assert validated.payload["audited_head"] != validated.payload["finality_head"]


def test_provenance_is_carried() -> None:
    path = _VALID_DIR / "freeze_receipt.v1.json"
    validated = validate_receipt("freeze_receipt.v1", path.read_bytes(), _PROVENANCE)
    assert validated.provenance is _PROVENANCE
    assert validated.provenance.verified_by == _PROVENANCE.verified_by
    assert validated.provenance.schema_set_digest == "0" * 64


def test_unknown_kind_raises() -> None:
    with pytest.raises(UnknownReceiptKind):
        validate_receipt("not_a_real_kind.v1", b'{"schema_version": "x"}', _PROVENANCE)


def test_not_json_raises_receipt_invalid() -> None:
    with pytest.raises(ReceiptInvalid):
        validate_receipt("freeze_receipt.v1", b"not json at all", _PROVENANCE)
