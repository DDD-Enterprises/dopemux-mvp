"""Normalized PM-plane read tools."""

from __future__ import annotations

import logging
import os
from importlib import import_module
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from core.config import Config
from dopemux.pm.adapters.conport import ConPortAdapter
from dopemux.pm.adapters.orchestrator import TaskOrchestratorAdapter
from dopemux.tools.conport_client import ConPortClient
from integrations.leantime_jsonrpc_client import LeantimeJSONRPCClient
logger = logging.getLogger(__name__)


class PMReadProvenance(BaseModel):
    source: str
    query_mode: str
    project_id: str


class PMReadSupportingSource(BaseModel):
    kind: str
    backend: str
    entity_ids: List[str] = Field(default_factory=list)


class PMReadEnvelope(BaseModel):
    canonical_backend: str
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    error: Optional[str] = None


class PMProjectContextResult(PMReadEnvelope):
    context_data: Dict[str, Any] = Field(default_factory=dict)


class PMPriorityQueueResult(PMReadEnvelope):
    legality_result: str = "unavailable"
    blockers: List[str] = Field(default_factory=list)
    queue_items: List[Dict[str, Any]] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None


class PMBlockersResult(PMReadEnvelope):
    legality_result: str = "unavailable"
    blockers: List[str] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None
    active_blockers: List[Dict[str, Any]] = Field(default_factory=list)


class PMWorkflowStateResult(PMReadEnvelope):
    legality_result: str = "unavailable"
    blockers: List[str] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    allowed_transitions: List[str] = Field(default_factory=list)


class PMSprintSnapshotResult(PMReadEnvelope):
    snapshot_data: Dict[str, Any] = Field(default_factory=dict)


class PMDecisionContextResult(PMReadEnvelope):
    decisions: List[Dict[str, Any]] = Field(default_factory=list)


class PMProjectKnowledgeResult(PMReadEnvelope):
    query: str
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class PMTechnicalContextResult(PMReadEnvelope):
    query: str
    technical_findings: List[Dict[str, Any]] = Field(default_factory=list)


_orchestrator = TaskOrchestratorAdapter()
_conport = ConPortAdapter()


class _PMMCPConfig:
    def __init__(self, timeout: int = 30, health_check_interval: int = 300):
        self.timeout = timeout
        self.health_check_interval = health_check_interval


def _project_provenance(source: str, query_mode: str, project_id: str) -> PMReadProvenance:
    return PMReadProvenance(source=source, query_mode=query_mode, project_id=project_id)


def _linked_ids(project_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    merged = {"project": project_id}
    if payload:
        merged.update(payload.get("linked_ids", {}))
    return merged


def _supporting_sources(*sources: tuple[str, str, List[str]]) -> List[PMReadSupportingSource]:
    return [
        PMReadSupportingSource(kind=kind, backend=backend, entity_ids=entity_ids)
        for kind, backend, entity_ids in sources
    ]


def _mcp_config() -> _PMMCPConfig:
    return _PMMCPConfig()


def _conport_context_client() -> ConPortClient:
    return ConPortClient(base_url=os.getenv("CONPORT_CONTEXT_URL", "http://localhost:3005"))


def _leantime_client() -> LeantimeJSONRPCClient:
    api_url = os.getenv("LEANTIME_API_URL") or os.getenv("LEANTIME_URL") or "http://localhost:8080"
    api_token = os.getenv("LEANTIME_API_TOKEN") or os.getenv("LEANTIME_TOKEN")
    if not api_token:
        raise RuntimeError("LEANTIME_API_TOKEN is not configured")
    return LeantimeJSONRPCClient(Config({"leantime": {"api_url": api_url, "api_token": api_token}}))


def _dope_context_client():
    client_cls = import_module("services.genetic_agent.shared.mcp.dope_context_client").DopeContextClient
    return client_cls(
        os.getenv("GENETIC_AGENT_DOPE_CONTEXT_URL", "http://localhost:3002"),
        _mcp_config(),
    )


def _serena_client():
    client_cls = import_module("services.genetic_agent.shared.mcp.serena_client").SerenaClient
    return client_cls(
        os.getenv("GENETIC_AGENT_SERENA_URL", "http://localhost:3001"),
        _mcp_config(),
    )


def _project_context_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMProjectContextResult:
    payload = payload or {}
    return PMProjectContextResult(
        canonical_backend="conport",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("conport", "project_context", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "conport", [project_id]),
            ("supporting", "leantime", [project_id]),
        ),
        context_data=payload.get("context_data", {}),
        error=error,
    )


def _priority_queue_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMPriorityQueueResult:
    payload = payload or {}
    return PMPriorityQueueResult(
        canonical_backend="task-orchestrator",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("task-orchestrator", "priority_queue", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "task-orchestrator", [project_id]),
            ("supporting", "leantime", [project_id]),
        ),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        queue_items=payload.get("queue_items", []),
        next_action=payload.get("next_action"),
        error=error,
    )


def _blockers_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMBlockersResult:
    payload = payload or {}
    return PMBlockersResult(
        canonical_backend="task-orchestrator",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("task-orchestrator", "blockers", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "task-orchestrator", [project_id]),
            ("supporting", "conport", [project_id]),
        ),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        next_action=payload.get("next_action"),
        active_blockers=payload.get("active_blockers", []),
        error=error,
    )


def _workflow_state_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMWorkflowStateResult:
    payload = payload or {}
    return PMWorkflowStateResult(
        canonical_backend="task-orchestrator",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("task-orchestrator", "workflow_state", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "task-orchestrator", [project_id]),
            ("supporting", "leantime", [project_id]),
        ),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        next_action=payload.get("next_action"),
        state=payload.get("state", {}),
        allowed_transitions=payload.get("allowed_transitions", []),
        error=error,
    )


def _sprint_snapshot_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMSprintSnapshotResult:
    payload = payload or {}
    return PMSprintSnapshotResult(
        canonical_backend="leantime",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("leantime", "sprint_snapshot", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "leantime", [project_id]),
            ("supporting", "conport", [project_id]),
        ),
        snapshot_data=payload.get("snapshot_data", {}),
        error=error,
    )


def _decision_context_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMDecisionContextResult:
    payload = payload or {}
    return PMDecisionContextResult(
        canonical_backend="conport",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("conport", "decision_context", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "conport", [project_id]),
            ("supporting", "dope-memory", [project_id]),
        ),
        decisions=payload.get("decisions", []),
        error=error,
    )


def _project_knowledge_result(
    project_id: str,
    query: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMProjectKnowledgeResult:
    payload = payload or {}
    return PMProjectKnowledgeResult(
        canonical_backend="dope-context",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("dope-context", "project_knowledge", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "dope-context", [project_id]),
            ("supporting", "conport", [project_id]),
            ("supporting", "dope-memory", [project_id]),
            ("supporting", "leantime", [project_id]),
        ),
        query=query,
        evidence=payload.get("evidence", []),
        error=error,
    )


def _technical_context_result(
    project_id: str,
    query: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMTechnicalContextResult:
    payload = payload or {}
    return PMTechnicalContextResult(
        canonical_backend="serena",
        project_id=project_id,
        linked_ids=_linked_ids(project_id, payload),
        provenance=_project_provenance("serena", "technical_context", project_id),
        supporting_sources=_supporting_sources(
            ("canonical", "serena", [project_id]),
            ("supporting", "conport", [project_id]),
            ("supporting", "dope-context", [project_id]),
        ),
        query=query,
        technical_findings=payload.get("technical_findings", []),
        error=error,
    )


def _normalize_knowledge_hits(raw_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_hits = raw_payload.get("results") or raw_payload.get("result") or raw_payload.get("hits") or []
    evidence: List[Dict[str, Any]] = []
    for index, item in enumerate(raw_hits, start=1):
        if not isinstance(item, dict):
            evidence.append(
                {
                    "rank": index,
                    "confidence": None,
                    "summary": str(item),
                    "source_plane": "dope-context",
                    "source_ref": None,
                }
            )
            continue
        evidence.append(
            {
                "rank": item.get("rank", index),
                "confidence": item.get("score", item.get("similarity")),
                "summary": item.get("summary") or item.get("snippet") or item.get("content") or item.get("title") or item.get("path") or "",
                "source_plane": "dope-context",
                "source_ref": item.get("source_path") or item.get("file_path") or item.get("path") or item.get("id") or item.get("url"),
                "source_kind": item.get("kind") or item.get("type"),
            }
        )
    return evidence


def _normalize_serena_findings(raw_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_findings = raw_payload.get("symbols") or raw_payload.get("results") or raw_payload.get("definitions") or []
    findings: List[Dict[str, Any]] = []
    for index, item in enumerate(raw_findings, start=1):
        if not isinstance(item, dict):
            findings.append(
                {
                    "rank": index,
                    "summary": str(item),
                    "source_plane": "serena",
                    "file_path": None,
                    "symbol": None,
                }
            )
            continue
        findings.append(
            {
                "rank": item.get("rank", index),
                "summary": item.get("summary") or item.get("name") or item.get("symbol") or item.get("file_path") or "",
                "source_plane": "serena",
                "file_path": item.get("file_path") or item.get("path"),
                "symbol": item.get("symbol") or item.get("name"),
                "symbol_type": item.get("symbol_type") or item.get("kind"),
                "line": item.get("line"),
                "column": item.get("column"),
            }
        )
    return findings


async def pm_get_project_context(project_id: str) -> PMProjectContextResult:
    """Read normalized project context from the PM record authority."""
    client = _conport_context_client()
    try:
        payload = await client.get_active_context(project_id)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        return _project_context_result(
            project_id,
            payload={
                "linked_ids": payload.get("linked_ids", {}),
                "context_data": payload,
            },
        )
    except Exception as exc:
        logger.warning("ConPort backend unavailable for pm_get_project_context: %s", exc)
        return _project_context_result(project_id, error=str(exc))
    finally:
        await client.close()


async def pm_get_priority_queue(project_id: str) -> PMPriorityQueueResult:
    """Read normalized priority queue from the workflow authority."""
    try:
        payload = await _orchestrator.get_queue(project_id)
        return _priority_queue_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("Task Orchestrator backend unavailable for pm_get_priority_queue")
        return _priority_queue_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_priority_queue: %s", exc)
        return _priority_queue_result(project_id, error=str(exc))


async def pm_get_blockers(project_id: str) -> PMBlockersResult:
    """Read normalized blockers from the workflow authority."""
    try:
        payload = await _orchestrator.get_blockers(project_id)
        return _blockers_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("Task Orchestrator backend unavailable for pm_get_blockers")
        return _blockers_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_blockers: %s", exc)
        return _blockers_result(project_id, error=str(exc))


async def pm_get_workflow_state(project_id: str) -> PMWorkflowStateResult:
    """Read normalized workflow state from the workflow authority."""
    try:
        payload = await _orchestrator.get_state(project_id)
        return _workflow_state_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("Task Orchestrator backend unavailable for pm_get_workflow_state")
        return _workflow_state_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_workflow_state: %s", exc)
        return _workflow_state_result(project_id, error=str(exc))


async def pm_get_sprint_snapshot(project_id: str) -> PMSprintSnapshotResult:
    """Read normalized sprint snapshot from the PM record authority."""
    try:
        numeric_project_id = int(project_id)
    except ValueError as exc:
        logger.warning("Leantime requires numeric project ids for pm_get_sprint_snapshot: %s", project_id)
        return _sprint_snapshot_result(project_id, error=f"invalid Leantime project id: {project_id}")

    client = _leantime_client()
    try:
        await client.connect()
        project_response = await client.get_project(numeric_project_id)
        tickets_response = await client.get_tickets(project_id=numeric_project_id, limit=100)
        if not project_response.success:
            raise RuntimeError(project_response.error or "Leantime project lookup failed")
        if not tickets_response.success:
            raise RuntimeError(tickets_response.error or "Leantime ticket lookup failed")
        tickets = tickets_response.data or []
        payload = {
            "linked_ids": {"leantime_project": str(numeric_project_id)},
            "snapshot_data": {
                "project": project_response.data,
                "tickets": tickets,
                "ticket_count": len(tickets),
            },
        }
        return _sprint_snapshot_result(project_id, payload=payload)
    except Exception as exc:
        logger.warning("Leantime backend unavailable for pm_get_sprint_snapshot: %s", exc)
        return _sprint_snapshot_result(project_id, error=str(exc))
    finally:
        await client.disconnect()


async def pm_get_decision_context(project_id: str) -> PMDecisionContextResult:
    """Read normalized decision context from ConPort."""
    try:
        payload = await _conport.search_decisions(limit=5)
        return _decision_context_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("ConPort backend unavailable for pm_get_decision_context")
        return _decision_context_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_decision_context: %s", exc)
        return _decision_context_result(project_id, error=str(exc))


async def pm_search_project_knowledge(project_id: str, query: str, top_k: int = 5) -> PMProjectKnowledgeResult:
    """Read normalized project knowledge from dope-context."""
    client = _dope_context_client()
    try:
        async with client:
            payload = await client.search_all(query, top_k=top_k)
        return _project_knowledge_result(
            project_id,
            query,
            payload={
                "evidence": _normalize_knowledge_hits(payload),
            },
        )
    except Exception as exc:
        logger.warning("dope-context backend unavailable for pm_search_project_knowledge: %s", exc)
        return _project_knowledge_result(project_id, query, error=str(exc))


async def pm_get_technical_context(project_id: str, query: str) -> PMTechnicalContextResult:
    """Read normalized technical context from Serena."""
    client = _serena_client()
    try:
        async with client:
            payload = await client.find_symbol(query)
        return _technical_context_result(
            project_id,
            query,
            payload={
                "technical_findings": _normalize_serena_findings(payload),
            },
        )
    except Exception as exc:
        logger.warning("Serena backend unavailable for pm_get_technical_context: %s", exc)
        return _technical_context_result(project_id, query, error=str(exc))
