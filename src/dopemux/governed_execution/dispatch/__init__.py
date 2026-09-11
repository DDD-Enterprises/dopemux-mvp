"""W02: derived DispatchQualification join over seven receipt dicts.

Public surface: qualify(), DispatchQualification, Reason, ReceiptInput,
Provenance, JoinInput, Finding, and the receipt/enum name constants.

This package computes authority NONE, is_execution_authority False. It is a
pure derivation over caller-supplied, already-validated receipt dicts: no
file reads, no subprocess, no digesting, no schema validation, no clock.
"""
from __future__ import annotations

from .join import (
    DISPATCH_QUALIFICATION_VALUES,
    DispatchQualification,
    DispatchResult,
    Reason,
    ReasonEffect,
    qualify,
)
from .receipts import (
    RECEIPT_NAMES,
    Effect,
    Finding,
    JoinInput,
    Provenance,
    ReceiptInput,
    ReceiptName,
)

__all__ = [
    "DISPATCH_QUALIFICATION_VALUES",
    "DispatchQualification",
    "DispatchResult",
    "Reason",
    "ReasonEffect",
    "qualify",
    "RECEIPT_NAMES",
    "Effect",
    "Finding",
    "JoinInput",
    "Provenance",
    "ReceiptInput",
    "ReceiptName",
]
