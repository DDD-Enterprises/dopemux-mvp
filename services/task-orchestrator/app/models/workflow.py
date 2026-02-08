"""Workflow Stage-1/Stage-2 models (Idea and Epic)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, root_validator, validator


IdeaSource = Literal["user-request", "brainstorm", "bug-report", "other"]
IdeaStatus = Literal["new", "under-review", "approved", "rejected", "promoted"]
EpicPriority = Literal["critical", "high", "medium", "low"]
EpicStatus = Literal["planned", "in-planning", "ready", "in-progress", "done"]
EnergyLevel = Literal["low", "medium", "high"]


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def normalize_tags(tags: Optional[List[str]]) -> List[str]:
    """Normalize tags by trimming and de-duplicating while preserving order."""
    if not tags:
        return []

    result: List[str] = []
    seen = set()
    for raw in tags:
        tag = str(raw).strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


class ADHDMetadata(BaseModel):
    """ADHD-oriented metadata attached to epics."""

    estimated_complexity: float = Field(0.0, ge=0.0, le=1.0)
    required_energy_level: EnergyLevel = "medium"
    can_work_parallel: bool = True


class WorkflowIdea(BaseModel):
    """Stage-1 workflow idea persisted in ConPort custom_data."""

    id: str
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    source: IdeaSource = "other"
    creator: str = Field("system", min_length=1)
    tags: List[str] = Field(default_factory=list)
    status: IdeaStatus = "new"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    promoted_to_epic_id: Optional[str] = None

    @validator("id")
    def validate_id(cls, value: str) -> str:
        if not value.startswith("idea_"):
            raise ValueError("idea id must start with 'idea_'")
        return value

    @validator("title", "description", "creator")
    def strip_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("value cannot be empty")
        return text

    @validator("tags", pre=True, always=True)
    def normalize_tag_values(cls, value: Optional[List[str]]) -> List[str]:
        return normalize_tags(value)

    @validator("promoted_to_epic_id")
    def validate_promoted_epic_id(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith("epic_"):
            raise ValueError("promoted_to_epic_id must start with 'epic_'")
        return value


class WorkflowEpic(BaseModel):
    """Stage-2 workflow epic persisted in ConPort custom_data."""

    id: str
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    business_value: str = Field(..., min_length=1)
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: EpicPriority = "medium"
    status: EpicStatus = "planned"
    created_from_idea_id: Optional[str] = None
    leantime_project_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    adhd_metadata: ADHDMetadata = Field(default_factory=ADHDMetadata)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

    @validator("id")
    def validate_id(cls, value: str) -> str:
        if not value.startswith("epic_"):
            raise ValueError("epic id must start with 'epic_'")
        return value

    @validator("title", "description", "business_value")
    def strip_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("value cannot be empty")
        return text

    @validator("acceptance_criteria", pre=True, always=True)
    def normalize_criteria(cls, value: Optional[List[str]]) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value if str(item).strip()]

    @validator("created_from_idea_id")
    def validate_created_from_idea_id(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith("idea_"):
            raise ValueError("created_from_idea_id must start with 'idea_'")
        return value

    @validator("tags", pre=True, always=True)
    def normalize_tag_values(cls, value: Optional[List[str]]) -> List[str]:
        return normalize_tags(value)


class CreateIdeaRequest(BaseModel):
    """API request for creating workflow ideas."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    source: IdeaSource = "other"
    creator: str = Field("system", min_length=1)
    tags: List[str] = Field(default_factory=list)

    _normalize_tags = validator("tags", pre=True, allow_reuse=True)(normalize_tags)


class UpdateIdeaRequest(BaseModel):
    """API request for patching workflow ideas."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IdeaStatus] = None
    tags: Optional[List[str]] = None

    _normalize_tags = validator("tags", pre=True, allow_reuse=True)(normalize_tags)

    @root_validator(skip_on_failure=True)
    def require_mutation(cls, values):
        if all(values.get(field) is None for field in ("title", "description", "status", "tags")):
            raise ValueError("at least one field must be provided")
        return values


class CreateEpicRequest(BaseModel):
    """API request for creating epics directly."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    business_value: str = Field(..., min_length=1)
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: EpicPriority = "medium"
    status: EpicStatus = "planned"
    created_from_idea_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    adhd_metadata: ADHDMetadata = Field(default_factory=ADHDMetadata)

    @validator("acceptance_criteria", pre=True, always=True)
    def normalize_criteria(cls, value: Optional[List[str]]) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value if str(item).strip()]

    _normalize_tags = validator("tags", pre=True, allow_reuse=True)(normalize_tags)


class UpdateEpicRequest(BaseModel):
    """API request for patching epics."""

    title: Optional[str] = None
    description: Optional[str] = None
    business_value: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    priority: Optional[EpicPriority] = None
    status: Optional[EpicStatus] = None
    tags: Optional[List[str]] = None
    leantime_project_id: Optional[int] = None
    adhd_metadata: Optional[ADHDMetadata] = None

    @validator("acceptance_criteria", pre=True, always=False)
    def normalize_criteria(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        return [item.strip() for item in value if str(item).strip()]

    _normalize_tags = validator("tags", pre=True, allow_reuse=True)(normalize_tags)

    @root_validator(skip_on_failure=True)
    def require_mutation(cls, values):
        mutable_fields = (
            "title",
            "description",
            "business_value",
            "acceptance_criteria",
            "priority",
            "status",
            "tags",
            "leantime_project_id",
            "adhd_metadata",
        )
        if all(values.get(field) is None for field in mutable_fields):
            raise ValueError("at least one field must be provided")
        return values


class PromoteIdeaRequest(BaseModel):
    """API request for promoting idea to epic."""

    sync_to_leantime: bool = True
    title: Optional[str] = None
    description: Optional[str] = None
    business_value: Optional[str] = None
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: EpicPriority = "medium"
    tags: Optional[List[str]] = None
    adhd_metadata: ADHDMetadata = Field(default_factory=ADHDMetadata)

    @validator("acceptance_criteria", pre=True, always=True)
    def normalize_criteria(cls, value: Optional[List[str]]) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value if str(item).strip()]

    _normalize_tags = validator("tags", pre=True, allow_reuse=True)(normalize_tags)
