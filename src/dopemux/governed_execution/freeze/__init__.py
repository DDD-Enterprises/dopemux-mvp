"""FreezeReceipt / FinalityReceipt authoring and the freeze lifecycle state
machine (W04 of MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001).
"""

from __future__ import annotations

from dopemux.governed_execution.freeze.finality import (
    AuditReceiptRef,
    SubjectMismatch,
    author_finality_receipt,
)
from dopemux.governed_execution.freeze.lifecycle import (
    AuditBeforeFreeze,
    FreezeLifecycle,
    FreezeState,
    IllegalTransition,
    NewFreeze,
    RepairRecorded,
    Revalidated,
    ReviewSettled,
    Unfreeze,
    attach_audit_ref,
)
from dopemux.governed_execution.freeze.receipt import (
    FreezeSubject,
    RepoIdentity,
    author_freeze_receipt,
    candidate_digest,
    substantive_path_digest,
)

__all__ = [
    "AuditBeforeFreeze",
    "AuditReceiptRef",
    "FreezeLifecycle",
    "FreezeState",
    "FreezeSubject",
    "IllegalTransition",
    "NewFreeze",
    "RepairRecorded",
    "RepoIdentity",
    "Revalidated",
    "ReviewSettled",
    "SubjectMismatch",
    "Unfreeze",
    "attach_audit_ref",
    "author_finality_receipt",
    "author_freeze_receipt",
    "candidate_digest",
    "substantive_path_digest",
]
