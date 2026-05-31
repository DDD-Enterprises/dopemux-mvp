import os
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

from dopemux.pm.writes import (
    pm_log_decision,
    pm_log_progress,
    PMWriteConfig,
)
from dopemux.orchestrator.operator_workflows import approve_phrase


class WriteReceipt(BaseModel):
    canonical_writer: str
    requested_by: str
    approval_id: str
    source_packet: str
    upstream_response: Dict[str, Any]
    mirror_writer: Optional[str] = None
    mirror_status: str  # "SUCCESS", "FAILED", or "NONE"
    status: str         # "SUCCESS", "PARTIAL", "REFUSED", "FAILED"
    idempotency_key: str
    chain_of_custody: Dict[str, Any]


def verify_approval(
    *,
    operation: str,
    resource: str,
    writer: str,
    proof_id: str,
    approval_phrase: str,
) -> bool:
    """Verify that the approval phrase is present, valid, and matches."""
    if not approval_phrase:
        return False
    # Check exact match
    expected = approve_phrase(
        operation=operation,
        resource=resource,
        writer=writer,
        proof_id=proof_id,
    )
    if approval_phrase == expected:
        return True
    # Support alternate space/underscore format for robustness
    alt_operation = operation.replace("_", " ")
    expected_alt = approve_phrase(
        operation=alt_operation,
        resource=resource,
        writer=writer,
        proof_id=proof_id,
    )
    return approval_phrase == expected_alt


def write_decision(
    *,
    task_id: str,
    content: str,
    approval_phrase: str,
    proof_id: str,
    source_packet: str,
    idempotency_key: str,
    conport_client: Any,
    requested_by: str = "operator",
    resource: str = "dopemux-mvp",
) -> WriteReceipt:
    """Write a decision to ConPort behind the typed approval phrase gate."""
    # Enforce approval phrase gate
    if not verify_approval(
        operation="record_decision",
        resource=resource,
        writer="ConPort",
        proof_id=proof_id,
        approval_phrase=approval_phrase,
    ):
        return WriteReceipt(
            canonical_writer="ConPort",
            requested_by=requested_by,
            approval_id=proof_id,
            source_packet=source_packet,
            upstream_response={"error": "Invalid or missing approval phrase"},
            mirror_status="NONE",
            status="REFUSED",
            idempotency_key=idempotency_key,
            chain_of_custody={"verified": False},
        )

    # Route via existing PM helper
    config = PMWriteConfig(
        leantime_client=None,
        orchestrator_client=None,
        conport_client=conport_client,
        memory_client=None,  # No mirror for decisions
    )

    try:
        receipt = pm_log_decision(
            config=config,
            task_id=task_id,
            decision_notes=content,
            idempotency_key=idempotency_key,
        )
        
        status = "SUCCESS" if receipt.success else "FAILED"
        return WriteReceipt(
            canonical_writer="ConPort",
            requested_by=requested_by,
            approval_id=proof_id,
            source_packet=source_packet,
            upstream_response={
                "canonical_id": receipt.canonical_id,
                "success": receipt.success,
                "reconciliation_state": receipt.reconciliation_state,
            },
            mirror_writer=None,
            mirror_status="NONE",
            status=status,
            idempotency_key=idempotency_key,
            chain_of_custody={
                "verified": True,
                "operation": "record_decision",
                "resource": resource,
            },
        )
    except Exception as exc:
        return WriteReceipt(
            canonical_writer="ConPort",
            requested_by=requested_by,
            approval_id=proof_id,
            source_packet=source_packet,
            upstream_response={"error": str(exc)},
            mirror_status="NONE",
            status="FAILED",
            idempotency_key=idempotency_key,
            chain_of_custody={"verified": True},
        )


def write_progress(
    *,
    task_id: str,
    content: str,
    approval_phrase: str,
    proof_id: str,
    source_packet: str,
    idempotency_key: str,
    conport_client: Any,
    memory_client: Any,
    requested_by: str = "operator",
    resource: str = "dopemux-mvp",
) -> WriteReceipt:
    """Write progress to ConPort and mirror to dope-memory behind approval phrase."""
    # Enforce approval phrase gate
    if not verify_approval(
        operation="record_progress",
        resource=resource,
        writer="ConPort",
        proof_id=proof_id,
        approval_phrase=approval_phrase,
    ):
        return WriteReceipt(
            canonical_writer="ConPort",
            requested_by=requested_by,
            approval_id=proof_id,
            source_packet=source_packet,
            upstream_response={"error": "Invalid or missing approval phrase"},
            mirror_status="NONE",
            status="REFUSED",
            idempotency_key=idempotency_key,
            chain_of_custody={"verified": False},
        )

    # Route via existing PM helper
    config = PMWriteConfig(
        leantime_client=None,
        orchestrator_client=None,
        conport_client=conport_client,
        memory_client=memory_client,
    )

    try:
        receipt = pm_log_progress(
            config=config,
            task_id=task_id,
            progress_notes=content,
            idempotency_key=idempotency_key,
        )
        
        # Determine mirror status
        mirror_success = False
        mirror_err = "No mirror receipts returned"
        if receipt.mirror_receipts:
            m_rec = receipt.mirror_receipts[0]
            mirror_success = m_rec.success
            mirror_err = m_rec.error or ""
            
        mirror_status = "SUCCESS" if mirror_success else "FAILED"
        status = "SUCCESS" if (receipt.success and mirror_success) else ("PARTIAL" if receipt.success else "FAILED")
        
        return WriteReceipt(
            canonical_writer="ConPort",
            requested_by=requested_by,
            approval_id=proof_id,
            source_packet=source_packet,
            upstream_response={
                "canonical_id": receipt.canonical_id,
                "success": receipt.success,
                "reconciliation_state": receipt.reconciliation_state,
                "mirror_error": mirror_err if not mirror_success else None,
            },
            mirror_writer="dope-memory",
            mirror_status=mirror_status,
            status=status,
            idempotency_key=idempotency_key,
            chain_of_custody={
                "verified": True,
                "operation": "record_progress",
                "resource": resource,
            },
        )
    except Exception as exc:
        return WriteReceipt(
            canonical_writer="ConPort",
            requested_by=requested_by,
            approval_id=proof_id,
            source_packet=source_packet,
            upstream_response={"error": str(exc)},
            mirror_writer="dope-memory",
            mirror_status="FAILED",
            status="FAILED",
            idempotency_key=idempotency_key,
            chain_of_custody={"verified": True},
        )
