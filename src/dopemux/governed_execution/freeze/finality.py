"""FinalityReceipt authoring.

A FinalityReceipt can only be authored from a FreezeReceipt subject whose
lifecycle is FROZEN and whose ``head_sha`` equals the supplied audit ref's
``audited_head`` (enforced by reusing
``freeze.lifecycle.attach_audit_ref``, which raises ``AuditBeforeFreeze``
otherwise); on top of that, ``audited_head`` must exactly equal
``finality_head`` (the "exact-head rule" a JSON Schema cannot express on its
own), or ``SubjectMismatch`` is raised.

A FinalityReceipt authored here always carries ``merge_authorized`` and
``activation_authorized`` both ``False`` and ``authority`` ``"NONE"``:
W04 records terminal state, it never mints merge or activation authority.
``steward_readiness`` is copied verbatim from the caller-supplied
``steward_snapshot``, or ``"UNKNOWN"`` when none was supplied -- it is never
computed here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from dopemux.governed_execution.freeze.lifecycle import FreezeLifecycle, attach_audit_ref
from dopemux.governed_execution.receipts.store import EvidenceRef
from dopemux.governed_execution.receipts.validate import Provenance, validate_receipt

_KIND = "finality_receipt.v1"
_SCHEMA_VERSION = "dopemux.governed_execution.finality_receipt.v1"


class SubjectMismatch(Exception):
    """Raised when an audit ref's audited_head does not equal finality_head."""


@dataclass(frozen=True)
class AuditReceiptRef:
    """A caller-supplied pointer to an independent audit's own receipt.

    ``path``/``sha256`` identify the stored audit receipt (embedded into the
    FinalityReceipt's ``audit_receipt_ref`` field); ``audited_head`` and
    ``verdict`` are the audit's own claims, used to populate the
    FinalityReceipt's top-level ``audited_head`` and ``audit_verdict``
    fields and to enforce subject binding.
    """

    path: str
    sha256: str
    audited_head: str
    verdict: str


def author_finality_receipt(
    lifecycle: FreezeLifecycle,
    freeze_ref: EvidenceRef,
    audit_ref: AuditReceiptRef,
    finality_head: str,
    pr_ref: str,
    steward_snapshot: str | None,
    recorded_at: str,
    *,
    packet_id: str,
    macro_id: str,
    provenance: Provenance,
) -> Mapping[str, Any]:
    """Author and schema-validate a FinalityReceipt.

    Raises ``AuditBeforeFreeze`` (via ``attach_audit_ref``) if ``lifecycle``
    is not FROZEN or ``audit_ref.audited_head`` does not equal the frozen
    ``head_sha``. Raises ``SubjectMismatch`` if ``audit_ref.audited_head``
    does not equal ``finality_head``.
    """
    attach_audit_ref(
        lifecycle,
        EvidenceRef(path=audit_ref.path, sha256=audit_ref.sha256),
        audit_ref.audited_head,
    )
    if audit_ref.audited_head != finality_head:
        raise SubjectMismatch(
            f"audited_head {audit_ref.audited_head!r} != finality_head {finality_head!r}"
        )

    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "packet_id": packet_id,
        "macro_id": macro_id,
        "freeze_ref": {"path": freeze_ref.path, "sha256": freeze_ref.sha256},
        "audit_receipt_ref": {"path": audit_ref.path, "sha256": audit_ref.sha256},
        "audited_head": audit_ref.audited_head,
        "finality_head": finality_head,
        "exact_head_equality": True,
        "audit_verdict": audit_ref.verdict,
        "pr_ref": pr_ref,
        "steward_readiness": steward_snapshot if steward_snapshot is not None else "UNKNOWN",
        "merge_authorized": False,
        "activation_authorized": False,
        "recorded_at": recorded_at,
        "authority": "NONE",
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    validated = validate_receipt(_KIND, raw, provenance)
    return validated.payload
