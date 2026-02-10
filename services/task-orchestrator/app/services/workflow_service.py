"""Business logic for ADR-197 Stage-1/Stage-2 workflow runtime."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

# Ensure repo-root imports work in isolated service runtime.
def _find_repo_root():
    curr = Path(__file__).resolve().parent
    while curr.parent != curr:
        if (curr / "services").exists() and (curr / "src").exists():
            return curr
        curr = curr.parent
    # Fallback to a reasonable default if markers not found
    try:
        return Path(__file__).resolve().parents[4]
    except IndexError:
        return Path(__file__).resolve().parents[2]

REPO_ROOT = _find_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.shared.dopecon_bridge_client import (  # type: ignore
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

from ..models.workflow import (
    CreateEpicRequest,
    CreateIdeaRequest,
    PromoteIdeaRequest,
    UpdateEpicRequest,
    UpdateIdeaRequest,
    WorkflowEpic,
    WorkflowIdea,
    normalize_tags,
    utc_now_iso,
)
from .workflow_store import WorkflowStore, WorkflowStoreError

logger = logging.getLogger(__name__)


class WorkflowServiceError(RuntimeError):
    """Base workflow service error."""


class WorkflowNotFoundError(WorkflowServiceError):
    """Raised when an entity cannot be found."""


class WorkflowConflictError(WorkflowServiceError):
    """Raised when workflow state transitions are invalid."""


class WorkflowUnavailableError(WorkflowServiceError):
    """Raised when upstream persistence or bridge services are unavailable."""


class WorkflowService:
    """Service implementing Idea/Epic create/list/update/promote behavior."""

    def __init__(
        self,
        workspace_id: str,
        *,
        store: Optional[WorkflowStore] = None,
        bridge_url: Optional[str] = None,
        bridge_token: Optional[str] = None,
    ) -> None:
        self.workspace_id = workspace_id
        self.enabled = os.getenv("DOPMUX_WORKFLOW_ENABLE", "true").lower() == "true"
        self.default_idea_limit = int(os.getenv("DOPMUX_WORKFLOW_DEFAULT_IDEA_LIMIT", "50"))
        self.default_epic_limit = int(os.getenv("DOPMUX_WORKFLOW_DEFAULT_EPIC_LIMIT", "50"))
        self.default_sync_to_leantime = (
            os.getenv("DOPMUX_WORKFLOW_PROMOTION_SYNC_LEANTIME", "true").lower() == "true"
        )

        self.store = store or WorkflowStore(
            workspace_id=workspace_id,
            bridge_url=bridge_url,
            bridge_token=bridge_token,
        )
        self.bridge_client = AsyncDopeconBridgeClient(
            config=DopeconBridgeConfig(
                base_url=bridge_url or os.getenv("DOPECON_BRIDGE_URL", "http://localhost:3016"),
                token=bridge_token if bridge_token is not None else os.getenv("DOPECON_BRIDGE_TOKEN"),
                timeout=10.0,
                source_plane=os.getenv("DOPECON_BRIDGE_SOURCE_PLANE", "cognitive_plane"),
            )
        )
        self.metrics: Dict[str, int] = {
            "workflow_ideas_created_total": 0,
            "workflow_epics_created_total": 0,
            "workflow_promotions_total": 0,
            "workflow_promotion_failures_total": 0,
        }

    async def close(self) -> None:
        await self.store.close()
        await self.bridge_client.aclose()

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise WorkflowConflictError("workflow runtime is disabled by DOPMUX_WORKFLOW_ENABLE")

    async def create_idea(self, request: CreateIdeaRequest) -> WorkflowIdea:
        self._require_enabled()
        now = utc_now_iso()
        idea = WorkflowIdea(
            id=f"idea_{uuid4().hex}",
            title=request.title,
            description=request.description,
            source=request.source,
            creator=request.creator,
            tags=request.tags,
            status="new",
            created_at=now,
            updated_at=now,
        )
        await self._save_idea_or_raise(idea)
        self.metrics["workflow_ideas_created_total"] += 1
        return idea

    async def list_ideas(
        self,
        *,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[WorkflowIdea]:
        self._require_enabled()
        resolved_limit = limit or self.default_idea_limit
        rows = await self._call_store(
            self.store.list_ideas(status=status, tag=tag, limit=resolved_limit)
        )
        return self._coerce_ideas(rows)

    async def update_idea(self, idea_id: str, request: UpdateIdeaRequest) -> WorkflowIdea:
        self._require_enabled()
        idea = await self.get_idea(idea_id)

        if idea.status == "promoted" and request.status and request.status != "promoted":
            raise WorkflowConflictError("promoted ideas cannot be moved to a non-promoted state")

        if request.title is not None:
            idea.title = request.title
        if request.description is not None:
            idea.description = request.description
        if request.status is not None:
            idea.status = request.status
        if request.tags is not None:
            idea.tags = request.tags

        if idea.status == "promoted" and not idea.promoted_to_epic_id:
            raise WorkflowConflictError("promoted ideas must include promoted_to_epic_id")

        idea.updated_at = utc_now_iso()
        await self._save_idea_or_raise(idea)
        return idea

    async def create_epic(self, request: CreateEpicRequest) -> WorkflowEpic:
        self._require_enabled()
        now = utc_now_iso()
        epic = WorkflowEpic(
            id=f"epic_{uuid4().hex}",
            title=request.title,
            description=request.description,
            business_value=request.business_value,
            acceptance_criteria=request.acceptance_criteria,
            priority=request.priority,
            status=request.status,
            created_from_idea_id=request.created_from_idea_id,
            tags=request.tags,
            adhd_metadata=request.adhd_metadata,
            created_at=now,
            updated_at=now,
        )
        await self._save_epic_or_raise(epic)
        self.metrics["workflow_epics_created_total"] += 1
        return epic

    async def list_epics(
        self,
        *,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[WorkflowEpic]:
        self._require_enabled()
        resolved_limit = limit or self.default_epic_limit
        rows = await self._call_store(
            self.store.list_epics(
                status=status,
                priority=priority,
                tag=tag,
                limit=resolved_limit,
            )
        )
        return self._coerce_epics(rows)

    async def update_epic(self, epic_id: str, request: UpdateEpicRequest) -> WorkflowEpic:
        self._require_enabled()
        epic = await self.get_epic(epic_id)

        if request.title is not None:
            epic.title = request.title
        if request.description is not None:
            epic.description = request.description
        if request.business_value is not None:
            epic.business_value = request.business_value
        if request.acceptance_criteria is not None:
            epic.acceptance_criteria = request.acceptance_criteria
        if request.priority is not None:
            epic.priority = request.priority
        if request.status is not None:
            epic.status = request.status
        if request.tags is not None:
            epic.tags = request.tags
        if request.leantime_project_id is not None:
            epic.leantime_project_id = request.leantime_project_id
        if request.adhd_metadata is not None:
            epic.adhd_metadata = request.adhd_metadata

        epic.updated_at = utc_now_iso()
        await self._save_epic_or_raise(epic)
        return epic

    async def promote_idea(
        self,
        idea_id: str,
        request: PromoteIdeaRequest,
    ) -> Dict[str, object]:
        self._require_enabled()
        idea = await self.get_idea(idea_id)

        if idea.promoted_to_epic_id:
            existing = await self.get_epic(idea.promoted_to_epic_id)
            self.metrics["workflow_promotions_total"] += 1
            return {
                "idea": idea,
                "epic": existing,
                "already_promoted": True,
                "warning": None,
            }

        now = utc_now_iso()
        epic = WorkflowEpic(
            id=f"epic_{uuid4().hex}",
            title=request.title or idea.title,
            description=request.description or idea.description,
            business_value=request.business_value or f"Promoted from idea {idea.id}",
            acceptance_criteria=request.acceptance_criteria,
            priority=request.priority,
            status="planned",
            created_from_idea_id=idea.id,
            tags=normalize_tags((idea.tags or []) + (request.tags or [])),
            adhd_metadata=request.adhd_metadata,
            created_at=now,
            updated_at=now,
        )

        sync_to_leantime = request.sync_to_leantime and self.default_sync_to_leantime
        warning: Optional[str] = None
        if sync_to_leantime:
            leantime_project_id, warning = await self._sync_epic_to_leantime(epic)
            epic.leantime_project_id = leantime_project_id
            if warning:
                logger.warning("Workflow promotion Leantime sync degraded: %s", warning)
                self.metrics["workflow_promotion_failures_total"] += 1

        await self._save_epic_or_raise(epic)

        idea.status = "promoted"
        idea.promoted_to_epic_id = epic.id
        idea.updated_at = utc_now_iso()
        await self._save_idea_or_raise(idea)

        self.metrics["workflow_epics_created_total"] += 1
        self.metrics["workflow_promotions_total"] += 1
        return {
            "idea": idea,
            "epic": epic,
            "already_promoted": False,
            "warning": warning,
        }

    async def get_idea(self, idea_id: str) -> WorkflowIdea:
        row = await self._call_store(self.store.get_idea(idea_id))
        if not row:
            raise WorkflowNotFoundError(f"idea not found: {idea_id}")
        return WorkflowIdea(**row)

    async def get_epic(self, epic_id: str) -> WorkflowEpic:
        row = await self._call_store(self.store.get_epic(epic_id))
        if not row:
            raise WorkflowNotFoundError(f"epic not found: {epic_id}")
        return WorkflowEpic(**row)

    async def _save_idea_or_raise(self, idea: WorkflowIdea) -> None:
        saved = await self._call_store(self.store.save_idea(idea.dict()))
        if not saved:
            raise WorkflowUnavailableError("failed to persist workflow idea")

    async def _save_epic_or_raise(self, epic: WorkflowEpic) -> None:
        saved = await self._call_store(self.store.save_epic(epic.dict()))
        if not saved:
            raise WorkflowUnavailableError("failed to persist workflow epic")

    async def _call_store(self, awaitable):
        try:
            return await awaitable
        except WorkflowStoreError as exc:
            raise WorkflowUnavailableError(str(exc)) from exc

    @staticmethod
    def _coerce_ideas(rows: List[Dict[str, object]]) -> List[WorkflowIdea]:
        ideas: List[WorkflowIdea] = []
        for row in rows:
            try:
                ideas.append(WorkflowIdea(**row))
            except Exception as exc:
                logger.warning("Skipping invalid workflow idea row: %s", exc)
        return ideas

    @staticmethod
    def _coerce_epics(rows: List[Dict[str, object]]) -> List[WorkflowEpic]:
        epics: List[WorkflowEpic] = []
        for row in rows:
            try:
                epics.append(WorkflowEpic(**row))
            except Exception as exc:
                logger.warning("Skipping invalid workflow epic row: %s", exc)
        return epics

    async def _sync_epic_to_leantime(self, epic: WorkflowEpic) -> tuple[Optional[int], Optional[str]]:
        """Best-effort PM-plane project creation for promoted epics."""
        try:
            response = await self.bridge_client.route_pm(
                operation="leantime.create_project",
                data={
                    "name": epic.title,
                    "project_name": epic.title,
                    "description": epic.description,
                    "priority": epic.priority,
                    "metadata": {
                        "epic_id": epic.id,
                        "created_from_idea_id": epic.created_from_idea_id,
                        "business_value": epic.business_value,
                    },
                },
                requester="task-orchestrator",
            )
        except Exception as exc:
            return None, str(exc)

        if not response.success:
            return None, response.error or "leantime route failed"

        payload = dict(response.data or {})
        for key in ("project_id", "id", "projectId"):
            if key not in payload:
                continue
            value = payload.get(key)
            if value is None or value == "":
                continue
            try:
                return int(value), None
            except (TypeError, ValueError):
                return None, f"unexpected non-integer Leantime project id: {value}"

        return None, "Leantime route succeeded but no project id returned"

