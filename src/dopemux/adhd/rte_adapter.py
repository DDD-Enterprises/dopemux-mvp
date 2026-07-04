import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import httpx

from dopemux.memory.capture_client import try_emit_promotable_capture_event

try:
    from src.dopemux.adhd.attention_monitor import AttentionMonitor
    from src.dopemux.adhd.task_decomposer import TaskDecomposer

    ADHD_AVAILABLE = True
except ImportError:
    ADHD_AVAILABLE = False

logger = logging.getLogger(__name__)


class RTEAdapter:
    """Boundary adapter between 2025 Cognitive Plane and 2026 RTE architecture."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.rte_output_dir = self.workspace_root / "extraction"
        self.conport_url = os.getenv("CONPORT_URL", "http://localhost:3004")

        self.attention_monitor = None
        self.task_decomposer = None

        if ADHD_AVAILABLE:
            self.attention_monitor = AttentionMonitor(project_path=workspace_root)
            self.task_decomposer = TaskDecomposer(project_path=workspace_root)

    def get_latest_truth(
        self, artifact_type: str = "doctor/DOCTOR_FULL"
    ) -> Dict[str, Any]:
        """Read the latest specified JSON artifact from RTE output."""
        path = self.rte_output_dir / f"{artifact_type}.json"
        if not path.exists():
            raise FileNotFoundError(f"RTE Artifact not found at: {path}")

        with open(path, "r") as f:
            return json.load(f)

    async def write_decision_to_conport(
        self, decision_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Write truth artifacts as 'decisions' into ConPort KG.

        On success, also emits a best-effort ``decision.logged`` promotable
        source event so this write is promotion-CAPABLE when the event bus is
        provisioned (ENABLE_EVENTBUS + REDIS_URL); default dev environments
        remain ledger-only (see ``pm.writes.emit_pm_promotable_source_event``
        for the same pattern). Emission is fail-open: a capture failure never
        surfaces as a ConPort write failure.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.conport_url}/api/decisions", json=decision_data, timeout=10.0
            )
            response.raise_for_status()
            result = response.json()

        # The capture emit writes SQLite synchronously; run it off the event
        # loop so async callers never eat a filesystem-latency spike. Fail-open:
        # a scheduling error must never surface as a ConPort write failure.
        try:
            await asyncio.to_thread(self._emit_decision_logged_event, decision_data, result)
        except Exception as exc:  # pragma: no cover - defensive, emit is best-effort
            logger.debug("decision.logged capture dispatch failed: %s", exc)
        return result

    def _emit_decision_logged_event(
        self, decision_data: Dict[str, Any], conport_result: Dict[str, Any]
    ) -> None:
        """Best-effort, fail-open emit of the decision.logged source event."""
        try:
            decision_id = (
                conport_result.get("decision_id")
                or conport_result.get("id")
                or decision_data.get("decision_id")
                or decision_data.get("id")
                or decision_data.get("title")
            )
            title = decision_data.get("title") or "RTE decision"
            rationale = decision_data.get("rationale") or decision_data.get("summary") or ""
            try_emit_promotable_capture_event(
                "decision.logged",
                {
                    "decision_id": str(decision_id) if decision_id is not None else title,
                    "title": title,
                    "rationale": rationale,
                    "canonical_system": "conport",
                    "operation_type": "decision_log",
                    "authority": "conport",
                },
                source="dopemux.rte_adapter",
                mode="auto",
                emit_event_bus=None,
            )
        except Exception as exc:  # pragma: no cover - defensive, fail-open
            logger.debug("decision.logged capture emit failed: %s", exc)

    async def process_truth_with_adhd_context(
        self, artifact_type: str = "doctor/DOCTOR_FULL"
    ) -> Dict[str, Any]:
        """
        Read RTE truth, analyze current ADHD energy state, and decompose the
        truth findings into actionable, bite-sized tasks.
        """
        truth = self.get_latest_truth(artifact_type)

        if not ADHD_AVAILABLE or not self.attention_monitor or not self.task_decomposer:
            logger.warning("ADHD Engine not available. Falling back to raw truth.")
            return {"status": "raw", "truth": truth}

        # 1. Measure Energy/Attention State
        metrics = self.attention_monitor.get_current_metrics()
        energy_level = metrics.get("state", "medium")

        logger.info(f"Current ADHD Energy State: {energy_level}")

        # 2. Extract Actionable Items from Truth
        # For DOCTOR_FULL, we might look at 'phases' or 'recommendations'
        phases = truth.get("phases", [])

        # 3. Task Decomposition based on Energy
        decomposed_tasks = []
        for phase in phases:
            # Create a parent task for the phase
            task_id = self.task_decomposer.add_task(
                title=f"Process RTE Phase {phase}",
                description=f"Analyze and integrate findings from RTE Phase {phase}",
                priority="high",
                estimated_hours=2.0,
            )
            # The decomposer automatically breaks it down further if energy is low
            # (handled internally or via get_recommended_task)
            decomposed_tasks.append(task_id)

        # 4. Get Recommended Next Action
        next_task = self.task_decomposer.get_recommended_task(energy_level=energy_level)

        # 5. Log the Decomposition Decision to ConPort KG
        decision_payload = {
            "title": "RTE Truth Decomposed",
            "summary": f"Analyzed RTE artifact '{artifact_type}' at energy level '{energy_level}' and generated {len(decomposed_tasks)} tasks.",
            "rationale": "Automated ADHD Engine task breakdown to prevent cognitive overload.",
            "context": {
                "energy_level": energy_level,
                "tasks_created": decomposed_tasks,
                "recommended_action": (
                    next_task.get("title")
                    if isinstance(next_task, dict)
                    else (next_task.title if next_task else None)
                ),
                "source": "RTE_ADAPTER_ADHD_ENGINE",
            },
            "workspace_id": str(self.workspace_root.name),
        }

        # We need to run the async write_decision_to_conport
        # Since this method itself is async, we can await it directly.
        conport_result = await self.write_decision_to_conport(decision_payload)

        return {
            "status": "processed",
            "energy_level": energy_level,
            "tasks_created": len(decomposed_tasks),
            "recommended_next_action": (
                next_task.get("title")
                if isinstance(next_task, dict)
                else (next_task.title if next_task else None)
            ),
            "truth_artifact": truth,
            "conport_logging": conport_result,
        }
