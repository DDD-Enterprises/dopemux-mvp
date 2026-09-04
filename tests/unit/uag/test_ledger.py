"""Mapping ledger primitive tests."""

from __future__ import annotations

import pytest

from dopemux.uag import CorrelationKind, LedgerEntry, MappingLedger


def _entry(kind: CorrelationKind, left: str, right: str) -> LedgerEntry:
    return LedgerEntry(
        entry_id=f"{left}->{right}",
        kind=kind,
        left_ref=left,
        right_ref=right,
    )


def test_ledger_is_append_only():
    ledger = MappingLedger()
    ledger2 = ledger.add(_entry(CorrelationKind.REQUEST_TO_ATTEMPT, "req-1", "a1"))
    ledger3 = ledger2.add(_entry(CorrelationKind.ATTEMPT_TO_RECEIPT, "a1", "r1"))

    assert len(ledger) == 0
    assert len(ledger2) == 1
    assert len(ledger3) == 2


def test_ledger_has_no_execution_or_approval_surface():
    ledger = MappingLedger().add(
        _entry(CorrelationKind.REQUEST_TO_ATTEMPT, "req-1", "a1")
    )
    for attr in ("execute", "approve", "run", "retry", "fallback", "grant"):
        assert not hasattr(ledger, attr)


def test_ledger_for_kind_filters():
    ledger = MappingLedger()
    ledger = ledger.add(_entry(CorrelationKind.REQUEST_TO_ATTEMPT, "req-1", "a1"))
    ledger = ledger.add(_entry(CorrelationKind.ATTEMPT_TO_RECEIPT, "a1", "r1"))
    assert len(ledger.for_kind(CorrelationKind.REQUEST_TO_ATTEMPT)) == 1
    assert ledger.for_kind(CorrelationKind.REQUEST_TO_ATTEMPT)[0].right_ref == "a1"


def test_empty_refs_rejected():
    with pytest.raises(ValueError):
        LedgerEntry(entry_id="e", kind=CorrelationKind.REQUEST_TO_ATTEMPT, left_ref="", right_ref="x")
