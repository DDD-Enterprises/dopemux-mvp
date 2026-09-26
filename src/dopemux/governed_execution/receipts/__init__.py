"""Receipt validation boundary and evidence store for the Governed Execution
Contract (W04 of MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001).
"""

from __future__ import annotations

from dopemux.governed_execution.receipts.store import (
    EvidenceRef,
    EvidenceStore,
    ImmutabilityViolation,
    ValidationRef,
)
from dopemux.governed_execution.receipts.validate import (
    DEFAULT_SCHEMA_DIR,
    Provenance,
    ReceiptInvalid,
    UnknownReceiptKind,
    ValidatedReceipt,
    load_registry,
    validate_receipt,
)

__all__ = [
    "DEFAULT_SCHEMA_DIR",
    "EvidenceRef",
    "EvidenceStore",
    "ImmutabilityViolation",
    "Provenance",
    "ReceiptInvalid",
    "UnknownReceiptKind",
    "ValidatedReceipt",
    "ValidationRef",
    "load_registry",
    "validate_receipt",
]
