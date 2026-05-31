import httpx
import json
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel

from dopemux.orchestrator.idempotency import IdempotencyStore, IdempotencyState
from dopemux.orchestrator.operator_workflows import approve_phrase


logger = logging.getLogger(__name__)


class TransitionReceipt(BaseModel):
    success: bool
    status: str                  # "SUCCESS", "REFUSED", "FAILED"
    transition_name: str
    workflow_id: str
    idempotency_key: str
    approval_id: str
    response_envelope: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def apply_transition(
    *,
    project_id: str = "dopemux-mvp",
    workflow_id: str,
    transition_name: str,
    idempotency_key: str,
    proof_id: str,
    approval_phrase: str,
    expected_version: Optional[int] = None,
    reason: Optional[str] = None,
    actor: str = "operator",
    base_url: Optional[str] = None,
) -> TransitionReceipt:
    """Execute a workflow transition behind approval phrase and idempotency locks."""
    # 1. Enforce typed approval phrase check
    expected = approve_phrase(
        operation=f"workflow transition {transition_name}",
        resource="dopemux-mvp",
        writer="task-orchestrator",
        proof_id=proof_id,
    )
    
    if not approval_phrase or approval_phrase != expected:
        return TransitionReceipt(
            success=False,
            status="REFUSED",
            transition_name=transition_name,
            workflow_id=workflow_id,
            idempotency_key=idempotency_key,
            approval_id=proof_id,
            error="Invalid or missing approval phrase"
        )

    # 2. Lock idempotency key using IdempotencyStore
    store = IdempotencyStore()
    try:
        claim = store.claim_transition(
            idempotency_key=idempotency_key,
            project_id=project_id,
            workflow_id=workflow_id,
            transition_name=transition_name,
        )
        if claim["action"] == "COMPLETED":
            response_json = claim["response_json"]
            envelope = json.loads(response_json) if response_json else {}
            return TransitionReceipt(
                success=True,
                status="SUCCESS",
                transition_name=transition_name,
                workflow_id=workflow_id,
                idempotency_key=idempotency_key,
                approval_id=proof_id,
                response_envelope=envelope,
            )
    except ValueError as e:
        # Reused key for a different transition
        return TransitionReceipt(
            success=False,
            status="FAILED",
            transition_name=transition_name,
            workflow_id=workflow_id,
            idempotency_key=idempotency_key,
            approval_id=proof_id,
            error=str(e),
        )
    except RuntimeError as e:
        # Timeout waiting/already in progress
        return TransitionReceipt(
            success=False,
            status="FAILED",
            transition_name=transition_name,
            workflow_id=workflow_id,
            idempotency_key=idempotency_key,
            approval_id=proof_id,
            error="Transition already in progress or idempotency lock timeout",
        )

    # 3. Proceed to live execution
    from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter
    adapter = SyncTaskOrchestratorAdapter(base_url=base_url)
    
    try:
        result = adapter.transition(
            project_id=project_id,
            workflow_id=workflow_id,
            transition_name=transition_name,
            actor=actor,
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            reason=reason,
        )
        
        # 4. Validate response envelope
        from dopemux.orchestrator.operator_workflows import _validate_transition_proof_envelope
        errors = _validate_transition_proof_envelope(result)
        if errors:
            err_msg = "; ".join(
                e.get("message", "Unknown issue") if isinstance(e, dict) else getattr(e, "message", str(e))
                for e in errors
            )
            store.update_status(idempotency_key, IdempotencyState.INTENT)  # rollback
            return TransitionReceipt(
                success=False,
                status="FAILED",
                transition_name=transition_name,
                workflow_id=workflow_id,
                idempotency_key=idempotency_key,
                approval_id=proof_id,
                error=f"Upstream envelope validation failed: {err_msg}",
                response_envelope=result,
            )
            
        # Complete idempotency record
        store.update_status(
            idempotency_key=idempotency_key,
            status=IdempotencyState.COMPLETED,
            response_json=json.dumps(result)
        )
        
        return TransitionReceipt(
            success=True,
            status="SUCCESS",
            transition_name=transition_name,
            workflow_id=workflow_id,
            idempotency_key=idempotency_key,
            approval_id=proof_id,
            response_envelope=result,
        )
    except Exception as e:
        try:
            store.update_status(idempotency_key, IdempotencyState.INTENT)
        except Exception:
            pass
        return TransitionReceipt(
            success=False,
            status="FAILED",
            transition_name=transition_name,
            workflow_id=workflow_id,
            idempotency_key=idempotency_key,
            approval_id=proof_id,
            error=str(e),
        )
    finally:
        adapter.close()
