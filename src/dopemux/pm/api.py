"""Legacy async PM write boundary aligned to the phase-1 authority split."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

TRANSITION_PHASE_CAPTURE_DEFAULTS = {
    "start": "implementation",
    "started": "implementation",
    "done": "deployment",
    "complete": "deployment",
    "completed": "deployment",
    "block": "review",
    "blocked": "review",
}

from .writes import (
    PMActionKind,
    classify_pm_action,
    classify_pm_write,
    emit_pm_promotable_source_event,
    is_workflow_significant_payload,
)

class PMWriteBoundary:
    """
    Enforces the split between PM metadata writes and workflow-significant writes.
    """

    def __init__(self, leantime_client=None, orchestrator_client=None, conport_client=None, memory_client=None, project_id: str = "default"):
        self.leantime = leantime_client
        self.orchestrator = orchestrator_client
        self.conport = conport_client
        self.memory = memory_client
        self.project_id = project_id

    async def pm_update_work_item(self, work_item_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record/reflection updater for PM metadata only.
        Fails closed if the payload contains workflow-significant fields.
        """
        if not payload:
            return {
                "success": False,
                "operation_type": "metadata_update",
                "error": "Empty payload or no valid metadata fields provided."
            }

        try:
            action_kind = classify_pm_action(payload)
        except ValueError as exc:
            return {
                "success": False,
                "operation_type": "metadata_update",
                "canonical_backend": "leantime",
                "reflection_state": "failed",
                "error": str(exc),
                "reconciliation_state": "rejected"
            }

        if action_kind != PMActionKind.METADATA_UPDATE:
            _, workflow_fields = classify_pm_write(payload)
            return {
                "success": False,
                "operation_type": "metadata_update",
                "canonical_backend": "leantime",
                "reflection_state": "failed",
                "error": f"Direct update rejected because payload included workflow-significant fields: {workflow_fields}. Please use pm_transition_work_item for status/state changes.",
                "reconciliation_state": "rejected"
            }

        try:
            if self.leantime:
                await self.leantime.update_ticket(work_item_id, payload)
            else:
                raise RuntimeError("Leantime client unavailable")

            return {
                "success": True,
                "operation_type": "metadata_update",
                "canonical_backend": "leantime",
                "reflection_state": "succeeded",
                "reconciliation_state": "synchronized"
            }
        except Exception as e:
            logger.error(f"Leantime update failed: {e}")
            return {
                "success": False,
                "operation_type": "metadata_update",
                "canonical_backend": "leantime",
                "reflection_state": "failed",
                "error": str(e),
                "reconciliation_state": "failed"
            }

    async def pm_transition_work_item(self, work_item_id: str, transition: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        The only sanctioned workflow-significant path.
        Routes to Task Orchestrator through the project-scoped workflow endpoint.
        """
        try:
            if not self.orchestrator:
                raise RuntimeError("Task Orchestrator client unavailable")
            await self.orchestrator.transition_task(
                self.project_id,
                work_item_id,
                transition,
                payload or {},
            )
            normalized_transition = str(transition).strip().lower()
            if normalized_transition in {"done", "complete", "completed"}:
                emit_pm_promotable_source_event(
                    "task.completed",
                    project_id=self.project_id,
                    work_item_id=work_item_id,
                    canonical_system="task-orchestrator",
                    operation_type="transition",
                    payload={
                        "title": f"Workflow item {work_item_id}",
                        "transition": transition,
                    },
                )
            elif normalized_transition in {"block", "blocked"}:
                emit_pm_promotable_source_event(
                    "task.blocked",
                    project_id=self.project_id,
                    work_item_id=work_item_id,
                    canonical_system="task-orchestrator",
                    operation_type="transition",
                    payload={
                        "title": f"Workflow item {work_item_id}",
                        "transition": transition,
                        "reason": (payload or {}).get("reason", ""),
                    },
                )
            emit_pm_promotable_source_event(
                "workflow.phase_changed",
                project_id=self.project_id,
                work_item_id=work_item_id,
                canonical_system="task-orchestrator",
                operation_type="transition",
                payload={
                    "from_phase": "unknown",
                    "to_phase": (payload or {}).get("phase")
                    or TRANSITION_PHASE_CAPTURE_DEFAULTS.get(
                        normalized_transition,
                        "implementation",
                    ),
                    "transition": transition,
                },
            )

            return {
                "success": True,
                "operation_type": "transition",
                "canonical_backend": "task_orchestrator",
                "reflection_state": "not_requested",
                "reconciliation_state": "synchronized",
                "message": "transition succeeded canonically via the project-scoped workflow endpoint"
            }

        except Exception as e:
            logger.error(f"Task Orchestrator transition failed: {e}")
            return {
                "success": False,
                "operation_type": "transition",
                "canonical_backend": "task_orchestrator",
                "reflection_state": "failed",
                "error": str(e)
            }

    async def pm_log_progress(self, work_item_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log progress to ConPort / Dope Memory
        """
        if not self.conport:
            return {
                "success": False,
                "operation_type": "log_progress",
                "canonical_backend": "conport",
                "reflection_state": "failed",
                "error": "ConPort client unavailable",
                "reconciliation_state": "failed",
            }

        description = str(payload.get("description") or payload.get("msg") or "").strip()
        if not description:
            return {
                "success": False,
                "operation_type": "log_progress",
                "canonical_backend": "conport",
                "reflection_state": "failed",
                "error": "Progress payload must include description or msg.",
                "reconciliation_state": "failed",
            }

        try:
            is_decision = payload.get("is_decision") is True
            await self.conport.record_progress(work_item_id, description, is_decision, payload.get("idempotency_key"))
            if is_decision:
                emit_pm_promotable_source_event(
                    "decision.logged",
                    project_id=self.project_id,
                    work_item_id=work_item_id,
                    canonical_system="conport",
                    operation_type="log_progress",
                    payload={
                        "decision_id": work_item_id,
                        "title": f"Decision for {work_item_id}",
                        "rationale": description,
                    },
                )
        except Exception as exc:
            logger.error("ConPort progress write failed: %s", exc)
            return {
                "success": False,
                "operation_type": "log_progress",
                "canonical_backend": "conport",
                "reflection_state": "failed",
                "error": str(exc),
                "reconciliation_state": "failed",
            }

        reflection_state = "succeeded"
        if self.memory:
            try:
                await self.memory.append_chronicle(work_item_id, description, False, payload.get("idempotency_key"))
            except Exception as exc:
                logger.warning("Dope-memory mirror failed for progress log %s: %s", work_item_id, exc)
                reflection_state = "degraded"
        else:
            reflection_state = "degraded"

        return {
            "success": True,
            "operation_type": "log_progress",
            "canonical_backend": "conport",
            "reflection_state": reflection_state,
            "reconciliation_state": "synchronized" if reflection_state == "succeeded" else "pending_reconciliation"
        }
