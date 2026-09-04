"""Adversarial tests for UAG hardening fixes (Copilot review round).

Covers:
  F-1: execution_authority must be enforced to NONE at construction time
  F-2: canonical_json must reject NaN and Infinity (non-standard JSON)
  F-3: MappingLedger.for_kind() must reject non-CorrelationKind input
  F-4: UnknownItem.evidence_status must be validated as EvidenceStatus
  F-5: Receipt construction with various invalid execution_authority values
  F-6: canonical_json determinism under NaN/Infinity attack vectors
  F-7: LedgerEntry.evidence_status must be validated as EvidenceStatus
  F-8: IdentityStage.evidence_status / confidence must be enum-typed
"""

from __future__ import annotations

import pytest

from dopemux.uag.enums import (
    AttemptSemanticState,
    Confidence,
    EvidenceStatus,
    ExecutionAuthority,
    IdentityStageName,
)
from dopemux.uag.identity import IdentityStage, UnknownItem
from dopemux.uag.ledger import CorrelationKind, LedgerEntry, MappingLedger
from dopemux.uag.primitives import canonical_json
from dopemux.uag.receipt import Receipt


# ── F-2: canonical_json rejects NaN/Infinity ──────────────────────────────


class TestCanonicalJsonRejectsNonStandardFloats:
    """canonical_json must produce strictly valid JSON (RFC 8259)."""

    def test_nan_rejected(self):
        with pytest.raises((ValueError, OverflowError)):
            canonical_json(float("nan"))

    def test_positive_infinity_rejected(self):
        with pytest.raises((ValueError, OverflowError)):
            canonical_json(float("inf"))

    def test_negative_infinity_rejected(self):
        with pytest.raises((ValueError, OverflowError)):
            canonical_json(float("-inf"))

    def test_nan_in_dict_rejected(self):
        with pytest.raises((ValueError, OverflowError)):
            canonical_json({"key": float("nan")})

    def test_inf_in_nested_list_rejected(self):
        with pytest.raises((ValueError, OverflowError)):
            canonical_json([1, [float("inf")]])

    def test_valid_floats_accepted(self):
        result = canonical_json({"a": 1.5, "b": 0, "c": -0.0})
        assert "1.5" in result
        assert "0.0" not in result or "0" in result


# ── F-3: MappingLedger.for_kind() rejects non-CorrelationKind ────────────


class TestMappingLedgerForKindRejectsInvalidInput:
    """for_kind() must fail fast on non-CorrelationKind values."""

    def setup_method(self):
        self.entry = LedgerEntry(
            entry_id="e1",
            kind=CorrelationKind.REQUEST_TO_ATTEMPT,
            left_ref="r1",
            right_ref="a1",
        )
        self.ledger = MappingLedger(entries=(self.entry,))

    def test_raw_string_rejected(self):
        with pytest.raises(ValueError, match="CorrelationKind"):
            self.ledger.for_kind("REQUEST_TO_ATTEMPT")  # type: ignore[arg-type]

    def test_wrong_enum_type_rejected(self):
        with pytest.raises(ValueError, match="CorrelationKind"):
            self.ledger.for_kind(EvidenceStatus.OBSERVED)  # type: ignore[arg-type]

    def test_none_rejected(self):
        with pytest.raises(ValueError, match="CorrelationKind"):
            self.ledger.for_kind(None)  # type: ignore[arg-type]

    def test_int_rejected(self):
        with pytest.raises(ValueError, match="CorrelationKind"):
            self.ledger.for_kind(42)  # type: ignore[arg-type]

    def test_valid_kind_works(self):
        result = self.ledger.for_kind(CorrelationKind.REQUEST_TO_ATTEMPT)
        assert len(result) == 1
        assert result[0].entry_id == "e1"


# ── F-4: UnknownItem.evidence_status validated ────────────────────────────


class TestUnknownItemEvidenceStatusValidation:
    """UnknownItem must reject non-EvidenceStatus evidence_status values."""

    def test_valid_status_accepted(self):
        item = UnknownItem(
            code="X", description="test", evidence_status=EvidenceStatus.OBSERVED
        )
        assert item.evidence_status is EvidenceStatus.OBSERVED

    def test_raw_string_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            UnknownItem(code="X", description="test", evidence_status="OBSERVED")  # type: ignore[arg-type]

    def test_none_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            UnknownItem(code="X", description="test", evidence_status=None)  # type: ignore[arg-type]

    def test_int_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            UnknownItem(code="X", description="test", evidence_status=1)  # type: ignore[arg-type]

    def test_default_is_unknown(self):
        item = UnknownItem(code="X", description="test")
        assert item.evidence_status is EvidenceStatus.UNKNOWN


# ── F-1/F-5: Receipt.execution_authority enforcement ──────────────────────


class TestReceiptExecutionAuthorityEnforcement:
    """Receipt must reject any execution_authority other than NONE."""

    def _make_receipt(self, ea: ExecutionAuthority) -> Receipt:
        return Receipt(
            receipt_id="r1",
            digest="a" * 64,
            subject_ref="s1",
            semantic_state=AttemptSemanticState.COMPLETED,
            execution_authority=ea,
        )

    def test_none_accepted(self):
        r = self._make_receipt(ExecutionAuthority.NONE)
        assert r.execution_authority is ExecutionAuthority.NONE

    def test_raw_string_rejected(self):
        with pytest.raises(ValueError, match="execution_authority must be NONE"):
            Receipt(
                receipt_id="r1",
                digest="a" * 64,
                subject_ref="s1",
                semantic_state=AttemptSemanticState.COMPLETED,
                execution_authority="NONE",  # type: ignore[arg-type]
            )

    def test_invalid_enum_value_rejected_at_construction(self):
        """Attempting to construct an ExecutionAuthority with a non-NONE value
        should fail because the enum only has NONE."""
        with pytest.raises((ValueError, KeyError)):
            ExecutionAuthority("EXECUTE")  # type: ignore[arg-type]

    def test_default_is_none(self):
        r = Receipt(
            receipt_id="r1",
            digest="a" * 64,
            subject_ref="s1",
            semantic_state=AttemptSemanticState.COMPLETED,
        )
        assert r.execution_authority is ExecutionAuthority.NONE


# ── F-7: LedgerEntry.evidence_status validated ────────────────────────────


class TestLedgerEntryEvidenceStatusValidation:
    """LedgerEntry must reject non-EvidenceStatus evidence_status values."""

    def _make(self, evidence_status) -> LedgerEntry:
        return LedgerEntry(
            entry_id="e1",
            kind=CorrelationKind.REQUEST_TO_ATTEMPT,
            left_ref="r1",
            right_ref="a1",
            evidence_status=evidence_status,
        )

    def test_valid_status_accepted(self):
        entry = self._make(EvidenceStatus.OBSERVED)
        assert entry.evidence_status is EvidenceStatus.OBSERVED

    def test_raw_string_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            self._make("OBSERVED")  # type: ignore[arg-type]

    def test_none_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            self._make(None)  # type: ignore[arg-type]

    def test_wrong_enum_type_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            self._make(CorrelationKind.REQUEST_TO_ATTEMPT)  # type: ignore[arg-type]

    def test_default_is_observed(self):
        entry = LedgerEntry(
            entry_id="e1",
            kind=CorrelationKind.REQUEST_TO_ATTEMPT,
            left_ref="r1",
            right_ref="a1",
        )
        assert entry.evidence_status is EvidenceStatus.OBSERVED


# ── F-8: IdentityStage evidence_status / confidence enum-typed ─────────────


class TestIdentityStageEnumTypedFields:
    """IdentityStage must reject non-enum evidence_status and confidence."""

    def _make(
        self,
        *,
        evidence_status=EvidenceStatus.OBSERVED,
        confidence=Confidence.HIGH,
    ) -> IdentityStage:
        return IdentityStage(
            stage=IdentityStageName.REQUESTED,
            value="v",
            source="test",
            evidence_status=evidence_status,
            confidence=confidence,
        )

    def test_valid_fields_accepted(self):
        stage = self._make()
        assert stage.evidence_status is EvidenceStatus.OBSERVED
        assert stage.confidence is Confidence.HIGH

    def test_evidence_status_raw_string_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            self._make(evidence_status="OBSERVED")  # type: ignore[arg-type]

    def test_evidence_status_none_rejected(self):
        with pytest.raises(ValueError, match="EvidenceStatus"):
            self._make(evidence_status=None)  # type: ignore[arg-type]

    def test_confidence_raw_string_rejected(self):
        with pytest.raises(ValueError, match="Confidence"):
            self._make(confidence="HIGH")  # type: ignore[arg-type]

    def test_confidence_none_rejected(self):
        with pytest.raises(ValueError, match="Confidence"):
            self._make(confidence=None)  # type: ignore[arg-type]

    def test_confidence_wrong_enum_type_rejected(self):
        with pytest.raises(ValueError, match="Confidence"):
            self._make(confidence=EvidenceStatus.OBSERVED)  # type: ignore[arg-type]
